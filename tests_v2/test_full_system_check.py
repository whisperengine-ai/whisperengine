import asyncio
import os
import sys
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src_v2.config.settings import settings
from src_v2.core.database import db_manager
from src_v2.memory.manager import memory_manager
from src_v2.knowledge.manager import knowledge_manager
from src_v2.evolution.trust import trust_manager
from src_v2.voice.tts import TTSManager
from src_v2.vision.manager import vision_manager
from src_v2.intelligence.activity import activity_modeler
from src_v2.agents.proactive import proactive_agent

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")

async def test_full_system():
    logger.info("=== STARTING FULL SYSTEM INTEGRATION TEST ===")
    
    # 1. Infrastructure Initialization
    logger.info("[1/7] Initializing Infrastructure...")
    try:
        await db_manager.connect_all()
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return

    if not db_manager.postgres_pool:
        logger.error("❌ Postgres connection failed.")
        return
    if not db_manager.qdrant_client:
        logger.error("❌ Qdrant connection failed.")
        return
    logger.info("✅ Infrastructure initialized.")

    # Test Data
    user_id = "test_user_integration_v2"
    character_name = settings.DISCORD_BOT_NAME or "default"
    test_content = "I am running a full system diagnostic test."

    # 2. Memory System
    logger.info("[2/7] Testing Memory System...")
    try:
        await memory_manager.initialize()
        # Add a message
        await memory_manager.add_message(
            user_id=user_id,
            character_name=character_name,
            role="user",
            content=test_content,
            metadata={"type": "test"}
        )
        # Search for it
        memories = await memory_manager.search_memories(test_content, user_id)
        if memories:
            logger.info(f"✅ Memory storage and retrieval successful. Found: {len(memories)} items.")
        else:
            logger.warning("⚠️ Memory stored but not retrieved immediately (might be indexing delay).")
    except Exception as e:
        logger.error(f"❌ Memory System failed: {e}")

    # 3. Knowledge System
    logger.info("[3/7] Testing Knowledge System...")
    try:
        # Just check if we can query the graph (even if empty)
        facts = await knowledge_manager.get_user_knowledge(user_id)
        logger.info(f"✅ Knowledge Graph query successful. Current facts: {len(facts)} chars.")
    except Exception as e:
        logger.error(f"❌ Knowledge System failed: {e}")

    # 4. Evolution (Trust)
    logger.info("[4/7] Testing Evolution System (Trust)...")
    try:
        relationship = await trust_manager.get_relationship_level(user_id, character_name)
        logger.info(f"✅ Trust System query successful. Level: {relationship['level']}")
    except Exception as e:
        logger.error(f"❌ Evolution System failed: {e}")

    # 5. Multimodal (Voice)
    logger.info("[5/7] Testing Voice System...")
    try:
        tts = TTSManager()
        if tts.client:
            logger.info("✅ TTS Manager initialized with ElevenLabs client.")
        else:
            logger.warning("⚠️ TTS Manager initialized but client is None (API Key missing?).")
    except Exception as e:
        logger.error(f"❌ Voice System failed: {e}")

    # 6. Multimodal (Vision)
    logger.info("[6/7] Testing Vision System...")
    try:
        # Just verify the manager exists and has an LLM
        if vision_manager.llm:
            logger.info("✅ Vision Manager initialized with LLM.")
        else:
            logger.error("❌ Vision Manager missing LLM.")
    except Exception as e:
        logger.error(f"❌ Vision System failed: {e}")

    # 7. Intelligence (Proactive)
    logger.info("[7/7] Testing Proactive Intelligence...")
    try:
        heatmap = await activity_modeler.get_user_activity_heatmap(user_id)
        logger.info(f"✅ Activity Modeler ran successfully. Heatmap size: {len(heatmap)}")
        
        # Test Opener Generation (Mock)
        # We won't actually call the LLM to save time/cost, just verify the agent exists
        if proactive_agent.llm:
            logger.info("✅ Proactive Agent initialized.")
    except Exception as e:
        logger.error(f"❌ Proactive Intelligence failed: {e}")

    logger.info("=== SYSTEM TEST COMPLETE ===")

if __name__ == "__main__":
    try:
        asyncio.run(test_full_system())
    except KeyboardInterrupt:
        pass
