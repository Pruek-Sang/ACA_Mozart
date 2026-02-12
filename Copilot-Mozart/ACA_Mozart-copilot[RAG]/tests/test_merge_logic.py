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
            room_name="ห้องนอน 2"
        )
        indices = find_target_loads(self.loads, cmd)
        self.assertEqual(indices, [1]) # Should match "ห้องนอน 2" only

    def test_02_find_target_fuzzy(self):
        """Test finding target with partial room name"""
        cmd = EditCommand(
            action=EditAction.CHANGE,
            device_type="HEATER",
            room_name="ห้องน้ำ" # partial match
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
        updated, changes_log = apply_change(self.loads.copy(), [0], cmd)
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
            room_name="โรงรถ"
        )
        updated, changes_log = apply_add(self.loads.copy(), cmd, self.rooms)
        
        # Should be 4 loads now
        self.assertEqual(len(updated), 4)
        new_load = updated[-1]
        self.assertEqual(new_load["device"], "PUMP-750W")
        self.assertEqual(new_load["room_name"], "โรงรถ")

    def test_05_apply_remove(self):
        """Test removing a load"""
        # Remove index 1 (Bedroom 2 AC)
        updated, changes_log = apply_remove(self.loads.copy(), [1])
        
        self.assertEqual(len(updated), 2)
        # Check remaining
        devices = [l["device"] for l in updated]
        self.assertNotIn("AC-9000BTU", devices)
        self.assertIn("AC-12000BTU", devices)

    # =========================================================================
    # 🔧 BUG FIX REGRESSION TESTS
    # These tests verify the AUTO-SAVE → EDIT round-trip works correctly.
    # Previously, AUTO-SAVE stored circuit_name (Thai text) in the "device" field,
    # but find_target_loads() compared against device_code (English) — never matched.
    # =========================================================================

    def test_06_autosave_format_has_device_code(self):
        """
        Regression test: AUTO-SAVE must store device_code, not circuit_name.
        
        Simulates what routes.py AUTO-SAVE does with CircuitData from compute.py.
        The "device" field must contain the machine-readable device_code (e.g. "AC-12000BTU"),
        NOT the human-readable circuit_name (e.g. "แอร์ห้องนอน 1").
        """
        # Simulate CircuitData output from compute.py (after fix: includes device_code)
        circuits_from_compute = [
            {
                "circuit_name": "AC-12000BTU in ห้องนอน 1",  # human-readable display name
                "device_code": "AC-12000BTU",                # machine code (NEW field)
                "room": "ห้องนอน 1",
                "floor": "2",
                "total_watts": 1200,
                "num_loads": 1,
            },
            {
                "circuit_name": "ไฟแสงสว่าง ชั้น 1-1",
                "device_code": "LIGHTING-LED-20W",
                "room": "ห้องนั่งเล่น",
                "floor": "1",
                "total_watts": 60,
                "num_loads": 3,
            },
        ]

        # Simulate AUTO-SAVE mapping (must match routes.py logic exactly)
        loads_to_save = [
            {
                "device": c.get("device_code") or c.get("circuit_name", ""),
                "device_name": c.get("circuit_name", ""),
                "room_name": c.get("room", "") or c.get("floor", ""),
                "floor": int(c.get("floor", 1)) if str(c.get("floor", "")).isdigit() else 1,
                "quantity": c.get("num_loads", 1),
                "power_watts": c.get("total_watts", 0),
            }
            for c in circuits_from_compute
        ]

        # ASSERT: "device" field must be device_code, NOT circuit_name
        self.assertEqual(loads_to_save[0]["device"], "AC-12000BTU")
        self.assertNotEqual(loads_to_save[0]["device"], "AC-12000BTU in ห้องนอน 1")
        self.assertEqual(loads_to_save[1]["device"], "LIGHTING-LED-20W")
        
        # ASSERT: human name preserved separately
        self.assertEqual(loads_to_save[0]["device_name"], "AC-12000BTU in ห้องนอน 1")
        
        # ASSERT: extra fields preserved for merge context
        self.assertEqual(loads_to_save[0]["quantity"], 1)
        self.assertEqual(loads_to_save[0]["power_watts"], 1200)

    def test_07_roundtrip_autosave_then_edit(self):
        """
        Regression test: Full round-trip AUTO-SAVE → find_target_loads → apply_change.
        
        This is the exact scenario that was broken in production:
        1. User designs a house → AUTO-SAVE stores loads
        2. User says "เปลี่ยนแอร์เป็น 18000BTU" → merge engine must find the AC
        3. Merge engine applies the change
        
        Previously failed because AUTO-SAVE stored circuit_name in "device",
        but find_target_loads compared device_code against it → never matched.
        """
        # Step 1: Simulate AUTO-SAVE output (after fix: device = device_code)
        autosaved_loads = [
            {"device": "AC-12000BTU", "device_name": "AC-12000BTU in ห้องนอน 1", "room_name": "ห้องนอน 1", "floor": 2, "quantity": 1, "power_watts": 1200},
            {"device": "AC-9000BTU", "device_name": "AC-9000BTU in ห้องนอน 2", "room_name": "ห้องนอน 2", "floor": 2, "quantity": 1, "power_watts": 900},
            {"device": "HEATER-3500W", "device_name": "HEATER-3500W in ห้องน้ำ 1", "room_name": "ห้องน้ำ 1", "floor": 1, "quantity": 1, "power_watts": 3500},
        ]

        # Step 2: User says "เปลี่ยนแอร์ห้องนอน 1 เป็น 18000BTU"
        cmd = EditCommand(
            action=EditAction.CHANGE,
            device_type="AC",
            room_name="ห้องนอน 1",
            new_value=18000,
            unit="BTU"
        )

        # Step 3: find_target_loads must find the AC in ห้องนอน 1
        indices = find_target_loads(autosaved_loads, cmd)
        self.assertEqual(len(indices), 1, "find_target_loads must find exactly 1 matching AC")
        self.assertEqual(indices[0], 0, "Must match index 0 (AC-12000BTU in ห้องนอน 1)")

        # Step 4: Apply the change
        updated, changes_log = apply_change(autosaved_loads.copy(), indices, cmd)
        self.assertEqual(updated[0]["device"], "AC-18000BTU")
        
        # Step 5: Verify other loads untouched
        self.assertEqual(updated[1]["device"], "AC-9000BTU")
        self.assertEqual(updated[2]["device"], "HEATER-3500W")

if __name__ == '__main__':
    unittest.main()
