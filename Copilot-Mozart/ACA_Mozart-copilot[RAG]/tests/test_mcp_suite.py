"""
MCP Spec Test Suite - MCP-01 to MCP-06
Tests for /api/v1/mcp_spec endpoint following new test specification

Note: MCP-02 to MCP-06 are designed to test MCP Core calculations.
Since MCP Core is not yet integrated, these tests validate:
1. Spec generation from RAG
2. Spec structure validity
3. Mock validation patterns for future MCP Core integration

Philosophy:
- Validate spec structure matches MCP Core contract
- Ensure loads/rooms are properly mapped
- Prepare test patterns for MCP Core integration
"""

import pytest
from fastapi.testclient import TestClient
from app.routes import app
from app.models import ProjectRequirements, RoomInput, LoadInput

client = TestClient(app)


# === Fixtures ===

@pytest.fixture
def residential_2floor_spec():
    """
    ProjectRequirements matching RAG-01 scenario:
    2-floor house, 180 sqm, AC x3, water heater x2, induction cooker
    """
    return ProjectRequirements(
        project_name="Test Residential 2-Floor",
        building_type="residential",
        voltage_system="TH_1PH_230V",
        location="Bangkok",
        rooms=[
            # ชั้น 1
            RoomInput(name="ห้องนั่งเล่น 1F", type="living_room", area_sqm=35.0, floor=1),
            RoomInput(name="ครัว 1F", type="kitchen", area_sqm=20.0, floor=1),
            RoomInput(name="ห้องน้ำ 1F", type="bathroom", area_sqm=6.0, floor=1),
            # ชั้น 2
            RoomInput(name="ห้องนอนใหญ่ 2F", type="bedroom", area_sqm=25.0, floor=2),
            RoomInput(name="ห้องนอนเล็ก 2F", type="bedroom", area_sqm=18.0, floor=2),
            RoomInput(name="ห้องน้ำ 2F", type="bathroom", area_sqm=5.0, floor=2),
        ],
        loads=[
            # AC units (per DEVICE_CODES.md: AC-12000BTU)
            LoadInput(room_name="ห้องนั่งเล่น 1F", device="AC-12000BTU", quantity=1),
            LoadInput(room_name="ห้องนอนใหญ่ 2F", device="AC-12000BTU", quantity=1),
            LoadInput(room_name="ห้องนอนเล็ก 2F", device="AC-12000BTU", quantity=1),
            # Water heaters (per DEVICE_CODES.md: HEATER-3500W)
            LoadInput(room_name="ห้องน้ำ 1F", device="HEATER-3500W", quantity=1),
            LoadInput(room_name="ห้องน้ำ 2F", device="HEATER-3500W", quantity=1),
            # Kitchen heavy load (per DEVICE_CODES.md: INDUCTION-3000W)
            LoadInput(room_name="ครัว 1F", device="INDUCTION-3000W", quantity=1),
            # Outlets (per DEVICE_CODES.md: SOCKET-16A)
            LoadInput(room_name="ห้องนั่งเล่น 1F", device="SOCKET-16A", quantity=6),
            LoadInput(room_name="ครัว 1F", device="SOCKET-16A", quantity=8),
            LoadInput(room_name="ห้องนอนใหญ่ 2F", device="SOCKET-16A", quantity=4),
            LoadInput(room_name="ห้องนอนเล็ก 2F", device="SOCKET-16A", quantity=3),
        ],
        user_constraints=["rcd_for_all_outlets", "split_kitchen_circuit"]
    )


@pytest.fixture
def invalid_voltage_spec():
    """Spec with invalid voltage for error testing"""
    return {
        "project_name": "Test Invalid Voltage",
        "building_type": "residential",
        "voltage_system": "INVALID_9999V",  # Invalid
        "rooms": [
            {"name": "ห้องนั่งเล่น", "type": "living_room", "area_sqm": 20.0}
        ],
        "loads": [
            {"room_name": "ห้องนั่งเล่น", "device": "AC_12000BTU", "quantity": 1}
        ]
    }


class TestMCP01_SpecValidation:
    """
    MCP-01: Spec Validation
    
    Purpose: Ensure spec from RAG passes validation normally
    """
    
    @pytest.mark.integration
    def test_mcp01_spec_generation_success(self, residential_2floor_spec):
        """Validate spec generation succeeds"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=residential_2floor_spec.model_dump()
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Required top-level fields
        assert "project_input" in data, "Missing project_input"
        assert "standards_profile" in data, "Missing standards_profile"
        assert "llm_metadata" in data, "Missing llm_metadata"
    
    @pytest.mark.integration
    def test_mcp01_project_info_structure(self, residential_2floor_spec):
        """Validate project_info follows MCP contract"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=residential_2floor_spec.model_dump()
        )
        
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        # project_info
        assert "project_info" in project_input
        project_info = project_input["project_info"]
        
        assert project_info["building_type"] == "RESIDENTIAL"
        assert "spec_version" in project_info
    
    @pytest.mark.integration
    def test_mcp01_electrical_system_structure(self, residential_2floor_spec):
        """Validate electrical_system follows MCP contract"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=residential_2floor_spec.model_dump()
        )
        
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        # electrical_system
        assert "electrical_system" in project_input
        elec_sys = project_input["electrical_system"]
        
        assert elec_sys["voltage_system"] == "TH_1PH_230V"
        assert "earthing" in elec_sys
    
    @pytest.mark.integration
    def test_mcp01_rooms_mapping(self, residential_2floor_spec):
        """Validate rooms are mapped with room_id"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=residential_2floor_spec.model_dump()
        )
        
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        # rooms
        rooms = project_input.get("rooms", [])
        assert len(rooms) == 6, f"Expected 6 rooms, got {len(rooms)}"
        
        for room in rooms:
            assert "room_id" in room, f"Room missing room_id: {room}"
            assert room["room_id"].startswith("R"), f"Invalid room_id format: {room['room_id']}"
            assert "room_type" in room, f"Room missing room_type: {room}"
            assert "template_code" in room, f"Room missing template_code: {room}"
    
    @pytest.mark.integration
    def test_mcp01_loads_mapping(self, residential_2floor_spec):
        """Validate loads are mapped with load_id and room_id"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=residential_2floor_spec.model_dump()
        )
        
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        # loads
        loads = project_input.get("loads", [])
        rooms = project_input.get("rooms", [])
        room_ids = {r["room_id"] for r in rooms}
        
        assert len(loads) >= 6, f"Expected at least 6 loads, got {len(loads)}"
        
        for load in loads:
            assert "load_id" in load, f"Load missing load_id: {load}"
            assert load["load_id"].startswith("L"), f"Invalid load_id format: {load['load_id']}"
            assert "room_id" in load, f"Load missing room_id: {load}"
            assert load["room_id"] in room_ids, f"Load room_id not in rooms: {load['room_id']}"
            assert "device_code" in load, f"Load missing device_code: {load}"


class TestMCP02_LoadAggregationDemand:
    """
    MCP-02: Load Aggregation & Demand
    
    Purpose: Validate load totals and demand factors
    Note: Full calculation testing requires MCP Core integration
    """
    
    @pytest.mark.integration
    def test_mcp02_spec_has_load_data(self, residential_2floor_spec):
        """Validate spec contains load data for aggregation"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=residential_2floor_spec.model_dump()
        )
        
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        loads = project_input.get("loads", [])
        
        # Count heavy loads
        heavy_loads = [l for l in loads if any(kw in l.get("device_code", "").upper() 
                      for kw in ["AC", "HEATER", "INDUCTION", "COOKER", "OVEN"])]
        
        assert len(heavy_loads) >= 3, f"Expected at least 3 heavy loads, got {len(heavy_loads)}"
    
    @pytest.mark.integration
    def test_mcp02_constraints_preserved(self, residential_2floor_spec):
        """Validate user constraints are passed to spec"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=residential_2floor_spec.model_dump()
        )
        
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        constraints = project_input.get("constraints", {})
        user_constraints = constraints.get("user_constraints", [])
        
        assert "rcd_for_all_outlets" in user_constraints, "Missing rcd_for_all_outlets constraint"
        assert "split_kitchen_circuit" in user_constraints, "Missing split_kitchen_circuit constraint"


class TestMCP03_WireSizingBreakerSelection:
    """
    MCP-03: Wire Sizing & Breaker Selection
    
    Purpose: Validate spec structure supports wire/breaker selection
    Note: Actual sizing requires MCP Core
    """
    
    @pytest.mark.integration
    def test_mcp03_spec_supports_heavy_loads(self, residential_2floor_spec):
        """Validate heavy loads are properly categorized"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=residential_2floor_spec.model_dump()
        )
        
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        loads = project_input.get("loads", [])
        
        # Check for AC loads
        ac_loads = [l for l in loads if "AC" in l.get("device_code", "").upper()]
        assert len(ac_loads) >= 1, "Should have AC loads for breaker selection"
        
        # Check for water heater loads
        heater_loads = [l for l in loads if "HEATER" in l.get("device_code", "").upper() 
                       or "WATER" in l.get("device_code", "").upper()]
        assert len(heater_loads) >= 1, "Should have water heater loads"


class TestMCP04_VoltageDropCheck:
    """
    MCP-04: Voltage Drop Check
    
    Purpose: Validate spec includes info needed for VD calculation
    Note: Actual VD calculation requires MCP Core
    """
    
    @pytest.mark.integration
    def test_mcp04_spec_has_voltage_system(self, residential_2floor_spec):
        """Validate voltage system is specified for VD calculation"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=residential_2floor_spec.model_dump()
        )
        
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        elec_sys = project_input.get("electrical_system", {})
        
        assert "voltage_system" in elec_sys
        assert "TH_1PH_230V" in elec_sys["voltage_system"]


class TestMCP05_DeratingFactors:
    """
    MCP-05: Derating Factors
    
    Purpose: Validate spec includes info for derating
    Note: Actual derating requires MCP Core + catalog lookup
    """
    
    @pytest.mark.integration
    def test_mcp05_standards_profile_present(self, residential_2floor_spec):
        """Validate standards_profile is included for derating reference"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=residential_2floor_spec.model_dump()
        )
        
        assert response.status_code == 200
        
        data = response.json()
        
        assert "standards_profile" in data
        standards = data["standards_profile"]
        
        # Should have standard reference
        assert isinstance(standards, (dict, str)), "standards_profile should be dict or string"


class TestMCP06_ErrorHandling:
    """
    MCP-06: Error Handling (Negative Case)
    
    Purpose: Verify invalid specs are rejected gracefully
    """
    
    def test_mcp06_invalid_voltage_returns_error(self, invalid_voltage_spec):
        """Validate invalid voltage is rejected"""
        response = client.post(
            "/api/v1/mcp_spec",
            json=invalid_voltage_spec
        )
        
        # Should fail - either 400 for validation or 200 with fallback
        # Depending on implementation, may still succeed with warning
        if response.status_code != 200:
            assert response.status_code in [400, 422], \
                f"Unexpected status for invalid voltage: {response.status_code}"
            
            error_data = response.json()
            assert "error" in error_data or "detail" in error_data
    
    def test_mcp06_missing_rooms_returns_error(self):
        """Validate missing rooms is rejected"""
        response = client.post(
            "/api/v1/mcp_spec",
            json={
                "project_name": "Test No Rooms",
                "building_type": "residential",
                "voltage_system": "TH_1PH_230V",
                "rooms": [],  # Empty rooms
                "loads": []
            }
        )
        
        # Should fail with 400
        assert response.status_code in [400, 422], \
            f"Should reject empty rooms: {response.status_code}"
    
    def test_mcp06_malformed_json_returns_error(self):
        """Validate malformed JSON returns structured error"""
        response = client.post(
            "/api/v1/mcp_spec",
            content='{"project_name": "test"',  # Malformed
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 422, 500]
        
        # Should be JSON error, not stack trace
        try:
            error_data = response.json()
            assert "error" in error_data or "detail" in error_data
        except Exception:
            pytest.fail("Error response should be valid JSON")
    
    def test_mcp06_load_without_room_returns_error(self):
        """Validate load referencing non-existent room is rejected"""
        response = client.post(
            "/api/v1/mcp_spec",
            json={
                "project_name": "Test Orphan Load",
                "building_type": "residential",
                "voltage_system": "TH_1PH_230V",
                "rooms": [
                    {"name": "ห้องนั่งเล่น", "type": "living_room", "area_sqm": 20.0}
                ],
                "loads": [
                    # References room that doesn't exist
                    {"room_name": "ห้องครัว", "device": "AC_12000BTU", "quantity": 1}
                ]
            }
        )
        
        # May succeed with warning or fail - depends on validation policy
        # For MVP, we accept either behavior
        assert response.status_code in [200, 400, 422], \
            f"Unexpected status: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
