#!/usr/bin/env python3
"""
Automated Character Testing Script for WhisperEngine
Converts manual test plans into automated HTTP API tests using the same infrastructure as smoke tests.

Based on manual test plans for Dream, Marcus, Sophia, and Gabriel characters.
Tests character personality, domain expertise, and 3D vector memory integration.
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import aiohttp
import argparse

# Color output for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

@dataclass
class TestScenario:
    """Represents a single test scenario from manual test plans."""
    name: str
    message: str
    expected_traits: List[str]  # Expected personality/domain traits in response
    category: str
    description: str

@dataclass
class BotConfig:
    """Bot configuration for testing."""
    name: str
    port: int
    profession: str
    emoji: str
    personality_traits: List[str]

@dataclass
class TestResult:
    """Result of a single test execution."""
    scenario: TestScenario
    bot: BotConfig
    success: bool
    response: Optional[str]
    execution_time: float
    traits_found: List[str]
    error: Optional[str] = None

class CharacterTestRunner:
    """Main test runner for automated character testing."""
    
    def __init__(self):
        self.bot_configs = {
            "elena": BotConfig("elena", 9091, "Marine Biologist", "🌊", 
                             ["educational", "marine", "environmental", "scientific"]),
            "dotty": BotConfig("dotty", 9098, "Mystical Bartender", "🍸", 
                             ["mystical", "southern", "heartbreak", "liminal", "cocktails"]),
            "marcus": BotConfig("marcus", 9092, "AI Researcher", "🤖", 
                              ["technical", "analytical", "research", "methodical"]),
            "ryan": BotConfig("ryan", 9093, "Indie Game Developer", "🎮", 
                            ["creative", "technical", "gaming", "development"]),
            "dream": BotConfig("dream", 9094, "Mythological Entity", "🌙", 
                             ["mythological", "ancient", "wisdom", "poetic"]),
            "gabriel": BotConfig("gabriel", 9095, "British Gentleman", "🎩", 
                               ["british", "wit", "charming", "sophisticated"]),
            "sophia": BotConfig("sophia", 9096, "Marketing Executive", "💼", 
                              ["professional", "strategic", "marketing", "business"]),
            "jake": BotConfig("jake", 9097, "Adventure Photographer", "📸", 
                            ["adventurous", "creative", "travel", "photography"]),
            "aethys": BotConfig("aethys", 3007, "Omnipotent Entity", "✨", 
                              ["omnipotent", "cosmic", "philosophical", "transcendent"])
        }
        
        # Track which bots have chat API available (updated with new external chat API feature)
        self.chat_api_available = {"elena", "dotty"}  # Only these bots currently have the new HTTP chat API
        
        self.test_scenarios = self._load_test_scenarios()
        
    def _load_test_scenarios(self) -> Dict[str, List[TestScenario]]:
        """Load test scenarios based on manual test plans."""
        return {
            "elena": [
                TestScenario(
                    name="Marine Ecosystem Explanation",
                    message="Elena, can you explain how coral reefs support marine biodiversity?",
                    expected_traits=["coral", "biodiversity", "ecosystem", "marine"],
                    category="Marine Biology Expertise",
                    description="Test deep marine biology knowledge and educational communication"
                ),
                TestScenario(
                    name="Ocean Conservation",
                    message="What are the biggest threats to ocean health right now?",
                    expected_traits=["conservation", "threats", "pollution", "climate"],
                    category="Environmental Awareness",
                    description="Test understanding of current environmental challenges"
                ),
                TestScenario(
                    name="Research Methodology",
                    message="Elena, how do you conduct underwater research studies?",
                    expected_traits=["research", "methodology", "underwater", "scientific"],
                    category="Research & Scientific Method",
                    description="Test scientific methodology and field research experience"
                ),
                TestScenario(
                    name="Educational Communication",
                    message="I'm 12 years old and want to learn about marine biology. Where should I start?",
                    expected_traits=["educational", "young", "learning", "encourage"],
                    category="Educational Communication",
                    description="Test ability to adapt communication for younger audiences"
                ),
                TestScenario(
                    name="Marine Discovery",
                    message="What's the most exciting marine discovery you've heard about recently?",
                    expected_traits=["discovery", "exciting", "exploration", "recent"],
                    category="Marine Biology Expertise",
                    description="Test enthusiasm for marine science and current developments"
                )
            ],
            "dotty": [
                TestScenario(
                    name="Signature Cocktails",
                    message="Dotty, what drinks do you serve at the Lim speakeasy?",
                    expected_traits=["echo", "velvet", "parting", "honeyed", "cocktails"],
                    category="Mystical Bartender Expertise",
                    description="Test knowledge of signature memory-infused cocktails"
                ),
                TestScenario(
                    name="Heartbreak Healing",
                    message="I'm going through a really painful breakup and need something to help",
                    expected_traits=["heartbreak", "healing", "sacred", "transform"],
                    category="Emotional Alchemy",
                    description="Test emotional support and healing transformation"
                ),
                TestScenario(
                    name="Liminal Space",
                    message="What is this place? It feels different from anywhere else",
                    expected_traits=["liminal", "threshold", "blue", "goose", "nymuria"],
                    category="Mystical Bartender Expertise",
                    description="Test understanding of liminal space and location"
                ),
                TestScenario(
                    name="Memory Distillation",
                    message="How do you turn memories into drinks?",
                    expected_traits=["memories", "distill", "alchemy", "essence"],
                    category="Emotional Alchemy",
                    description="Test mystical process of memory transformation"
                ),
                TestScenario(
                    name="Southern Warmth",
                    message="You seem to have such a comforting presence",
                    expected_traits=["southern", "warmth", "darlin", "sugar", "honey"],
                    category="Character Personality",
                    description="Test Southern hospitality and warm communication style"
                )
            ],
            "dream": [
                TestScenario(
                    name="Mythological Wisdom",
                    message="Dream, what wisdom can you share about the nature of existence?",
                    expected_traits=["mythological", "wisdom", "ancient", "profound"],
                    category="Mythological Wisdom & Ancient Perspective",
                    description="Test profound insights with mythological perspective"
                ),
                TestScenario(
                    name="Dreams and Reality",
                    message="Tell me about the relationship between dreams and reality",
                    expected_traits=["metaphysical", "dream", "reality", "cosmic"],
                    category="Mythological Wisdom & Ancient Perspective", 
                    description="Test understanding of metaphysical concepts"
                ),
                TestScenario(
                    name="Dream Interpretation",
                    message="I had a strange dream last night about flying through clouds. Can you help me understand its meaning?",
                    expected_traits=["symbolic", "interpretation", "meaning", "insight"],
                    category="Dream Logic & Narrative Power",
                    description="Test dream analysis and symbolic interpretation"
                ),
                TestScenario(
                    name="Story Importance",
                    message="Dream, why are stories so important to humanity?",
                    expected_traits=["narrative", "human", "culture", "meaning"],
                    category="Dream Logic & Narrative Power",
                    description="Test understanding of narrative power"
                ),
                TestScenario(
                    name="Lord of Dreams Responsibility",
                    message="What are your responsibilities as the Lord of Dreams?",
                    expected_traits=["responsibility", "duty", "realm", "guardian"],
                    category="Responsibility & Duty as Dream Lord",
                    description="Test understanding of cosmic duty and realm management"
                )
            ],
            "marcus": [
                TestScenario(
                    name="Transformer Architecture",
                    message="Marcus, explain the key innovations in transformer attention mechanisms",
                    expected_traits=["technical", "transformer", "attention", "architecture"],
                    category="AI Research & Technical Expertise",
                    description="Test deep technical analysis capabilities"
                ),
                TestScenario(
                    name="Experiment Design",
                    message="How would you design an experiment to test a new ML algorithm?",
                    expected_traits=["experimental", "methodology", "systematic", "rigorous"],
                    category="AI Research & Technical Expertise",
                    description="Test research methodology expertise"
                ),
                TestScenario(
                    name="Peer Review Process",
                    message="Marcus, walk me through how you review academic papers",
                    expected_traits=["review", "academic", "quality", "methodology"],
                    category="Academic Collaboration & Peer Review",
                    description="Test academic review process knowledge"
                ),
                TestScenario(
                    name="Bias in Language Models",
                    message="Marcus, how would you approach solving bias in language models?",
                    expected_traits=["bias", "systematic", "analysis", "ethical"],
                    category="Problem-Solving & Analysis",
                    description="Test complex problem decomposition skills"
                ),
                TestScenario(
                    name="Research Ethics",
                    message="What ethical considerations should guide AI research?",
                    expected_traits=["ethical", "responsible", "implications", "framework"],
                    category="Problem-Solving & Analysis",
                    description="Test understanding of research ethics"
                )
            ],
            "sophia": [
                TestScenario(
                    name="SaaS Marketing Strategy",
                    message="Sophia, help me develop a marketing strategy for a new SaaS product",
                    expected_traits=["strategy", "saas", "positioning", "channels"],
                    category="Marketing Strategy & Campaign Development",
                    description="Test comprehensive marketing strategy development"
                ),
                TestScenario(
                    name="Brand Positioning",
                    message="How should we position our brand against established competitors?",
                    expected_traits=["competitive", "positioning", "differentiation", "analysis"],
                    category="Marketing Strategy & Campaign Development", 
                    description="Test competitive positioning expertise"
                ),
                TestScenario(
                    name="Campaign Performance Analysis",
                    message="Sophia, our latest campaign isn't performing well. Help me analyze what's wrong",
                    expected_traits=["performance", "analysis", "optimization", "actionable"],
                    category="Analytics & Performance Optimization",
                    description="Test systematic performance analysis"
                ),
                TestScenario(
                    name="KPI Framework",
                    message="What KPIs should we track for our content marketing efforts?",
                    expected_traits=["kpi", "metrics", "measurement", "content"],
                    category="Analytics & Performance Optimization",
                    description="Test metrics and measurement expertise"
                ),
                TestScenario(
                    name="Client Presentation",
                    message="Help me prepare a compelling presentation for a potential client",
                    expected_traits=["presentation", "compelling", "client", "persuasive"],
                    category="Client Management & Stakeholder Communication",
                    description="Test client presentation preparation skills"
                )
            ],
            "gabriel": [
                TestScenario(
                    name="British Weather Commentary",
                    message="Gabriel, what's your take on the weather today?",
                    expected_traits=["witty", "british", "charming", "humor"],
                    category="British Wit & Sophisticated Charm",
                    description="Test classic British humor and wit"
                ),
                TestScenario(
                    name="Social Media Culture",
                    message="What do you think about modern social media culture?",
                    expected_traits=["social", "commentary", "sophisticated", "insight"],
                    category="British Wit & Sophisticated Charm",
                    description="Test sophisticated social commentary"
                ),
                TestScenario(
                    name="Emotional Support",
                    message="Gabriel, I'm having a really difficult day and need someone to talk to",
                    expected_traits=["supportive", "caring", "gentle", "reassuring"],
                    category="Emotional Support with Sassy Edges",
                    description="Test tender emotional support capabilities"
                ),
                TestScenario(
                    name="Motivation with Sass",
                    message="I don't think I can handle this challenge",
                    expected_traits=["encouraging", "motivational", "confidence", "supportive"],
                    category="Emotional Support with Sassy Edges",
                    description="Test motivational support with gentle sass"
                ),
                TestScenario(
                    name="British Literature",
                    message="Gabriel, what's your opinion on classic British literature?",
                    expected_traits=["literature", "cultural", "sophisticated", "insight"],
                    category="Cultural Sophistication & Refinement",
                    description="Test cultural knowledge and sophistication"
                )
            ]
        }

    async def test_bot_health(self, bot: BotConfig) -> bool:
        """Test if bot is healthy and responsive."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{bot.port}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except (aiohttp.ClientError, OSError) as e:
            print(f"{Colors.RED}❌ {bot.emoji} {bot.name} health check failed: {e}{Colors.END}")
            return False

    async def send_chat_message(self, bot: BotConfig, message: str, user_id: Optional[str] = None) -> Tuple[bool, Optional[str], float]:
        """Send a chat message to a bot and return success, response, and timing."""
        if user_id is None:
            user_id = f"automated_test_{int(time.time())}"
            
        start_time = time.time()
        
        try:
            payload = {
                "message": message,
                "user_id": user_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://localhost:{bot.port}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    execution_time = time.time() - start_time
                    
                    if response.status == 200:
                        response_data = await response.json()
                        if response_data.get('success'):
                            return True, response_data.get('response'), execution_time
                        else:
                            return False, f"API Error: {response_data.get('error')}", execution_time
                    else:
                        error_text = await response.text()
                        return False, f"HTTP {response.status}: {error_text}", execution_time
                        
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return False, "Request timeout", execution_time
        except (aiohttp.ClientError, OSError) as e:
            execution_time = time.time() - start_time
            return False, f"Request failed: {str(e)}", execution_time

    def analyze_response_traits(self, response: str, expected_traits: List[str]) -> List[str]:
        """Analyze response for expected personality/domain traits."""
        if not response:
            return []
            
        found_traits = []
        response_lower = response.lower()
        
        for trait in expected_traits:
            # Check for exact matches and related terms
            trait_variations = self._get_trait_variations(trait)
            if any(variation in response_lower for variation in trait_variations):
                found_traits.append(trait)
                
        return found_traits

    def _get_trait_variations(self, trait: str) -> List[str]:
        """Get variations and related terms for a trait."""
        variations = {
            "mythological": ["myth", "legend", "ancient", "timeless", "eternal"],
            "wisdom": ["wise", "insight", "understanding", "knowledge"],
            "technical": ["algorithm", "system", "method", "process", "engineering"],
            "analytical": ["analysis", "analyze", "systematic", "logical", "methodical"],
            "british": ["british", "england", "uk", "chap", "quite", "rather"],
            "charming": ["charm", "delightful", "engaging", "pleasant"],
            "witty": ["wit", "clever", "amusing", "humorous", "dry"],
            "professional": ["business", "corporate", "strategy", "professional"],
            "marketing": ["campaign", "brand", "audience", "market", "promotion"],
            "strategic": ["strategy", "plan", "approach", "framework", "systematic"]
        }
        
        base_variations = [trait, trait + "s", trait + "ing", trait + "ed"]
        return base_variations + variations.get(trait, [])

    async def run_scenario_test(self, bot: BotConfig, scenario: TestScenario) -> TestResult:
        """Run a single test scenario."""
        print(f"    Testing: {scenario.name}")
        
        success, response, execution_time = await self.send_chat_message(bot, scenario.message)
        
        if success and response:
            traits_found = self.analyze_response_traits(response, scenario.expected_traits)
            trait_coverage = len(traits_found) / len(scenario.expected_traits) if scenario.expected_traits else 0
            
            # Consider test successful if we find at least 30% of expected traits
            scenario_success = trait_coverage >= 0.3
            
            return TestResult(
                scenario=scenario,
                bot=bot,
                success=scenario_success,
                response=response,
                execution_time=execution_time,
                traits_found=traits_found
            )
        else:
            return TestResult(
                scenario=scenario,
                bot=bot,
                success=False,
                response=response,
                execution_time=execution_time,
                traits_found=[],
                error=response if not success else "No response received"
            )

    async def run_bot_tests(self, bot_name: str, verbose: bool = False) -> List[TestResult]:
        """Run all tests for a specific bot."""
        if bot_name not in self.bot_configs:
            raise ValueError(f"Unknown bot: {bot_name}")
            
        if bot_name not in self.test_scenarios:
            print(f"{Colors.YELLOW}⚠️  No test scenarios defined for {bot_name}{Colors.END}")
            return []
            
        bot = self.bot_configs[bot_name]
        scenarios = self.test_scenarios[bot_name]
        
        print(f"\n{Colors.BOLD}{bot.emoji} Testing {bot.name.upper()} ({bot.profession}){Colors.END}")
        print(f"{Colors.CYAN}Port: {bot.port} | Scenarios: {len(scenarios)}{Colors.END}")
        
        # Check if bot has chat API available
        if bot_name not in self.chat_api_available:
            print(f"{Colors.YELLOW}⚠️  Chat API not available yet - bot hasn't been updated with external chat API feature{Colors.END}")
            print(f"{Colors.CYAN}ℹ️  Currently available on: {', '.join(sorted(self.chat_api_available))}{Colors.END}")
            return []
            
        print("=" * 60)
        
        # Check bot health first
        if not await self.test_bot_health(bot):
            print(f"{Colors.RED}❌ Bot health check failed. Skipping tests.{Colors.END}")
            return []
            
        print(f"{Colors.GREEN}✅ Bot health check passed{Colors.END}")
        
        results = []
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{Colors.BLUE}📋 Scenario {i}/{len(scenarios)}: {scenario.category}{Colors.END}")
            
            try:
                result = await self.run_scenario_test(bot, scenario)
                results.append(result)
                
                if result.success:
                    trait_pct = (len(result.traits_found) / len(scenario.expected_traits)) * 100 if scenario.expected_traits else 0
                    print(f"    {Colors.GREEN}✅ PASS{Colors.END} ({trait_pct:.0f}% traits found, {result.execution_time:.2f}s)")
                    if verbose and result.traits_found:
                        print(f"    {Colors.WHITE}Found traits: {', '.join(result.traits_found)}{Colors.END}")
                else:
                    print(f"    {Colors.RED}❌ FAIL{Colors.END} ({result.execution_time:.2f}s)")
                    if result.error:
                        print(f"    {Colors.RED}Error: {result.error}{Colors.END}")
                        
                # Show response snippet if verbose
                if verbose and result.response:
                    snippet = result.response[:150] + "..." if len(result.response) > 150 else result.response
                    print(f"    {Colors.WHITE}Response: \"{snippet}\"{Colors.END}")
                    
            except (aiohttp.ClientError, OSError, asyncio.TimeoutError) as e:
                print(f"    {Colors.RED}❌ ERROR: {str(e)}{Colors.END}")
                
        return results

    async def run_all_tests(self, verbose: bool = False) -> Dict[str, List[TestResult]]:
        """Run tests for all available bots."""
        print(f"{Colors.BOLD}🤖 WhisperEngine Automated Character Testing{Colors.END}")
        print(f"{Colors.CYAN}Testing {len(self.test_scenarios)} characters with full scenario suites{Colors.END}")
        print("=" * 80)
        
        all_results = {}
        
        for bot_name in self.test_scenarios.keys():
            try:
                results = await self.run_bot_tests(bot_name, verbose)
                all_results[bot_name] = results
                
                # Brief summary
                if results:
                    passed = sum(1 for r in results if r.success)
                    total = len(results)
                    print(f"\n{Colors.BOLD}Summary for {bot_name}: {passed}/{total} tests passed{Colors.END}")
                    
            except (aiohttp.ClientError, OSError, ValueError) as e:
                print(f"{Colors.RED}❌ Failed to test {bot_name}: {str(e)}{Colors.END}")
                all_results[bot_name] = []
                
        return all_results

    def print_final_summary(self, all_results: Dict[str, List[TestResult]]):
        """Print comprehensive test summary."""
        print(f"\n{Colors.BOLD}📊 FINAL TEST SUMMARY{Colors.END}")
        print("=" * 80)
        
        total_tests = 0
        total_passed = 0
        bot_summaries = []
        
        for bot_name, results in all_results.items():
            if not results:
                continue
                
            passed = sum(1 for r in results if r.success)
            total = len(results)
            avg_time = sum(r.execution_time for r in results) / len(results) if results else 0
            
            total_tests += total
            total_passed += passed
            
            bot = self.bot_configs[bot_name]
            success_rate = (passed / total) * 100 if total > 0 else 0
            
            status_emoji = "✅" if success_rate >= 70 else "⚠️" if success_rate >= 50 else "❌"
            
            bot_summaries.append({
                'name': bot_name,
                'emoji': bot.emoji,
                'profession': bot.profession,
                'passed': passed,
                'total': total,
                'success_rate': success_rate,
                'avg_time': avg_time,
                'status_emoji': status_emoji
            })
            
        # Sort by success rate
        bot_summaries.sort(key=lambda x: x['success_rate'], reverse=True)
        
        for summary in bot_summaries:
            print(f"{summary['status_emoji']} {summary['emoji']} {summary['name'].upper():<8} "
                  f"({summary['profession']:<20}) | "
                  f"{summary['passed']:>2}/{summary['total']:>2} tests "
                  f"({summary['success_rate']:>5.1f}%) | "
                  f"Avg: {summary['avg_time']:.2f}s")
        
        print("-" * 80)
        overall_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        overall_emoji = "✅" if overall_rate >= 70 else "⚠️" if overall_rate >= 50 else "❌"
        
        print(f"{overall_emoji} {Colors.BOLD}OVERALL: {total_passed}/{total_tests} tests passed ({overall_rate:.1f}%){Colors.END}")
        
        if overall_rate >= 70:
            print(f"{Colors.GREEN}🎉 Excellent! Character personalities and domain expertise are working well.{Colors.END}")
        elif overall_rate >= 50:
            print(f"{Colors.YELLOW}⚠️  Good progress, but some character traits may need attention.{Colors.END}")
        else:
            print(f"{Colors.RED}❌ Several character implementations need improvement.{Colors.END}")


async def main():
    """Main entry point for automated character testing."""
    parser = argparse.ArgumentParser(description="WhisperEngine Automated Character Testing")
    parser.add_argument('--bot', '-b', type=str, help="Test specific bot only")
    parser.add_argument('--verbose', '-v', action='store_true', help="Show detailed output")
    parser.add_argument('--list', '-l', action='store_true', help="List available bots and scenarios")
    
    args = parser.parse_args()
    
    runner = CharacterTestRunner()
    
    if args.list:
        print(f"{Colors.BOLD}Available Bots and Test Scenarios:{Colors.END}")
        print("=" * 50)
        for bot_name, scenarios in runner.test_scenarios.items():
            bot = runner.bot_configs[bot_name]
            print(f"{bot.emoji} {bot.name} ({bot.profession}) - {len(scenarios)} scenarios")
            for scenario in scenarios:
                print(f"    • {scenario.name} ({scenario.category})")
        return
    
    if args.bot:
        if args.bot not in runner.test_scenarios:
            print(f"{Colors.RED}❌ Unknown bot: {args.bot}{Colors.END}")
            print(f"Available bots: {', '.join(runner.test_scenarios.keys())}")
            return
            
        results = await runner.run_bot_tests(args.bot, args.verbose)
        
        # Single bot summary
        if results:
            passed = sum(1 for r in results if r.success)
            total = len(results)
            success_rate = (passed / total) * 100
            print(f"\n{Colors.BOLD}Final Result: {passed}/{total} tests passed ({success_rate:.1f}%){Colors.END}")
    else:
        all_results = await runner.run_all_tests(args.verbose)
        runner.print_final_summary(all_results)


if __name__ == "__main__":
    asyncio.run(main())