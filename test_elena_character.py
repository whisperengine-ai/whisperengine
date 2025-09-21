#!/usr/bin/env python3
"""
Quick test script to verify Elena character JSON loading works correctly
"""

import json
import sys
from pathlib import Path

def test_elena_character():
    """Test Elena character JSON loading and validation"""
    
    # Load Elena character
    elena_path = Path("characters/examples/elena-rodriguez.json")
    
    if not elena_path.exists():
        print(f"❌ ERROR: Elena character file not found at {elena_path}")
        return False
    
    try:
        with open(elena_path, 'r', encoding='utf-8') as f:
            elena_data = json.load(f)
        
        print(f"✅ SUCCESS: Loaded Elena character JSON ({len(json.dumps(elena_data))} chars)")
        
        # Validate structure
        character_info = elena_data.get('character', {})
        identity = character_info.get('identity', {})
        
        print(f"Character Name: {identity.get('name', 'Unknown')}")
        print(f"Character Age: {identity.get('age', 'Unknown')}")
        print(f"Character Occupation: {identity.get('occupation', 'Unknown')}")
        print(f"Character Location: {identity.get('location', 'Unknown')}")
        
        # Create simple character prompt
        character_prompt = f"""You are {identity.get('name', 'Unknown')}, {identity.get('description', 'a character')}.

CHARACTER DETAILS:
- Age: {identity.get('age', 'Unknown')}
- Occupation: {identity.get('occupation', 'Unknown')}
- Location: {identity.get('location', 'Unknown')}

IMPORTANT: You must respond as {identity.get('name', 'this character')}, not as Dream or any other character. Stay completely in character.

Test Message: "Hi Elena! How are you doing today?"

Respond as {identity.get('name', 'this character')}:"""

        print(f"\n🎭 CHARACTER PROMPT PREVIEW:")
        print("=" * 80)
        print(character_prompt[:500] + "..." if len(character_prompt) > 500 else character_prompt)
        print("=" * 80)
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON ERROR: Failed to parse Elena character: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Failed to load Elena character: {e}")
        return False

def test_marcus_character():
    """Test Marcus character JSON loading"""
    
    marcus_path = Path("characters/examples/marcus-chen.json")
    
    if not marcus_path.exists():
        print(f"❌ ERROR: Marcus character file not found at {marcus_path}")
        return False
    
    try:
        with open(marcus_path, 'r', encoding='utf-8') as f:
            marcus_data = json.load(f)
        
        print(f"✅ SUCCESS: Loaded Marcus character JSON ({len(json.dumps(marcus_data))} chars)")
        
        character_info = marcus_data.get('character', {})
        identity = character_info.get('identity', {})
        
        print(f"Character Name: {identity.get('name', 'Unknown')}")
        print(f"Character Occupation: {identity.get('occupation', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to load Marcus character: {e}")
        return False

if __name__ == "__main__":
    print("🎭 CHARACTER JSON LOADING TEST")
    print("=" * 50)
    
    elena_ok = test_elena_character()
    print("\n" + "-" * 50)
    marcus_ok = test_marcus_character()
    
    print("\n" + "=" * 50)
    if elena_ok and marcus_ok:
        print("✅ ALL TESTS PASSED: Both characters loaded successfully!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED: Check character files!")
        sys.exit(1)