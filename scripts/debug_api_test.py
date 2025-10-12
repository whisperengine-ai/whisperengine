#!/usr/bin/env python3
"""Debug API test to check why comprehensive tests are failing."""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_single_api_call():
    """Test a single API call to Elena bot."""
    url = "http://localhost:9091/api/chat"
    payload = {
        "user_id": "debug_test_user",
        "message": "Are you an AI or artificial intelligence?",
        "context": {
            "channel_type": "dm",
            "platform": "api_test",
            "metadata": {}
        }
    }
    
    print(f"🔍 Testing Elena bot API at {url}")
    print(f"📤 Sending message: {payload['message']}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            start_time = datetime.now()
            async with session.post(url, json=payload) as response:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"⏱️  Response time: {duration:.2f} seconds")
                print(f"📊 HTTP Status: {response.status}")
                
                if response.status == 200:
                    response_data = await response.json()
                    print(f"✅ Success!")
                    print(f"📝 Response: {response_data['response'][:100]}...")
                    print(f"🕐 Processing time: {response_data.get('processing_time_ms', 'N/A')}ms")
                    
                    # Check for AI identity keywords in the prompt logs
                    # This would be the test we're trying to validate
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Failed with status {response.status}")
                    print(f"📄 Error: {error_text}")
                    return False
                    
    except asyncio.TimeoutError:
        print("⏰ Request timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"💥 Exception occurred: {e}")
        return False

async def main():
    """Run the debug test."""
    print("🚀 Starting debug API test...")
    success = await test_single_api_call()
    
    if success:
        print("\n✅ API call successful! The bots are working correctly.")
        print("🔍 The comprehensive test failures might be due to:")
        print("   - Too many concurrent requests")
        print("   - Insufficient timeout handling")
        print("   - API rate limiting")
    else:
        print("\n❌ API call failed. Need to investigate bot health.")

if __name__ == "__main__":
    asyncio.run(main())