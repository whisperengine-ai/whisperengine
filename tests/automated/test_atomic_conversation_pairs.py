#!/usr/bin/env python3
"""
Test atomic conversation pair storage - new architecture where user message
and bot response are stored as a single point instead of separate points.

Benefits:
- Atomic retrieval (no split pairs across scroll limit)
- Half the storage (1 point instead of 2)
- No orphaned responses
- Simpler logic
"""

import asyncio
import os
import sys
from datetime import datetime

# Set up path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.memory.vector_memory_system import VectorMemoryManager

async def test_atomic_storage():
    """Test storing and retrieving atomic conversation pairs."""
    
    print("\n" + "="*80)
    print("🚀 ATOMIC CONVERSATION PAIRS TEST")
    print("="*80 + "\n")
    
    # Initialize memory manager
    print("📦 Initializing VectorMemoryManager...")
    
    # Create config matching WhisperEngine structure
    config = {
        'qdrant': {
            'host': os.getenv("QDRANT_HOST", "localhost"),
            'port': int(os.getenv("QDRANT_PORT", "6334")),
            'collection_name': f"test_atomic_pairs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        },
        'embeddings': {
            'model_name': 'sentence-transformers/all-MiniLM-L6-v2'
        }
    }
    
    memory_manager = VectorMemoryManager(config=config)
    print("✅ Memory manager initialized\n")
    
    # Test user
    test_user_id = "test_atomic_user_12345"
    
    # Store test conversation
    print("💾 Storing test conversation as atomic pair...")
    user_message = "I'm interested in marine biology and conservation work in San Diego."
    bot_response = "That's wonderful! San Diego has incredible marine ecosystems. The Scripps Institution of Oceanography does groundbreaking work here. What aspect of marine biology interests you most?"
    
    success = await memory_manager.store_conversation(
        user_id=test_user_id,
        user_message=user_message,
        bot_response=bot_response,
        channel_id="test_channel",
        pre_analyzed_emotion_data={
            "primary_emotion": "curiosity",
            "roberta_confidence": 0.85,
            "emotional_intensity": 0.7
        }
    )
    
    if success:
        print("✅ Conversation stored successfully\n")
    else:
        print("❌ Failed to store conversation\n")
        return
    
    # Wait a moment for indexing
    await asyncio.sleep(1)
    
    # Retrieve conversation history
    print("📖 Retrieving conversation history...")
    history = await memory_manager.get_conversation_history(
        user_id=test_user_id,
        limit=10
    )
    
    print(f"📊 Retrieved {len(history)} messages:\n")
    
    for idx, msg in enumerate(history):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        
        print(f"[{idx}] Role: {role}")
        print(f"    Time: {timestamp}")
        print(f"    Content: {content[:80]}...")
        print()
    
    # Validate results
    print("\n" + "="*80)
    print("🔍 VALIDATION")
    print("="*80 + "\n")
    
    if len(history) >= 2:
        # Check if both user and bot messages are present
        roles = [msg.get("role") for msg in history]
        
        has_user = "user" in roles
        has_bot = "bot" in roles or "assistant" in roles
        
        print(f"✅ Has user message: {has_user}")
        print(f"✅ Has bot response: {has_bot}")
        
        # Check content
        user_found = any(user_message in msg.get("content", "") for msg in history)
        bot_found = any(bot_response in msg.get("content", "") for msg in history)
        
        print(f"✅ User message content matches: {user_found}")
        print(f"✅ Bot response content matches: {bot_found}")
        
        if has_user and has_bot and user_found and bot_found:
            print("\n🎉 SUCCESS: Atomic conversation pair storage and retrieval working!")
        else:
            print("\n⚠️  WARNING: Some data missing from retrieval")
    else:
        print(f"❌ Expected at least 2 messages, got {len(history)}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(test_atomic_storage())
