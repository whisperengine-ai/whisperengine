#!/usr/bin/env python3
"""
Test script for CDL character import functionality
Tests the integration between CDL parser and multi-entity system
"""

import asyncio
import sys
import os
import yaml
from datetime import datetime

# Add the project root to Python path
sys.path.append('/Users/markcastillo/git/whisperengine')

from src.characters.cdl.parser import CDLParser, CDLParseError

async def test_cdl_import():
    """Test the CDL import process"""
    print("🧪 Testing CDL Character Import Integration")
    print("=" * 50)
    
    # Test 1: Parse the CDL file
    print("\n📋 Test 1: CDL File Parsing")
    try:
        parser = CDLParser()
        character = parser.parse_file('test_character_sage.yaml')
        print(f"✅ CDL parse successful!")
        print(f"   Character: {character.identity.name}")
        print(f"   Age: {character.identity.age}")
        print(f"   Occupation: {character.identity.occupation}")
    except Exception as e:
        print(f"❌ CDL parse failed: {e}")
        return
    
    # Test 2: Convert to multi-entity format
    print("\n🔄 Test 2: Convert to Multi-Entity Format")
    try:
        # Simulate the conversion logic from our handler
        character_data = {
            "name": character.identity.name,
            "description": f"CDL imported character: {character.identity.occupation}",
            "personality_type": "companion",
            "traits": character.personality.values + character.personality.quirks,
            "background": f"Occupation: {character.identity.occupation}, Location: {character.identity.location}",
            "created_by": "test_user_123",
            "import_source": "CDL test",
            "metadata": {
                "cdl_version": character.metadata.version if character.metadata else "1.0",
                "original_name": character.identity.name,
                "imported_at": datetime.now().isoformat(),
                "character_id": character.metadata.character_id
            }
        }
        
        # Add Big Five personality data
        if character.personality and hasattr(character.personality, 'big_five'):
            big_five = character.personality.big_five
            if big_five:
                character_data["metadata"]["big_five"] = {
                    "openness": big_five.openness,
                    "conscientiousness": big_five.conscientiousness,
                    "extraversion": big_five.extraversion,
                    "agreeableness": big_five.agreeableness,
                    "neuroticism": big_five.neuroticism
                }
        
        print("✅ Conversion successful!")
        print(f"   Name: {character_data['name']}")
        print(f"   Type: {character_data['personality_type']}")
        print(f"   Traits: {len(character_data['traits'])} traits")
        print(f"   Big Five: {bool(character_data['metadata'].get('big_five'))}")
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return
    
    # Test 3: Validate required fields
    print("\n✅ Test 3: Field Validation")
    required_fields = ["name", "description", "personality_type", "created_by"]
    missing_fields = [field for field in required_fields if not character_data.get(field)]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
    else:
        print("✅ All required fields present!")
        
    print(f"\n📊 Character Data Summary:")
    print(f"   - Name: {character_data['name']}")
    print(f"   - Traits: {character_data['traits'][:3]}..." if len(character_data['traits']) > 3 else f"   - Traits: {character_data['traits']}")
    print(f"   - Background: {character_data['background'][:50]}...")
    print(f"   - Metadata: {len(character_data['metadata'])} items")
    
    # Test 4: YAML round-trip test
    print("\n🔄 Test 4: YAML Round-trip")
    try:
        # Test parsing raw YAML content (as Discord command would)
        with open('test_character_sage.yaml', 'r') as f:
            yaml_content = f.read()
        
        yaml_dict = yaml.safe_load(yaml_content)
        character2 = parser.parse_dict(yaml_dict)
        
        if character2.identity.name == character.identity.name:
            print("✅ YAML round-trip successful!")
        else:
            print("❌ YAML round-trip failed - names don't match")
            
    except Exception as e:
        print(f"❌ YAML round-trip failed: {e}")
    
    print("\n🎉 CDL Import Integration Test Complete!")
    return character_data

if __name__ == "__main__":
    asyncio.run(test_cdl_import())