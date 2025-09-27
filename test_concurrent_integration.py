#!/usr/bin/env python3
"""
Test script for ConcurrentConversationManager integration
"""
import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_concurrent_conversation_manager():
    """Test ConcurrentConversationManager integration with DiscordBotCore"""
    
    # Set test environment
    os.environ.update({
        'ENABLE_CONCURRENT_CONVERSATION_MANAGER': 'true',
        'MAX_CONCURRENT_SESSIONS': '10',
        'MAX_WORKER_THREADS': '2',
        'MAX_WORKER_PROCESSES': '1',
        'SESSION_TIMEOUT_MINUTES': '5',
    })
    
    try:
        # Test factory function
        logger.info("🔧 Testing factory function...")
        from src.conversation.concurrent_conversation_manager import create_concurrent_conversation_manager
        
        manager = await create_concurrent_conversation_manager(
            max_concurrent_sessions=5,
            max_workers_threads=2,
            max_workers_processes=1,
            session_timeout_minutes=2
        )
        
        logger.info("✅ ConcurrentConversationManager created via factory")
        
        # Test basic functionality
        logger.info("🔧 Testing basic conversation processing...")
        
        result = await manager.process_conversation_message(
            user_id="test_user_123",
            message="Hello! This is a test message.",
            channel_id="test_channel",
            priority="high"  # High priority for immediate processing
        )
        
        logger.info(f"✅ Conversation processed: {result.get('status')}")
        
        # Test performance stats
        stats = manager.get_performance_stats()
        logger.info(f"✅ Performance stats available: {list(stats.keys())}")
        
        # Cleanup
        logger.info("🧹 Cleaning up...")
        await manager.stop()
        logger.info("✅ Manager stopped cleanly")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bot_core_integration():
    """Test integration with DiscordBotCore"""
    
    # Set test environment
    os.environ.update({
        'ENABLE_CONCURRENT_CONVERSATION_MANAGER': 'true',
        'MAX_CONCURRENT_SESSIONS': '10',
    })
    
    try:
        from src.core.bot import DiscordBotCore
        
        logger.info("🔧 Testing DiscordBotCore integration...")
        
        # Create bot core instance
        bot_core = DiscordBotCore()
        
        # Test conversation manager initialization
        await bot_core.initialize_conversation_manager()
        
        if bot_core.conversation_manager:
            logger.info("✅ ConcurrentConversationManager initialized in bot core")
            
            # Test that it's accessible via get_components
            components = bot_core.get_components()
            if 'conversation_manager' in components:
                logger.info("✅ Conversation manager available in components")
            else:
                logger.warning("⚠️ Conversation manager not in components dict")
                
            # Cleanup
            await bot_core.conversation_manager.stop()
            logger.info("✅ Bot core conversation manager cleaned up")
            
        else:
            logger.error("❌ ConcurrentConversationManager not initialized")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot core integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all integration tests"""
    
    logger.info("🚀 Starting ConcurrentConversationManager Integration Tests")
    logger.info("=" * 60)
    
    # Test 1: Factory function and basic functionality
    logger.info("Test 1: Factory Function and Basic Functionality")
    test1_result = await test_concurrent_conversation_manager()
    
    # Test 2: Bot Core Integration
    logger.info("\nTest 2: DiscordBotCore Integration")
    test2_result = await test_bot_core_integration()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    if test1_result and test2_result:
        logger.info("✅ ALL TESTS PASSED - Integration successful!")
        logger.info("🎉 ConcurrentConversationManager is ready for production use")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED - Integration needs attention")
        if not test1_result:
            logger.error("   - Factory function test failed")
        if not test2_result:
            logger.error("   - Bot core integration test failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)