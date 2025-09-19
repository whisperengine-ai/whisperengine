"""
Comprehensive tests for Memory Importance Engine persistence functionality.

Tests the Sprint 2 implementation of user-specific memory importance pattern learning
and persistence capabilities.
"""

import asyncio
import json
import os
import pytest
import pytest_asyncio
from datetime import datetime, timezone as tz
from unittest.mock import AsyncMock, MagicMock, patch

# Import the classes to test
from src.memory.memory_importance_engine import (
    MemoryImportanceEngine,
    MemoryImportanceScore,
    ImportanceFactors,
    ImportanceFactor,
)


class TestMemoryImportancePersistence:
    """Test suite for memory importance persistence functionality"""

    @pytest_asyncio.fixture
    async def engine(self):
        """Create a MemoryImportanceEngine instance for testing"""
        engine = MemoryImportanceEngine()
        # Mock the persistence initialization to avoid real database calls
        engine._persistence_initialized = True
        return engine

    @pytest.fixture
    def sample_memory_data(self):
        """Sample memory data for testing"""
        return {
            "content": "I'm really excited about my new job at the tech company!",
            "metadata": {
                "emotional_context": {
                    "primary_emotion": "excitement",
                    "emotion_intensity": 0.8,
                },
                "timestamp": datetime.now(tz.utc).isoformat(),
                "source": "chat",
            },
        }

    @pytest.fixture
    def sample_user_patterns(self):
        """Sample user importance patterns for testing"""
        return [
            {
                "pattern_type": "emotional_trigger",
                "pattern_name": "excitement_work",
                "importance_multiplier": 1.5,
                "confidence_score": 0.8,
                "pattern_keywords": ["excited", "job", "work"],
                "emotional_associations": ["excitement"],
                "frequency_count": 5,
            },
            {
                "pattern_type": "topic_interest", 
                "pattern_name": "technology_career",
                "importance_multiplier": 1.3,
                "confidence_score": 0.7,
                "pattern_keywords": ["tech", "technology", "company"],
                "emotional_associations": [],
                "frequency_count": 3,
            },
        ]

    @pytest.mark.asyncio
    async def test_database_initialization(self, engine):
        """Test database tables are properly initialized"""
        # Mock the database connection and cursor
        mock_cursor = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        
        with patch.object(engine, '_get_db_connection', return_value=mock_connection):
            await engine.initialize_persistence()
            
        # Verify tables were created
        assert mock_cursor.execute.call_count >= 5  # 5 tables should be created
        mock_connection.commit.assert_called()

    @pytest.mark.asyncio
    async def test_save_user_memory_statistics(self, engine):
        """Test saving user memory statistics"""
        user_id = "test_user_123"
        stats = {
            "total_memories": 100,
            "high_importance_count": 25,
            "emotional_intensity_weight": 0.35,
            "personal_relevance_weight": 0.30,
        }
        
        # Mock database operations
        mock_cursor = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        
        with patch.object(engine, '_get_db_connection', return_value=mock_connection):
            await engine.save_user_memory_statistics(user_id, stats)
            
        # Verify the insert/update query was executed
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()
        
        # Check that the query contains the expected user_id
        call_args = mock_cursor.execute.call_args
        assert user_id in str(call_args)

    @pytest.mark.asyncio
    async def test_load_user_memory_statistics(self, engine):
        """Test loading user memory statistics"""
        user_id = "test_user_123"
        expected_stats = {
            "total_memories": 100,
            "high_importance_count": 25,
            "emotional_intensity_weight": 0.35,
            "personal_relevance_weight": 0.30,
        }
        
        # Mock database response
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = [json.dumps(expected_stats)]
        mock_connection = AsyncMock()
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        
        with patch.object(engine, '_get_db_connection', return_value=mock_connection):
            result = await engine.load_user_memory_statistics(user_id)
            
        assert result == expected_stats
        mock_cursor.execute.assert_called()

    @pytest.mark.asyncio
    async def test_save_importance_pattern(self, engine):
        """Test saving user importance patterns"""
        user_id = "test_user_123"
        pattern_type = "emotional_trigger"
        pattern_data = {
            "pattern_name": "excitement_work",
            "importance_multiplier": 1.5,
            "confidence_score": 0.8,
            "pattern_keywords": ["excited", "job", "work"],
        }
        
        # Mock database operations
        mock_cursor = AsyncMock()
        mock_connection = AsyncMock()
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        
        with patch.object(engine, '_get_db_connection', return_value=mock_connection):
            await engine.save_importance_pattern(user_id, pattern_type, pattern_data)
            
        # Verify the insert/update query was executed
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()

    @pytest.mark.asyncio
    async def test_load_user_importance_patterns(self, engine, sample_user_patterns):
        """Test loading user importance patterns"""
        user_id = "test_user_123"
        
        # Mock database response
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            (pattern["pattern_type"], json.dumps(pattern))
            for pattern in sample_user_patterns
        ]
        mock_connection = AsyncMock()
        mock_connection.cursor.return_value.__aenter__.return_value = mock_connection
        
        with patch.object(engine, '_get_db_connection', return_value=mock_connection):
            result = await engine.load_user_importance_patterns(user_id)
            
        assert len(result) == 2
        assert result[0]["pattern_name"] == "excitement_work"
        assert result[1]["pattern_name"] == "technology_career"

    @pytest.mark.asyncio
    async def test_update_user_importance_weights(self, engine):
        """Test updating user importance weights"""
        user_id = "test_user_123"
        weight_adjustments = {
            "emotional_intensity_weight": 0.05,
            "personal_relevance_weight": -0.02,
        }
        
        # Mock existing statistics
        existing_stats = {
            "emotional_intensity_weight": 0.30,
            "personal_relevance_weight": 0.25,
        }
        
        with patch.object(engine, 'load_user_memory_statistics', return_value=existing_stats), \
             patch.object(engine, 'save_user_memory_statistics') as mock_save:
            
            await engine.update_user_importance_weights(user_id, weight_adjustments)
            
            # Verify the updated weights were saved
            mock_save.assert_called_once()
            saved_stats = mock_save.call_args[0][1]
            assert saved_stats["emotional_intensity_weight"] == 0.35  # 0.30 + 0.05
            assert saved_stats["personal_relevance_weight"] == 0.23  # 0.25 - 0.02

    @pytest.mark.asyncio
    async def test_calculate_memory_importance_with_patterns(
        self, engine, sample_memory_data, sample_user_patterns
    ):
        """Test enhanced importance calculation with learned patterns"""
        user_id = "test_user_123"
        memory_id = "memory_456"
        user_history = []
        
        # Mock the dependencies
        with patch.object(engine, 'load_user_importance_patterns', return_value=sample_user_patterns), \
             patch.object(engine, 'load_user_memory_statistics', return_value=None), \
             patch.object(engine, 'calculate_memory_importance') as mock_base_calc, \
             patch.object(engine, '_update_pattern_learning') as mock_update:
            
            # Mock base calculation result
            base_score = MemoryImportanceScore(
                memory_id=memory_id,
                user_id=user_id,
                overall_score=0.65,
                factor_scores=ImportanceFactors(
                    emotional_intensity=0.7,
                    personal_relevance=0.6,
                    recency=0.8,
                    access_frequency=0.1,
                    uniqueness=0.5,
                    relationship_milestone=0.0,
                ),
                calculation_timestamp=datetime.now(tz.utc),
                score_explanation="Base calculation",
                decay_rate=0.95,
                boost_events=[],
            )
            mock_base_calc.return_value = base_score
            
            # Calculate enhanced importance
            result = await engine.calculate_memory_importance_with_patterns(
                memory_id, user_id, sample_memory_data, user_history
            )
            
            # Verify the result
            assert isinstance(result, MemoryImportanceScore)
            assert result.memory_id == memory_id
            assert result.user_id == user_id
            assert result.overall_score >= base_score.overall_score  # Should be enhanced
            assert "pattern_learning_applied" in result.boost_events
            
            # Verify pattern learning was updated
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_pattern_boost_application(self, engine, sample_user_patterns):
        """Test pattern boost calculation"""
        memory_data = {
            "content": "I'm really excited about my new job at the tech company!",
            "metadata": {},
        }
        
        boosts = await engine._apply_pattern_boosts(memory_data, sample_user_patterns)
        
        # Should have emotional and personal multipliers > 1.0 due to matching keywords
        assert boosts["emotional_multiplier"] > 1.0
        assert boosts["personal_multiplier"] > 1.0
        assert boosts["total_boost"] > 0.0

    @pytest.mark.asyncio
    async def test_pattern_learning_updates(self, engine, sample_memory_data):
        """Test that patterns are learned from high-importance memories"""
        user_id = "test_user_123"
        high_importance_score = 0.85
        
        with patch.object(engine, '_learn_emotional_pattern') as mock_emotional, \
             patch.object(engine, '_learn_topic_pattern') as mock_topic:
            
            await engine._update_pattern_learning(
                user_id, sample_memory_data, high_importance_score
            )
            
            # Should learn emotional patterns for high importance
            mock_emotional.assert_called_once()
            # Should learn topic patterns
            assert mock_topic.call_count > 0

    @pytest.mark.asyncio
    async def test_emotional_pattern_learning(self, engine):
        """Test emotional pattern learning"""
        user_id = "test_user_123"
        content = "I'm so excited about this amazing opportunity!"
        emotional_context = {
            "primary_emotion": "excitement",
            "emotion_intensity": 0.9,
        }
        importance_score = 0.8
        
        with patch.object(engine, 'save_importance_pattern') as mock_save:
            await engine._learn_emotional_pattern(
                user_id, content, emotional_context, importance_score
            )
            
            # Verify pattern was saved
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args[0][0] == user_id  # user_id
            assert call_args[0][1] == "emotional_trigger"  # pattern_type
            pattern_data = call_args[0][2]
            assert "excitement" in pattern_data["emotional_associations"]

    @pytest.mark.asyncio
    async def test_topic_pattern_learning(self, engine):
        """Test topic pattern learning"""
        user_id = "test_user_123"
        topic = "technology"
        importance_score = 0.75
        
        with patch.object(engine, 'save_importance_pattern') as mock_save:
            await engine._learn_topic_pattern(user_id, topic, importance_score)
            
            # Verify pattern was saved
            mock_save.assert_called_once()
            call_args = mock_save.call_args
            assert call_args[0][0] == user_id  # user_id
            assert call_args[0][1] == "topic_interest"  # pattern_type
            pattern_data = call_args[0][2]
            assert topic in pattern_data["pattern_keywords"]

    def test_topic_extraction(self, engine):
        """Test topic extraction from content"""
        content = "I love programming and working on new software projects at my job"
        topics = engine._extract_topics_from_content(content)
        
        assert "technology" in topics
        assert "work" in topics
        assert len(topics) <= 3  # Should limit to top 3

    def test_emotional_keyword_extraction(self, engine):
        """Test emotional keyword extraction"""
        content = "I'm really excited and happy about this but also a bit worried"
        keywords = engine._extract_emotional_keywords(content)
        
        assert "excited" in keywords
        assert "happy" in keywords
        assert "worried" in keywords
        assert len(keywords) <= 5  # Should limit to top 5

    @pytest.mark.asyncio
    async def test_lazy_persistence_initialization(self, engine):
        """Test that persistence is initialized lazily"""
        engine._persistence_initialized = False
        
        with patch.object(engine, 'initialize_persistence') as mock_init:
            await engine.ensure_persistence_initialized()
            mock_init.assert_called_once()
            assert engine._persistence_initialized is True
            
            # Second call should not initialize again
            await engine.ensure_persistence_initialized()
            assert mock_init.call_count == 1

    @pytest.mark.asyncio
    async def test_database_connection_error_handling(self, engine):
        """Test handling of database connection errors"""
        user_id = "test_user_123"
        
        # Mock database connection failure
        with patch.object(engine, '_get_db_connection', side_effect=Exception("Connection failed")):
            # Should not raise exception, should handle gracefully
            result = await engine.load_user_memory_statistics(user_id)
            assert result is None

    @pytest.mark.asyncio 
    async def test_json_parsing_error_handling(self, engine):
        """Test handling of JSON parsing errors in pattern data"""
        user_id = "test_user_123"
        
        # Mock database response with invalid JSON
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            ("emotional_trigger", "invalid_json_data"),
        ]
        mock_connection = AsyncMock()
        mock_connection.cursor.return_value.__aenter__.return_value = mock_cursor
        
        with patch.object(engine, '_get_db_connection', return_value=mock_connection):
            result = await engine.load_user_importance_patterns(user_id)
            
        # Should return empty list when JSON parsing fails
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])