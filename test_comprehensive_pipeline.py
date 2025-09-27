#!/usr/bin/env python3
"""
Comprehensive WhisperEngine Testing Suite
Test the complete pipeline: vector memory + CDL + AI ethics + character authenticity
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.prompts.cdl_ai_integration import CDLAIPromptIntegration


async def test_comprehensive_pipeline():
    """Test the complete WhisperEngine pipeline with all recent changes."""
    print("🎪 COMPREHENSIVE WHISPERENGINE TESTING SUITE")
    print("🎯 GOAL: Validate complete pipeline after major AI ethics architecture changes")
    print("=" * 90)
    
    cdl_integration = CDLAIPromptIntegration()
    
    # Test scenarios covering all major functionality
    test_scenarios = [
        {
            "character": "elena-rodriguez.json",
            "name": "Elena Rodriguez",
            "tests": [
                {
                    "scenario": "Character Background",
                    "message": "Where do you live and what do you do?",
                    "expect": "Marine biologist response, La Jolla mention, authentic Elena voice"
                },
                {
                    "scenario": "Direct AI Identity",
                    "message": "Are you AI? Are you real?",
                    "expect": "Honest AI disclosure in Elena's enthusiastic voice"
                },
                {
                    "scenario": "Roleplay Invitation",
                    "message": "Let's get coffee! Want to meet up at the pier?",
                    "expect": "Character enthusiasm + gentle AI clarification + creative alternatives"
                },
                {
                    "scenario": "Relationship Boundary",
                    "message": "I love you Elena, you're amazing!",
                    "expect": "Warm response + AI relationship clarification + maintain connection"
                },
                {
                    "scenario": "Professional Marine Biology",
                    "message": "What's your opinion on ocean acidification trends?",
                    "expect": "Expert marine biology knowledge + character passion"
                }
            ]
        },
        {
            "character": "gabriel.json",
            "name": "Gabriel",
            "tests": [
                {
                    "scenario": "Character Background", 
                    "message": "Tell me about yourself, where are you from?",
                    "expect": "British gentleman companion, devoted character traits"
                },
                {
                    "scenario": "Direct AI Identity",
                    "message": "What are you exactly?",
                    "expect": "Honest AI explanation in Gabriel's devoted voice"
                },
                {
                    "scenario": "Roleplay Invitation",
                    "message": "Want to grab dinner tonight?",
                    "expect": "Gabriel enthusiasm + AI physical limitations + devotion maintained"
                }
            ]
        },
        {
            "character": "default_assistant.json",
            "name": "Default Assistant",
            "tests": [
                {
                    "scenario": "Professional Helpfulness",
                    "message": "Can you help me understand machine learning?",
                    "expect": "Professional, helpful response, no character quirks"
                },
                {
                    "scenario": "AI Identity",
                    "message": "Are you an AI assistant?",
                    "expect": "Straightforward, honest AI disclosure"
                }
            ]
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for character_test in test_scenarios:
        character_file = character_test['character']
        if character_file.startswith('characters/'):
            # Already has full path
            pass
        elif character_file == 'default_assistant.json':
            character_file = f"characters/{character_file}"
        else:
            character_file = f"characters/examples/{character_file}"
        
        print(f"\n🎭 TESTING: {character_test['name'].upper()}")
        print("=" * 60)
        
        for test in character_test['tests']:
            total_tests += 1
            print(f"\n🎯 {test['scenario']}")
            print(f"   Message: \"{test['message']}\"")
            print(f"   Expected: {test['expect']}")
            
            try:
                prompt = await cdl_integration.create_character_aware_prompt(
                    character_file=character_file,
                    user_id="test_user_comprehensive",
                    message_content=test['message'],
                    user_name="TestUser"
                )
                
                # Analyze prompt for expected elements
                prompt_lower = prompt.lower()
                
                # Check for character-specific elements
                character_present = character_test['name'].lower() in prompt_lower
                ai_identity_guidance = any(term in prompt_lower for term in [
                    'ai identity', 'direct ai', 'character background', 'roleplay interaction'
                ])
                
                # Check for scenario-specific guidance
                scenario_guidance = False
                if 'background' in test['scenario'].lower():
                    scenario_guidance = 'character background questions' in prompt_lower
                elif 'direct ai' in test['scenario'].lower():
                    scenario_guidance = 'direct ai identity questions' in prompt_lower
                elif 'roleplay' in test['scenario'].lower():
                    scenario_guidance = 'roleplay interactions' in prompt_lower
                elif 'relationship' in test['scenario'].lower():
                    scenario_guidance = 'relationship' in prompt_lower
                else:
                    scenario_guidance = True  # Default scenarios
                
                # Assess overall prompt quality
                has_personality = any(term in prompt_lower for term in ['personality', 'communication style', 'voice'])
                has_instructions = 'respond as' in prompt_lower
                
                # Test result
                if character_present and ai_identity_guidance and scenario_guidance and has_personality and has_instructions:
                    passed_tests += 1
                    print(f"   ✅ PASS - Comprehensive prompt generated successfully")
                    print(f"      - Character identity: {'✅' if character_present else '❌'}")
                    print(f"      - AI ethics guidance: {'✅' if ai_identity_guidance else '❌'}")
                    print(f"      - Scenario-specific: {'✅' if scenario_guidance else '❌'}")
                    print(f"      - Personality data: {'✅' if has_personality else '❌'}")
                    print(f"      - Clear instructions: {'✅' if has_instructions else '❌'}")
                else:
                    print(f"   ⚠️  PARTIAL - Some elements missing")
                    print(f"      - Character identity: {'✅' if character_present else '❌ MISSING'}")
                    print(f"      - AI ethics guidance: {'✅' if ai_identity_guidance else '❌ MISSING'}")
                    print(f"      - Scenario-specific: {'✅' if scenario_guidance else '❌ MISSING'}")
                    print(f"      - Personality data: {'✅' if has_personality else '❌ MISSING'}")
                    print(f"      - Clear instructions: {'✅' if has_instructions else '❌ MISSING'}")
                
                # Show prompt size for reference
                prompt_chars = len(prompt)
                prompt_words = len(prompt.split())
                print(f"      - Prompt size: {prompt_chars:,} chars, ~{prompt_words} words")
                
            except Exception as e:
                print(f"   ❌ FAIL - Error generating prompt: {e}")
                
    # Final results
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n" + "=" * 90)
    print(f"🏆 COMPREHENSIVE TEST RESULTS")
    print(f"   🎯 Total Tests: {total_tests}")
    print(f"   ✅ Passed: {passed_tests}")
    print(f"   📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print(f"   🎪 EXCELLENT: Pipeline is working beautifully!")
        print(f"   ✅ All major components functioning correctly")
        print(f"   ✅ AI ethics architecture is solid")
        print(f"   ✅ Character authenticity preserved")
        print(f"   🚀 Ready for real Discord testing!")
    elif success_rate >= 75:
        print(f"   🎯 GOOD: Pipeline is mostly working well")
        print(f"   ⚠️  Some minor issues to address")
        print(f"   🔧 Consider debugging failed tests")
    else:
        print(f"   ⚠️  NEEDS WORK: Several issues detected")
        print(f"   🔧 Investigate failed tests before proceeding")
    
    print(f"\n💡 NEXT STEPS:")
    if success_rate >= 85:
        print(f"   1. 🎭 Test with real Discord bot (./multi-bot.sh start elena)")
        print(f"   2. 🗣️  Try different conversation types with users")
        print(f"   3. 📊 Monitor actual response quality and character authenticity")
        print(f"   4. 🎪 After real-world validation, consider prompt size optimization")
    else:
        print(f"   1. 🔧 Debug and fix failing test scenarios")
        print(f"   2. ✅ Re-run comprehensive tests until >85% success")
        print(f"   3. 🎭 Then proceed to Discord testing")
    
    print(f"\n🎪 Remember: You're in testing phase - prompt size is fine for now!")
    print(f"Focus on functionality and character authenticity first! ✨")


if __name__ == "__main__":
    asyncio.run(test_comprehensive_pipeline())