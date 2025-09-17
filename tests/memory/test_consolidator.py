"""Unit tests for MemoryConsolidator."""

import pytest
from unittest.mock import Mock

from src.memory.aging.consolidator import MemoryConsolidator


class TestMemoryConsolidator:
    """Test memory consolidation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # pylint: disable=attribute-defined-outside-init
        self.mock_embedding_manager = Mock()
        self.consolidator = MemoryConsolidator(
            embedding_manager=self.mock_embedding_manager,
            similarity_threshold=0.92
        )

    @pytest.mark.asyncio
    async def test_consolidate_empty_memories(self):
        """Test consolidation with empty memory list."""
        memories = []
        
        result = await self.consolidator.consolidate(memories)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_consolidate_single_memory(self):
        """Test consolidation with single memory."""
        memories = [
            {
                'id': 'memory1',
                'content': 'Single memory for testing',
                'importance_score': 0.3
            }
        ]
        
        result = await self.consolidator.consolidate(memories)
        
        # Single memory should be returned as-is
        assert len(result) == 1
        assert result[0]['id'] == 'memory1'

    @pytest.mark.asyncio
    async def test_consolidate_multiple_memories(self):
        """Test consolidation with multiple memories."""
        memories = [
            {
                'id': 'memory1',
                'content': 'First memory about cats',
                'importance_score': 0.2
            },
            {
                'id': 'memory2', 
                'content': 'Second memory about cats',
                'importance_score': 0.3
            },
            {
                'id': 'memory3',
                'content': 'Memory about dogs',
                'importance_score': 0.25
            }
        ]
        
        result = await self.consolidator.consolidate(memories)
        
        # Should create consolidated memory
        assert len(result) == 1
        consolidated = result[0]
        assert consolidated['type'] == 'consolidated'
        assert consolidated['original_count'] == 3
        assert len(consolidated['original_ids']) == 3

    @pytest.mark.asyncio
    async def test_consolidation_threshold_configuration(self):
        """Test that consolidator respects similarity threshold."""
        # Test with different threshold
        high_threshold_consolidator = MemoryConsolidator(
            embedding_manager=self.mock_embedding_manager,
            similarity_threshold=0.99
        )
        
        assert high_threshold_consolidator.similarity_threshold == 0.99

    def test_consolidator_initialization(self):
        """Test consolidator initialization."""
        consolidator = MemoryConsolidator(
            embedding_manager=self.mock_embedding_manager
        )
        
        assert consolidator.embedding_manager is not None
        assert consolidator.similarity_threshold == 0.92  # Default value

    @pytest.mark.asyncio
    async def test_consolidate_preserves_metadata(self):
        """Test that consolidation preserves important metadata."""
        memories = [
            {
                'id': 'memory1',
                'content': 'First memory',
                'importance_score': 0.2,
                'emotional_intensity': 0.3,
                'user_id': 'test_user'
            },
            {
                'id': 'memory2',
                'content': 'Second memory', 
                'importance_score': 0.3,
                'emotional_intensity': 0.4,
                'user_id': 'test_user'
            }
        ]
        
        result = await self.consolidator.consolidate(memories)
        
        # Should have consolidated result
        assert len(result) == 1
        consolidated = result[0]
        
        # Check metadata preservation
        assert 'original_ids' in consolidated
        assert 'original_count' in consolidated
        assert consolidated['original_count'] == 2

    def test_embedding_manager_integration(self):
        """Test integration with embedding manager."""
        # This tests the interface, not the implementation
        # since consolidation logic is currently a placeholder
        
        assert self.consolidator.embedding_manager is self.mock_embedding_manager
        
        # Future implementation would use embedding_manager.get_similarity()
        # or similar methods for actual semantic clustering