import asyncio
import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.getcwd())

from src_v2.config.settings import settings
from src_v2.core.database import db_manager

async def reset_collection():
    logger.info("Resetting Qdrant Collection...")
    
    await db_manager.connect_qdrant()
    
    collection_name = f"whisperengine_memory_{settings.DISCORD_BOT_NAME}"
    logger.info(f"Deleting collection: {collection_name}")
    
    try:
        await db_manager.qdrant_client.delete_collection(collection_name)
        logger.info("✅ Collection deleted.")
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        
    await db_manager.disconnect_all()

if __name__ == "__main__":
    if not settings.DISCORD_BOT_NAME:
        logger.error("DISCORD_BOT_NAME not set")
        sys.exit(1)
        
    asyncio.run(reset_collection())
