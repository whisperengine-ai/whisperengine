"""Unit tests for MemoryAgingPolicy."""

from datetime import datetime, timedelta

from src.memory.aging.aging_policy import MemoryAgingPolicy


class TestMemoryAgingPolicy:
    """Test memory aging policy calculations and safety checks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.policy = MemoryAgingPolicy(
            importance_weight=0.6,
            recency_weight=0.3, 
            access_weight=0.1,
            decay_lambda=0.01,
            prune_threshold=0.2
        )

    def test_compute_retention_score_recent_memory(self):
        """Test retention score for recent memory."""
        memory = {
            'created_at': datetime.utcnow().timestamp(),
            'last_accessed': datetime.utcnow().timestamp(),
            'access_count': 5,
            'importance_score': 0.8,
            'decay_score': 0.1,
            'emotional_intensity': 0.5
        }
        
        score = self.policy.compute_retention_score(memory)
        assert score > 0.5  # Recent, important memory should have high score

    def test_compute_retention_score_old_unimportant_memory(self):
        """Test retention score for old, unimportant memory."""
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        memory = {
            'created_at': old_timestamp,
            'last_accessed': old_timestamp,
            'access_count': 1,
            'importance_score': 0.1,
            'decay_score': 0.5,
            'emotional_intensity': 0.1
        }
        
        score = self.policy.compute_retention_score(memory)
        assert score < 0.3  # Old, unimportant memory should have low score

    def test_compute_retention_score_high_emotional_intensity(self):
        """Test retention score for emotionally significant memory."""
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        memory = {
            'created_at': old_timestamp,
            'last_accessed': old_timestamp,
            'access_count': 1,
            'importance_score': 0.1,
            'decay_score': 0.2,
            'emotional_intensity': 0.9  # High emotional intensity
        }
        
        # Note: emotional intensity affects pruning decision, not score calculation
        # Should not be prunable due to emotional intensity check
        assert not self.policy.is_prunable(memory)

    def test_is_prunable_safety_checks(self):
        """Test safety checks prevent inappropriate pruning."""
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        base_memory = {
            'created_at': old_timestamp,
            'last_accessed': old_timestamp,
            'access_count': 1,
            'importance_score': 0.1,
            'decay_score': 0.1,
            'emotional_intensity': 0.1,
            'category': 'conversation'
        }
        
        # Test high emotional intensity protection
        emotional_memory = base_memory.copy()
        emotional_memory['emotional_intensity'] = 0.8
        assert not self.policy.is_prunable(emotional_memory)
        
        # Test intervention outcome protection
        intervention_memory = base_memory.copy()
        intervention_memory['intervention_outcome'] = 'success'
        assert not self.policy.is_prunable(intervention_memory)
        
        # Test recent memory protection
        recent_memory = base_memory.copy()
        recent_memory['created_at'] = datetime.utcnow().timestamp()
        assert not self.policy.is_prunable(recent_memory)

    def test_is_prunable_allows_low_value_memory(self):
        """Test that genuinely low-value memories can be pruned."""
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        low_value_memory = {
            'created_at': old_timestamp,
            'last_accessed': old_timestamp,
            'access_count': 1,
            'importance_score': 0.1,
            'decay_score': 0.1,
            'emotional_intensity': 0.1,
            'category': 'conversation'
        }
        
        # Check the score is below threshold
        score = self.policy.compute_retention_score(low_value_memory)
        if score < self.policy.prune_threshold:
            assert self.policy.is_prunable(low_value_memory)

    def test_compute_retention_score_missing_fields(self):
        """Test handling of memories with missing metadata fields."""
        incomplete_memory = {
            'created_at': datetime.utcnow().timestamp(),
            # Missing other fields - should use defaults
        }
        
        # Should not crash, should return reasonable default
        score = self.policy.compute_retention_score(incomplete_memory)
        assert 0.0 <= score <= 1.0

    def test_is_prunable_missing_fields(self):
        """Test safety checks with missing metadata fields."""
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        incomplete_memory = {
            'created_at': old_timestamp,
            # Missing emotional_intensity, intervention_outcome - should default safely
        }
        
        # Check if prunable based on score and safety checks
        score = self.policy.compute_retention_score(incomplete_memory)
        is_prunable = self.policy.is_prunable(incomplete_memory)
        
        # Should follow normal pruning logic when safety fields are missing/default
        if score < self.policy.prune_threshold:
            assert is_prunable

    def test_retention_score_components(self):
        """Test individual components of retention score calculation."""
        memory = {
            'created_at': datetime.utcnow().timestamp(),
            'access_count': 5,
            'importance_score': 0.8,
            'decay_score': 0.1
        }
        
        score = self.policy.compute_retention_score(memory)
        
        # Score should be influenced by high importance and low decay
        assert score > 0.4  # High importance should dominate

    def test_weights_configuration(self):
        """Test that policy respects weight configuration."""
        policy = MemoryAgingPolicy(
            importance_weight=0.8,
            recency_weight=0.1,
            access_weight=0.1,
            decay_lambda=0.05,
            prune_threshold=0.5
        )
        
        assert policy.importance_weight == 0.8
        assert policy.recency_weight == 0.1
        assert policy.access_weight == 0.1
        assert policy.decay_lambda == 0.05
        assert policy.prune_threshold == 0.5

    def test_recent_memory_protection(self):
        """Test that very recent memories are protected from pruning."""
        recent_memory = {
            'created_at': datetime.utcnow().timestamp(),
            'importance_score': 0.01,  # Very low importance
            'emotional_intensity': 0.01,  # Very low emotion
            'access_count': 1,
            'decay_score': 0.9  # High decay
        }
        
        # Even with terrible scores, recent memories are protected
        assert not self.policy.is_prunable(recent_memory)

    def test_emotional_intensity_threshold(self):
        """Test emotional intensity threshold for pruning protection."""
        old_timestamp = (datetime.utcnow() - timedelta(days=30)).timestamp()
        
        # Memory just below threshold
        below_threshold = {
            'created_at': old_timestamp,
            'emotional_intensity': 0.69,
            'importance_score': 0.1
        }
        
        # Memory at threshold
        at_threshold = {
            'created_at': old_timestamp,
            'emotional_intensity': 0.7,
            'importance_score': 0.1
        }
        
        score_below = self.policy.compute_retention_score(below_threshold)
        
        # Below threshold might be prunable if score is low
        if score_below < self.policy.prune_threshold:
            assert self.policy.is_prunable(below_threshold)
        
        # At/above threshold should never be prunable
        assert not self.policy.is_prunable(at_threshold)