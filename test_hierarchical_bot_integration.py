#!/usr/bin/env python3
"""
Test Hierarchical Memory Integration with Discord Bot Core
"""

import asyncio
import os
import sys
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_hierarchical_memory_only():
    """Test just the hierarchical memory components without Discord"""
    
    logger.info("🧪 Testing Hierarchical Memory System Standalone")
    
    try:
        # Load environment
        from env_manager import load_environment
        load_environment()
        
        # Import hierarchical memory directly
        from src.memory.core.storage_abstraction import HierarchicalMemoryManager
        
        logger.info("✅ HierarchicalMemoryManager imported successfully")
        
        # Build configuration
        hierarchical_config = {
            'redis': {
                'url': f"redis://{os.getenv('HIERARCHICAL_REDIS_HOST', 'localhost')}:{os.getenv('HIERARCHICAL_REDIS_PORT', '6379')}",
                'ttl': int(os.getenv('HIERARCHICAL_REDIS_TTL', '1800'))
            },
            'postgresql': {
                'url': f"postgresql://{os.getenv('HIERARCHICAL_POSTGRESQL_USERNAME', 'bot_user')}:{os.getenv('HIERARCHICAL_POSTGRESQL_PASSWORD', 'securepassword123')}@{os.getenv('HIERARCHICAL_POSTGRESQL_HOST', 'localhost')}:{os.getenv('HIERARCHICAL_POSTGRESQL_PORT', '5432')}/{os.getenv('HIERARCHICAL_POSTGRESQL_DATABASE', 'whisper_engine')}"
            },
            'chromadb': {
                'host': os.getenv('HIERARCHICAL_CHROMADB_HOST', 'localhost'),
                'port': int(os.getenv('HIERARCHICAL_CHROMADB_PORT', '8000'))
            },
            'neo4j': {
                'uri': f"bolt://{os.getenv('HIERARCHICAL_NEO4J_HOST', 'localhost')}:{os.getenv('HIERARCHICAL_NEO4J_PORT', '7687')}",
                'username': os.getenv('HIERARCHICAL_NEO4J_USERNAME', 'neo4j'),
                'password': os.getenv('HIERARCHICAL_NEO4J_PASSWORD', 'neo4j_password_change_me'),
                'database': os.getenv('HIERARCHICAL_NEO4J_DATABASE', 'neo4j')
            },
            'redis_enabled': os.getenv('HIERARCHICAL_REDIS_ENABLED', 'true').lower() == 'true',
            'postgresql_enabled': os.getenv('HIERARCHICAL_POSTGRESQL_ENABLED', 'true').lower() == 'true',
            'chromadb_enabled': os.getenv('HIERARCHICAL_CHROMADB_ENABLED', 'true').lower() == 'true',
            'neo4j_enabled': os.getenv('HIERARCHICAL_NEO4J_ENABLED', 'true').lower() == 'true'
        }
        
        # Initialize hierarchical memory manager
        hierarchical_memory_manager = HierarchicalMemoryManager(hierarchical_config)
        logger.info("✅ HierarchicalMemoryManager created")
        
        # Initialize connections
        logger.info("🔄 Initializing storage connections...")
        await hierarchical_memory_manager.initialize()
        logger.info("✅ Hierarchical memory initialized successfully")
        
        # Test context assembly
        logger.info("🧪 Testing context assembly...")
        context = await hierarchical_memory_manager.get_conversation_context("test_user_123", "test query")
        
        logger.info(f"✅ Context assembled successfully:")
        logger.info(f"  - Recent messages: {len(context.recent_messages)}")
        logger.info(f"  - Semantic summaries: {len(context.semantic_summaries)}")
        logger.info(f"  - Related topics: {len(context.related_topics)}")
        logger.info(f"  - Assembly time: {context.assembly_metadata.get('total_time_ms', 'N/A')}ms")
        
        # Test memory storage
        logger.info("🧪 Testing memory storage...")
        await hierarchical_memory_manager.store_conversation(
            user_id="test_user_123",
            user_message="Hello, this is a test message from bot integration",
            bot_response="Hello! I'm WhisperEngine with hierarchical memory working perfectly.",
            metadata={"integration_test": True, "test_timestamp": "2024"}
        )
        logger.info("✅ Memory storage test completed")
        
        # Test context assembly again to see if we stored it
        logger.info("🧪 Testing context assembly after storage...")
        context2 = await hierarchical_memory_manager.get_conversation_context("test_user_123", "integration test")
        logger.info(f"✅ Second context assembled:")
        logger.info(f"  - Recent messages: {len(context2.recent_messages)}")
        logger.info(f"  - Assembly time: {context2.assembly_metadata.get('total_time_ms', 'N/A')}ms")
        
        logger.info("🎉 HIERARCHICAL MEMORY SYSTEM FULLY OPERATIONAL!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Hierarchical memory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bot_memory_initialization():
    """Test memory initialization in bot context"""
    
    logger.info("\n🤖 Testing Bot Memory System Initialization")
    
    try:
        # Load environment
        from env_manager import load_environment
        load_environment()
        
        # Mock just the discord imports at module level
        import sys
        from unittest.mock import MagicMock
        
        # Create mock modules
        discord_mock = MagicMock()
        discord_mock.Client = MagicMock
        discord_mock.ext = MagicMock()
        discord_mock.ext.commands = MagicMock()
        discord_mock.ext.commands.Bot = MagicMock
        
        # Install mocks
        sys.modules['discord'] = discord_mock
        sys.modules['discord.ext'] = discord_mock.ext
        sys.modules['discord.ext.commands'] = discord_mock.ext.commands
        
        # Now import bot core
        from src.core.bot import DiscordBotCore
        
        logger.info("✅ DiscordBotCore imported with mocked Discord")
        
        # Create bot instance with memory system only
        bot_core = DiscordBotCore()
        logger.info("✅ Bot core instance created")
        
        # Test hierarchical memory detection
        enable_hierarchical = os.getenv("ENABLE_HIERARCHICAL_MEMORY", "false").lower() == "true"
        logger.info(f"📊 ENABLE_HIERARCHICAL_MEMORY: {enable_hierarchical}")
        
        # Initialize just the memory system 
        bot_core.initialize_memory_system()
        logger.info("✅ Memory system initialization completed")
        
        # Check what type of memory was initialized
        if hasattr(bot_core, '_hierarchical_memory_manager'):
            logger.info("🚀 HIERARCHICAL MEMORY MANAGER DETECTED!")
            logger.info(f"  Type: {type(bot_core._hierarchical_memory_manager)}")
            logger.info(f"  Needs async init: {getattr(bot_core, '_needs_hierarchical_init', False)}")
            
            # Test async initialization
            if getattr(bot_core, '_needs_hierarchical_init', False):
                logger.info("🔄 Running hierarchical memory async initialization...")
                await bot_core.initialize_hierarchical_memory()
                logger.info("✅ Hierarchical memory async initialization completed")
            
            return True
        else:
            logger.warning("⚠️ Standard memory system was initialized instead")
            logger.info(f"  Memory manager type: {type(getattr(bot_core, 'memory_manager', None))}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Bot memory initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    
    logger.info("🎯 HIERARCHICAL MEMORY WHISPERNENGINE INTEGRATION TESTS")
    logger.info("=" * 60)
    
    # Test 1: Direct hierarchical memory
    success1 = await test_hierarchical_memory_only()
    
    # Test 2: Bot integration
    success2 = await test_bot_memory_initialization()
    
    if success1 and success2:
        logger.info("\n🎉 ALL TESTS PASSED! HIERARCHICAL MEMORY INTEGRATION COMPLETE!")
        return True
    else:
        logger.error("\n❌ SOME TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 HIERARCHICAL MEMORY BOT INTEGRATION: SUCCESS!")
        sys.exit(0)
    else:
        print("\n❌ HIERARCHICAL MEMORY BOT INTEGRATION: FAILED!")
        sys.exit(1)