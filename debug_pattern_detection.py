#!/usr/bin/env python3
"""
Debug custom pattern detection to see what's happening inside the method
"""

import json
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from prompts.cdl_ai_integration import CDLAIPromptIntegration
from characters.cdl.parser import load_character


def debug_pattern_detection():
    """Debug the pattern detection step by step."""
    cdl = CDLAIPromptIntegration()
    marcus = load_character('characters/examples/marcus-thompson.json')
    
    print("🔍 DEBUGGING CUSTOM PATTERN DETECTION")
    print("=" * 50)
    
    message_content = "Can you explain how machine learning algorithms work?"
    message_lower = message_content.lower()
    
    print(f"Message: {message_content}")
    print(f"Character: {marcus.identity.name}")
    
    # Manually replicate the method's logic step by step
    character_file_path = cdl._find_character_file(marcus.identity.name)
    print(f"Character file path: {character_file_path}")
    
    if not character_file_path:
        print("❌ No character file found!")
        return
        
    with open(character_file_path, 'r', encoding='utf-8') as f:
        character_data = json.load(f)
    
    # Get conversation flow guidance patterns from multiple possible locations
    flow_guidance = {}
    
    # Location 1: character.personality.communication_style.conversation_flow_guidance
    guidance_1 = (character_data.get('character', {})
                 .get('personality', {})
                 .get('communication_style', {})
                 .get('conversation_flow_guidance', {}))
    
    # Location 2: character.communication.conversation_flow_guidance
    guidance_2 = (character_data.get('character', {})
                 .get('communication', {})
                 .get('conversation_flow_guidance', {}))
    
    flow_guidance.update(guidance_2)
    flow_guidance.update(guidance_1)
    
    print(f"Flow guidance found: {list(flow_guidance.keys())}")
    
    if not flow_guidance:
        print("❌ No flow guidance found!")
        return
    
    # Get message pattern triggers from CDL (generic approach)
    message_triggers = {}
    
    # Location 1: character.personality.communication_style.message_pattern_triggers
    triggers_1 = (character_data.get('character', {})
                 .get('personality', {})
                 .get('communication_style', {})
                 .get('message_pattern_triggers', {}))
    
    # Location 2: character.communication.message_pattern_triggers  
    triggers_2 = (character_data.get('character', {})
                 .get('communication', {})
                 .get('message_pattern_triggers', {}))
    
    message_triggers.update(triggers_2)
    message_triggers.update(triggers_1)
    
    print(f"Message triggers found: {list(message_triggers.keys())}")
    
    custom_scenarios = {}
    
    # Check each trigger pattern defined in the character's CDL
    for trigger_name, trigger_config in message_triggers.items():
        print(f"\n🔍 Checking trigger: {trigger_name}")
        
        if trigger_name in flow_guidance:  # Only process if flow guidance exists for this trigger
            print(f"   ✅ Flow guidance exists for {trigger_name}")
            
            keywords = trigger_config.get('keywords', [])
            phrases = trigger_config.get('phrases', [])
            
            print(f"   Keywords: {keywords}")
            print(f"   Phrases: {phrases}")
            
            # Check for keyword matches
            for keyword in keywords:
                print(f"   Checking keyword '{keyword}' in '{message_lower}'")
                if keyword.lower() in message_lower:
                    custom_scenarios[trigger_name] = [f"Triggered by keyword: {keyword}"]
                    print(f"   ✅ MATCH! Detected pattern '{trigger_name}' via keyword '{keyword}'")
                    break
            
            # Check for phrase matches (if keyword didn't match)
            if trigger_name not in custom_scenarios:
                for phrase in phrases:
                    print(f"   Checking phrase '{phrase}' in '{message_lower}'")
                    if phrase.lower() in message_lower:
                        custom_scenarios[trigger_name] = [f"Triggered by phrase: {phrase}"]
                        print(f"   ✅ MATCH! Detected pattern '{trigger_name}' via phrase '{phrase}'")
                        break
        else:
            print(f"   ❌ No flow guidance for {trigger_name}")
    
    print(f"\n🎯 Final detected patterns: {list(custom_scenarios.keys())}")


if __name__ == "__main__":
    debug_pattern_detection()