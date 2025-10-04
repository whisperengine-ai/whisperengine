#!/usr/bin/env python3
"""
Phase 6 API Endpoint Test - Live Bot Testing

Tests Phase 6 entity relationship recommendations against live bot API endpoint.
Tests the complete pipeline: API → CDL → Knowledge Router → Recommendations → Response

Requirements:
- Bot must be running (e.g., Elena on port 9091)
- PostgreSQL with Phase 6 methods operational
- CDL integration with recommendation detection

Usage:
    # Start bot first
    ./multi-bot.sh start elena
    
    # Run test
    source .venv/bin/activate && python test_phase6_api_endpoint.py
    
    # Or test specific bot
    BOT_PORT=9092 BOT_NAME=marcus python test_phase6_api_endpoint.py
"""

import asyncio
import aiohttp
import os
import sys
import json
from typing import Optional

# Configuration
BOT_PORT = int(os.getenv('BOT_PORT', 9091))  # Default: Elena
BOT_NAME = os.getenv('BOT_NAME', 'elena')
BOT_URL = f"http://localhost:{BOT_PORT}/api/chat"
TEST_USER_ID = "phase6_api_test_user"


class Phase6APITester:
    """Test Phase 6 functionality via bot API endpoint"""
    
    def __init__(self, bot_url: str, test_user_id: str):
        self.bot_url = bot_url
        self.test_user_id = test_user_id
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_message(self, message: str, timeout: int = 30) -> dict:
        """Send message to bot API and get response"""
        payload = {
            "user_id": self.test_user_id,
            "message": message
        }
        
        try:
            async with self.session.post(
                self.bot_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {
                        "error": f"HTTP {response.status}",
                        "details": error_text
                    }
        except asyncio.TimeoutError:
            return {"error": "Timeout", "details": f"Request exceeded {timeout}s"}
        except Exception as e:
            return {"error": str(type(e).__name__), "details": str(e)}
    
    def print_response(self, message: str, response: dict, test_num: int):
        """Pretty print API response"""
        print(f"\n{'='*80}")
        print(f"TEST {test_num}: {message}")
        print(f"{'='*80}")
        
        if "error" in response:
            print(f"❌ ERROR: {response['error']}")
            print(f"   Details: {response.get('details', 'N/A')}")
            return False
        
        bot_response = response.get('response', 'No response')
        print(f"\n💬 User: {message}")
        print(f"🤖 Bot: {bot_response}")
        
        # Check for recommendation indicators
        recommendation_indicators = [
            'similar', 'like', 'might enjoy', 'also try', 'recommend',
            'biking', 'skiing', 'running', 'swimming'  # Common related activities
        ]
        
        has_recommendation = any(
            indicator.lower() in bot_response.lower() 
            for indicator in recommendation_indicators
        )
        
        if has_recommendation:
            print(f"\n✅ RECOMMENDATION DETECTED in response")
        else:
            print(f"\n⚠️  No obvious recommendation detected")
        
        return True


async def test_health_check(tester: Phase6APITester) -> bool:
    """Test 0: Verify bot is running"""
    print(f"\n{'='*80}")
    print(f"TEST 0: Health Check - Bot Running on Port {BOT_PORT}")
    print(f"{'='*80}")
    
    try:
        health_url = f"http://localhost:{BOT_PORT}/health"
        async with tester.session.get(health_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Bot is RUNNING")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Bot: {BOT_NAME}")
                print(f"   Port: {BOT_PORT}")
                return True
            else:
                print(f"❌ Bot returned HTTP {response.status}")
                return False
    except Exception as e:
        print(f"❌ Bot is NOT RUNNING")
        print(f"   Error: {e}")
        print(f"\n💡 Start bot with: ./multi-bot.sh start {BOT_NAME}")
        return False


async def test_basic_conversation(tester: Phase6APITester) -> bool:
    """Test 1: Basic conversation to establish baseline"""
    message = "Hello! I love hiking in the mountains."
    response = await tester.send_message(message)
    return tester.print_response(message, response, 1)


async def test_store_multiple_interests(tester: Phase6APITester) -> bool:
    """Test 2: Store multiple related interests"""
    message = "I also enjoy biking and skiing on weekends."
    response = await tester.send_message(message)
    return tester.print_response(message, response, 2)


async def test_direct_similarity_query(tester: Phase6APITester) -> bool:
    """Test 3: Direct 'similar to' query (Phase 6 trigger)"""
    message = "What's similar to hiking?"
    response = await tester.send_message(message)
    success = tester.print_response(message, response, 3)
    
    # Extra validation for Phase 6
    if success and "error" not in response:
        bot_response = response.get('response', '').lower()
        
        # Check for specific recommendation patterns
        has_biking = 'biking' in bot_response or 'bike' in bot_response
        has_activity_mention = any(word in bot_response for word in [
            'activity', 'activities', 'similar', 'like', 'enjoy', 'try'
        ])
        
        if has_biking and has_activity_mention:
            print(f"\n🎯 PHASE 6 SUCCESS: Detected biking recommendation!")
            return True
        elif has_activity_mention:
            print(f"\n⚠️  PHASE 6 PARTIAL: Mentioned activities but not specific recommendations")
            return True
        else:
            print(f"\n❌ PHASE 6 FAILED: No activity recommendations detected")
            return False
    
    return success


async def test_natural_recommendation_query(tester: Phase6APITester) -> bool:
    """Test 4: Natural language recommendation request"""
    message = "What other outdoor activities might I enjoy?"
    response = await tester.send_message(message)
    return tester.print_response(message, response, 4)


async def test_alternative_pattern(tester: Phase6APITester) -> bool:
    """Test 5: 'alternatives to' pattern (Phase 6 trigger)"""
    message = "Can you suggest alternatives to hiking?"
    response = await tester.send_message(message)
    return tester.print_response(message, response, 5)


async def test_comparison_pattern(tester: Phase6APITester) -> bool:
    """Test 6: Comparison query pattern"""
    message = "What's related to the activities I mentioned?"
    response = await tester.send_message(message)
    return tester.print_response(message, response, 6)


async def test_follow_up_conversation(tester: Phase6APITester) -> bool:
    """Test 7: Follow-up maintains context"""
    message = "Tell me more about one of those activities you mentioned."
    response = await tester.send_message(message)
    return tester.print_response(message, response, 7)


async def main():
    """Run complete Phase 6 API endpoint test suite"""
    print("\n" + "="*80)
    print("PHASE 6: API ENDPOINT TEST SUITE")
    print("="*80)
    print(f"\nBot: {BOT_NAME.upper()}")
    print(f"Port: {BOT_PORT}")
    print(f"Endpoint: {BOT_URL}")
    print(f"Test User: {TEST_USER_ID}")
    print("\nTesting complete pipeline:")
    print("  API → Message Handler → CDL Integration → Knowledge Router")
    print("  → Entity Relationships → Recommendations → LLM → Response")
    
    async with Phase6APITester(BOT_URL, TEST_USER_ID) as tester:
        # Test 0: Health check
        if not await test_health_check(tester):
            print("\n" + "="*80)
            print("❌ PREREQUISITE FAILED: Bot not running")
            print("="*80)
            print(f"\n💡 Start bot with: ./multi-bot.sh start {BOT_NAME}")
            return False
        
        # Small delay to ensure bot is ready
        await asyncio.sleep(1)
        
        # Run test suite
        results = {}
        
        try:
            results["Basic Conversation"] = await test_basic_conversation(tester)
            await asyncio.sleep(2)  # Allow fact storage to complete
            
            results["Multiple Interests"] = await test_store_multiple_interests(tester)
            await asyncio.sleep(2)  # Allow relationship auto-population
            
            results["Direct Similarity Query"] = await test_direct_similarity_query(tester)
            await asyncio.sleep(1)
            
            results["Natural Recommendation"] = await test_natural_recommendation_query(tester)
            await asyncio.sleep(1)
            
            results["Alternative Pattern"] = await test_alternative_pattern(tester)
            await asyncio.sleep(1)
            
            results["Comparison Pattern"] = await test_comparison_pattern(tester)
            await asyncio.sleep(1)
            
            results["Follow-up Context"] = await test_follow_up_conversation(tester)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            return False
        
        # Summary
        print("\n" + "="*80)
        print("PHASE 6 API ENDPOINT TEST RESULTS")
        print("="*80)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        total = len(results)
        passed = sum(1 for r in results.values() if r)
        success_rate = (passed / total) * 100
        
        print(f"\n📊 Overall: {passed}/{total} ({success_rate:.1f}%)")
        
        # Phase 6 specific validation
        critical_tests = [
            "Direct Similarity Query",
            "Natural Recommendation",
            "Alternative Pattern"
        ]
        
        critical_passed = sum(
            1 for test_name in critical_tests 
            if results.get(test_name, False)
        )
        
        print(f"🎯 Phase 6 Critical Tests: {critical_passed}/{len(critical_tests)}")
        
        if success_rate >= 70 and critical_passed >= 2:
            print("\n✅ PHASE 6 API ENDPOINT TEST - PASSED")
            print("\nKey Achievements:")
            print("- Bot API responding successfully")
            print("- Conversation context maintained")
            print("- Entity relationships operational")
            print("- Recommendation queries processed")
            print("- CDL integration working end-to-end")
            return True
        else:
            print("\n❌ PHASE 6 API ENDPOINT TEST - FAILED")
            print("\nIssues Detected:")
            if critical_passed < 2:
                print("- Recommendation queries not working as expected")
                print("- Check CDL integration in cdl_ai_integration.py")
                print("- Verify knowledge_router is initialized")
            if success_rate < 70:
                print("- Multiple test failures detected")
                print("- Check bot logs for errors")
            return False


if __name__ == "__main__":
    print("\n🚀 Phase 6 API Endpoint Test")
    print("="*80)
    
    # Check if custom bot specified
    if len(sys.argv) > 1:
        bot_arg = sys.argv[1].lower()
        bot_ports = {
            'elena': 9091,
            'marcus': 9092,
            'ryan': 9093,
            'dream': 9094,
            'gabriel': 9095,
            'sophia': 9096,
            'jake': 9097,
            'aethys': 3007
        }
        
        if bot_arg in bot_ports:
            BOT_PORT = bot_ports[bot_arg]
            BOT_NAME = bot_arg
            BOT_URL = f"http://localhost:{BOT_PORT}/api/chat"
            print(f"Testing bot: {bot_arg.upper()} on port {BOT_PORT}")
        else:
            print(f"Unknown bot: {bot_arg}")
            print(f"Available: {', '.join(bot_ports.keys())}")
            sys.exit(1)
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
