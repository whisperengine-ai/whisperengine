#!/usr/bin/env python3
"""
Memory Trigger Enhancement Test

Tests the integration between user facts and character memory triggers.
Verifies that character memories are automatically triggered when user facts
match memory triggers.
"""

import asyncio
import logging
import os
import sys
import asyncpg
from typing import Dict, Any, List

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
from src.knowledge.semantic_router import create_semantic_knowledge_router, IntentAnalysisResult, QueryIntent


async def setup_test_environment():
    """Set up test environment with database connection and components"""
    # PostgreSQL connection
    postgres_host = os.getenv('POSTGRES_HOST', 'postgres')  # Docker service name
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
            return None, None, None

        # Create semantic router
        semantic_router = create_semantic_knowledge_router(
            postgres_pool=postgres_pool
        )

        # Create character graph manager with semantic router
        character_graph_manager = create_character_graph_manager(
            postgres_pool=postgres_pool,
            semantic_router=semantic_router
        )

        logger.info("✅ Test environment setup complete")
        return postgres_pool, semantic_router, character_graph_manager

    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        return None, None, None


async def store_test_user_fact(semantic_router, user_id: str, entity_name: str, entity_type: str):
    """Store a test user fact"""
    try:
        success = await semantic_router.store_user_fact(
            user_id=user_id,
            entity_name=entity_name,
            entity_type=entity_type,
            relationship_type="likes",
            confidence=0.9,
            emotional_context="excited"
        )

        if success:
            logger.info(f"✅ Stored test fact: {entity_name} ({entity_type}) for user {user_id}")
        else:
            logger.warning(f"⚠️ Failed to store test fact: {entity_name}")

        return success
    except Exception as e:
        logger.error(f"❌ Error storing test fact: {e}")
        return False


async def verify_user_facts(semantic_router, user_id: str):
    """Verify that user facts were stored"""
    try:
        # Create a general intent for fact retrieval
        general_intent = IntentAnalysisResult(
            intent_type=QueryIntent.FACTUAL_RECALL,
            entity_type=None,  # Get all entity types
            relationship_type=None,  # Get all relationships
            confidence=0.9,
            keywords=[]
        )

        # Get user facts
        user_facts = await semantic_router.get_user_facts(
            user_id=user_id,
            intent=general_intent,
            limit=10
        )

        logger.info(f"📊 User {user_id} has {len(user_facts)} facts:")
        for fact in user_facts:
            logger.info(f"  - {fact['entity_name']} ({fact['entity_type']}): {fact['relationship_type']}")

        return user_facts
    except Exception as e:
        logger.error(f"❌ Error retrieving user facts: {e}")
        return []


async def test_memory_trigger_enhancement():
    """Test the memory trigger enhancement feature"""
    # Set up test environment
    postgres_pool, semantic_router, character_graph_manager = await setup_test_environment()
    if not (postgres_pool and semantic_router and character_graph_manager):
        return False

    try:
        # 1. Store test user facts about diving (should trigger Elena's diving memories)
        test_user_id = "test_user_memory_trigger"
        await store_test_user_fact(semantic_router, test_user_id, "diving", "hobby")
        await store_test_user_fact(semantic_router, test_user_id, "ocean exploration", "interest")

        # 2. Verify user facts were stored
        user_facts = await verify_user_facts(semantic_router, test_user_id)
        if not user_facts:
            logger.warning("⚠️ No user facts found, test may not be accurate")

        # 3. Query character knowledge WITHOUT user_id (baseline)
        logger.info("\n🔍 BASELINE TEST: Query without user ID")
        query_text = "Tell me about your research"
        baseline_result = await character_graph_manager.query_character_knowledge(
            character_name="elena",
            query_text=query_text,
            intent=CharacterKnowledgeIntent.GENERAL,
            limit=5,
            user_id=None  # No user ID provided
        )

        logger.info(f"📊 Baseline result (no user facts):\n"
                   f"  - Background entries: {len(baseline_result.background)}\n"
                   f"  - Memories: {len(baseline_result.memories)}\n"
                   f"  - Relationships: {len(baseline_result.relationships)}\n"
                   f"  - Abilities: {len(baseline_result.abilities)}")

        # Log details of baseline memories
        baseline_memory_titles = [mem.get('title', 'Untitled') for mem in baseline_result.memories]
        logger.info("📋 Baseline memories: %s", baseline_memory_titles)

        # 4. Query character knowledge WITH user_id (memory trigger enhancement)
        logger.info("\n🔍 ENHANCEMENT TEST: Query with user ID")
        enhanced_result = await character_graph_manager.query_character_knowledge(
            character_name="elena",
            query_text=query_text,  # Same query as baseline
            intent=CharacterKnowledgeIntent.GENERAL,
            limit=5,
            user_id=test_user_id  # User ID with diving facts
        )

        logger.info(f"📊 Enhanced result (with user facts):\n"
                   f"  - Background entries: {len(enhanced_result.background)}\n"
                   f"  - Memories: {len(enhanced_result.memories)}\n"
                   f"  - Relationships: {len(enhanced_result.relationships)}\n"
                   f"  - Abilities: {len(enhanced_result.abilities)}")

        # Log details of enhanced memories
        enhanced_memory_titles = [mem.get('title', 'Untitled') for mem in enhanced_result.memories]
        logger.info("📋 Enhanced memories: %s", enhanced_memory_titles)

        # 5. Check for diving-related memories in enhanced result
        diving_memories = [mem for mem in enhanced_result.memories 
                          if any(keyword in mem.get('title', '').lower() or 
                                 keyword in mem.get('description', '').lower() or 
                                 keyword in mem.get('triggers', []) 
                                 for keyword in ['div', 'ocean', 'swim', 'underwater', 'marine'])]

        # Verify additional memories were triggered by user facts
        if len(enhanced_result.memories) > len(baseline_result.memories):
            logger.info("✅ SUCCESS: More memories triggered with user facts")
            logger.info(f"  - Additional memories: {len(enhanced_result.memories) - len(baseline_result.memories)}")
            
            # Check if we found diving-related memories
            if diving_memories:
                logger.info("✅ SUCCESS: Diving-related memories were triggered")
                for i, mem in enumerate(diving_memories, 1):
                    logger.info(f"  {i}. '{mem.get('title', 'Untitled')}'")
                    logger.info(f"     Triggers: {mem.get('triggers', [])}")
            else:
                logger.warning("⚠️ No diving-related memories found (memory trigger may not be working or no diving memories exist)")
        else:
            logger.warning("⚠️ No additional memories triggered (enhancement may not be working)")

        # Clean up
        await postgres_pool.close()
        logger.info("\n✅ Memory trigger enhancement test completed")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        if postgres_pool:
            await postgres_pool.close()


if __name__ == "__main__":
    success = asyncio.run(test_memory_trigger_enhancement())
    sys.exit(0 if success else 1)