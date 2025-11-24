"""
MCP Core v2 Pipeline
Main orchestration pipeline for electrical design generation.
"""

from typing import List, Dict, Any, Optional

from models.contracts import (
    RoomInput,
    ProjectInput,
    RoomDesign,
    ProjectDesign,
    ComplianceResult,
)
from core.template_resolver import TemplateResolver
from core.load_calculator import LoadCalculator
from core.wire_sizer import WireSizer
from core.breaker_selector import BreakerSelector
from core.conduit_sizer import ConduitSizer
from core.compliance_checker import ComplianceChecker
from core.pandapower_adapter import PandapowerAdapter
from core.autolisp_generator import AutoLISPGenerator
from core.result_builder import ResultBuilder


class DesignPipeline:
    """
    Main design pipeline orchestrating all modules.
    
    Pipeline flow:
    1. Template Resolution - Get placement rules
    2. Load Calculation - Calculate electrical loads
    3. Wire Sizing - Select wire sizes
    4. Breaker Selection - Select breakers
    5. Conduit Sizing - Select conduit sizes
    6. Power Flow Analysis - Validate with pandapower
    7. Compliance Check - Verify against standards
    8. Result Building - Assemble final output
    9. AutoLISP Generation - Create CAD scripts
    """
    
    def __init__(self, voltage: float = 220.0, phases: int = 1):
        """
        Initialize pipeline with system parameters.
        
        Args:
            voltage: System voltage (default 220V for Thailand)
            phases: Number of phases
        """
        self.voltage = voltage
        self.phases = phases
        
        # Initialize modules
        self.template_resolver = TemplateResolver()
        self.load_calculator = LoadCalculator(voltage)
        self.wire_sizer = WireSizer(voltage)
        self.breaker_selector = BreakerSelector(voltage)
        self.conduit_sizer = ConduitSizer()
        self.compliance_checker = ComplianceChecker()
        self.pandapower_adapter = PandapowerAdapter(voltage / 1000)
        self.autolisp_generator = AutoLISPGenerator()
        self.result_builder = ResultBuilder()
    
    def design_room(self, room: RoomInput) -> RoomDesign:
        """
        Design a single room.
        
        Args:
            room: Room input specification
            
        Returns:
            Complete room design
        """
        # Step 1: Resolve template and get positions
        outlet_positions = self.template_resolver.calculate_outlet_positions(room)
        light_positions = self.template_resolver.calculate_light_positions(room)
        outlet_type = self.template_resolver.get_outlet_type(room)
        light_type = self.template_resolver.get_preferred_light_type(room)
        light_wattage = self.template_resolver.get_light_wattage(
            room, len(light_positions)
        )
        
        # Step 2: Calculate loads
        outlet_load = len(outlet_positions) * 180  # 180W per outlet
        lighting_load = len(light_positions) * light_wattage
        special_load = self.load_calculator.calculate_special_loads(
            room.special_loads or []
        )
        total_load = outlet_load + lighting_load + special_load
        
        # Step 3: Size wires (for outlet circuit)
        wire_result = self.wire_sizer.select_wire_size(outlet_load)
        wire_size = wire_result["wire_size_sqmm"]
        
        # Step 4: Select breaker
        breaker_result = self.breaker_selector.select_breaker(
            outlet_load, wire_result["max_ampacity"]
        )
        breaker_size = breaker_result["breaker_size"]
        
        # Step 5: Size conduit
        conduit_result = self.conduit_sizer.select_for_circuit(wire_size)
        conduit_size = conduit_result["conduit_size_mm"]
        
        # Step 6: Build result
        room_design = self.result_builder.build_from_template_output(
            room=room,
            outlet_positions=outlet_positions,
            light_positions=light_positions,
            outlet_type=outlet_type,
            light_type=light_type,
            light_wattage=light_wattage,
            wire_size=wire_size,
            conduit_size=conduit_size,
            breaker_size=breaker_size,
        )
        
        return room_design
    
    def design_project(self, project: ProjectInput) -> ProjectDesign:
        """
        Design a complete project.
        
        Args:
            project: Project input specification
            
        Returns:
            Complete project design
        """
        # Design each room
        room_designs: List[RoomDesign] = []
        total_connected = 0.0
        all_circuits = []
        
        for room in project.rooms:
            room_design = self.design_room(room)
            room_designs.append(room_design)
            total_connected += room_design.total_load_watts
            all_circuits.extend(room_design.circuits)
        
        # Calculate total demand with diversity factors
        room_loads = [
            (
                sum(c.total_load for c in r.circuits if c.circuit_type == "outlet"),
                sum(c.total_load for c in r.circuits if c.circuit_type == "lighting"),
                sum(c.total_load for c in r.circuits if c.circuit_type == "dedicated"),
            )
            for r in room_designs
        ]
        total_demand = self.load_calculator.calculate_total_demand(room_loads)
        
        # Select main breaker
        main_result = self.breaker_selector.select_main_breaker(
            total_demand, project.phases
        )
        main_breaker = main_result["main_breaker_size"]
        
        # Power flow analysis
        pf_results = self.pandapower_adapter.analyze_circuits(all_circuits)
        
        # Build initial project design (without compliance and AutoLISP)
        initial_design = ProjectDesign(
            project_id=project.project_id,
            project_name=project.project_name,
            rooms=room_designs,
            main_breaker_size=main_breaker,
            total_connected_load=total_connected,
            total_demand_load=total_demand,
            compliance=ComplianceResult(is_compliant=True),
            autolisp_script="",
            metadata={"power_flow": pf_results},
        )
        
        # Compliance check
        compliance = self.compliance_checker.check_project(initial_design)
        
        # Generate AutoLISP
        autolisp = self.autolisp_generator.generate_project(initial_design)
        
        # Build final design
        project_design = self.result_builder.build_project_design(
            project=project,
            rooms=room_designs,
            main_breaker_size=main_breaker,
            total_connected_load=total_connected,
            total_demand_load=total_demand,
            compliance=compliance,
            autolisp_script=autolisp,
            metadata={"power_flow": pf_results},
        )
        
        return project_design
    
    def quick_design(
        self,
        room_type: str,
        width: float,
        length: float,
        room_id: str = "room-001"
    ) -> RoomDesign:
        """
        Quick design for a single room with minimal input.
        
        Args:
            room_type: Type of room (bedroom, living_room, etc.)
            width: Room width in meters
            length: Room length in meters
            room_id: Optional room ID
            
        Returns:
            Room design
        """
        from models.contracts import RoomType
        
        room = RoomInput(
            room_id=room_id,
            room_type=RoomType(room_type),
            width=width,
            length=length,
        )
        
        return self.design_room(room)


def create_demo_project() -> ProjectInput:
    """
    Create demo project for testing.
    Uses the 4x3m bedroom from baseline.
    
    Returns:
        Demo project input
    """
    from models.contracts import RoomType
    from models.baseline import DEMO_BEDROOM
    
    demo_room = RoomInput(
        room_id=DEMO_BEDROOM["room_id"],
        room_type=RoomType(DEMO_BEDROOM["room_type"]),
        width=DEMO_BEDROOM["width"],
        length=DEMO_BEDROOM["length"],
        height=DEMO_BEDROOM["height"],
    )
    
    return ProjectInput(
        project_id="demo-project-001",
        project_name="Demo Bedroom Project",
        rooms=[demo_room],
    )


def run_demo() -> ProjectDesign:
    """
    Run demo design pipeline.
    
    Returns:
        Demo project design
    """
    project = create_demo_project()
    pipeline = DesignPipeline()
    return pipeline.design_project(project)
