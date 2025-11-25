"""
Model Tests - Validate Pydantic Schemas
Tests that all models parse correctly
"""

import pytest
import json
from app.models import (
    ProjectRequirements, RoomInput, LoadInput,
    ProjectInputSpec, ProjectInfo, ElectricalSystem, RoomSpec, LoadSpec, Constraints,
    McpSpecResponse, StandardsProfile, LlmMetadata
)


def test_room_input_basic():
    """Test RoomInput model"""
    room = RoomInput(
        name="ห้องนั่งเล่น",
        type="living_room",
        area_m2=25.0
    )
    assert room.name == "ห้องนั่งเล่น"
    assert room.type == "living_room"
    assert room.area_m2 == 25.0


def test_load_input_basic():
    """Test LoadInput model"""
    load = LoadInput(
        room_name="ห้องนั่งเล่น",
        device="AC_12000BTU",
        quantity=1
    )
    assert load.room_name == "ห้องนั่งเล่น"
    assert load.device == "AC_12000BTU"
    assert load.quantity == 1


def test_project_requirements_structured():
    """Test that ProjectRequirements now uses structured models"""
    req = ProjectRequirements(
        project_name="Test House",
        building_type="residential",
        voltage_system="TH_1PH_230V",
        rooms=[
            RoomInput(name="Living", type="living_room", area_m2=20.0),
            RoomInput(name="Bedroom", type="bedroom", area_m2=15.0)
        ],
        loads=[
            LoadInput(room_name="Living", device="AC_12000BTU", quantity=1),
            LoadInput(room_name="Bedroom", device="OUTLET_16A", quantity=2)
        ],
        user_constraints=["rcd_for_all_outlets"]
    )
    
    assert len(req.rooms) == 2
    assert isinstance(req.rooms[0], RoomInput)
    assert len(req.loads) == 2
    assert isinstance(req.loads[0], LoadInput)


def test_project_input_spec_complete():
    """Test complete ProjectInputSpec structure"""
    spec = ProjectInputSpec(
        project_info=ProjectInfo(
            project_name="Test",
            building_type="RESIDENTIAL",
            spec_version="2.0"
        ),
        electrical_system=ElectricalSystem(
            voltage_system="TH_1PH_230V",
            earthing="TT"
        ),
        rooms=[
            RoomSpec(
                room_id="R1",
                name="Living",
                room_type="LIVING",
                template_code="ROOMT-LIVING-STD",
                area_m2=20.0
            )
        ],
        loads=[
            LoadSpec(
                load_id="L1",
                room_id="R1",
                device_code="AC-12000BTU",
                qty=1,
                notes="Living room AC"
            )
        ],
        constraints=Constraints(
            rule_profile_id="TH_RESIDENTIAL_LV",
            user_constraints=["rcd_for_all_outlets"]
        )
    )
    
    # Validate structure
    assert spec.project_info.spec_version == "2.0"
    assert spec.electrical_system.earthing == "TT"
    assert len(spec.rooms) == 1
    assert spec.rooms[0].room_id == "R1"
    assert len(spec.loads) == 1
    assert spec.loads[0].room_id == "R1"
    assert spec.constraints.rule_profile_id == "TH_RESIDENTIAL_LV"


def test_mcp_spec_response_with_metadata():
    """Test that McpSpecResponse includes llm_metadata"""
    response = McpSpecResponse(
        project_input=ProjectInputSpec(
            project_info=ProjectInfo(
                project_name="Test",
                building_type="RESIDENTIAL",
                spec_version="2.0"
            ),
            electrical_system=ElectricalSystem(
                voltage_system="TH_1PH_230V",
                earthing="TT"
            ),
            rooms=[],
            loads=[],
            constraints=Constraints(
                rule_profile_id="TH_RESIDENTIAL_LV",
                user_constraints=[]
            )
        ),
        standards_profile=StandardsProfile(
            rule_profile_id="TH_RESIDENTIAL_LV",
            notes="Test profile"
        ),
        llm_metadata=LlmMetadata(
            model="gemini-1.5-pro",
            retrieved_docs=["DOC_MCP_CONTRACT"],
            temperature=0.0
        )
    )
    
    # Validate llm_metadata exists
    assert response.llm_metadata.model == "gemini-1.5-pro"
    assert len(response.llm_metadata.retrieved_docs) == 1
    assert response.llm_metadata.temperature == 0.0
    assert response.llm_metadata.timestamp is not None


def test_json_serialization():
    """Test that models serialize to JSON correctly"""
    req = ProjectRequirements(
        project_name="Test",
        building_type="residential",
        voltage_system="TH_1PH_230V",
        rooms=[RoomInput(name="Living", type="living_room")],
        loads=[LoadInput(room_name="Living", device="AC_12000BTU", quantity=1)]
    )
    
    json_str = req.model_dump_json()
    parsed = json.loads(json_str)
    
    assert parsed["project_name"] == "Test"
    assert len(parsed["rooms"]) == 1
    assert parsed["rooms"][0]["type"] == "living_room"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
