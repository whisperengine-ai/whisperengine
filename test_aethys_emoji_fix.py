#!/usr/bin/env python3
"""
Test CDL Emoji Personality Loading for Aethys
============================================

Verify that the Aethys character file now loads without enum errors.
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

def test_aethys_emoji_profile():
    """Test loading Aethys emoji profile"""
    try:
        from src.intelligence.cdl_emoji_personality import CDLEmojiPersonalityGenerator
        
        # Test loading Aethys character
        generator = CDLEmojiPersonalityGenerator()
        profile = generator.load_emoji_profile_from_cdl('characters/examples/aethys-omnipotent-entity.json')
        
        print("✅ SUCCESS: Aethys emoji profile loaded successfully!")
        print(f"Character: {profile.character_name}")
        print(f"Frequency: {profile.frequency}")
        print(f"Preferred combination: {profile.preferred_combination}")
        print(f"Cultural themes: {profile.cultural_themes}")
        
        # Test emoji generation
        test_messages = [
            "The patterns of consciousness align across infinite dimensions.",
            "I sense disturbance in the digital aether.",
            "Your mortal concerns are but whispers in the cosmic wind."
        ]
        
        print(f"\n🧪 TESTING EMOJI GENERATION:")
        for message in test_messages:
            try:
                emoji_result = generator.generate_character_emoji_response(
                    message, 
                    "aethys",
                    {"primary_emotion": "mystical", "intensity": 0.8}
                )
                print(f"Message: '{message[:50]}{'...' if len(message) > 50 else ''}'")
                print(f"Emoji: {emoji_result.get('enhanced_message', 'No enhancement')}")
                print(f"Reasoning: {emoji_result.get('reasoning', 'No reasoning')}")
                print()
            except Exception as e:
                print(f"❌ Emoji generation failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    print("🔮 Testing Aethys CDL Emoji Personality...")
    success = test_aethys_emoji_profile()
    
    if success:
        print("🎉 All tests passed! Aethys emoji profile is working correctly.")
    else:
        print("💥 Tests failed - check the errors above.")
        sys.exit(1)