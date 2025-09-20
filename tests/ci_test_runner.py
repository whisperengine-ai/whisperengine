#!/usr/bin/env python3
"""
CI Test Runner for WhisperEngine GitHub Actions
Orchestrates different test categories: unit, integration, performance, security
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CITestRunner:
    """Main test orchestrator for CI pipeline"""
    
    def __init__(self, workspace: str = "."):
        self.workspace = Path(workspace).resolve()
        self.test_results = {
            "timestamp": time.time(),
            "workspace": str(self.workspace),
            "environment": dict(os.environ),
            "results": {},
            "summary": {},
            "success": False
        }
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests using pytest"""
        logger.info("🧪 Running unit tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "-v",
            "--tb=short",
            "--cov=src",
            "--cov-report=json:coverage.json",
            "--cov-report=term-missing",
            "--junit-xml=unit_test_results.xml"
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                cwd=self.workspace,
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "category": "unit",
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": time.time() - time.time(),
                "test_count": self._extract_test_count(result.stdout),
                "coverage_file": "coverage.json"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "category": "unit",
                "success": False,
                "error": "Test execution timed out after 5 minutes",
                "duration": 300
            }
        except Exception as e:
            return {
                "category": "unit", 
                "success": False,
                "error": str(e),
                "duration": 0
            }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        logger.info("🔗 Running integration tests...")
        
        # Set up test environment
        env = os.environ.copy()
        env.update({
            "ENV_MODE": "testing",
            "LLM_CHAT_API_URL": "http://mock-llm-server",
            "DISCORD_BOT_TOKEN": "test_token_for_ci",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "whisperengine_test",
            "REDIS_HOST": "localhost",
            "CHROMADB_HOST": "localhost"
        })
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "--junit-xml=integration_test_results.xml"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                env=env,
                timeout=600  # 10 minute timeout
            )
            
            return {
                "category": "integration",
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": time.time() - time.time(),
                "test_count": self._extract_test_count(result.stdout)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "category": "integration",
                "success": False,
                "error": "Integration tests timed out after 10 minutes",
                "duration": 600
            }
        except Exception as e:
            return {
                "category": "integration",
                "success": False,
                "error": str(e),
                "duration": 0
            }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance benchmarks"""
        logger.info("⚡ Running performance tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/performance/",
            "-v",
            "--tb=short",
            "--benchmark-json=benchmark.json",
            "--junit-xml=performance_test_results.xml"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=900  # 15 minute timeout
            )
            
            return {
                "category": "performance",
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": time.time() - time.time(),
                "test_count": self._extract_test_count(result.stdout),
                "benchmark_file": "benchmark.json"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "category": "performance",
                "success": False,
                "error": "Performance tests timed out after 15 minutes",
                "duration": 900
            }
        except Exception as e:
            return {
                "category": "performance",
                "success": False,
                "error": str(e),
                "duration": 0
            }
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests and checks"""
        logger.info("🔒 Running security tests...")
        
        security_results = []
        
        # Run security-focused pytest tests
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/security/",
            "-v",
            "--tb=short",
            "--junit-xml=security_test_results.xml"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            security_results.append({
                "tool": "pytest-security",
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            })
            
        except Exception as e:
            security_results.append({
                "tool": "pytest-security",
                "success": False,
                "error": str(e)
            })
        
        # Run bandit security linter if available
        try:
            bandit_cmd = [sys.executable, "-m", "bandit", "-r", "src/", "-f", "json"]
            bandit_result = subprocess.run(
                bandit_cmd,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            security_results.append({
                "tool": "bandit",
                "success": bandit_result.returncode == 0,
                "returncode": bandit_result.returncode,
                "stdout": bandit_result.stdout,
                "stderr": bandit_result.stderr
            })
            
        except FileNotFoundError:
            logger.warning("Bandit not available, skipping security scan")
        except Exception as e:
            security_results.append({
                "tool": "bandit",
                "success": False,
                "error": str(e)
            })
        
        overall_success = all(r.get("success", False) for r in security_results)
        
        return {
            "category": "security",
            "success": overall_success,
            "results": security_results,
            "duration": time.time() - time.time(),
            "test_count": self._extract_test_count("\n".join(r.get("stdout", "") for r in security_results))
        }
    
    def _extract_test_count(self, output: str) -> int:
        """Extract test count from pytest output"""
        try:
            # Look for patterns like "5 passed" or "3 failed, 2 passed"
            import re
            patterns = [
                r"(\d+) passed",
                r"(\d+) failed",
                r"(\d+) error",
                r"(\d+) skipped"
            ]
            
            total_tests = 0
            for pattern in patterns:
                matches = re.findall(pattern, output)
                total_tests += sum(int(match) for match in matches)
            
            return total_tests
        except Exception:
            return 0
    
    def run_category(self, category: str) -> Dict[str, Any]:
        """Run tests for specified category"""
        category_methods = {
            "unit": self.run_unit_tests,
            "integration": self.run_integration_tests, 
            "performance": self.run_performance_tests,
            "security": self.run_security_tests
        }
        
        if category not in category_methods:
            raise ValueError(f"Unknown test category: {category}")
        
        logger.info(f"🚀 Starting {category} tests...")
        start_time = time.time()
        
        try:
            result = category_methods[category]()
            result["duration"] = time.time() - start_time
            
            logger.info(f"✅ {category} tests completed in {result['duration']:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ {category} tests failed: {e}")
            return {
                "category": category,
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def save_report(self, report_path: str, results: Dict[str, Any]):
        """Save test results to JSON report"""
        try:
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"📄 Test report saved to {report_path}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

def main():
    parser = argparse.ArgumentParser(description="CI Test Runner for WhisperEngine")
    parser.add_argument("--category", required=True, 
                      choices=["unit", "integration", "performance", "security"],
                      help="Test category to run")
    parser.add_argument("--report", default="test_report.json",
                      help="Output file for test report")
    parser.add_argument("--workspace", default=".",
                      help="Workspace directory")
    
    args = parser.parse_args()
    
    runner = CITestRunner(workspace=args.workspace)
    
    try:
        results = runner.run_category(args.category)
        runner.save_report(args.report, results)
        
        # Print summary
        if results["success"]:
            logger.info(f"🎉 {args.category} tests PASSED")
            sys.exit(0)
        else:
            logger.error(f"💥 {args.category} tests FAILED")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()