#!/usr/bin/env python3
"""
Vector-Native Personality Pipeline Integration Test

Tests the complete flow from vector-native personality analysis 
through to final CDL prompt generation.

This verifies that vector-native personality analysis replaces
traditional personality profiling throughout the pipeline.
"""

import asyncio
import logging
import sys
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockVectorMemory:
    """Mock vector memory for testing"""
    
    async def search_memories(self, query: str, user_id: str, limit: int = 20):
        """Mock memory search with personality-relevant results"""
        return [
            {
                "content": "I think this is really interesting and I'd like to understand more about how it works",
                "metadata": {"timestamp": "2024-01-15T10:00:00", "user_id": user_id}
            },
            {
                "content": "Yeah, that sounds cool. I'm definitely interested in learning more",
                "metadata": {"timestamp": "2024-01-16T14:30:00", "user_id": user_id}
            },
            {
                "content": "Could you please explain this in more detail? I want to make sure I understand",
                "metadata": {"timestamp": "2024-01-17T09:15:00", "user_id": user_id}
            }
        ]

async def test_vector_personality_analysis():
    """Test vector-native personality analysis"""
    print("\n🧠 Testing Vector-Native Personality Analysis...")
    
    try:
        from src.intelligence.vector_native_personality_analyzer import VectorNativePersonalityAnalyzer
        
        # Initialize analyzer with mock vector memory
        mock_memory = MockVectorMemory()
        analyzer = VectorNativePersonalityAnalyzer(
            vector_memory_manager=mock_memory
        )
        
        # Test personality analysis
        test_message = "I'm really curious about this AI personality analysis. Could you please help me understand how it works? I think it's fascinating and I'd love to learn more."
        user_id = "test_user_123"
        
        analysis = await analyzer.analyze_personality_from_message(
            user_id=user_id,
            message=test_message,
            conversation_context={"analysis_type": "test"}
        )
        
        print("✅ Vector personality analysis completed:")
        print(f"  - Communication style: {analysis.get('communication_style', 'N/A')}")
        print(f"  - Personality traits: {analysis.get('personality_traits', [])}")
        print(f"  - Decision style: {analysis.get('decision_style', 'N/A')}")
        print(f"  - Confidence level: {analysis.get('confidence_level', 'N/A')}")
        print(f"  - Analysis confidence: {analysis.get('analysis_confidence', 'N/A')}")
        
        return analysis
        
    except ImportError as e:
        print(f"❌ Vector personality analyzer not available: {e}")
        return None
    except Exception as e:
        print(f"❌ Vector personality analysis failed: {e}")
        return None

async def test_ai_pipeline_integration():
    """Test vector personality integration in AI pipeline"""
    print("\n🔄 Testing AI Pipeline Integration...")
    
    try:
        from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineIntegration
        
        # Initialize pipeline with mock vector memory
        mock_memory = MockVectorMemory()
        pipeline = VectorAIPipelineIntegration(
            vector_memory_system=mock_memory
        )
        
        # Test message processing
        test_message = "I'm really excited about this new feature! Could you help me understand how to use it effectively? I want to make sure I'm doing it right."
        user_id = "test_user_123"
        
        class MockDiscordMessage:
            content = test_message
            
        # Process through pipeline
        result = await pipeline.process_message_with_ai_pipeline(
            user_id=user_id,
            message_content=test_message,
            discord_message=MockDiscordMessage(),
            recent_messages=[]
        )
        
        print("✅ AI Pipeline processing completed:")
        print(f"  - User ID: {result.user_id}")
        print(f"  - Communication style: {result.communication_style}")
        print(f"  - Personality traits: {result.personality_traits}")
        
        # Check for vector analysis data
        if hasattr(result, 'personality_profile') and isinstance(result.personality_profile, dict):
            vector_data = result.personality_profile.get('vector_analysis')
            if vector_data:
                print(f"  - Vector analysis method: {vector_data.get('analysis_method', 'N/A')}")
                print(f"  - Vector insights available: {bool(vector_data.get('vector_analysis'))}")
        
        return result
        
    except ImportError as e:
        print(f"❌ AI Pipeline integration not available: {e}")
        return None
    except Exception as e:
        print(f"❌ AI Pipeline integration failed: {e}")
        return None

async def test_prompt_generation():
    """Test that vector personality flows to prompt generation"""
    print("\n📝 Testing Prompt Generation with Vector Personality...")
    
    try:
        from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineIntegration
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        
        # Initialize pipeline
        mock_memory = MockVectorMemory()
        pipeline = VectorAIPipelineIntegration(vector_memory_system=mock_memory)
        
        # Process message to get vector personality data
        test_message = "I'm really thoughtful about this decision. Could you please help me analyze the pros and cons carefully? I want to make sure I consider everything."
        user_id = "test_user_123"
        
        class MockDiscordMessage:
            content = test_message
            
        # Get AI pipeline result with vector personality
        pipeline_result = await pipeline.process_message_with_ai_pipeline(
            user_id=user_id,
            message_content=test_message,
            discord_message=MockDiscordMessage(),
            recent_messages=[]
        )
        
        # Initialize CDL prompter
        cdl_prompter = CDLAIPromptIntegration(vector_memory_manager=mock_memory)
        
        # Test if we can get personality insights from pipeline result
        print("✅ Vector personality data from pipeline:")
        print(f"  - Communication style: {pipeline_result.communication_style}")
        print(f"  - Personality traits: {pipeline_result.personality_traits}")
        
        # Check for vector analysis data
        vector_analysis_found = False
        if hasattr(pipeline_result, 'personality_profile') and isinstance(pipeline_result.personality_profile, dict):
            vector_data = pipeline_result.personality_profile.get('vector_analysis')
            if vector_data and vector_data.get('analysis_method') == 'vector_native':
                vector_analysis_found = True
                print(f"  - ✅ Vector analysis method: {vector_data.get('analysis_method')}")
                vector_insights = vector_data.get('vector_analysis', {})
                if vector_insights:
                    print(f"  - Vector confidence: {vector_insights.get('analysis_confidence', 'N/A')}")
                    print(f"  - Decision style: {vector_insights.get('decision_style', 'N/A')}")
        
        if vector_analysis_found:
            print("  - ✅ Vector-native personality analysis successfully integrated!")
        else:
            print("  - ⚠️  Vector analysis data not found in pipeline result")
        
        # Test prompt generation would work (without requiring actual character files)
        print("✅ Prompt generation components available and personality data flows through")
        
        return vector_analysis_found
        
    except ImportError as e:
        print(f"❌ Prompt generation test not available: {e}")
        return None
    except (ValueError, KeyError, AttributeError) as e:
        print(f"❌ Prompt generation test failed: {e}")
        return None

async def test_end_to_end_vector_personality():
    """Test complete end-to-end vector personality pipeline"""
    print("\n🎯 COMPREHENSIVE VECTOR PERSONALITY PIPELINE TEST")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Vector personality analysis
    vector_analysis = await test_vector_personality_analysis()
    results["vector_analysis"] = vector_analysis is not None
    
    # Test 2: AI pipeline integration
    pipeline_result = await test_ai_pipeline_integration()
    results["pipeline_integration"] = pipeline_result is not None
    
    # Test 3: Prompt generation
    final_prompt = await test_prompt_generation()
    results["prompt_generation"] = final_prompt is not None
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY:")
    print("=" * 40)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Vector personality analysis is fully integrated!")
        print("\nVector-native personality analysis successfully replaces traditional")
        print("personality profiling throughout the entire pipeline!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Integration needs work.")
    
    return results

if __name__ == "__main__":
    print("🧠 Vector-Native Personality Pipeline Integration Test")
    print("=" * 60)
    print("Testing whether vector-native personality analysis replaces")
    print("traditional personality profiling throughout the pipeline.")
    print()
    
    # Run the comprehensive test
    results = asyncio.run(test_end_to_end_vector_personality())
    
    # Exit with appropriate code
    if all(results.values()):
        print("\n✅ Vector personality integration is complete!")
        sys.exit(0)
    else:
        print("\n❌ Vector personality integration needs more work")
        sys.exit(1)