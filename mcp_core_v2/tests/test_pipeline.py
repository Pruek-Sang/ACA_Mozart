"""
MCP Core v2 Pipeline Tests
Tests the end-to-end design pipeline with demo scenarios.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from models.contracts import (
    RoomType,
    RoomInput,
    ProjectInput,
    OutletType,
    LightType,
)
from models.baseline import DEMO_BEDROOM
from pipeline import DesignPipeline, create_demo_project, run_demo
from core.template_resolver import TemplateResolver
from core.load_calculator import LoadCalculator
from core.wire_sizer import WireSizer
from core.breaker_selector import BreakerSelector
from core.conduit_sizer import ConduitSizer
from core.compliance_checker import ComplianceChecker
from core.autolisp_generator import AutoLISPGenerator
from core.result_builder import ResultBuilder


class TestDemoRoom(unittest.TestCase):
    """Test with demo 4x3m bedroom."""
    
    def setUp(self):
        """Set up demo room."""
        self.room = RoomInput(
            room_id=DEMO_BEDROOM["room_id"],
            room_type=RoomType(DEMO_BEDROOM["room_type"]),
            width=DEMO_BEDROOM["width"],
            length=DEMO_BEDROOM["length"],
            height=DEMO_BEDROOM["height"],
        )
        self.pipeline = DesignPipeline()
    
    def test_demo_room_area(self):
        """Test demo room has correct area."""
        area = self.room.width * self.room.length
        self.assertEqual(area, 12.0)  # 4 * 3 = 12 m²
    
    def test_demo_room_design(self):
        """Test complete room design."""
        design = self.pipeline.design_room(self.room)
        
        # Check room properties
        self.assertEqual(design.room_id, self.room.room_id)
        self.assertEqual(design.room_type, RoomType.BEDROOM)
        self.assertEqual(design.area, 12.0)
        
        # Check outlets (should have minimum for bedroom)
        self.assertGreaterEqual(len(design.outlets), 3)
        
        # Check lights (should have at least 1)
        self.assertGreaterEqual(len(design.lights), 1)
        
        # Check switches (at least 1 for lights)
        self.assertGreaterEqual(len(design.switches), 1)
        
        # Check circuits
        self.assertGreaterEqual(len(design.circuits), 2)  # outlet + lighting
        
        # Check total load is calculated
        self.assertGreater(design.total_load_watts, 0)


class TestTemplateResolver(unittest.TestCase):
    """Test template resolver module."""
    
    def setUp(self):
        self.resolver = TemplateResolver()
        self.bedroom = RoomInput(
            room_id="test-bedroom",
            room_type=RoomType.BEDROOM,
            width=4.0,
            length=3.0,
        )
        self.kitchen = RoomInput(
            room_id="test-kitchen",
            room_type=RoomType.KITCHEN,
            width=3.0,
            length=3.0,
        )
    
    def test_outlet_count_bedroom(self):
        """Test outlet count for bedroom."""
        count = self.resolver.calculate_outlet_count(self.bedroom)
        self.assertGreaterEqual(count, 3)  # Minimum for bedroom
    
    def test_outlet_positions(self):
        """Test outlet positions are within room bounds."""
        positions = self.resolver.calculate_outlet_positions(self.bedroom)
        
        for x, y in positions:
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x, self.bedroom.width)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(y, self.bedroom.length)
    
    def test_light_count(self):
        """Test light fixture count."""
        count = self.resolver.calculate_light_count(self.bedroom)
        self.assertGreaterEqual(count, 1)
    
    def test_light_positions(self):
        """Test light positions are within room bounds."""
        positions = self.resolver.calculate_light_positions(self.bedroom)
        
        for x, y in positions:
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x, self.bedroom.width)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(y, self.bedroom.length)
    
    def test_outlet_type_kitchen(self):
        """Test kitchen gets grounded outlets."""
        outlet_type = self.resolver.get_outlet_type(self.kitchen)
        self.assertEqual(outlet_type, OutletType.GROUNDED)
    
    def test_outlet_type_bedroom(self):
        """Test bedroom gets standard outlets."""
        outlet_type = self.resolver.get_outlet_type(self.bedroom)
        self.assertEqual(outlet_type, OutletType.STANDARD)


class TestLoadCalculator(unittest.TestCase):
    """Test load calculator module."""
    
    def setUp(self):
        self.calculator = LoadCalculator(voltage=220.0)
    
    def test_outlet_load(self):
        """Test outlet load calculation."""
        from models.contracts import OutletPlacement
        
        outlets = [
            OutletPlacement(
                outlet_id="out1",
                outlet_type=OutletType.STANDARD,
                x=1.0, y=1.0,
                circuit_id="c1"
            ),
            OutletPlacement(
                outlet_id="out2",
                outlet_type=OutletType.STANDARD,
                x=2.0, y=1.0,
                circuit_id="c1"
            ),
        ]
        
        load = self.calculator.calculate_outlet_load(outlets, RoomType.BEDROOM)
        self.assertEqual(load, 360)  # 2 * 180W
    
    def test_lighting_load(self):
        """Test lighting load calculation."""
        from models.contracts import LightPlacement
        
        lights = [
            LightPlacement(
                light_id="lt1",
                light_type=LightType.CEILING,
                x=2.0, y=1.5,
                wattage=15,
                circuit_id="c1"
            ),
        ]
        
        load = self.calculator.calculate_lighting_load(lights)
        self.assertEqual(load, 15)
    
    def test_watts_to_amps(self):
        """Test watts to amps conversion."""
        amps = self.calculator.watts_to_amps(1980, power_factor=0.9)
        self.assertAlmostEqual(amps, 10.0, places=1)
    
    def test_demand_factor_lighting(self):
        """Test demand factor for lighting."""
        # Under 2000W - should be 100%
        demand = self.calculator.apply_demand_factor(1000, "lighting")
        self.assertEqual(demand, 1000)
        
        # Over 2000W - first 2000 at 100%, rest at 35%
        demand = self.calculator.apply_demand_factor(3000, "lighting")
        expected = 2000 + (1000 * 0.35)
        self.assertEqual(demand, expected)


class TestWireSizer(unittest.TestCase):
    """Test wire sizer module."""
    
    def setUp(self):
        self.sizer = WireSizer(voltage=220.0)
    
    def test_select_wire_for_load(self):
        """Test wire selection for given load."""
        result = self.sizer.select_wire_size(
            load_watts=1000,
            max_voltage_drop_percent=3.0,
            length_m=20.0
        )
        
        self.assertIn("wire_size_sqmm", result)
        self.assertIn("max_ampacity", result)
        self.assertIn("voltage_drop_percent", result)
        self.assertTrue(result["compliant"])
    
    def test_wire_ampacity(self):
        """Test required ampacity calculation."""
        ampacity = self.sizer.calculate_required_ampacity(1000, 0.9)
        
        # 1000W / 220V / 0.9 * 1.25 = ~6.3A
        self.assertGreater(ampacity, 5)
        self.assertLess(ampacity, 10)


class TestBreakerSelector(unittest.TestCase):
    """Test breaker selector module."""
    
    def setUp(self):
        self.selector = BreakerSelector(voltage=220.0)
    
    def test_select_breaker(self):
        """Test breaker selection."""
        result = self.selector.select_breaker(
            load_watts=1000,
            wire_ampacity=18,
            circuit_type="general"
        )
        
        self.assertIn("breaker_size", result)
        self.assertIn("coordinated", result)
        self.assertTrue(result["coordinated"])
    
    def test_main_breaker(self):
        """Test main breaker selection."""
        result = self.selector.select_main_breaker(
            total_demand_load=5000,
            phases=1
        )
        
        self.assertIn("main_breaker_size", result)
        # 5000W / 220V / 0.9 * 1.25 ≈ 32A
        self.assertGreaterEqual(result["main_breaker_size"], 32)


class TestConduitSizer(unittest.TestCase):
    """Test conduit sizer module."""
    
    def setUp(self):
        self.sizer = ConduitSizer()
    
    def test_select_conduit(self):
        """Test conduit selection."""
        result = self.sizer.select_for_circuit(
            wire_size_sqmm=2.5,
            with_ground=True,
            with_neutral=True
        )
        
        self.assertIn("conduit_size_mm", result)
        self.assertIn("compliant", result)
        self.assertTrue(result["compliant"])


class TestComplianceChecker(unittest.TestCase):
    """Test compliance checker module."""
    
    def setUp(self):
        self.checker = ComplianceChecker()
    
    def test_quick_check(self):
        """Test quick compliance check."""
        from models.contracts import OutletPlacement, LightPlacement, CircuitSpec
        
        outlets = [
            OutletPlacement(
                outlet_id="o1",
                outlet_type=OutletType.STANDARD,
                x=1.0, y=0.1,
                circuit_id="c1"
            ),
            OutletPlacement(
                outlet_id="o2",
                outlet_type=OutletType.STANDARD,
                x=3.0, y=0.1,
                circuit_id="c1"
            ),
        ]
        
        lights = [
            LightPlacement(
                light_id="l1",
                light_type=LightType.CEILING,
                x=2.0, y=1.5,
                wattage=15,
                circuit_id="c2"
            ),
        ]
        
        circuits = [
            CircuitSpec(
                circuit_id="c1",
                circuit_type="outlet",
                breaker_size=16,
                wire_size=2.5,
                conduit_size=16,
                total_load=360,
                connected_devices=["o1", "o2"]
            ),
        ]
        
        result = self.checker.quick_check(outlets, lights, circuits, room_area=12.0)
        
        self.assertIn("passed", result)
        self.assertIn("issues", result)


class TestAutoLISPGenerator(unittest.TestCase):
    """Test AutoLISP generator module."""
    
    def setUp(self):
        self.generator = AutoLISPGenerator()
    
    def test_generate_simple_script(self):
        """Test simple outlet script generation."""
        outlets = [
            {"x": 1.0, "y": 0.1},
            {"x": 3.0, "y": 0.1},
        ]
        
        script = self.generator.generate_simple_outlet_script(outlets)
        
        self.assertIn("defun", script)
        self.assertIn("INSERT", script)
        self.assertIn("ELEC_OUTLET", script)


class TestPipeline(unittest.TestCase):
    """Test complete pipeline."""
    
    def test_create_demo_project(self):
        """Test demo project creation."""
        project = create_demo_project()
        
        self.assertEqual(project.project_id, "demo-project-001")
        self.assertEqual(len(project.rooms), 1)
        self.assertEqual(project.rooms[0].room_type, RoomType.BEDROOM)
    
    def test_run_demo(self):
        """Test demo pipeline execution."""
        result = run_demo()
        
        # Check result structure
        self.assertEqual(result.project_id, "demo-project-001")
        self.assertEqual(len(result.rooms), 1)
        
        # Check room design
        room = result.rooms[0]
        self.assertEqual(room.room_type, RoomType.BEDROOM)
        self.assertEqual(room.area, 12.0)
        
        # Check compliance
        self.assertIsNotNone(result.compliance)
        
        # Check AutoLISP script is generated
        self.assertTrue(len(result.autolisp_script) > 0)
        self.assertIn("defun", result.autolisp_script)
    
    def test_quick_design(self):
        """Test quick design functionality."""
        pipeline = DesignPipeline()
        result = pipeline.quick_design(
            room_type="bedroom",
            width=4.0,
            length=3.0
        )
        
        self.assertEqual(result.room_type, RoomType.BEDROOM)
        self.assertEqual(result.area, 12.0)
        self.assertGreater(len(result.outlets), 0)
        self.assertGreater(len(result.lights), 0)


class TestResultBuilder(unittest.TestCase):
    """Test result builder module."""
    
    def setUp(self):
        self.builder = ResultBuilder()
    
    def test_build_outlet(self):
        """Test outlet building."""
        outlet = self.builder.build_outlet(
            room_id="room-1",
            x=1.0,
            y=0.1,
            outlet_type=OutletType.STANDARD,
            circuit_id="c1"
        )
        
        self.assertEqual(outlet.x, 1.0)
        self.assertEqual(outlet.y, 0.1)
        self.assertEqual(outlet.outlet_type, OutletType.STANDARD)
        self.assertIn("room-1", outlet.outlet_id)
    
    def test_build_circuit(self):
        """Test circuit building."""
        circuit = self.builder.build_circuit(
            room_id="room-1",
            circuit_type="outlet",
            breaker_size=16,
            wire_size=2.5,
            conduit_size=16,
            total_load=360,
            connected_devices=["o1", "o2"]
        )
        
        self.assertEqual(circuit.circuit_type, "outlet")
        self.assertEqual(circuit.breaker_size, 16)
        self.assertIn("room-1", circuit.circuit_id)


if __name__ == "__main__":
    unittest.main()
