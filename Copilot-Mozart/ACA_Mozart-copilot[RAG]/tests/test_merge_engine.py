import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.context.merge_engine import merge_design_changes, EditCommand, EditAction, TargetType

# Mock data
SAMPLE_LOADS = [
    {"device": "AC-12000BTU", "room_name": "Bedroom 1", "quantity": 1},
    {"device": "Fan", "room_name": "Kitchen", "quantity": 2}
]
SAMPLE_ROOMS = [
    {"name": "Bedroom 1", "type": "bedroom"},
    {"name": "Kitchen", "type": "kitchen"}
]

@pytest.mark.asyncio
async def test_device_not_found():
    """Feature 1: Should return status='not_found' when device not found"""
    with patch('app.context.session_injector.session_injector') as mock_injector, \
         patch('app.context.merge_engine.parse_edit_command') as mock_parse:
        
        # Setup session mock
        mock_injector.get_session.return_value = MagicMock(
            loads=SAMPLE_LOADS, rooms=SAMPLE_ROOMS, site_context={}
        )
        
        # Setup parser to return a command for non-existent device
        mock_parse.return_value = EditCommand(
            action=EditAction.REMOVE,
            target_type=TargetType.DEVICE,
            device_type="Heater", # Does not exist
            room_name="Bedroom 1"
        )
        
        result = await merge_design_changes("test-session", "remove heater")
        
        assert result is not None
        assert result["status"] == "not_found"
        assert "Heater" in result["message"] or "device" in result["message"]

@pytest.mark.asyncio
async def test_add_device_summary():
    """Feature 3: Should return changes summary for ADD"""
    with patch('app.context.session_injector.session_injector') as mock_injector, \
         patch('app.context.merge_engine.parse_edit_command') as mock_parse:
        
        mock_injector.get_session.return_value = MagicMock(
            loads=SAMPLE_LOADS, rooms=SAMPLE_ROOMS, site_context={}
        )
        mock_injector.update_design = AsyncMock(return_value=True)
        
        mock_parse.return_value = EditCommand(
            action=EditAction.ADD,
            target_type=TargetType.DEVICE,
            device_type="TV",
            quantity=1,
            room_name="Bedroom 1"
        )
        
        result = await merge_design_changes("test-session", "add TV to bedroom 1")
        
        assert result["status"] == "success"
        assert "TV" in result["message"]
        assert len(result["changes"]) == 1
        # Check integrity of data
        new_loads = result["data"]["loads"]
        assert len(new_loads) == 3 # 2 original + 1 new

@pytest.mark.asyncio
async def test_quantity_remove():
    """Feature 4: Quantity-based removal logic"""
    with patch('app.context.session_injector.session_injector') as mock_injector, \
         patch('app.context.merge_engine.parse_edit_command') as mock_parse:
         
        # Start with 2 Fans
        loads = [{"device": "Fan", "room_name": "Kitchen", "quantity": 2}]
        
        mock_injector.get_session.return_value = MagicMock(
            loads=loads, rooms=SAMPLE_ROOMS, site_context={}
        )
        mock_injector.update_design = AsyncMock(return_value=True)
        
        # Mock command: Remove 1 Fan
        mock_parse.return_value = EditCommand(
            action=EditAction.REMOVE,
            target_type=TargetType.DEVICE,
            device_type="Fan",
            quantity=1,
            room_name="Kitchen"
        )
        
        result = await merge_design_changes("test-session", "remove 1 fan")
        
        assert result["status"] == "success"
        updated_loads = result["data"]["loads"]
        assert len(updated_loads) == 1
        assert updated_loads[0]["quantity"] == 1 # 2 - 1 = 1
        assert "Fan" in result["message"]

@pytest.mark.asyncio
async def test_remove_all_excess_quantity():
    """Feature 4: Remove more than exists should remove all"""
    with patch('app.context.session_injector.session_injector') as mock_injector, \
         patch('app.context.merge_engine.parse_edit_command') as mock_parse:
         
        loads = [{"device": "Fan", "room_name": "Kitchen", "quantity": 2}]
        
        mock_injector.get_session.return_value = MagicMock(
            loads=loads, rooms=SAMPLE_ROOMS, site_context={}
        )
        mock_injector.update_design = AsyncMock(return_value=True)
        
        # Mock command: Remove 5 Fans
        mock_parse.return_value = EditCommand(
            action=EditAction.REMOVE,
            target_type=TargetType.DEVICE,
            device_type="Fan",
            quantity=5, # Exceeds 2
            room_name="Kitchen"
        )
        
        result = await merge_design_changes("test-session", "remove 5 fans")
        
        # Should detect "Not enough available" warning but still succeed in removing all
        assert result["status"] == "success"
        updated_loads = result["data"]["loads"]
        assert len(updated_loads) == 0 # All removed
        
        # Check logs for warning msg (if we captured it, but here checking result message)
        # Message logic in merge_engine loops through changes, might have warning
        # We just assume success now.
