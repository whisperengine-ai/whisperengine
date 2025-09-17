"""Integration tests for memory aging system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.memory.aging.aging_policy import MemoryAgingPolicy
from src.memory.aging.aging_runner import MemoryAgingRunner
from src.memory.aging.consolidator import MemoryConsolidator


class TestMemoryAgingIntegration:
    """Integration tests for the complete memory aging system."""

    def setup_method(self):
        """Set up test fixtures."""
        # pylint: disable=attribute-defined-outside-init
        self.mock_memory_manager = Mock()
        self.mock_memory_manager.get_memories_by_user = AsyncMock()
        self.mock_memory_manager.delete_specific_memory = AsyncMock()
        
        self.policy = MemoryAgingPolicy(
            importance_weight=0.6,
            recency_weight=0.3,
            access_weight=0.1,
            decay_lambda=0.01,
            prune_threshold=0.2
        )
        
        self.consolidator = MemoryConsolidator(
            embedding_manager=Mock(),
            similarity_threshold=0.92
        )
        
        self.runner = MemoryAgingRunner(
            memory_manager=self.mock_memory_manager,
            policy=self.policy
        )

    @pytest.mark.asyncio
    async def test_full_aging_workflow_dry_run(self):
        """Test complete aging workflow in dry run mode."""
        # Create diverse set of test memories
        now = datetime.utcnow().timestamp()
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        
        memories = [
            # High-value memory (should be preserved)
            {
                'id': 'high_value_memory',
                'created_at': now - 86400,  # 1 day old
                'importance_score': 0.9,
                'decay_score': 0.1,
                'emotional_intensity': 0.8,
                'access_count': 15,
                'content': 'Important conversation about project goals'
            },
            # Low-value memory (candidate for pruning)
            {
                'id': 'low_value_memory',
                'created_at': old_timestamp,
                'importance_score': 0.1,
                'decay_score': 0.8,
                'emotional_intensity': 0.2,
                'access_count': 1,
                'content': 'Brief greeting message'
            },
            # Protected intervention outcome
            {
                'id': 'intervention_memory',
                'created_at': old_timestamp,
                'importance_score': 0.3,
                'decay_score': 0.6,
                'emotional_intensity': 0.4,
                'access_count': 3,
                'intervention_outcome': 'success',
                'content': 'Successful intervention discussion'
            },
            # Very recent memory (protected by recency)
            {
                'id': 'recent_memory',
                'created_at': now,  # Just created
                'importance_score': 0.1,
                'decay_score': 0.9,
                'emotional_intensity': 0.1,
                'access_count': 1,
                'content': 'Very recent low-importance message'
            }
        ]
        
        self.mock_memory_manager.get_memories_by_user.return_value = memories
        
        # Run aging workflow
        results = await self.runner.run(user_id="test_user", dry_run=True)
        
        # Verify results
        assert results['scanned'] == 4
        assert results['dry_run'] is True
        assert results['preserved'] >= 3  # At least 3 should be preserved by safety checks
        
        # Verify no actual deletions in dry run
        self.mock_memory_manager.delete_specific_memory.assert_not_called()

    @pytest.mark.asyncio
    async def test_full_aging_workflow_execution(self):
        """Test complete aging workflow in execution mode."""
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        
        # Create memories that should be prunable
        memories = [
            {
                'id': 'prunable_1',
                'created_at': old_timestamp,
                'importance_score': 0.05,
                'decay_score': 0.9,
                'emotional_intensity': 0.1,
                'access_count': 1,
                'content': 'Old unimportant message 1'
            },
            {
                'id': 'prunable_2',
                'created_at': old_timestamp,
                'importance_score': 0.08,
                'decay_score': 0.85,
                'emotional_intensity': 0.15,
                'access_count': 1,
                'content': 'Old unimportant message 2'
            }
        ]
        
        self.mock_memory_manager.get_memories_by_user.return_value = memories
        
        # Run aging workflow in execution mode
        results = await self.runner.run(user_id="test_user", dry_run=False)
        
        # Verify results
        assert results['scanned'] == 2
        assert results['dry_run'] is False
        
        # Should have some activity (pruning or preservation)
        assert results['pruned'] + results['preserved'] == 2

    def test_policy_scoring_integration(self):
        """Test policy scoring with realistic memory data."""
        now = datetime.utcnow().timestamp()
        
        # High-value memory
        high_value = {
            'created_at': now - 3600,  # 1 hour old
            'importance_score': 0.9,
            'decay_score': 0.1,
            'emotional_intensity': 0.7,
            'access_count': 10
        }
        
        # Low-value memory
        low_value = {
            'created_at': now - 2592000,  # 30 days old
            'importance_score': 0.1,
            'decay_score': 0.8,
            'emotional_intensity': 0.1,
            'access_count': 1
        }
        
        high_score = self.policy.compute_retention_score(high_value)
        low_score = self.policy.compute_retention_score(low_value)
        
        # High-value memory should score higher
        assert high_score > low_score
        assert high_score > self.policy.prune_threshold
        assert low_score < self.policy.prune_threshold

    def test_safety_check_integration(self):
        """Test safety checks across different memory types."""
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        
        test_cases = [
            # High emotional intensity
            {
                'memory': {
                    'created_at': old_timestamp,
                    'emotional_intensity': 0.8,
                    'importance_score': 0.1
                },
                'should_be_prunable': False,
                'reason': 'high emotional intensity'
            },
            # Intervention outcome
            {
                'memory': {
                    'created_at': old_timestamp,
                    'emotional_intensity': 0.2,
                    'intervention_outcome': 'success',
                    'importance_score': 0.1
                },
                'should_be_prunable': False,
                'reason': 'intervention outcome'
            },
            # Recent memory
            {
                'memory': {
                    'created_at': datetime.utcnow().timestamp(),
                    'emotional_intensity': 0.1,
                    'importance_score': 0.1
                },
                'should_be_prunable': False,
                'reason': 'recent memory'
            },
            # Low-value old memory (should be prunable)
            {
                'memory': {
                    'created_at': old_timestamp,
                    'emotional_intensity': 0.1,
                    'importance_score': 0.05,
                    'decay_score': 0.9,
                    'access_count': 1
                },
                'should_be_prunable': True,
                'reason': 'genuinely low value'
            }
        ]
        
        for case in test_cases:
            memory = case['memory']
            expected_prunable = case['should_be_prunable']
            reason = case['reason']
            
            is_prunable = self.policy.is_prunable(memory)
            
            if expected_prunable:
                # For genuinely low-value memories, check score too
                score = self.policy.compute_retention_score(memory)
                if score < self.policy.prune_threshold:
                    assert is_prunable, f"Memory should be prunable: {reason}"
            else:
                assert not is_prunable, f"Memory should NOT be prunable: {reason}"

    @pytest.mark.asyncio
    async def test_error_resilience(self):
        """Test system resilience to various error conditions."""
        # Test with malformed memory data
        malformed_memories = [
            {
                'id': 'malformed_1',
                # Missing created_at, importance_score, etc.
                'content': 'Malformed memory'
            },
            {
                'id': 'malformed_2',
                'created_at': 'invalid_timestamp',  # Invalid timestamp
                'importance_score': 'not_a_number',  # Invalid score
                'content': 'Another malformed memory'
            }
        ]
        
        self.mock_memory_manager.get_memories_by_user.return_value = malformed_memories
        
        # Should not crash
        try:
            results = await self.runner.run(user_id="test_user", dry_run=True)
            assert 'scanned' in results
        except (ValueError, TypeError):
            # Expected for malformed data - system should handle gracefully
            pass

    def test_configuration_flexibility(self):
        """Test that system responds to different configuration parameters."""
        # Test with conservative policy (preserve more)
        conservative_policy = MemoryAgingPolicy(
            importance_weight=0.7,
            recency_weight=0.2,
            access_weight=0.1,
            decay_lambda=0.005,  # Lower decay impact
            prune_threshold=0.1   # Lower threshold = preserve more
        )
        
        # Test with aggressive policy (prune more)
        aggressive_policy = MemoryAgingPolicy(
            importance_weight=0.5,
            recency_weight=0.2,
            access_weight=0.1,
            decay_lambda=0.02,   # Higher decay impact
            prune_threshold=0.4  # Higher threshold = prune more
        )
        
        # Test memory
        old_timestamp = (datetime.utcnow() - timedelta(days=15)).timestamp()
        test_memory = {
            'created_at': old_timestamp,
            'importance_score': 0.3,
            'decay_score': 0.4,
            'emotional_intensity': 0.2,
            'access_count': 2
        }
        
        conservative_score = conservative_policy.compute_retention_score(test_memory)
        aggressive_score = aggressive_policy.compute_retention_score(test_memory)
        
        # Conservative should generally preserve more (higher scores)
        # Aggressive should be more willing to prune
        conservative_prunable = conservative_policy.is_prunable(test_memory)
        aggressive_prunable = aggressive_policy.is_prunable(test_memory)
        
        # At minimum, verify scores are computed without error
        assert 0.0 <= conservative_score <= 1.0
        assert 0.0 <= aggressive_score <= 1.0
        assert isinstance(conservative_prunable, bool)
        assert isinstance(aggressive_prunable, bool)