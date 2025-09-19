"""
Sprint 3 Task 3.2: Emotional-Memory Integration Test

Tests the emotional-memory bridge that connects Sprint 1 emotional 
intelligence with Sprint 2 memory importance patterns to create 
enhanced memory scoring based on emotional context.
"""

import pytest
import asyncio
import logging
from datetime import datetime, timezone as tz
from unittest.mock import AsyncMock, MagicMock, patch

# Test imports
from src.utils.llm_enhanced_memory_manager import LLMEnhancedMemoryManager
from src.utils.emotional_memory_bridge import EmotionalMemoryBridge, EmotionalMemoryContext

# Mock imports for testing
try:
    from src.intelligence.emotional_intelligence import (
        PredictiveEmotionalIntelligence, 
        EmotionalIntelligenceAssessment
    )
    from src.memory.memory_importance_engine import MemoryImportanceEngine
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

logger = logging.getLogger(__name__)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Sprint 1-2 dependencies not available")
class TestSprint3Task32EmotionalMemoryIntegration:
    """Test Sprint 3 Task 3.2: Emotional-Memory Integration"""

    @pytest.fixture
    async def mock_emotional_assessment(self):
        """Create mock emotional intelligence assessment"""
        assessment = MagicMock()
        assessment.mood_assessment.category.value = "anxious"
        assessment.stress_assessment.level.value = "high"
        assessment.emotional_prediction.predicted_emotion = "worried"
        assessment.emotional_prediction.confidence = 0.85
        assessment.emotional_prediction.triggering_factors = ["work stress", "deadline pressure"]
        assessment.emotional_alerts = [
            MagicMock(
                alert_type=MagicMock(value="stress_alert"),
                priority=MagicMock(value="high"),
                message="High stress levels detected"
            )
        ]
        return assessment

    @pytest.fixture
    async def mock_memory_data(self):
        """Create mock memory data for testing"""
        return [
            {
                "id": "memory_1",
                "content": "I'm really worried about this project deadline tomorrow",
                "timestamp": datetime.now(tz.utc).isoformat(),
                "importance_score": 0.6,
                "user_id": "test_user_123"
            },
            {
                "id": "memory_2", 
                "content": "Had a great day at the beach with friends",
                "timestamp": datetime.now(tz.utc).isoformat(),
                "importance_score": 0.4,
                "user_id": "test_user_123"
            }
        ]

    @pytest.fixture
    async def emotional_memory_bridge(self, mock_emotional_assessment):
        """Create emotional-memory bridge with mocked dependencies"""
        # Mock emotional intelligence
        mock_emotional_intelligence = AsyncMock()
        mock_emotional_intelligence.comprehensive_emotional_assessment.return_value = mock_emotional_assessment
        
        # Mock memory importance engine
        mock_memory_engine = AsyncMock()
        mock_memory_engine.load_user_importance_patterns.return_value = [
            {
                "pattern_type": "emotional_trigger",
                "pattern_name": "work_stress_pattern",
                "emotional_associations": ["worried", "anxious"],
                "pattern_keywords": ["deadline", "project", "work"],
                "confidence_score": 0.8,
                "importance_multiplier": 1.4
            }
        ]
        mock_memory_engine.save_importance_pattern.return_value = None
        
        # Create bridge
        bridge = EmotionalMemoryBridge(
            emotional_intelligence=mock_emotional_intelligence,
            memory_importance_engine=mock_memory_engine
        )
        
        return bridge

    @pytest.mark.asyncio
    async def test_emotional_memory_context_creation(self, emotional_memory_bridge, mock_memory_data):
        """Test that emotional memory context is created correctly"""
        user_id = "test_user_123"
        memory = mock_memory_data[0]
        current_message = "I'm feeling really stressed about work"
        base_importance = 0.6
        
        # Test emotional context enhancement
        context = await emotional_memory_bridge.enhance_memory_with_emotional_context(
            user_id=user_id,
            memory_id=memory["id"],
            memory_data=memory,
            current_message=current_message,
            base_importance_score=base_importance
        )
        
        # Verify context structure
        assert isinstance(context, EmotionalMemoryContext)
        assert context.user_id == user_id
        assert context.memory_id == memory["id"]
        assert context.base_importance_score == base_importance
        assert context.enhancement_applied is True
        
        # Verify emotional data
        assert context.mood_category == "anxious"
        assert context.stress_level == "high"
        assert context.emotional_prediction["emotion"] == "worried"
        assert context.emotional_prediction["confidence"] == 0.85
        
        # Verify importance boost was applied
        assert context.final_importance_score > base_importance
        assert context.emotional_importance_boost > 0.0

    @pytest.mark.asyncio
    async def test_emotional_trigger_pattern_matching(self, emotional_memory_bridge, mock_memory_data):
        """Test that emotional trigger patterns are matched correctly"""
        user_id = "test_user_123"
        memory = mock_memory_data[0]  # Contains "deadline" and "project"
        current_message = "Worried about project deadline"
        
        context = await emotional_memory_bridge.enhance_memory_with_emotional_context(
            user_id=user_id,
            memory_id=memory["id"],
            memory_data=memory,
            current_message=current_message,
            base_importance_score=0.6
        )
        
        # Verify pattern matching
        assert context.emotional_trigger_match is True
        assert context.emotional_pattern_confidence > 0.7
        
        # Verify emotional boost was applied
        assert context.emotional_importance_boost > 0.0

    @pytest.mark.asyncio
    async def test_emotional_boost_calculation(self, emotional_memory_bridge, mock_memory_data):
        """Test that emotional boosts are calculated correctly"""
        user_id = "test_user_123"
        memory = mock_memory_data[0]
        current_message = "Extremely stressed about work emergency"
        
        context = await emotional_memory_bridge.enhance_memory_with_emotional_context(
            user_id=user_id,
            memory_id=memory["id"],
            memory_data=memory,
            current_message=current_message,
            base_importance_score=0.5
        )
        
        # High stress should trigger emotional boost
        assert context.emotional_importance_boost > 0.0
        assert context.final_importance_score > 0.5
        
        # Crisis alerts should add additional boost
        assert len(context.emotional_alerts) > 0
        high_priority_alert = any(
            alert["priority"] == "high" for alert in context.emotional_alerts
        )
        assert high_priority_alert

    @pytest.mark.asyncio
    async def test_pattern_learning_from_emotional_memories(self, emotional_memory_bridge):
        """Test that emotional patterns are learned from high-importance memories"""
        user_id = "test_user_123"
        memory_data = {
            "id": "memory_learning",
            "content": "Panic attack during presentation - need coping strategies",
            "user_id": user_id
        }
        current_message = "Having anxiety about public speaking"
        
        # Process memory with high emotional significance
        context = await emotional_memory_bridge.enhance_memory_with_emotional_context(
            user_id=user_id,
            memory_id=memory_data["id"],
            memory_data=memory_data,
            current_message=current_message,
            base_importance_score=0.8
        )
        
        # High importance should trigger pattern learning
        assert context.final_importance_score >= 0.8
        
        # Verify pattern learning was called
        bridge = emotional_memory_bridge
        bridge.memory_importance_engine.save_importance_pattern.assert_called()

    @pytest.mark.asyncio
    async def test_llm_memory_manager_integration(self, mock_memory_data, mock_emotional_assessment):
        """Test integration with LLMEnhancedMemoryManager"""
        # Mock base memory manager
        mock_base_manager = AsyncMock()
        mock_llm_client = AsyncMock()
        
        # Create LLM memory manager with mocked bridge
        with patch('src.utils.llm_enhanced_memory_manager.EmotionalMemoryBridge') as mock_bridge_class:
            # Setup mock bridge instance
            mock_bridge = AsyncMock()
            mock_bridge_class.return_value = mock_bridge
            
            # Mock emotional context response
            mock_emotional_context = EmotionalMemoryContext(
                memory_id="memory_1",
                user_id="test_user_123",
                content="test content",
                base_importance_score=0.6,
                mood_category="anxious",
                stress_level="high", 
                emotional_prediction={"emotion": "worried", "confidence": 0.85, "factors": []},
                emotional_alerts=[],
                emotional_importance_boost=0.3,
                emotional_trigger_match=True,
                emotional_pattern_confidence=0.8,
                final_importance_score=0.9,
                assessment_timestamp=datetime.now(tz.utc),
                enhancement_applied=True
            )
            mock_bridge.enhance_memory_with_emotional_context.return_value = mock_emotional_context
            
            # Create manager
            manager = LLMEnhancedMemoryManager(
                base_memory_manager=mock_base_manager,
                llm_client=mock_llm_client
            )
            
            # Manually set emotional bridge (simulating initialization)
            manager.emotional_memory_bridge = mock_bridge
            
            # Test emotional enhancement
            result = await manager.enhance_memories_with_emotional_intelligence(
                user_id="test_user_123",
                memories=mock_memory_data,
                current_message="Feeling stressed about work"
            )
            
            # Verify enhancement results
            assert len(result) == len(mock_memory_data)
            enhanced_memory = result[0]
            
            # Check emotional enhancement data was added
            assert "emotional_enhancement" in enhanced_memory
            enhancement = enhanced_memory["emotional_enhancement"]
            assert enhancement["base_score"] == 0.6
            assert enhancement["trigger_match"] is True
            assert enhancement["mood_category"] == "anxious"
            assert enhancement["enhancement_applied"] is True
            
            # Check final importance score was updated
            assert enhanced_memory["importance_score"] == 0.9

    @pytest.mark.asyncio
    async def test_emotional_memory_insights(self, emotional_memory_bridge):
        """Test emotional memory pattern insights"""
        user_id = "test_user_123"
        
        # Get insights about user's emotional patterns
        insights = await emotional_memory_bridge.get_emotional_memory_insights(user_id)
        
        # Verify insights structure
        assert "total_emotional_patterns" in insights
        assert "dominant_emotions" in insights
        assert "emotional_triggers" in insights
        assert "emotional_memory_enhancement_active" in insights
        
        # Should have some patterns from the mock data
        assert insights["total_emotional_patterns"] > 0
        assert insights["emotional_memory_enhancement_active"] is True

    @pytest.mark.asyncio
    async def test_emotional_resolution_detection(self, emotional_memory_bridge):
        """Test detection of emotional resolution memories"""
        user_id = "test_user_123"
        
        # Memory showing emotional resolution
        resolution_memory = {
            "id": "resolution_memory",
            "content": "I feel much better now - found peace and clarity about the situation",
            "user_id": user_id
        }
        
        # Message indicating emotional improvement
        current_message = "I've learned to cope better and feel hopeful"
        
        # Mock assessment to show positive emotional state
        mock_assessment = MagicMock()
        mock_assessment.mood_assessment.category.value = "peaceful"
        mock_assessment.stress_assessment.level.value = "low"
        mock_assessment.emotional_prediction.predicted_emotion = "hopeful"
        mock_assessment.emotional_prediction.confidence = 0.9
        mock_assessment.emotional_alerts = []
        
        # Update bridge's mock
        bridge = emotional_memory_bridge
        bridge.emotional_intelligence.comprehensive_emotional_assessment.return_value = mock_assessment
        
        context = await bridge.enhance_memory_with_emotional_context(
            user_id=user_id,
            memory_id=resolution_memory["id"],
            memory_data=resolution_memory,
            current_message=current_message,
            base_importance_score=0.5
        )
        
        # Resolution memories should get importance boost
        assert context.emotional_importance_boost > 0.0
        assert context.final_importance_score > 0.5

    @pytest.mark.asyncio
    async def test_error_handling_graceful_degradation(self, mock_memory_data):
        """Test graceful degradation when emotional intelligence fails"""
        # Create bridge with failing emotional intelligence
        mock_emotional_intelligence = AsyncMock()
        mock_emotional_intelligence.comprehensive_emotional_assessment.side_effect = Exception("API Error")
        
        mock_memory_engine = AsyncMock()
        bridge = EmotionalMemoryBridge(
            emotional_intelligence=mock_emotional_intelligence,
            memory_importance_engine=mock_memory_engine
        )
        
        # Should handle errors gracefully
        context = await bridge.enhance_memory_with_emotional_context(
            user_id="test_user_123",
            memory_id="memory_1",
            memory_data=mock_memory_data[0],
            current_message="test message",
            base_importance_score=0.6
        )
        
        # Should return basic context without enhancement
        assert context.enhancement_applied is False
        assert context.final_importance_score == 0.6  # No change from base score
        assert context.emotional_importance_boost == 0.0


if __name__ == "__main__":
    # Run emotional-memory integration tests
    pytest.main([__file__, "-v", "--tb=short"])