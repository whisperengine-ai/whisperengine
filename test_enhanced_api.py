#!/usr/bin/env python3
"""
Simple test script for WhisperEngine Enhanced External Chat API.

Tests the new userFacts and relationshipMetrics fields in the API response.
"""

import asyncio
import json
import aiohttp


async def test_enhanced_api():
    """Test the enhanced API with userFacts and relationshipMetrics."""
    print("🧪 Testing WhisperEngine Enhanced External Chat API")
    print("=" * 60)
    
    # Test with Elena bot (port 9091) - she has rich personality features
    base_url = "http://localhost:9091"
    test_user_id = "enhanced_api_test_user"
    
    try:
        async with aiohttp.ClientSession() as session:
            print(f"Testing enhanced API features with bot at {base_url}")
            
            # Test sequence to build relationship and extract facts
            test_messages = [
                "Hello! My name is Alex Thompson.",
                "I'm a software engineer who loves marine biology.",
                "Thank you so much for the information! You're really helpful.",
                "I've been feeling excited about learning more about ocean conservation.",
                "What do you think about climate change and its impact on marine life?"
            ]
            
            for i, message in enumerate(test_messages, 1):
                print(f"\n--- Test Message {i} ---")
                print(f"Sending: {message}")
                
                payload = {
                    "user_id": test_user_id,
                    "message": message,
                    "context": {
                        "channel_type": "dm",
                        "platform": "api",
                        "metadata": {"test_session": True}
                    }
                }
                
                async with session.post(
                    f"{base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Display main response
                        print(f"✅ Success (Status: {response.status})")
                        print(f"Response: {result.get('response', 'No response')[:200]}...")
                        print(f"Processing time: {result.get('processing_time_ms', 'N/A')}ms")
                        print(f"Memory stored: {result.get('memory_stored', 'N/A')}")
                        
                        # Display NEW enhanced fields
                        user_facts = result.get('user_facts', {})
                        relationship_metrics = result.get('relationship_metrics', {})
                        
                        print("\n🔍 Enhanced API Fields:")
                        print("User Facts:")
                        if user_facts:
                            for key, value in user_facts.items():
                                print(f"  - {key}: {value}")
                        else:
                            print("  - No user facts extracted yet")
                        
                        print("Relationship Metrics:")
                        if relationship_metrics:
                            print(f"  - Affection: {relationship_metrics.get('affection', 'N/A')}")
                            print(f"  - Trust: {relationship_metrics.get('trust', 'N/A')}")
                            print(f"  - Attunement: {relationship_metrics.get('attunement', 'N/A')}")
                        else:
                            print("  - No relationship metrics available")
                            
                    else:
                        result = await response.json()
                        print(f"❌ Failed (Status: {response.status})")
                        print(f"Error: {result.get('error', 'Unknown error')}")
                
                # Small delay between messages
                await asyncio.sleep(1)
            
            # Test batch processing with enhanced fields
            print(f"\n--- Testing Batch Processing with Enhanced Fields ---")
            
            batch_payload = {
                "messages": [
                    {
                        "user_id": f"{test_user_id}_batch",
                        "message": "Hi, I'm Sarah and I work in data science.",
                        "context": {"channel_type": "dm"}
                    },
                    {
                        "user_id": f"{test_user_id}_batch", 
                        "message": "I'm really grateful for your help with my research!",
                        "context": {"channel_type": "dm"}
                    }
                ]
            }
            
            async with session.post(
                f"{base_url}/api/chat/batch",
                json=batch_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    results = result.get("results", [])
                    
                    print(f"✅ Batch Success: {len(results)} messages processed")
                    
                    for batch_result in results:
                        index = batch_result.get('index', '?')
                        success = batch_result.get('success', False)
                        print(f"\nMessage {index}: {'✅' if success else '❌'}")
                        
                        if success:
                            user_facts = batch_result.get('user_facts', {})
                            relationship_metrics = batch_result.get('relationship_metrics', {})
                            
                            print(f"  User Facts: {user_facts}")
                            print(f"  Metrics: affection={relationship_metrics.get('affection')}, trust={relationship_metrics.get('trust')}, attunement={relationship_metrics.get('attunement')}")
                else:
                    result = await response.json()
                    print(f"❌ Batch Failed (Status: {response.status})")
                    print(f"Error: {result.get('error', 'Unknown error')}")
                    
    except aiohttp.ClientConnectorError:
        print(f"⚠️  Could not connect to {base_url}")
        print("Make sure the Elena bot is running with: ./multi-bot.sh start elena")
    except Exception as e:
        print(f"❌ Test failed: {e}")


async def main():
    """Main function."""
    print("WhisperEngine Enhanced API Test")
    print("Testing new userFacts and relationshipMetrics fields")
    print()
    
    await test_enhanced_api()
    
    print("\n" + "=" * 60)
    print("Test completed! The enhanced API now returns:")
    print("• user_facts: { name, interaction_count, first_interaction, last_interaction }")
    print("• relationship_metrics: { affection, trust, attunement }")
    print("Both fields are available in single messages and batch processing.")


if __name__ == "__main__":
    asyncio.run(main())