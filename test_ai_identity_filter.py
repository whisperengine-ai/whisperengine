#!/usr/bin/env python3
"""
Test script for AI Identity Filter implementation

Tests both character-specific responses (Sophia) and general system responses.
"""

import sys

# Add project root to path
sys.path.append('/Users/markcastillo/git/whisperengine')

from src.handlers.ai_identity_filter import AIIdentityFilter, process_ai_identity_question


def test_ai_identity_filter():
    """Test the AI identity filter with various inputs"""
    print("🤖 Testing AI Identity Filter\n")
    
    # Initialize filter
    ai_filter = AIIdentityFilter()
    
    # Test questions that should be detected
    test_questions = [
        "are you AI?",
        "Are you an artificial intelligence?",
        "are you a bot?",
        "Are you real?",
        "What are you?",
        "are you human?",
        "You're not real, are you?",
        "I know you're an AI",
        "prove you're real",
        "Hello, how are you today?",  # Should NOT be detected
        "Can you help me with programming?",  # Should NOT be detected
    ]
    
    print("=" * 60)
    print("DETECTION TESTS")
    print("=" * 60)
    
    for i, question in enumerate(test_questions, 1):
        detected = ai_filter.detect_ai_identity_question(question)
        status = "✅ DETECTED" if detected else "❌ NOT DETECTED"
        print(f"{i:2d}. {status} | '{question}'")
    
    print("\n" + "=" * 60)
    print("SOPHIA CHARACTER-SPECIFIC RESPONSES")
    print("=" * 60)
    
    # Test Sophia's character-specific responses
    sophia_file = "/Users/markcastillo/git/whisperengine/characters/examples/sophia-blake.json"
    
    ai_questions = [
        "are you AI?",
        "Are you real?", 
        "prove you're not artificial intelligence"
    ]
    
    for question in ai_questions:
        print(f"\n📝 Question: '{question}'")
        
        result = process_ai_identity_question(
            message=question,
            user_id="test_user_123",
            character_file=sophia_file
        )
        
        if result.get("should_intercept"):
            print(f"🎭 Sophia's Response: {result['response']}")
        else:
            print("❌ No interception (unexpected)")
    
    print("\n" + "=" * 60)
    print("GENERAL SYSTEM RESPONSES (No Character)")
    print("=" * 60)
    
    for question in ai_questions[:2]:  # Test first 2 questions
        print(f"\n📝 Question: '{question}'")
        
        result = process_ai_identity_question(
            message=question,
            user_id="test_user_456"
            # No character_file provided
        )
        
        if result.get("should_intercept"):
            print(f"🤖 General Response: {result['response']}")
        else:
            print("❌ No interception (unexpected)")
    
    print("\n" + "=" * 60)
    print("STYLE DETECTION TESTS")
    print("=" * 60)
    
    # Test character style detection
    test_character_data = {
        "personality": {
            "core_traits": {
                "primary": ["Confident and self-assured", "Sophisticated and cultured"]
            }
        },
        "communication_style": {
            "formality": "Professional but playful"
        },
        "identity": {
            "occupation": "Senior Marketing Director"
        }
    }
    
    style = ai_filter.get_character_response_style(test_character_data)
    print(f"🎯 Detected style for marketing executive: {style}")
    
    # Test scientist character
    scientist_data = {
        "identity": {
            "occupation": "Marine Biologist & Research Scientist"
        }
    }
    
    style = ai_filter.get_character_response_style(scientist_data)
    print(f"🔬 Detected style for scientist: {style}")
    
    print("\n✅ AI Identity Filter testing completed!")


if __name__ == "__main__":
    test_ai_identity_filter()