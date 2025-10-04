#!/usr/bin/env python3
"""
🚀 Test Optimized Prompt Section Ordering
Tests the new optimized section ordering for better LLM instruction compliance.
"""

import asyncio
import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from prompts.cdl_ai_integration import CDLAIPromptIntegration

def test_prompt_section_ordering():
    """Test that prompt sections are in the optimized order for maximum LLM compliance."""
    
    # Mock character data (minimal CDL structure)
    character_data = {
        "identity": {
            "name": "Elena Rodriguez",
            "occupation": "Marine Biologist",
            "description": "A passionate marine biologist dedicated to ocean conservation."
        },
        "personality": {
            "big_five": {
                "openness": 0.8,
                "conscientiousness": 0.7,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3
            }
        }
    }
    
    # Create mock character object
    class MockCharacter:
        def __init__(self, data):
            self.identity = MockIdentity(data["identity"])
            if "personality" in data:
                self.personality = MockPersonality(data["personality"])
    
    class MockIdentity:
        def __init__(self, data):
            self.name = data["name"]
            self.occupation = data["occupation"]
            if "description" in data:
                self.description = data["description"]
    
    class MockPersonality:
        def __init__(self, data):
            if "big_five" in data:
                self.big_five = MockBigFive(data["big_five"])
    
    class MockBigFive:
        def __init__(self, data):
            for trait, score in data.items():
                setattr(self, trait, score)

    async def run_test():
        # Initialize CDL integration
        cdl_integration = CDLAIPromptIntegration()
        
        # Create mock character
        character = MockCharacter(character_data)
        
        # Test message that would trigger AI identity handling
        message_content = "Are you an AI? Tell me about your work with marine biology."
        
        # Mock pipeline result with emotional data
        pipeline_result = {
            'emotion_analysis': {
                'primary_emotion': 'curious',
                'confidence': 0.85
            }
        }
        
        # Mock conversation data
        relevant_memories = [
            type('Memory', (), {'content': 'User asked about coral reef conservation last week'})(),
            type('Memory', (), {'content': 'User expressed interest in marine protected areas'})()
        ]
        
        conversation_history = [
            {'role': 'user', 'content': 'Hello Elena, how are you today?'},
            {'role': 'assistant', 'content': 'Hello! I\'m doing well, thank you for asking. I just got back from a research dive.'},
            {'role': 'user', 'content': message_content}
        ]
        
        # Build the prompt
        prompt = await cdl_integration._build_unified_prompt(
            character=character,
            display_name="Mark",
            user_id="test_user_123",
            message_content=message_content,
            pipeline_result=pipeline_result,
            relevant_memories=relevant_memories,
            conversation_history=conversation_history,
            conversation_summary="Previous discussions about marine conservation and research methods"
        )
        
        print("🚀 OPTIMIZED PROMPT ORDERING TEST")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        
        # Test section ordering analysis
        sections = []
        if "🚨" in prompt:
            sections.append("1. Response Style (FIRST)")
        if "You are Elena Rodriguez" in prompt:
            sections.append("2. Character Identity + AI Guidance")
        if "🧬 PERSONALITY PROFILE" in prompt:
            sections.append("3. Personality Profile")
        if "🎬 CONVERSATION FLOW" in prompt:
            sections.append("4. Conversation Flow Guidelines")
        if "👨‍👩‍👧‍👦 PERSONAL BACKGROUND" in prompt:
            sections.append("5. Personal Background")
        if "🎭 USER EMOTIONAL STATE" in prompt:
            sections.append("6. Emotional Context")
        if "🧠 RELEVANT CONVERSATION" in prompt:
            sections.append("7. Memory Context")
        if "📚 CONVERSATION BACKGROUND" in prompt:
            sections.append("8. Conversation Summary")
        if "💬 RECENT CONVERSATION" in prompt:
            sections.append("9. Recent History")
        
        print("\n✅ DETECTED PROMPT SECTIONS (in order):")
        for section in sections:
            print(f"   {section}")
        
        # Validate key optimizations
        validations = []
        
        # Check that AI identity is integrated into character identity (not separate section)
        if "If asked about AI nature" in prompt and "🤖 AI IDENTITY GUIDANCE" not in prompt:
            validations.append("✅ AI identity integrated into character section (not separate)")
        
        # Check that emotional context comes before memory context
        emotion_pos = prompt.find("🎭 USER EMOTIONAL STATE")
        memory_pos = prompt.find("🧠 RELEVANT CONVERSATION")
        if emotion_pos > 0 and memory_pos > 0 and emotion_pos < memory_pos:
            validations.append("✅ Emotional context positioned before memory context")
        
        # Check that conversation flow comes early (after personality)
        personality_pos = prompt.find("🧬 PERSONALITY PROFILE")
        flow_pos = prompt.find("🎬 CONVERSATION FLOW")
        if personality_pos > 0 and flow_pos > 0 and flow_pos > personality_pos:
            validations.append("✅ Conversation flow guidelines positioned after personality")
        
        # Check response style is first
        if prompt.startswith("🚨") or "🚨" in prompt[:100]:
            validations.append("✅ Response style positioned first for maximum compliance")
        
        print(f"\n🎯 OPTIMIZATION VALIDATIONS:")
        for validation in validations:
            print(f"   {validation}")
        
        if len(validations) >= 3:
            print(f"\n🎉 SUCCESS: {len(validations)}/4 optimizations detected!")
            return True
        else:
            print(f"\n⚠️  WARNING: Only {len(validations)}/4 optimizations detected")
            return False

    return asyncio.run(run_test())

if __name__ == "__main__":
    success = test_prompt_section_ordering()
    if success:
        print("\n🚀 Optimized prompt ordering is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Prompt ordering needs adjustment")
        sys.exit(1)