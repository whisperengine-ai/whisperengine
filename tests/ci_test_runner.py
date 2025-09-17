"""
Enhanced CI/CD test runner for WhisperEngine.

Provides comprehensive testing automation with:
- Test suite organization
- Parallel test execution  
- Coverage reporting
- Performance benchmarking
- Security validation
- Multi-environment testing
"""

import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class TestCategory(Enum):
    """Test categories for organized execution"""
    UNIT = "unit"
    INTEGRATION = "integration" 
    PERFORMANCE = "performance"
    SECURITY = "security"
    ALL = "all"


class TestResult(Enum):
    """Test execution results"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestSuiteResult:
    """Results from a test suite execution"""
    category: TestCategory
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    coverage_percentage: Optional[float] = None
    performance_metrics: Optional[Dict] = None


class WhisperEngineTestRunner:
    """Comprehensive test runner for WhisperEngine"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.test_dir = workspace_root / "tests"
        self.results: List[TestSuiteResult] = []
        
    def run_test_category(self, category: TestCategory, parallel: bool = True, coverage: bool = True) -> TestSuiteResult:
        """Run tests for a specific category"""
        print(f"\\n🧪 Running {category.value} tests...")
        
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]
        
        # Add test directory
        if category == TestCategory.ALL:
            cmd.append(str(self.test_dir))
        else:
            cmd.extend(["-m", category.value])
            cmd.append(str(self.test_dir))
        
        # Add options
        cmd.extend([
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--strict-markers",  # Strict marker validation
            "--strict-config",  # Strict config validation
        ])
        
        # Add parallel execution
        if parallel:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            cmd.extend(["-n", str(min(cpu_count, 4))])  # Max 4 workers
        
        # Add coverage for unit and integration tests
        if coverage and category in [TestCategory.UNIT, TestCategory.INTEGRATION, TestCategory.ALL]:
            cmd.extend([
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=json:coverage.json",
                "--cov-fail-under=0",  # Don't fail on low coverage, just report
            ])
        
        # Add performance benchmarking for performance tests
        if category == TestCategory.PERFORMANCE:
            cmd.extend([
                "--benchmark-only",
                "--benchmark-json=benchmark.json"
            ])
        
        start_time = time.time()
        
        try:
            # Run tests
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
                check=False  # Don't raise exception on non-zero exit
            )
            
            duration = time.time() - start_time
            
            # Parse results
            output_lines = result.stdout.split('\\n')
            return self._parse_test_output(category, output_lines, duration)
            
        except subprocess.TimeoutExpired:
            print(f"❌ {category.value} tests timed out after 30 minutes")
            return TestSuiteResult(
                category=category,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0,
                errors=0,
                duration=1800
            )
        except OSError as e:
            print(f"❌ Error running {category.value} tests: {e}")
            return TestSuiteResult(
                category=category,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=time.time() - start_time
            )

    def _parse_test_output(self, category: TestCategory, output_lines: List[str], duration: float) -> TestSuiteResult:
        """Parse pytest output to extract test results"""
        total_tests = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        coverage_percentage = None
        performance_metrics = None
        
        # Parse pytest summary line
        for line in output_lines:
            if "failed" in line and "passed" in line:
                # Example: "5 failed, 10 passed, 2 skipped in 12.34s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "failed" and i > 0:
                        failed = int(parts[i-1])
                    elif part == "passed" and i > 0:
                        passed = int(parts[i-1])
                    elif part == "skipped" and i > 0:
                        skipped = int(parts[i-1])
                    elif part == "error" and i > 0:
                        errors = int(parts[i-1])
                
                total_tests = passed + failed + skipped + errors
                break
            elif "passed" in line and ("failed" not in line):
                # Example: "10 passed in 5.67s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        passed = int(parts[i-1])
                        total_tests = passed
                        break
        
        # Parse coverage information
        if category in [TestCategory.UNIT, TestCategory.INTEGRATION, TestCategory.ALL]:
            coverage_file = self.workspace_root / "coverage.json"
            if coverage_file.exists():
                try:
                    with open(coverage_file, encoding='utf-8') as f:
                        coverage_data = json.load(f)
                        coverage_percentage = coverage_data.get("totals", {}).get("percent_covered")
                except (OSError, json.JSONDecodeError, KeyError):
                    pass  # Coverage parsing failed, continue without it
        
        # Parse performance metrics
        if category == TestCategory.PERFORMANCE:
            benchmark_file = self.workspace_root / "benchmark.json"
            if benchmark_file.exists():
                try:
                    with open(benchmark_file, encoding='utf-8') as f:
                        benchmark_data = json.load(f)
                        performance_metrics = {
                            "benchmarks": len(benchmark_data.get("benchmarks", [])),
                            "machine_info": benchmark_data.get("machine_info", {})
                        }
                except (OSError, json.JSONDecodeError, KeyError):
                    pass  # Benchmark parsing failed, continue without it
        
        return TestSuiteResult(
            category=category,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            coverage_percentage=coverage_percentage,
            performance_metrics=performance_metrics
        )

    def run_comprehensive_test_suite(self, categories: Optional[List[TestCategory]] = None, parallel: bool = True) -> List[TestSuiteResult]:
        """Run comprehensive test suite across all or specified categories"""
        if categories is None:
            categories = [TestCategory.UNIT, TestCategory.INTEGRATION, TestCategory.PERFORMANCE, TestCategory.SECURITY]
        
        print("🚀 Starting WhisperEngine Comprehensive Test Suite")
        print(f"📂 Workspace: {self.workspace_root}")
        print(f"🧪 Categories: {', '.join(cat.value for cat in categories)}")
        
        results = []
        
        for category in categories:
            result = self.run_test_category(category, parallel=parallel)
            results.append(result)
            self._print_category_summary(result)
        
        self.results = results
        return results

    def _print_category_summary(self, result: TestSuiteResult):
        """Print summary for a test category"""
        status_emoji = "✅" if result.failed == 0 and result.errors == 0 else "❌"
        
        print(f"\\n{status_emoji} {result.category.value.upper()} TESTS SUMMARY")
        print(f"   Total Tests: {result.total_tests}")
        print(f"   ✅ Passed: {result.passed}")
        print(f"   ❌ Failed: {result.failed}")
        print(f"   ⏭️  Skipped: {result.skipped}")
        print(f"   🚨 Errors: {result.errors}")
        print(f"   ⏱️  Duration: {result.duration:.2f}s")
        
        if result.coverage_percentage is not None:
            print(f"   📊 Coverage: {result.coverage_percentage:.1f}%")
        
        if result.performance_metrics:
            print(f"   🏃 Benchmarks: {result.performance_metrics.get('benchmarks', 0)}")

    def generate_test_report(self, output_file: Optional[Path] = None) -> Dict:
        """Generate comprehensive test report"""
        if not self.results:
            print("⚠️  No test results available. Run tests first.")
            return {}
        
        # Calculate overall statistics
        total_tests = sum(r.total_tests for r in self.results)
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        
        # Calculate success rate
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Get coverage information
        coverage_results = [r for r in self.results if r.coverage_percentage is not None]
        avg_coverage = (
            sum(r.coverage_percentage for r in coverage_results if r.coverage_percentage is not None) / len(coverage_results) 
            if coverage_results else None
        )
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "workspace": str(self.workspace_root),
            "overall_statistics": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "errors": total_errors,
                "success_rate_percent": round(success_rate, 2),
                "total_duration_seconds": round(total_duration, 2),
                "average_coverage_percent": round(avg_coverage, 2) if avg_coverage else None
            },
            "category_results": [
                {
                    "category": r.category.value,
                    "total_tests": r.total_tests,
                    "passed": r.passed,
                    "failed": r.failed,
                    "skipped": r.skipped,
                    "errors": r.errors,
                    "duration_seconds": round(r.duration, 2),
                    "coverage_percent": round(r.coverage_percentage, 2) if r.coverage_percentage else None,
                    "performance_metrics": r.performance_metrics
                }
                for r in self.results
            ]
        }
        
        # Save report if output file specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Test report saved to: {output_file}")
        
        return report

    def print_final_summary(self):
        """Print final test suite summary"""
        if not self.results:
            print("⚠️  No test results available.")
            return
        
        report = self.generate_test_report()
        stats = report["overall_statistics"]
        
        print("\\n" + "="*60)
        print("🎯 WHISPERENGINE TEST SUITE FINAL SUMMARY")
        print("="*60)
        
        # Overall status
        if stats["failed"] == 0 and stats["errors"] == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED")
        
        print("\\n📊 OVERALL STATISTICS:")
        print(f"   Total Tests: {stats['total_tests']}")
        print(f"   ✅ Passed: {stats['passed']}")
        print(f"   ❌ Failed: {stats['failed']}")
        print(f"   ⏭️  Skipped: {stats['skipped']}")
        print(f"   🚨 Errors: {stats['errors']}")
        print(f"   📈 Success Rate: {stats['success_rate_percent']}%")
        print(f"   ⏱️  Total Duration: {stats['total_duration_seconds']}s")
        
        if stats["average_coverage_percent"]:
            print(f"   📊 Average Coverage: {stats['average_coverage_percent']}%")
        
        # Category breakdown
        print("\\n📋 CATEGORY BREAKDOWN:")
        for result in self.results:
            status = "✅" if result.failed == 0 and result.errors == 0 else "❌"
            print(f"   {status} {result.category.value.title()}: {result.passed}/{result.total_tests} passed")
        
        print("\\n" + "="*60)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="WhisperEngine Comprehensive Test Runner")
    parser.add_argument(
        "--category", 
        choices=[cat.value for cat in TestCategory],
        default="all",
        help="Test category to run (default: all)"
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Disable parallel test execution"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true", 
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "--report",
        type=str,
        help="Output file for test report (JSON format)"
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=".",
        help="Workspace root directory"
    )
    
    args = parser.parse_args()
    
    # Setup
    workspace_root = Path(args.workspace).resolve()
    if not workspace_root.exists():
        print(f"❌ Workspace directory not found: {workspace_root}")
        sys.exit(1)
    
    runner = WhisperEngineTestRunner(workspace_root)
    
    # Determine categories to run
    if args.category == "all":
        categories = [TestCategory.UNIT, TestCategory.INTEGRATION, TestCategory.PERFORMANCE, TestCategory.SECURITY]
    else:
        categories = [TestCategory(args.category)]
    
    # Run tests
    results = runner.run_comprehensive_test_suite(
        categories=categories,
        parallel=not args.no_parallel
    )
    
    # Generate report
    if args.report:
        runner.generate_test_report(Path(args.report))
    
    # Print final summary
    runner.print_final_summary()
    
    # Exit with appropriate code
    total_failures = sum(r.failed + r.errors for r in results)
    sys.exit(0 if total_failures == 0 else 1)


if __name__ == "__main__":
    main()