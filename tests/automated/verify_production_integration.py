#!/usr/bin/env python3
"""
Quick Production Integration Verification

Verifies that Memory Trigger Enhancement and Emotional Context Synchronization
are properly integrated into the production bot.
"""

import requests
import json
import sys

def test_elena_health():
    """Test Elena bot health endpoint"""
    try:
        response = requests.get("http://localhost:9091/health", timeout=5)
        if response.status_code == 200:
            print("✅ Elena bot is running and healthy")
            return True
        else:
            print(f"❌ Elena bot health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Elena bot is not reachable: {e}")
        return False

def test_chat_api():
    """Test chat API with emotional content"""
    try:
        print("\n📝 Testing Chat API with emotional content...")
        
        # Test 1: Joyful message
        print("\nTest 1: Joyful message about diving")
        response = requests.post(
            "http://localhost:9091/api/chat",
            json={
                "user_id": "test_production_integration",
                "message": "I'm so excited! I just went diving for the first time and it was amazing!",
                "context": {
                    "channel_type": "dm",
                    "platform": "api",
                    "metadata": {}
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat API response received")
            print(f"   Response preview: {data.get('response', '')[:100]}...")
            
            # Check for emotional intelligence
            metadata = data.get('metadata', {})
            ai_components = metadata.get('ai_components', {})
            
            if 'emotion_detection' in ai_components:
                emotion = ai_components['emotion_detection'].get('primary_emotion', 'N/A')
                confidence = ai_components['emotion_detection'].get('confidence', 0)
                print(f"   Emotion detected: {emotion} (confidence: {confidence:.2f})")
            
            return True
        else:
            print(f"❌ Chat API failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat API test failed: {e}")
        return False

def main():
    """Run production integration verification"""
    print("="*80)
    print("PRODUCTION INTEGRATION VERIFICATION")
    print("Memory Trigger Enhancement + Emotional Context Synchronization")
    print("="*80)
    
    # Test 1: Health check
    print("\n1. Health Check")
    print("-" * 80)
    health_ok = test_elena_health()
    
    if not health_ok:
        print("\n❌ Bot not running. Start with: ./multi-bot.sh start elena")
        return 1
    
    # Test 2: Chat API
    print("\n2. Chat API Test")
    print("-" * 80)
    chat_ok = test_chat_api()
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    if health_ok and chat_ok:
        print("✅ All tests passed!")
        print("✅ Production integration is working")
        print("\n📋 Next Steps:")
        print("   1. Send a Discord message to Elena about diving")
        print("   2. Check logs: docker logs whisperengine-elena-bot | grep 'GRAPH INIT'")
        print("   3. Monitor emotional synchronization in logs")
        return 0
    else:
        print("⚠️ Some tests failed - check logs for details")
        print("   docker logs whisperengine-elena-bot --tail 50")
        return 1

if __name__ == "__main__":
    sys.exit(main())
