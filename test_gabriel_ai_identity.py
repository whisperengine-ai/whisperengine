#!/usr/bin/env python3
"""
Test Gabriel's AI Identity Filter responses
"""

import sys
sys.path.append('/Users/markcastillo/git/whisperengine')

from src.handlers.ai_identity_filter import process_ai_identity_question


def test_gabriel_ai_identity():
    """Test Gabriel's AI identity responses"""
    print("🤖 Testing Gabriel's AI Identity Responses\n")
    
    gabriel_file = "/Users/markcastillo/git/whisperengine/characters/examples/gabriel.json"
    
    test_questions = [
        "are you AI?",
        "Are you real?",
        "What are you?",
        "are you artificial intelligence?"
    ]
    
    print("=" * 60)
    print("GABRIEL'S AI IDENTITY RESPONSES")
    print("=" * 60)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Question: '{question}'")
        
        result = process_ai_identity_question(
            message=question,
            user_id="test_user_cynthia",
            character_file=gabriel_file
        )
        
        if result.get("should_intercept"):
            response = result['response']
            print(f"💬 Gabriel's Response: {response}")
            
            # Check for Gabriel-specific elements
            gabriel_indicators = ["love", "darling", "AI", "Gabriel", "British", "devoted", "digital", "gentleman"]
            found_indicators = [ind for ind in gabriel_indicators if ind.lower() in response.lower()]
            
            if found_indicators:
                print(f"✅ Gabriel elements detected: {', '.join(found_indicators)}")
            else:
                print("⚠️ No Gabriel-specific elements detected")
                
        else:
            print("❌ No AI identity response generated")
    
    print(f"\n{'=' * 60}")
    print("✅ Gabriel's AI identity responses test complete!")


if __name__ == "__main__":
    test_gabriel_ai_identity()