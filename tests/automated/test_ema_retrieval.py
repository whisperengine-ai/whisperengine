"""
Async tests for EMA retrieval from memory system

Tests the _get_previous_ema() async method which retrieves EMA values
from Qdrant vector memory for use in trajectory smoothing.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.intelligence.advanced_emotion_detector import AdvancedEmotionDetector


class TestEMARetrieval:
    """Test EMA retrieval from memory system"""
    
    @pytest.fixture
    def detector_with_memory(self):
        """Create detector with mocked memory manager"""
        mock_memory = AsyncMock()
        detector = AdvancedEmotionDetector(memory_manager=mock_memory)
        return detector, mock_memory
    
    @pytest.mark.asyncio
    async def test_get_previous_ema_cold_start(self, detector_with_memory):
        """First user: No previous EMA should return None"""
        detector, mock_memory = detector_with_memory
        mock_memory.retrieve_relevant_memories.return_value = []
        
        ema = await detector._get_previous_ema(user_id="new_user")
        assert ema is None, "First user should have no previous EMA"
    
    @pytest.mark.asyncio
    async def test_get_previous_ema_with_ema_field(self, detector_with_memory):
        """Existing user with EMA field: Should return EMA value"""
        detector, mock_memory = detector_with_memory
        
        mock_memory_data = {
            'payload': {
                'emotional_intensity_ema': 0.75,
                'emotional_intensity': 0.70,
            }
        }
        mock_memory.retrieve_relevant_memories.return_value = [mock_memory_data]
        
        ema = await detector._get_previous_ema(user_id="existing_user")
        assert ema == 0.75, "Should return EMA field when available"
    
    @pytest.mark.asyncio
    async def test_get_previous_ema_backward_compat(self, detector_with_memory):
        """Old payload without EMA: Should fallback to raw intensity"""
        detector, mock_memory = detector_with_memory
        
        mock_memory_data = {
            'payload': {
                'emotional_intensity': 0.68,
                # No emotional_intensity_ema field!
            }
        }
        mock_memory.retrieve_relevant_memories.return_value = [mock_memory_data]
        
        ema = await detector._get_previous_ema(user_id="legacy_user")
        assert ema == 0.68, "Should fallback to raw intensity for old payloads"
    
    @pytest.mark.asyncio
    async def test_get_previous_ema_no_memory_manager(self):
        """No memory manager: Should return None gracefully"""
        detector = AdvancedEmotionDetector(memory_manager=None)
        
        ema = await detector._get_previous_ema(user_id="any_user")
        assert ema is None, "Should return None if memory manager unavailable"
    
    @pytest.mark.asyncio
    async def test_get_previous_ema_memory_error(self, detector_with_memory):
        """Memory retrieval error: Should return None gracefully"""
        detector, mock_memory = detector_with_memory
        mock_memory.retrieve_relevant_memories.side_effect = Exception("Memory error")
        
        ema = await detector._get_previous_ema(user_id="error_user")
        assert ema is None, "Should return None on retrieval error"
    
    @pytest.mark.asyncio
    async def test_get_previous_ema_empty_payload(self, detector_with_memory):
        """Empty payload: Should return None"""
        detector, mock_memory = detector_with_memory
        mock_memory.retrieve_relevant_memories.return_value = [
            {'payload': {}}  # Empty payload
        ]
        
        ema = await detector._get_previous_ema(user_id="empty_payload_user")
        assert ema is None, "Should return None for empty payload"
    
    @pytest.mark.asyncio
    async def test_get_previous_ema_zero_value(self, detector_with_memory):
        """EMA of 0.0 is valid: Should return 0.0, not None"""
        detector, mock_memory = detector_with_memory
        mock_memory.retrieve_relevant_memories.return_value = [
            {
                'payload': {
                    'emotional_intensity_ema': 0.0,
                }
            }
        ]
        
        ema = await detector._get_previous_ema(user_id="zero_ema_user")
        assert ema == 0.0, "Zero is valid EMA value"
        assert ema is not None
    
    @pytest.mark.asyncio
    async def test_get_previous_ema_one_value(self, detector_with_memory):
        """EMA of 1.0 is valid: Should return 1.0, not None"""
        detector, mock_memory = detector_with_memory
        mock_memory.retrieve_relevant_memories.return_value = [
            {
                'payload': {
                    'emotional_intensity_ema': 1.0,
                }
            }
        ]
        
        ema = await detector._get_previous_ema(user_id="max_ema_user")
        assert ema == 1.0, "1.0 is valid EMA value"
        assert ema is not None


class TestEMAIntegration:
    """Integration tests: EMA calculation + retrieval"""
    
    def test_ema_calculation_chain(self):
        """Multiple EMA calculations form a smoothed sequence"""
        detector = AdvancedEmotionDetector()
        
        # Simulate conversation
        intensities = [0.3, 0.9, 0.2, 0.8, 0.7]
        ema_values = []
        
        # First message (cold start)
        current_ema = detector._calculate_ema(current=intensities[0], previous_ema=None)
        ema_values.append(current_ema)
        
        # Subsequent messages (using previous EMA)
        for intensity in intensities[1:]:
            current_ema = detector._calculate_ema(current=intensity, previous_ema=current_ema)
            ema_values.append(current_ema)
        
        # Verify results
        assert len(ema_values) == len(intensities)
        assert ema_values[0] == 0.3, "First EMA should be raw value"
        
        # Second value should reflect smoothing
        alpha = 0.3
        expected_second = alpha * 0.9 + (1 - alpha) * 0.3
        assert abs(ema_values[1] - expected_second) < 0.001
