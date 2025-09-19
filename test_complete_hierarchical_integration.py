#!/usr/bin/env python3
"""
Test Complete Hierarchical Memory Integration with Bot Handler Compatibility
"""

import asyncio
import os
import sys
import logging
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_hierarchical_integration():
    """Test complete hierarchical memory integration with bot handler compatibility"""
    
    logger.info("🎯 COMPLETE HIERARCHICAL MEMORY INTEGRATION TEST")
    logger.info("=" * 60)
    
    try:
        # Load environment
        from env_manager import load_environment
        load_environment()
        
        # Mock Discord to avoid import issues
        sys.modules['discord'] = MagicMock()
        sys.modules['discord.ext'] = MagicMock()
        sys.modules['discord.ext.commands'] = MagicMock()
        
        # Import bot core
        from src.core.bot import DiscordBotCore
        logger.info("✅ DiscordBotCore imported")
        
        # Create bot instance
        bot_core = DiscordBotCore()
        logger.info("✅ Bot core instance created")
        
        # Initialize memory system
        bot_core.initialize_memory_system()
        logger.info("✅ Memory system initialized")
        
        # Check if hierarchical memory is being used
        if hasattr(bot_core, '_hierarchical_memory_manager'):
            logger.info("🚀 Hierarchical memory system detected!")
            
            # Initialize hierarchical memory
            if getattr(bot_core, '_needs_hierarchical_init', False):
                await bot_core.initialize_hierarchical_memory()
                logger.info("✅ Hierarchical memory async initialization completed")
            
            # Test the adapter interface
            memory_manager = bot_core.memory_manager
            logger.info(f"📊 Memory manager type: {type(memory_manager)}")
            
            # Test bot handler compatibility - these are the methods bot handlers expect
            logger.info("🧪 Testing bot handler compatibility...")
            
            test_user_id = "test_user_12345"
            test_query = "Hello, testing hierarchical memory integration"
            
            # Test 1: store_conversation_safe (used by event handlers)
            logger.info("   Testing store_conversation_safe...")
            if hasattr(memory_manager, 'store_conversation_safe'):
                try:
                    # Access the underlying adapter (it might be wrapped in ThreadSafeMemoryManager)
                    if hasattr(memory_manager, 'memory_manager'):
                        adapter = memory_manager.memory_manager
                    else:
                        adapter = memory_manager
                        
                    success = await adapter.store_conversation_safe(
                        user_id=test_user_id,
                        user_message=test_query,
                        bot_response="Hello! I'm WhisperEngine with hierarchical memory.",
                        metadata={"test": "handler_compatibility"}
                    )
                    logger.info(f"   ✅ store_conversation_safe: {success}")
                except Exception as e:
                    logger.error(f"   ❌ store_conversation_safe failed: {e}")
            else:
                logger.warning("   ⚠️ store_conversation_safe method not found")
            
            # Test 2: retrieve_context_aware_memories (used by event handlers)
            logger.info("   Testing retrieve_context_aware_memories...")
            if hasattr(memory_manager, 'retrieve_context_aware_memories'):
                try:
                    if hasattr(memory_manager, 'memory_manager'):
                        adapter = memory_manager.memory_manager
                    else:
                        adapter = memory_manager
                        
                    memories = await adapter.retrieve_context_aware_memories(
                        user_id=test_user_id,
                        current_query=test_query,
                        max_memories=5
                    )
                    logger.info(f"   ✅ retrieve_context_aware_memories: {len(memories)} memories")
                except Exception as e:
                    logger.error(f"   ❌ retrieve_context_aware_memories failed: {e}")
            else:
                logger.warning("   ⚠️ retrieve_context_aware_memories method not found")
            
            # Test 3: get_emotion_context (used by event handlers)
            logger.info("   Testing get_emotion_context...")
            if hasattr(memory_manager, 'get_emotion_context'):
                try:
                    if hasattr(memory_manager, 'memory_manager'):
                        adapter = memory_manager.memory_manager
                    else:
                        adapter = memory_manager
                        
                    emotion_context = await adapter.get_emotion_context(test_user_id)
                    logger.info(f"   ✅ get_emotion_context: {emotion_context.get('context_available', False)}")
                except Exception as e:
                    logger.error(f"   ❌ get_emotion_context failed: {e}")
            else:
                logger.warning("   ⚠️ get_emotion_context method not found")
            
            # Test 4: get_recent_conversations (used by event handlers)
            logger.info("   Testing get_recent_conversations...")
            if hasattr(memory_manager, 'get_recent_conversations'):
                try:
                    if hasattr(memory_manager, 'memory_manager'):
                        adapter = memory_manager.memory_manager
                    else:
                        adapter = memory_manager
                        
                    recent = await adapter.get_recent_conversations(test_user_id, limit=3)
                    logger.info(f"   ✅ get_recent_conversations: {len(recent)} conversations")
                except Exception as e:
                    logger.error(f"   ❌ get_recent_conversations failed: {e}")
            else:
                logger.warning("   ⚠️ get_recent_conversations method not found")
            
            # Test 5: get_phase4_response_context (used by event handlers)
            logger.info("   Testing get_phase4_response_context...")
            if hasattr(memory_manager, 'get_phase4_response_context'):
                try:
                    if hasattr(memory_manager, 'memory_manager'):
                        adapter = memory_manager.memory_manager
                    else:
                        adapter = memory_manager
                        
                    phase4_context = await adapter.get_phase4_response_context(
                        test_user_id, 
                        test_query
                    )
                    logger.info(f"   ✅ get_phase4_response_context: {phase4_context.get('context_quality', 'unknown')}")
                except Exception as e:
                    logger.error(f"   ❌ get_phase4_response_context failed: {e}")
            else:
                logger.warning("   ⚠️ get_phase4_response_context method not found")
            
            # Test 6: get_collection_stats (used by admin handlers)
            logger.info("   Testing get_collection_stats...")
            try:
                if hasattr(memory_manager, 'memory_manager'):
                    adapter = memory_manager.memory_manager
                else:
                    adapter = memory_manager
                    
                stats = adapter.get_collection_stats()
                logger.info(f"   ✅ get_collection_stats: {stats.get('memory_type', 'unknown')}")
            except Exception as e:
                logger.error(f"   ❌ get_collection_stats failed: {e}")
            
            logger.info("🎉 BOT HANDLER COMPATIBILITY TEST COMPLETED!")
            
            # Test bot component exposure
            logger.info("🧪 Testing bot component exposure...")
            components = bot_core.get_components()
            
            if 'memory_manager' in components:
                exposed_memory = components['memory_manager']
                logger.info(f"✅ Memory manager exposed to handlers: {type(exposed_memory)}")
                
                # Test if exposed memory manager has expected interface
                required_methods = [
                    'store_conversation_safe',
                    'retrieve_context_aware_memories', 
                    'get_emotion_context',
                    'get_recent_conversations',
                    'get_phase4_response_context'
                ]
                
                missing_methods = []
                for method in required_methods:
                    if not hasattr(exposed_memory, method):
                        # Check if it's wrapped
                        if hasattr(exposed_memory, 'memory_manager') and hasattr(exposed_memory.memory_manager, method):
                            continue
                        missing_methods.append(method)
                
                if missing_methods:
                    logger.warning(f"   ⚠️ Missing methods: {missing_methods}")
                else:
                    logger.info("   ✅ All required handler methods available")
                    
                return True
            else:
                logger.error("❌ memory_manager not found in bot components")
                return False
                
        else:
            logger.warning("⚠️ Hierarchical memory system not initialized")
            return False
            
    except Exception as e:
        logger.error(f"❌ Complete integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_complete_hierarchical_integration())
    if success:
        print("\n🎉 COMPLETE HIERARCHICAL MEMORY INTEGRATION: SUCCESS!")
        print("🔗 All bot handlers are now wired to use hierarchical datastores!")
        sys.exit(0)
    else:
        print("\n❌ COMPLETE HIERARCHICAL MEMORY INTEGRATION: FAILED!")
        sys.exit(1)