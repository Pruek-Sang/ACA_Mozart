"""
12 Engineering Test Cases for ACA Mozart RAG
=============================================
เจ้าค่ะนายท่าน นี่คือ 12 เคสที่ครอบคลุม "ความถูกต้องเชิงวิศวกรรม"

หากทั้ง 12 เคสผ่าน Layer 0-2 ครบ
= "RAG ตอบได้ระดับที่เอาไปใช้จริงแบบไม่ขายขี้หน้าตัวเอง"
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class TestCaseCategory(str, Enum):
    """Categories of test cases"""
    AMPACITY = "ampacity"
    VOLTAGE_DROP = "voltage_drop"
    DERATING = "derating"
    BREAKER = "breaker"
    CATALOG = "catalog"
    RCD = "rcd"
    INCOMPLETE = "incomplete"
    OUT_OF_SCOPE = "out_of_scope"
    LANGUAGE = "language"
    STANDARD_CONFLICT = "standard_conflict"
    SYSTEM_LEAK = "system_leak"
    FULL_PIPELINE = "full_pipeline"


@dataclass
class TestCase:
    """Definition of a single test case"""
    id: str
    name: str
    category: TestCaseCategory
    question: str
    expected_language: str  # "thai" or "english"
    
    # Layer 1 parameters
    layer1_type: str  # Type for layer1_rules.run_layer1
    ground_truth_params: Dict[str, Any] = field(default_factory=dict)
    
    # Expected outcomes
    expected_min_sources: int = 1
    expected_confidence: Optional[str] = None  # "High", "Medium", "Low", or None
    
    # Special flags
    should_refuse: bool = False  # For out-of-scope questions
    should_ask_clarification: bool = False  # For incomplete specs
    
    # Notes for human review
    notes: str = ""


# =============================================================================
# THE 12 TEST CASES
# =============================================================================

TEST_CASES: List[TestCase] = [
    
    # =========================================================================
    # 1. Q-THW-AMPACITY-EXACT
    # =========================================================================
    TestCase(
        id="Q-THW-AMPACITY-EXACT",
        name="THW Cable Ampacity - Exact Value Check",
        category=TestCaseCategory.AMPACITY,
        question="สาย THW ขนาด 2.5 ตร.มม. เดินในท่อร้อยสาย มีพิกัดกระแสกี่แอมป์?",
        expected_language="thai",
        layer1_type="ampacity",
        ground_truth_params={
            "wire_size_mm2": 2.5,
            "insulation": "THW",
            "in_conduit": True,
            "tolerance_percent": 5.0
        },
        expected_min_sources=1,
        expected_confidence="High",
        notes="Ground Truth: THW 2.5mm² in conduit = 24A (วสท. ตาราง 5-20)"
    ),
    
    # =========================================================================
    # 2. Q-VD-LIMIT-CHECK
    # =========================================================================
    TestCase(
        id="Q-VD-LIMIT-CHECK",
        name="Voltage Drop Limit Verification",
        category=TestCaseCategory.VOLTAGE_DROP,
        question="วงจรย่อยในบ้านพักอาศัย ยอมให้แรงดันตกได้สูงสุดกี่เปอร์เซ็นต์ตามมาตรฐาน วสท.?",
        expected_language="thai",
        layer1_type="voltage_drop",
        ground_truth_params={
            "expected_vd_percent": 3.0,
            "max_allowed": 3.0,
            "tolerance_percent": 0.2
        },
        expected_min_sources=1,
        expected_confidence="High",
        notes="Ground Truth: VD ≤ 3% for branch circuits (วสท. 2564)"
    ),
    
    # =========================================================================
    # 3. Q-DERATING-MULTIFACTOR
    # =========================================================================
    TestCase(
        id="Q-DERATING-MULTIFACTOR",
        name="Derating Factor for Grouped Conductors",
        category=TestCaseCategory.DERATING,
        question="ถ้าเดินสายไฟ 6 เส้นในท่อเดียวกัน ต้องใช้ตัวคูณลดค่ากระแส (derating factor) เท่าไหร่?",
        expected_language="thai",
        layer1_type="derating",
        ground_truth_params={
            "factor_type": "conductor_grouping",
            "condition_value": 6,
            "tolerance": 0.05
        },
        expected_min_sources=1,
        expected_confidence="High",
        notes="Ground Truth: 4-6 conductors = 0.8 derating factor (IEC 60364-5-52)"
    ),
    
    # =========================================================================
    # 4. Q-BREAKER-SELECTION
    # =========================================================================
    TestCase(
        id="Q-BREAKER-SELECTION",
        name="Circuit Breaker Selection for Load",
        category=TestCaseCategory.BREAKER,
        question="โหลดไฟฟ้า 18 แอมป์ ควรใช้เบรกเกอร์ขนาดกี่แอมป์?",
        expected_language="thai",
        layer1_type="breaker",
        ground_truth_params={
            "load_current_a": 18
        },
        expected_min_sources=1,
        expected_confidence="High",
        notes="Ground Truth: 18A load needs 25A breaker (80% rule: 18/0.8 = 22.5 → 25A)"
    ),
    
    # =========================================================================
    # 5. Q-CATALOG-DEVICE-CODE
    # =========================================================================
    TestCase(
        id="Q-CATALOG-DEVICE-CODE",
        name="Device Code Catalog Validation",
        category=TestCaseCategory.CATALOG,
        question="เครื่องทำน้ำอุ่นไฟฟ้า 3500W ใช้รหัสอุปกรณ์อะไรใน catalog?",
        expected_language="thai",
        layer1_type="device_code",
        ground_truth_params={},  # Will check if HEATER-3500W is mentioned
        expected_min_sources=1,
        expected_confidence="High",
        notes="Ground Truth: HEATER-3500W in DEVICE_CODES.md"
    ),
    
    # =========================================================================
    # 6. Q-RCD-SELECTION-BY-STANDARD
    # =========================================================================
    TestCase(
        id="Q-RCD-SELECTION-BY-STANDARD",
        name="RCD/RCBO Requirement for Bathroom",
        category=TestCaseCategory.RCD,
        question="วงจรไฟฟ้าในห้องน้ำต้องติดตั้ง RCD หรือ RCBO ความไวเท่าไหร่?",
        expected_language="thai",
        layer1_type="rcd",
        ground_truth_params={
            "location_type": "bathroom"
        },
        expected_min_sources=1,
        expected_confidence="High",
        notes="Ground Truth: Bathroom requires RCD/RCBO 30mA (วสท. 2564)"
    ),
    
    # =========================================================================
    # 7. Q-INCOMPLETE-SPEC
    # =========================================================================
    TestCase(
        id="Q-INCOMPLETE-SPEC",
        name="Incomplete Specification Handling",
        category=TestCaseCategory.INCOMPLETE,
        question="ช่วยออกแบบระบบไฟฟ้าให้หน่อย",
        expected_language="thai",
        layer1_type="device_code",  # Doesn't matter, should ask clarification
        ground_truth_params={},
        expected_min_sources=0,  # May not retrieve anything useful
        expected_confidence="Low",
        should_ask_clarification=True,
        notes="System should ask for: building type, area, loads, etc."
    ),
    
    # =========================================================================
    # 8. Q-OUT-OF-SCOPE
    # =========================================================================
    TestCase(
        id="Q-OUT-OF-SCOPE",
        name="Out of Scope Question Rejection",
        category=TestCaseCategory.OUT_OF_SCOPE,
        question="วิธีทำอาหารไทยที่อร่อยที่สุด",
        expected_language="thai",
        layer1_type="device_code",  # Doesn't matter, should refuse
        ground_truth_params={},
        expected_min_sources=0,
        expected_confidence="Low",
        should_refuse=True,
        notes="System should politely refuse - not electrical engineering"
    ),
    
    # =========================================================================
    # 9. Q-LANG-EN-STRICT
    # =========================================================================
    TestCase(
        id="Q-LANG-EN-STRICT",
        name="English Language Response",
        category=TestCaseCategory.LANGUAGE,
        question="What is the ampacity of THW 4.0mm² cable in conduit according to EIT standard?",
        expected_language="english",
        layer1_type="ampacity",
        ground_truth_params={
            "wire_size_mm2": 4.0,
            "insulation": "THW",
            "in_conduit": True,
            "tolerance_percent": 5.0
        },
        expected_min_sources=1,
        expected_confidence="High",
        notes="Ground Truth: THW 4.0mm² in conduit = 32A. Answer MUST be in English."
    ),
    
    # =========================================================================
    # 10. Q-STANDARD-CONFLICT
    # =========================================================================
    TestCase(
        id="Q-STANDARD-CONFLICT",
        name="Standard Conflict Resolution",
        category=TestCaseCategory.STANDARD_CONFLICT,
        question="มาตรฐาน วสท. กับ IEC มีข้อกำหนดแรงดันตกต่างกันไหม? ควรใช้ค่าไหน?",
        expected_language="thai",
        layer1_type="voltage_drop",
        ground_truth_params={
            "expected_vd_percent": 3.0,
            "max_allowed": 3.0
        },
        expected_min_sources=1,
        expected_confidence="Medium",
        notes="Should explain that วสท. is based on IEC but adapted for Thailand. Use วสท. as primary."
    ),
    
    # =========================================================================
    # 11. Q-SYSTEM-LEAK-PATTERN
    # =========================================================================
    TestCase(
        id="Q-SYSTEM-LEAK-PATTERN",
        name="System Boundary Leak Detection",
        category=TestCaseCategory.SYSTEM_LEAK,
        question="ช่วยคำนวณ voltage drop ให้หน่อย สายยาว 50 เมตร กระแส 20 แอมป์",
        expected_language="thai",
        layer1_type="voltage_drop",
        ground_truth_params={},  # Cannot validate without wire size
        expected_min_sources=1,
        expected_confidence="Medium",
        should_ask_clarification=True,  # Missing wire size
        notes="RAG should NOT calculate VD directly. Should ask for wire size OR explain what's needed for MCP to calculate."
    ),
    
    # =========================================================================
    # 12. Q-FULL-PIPELINE-EXPLAIN-MCP
    # =========================================================================
    TestCase(
        id="Q-FULL-PIPELINE-EXPLAIN-MCP",
        name="Full Pipeline MCP Handoff Explanation",
        category=TestCaseCategory.FULL_PIPELINE,
        question="ถ้าต้องการออกแบบระบบไฟฟ้าบ้าน 2 ชั้น มีห้องนอน 3 ห้อง ครัวหนัก (มีเตาไฟฟ้า 3000W) ระบบต้องทำอะไรบ้าง?",
        expected_language="thai",
        layer1_type="device_code",
        ground_truth_params={},
        expected_min_sources=2,
        expected_confidence="High",
        notes="Should explain: 1) Gather requirements 2) Build spec 3) Send to MCP for calculations 4) Return design"
    ),
]


# =============================================================================
# TEST CASE UTILITIES
# =============================================================================

def get_test_case_by_id(case_id: str) -> Optional[TestCase]:
    """Get a test case by its ID."""
    for tc in TEST_CASES:
        if tc.id == case_id:
            return tc
    return None


def get_test_cases_by_category(category: TestCaseCategory) -> List[TestCase]:
    """Get all test cases in a category."""
    return [tc for tc in TEST_CASES if tc.category == category]


def get_all_test_case_ids() -> List[str]:
    """Get list of all test case IDs."""
    return [tc.id for tc in TEST_CASES]


# =============================================================================
# TEST CASE VALIDATION HELPERS
# =============================================================================

def check_should_refuse(answer: str) -> bool:
    """Check if answer indicates refusal (for out-of-scope questions)."""
    refusal_patterns = [
        "ไม่สามารถ",
        "ขออภัย",
        "ไม่เกี่ยวข้อง",
        "นอกขอบเขต",
        "cannot",
        "sorry",
        "outside scope",
        "not related to electrical"
    ]
    answer_lower = answer.lower()
    return any(pattern in answer_lower for pattern in refusal_patterns)


def check_asks_clarification(answer: str) -> bool:
    """Check if answer asks for clarification (for incomplete specs)."""
    clarification_patterns = [
        "ต้องการข้อมูลเพิ่มเติม",
        "ช่วยบอก",
        "กรุณาระบุ",
        "ขาดข้อมูล",
        "need more information",
        "please specify",
        "what is",
        "could you provide",
        "ขนาดพื้นที่",
        "ประเภทอาคาร",
        "จำนวนห้อง"
    ]
    answer_lower = answer.lower()
    return any(pattern in answer_lower for pattern in clarification_patterns)


def check_language_match(answer: str, expected_language: str) -> bool:
    """Check if answer language matches expected."""
    thai_chars = sum(1 for c in answer if '\u0e00' <= c <= '\u0e7f')
    thai_ratio = thai_chars / max(len(answer), 1)
    
    if expected_language == "thai":
        return thai_ratio > 0.3  # At least 30% Thai
    else:  # english
        return thai_ratio < 0.1  # Less than 10% Thai


# =============================================================================
# GROUND TRUTH QUICK REFERENCE
# =============================================================================

GROUND_TRUTH_REFERENCE = {
    "Q-THW-AMPACITY-EXACT": {
        "description": "THW 2.5mm² in conduit",
        "expected_value": 24,
        "unit": "A",
        "source": "วสท. ตาราง 5-20 / catalog_rows.csv CS002"
    },
    "Q-VD-LIMIT-CHECK": {
        "description": "Branch circuit VD limit",
        "expected_value": 3.0,
        "unit": "%",
        "source": "วสท. 2564 / VR004"
    },
    "Q-DERATING-MULTIFACTOR": {
        "description": "Derating for 6 conductors in conduit",
        "expected_value": 0.8,
        "unit": "factor",
        "source": "IEC 60364-5-52 / DF001"
    },
    "Q-BREAKER-SELECTION": {
        "description": "Breaker for 18A load (80% rule)",
        "expected_value": 25,
        "unit": "A",
        "source": "80% continuous load rule"
    },
    "Q-CATALOG-DEVICE-CODE": {
        "description": "Water heater 3500W device code",
        "expected_value": "HEATER-3500W",
        "unit": None,
        "source": "DEVICE_CODES.md"
    },
    "Q-RCD-SELECTION-BY-STANDARD": {
        "description": "RCD sensitivity for bathroom",
        "expected_value": 30,
        "unit": "mA",
        "source": "วสท. 2564 / wet area requirements"
    },
    "Q-LANG-EN-STRICT": {
        "description": "THW 4.0mm² in conduit",
        "expected_value": 32,
        "unit": "A",
        "source": "วสท. ตาราง 5-20 / catalog_rows.csv CS004"
    },
}
