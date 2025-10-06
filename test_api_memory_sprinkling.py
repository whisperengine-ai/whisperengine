#!/usr/bin/env python3
"""
Test ChatGPT-like memory sprinkling via HTTP API
"""

import asyncio
import aiohttp
import json

async def test_memory_sprinkling():
    """Test various query types to see memory sprinkling behavior"""
    
    test_queries = [
        # Direct factual recall (should get primary facts)
        "What art books do I have?",
        
        # Creative/conversational (should get contextual memory sprinkling)
        "I'm feeling stuck with my art today",
        
        # Recommendation style (should trigger relationship discovery)
        "What books might help me with drawing figures?",
        
        # Equipment question (should find equipment facts)
        "What drawing tablet should I use?",
    ]
    
    base_url = "http://localhost:9099"
    user_id = "672814231002939413"
    
    async with aiohttp.ClientSession() as session:
        for query in test_queries:
            print(f"🎯 Testing: '{query}'")
            print("-" * 60)
            
            try:
                payload = {
                    "user_id": user_id,
                    "message": query,
                    "context": {"platform": "api"}
                }
                
                async with session.post(
                    f"{base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get('response', 'No response')
                        
                        # Show first 300 chars of response
                        preview = response_text[:300] + "..." if len(response_text) > 300 else response_text
                        print(f"✅ Response: {preview}")
                        
                        # Check if memories were used
                        metadata = data.get('metadata', {})
                        ai_components = metadata.get('ai_components', {})
                        
                        print(f"📊 Processing time: {data.get('processing_time_ms', 0)}ms")
                        print(f"💾 Memory stored: {data.get('memory_stored', False)}")
                        
                    else:
                        print(f"❌ Error: HTTP {response.status}")
                        
            except asyncio.TimeoutError:
                print("⏰ Request timed out")
            except Exception as e:
                print(f"❌ Error: {e}")
                
            print()
            print()

if __name__ == "__main__":
    asyncio.run(test_memory_sprinkling())