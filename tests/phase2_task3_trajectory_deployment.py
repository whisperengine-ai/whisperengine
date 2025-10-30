"""
Phase 2 Task 3: Production Deployment Test

Tests CDLTrajectoryIntegration deployment into ai_pipeline_vector_integration.py
for trajectory-aware emotional context in character responses.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta

# Import the integration
from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineIntegration
from src.prompts.cdl_trajectory_integration import CDLTrajectoryIntegration
from src.intelligence.trajectory_analyzer import TrajectoryAnalyzer


class TestTrajectoryDeployment:
    """Test trajectory integration deployment"""
    
    @pytest.fixture
    def mock_memory_system(self):
        """Create mock memory system"""
        mock = AsyncMock()
        mock.retrieve_relevant_memories = AsyncMock(return_value=[])
        mock.store_conversation = AsyncMock(return_value=True)
        return mock
    
    @pytest.fixture
    def pipeline_integration(self, mock_memory_system):
        """Create pipeline integration with trajectory support"""
        return VectorAIPipelineIntegration(
            vector_memory_system=mock_memory_system
        )
    
    def test_cdl_trajectory_integration_initialized(self, pipeline_integration):
        """Test that CDL trajectory integration is properly initialized"""
        assert pipeline_integration.cdl_trajectory_integration is not None
        assert isinstance(pipeline_integration.cdl_trajectory_integration, CDLTrajectoryIntegration)
    
    @pytest.mark.asyncio
    async def test_trajectory_context_retrieval(self, pipeline_integration):
        """Test trajectory context can be retrieved"""
        if pipeline_integration.cdl_trajectory_integration:
            # Create mock trajectory context
            trajectory_context = {
                'has_trajectory': True,
                'trajectory_summary': 'escalating emotional state',
                'trend_type': 'RISING_SHARP',
                'emotional_awareness': 'getting increasingly intense',
                'confidence': 0.85,
                'time_context': 'over the last 15 minutes',
                'injection_priority': 0.81,
                'trajectory_metadata': {}
            }
            
            # Verify formatting works
            formatted = pipeline_integration.cdl_trajectory_integration.format_for_cdl_prompt(
                trajectory_context,
                character_archetype='real-world'
            )
            
            assert formatted is not None
            assert len(formatted) > 0
            assert 'intense' in formatted.lower() or 'escalat' in formatted.lower()
    
    def test_injection_decision_logic(self, pipeline_integration):
        """Test injection decision logic filters low-quality data"""
        if pipeline_integration.cdl_trajectory_integration:
            # High quality data should be injected
            high_quality = {
                'has_trajectory': True,
                'confidence': 0.85,
                'injection_priority': 0.81,
                'trajectory_metadata': {'points_count': 10}
            }
            assert pipeline_integration.cdl_trajectory_integration.should_inject_trajectory_into_prompt(
                high_quality,
                prompt_word_count=500
            )
            
            # Low confidence data should be skipped
            low_confidence = {
                'has_trajectory': True,
                'confidence': 0.3,
                'injection_priority': 0.2,
                'trajectory_metadata': {'points_count': 1}
            }
            assert not pipeline_integration.cdl_trajectory_integration.should_inject_trajectory_into_prompt(
                low_confidence,
                prompt_word_count=500
            )
    
    def test_archetype_specific_formatting(self, pipeline_integration):
        """Test formatting adapts to character archetype"""
        if pipeline_integration.cdl_trajectory_integration:
            trajectory_context = {
                'has_trajectory': True,
                'emotional_awareness': 'getting increasingly frustrated',
                'time_context': 'over the past 20 minutes',
                'trend_type': 'RISING_SHARP',
                'confidence': 0.85,
                'injection_priority': 0.81,
                'trajectory_metadata': {}
            }
            
            # Real-world archetype
            real_world = pipeline_integration.cdl_trajectory_integration.format_for_cdl_prompt(
                trajectory_context,
                character_archetype='real-world'
            )
            assert '[Context Note:' in real_world or 'frustrated' in real_world.lower()
            
            # Fantasy archetype
            fantasy = pipeline_integration.cdl_trajectory_integration.format_for_cdl_prompt(
                trajectory_context,
                character_archetype='fantasy'
            )
            assert '[Emotional Context:' in fantasy or 'frustrated' in fantasy.lower()
            
            # Narrative AI archetype
            narrative = pipeline_integration.cdl_trajectory_integration.format_for_cdl_prompt(
                trajectory_context,
                character_archetype='narrative_ai'
            )
            assert '[Character Context:' in narrative or 'frustrated' in narrative.lower()


class TestElenaCharacterDeployment:
    """Test trajectory deployment specifically for Elena character"""
    
    @pytest.fixture
    def mock_elena_context(self):
        """Create mock Elena character context"""
        return {
            'character_name': 'Elena',
            'character_archetype': 'real-world',
            'bot_name': 'elena',
            'user_id': 'test_user_elena_001',
            'message': 'This is really frustrating me'
        }
    
    def test_elena_trajectory_injection(self, mock_elena_context):
        """Test trajectory injection for Elena marine biologist character"""
        # Simulated trajectory for Elena interaction
        trajectory_context = {
            'has_trajectory': True,
            'trajectory_summary': 'user becoming increasingly frustrated over 18 minutes',
            'trend_type': 'RISING_SHARP',
            'emotional_awareness': 'noticeably more frustrated',
            'confidence': 0.82,
            'time_context': 'over the last 18 minutes',
            'injection_priority': 0.79,
            'trajectory_metadata': {
                'points_count': 8,
                'magnitude': 0.68,
                'variance': 0.12
            }
        }
        
        # Elena would get real-world formatting with marine biology context
        integration = CDLTrajectoryIntegration()
        formatted = integration.format_for_cdl_prompt(
            trajectory_context,
            character_archetype='real-world'
        )
        
        assert formatted is not None
        assert len(formatted) > 0
        # Elena would understand user's frustration in scientific context
        assert 'frustrated' in formatted.lower() or 'frustrat' in formatted.lower()


class TestDeploymentIntegration:
    """Integration tests for production deployment"""
    
    @pytest.mark.asyncio
    async def test_deployment_fallback_behavior(self):
        """Test graceful fallback when trajectory data unavailable"""
        mock_memory = AsyncMock()
        pipeline = VectorAIPipelineIntegration(
            vector_memory_system=mock_memory
        )
        
        # Simulate empty trajectory data
        empty_context = {
            'has_trajectory': False,
            'trajectory_summary': None,
            'trend_type': None,
            'emotional_awareness': None,
            'confidence': 0.0,
            'time_context': None,
            'injection_priority': 0.0,
            'trajectory_metadata': {}
        }
        
        # Should not inject when no data available
        if pipeline.cdl_trajectory_integration:
            should_inject = pipeline.cdl_trajectory_integration.should_inject_trajectory_into_prompt(
                empty_context,
                prompt_word_count=500
            )
            assert not should_inject
    
    def test_production_deployment_readiness(self):
        """Verify system is ready for production deployment"""
        # Check Phase 2 Task 2 code availability
        try:
            from src.prompts.cdl_trajectory_integration import CDLTrajectoryIntegration
            from src.intelligence.trajectory_analyzer import TrajectoryAnalyzer
            
            # Create instance
            integration = CDLTrajectoryIntegration()
            
            # Verify all methods are callable
            assert callable(integration.get_trajectory_context_for_cdl)
            assert callable(integration.format_for_cdl_prompt)
            assert callable(integration.should_inject_trajectory_into_prompt)
            
            # Verify integration with ai_pipeline_vector_integration
            from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineIntegration
            mock_memory = AsyncMock()
            pipeline = VectorAIPipelineIntegration(vector_memory_system=mock_memory)
            
            assert pipeline.cdl_trajectory_integration is not None
            
            print("✅ Production deployment ready: All components initialized")
            
        except ImportError as e:
            pytest.fail(f"Deployment import failed: {e}")


if __name__ == '__main__':
    # Run basic deployment tests
    print("🚀 Phase 2 Task 3: Production Deployment Tests\n")
    pytest.main([__file__, '-v', '--tb=short'])
