"""Memory aging/retention policy logic for scoring and pruning decisions."""

from datetime import datetime

class MemoryAgingPolicy:
    def __init__(self, importance_weight=0.6, recency_weight=0.3, access_weight=0.1, decay_lambda=0.01, prune_threshold=0.2):
        self.importance_weight = importance_weight
        self.recency_weight = recency_weight
        self.access_weight = access_weight
        self.decay_lambda = decay_lambda
        self.prune_threshold = prune_threshold

    def compute_retention_score(self, memory: dict) -> float:
        """Returns a score; below threshold means candidate for pruning/consolidation."""
        importance = float(memory.get("importance_score", 0.5))
        now = datetime.utcnow().timestamp()
        created = memory.get("created_at")
        if created is None:
            recency = 1.0
        else:
            age_days = max((now - float(created)) / 86400, 0.01)
            recency = 1.0 / (1.0 + age_days)
        access_count = float(memory.get("access_count", 1))
        access = min(access_count / 10.0, 1.0)
        decay = float(memory.get("decay_score", 0.0))
        score = (
            self.importance_weight * importance +
            self.recency_weight * recency +
            self.access_weight * access -
            self.decay_lambda * decay
        )
        return score

    def is_prunable(self, memory: dict) -> bool:
        """Check if memory is candidate for pruning, with safety checks."""
        # Never prune high emotional intensity memories
        if memory.get("emotional_intensity", 0.0) >= 0.7:
            return False
        
        # Never prune intervention outcomes
        if memory.get("intervention_outcome") in {"success", "pending_followup"}:
            return False
            
        # Never prune very recent memories (< 1 day old)
        created = memory.get("created_at")
        if created:
            age_hours = (datetime.utcnow().timestamp() - float(created)) / 3600
            if age_hours < 24:
                return False
        
        return self.compute_retention_score(memory) < self.prune_threshold
