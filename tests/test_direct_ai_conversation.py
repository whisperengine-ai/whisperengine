#!/usr/bin/env python3
"""
Direct AI Conversation Test
Tests the core AI conversation components without requiring the web server
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_direct_ai_conversation():
    """Test AI conversation components directly"""

    try:
        # Force SQLite for desktop mode
        os.environ["WHISPERENGINE_DATABASE_TYPE"] = "sqlite"
        os.environ["WHISPERENGINE_MODE"] = "desktop"

        # Step 1: Initialize Configuration
        from src.config.adaptive_config import AdaptiveConfigManager

        config_manager = AdaptiveConfigManager()

        # Step 2: Initialize Local Database
        from src.database.local_database_integration import LocalDatabaseIntegrationManager

        db_manager = LocalDatabaseIntegrationManager(config_manager)
        db_success = await db_manager.initialize()

        if db_success:

            # Get storage stats
            db_manager.get_vector_storage()
            db_manager.get_graph_storage()

        else:
            return False

        # Step 3: Test Universal Chat Orchestrator
        from src.platforms.universal_chat import (
            ChatPlatform,
            Message,
            MessageType,
            UniversalChatOrchestrator,
        )

        # Create orchestrator with local DB (no enhanced core to avoid external dependencies)
        orchestrator = UniversalChatOrchestrator(
            config_manager=config_manager,
            db_manager=db_manager,
            bot_core=None,
            use_enhanced_core=False,
        )

        init_success = await orchestrator.initialize()
        if init_success:
            pass
        else:
            return False

        # Step 4: Test AI Response Generation

        test_message = Message(
            message_id="test_001",
            user_id="test_user_direct",
            content="Hello! I'm testing the WhisperEngine AI system. Can you tell me about your local database capabilities?",
            platform=ChatPlatform.WEB_UI,
            channel_id="test_channel",
            message_type=MessageType.TEXT,
        )

        # Create conversation
        await orchestrator.get_or_create_conversation(test_message)

        # Generate AI response
        try:
            ai_response = await orchestrator.generate_ai_response(test_message, [])

            if len(ai_response.content) > 50 and "error" not in ai_response.content.lower():
                ai_success = True
            else:
                ai_success = False

        except Exception:
            ai_success = False

        # Step 5: Test Memory Storage

        test_user_id = "test_user_direct"
        user_message = test_message.content
        bot_response = "Test AI response for memory storage"

        try:
            # Store test conversation in local database using cache
            local_cache = db_manager.get_local_cache()
            conversation_id = f"test_conv_{test_user_id}"

            await local_cache.add_message(
                conversation_id,
                {
                    "content": user_message,
                    "author_id": test_user_id,
                    "author_name": "test_user",
                    "bot": False,
                    "timestamp": "2025-09-14T15:47:00",
                },
            )

            await local_cache.add_message(
                conversation_id,
                {
                    "content": bot_response,
                    "author_id": "whisperengine",
                    "author_name": "WhisperEngine",
                    "bot": True,
                    "timestamp": "2025-09-14T15:47:01",
                },
            )

            # Test user creation in graph
            await db_manager.create_user_in_graph(
                user_id=test_user_id, username="test_user", display_name="Test User"
            )

            memory_success = True

        except Exception:
            memory_success = False

        # Step 6: Test Memory Retrieval

        try:
            # Test conversation retrieval from cache
            local_cache = db_manager.get_local_cache()
            conversation_id = f"test_conv_{test_user_id}"

            await local_cache.get_conversation_messages(conversation_id)

            # Test vector similarity search with dummy embedding
            import numpy as np

            test_embedding = np.random.random(384).tolist()  # Standard embedding dimension

            # Search for similar conversations
            await db_manager.search_similar_conversations(
                query_embedding=test_embedding, user_id=test_user_id, limit=5
            )

            # Test user context from graph
            await db_manager.get_user_context(test_user_id)

            retrieval_success = True

        except Exception:
            retrieval_success = False

        # Summary

        overall_success = ai_success and memory_success and retrieval_success

        if overall_success:
            pass
        else:
            pass

        return overall_success

    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_direct_ai_conversation())

    if success:
        pass
    else:
        pass
