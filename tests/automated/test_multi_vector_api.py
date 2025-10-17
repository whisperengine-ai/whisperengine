#!/usr/bin/env python3
"""
Comprehensive Multi-Vector Testing via Elena's Chat API

Tests semantic vector routing, emotion hint detection, and system stability
with a wide variety of query types.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, List

# Elena's API endpoint
ELENA_API_URL = "http://localhost:9091"
TEST_USER_ID = "test_multi_vector_user_001"


class MultiVectorTester:
    """Comprehensive tester for multi-vector intelligence features."""
    
    def __init__(self):
        self.results = []
        self.session = None
    
    async def setup(self):
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession()
    
    async def cleanup(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
    
    async def send_message(self, message: str, test_name: str) -> Dict[str, Any]:
        """Send a message to Elena and return response with timing."""
        start_time = datetime.now()
        
        try:
            async with self.session.post(
                f"{ELENA_API_URL}/api/chat",
                json={
                    "user_id": TEST_USER_ID,
                    "message": message,
                    "context": {
                        "channel_type": "dm",
                        "platform": "api"
                    }
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "test_name": test_name,
                        "message": message,
                        "response": data.get("response", ""),
                        "elapsed_ms": elapsed,
                        "metadata": data.get("metadata", {})
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "test_name": test_name,
                        "message": message,
                        "error": f"HTTP {response.status}: {error_text}",
                        "elapsed_ms": elapsed
                    }
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "success": False,
                "test_name": test_name,
                "message": message,
                "error": str(e),
                "elapsed_ms": elapsed
            }
    
    def print_result(self, result: Dict[str, Any]):
        """Pretty print test result."""
        if result["success"]:
            print(f"   ✅ {result['test_name']}")
            print(f"      Query: '{result['message'][:60]}...'")
            print(f"      Response: '{result['response'][:80]}...'")
            print(f"      Time: {result['elapsed_ms']:.0f}ms")
        else:
            print(f"   ❌ {result['test_name']}")
            print(f"      Query: '{result['message'][:60]}...'")
            print(f"      Error: {result['error']}")
            print(f"      Time: {result['elapsed_ms']:.0f}ms")
        print()
    
    async def run_tests(self):
        """Run comprehensive test suite."""
        print("\n" + "="*80)
        print("🧪 COMPREHENSIVE MULTI-VECTOR INTELLIGENCE TESTING")
        print(f"   Target: Elena (localhost:9091)")
        print(f"   Test User: {TEST_USER_ID}")
        print("="*80 + "\n")
        
        await self.setup()
        
        # Test Category 1: Semantic Vector Routing (Pattern Queries)
        print("📊 TEST CATEGORY 1: Semantic Vector Routing (Pattern Queries)")
        print("-" * 80)
        
        semantic_tests = [
            ("Pattern Recognition 1", "relationship between marine life and climate"),
            ("Pattern Recognition 2", "connection between ocean temperature and species"),
            ("Pattern Recognition 3", "similar topics in biology"),
            ("Behavioral Pattern", "habit of dolphins in groups"),
            ("Recurring Theme", "tend to discuss coral reefs"),
            ("Conceptual Link", "relate plankton to larger ecosystems"),
        ]
        
        for test_name, message in semantic_tests:
            result = await self.send_message(message, test_name)
            self.results.append(result)
            self.print_result(result)
            await asyncio.sleep(0.5)  # Rate limiting
        
        # Test Category 2: Conversational Recall (Semantic Vector)
        print("\n📚 TEST CATEGORY 2: Conversational Recall Queries")
        print("-" * 80)
        
        recall_tests = [
            ("Recall 1", "topics we discussed about ocean ecosystems"),
            ("Recall 2", "what we talked about regarding marine biology"),
            ("Recall 3", "our conversation about coral reefs"),
            ("Recall 4", "between us, what did we explore?"),
            ("Recall 5", "connect what we learned about dolphins"),
        ]
        
        for test_name, message in recall_tests:
            result = await self.send_message(message, test_name)
            self.results.append(result)
            self.print_result(result)
            await asyncio.sleep(0.5)
        
        # Test Category 3: Emotion Detection (Keyword-Based)
        print("\n🎭 TEST CATEGORY 3: Emotional Queries (Keyword Detection)")
        print("-" * 80)
        
        emotion_tests = [
            ("Emotion 1: Joy", "I feel so happy about learning marine biology!"),
            ("Emotion 2: Sadness", "I'm feeling sad about ocean pollution"),
            ("Emotion 3: Worry", "I'm worried about coral reef destruction"),
            ("Emotion 4: Excitement", "I'm so excited to explore deep sea creatures!"),
            ("Emotion 5: Frustration", "I'm frustrated with plastic pollution"),
            ("Emotion 6: Contentment", "I feel content learning about ocean life"),
        ]
        
        for test_name, message in emotion_tests:
            result = await self.send_message(message, test_name)
            self.results.append(result)
            self.print_result(result)
            await asyncio.sleep(0.5)
        
        # Test Category 4: Mixed Intent Queries
        print("\n🔀 TEST CATEGORY 4: Mixed Intent Queries")
        print("-" * 80)
        
        mixed_tests = [
            ("Mixed 1", "I feel amazed by the pattern of whale migration"),
            ("Mixed 2", "relationship between my emotions and ocean conservation"),
            ("Mixed 3", "connect my excitement to learning about biodiversity"),
            ("Mixed 4", "usually I'm happy when we discuss marine life"),
        ]
        
        for test_name, message in mixed_tests:
            result = await self.send_message(message, test_name)
            self.results.append(result)
            self.print_result(result)
            await asyncio.sleep(0.5)
        
        # Test Category 5: Temporal Queries (Should bypass semantic)
        print("\n⏰ TEST CATEGORY 5: Temporal Queries (Verify Priority)")
        print("-" * 80)
        
        temporal_tests = [
            ("Temporal 1", "what did we discuss yesterday?"),
            ("Temporal 2", "recent conversation about dolphins"),
            ("Temporal 3", "last time we talked about coral"),
            ("Temporal 4", "first message today"),
        ]
        
        for test_name, message in temporal_tests:
            result = await self.send_message(message, test_name)
            self.results.append(result)
            self.print_result(result)
            await asyncio.sleep(0.5)
        
        # Test Category 6: Content Vector (Default Routing)
        print("\n🧠 TEST CATEGORY 6: Content Vector (Default Routing)")
        print("-" * 80)
        
        content_tests = [
            ("Content 1", "ocean ecosystems"),
            ("Content 2", "coral reef biodiversity"),
            ("Content 3", "marine biology research"),
            ("Content 4", "deep sea creatures"),
        ]
        
        for test_name, message in content_tests:
            result = await self.send_message(message, test_name)
            self.results.append(result)
            self.print_result(result)
            await asyncio.sleep(0.5)
        
        # Test Category 7: Stress Testing (No Recursion)
        print("\n💪 TEST CATEGORY 7: Stress Testing (Stability)")
        print("-" * 80)
        
        stress_tests = [
            ("Stress 1", "pattern relationship connection between similar topics we usually discuss"),
            ("Stress 2", "I feel worried about the pattern of climate change affecting ocean habitats"),
            ("Stress 3", "remember when we talked about the connection between emotions and conservation?"),
        ]
        
        for test_name, message in stress_tests:
            result = await self.send_message(message, test_name)
            self.results.append(result)
            self.print_result(result)
            await asyncio.sleep(0.5)
        
        await self.cleanup()
        
        # Generate Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary statistics."""
        print("\n" + "="*80)
        print("📈 TEST SUMMARY")
        print("="*80 + "\n")
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful
        
        avg_time = sum(r["elapsed_ms"] for r in self.results if r["success"]) / successful if successful > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"✅ Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"⚡ Average Response Time: {avg_time:.0f}ms")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for r in self.results:
                if not r["success"]:
                    print(f"   - {r['test_name']}: {r['error']}")
        
        print("\n" + "="*80)
        
        # Category breakdown
        categories = {}
        for r in self.results:
            category = r["test_name"].split(":")[0].split(" ")[0]
            if category not in categories:
                categories[category] = {"total": 0, "success": 0}
            categories[category]["total"] += 1
            if r["success"]:
                categories[category]["success"] += 1
        
        print("\n📊 CATEGORY BREAKDOWN:")
        for category, stats in categories.items():
            success_rate = stats["success"] / stats["total"] * 100
            print(f"   {category}: {stats['success']}/{stats['total']} ({success_rate:.0f}%)")
        
        print("\n" + "="*80)


async def main():
    """Run comprehensive multi-vector tests."""
    tester = MultiVectorTester()
    try:
        await tester.run_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
