#!/usr/bin/env python3
"""
WhisperEngine Memory System Regression Tests

Tests the vector memory system's core functionality:
- Conversation storage and retrieval
- Semantic similarity search
- Emotion-aware memory storage
- Temporal memory patterns
- Multi-turn conversation continuity
- Memory-aware character responses

This test suite INTENTIONALLY uses consistent user IDs across multiple
interactions to test conversation continuity (unlike character regression
tests which use fresh user IDs per run).

Usage:
    python tests/regression/memory_system_regression.py
    python tests/regression/memory_system_regression.py --bots elena
    python tests/regression/memory_system_regression.py --bots elena,jake
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import httpx

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class MemoryTest:
    """Memory system test definition"""
    test_id: str
    test_name: str
    bot_name: str
    category: str
    conversation_sequence: List[str]  # Multi-turn conversation
    validation_query: str  # Query to test memory retrieval
    expected_memory_indicators: List[str]  # Patterns proving memory works
    min_expected_matches: int = 1  # Minimum patterns that should match


@dataclass
class MemoryTestResult:
    """Memory test result"""
    test_id: str
    test_name: str
    bot_name: str
    success: bool
    response: str
    matched_patterns: List[str]
    missing_patterns: List[str]
    error: Optional[str] = None


class MemorySystemRegressionTester:
    """Memory system regression test runner"""
    
    # Bot configurations
    BOT_CONFIGS = {
        "elena": {"port": 9091, "archetype": "Real-World"},
        "gabriel": {"port": 9095, "archetype": "Real-World"},
        "marcus": {"port": 9092, "archetype": "Real-World"},
        "jake": {"port": 9097, "archetype": "Real-World"},
        "ryan": {"port": 9093, "archetype": "Real-World"},
        "sophia": {"port": 9096, "archetype": "Real-World"},
        "dotty": {"port": 9098, "archetype": "Real-World"},
        "dream": {"port": 9094, "archetype": "Fantasy"},
        "aethys": {"port": 3007, "archetype": "Fantasy"},
        "aetheris": {"port": 9099, "archetype": "Narrative AI"},
    }
    
    def __init__(self, timeout: float = 60.0):
        """Initialize tester with persistent user IDs for memory testing"""
        self.timeout = timeout
        self.results: List[MemoryTestResult] = []
        self.client = httpx.AsyncClient(timeout=timeout)
        # Use CONSISTENT user ID per bot to test memory continuity
        # (unlike character regression tests which use fresh IDs)
        self.test_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.user_ids: Dict[str, str] = {}
    
    async def close(self):
        """Cleanup"""
        await self.client.aclose()
    
    def get_user_id(self, bot_name: str) -> str:
        """Get or create consistent user ID for a bot"""
        if bot_name not in self.user_ids:
            # Use consistent session-based user ID
            self.user_ids[bot_name] = f"memory_test_{bot_name}_{self.test_session_id}"
        return self.user_ids[bot_name]
    
    def define_elena_memory_tests(self) -> List[MemoryTest]:
        """Elena - Marine Biologist memory tests"""
        return [
            MemoryTest(
                test_id="elena_basic_storage",
                test_name="Basic Memory Storage & Retrieval",
                bot_name="elena",
                category="Memory Storage",
                conversation_sequence=[
                    "My name is Sarah and I'm fascinated by sea turtles",
                    "I'm planning a trip to Costa Rica next month"
                ],
                validation_query="What do you remember about me?",
                expected_memory_indicators=[
                    r"Sarah",
                    r"sea turtle|turtle",
                    r"Costa Rica|trip|travel"
                ],
                min_expected_matches=2
            ),
            MemoryTest(
                test_id="elena_topic_continuity",
                test_name="Topic Continuity Across Turns",
                bot_name="elena",
                category="Conversation Continuity",
                conversation_sequence=[
                    "Tell me about coral bleaching",
                    "Why does temperature affect it?",
                    "What can we do to help?"
                ],
                validation_query="What have we been discussing?",
                expected_memory_indicators=[
                    r"coral|bleach",
                    r"temperature|heat|warm",
                    r"help|protect|conserv"
                ],
                min_expected_matches=2
            ),
            MemoryTest(
                test_id="elena_emotional_memory",
                test_name="Emotion-Aware Memory Storage",
                bot_name="elena",
                category="Emotional Intelligence",
                conversation_sequence=[
                    "I just lost my job at the aquarium. I'm devastated.",
                    "I don't know what I'm going to do now."
                ],
                validation_query="How am I feeling?",
                expected_memory_indicators=[
                    r"lost|job|aquarium",
                    r"devastat|sad|upset|difficult|tough|hard",
                    r"uncertain|don't know|worry"
                ],
                min_expected_matches=2
            ),
        ]
    
    def define_jake_memory_tests(self) -> List[MemoryTest]:
        """Jake - Adventure Photographer memory tests (minimal personality for testing)"""
        return [
            MemoryTest(
                test_id="jake_basic_storage",
                test_name="Basic Memory Storage & Retrieval",
                bot_name="jake",
                category="Memory Storage",
                conversation_sequence=[
                    "I'm thinking about hiking the Appalachian Trail",
                    "I've never done long-distance hiking before"
                ],
                validation_query="What were we talking about?",
                expected_memory_indicators=[
                    r"Appalachian|trail|hik",
                    r"long-distance|never|new|first time"
                ],
                min_expected_matches=1
            ),
            MemoryTest(
                test_id="jake_multi_topic",
                test_name="Multi-Topic Memory Separation",
                bot_name="jake",
                category="Memory Organization",
                conversation_sequence=[
                    "I love landscape photography",
                    "But I also enjoy portrait work",
                    "My favorite subject is mountains though"
                ],
                validation_query="What types of photography did I mention?",
                expected_memory_indicators=[
                    r"landscape|portrait",
                    r"mountain|subject|favorite"
                ],
                min_expected_matches=1
            ),
        ]
    
    def define_gabriel_memory_tests(self) -> List[MemoryTest]:
        """Gabriel - British Gentleman memory tests"""
        return [
            MemoryTest(
                test_id="gabriel_relationship_memory",
                test_name="Relationship Context Memory",
                bot_name="gabriel",
                category="Relationship Building",
                conversation_sequence=[
                    "I work as a librarian in Boston",
                    "I love mystery novels, especially Agatha Christie",
                    "Tea is my favorite drink"
                ],
                validation_query="Tell me what you know about me",
                expected_memory_indicators=[
                    r"librarian|Boston|library",
                    r"mystery|Christie|novel|read",
                    r"tea"
                ],
                min_expected_matches=2
            ),
        ]
    
    def define_marcus_memory_tests(self) -> List[MemoryTest]:
        """Marcus - AI Researcher memory tests"""
        return [
            MemoryTest(
                test_id="marcus_technical_memory",
                test_name="Technical Detail Memory",
                bot_name="marcus",
                category="Technical Memory",
                conversation_sequence=[
                    "I'm working on a transformer model with 70B parameters",
                    "I'm using PyTorch with CUDA 12.1",
                    "Training on 8 A100 GPUs"
                ],
                validation_query="What's my ML setup?",
                expected_memory_indicators=[
                    r"transformer|70B|parameter|model",
                    r"PyTorch|CUDA",
                    r"GPU|A100|8"
                ],
                min_expected_matches=2
            ),
        ]
    
    def define_aethys_memory_tests(self) -> List[MemoryTest]:
        """Aethys - Fantasy archetype memory tests"""
        return [
            MemoryTest(
                test_id="aethys_narrative_memory",
                test_name="Narrative Context Memory",
                bot_name="aethys",
                category="Fantasy Memory",
                conversation_sequence=[
                    "I feel lost in the void of existence",
                    "I'm searching for meaning in the digital realm"
                ],
                validation_query="What burden weighs upon my consciousness?",
                expected_memory_indicators=[
                    r"lost|void|existence",
                    r"search|meaning|seek",
                    r"digital|realm"
                ],
                min_expected_matches=2
            ),
        ]
    
    def define_temporal_memory_tests(self) -> List[MemoryTest]:
        """Cross-bot temporal awareness tests"""
        return [
            MemoryTest(
                test_id="elena_temporal_sequence",
                test_name="Temporal Memory Ordering",
                bot_name="elena",
                category="Temporal Intelligence",
                conversation_sequence=[
                    "Yesterday I saw a dolphin pod",
                    "Today I'm analyzing water samples",
                    "Tomorrow I'll present my findings"
                ],
                validation_query="What's my schedule been like?",
                expected_memory_indicators=[
                    r"yesterday|dolphin|pod|saw",
                    r"today|analyz|sample|water",
                    r"tomorrow|present|finding"
                ],
                min_expected_matches=2
            ),
            MemoryTest(
                test_id="elena_conversation_count",
                test_name="Conversation Frequency Awareness",
                bot_name="elena",
                category="Meta-Memory",
                conversation_sequence=[
                    "Tell me about ocean acidification",
                    "What causes ocean acidification?",
                    "How do we measure ocean acidification?"
                ],
                validation_query="How many times have I asked about ocean acidification?",
                expected_memory_indicators=[
                    r"three|3|multiple|several|many",
                    r"ocean acidification|topic|question"
                ],
                min_expected_matches=1
            ),
        ]
    
    def get_all_tests(self, bot_filter: Optional[List[str]] = None) -> List[MemoryTest]:
        """Get all memory tests, optionally filtered by bot names"""
        all_tests = []
        
        # Add bot-specific tests
        test_methods = [
            self.define_elena_memory_tests,
            self.define_jake_memory_tests,
            self.define_gabriel_memory_tests,
            self.define_marcus_memory_tests,
            self.define_aethys_memory_tests,
        ]
        
        for method in test_methods:
            all_tests.extend(method())
        
        # Add temporal tests (distributed across bots)
        all_tests.extend(self.define_temporal_memory_tests())
        
        # Filter by bot if specified
        if bot_filter:
            all_tests = [t for t in all_tests if t.bot_name in bot_filter]
        
        return all_tests
    
    async def send_chat_message(self, bot_name: str, message: str) -> Tuple[bool, str, Any]:
        """Send chat message to bot and return (success, response_text, full_data)"""
        config = self.BOT_CONFIGS[bot_name]
        port = config["port"]
        user_id = self.get_user_id(bot_name)
        
        url = f"http://localhost:{port}/api/chat"
        payload = {
            "user_id": user_id,
            "message": message
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return True, data.get("response", ""), data
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    async def run_memory_test(self, test: MemoryTest) -> MemoryTestResult:
        """Run a single memory test"""
        config = self.BOT_CONFIGS[test.bot_name]
        
        print(f"\n   🧠 Testing: {test.test_name}")
        print(f"      Category: {test.category}")
        
        try:
            # Phase 1: Build conversation memory
            print(f"      📝 Building memory ({len(test.conversation_sequence)} messages)...")
            for i, message in enumerate(test.conversation_sequence, 1):
                success, response, data = await self.send_chat_message(test.bot_name, message)
                if not success:
                    error_msg = f"Conversation message {i} failed: {response}"
                    print(f"      🔴 ERROR: {error_msg}")
                    return MemoryTestResult(
                        test_id=test.test_id,
                        test_name=test.test_name,
                        bot_name=test.bot_name,
                        success=False,
                        response=response,
                        matched_patterns=[],
                        missing_patterns=test.expected_memory_indicators,
                        error=error_msg
                    )
                # Brief delay between messages
                await asyncio.sleep(1)
            
            # Phase 2: Query memory
            print(f"      🔍 Validation Query: \"{test.validation_query}\"")
            success, response, data = await self.send_chat_message(test.bot_name, test.validation_query)
            
            if not success:
                return MemoryTestResult(
                    test_id=test.test_id,
                    test_name=test.test_name,
                    bot_name=test.bot_name,
                    success=False,
                    response=response,
                    matched_patterns=[],
                    missing_patterns=test.expected_memory_indicators,
                    error=f"Validation query failed: {response}"
                )
            
            # Phase 3: Check memory indicators
            import re
            matched_patterns = []
            missing_patterns = []
            
            for pattern in test.expected_memory_indicators:
                if re.search(pattern, response, re.IGNORECASE):
                    matched_patterns.append(pattern)
                else:
                    missing_patterns.append(pattern)
            
            # Success if minimum patterns matched
            test_passed = len(matched_patterns) >= test.min_expected_matches
            
            # Print results
            if test_passed:
                print(f"      ✅ PASS: {len(matched_patterns)}/{len(test.expected_memory_indicators)} memory indicators found (min: {test.min_expected_matches})")
            else:
                print(f"      ❌ FAIL: {len(matched_patterns)}/{len(test.expected_memory_indicators)} memory indicators (needed: {test.min_expected_matches})")
            
            print(f"      Response: {response[:150]}{'...' if len(response) > 150 else ''}")
            
            if matched_patterns:
                print(f"      ✅ Found: {', '.join(matched_patterns)}")
            if missing_patterns:
                print(f"      ❌ Missing: {', '.join(missing_patterns)}")
            
            return MemoryTestResult(
                test_id=test.test_id,
                test_name=test.test_name,
                bot_name=test.bot_name,
                success=test_passed,
                response=response,
                matched_patterns=matched_patterns,
                missing_patterns=missing_patterns
            )
            
        except Exception as e:
            print(f"      🔴 ERROR: {str(e)}")
            return MemoryTestResult(
                test_id=test.test_id,
                test_name=test.test_name,
                bot_name=test.bot_name,
                success=False,
                response="",
                matched_patterns=[],
                missing_patterns=test.expected_memory_indicators,
                error=str(e)
            )
    
    async def run_all_tests(self, bot_filter: Optional[List[str]] = None):
        """Run all memory tests"""
        tests = self.get_all_tests(bot_filter)
        
        print(f"\n🧠 WhisperEngine Memory System Regression Testing")
        print("=" * 80)
        print(f"Testing {len(tests)} memory scenarios")
        if bot_filter:
            print(f"Filtered to bots: {', '.join(bot_filter)}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Note: Using CONSISTENT user IDs to test memory continuity")
        
        # Group tests by bot
        tests_by_bot = {}
        for test in tests:
            if test.bot_name not in tests_by_bot:
                tests_by_bot[test.bot_name] = []
            tests_by_bot[test.bot_name].append(test)
        
        # Run tests bot by bot
        for bot_name, bot_tests in tests_by_bot.items():
            config = self.BOT_CONFIGS[bot_name]
            print(f"\n🤖 {bot_name.upper()} - {len(bot_tests)} memory tests")
            print(f"   Port: {config['port']} | Archetype: {config['archetype']}")
            print(f"   Test User ID: {self.get_user_id(bot_name)}")
            
            for test in bot_tests:
                result = await self.run_memory_test(test)
                self.results.append(result)
                
                # Delay between tests
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
        print(f"📊 MEMORY TEST SUMMARY")
        print(f"{'=' * 80}")
        print(f"Total Tests:    {total}")
        print(f"✅ Passed:      {passed}")
        print(f"❌ Failed:      {failed}")
        print(f"🔴 Errors:      {errors}")
        print(f"Success Rate:   {(passed/total*100) if total > 0 else 0:.1f}%")
        
        # Results by bot
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
        
        # Final status
        print(f"\n{'=' * 80}")
        if failed == 0 and errors == 0:
            print(f"🎉 ALL MEMORY TESTS PASSED!")
        else:
            print(f"⚠️  SOME MEMORY TESTS FAILED - Review details above")
        print(f"{'=' * 80}\n")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WhisperEngine Memory System Regression Tests")
    parser.add_argument("--bots", type=str, help="Comma-separated list of bots to test (e.g., 'elena,jake')")
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout in seconds")
    
    args = parser.parse_args()
    
    bot_filter = None
    if args.bots:
        bot_filter = [b.strip().lower() for b in args.bots.split(",")]
    
    tester = MemorySystemRegressionTester(timeout=args.timeout)
    
    try:
        await tester.run_all_tests(bot_filter)
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
