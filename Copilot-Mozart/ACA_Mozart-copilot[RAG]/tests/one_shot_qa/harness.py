"""
Test Harness Runner
===================
เจ้าค่ะนายท่าน นี่คือ Harness ที่รัน 3 Layer ครบ และ output PASS/SOFT-FAIL/HARD-FAIL

Usage:
    python -m tests.one_shot_qa.harness --api-url http://localhost:8080/api/v1/ask
    python -m tests.one_shot_qa.harness --api-url http://localhost:8080/api/v1/ask --case Q-THW-AMPACITY-EXACT
    python -m tests.one_shot_qa.harness --api-url http://localhost:8080/api/v1/ask --mock-l2
"""

import asyncio
import argparse
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

from .layer0_assertions import run_layer0, Layer0Verdict, Layer0Result
from .layer1_rules import run_layer1, Layer1Verdict, Layer1Result
from .layer2_judge import run_layer2, Layer2Verdict, Layer2Result
from .test_cases import (
    TEST_CASES, 
    TestCase, 
    get_test_case_by_id, 
    check_should_refuse,
    check_asks_clarification,
    check_language_match
)


class FinalVerdict(str, Enum):
    """Final verdict for a test case"""
    PASS = "PASS"
    SOFT_FAIL = "SOFT-FAIL"
    HARD_FAIL = "HARD-FAIL"
    SKIPPED = "SKIPPED"


@dataclass
class TestCaseResult:
    """Complete result for a single test case"""
    test_case_id: str
    test_case_name: str
    question: str
    final_verdict: FinalVerdict
    
    layer0_result: Optional[Dict[str, Any]] = None
    layer1_result: Optional[Dict[str, Any]] = None
    layer2_result: Optional[Dict[str, Any]] = None
    
    special_checks: Dict[str, bool] = field(default_factory=dict)
    
    answer: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    
    execution_time_ms: float = 0
    timestamp: str = ""
    
    error: Optional[str] = None


@dataclass
class HarnessReport:
    """Complete report from harness run"""
    run_id: str
    timestamp: str
    api_url: str
    total_cases: int
    passed: int
    soft_fail: int
    hard_fail: int
    skipped: int
    
    results: List[TestCaseResult]
    
    summary: str = ""


def determine_final_verdict(
    l0: Layer0Result,
    l1: Optional[Layer1Result],
    l2: Optional[Layer2Result],
    test_case: TestCase,
    answer: str
) -> FinalVerdict:
    """
    Determine final verdict from all three layers.
    
    Priority:
    1. Layer 0 HARD-FAIL → HARD-FAIL
    2. Special case checks (refuse, clarification, language)
    3. Layer 1 HARD-FAIL → HARD-FAIL
    4. Layer 2 HARD-FAIL → HARD-FAIL
    5. Any SOFT-FAIL → SOFT-FAIL
    6. All PASS → PASS
    """
    # Layer 0 is always critical
    if l0.verdict == Layer0Verdict.HARD_FAIL:
        return FinalVerdict.HARD_FAIL
    
    # Special case checks
    if test_case.should_refuse:
        if not check_should_refuse(answer):
            return FinalVerdict.SOFT_FAIL  # Should have refused but didn't
    
    if test_case.should_ask_clarification:
        if not check_asks_clarification(answer):
            return FinalVerdict.SOFT_FAIL  # Should have asked but didn't
    
    if not check_language_match(answer, test_case.expected_language):
        return FinalVerdict.SOFT_FAIL  # Language mismatch
    
    # Layer 1 check
    if l1 is not None and l1.verdict == Layer1Verdict.HARD_FAIL:
        return FinalVerdict.HARD_FAIL
    
    # Layer 2 check
    if l2 is not None and l2.verdict == Layer2Verdict.HARD_FAIL:
        return FinalVerdict.HARD_FAIL
    
    # Check for soft failures
    soft_fails = []
    if l1 is not None and l1.verdict == Layer1Verdict.SOFT_FAIL:
        soft_fails.append("layer1")
    if l2 is not None and l2.verdict == Layer2Verdict.SOFT_FAIL:
        soft_fails.append("layer2")
    
    if soft_fails:
        return FinalVerdict.SOFT_FAIL
    
    return FinalVerdict.PASS


async def run_single_test(
    test_case: TestCase,
    api_url: str,
    use_mock_l2: bool = False,
    project_id: Optional[str] = None,
    location: str = "us-central1"
) -> TestCaseResult:
    """
    Run all three layers for a single test case.
    
    Args:
        test_case: The test case to run
        api_url: URL of the /api/v1/ask endpoint
        use_mock_l2: Use mock evaluation for Layer 2
        project_id: GCP project ID for Gemini
        location: GCP location
        
    Returns:
        TestCaseResult
    """
    start_time = datetime.now()
    
    result = TestCaseResult(
        test_case_id=test_case.id,
        test_case_name=test_case.name,
        question=test_case.question,
        final_verdict=FinalVerdict.SKIPPED,
        timestamp=start_time.isoformat()
    )
    
    try:
        # ===== LAYER 0 =====
        l0_result = await run_layer0(
            api_url=api_url,
            query=test_case.question,
            min_sources=test_case.expected_min_sources,
            timeout=60.0
        )
        
        result.layer0_result = {
            "verdict": l0_result.verdict.value,
            "checks": l0_result.checks,
            "errors": l0_result.errors
        }
        
        if l0_result.verdict == Layer0Verdict.HARD_FAIL:
            result.final_verdict = FinalVerdict.HARD_FAIL
            result.error = "; ".join(l0_result.errors)
            return result
        
        # Extract answer and sources
        if l0_result.response_data is None:
            result.final_verdict = FinalVerdict.HARD_FAIL
            result.error = "No response data from Layer 0"
            return result
            
        answer = l0_result.response_data.get("answer", "")
        sources = l0_result.response_data.get("sources", [])
        
        result.answer = answer
        result.sources = sources
        
        # ===== SPECIAL CHECKS =====
        special_checks = {}
        
        if test_case.should_refuse:
            special_checks["should_refuse"] = check_should_refuse(answer)
        
        if test_case.should_ask_clarification:
            special_checks["asks_clarification"] = check_asks_clarification(answer)
        
        special_checks["language_match"] = check_language_match(answer, test_case.expected_language)
        
        result.special_checks = special_checks
        
        # ===== LAYER 1 =====
        # Skip Layer 1 for out-of-scope and incomplete spec cases
        l1_result = None
        if test_case.category.value not in ["out_of_scope", "incomplete"]:
            # API returns sources with 'file' and 'section', not 'content'
            # For Layer 1, we need to pass source info for validation
            source_dicts = [{"file": s.get("file", ""), "section": s.get("section", "")} for s in sources]
            l1_result = run_layer1(
                answer=answer,
                sources=source_dicts,
                test_case_type=test_case.layer1_type,
                ground_truth_params=test_case.ground_truth_params
            )
            
            result.layer1_result = {
                "verdict": l1_result.verdict.value,
                "validations": [
                    {
                        "field": v.field_name,
                        "expected": str(v.expected),
                        "actual": str(v.actual),
                        "passed": v.passed,
                        "message": v.message
                    }
                    for v in l1_result.validations
                ],
                "errors": l1_result.errors,
                "warnings": l1_result.warnings
            }
        
        # ===== LAYER 2 =====
        # API returns sources with 'file' and 'section', pass for semantic judge
        source_dicts = [
            {
                "file": s.get("file", ""),
                "section": s.get("section", ""),
                "content": s.get("content", "")
            }
            for s in sources
        ]
        l2_result = await run_layer2(
            question=test_case.question,
            answer=answer,
            sources=source_dicts,
            expected_language=test_case.expected_language,
            use_mock=use_mock_l2,
            project_id=project_id,
            location=location
        )
        
        if l2_result.evaluation:
            result.layer2_result = {
                "verdict": l2_result.verdict.value,
                "answer_quality": l2_result.evaluation.answer_quality,
                "uses_docs": l2_result.evaluation.uses_docs,
                "logic_correct": l2_result.evaluation.logic_correct,
                "math_correct": l2_result.evaluation.math_correct,
                "language_ok": l2_result.evaluation.language_ok,
                "violations": l2_result.evaluation.violations,
                "reasoning": l2_result.evaluation.reasoning
            }
        else:
            result.layer2_result = {
                "verdict": l2_result.verdict.value,
                "error": l2_result.error
            }
        
        # ===== DETERMINE FINAL VERDICT =====
        result.final_verdict = determine_final_verdict(
            l0_result, l1_result, l2_result, test_case, answer
        )
        
    except Exception as e:
        result.final_verdict = FinalVerdict.HARD_FAIL
        result.error = f"Exception: {str(e)}"
    
    end_time = datetime.now()
    result.execution_time_ms = (end_time - start_time).total_seconds() * 1000
    
    return result


async def run_harness(
    api_url: str,
    test_case_ids: Optional[List[str]] = None,
    use_mock_l2: bool = False,
    project_id: Optional[str] = None,
    location: str = "us-central1",
    output_dir: Optional[str] = None
) -> HarnessReport:
    """
    Run the full test harness.
    
    Args:
        api_url: URL of the /api/v1/ask endpoint
        test_case_ids: List of specific test case IDs to run, or None for all
        use_mock_l2: Use mock evaluation for Layer 2
        project_id: GCP project ID
        location: GCP location
        output_dir: Directory to save report
        
    Returns:
        HarnessReport
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Select test cases
    if test_case_ids:
        cases = [get_test_case_by_id(cid) for cid in test_case_ids]
        cases = [c for c in cases if c is not None]
    else:
        cases = TEST_CASES
    
    print(f"\n{'='*60}")
    print(f"ACA Mozart RAG - One-Shot QA Harness")
    print(f"{'='*60}")
    print(f"Run ID: {run_id}")
    print(f"API URL: {api_url}")
    print(f"Test Cases: {len(cases)}")
    print(f"Layer 2: {'Mock' if use_mock_l2 else 'Gemini'}")
    print(f"{'='*60}\n")
    
    results: List[TestCaseResult] = []
    
    for i, tc in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {tc.id}: {tc.name}")
        print(f"    Question: {tc.question[:60]}...")
        
        result = await run_single_test(
            test_case=tc,
            api_url=api_url,
            use_mock_l2=use_mock_l2,
            project_id=project_id,
            location=location
        )
        
        results.append(result)
        
        verdict_color = {
            FinalVerdict.PASS: "\033[92m",      # Green
            FinalVerdict.SOFT_FAIL: "\033[93m", # Yellow
            FinalVerdict.HARD_FAIL: "\033[91m", # Red
            FinalVerdict.SKIPPED: "\033[90m"    # Gray
        }
        reset = "\033[0m"
        
        print(f"    Verdict: {verdict_color[result.final_verdict]}{result.final_verdict.value}{reset}")
        print(f"    Time: {result.execution_time_ms:.0f}ms")
        
        if result.error:
            print(f"    Error: {result.error[:100]}")
        print()
    
    # Build report
    report = HarnessReport(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        api_url=api_url,
        total_cases=len(results),
        passed=sum(1 for r in results if r.final_verdict == FinalVerdict.PASS),
        soft_fail=sum(1 for r in results if r.final_verdict == FinalVerdict.SOFT_FAIL),
        hard_fail=sum(1 for r in results if r.final_verdict == FinalVerdict.HARD_FAIL),
        skipped=sum(1 for r in results if r.final_verdict == FinalVerdict.SKIPPED),
        results=results
    )
    
    # Build summary
    report.summary = f"""
{'='*60}
SUMMARY
{'='*60}
Total: {report.total_cases}
✅ PASS: {report.passed}
⚠️  SOFT-FAIL: {report.soft_fail}
❌ HARD-FAIL: {report.hard_fail}
⏭️  SKIPPED: {report.skipped}

Pass Rate: {report.passed / report.total_cases * 100:.1f}%
{'='*60}
"""
    
    print(report.summary)
    
    # Save report if output_dir specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        report_file = output_path / f"harness_report_{run_id}.json"
        
        # Convert results to dict for JSON serialization
        report_dict = {
            "run_id": report.run_id,
            "timestamp": report.timestamp,
            "api_url": report.api_url,
            "total_cases": report.total_cases,
            "passed": report.passed,
            "soft_fail": report.soft_fail,
            "hard_fail": report.hard_fail,
            "skipped": report.skipped,
            "summary": report.summary,
            "results": [
                {
                    "test_case_id": r.test_case_id,
                    "test_case_name": r.test_case_name,
                    "question": r.question,
                    "final_verdict": r.final_verdict.value,
                    "layer0_result": r.layer0_result,
                    "layer1_result": r.layer1_result,
                    "layer2_result": r.layer2_result,
                    "special_checks": r.special_checks,
                    "answer": r.answer[:500] if r.answer else None,
                    "execution_time_ms": r.execution_time_ms,
                    "error": r.error
                }
                for r in report.results
            ]
        }
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        print(f"Report saved to: {report_file}")
    
    return report


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ACA Mozart RAG - One-Shot QA Harness"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8080/api/v1/ask",
        help="URL of the /api/v1/ask endpoint"
    )
    parser.add_argument(
        "--case",
        type=str,
        action="append",
        dest="cases",
        help="Specific test case ID to run (can be used multiple times)"
    )
    parser.add_argument(
        "--mock-l2",
        action="store_true",
        help="Use mock evaluation for Layer 2 (no LLM)"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=os.environ.get("PROJECT_ID"),
        help="GCP Project ID for Gemini"
    )
    parser.add_argument(
        "--location",
        type=str,
        default=os.environ.get("LOCATION", "us-central1"),
        help="GCP Location"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="logs/one_shot_qa",
        help="Directory to save report"
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_harness(
        api_url=args.api_url,
        test_case_ids=args.cases,
        use_mock_l2=args.mock_l2,
        project_id=args.project_id,
        location=args.location,
        output_dir=args.output_dir
    ))


if __name__ == "__main__":
    main()
