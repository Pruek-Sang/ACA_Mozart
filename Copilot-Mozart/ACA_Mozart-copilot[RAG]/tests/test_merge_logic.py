"""
Test Suite for Merge Engine Logic (Level 2 Testing)

Tests the integration logic of merging changes into design data.
Mocking session_injector to avoid DB calls.

Run independently: python3 tests/test_merge_logic.py
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, patch

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.context.merge_engine import apply_change, apply_add, apply_remove, find_target_loads
from app.parsers.edit_command import EditCommand, EditAction

class TestMergeLogic(unittest.TestCase):
    
    def setUp(self):
        # Sample loads
        self.loads = [
            {"device": "AC-12000BTU", "room_name": "ห้องนอน 1", "floor": 2},
            {"device": "AC-9000BTU", "room_name": "ห้องนอน 2", "floor": 2},
            {"device": "HEATER-3500W", "room_name": "ห้องน้ำ 1", "floor": 1},
        ]
        self.rooms = [
            {"name": "ห้องนอน 1", "floor": 2},
            {"name": "ห้องน้ำ 1", "floor": 1}
        ]

    def test_01_find_target_exact(self):
        """Test finding exact target load"""
        cmd = EditCommand(
            action=EditAction.CHANGE,
            device_type="AC",
            target_room="ห้องนอน 2"
        )
        indices = find_target_loads(self.loads, cmd)
        self.assertEqual(indices, [1]) # Should match "ห้องนอน 2" only

    def test_02_find_target_fuzzy(self):
        """Test finding target with partial room name"""
        cmd = EditCommand(
            action=EditAction.CHANGE,
            device_type="HEATER",
            target_room="ห้องน้ำ" # partial match
        )
        indices = find_target_loads(self.loads, cmd)
        self.assertEqual(indices, [2]) # Should match "ห้องน้ำ 1"

    def test_03_apply_change_btu(self):
        """Test changing BTU value"""
        cmd = EditCommand(
            action=EditAction.CHANGE,
            device_type="AC",
            new_value=18000,
            unit="BTU"
        )
        # Apply to index 0 (Bedroom 1)
        updated = apply_change(self.loads.copy(), [0], cmd)
        self.assertEqual(updated[0]["device"], "AC-18000BTU")
        # Ensure others untouched
        self.assertEqual(updated[1]["device"], "AC-9000BTU")

    def test_04_apply_add_new_load(self):
        """Test adding new load"""
        cmd = EditCommand(
            action=EditAction.ADD,
            device_type="PUMP",
            new_value=750,
            unit="W",
            target_room="โรงรถ"
        )
        updated = apply_add(self.loads.copy(), cmd, self.rooms)
        
        # Should be 4 loads now
        self.assertEqual(len(updated), 4)
        new_load = updated[-1]
        self.assertEqual(new_load["device"], "PUMP-750W")
        self.assertEqual(new_load["room_name"], "โรงรถ")

    def test_05_apply_remove(self):
        """Test removing a load"""
        # Remove index 1 (Bedroom 2 AC)
        updated = apply_remove(self.loads.copy(), [1])
        
        self.assertEqual(len(updated), 2)
        # Check remaining
        devices = [l["device"] for l in updated]
        self.assertNotIn("AC-9000BTU", devices)
        self.assertIn("AC-12000BTU", devices)

if __name__ == '__main__':
    unittest.main()
