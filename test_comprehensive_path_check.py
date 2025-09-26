#!/usr/bin/env python3
"""
Comprehensive cross-check of ALL character JSON paths used by WhisperEngine code.
"""
import json
import os
from pathlib import Path

def get_all_code_paths():
    """Define all paths that our code actually uses."""
    return {
        # CDL Emoji Personality paths
        "character.metadata.name": "Character name (emoji system)",
        "character.identity.digital_communication": "Digital comm section (emoji system)",
        "character.identity.digital_communication.emoji_personality": "Emoji personality config",
        "character.identity.digital_communication.emoji_personality.frequency": "Emoji frequency",
        "character.identity.digital_communication.emoji_personality.style": "Emoji style",
        "character.identity.digital_communication.emoji_personality.age_demographic": "Age demo",
        "character.identity.digital_communication.emoji_personality.cultural_influence": "Cultural influence", 
        "character.identity.digital_communication.emoji_personality.preferred_combination": "Preferred combo",
        "character.identity.digital_communication.emoji_personality.emoji_placement": "Emoji placement",
        "character.identity.digital_communication.emoji_usage_patterns": "Emoji usage patterns",
        
        # CDL AI Integration paths
        "character.personality": "Personality section",
        "character.personality.big_five": "Big Five personality scores",
        "character.personality.communication_style": "Communication style",
        "character.personality.communication_style.tone": "Communication tone",
        "character.personality.communication_style.formality": "Communication formality",
        "character.personality.communication_style.humor": "Communication humor",
        "character.personality.communication_style.empathy_level": "Empathy level",
        "character.personality.communication_style.directness": "Communication directness",
        "character.personality.communication_style.custom_speaking_instructions": "Custom speaking",
        "character.personality.communication_style.category": "Speaking category",
        
        # Background and backstory
        "character.background": "Background section",
        "character.background.life_phases": "Life phases (optional)",
        
        # Speech patterns (dual location)
        "character.speech_patterns": "Speech patterns (root level)",
        "character.speech_patterns.vocabulary": "Speech vocabulary",
        "character.speech_patterns.vocabulary.preferred_words": "Preferred words",
        "character.speech_patterns.vocabulary.avoided_words": "Avoided words",
        "character.speech_patterns.sentence_structure": "Sentence structure",
        "character.identity.voice.speech_patterns": "Speech patterns (voice level)",
        
        # Communication responses
        "character.communication": "Communication section",
        "character.communication.response_length": "Response length controls",
        "character.communication.typical_responses": "Typical responses",
        "character.communication.emotional_expressions": "Emotional expressions",
        
        # CDL Parser paths
        "character.metadata": "Metadata section",
        "character.identity": "Identity section", 
        "character.backstory": "Backstory section (CDL parser)",
        "character.current_life": "Current life section",
        
        # Legacy multi-entity manager paths (potentially problematic)
        "character_id": "Character ID (legacy - WRONG PATH!)",
        "name": "Name (legacy - WRONG PATH!)", 
        "occupation": "Occupation (legacy - WRONG PATH!)",
        "age": "Age (legacy - WRONG PATH!)",
        "personality_traits": "Personality traits (legacy - WRONG PATH!)",
        "communication_style": "Comm style (legacy - WRONG PATH!)",
        "background_summary": "Background (legacy - WRONG PATH!)",
        "preferred_topics": "Topics (legacy - WRONG PATH!)",
        "conversation_style": "Conv style (legacy - WRONG PATH!)",
    }

def evaluate_path(data, path):
    """Evaluate a nested path in JSON data."""
    try:
        parts = path.split('.')
        current = data
        for part in parts:
            current = current.get(part, {})
            if current == {}:
                return None
        return current if current != {} else None
    except:
        return None

def test_all_character_paths():
    """Test ALL paths used by code against ALL character files."""
    characters_dir = Path("characters/examples")
    if not characters_dir.exists():
        print(f"❌ Characters directory not found: {characters_dir}")
        return
    
    all_paths = get_all_code_paths()
    print("🔍 COMPREHENSIVE CHARACTER PATH CROSS-CHECK\n")
    print(f"Testing {len(all_paths)} code paths against all character files...\n")
    
    character_files = list(characters_dir.glob("*.json"))
    issues_found = {}
    
    for json_file in character_files:
        print(f"📄 {json_file.name}")
        print("=" * 50)
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_issues = []
            
            for path, description in all_paths.items():
                result = evaluate_path(data, path)
                
                if path.startswith("character."):
                    # These should exist in CDL format
                    if result is None:
                        status = "❌ MISSING"
                        file_issues.append(f"MISSING: {path}")
                    elif isinstance(result, dict) and not result:
                        status = "❌ EMPTY"
                        file_issues.append(f"EMPTY: {path}")
                    elif isinstance(result, list) and not result:
                        status = "❌ EMPTY LIST"
                        file_issues.append(f"EMPTY: {path}")
                    else:
                        status = "✅ OK"
                        if isinstance(result, dict):
                            status += f" (dict: {len(result)} keys)"
                        elif isinstance(result, list):
                            status += f" (list: {len(result)} items)"
                        elif isinstance(result, str):
                            status += f" (str: {len(result)} chars)"
                        else:
                            status += f" ({type(result).__name__})"
                else:
                    # These are legacy paths that SHOULD be missing in CDL format
                    if result is not None:
                        status = "⚠️  LEGACY PATH EXISTS"
                        file_issues.append(f"LEGACY: {path} exists but shouldn't")
                    else:
                        status = "✅ OK (missing as expected)"
                
                print(f"  {path}: {status}")
            
            if file_issues:
                issues_found[json_file.name] = file_issues
                print(f"\n⚠️  {len(file_issues)} issues found in {json_file.name}")
            else:
                print(f"\n✅ {json_file.name} is fully compliant!")
                
            print()
            
        except Exception as e:
            print(f"  ❌ ERROR reading {json_file.name}: {e}")
            print()
    
    # Summary report
    print("\n" + "="*80)
    print("📊 SUMMARY REPORT")
    print("="*80)
    
    if issues_found:
        print(f"⚠️  Issues found in {len(issues_found)} files:")
        for filename, issues in issues_found.items():
            print(f"\n📄 {filename}:")
            for issue in issues:
                print(f"  • {issue}")
    else:
        print("🎉 ALL CHARACTER FILES ARE FULLY COMPLIANT!")
    
    print(f"\nTested {len(character_files)} character files against {len(all_paths)} code paths.")

if __name__ == "__main__":
    test_all_character_paths()