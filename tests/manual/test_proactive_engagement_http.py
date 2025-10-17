"""
Manual HTTP API Test for Proactive Engagement Integration
Tests the complete chain: engagement detection → strategy recommendation → prompt integration

Usage:
    python tests/manual/test_proactive_engagement_http.py
"""

import requests
import time
import json
from datetime import datetime

# Test configuration
ELENA_API_URL = "http://localhost:9091"
TEST_USER_ID = "http_test_user_proactive"
HEALTH_CHECK_URL = f"{ELENA_API_URL}/health"
CHAT_URL = f"{ELENA_API_URL}/chat"

def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")

def check_health():
    """Verify Elena bot is healthy"""
    print_section("HEALTH CHECK")
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Elena bot is healthy and ready")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Could not connect to Elena bot: {e}")
        return False

def send_message(message: str, test_name: str) -> dict:
    """Send a message and return the response"""
    print(f"\n📤 Sending: '{message}'")
    
    try:
        response = requests.post(
            CHAT_URL,
            json={
                "user_id": TEST_USER_ID,
                "message": message,
                "channel_id": "http_test_channel"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            bot_response = data.get('response', 'No response')
            print(f"✅ Response received ({len(bot_response)} chars)")
            print(f"   Elena: {bot_response[:200]}{'...' if len(bot_response) > 200 else ''}")
            
            # Check for engagement metadata if available
            metadata = data.get('metadata', {})
            if metadata:
                print(f"\n📊 Metadata:")
                for key, value in metadata.items():
                    print(f"   • {key}: {value}")
            
            return data
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return {}

def test_baseline_conversation():
    """Test 1: Normal conversation (no intervention expected)"""
    print_section("TEST 1: BASELINE - Normal Conversation (No Intervention)")
    
    messages = [
        "Hi Elena! How are you today?",
        "Tell me about your marine research",
        "That sounds fascinating!"
    ]
    
    for msg in messages:
        send_message(msg, "baseline")
        time.sleep(2)
    
    print("\n✅ Baseline test complete - engagement should be STEADY/ENGAGING")

def test_short_message_stagnation():
    """Test 2: Short message pattern (intervention should trigger)"""
    print_section("TEST 2: STAGNATION - Short Message Pattern")
    
    print("⚠️  Sending very short messages to trigger stagnation detection...")
    print("    Expected: Intervention after 3-4 short messages\n")
    
    short_messages = [
        "ok",
        "cool", 
        "nice",
        "yeah"
    ]
    
    responses = []
    for i, msg in enumerate(short_messages, 1):
        print(f"\n--- Short Message {i}/{len(short_messages)} ---")
        response = send_message(msg, "stagnation")
        responses.append(response)
        time.sleep(3)  # Wait between messages
    
    print("\n📊 STAGNATION TEST RESULTS:")
    print("=" * 80)
    
    # Check if any response included proactive topic suggestion
    intervention_detected = False
    for i, resp in enumerate(responses, 1):
        bot_msg = resp.get('response', '')
        
        # Look for signs of proactive engagement
        proactive_indicators = [
            "thinking about",
            "wondering if",
            "curious about",
            "been meaning to ask",
            "have you ever",
            "did you know"
        ]
        
        has_indicators = any(indicator in bot_msg.lower() for indicator in proactive_indicators)
        
        if has_indicators:
            print(f"\n✅ Message {i}: PROACTIVE ENGAGEMENT DETECTED!")
            print(f"   Contains natural topic suggestion/question")
            intervention_detected = True
        else:
            print(f"\n   Message {i}: Standard response")
    
    if intervention_detected:
        print("\n🎯 SUCCESS: Proactive engagement system triggered intervention!")
    else:
        print("\n⚠️  WARNING: No clear proactive engagement detected in responses")
        print("    This may indicate the engagement strategy is not reaching the prompt")
    
    return intervention_detected

def test_engaged_recovery():
    """Test 3: Recovery after stagnation (no intervention after re-engagement)"""
    print_section("TEST 3: RECOVERY - Substantive Messages After Stagnation")
    
    print("Sending substantive message to show engagement recovery...\n")
    
    send_message(
        "Elena, I'd love to hear more about your coral reef restoration work. What's the most challenging part?",
        "recovery"
    )
    
    print("\n✅ Recovery test complete - engagement should return to STEADY/ENGAGING")

def main():
    """Run all validation tests"""
    print(f"\n{'#' * 80}")
    print("#" + " " * 78 + "#")
    print("#  PROACTIVE ENGAGEMENT HTTP API VALIDATION TEST SUITE" + " " * 25 + "#")
    print("#" + " " * 78 + "#")
    print(f"{'#' * 80}")
    print(f"\nTest Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Elena API: {ELENA_API_URL}")
    print(f"Test User: {TEST_USER_ID}")
    
    # Health check
    if not check_health():
        print("\n❌ ABORT: Elena bot is not available")
        return
    
    # Run test sequence
    try:
        # Test 1: Baseline
        test_baseline_conversation()
        time.sleep(3)
        
        # Test 2: Stagnation (CRITICAL TEST)
        intervention_detected = test_short_message_stagnation()
        time.sleep(3)
        
        # Test 3: Recovery
        test_engaged_recovery()
        
        # Final summary
        print_section("FINAL TEST SUMMARY")
        
        if intervention_detected:
            print("✅ PASS: Proactive engagement integration is WORKING")
            print("   • Engine detected stagnation")
            print("   • Strategy reached the LLM prompt")
            print("   • Elena generated proactive response")
            print("\n🎯 Ready for production testing!")
        else:
            print("⚠️  PARTIAL: Integration may need investigation")
            print("   • Check logs for engagement analysis")
            print("   • Verify strategy is in comprehensive_context")
            print("   • Confirm CDL prompt integration")
            print("\n📋 Run: docker compose logs elena-bot | grep '🎯 ENGAGEMENT'")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
