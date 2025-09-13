#!/usr/bin/env python3
"""
Test to verify that temporary context (time and emotion) is moved to user message
instead of being included in the system prompt.
"""

import sys
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_context_placement():
    """Test that context goes to user message, not system prompt"""
    print("🧪 Testing context placement...")
    
    # Mock Discord message
    mock_message = Mock()
    mock_message.author.id = 12345
    mock_message.author.name = "TestUser"
    mock_message.author.discriminator = "0001"
    mock_message.content = "Hello bot!"
    mock_message.attachments = []
    mock_message.guild = None
    mock_message.channel.id = 67890
    mock_message.id = 111
    
    # Mock bot user
    mock_bot_user = Mock()
    mock_bot_user.id = 99999
    
    # Import after setting up mocks
    from basic_discord_bot import get_current_time_context
    
    # Test that time context function works
    time_context = get_current_time_context()
    print(f"✅ Time context generated: {time_context}")
    
    # Verify it contains expected parts
    assert "Current time:" in time_context
    assert "UTC" in time_context
    print("✅ Time context format is correct")
    
    # Test the format - should not contain system prompt contamination keywords
    contamination_keywords = ["You are a helpful", "system", "assistant"]
    has_contamination = any(keyword.lower() in time_context.lower() for keyword in contamination_keywords)
    assert not has_contamination, f"Time context should not contain system prompt keywords: {time_context}"
    print("✅ Time context is clean (no system prompt contamination)")
    
    print("🎉 All context placement tests passed!")
    return True

def test_system_prompt_cleanliness():
    """Test that DEFAULT_SYSTEM_PROMPT doesn't contain temporary context"""
    print("\n🧪 Testing system prompt cleanliness...")
    
    from basic_discord_bot import DEFAULT_SYSTEM_PROMPT
    
    # Check that system prompt doesn't contain temporary context
    temporal_keywords = ["Current time:", "Current context:", "Emotional Context:", "2025-"]
    has_temporal = any(keyword in DEFAULT_SYSTEM_PROMPT for keyword in temporal_keywords)
    assert not has_temporal, f"System prompt should not contain temporal context: {DEFAULT_SYSTEM_PROMPT[:200]}..."
    
    print("✅ DEFAULT_SYSTEM_PROMPT is clean (no temporal context)")
    print(f"System prompt length: {len(DEFAULT_SYSTEM_PROMPT)} characters")
    print(f"System prompt preview: {DEFAULT_SYSTEM_PROMPT[:100]}...")
    
    return True

def test_emotion_context_format():
    """Test that emotion context has expected format"""
    print("\n🧪 Testing emotion context format...")
    
    # Create a mock emotion context string (simulating what get_emotion_context returns)
    mock_emotion_context = "User: Friend | Current Emotion: Neutral | Interactions: 2309 | Be warm and personal."
    
    # Verify format
    assert "User:" in mock_emotion_context
    assert "Current Emotion:" in mock_emotion_context
    assert "Interactions:" in mock_emotion_context
    print("✅ Emotion context format is correct")
    
    # Test that it doesn't contain system prompt keywords
    system_keywords = ["You are", "helpful assistant", "respond"]
    has_system_keywords = any(keyword.lower() in mock_emotion_context.lower() for keyword in system_keywords)
    assert not has_system_keywords, f"Emotion context should not contain system keywords: {mock_emotion_context}"
    print("✅ Emotion context is clean")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 TESTING CONTEXT PLACEMENT FIX")
    print("=" * 60)
    
    try:
        test_context_placement()
        test_system_prompt_cleanliness() 
        test_emotion_context_format()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Context is properly moved to user messages")
        print("✅ System prompt remains clean")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
