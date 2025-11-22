import asyncio
import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from src_v2.config.settings import settings
from src_v2.core.database import db_manager
from src_v2.memory.manager import memory_manager

async def test_memory_system():
    logger.info("Starting Memory System Test...")
    
    # 1. Initialize
    logger.info("Initializing Database...")
    await db_manager.connect_qdrant()
    
    logger.info("Initializing Memory Manager...")
    await memory_manager.initialize()
    
    # 2. Test Data
    user_id = "test_user_123"
    character_name = "elena"
    content = "My favorite color is blue and I love dolphins."
    
    # 3. Store Memory
    logger.info(f"Storing memory: '{content}'")
    # We only test the vector part here, so we call _save_vector_memory directly 
    # or mock the postgres part if we used add_message. 
    # Let's use _save_vector_memory to test Qdrant specifically.
    await memory_manager._save_vector_memory(user_id, "human", content)
    
    # Allow some time for indexing (though usually instant for single point)
    await asyncio.sleep(1)
    
    # 4. Search Memory
    query = "What is my favorite color?"
    logger.info(f"Searching memory with query: '{query}'")
    
    memories = await memory_manager.search_memories(query, user_id)
    
    # 5. Verify
    if memories:
        logger.info("✅ Memory found!")
        for m in memories:
            logger.info(f" - Content: {m['content']}")
            logger.info(f" - Score: {m['score']}")
            
        if "blue" in memories[0]['content']:
             logger.info("✅ Content verification passed.")
        else:
             logger.error("❌ Content verification failed.")
    else:
        logger.error("❌ No memories found.")

    # Cleanup
    await db_manager.disconnect_all()

if __name__ == "__main__":
    # Set a dummy bot name for the test if not set
    if not settings.DISCORD_BOT_NAME:
        os.environ["DISCORD_BOT_NAME"] = "test_bot"
        
    asyncio.run(test_memory_system())
