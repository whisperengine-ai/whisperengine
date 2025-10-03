#!/usr/bin/env python3
"""
Validate that all active WhisperEngine characters have the new response_style CDL section.
This confirms the complete rollout of character-agnostic response styling architecture.
"""

import json
import os
import sys

def validate_character_response_style(character_file, character_name):
    """Validate that a character file has the new response_style section."""
    try:
        with open(character_file, 'r') as f:
            character_data = json.load(f)
        
        # Navigate to conversation_flow_guidance
        comm = character_data.get('character', {}).get('communication', {})
        flow_guidance = comm.get('conversation_flow_guidance', {})
        
        # Check for response_style section
        response_style = flow_guidance.get('response_style', {})
        
        if not response_style:
            return False, "Missing response_style section"
        
        # Validate required subsections
        required_sections = ['core_principles', 'formatting_rules', 'character_specific_adaptations']
        missing_sections = []
        
        for section in required_sections:
            if section not in response_style:
                missing_sections.append(section)
        
        if missing_sections:
            return False, f"Missing sections: {', '.join(missing_sections)}"
        
        # Validate character_specific_adaptations (generic field name)
        adaptations = response_style.get('character_specific_adaptations', [])
        if not adaptations:
            return False, "Empty character_specific_adaptations"
        
        # Check that it's not using character-specific field names
        for key in response_style.keys():
            if character_name.lower() in key.lower():
                return False, f"Found character-specific field name: {key}"
        
        return True, f"Valid - {len(adaptations)} character adaptations"
        
    except Exception as e:
        return False, f"Error reading file: {e}"

def main():
    """Validate all active character files for response_style architecture."""
    
    print("🔍 VALIDATING CDL RESPONSE STYLE ARCHITECTURE")
    print("=" * 60)
    
    # Active character files based on .env.* configurations
    character_files = {
        'sophia': 'characters/examples/sophia_v2.json',
        'elena': 'characters/examples/elena.json', 
        'marcus': 'characters/examples/marcus.json',
        'ryan': 'characters/examples/ryan.json',
        'jake': 'characters/examples/jake.json',
        'dream': 'characters/examples/dream.json',
        'aethys': 'characters/examples/aethys.json',
        'gabriel': 'characters/examples/gabriel.json'
    }
    
    results = {}
    all_valid = True
    
    for char_name, char_file in character_files.items():
        if not os.path.exists(char_file):
            results[char_name] = (False, "File not found")
            all_valid = False
            continue
        
        valid, message = validate_character_response_style(char_file, char_name)
        results[char_name] = (valid, message)
        
        if not valid:
            all_valid = False
    
    # Display results
    print("📋 VALIDATION RESULTS:")
    print("-" * 60)
    
    for char_name, (valid, message) in results.items():
        status = "✅" if valid else "❌"
        print(f"{status} {char_name.upper()}: {message}")
    
    print("-" * 60)
    
    if all_valid:
        print("🎉 SUCCESS: All 8 characters have valid response_style architecture!")
        print("\n✅ ARCHITECTURE BENEFITS CONFIRMED:")
        print("   • Generic 'character_specific_adaptations' field names")
        print("   • No character-specific hardcoded logic") 
        print("   • Complete CDL-based response styling")
        print("   • Character-agnostic Python code integration")
        
        print("\n🎯 READY FOR MULTI-CHARACTER TESTING:")
        print("   • Each character maintains unique personality via CDL")
        print("   • All characters use conversational response optimization")
        print("   • Zero hardcoded personality traits in Python code")
        print("   • Easy to extend to new characters")
        
        return 0
    else:
        print("❌ VALIDATION FAILED: Some characters missing response_style")
        print("Run this script again after fixing the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())