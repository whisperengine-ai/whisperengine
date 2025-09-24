#!/usr/bin/env python3
"""
Debug Elena's memory access patterns
"""
import asyncio
import os
import logging
from datetime import datetime
from src.memory.memory_protocol import create_memory_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_elena_memory():
    """Debug Elena's memory access"""
    
    # Set environment for Elena
    os.environ["DISCORD_BOT_NAME"] = "Elena"
    os.environ["QDRANT_HOST"] = "localhost"
    os.environ["QDRANT_PORT"] = "6334"
    os.environ["QDRANT_COLLECTION_NAME"] = "whisperengine_memory"
    
    user_id = "672814231002939413"  # MarkAnthony's user ID
    
    try:
        # Create memory manager
        memory_manager = create_memory_manager(memory_type="vector")
        
        logger.info("🔍 Testing Elena's memory access...")
        
        # Test 1: Basic memory retrieval
        logger.info("=== Test 1: Basic Memory Retrieval ===")
        memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="conversation history patterns interactions",
            limit=5
        )
        
        logger.info(f"Retrieved {len(memories) if memories else 0} memories")
        if memories:
            for i, memory in enumerate(memories[:3]):
                content = memory.get('content', '')[:100] + '...' if len(memory.get('content', '')) > 100 else memory.get('content', '')
                timestamp = memory.get('timestamp', 'Unknown')
                score = memory.get('score', 'N/A')
                logger.info(f"Memory {i+1}: [{timestamp}] Score: {score} - {content}")
        
        # Test 2: Conversation history
        logger.info("\n=== Test 2: Conversation History ===")
        history = await memory_manager.get_conversation_history(
            user_id=user_id,
            limit=5
        )
        
        logger.info(f"Retrieved {len(history) if history else 0} conversation entries")
        if history:
            for i, entry in enumerate(history[:3]):
                content = entry.get('content', '')[:80] + '...' if len(entry.get('content', '')) > 80 else entry.get('content', '')
                role = entry.get('role', 'Unknown')
                timestamp = entry.get('timestamp', 'Unknown')
                logger.info(f"Entry {i+1}: [{timestamp}] {role} - {content}")
        
        # Test 3: Context-aware memory retrieval
        logger.info("\n=== Test 3: Context-Aware Memory Retrieval ===")
        if hasattr(memory_manager, 'retrieve_context_aware_memories'):
            context_memories = await memory_manager.retrieve_context_aware_memories(
                user_id=user_id,
                query="what do you know about me personal interests career",
                max_memories=5,
                context={"type": "personal_information"},
                emotional_context="general conversation"
            )
            
            logger.info(f"Retrieved {len(context_memories) if context_memories else 0} context-aware memories")
            if context_memories:
                for i, memory in enumerate(context_memories[:3]):
                    content = memory.get('content', '')[:100] + '...' if len(memory.get('content', '')) > 100 else memory.get('content', '')
                    timestamp = memory.get('timestamp', 'Unknown')
                    score = memory.get('score', 'N/A')
                    logger.info(f"Context Memory {i+1}: [{timestamp}] Score: {score} - {content}")
        else:
            logger.info("Context-aware memory retrieval not available")
        
        # Test 4: Check bot_name filtering
        logger.info("\n=== Test 4: Bot Name Filtering Check ===")
        logger.info(f"Current DISCORD_BOT_NAME: {os.getenv('DISCORD_BOT_NAME')}")
        logger.info(f"Memory manager type: {type(memory_manager).__name__}")
        
        logger.info("🔍 Elena memory debugging complete!")
        
    except Exception as e:
        logger.error(f"Error during memory debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_elena_memory())