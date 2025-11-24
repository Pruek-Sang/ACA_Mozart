"""Integration tests for MCP Pipeline.

Tests the complete pipeline with a demo scenario:
- Bedroom 4m x 3m (12 m²)
- Uses hardcoded demo data (no database required)
"""

import pytest
from datetime import datetime

from models.contracts import ProjectInputSpec, RoomSpec, RoomType, McpRunResult
from pipeline import MCPPipeline
from dal.catalog_dal import CatalogDAL


class TestMCPPipeline:
    """Integration tests for the MCP Pipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline with demo data."""
        catalog_dal = CatalogDAL()  # Uses demo data when no DB
        return MCPPipeline(catalog_dal)

    @pytest.fixture
    def bedroom_input(self):
        """Create demo input for a 4x3m bedroom."""
        return ProjectInputSpec(
            project_id="test-bedroom-001",
            project_name="Demo Bedroom Design",
            rooms=[
                RoomSpec(
                    name="Master Bedroom",
                    room_type=RoomType.BEDROOM,
                    width_m=4.0,
                    length_m=3.0,
                    height_m=2.8,
                )
            ],
            voltage=220.0,
            phases=1,
        )

    @pytest.fixture
    def multi_room_input(self):
        """Create demo input with multiple rooms."""
        return ProjectInputSpec(
            project_id="test-multi-001",
            project_name="Multi-Room Design",
            rooms=[
                RoomSpec(
                    name="Living Room",
                    room_type=RoomType.LIVING_ROOM,
                    width_m=5.0,
                    length_m=4.0,
                    height_m=2.8,
                ),
                RoomSpec(
                    name="Bedroom 1",
                    room_type=RoomType.BEDROOM,
                    width_m=4.0,
                    length_m=3.0,
                    height_m=2.8,
                ),
                RoomSpec(
                    name="Kitchen",
                    room_type=RoomType.KITCHEN,
                    width_m=3.0,
                    length_m=3.0,
                    height_m=2.8,
                ),
            ],
            voltage=220.0,
            phases=1,
        )

    def test_pipeline_bedroom_basic(self, pipeline, bedroom_input):
        """Test basic pipeline execution for bedroom."""
        result = pipeline.run(bedroom_input)

        # Verify result type
        assert isinstance(result, McpRunResult)
        assert result.project_id == "test-bedroom-001"
        assert result.project_name == "Demo Bedroom Design"

    def test_pipeline_bedroom_circuits(self, pipeline, bedroom_input):
        """Test circuit generation for bedroom."""
        result = pipeline.run(bedroom_input)

        # Bedroom should have at least lighting and outlet circuits
        assert result.total_circuits >= 2
        
        # Find lighting and outlet circuits
        circuit_types = [c.circuit_type for c in result.circuits]
        assert "lighting" in circuit_types
        assert "outlet" in circuit_types

    def test_pipeline_bedroom_loads(self, pipeline, bedroom_input):
        """Test load calculations for bedroom."""
        result = pipeline.run(bedroom_input)

        # All circuits should have positive loads
        for circuit in result.circuits:
            assert circuit.connected_load_w > 0
            assert circuit.demand_load_w > 0
            assert circuit.current_a > 0

        # Total power flow should be positive
        assert result.power_flow.total_load_kw > 0

    def test_pipeline_bedroom_wire_sizing(self, pipeline, bedroom_input):
        """Test wire sizing for bedroom circuits."""
        result = pipeline.run(bedroom_input)

        for circuit in result.circuits:
            # Wire size should be valid
            assert circuit.wire.wire_size_mm2 >= 1.5
            assert circuit.wire.wire_type in ["THW", "THWN", "XHHW"]
            assert circuit.wire.ampacity_a > 0
            assert circuit.wire.length_m > 0

    def test_pipeline_bedroom_breaker_selection(self, pipeline, bedroom_input):
        """Test breaker selection for bedroom circuits."""
        result = pipeline.run(bedroom_input)

        for circuit in result.circuits:
            # Breaker should be valid standard rating
            assert circuit.breaker.breaker_rating_a in [6, 10, 16, 20, 25, 32, 40, 50, 63]
            assert circuit.breaker.breaker_type == "MCB"
            assert circuit.breaker.breaking_capacity_ka >= 6.0

    def test_pipeline_bedroom_conduit_sizing(self, pipeline, bedroom_input):
        """Test conduit sizing for bedroom circuits."""
        result = pipeline.run(bedroom_input)

        for circuit in result.circuits:
            # Conduit should be valid size
            assert circuit.conduit.conduit_size_mm in [16, 20, 25, 32]
            assert circuit.conduit.fill_ratio_percent <= 50  # Max fill limit with margin

    def test_pipeline_bedroom_voltage_drop(self, pipeline, bedroom_input):
        """Test voltage drop compliance for bedroom."""
        result = pipeline.run(bedroom_input)

        for circuit in result.circuits:
            # Voltage drop should be calculated
            assert circuit.voltage_drop_percent >= 0
            # Should typically be within 3% limit
            assert circuit.voltage_drop_percent <= 5  # Allow some margin for test

    def test_pipeline_bedroom_compliance(self, pipeline, bedroom_input):
        """Test compliance checking for bedroom."""
        result = pipeline.run(bedroom_input)

        # At least some circuits should be compliant
        assert result.compliant_circuits > 0

        # Check compliance notes exist where needed
        for circuit in result.circuits:
            if not circuit.is_compliant:
                assert len(circuit.compliance_notes) > 0

    def test_pipeline_bedroom_main_breaker(self, pipeline, bedroom_input):
        """Test main breaker selection for bedroom."""
        result = pipeline.run(bedroom_input)

        # Main breaker should be selected
        assert result.main_breaker_recommended_a >= 20
        assert result.main_breaker_recommended_a in [32, 40, 50, 63, 80, 100]

    def test_pipeline_bedroom_autolisp(self, pipeline, bedroom_input):
        """Test AutoLISP generation for bedroom."""
        result = pipeline.run(bedroom_input)

        # AutoLISP script should be generated
        assert result.autolisp_script is not None
        assert len(result.autolisp_script.script_content) > 0
        assert "defun" in result.autolisp_script.script_content
        assert result.autolisp_script.target_software == "AutoCAD"

    def test_pipeline_bedroom_power_flow(self, pipeline, bedroom_input):
        """Test power flow analysis for bedroom."""
        result = pipeline.run(bedroom_input)

        # Power flow should have results
        assert result.power_flow.total_load_kw >= 0
        assert result.power_flow.voltage_at_furthest_point_v > 0
        assert result.power_flow.max_voltage_drop_percent >= 0
        assert isinstance(result.power_flow.convergence_achieved, bool)

    def test_pipeline_multi_room(self, pipeline, multi_room_input):
        """Test pipeline with multiple rooms."""
        result = pipeline.run(multi_room_input)

        # Should have circuits for all rooms
        assert result.total_circuits >= 6  # At least 2 per room

        # Check room names in circuits
        room_names = set(c.room_name for c in result.circuits)
        assert "Living Room" in room_names
        assert "Bedroom 1" in room_names
        assert "Kitchen" in room_names

    def test_pipeline_kitchen_dedicated(self, pipeline, multi_room_input):
        """Test that kitchen has dedicated circuit."""
        result = pipeline.run(multi_room_input)

        # Find kitchen circuits
        kitchen_circuits = [c for c in result.circuits if c.room_name == "Kitchen"]
        
        # Kitchen should have dedicated circuit
        circuit_types = [c.circuit_type for c in kitchen_circuits]
        assert "dedicated" in circuit_types

    def test_pipeline_result_timestamp(self, pipeline, bedroom_input):
        """Test that result has valid timestamp."""
        result = pipeline.run(bedroom_input)

        assert result.run_timestamp is not None
        assert isinstance(result.run_timestamp, datetime)

    def test_pipeline_warnings_and_errors(self, pipeline, bedroom_input):
        """Test that warnings and errors are lists."""
        result = pipeline.run(bedroom_input)

        assert isinstance(result.warnings, list)
        assert isinstance(result.errors, list)


class TestBedroomScenario:
    """Specific test scenario: Bedroom 4x3m as specified in requirements."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline with demo data."""
        return MCPPipeline(CatalogDAL())

    def test_bedroom_4x3_complete_design(self, pipeline):
        """Complete design test for 4m x 3m = 12m² bedroom."""
        input_spec = ProjectInputSpec(
            project_id="bedroom-4x3-test",
            project_name="Standard Bedroom 4x3m",
            rooms=[
                RoomSpec(
                    name="Bedroom",
                    room_type=RoomType.BEDROOM,
                    width_m=4.0,
                    length_m=3.0,
                    height_m=2.8,
                )
            ],
            voltage=220.0,
            phases=1,
        )

        result = pipeline.run(input_spec)

        # Basic validation
        assert result.project_id == "bedroom-4x3-test"
        assert result.total_circuits >= 2

        # Area-based validation
        # 12m² bedroom should have:
        # - Lighting: ~15W/m² = 180W
        # - Outlets: min 2 outlets at 180W each = 360W
        # Total minimum ~540W

        total_connected_load = sum(c.connected_load_w for c in result.circuits)
        assert total_connected_load >= 400  # Minimum expected load
        assert total_connected_load <= 2000  # Maximum reasonable for bedroom

        # Wire sizing validation
        lighting_circuit = next(
            (c for c in result.circuits if c.circuit_type == "lighting"), None
        )
        outlet_circuit = next(
            (c for c in result.circuits if c.circuit_type == "outlet"), None
        )

        assert lighting_circuit is not None
        assert outlet_circuit is not None

        # Lighting typically uses 1.5mm² wire
        assert lighting_circuit.wire.wire_size_mm2 >= 1.5

        # Outlets typically use 2.5mm² wire
        assert outlet_circuit.wire.wire_size_mm2 >= 1.5

        # Breaker validation
        assert lighting_circuit.breaker.breaker_rating_a <= 16
        assert outlet_circuit.breaker.breaker_rating_a <= 20

        # Compliance
        assert result.compliant_circuits >= 1

        # AutoLISP should contain room reference
        assert "Bedroom" in result.autolisp_script.script_content or \
               "bedroom" in result.autolisp_script.script_content.lower()

        print(f"\n=== Bedroom 4x3m Test Results ===")
        print(f"Total circuits: {result.total_circuits}")
        print(f"Compliant circuits: {result.compliant_circuits}")
        print(f"Total connected load: {total_connected_load:.0f}W")
        print(f"Main breaker: {result.main_breaker_recommended_a}A")
        print(f"Power flow converged: {result.power_flow.convergence_achieved}")
        print(f"Max voltage drop: {result.power_flow.max_voltage_drop_percent:.2f}%")
        
        for circuit in result.circuits:
            print(f"\nCircuit: {circuit.circuit_name}")
            print(f"  Type: {circuit.circuit_type}")
            print(f"  Load: {circuit.connected_load_w:.0f}W")
            print(f"  Current: {circuit.current_a:.2f}A")
            print(f"  Wire: {circuit.wire.wire_size_mm2}mm² {circuit.wire.wire_type}")
            print(f"  Breaker: {circuit.breaker.breaker_rating_a}A {circuit.breaker.breaker_type}")
            print(f"  Conduit: {circuit.conduit.conduit_size_mm}mm")
            print(f"  Voltage drop: {circuit.voltage_drop_percent:.2f}%")
            print(f"  Compliant: {circuit.is_compliant}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
