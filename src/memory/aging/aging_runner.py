"""Batch runner for memory aging, decay, and pruning."""

import time
from src.memory.aging.aging_policy import MemoryAgingPolicy

try:
    from src.metrics import metrics_collector as metrics
except ImportError:
    metrics = None

class MemoryAgingRunner:
    def __init__(self, memory_manager, policy: MemoryAgingPolicy):
        self.memory_manager = memory_manager
        self.policy = policy

    async def run(self, user_id: str, dry_run: bool = True):
        """Run aging cycle on user's memories with metrics tracking."""
        start = time.time()
        
        if metrics:
            metrics.incr("memory_aging_runs_started", user_id=user_id)
        
        all_memories = await self.memory_manager.get_memories_by_user(user_id)
        scanned, flagged, pruned, preserved = 0, 0, 0, 0
        
        for mem in all_memories:
            scanned += 1
            if metrics:
                metrics.incr("memories_scanned", user_id=user_id)
                
            if self.policy.is_prunable(mem):
                flagged += 1
                if metrics:
                    metrics.incr("memories_flagged_low_value", user_id=user_id)
                    
                if not dry_run:
                    await self.memory_manager.delete_specific_memory(mem["id"])
                    pruned += 1
                    if metrics:
                        metrics.incr("memories_pruned", user_id=user_id)
            else:
                preserved += 1
                if metrics:
                    metrics.incr("high_value_memories_preserved", user_id=user_id)
        
        elapsed = time.time() - start
        if metrics:
            metrics.record_timing("memory_aging_run_seconds", elapsed, user_id=user_id)
        
        return {
            "user_id": user_id,
            "scanned": scanned,
            "flagged": flagged,
            "pruned": pruned,
            "preserved": preserved,
            "elapsed_seconds": elapsed,
            "dry_run": dry_run
        }
