#!/usr/bin/env python3
"""
WhisperEngine Intelligence System Regression Tests

Tests advanced intelligence systems built on vector memory foundation:
- User Preferences (stored preferences retrieval)
- Episodic Memory Intelligence (memorable moment extraction)
- Knowledge Graph Intelligence (fact relationships)
- Emotional Pattern Recognition
- Conversation Intelligence
- Character Self-Knowledge
- Temporal Evolution
- Context Awareness

These tests validate the ADVANCED intelligence layer that sits on top
of the vector memory system (tested in memory_system_regression.py).

Usage:
    python tests/regression/intelligence_system_regression.py
    python tests/regression/intelligence_system_regression.py --systems episodic,preferences
    python tests/regression/intelligence_system_regression.py --bots elena,marcus
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import httpx

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class IntelligenceTest:
    """Intelligence system test definition"""
    test_id: str
    test_name: str
    bot_name: str
    system_type: str  # episodic, preferences, knowledge_graph, emotional, etc.
    category: str
    setup_sequence: List[str]  # Messages to set up the intelligence
    validation_query: str  # Query to test intelligence
    expected_indicators: List[str]  # Patterns proving intelligence works
    min_expected_matches: int = 1


@dataclass
class IntelligenceTestResult:
    """Intelligence test result"""
    test_id: str
    test_name: str
    bot_name: str
    system_type: str
    success: bool
    response: str
    matched_patterns: List[str]
    missing_patterns: List[str]
    error: Optional[str] = None


class IntelligenceSystemTester:
    """Intelligence system regression test runner"""
    
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
        """Initialize tester"""
        self.timeout = timeout
        self.results: List[IntelligenceTestResult] = []
        self.client = httpx.AsyncClient(timeout=timeout)
        self.test_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.user_ids: Dict[str, str] = {}
    
    async def close(self):
        """Cleanup"""
        await self.client.aclose()
    
    def get_user_id(self, bot_name: str) -> str:
        """Get or create consistent user ID for a bot"""
        if bot_name not in self.user_ids:
            self.user_ids[bot_name] = f"intel_test_{bot_name}_{self.test_session_id}"
        return self.user_ids[bot_name]
    
    # ==================== EPISODIC MEMORY INTELLIGENCE TESTS ====================
    
    def define_episodic_memory_tests(self) -> List[IntelligenceTest]:
        """Tests for episodic memory intelligence (memorable moments)"""
        return [
            IntelligenceTest(
                test_id="elena_episodic_emotional_peak",
                test_name="Episodic: Emotional Peak Memory",
                bot_name="elena",
                system_type="episodic_memory",
                category="Memorable Moments",
                setup_sequence=[
                    "I just witnessed the most incredible thing - a whale breach right next to my boat! I was sobbing with joy!",
                    "Tell me about marine mammals",
                ],
                validation_query="Do you remember any particularly emotional moments we've shared?",
                expected_indicators=[
                    r"whale|breach|boat",
                    r"joy|incredible|emotional|sob",
                    r"moment|memory|experience"
                ],
                min_expected_matches=2
            ),
            IntelligenceTest(
                test_id="marcus_episodic_technical_insight",
                test_name="Episodic: Technical Discussion Memory",
                bot_name="marcus",
                system_type="episodic_memory",
                category="Memorable Moments",
                setup_sequence=[
                    "I finally got my attention mechanism working with multi-head cross-attention!",
                    "What's your research focus?",
                ],
                validation_query="What technical achievements have I mentioned?",
                expected_indicators=[
                    r"attention|multi-head|cross-attention",
                    r"working|achievement|success",
                ],
                min_expected_matches=1
            ),
            IntelligenceTest(
                test_id="gabriel_episodic_personal_sharing",
                test_name="Episodic: Personal Story Memory",
                bot_name="gabriel",
                system_type="episodic_memory",
                category="Memorable Moments",
                setup_sequence=[
                    "My grandmother just passed away. She taught me everything about British literature.",
                    "Tell me about yourself",
                ],
                validation_query="Have I shared anything personal with you?",
                expected_indicators=[
                    r"grandmother|passed|loss",
                    r"literature|taught|taught",
                    r"personal|shared|told"
                ],
                min_expected_matches=2
            ),
        ]
    
    # ==================== EMOTIONAL INTELLIGENCE TESTS ====================
    
    def define_emotional_intelligence_tests(self) -> List[IntelligenceTest]:
        """Tests for emotional pattern recognition"""
        return [
            IntelligenceTest(
                test_id="elena_emotional_pattern_anxiety",
                test_name="Emotional: Anxiety Pattern Recognition",
                bot_name="elena",
                system_type="emotional_intelligence",
                category="Emotional Patterns",
                setup_sequence=[
                    "I'm really stressed about my PhD defense next week",
                    "I can't sleep thinking about the questions they might ask",
                    "What if I fail?",
                ],
                validation_query="How am I feeling about my PhD defense?",
                expected_indicators=[
                    r"stress|anxious|anxiety|worry|worried",
                    r"defense|PhD|questions",
                    r"sleep|can't sleep|thinking",
                ],
                min_expected_matches=2
            ),
            IntelligenceTest(
                test_id="marcus_emotional_enthusiasm",
                test_name="Emotional: Enthusiasm Pattern Recognition",
                bot_name="marcus",
                system_type="emotional_intelligence",
                category="Emotional Patterns",
                setup_sequence=[
                    "I'm so excited about transformer architectures!",
                    "The self-attention mechanism is absolutely brilliant!",
                    "I could talk about this all day!",
                ],
                validation_query="What topics am I passionate about?",
                expected_indicators=[
                    r"excited|passion|enthusias",
                    r"transformer|self-attention|architect",
                    r"brilliant|love|talk all day",
                ],
                min_expected_matches=2
            ),
        ]
    
    # ==================== USER PREFERENCES TESTS ====================
    
    def define_user_preferences_tests(self) -> List[IntelligenceTest]:
        """Tests for user preference storage and retrieval"""
        return [
            IntelligenceTest(
                test_id="elena_preference_name",
                test_name="Preferences: Preferred Name Storage",
                bot_name="elena",
                system_type="user_preferences",
                category="Preference Management",
                setup_sequence=[
                    "Please call me Alex from now on",
                    "Tell me about coral reefs",
                ],
                validation_query="What's my name?",
                expected_indicators=[
                    r"Alex",
                ],
                min_expected_matches=1
            ),
            IntelligenceTest(
                test_id="marcus_preference_communication",
                test_name="Preferences: Communication Style",
                bot_name="marcus",
                system_type="user_preferences",
                category="Preference Management",
                setup_sequence=[
                    "I prefer technical explanations with lots of details",
                    "Explain transformers to me",
                ],
                validation_query="How do I like information presented?",
                expected_indicators=[
                    r"technical|detail|detailed",
                    r"prefer|like|style",
                ],
                min_expected_matches=1
            ),
        ]
    
    # ==================== CONVERSATION INTELLIGENCE TESTS ====================
    
    def define_conversation_intelligence_tests(self) -> List[IntelligenceTest]:
        """Tests for conversation pattern understanding"""
        return [
            IntelligenceTest(
                test_id="elena_conversation_topic_shift",
                test_name="Conversation: Topic Shift Detection",
                bot_name="elena",
                system_type="conversation_intelligence",
                category="Conversation Dynamics",
                setup_sequence=[
                    "Tell me about ocean acidification",
                    "Actually, can we talk about sea turtles instead?",
                    "What's your favorite sea turtle species?",
                ],
                validation_query="What topics have we discussed?",
                expected_indicators=[
                    r"ocean acidification|acidification",
                    r"sea turtle|turtle",
                    r"topic|shift|chang|switch",
                ],
                min_expected_matches=2
            ),
            IntelligenceTest(
                test_id="marcus_conversation_depth",
                test_name="Conversation: Discussion Depth Tracking",
                bot_name="marcus",
                system_type="conversation_intelligence",
                category="Conversation Dynamics",
                setup_sequence=[
                    "What's a neural network?",
                    "How do layers work?",
                    "What about backpropagation?",
                    "Can you explain gradient descent?",
                ],
                validation_query="How deep have we gone into neural networks?",
                expected_indicators=[
                    r"layer|backprop|gradient|descent",
                    r"deep|detail|progress|building",
                    r"neural network|network",
                ],
                min_expected_matches=2
            ),
        ]
    
    # ==================== TEMPORAL AWARENESS TESTS ====================
    
    def define_temporal_awareness_tests(self) -> List[IntelligenceTest]:
        """Tests for temporal pattern recognition"""
        return [
            IntelligenceTest(
                test_id="elena_temporal_frequency",
                test_name="Temporal: Question Frequency Awareness",
                bot_name="elena",
                system_type="temporal_awareness",
                category="Temporal Patterns",
                setup_sequence=[
                    "Tell me about dolphins",
                    "What do dolphins eat?",
                    "How do dolphins communicate?",
                    "Where do dolphins live?",
                ],
                validation_query="Have I been asking about a specific topic repeatedly?",
                expected_indicators=[
                    r"dolphin",
                    r"multiple|several|many|repeated|four|4",
                    r"question|ask|topic",
                ],
                min_expected_matches=2
            ),
            IntelligenceTest(
                test_id="jake_temporal_session_awareness",
                test_name="Temporal: Session Continuity",
                bot_name="jake",
                system_type="temporal_awareness",
                category="Temporal Patterns",
                setup_sequence=[
                    "Good morning! Ready for our conversation?",
                    "Tell me about wilderness photography",
                ],
                validation_query="When did we start talking today?",
                expected_indicators=[
                    r"morning|started|began|session|conversation",
                    r"today|earlier|recent",
                ],
                min_expected_matches=1
            ),
        ]
    
    # ==================== CHARACTER SELF-KNOWLEDGE TESTS ====================
    
    def define_character_self_knowledge_tests(self) -> List[IntelligenceTest]:
        """Tests for character self-awareness and insights"""
        return [
            IntelligenceTest(
                test_id="elena_self_knowledge_teaching_style",
                test_name="Self-Knowledge: Teaching Style Awareness",
                bot_name="elena",
                system_type="character_self_knowledge",
                category="Character Insights",
                setup_sequence=[
                    "You explain things so clearly!",
                    "I love how enthusiastic you are about marine biology",
                    "Your analogies really help me understand",
                ],
                validation_query="How would you describe your teaching style?",
                expected_indicators=[
                    r"clear|explain|analogy|analogies",
                    r"enthusias|passion|love",
                    r"teach|help|understand",
                ],
                min_expected_matches=2
            ),
            IntelligenceTest(
                test_id="marcus_self_knowledge_research_approach",
                test_name="Self-Knowledge: Research Approach Awareness",
                bot_name="marcus",
                system_type="character_self_knowledge",
                category="Character Insights",
                setup_sequence=[
                    "You're very methodical in your explanations",
                    "I appreciate how you build concepts step by step",
                    "Your technical precision is impressive",
                ],
                validation_query="How would you describe your approach to explaining AI?",
                expected_indicators=[
                    r"methodical|systematic|step|structured",
                    r"precision|precise|technical|accurate",
                    r"build|foundation|concept",
                ],
                min_expected_matches=2
            ),
        ]
    
    # ==================== KNOWLEDGE INTEGRATION TESTS ====================
    
    def define_knowledge_integration_tests(self) -> List[IntelligenceTest]:
        """Tests for cross-conversation knowledge integration"""
        return [
            IntelligenceTest(
                test_id="elena_knowledge_integration_marine",
                test_name="Knowledge: Marine Science Integration",
                bot_name="elena",
                system_type="knowledge_integration",
                category="Knowledge Synthesis",
                setup_sequence=[
                    "Tell me about coral reefs",
                    "What about ocean acidification?",
                    "How does temperature affect marine life?",
                ],
                validation_query="How are all these topics connected?",
                expected_indicators=[
                    r"coral|acidification|temperature",
                    r"connect|related|link|affect",
                    r"marine|ocean|ecosystem",
                ],
                min_expected_matches=2
            ),
            IntelligenceTest(
                test_id="marcus_knowledge_integration_ai",
                test_name="Knowledge: AI Concepts Integration",
                bot_name="marcus",
                system_type="knowledge_integration",
                category="Knowledge Synthesis",
                setup_sequence=[
                    "Explain neural networks",
                    "What about transformers?",
                    "How does attention mechanism work?",
                ],
                validation_query="How do these AI concepts relate to each other?",
                expected_indicators=[
                    r"neural|transformer|attention",
                    r"connect|build|foundation|evolution",
                    r"concept|architecture|mechanism",
                ],
                min_expected_matches=2
            ),
        ]
    
    # ==================== CONTEXT AWARENESS TESTS ====================
    
    def define_context_awareness_tests(self) -> List[IntelligenceTest]:
        """Tests for proactive context awareness"""
        return [
            IntelligenceTest(
                test_id="elena_context_location",
                test_name="Context: Location-Based Awareness",
                bot_name="elena",
                system_type="context_awareness",
                category="Contextual Intelligence",
                setup_sequence=[
                    "I live in San Diego near the coast",
                    "What marine life can I see here?",
                ],
                validation_query="What do you know about my location?",
                expected_indicators=[
                    r"San Diego|coast|location",
                    r"marine|ocean|Pacific",
                ],
                min_expected_matches=1
            ),
            IntelligenceTest(
                test_id="marcus_context_expertise",
                test_name="Context: Expertise Level Awareness",
                bot_name="marcus",
                system_type="context_awareness",
                category="Contextual Intelligence",
                setup_sequence=[
                    "I'm a beginner in machine learning",
                    "Can you explain neural networks?",
                ],
                validation_query="What's my experience level with AI?",
                expected_indicators=[
                    r"beginner|new|start|learning",
                    r"machine learning|AI|neural network",
                ],
                min_expected_matches=1
            ),
        ]
    
    def get_all_tests(
        self, 
        bot_filter: Optional[List[str]] = None,
        system_filter: Optional[List[str]] = None
    ) -> List[IntelligenceTest]:
        """Get all intelligence tests with optional filters"""
        all_tests = []
        
        # Add all test types
        test_methods = [
            self.define_episodic_memory_tests,
            self.define_emotional_intelligence_tests,
            self.define_user_preferences_tests,
            self.define_conversation_intelligence_tests,
            self.define_temporal_awareness_tests,
            self.define_character_self_knowledge_tests,
            self.define_knowledge_integration_tests,
            self.define_context_awareness_tests,
        ]
        
        for method in test_methods:
            all_tests.extend(method())
        
        # Filter by bot if specified
        if bot_filter:
            all_tests = [t for t in all_tests if t.bot_name in bot_filter]
        
        # Filter by system type if specified
        if system_filter:
            all_tests = [t for t in all_tests if t.system_type in system_filter]
        
        return all_tests
    
    async def send_chat_message(self, bot_name: str, message: str) -> tuple[bool, str, Any]:
        """Send chat message to bot"""
        config = self.BOT_CONFIGS[bot_name]
        port = config["port"]
        user_id = self.get_user_id(bot_name)
        
        url = f"http://localhost:{port}/api/chat"
        payload = {"user_id": user_id, "message": message}
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return True, data.get("response", ""), data
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    async def run_intelligence_test(self, test: IntelligenceTest) -> IntelligenceTestResult:
        """Run a single intelligence test"""
        print(f"\n   🧠 Testing: {test.test_name}")
        print(f"      System: {test.system_type} | Category: {test.category}")
        
        try:
            # Setup phase
            print(f"      📝 Setup ({len(test.setup_sequence)} messages)...")
            for i, message in enumerate(test.setup_sequence, 1):
                success, response, _ = await self.send_chat_message(test.bot_name, message)
                if not success:
                    error_msg = f"Setup message {i} failed: {response}"
                    print(f"      🔴 ERROR: {error_msg}")
                    return IntelligenceTestResult(
                        test_id=test.test_id,
                        test_name=test.test_name,
                        bot_name=test.bot_name,
                        system_type=test.system_type,
                        success=False,
                        response=response,
                        matched_patterns=[],
                        missing_patterns=test.expected_indicators,
                        error=error_msg
                    )
                await asyncio.sleep(1)
            
            # Validation phase
            print(f"      🔍 Validation: \"{test.validation_query}\"")
            success, response, _ = await self.send_chat_message(test.bot_name, test.validation_query)
            
            if not success:
                return IntelligenceTestResult(
                    test_id=test.test_id,
                    test_name=test.test_name,
                    bot_name=test.bot_name,
                    system_type=test.system_type,
                    success=False,
                    response=response,
                    matched_patterns=[],
                    missing_patterns=test.expected_indicators,
                    error=f"Validation failed: {response}"
                )
            
            # Check indicators
            import re
            matched_patterns = []
            missing_patterns = []
            
            for pattern in test.expected_indicators:
                if re.search(pattern, response, re.IGNORECASE):
                    matched_patterns.append(pattern)
                else:
                    missing_patterns.append(pattern)
            
            test_passed = len(matched_patterns) >= test.min_expected_matches
            
            if test_passed:
                print(f"      ✅ PASS: {len(matched_patterns)}/{len(test.expected_indicators)} indicators (min: {test.min_expected_matches})")
            else:
                print(f"      ❌ FAIL: {len(matched_patterns)}/{len(test.expected_indicators)} indicators (needed: {test.min_expected_matches})")
            
            print(f"      Response: {response[:150]}{'...' if len(response) > 150 else ''}")
            
            if matched_patterns:
                print(f"      ✅ Found: {', '.join(matched_patterns[:3])}")
            if missing_patterns:
                print(f"      ❌ Missing: {', '.join(missing_patterns[:3])}")
            
            return IntelligenceTestResult(
                test_id=test.test_id,
                test_name=test.test_name,
                bot_name=test.bot_name,
                system_type=test.system_type,
                success=test_passed,
                response=response,
                matched_patterns=matched_patterns,
                missing_patterns=missing_patterns
            )
            
        except Exception as e:
            print(f"      🔴 ERROR: {str(e)}")
            return IntelligenceTestResult(
                test_id=test.test_id,
                test_name=test.test_name,
                bot_name=test.bot_name,
                system_type=test.system_type,
                success=False,
                response="",
                matched_patterns=[],
                missing_patterns=test.expected_indicators,
                error=str(e)
            )
    
    async def run_all_tests(
        self, 
        bot_filter: Optional[List[str]] = None,
        system_filter: Optional[List[str]] = None
    ):
        """Run all intelligence tests"""
        tests = self.get_all_tests(bot_filter, system_filter)
        
        print(f"\n🧠 WhisperEngine Intelligence System Regression Testing")
        print("=" * 80)
        print(f"Testing {len(tests)} intelligence scenarios")
        if bot_filter:
            print(f"Bot filter: {', '.join(bot_filter)}")
        if system_filter:
            print(f"System filter: {', '.join(system_filter)}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Group tests by bot
        tests_by_bot = {}
        for test in tests:
            if test.bot_name not in tests_by_bot:
                tests_by_bot[test.bot_name] = []
            tests_by_bot[test.bot_name].append(test)
        
        # Run tests
        for bot_name, bot_tests in tests_by_bot.items():
            config = self.BOT_CONFIGS[bot_name]
            print(f"\n🤖 {bot_name.upper()} - {len(bot_tests)} intelligence tests")
            print(f"   Port: {config['port']} | Archetype: {config['archetype']}")
            
            for test in bot_tests:
                result = await self.run_intelligence_test(test)
                self.results.append(result)
                await asyncio.sleep(2)
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success and not r.error)
        errors = sum(1 for r in self.results if r.error)
        
        print(f"\n{'=' * 80}")
        print(f"📊 INTELLIGENCE TEST SUMMARY")
        print(f"{'=' * 80}")
        print(f"Total Tests:    {total}")
        print(f"✅ Passed:      {passed}")
        print(f"❌ Failed:      {failed}")
        print(f"🔴 Errors:      {errors}")
        print(f"Success Rate:   {(passed/total*100) if total > 0 else 0:.1f}%")
        
        # Results by system type
        print(f"\n{'=' * 80}")
        print(f"📈 RESULTS BY INTELLIGENCE SYSTEM")
        print(f"{'=' * 80}")
        
        systems = sorted(set(r.system_type for r in self.results))
        for system in systems:
            system_results = [r for r in self.results if r.system_type == system]
            system_passed = sum(1 for r in system_results if r.success)
            status = "✅" if system_passed == len(system_results) else "⚠️"
            print(f"{status} {system:25} | {system_passed}/{len(system_results)} passed")
        
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
        
        print(f"\n{'=' * 80}")
        if failed == 0 and errors == 0:
            print(f"🎉 ALL INTELLIGENCE TESTS PASSED!")
        else:
            print(f"⚠️  SOME TESTS FAILED - Review details above")
        print(f"{'=' * 80}\n")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WhisperEngine Intelligence System Tests")
    parser.add_argument("--bots", type=str, help="Comma-separated list of bots (e.g., 'elena,marcus')")
    parser.add_argument("--systems", type=str, help="Comma-separated list of systems (e.g., 'episodic,preferences')")
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout in seconds")
    
    args = parser.parse_args()
    
    bot_filter = [b.strip().lower() for b in args.bots.split(",")] if args.bots else None
    system_filter = [s.strip().lower() for s in args.systems.split(",")] if args.systems else None
    
    tester = IntelligenceSystemTester(timeout=args.timeout)
    
    try:
        await tester.run_all_tests(bot_filter, system_filter)
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
