"""Tests for MCP Pipeline."""

from unittest.mock import MagicMock, patch

import pytest

from src.dal.catalog_dal import (
    DEFAULT_BREAKER_SPECS,
    DEFAULT_CABLE_SPECS,
    DEFAULT_CONDUIT_SPECS,
    DEFAULT_ROOM_TEMPLATES,
    CatalogDAL,
)
from src.models.contracts import ProjectInputSpec, RoomInputSpec
from src.orchestration.pipeline import MCPPipeline


class MockCatalogDAL(CatalogDAL):
    """Mock DAL that returns default values without database access."""

    def __init__(self):
        """Initialize with mock client."""
        super().__init__(client=MagicMock())
        self._room_templates_cache = DEFAULT_ROOM_TEMPLATES
        self._cable_specs_cache = DEFAULT_CABLE_SPECS
        self._breaker_specs_cache = DEFAULT_BREAKER_SPECS
        self._conduit_specs_cache = DEFAULT_CONDUIT_SPECS


@pytest.fixture
def mock_dal():
    """Fixture providing mock DAL."""
    return MockCatalogDAL()


@pytest.fixture
def sample_project_input():
    """Fixture providing sample project input."""
    return ProjectInputSpec(
        project_id="TEST-001",
        project_name="Test Residential Project",
        voltage_system="230V",
        phase_system="1-phase",
        power_factor=0.85,
        ambient_temp_c=40.0,
        rooms=[
            RoomInputSpec(
                room_id="R001",
                room_type="bedroom",
                area_sqm=15.0,
                floor_level=1,
            ),
            RoomInputSpec(
                room_id="R002",
                room_type="kitchen",
                area_sqm=12.0,
                floor_level=1,
            ),
            RoomInputSpec(
                room_id="R003",
                room_type="living_room",
                area_sqm=25.0,
                floor_level=1,
            ),
        ],
    )


class TestMCPPipeline:
    """Test cases for MCP Pipeline."""

    def test_pipeline_initialization(self, mock_dal):
        """Test pipeline initializes correctly."""
        pipeline = MCPPipeline(dal=mock_dal)

        assert pipeline.template_resolver is not None
        assert pipeline.load_calculator is not None
        assert pipeline.wire_sizer is not None
        assert pipeline.pandapower_adapter is not None
        assert pipeline.breaker_selector is not None
        assert pipeline.conduit_sizer is not None
        assert pipeline.compliance_checker is not None
        assert pipeline.autolisp_generator is not None
        assert pipeline.result_builder is not None

    def test_pipeline_run_basic(self, mock_dal, sample_project_input):
        """Test basic pipeline run produces valid output."""
        pipeline = MCPPipeline(dal=mock_dal)
        result = pipeline.run(sample_project_input)

        # Check result structure
        assert result.project_id == "TEST-001"
        assert result.project_name == "Test Residential Project"
        assert len(result.rooms) == 3

        # Check loads are calculated
        assert result.total_connected_load_kw > 0
        assert result.total_demand_load_kw > 0

        # Check main breaker is selected
        assert result.main_breaker_rating_a > 0

        # Check AutoLISP script is generated
        assert result.autolisp_script != ""
        assert "MCP Core v2" in result.autolisp_script

    def test_pipeline_bedroom_circuits(self, mock_dal):
        """Test bedroom generates correct circuits."""
        project_input = ProjectInputSpec(
            project_id="TEST-002",
            project_name="Bedroom Test",
            rooms=[
                RoomInputSpec(
                    room_id="BR001",
                    room_type="bedroom",
                    area_sqm=20.0,
                    floor_level=2,
                ),
            ],
        )

        pipeline = MCPPipeline(dal=mock_dal)
        result = pipeline.run(project_input)

        assert len(result.rooms) == 1
        bedroom = result.rooms[0]

        # Bedroom should have lighting, outlet, and AC circuits
        circuit_types = [c.circuit_type for c in bedroom.circuits]
        assert "lighting" in circuit_types
        assert "outlet" in circuit_types
        assert "ac" in circuit_types

    def test_pipeline_kitchen_circuits(self, mock_dal):
        """Test kitchen generates correct circuits."""
        project_input = ProjectInputSpec(
            project_id="TEST-003",
            project_name="Kitchen Test",
            rooms=[
                RoomInputSpec(
                    room_id="KT001",
                    room_type="kitchen",
                    area_sqm=15.0,
                    floor_level=1,
                ),
            ],
        )

        pipeline = MCPPipeline(dal=mock_dal)
        result = pipeline.run(project_input)

        kitchen = result.rooms[0]

        # Kitchen should have special outlet
        circuit_types = [c.circuit_type for c in kitchen.circuits]
        assert "special_outlet" in circuit_types

    def test_pipeline_circuit_sizing(self, mock_dal, sample_project_input):
        """Test circuits have proper sizing."""
        pipeline = MCPPipeline(dal=mock_dal)
        result = pipeline.run(sample_project_input)

        for room in result.rooms:
            for circuit in room.circuits:
                # All circuits should have sizing
                assert circuit.wire_size_sqmm > 0
                assert circuit.breaker_rating_a > 0
                assert circuit.conduit_size_mm > 0

                # Breaker should be >= design current
                assert circuit.breaker_rating_a >= circuit.design_current_a

    def test_pipeline_voltage_drop_calculated(self, mock_dal, sample_project_input):
        """Test voltage drop is calculated for circuits."""
        pipeline = MCPPipeline(dal=mock_dal)
        result = pipeline.run(sample_project_input)

        for room in result.rooms:
            for circuit in room.circuits:
                # Voltage drop should be calculated (may be 0 for very light loads)
                assert circuit.voltage_drop_pct >= 0
                # Should be reasonable (< 10% even for worst case)
                assert circuit.voltage_drop_pct < 10

    def test_pipeline_compliance_check(self, mock_dal, sample_project_input):
        """Test compliance checking is performed."""
        pipeline = MCPPipeline(dal=mock_dal)
        result = pipeline.run(sample_project_input)

        # Should have compliance status
        assert isinstance(result.overall_compliant, bool)

        # Each circuit should have compliance status
        for room in result.rooms:
            for circuit in room.circuits:
                assert isinstance(circuit.compliant, bool)

    def test_pipeline_custom_loads(self, mock_dal):
        """Test custom loads are processed."""
        project_input = ProjectInputSpec(
            project_id="TEST-004",
            project_name="Custom Load Test",
            rooms=[
                RoomInputSpec(
                    room_id="R001",
                    room_type="office",
                    area_sqm=20.0,
                    floor_level=1,
                    custom_loads=[
                        {
                            "type": "server_rack",
                            "load_w": 2000.0,
                            "demand_factor": 1.0,
                            "cable_length_m": 10.0,
                        }
                    ],
                ),
            ],
        )

        pipeline = MCPPipeline(dal=mock_dal)
        result = pipeline.run(project_input)

        office = result.rooms[0]
        circuit_types = [c.circuit_type for c in office.circuits]

        # Should have custom load circuit
        assert "server_rack" in circuit_types

    def test_pipeline_three_phase(self, mock_dal):
        """Test 3-phase system calculations."""
        project_input = ProjectInputSpec(
            project_id="TEST-005",
            project_name="3-Phase Test",
            voltage_system="400V",
            phase_system="3-phase",
            rooms=[
                RoomInputSpec(
                    room_id="R001",
                    room_type="office",
                    area_sqm=50.0,
                    floor_level=1,
                ),
            ],
        )

        pipeline = MCPPipeline(dal=mock_dal)
        result = pipeline.run(project_input)

        # Should complete without errors
        assert result.project_id == "TEST-005"
        assert result.total_demand_load_kw > 0


class TestLoadCalculator:
    """Test cases for load calculator."""

    def test_load_calculation(self, mock_dal):
        """Test load calculations are correct."""
        from src.core.load_calculator import LoadCalculator
        from src.core.template_resolver import TemplateResolver

        resolver = TemplateResolver(dal=mock_dal)
        calculator = LoadCalculator()

        project_input = ProjectInputSpec(
            project_id="CALC-001",
            project_name="Calc Test",
            rooms=[
                RoomInputSpec(
                    room_id="R001",
                    room_type="bedroom",
                    area_sqm=10.0,
                    floor_level=1,
                ),
            ],
        )

        context = resolver.resolve(project_input)
        context = calculator.calculate(context)

        # Check that totals are accumulated
        assert context.total_connected_load_w > 0
        assert context.total_demand_load_w > 0
        assert context.total_demand_load_w <= context.total_connected_load_w

        # Check room totals
        room = context.rooms[0]
        assert room.total_connected_load_w > 0

        # Check circuit calculations
        for circuit in room.circuits:
            assert circuit.demand_load_w == circuit.connected_load_w * circuit.demand_factor
            assert circuit.design_current_a > 0


class TestWireSizer:
    """Test cases for wire sizer."""

    def test_wire_selection(self, mock_dal):
        """Test wire selection meets requirements."""
        from src.core.wire_sizer import WireSizer

        sizer = WireSizer(dal=mock_dal)

        # Test for 10A circuit
        size, spec = sizer.select_wire_size(
            design_current_a=10.0,
            cable_length_m=20.0,
            voltage_v=230.0,
            ambient_temp=40.0,
        )

        # Wire should have adequate ampacity (using safety factor from WireSizer)
        assert spec.ampacity_40c >= 10.0 * WireSizer.AMPACITY_SAFETY_FACTOR


class TestBreakerSelector:
    """Test cases for breaker selector."""

    def test_breaker_selection(self, mock_dal):
        """Test breaker selection meets requirements."""
        from src.core.breaker_selector import BreakerSelector

        selector = BreakerSelector(dal=mock_dal)

        # Test for 15A design current
        breaker = selector.select_breaker(design_current_a=15.0)

        # Breaker rating should be >= design current
        assert breaker.rating_a >= 15.0


class TestComplianceChecker:
    """Test cases for compliance checker."""

    def test_compliant_circuit(self):
        """Test compliance check for compliant circuit."""
        from src.core.compliance_checker import ComplianceChecker

        checker = ComplianceChecker()

        compliant, notes = checker.check_circuit_compliance(
            voltage_drop_pct=2.5,  # Below 3% limit
            breaker_rating_a=16.0,
            design_current_a=10.0,
            wire_size_sqmm=2.5,
        )

        assert compliant is True

    def test_non_compliant_voltage_drop(self):
        """Test compliance check for excessive voltage drop."""
        from src.core.compliance_checker import ComplianceChecker

        checker = ComplianceChecker()

        compliant, notes = checker.check_circuit_compliance(
            voltage_drop_pct=4.5,  # Above 3% limit
            breaker_rating_a=16.0,
            design_current_a=10.0,
            wire_size_sqmm=2.5,
        )

        assert compliant is False
        assert any("voltage drop" in note.lower() for note in notes)


class TestAutoLispGenerator:
    """Test cases for AutoLISP generator."""

    def test_script_generation(self, mock_dal, sample_project_input):
        """Test AutoLISP script is generated correctly."""
        pipeline = MCPPipeline(dal=mock_dal)
        result = pipeline.run(sample_project_input)

        script = result.autolisp_script

        # Check script contains expected elements
        assert "MCP Core v2" in script
        assert "Test Residential Project" in script
        assert "draw-circuit-tag" in script
        assert "LOAD SCHEDULE" in script
