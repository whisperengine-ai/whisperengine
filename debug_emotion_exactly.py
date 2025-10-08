#!/usr/bin/env python3
"""
Debug RoBERTa emotion detection for "Exactly!" message
"""

import asyncio
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine/src')

try:
    from transformers import pipeline
    ROBERTA_AVAILABLE = True
except ImportError:
    ROBERTA_AVAILABLE = False

async def test_roberta_emotion():
    """Test RoBERTa emotion detection on 'Exactly!' message"""
    
    if not ROBERTA_AVAILABLE:
        print("❌ RoBERTa not available - transformers library not installed")
        return
    
    print("🤖 Testing RoBERTa emotion detection for 'Exactly!' message...")
    
    try:
        # Initialize RoBERTa classifier (same as WhisperEngine)
        roberta_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base", 
            return_all_scores=True
        )
        
        # Test the exact message
        test_message = "Exactly!"
        print(f"📝 Testing message: '{test_message}'")
        
        # Run analysis
        results = roberta_classifier(test_message)
        
        print("🎭 RoBERTa Results:")
        print(f"Results type: {type(results)}")
        print(f"Results content: {results}")
        
        # Handle different result formats
        if isinstance(results, list) and len(results) > 0:
            emotion_results = results[0] if isinstance(results[0], list) else results
            
            for result in emotion_results:
                emotion = result['label']
                score = result['score']
                print(f"   {emotion}: {score:.4f} ({score*100:.1f}%)")
            
            # Find highest scoring emotion
            top_emotion = max(emotion_results, key=lambda x: x['score'])
            print(f"\n🏆 Top emotion: {top_emotion['label']} ({top_emotion['score']*100:.1f}%)")
        else:
            print(f"Unexpected results format: {results}")
        
        # Test some similar messages for comparison
        test_messages = [
            "Yes!",
            "Absolutely!",
            "Perfect!",
            "Great!",
            "Exactly right!",
            "That's it!",
            "Correct!"
        ]
        
        print("\n🔍 Comparison with similar messages:")
        for msg in test_messages:
            results = roberta_classifier(msg)
            top = max(results, key=lambda x: x['score'])
            print(f"   '{msg}' → {top['label']} ({top['score']*100:.1f}%)")
            
    except Exception as e:
        print(f"❌ Error testing RoBERTa: {e}")

if __name__ == "__main__":
    asyncio.run(test_roberta_emotion())