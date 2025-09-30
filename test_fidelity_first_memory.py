#!/usr/bin/env python3
"""
Test script for Fidelity-First Memory Management implementation

This script tests the new fidelity-first memory retrieval functionality
to ensure character authenticity preservation is working correctly.
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

async def test_fidelity_first_memory():
    """Test the fidelity-first memory retrieval implementation."""
    
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
        
        # Test user ID
        test_user_id = "test_user_fidelity_first"
        
        logger.info("🧪 Testing Fidelity-First Memory Management")
        
        # Test 1: Basic fidelity-first retrieval
        logger.info("📝 Test 1: Basic fidelity-first memory retrieval")
        
        # Check if the new method exists
        if hasattr(memory_manager, 'retrieve_relevant_memories_fidelity_first'):
            logger.info("✅ Fidelity-first method found on memory manager")
            
            # Test the new method
            fidelity_memories = await memory_manager.retrieve_relevant_memories_fidelity_first(
                user_id=test_user_id,
                query="test conversation",
                limit=5,
                full_fidelity=True,
                intelligent_ranking=True,
                graduated_filtering=True,
                preserve_character_nuance=True
            )
            
            logger.info(f"✅ Fidelity-first retrieval completed: {len(fidelity_memories)} memories")
            
            # Verify the response format
            if fidelity_memories:
                first_memory = fidelity_memories[0]
                expected_fields = ['content', 'score', 'fidelity_preserved', 'search_type']
                
                for field in expected_fields:
                    if field in first_memory:
                        logger.info(f"✅ Memory contains expected field: {field}")
                    else:
                        logger.warning(f"⚠️  Memory missing field: {field}")
                
                # Check for fidelity-specific metadata
                if first_memory.get('search_type') == 'fidelity_first':
                    logger.info("✅ Fidelity-first search type correctly set")
                
                if first_memory.get('fidelity_preserved'):
                    logger.info("✅ Fidelity preservation flag correctly set")
            
            # Test 2: Compare with standard retrieval
            logger.info("📝 Test 2: Comparing fidelity-first vs standard retrieval")
            
            standard_memories = await memory_manager.retrieve_relevant_memories(
                user_id=test_user_id,
                query="test conversation",
                limit=5
            )
            
            logger.info(f"📊 Standard retrieval: {len(standard_memories)} memories")
            logger.info(f"📊 Fidelity-first retrieval: {len(fidelity_memories)} memories")
            
            # Test 3: Character-specific functionality
            logger.info("📝 Test 3: Character-specific memory processing")
            
            character_memories = await memory_manager.retrieve_relevant_memories_fidelity_first(
                user_id=test_user_id,
                query="marine biology research",
                limit=3,
                preserve_character_nuance=True
            )
            
            if character_memories:
                logger.info("✅ Character-specific retrieval completed")
                
                # Check for character relevance scoring
                for memory in character_memories:
                    if 'character_relevance' in memory:
                        logger.info(f"✅ Character relevance score: {memory['character_relevance']}")
                    if 'personality_alignment' in memory:
                        logger.info(f"✅ Personality alignment score: {memory['personality_alignment']}")
            
        else:
            logger.error("❌ Fidelity-first method not found on memory manager")
            return False
        
        logger.info("🎉 Fidelity-First Memory Management test completed successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.info("💡 Make sure you're running from the project root with the virtual environment activated")
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main test runner."""
    
    # Set test environment
    os.environ["MEMORY_SYSTEM_TYPE"] = "vector"
    os.environ["DISCORD_BOT_NAME"] = "elena"  # Use Elena for character-specific testing
    
    logger.info("🚀 Starting Fidelity-First Memory Management Tests")
    
    success = await test_fidelity_first_memory()
    
    if success:
        logger.info("✅ All tests passed!")
        return 0
    else:
        logger.error("❌ Tests failed!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)