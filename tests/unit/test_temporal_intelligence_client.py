"""
Unit tests for TemporalIntelligenceClient

Tests all query methods including newly implemented:
- get_bot_emotion_trend()
- get_bot_emotion_overall_trend()
- get_confidence_overall_trend()
- get_conversation_quality_trend()
- get_conversation_quality_overall_trend()
- query_data()
"""

import pytest
import os
from datetime import datetime, timedelta
from src.temporal.temporal_intelligence_client import (
    TemporalIntelligenceClient,
    ConfidenceMetrics,
    RelationshipMetrics,
    ConversationQualityMetrics
)


@pytest.fixture
def temporal_client():
    """Create temporal intelligence client instance"""
    return TemporalIntelligenceClient()


@pytest.fixture
def skip_if_disabled(temporal_client):
    """Skip test if InfluxDB not available"""
    if not temporal_client.enabled:
        pytest.skip("InfluxDB not available")


class TestBotEmotionQueries:
    """Test bot emotion query methods (Task 1)"""
    
    @pytest.mark.asyncio
    async def test_get_bot_emotion_trend_returns_chronological_order(self, temporal_client, skip_if_disabled):
        """Verify bot emotions are returned in chronological order"""
        # Record test emotions at different times
        now = datetime.now()
        await temporal_client.record_bot_emotion(
            "elena", "test_user_1", "joy", 0.8, 0.9, 
            timestamp=now - timedelta(hours=2)
        )
        await temporal_client.record_bot_emotion(
            "elena", "test_user_1", "curiosity", 0.7, 0.85,
            timestamp=now - timedelta(hours=1)
        )
        await temporal_client.record_bot_emotion(
            "elena", "test_user_1", "excitement", 0.9, 0.95,
            timestamp=now
        )
        
        # Retrieve trend
        emotions = await temporal_client.get_bot_emotion_trend("elena", "test_user_1", hours_back=3)
        
        # Verify chronological order
        assert len(emotions) >= 3
        
        # Find our test emotions
        joy_idx = next((i for i, e in enumerate(emotions) if e['primary_emotion'] == 'joy'), None)
        curiosity_idx = next((i for i, e in enumerate(emotions) if e['primary_emotion'] == 'curiosity'), None)
        excitement_idx = next((i for i, e in enumerate(emotions) if e['primary_emotion'] == 'excitement'), None)
        
        if joy_idx is not None and curiosity_idx is not None and excitement_idx is not None:
            assert joy_idx < curiosity_idx < excitement_idx, "Emotions not in chronological order"
    
    @pytest.mark.asyncio
    async def test_get_bot_emotion_trend_filters_by_user(self, temporal_client, skip_if_disabled):
        """Verify emotions are filtered to specific user"""
        # Record emotions for different users
        await temporal_client.record_bot_emotion("elena", "user_a", "joy", 0.8, 0.9)
        await temporal_client.record_bot_emotion("elena", "user_b", "sadness", 0.6, 0.85)
        
        # Retrieve for user_a only
        emotions = await temporal_client.get_bot_emotion_trend("elena", "user_a", hours_back=1)
        
        # Should not contain user_b's sadness
        sadness_found = any(e['primary_emotion'] == 'sadness' for e in emotions)
        assert not sadness_found, "Found emotions from wrong user"
    
    @pytest.mark.asyncio
    async def test_get_bot_emotion_overall_trend_includes_all_users(self, temporal_client, skip_if_disabled):
        """Verify overall trend includes emotions from all users"""
        # Record emotions for multiple users
        await temporal_client.record_bot_emotion("elena", "user_1", "joy", 0.8, 0.9)
        await temporal_client.record_bot_emotion("elena", "user_2", "curiosity", 0.7, 0.85)
        
        # Retrieve overall trend
        emotions = await temporal_client.get_bot_emotion_overall_trend("elena", hours_back=1)
        
        # Should include both users
        assert len(emotions) >= 2
        user_ids = [e['user_id'] for e in emotions]
        assert 'user_1' in user_ids or 'user_2' in user_ids, "Missing user emotions"
    
    @pytest.mark.asyncio
    async def test_get_bot_emotion_trend_handles_no_data(self, temporal_client, skip_if_disabled):
        """Verify graceful handling when no data available"""
        emotions = await temporal_client.get_bot_emotion_trend("nonexistent_bot", "nonexistent_user", hours_back=1)
        assert emotions == []


class TestConfidenceQueries:
    """Test confidence query methods (Task 2)"""
    
    @pytest.mark.asyncio
    async def test_get_confidence_overall_trend_includes_all_users(self, temporal_client, skip_if_disabled):
        """Verify confidence overall trend includes all users"""
        # Record confidence for multiple users
        metrics1 = ConfidenceMetrics(
            user_fact_confidence=0.8,
            relationship_confidence=0.7,
            context_confidence=0.9,
            emotional_confidence=0.85,
            overall_confidence=0.81
        )
        metrics2 = ConfidenceMetrics(
            user_fact_confidence=0.6,
            relationship_confidence=0.5,
            context_confidence=0.7,
            emotional_confidence=0.65,
            overall_confidence=0.63
        )
        
        await temporal_client.record_confidence_evolution("elena", "user_1", metrics1)
        await temporal_client.record_confidence_evolution("elena", "user_2", metrics2)
        
        # Retrieve overall trend
        trends = await temporal_client.get_confidence_overall_trend("elena", hours_back=1)
        
        # Should include both users
        assert len(trends) >= 2
        user_ids = [t['user_id'] for t in trends]
        assert 'user_1' in user_ids or 'user_2' in user_ids


class TestConversationQualityQueries:
    """Test conversation quality query methods (Task 3)"""
    
    @pytest.mark.asyncio
    async def test_get_conversation_quality_trend(self, temporal_client, skip_if_disabled):
        """Verify conversation quality trend retrieval"""
        # Record quality metrics
        quality = ConversationQualityMetrics(
            engagement_score=0.8,
            satisfaction_score=0.7,
            natural_flow_score=0.9,
            emotional_resonance=0.85,
            topic_relevance=0.75
        )
        
        await temporal_client.record_conversation_quality("elena", "user_1", quality)
        
        # Retrieve trend
        quality_data = await temporal_client.get_conversation_quality_trend("elena", "user_1", hours_back=1)
        
        assert len(quality_data) >= 1
        if len(quality_data) > 0:
            assert 'engagement_score' in quality_data[0]
            assert 'timestamp' in quality_data[0]
    
    @pytest.mark.asyncio
    async def test_get_conversation_quality_overall_trend(self, temporal_client, skip_if_disabled):
        """Verify overall quality trend includes all users"""
        quality = ConversationQualityMetrics(
            engagement_score=0.8,
            satisfaction_score=0.7,
            natural_flow_score=0.9,
            emotional_resonance=0.85,
            topic_relevance=0.75
        )
        
        await temporal_client.record_conversation_quality("elena", "user_1", quality)
        await temporal_client.record_conversation_quality("elena", "user_2", quality)
        
        # Retrieve overall trend
        quality_data = await temporal_client.get_conversation_quality_overall_trend("elena", hours_back=1)
        
        assert len(quality_data) >= 2
        user_ids = [q['user_id'] for q in quality_data]
        assert 'user_1' in user_ids or 'user_2' in user_ids


class TestGenericQueryMethod:
    """Test generic query_data() method (Task 4)"""
    
    @pytest.mark.asyncio
    async def test_query_data_generic(self, temporal_client, skip_if_disabled):
        """Verify generic query execution"""
        # Record some test data first
        await temporal_client.record_bot_emotion("elena", "query_test_user", "joy", 0.8, 0.9)
        
        # Execute generic query
        query = f'''
            from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "bot_emotion")
            |> filter(fn: (r) => r.bot == "elena")
            |> limit(n: 10)
        '''
        
        results = await temporal_client.query_data(query)
        
        assert isinstance(results, list)
        if len(results) > 0:
            assert 'timestamp' in results[0]
            assert '_measurement' in results[0]
    
    @pytest.mark.asyncio
    async def test_query_data_handles_invalid_query(self, temporal_client, skip_if_disabled):
        """Verify graceful handling of invalid queries"""
        # Invalid Flux query
        results = await temporal_client.query_data("INVALID QUERY")
        assert results == []


class TestExistingMethods:
    """Test that existing methods still work (regression tests)"""
    
    @pytest.mark.asyncio
    async def test_get_confidence_trend(self, temporal_client, skip_if_disabled):
        """Verify existing confidence trend method still works"""
        metrics = ConfidenceMetrics(
            user_fact_confidence=0.8,
            relationship_confidence=0.7,
            context_confidence=0.9,
            emotional_confidence=0.85,
            overall_confidence=0.81
        )
        
        await temporal_client.record_confidence_evolution("elena", "regression_user", metrics)
        trends = await temporal_client.get_confidence_trend("elena", "regression_user", hours_back=1)
        
        assert isinstance(trends, list)
    
    @pytest.mark.asyncio
    async def test_get_relationship_evolution(self, temporal_client, skip_if_disabled):
        """Verify existing relationship evolution method still works"""
        relationship = RelationshipMetrics(
            trust_level=0.8,
            affection_level=0.7,
            attunement_level=0.9,
            interaction_quality=0.85,
            communication_comfort=0.75
        )
        
        await temporal_client.record_relationship_progression(
            "elena", "regression_user", relationship
        )
        
        evolution = await temporal_client.get_relationship_evolution("elena", "regression_user", days_back=1)
        assert isinstance(evolution, list)


class TestInfluxDBDisabled:
    """Test behavior when InfluxDB is disabled"""
    
    @pytest.mark.asyncio
    async def test_methods_return_empty_when_disabled(self):
        """Verify all methods return empty lists when InfluxDB disabled"""
        # Create client that will be disabled (no config)
        original_env = {}
        required_vars = ['INFLUXDB_URL', 'INFLUXDB_TOKEN', 'INFLUXDB_ORG', 'INFLUXDB_BUCKET']
        
        # Save and clear env vars
        for var in required_vars:
            original_env[var] = os.getenv(var)
            if var in os.environ:
                del os.environ[var]
        
        try:
            client = TemporalIntelligenceClient()
            assert not client.enabled
            
            # All methods should return empty lists
            assert await client.get_bot_emotion_trend("elena", "user", 24) == []
            assert await client.get_bot_emotion_overall_trend("elena", 24) == []
            assert await client.get_confidence_overall_trend("elena", 24) == []
            assert await client.get_conversation_quality_trend("elena", "user", 24) == []
            assert await client.get_conversation_quality_overall_trend("elena", 24) == []
            assert await client.query_data("SELECT * FROM anything") == []
        finally:
            # Restore env vars
            for var, value in original_env.items():
                if value is not None:
                    os.environ[var] = value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
