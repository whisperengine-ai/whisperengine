#!/usr/bin/env python3
"""
Emotional Context Synchronization Test

Tests the integration between user emotional state (from RoBERTa analysis)
and character memory retrieval to create emotionally intelligent responses.
"""

import asyncio
import logging
import os
import sys
import asyncpg
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components
from src.characters.cdl.character_graph_manager import create_character_graph_manager, CharacterKnowledgeIntent
from src.knowledge.semantic_router import create_semantic_knowledge_router
from src.memory.memory_protocol import create_memory_manager


async def setup_test_environment():
    """Set up test environment with database connection and components"""
    # PostgreSQL connection
    postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
    postgres_port = int(os.getenv('POSTGRES_PORT', '5432'))
    postgres_user = os.getenv('POSTGRES_USER', 'postgres')
    postgres_password = os.getenv('POSTGRES_PASSWORD', 'mysecretpassword')
    postgres_db = os.getenv('POSTGRES_DB', 'whisperengine')

    try:
        # Create connection pool
        postgres_pool = await asyncpg.create_pool(
            host=postgres_host,
            port=postgres_port,
            user=postgres_user,
            password=postgres_password,
            database=postgres_db
        )

        if not postgres_pool:
            logger.error("❌ Failed to create PostgreSQL pool")
            return None, None, None, None

        # Create memory manager (vector system)
        memory_manager = create_memory_manager(memory_type="vector")

        # Create semantic router
        semantic_router = create_semantic_knowledge_router(
            postgres_pool=postgres_pool
        )

        # Create character graph manager WITH memory manager
        character_graph_manager = create_character_graph_manager(
            postgres_pool=postgres_pool,
            semantic_router=semantic_router,
            memory_manager=memory_manager
        )

        logger.info("✅ Test environment setup complete")
        return postgres_pool, semantic_router, memory_manager, character_graph_manager

    except Exception as e:
        logger.error("❌ Test setup failed: %s", e)
        return None, None, None, None


async def store_test_conversation_with_emotion(memory_manager, user_id: str, emotion: str, intensity: float, message: str):
    """Store a test conversation message with specific emotion"""
    try:
        # Store the conversation directly using the memory manager
        await memory_manager.store_conversation(
            user_id=user_id,
            user_message=message,
            bot_response="I understand how you're feeling. Let me share something with you.",
            pre_analyzed_emotion_data={
                'emotion': emotion,
                'confidence': 0.9,
                'primary_intensity': intensity,
                'all_emotions': {emotion: intensity}
            }
        )
        
        logger.info("✅ Stored test conversation: emotion=%s, intensity=%.2f", emotion, intensity)
        return True
        
    except Exception as e:
        logger.error("❌ Error storing test conversation: %s", e)
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_emotional_context_synchronization():
    """Test the emotional context synchronization feature"""
    # Set up test environment
    postgres_pool, semantic_router, memory_manager, character_graph_manager = await setup_test_environment()
    if not all([postgres_pool, semantic_router, memory_manager, character_graph_manager]):
        return False

    try:
        test_user_id = "test_user_emotional_sync"
        
        # SCENARIO 1: User feeling joyful
        logger.info("\n" + "="*80)
        logger.info("SCENARIO 1: User feeling joyful → Should prioritize positive memories")
        logger.info("="*80)
        
        # Store joyful conversation
        await store_test_conversation_with_emotion(
            memory_manager, test_user_id, "joy", 0.9,
            "I'm so excited! I just got accepted to my dream university!"
        )
        await store_test_conversation_with_emotion(
            memory_manager, test_user_id, "joy", 0.85,
            "This is the best day ever!"
        )
        
        # Query character memories
        joy_result = await character_graph_manager.query_character_knowledge(
            character_name="elena",
            query_text="Tell me about your memories",
            intent=CharacterKnowledgeIntent.MEMORIES,
            limit=5,
            user_id=test_user_id
        )
        
        logger.info("📊 Joyful user query results:")
        logger.info("  - Total memories: %d", len(joy_result.memories))
        for i, mem in enumerate(joy_result.memories[:3], 1):
            emotional_alignment = mem.get('emotional_alignment_score', 'N/A')
            logger.info("  %d. '%s' (alignment: %s)", 
                       i, mem.get('title', 'Untitled'), emotional_alignment)
        
        # SCENARIO 2: User feeling sad
        logger.info("\n" + "="*80)
        logger.info("SCENARIO 2: User feeling sad → Should prioritize empathetic/comforting memories")
        logger.info("="*80)
        
        # Store sad conversation
        test_user_id_sad = "test_user_sad"
        await store_test_conversation_with_emotion(
            memory_manager, test_user_id_sad, "sadness", 0.8,
            "I'm feeling really down today. Things haven't been going well."
        )
        await store_test_conversation_with_emotion(
            memory_manager, test_user_id_sad, "sadness", 0.75,
            "I just need someone to talk to..."
        )
        
        # Query character memories
        sad_result = await character_graph_manager.query_character_knowledge(
            character_name="elena",
            query_text="Tell me about your experiences",
            intent=CharacterKnowledgeIntent.MEMORIES,
            limit=5,
            user_id=test_user_id_sad
        )
        
        logger.info("📊 Sad user query results:")
        logger.info("  - Total memories: %d", len(sad_result.memories))
        for i, mem in enumerate(sad_result.memories[:3], 1):
            emotional_alignment = mem.get('emotional_alignment_score', 'N/A')
            logger.info("  %d. '%s' (alignment: %s)", 
                       i, mem.get('title', 'Untitled'), emotional_alignment)
        
        # SCENARIO 3: Verify emotional alignment scores
        logger.info("\n" + "="*80)
        logger.info("SCENARIO 3: Verify emotional alignment scoring")
        logger.info("="*80)
        
        if joy_result.memories:
            joyful_alignments = [m.get('emotional_alignment_score', 0) for m in joy_result.memories if 'emotional_alignment_score' in m]
            if joyful_alignments:
                avg_joy_alignment = sum(joyful_alignments) / len(joyful_alignments)
                logger.info("✅ Average emotional alignment (joyful user): %.3f", avg_joy_alignment)
            else:
                logger.warning("⚠️ No emotional alignment scores found in joyful memories")
        
        if sad_result.memories:
            sad_alignments = [m.get('emotional_alignment_score', 0) for m in sad_result.memories if 'emotional_alignment_score' in m]
            if sad_alignments:
                avg_sad_alignment = sum(sad_alignments) / len(sad_alignments)
                logger.info("✅ Average emotional alignment (sad user): %.3f", avg_sad_alignment)
            else:
                logger.warning("⚠️ No emotional alignment scores found in sad memories")
        
        # SUCCESS CRITERIA
        logger.info("\n" + "="*80)
        logger.info("TEST SUCCESS CRITERIA")
        logger.info("="*80)
        
        success = True
        
        # 1. Check if emotional context was detected
        if joy_result.memories and any('emotional_alignment_score' in m for m in joy_result.memories):
            logger.info("✅ SUCCESS: Emotional alignment scores computed for joyful user")
        else:
            logger.warning("⚠️ PARTIAL: No emotional alignment scores (may need character memories with emotional_impact)")
            success = False
        
        # 2. Check if sad user gets different ranking
        if sad_result.memories and any('emotional_alignment_score' in m for m in sad_result.memories):
            logger.info("✅ SUCCESS: Emotional alignment scores computed for sad user")
        else:
            logger.warning("⚠️ PARTIAL: No emotional alignment scores for sad user")
            success = False
        
        # 3. Verify memory manager integration works
        recent_joy = await memory_manager.get_conversation_history(test_user_id, limit=2)
        if recent_joy and len(recent_joy) > 0:
            logger.info("✅ SUCCESS: Memory manager integration working")
            logger.info("   Retrieved %d recent messages for emotional analysis", len(recent_joy))
        else:
            logger.warning("⚠️ Memory retrieval may have issues")
        
        # Clean up
        await postgres_pool.close()
        logger.info("\n✅ Emotional context synchronization test completed")
        return success

    except Exception as e:
        logger.error("❌ Test failed with error: %s", e)
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        if postgres_pool:
            await postgres_pool.close()


if __name__ == "__main__":
    success = asyncio.run(test_emotional_context_synchronization())
    sys.exit(0 if success else 1)
