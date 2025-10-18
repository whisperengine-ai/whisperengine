"""
Tests for QueryClassifier - Phase 2 Multi-Vector Intelligence

Tests the query classification system that enables intelligent vector routing:
- Factual query detection
- Emotional query detection (RoBERTa-based)
- Conversational query detection
- Temporal query handling
- General query fallback
- Vector strategy mapping

Part of Phase 2: Multi-Vector Intelligence Roadmap
"""
import pytest
from src.memory.query_classifier import (
    QueryClassifier,
    QueryCategory,
    create_query_classifier
)


class TestQueryClassifierBasics:
    """Test basic QueryClassifier functionality."""
    
    def test_classifier_initialization(self):
        """Test QueryClassifier initializes with correct patterns."""
        classifier = QueryClassifier()
        
        # Check factual patterns exist
        assert len(classifier.factual_patterns) > 0
        assert 'what is' in classifier.factual_patterns
        assert 'define' in classifier.factual_patterns
        
        # Check conversational patterns exist
        assert len(classifier.conversational_patterns) > 0
        assert 'we talked' in classifier.conversational_patterns
        assert 'remember when' in classifier.conversational_patterns
        
        # Check emotion threshold
        assert classifier.emotion_intensity_threshold == 0.3
    
    def test_factory_function(self):
        """Test factory function creates classifier correctly."""
        classifier = create_query_classifier()
        assert isinstance(classifier, QueryClassifier)
        assert len(classifier.factual_patterns) > 0


class TestFactualQueryDetection:
    """Test factual query detection (high-precision patterns)."""
    
    @pytest.mark.asyncio
    async def test_factual_what_is_question(self):
        """Test 'what is' questions classified as factual."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="What is the capital of France?",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.FACTUAL
    
    @pytest.mark.asyncio
    async def test_factual_define_question(self):
        """Test 'define' questions classified as factual."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="Define artificial intelligence",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.FACTUAL
    
    @pytest.mark.asyncio
    async def test_factual_how_to_question(self):
        """Test 'how to' questions classified as factual."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="How to calculate the area of a circle?",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.FACTUAL
    
    @pytest.mark.asyncio
    async def test_factual_explain_question(self):
        """Test 'explain' questions classified as factual."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="Explain quantum mechanics",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.FACTUAL
    
    @pytest.mark.asyncio
    async def test_factual_case_insensitive(self):
        """Test factual detection is case-insensitive."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="WHAT IS the meaning of life?",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.FACTUAL


class TestConversationalQueryDetection:
    """Test conversational query detection (relationship memory patterns)."""
    
    @pytest.mark.asyncio
    async def test_conversational_we_talked(self):
        """Test 'we talked' phrases classified as conversational."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="What did we talk about yesterday?",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.CONVERSATIONAL
    
    @pytest.mark.asyncio
    async def test_conversational_remember_when(self):
        """Test 'remember when' phrases classified as conversational."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="Remember when we discussed my project?",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.CONVERSATIONAL
    
    @pytest.mark.asyncio
    async def test_conversational_you_mentioned(self):
        """Test 'you mentioned' phrases classified as conversational."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="You mentioned something about vectors earlier",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.CONVERSATIONAL
    
    @pytest.mark.asyncio
    async def test_conversational_our_conversation(self):
        """Test 'our conversation' phrases classified as conversational."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="What topics came up in our conversation?",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.CONVERSATIONAL
    
    @pytest.mark.asyncio
    async def test_conversational_what_did_we(self):
        """Test 'what did we' phrases classified as conversational."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="What did we discuss about AI?",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.CONVERSATIONAL


class TestEmotionalQueryDetection:
    """Test emotional query detection (RoBERTa-based, not keyword-based)."""
    
    @pytest.mark.asyncio
    async def test_emotional_high_intensity(self):
        """Test high emotional intensity triggers emotional classification."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="How are you doing?",
            emotion_data={
                'emotional_intensity': 0.65,
                'dominant_emotion': 'joy'
            },
            is_temporal=False
        )
        
        assert category == QueryCategory.EMOTIONAL
    
    @pytest.mark.asyncio
    async def test_emotional_threshold_boundary(self):
        """Test emotion intensity right at threshold."""
        classifier = QueryClassifier()
        
        # Just above threshold (0.3)
        category = await classifier.classify_query(
            query="I'm excited about this!",
            emotion_data={
                'emotional_intensity': 0.31,
                'dominant_emotion': 'joy'
            },
            is_temporal=False
        )
        
        assert category == QueryCategory.EMOTIONAL
    
    @pytest.mark.asyncio
    async def test_emotional_below_threshold(self):
        """Test low emotional intensity falls back to general."""
        classifier = QueryClassifier()
        
        # Below threshold (0.3)
        category = await classifier.classify_query(
            query="How was your day?",  # No factual patterns
            emotion_data={
                'emotional_intensity': 0.15,
                'dominant_emotion': 'neutral'
            },
            is_temporal=False
        )
        
        assert category == QueryCategory.GENERAL
    
    @pytest.mark.asyncio
    async def test_emotional_no_emotion_data(self):
        """Test queries without emotion data don't trigger emotional route."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="How are you feeling?",
            emotion_data=None,
            is_temporal=False
        )
        
        # Should not be emotional without emotion_data
        assert category != QueryCategory.EMOTIONAL
    
    @pytest.mark.asyncio
    async def test_emotional_various_emotions(self):
        """Test different emotion types all trigger emotional classification."""
        classifier = QueryClassifier()
        
        emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'love']
        
        for emotion in emotions:
            category = await classifier.classify_query(
                query=f"I'm feeling {emotion}",
                emotion_data={
                    'emotional_intensity': 0.7,
                    'dominant_emotion': emotion
                },
                is_temporal=False
            )
            
            assert category == QueryCategory.EMOTIONAL, \
                f"Failed for emotion: {emotion}"


class TestTemporalQueryDetection:
    """Test temporal query detection (already handled by existing system)."""
    
    @pytest.mark.asyncio
    async def test_temporal_flag_true(self):
        """Test is_temporal=True always returns TEMPORAL."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="What was the first thing I told you?",
            emotion_data=None,
            is_temporal=True  # Pre-detected by existing system
        )
        
        assert category == QueryCategory.TEMPORAL
    
    @pytest.mark.asyncio
    async def test_temporal_overrides_factual(self):
        """Test temporal flag overrides factual pattern."""
        classifier = QueryClassifier()
        
        # Query matches factual pattern, but temporal flag takes priority
        category = await classifier.classify_query(
            query="What is the first message?",  # Has "what is" (factual)
            emotion_data=None,
            is_temporal=True  # But temporal detection wins
        )
        
        assert category == QueryCategory.TEMPORAL
    
    @pytest.mark.asyncio
    async def test_temporal_overrides_conversational(self):
        """Test temporal flag overrides conversational pattern."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="What did we talk about first?",  # Has "what did we" (conversational)
            emotion_data=None,
            is_temporal=True  # But temporal detection wins
        )
        
        assert category == QueryCategory.TEMPORAL


class TestGeneralQueryFallback:
    """Test general query classification (default fallback)."""
    
    @pytest.mark.asyncio
    async def test_general_simple_question(self):
        """Test simple questions without patterns fall back to general."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="Tell me more",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.GENERAL
    
    @pytest.mark.asyncio
    async def test_general_statement(self):
        """Test statements fall back to general."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="That's interesting",
            emotion_data=None,
            is_temporal=False
        )
        
        assert category == QueryCategory.GENERAL
    
    @pytest.mark.asyncio
    async def test_general_no_match(self):
        """Test queries that don't match any pattern."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="Random query with no patterns",
            emotion_data={'emotional_intensity': 0.1},  # Below threshold
            is_temporal=False
        )
        
        assert category == QueryCategory.GENERAL


class TestClassificationPriority:
    """Test classification priority order."""
    
    @pytest.mark.asyncio
    async def test_temporal_highest_priority(self):
        """Test temporal beats all other patterns."""
        classifier = QueryClassifier()
        
        # Query matches multiple patterns + high emotion + temporal flag
        category = await classifier.classify_query(
            query="What is the first thing we talked about?",  # factual + conversational
            emotion_data={'emotional_intensity': 0.8},  # High emotion
            is_temporal=True  # Temporal flag
        )
        
        # Temporal should win
        assert category == QueryCategory.TEMPORAL
    
    @pytest.mark.asyncio
    async def test_factual_beats_general(self):
        """Test factual pattern beats general fallback."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="What is the meaning of this?",
            emotion_data={'emotional_intensity': 0.1},  # Low emotion
            is_temporal=False
        )
        
        # Factual should win over general
        assert category == QueryCategory.FACTUAL
    
    @pytest.mark.asyncio
    async def test_conversational_beats_general(self):
        """Test conversational pattern beats general fallback."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="What did we discuss?",
            emotion_data={'emotional_intensity': 0.1},  # Low emotion
            is_temporal=False
        )
        
        # Conversational should win over general
        assert category == QueryCategory.CONVERSATIONAL
    
    @pytest.mark.asyncio
    async def test_emotional_beats_general(self):
        """Test emotional (high intensity) beats general fallback."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="That sounds interesting",  # No specific patterns
            emotion_data={'emotional_intensity': 0.5},  # High emotion
            is_temporal=False
        )
        
        # Emotional should win over general
        assert category == QueryCategory.EMOTIONAL


class TestVectorStrategyMapping:
    """Test vector strategy retrieval for each category."""
    
    def test_factual_strategy(self):
        """Test factual category returns single content vector."""
        classifier = QueryClassifier()
        
        strategy = classifier.get_vector_strategy(QueryCategory.FACTUAL)
        
        assert strategy['vectors'] == ['content']
        assert strategy['weights'] == [1.0]
        assert strategy['use_fusion'] is False
        assert 'fast path' in strategy['description'].lower()
    
    def test_emotional_strategy(self):
        """Test emotional category returns content + emotion fusion."""
        classifier = QueryClassifier()
        
        strategy = classifier.get_vector_strategy(QueryCategory.EMOTIONAL)
        
        assert strategy['vectors'] == ['content', 'emotion']
        assert strategy['weights'] == [0.4, 0.6]  # Emotion weighted higher
        assert strategy['use_fusion'] is True
        assert 'emotion' in strategy['description'].lower()
    
    def test_conversational_strategy(self):
        """Test conversational category returns content + semantic fusion."""
        classifier = QueryClassifier()
        
        strategy = classifier.get_vector_strategy(QueryCategory.CONVERSATIONAL)
        
        assert strategy['vectors'] == ['content', 'semantic']
        assert strategy['weights'] == [0.5, 0.5]  # Balanced
        assert strategy['use_fusion'] is True
        assert 'semantic' in strategy['description'].lower()
    
    def test_temporal_strategy(self):
        """Test temporal category returns no vectors (chronological scroll)."""
        classifier = QueryClassifier()
        
        strategy = classifier.get_vector_strategy(QueryCategory.TEMPORAL)
        
        assert strategy['vectors'] == []
        assert strategy['weights'] == []
        assert strategy['use_fusion'] is False
        assert 'chronological' in strategy['description'].lower()
    
    def test_general_strategy(self):
        """Test general category returns single content vector."""
        classifier = QueryClassifier()
        
        strategy = classifier.get_vector_strategy(QueryCategory.GENERAL)
        
        assert strategy['vectors'] == ['content']
        assert strategy['weights'] == [1.0]
        assert strategy['use_fusion'] is False
        assert 'default' in strategy['description'].lower()


class TestPatternUpdates:
    """Test runtime pattern updates for tuning."""
    
    def test_update_factual_patterns(self):
        """Test updating factual patterns."""
        classifier = QueryClassifier()
        
        new_patterns = ['calculate', 'compute', 'solve']
        classifier.update_patterns(factual_patterns=new_patterns)
        
        assert classifier.factual_patterns == new_patterns
    
    def test_update_conversational_patterns(self):
        """Test updating conversational patterns."""
        classifier = QueryClassifier()
        
        new_patterns = ['we chatted', 'our talk']
        classifier.update_patterns(conversational_patterns=new_patterns)
        
        assert classifier.conversational_patterns == new_patterns
    
    def test_update_emotion_threshold(self):
        """Test updating emotion intensity threshold."""
        classifier = QueryClassifier()
        
        assert classifier.emotion_intensity_threshold == 0.3
        
        classifier.update_patterns(emotion_threshold=0.5)
        
        assert classifier.emotion_intensity_threshold == 0.5
    
    @pytest.mark.asyncio
    async def test_updated_threshold_affects_classification(self):
        """Test updated threshold changes classification behavior."""
        classifier = QueryClassifier()
        
        # Original threshold: 0.3
        category1 = await classifier.classify_query(
            query="Test query",
            emotion_data={'emotional_intensity': 0.4},
            is_temporal=False
        )
        
        assert category1 == QueryCategory.EMOTIONAL
        
        # Raise threshold to 0.5
        classifier.update_patterns(emotion_threshold=0.5)
        
        # Same query now falls below threshold
        category2 = await classifier.classify_query(
            query="Test query",
            emotion_data={'emotional_intensity': 0.4},
            is_temporal=False
        )
        
        assert category2 == QueryCategory.GENERAL


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Test empty query string."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="",
            emotion_data=None,
            is_temporal=False
        )
        
        # Should fall back to general
        assert category == QueryCategory.GENERAL
    
    @pytest.mark.asyncio
    async def test_whitespace_only_query(self):
        """Test query with only whitespace."""
        classifier = QueryClassifier()
        
        category = await classifier.classify_query(
            query="   \n\t  ",
            emotion_data=None,
            is_temporal=False
        )
        
        # Should fall back to general
        assert category == QueryCategory.GENERAL
    
    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """Test very long query (performance check)."""
        classifier = QueryClassifier()
        
        # 1000-word query
        long_query = "What is " + "meaning " * 1000
        
        category = await classifier.classify_query(
            query=long_query,
            emotion_data=None,
            is_temporal=False
        )
        
        # Should still detect factual pattern
        assert category == QueryCategory.FACTUAL
    
    @pytest.mark.asyncio
    async def test_multiple_pattern_matches(self):
        """Test query matching multiple patterns (priority test)."""
        classifier = QueryClassifier()
        
        # Matches both factual ("what is") and conversational ("we talked")
        category = await classifier.classify_query(
            query="What is the thing we talked about?",
            emotion_data=None,
            is_temporal=False
        )
        
        # Factual should win (higher priority)
        assert category == QueryCategory.FACTUAL
    
    @pytest.mark.asyncio
    async def test_emotion_data_missing_fields(self):
        """Test emotion_data with missing fields."""
        classifier = QueryClassifier()
        
        # Missing emotional_intensity
        category = await classifier.classify_query(
            query="Test query",
            emotion_data={'dominant_emotion': 'joy'},
            is_temporal=False
        )
        
        # Should fall back to general (intensity defaults to 0.0)
        assert category == QueryCategory.GENERAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
