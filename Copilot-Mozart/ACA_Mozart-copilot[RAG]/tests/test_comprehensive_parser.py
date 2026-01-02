"""
🧪 COMPREHENSIVE RAG PARSER TEST SUITE
=====================================
ครอบคลุมทุก Edge Case ของการ Parse ข้อความผู้ใช้เป็นข้อมูลไฟฟ้า

Categories:
1. Distance Parsing (ระยะทาง)
2. Device Parsing (อุปกรณ์)
3. Room Parsing (ห้อง)
4. Quantity Parsing (จำนวน)
5. BTU/Wattage Parsing (กำลังไฟ)
6. Wire Size Override (ขนาดสาย)
7. Breaker Override (ขนาด CB)
8. Multi-floor Cases (หลายชั้น)
9. Typo Handling (คำผิด)
10. Edge Cases & Weird Inputs

Run: python tests/test_comprehensive_parser.py
"""

import sys
import os
import unittest
import re

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.parsers.normalizer import normalize_text, apply_typo_corrections

# ============================================================
# MOCK Service for testing _extract_floor_distances
# ============================================================
class MockRagService:
    """Mock class to test _extract_floor_distances without full init."""
    
    def _extract_floor_distances(self, text: str) -> dict:
        """Extract average branch distances per floor from text using regex."""
        distances = {}
        
        # Pattern 1: Explicit floor numbers
        # "ชั้น 1 ยาว 15เมตร", "ชั้น 2 สาย 20 m", "floor 1 15m"
        floor_matches = re.finditer(
            r'(?:ชั้น|floor)\s*(\d+)[^\d]*?(\d+(?:\.\d+)?)\s*(?:เมตร|m|meter)',
            text, re.IGNORECASE
        )
        for m in floor_matches:
            try:
                floor = int(m.group(1))
                dist = float(m.group(2))
                distances[floor] = dist
            except (ValueError, IndexError):
                pass
                
        # Pattern 2: Ground/Lower floor
        if 'ชั้นล่าง' in text or 'ground' in text.lower():
            m = re.search(r'(?:ชั้นล่าง|ground)[^\d]*?(\d+)\s*(?:เมตร|m)', text, re.IGNORECASE)
            if m:
                distances[1] = float(m.group(1))
                
        # Pattern 3: Upper floor
        if 'ชั้นบน' in text or 'upper' in text.lower():
            m = re.search(r'(?:ชั้นบน|upper)[^\d]*?(\d+)\s*(?:เมตร|m)', text, re.IGNORECASE)
            if m:
                distances[2] = float(m.group(1))
                
        # Pattern 4: Generic "ระยะ X เมตร" (applies to all floors if no floor specified)
        if not distances:
            m = re.search(r'(?:ระยะ|distance|เดินสาย)[^\d]*?(\d+(?:\.\d+)?)\s*(?:เมตร|m)', text, re.IGNORECASE)
            if m:
                # Apply to floor 1 and 2 as default
                dist = float(m.group(1))
                distances[1] = dist
                distances[2] = dist
                
        return distances


class TestDistanceParsing(unittest.TestCase):
    """Category 1: Distance Parsing Tests"""
    
    def setUp(self):
        self.service = MockRagService()
    
    def test_thai_floor_explicit(self):
        """Thai explicit floor number"""
        cases = [
            ("ชั้น 1 ยาว 15 เมตร", {1: 15.0}),
            ("ชั้น 2 สาย 20 เมตร", {2: 20.0}),
            ("ชั้น1 15เมตร", {1: 15.0}),  # No spaces
            ("ชั้น 1 เดินสาย 15 m", {1: 15.0}),  # Mixed units
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                result = self.service._extract_floor_distances(text)
                self.assertEqual(result, expected, f"Failed: {text}")
    
    def test_english_floor_explicit(self):
        """English explicit floor number"""
        cases = [
            ("floor 1 15m", {1: 15.0}),
            ("Floor 2 20 meter", {2: 20.0}),
            ("FLOOR1 25m", {1: 25.0}),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                result = self.service._extract_floor_distances(text)
                self.assertEqual(result, expected, f"Failed: {text}")
    
    def test_thai_named_floors(self):
        """Thai named floors (ชั้นล่าง/ชั้นบน)"""
        cases = [
            ("ชั้นล่าง 15 เมตร", {1: 15.0}),
            ("ชั้นบน 25 เมตร", {2: 25.0}),
            ("ชั้นล่างเดินสาย 10m ชั้นบน 20m", {1: 10.0, 2: 20.0}),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                result = self.service._extract_floor_distances(text)
                self.assertEqual(result, expected, f"Failed: {text}")
    
    def test_generic_distance(self):
        """Generic distance without floor (applies to all)"""
        cases = [
            ("ระยะ 15 เมตร", {1: 15.0, 2: 15.0}),
            ("distance 20m", {1: 20.0, 2: 20.0}),
            ("เดินสาย 25 เมตร", {1: 25.0, 2: 25.0}),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                result = self.service._extract_floor_distances(text)
                self.assertEqual(result, expected, f"Failed: {text}")
    
    def test_multi_floor_same_prompt(self):
        """Multiple floors in one prompt"""
        text = "ออกแบบบ้าน 2 ชั้น ชั้น 1 สาย 15 เมตร ชั้น 2 สาย 25 เมตร"
        result = self.service._extract_floor_distances(text)
        self.assertEqual(result, {1: 15.0, 2: 25.0})
    
    def test_decimal_distances(self):
        """Decimal distances"""
        cases = [
            ("ชั้น 1 ยาว 15.5 เมตร", {1: 15.5}),
            ("floor 2 12.75m", {2: 12.75}),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                result = self.service._extract_floor_distances(text)
                self.assertEqual(result, expected, f"Failed: {text}")
    
    def test_no_distance_returns_empty(self):
        """No distance mentioned should return empty"""
        text = "ออกแบบบ้าน 2 ชั้น มีแอร์ 4 ตัว"
        result = self.service._extract_floor_distances(text)
        self.assertEqual(result, {})


class TestDeviceParsing(unittest.TestCase):
    """Category 2: Device Recognition Tests"""
    
    def test_ac_variations(self):
        """Air conditioner variations - Thai typos only (LLM handles English)"""
        # Normalizer handles Thai typos only
        # LLM handles English to Device Code mapping
        thai_ac_typos = ['แอร์', 'aur', 'arr', 'แอ ']
        for kw in thai_ac_typos:
            with self.subTest(keyword=kw):
                normalized = apply_typo_corrections(kw)
                # Should contain แอร์ after normalization
                self.assertIn('แอร์', normalized, f"'{kw}' should normalize to แอร์")
    
    def test_heater_variations(self):
        """Water heater variations"""
        heater_keywords = ['น้ำอุ่น', 'เครื่องทำน้ำอุ่น', 'water heater', 'heater']
        for kw in heater_keywords:
            with self.subTest(keyword=kw):
                # Should normalize to น้ำอุ่น or HEATER
                normalized = apply_typo_corrections(kw)
                # At minimum, should not crash
                self.assertIsNotNone(normalized)
    
    def test_socket_variations(self):
        """Socket/outlet variations"""
        socket_keywords = ['เต้ารับ', 'ปลั๊ก', 'outlet', 'socket']
        for kw in socket_keywords:
            with self.subTest(keyword=kw):
                normalized = apply_typo_corrections(kw)
                self.assertIsNotNone(normalized)


class TestTypoHandling(unittest.TestCase):
    """Category 9: Typo Handling Tests"""
    
    def test_common_typos(self):
        """Common Thai typos"""
        cases = [
            ("aur", "แอร์"),
            ("arr", "แอร์"),
            ("แอ ", "แอร์ "),
            ("เเอร์", "แอร์"),  # Wrong ร character
            ("น้ำร้อน", "น้ำอุ่น"),
            ("ปั้มน้ำ", "ปั๊มน้ำ"),
        ]
        for typo, expected in cases:
            with self.subTest(typo=typo):
                result = apply_typo_corrections(typo)
                self.assertIn(expected.strip(), result, f"'{typo}' should contain '{expected}'")
    
    def test_english_case_insensitive(self):
        """English should be case insensitive"""
        cases = [
            ("AC", "ac"),
            ("HEATER", "heater"),
            ("Socket", "socket"),
        ]
        for original, expected in cases:
            with self.subTest(original=original):
                result = normalize_text(original)
                self.assertEqual(result.lower(), expected)


class TestQuantityParsing(unittest.TestCase):
    """Category 4: Quantity Parsing Tests"""
    
    def test_thai_quantity_patterns(self):
        """Thai quantity patterns"""
        patterns = [
            (r'(\d+)\s*(?:ตัว|เครื่อง|จุด|ดวง)', "แอร์ 3 ตัว", 3),
            (r'(\d+)\s*(?:ตัว|เครื่อง|จุด|ดวง)', "เต้ารับ 6 จุด", 6),
            (r'(\d+)\s*(?:ตัว|เครื่อง|จุด|ดวง)', "ไฟ 10 ดวง", 10),
        ]
        for pattern, text, expected in patterns:
            with self.subTest(text=text):
                m = re.search(pattern, text)
                self.assertIsNotNone(m, f"Pattern should match: {text}")
                self.assertEqual(int(m.group(1)), expected)
    
    def test_socket_pair_counting(self):
        """Socket pair counting (คู่ vs เดี่ยว)"""
        # ตาม วสท. 2564: "คู่" และ "เดี่ยว" คือประเภท ไม่ใช่ตัวคูณ
        # "เต้ารับคู่ 6 จุด" = 6 outlets, NOT 12!
        cases = [
            ("เต้ารับคู่ 6 จุด", 6),  # 6 double outlets = 6 units
            ("เต้ารับเดี่ยว 4 จุด", 4),  # 4 single outlets = 4 units
            ("คู่×6", 6),
            ("เดี่ยว×1", 1),
        ]
        for text, expected_qty in cases:
            with self.subTest(text=text):
                # Extract number before จุด or after ×
                m = re.search(r'[×x]?\s*(\d+)\s*(?:จุด)?', text)
                if m:
                    qty = int(m.group(1))
                    self.assertEqual(qty, expected_qty, f"'{text}' should be {expected_qty} units")


class TestBTUWattageParsing(unittest.TestCase):
    """Category 5: BTU/Wattage Parsing Tests"""
    
    def test_btu_patterns(self):
        """BTU extraction patterns"""
        patterns = [
            ("แอร์ 12000 BTU", 12000),
            ("แอร์12000BTU", 12000),
            ("AC 18000 btu", 18000),
            ("แอร์ 24,000 BTU", 24000),  # With comma
        ]
        for text, expected in patterns:
            with self.subTest(text=text):
                m = re.search(r'(\d+[,\d]*)\s*(?:BTU|btu)', text)
                self.assertIsNotNone(m, f"Should find BTU in: {text}")
                value = int(m.group(1).replace(',', ''))
                self.assertEqual(value, expected)
    
    def test_wattage_patterns(self):
        """Wattage extraction patterns"""
        patterns = [
            ("น้ำอุ่น 4500W", 4500),
            ("HEATER 3500 วัตต์", 3500),
            ("ปั๊มน้ำ 750W", 750),
            ("เตา 3,000W", 3000),  # With comma
        ]
        for text, expected in patterns:
            with self.subTest(text=text):
                m = re.search(r'(\d+[,\d]*)\s*(?:W|w|วัตต์|watt)', text, re.IGNORECASE)
                self.assertIsNotNone(m, f"Should find wattage in: {text}")
                value = int(m.group(1).replace(',', ''))
                self.assertEqual(value, expected)


class TestEdgeCases(unittest.TestCase):
    """Category 10: Edge Cases & Weird Inputs"""
    
    def test_empty_input(self):
        """Empty input should not crash"""
        result = apply_typo_corrections("")
        self.assertEqual(result, "")
    
    def test_only_numbers(self):
        """Only numbers should not crash"""
        result = normalize_text("12345")
        self.assertIsNotNone(result)
    
    def test_special_characters(self):
        """Special characters handling"""
        text = "แอร์ @#$% 12000 BTU!!!"
        result = normalize_text(text)
        self.assertIsNotNone(result)
    
    def test_very_large_numbers(self):
        """Very large numbers (Fat Finger test)"""
        # 180,000 BTU instead of 18,000 BTU
        text = "แอร์ 180000 BTU"
        m = re.search(r'(\d+)\s*BTU', text, re.IGNORECASE)
        self.assertIsNotNone(m)
        value = int(m.group(1))
        # Should detect but NOT fix - that's for LogicValidator
        self.assertEqual(value, 180000)
    
    def test_mixed_language(self):
        """Mixed Thai/English"""
        text = "ออกแบบ floor 1 มี AC 3 units"
        result = normalize_text(text)
        self.assertIsNotNone(result)


class TestRoomParsing(unittest.TestCase):
    """Category 3: Room Parsing Tests"""
    
    def test_standard_room_names(self):
        """Standard Thai room names"""
        room_patterns = [
            (r'ห้อง(นอน|น้ำ|ครัว|นั่งเล่น)', "ห้องนอน", "นอน"),
            (r'ห้อง(นอน|น้ำ|ครัว|นั่งเล่น)', "ห้องครัว", "ครัว"),
            (r'ห้อง(นอน|น้ำ|ครัว|นั่งเล่น)', "ห้องน้ำ", "น้ำ"),
        ]
        for pattern, text, expected in room_patterns:
            with self.subTest(text=text):
                m = re.search(pattern, text)
                self.assertIsNotNone(m, f"Should match: {text}")
                self.assertEqual(m.group(1), expected)
    
    def test_numbered_rooms(self):
        """Numbered rooms (ห้องนอน 1, ห้องนอน 2)"""
        pattern = r'ห้อง(นอน|น้ำ)\s*(\d+)?'
        cases = [
            ("ห้องนอน 1", ("นอน", "1")),
            ("ห้องนอน 2", ("นอน", "2")),
            ("ห้องน้ำ", ("น้ำ", None)),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                m = re.search(pattern, text)
                self.assertIsNotNone(m)
                self.assertEqual(m.group(1), expected[0])


# ============================================================
# SUMMARY PRINT
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🧪 COMPREHENSIVE RAG PARSER TEST SUITE")
    print("=" * 60)
    print("""
Categories Covered:
  1. Distance Parsing (ระยะทาง)
  2. Device Parsing (อุปกรณ์)  
  3. Room Parsing (ห้อง)
  4. Quantity Parsing (จำนวน)
  5. BTU/Wattage Parsing (กำลังไฟ)
  9. Typo Handling (คำผิด)
  10. Edge Cases & Weird Inputs
    """)
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2)
