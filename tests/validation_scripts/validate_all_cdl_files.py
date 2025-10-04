#!/usr/bin/env python3
"""
🔍 CDL Comprehensive Validation Suite
Validates all character CDL files and checks pipeline consistency.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def validate_cdl_structure(character_data: Dict[str, Any], character_name: str) -> List[str]:
    """Validate CDL structure matches what the pipeline expects."""
    issues = []
    
    # Check required root sections
    required_sections = ["identity", "personality", "communication"]
    for section in required_sections:
        if section not in character_data:
            issues.append(f"❌ Missing required section: {section}")
    
    # Check values - can be in personality or at root level
    has_values = False
    if "values" in character_data:
        has_values = True
    elif "personality" in character_data and "values" in character_data["personality"]:
        has_values = True
    
    if not has_values:
        issues.append(f"⚠️  Missing values section (can be in personality or root level)")
    
    # Validate identity section
    if "identity" in character_data:
        identity = character_data["identity"]
        required_identity_fields = ["name", "occupation"]
        for field in required_identity_fields:
            if field not in identity:
                issues.append(f"❌ Missing identity.{field}")
        
        # Check for physical_appearance (used by pipeline) vs appearance (old format)
        if "appearance" in identity and "physical_appearance" not in identity:
            issues.append(f"⚠️  identity.appearance should be identity.physical_appearance")
        elif "physical_appearance" not in identity:
            issues.append(f"⚠️  Missing identity.physical_appearance")
    
    # Validate personality section
    if "personality" in character_data:
        personality = character_data["personality"]
        if "big_five" not in personality:
            issues.append(f"❌ Missing personality.big_five")
        else:
            big_five = personality["big_five"]
            required_traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
            for trait in required_traits:
                if trait not in big_five:
                    issues.append(f"❌ Missing personality.big_five.{trait}")
    
    # Validate communication section
    if "communication" in character_data:
        communication = character_data["communication"]
        recommended_fields = ["conversation_flow_guidance"]
        for field in recommended_fields:
            if field not in communication:
                issues.append(f"⚠️  Missing communication.{field}")
    
    return issues

def validate_pipeline_consistency(character_data: Dict[str, Any], character_name: str) -> List[str]:
    """Check that CDL structure matches how the pipeline actually uses it."""
    issues = []
    
    # Check what the pipeline looks for in cdl_ai_integration.py
    # Based on our analysis, the pipeline looks for:
    
    # 1. character.identity.name
    if not character_data.get("identity", {}).get("name"):
        issues.append("❌ Pipeline expects character.identity.name")
    
    # 2. character.identity.occupation  
    if not character_data.get("identity", {}).get("occupation"):
        issues.append("❌ Pipeline expects character.identity.occupation")
    
    # 3. character.identity.description
    if not character_data.get("identity", {}).get("description"):
        issues.append("⚠️  Pipeline expects character.identity.description")
    
    # 4. character.personality.big_five with traits
    personality = character_data.get("personality", {})
    big_five = personality.get("big_five", {})
    if not big_five:
        issues.append("❌ Pipeline expects character.personality.big_five")
    
    # 5. character.identity.physical_appearance (NOT appearance)
    identity = character_data.get("identity", {})
    if "appearance" in identity and "physical_appearance" not in identity:
        issues.append("🔧 Pipeline uses identity.physical_appearance, not identity.appearance")
    
    # 6. Response style extraction - CDL manager looks for conversation_flow_guidance.response_style
    communication = character_data.get("communication", {})
    
    # Check for conversation_flow_guidelines vs conversation_flow_guidance mismatch
    has_guidelines = "conversation_flow_guidelines" in communication
    has_guidance = "conversation_flow_guidance" in communication
    
    if has_guidelines and not has_guidance:
        issues.append("🔧 Pipeline expects communication.conversation_flow_guidance (you have conversation_flow_guidelines)")
    elif not has_guidelines and not has_guidance:
        issues.append("⚠️  Pipeline extracts communication.conversation_flow_guidance")
    
    # Check response_style specifically - should be nested in conversation_flow_guidance
    if has_guidance:
        flow_guidance = communication.get("conversation_flow_guidance", {})
        if not flow_guidance.get("response_style"):
            issues.append("⚠️  Pipeline extracts conversation_flow_guidance.response_style")
    elif has_guidelines:
        # If they have guidelines, check if response_style exists there
        flow_guidelines = communication.get("conversation_flow_guidelines", {})
        if not flow_guidelines.get("response_style"):
            issues.append("⚠️  Missing response_style in conversation flow section")
    
    return issues

def load_and_validate_character(file_path: str) -> Dict[str, Any]:
    """Load and validate a single character file."""
    character_name = Path(file_path).stem
    
    print(f"\n🔍 VALIDATING: {character_name.upper()}")
    print("=" * 50)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {file_path}: {e}")
        return {"character_name": character_name, "load_error": str(e)}
    
    # CDL files have nested structure - extract the character data
    if "character" in file_data:
        character_data = file_data["character"]
        print(f"📁 CDL Format: Extracted character data from nested structure")
    else:
        character_data = file_data
        print(f"📁 Direct Format: Using root-level character data")
    
    # Structure validation
    structure_issues = validate_cdl_structure(character_data, character_name)
    
    # Pipeline consistency validation
    pipeline_issues = validate_pipeline_consistency(character_data, character_name)
    
    # Report results
    all_issues = structure_issues + pipeline_issues
    
    if not all_issues:
        print("✅ PERFECT: No issues found!")
    else:
        print(f"📊 FOUND {len(all_issues)} ISSUES:")
        for issue in all_issues:
            print(f"   {issue}")
    
    # Character info summary
    identity = character_data.get("identity", {})
    print(f"\n📋 CHARACTER SUMMARY:")
    print(f"   Name: {identity.get('name', 'Unknown')}")
    print(f"   Occupation: {identity.get('occupation', 'Unknown')}")
    print(f"   Has Big Five: {'✅' if character_data.get('personality', {}).get('big_five') else '❌'}")
    print(f"   Has Response Style: {'✅' if character_data.get('communication', {}).get('response_style') else '❌'}")
    
    return {
        "character_name": character_name,
        "structure_issues": structure_issues,
        "pipeline_issues": pipeline_issues,
        "total_issues": len(all_issues),
        "data": character_data,
        "file_data": file_data  # Keep the original file structure
    }

def main():
    """Run comprehensive CDL validation on all character files."""
    
    print("🚀 CDL COMPREHENSIVE VALIDATION SUITE")
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
        result = load_and_validate_character(str(file_path))
        results.append(result)
    
    # Summary report
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY REPORT")
    print("=" * 60)
    
    total_characters = len(results)
    perfect_characters = len([r for r in results if r.get("total_issues", 0) == 0])
    total_issues = sum(r.get("total_issues", 0) for r in results)
    
    print(f"📈 STATISTICS:")
    print(f"   Total Characters: {total_characters}")
    print(f"   Perfect Characters: {perfect_characters}")
    print(f"   Characters with Issues: {total_characters - perfect_characters}")
    print(f"   Total Issues Found: {total_issues}")
    
    print(f"\n🎯 CHARACTER STATUS:")
    for result in results:
        if "load_error" in result:
            print(f"   ❌ {result['character_name']}: Load Error")
        elif result.get("total_issues", 0) == 0:
            print(f"   ✅ {result['character_name']}: Perfect")
        else:
            issues = result.get("total_issues", 0)
            print(f"   ⚠️  {result['character_name']}: {issues} issues")
    
    # Pipeline consistency check
    print(f"\n🔧 PIPELINE CONSISTENCY ANALYSIS:")
    pipeline_inconsistencies = []
    for result in results:
        if result.get("pipeline_issues"):
            pipeline_inconsistencies.extend(result["pipeline_issues"])
    
    if pipeline_inconsistencies:
        print(f"   Found {len(pipeline_inconsistencies)} pipeline inconsistencies")
        unique_issues = set(pipeline_inconsistencies)
        for issue in sorted(unique_issues):
            count = pipeline_inconsistencies.count(issue)
            print(f"   • {issue} (affects {count} characters)")
    else:
        print("   ✅ All characters are pipeline-consistent!")
    
    # Recommendations
    if total_issues > 0:
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   1. Fix pipeline inconsistencies first (affects functionality)")
        print(f"   2. Address missing required fields")
        print(f"   3. Update identity.appearance → identity.physical_appearance")
        print(f"   4. Ensure all characters have response_style for consistency")
    
    return results

if __name__ == "__main__":
    results = main()
    
    # Exit code based on critical issues
    critical_issues = sum(1 for r in results if r.get("pipeline_issues"))
    if critical_issues > 0:
        print(f"\n⚠️  {critical_issues} characters have pipeline inconsistencies!")
        sys.exit(1)
    else:
        print(f"\n🎉 All characters are pipeline-consistent!")
        sys.exit(0)