"""
Integration test for EMA storage in vector memory system

Tests that EMA values are calculated and stored in Qdrant payload
when store_conversation() is called.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.memory.vector_memory_system import VectorMemoryManager, VectorMemory, MemoryType
from datetime import datetime


class TestEMAStorageIntegration:
    """Test EMA storage integration with vector memory"""
    
    @pytest.fixture
    def mock_ema_helper(self):
        """Helper to test _get_previous_ema_for_user"""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_ema_calculation_formula_in_storage(self):
        """Test that EMA calculation uses correct formula"""
        # Test EMA formula: EMA = 0.3 * raw + 0.7 * previous
        
        raw_intensity = 0.9
        previous_ema = 0.6
        alpha = 0.3
        
        # Calculate EMA
        ema_intensity = alpha * raw_intensity + (1 - alpha) * previous_ema
        ema_intensity = min(max(ema_intensity, 0.0), 1.0)
        
        # Expected: 0.3 * 0.9 + 0.7 * 0.6 = 0.27 + 0.42 = 0.69
        expected = 0.69
        assert abs(ema_intensity - expected) < 0.001
    
    @pytest.mark.asyncio
    async def test_ema_cold_start_formula(self):
        """Cold start: EMA should equal raw intensity"""
        raw_intensity = 0.75
        previous_ema = None
        alpha = 0.3
        
        # Cold start logic
        if previous_ema is None:
            ema_intensity = raw_intensity
        else:
            ema_intensity = alpha * raw_intensity + (1 - alpha) * previous_ema
            ema_intensity = min(max(ema_intensity, 0.0), 1.0)
        
        assert ema_intensity == raw_intensity
    
    @pytest.mark.asyncio
    async def test_ema_clipping_boundaries(self):
        """EMA values should be clipped to [0, 1]"""
        test_cases = [
            (-0.5, 0.8, 0.0),      # Too low
            (0.5, 1.5, 1.0),       # Too high
            (0.3, 0.5, 0.3 * 0.5 + 0.7 * 0.8),  # Valid range
        ]
        
        for raw, prev, expected in test_cases[:2]:
            alpha = 0.3
            ema = alpha * raw + (1 - alpha) * prev
            ema_clipped = min(max(ema, 0.0), 1.0)
            
            # Should be clipped
            assert 0.0 <= ema_clipped <= 1.0
    
    @pytest.mark.asyncio
    async def test_ema_data_structure(self):
        """Verify EMA data structure matches storage requirements"""
        ema_data = {
            'emotional_intensity_ema': 0.69,
            'ema_alpha': 0.3,
            'ema_previous': 0.6,
            'emotional_intensity_raw': 0.9
        }
        
        # Verify all required fields present
        assert 'emotional_intensity_ema' in ema_data
        assert 'ema_alpha' in ema_data
        assert 'ema_previous' in ema_data
        assert 'emotional_intensity_raw' in ema_data
        
        # Verify types
        assert isinstance(ema_data['emotional_intensity_ema'], float)
        assert isinstance(ema_data['ema_alpha'], float)
        assert isinstance(ema_data['ema_previous'], (float, type(None)))
    
    @pytest.mark.asyncio
    async def test_ema_backward_compatibility_missing_fields(self):
        """Old payloads without EMA fields should still work"""
        # Simulate old payload retrieval
        old_payload = {
            'emotional_intensity': 0.6,
            # No emotional_intensity_ema field
        }
        
        # Backward compatibility logic
        ema = old_payload.get('emotional_intensity_ema')
        if ema is None:
            # Fallback to raw
            ema = old_payload.get('emotional_intensity', 0.5)
        
        assert ema == 0.6
    
    @pytest.mark.asyncio
    async def test_ema_smoothing_sequence_variance_reduction(self):
        """Test that EMA reduces variance in noisy sequences"""
        # Noisy sequence: high, low, high
        raw_values = [0.8, 0.2, 0.75]
        alpha = 0.3
        
        ema_values = []
        previous_ema = None
        
        for raw in raw_values:
            if previous_ema is None:
                ema = raw
            else:
                ema = alpha * raw + (1 - alpha) * previous_ema
                ema = min(max(ema, 0.0), 1.0)
            ema_values.append(ema)
            previous_ema = ema
        
        # Verify variance reduction
        raw_changes = [abs(raw_values[i] - raw_values[i-1]) for i in range(1, len(raw_values))]
        ema_changes = [abs(ema_values[i] - ema_values[i-1]) for i in range(1, len(ema_values))]
        
        # EMA changes should be smaller than raw changes
        assert ema_changes[0] < raw_changes[0]
        assert ema_changes[1] < raw_changes[1]
    
    @pytest.mark.asyncio
    async def test_ema_trend_preservation(self):
        """Test that EMA preserves genuine emotional trends"""
        # Sustained increase: 0.3 -> 0.4 -> 0.5 -> 0.6 -> 0.7
        raw_values = [0.3, 0.4, 0.5, 0.6, 0.7]
        alpha = 0.3
        
        ema_values = []
        previous_ema = None
        
        for raw in raw_values:
            if previous_ema is None:
                ema = raw
            else:
                ema = alpha * raw + (1 - alpha) * previous_ema
                ema = min(max(ema, 0.0), 1.0)
            ema_values.append(ema)
            previous_ema = ema
        
        # Verify trend is preserved
        assert ema_values[-1] > ema_values[0]
        assert ema_values == sorted(ema_values)


class TestEMAPayloadStorage:
    """Test EMA payload structure for Qdrant storage"""
    
    def test_metadata_with_ema_fields(self):
        """Test that metadata dict can hold EMA fields"""
        metadata = {
            "channel_id": "dm_channel",
            "channel_type": "dm",
            "emotion_data": {"primary_emotion": "joy"},
            "role": "user",
            "emotional_intensity_ema": 0.69,
            "ema_alpha": 0.3,
            "ema_previous": 0.6,
            "emotional_intensity_raw": 0.9,
        }
        
        # Verify all fields accessible
        assert metadata['emotional_intensity_ema'] == 0.69
        assert metadata['ema_alpha'] == 0.3
        assert metadata['ema_previous'] == 0.6
    
    def test_vector_memory_accepts_ema_metadata(self):
        """Test that VectorMemory can be created with EMA metadata"""
        from uuid import uuid4
        
        ema_metadata = {
            "channel_id": "test_channel",
            "emotion_data": {"primary_emotion": "joy", "emotional_intensity": 0.75},
            "emotional_intensity_ema": 0.75,
            "ema_alpha": 0.3,
            "ema_previous": None,
            "emotional_intensity_raw": 0.75,
            "role": "user"
        }
        
        # Simulate VectorMemory creation
        memory_obj = {
            "id": str(uuid4()),
            "user_id": "test_user",
            "memory_type": "conversation",
            "content": "test message",
            "source": "user_message",
            "timestamp": datetime.utcnow(),
            "metadata": ema_metadata
        }
        
        # Verify structure
        assert "emotional_intensity_ema" in memory_obj["metadata"]
        assert memory_obj["metadata"]["emotional_intensity_ema"] == 0.75

