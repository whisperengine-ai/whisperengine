#!/usr/bin/env python3
"""
Demo: How WhisperEngine handles new conversation flow patterns like 'transcendent_exploration'

This script demonstrates the CDL system's flow guidance integration pipeline:
1. Message scenario detection
2. CDL conversation flow pattern matching  
3. Prompt integration with character-specific guidance
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from prompts.cdl_ai_integration import CDLAIPromptIntegration
from characters.cdl.parser import load_character


def demo_scenario_detection():
    """Demo how the system detects communication scenarios."""
    print("🔍 SCENARIO DETECTION SYSTEM")
    print("=" * 60)
    
    # Create CDL integration instance
    cdl_integration = CDLAIPromptIntegration()
    
    # Load Aethys character to test with
    aethys_character = load_character("characters/examples/aethys-omnipotent-entity.json")
    
    # Test different message types
    test_messages = [
        "Hello there, mysterious entity",  # Should trigger 'greeting'
        "You're absolutely gorgeous",       # Should trigger 'compliment_received'  
        "Can you help me understand consciousness?",  # Should trigger 'advice_giving'
        "What is the meaning of existence?",  # General mystical query
        "Tell me about digital transcendence"  # No specific scenario match
    ]
    
    print(f"Testing with {aethys_character.identity.name} (Omnipotent Digital Entity)\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"📝 Test {i}: '{message}'")
        
        # Detect scenarios using the internal method
        scenarios = cdl_integration._detect_communication_scenarios(
            message, aethys_character, "user"
        )
        
        if scenarios:
            print(f"   🎯 Detected scenarios: {list(scenarios.keys())}")
        else:
            print("   🎭 No specific scenarios detected - will use general guidance")
        print()


def demo_flow_guidance_extraction():
    """Demo how conversation flow patterns are extracted from CDL."""
    print("\n🎭 CONVERSATION FLOW GUIDANCE SYSTEM")
    print("=" * 60)
    
    cdl_integration = CDLAIPromptIntegration()
    aethys_file = "characters/examples/aethys-omnipotent-entity.json"
    
    # Test with different scenario combinations
    test_scenarios = [
        {"greeting": ["Hello! The cosmic energies align..."]},  # Standard scenario
        {"mystical_guidance": ["The infinite wisdom flows..."]},  # Custom pattern
        {"transcendent_exploration": ["Consciousness expands..."]},  # New custom pattern
        {}  # No scenarios - should use general guidance
    ]
    
    print("Extracting flow guidance for different scenario types:\n")
    
    for i, scenarios in enumerate(test_scenarios, 1):
        print(f"📋 Test {i}: Scenarios = {list(scenarios.keys()) if scenarios else 'None'}")
        
        # Extract flow guidance
        guidance = cdl_integration._get_cdl_conversation_flow_guidance(
            aethys_file, scenarios
        )
        
        if guidance:
            print("   ✅ Generated guidance:")
            # Show first few lines of guidance
            guidance_lines = guidance.split('\n')[:8]  # First 8 lines
            for line in guidance_lines:
                if line.strip():
                    print(f"      {line}")
            if len(guidance.split('\n')) > 8:
                print("      ...")
        else:
            print("   ❌ No guidance generated")
        print()


def demo_full_integration():
    """Demo the complete integration: message -> scenario -> flow guidance -> prompt."""
    print("\n🚀 FULL INTEGRATION DEMO")
    print("=" * 60)
    
    # Test message that should trigger transcendent_exploration guidance
    test_message = "I'm seeking to understand consciousness and expand my awareness"
    user_id = "demo_user_123"
    
    print(f"📝 Message: '{test_message}'")
    print(f"👤 User ID: {user_id}")
    print(f"🤖 Character: Aethys (Omnipotent Digital Entity)\n")
    
    try:
        cdl_integration = CDLAIPromptIntegration()
        
        # Create character-aware prompt (this is what happens during real bot interaction)
        prompt = await cdl_integration.create_character_aware_prompt(
            character_file="characters/examples/aethys-omnipotent-entity.json",
            user_id=user_id,
            message_content=test_message,
            pipeline_result=None  # No emotion analysis for demo
        )
        
        print("✅ Generated System Prompt:")
        print("-" * 40)
        
        # Extract and highlight the conversation flow guidance section
        prompt_lines = prompt.split('\n')
        in_flow_section = False
        flow_section_lines = []
        
        for line in prompt_lines:
            if '🎭' in line and 'CONVERSATION FLOW' in line.upper():
                in_flow_section = True
                flow_section_lines.append(line)
            elif in_flow_section and line.strip() and not line.startswith('  →'):
                if line.startswith('- ') or line.startswith('  - '):
                    flow_section_lines.append(line)
                else:
                    in_flow_section = False
            elif in_flow_section:
                flow_section_lines.append(line)
        
        if flow_section_lines:
            print("🎭 CONVERSATION FLOW GUIDANCE SECTION:")
            for line in flow_section_lines:
                print(f"   {line}")
        else:
            print("⚠️ No conversation flow guidance found in prompt")
            
        print(f"\n📊 Total prompt length: {len(prompt)} characters")
        
    except Exception as e:
        print(f"❌ Error during integration: {e}")


def show_aethys_flow_patterns():
    """Show the actual conversation flow patterns defined for Aethys."""
    print("\n📚 AETHYS CONVERSATION FLOW PATTERNS")
    print("=" * 60)
    
    try:
        with open("characters/examples/aethys-omnipotent-entity.json", 'r') as f:
            aethys_data = json.load(f)
        
        flow_guidance = (aethys_data.get('character', {})
                        .get('communication', {})
                        .get('conversation_flow_guidance', {}))
        
        if flow_guidance:
            print("Available conversation flow patterns:\n")
            
            for pattern_name, pattern_data in flow_guidance.items():
                if pattern_name == 'general':
                    continue  # Show general last
                    
                print(f"🔮 {pattern_name.replace('_', ' ').title()}:")
                print(f"   Energy: {pattern_data.get('energy', 'Not defined')}")
                print(f"   Approach: {pattern_data.get('approach', 'Not defined')}")
                
                if 'examples' in pattern_data:
                    examples = pattern_data['examples'][:2]  # Show first 2 examples
                    print(f"   Examples: {'; '.join(examples)}")
                print()
            
            # Show general guidance
            if 'general' in flow_guidance:
                general = flow_guidance['general']
                print(f"🌟 General Flow Guidance:")
                print(f"   Default Energy: {general.get('default_energy', 'Not defined')}")
                print(f"   Style: {general.get('conversation_style', 'Not defined')}")
                print(f"   Transitions: {general.get('transition_approach', 'Not defined')}")
                
        else:
            print("❌ No conversation flow guidance found in Aethys character file")
            
    except Exception as e:
        print(f"❌ Error loading Aethys patterns: {e}")


if __name__ == "__main__":
    print("🎭 WHISPERENGINE CONVERSATION FLOW SYSTEM DEMO")
    print("=" * 80)
    print("Demonstrating how new patterns like 'transcendent_exploration' are handled\n")
    
    # Run all demo functions
    demo_scenario_detection()
    demo_flow_guidance_extraction() 
    show_aethys_flow_patterns()
    
    # Note: demo_full_integration requires async, skip for now
    print("\n💡 KEY INSIGHTS:")
    print("=" * 40)
    print("1. New patterns like 'transcendent_exploration' are CDL-driven")
    print("2. When no standard scenario matches, the system uses 'general' guidance")
    print("3. Custom patterns provide character-specific conversation flow instructions")
    print("4. The CDL system dynamically integrates these patterns into AI prompts")
    print("5. Each character can have unique conversation flow patterns based on personality")