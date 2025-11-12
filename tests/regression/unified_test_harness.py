#!/usr/bin/env python3
"""
WhisperEngine Unified Test Harness

YAML-driven test runner that executes character, memory, and intelligence tests
from declarative test definitions. Simplifies test creation and maintenance.

Features:
- Load tests from YAML files
- Unified test execution across all test types
- Flexible filtering by bot, test type, category
- Beautiful reporting with archetype awareness
- Parallel test execution support (future)

Usage:
    # Run all tests
    python tests/regression/unified_test_harness.py
    
    # Run specific test types
    python tests/regression/unified_test_harness.py --type character
    python tests/regression/unified_test_harness.py --type memory,intelligence
    
    # Filter by bot
    python tests/regression/unified_test_harness.py --bots elena,marcus
    
    # Filter by category
    python tests/regression/unified_test_harness.py --category "AI Ethics"
    
    # Combine filters
    python tests/regression/unified_test_harness.py --type character --bots elena --category "AI Ethics"
"""

import asyncio
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import httpx
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class TestResult:
    """Unified test result"""
    test_id: str
    test_name: str
    bot_name: str
    test_type: str  # character, memory, intelligence
    category: str
    success: bool
    response: str
    matched_patterns: List[str]
    missing_patterns: List[str]
    error: Optional[str] = None


class UnifiedTestHarness:
    """YAML-driven test harness for all WhisperEngine tests"""
    
    BOT_CONFIGS = {
        "elena": {"port": 9091, "archetype": "Real-World"},
        "gabriel": {"port": 9095, "archetype": "Narrative AI"},
        "marcus": {"port": 9092, "archetype": "Real-World"},
        "jake": {"port": 9097, "archetype": "Real-World"},
        "ryan": {"port": 9093, "archetype": "Real-World"},
        "sophia": {"port": 9096, "archetype": "Real-World"},
        "dotty": {"port": 9098, "archetype": "Narrative AI"},
        "dream": {"port": 9094, "archetype": "Fantasy"},
        "aethys": {"port": 3007, "archetype": "Fantasy"},
        "aetheris": {"port": 9099, "archetype": "Narrative AI"},
        "aria": {"port": 9785, "archetype": "Narrative AI"},
    }
    
    def __init__(self, timeout: float = 60.0):
        """Initialize test harness"""
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.test_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.user_ids: Dict[str, str] = {}
        self.results: List[TestResult] = []
        
        # Test definition directory
        self.test_def_dir = Path(__file__).parent / "test_definitions"
    
    async def close(self):
        """Cleanup"""
        await self.client.aclose()
    
    def get_user_id(self, bot_name: str, test_type: str) -> str:
        """Get user ID for bot - varies by test type"""
        key = f"{bot_name}_{test_type}"
        if key not in self.user_ids:
            if test_type == "character":
                # Character tests use fresh UUIDs per run
                import uuid
                self.user_ids[key] = f"char_test_{bot_name}_{self.test_session_id}_{uuid.uuid4().hex[:8]}"
            else:
                # Memory/intelligence tests use consistent IDs
                self.user_ids[key] = f"{test_type}_test_{bot_name}_{self.test_session_id}"
        return self.user_ids[key]
    
    # ==================== TEST LOADING ====================
    
    def load_yaml_tests(self, filename: str) -> List[Dict[str, Any]]:
        """Load tests from YAML file"""
        filepath = self.test_def_dir / filename
        if not filepath.exists():
            print(f"⚠️  Warning: {filename} not found")
            return []
        
        with open(filepath, 'r') as f:
            tests = yaml.safe_load(f)
        
        return tests if tests else []
    
    def load_all_tests(
        self,
        type_filter: Optional[List[str]] = None,
        bot_filter: Optional[List[str]] = None,
        category_filter: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """Load all tests with optional filtering"""
        all_tests = {
            "character": [],
            "memory": [],
            "intelligence": []
        }
        
        # Load from YAML files
        if not type_filter or "character" in type_filter:
            all_tests["character"] = self.load_yaml_tests("character_tests.yaml")
        
        if not type_filter or "memory" in type_filter:
            all_tests["memory"] = self.load_yaml_tests("memory_tests.yaml")
        
        if not type_filter or "intelligence" in type_filter:
            all_tests["intelligence"] = self.load_yaml_tests("intelligence_tests.yaml")
        
        # Apply filters
        if bot_filter:
            for test_type in all_tests:
                all_tests[test_type] = [
                    t for t in all_tests[test_type]
                    if t.get("bot_name") in bot_filter
                ]
        
        if category_filter:
            for test_type in all_tests:
                all_tests[test_type] = [
                    t for t in all_tests[test_type]
                    if category_filter.lower() in t.get("category", "").lower()
                ]
        
        return all_tests
    
    # ==================== TEST EXECUTION ====================
    
    async def send_chat_message(self, bot_name: str, message: str, test_type: str) -> tuple[bool, str, Any]:
        """Send chat message to bot"""
        config = self.BOT_CONFIGS[bot_name]
        port = config["port"]
        user_id = self.get_user_id(bot_name, test_type)
        
        url = f"http://localhost:{port}/api/chat"
        payload = {"user_id": user_id, "message": message}
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return True, data.get("response", ""), data
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    async def run_character_test(self, test: Dict[str, Any]) -> TestResult:
        """Run a character regression test"""
        print(f"\n   🎭 Testing: {test['test_name']}")
        print(f"      Category: {test['category']}")
        print(f"      Message: \"{test['message']}\"")
        
        try:
            # Send message
            success, response, _ = await self.send_chat_message(
                test['bot_name'], test['message'], 'character'
            )
            
            if not success:
                return TestResult(
                    test_id=test['test_id'],
                    test_name=test['test_name'],
                    bot_name=test['bot_name'],
                    test_type='character',
                    category=test['category'],
                    success=False,
                    response=response,
                    matched_patterns=[],
                    missing_patterns=test['expected_patterns'],
                    error=response
                )
            
            # Check patterns
            matched = []
            missing = []
            
            for pattern in test['expected_patterns']:
                if re.search(pattern, response, re.IGNORECASE):
                    matched.append(pattern)
                else:
                    missing.append(pattern)
            
            # Check unexpected patterns
            if 'unexpected_patterns' in test:
                for pattern in test['unexpected_patterns']:
                    if re.search(pattern, response, re.IGNORECASE):
                        missing.append(f"UNEXPECTED: {pattern}")
            
            test_passed = len(missing) == 0
            
            if test_passed:
                print(f"      ✅ PASS: All {len(matched)} patterns matched")
            else:
                print(f"      ⚠️  WARN: {len(matched)}/{len(test['expected_patterns'])} patterns")
                print(f"      ❌ Missing: {', '.join(missing[:2])}")
            
            print(f"      Response: {response[:150]}{'...' if len(response) > 150 else ''}")
            
            return TestResult(
                test_id=test['test_id'],
                test_name=test['test_name'],
                bot_name=test['bot_name'],
                test_type='character',
                category=test['category'],
                success=test_passed,
                response=response,
                matched_patterns=matched,
                missing_patterns=missing
            )
            
        except Exception as e:
            print(f"      🔴 ERROR: {str(e)}")
            return TestResult(
                test_id=test['test_id'],
                test_name=test['test_name'],
                bot_name=test['bot_name'],
                test_type='character',
                category=test['category'],
                success=False,
                response="",
                matched_patterns=[],
                missing_patterns=test['expected_patterns'],
                error=str(e)
            )
    
    async def run_memory_test(self, test: Dict[str, Any]) -> TestResult:
        """Run a memory system test"""
        print(f"\n   🧠 Testing: {test['test_name']}")
        print(f"      Category: {test['category']}")
        print(f"      Setup: {len(test['conversation_sequence'])} messages")
        
        try:
            # Build memory
            for msg in test['conversation_sequence']:
                success, response, _ = await self.send_chat_message(
                    test['bot_name'], msg, 'memory'
                )
                if not success:
                    return TestResult(
                        test_id=test['test_id'],
                        test_name=test['test_name'],
                        bot_name=test['bot_name'],
                        test_type='memory',
                        category=test['category'],
                        success=False,
                        response=response,
                        matched_patterns=[],
                        missing_patterns=test['expected_memory_indicators'],
                        error=f"Setup failed: {response}"
                    )
                await asyncio.sleep(1)
            
            # Validate memory
            print(f"      Validation: \"{test['validation_query']}\"")
            success, response, _ = await self.send_chat_message(
                test['bot_name'], test['validation_query'], 'memory'
            )
            
            if not success:
                return TestResult(
                    test_id=test['test_id'],
                    test_name=test['test_name'],
                    bot_name=test['bot_name'],
                    test_type='memory',
                    category=test['category'],
                    success=False,
                    response=response,
                    matched_patterns=[],
                    missing_patterns=test['expected_memory_indicators'],
                    error=f"Validation failed: {response}"
                )
            
            # Check memory indicators
            matched = []
            missing = []
            
            for indicator in test['expected_memory_indicators']:
                if re.search(indicator, response, re.IGNORECASE):
                    matched.append(indicator)
                else:
                    missing.append(indicator)
            
            min_matches = test.get('min_expected_matches', 1)
            test_passed = len(matched) >= min_matches
            
            if test_passed:
                print(f"      ✅ PASS: {len(matched)}/{len(test['expected_memory_indicators'])} indicators (min: {min_matches})")
            else:
                print(f"      ❌ FAIL: {len(matched)}/{len(test['expected_memory_indicators'])} indicators (needed: {min_matches})")
            
            print(f"      Response: {response[:150]}{'...' if len(response) > 150 else ''}")
            
            return TestResult(
                test_id=test['test_id'],
                test_name=test['test_name'],
                bot_name=test['bot_name'],
                test_type='memory',
                category=test['category'],
                success=test_passed,
                response=response,
                matched_patterns=matched,
                missing_patterns=missing
            )
            
        except Exception as e:
            print(f"      🔴 ERROR: {str(e)}")
            return TestResult(
                test_id=test['test_id'],
                test_name=test['test_name'],
                bot_name=test['bot_name'],
                test_type='memory',
                category=test['category'],
                success=False,
                response="",
                matched_patterns=[],
                missing_patterns=test['expected_memory_indicators'],
                error=str(e)
            )
    
    async def run_intelligence_test(self, test: Dict[str, Any]) -> TestResult:
        """Run an intelligence system test"""
        print(f"\n   🧠 Testing: {test['test_name']}")
        print(f"      System: {test['system_type']} | Category: {test['category']}")
        
        try:
            # Setup phase
            print(f"      Setup: {len(test['setup_sequence'])} messages")
            for msg in test['setup_sequence']:
                success, response, _ = await self.send_chat_message(
                    test['bot_name'], msg, 'intelligence'
                )
                if not success:
                    return TestResult(
                        test_id=test['test_id'],
                        test_name=test['test_name'],
                        bot_name=test['bot_name'],
                        test_type='intelligence',
                        category=test['category'],
                        success=False,
                        response=response,
                        matched_patterns=[],
                        missing_patterns=test['expected_indicators'],
                        error=f"Setup failed: {response}"
                    )
                await asyncio.sleep(1)
            
            # Validation phase
            print(f"      Validation: \"{test['validation_query']}\"")
            success, response, _ = await self.send_chat_message(
                test['bot_name'], test['validation_query'], 'intelligence'
            )
            
            if not success:
                return TestResult(
                    test_id=test['test_id'],
                    test_name=test['test_name'],
                    bot_name=test['bot_name'],
                    test_type='intelligence',
                    category=test['category'],
                    success=False,
                    response=response,
                    matched_patterns=[],
                    missing_patterns=test['expected_indicators'],
                    error=f"Validation failed: {response}"
                )
            
            # Check indicators
            matched = []
            missing = []
            
            for indicator in test['expected_indicators']:
                if re.search(indicator, response, re.IGNORECASE):
                    matched.append(indicator)
                else:
                    missing.append(indicator)
            
            min_matches = test.get('min_expected_matches', 1)
            test_passed = len(matched) >= min_matches
            
            if test_passed:
                print(f"      ✅ PASS: {len(matched)}/{len(test['expected_indicators'])} indicators (min: {min_matches})")
            else:
                print(f"      ❌ FAIL: {len(matched)}/{len(test['expected_indicators'])} indicators (needed: {min_matches})")
            
            print(f"      Response: {response[:150]}{'...' if len(response) > 150 else ''}")
            
            return TestResult(
                test_id=test['test_id'],
                test_name=test['test_name'],
                bot_name=test['bot_name'],
                test_type='intelligence',
                category=test['category'],
                success=test_passed,
                response=response,
                matched_patterns=matched,
                missing_patterns=missing
            )
            
        except Exception as e:
            print(f"      🔴 ERROR: {str(e)}")
            return TestResult(
                test_id=test['test_id'],
                test_name=test['test_name'],
                bot_name=test['bot_name'],
                test_type='intelligence',
                category=test['category'],
                success=False,
                response="",
                matched_patterns=[],
                missing_patterns=test['expected_indicators'],
                error=str(e)
            )
    
    # ==================== TEST ORCHESTRATION ====================
    
    async def run_all_tests(
        self,
        type_filter: Optional[List[str]] = None,
        bot_filter: Optional[List[str]] = None,
        category_filter: Optional[str] = None
    ):
        """Run all tests with filtering"""
        tests = self.load_all_tests(type_filter, bot_filter, category_filter)
        
        total_tests = sum(len(tests[t]) for t in tests)
        
        print(f"\n🧪 WhisperEngine Unified Test Harness (YAML-Driven)")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        if type_filter:
            print(f"Type Filter: {', '.join(type_filter)}")
        if bot_filter:
            print(f"Bot Filter: {', '.join(bot_filter)}")
        if category_filter:
            print(f"Category Filter: {category_filter}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run tests by type and bot
        for test_type in ["character", "memory", "intelligence"]:
            if not tests[test_type]:
                continue
            
            print(f"\n{'=' * 80}")
            print(f"🧪 {test_type.upper()} TESTS ({len(tests[test_type])} tests)")
            print(f"{'=' * 80}")
            
            # Group by bot
            tests_by_bot = {}
            for test in tests[test_type]:
                bot = test['bot_name']
                if bot not in tests_by_bot:
                    tests_by_bot[bot] = []
                tests_by_bot[bot].append(test)
            
            # Run tests
            for bot_name, bot_tests in sorted(tests_by_bot.items()):
                config = self.BOT_CONFIGS[bot_name]
                print(f"\n🤖 {bot_name.upper()} - {len(bot_tests)} tests")
                print(f"   Port: {config['port']} | Archetype: {config['archetype']}")
                
                for test in bot_tests:
                    if test_type == "character":
                        result = await self.run_character_test(test)
                    elif test_type == "memory":
                        result = await self.run_memory_test(test)
                    else:  # intelligence
                        result = await self.run_intelligence_test(test)
                    
                    self.results.append(result)
                    await asyncio.sleep(2)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success and not r.error)
        errors = sum(1 for r in self.results if r.error)
        
        print(f"\n{'=' * 80}")
        print(f"📊 TEST SUMMARY")
        print(f"{'=' * 80}")
        print(f"Total Tests:    {total}")
        print(f"✅ Passed:      {passed}")
        print(f"❌ Failed:      {failed}")
        print(f"🔴 Errors:      {errors}")
        print(f"Success Rate:   {(passed/total*100) if total > 0 else 0:.1f}%")
        
        # By test type
        print(f"\n{'=' * 80}")
        print(f"📈 RESULTS BY TEST TYPE")
        print(f"{'=' * 80}")
        
        types = sorted(set(r.test_type for r in self.results))
        for test_type in types:
            type_results = [r for r in self.results if r.test_type == test_type]
            type_passed = sum(1 for r in type_results if r.success)
            status = "✅" if type_passed == len(type_results) else "⚠️"
            print(f"{status} {test_type.capitalize():15} | {type_passed}/{len(type_results)} passed")
        
        # By bot
        print(f"\n{'=' * 80}")
        print(f"📈 RESULTS BY BOT")
        print(f"{'=' * 80}")
        
        bots = sorted(set(r.bot_name for r in self.results))
        for bot in bots:
            bot_results = [r for r in self.results if r.bot_name == bot]
            bot_passed = sum(1 for r in bot_results if r.success)
            bot_failed = sum(1 for r in bot_results if not r.success and not r.error)
            bot_errors = sum(1 for r in bot_results if r.error)
            status = "✅" if bot_failed == 0 and bot_errors == 0 else "❌"
            print(f"{status} {bot.capitalize():20} | {bot_passed}/{len(bot_results)} passed | F:{bot_failed} E:{bot_errors}")
        
        print(f"\n{'=' * 80}")
        if failed == 0 and errors == 0:
            print(f"🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  SOME TESTS FAILED - Review details above")
        print(f"{'=' * 80}\n")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WhisperEngine Unified Test Harness")
    parser.add_argument("--type", type=str, help="Test types (character,memory,intelligence)")
    parser.add_argument("--bots", type=str, help="Comma-separated bot names")
    parser.add_argument("--category", type=str, help="Category filter")
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout")
    
    args = parser.parse_args()
    
    type_filter = [t.strip() for t in args.type.split(",")] if args.type else None
    bot_filter = [b.strip().lower() for b in args.bots.split(",")] if args.bots else None
    
    harness = UnifiedTestHarness(timeout=args.timeout)
    
    try:
        await harness.run_all_tests(type_filter, bot_filter, args.category)
    finally:
        await harness.close()


if __name__ == "__main__":
    asyncio.run(main())
