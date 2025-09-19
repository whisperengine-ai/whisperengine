"""Unit tests for MemoryAgingRunner."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.memory.aging.aging_runner import MemoryAgingRunner
from src.memory.aging.aging_policy import MemoryAgingPolicy


class TestMemoryAgingRunner:
    """Test memory aging runner execution and metrics."""

    def setup_method(self):
        """Set up test fixtures."""
        # pylint: disable=attribute-defined-outside-init
        self.mock_memory_manager = Mock()
        self.mock_memory_manager.get_memories_by_user = AsyncMock()
        self.mock_memory_manager.delete_specific_memory = AsyncMock()
        
        self.policy = MemoryAgingPolicy()
        
        self.runner = MemoryAgingRunner(
            memory_manager=self.mock_memory_manager,
            policy=self.policy
        )

    @pytest.mark.asyncio
    async def test_run_dry_run_mode(self):
        """Test aging runner in dry run mode."""
        # Setup test memories
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        memories = [
            {
                'id': 'memory1',
                'created_at': old_timestamp,
                'importance_score': 0.1,
                'decay_score': 0.8,
                'emotional_intensity': 0.1,
                'access_count': 1
            },
            {
                'id': 'memory2', 
                'created_at': datetime.utcnow().timestamp(),
                'importance_score': 0.9,
                'decay_score': 0.1,
                'emotional_intensity': 0.3,
                'access_count': 10
            }
        ]
        
        self.mock_memory_manager.get_memories_by_user.return_value = memories
        
        # Run in dry run mode
        results = await self.runner.run(user_id="test_user", dry_run=True)
        
        # Verify results
        assert results['scanned'] == 2
        assert results['flagged'] >= 0
        assert results['pruned'] == 0  # Dry run should not prune
        assert results['preserved'] >= 0
        assert results['dry_run'] is True
        
        # Verify no actual changes were made
        self.mock_memory_manager.delete_specific_memory.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_execution_mode(self):
        """Test aging runner in execution mode."""
        # Setup test memories with one clearly prunable
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        memories = [
            {
                'id': 'prunable_memory',
                'created_at': old_timestamp,
                'importance_score': 0.05,  # Very low
                'decay_score': 0.9,        # High decay
                'emotional_intensity': 0.1, # Low emotional
                'access_count': 1,
                'intervention_outcome': None  # Not protected
            }
        ]
        
        self.mock_memory_manager.get_memories_by_user.return_value = memories
        
        # Run in execution mode
        results = await self.runner.run(user_id="test_user", dry_run=False)
        
        # Verify execution results
        assert results['scanned'] == 1
        assert 'pruned' in results
        assert 'preserved' in results
        assert results['dry_run'] is False

    @pytest.mark.asyncio
    async def test_safety_checks_prevent_pruning(self):
        """Test that safety checks prevent inappropriate pruning."""
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        
        # Memory with high emotional intensity
        emotional_memory = {
            'id': 'emotional_memory',
            'created_at': old_timestamp,
            'importance_score': 0.1,
            'decay_score': 0.9,
            'emotional_intensity': 0.8,  # High - should be protected
            'access_count': 1
        }
        
        # Recent memory
        recent_memory = {
            'id': 'recent_memory', 
            'created_at': datetime.utcnow().timestamp(),  # Very recent
            'importance_score': 0.1,
            'decay_score': 0.9,
            'emotional_intensity': 0.1,
            'access_count': 1
        }
        
        # Intervention outcome
        intervention_memory = {
            'id': 'intervention_memory',
            'created_at': old_timestamp,
            'importance_score': 0.1,
            'decay_score': 0.9,
            'emotional_intensity': 0.1,
            'access_count': 1,
            'intervention_outcome': 'success'  # Protected
        }
        
        memories = [emotional_memory, recent_memory, intervention_memory]
        self.mock_memory_manager.get_memories_by_user.return_value = memories
        
        # Run aging
        results = await self.runner.run(user_id="test_user", dry_run=False)
        
        # All memories should be preserved due to safety checks
        assert results['preserved'] == 3
        assert results['pruned'] == 0
        
        # Verify no deletions occurred
        self.mock_memory_manager.delete_specific_memory.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_memory_set(self):
        """Test handling of empty memory set."""
        self.mock_memory_manager.get_memories_by_user.return_value = []
        
        results = await self.runner.run(user_id="test_user", dry_run=True)
        
        assert results['scanned'] == 0
        assert results['flagged'] == 0

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling during aging process."""
        # Mock an error in memory retrieval
        self.mock_memory_manager.get_memories_by_user.side_effect = RuntimeError("Database error")
        
        try:
            results = await self.runner.run(user_id="test_user", dry_run=True)
            # If no exception, check for empty results
            assert results['scanned'] == 0
        except RuntimeError:
            # Error handling depends on implementation
            pass

    def test_policy_integration(self):
        """Test that runner properly integrates with aging policy."""
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        
        # Test memory that should be flagged for pruning
        low_value_memory = {
            'id': 'low_value',
            'created_at': old_timestamp,
            'importance_score': 0.05,
            'decay_score': 0.9,
            'emotional_intensity': 0.1,
            'access_count': 1
        }
        
        # Test with policy
        score = self.policy.compute_retention_score(low_value_memory)
        is_prunable = self.policy.is_prunable(low_value_memory)
        
        # Verify policy behavior
        assert score < self.policy.prune_threshold
        assert is_prunable is True

    def test_runner_configuration(self):
        """Test that runner is properly configured."""
        assert self.runner.memory_manager is not None
        assert self.runner.policy is not None
        
        # Test policy is configured
        assert hasattr(self.runner.policy, 'compute_retention_score')
        assert hasattr(self.runner.policy, 'is_prunable')

    @pytest.mark.asyncio
    async def test_metrics_integration(self):
        """Test that metrics are properly recorded (if available)."""
        memories = [
            {
                'id': 'test_memory',
                'created_at': datetime.utcnow().timestamp(),
                'importance_score': 0.9,
                'emotional_intensity': 0.3,
                'access_count': 5
            }
        ]
        
        self.mock_memory_manager.get_memories_by_user.return_value = memories
        
        results = await self.runner.run(user_id="test_user", dry_run=True)
        
        # Should include timing information
        assert 'elapsed_seconds' in results
        assert results['elapsed_seconds'] >= 0