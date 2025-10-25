"""
Integration test for mystical symbol detection in message processing.

This test validates that messages with mystical symbols are silently ignored
at the message processing level.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.mystical_symbol_detector import get_mystical_symbol_detector


def test_integration():
    """Test integration with message security validation."""
    detector = get_mystical_symbol_detector()
    
    print("=" * 80)
    print("MYSTICAL SYMBOL DETECTION - INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Simulated messages from users
    test_messages = [
        ("user_123", "Hello! How are you today?", False, "Normal conversation"),
        ("user_456", "☯️🕉️✡️☪️☸️⛤⛥", True, "Pure mystical symbols"),
        ("user_789", "Can you help me with Python?", False, "Programming question"),
        ("user_101", "Tell me about ♈♉♊♋♌♍♎♏", True, "Zodiac spam"),
        ("user_102", "What's your favorite emoji? 😊", False, "Emoji question"),
        ("user_103", "ᚠᚢᚦᚨᚱᚲᚷᚹ runes", True, "Runic text"),
    ]
    
    ignored_count = 0
    processed_count = 0
    
    print("Simulating message security validation:\n")
    
    for user_id, message, should_ignore, description in test_messages:
        is_ignored, reason = detector.should_ignore_message(message)
        
        # Check if result matches expectation
        status = "✅" if is_ignored == should_ignore else "❌"
        
        if is_ignored:
            ignored_count += 1
            action = "🔮 SILENTLY IGNORED"
        else:
            processed_count += 1
            action = "✅ PROCESSED"
        
        print(f"{status} User: {user_id}")
        print(f"   Message: {repr(message[:50])}")
        print(f"   Action: {action}")
        print(f"   Description: {description}")
        if reason:
            print(f"   Reason: {reason}")
        print()
    
    print("=" * 80)
    print(f"SUMMARY:")
    print(f"  Processed: {processed_count} messages")
    print(f"  Silently Ignored: {ignored_count} messages")
    print("=" * 80)
    print()
    
    # Verify expected counts
    expected_ignored = sum(1 for _, _, should_ignore, _ in test_messages if should_ignore)
    expected_processed = len(test_messages) - expected_ignored
    
    if ignored_count == expected_ignored and processed_count == expected_processed:
        print("✅ INTEGRATION TEST PASSED")
        print(f"   All {len(test_messages)} messages handled correctly")
        return True
    else:
        print("❌ INTEGRATION TEST FAILED")
        print(f"   Expected: {expected_ignored} ignored, {expected_processed} processed")
        print(f"   Got: {ignored_count} ignored, {processed_count} processed")
        return False


if __name__ == "__main__":
    print("\n🔮 Mystical Symbol Detection - Integration Test\n")
    success = test_integration()
    sys.exit(0 if success else 1)
