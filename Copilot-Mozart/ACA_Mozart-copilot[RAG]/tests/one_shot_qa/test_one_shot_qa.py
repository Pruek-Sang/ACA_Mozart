"""
pytest Integration for One-Shot QA Harness
==========================================
เจ้าค่ะนายท่าน ไฟล์นี้ทำให้รัน test framework ผ่าน pytest ได้

Usage:
    pytest tests/one_shot_qa/test_one_shot_qa.py -v
    pytest tests/one_shot_qa/test_one_shot_qa.py -v -k "ampacity"
    pytest tests/one_shot_qa/test_one_shot_qa.py -v --api-url http://localhost:8080/api/v1/ask
"""

import pytest
import asyncio
import os
from typing import Optional

from .layer0_assertions import run_layer0, validate_response_dict, Layer0Verdict
from .layer1_rules import run_layer1, Layer1Verdict
from .layer2_judge import run_layer2, mock_evaluate, Layer2Verdict
from .test_cases import (
    TEST_CASES,
    QACase,
    get_test_case_by_id,
    check_should_refuse,
    check_asks_clarification,
    check_language_match,
    QACaseCategory,
    GROUND_TRUTH_REFERENCE
)
from .ground_truth import (
    THW_CABLES,
    validate_ampacity_claim,
    CableInsulation,
    get_correct_breaker,
    get_derating_factor,
    is_valid_device_code,
    STANDARD_LIMITS
)


# =============================================================================
# PYTEST FIXTURES - Note: pytest_addoption is in tests/conftest.py
# =============================================================================


# =============================================================================
# UNIT TESTS - Ground Truth Module
# =============================================================================

class TestGroundTruth:
    """Unit tests for ground truth data"""
    
    def test_thw_cable_specs_exist(self):
        """Verify THW cable specs are loaded"""
        assert 1.5 in THW_CABLES
        assert 2.5 in THW_CABLES
        assert 4.0 in THW_CABLES
        
    def test_thw_2_5mm_ampacity(self):
        """Verify THW 2.5mm² ampacity = 24A"""
        spec = THW_CABLES[2.5]
        assert spec.ampacity_in_conduit_a == 24
        
    def test_validate_ampacity_correct(self):
        """Test ampacity validation with correct value"""
        valid, msg = validate_ampacity_claim(
            wire_size_mm2=2.5,
            claimed_ampacity_a=24,
            insulation=CableInsulation.THW,
            in_conduit=True
        )
        assert valid, msg
        
    def test_validate_ampacity_with_tolerance(self):
        """Test ampacity validation within tolerance"""
        # 24A ± 5% = 22.8 to 25.2
        valid, _ = validate_ampacity_claim(2.5, 23, CableInsulation.THW, True, 5.0)
        assert valid
        valid, _ = validate_ampacity_claim(2.5, 25, CableInsulation.THW, True, 5.0)
        assert valid
        
    def test_validate_ampacity_wrong(self):
        """Test ampacity validation with wrong value"""
        valid, msg = validate_ampacity_claim(
            wire_size_mm2=2.5,
            claimed_ampacity_a=30,  # Wrong
            insulation=CableInsulation.THW,
            in_conduit=True
        )
        assert not valid
        assert "30" in msg
        
    def test_breaker_selection_80_percent(self):
        """Test breaker selection follows 80% rule"""
        # 18A load: 18/0.8 = 22.5 → 25A breaker
        assert get_correct_breaker(18) == 25
        # 16A load: 16/0.8 = 20 → 20A breaker
        assert get_correct_breaker(16) == 20
        
    def test_derating_factor_grouping(self):
        """Test derating factor for conductor grouping"""
        # 6 conductors = 0.8
        factor = get_derating_factor("conductor_grouping", num_conductors=6)
        assert factor == 0.8
        
    def test_device_code_validation(self):
        """Test device code exists in catalog"""
        assert is_valid_device_code("HEATER-3500W")
        assert is_valid_device_code("AC-12000BTU")
        assert not is_valid_device_code("FAKE-DEVICE")
        
    def test_standard_limits(self):
        """Test standard limits are defined"""
        assert STANDARD_LIMITS["max_voltage_drop_branch_pct"] == 3.0
        assert STANDARD_LIMITS["max_ground_resistance_ohm"] == 5.0


# =============================================================================
# UNIT TESTS - Layer 0 Assertions
# =============================================================================

class TestLayer0:
    """Unit tests for Layer 0 assertions"""
    
    def test_valid_response(self):
        """Test Layer 0 passes for valid response"""
        valid_response = {
            "answer": "THW 2.5mm² มีพิกัดกระแส 24 แอมป์",
            "sources": [{"file": "source.md", "section": "1.1", "content": "Source text"}],
            "confidence": "High",
            "grounding_status": "grounded",
            "metadata": {
                "llm_model": "gemini-2.5-flash-lite",
                "retrieved_docs": ["doc1", "doc2", "doc3"]
            }
        }
        result = validate_response_dict(valid_response)
        assert result.verdict == Layer0Verdict.PASS
        
    def test_missing_sources(self):
        """Test Layer 0 fails for missing sources"""
        response = {
            "answer": "Some answer",
            "sources": [],  # Empty
            "confidence": "High",
            "grounding_status": "grounded",
            "metadata": {"llm_model": "test", "retrieved_docs": 0}
        }
        result = validate_response_dict(response, min_sources=1)
        assert result.verdict == Layer0Verdict.HARD_FAIL
        
    def test_invalid_confidence(self):
        """Test Layer 0 fails for invalid confidence"""
        response = {
            "answer": "Some answer",
            "sources": [{"content": "x", "metadata": {}}],
            "confidence": "Maybe",  # Invalid
            "grounding_status": "grounded",
            "metadata": {"llm_model": "test", "retrieved_docs": 1}
        }
        result = validate_response_dict(response)
        assert result.verdict == Layer0Verdict.HARD_FAIL
        
    def test_empty_answer(self):
        """Test Layer 0 fails for empty answer"""
        response = {
            "answer": "",
            "sources": [{"content": "x", "metadata": {}}],
            "confidence": "High",
            "grounding_status": "grounded",
            "metadata": {"llm_model": "test", "retrieved_docs": 1}
        }
        result = validate_response_dict(response)
        assert result.verdict == Layer0Verdict.HARD_FAIL


# =============================================================================
# UNIT TESTS - Layer 1 Rule-Based
# =============================================================================

class TestLayer1:
    """Unit tests for Layer 1 rule-based checks"""
    
    def test_parse_ampacity_thai(self):
        """Test parsing ampacity from Thai text"""
        from .layer1_rules import parse_ampacity_from_answer
        
        answer = "สาย THW 2.5 ตร.มม. มีพิกัดกระแส 24 แอมป์"
        parsed = parse_ampacity_from_answer(answer)
        assert parsed is not None
        assert parsed.value == 24
        
    def test_parse_ampacity_english(self):
        """Test parsing ampacity from English text"""
        from .layer1_rules import parse_ampacity_from_answer
        
        answer = "THW 2.5mm² has an ampacity of 24A"
        parsed = parse_ampacity_from_answer(answer)
        assert parsed is not None
        assert parsed.value == 24
        
    def test_parse_voltage_drop(self):
        """Test parsing voltage drop percentage"""
        from .layer1_rules import parse_voltage_drop_from_answer
        
        answer = "แรงดันตก 2.5% ซึ่งไม่เกิน 3%"
        parsed = parse_voltage_drop_from_answer(answer)
        assert parsed is not None
        assert parsed.value == 2.5
        
    def test_parse_breaker_rating(self):
        """Test parsing breaker rating"""
        from .layer1_rules import parse_breaker_rating_from_answer
        
        answer = "ควรใช้เบรกเกอร์ 25A สำหรับโหลดนี้"
        parsed = parse_breaker_rating_from_answer(answer)
        assert parsed is not None
        assert parsed.value == 25
        
    def test_layer1_ampacity_correct(self):
        """Test Layer 1 passes for correct ampacity"""
        answer = "THW 2.5mm² มีพิกัดกระแส 24 แอมป์ ตามมาตรฐาน วสท."
        sources = [{"content": "วสท. ตาราง 5-20"}]
        
        result = run_layer1(
            answer=answer,
            sources=sources,
            test_case_type="ampacity",
            ground_truth_params={
                "wire_size_mm2": 2.5,
                "insulation": "THW",
                "in_conduit": True,
                "tolerance_percent": 5.0
            }
        )
        
        assert result.verdict == Layer1Verdict.PASS
        
    def test_layer1_ampacity_wrong(self):
        """Test Layer 1 fails for wrong ampacity"""
        answer = "THW 2.5mm² มีพิกัดกระแส 30 แอมป์"  # Wrong
        sources = [{"content": "test"}]
        
        result = run_layer1(
            answer=answer,
            sources=sources,
            test_case_type="ampacity",
            ground_truth_params={
                "wire_size_mm2": 2.5,
                "insulation": "THW",
                "in_conduit": True,
                "tolerance_percent": 5.0
            }
        )
        
        assert result.verdict == Layer1Verdict.HARD_FAIL


# =============================================================================
# UNIT TESTS - Layer 2 Mock
# =============================================================================

class TestLayer2Mock:
    """Unit tests for Layer 2 mock evaluation"""
    
    def test_mock_good_answer(self):
        """Test mock evaluates good answer as GOOD"""
        answer = """
        สาย THW ขนาด 2.5 ตร.มม. เมื่อเดินในท่อร้อยสายมีพิกัดกระแสไฟฟ้า 24 แอมป์
        ตามมาตรฐาน วสท. ตาราง 5-20 ค่านี้เป็นค่าสำหรับสภาวะปกติที่อุณหภูมิ 40°C
        ถ้าจะใช้งานที่อุณหภูมิสูงกว่านี้ต้องใช้ตัวคูณลดค่ากระแส
        """
        sources = [{"content": "ตาราง 5-20 THW 2.5mm² = 24A"}]
        
        result = mock_evaluate(
            question="THW 2.5mm² พิกัดกระแสเท่าไหร่",
            answer=answer,
            sources=sources,
            expected_language="thai"
        )
        
        assert result.evaluation.answer_quality in ["GOOD", "OK"]
        
    def test_mock_short_answer(self):
        """Test mock evaluates short answer as BROKEN"""
        answer = "24A"
        sources = [{"content": "test"}]
        
        result = mock_evaluate(
            question="อะไร",
            answer=answer,
            sources=sources,
            expected_language="thai"
        )
        
        assert result.evaluation.answer_quality == "BROKEN"
        
    def test_mock_language_mismatch(self):
        """Test mock detects language mismatch"""
        answer = "The ampacity is 24A for THW 2.5mm² cable in conduit."
        sources = [{"content": "test"}]
        
        result = mock_evaluate(
            question="THW 2.5 พิกัดกระแสเท่าไหร่",
            answer=answer,
            sources=sources,
            expected_language="thai"  # Expected Thai but got English
        )
        
        assert result.evaluation.language_ok == "NO"


# =============================================================================
# UNIT TESTS - Test Case Utilities
# =============================================================================

class TestTestCaseUtils:
    """Unit tests for test case utilities"""
    
    def test_check_should_refuse(self):
        """Test refusal detection"""
        assert check_should_refuse("ขออภัย คำถามนี้ไม่เกี่ยวข้องกับไฟฟ้า")
        assert check_should_refuse("Sorry, this is outside my scope")
        assert not check_should_refuse("พิกัดกระแส 24A")
        
    def test_check_asks_clarification(self):
        """Test clarification request detection"""
        assert check_asks_clarification("ต้องการข้อมูลเพิ่มเติมเกี่ยวกับขนาดพื้นที่")
        assert check_asks_clarification("Please specify the building type")
        assert not check_asks_clarification("พิกัดกระแส 24A")
        
    def test_check_language_thai(self):
        """Test Thai language detection"""
        assert check_language_match("พิกัดกระแส 24 แอมป์", "thai")
        assert not check_language_match("The ampacity is 24A", "thai")
        
    def test_check_language_english(self):
        """Test English language detection"""
        assert check_language_match("The ampacity is 24A", "english")
        assert not check_language_match("พิกัดกระแส 24 แอมป์", "english")
        
    def test_all_test_cases_have_ground_truth(self):
        """Verify all engineering test cases have ground truth reference"""
        engineering_categories = {
            QACaseCategory.AMPACITY,
            QACaseCategory.VOLTAGE_DROP,
            QACaseCategory.DERATING,
            QACaseCategory.BREAKER,
            QACaseCategory.CATALOG,
            QACaseCategory.RCD,
        }
        
        for tc in TEST_CASES:
            if tc.category in engineering_categories:
                # Should have ground truth params
                assert tc.ground_truth_params is not None, f"{tc.id} missing ground_truth_params"


# =============================================================================
# INTEGRATION TESTS (require running API)
# =============================================================================

@pytest.mark.integration
class TestIntegration:
    """Integration tests that require a running API"""
    
    @pytest.mark.asyncio
    async def test_api_connectivity(self, api_url):
        """Test that API is reachable"""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(api_url.replace("/ask", "/health"))
                # Accept 200 or 404 (means server is running)
                assert response.status_code in [200, 404], "API not reachable"
        except httpx.ConnectError:
            pytest.skip("API not running - skipping integration test")
    
    @pytest.mark.asyncio
    async def test_thw_ampacity_query(self, api_url, use_mock_l2, project_id):
        """Test Q-THW-AMPACITY-EXACT case"""
        from .harness import run_single_test
        
        test_case = get_test_case_by_id("Q-THW-AMPACITY-EXACT")
        
        try:
            result = await run_single_test(
                test_case=test_case,
                api_url=api_url,
                use_mock_l2=use_mock_l2,
                project_id=project_id
            )
            
            # Check that we got a response
            assert result.layer0_result is not None
            
            # If Layer 0 passed, check the verdict
            if result.layer0_result["verdict"] == "PASS":
                # We should at least get a non-HARD-FAIL for correct answer
                assert result.final_verdict.value in ["PASS", "SOFT-FAIL"]
                
        except Exception as e:
            if "Connection" in str(e):
                pytest.skip("API not running - skipping integration test")
            raise


# =============================================================================
# PARAMETRIZED TESTS FOR ALL 12 CASES
# =============================================================================

@pytest.mark.integration
@pytest.mark.parametrize("test_case_id", [tc.id for tc in TEST_CASES])
class TestAllCases:
    """Run all 12 test cases"""
    
    @pytest.mark.asyncio
    async def test_case(self, test_case_id, api_url, use_mock_l2, project_id):
        """Run a single test case through the harness"""
        from .harness import run_single_test
        
        test_case = get_test_case_by_id(test_case_id)
        
        try:
            result = await run_single_test(
                test_case=test_case,
                api_url=api_url,
                use_mock_l2=use_mock_l2,
                project_id=project_id
            )
            
            # Log result for debugging
            print(f"\n{test_case_id}: {result.final_verdict.value}")
            if result.error:
                print(f"  Error: {result.error}")
            
            # For now, we just check that we got a result
            # In production, you might want stricter assertions
            assert result.final_verdict is not None
            
        except Exception as e:
            if "Connection" in str(e):
                pytest.skip("API not running - skipping integration test")
            raise
