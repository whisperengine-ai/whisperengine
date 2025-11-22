import asyncio
import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from src_v2.config.settings import settings
from src_v2.core.database import db_manager
from src_v2.knowledge.manager import knowledge_manager

async def test_knowledge_system():
    logger.info("Starting Knowledge System Test...")
    
    # 1. Initialize
    logger.info("Initializing Database...")
    await db_manager.connect_neo4j()
    
    # 2. Test Data
    user_id = "test_user_knowledge_1"
    message = "I live in San Diego and I have a dog named Rex."
    
    # 3. Process Message (Extract & Store)
    logger.info(f"Processing message: '{message}'")
    await knowledge_manager.process_user_message(user_id, message)
    
    # 4. Retrieve Knowledge
    logger.info("Retrieving knowledge...")
    facts = await knowledge_manager.get_user_knowledge(user_id)
    
    # 5. Verify
    if facts:
        logger.info("✅ Knowledge found!")
        logger.info(f"Facts:\n{facts}")
        
        if "San Diego" in facts and "Rex" in facts:
             logger.info("✅ Fact verification passed.")
        else:
             logger.error("❌ Fact verification failed.")
    else:
        logger.error("❌ No knowledge found.")

    # Cleanup
    await db_manager.disconnect_all()

if __name__ == "__main__":
    asyncio.run(test_knowledge_system())
