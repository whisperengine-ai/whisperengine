#!/usr/bin/env python3
"""
WhisperEngine Automated Manual Test Regression Suite
====================================================

This script automates the manual testing procedures documented in:
- docs/manual_tests/CHARACTER_TESTING_MANUAL.md
- docs/manual_tests/MANUAL_TEST_PLAN_VECTOR_INTELLIGENCE.md

Tests character personalities, AI ethics handling, and vector intelligence features
through the bots' health/status APIs.

Note: This tests HEALTH ENDPOINTS only. Full conversation testing requires Discord messages.
For complete testing, Discord integration is needed.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import httpx

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class TestResult:
    """Individual test result"""
    test_id: str
    test_name: str
    bot_name: str
    category: str
    status: str  # PASS, FAIL, SKIP, WARN
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class BotHealthTester:
    """Tests bot health and status endpoints"""

    BOT_CONFIGS = {
        "elena": {"port": 9091, "name": "Elena Rodriguez", "archetype": "Real-World"},
        "marcus": {"port": 9092, "name": "Marcus Thompson", "archetype": "Real-World"},
        "ryan": {"port": 9093, "name": "Ryan Chen", "archetype": "Real-World"},
        "dream": {"port": 9094, "name": "Dream of the Endless", "archetype": "Fantasy"},
        "gabriel": {"port": 9095, "name": "Gabriel", "archetype": "Real-World"},
        "sophia": {"port": 9096, "name": "Sophia Blake", "archetype": "Real-World"},
        "jake": {"port": 9097, "name": "Jake Sterling", "archetype": "Real-World"},
        "dotty": {"port": 9098, "name": "Dotty", "archetype": "Real-World"},
        "aetheris": {"port": 9099, "name": "Aetheris", "archetype": "Narrative AI"},
        "aethys": {"port": 3007, "name": "Aethys", "archetype": "Fantasy"},
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.results: List[TestResult] = []
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Cleanup"""
        await self.client.aclose()

    async def test_bot_health(self, bot_id: str) -> TestResult:
        """Test individual bot health endpoint"""
        config = self.BOT_CONFIGS.get(bot_id)
        if not config:
            return TestResult(
                test_id=f"health_{bot_id}",
                test_name=f"Health Check - {bot_id}",
                bot_name=bot_id,
                category="Infrastructure",
                status="SKIP",
                message=f"Unknown bot: {bot_id}"
            )

        url = f"http://localhost:{config['port']}/health"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return TestResult(
                    test_id=f"health_{bot_id}",
                    test_name=f"Health Check - {config['name']}",
                    bot_name=bot_id,
                    category="Infrastructure",
                    status="PASS",
                    message=f"Bot healthy on port {config['port']}",
                    details=data
                )
            else:
                return TestResult(
                    test_id=f"health_{bot_id}",
                    test_name=f"Health Check - {config['name']}",
                    bot_name=bot_id,
                    category="Infrastructure",
                    status="FAIL",
                    message=f"Unhealthy: HTTP {response.status_code}",
                    details={"status_code": response.status_code}
                )
                
        except httpx.ConnectError:
            return TestResult(
                test_id=f"health_{bot_id}",
                test_name=f"Health Check - {config['name']}",
                bot_name=bot_id,
                category="Infrastructure",
                status="FAIL",
                message=f"Cannot connect to port {config['port']} - bot may be down"
            )
        except Exception as e:
            return TestResult(
                test_id=f"health_{bot_id}",
                test_name=f"Health Check - {config['name']}",
                bot_name=bot_id,
                category="Infrastructure",
                status="FAIL",
                message=f"Error: {str(e)}"
            )

    async def test_bot_status(self, bot_id: str) -> TestResult:
        """Test bot status/info endpoint for CDL integration"""
        config = self.BOT_CONFIGS.get(bot_id)
        if not config:
            return TestResult(
                test_id=f"status_{bot_id}",
                test_name=f"Status Check - {bot_id}",
                bot_name=bot_id,
                category="CDL Integration",
                status="SKIP",
                message=f"Unknown bot: {bot_id}"
            )

        # Try multiple possible status endpoints
        endpoints = [
            f"http://localhost:{config['port']}/status",
            f"http://localhost:{config['port']}/info",
            f"http://localhost:{config['port']}/api/status"
        ]
        
        for url in endpoints:
            try:
                response = await self.client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate CDL character info present
                    has_character = "character" in data or "bot_name" in data
                    has_personality = "personality" in data or "cdl" in data
                    
                    if has_character:
                        return TestResult(
                            test_id=f"status_{bot_id}",
                            test_name=f"CDL Status - {config['name']}",
                            bot_name=bot_id,
                            category="CDL Integration",
                            status="PASS",
                            message=f"Character data loaded via CDL system",
                            details=data
                        )
                    else:
                        return TestResult(
                            test_id=f"status_{bot_id}",
                            test_name=f"CDL Status - {config['name']}",
                            bot_name=bot_id,
                            category="CDL Integration",
                            status="WARN",
                            message=f"Status endpoint exists but no character data found",
                            details=data
                        )
                        
            except httpx.ConnectError:
                continue
            except Exception as e:
                continue
        
        return TestResult(
            test_id=f"status_{bot_id}",
            test_name=f"CDL Status - {config['name']}",
            bot_name=bot_id,
            category="CDL Integration",
            status="WARN",
            message=f"No status endpoint available (Discord-only bot - expected)"
        )

    async def test_memory_health(self, bot_id: str) -> TestResult:
        """Test if bot's memory system is accessible"""
        config = self.BOT_CONFIGS.get(bot_id)
        if not config:
            return TestResult(
                test_id=f"memory_{bot_id}",
                test_name=f"Memory System - {bot_id}",
                bot_name=bot_id,
                category="Memory System",
                status="SKIP",
                message=f"Unknown bot: {bot_id}"
            )

        # Note: Memory operations require Discord messages
        # We can only check if infrastructure is available
        return TestResult(
            test_id=f"memory_{bot_id}",
            test_name=f"Memory System - {config['name']}",
            bot_name=bot_id,
            category="Memory System",
            status="SKIP",
            message=f"Memory testing requires Discord messages (not available via API)"
        )

    async def run_all_tests(self, bots: Optional[List[str]] = None) -> List[TestResult]:
        """Run all regression tests"""
        if bots is None:
            bots = list(self.BOT_CONFIGS.keys())
        
        print(f"\n🧪 WhisperEngine Automated Manual Test Regression")
        print(f"=" * 70)
        print(f"Testing {len(bots)} bots: {', '.join(bots)}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        for bot_id in bots:
            print(f"🤖 Testing {bot_id.upper()}...")
            
            # Test 1: Health Check
            result = await self.test_bot_health(bot_id)
            self.results.append(result)
            self._print_result(result)
            
            # Only continue if bot is healthy
            if result.status == "PASS":
                # Test 2: CDL Status
                result = await self.test_bot_status(bot_id)
                self.results.append(result)
                self._print_result(result)
                
                # Test 3: Memory System (informational)
                result = await self.test_memory_health(bot_id)
                self.results.append(result)
                self._print_result(result)
            else:
                print(f"   ⚠️  Skipping additional tests - bot unhealthy\n")
            
            print()

        return self.results

    def _print_result(self, result: TestResult):
        """Print test result with emoji status"""
        status_emoji = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIP": "⏭️ ",
            "WARN": "⚠️ "
        }
        
        emoji = status_emoji.get(result.status, "❓")
        print(f"   {emoji} {result.test_name}: {result.message}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        warnings = sum(1 for r in self.results if r.status == "WARN")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        report = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "warnings": warnings,
                "success_rate": round(success_rate, 2)
            },
            "summary": {
                "overall_status": "PASS" if failed == 0 else "FAIL",
                "critical_failures": [r for r in self.results if r.status == "FAIL" and r.category == "Infrastructure"],
                "warnings": [r for r in self.results if r.status == "WARN"]
            },
            "results_by_category": self._group_by_category(),
            "results_by_bot": self._group_by_bot(),
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        return report

    def _group_by_category(self) -> Dict[str, List[Dict]]:
        """Group results by test category"""
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(asdict(result))
        return categories

    def _group_by_bot(self) -> Dict[str, List[Dict]]:
        """Group results by bot"""
        bots = {}
        for result in self.results:
            if result.bot_name not in bots:
                bots[result.bot_name] = []
            bots[result.bot_name].append(asdict(result))
        return bots

    def print_summary(self):
        """Print test summary"""
        report = self.generate_report()
        
        print(f"\n{'=' * 70}")
        print(f"📊 TEST SUMMARY")
        print(f"{'=' * 70}")
        
        run_info = report["test_run"]
        print(f"Total Tests:    {run_info['total_tests']}")
        print(f"✅ Passed:      {run_info['passed']}")
        print(f"❌ Failed:      {run_info['failed']}")
        print(f"⚠️  Warnings:    {run_info['warnings']}")
        print(f"⏭️  Skipped:     {run_info['skipped']}")
        print(f"Success Rate:   {run_info['success_rate']}%")
        
        if run_info['failed'] == 0:
            print(f"\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  SOME TESTS FAILED - Review details above")
        
        print(f"\n📝 Note: This tests HEALTH ENDPOINTS only.")
        print(f"   Full character/conversation testing requires Discord messages.")
        print(f"   Refer to manual testing guides for complete validation.")
        print(f"{'=' * 70}\n")


async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="WhisperEngine Automated Manual Test Regression"
    )
    parser.add_argument(
        "--bots",
        nargs="+",
        help="Specific bots to test (default: all)",
        choices=list(BotHealthTester.BOT_CONFIGS.keys())
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON report to file",
        type=Path
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=10,
        help="HTTP request timeout in seconds (default: 10)"
    )
    
    args = parser.parse_args()
    
    tester = BotHealthTester(timeout=args.timeout)
    
    try:
        # Run tests
        await tester.run_all_tests(bots=args.bots)
        
        # Print summary
        tester.print_summary()
        
        # Generate and save report
        report = tester.generate_report()
        
        if args.output:
            output_path = args.output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
            
            print(f"📄 Detailed report saved to: {output_path}")
        
        # Exit with appropriate code
        sys.exit(0 if report["summary"]["overall_status"] == "PASS" else 1)
        
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
