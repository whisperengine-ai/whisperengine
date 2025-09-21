#!/usr/bin/env python3
"""
Debug script to test emotion detection in isolation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.memory.vector_memory_system import VectorMemoryStore

def test_emotion_detection():
    """Test emotion detection method directly"""
    store = VectorMemoryStore(
        qdrant_host='localhost',
        qdrant_port=6333,
        collection_name='test_emotions',
        embedding_model='snowflake/snowflake-arctic-embed-xs'
    )
    
    test_messages = [
        "I'm absolutely ecstatic about my promotion!",
        "I feel completely devastated by this loss",
        "I'm somewhat concerned about the weather tomorrow",
        "That's an interesting perspective on the topic",
        "I'm terrified and furious about what happened!",
        "What time is it?"
    ]
    
    print("🧪 Testing emotion detection directly:")
    for msg in test_messages:
        emotion, intensity = store._extract_emotional_context(msg)
        print(f"  Message: '{msg}'")
        print(f"  → Emotion: {emotion}, Intensity: {intensity:.3f}")
        print()

if __name__ == "__main__":
    test_emotion_detection()