#!/usr/bin/env python3
"""
Test script to verify character JSON path consistency across all calling code.
"""
import json
import os
from pathlib import Path

def test_character_file_paths():
    """Test that all character files have the expected structure."""
    characters_dir = Path("characters/examples")
    if not characters_dir.exists():
        print(f"❌ Characters directory not found: {characters_dir}")
        return
    
    print("🔍 TESTING CHARACTER PATH CONSISTENCY\n")
    
    for json_file in characters_dir.glob("*.json"):
        print(f"📄 {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Test required paths our code uses
            character_data = data.get('character', {})
            
            # 1. Metadata name (used by emoji system)
            metadata_name = character_data.get('metadata', {}).get('name')
            print(f"  ✅ metadata.name: {metadata_name}")
            
            # 2. Emoji personality (used by emoji system)
            emoji_config = character_data.get('identity', {}).get('digital_communication', {}).get('emoji_personality', {})
            if emoji_config:
                print(f"  ✅ emoji_personality: {emoji_config.get('frequency', 'missing')}")
            else:
                print(f"  ❌ emoji_personality: MISSING")
            
            # 3. Communication style (used by CDL integration)
            comm_style = character_data.get('personality', {}).get('communication_style', {})
            if comm_style:
                print(f"  ✅ personality.communication_style: {comm_style.get('tone', 'missing tone')}")
            else:
                print(f"  ❌ personality.communication_style: MISSING")
            
            # 4. Response length (used by CDL integration)
            response_length = character_data.get('communication', {}).get('response_length')
            if response_length:
                print(f"  ✅ communication.response_length: {response_length[:50]}...")
            else:
                print(f"  ❌ communication.response_length: MISSING")
            
            # 5. Check speech_patterns inconsistency
            root_speech = character_data.get('speech_patterns', {})
            voice_speech = character_data.get('identity', {}).get('voice', {}).get('speech_patterns', [])
            
            if root_speech and voice_speech:
                print(f"  ⚠️  DUAL speech_patterns: root={bool(root_speech)}, voice={len(voice_speech)} items")
            elif root_speech:
                print(f"  ✅ speech_patterns: root level (vocabulary format)")
            elif voice_speech:
                print(f"  ✅ speech_patterns: voice level ({len(voice_speech)} patterns)")
            else:
                print(f"  ❌ speech_patterns: MISSING both locations")
            
            print()
            
        except Exception as e:
            print(f"  ❌ ERROR reading {json_file.name}: {e}")
            print()

if __name__ == "__main__":
    test_character_file_paths()