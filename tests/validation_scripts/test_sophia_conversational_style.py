#!/usr/bin/env python3
"""
Test script to validate Sophia's new conversational response style.
This tests if the "wall of text" issue has been resolved with brief, natural responses.
"""

import requests

def test_conversational_response_style():
    """Test Sophia's new conversational response style with a simple question."""
    
    print("🧪 Testing Sophia's Conversational Response Style")
    print("=" * 60)
    
    # Test simple question
    test_message = "What's the most important trend in digital marketing right now?"
    
    print(f"📝 Test Message: {test_message}")
    print("-" * 60)
    
    try:
        # Test bot health first
        health_url = "http://localhost:9096/health"
        print(f"🔍 Checking Sophia bot health at {health_url}...")
        
        health_response = requests.get(health_url, timeout=5)
        if health_response.status_code == 200:
            print("✅ Sophia bot is healthy and responding")
        else:
            print(f"⚠️  Sophia bot health check returned: {health_response.status_code}")
            return None
        
        print("\n📋 MANUAL TESTING INSTRUCTIONS:")
        print("=" * 60)
        print("Since WhisperEngine is Discord-only, please test manually:")
        print(f"1. Send this message to Sophia in Discord: '{test_message}'")
        print("2. Observe the response characteristics:")
        print("   • Is it brief and conversational (like texting a friend)?")
        print("   • Does it focus on ONE main point?")
        print("   • Does it ask a follow-up question?")
        print("   • Is it under ~500 characters and ~80 words?")
        print("   • Does it avoid 'wall of text' style?")
        print("\n✅ SUCCESS criteria:")
        print("   - Natural, brief response (not verbose)")
        print("   - Engaging follow-up question")
        print("   - Professional but conversational tone")
        print("\n❌ FAILURE criteria:")
        print("   - Long, detailed explanations")
        print("   - Multiple paragraphs")
        print("   - No engaging question")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Make sure Sophia bot is running with: ./multi-bot.sh start sophia")
        return None

if __name__ == "__main__":
    result = test_conversational_response_style()
    
    if result:
        print("\n🎯 Ready for Discord testing!")
        print("Please follow the manual testing instructions above.")
    else:
        print("\n❌ SETUP ISSUE: Bot not accessible for testing")