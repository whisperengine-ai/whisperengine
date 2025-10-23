#!/usr/bin/env python3
"""
Multi-Vector Routing Integration Test

Tests the multi-vector routing system by sending different query types
to a character bot via HTTP API and validating the routing behavior.

Query Types Tested:
1. EMOTION_FOCUSED → emotion_primary vector strategy
2. SEMANTIC_FOCUSED → semantic_primary vector strategy  
3. BALANCED → balanced_fusion vector strategy
4. SIMPLE → content_primary vector strategy
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, Any, List


class MultiVectorRoutingTester:
    """Test multi-vector routing with fresh user IDs"""
    
    def __init__(self, bot_name: str = "elena", bot_port: int = 9091):
        self.bot_name = bot_name
        self.bot_port = bot_port
        self.base_url = f"http://localhost:{bot_port}"
        self.test_results = []
        
    async def send_test_message(self, user_id: str, message: str, expected_classification: str) -> Dict[str, Any]:
        """Send a test message and return the response"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "user_id": user_id,
            "message": message,
            "metadata": {
                "platform": "api_test",
                "channel_type": "dm"
            }
        }
        
        print(f"\n📤 Sending test message:")
        print(f"   User: {user_id}")
        print(f"   Message: {message}")
        print(f"   Expected: {expected_classification}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Response received: {result.get('response', '')[:100]}...")
                        return {
                            'success': True,
                            'user_id': user_id,
                            'message': message,
                            'expected_classification': expected_classification,
                            'response': result.get('response'),
                            'metadata': result.get('metadata', {})
                        }
                    else:
                        error_text = await response.text()
                        print(f"❌ HTTP {response.status}: {error_text}")
                        return {
                            'success': False,
                            'user_id': user_id,
                            'message': message,
                            'expected_classification': expected_classification,
                            'error': f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {
                'success': False,
                'user_id': user_id,
                'message': message,
                'expected_classification': expected_classification,
                'error': str(e)
            }
    
    async def run_test_suite(self) -> List[Dict[str, Any]]:
        """Run complete test suite with all query types"""
        
        print("=" * 80)
        print(f"🧪 Multi-Vector Routing Test Suite")
        print(f"   Bot: {self.bot_name} (port {self.bot_port})")
        print(f"   Time: {datetime.utcnow().isoformat()}")
        print("=" * 80)
        
        # Generate unique user IDs for this test run
        timestamp = int(datetime.utcnow().timestamp())
        
        test_cases = [
            {
                'user_id': f'test_emotion_{timestamp}',
                'message': "I'm feeling really anxious about my upcoming presentation. I keep worrying about what could go wrong and it's affecting my sleep.",
                'expected_classification': 'EMOTION_FOCUSED',
                'description': 'Emotional query with anxiety and worry'
            },
            {
                'user_id': f'test_semantic_{timestamp}',
                'message': "Can you explain the difference between machine learning and deep learning? What are the key architectural differences?",
                'expected_classification': 'SEMANTIC_FOCUSED',
                'description': 'Technical/semantic query about concepts'
            },
            {
                'user_id': f'test_balanced_{timestamp}',
                'message': "How do you personally deal with stress and pressure? I'd love to hear your approach to maintaining balance.",
                'expected_classification': 'BALANCED',
                'description': 'Complex query mixing personal/emotional/semantic'
            },
            {
                'user_id': f'test_simple_{timestamp}',
                'message': "What's your favorite color?",
                'expected_classification': 'SIMPLE',
                'description': 'Simple factual query'
            }
        ]
        
        results = []
        
        for idx, test_case in enumerate(test_cases, 1):
            print(f"\n{'=' * 80}")
            print(f"Test {idx}/{len(test_cases)}: {test_case['description']}")
            print(f"{'=' * 80}")
            
            result = await self.send_test_message(
                user_id=test_case['user_id'],
                message=test_case['message'],
                expected_classification=test_case['expected_classification']
            )
            
            result['description'] = test_case['description']
            results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(2)
        
        self.test_results = results
        return results
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        successful = [r for r in self.test_results if r['success']]
        failed = [r for r in self.test_results if not r['success']]
        
        print(f"\n✅ Successful: {len(successful)}/{len(self.test_results)}")
        print(f"❌ Failed: {len(failed)}/{len(self.test_results)}")
        
        if successful:
            print("\n✅ PASSED TESTS:")
            for result in successful:
                print(f"   • {result['expected_classification']}: {result['description']}")
        
        if failed:
            print("\n❌ FAILED TESTS:")
            for result in failed:
                print(f"   • {result['expected_classification']}: {result['description']}")
                print(f"     Error: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 80)
        print("📝 LOG VALIDATION INSTRUCTIONS")
        print("=" * 80)
        print("\nTo validate multi-vector routing is working, check the bot logs for:")
        print("\n1. Query Classification:")
        print("   🎯 MULTI-VECTOR: Query classified as EMOTION_FOCUSED")
        print("   🎯 MULTI-VECTOR: Query classified as SEMANTIC_FOCUSED")
        print("   🎯 MULTI-VECTOR: Query classified as BALANCED")
        print("   🎯 MULTI-VECTOR: Query classified as SIMPLE")
        
        print("\n2. Vector Strategy Selection:")
        print("   🎭 MULTI-VECTOR: Using emotion-primary search")
        print("   🎭 MULTI-VECTOR: Using semantic-primary search")
        print("   🎭 MULTI-VECTOR: Using balanced-fusion search")
        print("   🎭 MULTI-VECTOR: Using content-primary search")
        
        print("\n3. Retrieval Results:")
        print("   ✅ MULTI-VECTOR: Retrieved X memories in Xms")
        
        print("\n4. Effectiveness Tracking:")
        print("   📊 TRACKING: Recorded vector strategy effectiveness")
        
        print("\n" + "=" * 80)
        print("🔍 Check logs with:")
        print(f"   docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs {self.bot_name}-bot | grep 'MULTI-VECTOR'")
        print("=" * 80)
        
        return len(failed) == 0
    
    def save_results(self, output_file: str = "multi_vector_routing_test_results.json"):
        """Save test results to JSON file"""
        output_path = f"/Users/markcastillo/git/whisperengine/tests/automated/{output_file}"
        
        output_data = {
            'test_suite': 'multi_vector_routing',
            'bot_name': self.bot_name,
            'bot_port': self.bot_port,
            'timestamp': datetime.utcnow().isoformat(),
            'total_tests': len(self.test_results),
            'successful': len([r for r in self.test_results if r['success']]),
            'failed': len([r for r in self.test_results if not r['success']]),
            'results': self.test_results
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")


async def main():
    """Main test execution"""
    # Parse command line arguments
    bot_name = sys.argv[1] if len(sys.argv) > 1 else "elena"
    
    # Bot port mapping
    bot_ports = {
        'elena': 9091,
        'marcus': 9092,
        'jake': 9097,
        'ryan': 9093,
        'gabriel': 9095,
        'sophia': 9096,
        'dream': 9094,
        'dotty': 9098,
        'aetheris': 9099,
        'aethys': 3007
    }
    
    bot_port = bot_ports.get(bot_name.lower(), 9091)
    
    # Run tests
    tester = MultiVectorRoutingTester(bot_name=bot_name, bot_port=bot_port)
    await tester.run_test_suite()
    
    # Print summary
    all_passed = tester.print_summary()
    
    # Save results
    tester.save_results()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
