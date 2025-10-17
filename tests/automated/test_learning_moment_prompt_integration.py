"""
Test Character Learning Moments Prompt Integration
Verifies that detected learning moments are properly injected into LLM prompts
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

async def test_learning_moment_prompt_integration():
    """Test that learning moments are added to character prompts."""
    print("🧪 Testing Learning Moment Prompt Integration")
    print("=" * 60)
    
    try:
        # Mock pipeline_dict with learning moment data
        pipeline_dict = {
            'ai_components': {
                'character_learning_moments': {
                    'surface_moment': True,
                    'learning_moments_detected': 1,
                    'suggested_integration': {
                        'type': 'user_observation',
                        'suggested_response': "I've noticed you seem really excited when we talk about marine biology!",
                        'confidence': 0.85,
                        'integration_point': 'When discussing ocean topics',
                        'character_voice': 'Express with warm enthusiasm'
                    },
                    'moments': [
                        {
                            'type': 'user_observation',
                            'confidence': 0.85,
                            'suggested_response': "I've noticed you seem really excited when we talk about marine biology!"
                        }
                    ]
                }
            }
        }
        
        # Create minimal CDL integration instance
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        
        # Initialize with minimal dependencies
        cdl_integration = CDLAIPromptIntegration()
        
        # Create a mock character (we'll use a simple approach)
        from src.characters.cdl.parser import Character, Identity, Personality, BigFive, BigFiveTrait
        
        # Create test character
        identity = Identity(
            name="Elena",
            occupation="Marine Biologist",
            age=28,
            gender="female"
        )
        
        big_five = BigFive(
            openness=BigFiveTrait(score=0.9, trait_description="Very open to new experiences"),
            conscientiousness=BigFiveTrait(score=0.7, trait_description="Highly organized"),
            extraversion=BigFiveTrait(score=0.6, trait_description="Moderately social"),
            agreeableness=BigFiveTrait(score=0.8, trait_description="Very cooperative"),
            neuroticism=BigFiveTrait(score=0.3, trait_description="Very emotionally stable")
        )
        
        personality = Personality(big_five=big_five)
        
        character = Character(
            identity=identity,
            personality=personality
        )
        
        # Build unified character prompt
        print("\n📝 Building character prompt with learning moment...")
        
        prompt = await cdl_integration.create_unified_character_prompt(
            character=character,
            user_id="test_user",
            display_name="TestUser",
            message_content="Tell me about coral reefs",
            pipeline_dict=pipeline_dict
        )
        
        # Verify learning moment was added to prompt
        if "🌟 NATURAL LEARNING MOMENT OPPORTUNITY:" in prompt:
            print("✅ Learning moment section found in prompt")
            
            # Check for specific components
            checks = {
                'Type field': '**Type**: user_observation' in prompt,
                'Confidence field': '**Confidence**: 0.85' in prompt or '**Confidence**: 0.8' in prompt,
                'Suggested response': "I've noticed you seem really excited when we talk about marine biology!" in prompt,
                'Integration point': '**Natural Integration Point**:' in prompt,
                'Character voice': '**Voice Adaptation**:' in prompt,
                'Guidance': '**GUIDANCE**:' in prompt
            }
            
            print("\n🔍 Component Verification:")
            for component, found in checks.items():
                status = "✅" if found else "❌"
                print(f"   {status} {component}")
            
            # Show relevant section
            print("\n📄 Learning Moment Section:")
            print("-" * 60)
            start_idx = prompt.find("🌟 NATURAL LEARNING MOMENT OPPORTUNITY:")
            if start_idx >= 0:
                end_idx = prompt.find("\n\n", start_idx + 200)
                if end_idx < 0:
                    end_idx = start_idx + 500
                learning_section = prompt[start_idx:end_idx]
                print(learning_section)
            print("-" * 60)
            
            if all(checks.values()):
                print("\n✅ ALL COMPONENTS VERIFIED - Integration is working!")
                return True
            else:
                print("\n⚠️ Some components missing - check implementation")
                return False
        else:
            print("❌ Learning moment section NOT found in prompt")
            print("\n📄 Prompt preview (first 1000 chars):")
            print(prompt[:1000])
            print("\n...")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_learning_moment_not_surfaced():
    """Test that learning moments are NOT added when surface_moment is False."""
    print("\n🧪 Testing Learning Moment Gating (surface_moment=False)")
    print("=" * 60)
    
    try:
        # Mock pipeline_dict with learning moment that should NOT surface
        pipeline_dict = {
            'ai_components': {
                'character_learning_moments': {
                    'surface_moment': False,  # Should NOT be added to prompt
                    'learning_moments_detected': 1,
                    'suggested_integration': {
                        'type': 'growth_insight',
                        'suggested_response': "I've learned so much from our conversations",
                        'confidence': 0.65  # Below threshold or wrong context
                    }
                }
            }
        }
        
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        from src.characters.cdl.parser import Character, Identity, Personality, BigFive, BigFiveTrait
        
        cdl_integration = CDLAIPromptIntegration()
        
        identity = Identity(name="Elena", occupation="Marine Biologist", age=28, gender="female")
        big_five = BigFive(
            openness=BigFiveTrait(score=0.9, trait_description="Very open"),
            conscientiousness=BigFiveTrait(score=0.7, trait_description="Organized"),
            extraversion=BigFiveTrait(score=0.6, trait_description="Social"),
            agreeableness=BigFiveTrait(score=0.8, trait_description="Cooperative"),
            neuroticism=BigFiveTrait(score=0.3, trait_description="Stable")
        )
        personality = Personality(big_five=big_five)
        character = Character(identity=identity, personality=personality)
        
        prompt = await cdl_integration.create_unified_character_prompt(
            character=character,
            user_id="test_user",
            display_name="TestUser",
            message_content="Tell me about coral reefs",
            pipeline_dict=pipeline_dict
        )
        
        # Verify learning moment was NOT added
        if "🌟 NATURAL LEARNING MOMENT OPPORTUNITY:" not in prompt:
            print("✅ Learning moment correctly NOT added (surface_moment=False)")
            return True
        else:
            print("❌ Learning moment was added despite surface_moment=False")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all integration tests."""
    print("🚀 Character Learning Moment Prompt Integration Tests")
    print("=" * 60)
    print()
    
    test1 = await test_learning_moment_prompt_integration()
    test2 = await test_learning_moment_not_surfaced()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Learning Moment Integration: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Learning Moment Gating:      {'✅ PASS' if test2 else '❌ FAIL'}")
    print()
    
    if test1 and test2:
        print("🎉 ALL TESTS PASSED - Character Learning Moments are now integrated!")
        return 0
    else:
        print("⚠️ SOME TESTS FAILED - Review implementation")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
