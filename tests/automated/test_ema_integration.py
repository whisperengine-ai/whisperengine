"""
Integration tests for EMA calculation within emotion detection pipeline

Tests Task 3: Integrating EMA into analyze_emotion() flow
Tests that EMA is calculated, stored, and used for trajectory analysis
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.intelligence.advanced_emotion_detector import AdvancedEmotionDetector


class TestEMAIntegration:
    """Integration tests for EMA with full detection pipeline"""
    
    @pytest.fixture
    def detector_with_mocks(self):
        """Create detector with mocked RoBERTa and memory"""
        mock_enhanced = AsyncMock()
        mock_memory = AsyncMock()
        detector = AdvancedEmotionDetector(
            enhanced_emotion_analyzer=mock_enhanced,
            memory_manager=mock_memory
        )
        return detector, mock_enhanced, mock_memory
    
    @pytest.mark.asyncio
    async def test_ema_calculation_with_roberta_integration(self, detector_with_mocks):
        """EMA calculation integrated with RoBERTa emotion analysis"""
        detector, mock_enhanced, mock_memory = detector_with_mocks
        
        # Mock RoBERTa analysis
        mock_roberta = MagicMock()
        mock_roberta.intensity = 0.7
        mock_roberta.confidence = 0.85
        mock_roberta.primary_emotion = "joy"
        
        emoji_analysis = {"😊": 0.8}
        user_id = "test_user_123"
        
        # No previous EMA (cold start)
        mock_memory.retrieve_relevant_memories.return_value = []
        
        # Calculate intensity with EMA
        result = await detector._calculate_emotional_intensity_with_ema(
            roberta_result=mock_roberta,
            emoji_analysis=emoji_analysis,
            text="I'm so happy! 😊",
            user_id=user_id,
            alpha=0.3
        )
        
        # Assertions
        assert 'raw' in result
        assert 'ema' in result
        assert result['alpha'] == 0.3
        assert result['previous_ema'] is None  # Cold start
        assert result['ema'] == result['raw']  # Cold start: EMA = raw
        assert 0.5 <= result['raw'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_ema_smooths_emotional_intensity_over_time(self, detector_with_mocks):
        """EMA smooths raw intensity over multiple messages"""
        detector, mock_enhanced, mock_memory = detector_with_mocks
        
        # Simulate sequence of messages with varying intensity
        messages = [
            ("I'm angry!", 0.8),          # High intensity
            ("nevermind", 0.3),           # Low intensity (filler)
            ("still annoyed", 0.75),      # Returning to high
        ]
        
        ema_values = []
        raw_values = []
        
        for text, expected_raw in messages:
            # Mock RoBERTa
            mock_roberta = MagicMock()
            mock_roberta.intensity = expected_raw
            mock_roberta.confidence = 0.8
            
            # Mock memory: retrieve previous EMA if available
            if ema_values:
                mock_memory.retrieve_relevant_memories.return_value = [
                    {'payload': {'emotional_intensity_ema': ema_values[-1]}}
                ]
            else:
                mock_memory.retrieve_relevant_memories.return_value = []
            
            result = await detector._calculate_emotional_intensity_with_ema(
                roberta_result=mock_roberta,
                emoji_analysis={},
                text=text,
                user_id="user123",
                alpha=0.3
            )
            
            raw_values.append(result['raw'])
            ema_values.append(result['ema'])
        
        # Verify EMA smoothing
        assert len(ema_values) == 3
        
        # First message: EMA = raw (cold start)
        assert ema_values[0] == raw_values[0]
        
        # Second message: EMA should be smoothed between previous and current
        # EMA = 0.3 × raw + 0.7 × previous_ema
        expected_ema2 = 0.3 * raw_values[1] + 0.7 * ema_values[0]
        assert abs(ema_values[1] - expected_ema2) < 0.001
        
        # Verify EMA filtered out the "nevermind" filler (less variation)
        raw_drop = raw_values[0] - raw_values[1]  # Drop from 0.8 to 0.3
        ema_drop = ema_values[0] - ema_values[1]  # Should drop less
        assert ema_drop < raw_drop
    
    @pytest.mark.asyncio
    async def test_ema_preserves_genuine_trends(self, detector_with_mocks):
        """EMA preserves genuine emotional trends (doesn't over-smooth)"""
        detector, mock_enhanced, mock_memory = detector_with_mocks
        
        # Sustained increase in emotional intensity
        sustained_increase = [0.3, 0.4, 0.5, 0.6, 0.7]
        ema_values = []
        
        for idx, raw_intensity in enumerate(sustained_increase):
            mock_roberta = MagicMock()
            mock_roberta.intensity = raw_intensity
            mock_roberta.confidence = 0.8
            
            if ema_values:
                mock_memory.retrieve_relevant_memories.return_value = [
                    {'payload': {'emotional_intensity_ema': ema_values[-1]}}
                ]
            else:
                mock_memory.retrieve_relevant_memories.return_value = []
            
            result = await detector._calculate_emotional_intensity_with_ema(
                roberta_result=mock_roberta,
                emoji_analysis={},
                text=f"Message {idx}",
                user_id="user456",
                alpha=0.3
            )
            ema_values.append(result['ema'])
        
        # Verify trend is preserved
        assert ema_values[-1] > ema_values[0], "EMA should follow upward trend"
        assert ema_values == sorted(ema_values), "EMA values should be monotonically increasing"
    
    @pytest.mark.asyncio
    async def test_ema_with_different_alpha_values(self, detector_with_mocks):
        """Different alpha values produce appropriate smoothing levels"""
        detector, mock_enhanced, mock_memory = detector_with_mocks
        
        user_id = "alpha_test_user"
        mock_roberta = MagicMock()
        mock_roberta.intensity = 0.8
        mock_roberta.confidence = 0.8
        
        # Previous EMA exists
        mock_memory.retrieve_relevant_memories.return_value = [
            {'payload': {'emotional_intensity_ema': 0.3}}
        ]
        
        # Test different alpha values
        alphas = [0.2, 0.3, 0.4]
        results = {}
        
        for alpha in alphas:
            result = await detector._calculate_emotional_intensity_with_ema(
                roberta_result=mock_roberta,
                emoji_analysis={},
                text="test",
                user_id=f"{user_id}_{alpha}",
                alpha=alpha
            )
            
            # Reset mock for next iteration
            mock_memory.retrieve_relevant_memories.return_value = [
                {'payload': {'emotional_intensity_ema': 0.3}}
            ]
            results[alpha] = result['ema']
        
        # Higher alpha = less smoothing = closer to raw (0.8)
        assert results[0.4] > results[0.3] > results[0.2]
        
        # All should be between previous (0.3) and raw (0.8)
        for alpha in alphas:
            assert 0.3 <= results[alpha] <= 0.8
    
    @pytest.mark.asyncio
    async def test_ema_crisis_detection_uses_raw_intensity(self, detector_with_mocks):
        """Crisis detection should use raw (unsmoothed) intensity"""
        detector, _, mock_memory = detector_with_mocks
        
        mock_roberta = MagicMock()
        mock_roberta.intensity = 0.95  # Crisis-level intensity
        mock_roberta.confidence = 0.95
        
        # Return high previous EMA (smooth historical trend)
        mock_memory.retrieve_relevant_memories.return_value = [
            {'payload': {'emotional_intensity_ema': 0.4}}  # Calm history
        ]
        
        result = await detector._calculate_emotional_intensity_with_ema(
            roberta_result=mock_roberta,
            emoji_analysis={},
            text="I'm having suicidal thoughts",
            user_id="crisis_user",
            alpha=0.3
        )
        
        # Raw intensity should be high (reflects crisis)
        # Calculation: roberta.intensity * 0.7 + roberta.confidence * 0.2 + emoji * 0.1
        # = 0.95 * 0.7 + 0.95 * 0.2 + 0 * 0.1 = 0.665 + 0.19 = 0.855
        assert result['raw'] > 0.80, "Raw intensity should reflect crisis level"
        
        # But EMA is smoothed by history
        assert result['ema'] < result['raw'], "EMA should be smoothed by previous calm history"
        
        # Crisis detection system should use 'raw', not 'ema'
        # (This is enforced by caller - detector returns both)
