"""
Memory Importance Engine
========================

Evaluates and ranks memory importance based on multiple factors including
recency, frequency, emotional intensity, and semantic relevance.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import math

logger = logging.getLogger(__name__)


@dataclass
class MemoryImportance:
    """Memory importance scoring result"""
    memory_id: str
    importance_score: float  # 0.0 to 1.0
    factors: Dict[str, float]
    reasoning: str


class MemoryImportanceEngine:
    """Evaluates memory importance using multiple weighted factors"""
    
    def __init__(self):
        # Importance factor weights
        self.weights = {
            'recency': 0.25,       # How recent the memory is
            'frequency': 0.20,     # How often referenced/similar memories appear
            'emotional_intensity': 0.30,  # Emotional significance
            'semantic_relevance': 0.25    # Relevance to user patterns
        }
    
    async def calculate_memory_importance(
        self, 
        memories: List[Dict[str, Any]], 
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[MemoryImportance]:
        """Calculate importance for multiple memories (alias for rank_memories_by_importance)"""
        return await self.rank_memories_by_importance(memories, user_context)
    
    async def identify_core_memories(
        self, 
        user_id: str, 
        limit: int = 10, 
        memory_manager=None
    ) -> List[Dict[str, Any]]:
        """Identify the most important core memories for a user"""
        # This would need access to all user memories to rank them
        # For now, return empty list since we need memory_manager integration
        return []
    
    def get_importance_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get importance statistics for a user"""
        # Placeholder - would need to track per-user statistics
        return {
            "total_memories_analyzed": 0,
            "high_importance_count": 0,
            "medium_importance_count": 0,
            "low_importance_count": 0,
            "average_importance_score": 0.0
        }
    
    async def auto_adjust_importance(self, user_id: str, memory_manager=None):
        """Automatically adjust importance scores based on usage patterns"""
        # Placeholder for auto-adjustment logic
        pass
    
    async def evaluate_memory_importance(
        self, 
        memory: Dict[str, Any], 
        user_context: Optional[Dict[str, Any]] = None
    ) -> MemoryImportance:
        """Evaluate importance of a single memory"""
        
        try:
            factors = {}
            
            # Recency factor (more recent = more important initially)
            factors['recency'] = self._calculate_recency_score(memory.get('timestamp'))
            
            # Emotional intensity factor
            factors['emotional_intensity'] = self._calculate_emotional_score(memory)
            
            # Frequency factor (would need access to similar memories)
            factors['frequency'] = self._calculate_frequency_score(memory, user_context)
            
            # Semantic relevance factor
            factors['semantic_relevance'] = self._calculate_semantic_relevance(memory, user_context)
            
            # Calculate weighted importance score
            importance_score = sum(
                factors[factor] * self.weights[factor] 
                for factor in factors
            )
            
            # Generate reasoning
            reasoning = self._generate_importance_reasoning(factors, importance_score)
            
            return MemoryImportance(
                memory_id=memory.get('id', 'unknown'),
                importance_score=importance_score,
                factors=factors,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error evaluating memory importance: {e}")
            return MemoryImportance(
                memory_id=memory.get('id', 'unknown'),
                importance_score=0.5,  # Default neutral importance
                factors={},
                reasoning="Error during evaluation"
            )
    
    async def rank_memories_by_importance(
        self, 
        memories: List[Dict[str, Any]], 
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[MemoryImportance]:
        """Rank a list of memories by importance"""
        
        importance_results = []
        for memory in memories:
            importance = await self.evaluate_memory_importance(memory, user_context)
            importance_results.append(importance)
        
        # Sort by importance score (highest first)
        importance_results.sort(key=lambda x: x.importance_score, reverse=True)
        
        return importance_results
    
    def _calculate_recency_score(self, timestamp: Optional[str]) -> float:
        """Calculate recency score (0.0 to 1.0)"""
        if not timestamp:
            return 0.5  # Default for missing timestamp
        
        try:
            if isinstance(timestamp, str):
                memory_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                memory_time = timestamp
            
            # Calculate days since memory
            days_old = (datetime.now(memory_time.tzinfo) - memory_time).days
            
            # Exponential decay over 30 days
            recency_score = math.exp(-days_old / 30.0)
            return max(0.0, min(1.0, recency_score))
            
        except Exception:
            return 0.5
    
    def _calculate_emotional_score(self, memory: Dict[str, Any]) -> float:
        """Calculate emotional intensity score"""
        try:
            # Look for emotion data in memory
            emotions = memory.get('emotions', {})
            if not emotions:
                # Check for emotion in metadata
                metadata = memory.get('metadata', {})
                emotions = metadata.get('emotions', {})
            
            if not emotions:
                return 0.3  # Default low emotional significance
            
            # Calculate emotional intensity from various emotion indicators
            intensity_scores = []
            
            # Check for high-intensity emotions
            high_intensity_emotions = ['joy', 'anger', 'fear', 'sadness', 'excitement', 'anxiety']
            for emotion in high_intensity_emotions:
                if emotion in emotions:
                    intensity_scores.append(emotions[emotion])
            
            # Check overall emotional magnitude
            if 'emotional_magnitude' in emotions:
                intensity_scores.append(emotions['emotional_magnitude'])
            
            if intensity_scores:
                return max(0.0, min(1.0, max(intensity_scores)))
            
            return 0.3
            
        except Exception:
            return 0.3
    
    def _calculate_frequency_score(
        self, 
        memory: Dict[str, Any], 
        user_context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate frequency/repetition score"""
        # Simplified frequency calculation
        # In a full implementation, this would analyze similar memories
        
        content = memory.get('content', '') or memory.get('user_message', '')
        if not content:
            return 0.3
        
        # Simple heuristic: longer, more detailed memories are often more important
        content_length = len(content)
        if content_length > 200:
            return 0.8
        elif content_length > 100:
            return 0.6
        else:
            return 0.4
    
    def _calculate_semantic_relevance(
        self, 
        memory: Dict[str, Any], 
        user_context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate semantic relevance to user patterns"""
        # Simplified semantic relevance
        # In a full implementation, this would use vector similarity
        
        content = memory.get('content', '') or memory.get('user_message', '')
        if not content:
            return 0.3
        
        # Simple keyword-based relevance
        high_value_keywords = [
            'remember', 'important', 'significant', 'care about', 'matters to me',
            'favorite', 'love', 'hate', 'prefer', 'goal', 'dream', 'plan'
        ]
        
        content_lower = content.lower()
        relevance_count = sum(1 for keyword in high_value_keywords if keyword in content_lower)
        
        if relevance_count >= 2:
            return 0.9
        elif relevance_count == 1:
            return 0.7
        else:
            return 0.4
    
    def _generate_importance_reasoning(self, factors: Dict[str, float], score: float) -> str:
        """Generate human-readable reasoning for importance score"""
        
        if score >= 0.8:
            level = "Very High"
        elif score >= 0.6:
            level = "High" 
        elif score >= 0.4:
            level = "Medium"
        else:
            level = "Low"
        
        # Find the top contributing factor
        top_factor = max(factors.items(), key=lambda x: x[1])
        
        reasoning = f"{level} importance (score: {score:.2f}). "
        reasoning += f"Primary factor: {top_factor[0]} ({top_factor[1]:.2f}). "
        
        return reasoning