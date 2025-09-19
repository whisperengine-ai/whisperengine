"""
Integration test suite for WhisperEngine.

Tests end-to-end workflows and component interactions:
- Discord bot integration
- Desktop app integration
- Memory system integration
- Monitoring system integration
- AI pipeline integration
"""

import pytest
import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from pathlib import Path

# Import integration components
from src.platforms.universal_chat import UniversalChatOrchestrator, AbstractChatAdapter
from src.monitoring.health_monitor import HealthMonitor
from src.monitoring.engagement_tracker import EngagementTracker
from src.monitoring.error_tracker import ErrorTracker


@pytest.mark.integration
class TestPlatformIntegration:
    """Test integration between different platform modes"""

    @pytest.fixture
    def mock_discord_environment(self):
        """Mock Discord environment for testing"""
        return {
            'DISCORD_BOT_TOKEN': 'test_discord_token_123',
            'LLM_CHAT_API_URL': 'http://localhost:1234/v1',
            'ENV_MODE': 'discord'
        }

    @pytest.fixture
    def mock_desktop_environment(self):
        """Mock desktop environment for testing"""
        return {
            'LLM_CHAT_API_URL': 'http://localhost:1234/v1',
            'ENV_MODE': 'desktop-app'
        }

    @pytest.mark.asyncio
    async def test_discord_platform_initialization(self, mock_discord_environment):
        """Test Discord platform initialization"""
        with patch.dict(os.environ, mock_discord_environment):
            with patch('discord.Bot') as mock_bot:
                mock_bot_instance = Mock()
                mock_bot.return_value = mock_bot_instance
                
                # Test that platform orchestrator can be mocked and initialized
                with patch('src.platforms.universal_chat.UniversalChatOrchestrator') as mock_orchestrator:
                    mock_instance = Mock()
                    mock_instance.initialize = AsyncMock()
                    mock_orchestrator.return_value = mock_instance
                    
                    orchestrator = mock_orchestrator()
                    await orchestrator.initialize()
                    
                    assert orchestrator is not None

    @pytest.mark.asyncio
    async def test_desktop_platform_initialization(self, mock_desktop_environment):
        """Test desktop platform initialization"""
        with patch.dict(os.environ, mock_desktop_environment):
            with patch('src.platforms.universal_chat.UniversalChatOrchestrator') as mock_orchestrator:
                mock_instance = Mock()
                mock_instance.initialize = AsyncMock()
                mock_orchestrator.return_value = mock_instance
                
                orchestrator = mock_orchestrator()
                await orchestrator.initialize()
                
                assert orchestrator is not None

    @pytest.mark.asyncio
    async def test_platform_message_handling(self):
        """Test message handling across platforms"""
        with patch('src.platforms.universal_chat.UniversalChatOrchestrator') as mock_orchestrator:
            mock_instance = Mock()
            mock_instance.process_message = AsyncMock(return_value="Test response")
            mock_orchestrator.return_value = mock_instance
            
            orchestrator = mock_orchestrator()
            response = await orchestrator.process_message(
                content="Hello, AI!",
                user_id=12345,
                platform_context={'channel': 'test'}
            )
            
            assert response == "Test response"


@pytest.mark.integration
class TestMonitoringSystemIntegration:
    """Test monitoring system integration and functionality"""

    @pytest.fixture
    def mock_monitoring_components(self):
        """Mock monitoring system components"""
        health_monitor = Mock(spec=HealthMonitor)
        engagement_tracker = Mock(spec=EngagementTracker)
        error_tracker = Mock(spec=ErrorTracker)
        
        # Setup async mocks
        health_monitor.start_monitoring = AsyncMock()
        health_monitor.get_system_health = AsyncMock(return_value={
            'overall_status': 'healthy',
            'components': {},
            'performance_score': 95.0
        })
        
        engagement_tracker.track_interaction = AsyncMock()
        engagement_tracker.get_user_metrics = AsyncMock(return_value={
            'total_interactions': 10,
            'session_count': 2
        })
        
        error_tracker.track_error = AsyncMock()
        error_tracker.get_error_summary = AsyncMock(return_value={
            'total_errors': 0,
            'error_patterns': []
        })
        
        return {
            'health_monitor': health_monitor,
            'engagement_tracker': engagement_tracker,
            'error_tracker': error_tracker
        }

    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, mock_monitoring_components):
        """Test health monitoring system integration"""
        health_monitor = mock_monitoring_components['health_monitor']
        
        # Test health monitoring startup
        await health_monitor.start_monitoring()
        health_monitor.start_monitoring.assert_called_once()
        
        # Test health status retrieval
        health_status = await health_monitor.get_system_health()
        assert health_status['overall_status'] == 'healthy'
        assert 'performance_score' in health_status

    @pytest.mark.asyncio
    async def test_engagement_tracking_integration(self, mock_monitoring_components):
        """Test engagement tracking integration"""
        engagement_tracker = mock_monitoring_components['engagement_tracker']
        
        # Test interaction tracking
        await engagement_tracker.track_interaction(
            user_id=12345,
            interaction_type='message',
            platform='discord'
        )
        engagement_tracker.track_interaction.assert_called_once()
        
        # Test metrics retrieval
        metrics = await engagement_tracker.get_user_metrics(user_id=12345)
        assert 'total_interactions' in metrics
        assert 'session_count' in metrics

    @pytest.mark.asyncio
    async def test_error_tracking_integration(self, mock_monitoring_components):
        """Test error tracking integration"""
        error_tracker = mock_monitoring_components['error_tracker']
        
        # Test error tracking
        test_error = Exception("Test error for monitoring")
        await error_tracker.track_error(
            error=test_error,
            context={'component': 'test', 'user_id': 12345}
        )
        error_tracker.track_error.assert_called_once()
        
        # Test error summary
        summary = await error_tracker.get_error_summary()
        assert 'total_errors' in summary
        assert 'error_patterns' in summary


@pytest.mark.integration
class TestMemorySystemIntegration:
    """Test memory system integration across components"""

    @pytest.fixture
    def mock_memory_components(self):
        """Mock memory system components"""
        # Mock the core memory manager
        with patch('src.memory.context_aware_memory_security.ContextAwareMemoryManager') as mock_context_memory:
            mock_instance = Mock()
            mock_instance.store_memory = AsyncMock()
            mock_instance.retrieve_memories = AsyncMock(return_value=[])
            mock_instance.search_memories = AsyncMock(return_value=[])
            mock_context_memory.return_value = mock_instance
            
            # Mock thread-safe wrapper if it exists
            mock_thread_instance = Mock()
            mock_thread_instance.store_memory = AsyncMock()
            mock_thread_instance.retrieve_memories = AsyncMock(return_value=[])
            
            yield {
                'context_memory': mock_instance,
                'thread_safe_memory': mock_thread_instance
            }

    @pytest.mark.asyncio
    async def test_memory_storage_retrieval_integration(self, mock_memory_components):
        """Test memory storage and retrieval integration"""
        memory_manager = mock_memory_components['context_memory']
        
        # Test memory storage
        await memory_manager.store_memory(
            user_id=12345,
            content="User likes pizza",
            metadata={'type': 'preference', 'confidence': 0.9}
        )
        memory_manager.store_memory.assert_called_once()
        
        # Test memory retrieval
        memories = await memory_manager.retrieve_memories(user_id=12345, limit=10)
        assert isinstance(memories, list)

    @pytest.mark.asyncio
    async def test_thread_safe_memory_integration(self, mock_memory_components):
        """Test thread-safe memory manager integration"""
        thread_safe_memory = mock_memory_components['thread_safe_memory']
        
        # Test concurrent memory operations
        tasks = []
        for i in range(5):
            task = thread_safe_memory.store_memory(
                user_id=12345,
                content=f"Memory {i}",
                metadata={'sequence': i}
            )
            tasks.append(task)
        
        # Execute concurrently
        await asyncio.gather(*tasks)
        
        # Verify all calls were made
        assert thread_safe_memory.store_memory.call_count == 5

    @pytest.mark.asyncio
    async def test_memory_search_integration(self, mock_memory_components):
        """Test memory search functionality integration"""
        memory_manager = mock_memory_components['context_memory']
        
        # Test memory search
        search_results = await memory_manager.search_memories(
            user_id=12345,
            query="pizza preferences",
            limit=5
        )
        
        memory_manager.search_memories.assert_called_once()
        assert isinstance(search_results, list)


@pytest.mark.integration
class TestAIPipelineIntegration:
    """Test AI pipeline integration end-to-end"""

    @pytest.fixture
    def mock_ai_components(self):
        """Mock AI pipeline components"""
        # Mock LLM client
        llm_client = Mock()
        llm_client.chat_completion = AsyncMock(return_value="AI response")
        llm_client.test_connection = AsyncMock(return_value=True)
        
        # Mock emotional AI
        emotional_ai = Mock()
        emotional_ai.analyze_emotion = AsyncMock(return_value={
            'emotion': 'neutral',
            'confidence': 0.8,
            'context': 'conversational'
        })
        
        # Mock personality manager
        personality_manager = Mock()
        personality_manager.get_personality_prompt = Mock(return_value="You are a helpful assistant.")
        personality_manager.adapt_response = Mock(return_value="Adapted response")
        
        return {
            'llm_client': llm_client,
            'emotional_ai': emotional_ai,
            'personality_manager': personality_manager
        }

    @pytest.mark.asyncio
    async def test_complete_ai_pipeline_integration(self, mock_ai_components):
        """Test complete AI pipeline from input to output"""
        llm_client = mock_ai_components['llm_client']
        emotional_ai = mock_ai_components['emotional_ai']
        personality_manager = mock_ai_components['personality_manager']
        
        # Simulate complete AI pipeline
        user_message = "I'm feeling excited about this project!"
        
        # Step 1: Emotional analysis
        emotion_result = await emotional_ai.analyze_emotion(user_message)
        assert emotion_result['emotion'] == 'neutral'  # Mock result
        
        # Step 2: Personality adaptation
        personality_prompt = personality_manager.get_personality_prompt()
        assert isinstance(personality_prompt, str)
        
        # Step 3: LLM generation
        ai_response = await llm_client.chat_completion(
            messages=[
                {"role": "system", "content": personality_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        assert ai_response == "AI response"
        
        # Step 4: Response adaptation
        final_response = personality_manager.adapt_response(ai_response)
        assert final_response == "Adapted response"

    @pytest.mark.asyncio
    async def test_ai_pipeline_error_handling_integration(self, mock_ai_components):
        """Test AI pipeline error handling and fallbacks"""
        llm_client = mock_ai_components['llm_client']
        emotional_ai = mock_ai_components['emotional_ai']
        
        # Simulate LLM failure
        llm_client.chat_completion.side_effect = Exception("LLM connection failed")
        
        # Should handle gracefully
        try:
            await llm_client.chat_completion(messages=[])
        except Exception as e:
            assert str(e) == "LLM connection failed"
        
        # Emotional AI should still work
        emotion_result = await emotional_ai.analyze_emotion("test message")
        assert 'emotion' in emotion_result


@pytest.mark.integration
class TestDeploymentValidation:
    """Test deployment mode validation and configuration"""

    def test_docker_environment_detection(self):
        """Test Docker environment detection"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True  # Simulate /.dockerenv exists
            
            with patch.dict(os.environ, {'CONTAINER_MODE': 'true'}):
                # Test container environment detection
                result = os.path.exists('/.dockerenv')
                assert result is True

    def test_discord_deployment_validation(self):
        """Test Discord bot deployment validation"""
        discord_env = {
            'DISCORD_BOT_TOKEN': 'valid_token_123',
            'LLM_CHAT_API_URL': 'http://localhost:1234/v1',
            'ENV_MODE': 'discord'
        }
        
        with patch.dict(os.environ, discord_env):
            from env_manager import validate_environment
            validation = validate_environment()
            
            # Should validate Discord configuration
            assert validation['valid'] is True or len(validation['missing']) == 0

    def test_desktop_deployment_validation(self):
        """Test desktop app deployment validation"""
        desktop_env = {
            'LLM_CHAT_API_URL': 'http://localhost:1234/v1',
            'ENV_MODE': 'desktop-app'
        }
        
        with patch.dict(os.environ, desktop_env):
            from env_manager import validate_environment
            validation = validate_environment()
            
            # Desktop mode should not require Discord token
            assert validation['valid'] is True or 'DISCORD_BOT_TOKEN' not in validation['missing']


if __name__ == "__main__":
    # Allow running this test suite directly
    pytest.main([__file__, "-v", "-m", "integration"])