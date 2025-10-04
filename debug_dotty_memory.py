#!/usr/bin/env python3
"""
Debug script for Dotty's memory/greeting loop issue
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
project_root = "/app" if os.path.exists("/app/src") else "/Users/markcastillo/git/whisperengine"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.memory.memory_protocol import create_memory_manager

async def debug_dotty_memory():
    """Debug Dotty's memory system for greeting loops"""
    
    # Load Dotty's environment
    env_path = os.path.join(project_root, ".env.dotty")
    print(f"Loading environment from: {env_path}")
    load_dotenv(env_path)
    
    # Initialize memory manager
    memory_manager = create_memory_manager("vector")
    bot_name = os.getenv('DISCORD_BOT_NAME', 'dotty')
    collection_name = os.getenv('QDRANT_COLLECTION_NAME')
    
    print(f"✅ Bot name: {bot_name}")
    print(f"✅ Collection: {collection_name}")
    print()
    
    # Test user ID from the conversation logs
    user_id = "672814231002939413"  # Discord user ID from bug report
    
    try:
        print("🔍 Testing conversation history retrieval...")
        history = await memory_manager.get_conversation_history(user_id=user_id, limit=15)
        print(f"📚 Found {len(history)} conversation messages:")
        for i, msg in enumerate(history[-10:], 1):  # Show last 10
            timestamp = msg.get('timestamp', 'unknown') if isinstance(msg, dict) else getattr(msg, 'timestamp', 'unknown')
            role = msg.get('role', 'unknown') if isinstance(msg, dict) else getattr(msg, 'role', 'unknown')
            content = msg.get('content', '') if isinstance(msg, dict) else getattr(msg, 'content', '')
            content_preview = content[:80] + "..." if len(content) > 80 else content
            print(f"  {i:2d}. [{timestamp}] {role:4s}: {content_preview}")
        print()
        
        print("🔍 Testing memory retrieval for 'Frosted Memory'...")
        memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="Frosted Memory drink vanilla crème de cacao peppermint",
            limit=8
        )
        print(f"🧠 Found {len(memories)} relevant memories:")
        for i, memory in enumerate(memories, 1):
            score = getattr(memory, 'relevance_score', 'N/A')
            content_preview = memory.content[:80] + "..." if len(memory.content) > 80 else memory.content
            print(f"  {i}. Score: {score} - {content_preview}")
        print()
        
        print("🔍 Testing memory retrieval for greeting patterns...")
        greeting_memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="Evenin' Whispers what's shakin sugar greeting",
            limit=8
        )
        print(f"👋 Found {len(greeting_memories)} greeting-related memories:")
        for i, memory in enumerate(greeting_memories, 1):
            score = getattr(memory, 'relevance_score', 'N/A')
            content_preview = memory.content[:80] + "..." if len(memory.content) > 80 else memory.content
            print(f"  {i}. Score: {score} - {content_preview}")
        print()
        
        # Test if memories contain conversation context
        if history:
            latest_msg = history[-1]
            print(f"🎯 Latest message: {latest_msg.content[:100]}...")
            
            # Check if recent conversation context would be retrieved
            context_memories = await memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=latest_msg.content,
                limit=5
            )
            print(f"🔗 Context memories for latest message: {len(context_memories)}")
            for i, memory in enumerate(context_memories, 1):
                score = getattr(memory, 'relevance_score', 'N/A')
                content_preview = memory.content[:60] + "..." if len(memory.content) > 60 else memory.content
                print(f"  {i}. Score: {score} - {content_preview}")
        
    except Exception as e:
        print(f"❌ Memory error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_dotty_memory())