"""
🎭 Memory Priority Visualization - Quick Win Feature
Add visual indicators when high-priority memories influence responses
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryPriorityIndicators:
    """Add visual indicators for memory prioritization in conversations"""
    
    def __init__(self):
        self.priority_emojis = {
            "crisis": "🚨",
            "high": "🔴", 
            "important": "⭐",
            "personal": "💝",
            "achievement": "🏆",
            "support": "🤝"
        }
    
    def format_memory_context_with_indicators(self, memories: List[Dict[str, Any]]) -> str:
        """Format memory context with visual priority indicators"""
        if not memories:
            return ""
        
        context_parts = []
        high_priority_count = 0
        
        for memory in memories:
            content = memory.get('content', '')
            emotional_weight = memory.get('emotional_weight', 0.5)
            priority_marker = memory.get('priority_marker', '')
            
            # Add priority indicator
            if emotional_weight > 0.8 or 'HIGH PRIORITY' in priority_marker:
                indicator = self.priority_emojis.get('crisis', '🔴')
                context_parts.append(f"{indicator} [HIGH PRIORITY] {content}")
                high_priority_count += 1
            elif emotional_weight > 0.6 or 'IMPORTANT' in priority_marker:
                indicator = self.priority_emojis.get('important', '⭐')
                context_parts.append(f"{indicator} [IMPORTANT] {content}")
            else:
                context_parts.append(content)
        
        # Add summary header if high-priority memories are present
        if high_priority_count > 0:
            header = f"\n💫 Drawing from {high_priority_count} high-priority emotional memories:\n"
            return header + "\n".join(context_parts)
        
        return "\n".join(context_parts)
    
    def add_memory_influence_footer(self, response: str, memories_used: List[Dict[str, Any]]) -> str:
        """Add subtle footer indicating memory influence on response"""
        if not memories_used:
            return response
        
        high_priority_memories = [m for m in memories_used if m.get('emotional_weight', 0) > 0.7]
        
        if high_priority_memories:
            footer = f"\n\n💭 *Response influenced by {len(high_priority_memories)} high-priority emotional memories*"
            return response + footer
        
        return response
    
    def generate_memory_insight_snippet(self, user_id: str, memories_count: int, high_priority_count: int) -> str:
        """Generate insight snippet about memory prioritization"""
        if high_priority_count == 0:
            return ""
        
        percentage = (high_priority_count / memories_count) * 100 if memories_count > 0 else 0
        
        if high_priority_count == 1:
            return f"🎯 *1 high-priority memory helped shape this response*"
        else:
            return f"🎯 *{high_priority_count} high-priority memories ({percentage:.0f}%) helped shape this response*"