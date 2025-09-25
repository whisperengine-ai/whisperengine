"""
🎭 Enhanced Memory Priority Logging - Quick Win Feature
Real-time logging system for memory prioritization decisions
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class MemoryPriorityEvent(Enum):
    """Types of memory priority events to track"""
    CRISIS_DETECTED = "crisis_detected"
    HIGH_PRIORITY_STORED = "high_priority_stored" 
    PRIORITY_BOOST_APPLIED = "priority_boost_applied"
    EMOTIONAL_CONTEXT_ENHANCED = "emotional_context_enhanced"
    MEMORY_PRIORITIZED_IN_RETRIEVAL = "memory_prioritized_in_retrieval"
    CONVERSATION_MOMENTUM_DETECTED = "conversation_momentum_detected"

class MemoryPriorityLogger:
    """Enhanced logging for memory prioritization system"""
    
    def __init__(self):
        self.logger = logging.getLogger('memory.priority')
        self.logger.setLevel(logging.INFO)
    
    def log_priority_decision(
        self, 
        event: MemoryPriorityEvent, 
        user_id: str, 
        details: Dict[str, Any],
        emotional_weight: Optional[float] = None
    ):
        """Log memory prioritization decisions with rich context"""
        
        timestamp = datetime.now().isoformat()
        
        base_msg = f"🎭 PRIORITY-{event.value.upper()}: User {user_id[:8]}"
        
        if emotional_weight:
            base_msg += f" | Weight: {emotional_weight:.2f}"
        
        # Event-specific logging
        if event == MemoryPriorityEvent.CRISIS_DETECTED:
            crisis_emotions = details.get('emotions', [])
            self.logger.warning(f"{base_msg} | Crisis emotions detected: {crisis_emotions}")
            
        elif event == MemoryPriorityEvent.HIGH_PRIORITY_STORED:
            reason = details.get('reason', 'unknown')
            self.logger.info(f"{base_msg} | High priority storage: {reason}")
            
        elif event == MemoryPriorityEvent.PRIORITY_BOOST_APPLIED:
            boost_type = details.get('boost_type', 'unknown')
            boost_amount = details.get('boost_amount', 0.0)
            self.logger.info(f"{base_msg} | Boost applied: {boost_type} (+{boost_amount:.2f})")
            
        elif event == MemoryPriorityEvent.EMOTIONAL_CONTEXT_ENHANCED:
            context_type = details.get('context_type', 'unknown')
            enhancement_score = details.get('enhancement_score', 0.0)
            self.logger.info(f"{base_msg} | Context enhanced: {context_type} (score: {enhancement_score:.2f})")
            
        elif event == MemoryPriorityEvent.MEMORY_PRIORITIZED_IN_RETRIEVAL:
            retrieval_count = details.get('high_priority_count', 0)
            total_count = details.get('total_memories', 0)
            percentage = (retrieval_count / total_count * 100) if total_count > 0 else 0
            self.logger.info(f"{base_msg} | Retrieval prioritization: {retrieval_count}/{total_count} ({percentage:.0f}%) high-priority")
            
        elif event == MemoryPriorityEvent.CONVERSATION_MOMENTUM_DETECTED:
            momentum_type = details.get('momentum_type', 'unknown')
            momentum_strength = details.get('momentum_strength', 0.0)
            self.logger.info(f"{base_msg} | Conversation momentum: {momentum_type} (strength: {momentum_strength:.2f})")
    
    def log_memory_stats_summary(self, user_id: str, stats: Dict[str, Any]):
        """Log periodic memory prioritization statistics"""
        total_memories = stats.get('total_memories', 0)
        high_priority = stats.get('high_priority_count', 0) 
        priority_percentage = (high_priority / total_memories * 100) if total_memories > 0 else 0
        
        avg_emotional_weight = stats.get('avg_emotional_weight', 0.0)
        crisis_memories = stats.get('crisis_memories', 0)
        
        self.logger.info(
            f"📊 MEMORY-STATS: User {user_id[:8]} | "
            f"Total: {total_memories} | High Priority: {high_priority} ({priority_percentage:.0f}%) | "
            f"Avg Weight: {avg_emotional_weight:.2f} | Crisis: {crisis_memories}"
        )
    
    def log_system_health(self, system_stats: Dict[str, Any]):
        """Log system-wide memory prioritization health"""
        total_users = system_stats.get('total_users', 0)
        avg_priority_percentage = system_stats.get('avg_priority_percentage', 0.0)
        total_high_priority = system_stats.get('total_high_priority_memories', 0)
        
        self.logger.info(
            f"🏥 SYSTEM-HEALTH: Users: {total_users} | "
            f"Avg Priority: {avg_priority_percentage:.1f}% | "
            f"Total High Priority: {total_high_priority}"
        )

# Global priority logger instance
priority_logger = MemoryPriorityLogger()