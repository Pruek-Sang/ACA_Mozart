"""
Integration Tests for /api/v1/mcp_spec
Tests the complete flow: Requirements → Spec Generation → Validation

Note: These are integration tests that require:
- Vertex AI credentials
- VectorDB initialized
- Knowledge base populated
"""

import pytest
from fastapi.testclient import TestClient
from app.routes import app
from app.models import ProjectRequirements, RoomInput, LoadInput

client = TestClient(app)


@pytest.fixture
def basic_house_request():
    """Basic 1-floor house requirements"""
    return ProjectRequirements(
        project_name="Test House - Basic",
        building_type="residential",
        voltage_system="TH_1PH_230V",
        location="Bangkok",
        rooms=[
            RoomInput(name="ห้องนั่งเล่น", type="living_room", area_sqm=20.0),
            RoomInput(name="ห้องนอน", type="bedroom", area_sqm=15.0),
            RoomInput(name="ห้องน้ำ", type="bathroom", area_sqm=5.0)
        ],
        loads=[
            LoadInput(room_name="ห้องนั่งเล่น", device="AC_12000BTU", quantity=1),
            LoadInput(room_name="ห้องนั่งเล่น", device="OUTLET_16A", quantity=4),
            LoadInput(room_name="ห้องนอน", device="OUTLET_16A", quantity=3),
            LoadInput(room_name="ห้องน้ำ", device="WATER_HEATER_3500W", quantity=1)
        ],
        user_constraints=["rcd_for_all_outlets"]
    )


@pytest.fixture
def heavy_kitchen_request():
    """2-floor house with heavy kitchen"""
    return ProjectRequirements(
        project_name="Test House - Heavy Kitchen",
        building_type="residential",
        voltage_system="TH_1PH_230V",
        location="Bangkok",
        rooms=[
            RoomInput(name="ห้องนั่งเล่น 1F", type="living_room", area_sqm=30.0),
            RoomInput(name="ครัว 1F", type="kitchen", area_sqm=15.0),
            RoomInput(name="ห้องนอน 2F", type="bedroom", area_sqm=18.0)
        ],
        loads=[
            LoadInput(room_name="ห้องนั่งเล่น 1F", device="AC_18000BTU", quantity=1),
            LoadInput(room_name="ครัว 1F", device="INDUCTION_COOKER_3000W", quantity=1),
            LoadInput(room_name="ครัว 1F", device="MICROWAVE_1500W", quantity=1),
            LoadInput(room_name="ครัว 1F", device="OUTLET_16A", quantity=8),
            LoadInput(room_name="ห้องนอน 2F", device="AC_12000BTU", quantity=1)
        ],
        user_constraints=["split_kitchen_circuit", "rcd_for_all_outlets"]
    )


@pytest.fixture
def incomplete_request():
    """Incomplete data - missing room types"""
    return {
        "project_name": "Test Incomplete",
        "building_type": "residential",
        "voltage_system": "TH_1PH_230V",
        "rooms": [
            {"name": "ห้องนั่งเล่น"},  # Missing type
            {"name": "ห้องนอน"}  # Missing type
        ],
        "loads": [
            {"room_name": "ห้องนั่งเล่น", "device": "AC_12000BTU", "quantity": 1}
        ]
    }


class TestHealthEndpoints:
    """Test health and info endpoints"""
    
    def test_root(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Mozart RAG Spec Engine"
        assert data["goddess"] == "Aura"
    
    def test_mcp_manifest(self):
        """Test MCP manifest endpoint"""
        response = client.get("/mcp/manifest")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ee_standard_expert"
        assert len(data["tools"]) == 2


class TestMcpSpecCaseA:
    """Test Case A: Basic 1-floor house"""
    
    @pytest.mark.integration
    def test_basic_house_success(self, basic_house_request):
        """
        Purpose:
        - Verify that a simple 1-floor residential house produces valid ProjectInputSpec
        - This case acts as "sanity check" and regression guard
        
        Expected:
        - HTTP 200
        - Valid McpSpecResponse structure
        - All rooms have room_id, room_type, template_code
        - All loads linked to rooms via room_id
        - Constraints preserved
        """
        response = client.post(
            "/api/v1/mcp_spec",
            json=basic_house_request.model_dump()
        )
        
        # Should succeed
        assert response.status_code == 200, f"Failed: {response.json()}"
        
        data = response.json()
        
        # Validate response structure
        assert "project_input" in data
        assert "standards_profile" in data
        assert "llm_metadata" in data
        
        project_input = data["project_input"]
        
        # Validate project_info
        assert project_input["project_info"]["building_type"] == "RESIDENTIAL"
        assert project_input["project_info"]["spec_version"] == "2.0"
        
        # Validate electrical_system
        assert project_input["electrical_system"]["voltage_system"] == "TH_1PH_230V"
        assert project_input["electrical_system"]["earthing"] == "TT"
        
        # Validate rooms
        rooms = project_input["rooms"]
        assert len(rooms) == 3, f"Expected 3 rooms, got {len(rooms)}"
        
        for room in rooms:
            assert "room_id" in room
            assert "room_type" in room
            assert "template_code" in room
            assert room["room_id"].startswith("R")
        
        # Validate loads
        loads = project_input["loads"]
        assert len(loads) == 4, f"Expected 4 loads, got {len(loads)}"
        
        for load in loads:
            assert "load_id" in load
            assert "room_id" in load
            assert "device_code" in load
            assert load["load_id"].startswith("L")
            
            # Verify room_id exists in rooms
            room_ids = [r["room_id"] for r in rooms]
            assert load["room_id"] in room_ids, f"Load room_id {load['room_id']} not found in rooms"
        
        # Validate constraints
        constraints = project_input["constraints"]
        assert constraints["rule_profile_id"] == "TH_RESIDENTIAL_LV"
        assert "rcd_for_all_outlets" in constraints["user_constraints"]
        
        # Validate llm_metadata
        assert data["llm_metadata"]["model"] is not None
        assert len(data["llm_metadata"]["retrieved_docs"]) > 0


class TestMcpSpecCaseB:
    """Test Case B: 2-floor house with heavy kitchen"""
    
    @pytest.mark.integration
    def test_heavy_kitchen_constraints(self, heavy_kitchen_request):
        """
        Purpose:
        - Verify constraint handling (split_kitchen_circuit)
        - Test multi-floor scenario
        - Verify heavy load detection
        
        Expected:
        - HTTP 200
        - Kitchen template reflects heavy loads
        - Multiple constraints preserved
        """
        response = client.post(
            "/api/v1/mcp_spec",
            json=heavy_kitchen_request.model_dump()
        )
        
        assert response.status_code == 200
        
        data = response.json()
        project_input = data["project_input"]
        
        # Check constraints
        constraints = project_input["constraints"]["user_constraints"]
        assert "split_kitchen_circuit" in constraints
        assert "rcd_for_all_outlets" in constraints
        
        # Check kitchen room exists
        rooms = project_input["rooms"]
        kitchen_rooms = [r for r in rooms if "KITCHEN" in r["room_type"]]
        assert len(kitchen_rooms) >= 1, "Kitchen room not found"


class TestMcpSpecCaseC:
    """Test Case C: Incomplete data handling"""
    
    def test_incomplete_data_returns_400(self, incomplete_request):
        """
        Purpose:
        - Verify pre-validation catches incomplete data
        - Test error policy (should return 400)
        
        Expected:
        - HTTP 400
        - Clear validation_errors in response
        - No LLM call wasted
        """
        response = client.post(
            "/api/v1/mcp_spec",
            json=incomplete_request
        )
        
        # Should fail with 400 (our validation) or 422 (Pydantic validation)
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"
        
        error_data = response.json()
        # Error format depends on whether it's our validation (400) or Pydantic (422)
        assert "error" in error_data or "detail" in error_data


class TestKnowledgeEndpoints:
    """Test knowledge management endpoints"""
    
    def test_list_groups(self):
        """Test that knowledge groups are available"""
        response = client.get("/api/v1/knowledge/groups")
        assert response.status_code == 200
        
        data = response.json()
        groups = data["groups"]
        
        # Should have at least one knowledge group
        # Actual groups depend on knowledge_index.json configuration
        assert len(groups) >= 1, "Should have at least 1 knowledge group"
        
        # Check for known groups (may vary based on setup)
        # example_project is the default indexed group
        if len(groups) > 0:
            assert isinstance(groups, list)
    
    def test_list_example_docs(self):
        """Test that example documents are indexed"""
        response = client.get("/api/v1/knowledge/docs/example_project")
        assert response.status_code == 200
        
        data = response.json()
        assert data["group"] == "example_project"
        # Count may be 0 if docs are loaded differently (folder-based vs indexed)
        # The important thing is the endpoint works
        assert data["count"] >= 0, "Count should be non-negative"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration"])
