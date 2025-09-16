#!/usr/bin/env python3
"""
Test Suite for Emotional Context Engine

This test suite validates the emotional intelligence system that integrates
emotional analysis with personality profiling to create context-aware,
empathetic AI companion responses.

Test Coverage:
- Emotional context analysis accuracy
- Personality integration effectiveness
- Emotional memory clustering functionality
- Adaptation strategy generation
- Privacy compliance and security
- Performance and scalability
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

# Import the system under test
try:
    from src.intelligence.emotional_context_engine import (
        EmotionalAdaptationStrategy,
        EmotionalContext,
        EmotionalContextEngine,
        EmotionalMemoryCluster,
        EmotionalPattern,
        EmotionalState,
        EmotionalTrigger,
        create_emotional_context_engine,
    )

    EMOTIONAL_CONTEXT_ENGINE_AVAILABLE = True
except ImportError:
    EMOTIONAL_CONTEXT_ENGINE_AVAILABLE = False


# Test fixtures and mock data
@pytest.fixture
def mock_emotional_ai():
    """Mock emotional AI for testing"""
    mock = AsyncMock()
    mock.analyze_emotion_cloud.return_value = {
        "primary_emotion": "joy",
        "confidence": 0.85,
        "intensity": 0.7,
        "all_emotions": {"joy": 0.7, "neutral": 0.3},
        "sentiment": {"score": 0.8},
    }
    return mock


@pytest.fixture
def mock_personality_profiler():
    """Mock personality profiler for testing"""
    mock = AsyncMock()
    profile_mock = Mock()
    profile_mock.relationship_depth = 0.6
    profile_mock.trust_level = 0.7
    profile_mock.traits = {}
    mock.get_personality_profile.return_value = profile_mock
    return mock


@pytest.fixture
def emotional_context_engine(mock_emotional_ai, mock_personality_profiler):
    """Create emotional context engine with mocked dependencies"""
    return EmotionalContextEngine(
        emotional_ai=mock_emotional_ai,
        personality_profiler=mock_personality_profiler,
        memory_tier_manager=None,
        personality_fact_classifier=None,
    )


@pytest.fixture
def sample_emotional_context():
    """Sample emotional context for testing"""
    return EmotionalContext(
        user_id="test_user_123",
        context_id="test_channel",
        timestamp=datetime.now(),
        primary_emotion=EmotionalState.JOY,
        emotion_confidence=0.85,
        emotion_intensity=0.7,
        all_emotions={"joy": 0.7, "neutral": 0.3},
        sentiment_score=0.8,
        emotional_triggers=[EmotionalTrigger.CELEBRATION_MOMENTS],
        personality_alignment=0.8,
        relationship_depth=0.6,
        trust_level=0.7,
        conversation_length=5,
        response_time_context=None,
        topic_emotional_weight=0.6,
        response_tone_adjustment="enthusiastic_sharing",
        empathy_level_needed=0.5,
        support_opportunity=False,
        celebration_opportunity=True,
    )


class TestEmotionalContextAnalysis:
    """Test emotional context analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_emotional_context_basic(self, emotional_context_engine):
        """Test basic emotional context analysis"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        user_id = "test_user_123"
        context_id = "test_channel"
        user_message = "I'm so excited about my promotion!"

        context = await emotional_context_engine.analyze_emotional_context(
            user_id=user_id, context_id=context_id, user_message=user_message
        )

        assert context.user_id == user_id
        assert context.context_id == context_id
        assert context.primary_emotion == EmotionalState.JOY
        assert context.emotion_confidence > 0.0
        assert context.emotion_intensity > 0.0
        assert EmotionalTrigger.CELEBRATION_MOMENTS in context.emotional_triggers

    @pytest.mark.asyncio
    async def test_emotional_trigger_detection(self, emotional_context_engine):
        """Test emotional trigger detection accuracy"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        test_cases = [
            {
                "message": "I'm feeling really stressed about this deadline",
                "expected_triggers": [EmotionalTrigger.STRESS_INDICATORS],
            },
            {
                "message": "I need help with this problem, I'm confused",
                "expected_triggers": [EmotionalTrigger.SUPPORT_OPPORTUNITIES],
            },
            {
                "message": "I just won the competition! Amazing achievement!",
                "expected_triggers": [EmotionalTrigger.CELEBRATION_MOMENTS],
            },
        ]

        for case in test_cases:
            # Mock sad emotion for stress case
            if "stressed" in case["message"]:
                emotional_context_engine.emotional_ai.analyze_emotion_cloud.return_value = {
                    "primary_emotion": "sadness",
                    "confidence": 0.8,
                    "intensity": 0.8,
                    "all_emotions": {"sadness": 0.8},
                    "sentiment": {"score": 0.2},
                }

            context = await emotional_context_engine.analyze_emotional_context(
                user_id="test_user", context_id="test", user_message=case["message"]
            )

            for expected_trigger in case["expected_triggers"]:
                assert (
                    expected_trigger in context.emotional_triggers
                ), f"Expected trigger {expected_trigger} not found for message: {case['message']}"

    @pytest.mark.asyncio
    async def test_personality_integration(self, emotional_context_engine):
        """Test integration with personality profiling system"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        user_id = "test_user_123"
        user_message = "I'm feeling a bit down today"

        context = await emotional_context_engine.analyze_emotional_context(
            user_id=user_id, context_id="test", user_message=user_message
        )

        # Verify personality context is included
        assert context.relationship_depth == 0.6  # From mock
        assert context.trust_level == 0.7  # From mock
        assert context.personality_alignment > 0.0

        # Verify personality profiler was called
        emotional_context_engine.personality_profiler.get_personality_profile.assert_called_once_with(
            user_id
        )

    @pytest.mark.asyncio
    async def test_fallback_emotional_analysis(self, emotional_context_engine):
        """Test fallback when emotional AI is unavailable"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        # Make emotional AI fail
        emotional_context_engine.emotional_ai.analyze_emotion_cloud.side_effect = ConnectionError(
            "API unavailable"
        )

        context = await emotional_context_engine.analyze_emotional_context(
            user_id="test_user", context_id="test", user_message="I'm happy today!"
        )

        # Should still work with fallback
        assert context.primary_emotion in [EmotionalState.JOY, EmotionalState.NEUTRAL]
        assert context.emotion_confidence > 0.0


class TestEmotionalAdaptationStrategy:
    """Test emotional adaptation strategy generation"""

    @pytest.mark.asyncio
    async def test_create_adaptation_strategy(
        self, emotional_context_engine, sample_emotional_context
    ):
        """Test adaptation strategy creation"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        strategy = await emotional_context_engine.create_adaptation_strategy(
            sample_emotional_context
        )

        assert strategy.user_id == sample_emotional_context.user_id
        assert strategy.emotional_context == sample_emotional_context
        assert strategy.expected_effectiveness > 0.0
        assert strategy.confidence_score > 0.0
        assert isinstance(strategy.tone_adjustments, dict)
        assert isinstance(strategy.acknowledge_emotion, bool)

    @pytest.mark.asyncio
    async def test_adaptation_for_different_emotions(self, emotional_context_engine):
        """Test adaptation strategies for different emotional states"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        emotions_to_test = [
            (EmotionalState.SADNESS, True, True),  # (emotion, should_acknowledge, should_support)
            (EmotionalState.JOY, True, False),
            (EmotionalState.ANGER, True, True),
            (EmotionalState.FEAR, True, True),
            (EmotionalState.NEUTRAL, False, False),
        ]

        for emotion, should_acknowledge, should_support in emotions_to_test:
            context = EmotionalContext(
                user_id="test_user",
                context_id="test",
                timestamp=datetime.now(),
                primary_emotion=emotion,
                emotion_confidence=0.8,
                emotion_intensity=0.7,
                all_emotions={emotion.value: 0.8},
                sentiment_score=0.5,
                emotional_triggers=(
                    [EmotionalTrigger.SUPPORT_OPPORTUNITIES] if should_support else []
                ),
                personality_alignment=0.7,
                relationship_depth=0.5,
                trust_level=0.5,
                conversation_length=3,
                response_time_context=None,
                topic_emotional_weight=0.5,
                response_tone_adjustment="balanced",
                empathy_level_needed=0.6 if should_support else 0.3,
                support_opportunity=should_support,
                celebration_opportunity=emotion == EmotionalState.JOY,
            )

            strategy = await emotional_context_engine.create_adaptation_strategy(context)

            assert (
                strategy.acknowledge_emotion == should_acknowledge
            ), f"Emotion {emotion} should acknowledge: {should_acknowledge}"
            assert (
                strategy.offer_support == should_support
            ), f"Emotion {emotion} should offer support: {should_support}"

    def test_emotional_adaptation_prompt_generation(
        self, emotional_context_engine, sample_emotional_context
    ):
        """Test generation of adaptation prompts for AI"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        # Create a strategy with specific adaptations
        strategy = EmotionalAdaptationStrategy(
            strategy_id="test_strategy",
            user_id="test_user",
            emotional_context=sample_emotional_context,
            tone_adjustments={"warmth": 0.8, "enthusiasm": 0.9},
            response_length_modifier=1.2,
            empathy_emphasis=0.7,
            personality_based_adjustments={},
            communication_style_override=None,
            acknowledge_emotion=True,
            offer_support=False,
            provide_validation=True,
            suggest_solutions=False,
            share_empathy=True,
            expected_effectiveness=0.8,
            confidence_score=0.7,
        )

        prompt = emotional_context_engine.get_emotional_adaptation_prompt(strategy)

        assert "joy" in prompt.lower()
        assert "acknowledge" in prompt.lower()
        assert "validation" in prompt.lower()
        assert "empathy" in prompt.lower()
        assert "warmth" in prompt.lower() or "enthusiasm" in prompt.lower()


class TestEmotionalMemoryClustering:
    """Test emotional memory clustering functionality"""

    @pytest.mark.asyncio
    async def test_cluster_emotional_memories_insufficient_data(self, emotional_context_engine):
        """Test clustering with insufficient data"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        # No previous contexts
        clusters = await emotional_context_engine.cluster_emotional_memories("new_user")

        assert len(clusters) == 0

    @pytest.mark.asyncio
    async def test_cluster_emotional_memories_with_data(self, emotional_context_engine):
        """Test clustering with sufficient emotional data"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        user_id = "test_user_clustering"

        # Create multiple similar emotional contexts
        for i in range(5):
            context = EmotionalContext(
                user_id=user_id,
                context_id="test",
                timestamp=datetime.now() - timedelta(days=i),
                primary_emotion=EmotionalState.JOY,
                emotion_confidence=0.8,
                emotion_intensity=0.7,
                all_emotions={"joy": 0.8},
                sentiment_score=0.8,
                emotional_triggers=[EmotionalTrigger.CELEBRATION_MOMENTS],
                personality_alignment=0.8,
                relationship_depth=0.6,
                trust_level=0.7,
                conversation_length=3,
                response_time_context=None,
                topic_emotional_weight=0.6,
                response_tone_adjustment="enthusiastic",
                empathy_level_needed=0.4,
                support_opportunity=False,
                celebration_opportunity=True,
            )
            emotional_context_engine.emotional_contexts[user_id].append(context)

        clusters = await emotional_context_engine.cluster_emotional_memories(user_id)

        assert len(clusters) > 0
        assert all(isinstance(cluster, EmotionalMemoryCluster) for cluster in clusters)
        assert all(cluster.user_id == user_id for cluster in clusters)

    def test_emotional_pattern_classification(self, emotional_context_engine):
        """Test classification of emotional patterns"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        test_contexts = [
            # Joy with celebration triggers -> CELEBRATION_MOMENTS
            EmotionalContext(
                user_id="test",
                context_id="test",
                timestamp=datetime.now(),
                primary_emotion=EmotionalState.JOY,
                emotion_confidence=0.8,
                emotion_intensity=0.8,
                all_emotions={},
                sentiment_score=0.8,
                emotional_triggers=[EmotionalTrigger.CELEBRATION_MOMENTS],
                personality_alignment=0.7,
                relationship_depth=0.5,
                trust_level=0.5,
                conversation_length=3,
                response_time_context=None,
                topic_emotional_weight=0.5,
                response_tone_adjustment="enthusiastic",
                empathy_level_needed=0.3,
                support_opportunity=False,
                celebration_opportunity=True,
            ),
            # Stress indicators -> STRESS_RESPONSE
            EmotionalContext(
                user_id="test",
                context_id="test",
                timestamp=datetime.now(),
                primary_emotion=EmotionalState.FEAR,
                emotion_confidence=0.7,
                emotion_intensity=0.6,
                all_emotions={},
                sentiment_score=0.3,
                emotional_triggers=[EmotionalTrigger.STRESS_INDICATORS],
                personality_alignment=0.6,
                relationship_depth=0.5,
                trust_level=0.5,
                conversation_length=3,
                response_time_context=None,
                topic_emotional_weight=0.7,
                response_tone_adjustment="calming",
                empathy_level_needed=0.8,
                support_opportunity=True,
                celebration_opportunity=False,
            ),
        ]

        for context in test_contexts:
            pattern = emotional_context_engine._classify_emotional_pattern(context)
            assert isinstance(pattern, EmotionalPattern)


class TestPerformanceAndScalability:
    """Test performance and scalability of emotional context engine"""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_analyses(self, emotional_context_engine):
        """Test handling multiple concurrent emotional analyses"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        # Create multiple concurrent analysis tasks
        tasks = []
        for i in range(10):
            task = emotional_context_engine.analyze_emotional_context(
                user_id=f"user_{i}", context_id="test", user_message=f"Test message {i}"
            )
            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(isinstance(result, EmotionalContext) for result in results)
        assert len({result.user_id for result in results}) == 10  # All different users

    @pytest.mark.asyncio
    async def test_memory_usage_with_large_history(self, emotional_context_engine):
        """Test memory usage with large emotional history"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        user_id = "heavy_user"

        # Create a large number of emotional contexts
        for i in range(100):
            context = EmotionalContext(
                user_id=user_id,
                context_id="test",
                timestamp=datetime.now() - timedelta(minutes=i),
                primary_emotion=EmotionalState.NEUTRAL,
                emotion_confidence=0.5,
                emotion_intensity=0.5,
                all_emotions={"neutral": 0.5},
                sentiment_score=0.5,
                emotional_triggers=[],
                personality_alignment=0.7,
                relationship_depth=0.5,
                trust_level=0.5,
                conversation_length=3,
                response_time_context=None,
                topic_emotional_weight=0.5,
                response_tone_adjustment="balanced",
                empathy_level_needed=0.3,
                support_opportunity=False,
                celebration_opportunity=False,
            )
            emotional_context_engine.emotional_contexts[user_id].append(context)

        # Test that analysis still works efficiently
        new_context = await emotional_context_engine.analyze_emotional_context(
            user_id=user_id, context_id="test", user_message="New message after large history"
        )

        assert new_context.user_id == user_id
        assert len(emotional_context_engine.emotional_contexts[user_id]) == 101

    @pytest.mark.asyncio
    async def test_user_emotional_summary_performance(self, emotional_context_engine):
        """Test performance of emotional summary generation"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        user_id = "summary_test_user"

        # Create diverse emotional contexts
        emotions = [EmotionalState.JOY, EmotionalState.SADNESS, EmotionalState.NEUTRAL]
        for i in range(30):
            context = EmotionalContext(
                user_id=user_id,
                context_id="test",
                timestamp=datetime.now() - timedelta(hours=i),
                primary_emotion=emotions[i % len(emotions)],
                emotion_confidence=0.7,
                emotion_intensity=0.6,
                all_emotions={emotions[i % len(emotions)].value: 0.6},
                sentiment_score=0.6,
                emotional_triggers=[],
                personality_alignment=0.7,
                relationship_depth=0.5 + (i * 0.01),  # Gradual relationship building
                trust_level=0.4 + (i * 0.01),
                conversation_length=3,
                response_time_context=None,
                topic_emotional_weight=0.5,
                response_tone_adjustment="balanced",
                empathy_level_needed=0.4,
                support_opportunity=False,
                celebration_opportunity=False,
            )
            emotional_context_engine.emotional_contexts[user_id].append(context)

        summary = await emotional_context_engine.get_user_emotional_summary(user_id)

        assert summary["total_interactions"] == 30
        assert "dominant_emotions" in summary
        assert "relationship_progression" in summary
        assert summary["current_relationship_depth"] > 0.5
        assert summary["current_trust_level"] > 0.4


class TestPrivacyAndSecurity:
    """Test privacy and security compliance"""

    @pytest.mark.asyncio
    async def test_user_data_isolation(self, emotional_context_engine):
        """Test that user emotional data is properly isolated"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        # Create contexts for different users
        user1_context = await emotional_context_engine.analyze_emotional_context(
            user_id="user_1", context_id="channel_1", user_message="I'm happy about my success"
        )

        user2_context = await emotional_context_engine.analyze_emotional_context(
            user_id="user_2", context_id="channel_2", user_message="I'm sad about my failure"
        )

        # Verify data isolation
        user1_summary = await emotional_context_engine.get_user_emotional_summary("user_1")
        user2_summary = await emotional_context_engine.get_user_emotional_summary("user_2")

        assert user1_summary["total_interactions"] == 1
        assert user2_summary["total_interactions"] == 1
        assert user1_context.user_id != user2_context.user_id

    @pytest.mark.asyncio
    async def test_context_boundary_respect(self, emotional_context_engine):
        """Test that context boundaries (DM vs channel) are respected"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        user_id = "boundary_test_user"

        # Create contexts in different channels/DMs
        dm_context = await emotional_context_engine.analyze_emotional_context(
            user_id=user_id, context_id="DM", user_message="Private emotional sharing"
        )

        channel_context = await emotional_context_engine.analyze_emotional_context(
            user_id=user_id, context_id="public_channel", user_message="Public message"
        )

        # Both should be stored but with different context IDs
        assert dm_context.context_id == "DM"
        assert channel_context.context_id == "public_channel"
        assert dm_context.user_id == channel_context.user_id

    def test_sensitive_information_handling(self, emotional_context_engine):
        """Test handling of sensitive emotional information"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        # Test that emotional adaptation doesn't leak sensitive info
        sensitive_context = EmotionalContext(
            user_id="sensitive_user",
            context_id="DM",
            timestamp=datetime.now(),
            primary_emotion=EmotionalState.SADNESS,
            emotion_confidence=0.9,
            emotion_intensity=0.8,
            all_emotions={"sadness": 0.8},
            sentiment_score=0.2,
            emotional_triggers=[EmotionalTrigger.SADNESS_ONSET],
            personality_alignment=0.7,
            relationship_depth=0.8,  # High trust
            trust_level=0.9,
            conversation_length=10,
            response_time_context=None,
            topic_emotional_weight=0.9,  # Heavy topic
            response_tone_adjustment="gentle_supportive",
            empathy_level_needed=0.9,
            support_opportunity=True,
            celebration_opportunity=False,
        )

        prompt = emotional_context_engine.get_emotional_adaptation_prompt(
            EmotionalAdaptationStrategy(
                strategy_id="test",
                user_id="sensitive_user",
                emotional_context=sensitive_context,
                tone_adjustments={"gentleness": 0.9},
                response_length_modifier=1.0,
                empathy_emphasis=0.9,
                personality_based_adjustments={},
                communication_style_override=None,
                acknowledge_emotion=True,
                offer_support=True,
                provide_validation=True,
                suggest_solutions=False,
                share_empathy=True,
                expected_effectiveness=0.8,
                confidence_score=0.7,
            )
        )

        # Prompt should focus on adaptation without exposing raw data
        assert "sadness" in prompt.lower()
        assert "support" in prompt.lower()
        assert "sensitive_user" not in prompt  # User ID should not be in prompt


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""

    @pytest.mark.asyncio
    async def test_relationship_building_scenario(self, emotional_context_engine):
        """Test a realistic relationship building scenario"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        user_id = "relationship_user"

        # Simulate conversation progression over time
        conversations = [
            ("Hello, nice to meet you", 0.2, 0.2),  # Initial contact
            ("I'm having a good day", 0.3, 0.3),  # Building rapport
            ("Can you help me with something?", 0.4, 0.4),  # Seeking help
            ("Thanks, that really helped!", 0.5, 0.5),  # Positive outcome
            ("I'm feeling a bit stressed lately", 0.6, 0.6),  # Sharing concerns
            ("I trust your advice on this", 0.7, 0.8),  # High trust sharing
        ]

        contexts = []
        for message, expected_depth, expected_trust in conversations:
            # Update mock to reflect growing relationship
            profile_mock = Mock()
            profile_mock.relationship_depth = expected_depth
            profile_mock.trust_level = expected_trust
            profile_mock.traits = {}
            emotional_context_engine.personality_profiler.get_personality_profile.return_value = (
                profile_mock
            )

            context = await emotional_context_engine.analyze_emotional_context(
                user_id=user_id, context_id="DM", user_message=message
            )
            contexts.append(context)

        # Verify relationship progression
        assert contexts[0].relationship_depth < contexts[-1].relationship_depth
        assert contexts[0].trust_level < contexts[-1].trust_level

        # Later conversations should have different adaptation strategies
        early_strategy = await emotional_context_engine.create_adaptation_strategy(contexts[0])
        late_strategy = await emotional_context_engine.create_adaptation_strategy(contexts[-1])

        assert early_strategy.empathy_emphasis <= late_strategy.empathy_emphasis

    @pytest.mark.asyncio
    async def test_crisis_support_scenario(self, emotional_context_engine):
        """Test handling of crisis/high-stress situations"""
        if not EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
            pytest.skip("Emotional Context Engine not available")

        # Mock high-stress emotional response
        emotional_context_engine.emotional_ai.analyze_emotion_cloud.return_value = {
            "primary_emotion": "fear",
            "confidence": 0.95,
            "intensity": 0.9,
            "all_emotions": {"fear": 0.9, "sadness": 0.7},
            "sentiment": {"score": 0.1},
        }

        context = await emotional_context_engine.analyze_emotional_context(
            user_id="crisis_user",
            context_id="DM",
            user_message="I'm having a panic attack and don't know what to do",
        )

        strategy = await emotional_context_engine.create_adaptation_strategy(context)

        # High-stress situations should trigger specific responses
        assert EmotionalTrigger.STRESS_INDICATORS in context.emotional_triggers
        assert EmotionalTrigger.OVERWHELMING_EMOTIONS in context.emotional_triggers
        assert strategy.offer_support
        assert strategy.empathy_emphasis > 0.8
        assert strategy.tone_adjustments.get("gentleness", 0) > 0.8
        assert strategy.communication_style_override in [
            None,
            "calm_grounding",
            "reassuring_stable",
        ]


# Test runner for easy execution
if __name__ == "__main__":
    if EMOTIONAL_CONTEXT_ENGINE_AVAILABLE:
        pytest.main([__file__, "-v", "--tb=short"])
    else:
        pass
