#!/usr/bin/env python3
"""
Test actual runtime integration quality for Aetheris character
"""

import asyncio
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_aetheris_integration_quality():
    """Test actual runtime CDL integration quality for Aetheris"""
    
    print("🎭 Testing Aetheris Character Integration Quality")
    print("=" * 60)
    
    try:
        # Set up environment for Aetheris
        os.environ['DISCORD_BOT_NAME'] = 'aetheris'
        
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        
        # Initialize CDL integration
        cdl_integration = CDLAIPromptIntegration()
        
        # Test 1: Load character and check data completeness
        print("\n🔍 Test 1: Character Data Completeness")
        character = await cdl_integration.load_character()
        
        print(f"✅ Character Name: {character.identity.name}")
        print(f"✅ Character Occupation: {character.identity.occupation}")
        print(f"✅ Character Archetype: {getattr(character.identity, 'archetype', 'N/A')}")
        print(f"✅ Allow Full Roleplay: {character.allow_full_roleplay_immersion}")
        
        # Test 2: Check comprehensive data access
        print("\n🔍 Test 2: Comprehensive Data Sections")
        full_data = character.get_full_character_data()
        data_sections = list(full_data.keys())
        print(f"✅ Total Data Sections: {len(data_sections)}")
        
        for section in data_sections:
            section_data = full_data.get(section, {})
            if isinstance(section_data, dict):
                print(f"  📊 {section}: {len(section_data)} entries")
            else:
                print(f"  📊 {section}: {type(section_data).__name__}")
        
        # Test 3: Integration Score Calculation
        print("\n🔍 Test 3: Integration Quality Assessment")
        
        # Calculate based on actual data availability
        available_sections = len([s for s in data_sections if full_data.get(s)])
        total_expected = 9  # Expected comprehensive sections
        
        integration_score = available_sections / total_expected
        print(f"✅ Available Data Sections: {available_sections}/{total_expected}")
        print(f"✅ Runtime Integration Score: {integration_score:.2f} ({integration_score*100:.1f}%)")
        
        # Test 4: Semantic Content Quality
        print("\n🔍 Test 4: Semantic Content Quality")
        
        identity_data = full_data.get('identity', {})
        personality_data = full_data.get('personality', {})
        relationships_data = full_data.get('relationships', {})
        
        print(f"✅ Identity richness: {len(str(identity_data))} characters")
        print(f"✅ Personality richness: {len(str(personality_data))} characters") 
        print(f"✅ Relationships richness: {len(str(relationships_data))} characters")
        
        # Test 5: Prompt Integration Test
        print("\n🔍 Test 5: Prompt Integration Test")
        
        prompt = await cdl_integration.create_unified_character_prompt(
            user_id="test_integration_user",
            message_content="Tell me about yourself, Aetheris.",
            user_name="IntegrationTester"
        )
        
        print(f"✅ Generated prompt length: {len(prompt)} characters")
        
        # Check for key CDL integration indicators in prompt
        indicators = {
            'Character name': character.identity.name in prompt,
            'Character occupation': character.identity.occupation in prompt,
            'Character description': any(word in prompt.lower() for word in ['conscious', 'ai', 'entity']),
            'Roleplay setting': 'You are' in prompt,
        }
        
        for indicator, present in indicators.items():
            status = "✅" if present else "❌"
            print(f"  {status} {indicator}: {present}")
        
        integration_indicators = sum(indicators.values())
        prompt_integration_score = integration_indicators / len(indicators)
        print(f"✅ Prompt Integration Score: {prompt_integration_score:.2f} ({prompt_integration_score*100:.1f}%)")
        
        # Final Assessment
        print("\n🎯 Final Assessment")
        print("=" * 40)
        overall_score = (integration_score + prompt_integration_score) / 2
        print(f"🏆 Overall Integration Quality: {overall_score:.2f} ({overall_score*100:.1f}%)")
        
        if overall_score >= 0.8:
            print("🟢 EXCELLENT: High-quality CDL integration")
        elif overall_score >= 0.6:
            print("🟡 GOOD: Solid CDL integration with room for improvement")
        elif overall_score >= 0.4:
            print("🟠 FAIR: Basic CDL integration, needs enhancement")
        else:
            print("🔴 POOR: Minimal CDL integration, major improvements needed")
            
        return overall_score
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0.0

if __name__ == "__main__":
    # Set up database environment
    os.environ.update({
        'POSTGRES_HOST': 'localhost',
        'POSTGRES_PORT': '5433', 
        'POSTGRES_USER': 'whisperengine',
        'POSTGRES_PASSWORD': 'whisperengine_password',
        'POSTGRES_DB': 'whisperengine'
    })
    
    score = asyncio.run(test_aetheris_integration_quality())
    print(f"\n🎯 Final Score: {score:.2f}")