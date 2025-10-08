#!/usr/bin/env python3
"""
Test script to debug emotion detection for Luna cat message
This will help us isolate whether the issue is in the emotion analyzer itself
or in the pipeline integration.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_luna_emotion():
    """Test emotion detection for the Luna cat message that was incorrectly detected as sadness"""
    
    print("🎭 TESTING LUNA CAT MESSAGE EMOTION DETECTION")
    print("=" * 60)
    
    # Your original Luna message
    luna_message = "I just got a new cat today! her name is Luna! she is soooo cute!"
    
    print(f"📝 INPUT MESSAGE: '{luna_message}'")
    print(f"📏 MESSAGE LENGTH: {len(luna_message)} characters")
    print("🔍 EXPECTED EMOTION: Joy/happiness")
    print("🚨 ACTUAL FROM LOGS: Sadness (0.908 confidence) - WRONG!")
    print()
    
    try:
        # Import the emotion analyzer
        from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
        
        # Create analyzer instance
        analyzer = EnhancedVectorEmotionAnalyzer()
        
        print("✅ Successfully created EnhancedVectorEmotionAnalyzer")
        print()
        
        # Test the emotion analysis
        print("🔬 RUNNING EMOTION ANALYSIS...")
        result = await analyzer.analyze_emotion(
            content=luna_message,
            user_id="test_user_luna",
            conversation_context=[],
            recent_emotions=None
        )
        
        print("📊 EMOTION ANALYSIS RESULTS:")
        print(f"  Primary Emotion: {result.primary_emotion}")
        print(f"  Confidence: {result.confidence:.3f}")
        print(f"  Intensity: {result.intensity:.3f}")
        print(f"  All Emotions: {result.all_emotions}")
        print(f"  Is Multi-Emotion: {hasattr(result, 'is_multi_emotion') and result.is_multi_emotion}")
        print(f"  Analysis Time: {result.analysis_time_ms}ms")
        
        if hasattr(result, 'mixed_emotions') and result.mixed_emotions:
            print(f"  Mixed Emotions: {result.mixed_emotions}")
        
        # Validate results
        print()
        print("🔍 VALIDATION:")
        
        if result.primary_emotion == 'joy':
            print("✅ CORRECT: Detected joy as expected!")
        elif result.primary_emotion == 'sadness':
            print("❌ BUG CONFIRMED: Still detecting sadness - analyzer is broken!")
        else:
            print(f"⚠️  UNEXPECTED: Detected {result.primary_emotion} - not joy or sadness")
        
        # Check confidence levels
        if result.confidence > 0.8:
            print(f"📈 HIGH CONFIDENCE: {result.confidence:.3f} - analyzer is very sure")
        else:
            print(f"📉 LOW CONFIDENCE: {result.confidence:.3f} - analyzer is uncertain")
            
        return result
        
    except Exception as e:
        print(f"❌ ERROR: Failed to run emotion analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_simple_happy_message():
    """Test with an even simpler happy message to see if analyzer works at all"""
    
    print("\n" + "=" * 60)
    print("🎭 TESTING SIMPLE HAPPY MESSAGE")
    print("=" * 60)
    
    simple_message = "I am so happy!"
    
    print(f"📝 INPUT MESSAGE: '{simple_message}'")
    print("🔍 EXPECTED EMOTION: Joy/happiness")
    
    try:
        from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
        analyzer = EnhancedVectorEmotionAnalyzer()
        
        result = await analyzer.analyze_emotion(
            content=simple_message,
            user_id="test_user_simple",
            conversation_context=[],
            recent_emotions=None
        )
        
        print("📊 SIMPLE MESSAGE RESULTS:")
        print(f"  Primary Emotion: {result.primary_emotion}")
        print(f"  Confidence: {result.confidence:.3f}")
        print(f"  All Emotions: {result.all_emotions}")
        
        if result.primary_emotion == 'joy':
            print("✅ SIMPLE MESSAGE: Correctly detected joy!")
        else:
            print(f"❌ SIMPLE MESSAGE: Failed - detected {result.primary_emotion}")
            
        return result
        
    except Exception as e:
        print(f"❌ ERROR: Failed to run simple emotion analysis: {e}")
        return None

async def main():
    """Main test function"""
    
    print("🚀 STARTING EMOTION DETECTION DEBUG SESSION")
    print("This will help us isolate the Luna cat message emotion detection bug")
    print()
    
    # Test 1: Your Luna message
    luna_result = await test_luna_emotion()
    
    # Test 2: Simple happy message
    simple_result = await test_simple_happy_message()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if luna_result and simple_result:
        print("✅ Both tests completed successfully")
        
        if luna_result.primary_emotion == 'joy' and simple_result.primary_emotion == 'joy':
            print("✅ CONCLUSION: Emotion analyzer is working correctly!")
            print("🔍 The bug may be in the pipeline integration or shared analyzer locks")
        elif luna_result.primary_emotion == 'sadness':
            print("❌ CONCLUSION: Emotion analyzer is broken - Luna message still shows sadness")
            print("🔧 Need to investigate RoBERTa model loading or preprocessing")
        else:
            print(f"⚠️  CONCLUSION: Mixed results - Luna: {luna_result.primary_emotion}, Simple: {simple_result.primary_emotion}")
    else:
        print("❌ Tests failed to complete - check error messages above")
    
    print("\n🎯 NEXT STEPS based on results:")
    print("  - If analyzer works: Check pipeline integration")
    print("  - If analyzer broken: Check RoBERTa model loading")
    print("  - If mixed results: Check text preprocessing")

if __name__ == "__main__":
    asyncio.run(main())