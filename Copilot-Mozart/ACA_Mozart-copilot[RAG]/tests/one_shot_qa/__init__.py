"""
ACA Mozart RAG - One-Shot QA Test Framework
============================================
3-Layer QA harness for validating LLM answer correctness

เจ้าค่ะนายท่าน Framework นี้ตรวจสอบ "ความถูกต้อง" ของคำตอบ RAG ใน 3 ชั้น:

Layer 0 (Hard Assertions):
    - HTTP 200
    - Valid JSON
    - Pydantic StandardResponse
    - min_sources check
    → HARD-FAIL if fails

Layer 1 (Rule-Based Engineering):
    - Parse numbers from answer (ampacity, VD%, breaker, derating)
    - Validate against ground truth (±tolerance)
    - Check standard references
    → SOFT-FAIL or HARD-FAIL

Layer 2 (Semantic Judge):
    - LLM evaluates answer quality
    - uses_docs, logic_correct, math_correct, language_ok
    → SOFT-FAIL or HARD-FAIL

Usage:
    # Run harness from CLI
    python -m tests.one_shot_qa.harness --api-url http://localhost:8080/api/v1/ask
    
    # Run via pytest
    pytest tests/one_shot_qa/test_one_shot_qa.py -v
    pytest tests/one_shot_qa/test_one_shot_qa.py -v -m "not integration"

12 Test Cases:
    Q-THW-AMPACITY-EXACT      - THW cable ampacity
    Q-VD-LIMIT-CHECK          - Voltage drop limit
    Q-DERATING-MULTIFACTOR    - Derating factors
    Q-BREAKER-SELECTION       - Breaker selection
    Q-CATALOG-DEVICE-CODE     - Device code validation
    Q-RCD-SELECTION-BY-STANDARD - RCD requirements
    Q-INCOMPLETE-SPEC         - Incomplete spec handling
    Q-OUT-OF-SCOPE            - Out of scope rejection
    Q-LANG-EN-STRICT          - English language response
    Q-STANDARD-CONFLICT       - Standard conflict resolution
    Q-SYSTEM-LEAK-PATTERN     - System boundary detection
    Q-FULL-PIPELINE-EXPLAIN-MCP - Full pipeline explanation
"""

from .ground_truth import (
    THW_CABLES,
    XLPE_CABLES,
    CableSpec,
    CableInsulation,
    STANDARD_BREAKERS,
    get_correct_breaker,
    DERATING_FACTORS,
    get_derating_factor,
    calculate_voltage_drop_1ph,
    is_voltage_drop_acceptable,
    VALID_DEVICE_CODES,
    is_valid_device_code,
    VALID_ROOM_TEMPLATES,
    is_valid_room_template,
    STANDARD_LIMITS,
    validate_ampacity_claim,
)

from .layer0_assertions import (
    Layer0Verdict,
    Layer0Result,
    run_layer0,
    validate_response_dict,
)

from .layer1_rules import (
    Layer1Verdict,
    Layer1Result,
    run_layer1,
)

from .layer2_judge import (
    Layer2Verdict,
    Layer2Result,
    SemanticEvaluation,
    run_layer2,
    mock_evaluate,
)

from .test_cases import (
    QACase,
    QACaseCategory,
    TEST_CASES,
    get_test_case_by_id,
    get_test_cases_by_category,
    get_all_test_case_ids,
    GROUND_TRUTH_REFERENCE,
)

from .harness import (
    FinalVerdict,
    TestCaseResult,
    HarnessReport,
    run_harness,
    run_single_test,
)

__all__ = [
    # Ground Truth
    "THW_CABLES", "XLPE_CABLES", "CableSpec", "CableInsulation",
    "STANDARD_BREAKERS", "get_correct_breaker",
    "DERATING_FACTORS", "get_derating_factor",
    "calculate_voltage_drop_1ph", "is_voltage_drop_acceptable",
    "VALID_DEVICE_CODES", "is_valid_device_code",
    "VALID_ROOM_TEMPLATES", "is_valid_room_template",
    "STANDARD_LIMITS", "validate_ampacity_claim",
    
    # Layer 0
    "Layer0Verdict", "Layer0Result", "run_layer0", "validate_response_dict",
    
    # Layer 1
    "Layer1Verdict", "Layer1Result", "run_layer1",
    
    # Layer 2
    "Layer2Verdict", "Layer2Result", "SemanticEvaluation", "run_layer2", "mock_evaluate",
    
    # Test Cases
    "QACase", "QACaseCategory", "TEST_CASES",
    "get_test_case_by_id", "get_test_cases_by_category", "get_all_test_case_ids",
    "GROUND_TRUTH_REFERENCE",
    
    # Harness
    "FinalVerdict", "TestCaseResult", "HarnessReport",
    "run_harness", "run_single_test",
]