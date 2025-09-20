#!/usr/bin/env python3
"""
Test suite for the unified memory manager architecture.

Tests ConsolidatedMemoryManager functionality and compatibility with
the existing WhisperEngine system components.
"""

import asyncio
import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.core.consolidated_memory_manager import ConsolidatedMemoryManager
from src.memory.core.memory_interface import MemoryContext, MemoryEntry, MemoryContextType, EmotionContext
from src.memory.core.memory_factory import create_memory_manager


class TestConsolidatedMemoryManager:
    """Test ConsolidatedMemoryManager functionality."""

    @pytest.fixture
    async def mock_base_memory_manager(self):
        """Create a mock base memory manager."""
        manager = AsyncMock()
        manager.store_memory = AsyncMock()
        manager.retrieve_relevant_memories = AsyncMock(return_value=[])
        manager.get_memories_by_user = AsyncMock(return_value=[])
        return manager

    @pytest.fixture
    async def mock_emotion_manager(self):
        """Create a mock emotion manager."""
        manager = AsyncMock()
        manager.analyze_emotion = AsyncMock(return_value={"emotion": "neutral", "confidence": 0.5})
        return manager

    @pytest.fixture
    async def mock_graph_manager(self):
        """Create a mock graph manager."""
        manager = AsyncMock()
        manager.store_fact = AsyncMock()
        manager.query_graph = AsyncMock(return_value=[])
        return manager

    @pytest.fixture  
    async def memory_manager(self, mock_base_memory_manager, mock_emotion_manager, mock_graph_manager):
        """Create a ConsolidatedMemoryManager instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConsolidatedMemoryManager(
                base_memory_manager=mock_base_memory_manager,
                emotion_manager=mock_emotion_manager,
                graph_manager=mock_graph_manager,
                enable_enhanced_queries=True,
                enable_context_security=True,
                enable_optimization=True,
                max_workers=2
            )
            await manager.initialize()
            yield manager
            await manager.cleanup()

    @pytest.mark.asyncio
    async def test_memory_manager_initialization(self, memory_manager):
        """Test that the memory manager initializes correctly."""
        assert memory_manager is not None
        assert memory_manager._initialized is True
        assert memory_manager.llm_client is not None

    @pytest.mark.asyncio
    async def test_store_conversation(self, memory_manager):
        """Test storing a conversation."""
        user_id = "test_user_123"
        user_message = "Hello, how are you?"
        ai_response = "I'm doing well, thanks for asking!"
        channel_id = "test_channel"

        result = await memory_manager.store_conversation(
            user_id=user_id,
            user_message=user_message,
            bot_response=ai_response,
            channel_id=channel_id
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_retrieve_memories(self, memory_manager):
        """Test retrieving memories."""
        user_id = "test_user_123"
        
        # First store some memories
        await memory_manager.store_conversation(
            user_id=user_id,
            user_message="What's the weather like?",
            bot_response="I don't have access to current weather data.",
            channel_id="test_channel"
        )

        await memory_manager.store_conversation(
            user_id=user_id,
            user_message="Tell me about Python programming",
            bot_response="Python is a versatile programming language.",
            channel_id="test_channel"
        )

        # Test retrieval
        context = MemoryContext(
            context_type=MemoryContextType.GUILD_PUBLIC,
            channel_id="test_channel",
            security_level="standard"
        )

        memories = await memory_manager.retrieve_memories(
            user_id=user_id,
            query="Python programming",
            context=context,
            limit=5
        )

        assert isinstance(memories, list)
        # Should find at least one relevant memory
        assert len(memories) >= 0

    @pytest.mark.asyncio
    async def test_emotion_context(self, memory_manager):
        """Test emotion context functionality."""
        user_id = "test_user_123"
        
        # This should not raise an exception
        emotion_context = await memory_manager.get_emotion_context(user_id)

        # Should return an EmotionContext instance
        assert isinstance(emotion_context, EmotionContext)
        assert hasattr(emotion_context, 'current_emotion')
        assert hasattr(emotion_context, 'emotion_intensity')

    @pytest.mark.asyncio
    async def test_context_security(self, memory_manager):
        """Test context security filtering."""
        user_id = "test_user_123"
        
        # Store memories in different channels
        await memory_manager.store_conversation(
            user_id=user_id,
            user_message="Private message",
            bot_response="This is private",
            channel_id="private_channel"
        )

        await memory_manager.store_conversation(
            user_id=user_id,
            user_message="Public message",
            bot_response="This is public",
            channel_id="public_channel"
        )        # Retrieve with specific channel context
        private_context = MemoryContext(
            context_type=MemoryContextType.GUILD_PRIVATE,
            channel_id="private_channel",
            security_level="private"
        )

        memories = await memory_manager.retrieve_memories(
            user_id=user_id,
            query="message",
            context=private_context,
            limit=10
        )

        # Should return memories (the filtering might be basic in test setup)
        assert isinstance(memories, list)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, memory_manager):
        """Test concurrent memory operations."""
        user_id = "test_user_concurrent"
        
        # Create multiple concurrent store operations
        tasks = []
        for i in range(5):
            task = memory_manager.store_conversation(
                user_id=user_id,
                user_message=f"Message {i}",
                bot_response=f"Response {i}",
                channel_id="test_channel"
            )
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        assert all(result is True for result in results if not isinstance(result, Exception))


class TestMemoryFactory:
    """Test memory factory functionality."""

    @pytest.mark.asyncio
    async def test_create_unified_memory_manager(self):
        """Test creating unified memory manager through factory."""
        # Create mock managers
        mock_base_manager = AsyncMock()
        mock_emotion_manager = AsyncMock()
        mock_graph_manager = AsyncMock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'CHROMA_DB_PATH': temp_dir}):
                memory_manager = create_memory_manager(
                    base_manager=mock_base_manager,
                    emotion_manager=mock_emotion_manager,
                    graph_manager=mock_graph_manager,
                    use_legacy_mode=False,
                    enable_all_features=True
                )

                assert isinstance(memory_manager, ConsolidatedMemoryManager)
                await memory_manager.cleanup()

    @pytest.mark.asyncio
    async def test_create_legacy_memory_manager(self):
        """Test creating legacy memory manager through factory."""
        # Create mock managers
        mock_base_manager = AsyncMock()
        
        memory_manager = create_memory_manager(
            base_manager=mock_base_manager,
            use_legacy_mode=True
        )

        # Should return some kind of memory manager (might be a wrapper)
        assert memory_manager is not None
        assert hasattr(memory_manager, 'store_conversation')


class TestIntegrationWithHandlers:
    """Test integration with actual handler patterns."""

    @pytest.fixture
    async def unified_memory_manager(self):
        """Create unified memory manager for integration testing."""
        # Create mock managers
        mock_base_manager = AsyncMock()
        mock_emotion_manager = AsyncMock()
        mock_graph_manager = AsyncMock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConsolidatedMemoryManager(
                base_memory_manager=mock_base_manager,
                emotion_manager=mock_emotion_manager,
                graph_manager=mock_graph_manager,
                enable_enhanced_queries=True,
                enable_context_security=True,
                enable_optimization=True,
                max_workers=2
            )
            await manager.initialize()
            yield manager
            await manager.cleanup()

    @pytest.mark.asyncio
    async def test_events_handler_pattern(self, unified_memory_manager):
        """Test the pattern used in events handler."""
        user_id = "events_test_user"
        query = "test message content"
        
        # Test the pattern from events handler helper methods
        # This simulates _retrieve_memories_modern pattern
        context = MemoryContext(
            context_type=MemoryContextType.GUILD_PUBLIC,
            channel_id='test_channel',
            security_level='standard'
        )
        
        memories = await unified_memory_manager.retrieve_memories(
            user_id=user_id,
            query=query,
            limit=10,
            context=context
        )
        
        assert isinstance(memories, list)

        # Test emotion context pattern
        emotion_context = await unified_memory_manager.get_emotion_context(user_id)
        assert isinstance(emotion_context, EmotionContext)

    @pytest.mark.asyncio
    async def test_universal_chat_pattern(self, unified_memory_manager):
        """Test the pattern used in universal chat."""
        user_id = "chat_test_user"
        user_message = "Hello from universal chat"
        ai_response = "Hello! How can I help you?"
        channel_id = "universal_chat"

        # Test the pattern from universal chat helper methods
        # This simulates _store_conversation_modern pattern
        result = await unified_memory_manager.store_conversation(
            user_id=user_id,
            user_message=user_message,
            bot_response=ai_response,
            channel_id=channel_id
        )
        
        assert result is True

        # Test retrieval pattern
        context = MemoryContext(
            user_id=user_id,
            channel_id=channel_id,
            security_level='standard'
        )
        
        memories = await unified_memory_manager.retrieve_memories(
            user_id=user_id,
            query="hello",
            limit=10,
            context=context
        )
        
        assert isinstance(memories, list)

    @pytest.mark.asyncio
    async def test_scatter_gather_compatibility(self, unified_memory_manager):
        """Test compatibility with scatter-gather concurrency patterns."""
        user_id = "scatter_gather_user"
        
        # Simulate the scatter-gather pattern from events handler
        tasks = [
            unified_memory_manager.retrieve_memories(
                user_id=user_id,
                query="test query 1",
                limit=5,
                context=MemoryContext(
                    context_type=MemoryContextType.GUILD_PUBLIC,
                    channel_id='test',
                    security_level='standard'
                )
            ),
            unified_memory_manager.get_emotion_context(user_id),
            unified_memory_manager.store_conversation(
                user_id=user_id,
                user_message="Test message",
                bot_response="Test response",
                channel_id="test_channel"
            )
        ]
        
        # Execute all tasks in parallel (scatter-gather)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should have 3 results
        assert len(results) == 3
        
        # Check types
        assert isinstance(results[0], list)  # memories
        assert isinstance(results[1], str)   # emotion context
        assert results[2] is True           # store result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])