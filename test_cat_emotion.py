#!/usr/bin/env python3
"""
Quick test to verify emotion detection for cat message
"""
import asyncio
import os
import sys
sys.path.append('/Users/markcastillo/git/whisperengine')

# Set required environment variables
os.environ['FASTEMBED_CACHE_PATH'] = '/tmp/fastembed_cache'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'

from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer

async def test_cat_emotion():
    """Test emotion detection for the cat message."""
    
    # Initialize the emotion analyzer
    analyzer = EnhancedVectorEmotionAnalyzer()
    
    # The actual message you sent
    cat_message = "I just got a new cat! she's so cute!"
    
    print(f"🐱 Testing emotion analysis for: '{cat_message}'")
    print("=" * 60)
    
    try:
        # Analyze the emotion
        result = await analyzer.analyze_emotion(
            content=cat_message,
            user_id="test_user"
        )
        
        print(f"📊 PRIMARY EMOTION: {result.primary_emotion}")
        print(f"📈 CONFIDENCE: {result.confidence:.3f}")
        print(f"🎭 ALL EMOTIONS: {result.all_emotions}")
        print(f"⚡ PROCESSING TIME: {result.analysis_time_ms:.1f}ms")
        print(f"🔥 INTENSITY: {result.intensity:.3f}")
        
        # Check for mixed emotions
        if result.mixed_emotions:
            print(f"🌈 MIXED EMOTIONS: {result.mixed_emotions}")
            
        # Check context emotions
        if result.context_emotions:
            print(f"� CONTEXT EMOTIONS: {result.context_emotions}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cat_emotion())