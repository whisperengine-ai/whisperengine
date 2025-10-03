#!/usr/bin/env python3
"""
🎭 CDL Emoji Configuration Validator
Validates all character emoji configurations against the actual enums in the codebase.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def validate_emoji_config(character_data: Dict[str, Any], character_name: str) -> List[str]:
    """Validate emoji configuration against the actual enum values."""
    issues = []
    
    # Valid enum values from src/intelligence/cdl_emoji_personality.py
    valid_frequencies = {
        "none", "minimal", "low", "moderate", "high", "selective_symbolic"
    }
    
    valid_combinations = {
        "emoji_only", "text_only", "text_plus_emoji", 
        "text_with_accent_emoji", "minimal_symbolic_emoji"
    }
    
    # Check if character has emoji personality configuration  
    # CDL structure: character.identity.digital_communication.emoji_personality
    identity = character_data.get("identity", {})
    digital_comm = identity.get("digital_communication", {})
    emoji_personality = digital_comm.get("emoji_personality", {})
    
    if not emoji_personality:
        issues.append("⚠️  Missing digital_communication.emoji_personality section")
        return issues
    
    # Validate frequency
    frequency = emoji_personality.get("frequency")
    if frequency and frequency not in valid_frequencies:
        issues.append(f"❌ Invalid emoji frequency: '{frequency}' (valid: {', '.join(sorted(valid_frequencies))})")
    elif not frequency:
        issues.append("⚠️  Missing emoji_personality.frequency")
    
    # Validate preferred_combination
    combination = emoji_personality.get("preferred_combination")
    if combination and combination not in valid_combinations:
        issues.append(f"❌ Invalid emoji combination: '{combination}' (valid: {', '.join(sorted(valid_combinations))})")
    elif not combination:
        issues.append("⚠️  Missing emoji_personality.preferred_combination")
    
    # Check for common configuration fields
    recommended_fields = ["style", "age_demographic", "cultural_influence", "emoji_placement"]
    for field in recommended_fields:
        if field not in emoji_personality:
            issues.append(f"⚠️  Missing emoji_personality.{field}")
    
    return issues

def validate_character_emoji_config(file_path: str) -> Dict[str, Any]:
    """Validate emoji configuration for a single character file."""
    character_name = Path(file_path).stem
    
    print(f"\n🎭 VALIDATING EMOJI CONFIG: {character_name.upper()}")
    print("=" * 55)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {file_path}: {e}")
        return {"character_name": character_name, "load_error": str(e)}
    
    # Extract character data (CDL files have nested structure)
    if "character" in file_data:
        character_data = file_data["character"]
    else:
        character_data = file_data
    
    # Validate emoji configuration
    emoji_issues = validate_emoji_config(character_data, character_name)
    
    # Report results
    if not emoji_issues:
        print("✅ PERFECT: Emoji configuration is valid!")
    else:
        print(f"📊 FOUND {len(emoji_issues)} EMOJI ISSUES:")
        for issue in emoji_issues:
            print(f"   {issue}")
    
    # Show current emoji configuration
    identity = character_data.get("identity", {})
    digital_comm = identity.get("digital_communication", {})
    emoji_personality = digital_comm.get("emoji_personality", {})
    
    if emoji_personality:
        print(f"\n📋 CURRENT EMOJI CONFIG:")
        print(f"   Frequency: {emoji_personality.get('frequency', 'Not set')}")
        print(f"   Combination: {emoji_personality.get('preferred_combination', 'Not set')}")
        print(f"   Style: {emoji_personality.get('style', 'Not set')}")
    else:
        print(f"\n📋 NO EMOJI CONFIGURATION FOUND")
    
    return {
        "character_name": character_name,
        "emoji_issues": emoji_issues,
        "total_issues": len(emoji_issues),
        "has_emoji_config": bool(emoji_personality)
    }

def main():
    """Run emoji configuration validation on all character files."""
    
    print("🎭 CDL EMOJI CONFIGURATION VALIDATOR")
    print("=" * 60)
    
    # Find all character files
    characters_dir = Path("characters/examples")
    if not characters_dir.exists():
        print("❌ Characters directory not found!")
        return
    
    character_files = list(characters_dir.glob("*.json"))
    if not character_files:
        print("❌ No character files found!")
        return
    
    print(f"📁 FOUND {len(character_files)} CHARACTER FILES")
    
    # Validate each character
    results = []
    for file_path in sorted(character_files):
        result = validate_character_emoji_config(str(file_path))
        results.append(result)
    
    # Summary report
    print("\n" + "=" * 60)
    print("📊 EMOJI CONFIGURATION SUMMARY REPORT")
    print("=" * 60)
    
    total_characters = len(results)
    perfect_characters = len([r for r in results if r.get("total_issues", 0) == 0 and not r.get("load_error")])
    characters_with_issues = total_characters - perfect_characters
    total_issues = sum(r.get("total_issues", 0) for r in results)
    characters_with_config = len([r for r in results if r.get("has_emoji_config", False)])
    
    print(f"📈 STATISTICS:")
    print(f"   Total Characters: {total_characters}")
    print(f"   Characters with Emoji Config: {characters_with_config}")
    print(f"   Perfect Emoji Config: {perfect_characters}")
    print(f"   Characters with Issues: {characters_with_issues}")
    print(f"   Total Issues Found: {total_issues}")
    
    print(f"\n🎯 CHARACTER STATUS:")
    for result in results:
        if "load_error" in result:
            print(f"   ❌ {result['character_name']}: Load Error")
        elif result.get("total_issues", 0) == 0:
            if result.get("has_emoji_config"):
                print(f"   ✅ {result['character_name']}: Perfect Config")
            else:
                print(f"   ⚠️  {result['character_name']}: No Emoji Config")
        else:
            issues = result.get("total_issues", 0)
            print(f"   ❌ {result['character_name']}: {issues} issues")
    
    # Show valid enum values for reference
    print(f"\n📚 VALID ENUM VALUES:")
    print(f"   Frequencies: none, minimal, low, moderate, high, selective_symbolic")
    print(f"   Combinations: emoji_only, text_only, text_plus_emoji, text_with_accent_emoji, minimal_symbolic_emoji")
    
    if characters_with_issues > 0:
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   1. Fix invalid enum values (critical - causes runtime errors)")
        print(f"   2. Add missing emoji configuration for complete characters")
        print(f"   3. Ensure all characters have consistent emoji personality setup")
    
    return results

if __name__ == "__main__":
    results = main()
    
    # Exit code based on critical issues
    critical_issues = sum(1 for r in results if r.get("total_issues", 0) > 0 and "load_error" not in r)
    if critical_issues > 0:
        print(f"\n⚠️  {critical_issues} characters have emoji configuration issues!")
        sys.exit(1)
    else:
        print(f"\n🎉 All characters have valid emoji configurations!")
        sys.exit(0)