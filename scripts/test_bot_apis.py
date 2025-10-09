#!/usr/bin/env python3
"""
WhisperEngine Bot API Test Script

Tests all individual bot HTTP API endpoints to verify they're working correctly.
This script tests health checks, bot info, and chat functionality for each bot.

Usage:
    # Normal Testing
    python scripts/test_bot_apis.py              # Test all bots in parallel
    python scripts/test_bot_apis.py elena        # Test only Elena bot
    python scripts/test_bot_apis.py sophia       # Test only Sophia bot
    
    # Load Testing
    python scripts/test_bot_apis.py load                           # Load test all bots (10 requests each, 1 concurrent)
    python scripts/test_bot_apis.py load --requests 50             # 50 requests per bot
    python scripts/test_bot_apis.py load --concurrent 5            # 5 concurrent requests per bot
    python scripts/test_bot_apis.py load --bot elena --requests 100 --concurrent 10  # Specific bot load test
    
Available bots: elena, marcus, ryan, dream, gabriel, sophia, jake, aethys

Features:
- Parallel testing of all bots for fast execution
- Individual bot testing with verbose output
- Health, info, and chat endpoint validation
- Load testing with randomized messages and detailed statistics
- Concurrent request support for performance testing
- Response time percentiles (P50, P95, P99)
- Requests per second measurements
- JSON report generation with timestamps
- Proper error handling and timeouts
"""

import asyncio
import aiohttp
import json
import time
import random
import statistics
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BotConfig:
    """Configuration for each bot"""
    name: str
    display_name: str
    profession: str
    port: int
    emoji: str

# Bot configurations based on current deployment
BOTS = [
    BotConfig("elena", "Elena Rodriguez", "Marine Biologist", 9091, "🌊"),
    BotConfig("marcus", "Dr. Marcus Thompson", "AI Researcher", 9092, "🤖"), 
    BotConfig("ryan", "Ryan Chen", "Indie Game Developer", 9093, "🎮"),
    BotConfig("dream", "Dream of the Endless", "Mythological Entity", 9094, "🌙"),
    BotConfig("gabriel", "Gabriel", "British Gentleman", 9095, "🎩"),
    BotConfig("sophia", "Sophia Blake", "Marketing Executive", 9096, "💼"),
    BotConfig("jake", "Jake Sterling", "Adventure Photographer", 9097, "📸"),
    BotConfig("aethys", "Aethys", "Omnipotent Entity", 3007, "✨"),
]

# Sample messages for load testing
LOAD_TEST_MESSAGES = [
    "Hello! How are you doing today?",
    "What's your favorite aspect of your work?",
    "Can you tell me something interesting?",
    "What advice would you give to someone starting out?",
    "How do you approach problem-solving?",
    "What motivates you in your profession?",
    "Tell me about a recent project you worked on.",
    "What are you passionate about?",
    "How has your field evolved over time?",
    "What challenges do you face in your work?",
    "What tools do you find most useful?",
    "Can you share a memorable experience?",
    "What's the most rewarding part of what you do?",
    "How do you stay current with developments?",
    "What would you change about your industry?",
    "What skills are most important in your field?",
    "Tell me about your background.",
    "What trends do you see emerging?",
    "How do you handle difficult situations?",
    "What inspires your creativity?",
    "What's your typical day like?",
    "How do you measure success?",
    "What misconceptions do people have about your work?",
    "What future developments excite you?",
    "How do you balance work and personal life?"
]

@dataclass
class LoadTestResult:
    """Result from a single load test request"""
    success: bool
    response_time: float
    response_length: int
    error: str = ""
    message_sent: str = ""
    bot_name: str = ""

@dataclass 
class LoadTestStats:
    """Statistics from load testing"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    success_rate: float
    total_response_length: int
    avg_response_length: float

class BotAPITester:
    """Test suite for WhisperEngine bot APIs"""
    
    def __init__(self):
        self.results = {}
        self.session: aiohttp.ClientSession | None = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_endpoint(self, bot: BotConfig) -> Dict:
        """Test bot health endpoint"""
        url = f"http://localhost:{bot.port}/health"
        try:
            if self.session is None:
                raise RuntimeError("Session not initialized")
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "✅ PASS",
                        "response_time": response.headers.get('X-Response-Time', 'N/A'),
                        "data": data
                    }
                else:
                    return {
                        "status": f"❌ FAIL - HTTP {response.status}",
                        "error": await response.text()
                    }
        except (aiohttp.ClientError, asyncio.TimeoutError, RuntimeError) as e:
            return {
                "status": f"❌ ERROR - {str(e)}",
                "error": str(e)
            }
    
    async def test_bot_info_endpoint(self, bot: BotConfig) -> Dict:
        """Test bot info endpoint"""
        url = f"http://localhost:{bot.port}/api/bot-info"
        try:
            if self.session is None:
                raise RuntimeError("Session not initialized")
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Validate expected fields
                    required_fields = ["bot_name", "bot_id", "status", "platform", "capabilities"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        return {
                            "status": f"⚠️  PARTIAL - Missing fields: {missing_fields}",
                            "data": data
                        }
                    else:
                        return {
                            "status": "✅ PASS",
                            "data": data
                        }
                else:
                    return {
                        "status": f"❌ FAIL - HTTP {response.status}",
                        "error": await response.text()
                    }
        except (aiohttp.ClientError, asyncio.TimeoutError, RuntimeError) as e:
            return {
                "status": f"❌ ERROR - {str(e)}",
                "error": str(e)
            }
    
    async def test_chat_endpoint(self, bot: BotConfig) -> Dict:
        """Test bot chat endpoint"""
        url = f"http://localhost:{bot.port}/api/chat"
        test_message = f"Hello {bot.display_name}! Can you tell me about your work as a {bot.profession.lower()}?"
        payload = {
            "message": test_message,
            "user_id": f"test_user_{int(time.time())}",
            "metadata_level": "extended"  # Request extended metadata for comprehensive testing
        }
        
        try:
            if self.session is None:
                raise RuntimeError("Session not initialized")
            async with self.session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Validate response structure
                    required_fields = ["response", "timestamp", "message_id", "bot_name", "success"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        return {
                            "status": f"⚠️  PARTIAL - Missing fields: {missing_fields}",
                            "data": data,
                            "request": payload
                        }
                    elif data.get("success") != True:
                        return {
                            "status": "⚠️  PARTIAL - Success=False",
                            "data": data,
                            "request": payload
                        }
                    else:
                        return {
                            "status": "✅ PASS",
                            "data": data,
                            "request": payload,
                            "response_length": len(data.get("response", ""))
                        }
                else:
                    return {
                        "status": f"❌ FAIL - HTTP {response.status}",
                        "error": await response.text(),
                        "request": payload
                    }
        except (aiohttp.ClientError, asyncio.TimeoutError, RuntimeError) as e:
            return {
                "status": f"❌ ERROR - {str(e)}",
                "error": str(e),
                "request": payload
            }
    
    async def test_bot_comprehensive(self, bot: BotConfig, verbose: bool = True) -> Dict:
        """Run comprehensive test suite for a single bot"""
        if verbose:
            print(f"\n{bot.emoji} Testing {bot.display_name} ({bot.profession}) on port {bot.port}...")
        
        # Run all tests
        health_result = await self.test_health_endpoint(bot)
        info_result = await self.test_bot_info_endpoint(bot)
        chat_result = await self.test_chat_endpoint(bot)
        
        # Determine overall status
        statuses = [health_result["status"], info_result["status"], chat_result["status"]]
        if all("✅" in status for status in statuses):
            overall_status = "✅ ALL PASS"
        elif any("❌" in status for status in statuses):
            overall_status = "❌ SOME FAILED"
        else:
            overall_status = "⚠️  PARTIAL"
        
        result = {
            "bot": bot,
            "overall_status": overall_status,
            "health": health_result,
            "info": info_result,
            "chat": chat_result,
            "timestamp": datetime.now().isoformat()
        }
        
        # Print summary only if verbose
        if verbose:
            print(f"  Health:   {health_result['status']}")
            print(f"  Info:     {info_result['status']}")
            print(f"  Chat:     {chat_result['status']}")
            print(f"  Overall:  {overall_status}")
        
        return result
    
    async def test_bot_parallel(self, bot: BotConfig) -> Dict:
        """Run comprehensive test suite for a single bot (parallel version - no verbose output)"""
        return await self.test_bot_comprehensive(bot, verbose=False)
    
    async def test_all_bots(self) -> Dict:
        """Test all configured bots in parallel"""
        print("🤖 WhisperEngine Bot API Test Suite")
        print("=" * 50)
        print(f"Testing {len(BOTS)} bots in parallel...")
        
        # Create tasks for testing all bots simultaneously
        tasks = []
        for bot in BOTS:
            task = asyncio.create_task(self.test_bot_parallel(bot))
            tasks.append((bot.name, task))
        
        # Wait for all tests to complete
        print("⏳ Running parallel tests...")
        test_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        # Store results
        for i, (bot_name, _) in enumerate(tasks):
            result = test_results[i]
            if isinstance(result, Exception):
                # Handle any exceptions that occurred during testing
                self.results[bot_name] = {
                    "bot": next(bot for bot in BOTS if bot.name == bot_name),
                    "overall_status": f"❌ EXCEPTION - {str(result)}",
                    "health": {"status": f"❌ ERROR - {str(result)}"},
                    "info": {"status": f"❌ ERROR - {str(result)}"},
                    "chat": {"status": f"❌ ERROR - {str(result)}"},
                    "timestamp": datetime.now().isoformat()
                }
            else:
                self.results[bot_name] = result
        
        # Print results summary after all tests complete
        print("\n✅ Parallel testing completed! Results:")
        print("-" * 40)
        for bot_name in [bot.name for bot in BOTS]:  # Maintain original order
            if bot_name in self.results:
                result = self.results[bot_name]
                bot = result["bot"]
                print(f"{bot.emoji} {bot.display_name}: {result['overall_status']}")
        
        return self.results
    
    async def test_single_bot(self, bot_name: str) -> Dict:
        """Test a single bot by name"""
        bot = next((b for b in BOTS if b.name == bot_name), None)
        if not bot:
            available_bots = [b.name for b in BOTS]
            raise ValueError(f"Unknown bot '{bot_name}'. Available bots: {available_bots}")
        
        self.results[bot.name] = await self.test_bot_comprehensive(bot, verbose=True)
        return self.results
    
    async def load_test_single_request(self, bot: BotConfig, message: str, user_id: str) -> LoadTestResult:
        """Execute a single load test request"""
        url = f"http://localhost:{bot.port}/api/chat"
        payload = {
            "message": message,
            "user_id": user_id,
            "metadata_level": "extended"  # Request extended metadata for comprehensive testing
        }
        
        start_time = time.time()
        try:
            if self.session is None:
                raise RuntimeError("Session not initialized")
            async with self.session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        return LoadTestResult(
                            success=True,
                            response_time=response_time,
                            response_length=len(data.get("response", "")),
                            message_sent=message,
                            bot_name=bot.name
                        )
                    else:
                        return LoadTestResult(
                            success=False,
                            response_time=response_time,
                            response_length=0,
                            error="Bot returned success=False",
                            message_sent=message,
                            bot_name=bot.name
                        )
                else:
                    error_text = await response.text()
                    return LoadTestResult(
                        success=False,
                        response_time=response_time,
                        response_length=0,
                        error=f"HTTP {response.status}: {error_text}",
                        message_sent=message,
                        bot_name=bot.name
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError, RuntimeError) as e:
            response_time = time.time() - start_time
            return LoadTestResult(
                success=False,
                response_time=response_time,
                response_length=0,
                error=str(e),
                message_sent=message,
                bot_name=bot.name
            )
    
    async def load_test_bot(self, bot: BotConfig, num_requests: int = 10, 
                           concurrent_requests: int = 1) -> Tuple[List[LoadTestResult], LoadTestStats]:
        """Load test a single bot with specified parameters"""
        print(f"\n🔄 Load testing {bot.emoji} {bot.display_name}")
        print(f"   Requests: {num_requests}, Concurrent: {concurrent_requests}")
        
        load_results = []
        start_time = time.time()
        
        # Create batches of concurrent requests
        for batch_start in range(0, num_requests, concurrent_requests):
            batch_size = min(concurrent_requests, num_requests - batch_start)
            batch_tasks = []
            
            for i in range(batch_size):
                message = random.choice(LOAD_TEST_MESSAGES)
                user_id = f"load_test_user_{batch_start + i}_{int(time.time())}"
                task = self.load_test_single_request(bot, message, user_id)
                batch_tasks.append(task)
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*batch_tasks)
            load_results.extend(batch_results)
            
            # Brief pause between batches to avoid overwhelming the bot
            if batch_start + concurrent_requests < num_requests:
                await asyncio.sleep(0.1)
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        stats = self._calculate_load_test_stats(load_results, total_time)
        
        return load_results, stats
    
    def _calculate_load_test_stats(self, load_results: List[LoadTestResult], total_time: float) -> LoadTestStats:
        """Calculate statistics from load test results"""
        successful_results = [r for r in load_results if r.success]
        failed_results = [r for r in load_results if not r.success]
        
        if not load_results:
            return LoadTestStats(
                total_requests=0, successful_requests=0, failed_requests=0,
                total_time=total_time, avg_response_time=0, min_response_time=0,
                max_response_time=0, p50_response_time=0, p95_response_time=0,
                p99_response_time=0, requests_per_second=0, success_rate=0,
                total_response_length=0, avg_response_length=0
            )
        
        response_times = [r.response_time for r in load_results]
        response_lengths = [r.response_length for r in successful_results]
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = statistics.median(sorted_times) if sorted_times else 0
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
        
        return LoadTestStats(
            total_requests=len(load_results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            total_time=total_time,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p50_response_time=p50,
            p95_response_time=p95,
            p99_response_time=p99,
            requests_per_second=len(load_results) / total_time if total_time > 0 else 0,
            success_rate=(len(successful_results) / len(load_results)) * 100 if load_results else 0,
            total_response_length=sum(response_lengths),
            avg_response_length=statistics.mean(response_lengths) if response_lengths else 0
        )
    
    async def load_test_all_bots(self, num_requests: int = 10, concurrent_requests: int = 1) -> Dict:
        """Load test all bots in parallel"""
        print("\n🚀 Load Testing All Bots")
        print(f"   Requests per bot: {num_requests}")
        print(f"   Concurrent requests per bot: {concurrent_requests}")
        print("=" * 60)
        
        # Create tasks for load testing all bots simultaneously
        tasks = []
        for bot in BOTS:
            task = asyncio.create_task(self.load_test_bot(bot, num_requests, concurrent_requests))
            tasks.append((bot.name, task))
        
        # Wait for all load tests to complete
        overall_start_time = time.time()
        test_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        overall_time = time.time() - overall_start_time
        
        # Store results
        load_test_results = {}
        for i, (bot_name, _) in enumerate(tasks):
            result = test_results[i]
            if isinstance(result, Exception):
                print(f"❌ {bot_name}: Exception - {str(result)}")
                load_test_results[bot_name] = {
                    "error": str(result),
                    "results": [],
                    "stats": None
                }
            else:
                # result is a tuple of (bot_results, stats)
                try:
                    bot_results, stats = result
                    load_test_results[bot_name] = {
                        "results": bot_results,
                        "stats": stats
                    }
                except (ValueError, TypeError) as e:
                    print(f"❌ {bot_name}: Result unpacking error - {str(e)}")
                    load_test_results[bot_name] = {
                        "error": f"Result unpacking error: {str(e)}",
                        "results": [],
                        "stats": None
                    }
        
        print(f"\n⚡ All bots load testing completed in {overall_time:.2f} seconds")
        
        # Print summary for all bots
        self._print_load_test_summary(load_test_results)
        
        return load_test_results
    
    def _print_load_test_summary(self, load_test_results: Dict) -> None:
        """Print summary of load test results"""
        print("\n📊 LOAD TEST SUMMARY")
        print("=" * 80)
        
        for bot_name in [bot.name for bot in BOTS]:  # Maintain order
            if bot_name not in load_test_results:
                continue
                
            result = load_test_results[bot_name]
            bot = next(b for b in BOTS if b.name == bot_name)
            
            if "error" in result:
                print(f"{bot.emoji} {bot.display_name}: ❌ ERROR - {result['error']}")
                continue
            
            stats = result["stats"]
            if not stats:
                continue
                
            print(f"\n{bot.emoji} {bot.display_name} ({bot.profession})")
            print(f"   Total Requests: {stats.total_requests}")
            print(f"   Success Rate: {stats.success_rate:.1f}% ({stats.successful_requests}/{stats.total_requests})")
            print(f"   Requests/sec: {stats.requests_per_second:.2f}")
            print(f"   Response Times: avg={stats.avg_response_time:.3f}s, "
                  f"p50={stats.p50_response_time:.3f}s, p95={stats.p95_response_time:.3f}s")
            print(f"   Response Length: avg={stats.avg_response_length:.0f} chars")
            
            if stats.failed_requests > 0:
                print(f"   ⚠️ Failed: {stats.failed_requests} requests")
        
        # Overall statistics
        all_stats = [result["stats"] for result in load_test_results.values() 
                    if result.get("stats") is not None]
        
        if all_stats:
            total_requests = sum(s.total_requests for s in all_stats)
            total_successful = sum(s.successful_requests for s in all_stats)
            overall_success_rate = (total_successful / total_requests) * 100 if total_requests > 0 else 0
            avg_rps = statistics.mean([s.requests_per_second for s in all_stats])
            avg_response_time = statistics.mean([s.avg_response_time for s in all_stats])
            
            print("\n🎯 OVERALL PERFORMANCE")
            print(f"   Total Requests: {total_requests}")
            print(f"   Overall Success Rate: {overall_success_rate:.1f}%")
            print(f"   Average RPS per bot: {avg_rps:.2f}")
            print(f"   Average Response Time: {avg_response_time:.3f}s")
    
    def generate_summary_report(self) -> str:
        """Generate a summary report of all test results"""
        if not self.results:
            return "No test results available."
        
        total_bots = len(self.results)
        passed_bots = sum(1 for result in self.results.values() 
                         if "✅ ALL PASS" in result["overall_status"])
        failed_bots = sum(1 for result in self.results.values() 
                         if "❌" in result["overall_status"])
        partial_bots = total_bots - passed_bots - failed_bots
        
        report = []
        report.append("\n" + "=" * 60)
        report.append("🤖 WHISPERENGINE BOT API TEST SUMMARY")
        report.append("=" * 60)
        report.append(f"Total Bots Tested: {total_bots}")
        report.append(f"✅ All Tests Passed: {passed_bots}")
        report.append(f"⚠️  Partial Success: {partial_bots}")
        report.append(f"❌ Failed: {failed_bots}")
        report.append("")
        
        # Detailed results
        report.append("DETAILED RESULTS:")
        report.append("-" * 40)
        
        for result in self.results.values():
            bot = result["bot"]
            report.append(f"{bot.emoji} {bot.display_name} ({bot.profession})")
            report.append(f"   Port: {bot.port}")
            report.append(f"   Status: {result['overall_status']}")
            
            # Show any errors
            for test_name, test_result in [("Health", result["health"]), 
                                         ("Info", result["info"]), 
                                         ("Chat", result["chat"])]:
                if "❌" in test_result["status"] or "ERROR" in test_result["status"]:
                    report.append(f"   {test_name} Error: {test_result.get('error', 'Unknown')}")
            
            report.append("")
        
        # Working endpoints summary
        working_endpoints = []
        for result in self.results.values():
            if "✅" in result["overall_status"]:
                bot = result["bot"]
                working_endpoints.append(f"  curl http://localhost:{bot.port}/api/chat  # {bot.display_name}")
        
        if working_endpoints:
            report.append("WORKING CHAT ENDPOINTS:")
            report.append("-" * 30)
            report.extend(working_endpoints)
        
        report.append("")
        report.append(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_detailed_report(self, filename: str | None = None) -> str | None:
        """Save detailed JSON report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bot_api_test_results_{timestamp}.json"
        
        filepath = f"/Users/markcastillo/git/whisperengine/logs/{filename}"
        
        # Prepare data for JSON serialization
        json_results = {}
        for result in self.results.values():
            bot_name = result["bot"].name
            json_result = {
                "bot_name": result["bot"].name,
                "display_name": result["bot"].display_name,
                "profession": result["bot"].profession,
                "port": result["bot"].port,
                "emoji": result["bot"].emoji,
                "overall_status": result["overall_status"],
                "timestamp": result["timestamp"],
                "tests": {
                    "health": result["health"],
                    "info": result["info"],
                    "chat": result["chat"]
                }
            }
            json_results[bot_name] = json_result
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_results, f, indent=2, default=str)
            return filepath
        except (OSError, IOError) as e:
            print(f"Failed to save detailed report: {e}")
            return None

async def main():
    """Main test runner"""
    import sys
    
    # Handle help request
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print(__doc__)
        return None
    
    async with BotAPITester() as tester:
        # Check for load test command
        if len(sys.argv) > 1 and sys.argv[1] == 'load':
            # Parse load test parameters
            num_requests = 10
            concurrent_requests = 1
            bot_name = None
            
            # Parse additional arguments
            i = 2
            while i < len(sys.argv):
                arg = sys.argv[i]
                if arg == '--requests' and i + 1 < len(sys.argv):
                    num_requests = int(sys.argv[i + 1])
                    i += 2
                elif arg == '--concurrent' and i + 1 < len(sys.argv):
                    concurrent_requests = int(sys.argv[i + 1])
                    i += 2
                elif arg == '--bot' and i + 1 < len(sys.argv):
                    bot_name = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            # Run load test
            if bot_name:
                # Load test specific bot
                bot = next((b for b in BOTS if b.name == bot_name), None)
                if not bot:
                    available_bots = [b.name for b in BOTS]
                    print(f"❌ Error: Unknown bot '{bot_name}'. Available bots: {available_bots}")
                    return None
                
                start_time = time.time()
                bot_results, stats = await tester.load_test_bot(bot, num_requests, concurrent_requests)
                end_time = time.time()
                
                print(f"\n📊 Load Test Results for {bot.emoji} {bot.display_name}")
                print("=" * 60)
                print(f"Total Requests: {stats.total_requests}")
                print(f"Success Rate: {stats.success_rate:.1f}% ({stats.successful_requests}/{stats.total_requests})")
                print(f"Total Time: {stats.total_time:.2f}s")
                print(f"Requests/sec: {stats.requests_per_second:.2f}")
                print("Response Times (seconds):")
                print(f"  Average: {stats.avg_response_time:.3f}")
                print(f"  Min: {stats.min_response_time:.3f}")
                print(f"  Max: {stats.max_response_time:.3f}")
                print(f"  P50: {stats.p50_response_time:.3f}")
                print(f"  P95: {stats.p95_response_time:.3f}")
                print(f"  P99: {stats.p99_response_time:.3f}")
                print(f"Response Length: {stats.avg_response_length:.0f} chars average")
                
                if stats.failed_requests > 0:
                    print(f"\n⚠️ Failed Requests: {stats.failed_requests}")
                    failed_results = [r for r in bot_results if not r.success]
                    for failed in failed_results[:5]:  # Show first 5 failures
                        print(f"   Error: {failed.error}")
            else:
                # Load test all bots
                start_time = time.time()
                await tester.load_test_all_bots(num_requests, concurrent_requests)
                end_time = time.time()
                print(f"\n⚡ All bots load testing completed in {end_time - start_time:.2f} seconds")
            
            return None
        
        # Check if specific bot was requested (normal testing)
        elif len(sys.argv) > 1:
            bot_name = sys.argv[1]
            try:
                await tester.test_single_bot(bot_name)
                print(f"\n🎯 Single bot test completed for {bot_name}")
            except ValueError as e:
                print(f"❌ Error: {e}")
                return None
        else:
            # Run all tests in parallel (normal testing)
            start_time = time.time()
            await tester.test_all_bots()
            end_time = time.time()
            print(f"\n⚡ Parallel testing completed in {end_time - start_time:.2f} seconds")
        
        # Generate and display summary (only for normal testing)
        summary = tester.generate_summary_report()
        print(summary)
        
        # Save detailed report
        report_file = tester.save_detailed_report()
        if report_file:
            print(f"\n📄 Detailed JSON report saved to: {report_file}")
        
        return tester.results

if __name__ == "__main__":
    # Run the test suite
    results = asyncio.run(main())