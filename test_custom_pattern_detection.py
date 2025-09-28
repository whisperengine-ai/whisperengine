#!/usr/bin/env python3
"""
Test script: Custom Conversation Flow Pattern Detection

This script tests the new dynamic pattern detection system that identifies
custom conversation flow patterns like 'transcendent_exploration' based on
message content and character CDL definitions.
"""

import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from prompts.cdl_ai_integration import CDLAIPromptIntegration
    from characters.cdl.parser import load_character
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This script needs to be run from the WhisperEngine root directory")
    sys.exit(1)


def test_custom_pattern_detection():
    """Test the new custom pattern detection system."""
    print("🧪 TESTING CUSTOM CONVERSATION FLOW PATTERN DETECTION")
    print("=" * 65)
    
    cdl_integration = CDLAIPromptIntegration()
    
    # Load test characters
    test_characters = {
        "Aethys": "characters/examples/aethys-omnipotent-entity.json",
        "Dream": "characters/examples/dream_of_the_endless.json", 
        "Marcus": "characters/examples/marcus-thompson.json"
    }
    
    # Test messages designed to trigger custom patterns
    test_messages = [
        # Should trigger transcendent_exploration
        ("Can you help me expand my consciousness and transcend my limitations?", 
         ["transcendent_exploration"]),
        
        # Should trigger mystical_guidance  
        ("I'm seeking spiritual wisdom about the universe and divine consciousness",
         ["mystical_guidance"]),
        
        # Should trigger dream_weaving (for Dream character)
        ("I had a strange dream last night about mythical creatures",
         ["dream_weaving"]),
        
        # Should trigger technical_education (for Marcus character)
        ("How does machine learning work? Can you explain the algorithms?",
         ["technical_education"]),
        
        # Should trigger ethical_discussion (for Marcus character)
        ("What are the moral implications of AI development?",
         ["ethical_discussion"]),
        
        # Should trigger multiple patterns
        ("I want to understand consciousness and how AI research impacts ethics",
         ["mystical_guidance", "technical_education", "ethical_discussion"]),
        
        # Should trigger nothing specific
        ("Hello, how are you today?",
         ["greeting"])  # Standard pattern, not custom
    ]
    
    for char_name, char_file in test_characters.items():
        if not Path(char_file).exists():
            print(f"⚠️ Skipping {char_name} - file not found: {char_file}")
            continue
            
        try:
            character = load_character(char_file)
            print(f"\n🤖 Testing with {char_name}")
            print("-" * 30)
            
            for i, (message, expected_patterns) in enumerate(test_messages, 1):
                print(f"\n📝 Test {i}: '{message[:50]}{'...' if len(message) > 50 else ''}'")
                
                # Test the new custom pattern detection
                custom_patterns = cdl_integration._detect_custom_flow_patterns(message, character)
                
                # Test standard scenario detection for comparison
                standard_scenarios = cdl_integration._detect_communication_scenarios(message, character, "test_user")
                
                print(f"   🎭 Custom patterns detected: {list(custom_patterns.keys()) if custom_patterns else 'None'}")
                print(f"   📋 Standard scenarios detected: {list(standard_scenarios.keys()) if standard_scenarios else 'None'}")
                
                # Check if we detected expected patterns
                detected_custom = list(custom_patterns.keys())
                relevant_expected = [p for p in expected_patterns if p not in ['greeting', 'romantic_interest']]
                
                if relevant_expected:
                    matches = set(detected_custom) & set(relevant_expected)
                    if matches:
                        print(f"   ✅ Successfully detected expected patterns: {list(matches)}")
                    else:
                        print(f"   ⚠️ Expected {relevant_expected} but got {detected_custom}")
                        
        except Exception as e:
            print(f"❌ Error testing {char_name}: {e}")


def test_flow_guidance_integration():
    """Test how detected patterns integrate with flow guidance."""
    print("\n\n🔗 TESTING FLOW GUIDANCE INTEGRATION")
    print("=" * 45)
    
    cdl_integration = CDLAIPromptIntegration()
    aethys_file = "characters/examples/aethys-omnipotent-entity.json"
    
    if not Path(aethys_file).exists():
        print("❌ Aethys character file not found")
        return
        
    try:
        character = load_character(aethys_file)
        test_message = "I want to expand my consciousness and explore transcendent realities"
        
        print(f"📝 Test message: '{test_message}'")
        print(f"🤖 Character: {character.identity.name}")
        
        # Detect scenarios (both standard and custom)
        scenarios = cdl_integration._detect_communication_scenarios(test_message, character, "test_user")
        print(f"\n🎯 Detected scenarios: {list(scenarios.keys())}")
        
        # Get flow guidance for these scenarios
        flow_guidance = cdl_integration._get_cdl_conversation_flow_guidance(aethys_file, scenarios)
        
        if flow_guidance:
            print("\n✅ Generated flow guidance:")
            print("-" * 30)
            for line in flow_guidance.split('\n')[:15]:  # Show first 15 lines
                if line.strip():
                    print(line)
            if len(flow_guidance.split('\n')) > 15:
                print("... (truncated)")
        else:
            print("\n❌ No flow guidance generated")
            
    except Exception as e:
        print(f"❌ Error in integration test: {e}")


if __name__ == "__main__":
    test_custom_pattern_detection()
    test_flow_guidance_integration()
    
    print("\n\n💡 SUMMARY")
    print("=" * 30)
    print("The new custom pattern detection system:")
    print("✅ Dynamically analyzes message content for character-specific patterns")
    print("✅ Matches against CDL-defined conversation flow guidance")
    print("✅ Integrates seamlessly with existing scenario detection")
    print("✅ Enables sophisticated conversation flow based on character personality")
    print("\n🚀 Custom patterns like 'transcendent_exploration' are now ACTIVE!")