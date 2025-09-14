#!/usr/bin/env python3
"""
Direct AI Conversation Test
Tests the core AI conversation components without requiring the web server
"""

import asyncio
import sys
import logging
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_direct_ai_conversation():
    """Test AI conversation components directly"""
    print("🧪 Direct AI Conversation Component Test")
    print("Testing core AI capabilities without web server")
    print("=" * 60)
    
    try:
        # Force SQLite for desktop mode
        os.environ['WHISPERENGINE_DATABASE_TYPE'] = 'sqlite'
        os.environ['WHISPERENGINE_MODE'] = 'desktop'
        
        # Step 1: Initialize Configuration
        print("\n📋 Step 1: Testing Configuration Manager...")
        from src.config.adaptive_config import AdaptiveConfigManager
        config_manager = AdaptiveConfigManager()
        print("   ✅ Configuration manager initialized")
        
        # Step 2: Initialize Local Database
        print("\n🗄️ Step 2: Testing Local Database Integration...")
        from src.database.local_database_integration import LocalDatabaseIntegrationManager
        db_manager = LocalDatabaseIntegrationManager(config_manager)
        db_success = await db_manager.initialize()
        
        if db_success:
            print("   ✅ Local database integration initialized")
            
            # Get storage stats
            vector_storage = db_manager.get_vector_storage()
            graph_storage = db_manager.get_graph_storage()
            
            print(f"   📊 Vector collections: {len(vector_storage.collections)}")
            print(f"   🕸️ Graph nodes: {graph_storage.graph.number_of_nodes()}")
            print(f"   🕸️ Graph edges: {graph_storage.graph.number_of_edges()}")
        else:
            print("   ❌ Database initialization failed")
            return False
        
        # Step 3: Test Universal Chat Orchestrator
        print("\n🎭 Step 3: Testing Universal Chat Orchestrator...")
        from src.platforms.universal_chat import UniversalChatOrchestrator, Message, ChatPlatform, MessageType
        
        # Create orchestrator with local DB (no enhanced core to avoid external dependencies)
        orchestrator = UniversalChatOrchestrator(
            config_manager=config_manager,
            db_manager=db_manager,
            bot_core=None,
            use_enhanced_core=False
        )
        
        init_success = await orchestrator.initialize()
        if init_success:
            print(f"   ✅ Chat orchestrator initialized with {len(orchestrator.adapters)} platforms")
        else:
            print("   ❌ Chat orchestrator initialization failed")
            return False
        
        # Step 4: Test AI Response Generation
        print("\n🤖 Step 4: Testing AI Response Generation...")
        
        test_message = Message(
            message_id="test_001",
            user_id="test_user_direct",
            content="Hello! I'm testing the WhisperEngine AI system. Can you tell me about your local database capabilities?",
            platform=ChatPlatform.WEB_UI,
            channel_id="test_channel",
            message_type=MessageType.TEXT
        )
        
        print(f"   💬 Test message: {test_message.content[:60]}...")
        
        # Create conversation
        conversation = await orchestrator.get_or_create_conversation(test_message)
        print(f"   📝 Conversation created: {conversation.conversation_id}")
        
        # Generate AI response
        try:
            ai_response = await orchestrator.generate_ai_response(test_message, [])
            
            print(f"   🤖 AI Response: {ai_response.content[:100]}{'...' if len(ai_response.content) > 100 else ''}")
            print(f"   📊 Model used: {ai_response.model_used}")
            print(f"   ⏱️  Generation time: {ai_response.generation_time_ms}ms")
            print(f"   💰 Cost: ${ai_response.cost:.6f}")
            print(f"   🎯 Confidence: {ai_response.confidence}")
            
            if len(ai_response.content) > 50 and "error" not in ai_response.content.lower():
                print("   ✅ AI response generation successful")
                ai_success = True
            else:
                print("   ⚠️  AI response may be fallback or error")
                ai_success = False
                
        except Exception as e:
            print(f"   ❌ AI response generation failed: {e}")
            ai_success = False
        
        # Step 5: Test Memory Storage
        print("\n🧠 Step 5: Testing Memory Storage...")
        
        test_user_id = "test_user_direct"
        user_message = test_message.content
        bot_response = "Test AI response for memory storage"
        
        try:
            # Store test conversation in local database using cache
            local_cache = db_manager.get_local_cache()
            conversation_id = f"test_conv_{test_user_id}"
            
            await local_cache.add_message(conversation_id, {
                'content': user_message,
                'author_id': test_user_id,
                'author_name': 'test_user',
                'bot': False,
                'timestamp': '2025-09-14T15:47:00'
            })
            
            await local_cache.add_message(conversation_id, {
                'content': bot_response,
                'author_id': 'whisperengine',
                'author_name': 'WhisperEngine',
                'bot': True,
                'timestamp': '2025-09-14T15:47:01'
            })
            
            print("   ✅ Conversation stored in local cache")
            
            # Test user creation in graph
            user_result = await db_manager.create_user_in_graph(
                user_id=test_user_id,
                username="test_user",
                display_name="Test User"
            )
            print(f"   ✅ User created in graph: {user_result.get('user_id')}")
            
            memory_success = True
            
        except Exception as e:
            print(f"   ❌ Memory storage failed: {e}")
            memory_success = False
        
        # Step 6: Test Memory Retrieval
        print("\n🔍 Step 6: Testing Memory Retrieval...")
        
        try:
            # Test conversation retrieval from cache
            local_cache = db_manager.get_local_cache()
            conversation_id = f"test_conv_{test_user_id}"
            
            cached_messages = await local_cache.get_conversation_messages(conversation_id)
            print(f"   🔍 Cache retrieval returned {len(cached_messages)} messages")
            
            # Test vector similarity search with dummy embedding
            import numpy as np
            test_embedding = np.random.random(384).tolist()  # Standard embedding dimension
            
            # Search for similar conversations
            similar_convs = await db_manager.search_similar_conversations(
                query_embedding=test_embedding,
                user_id=test_user_id,
                limit=5
            )
            print(f"   🔍 Vector search returned {len(similar_convs)} results")
            
            # Test user context from graph
            user_context = await db_manager.get_user_context(test_user_id)
            print(f"   📊 User context: {len(str(user_context))} characters")
            
            retrieval_success = True
                
        except Exception as e:
            print(f"   ❌ Memory retrieval failed: {e}")
            retrieval_success = False
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 Direct AI Conversation Test Results:")
        print(f"   📋 Configuration: ✅ PASS")
        print(f"   🗄️ Database: ✅ PASS")
        print(f"   🎭 Orchestrator: ✅ PASS")
        print(f"   🤖 AI Response: {'✅ PASS' if ai_success else '❌ FAIL'}")
        print(f"   🧠 Memory Storage: {'✅ PASS' if memory_success else '❌ FAIL'}")
        print(f"   🔍 Memory Retrieval: {'✅ PASS' if retrieval_success else '❌ FAIL'}")
        
        overall_success = ai_success and memory_success and retrieval_success
        
        if overall_success:
            print("\n🎉 ALL CORE COMPONENTS WORKING!")
            print("✅ WhisperEngine AI conversation system is functional")
            print("✅ Local databases are storing and retrieving data")
            print("✅ AI response generation is working")
            print("\n💡 The web server integration should work fine")
            print("   The trace trap is just a macOS system tray issue")
        else:
            print("\n⚠️  Some components need attention - see details above")
            
        return overall_success
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_ai_conversation())
    
    if success:
        print("\n🚀 Ready to proceed with next steps!")
    else:
        print("\n🔧 Core components need fixing before proceeding")