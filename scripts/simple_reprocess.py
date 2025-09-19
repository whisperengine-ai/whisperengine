#!/usr/bin/env python3
"""
Simple script to reprocess historical conversations through the bot's existing memory system
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.memory.optimized_adapter import get_optimized_chromadb_manager
from src.memory.integrated_memory_manager import IntegratedMemoryManager
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


async def main():
    try:
        # Get user ID from command line
        if len(sys.argv) != 2:
            print("Usage: python scripts/simple_reprocess.py <user_id>")
            return 1
            
        user_id = sys.argv[1]
        logger.info(f"Starting reprocessing for user {user_id}")
        
        # Initialize managers
        memory_adapter = await get_optimized_chromadb_manager()
        integrated_manager = IntegratedMemoryManager()
        await integrated_manager.initialize()
        
        # Try to get user memories from ChromaDB
        logger.info("Attempting to retrieve user memories...")
        
        # Use the search functionality to find existing memories
        try:
            if hasattr(memory_adapter, 'retrieve_relevant_memories'):
                memories = await memory_adapter.retrieve_relevant_memories(user_id, "conversation", limit=50)
                logger.info(f"Found {len(memories)} memories to potentially reprocess")
                
                count = 0
                for memory in memories[:10]:  # Start with just 10 for testing
                    if isinstance(memory, dict):
                        user_msg = memory.get('user_message', memory.get('content', ''))
                        bot_resp = memory.get('bot_response', memory.get('response', ''))
                        
                        if user_msg and bot_resp:
                            logger.info(f"Reprocessing: {user_msg[:50]}...")
                            result = integrated_manager.store_conversation_with_full_context(
                                user_id=user_id,
                                message=user_msg,
                                response=bot_resp
                            )
                            if result:
                                count += 1
                                
                logger.info(f"Successfully reprocessed {count} conversations")
            else:
                logger.error("Memory adapter doesn't have retrieve_relevant_memories method")
                
        except Exception as e:
            logger.error(f"Error during reprocessing: {e}")
            
        return 0
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))