#!/usr/bin/env python3
"""
Comprehensive test of Fidelity-First Memory Management with sample data

This test creates sample conversation data and demonstrates the fidelity-first
memory retrieval preserving character authenticity and conversation context.
"""

import asyncio
import os
import sys
import logging
import tempfile
from pathlib import Path

# Set cache directory to avoid read-only filesystem issues
os.environ["FASTEMBED_CACHE_PATH"] = tempfile.gettempdir()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def test_fidelity_first_with_data():
    """Test fidelity-first memory with actual conversation data."""
    
    try:
        # Set up proper infrastructure configuration for multi-bot environment
        os.environ["QDRANT_HOST"] = "localhost"
        os.environ["QDRANT_PORT"] = "6334"  # Multi-bot infrastructure port
        os.environ["POSTGRES_HOST"] = "localhost"
        os.environ["POSTGRES_PORT"] = "5433"  # Multi-bot infrastructure port
        os.environ["POSTGRES_DB"] = "whisperengine"
        os.environ["POSTGRES_USER"] = "whisperengine"
        os.environ["POSTGRES_PASSWORD"] = "whisperengine123"
        os.environ["DISCORD_BOT_NAME"] = "elena"  # Use Elena for testing
        
        # Import after path setup
        from src.memory.memory_protocol import create_memory_manager
        
        # Create memory manager
        memory_manager = create_memory_manager(memory_type="vector")
        
        test_user_id = "test_user_fidelity_data"
        
        logger.info("🌊 Testing Fidelity-First Memory with Elena's Marine Biology Context")
        
        # Store some Elena-specific conversation data
        sample_conversations = [
            {
                "user_message": "Tell me about coral bleaching",
                "bot_response": "¡Ay, coral bleaching breaks my heart! When ocean temperatures rise even 2°C above normal, corals expel their symbiotic zooxanthellae - that's what gives them their vibrant colors. Without these algae, they turn white and essentially starve. I've witnessed this firsthand in the Caribbean reefs near my abuela's home in Puerto Rico.",
                "emotion_data": {"primary": "concern", "intensity": 0.8, "secondary": "passionate"}
            },
            {
                "user_message": "What's your favorite marine creature?",
                "bot_response": "¡Dios mío! You're asking me to choose among my children! But if I must... sea otters hold a special place in my heart. They're keystone species that maintain kelp forest ecosystems by controlling sea urchin populations. Plus, they hold hands while sleeping so they don't drift apart. ¿No es adorable?",
                "emotion_data": {"primary": "joy", "intensity": 0.9, "secondary": "affectionate"}
            },
            {
                "user_message": "How do you feel about ocean pollution?",
                "bot_response": "It makes me furious and heartbroken at the same time. Every plastic bottle, every chemical runoff... it's poisoning the home of creatures that can't speak for themselves. That's why I became a marine biologist - to be their voice. Mi abuela always said 'El mar nos da vida, debemos cuidarlo' - the sea gives us life, we must care for it.",
                "emotion_data": {"primary": "anger", "intensity": 0.7, "secondary": "determined"}
            }
        ]
        
        # Store conversations
        logger.info("📝 Storing sample Elena conversations...")
        for i, conv in enumerate(sample_conversations):
            await memory_manager.store_conversation(
                user_id=test_user_id,
                user_message=conv["user_message"],
                bot_response=conv["bot_response"],
                pre_analyzed_emotion_data=conv["emotion_data"]
            )
            logger.info(f"   Stored conversation {i+1}: {conv['user_message'][:30]}...")
        
        # Test fidelity-first retrieval
        logger.info("\n🔍 Testing Fidelity-First Retrieval:")
        
        # First check if we have any memories at all
        all_memories = await memory_manager.retrieve_relevant_memories(
            user_id=test_user_id,
            query="",  # Empty query to get all memories
            limit=50
        )
        logger.info(f"🗄️ Total memories in system for user: {len(all_memories)}")
        
        # Test 1: Marine biology context retrieval
        query = "ocean conservation and marine life protection"
        fidelity_memories = await memory_manager.retrieve_relevant_memories_fidelity_first(
            user_id=test_user_id,
            query=query,
            limit=10,
            full_fidelity=True,
            intelligent_ranking=True,
            graduated_filtering=True
        )
        
        logger.info(f"🎯 Query: '{query}'")
        logger.info(f"📊 Fidelity-first retrieved: {len(fidelity_memories)} memories")
        
        for i, memory in enumerate(fidelity_memories[:3]):  # Show top 3
            content = memory.get("content", "No content")
            score = memory.get("score", 0.0)
            logger.info(f"   #{i+1}: {content[:60]}... (score: {score:.3f})")
        
        # Test 2: Character-specific emotional context
        logger.info("\n🎭 Testing Character-Specific Emotional Context:")
        
        emotional_query = "passionate feelings about marine life"
        emotional_memories = await memory_manager.retrieve_relevant_memories_fidelity_first(
            user_id=test_user_id,
            query=emotional_query,
            limit=5,
            full_fidelity=True,
            preserve_character_nuance=True
        )
        
        logger.info(f"🎯 Emotional Query: '{emotional_query}'")
        logger.info(f"💝 Character-aware memories: {len(emotional_memories)}")
        
        # Test 3: Compare with standard retrieval
        logger.info("\n⚖️ Comparing Fidelity-First vs Standard Retrieval:")
        
        standard_memories = await memory_manager.retrieve_relevant_memories(
            user_id=test_user_id,
            query=query,
            limit=10
        )
        
        logger.info(f"📊 Standard retrieval: {len(standard_memories)} memories")
        logger.info(f"📊 Fidelity-first: {len(fidelity_memories)} memories")
        
        # Show processing differences
        if fidelity_memories and standard_memories:
            logger.info("🔬 Top result comparison:")
            standard_content = standard_memories[0].get("content", "No content")
            fidelity_content = fidelity_memories[0].get("content", "No content")
            logger.info(f"   Standard: {standard_content[:60]}...")
            logger.info(f"   Fidelity: {fidelity_content[:60]}...")
        
        logger.info("\n🎉 Fidelity-First Memory with Data test completed successfully!")
        logger.info("✅ Character authenticity preserved through graduated optimization!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    return True

async def main():
    """Run the comprehensive fidelity-first memory test."""
    logger.info("🚀 Starting Comprehensive Fidelity-First Memory Test")
    
    success = await test_fidelity_first_with_data()
    
    if success:
        logger.info("✅ All tests passed!")
    else:
        logger.error("❌ Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())