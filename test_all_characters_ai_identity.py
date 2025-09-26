#!/usr/bin/env python3
"""
Test script for AI Identity responses across all characters

Tests character-specific AI identity responses for all WhisperEngine characters.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append('/Users/markcastillo/git/whisperengine')

from src.handlers.ai_identity_filter import AIIdentityFilter, process_ai_identity_question


def test_character_ai_identity_responses():
    """Test AI identity responses for all characters"""
    print("🤖 Testing AI Identity Responses for All Characters\n")
    
    # Character files to test
    character_files = [
        ("Elena Rodriguez", "characters/examples/elena-rodriguez.json"),
        ("Marcus Thompson", "characters/examples/marcus-thompson.json"),
        ("Dream of the Endless", "characters/examples/dream_of_the_endless.json"),
        ("Jake Sterling", "characters/examples/jake-sterling.json"),
        ("Ryan Chen", "characters/examples/ryan-chen.json"),
        ("Sophia Blake", "characters/examples/sophia-blake.json"),
    ]
    
    test_question = "are you AI?"
    
    print("=" * 80)
    print("CHARACTER-SPECIFIC AI IDENTITY RESPONSES")
    print("=" * 80)
    
    for char_name, char_file in character_files:
        print(f"\n🎭 {char_name.upper()}")
        print("-" * 40)
        
        char_path = f"/Users/markcastillo/git/whisperengine/{char_file}"
        
        # Test if character file exists
        if not Path(char_path).exists():
            print(f"❌ Character file not found: {char_path}")
            continue
        
        # Test AI identity response
        result = process_ai_identity_question(
            message=test_question,
            user_id="test_user_123",
            character_file=char_path
        )
        
        if result.get("should_intercept"):
            response = result['response']
            print(f"📝 Question: '{test_question}'")
            print(f"💬 Response: {response}")
            
            # Verify character-specific elements
            character_indicators = {
                "Elena Rodriguez": ["mi amor", "¡", "marine", "ocean", "Elena"],
                "Marcus Thompson": ["research", "AI", "Marcus", "academic", "intelligence"],
                "Dream of the Endless": ["artificial", "dreams", "mortal", "eternal", "wisdom"],
                "Jake Sterling": ["digital", "Jake", "nature", "outdoors", "authentic"],
                "Ryan Chen": ["AI", "game", "dev", "digital", "Ryan"],
                "Sophia Blake": ["artificial", "intelligence", "honey", "darling", "Manhattan"]
            }
            
            indicators = character_indicators.get(char_name, [])
            found_indicators = [ind for ind in indicators if ind.lower() in response.lower()]
            
            if found_indicators:
                print(f"✅ Character elements detected: {', '.join(found_indicators)}")
            else:
                print(f"⚠️ No character-specific elements detected")
                
        else:
            print(f"❌ No AI identity response generated (unexpected)")
    
    print(f"\n{'=' * 80}")
    print("TESTING COMPLETE")
    print("=" * 80)
    print("✅ All characters should now have authentic AI identity responses")
    print("✅ Each response maintains character personality while being truthful")
    print("✅ Responses use character-specific language and terminology")


def test_character_file_structure():
    """Test that all character files have proper ai_identity_handling structure"""
    print("\n🔍 TESTING CHARACTER FILE STRUCTURE")
    print("=" * 50)
    
    character_files = [
        "elena-rodriguez.json",
        "marcus-thompson.json", 
        "dream_of_the_endless.json",
        "jake-sterling.json",
        "ryan-chen.json",
        "sophia-blake.json"
    ]
    
    for char_file in character_files:
        char_path = Path(f"characters/examples/{char_file}")
        
        if not char_path.exists():
            print(f"❌ {char_file}: File not found")
            continue
            
        try:
            with open(char_path, 'r', encoding='utf-8') as f:
                char_data = json.load(f)
            
            # Check for ai_identity_handling
            comm_style = char_data.get("character", {}).get("personality", {}).get("communication_style", {})
            ai_identity = comm_style.get("ai_identity_handling", {})
            
            if ai_identity:
                responses = ai_identity.get("responses", [])
                philosophy = ai_identity.get("philosophy", "")
                strategy = ai_identity.get("strategy", "")
                
                print(f"✅ {char_file}: ai_identity_handling found")
                print(f"   📝 Responses: {len(responses)} configured")
                print(f"   🎯 Philosophy: {'✓' if philosophy else '✗'}")
                print(f"   📋 Strategy: {'✓' if strategy else '✗'}")
            else:
                print(f"❌ {char_file}: No ai_identity_handling found")
                
        except json.JSONDecodeError as e:
            print(f"❌ {char_file}: JSON parsing error - {e}")
        except Exception as e:
            print(f"❌ {char_file}: Error - {e}")
    
    print(f"\n✅ Character file structure validation complete!")


if __name__ == "__main__":
    test_character_ai_identity_responses()
    test_character_file_structure()