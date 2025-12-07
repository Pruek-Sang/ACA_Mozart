"""
One-Shot E2E Test Runner

Runs complete end-to-end tests covering:
- Layer 0: Infrastructure (health checks)
- Layer 1: RAG → Spec validation
- Layer 2: Spec → MCP → Calculation validation

Usage:
    python test_runner.py
    python test_runner.py --layer 1
    python test_runner.py --test-id OS-1
"""

import json
import yaml
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import sys

# Import test layers
from layer0_infra import InfraTests
from layer1_rag_spec import RagSpecTests
from layer2_mcp_calc import McpCalcTests


class TestStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


@dataclass
class TestResult:
    test_id: str
    test_name: str
    layer: int
    status: TestStatus
    duration_s: float
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class OneshotTestRunner:
    """Main test orchestrator for one-shot E2E tests."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.results: List[TestResult] = []
        
        # Initialize test layers
        self.layer0 = InfraTests(self.config)
        self.layer1 = RagSpecTests(self.config)
        self.layer2 = McpCalcTests(self.config)
        
        # Directories
        self.base_dir = Path(__file__).parent
        self.fixtures_dir = self.base_dir / "fixtures"
        self.reports_dir = self.base_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load test configuration."""
        config_file = Path(__file__).parent / config_path
        with open(config_file) as f:
            return yaml.safe_load(f)
    
    def run_all(self, layer_filter: Optional[int] = None, test_id_filter: Optional[str] = None):
        """
        Run all tests or filtered subset.
        
        Args:
            layer_filter: Run only specific layer (0, 1, or 2)
            test_id_filter: Run only specific test (e.g., "OS-1")
        """
        print("=" * 80)
        print("🚀 ACA Mozart - One-Shot E2E Test Suite")
        print("=" * 80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Config: {self.config.get('rag_endpoint', 'N/A')}\n")
        
        # Layer 0: Infrastructure
        if layer_filter is None or layer_filter == 0:
            print("\n" + "=" * 80)
            print("🔧 LAYER 0: Infrastructure Tests")
            print("=" * 80)
            self._run_layer0()
            
            # Stop if infra fails
            if any(r.status == TestStatus.FAIL for r in self.results if r.layer == 0):
                print("\n❌ Infrastructure tests failed. Stopping.")
                self._generate_report()
                return
        
        # Layer 1: RAG → Spec
        if layer_filter is None or layer_filter == 1:
            print("\n" + "=" * 80)
            print("📝 LAYER 1: RAG → Spec Validation")
            print("=" * 80)
            self._run_layer1(test_id_filter)
        
        # Layer 2: Spec → MCP → Result
        if layer_filter is None or layer_filter == 2:
            print("\n" + "=" * 80)
            print("⚙️  LAYER 2: MCP Calculation Validation")
            print("=" * 80)
            self._run_layer2(test_id_filter)
        
        # Generate report
        self._generate_report()
    
    def _run_layer0(self):
        """Run infrastructure tests."""
        tests = [
            ("RAG health check", self.layer0.test_rag_health),
            ("MCP health check", self.layer0.test_mcp_health),
            ("Knowledge base accessible", self.layer0.test_knowledge_accessible),
        ]
        
        for test_name, test_func in tests:
            result = self._execute_test(f"L0-{test_name}", test_name, 0, test_func)
            self.results.append(result)
            self._print_result(result)
    
    def _run_layer1(self, test_id_filter: Optional[str] = None):
        """Run RAG spec generation tests."""
        # Find all test cases
        test_cases = self._discover_test_cases()
        
        for test_case in test_cases:
            if test_id_filter and test_case["id"] != test_id_filter:
                continue
            
            result = self._execute_test(
                test_id=f"L1-{test_case['id']}",
                test_name=f"{test_case['id']}: RAG spec generation",
                layer=1,
                test_func=lambda tc=test_case: self.layer1.test_spec_generation(tc)
            )
            self.results.append(result)
            self._print_result(result)
    
    def _run_layer2(self, test_id_filter: Optional[str] = None):
        """Run MCP calculation tests."""
        test_cases = self._discover_test_cases()
        
        for test_case in test_cases:
            if test_id_filter and test_case["id"] != test_id_filter:
                continue
            
            result = self._execute_test(
                test_id=f"L2-{test_case['id']}",
                test_name=f"{test_case['id']}: MCP calculation",
                layer=2,
                test_func=lambda tc=test_case: self.layer2.test_calculation(tc)
            )
            self.results.append(result)
            self._print_result(result)
    
    def _discover_test_cases(self) -> List[Dict[str, Any]]:
        """Discover all test cases from fixtures."""
        prompts_dir = self.fixtures_dir / "prompts"
        test_cases = []
        
        for prompt_file in sorted(prompts_dir.glob("OS-*.txt")):
            test_id = prompt_file.stem.split('_')[0]  # e.g., "OS-1"
            
            test_cases.append({
                "id": test_id,
                "prompt_file": prompt_file.name,
                "spec_file": f"{test_id}_spec.json",
                "result_file": f"{test_id}_result.json"
            })
        
        return test_cases
    
    def _execute_test(self, test_id: str, test_name: str, layer: int, test_func) -> TestResult:
        """Execute a single test and return result."""
        start_time = datetime.now()
        
        try:
            # Run test
            success, message, details = test_func()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                test_id=test_id,
                test_name=test_name,
                layer=layer,
                status=TestStatus.PASS if success else TestStatus.FAIL,
                duration_s=duration,
                message=message,
                details=details
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                test_id=test_id,
                test_name=test_name,
                layer=layer,
                status=TestStatus.ERROR,
                duration_s=duration,
                message=f"Exception: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    def _print_result(self, result: TestResult):
        """Print test result with color."""
        status_icons = {
            TestStatus.PASS: "✅",
            TestStatus.FAIL: "❌",
            TestStatus.SKIP: "⏭️",
            TestStatus.ERROR: "💥"
        }
        
        icon = status_icons.get(result.status, "❓")
        print(f"{icon} {result.test_id}: {result.test_name}")
        print(f"   Duration: {result.duration_s:.2f}s")
        print(f"   Message: {result.message}")
        
        if result.details and result.status != TestStatus.PASS:
            print(f"   Details: {json.dumps(result.details, indent=6)}")
        print()
    
    def _generate_report(self):
        """Generate test report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f"run_{timestamp}.json"
        
        # Calculate stats
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        
        report = {
            "timestamp": timestamp,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            "config": self.config,
            "results": [asdict(r) for r in self.results]
        }
        
        # Save JSON report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total:  {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Errors: {errors} 💥")
        print(f"Pass Rate: {report['summary']['pass_rate']}")
        print(f"\nReport saved: {report_path}")
        print("=" * 80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run one-shot E2E tests")
    parser.add_argument("--layer", type=int, choices=[0, 1, 2], help="Run specific layer only")
    parser.add_argument("--test-id", help="Run specific test (e.g., OS-1)")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    
    args = parser.parse_args()
    
    runner = OnehotTestRunner(config_path=args.config)
    runner.run_all(layer_filter=args.layer, test_id_filter=args.test_id)


if __name__ == "__main__":
    main()
