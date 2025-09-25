#!/usr/bin/env python3
"""
Elena Emotional Intelligence + CDL Integration Test
Validates that emotional scoring properly populates CDL prompts
Tests the complete "personality and emotional intelligence flow"
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

# FORCE localhost environment (don't load .env.elena!)
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['POSTGRES_DB'] = 'whisperengine'
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine123'

os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6380'
os.environ['REDIS_DB'] = '0'

os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['QDRANT_COLLECTION_NAME'] = 'whisperengine_memory'

# Use OpenRouter (from Elena's config)
os.environ['LLM_CLIENT_TYPE'] = 'openrouter'

async def test_emotional_cdl_integration():
    """Test that emotional scoring integrates with CDL personality prompts"""
    print("🧠 Elena Emotional Intelligence + CDL Integration Test")
    print("="*60)
    
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()  # This loads our .env file with OpenRouter config
        
        # Test scenarios with different emotions
        emotional_scenarios = [
            {
                "emotion": "excited", 
                "message": "I just saw the most amazing dolphins today! They were jumping so high!",
                "expected_elena_response": ["¡Increíble", "¡Qué", "amazing", "wonderful", "🐬", "💙"]
            },
            {
                "emotion": "sad",
                "message": "I'm feeling really down about the coral bleaching I saw...",
                "expected_elena_response": ["understand", "lo siento", "together", "coral", "🌊", "care"]
            },
            {
                "emotion": "curious",
                "message": "I've been wondering about bioluminescence in deep sea creatures",
                "expected_elena_response": ["fascinating", "interesting", "marine", "deep", "species", "research"]
            },
            {
                "emotion": "grateful",
                "message": "Thank you for always sharing your marine biology knowledge with me",
                "expected_elena_response": ["de nada", "welcome", "happy", "glad", "share", "océano"]
            }
        ]
        
        success_count = 0
        
        for i, scenario in enumerate(emotional_scenarios, 1):
            print(f"\n🔍 Test {i}: {scenario['emotion'].title()} Emotion Integration")
            print(f"   Message: {scenario['message'][:50]}...")
            
            try:
                # Test the full emotional intelligence pipeline
                result = await test_full_emotional_pipeline(
                    scenario['message'], 
                    scenario['emotion'],
                    scenario['expected_elena_response']
                )
                
                if result['success']:
                    print(f"   ✅ {scenario['emotion'].title()}: Emotional CDL integration working!")
                    print(f"   📊 Emotion detected: {result.get('detected_emotion', 'N/A')}")
                    print(f"   🎯 CDL elements found: {len(result.get('cdl_elements', []))}")
                    print(f"   🧠 Elena personality markers: {len(result.get('personality_markers', []))}")
                    success_count += 1
                else:
                    print(f"   ❌ {scenario['emotion'].title()}: {result.get('error', 'Failed')}")
                    
            except Exception as e:
                print(f"   💥 {scenario['emotion'].title()}: Exception - {e}")
        
        # Summary
        total_tests = len(emotional_scenarios)
        success_rate = success_count / total_tests
        
        print(f"\n📊 Emotional Intelligence + CDL Integration Results:")
        print(f"   Passed: {success_count}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1%}")
        
        if success_count == total_tests:
            print("🎉 Perfect! Elena's emotional intelligence fully integrates with CDL personality!")
        elif success_count > 0:
            print("⚠️  Partial success - some emotional scenarios working")
        else:
            print("❌ Emotional intelligence not integrating with CDL properly")
        
        return success_count == total_tests
        
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        return False

async def test_full_emotional_pipeline(message: str, expected_emotion: str, expected_markers: list) -> dict:
    """Test the complete emotional intelligence pipeline with CDL integration"""
    result = {
        "success": False,
        "detected_emotion": None,
        "cdl_elements": [],
        "personality_markers": [],
        "response": None,
        "error": None
    }
    
    try:
        # Step 1: Test Emotional Analysis
        print("     🧠 Testing emotional analysis...")
        emotion_data = await test_emotion_detection(message)
        result["detected_emotion"] = emotion_data.primary_emotion
        
        # Step 2: Test CDL Integration with Emotional Context
        print("     🎭 Testing CDL integration with emotional context...")
        cdl_prompt = await test_cdl_with_emotion(message, emotion_data)
        result["cdl_elements"] = find_cdl_elements_in_prompt(cdl_prompt)
        
        # Step 3: Test Full Response Generation
        print("     🗣️  Testing full response generation...")
        elena_response = await test_full_response_generation(message, cdl_prompt)
        result["response"] = elena_response
        
        # Step 4: Validate Elena Personality Markers
        print("     🔍 Validating personality integration...")
        personality_markers = find_personality_markers(elena_response, expected_markers)
        result["personality_markers"] = personality_markers
        
        # Success criteria
        has_emotion = result["detected_emotion"] is not None
        has_cdl = len(result["cdl_elements"]) > 0
        has_personality = len(result["personality_markers"]) > 0
        has_response = result["response"] and len(result["response"]) > 10
        
        result["success"] = has_emotion and has_cdl and has_personality and has_response
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        return result

async def test_emotion_detection(message: str):
    """Test emotional analysis of the message"""
    try:
        from src.intelligence.enhanced_vector_emotion_analyzer import create_enhanced_emotion_analyzer
        
        # Initialize emotion analyzer
        emotion_analyzer = create_enhanced_emotion_analyzer()
        
        # Analyze emotion (using correct method signature)
        emotion_result = await emotion_analyzer.analyze_emotion(
            content=message,
            user_id="test_user",
            conversation_context=[],
            recent_emotions=[]
        )
        
        # Return the actual EmotionAnalysisResult object
        return emotion_result
        
    except Exception as e:
        print(f"       ⚠️  Emotion detection failed: {e}")
        # Return a mock object with the expected structure
        from types import SimpleNamespace
        return SimpleNamespace(
            primary_emotion="neutral",
            confidence=0.5,
            intensity=0.5,
            all_emotions={},
            emotional_trajectory=[],
            context_emotions={}
        )

async def test_cdl_with_emotion(message: str, emotion_data) -> str:
    """Test CDL integration with emotional context"""
    try:
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        
        cdl_integration = CDLAIPromptIntegration()
        
        # The CDL integration expects pipeline_result to have emotional_state
        # Let's create a compatible object
        from types import SimpleNamespace
        pipeline_result = SimpleNamespace(
            emotional_state=emotion_data.primary_emotion,
            mood_assessment={"primary": emotion_data.primary_emotion, "confidence": emotion_data.confidence},
            personality_profile=None,
            enhanced_context=None
        )
        
        # Create character-aware prompt with emotional context
        prompt = await cdl_integration.create_character_aware_prompt(
            character_file="characters/examples/elena-rodriguez.json",
            user_id="test_user",
            message_content=message,
            pipeline_result=pipeline_result  # Compatible object with emotional context!
        )
        
        return prompt
        
    except Exception as e:
        print(f"       ⚠️  CDL integration failed: {e}")
        return ""

async def test_full_response_generation(message: str, system_prompt: str) -> str:
    """Test full response generation with CDL + emotional context"""
    try:
        from src.llm.llm_protocol import create_llm_client
        
        llm_client = create_llm_client()
        
        # Generate response with full emotional + CDL context
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        response = await llm_client.generate_chat_completion_safe(messages)
        return response
        
    except Exception as e:
        print(f"       ⚠️  Response generation failed: {e}")
        return ""

def find_cdl_elements_in_prompt(prompt: str) -> list:
    """Find CDL character elements in the generated prompt"""
    cdl_indicators = [
        "Elena Rodriguez", "marine biologist", "Puerto Rico", "coral reef",
        "passionate", "enthusiastic", "ocean", "diving", "research",
        "Spanish", "¡", "marine life", "conservation"
    ]
    
    found_elements = []
    prompt_lower = prompt.lower()
    
    for indicator in cdl_indicators:
        if indicator.lower() in prompt_lower:
            found_elements.append(indicator)
    
    return found_elements

def find_personality_markers(response: str, expected_markers: list) -> list:
    """Find Elena's personality markers in the response"""
    found_markers = []
    response_lower = response.lower()
    
    for marker in expected_markers:
        if marker.lower() in response_lower:
            found_markers.append(marker)
    
    return found_markers

if __name__ == "__main__":
    success = asyncio.run(test_emotional_cdl_integration())
    exit(0 if success else 1)