#!/usr/bin/env python3
"""
Manual test script for Phase 2 Hybrid Vector Routing with Elena.

Tests all query categories via HTTP chat endpoint:
- FACTUAL queries (content vector only)
- EMOTIONAL queries (content + emotion fusion)
- CONVERSATIONAL queries (content + semantic fusion)
- TEMPORAL queries (chronological scroll)
- GENERAL queries (content default)
"""

import asyncio
import json
import sys
from typing import Dict, Any, List
import httpx
from datetime import datetime

# Elena's HTTP endpoint
ELENA_URL = "http://localhost:9091"
CHAT_ENDPOINT = f"{ELENA_URL}/api/chat"

# Test user ID
TEST_USER_ID = "phase2_test_user"


class Phase2RoutingTester:
    """Test Phase 2 query classification and routing."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.total_tests = 0
        self.passed_tests = 0
        
    async def send_message(
        self, 
        message: str, 
        expected_category: str,
        metadata_level: str = "extended"
    ) -> Dict[str, Any]:
        """
        Send a message to Elena and check routing.
        
        Args:
            message: Message to send
            expected_category: Expected query category
            metadata_level: Metadata detail level
            
        Returns:
            Test result dictionary
        """
        self.total_tests += 1
        
        payload = {
            "user_id": TEST_USER_ID,
            "message": message,
            "metadata_level": metadata_level,
            "context": {
                "channel_type": "dm",
                "platform": "api"
            }
        }
        
        print(f"\n{'='*80}")
        print(f"TEST {self.total_tests}: {expected_category.upper()} Query")
        print(f"{'='*80}")
        print(f"📝 Message: {message}")
        print(f"🎯 Expected Category: {expected_category}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(CHAT_ENDPOINT, json=payload)
                
                if response.status_code != 200:
                    print(f"❌ HTTP Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    return {
                        "test": self.total_tests,
                        "message": message,
                        "expected_category": expected_category,
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "timestamp": datetime.now().isoformat()
                    }
                
                data = response.json()
                
                # Extract routing information from metadata
                metadata = data.get('metadata', {})
                ai_components = metadata.get('ai_components', {})
                memory_metadata = ai_components.get('memory', {})
                
                # Check for Phase 2 routing metadata
                search_type = None
                vectors_used = None
                query_category = None
                
                # Look for routing info in memory metadata
                if memory_metadata:
                    if 'memories' in memory_metadata:
                        memories = memory_metadata['memories']
                        if memories and len(memories) > 0:
                            first_memory = memories[0]
                            search_type = first_memory.get('search_type', 'unknown')
                            vectors_used = first_memory.get('vectors_used', [])
                            query_category = first_memory.get('query_category', 'unknown')
                
                # Determine if routing matches expectation
                routing_correct = self._validate_routing(
                    expected_category, 
                    search_type, 
                    vectors_used
                )
                
                if routing_correct:
                    self.passed_tests += 1
                    print(f"✅ PASS - Routing correct!")
                else:
                    print(f"❌ FAIL - Routing mismatch!")
                
                print(f"\n📊 Response Details:")
                print(f"  • Bot Response: {data.get('response', 'N/A')[:100]}...")
                print(f"  • Search Type: {search_type}")
                print(f"  • Vectors Used: {vectors_used}")
                print(f"  • Query Category: {query_category}")
                print(f"  • Memory Count: {memory_metadata.get('memory_count', 0)}")
                
                result = {
                    "test": self.total_tests,
                    "message": message,
                    "expected_category": expected_category,
                    "actual_search_type": search_type,
                    "vectors_used": vectors_used,
                    "query_category": query_category,
                    "routing_correct": routing_correct,
                    "response_preview": data.get('response', '')[:200],
                    "success": data.get('success', False),
                    "timestamp": datetime.now().isoformat()
                }
                
                self.results.append(result)
                return result
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            result = {
                "test": self.total_tests,
                "message": message,
                "expected_category": expected_category,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            return result
    
    def _validate_routing(
        self, 
        expected_category: str, 
        search_type: str, 
        vectors_used: List[str]
    ) -> bool:
        """
        Validate that routing matches expected category.
        
        Args:
            expected_category: Expected query category
            search_type: Actual search type from response
            vectors_used: Vectors used in search
            
        Returns:
            True if routing is correct
        """
        if not search_type:
            print(f"  ⚠️  No search_type in response (may be using legacy method)")
            return False
        
        # FACTUAL → content_vector
        if expected_category == "factual":
            return search_type == "content_vector" or "content" in str(vectors_used)
        
        # EMOTIONAL → multi_vector_fusion with emotion
        elif expected_category == "emotional":
            return (search_type == "multi_vector_fusion" and 
                    vectors_used and "emotion" in vectors_used)
        
        # CONVERSATIONAL → multi_vector_fusion with semantic
        elif expected_category == "conversational":
            return (search_type == "multi_vector_fusion" and 
                    vectors_used and "semantic" in vectors_used)
        
        # TEMPORAL → temporal_scroll
        elif expected_category == "temporal":
            return "temporal" in search_type or "scroll" in search_type
        
        # GENERAL → content_vector (default)
        elif expected_category == "general":
            return search_type == "content_vector"
        
        return False
    
    async def run_comprehensive_tests(self):
        """Run all query category tests."""
        
        print(f"\n{'#'*80}")
        print(f"# PHASE 2 HYBRID VECTOR ROUTING TEST SUITE")
        print(f"# Testing with Elena on {ELENA_URL}")
        print(f"# User ID: {TEST_USER_ID}")
        print(f"{'#'*80}\n")
        
        # Wait for bot to be ready
        print("⏳ Checking if Elena is ready...")
        await asyncio.sleep(2)
        
        # Test 1: FACTUAL queries (content vector only)
        await self.send_message(
            "What is 2+2?",
            expected_category="factual"
        )
        
        await asyncio.sleep(1)
        
        await self.send_message(
            "Define photosynthesis",
            expected_category="factual"
        )
        
        await asyncio.sleep(1)
        
        # Test 2: EMOTIONAL queries (content + emotion fusion)
        await self.send_message(
            "How are you feeling today?",
            expected_category="emotional"
        )
        
        await asyncio.sleep(1)
        
        await self.send_message(
            "I'm so excited about this project!",
            expected_category="emotional"
        )
        
        await asyncio.sleep(1)
        
        # Test 3: CONVERSATIONAL queries (content + semantic fusion)
        await self.send_message(
            "What did we discuss earlier?",
            expected_category="conversational"
        )
        
        await asyncio.sleep(1)
        
        await self.send_message(
            "Remember when we talked about marine biology?",
            expected_category="conversational"
        )
        
        await asyncio.sleep(1)
        
        # Test 4: TEMPORAL queries (chronological scroll)
        await self.send_message(
            "What was the first thing I asked you?",
            expected_category="temporal"
        )
        
        await asyncio.sleep(1)
        
        # Test 5: GENERAL queries (content default)
        await self.send_message(
            "Tell me about the ocean",
            expected_category="general"
        )
        
        await asyncio.sleep(1)
        
        await self.send_message(
            "What do you think about coral reefs?",
            expected_category="general"
        )
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print test summary."""
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print(f"{'='*80}\n")
        
        # Print detailed results
        print("Detailed Results:")
        for result in self.results:
            status = "✅" if result.get('routing_correct') else "❌"
            print(f"{status} Test {result['test']}: {result['expected_category'].upper()}")
            print(f"   Message: {result['message']}")
            print(f"   Search Type: {result.get('actual_search_type', 'N/A')}")
            print(f"   Vectors: {result.get('vectors_used', 'N/A')}")
            print()
        
        # Save results to JSON
        output_file = "/tmp/phase2_routing_test_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": self.total_tests,
                    "passed": self.passed_tests,
                    "failed": self.total_tests - self.passed_tests,
                    "success_rate": f"{(self.passed_tests/self.total_tests*100):.1f}%"
                },
                "results": self.results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"📝 Results saved to: {output_file}")


async def main():
    """Main test runner."""
    tester = Phase2RoutingTester()
    
    try:
        await tester.run_comprehensive_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0 if tester.passed_tests == tester.total_tests else 1)


if __name__ == "__main__":
    asyncio.run(main())
