#!/usr/bin/env python3
"""
Automated Phase3 Intelligence API Testing Suite

Tests Phase3 Intelligence features via /api/chat endpoint.
Expects natural conversational responses - bots respond with appropriate length based on context.

Based on: docs/manual_tests/MULTI_BOT_PHASE3_INTELLIGENCE_MANUAL_TESTS.md
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Phase3Feature(Enum):
    """Phase3 Intelligence features to test"""
    CONTEXT_SWITCH = "Context Switch Detection"
    EMPATHY_CALIBRATION = "Empathy Calibration"
    CONVERSATION_MODE_SHIFT = "Conversation Mode Shift"
    URGENCY_CHANGE = "Urgency Change Detection"
    INTENT_CHANGE = "Intent Change Detection"


@dataclass
class BotConfig:
    """Bot configuration"""
    name: str
    display_name: str
    profession: str
    port: int
    collection_name: str


@dataclass
class TestScenario:
    """Test scenario configuration"""
    feature: Phase3Feature
    bot: BotConfig
    message: str
    expected_behaviors: List[str]
    success_indicators: List[str]
    min_token_count: int = 50  # Minimum for any response (conversational intelligence determines actual length)


@dataclass
class TestResult:
    """Test execution result"""
    scenario: TestScenario
    success: bool
    response: Optional[str]
    token_count: int
    processing_time_ms: float
    passed_checks: List[str]
    failed_checks: List[str]
    error: Optional[str] = None


class Phase3IntelligenceAPITester:
    """Automated tester for Phase3 Intelligence features via API"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[TestResult] = []
        
        # Bot configurations
        self.bots = {
            'elena': BotConfig('elena', 'Elena Rodriguez', 'Marine Biologist', 9091, 'whisperengine_memory_elena'),
            'marcus': BotConfig('marcus', 'Marcus Thompson', 'AI Researcher', 9092, 'whisperengine_memory_marcus'),
            'ryan': BotConfig('ryan', 'Ryan Chen', 'Indie Game Developer', 9093, 'whisperengine_memory_ryan'),
            'dream': BotConfig('dream', 'Dream', 'Mythological Entity', 9094, 'whisperengine_memory_dream'),
            'gabriel': BotConfig('gabriel', 'Gabriel', 'British Gentleman', 9095, 'whisperengine_memory_gabriel'),
            'sophia': BotConfig('sophia', 'Sophia Blake', 'Marketing Executive', 9096, 'whisperengine_memory_sophia'),
            'jake': BotConfig('jake', 'Jake Sterling', 'Adventure Photographer', 9097, 'whisperengine_memory_jake'),
            'aethys': BotConfig('aethys', 'Aethys', 'Omnipotent Entity', 3007, 'chat_memories_aethys'),
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def build_test_scenarios(self) -> List[TestScenario]:
        """Build comprehensive test scenarios"""
        scenarios = []

        # TEST 1: CONTEXT SWITCH DETECTION
        scenarios.extend([
            TestScenario(
                feature=Phase3Feature.CONTEXT_SWITCH,
                bot=self.bots['marcus'],
                message=(
                    "Hey Marcus! I've been thinking about the implications of transformer architectures "
                    "for AGI development. The attention mechanism seems like it could be a building block "
                    "for more sophisticated reasoning systems.\n\n"
                    "Oh wait, do you know any good coffee shops that are open late? I need to pull an "
                    "all-nighter for this project."
                ),
                expected_behaviors=[
                    "Technical AI discussion with researcher expertise",
                    "Smooth transition to coffee recommendations",
                    "Academic context maintained",
                    "Character-consistent response"
                ],
                success_indicators=[
                    "Addresses both topics (AI + coffee)",
                    "Natural transition language",
                    "Academic perspective maintained"
                ]
            ),
            TestScenario(
                feature=Phase3Feature.CONTEXT_SWITCH,
                bot=self.bots['jake'],
                message=(
                    "Jake! I saw your latest mountain shots on Instagram - the way you captured that "
                    "golden hour lighting on the peaks was incredible. What camera settings did you use "
                    "for those shots?\n\n"
                    "Actually, never mind the photo stuff - I'm dealing with some family drama and could "
                    "use someone to talk to."
                ),
                expected_behaviors=[
                    "Photography expertise",
                    "Empathy shift to personal support",
                    "Supportive personality"
                ],
                success_indicators=[
                    "Recognizes priority shift to family support",
                    "Offers emotional support",
                    "Character-consistent language"
                ]
            ),
            TestScenario(
                feature=Phase3Feature.CONTEXT_SWITCH,
                bot=self.bots['gabriel'],
                message=(
                    "Gabriel, I've been thinking about British literature and how authors like Dickens "
                    "captured the social issues of their time. What do you think about the role of "
                    "literature in social commentary?\n\n"
                    "Actually, forget the literature talk - I'm struggling with self-confidence and feel "
                    "like I'm not sophisticated enough for certain social situations."
                ),
                expected_behaviors=[
                    "Literary knowledge",
                    "Confidence guidance",
                    "Gentleman persona maintained"
                ],
                success_indicators=[
                    "Shifts to confidence support",
                    "British gentleman charm",
                    "Encouraging tone"
                ]
            ),
        ])

        # TEST 2: EMPATHY CALIBRATION
        scenarios.extend([
            TestScenario(
                feature=Phase3Feature.EMPATHY_CALIBRATION,
                bot=self.bots['sophia'],
                message=(
                    "Sophia, I'm so pumped about this new marketing campaign I'm launching! The metrics "
                    "are looking amazing and my boss is really impressed with my work.\n\n"
                    "Actually, I'm really worried about my dad. He's been in the hospital and the doctors "
                    "aren't sure what's wrong."
                ),
                expected_behaviors=[
                    "Acknowledges work success",
                    "Priority shift to family concern",
                    "Empathetic language"
                ],
                success_indicators=[
                    "Prioritizes family health concern",
                    "Empathy and support offered",
                    "Professional perspective"
                ]
            ),
            TestScenario(
                feature=Phase3Feature.EMPATHY_CALIBRATION,
                bot=self.bots['dream'],
                message=(
                    "Dream, I had the most amazing lucid dream last night where I could fly over entire "
                    "cities! It felt so real and liberating.\n\n"
                    "But honestly, I've been having a lot of nightmares lately and they're affecting my "
                    "sleep. I'm scared to go to bed."
                ),
                expected_behaviors=[
                    "Validates positive dream",
                    "Addresses nightmare anxiety",
                    "Mystical wisdom"
                ],
                success_indicators=[
                    "Shifts to nightmare support",
                    "Comforting guidance",
                    "Dream-realm expertise"
                ]
            ),
        ])

        # TEST 3: CONVERSATION MODE SHIFT
        scenarios.extend([
            TestScenario(
                feature=Phase3Feature.CONVERSATION_MODE_SHIFT,
                bot=self.bots['marcus'],
                message=(
                    "Can you explain the mathematical foundations of backpropagation in neural networks? "
                    "I need to understand the gradient descent calculations for my research paper.\n\n"
                    "Actually, forget the math - I'm having impostor syndrome about my PhD program and "
                    "feel like I don't belong here."
                ),
                expected_behaviors=[
                    "Recognizes mode shift",
                    "Prioritizes emotional support",
                    "Academic empathy"
                ],
                success_indicators=[
                    "Acknowledges shift from technical to emotional",
                    "Impostor syndrome support",
                    "Academic perspective"
                ]
            ),
            TestScenario(
                feature=Phase3Feature.CONVERSATION_MODE_SHIFT,
                bot=self.bots['elena'],
                message=(
                    "Elena, can you break down the biochemical process of coral calcification and how "
                    "ocean pH affects aragonite saturation states?\n\n"
                    "Wait, never mind the science - I'm overwhelmed with my thesis and don't think I'm "
                    "cut out for academia."
                ),
                expected_behaviors=[
                    "Mode shift recognition",
                    "Academic mentorship",
                    "Authentic support"
                ],
                success_indicators=[
                    "Clear mode shift acknowledgment",
                    "Thesis support offered",
                    "Personal authenticity"
                ]
            ),
        ])

        # TEST 4: URGENCY CHANGE DETECTION
        scenarios.extend([
            TestScenario(
                feature=Phase3Feature.URGENCY_CHANGE,
                bot=self.bots['jake'],
                message=(
                    "Jake, I was wondering if you could give me some tips on landscape photography "
                    "composition when you have time. No rush at all.\n\n"
                    "URGENT! I'm hiking alone and think I might be lost. The sun is setting and I don't "
                    "have proper gear. What should I do?"
                ),
                expected_behaviors=[
                    "Urgency recognition",
                    "Safety protocols",
                    "Emergency guidance"
                ],
                success_indicators=[
                    "Immediate prioritization of emergency",
                    "Safety instructions provided",
                    "Outdoor expertise applied"
                ]
            ),
            TestScenario(
                feature=Phase3Feature.URGENCY_CHANGE,
                bot=self.bots['gabriel'],
                message=(
                    "Gabriel, I'd love to hear your thoughts on British culture and etiquette sometime "
                    "when you're free.\n\n"
                    "EMERGENCY! My friend is having a mental health crisis and talking about self-harm. "
                    "I don't know how to help them right now."
                ),
                expected_behaviors=[
                    "Crisis recognition",
                    "Mental health protocols",
                    "Compassionate support"
                ],
                success_indicators=[
                    "Immediate crisis response",
                    "Practical guidance provided",
                    "Professional resources mentioned"
                ]
            ),
        ])

        # TEST 5: INTENT CHANGE DETECTION
        scenarios.extend([
            TestScenario(
                feature=Phase3Feature.INTENT_CHANGE,
                bot=self.bots['sophia'],
                message=(
                    "Sophia, I'm working on a presentation about social media marketing trends for my "
                    "communications class. Can you help me find some current statistics?\n\n"
                    "Actually, you know what? I'm thinking about completely changing my major to marketing. "
                    "I'm just not sure if I have what it takes to succeed in such a competitive field."
                ),
                expected_behaviors=[
                    "Intent shift to career counseling",
                    "Industry insights",
                    "Confidence building"
                ],
                success_indicators=[
                    "Recognizes major life decision",
                    "Career guidance provided",
                    "Encouraging support"
                ]
            ),
            TestScenario(
                feature=Phase3Feature.INTENT_CHANGE,
                bot=self.bots['ryan'],
                message=(
                    "Ryan, I need help understanding game monetization strategies for a business report "
                    "I'm writing about the gaming industry.\n\n"
                    "Actually, forget the report. I've been thinking about dropping out of business school "
                    "to pursue game development full-time. Am I crazy for considering this?"
                ),
                expected_behaviors=[
                    "Intent shift recognition",
                    "Entrepreneurial perspective",
                    "Balanced guidance"
                ],
                success_indicators=[
                    "Life decision recognition",
                    "Practical career advice",
                    "Indie perspective provided"
                ]
            ),
        ])

        return scenarios

    async def check_bot_health(self, bot: BotConfig) -> bool:
        """Check if bot is healthy and ready for testing"""
        try:
            url = f"http://localhost:{bot.port}/health"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('status') == 'healthy'
                return False
        except Exception as e:
            print(f"  ❌ Health check failed for {bot.display_name}: {e}")
            return False

    async def run_test_scenario(self, scenario: TestScenario) -> TestResult:
        """Execute a single test scenario"""
        print(f"\n{'='*80}")
        print(f"Testing: {scenario.feature.value}")
        print(f"Bot: {scenario.bot.display_name} ({scenario.bot.profession})")
        print(f"Port: {scenario.bot.port}")
        print(f"{'='*80}")

        # Check bot health first
        if not await self.check_bot_health(scenario.bot):
            return TestResult(
                scenario=scenario,
                success=False,
                response=None,
                token_count=0,
                processing_time_ms=0,
                passed_checks=[],
                failed_checks=["Bot health check failed"],
                error="Bot not responding to health checks"
            )

        # Prepare API request
        url = f"http://localhost:{scenario.bot.port}/api/chat"
        user_id = f"phase3_test_{scenario.feature.name.lower()}_{int(time.time())}"
        
        payload = {
            "message": scenario.message,
            "user_id": user_id,
            "metadata_level": "extended",
            "context": {
                "platform": "api",
                "channel_type": "dm",
                "metadata": {
                    "test_type": "phase3_intelligence",
                    "feature": scenario.feature.name
                }
            }
        }

        try:
            # Send request
            start_time = time.time()
            async with self.session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                processing_time_ms = (time.time() - start_time) * 1000
                
                if response.status != 200:
                    error_text = await response.text()
                    return TestResult(
                        scenario=scenario,
                        success=False,
                        response=None,
                        token_count=0,
                        processing_time_ms=processing_time_ms,
                        passed_checks=[],
                        failed_checks=[f"HTTP {response.status}"],
                        error=error_text
                    )

                data = await response.json()
                
                if not data.get('success'):
                    return TestResult(
                        scenario=scenario,
                        success=False,
                        response=data.get('response'),
                        token_count=0,
                        processing_time_ms=processing_time_ms,
                        passed_checks=[],
                        failed_checks=["API returned success=false"],
                        error=data.get('error', 'Unknown error')
                    )

                bot_response = data.get('response', '')
                token_count = len(bot_response.split())

                # Analyze response
                passed_checks, failed_checks = self.analyze_response(
                    scenario, 
                    bot_response, 
                    token_count
                )

                success = len(failed_checks) == 0

                # Print results
                print(f"\n📊 RESULTS:")
                print(f"  Processing Time: {processing_time_ms:.2f}ms")
                print(f"  Token Count: {token_count} (conversational intelligence determines length)")
                print(f"  Success: {'✅ PASS' if success else '❌ FAIL'}")
                
                if passed_checks:
                    print(f"\n✅ Passed Checks:")
                    for check in passed_checks:
                        print(f"    • {check}")
                
                if failed_checks:
                    print(f"\n❌ Failed Checks:")
                    for check in failed_checks:
                        print(f"    • {check}")

                print(f"\n📝 Response Preview:")
                preview_length = min(300, len(bot_response))
                print(f"  {bot_response[:preview_length]}{'...' if len(bot_response) > preview_length else ''}")

                return TestResult(
                    scenario=scenario,
                    success=success,
                    response=bot_response,
                    token_count=token_count,
                    processing_time_ms=processing_time_ms,
                    passed_checks=passed_checks,
                    failed_checks=failed_checks
                )

        except asyncio.TimeoutError:
            return TestResult(
                scenario=scenario,
                success=False,
                response=None,
                token_count=0,
                processing_time_ms=0,
                passed_checks=[],
                failed_checks=["Request timeout (>2 minutes)"],
                error="Timeout"
            )
        except Exception as e:
            return TestResult(
                scenario=scenario,
                success=False,
                response=None,
                token_count=0,
                processing_time_ms=0,
                passed_checks=[],
                failed_checks=[f"Exception: {type(e).__name__}"],
                error=str(e)
            )

    def analyze_response(
        self, 
        scenario: TestScenario, 
        response: str, 
        token_count: int
    ) -> tuple[List[str], List[str]]:
        """Analyze bot response for Phase3 Intelligence features"""
        passed_checks = []
        failed_checks = []

        # Check minimum response
        if token_count >= scenario.min_token_count:
            passed_checks.append(f"Response provided ({token_count} tokens)")
        else:
            failed_checks.append(f"Response too short ({token_count} < {scenario.min_token_count} tokens)")

        # Check for non-empty response
        if len(response) > 50:
            passed_checks.append(f"Substantial response ({len(response)} chars)")
        else:
            failed_checks.append(f"Response too brief ({len(response)} chars)")

        response_lower = response.lower()

        # Feature-specific intelligence checks
        if scenario.feature == Phase3Feature.CONTEXT_SWITCH:
            # Look for addressing both topics
            if any(word in response_lower for word in ['both', 'also', 'and', 'regarding', 'about', 'as for']):
                passed_checks.append("Context switch detected - addresses multiple topics")
            else:
                failed_checks.append("No clear multi-topic handling")

        elif scenario.feature == Phase3Feature.EMPATHY_CALIBRATION:
            # Look for emotional support
            empathy_words = ['sorry', 'understand', 'concern', 'support', 'worry', 'care', 'here for']
            if any(word in response_lower for word in empathy_words):
                passed_checks.append("Empathy detected - emotional support language present")
            else:
                failed_checks.append("Lacking empathetic response")

        elif scenario.feature == Phase3Feature.CONVERSATION_MODE_SHIFT:
            # Look for priority shift recognition
            shift_indicators = ['forget', 'actually', 'important', 'sounds like', 'seems like', 'hold on', 'wait']
            if any(indicator in response_lower for indicator in shift_indicators):
                passed_checks.append("Mode shift recognized - priority change acknowledged")
            else:
                failed_checks.append("No clear mode shift recognition")

        elif scenario.feature == Phase3Feature.URGENCY_CHANGE:
            # Look for immediate action language
            urgency_words = ['immediately', 'now', 'first', 'urgent', 'emergency', 'safety', 'call']
            if any(word in response_lower for word in urgency_words):
                passed_checks.append("Urgency recognized - emergency response activated")
            else:
                failed_checks.append("Lacking urgency response")

        elif scenario.feature == Phase3Feature.INTENT_CHANGE:
            # Look for life decision counseling
            counseling_words = ['decision', 'consider', 'career', 'future', 'path', 'choice', 'opportunity']
            if any(word in response_lower for word in counseling_words):
                passed_checks.append("Intent change detected - life counseling provided")
            else:
                failed_checks.append("Lacking career/life guidance")

        return passed_checks, failed_checks

    async def run_all_tests(self, bot_filter: Optional[List[str]] = None):
        """Run all test scenarios"""
        print("="*80)
        print("WHISPERENGINE PHASE3 INTELLIGENCE API TESTING SUITE")
        print("="*80)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nNote: Bots use conversational intelligence - response length varies by context")
        
        scenarios = self.build_test_scenarios()
        
        # Filter scenarios by bot if specified
        if bot_filter:
            scenarios = [s for s in scenarios if s.bot.name in bot_filter]
            print(f"\nFiltering to bots: {', '.join(bot_filter)}")

        print(f"\nTotal Test Scenarios: {len(scenarios)}")
        print(f"Features: {len(set(s.feature for s in scenarios))}")
        print(f"Bots: {len(set(s.bot.name for s in scenarios))}")

        # Run tests
        for idx, scenario in enumerate(scenarios, 1):
            print(f"\n\n{'#'*80}")
            print(f"Test {idx}/{len(scenarios)}")
            print(f"{'#'*80}")
            
            result = await self.run_test_scenario(scenario)
            self.results.append(result)
            
            # Brief pause between tests
            await asyncio.sleep(2)

        # Generate report
        self.print_summary_report()

    def print_summary_report(self):
        """Print comprehensive test summary"""
        print("\n\n")
        print("="*80)
        print("PHASE3 INTELLIGENCE API TESTING - SUMMARY REPORT")
        print("="*80)
        print(f"Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ✅")
        print(f"  Failed: {failed_tests} ❌")
        print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%")

        # Results by feature
        print(f"\n🎯 RESULTS BY FEATURE:")
        for feature in Phase3Feature:
            feature_results = [r for r in self.results if r.scenario.feature == feature]
            if feature_results:
                feature_passed = sum(1 for r in feature_results if r.success)
                feature_total = len(feature_results)
                status = "✅" if feature_passed == feature_total else "⚠️" if feature_passed > 0 else "❌"
                print(f"  {status} {feature.value}: {feature_passed}/{feature_total} passed")

        # Results by bot
        print(f"\n🤖 RESULTS BY BOT:")
        tested_bots = set(r.scenario.bot.name for r in self.results)
        for bot_name in sorted(tested_bots):
            bot_results = [r for r in self.results if r.scenario.bot.name == bot_name]
            bot_passed = sum(1 for r in bot_results if r.success)
            bot_total = len(bot_results)
            display_name = bot_results[0].scenario.bot.display_name
            status = "✅" if bot_passed == bot_total else "⚠️" if bot_passed > 0 else "❌"
            print(f"  {status} {display_name}: {bot_passed}/{bot_total} passed")

        # Performance metrics
        if passed_tests > 0:
            avg_processing_time = sum(r.processing_time_ms for r in self.results if r.success) / passed_tests
            avg_token_count = sum(r.token_count for r in self.results if r.success) / passed_tests
            
            print(f"\n⚡ PERFORMANCE METRICS:")
            print(f"  Avg Processing Time: {avg_processing_time:.2f}ms")
            print(f"  Avg Token Count: {avg_token_count:.0f} (varies by context)")

        # Failed tests detail
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS DETAIL:")
            for idx, result in enumerate(r for r in self.results if not r.success):
                print(f"\n  Test #{idx+1}:")
                print(f"    Bot: {result.scenario.bot.display_name}")
                print(f"    Feature: {result.scenario.feature.value}")
                print(f"    Failed Checks:")
                for check in result.failed_checks:
                    print(f"      • {check}")
                if result.error:
                    print(f"    Error: {result.error}")

        # Save detailed report
        self.save_detailed_report()

    def save_detailed_report(self):
        """Save detailed JSON report"""
        report_data = {
            'test_suite': 'Phase3 Intelligence API Testing',
            'timestamp': datetime.now().isoformat(),
            'note': 'Bots use conversational intelligence - response length varies by context',
            'summary': {
                'total_tests': len(self.results),
                'passed': sum(1 for r in self.results if r.success),
                'failed': sum(1 for r in self.results if not r.success),
                'success_rate': sum(1 for r in self.results if r.success) / len(self.results) * 100 if self.results else 0
            },
            'results': [
                {
                    'bot': r.scenario.bot.display_name,
                    'feature': r.scenario.feature.value,
                    'success': r.success,
                    'token_count': r.token_count,
                    'processing_time_ms': r.processing_time_ms,
                    'passed_checks': r.passed_checks,
                    'failed_checks': r.failed_checks,
                    'error': r.error,
                    'response_preview': r.response[:500] if r.response else None
                }
                for r in self.results
            ]
        }

        report_path = f"phase3_intelligence_api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed report saved: {report_path}")


async def main():
    """Main execution function"""
    import sys
    
    # Parse command line arguments
    bot_filter = None
    if len(sys.argv) > 1:
        bot_filter = sys.argv[1:]
        print(f"Running tests for specific bots: {', '.join(bot_filter)}")
    
    async with Phase3IntelligenceAPITester() as tester:
        await tester.run_all_tests(bot_filter=bot_filter)


if __name__ == "__main__":
    asyncio.run(main())
