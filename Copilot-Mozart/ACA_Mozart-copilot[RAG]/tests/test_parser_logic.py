"""
Test Suite for Edit Parser Module (Level 1 Testing)

Tests the "Brain" of the edit system:
1. Normalizer (Typo handling)
2. Regex Parser (Pattern matching)
3. Hybrid Parser (Integration)

Run independently: python3 tests/test_parser_logic.py
"""

import sys
import os
import asyncio
import unittest

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.parsers.normalizer import normalize_text, apply_typo_corrections
from app.parsers.regex_parser import regex_parse
from app.parsers.hybrid_parser import parse_edit_command_sync
from app.parsers.edit_command import EditAction

class TestParserLogic(unittest.TestCase):
    
    def test_01_typo_map(self):
        """Test direct typo replacement (The easy stuff)"""
        cases = [
            ("aur", "แอร์"),
            ("arr", "แอร์"),
            ("แอ", "แอร์"),
            ("เเอร์", "แอร์"), # Wrong tone mark
            ("น้ำร้อน", "น้ำอุ่น"),
            ("ปั้มน้ำ", "ปั๊มน้ำ"),
        ]
        for typo, expected in cases:
            result = apply_typo_corrections(typo)
            self.assertIn(expected, result, f"Failed to correct '{typo}' -> '{expected}'")

    def test_02_normalization_chain(self):
        """Test full normalization chain (The messy stuff)"""
        cases = [
            ("เปลี่ยน aur เป็น 18000", "เปลี่ยน แอร์ เป็น 18000"),
            ("  ลบ  ปั้มน้ำ  ", "ลบ ปั๊มน้ำ"), # Whitespace handling
            ("Change AC to 12000 BTU", "change ac to 12000 btu"), # Lowercase
        ]
        for raw, expected in cases:
            result = normalize_text(raw)
            self.assertEqual(result, expected)

    def test_03_regex_change_ac(self):
        """Test CHANGE AC command patterns"""
        cases = [
            # Standard Thai
            ("เปลี่ยนแอร์เป็น 18000 BTU", "AC", 18000, "BTU"),
            ("เปลี่ยนแอร์ห้องนอนเป็น 24000", "AC", 24000, "BTU"),
            ("แก้แอร์ = 9000", "AC", 9000, "BTU"),
            
            # English
            ("change ac to 12000 btu", "AC", 12000, "BTU"),
            ("modify aircon to 18000", "AC", 18000, "BTU"),
            
            # With Typos (Normalized first)
            (normalize_text("เปลี่ยน aur เป็น 18000"), "AC", 18000, "BTU"),
        ]
        
        for text, exp_dev, exp_val, exp_unit in cases:
            # Note: Regex parser expects normalized input if called directly, 
            # but here we test patterns that match normalized form
            cmd = regex_parse(normalize_text(text))
            self.assertIsNotNone(cmd, f"Failed to parse: {text}")
            self.assertEqual(cmd.action, EditAction.CHANGE)
            self.assertEqual(cmd.device_type, exp_dev)
            self.assertEqual(cmd.new_value, exp_val)
            self.assertEqual(cmd.unit, exp_unit)

    def test_04_regex_add_remove(self):
        """Test ADD and REMOVE commands"""
        cases = [
            # ADD
            ("เพิ่มน้ำอุ่น 4500W", EditAction.ADD, "HEATER", 4500),
            ("ติดตั้งปั๊มน้ำ 750 วัตต์", EditAction.ADD, "PUMP", 750),
            ("add socket 4 points", EditAction.ADD, "SOCKET", None), # Complex
            
            # REMOVE
            ("ลบแอร์ออก", EditAction.REMOVE, "AC", None),
            ("เอาปั๊มน้ำออก", EditAction.REMOVE, "PUMP", None),
            ("remove heater", EditAction.REMOVE, "HEATER", None),
        ]
        
        for text, exp_action, exp_dev, exp_val in cases:
            # Skip complex ones for regex if not supported yet
            if "socket" in text: continue 
            
            cmd = regex_parse(normalize_text(text))
            self.assertIsNotNone(cmd, f"Failed to parse: {text}")
            self.assertEqual(cmd.action, exp_action)
            self.assertEqual(cmd.device_type, exp_dev)
            if exp_val:
                self.assertEqual(cmd.new_value, exp_val)

    def test_05_hybrid_orchestrator(self):
        """Test the main entry point (Hybrid Sync)"""
        # This simulates what the Merge Engine calls
        cmd = parse_edit_command_sync("เปลี่ยนแอร์ห้องนอนเป็น 18000 BTU")
        
        self.assertIsNotNone(cmd)
        # Normalizer doesn't add spaces for Thai, so expect attached string
        self.assertEqual(cmd.normalized_input, "เปลี่ยนแอร์ห้องนอนเป็น 18000 btu")
        self.assertEqual(cmd.action, EditAction.CHANGE)
        self.assertEqual(cmd.target_room, "นอน")

if __name__ == '__main__':
    unittest.main()
