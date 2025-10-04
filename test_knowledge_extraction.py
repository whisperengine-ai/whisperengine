#!/usr/bin/env python3
"""
Quick test script for Phase 3 Knowledge Extraction Pipeline

Tests:
1. Pattern detection for factual statements
2. Entity extraction from messages
3. PostgreSQL storage via knowledge_router
"""

import asyncio
import logging
import os
from env_manager import load_environment

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_knowledge_extraction():
    """Test knowledge extraction and storage"""
    
    # Load environment
    load_environment()
    
    # Import required components
    from src.core.message_processor import MessageProcessor, MessageContext
    from src.core.bot import DiscordBotCore
    
    logger.info("🚀 Initializing bot core for testing...")
    
    # Initialize bot core (minimal setup)
    bot_core = DiscordBotCore(debug_mode=True)
    bot_core.initialize_llm_client()
    bot_core.initialize_memory_system()
    
    # Wait for postgres pool initialization
    await asyncio.sleep(2)
    
    # Check if knowledge router is available
    if not hasattr(bot_core, 'knowledge_router') or not bot_core.knowledge_router:
        logger.error("❌ Knowledge router not initialized - cannot test")
        return
    
    logger.info("✅ Knowledge router available")
    
    # Create message processor
    processor = MessageProcessor(
        bot_core=bot_core,
        memory_manager=bot_core.memory_manager,
        llm_client=bot_core.llm_client
    )
    
    # Test cases
    test_messages = [
        "I love pizza!",
        "I really enjoy hiking",
        "I hate mushrooms",
        "My favorite drink is coffee"
    ]
    
    test_user_id = "test_user_123"
    
    for message in test_messages:
        logger.info(f"\n📝 Testing message: '{message}'")
        
        # Create message context
        context = MessageContext(
            user_id=test_user_id,
            content=message,
            platform="test",
            channel_id="test_channel"
        )
        
        # Test entity extraction
        extracted = processor._extract_entity_from_content(message.lower(), "love", "food")
        logger.info(f"   Extracted entity: {extracted}")
        
        # Test full knowledge extraction
        ai_components = {'emotion_data': {'primary_emotion': 'happy'}}
        result = await processor._extract_and_store_knowledge(context, ai_components)
        logger.info(f"   Knowledge stored: {result}")
    
    # Query stored facts
    logger.info("\n📊 Querying stored facts...")
    
    try:
        from src.knowledge.semantic_router import QueryIntent, IntentAnalysisResult
        
        intent = IntentAnalysisResult(
            intent_type=QueryIntent.FACTUAL_RECALL,
            entity_type="food",
            relationship_type="likes",
            confidence=0.9
        )
        
        facts = await bot_core.knowledge_router.get_user_facts(
            user_id=test_user_id,
            intent=intent,
            limit=10
        )
        
        logger.info(f"\n✅ Retrieved {len(facts)} facts:")
        for fact in facts:
            logger.info(f"   - {fact['entity_name']} ({fact['entity_type']}): "
                       f"{fact['relationship_type']} (confidence: {fact['confidence']})")
    
    except Exception as e:
        logger.error(f"❌ Error querying facts: {e}")
    
    logger.info("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_knowledge_extraction())
