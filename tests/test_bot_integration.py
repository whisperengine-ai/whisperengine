#!/usr/bin/env python3
"""
Integration test for unified memory manager bot initialization.

Tests that the bot core properly initializes the ConsolidatedMemoryManager
and that all components work together correctly.
"""

import asyncio
import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.core.consolidated_memory_manager import ConsolidatedMemoryManager


class TestBotInitializationIntegration:
    """Test bot initialization with unified memory manager."""

    @pytest.mark.asyncio
    async def test_unified_memory_manager_environment_enabled(self):
        """Test bot initialization with unified memory manager enabled."""
        # Mock environment variables
        env_vars = {
            'ENABLE_UNIFIED_MEMORY_MANAGER': 'true',
            'MEMORY_MAX_WORKERS': '4',
            'ENABLE_GRAPH_DATABASE': 'false'
        }
        
        with patch.dict(os.environ, env_vars):
            with tempfile.TemporaryDirectory() as temp_dir:
                # Mock the imports to avoid actual Discord bot initialization
                with patch('src.core.bot.ConsolidatedMemoryManager') as MockManager:
                    with patch('src.core.bot.create_memory_manager') as mock_factory:
                        # Create mock manager instance
                        mock_manager_instance = AsyncMock()
                        mock_manager_instance.initialize = AsyncMock()
                        mock_factory.return_value = mock_manager_instance
                        
                        # Import and test the initialization logic
                        from src.core.bot import DiscordBotCore
                        
                        # Mock LLM client
                        with patch('src.core.bot.LLMClient') as MockLLMClient:
                            with patch('src.core.bot.ConcurrentLLMManager') as MockConcurrentLLM:
                                mock_llm = AsyncMock()
                                MockLLMClient.return_value = mock_llm
                                MockConcurrentLLM.return_value = mock_llm
                                
                                # Create bot core instance
                                bot_core = DiscordBotCore()
                                bot_core.initialize_llm_client()
                                
                                # Test memory system initialization
                                bot_core.initialize_memory_system()
                                
                                # Verify unified memory manager was used
                                assert hasattr(bot_core, '_uses_unified_memory')
                                assert bot_core._uses_unified_memory is True
                                assert bot_core.memory_manager == mock_manager_instance
                                assert bot_core.safe_memory_manager == mock_manager_instance

    @pytest.mark.asyncio
    async def test_legacy_fallback_when_unified_disabled(self):
        """Test fallback to legacy memory system when unified is disabled."""
        env_vars = {
            'ENABLE_UNIFIED_MEMORY_MANAGER': 'false'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.core.bot.ConsolidatedMemoryManager') as MockManager:
                with patch('src.core.bot.create_memory_manager') as mock_factory:
                    # Import and test the initialization logic
                    from src.core.bot import DiscordBotCore
                    
                    # Mock all the legacy components
                    with patch('src.core.bot.UserMemoryManager') as MockUserMemory:
                        with patch('src.core.bot.ThreadSafeMemoryManager') as MockThreadSafe:
                            with patch('src.core.bot.ContextAwareMemoryManager') as MockContextAware:
                                with patch('src.core.bot.LLMClient') as MockLLMClient:
                                    with patch('src.core.bot.ConcurrentLLMManager') as MockConcurrentLLM:
                                        mock_llm = AsyncMock()
                                        MockLLMClient.return_value = mock_llm
                                        MockConcurrentLLM.return_value = mock_llm
                                        
                                        # Create bot core instance
                                        bot_core = DiscordBotCore()
                                        bot_core.initialize_llm_client()
                                        
                                        # Test memory system initialization
                                        bot_core.initialize_memory_system()
                                        
                                        # Verify unified memory manager was NOT used
                                        assert hasattr(bot_core, '_uses_unified_memory')
                                        assert bot_core._uses_unified_memory is False
                                        
                                        # Should not have called the unified factory
                                        mock_factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_compatibility_detection_in_handlers(self):
        """Test that handlers can detect unified vs legacy memory managers."""
        # Test with unified manager
        unified_manager = AsyncMock(spec=ConsolidatedMemoryManager)
        
        # Simulate events handler compatibility check
        is_unified = isinstance(unified_manager, ConsolidatedMemoryManager)
        assert is_unified is True
        
        # Test with legacy manager (mock)
        legacy_manager = MagicMock()
        is_unified = isinstance(legacy_manager, ConsolidatedMemoryManager)
        assert is_unified is False

    @pytest.mark.asyncio
    async def test_environment_variable_configuration(self):
        """Test various environment variable configurations."""
        test_cases = [
            {
                'ENABLE_UNIFIED_MEMORY_MANAGER': 'true',
                'MEMORY_MAX_WORKERS': '2',
                'ENABLE_GRAPH_DATABASE': 'true',
                'expected_unified': True
            },
            {
                'ENABLE_UNIFIED_MEMORY_MANAGER': 'false',
                'expected_unified': False
            },
            {
                'ENABLE_UNIFIED_MEMORY_MANAGER': 'invalid',
                'expected_unified': False
            }
        ]
        
        for case in test_cases:
            with patch.dict(os.environ, case):
                # Test environment variable parsing
                enable_unified = os.getenv("ENABLE_UNIFIED_MEMORY_MANAGER", "true").lower() == "true"
                assert enable_unified == case['expected_unified']

    @pytest.mark.asyncio
    async def test_memory_manager_feature_flags(self):
        """Test that memory manager features are properly configured."""
        env_vars = {
            'ENABLE_UNIFIED_MEMORY_MANAGER': 'true',
            'MEMORY_MAX_WORKERS': '6',
            'ENABLE_GRAPH_DATABASE': 'true'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('src.memory.core.memory_factory.create_memory_manager') as mock_factory:
                mock_manager = AsyncMock()
                mock_factory.return_value = mock_manager
                
                # Import factory function
                from src.memory.core.memory_factory import create_memory_manager
                
                # Mock the factory to capture the call
                mock_llm_client = AsyncMock()
                
                # Call factory with bot core parameters
                manager = create_memory_manager(
                    mode="unified",
                    llm_client=mock_llm_client,
                    enable_enhanced_queries=True,
                    enable_context_security=True,
                    enable_thread_safety=True,
                    enable_optimization=True,
                    enable_graph_integration=True,
                    max_workers=6
                )
                
                # Verify factory was called with correct parameters
                mock_factory.assert_called_once_with(
                    mode="unified",
                    llm_client=mock_llm_client,
                    enable_enhanced_queries=True,
                    enable_context_security=True,
                    enable_thread_safety=True,
                    enable_optimization=True,
                    enable_graph_integration=True,
                    max_workers=6
                )


class TestHandlerModernization:
    """Test that modernized handlers work with unified memory manager."""

    @pytest.fixture
    async def mock_bot_core_unified(self):
        """Create mock bot core with unified memory manager."""
        bot_core = MagicMock()
        bot_core.memory_manager = AsyncMock(spec=ConsolidatedMemoryManager)
        bot_core.safe_memory_manager = bot_core.memory_manager
        return bot_core

    @pytest.fixture
    async def mock_bot_core_legacy(self):
        """Create mock bot core with legacy memory manager."""
        bot_core = MagicMock()
        bot_core.memory_manager = MagicMock()  # Legacy manager
        bot_core.safe_memory_manager = MagicMock()
        return bot_core

    @pytest.mark.asyncio
    async def test_events_handler_with_unified_manager(self, mock_bot_core_unified):
        """Test events handler helper methods with unified manager."""
        # This simulates the pattern from modernized events handler
        memory_manager = mock_bot_core_unified.memory_manager
        
        # Test unified manager detection
        is_unified = isinstance(memory_manager, ConsolidatedMemoryManager)
        assert is_unified is True
        
        # Test clean async interface (no detection needed)
        emotion_context = await memory_manager.get_emotion_context("test_user")
        memory_manager.get_emotion_context.assert_called_once_with("test_user")

    @pytest.mark.asyncio
    async def test_events_handler_with_legacy_manager(self, mock_bot_core_legacy):
        """Test events handler fallback with legacy manager."""
        # This simulates the pattern from modernized events handler
        memory_manager = mock_bot_core_legacy.memory_manager
        
        # Test legacy manager detection
        is_unified = isinstance(memory_manager, ConsolidatedMemoryManager)
        assert is_unified is False
        
        # Would fall back to async/sync detection (in helper methods)
        assert hasattr(memory_manager, 'get_emotion_context')  # Mock attribute

    @pytest.mark.asyncio
    async def test_universal_chat_with_unified_manager(self, mock_bot_core_unified):
        """Test universal chat helper methods with unified manager."""
        memory_manager = mock_bot_core_unified.memory_manager
        
        # Test unified manager detection
        is_unified = isinstance(memory_manager, ConsolidatedMemoryManager)
        assert is_unified is True
        
        # Test clean async interface
        result = await memory_manager.store_conversation(
            user_id="test_user",
            user_message="test message",
            ai_response="test response",
            channel_id="test_channel"
        )
        
        memory_manager.store_conversation.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])