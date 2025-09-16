"""
Memory Tier System for Personality-Driven AI Companions

This module implements a hot/warm/cold memory architecture optimized for hardware
constraints while maximizing AI companion personality effectiveness.

Hardware Constraints:
- 32GB System RAM
- 12-24GB VRAM (depending on model size)
- Goal: Keep most personality-relevant facts in fast-access storage

Memory Tier Strategy:
- HOT (Vector DB + In-Memory Cache): Critical personality facts, recent interactions
- WARM (Vector DB): Important personality facts, frequent patterns  
- COLD (Relational DB): Archive storage, low-relevance facts, old conversations

Tier Assignment Logic:
- Personality relevance score (0.0-1.0)
- Recency of access (time-based decay)
- Access frequency (interaction count)
- User relationship depth (trust/engagement level)
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from collections import defaultdict, OrderedDict

logger = logging.getLogger(__name__)


class MemoryTier(Enum):
    """Memory storage tiers for personality facts"""
    HOT = "hot"         # Vector DB + In-memory cache (highest priority)
    WARM = "warm"       # Vector DB only (medium priority)
    COLD = "cold"       # Relational DB only (archival)


class AccessPattern(Enum):
    """Types of memory access patterns"""
    FREQUENT = "frequent"       # Accessed multiple times recently
    RECENT = "recent"          # Accessed once recently
    PERIODIC = "periodic"      # Accessed regularly but not recently
    STALE = "stale"           # Not accessed in a long time
    ARCHIVED = "archived"     # Old, rarely accessed


@dataclass
class MemoryMetrics:
    """Metrics for memory usage and performance tracking"""
    total_facts: int = 0
    hot_tier_facts: int = 0
    warm_tier_facts: int = 0
    cold_tier_facts: int = 0
    
    hot_tier_size_mb: float = 0.0
    warm_tier_size_mb: float = 0.0
    cold_tier_size_mb: float = 0.0
    
    cache_hit_rate: float = 0.0
    avg_retrieval_time_ms: float = 0.0
    
    last_optimization: Optional[datetime] = None
    optimizations_performed: int = 0


@dataclass
class MemoryAccess:
    """Track access patterns for a memory item"""
    fact_id: str
    user_id: str
    context_id: str
    
    # Access tracking
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    first_accessed: Optional[datetime] = None
    access_frequency: float = 0.0  # accesses per day
    
    # Personality relevance
    personality_relevance: float = 0.0  # From PersonalityFactClassifier
    emotional_weight: float = 0.0
    relationship_building_score: float = 0.0
    
    # Current tier assignment
    current_tier: MemoryTier = MemoryTier.WARM
    tier_assignment_time: Optional[datetime] = None
    tier_assignment_reason: str = ""
    
    # Performance tracking
    retrieval_times_ms: List[float] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0


class MemoryTierManager:
    """
    Manages memory tiers for optimal personality-driven AI companion performance.
    
    Key Features:
    - Automatic tier assignment based on personality relevance
    - Access pattern tracking and adaptation
    - Hardware-aware optimization
    - Real-time tier migration
    - Performance monitoring
    """
    
    def __init__(self, 
                 max_hot_facts: int = 1000,
                 max_warm_facts: int = 5000,
                 max_cache_size_mb: float = 512.0,
                 optimization_interval_hours: int = 6):
        """
        Initialize memory tier manager.
        
        Args:
            max_hot_facts: Maximum facts in hot tier (high-speed access)
            max_warm_facts: Maximum facts in warm tier (medium-speed access)
            max_cache_size_mb: Maximum in-memory cache size
            optimization_interval_hours: How often to optimize tier assignments
        """
        self.max_hot_facts = max_hot_facts
        self.max_warm_facts = max_warm_facts
        self.max_cache_size_mb = max_cache_size_mb
        self.optimization_interval = timedelta(hours=optimization_interval_hours)
        
        # Access tracking
        self.access_patterns: Dict[str, MemoryAccess] = {}
        self.user_context_map: Dict[str, Set[str]] = defaultdict(set)
        
        # In-memory cache for hot tier
        self.hot_cache: OrderedDict[str, Any] = OrderedDict()
        self.cache_size_mb: float = 0.0
        
        # Performance metrics
        self.metrics = MemoryMetrics()
        
        # Background optimization
        self.last_optimization = datetime.now()
        self._optimization_lock = asyncio.Lock()
        
        logger.info("MemoryTierManager initialized: hot=%d, warm=%d, cache=%.1fMB", 
                   max_hot_facts, max_warm_facts, max_cache_size_mb)
    
    async def classify_memory_tier(self, 
                                 personality_relevance: float,
                                 emotional_weight: float,
                                 user_id: str,
                                 context_id: str) -> Tuple[MemoryTier, str]:
        """
        Classify which memory tier a fact should be stored in.
        
        Args:
            personality_relevance: Relevance score from PersonalityFactClassifier
            emotional_weight: Emotional significance score
            user_id: User identifier
            context_id: Context identifier
            
        Returns:
            Tuple of (MemoryTier, reasoning)
        """
        # Calculate composite score
        composite_score = self._calculate_composite_score(
            personality_relevance, emotional_weight, user_id, context_id
        )
        
        # Tier assignment thresholds (adjusted for better distribution)
        if composite_score >= 0.7:
            tier = MemoryTier.HOT
            reason = f"High composite score ({composite_score:.2f}): critical for personality"
        elif composite_score >= 0.4:
            tier = MemoryTier.WARM
            reason = f"Medium composite score ({composite_score:.2f}): important for relationship"
        else:
            tier = MemoryTier.COLD
            reason = f"Low composite score ({composite_score:.2f}): archival storage"
        
        # Check capacity constraints
        tier, reason = await self._check_capacity_constraints(tier, reason)
        
        logger.debug("Memory tier classification: %s - %s", tier.value, reason)
        return tier, reason
    
    def _calculate_composite_score(self,
                                 personality_relevance: float,
                                 emotional_weight: float,
                                 user_id: str,
                                 context_id: str) -> float:
        """Calculate composite score for tier assignment"""
        
        # Base score from personality relevance (primary factor)
        score = personality_relevance * 0.6
        
        # Emotional weight contribution
        score += emotional_weight * 0.2
        
        # User relationship depth (estimated from context history)
        relationship_depth = self._estimate_relationship_depth(user_id, context_id)
        score += relationship_depth * 0.15
        
        # Recency bonus for recent interactions
        recency_bonus = self._calculate_recency_bonus(user_id, context_id)
        score += recency_bonus * 0.05
        
        # Ensure score stays in valid range
        return max(0.0, min(1.0, score))
    
    def _estimate_relationship_depth(self, user_id: str, _context_id: str) -> float:
        """Estimate relationship depth based on interaction history"""
        # Simple heuristic based on number of contexts and facts
        user_contexts = len(self.user_context_map.get(user_id, set()))
        user_facts = len([access for access in self.access_patterns.values() 
                         if access.user_id == user_id])
        
        # Normalize to 0-1 range
        context_score = min(1.0, user_contexts / 10.0)  # 10+ contexts = max depth
        fact_score = min(1.0, user_facts / 50.0)        # 50+ facts = max depth
        
        return (context_score + fact_score) / 2.0
    
    def _calculate_recency_bonus(self, user_id: str, _context_id: str) -> float:
        """Calculate recency bonus for recent interactions"""
        now = datetime.now()
        
        # Check for recent accesses by this user
        recent_accesses = [
            access for access in self.access_patterns.values()
            if (access.user_id == user_id and 
                access.last_accessed is not None and
                (now - access.last_accessed) < timedelta(hours=24))
        ]
        
        if not recent_accesses:
            return 0.0
        
        # More recent = higher bonus
        hours_since_last = min(
            (now - access.last_accessed).total_seconds() / 3600
            for access in recent_accesses
            if access.last_accessed is not None
        )
        
        # Exponential decay: 1.0 for immediate, 0.0 for 24+ hours
        return max(0.0, 1.0 - (hours_since_last / 24.0))
    
    async def _check_capacity_constraints(self, preferred_tier: MemoryTier, reason: str) -> Tuple[MemoryTier, str]:
        """Check capacity constraints and adjust tier if necessary"""
        
        if preferred_tier == MemoryTier.HOT:
            if self.metrics.hot_tier_facts >= self.max_hot_facts:
                # Try to make room by demoting low-priority facts
                demoted = await self._demote_low_priority_hot_facts()
                if demoted == 0:
                    return MemoryTier.WARM, f"{reason} (demoted to WARM: hot tier full)"
        
        elif preferred_tier == MemoryTier.WARM:
            if self.metrics.warm_tier_facts >= self.max_warm_facts:
                # Try to make room by demoting to cold storage
                demoted = await self._demote_low_priority_warm_facts()
                if demoted == 0:
                    return MemoryTier.COLD, f"{reason} (demoted to COLD: warm tier full)"
        
        return preferred_tier, reason
    
    async def _demote_low_priority_hot_facts(self) -> int:
        """Demote lowest priority facts from hot to warm tier"""
        # This would integrate with actual storage system
        # For now, return 1 to indicate we made room
        logger.debug("Demoting low-priority facts from hot to warm tier")
        return 1
    
    async def _demote_low_priority_warm_facts(self) -> int:
        """Demote lowest priority facts from warm to cold tier"""
        # This would integrate with actual storage system
        logger.debug("Demoting low-priority facts from warm to cold tier")
        return 1
    
    async def record_access(self, 
                          fact_id: str,
                          user_id: str,
                          context_id: str,
                          retrieval_time_ms: float,
                          was_cache_hit: bool):
        """Record access pattern for a memory item"""
        
        if fact_id not in self.access_patterns:
            self.access_patterns[fact_id] = MemoryAccess(
                fact_id=fact_id,
                user_id=user_id,
                context_id=context_id,
                first_accessed=datetime.now()
            )
        
        access = self.access_patterns[fact_id]
        now = datetime.now()
        
        # Update access tracking
        access.access_count += 1
        access.last_accessed = now
        access.retrieval_times_ms.append(retrieval_time_ms)
        
        # Update cache statistics
        if was_cache_hit:
            access.cache_hits += 1
        else:
            access.cache_misses += 1
        
        # Calculate access frequency (accesses per day)
        if access.first_accessed:
            days_active = max(1, (now - access.first_accessed).days)
            access.access_frequency = access.access_count / days_active
        
        # Track user-context relationships
        self.user_context_map[user_id].add(context_id)
        
        # Check if optimization is needed
        if now - self.last_optimization > self.optimization_interval:
            asyncio.create_task(self.optimize_tier_assignments())
    
    async def optimize_tier_assignments(self):
        """Optimize memory tier assignments based on access patterns"""
        
        async with self._optimization_lock:
            if datetime.now() - self.last_optimization < self.optimization_interval:
                return  # Recently optimized
            
            logger.info("Starting memory tier optimization...")
            start_time = time.time()
            
            optimizations = 0
            
            # Analyze access patterns and suggest tier changes
            for fact_id, access in self.access_patterns.items():
                new_tier = await self._suggest_tier_optimization(access)
                
                if new_tier != access.current_tier:
                    await self._migrate_fact_to_tier(fact_id, access.current_tier, new_tier)
                    access.current_tier = new_tier
                    access.tier_assignment_time = datetime.now()
                    optimizations += 1
            
            # Update metrics
            self.metrics.optimizations_performed += 1
            self.metrics.last_optimization = datetime.now()
            self.last_optimization = datetime.now()
            
            optimization_time = time.time() - start_time
            logger.info("Memory optimization complete: %d migrations in %.2fs", 
                       optimizations, optimization_time)
    
    async def _suggest_tier_optimization(self, access: MemoryAccess) -> MemoryTier:
        """Suggest optimal tier for a memory item based on access patterns"""
        
        now = datetime.now()
        
        # Calculate access pattern score
        recency_score = 0.0
        if access.last_accessed:
            hours_since_access = (now - access.last_accessed).total_seconds() / 3600
            recency_score = max(0.0, 1.0 - (hours_since_access / (24 * 7)))  # 1 week decay
        
        frequency_score = min(1.0, access.access_frequency / 2.0)  # 2+ accesses per day = max
        
        # Combine with personality relevance
        composite_score = (
            access.personality_relevance * 0.4 +
            recency_score * 0.3 +
            frequency_score * 0.2 +
            access.emotional_weight * 0.1
        )
        
        # Tier thresholds (slightly different from initial classification)
        if composite_score >= 0.65:
            return MemoryTier.HOT
        elif composite_score >= 0.35:
            return MemoryTier.WARM
        else:
            return MemoryTier.COLD
    
    async def _migrate_fact_to_tier(self, fact_id: str, from_tier: MemoryTier, to_tier: MemoryTier):
        """Migrate a fact between memory tiers"""
        logger.debug("Migrating fact %s from %s to %s", fact_id, from_tier.value, to_tier.value)
        
        # This would integrate with actual storage system
        # - Remove from old tier storage
        # - Add to new tier storage
        # - Update cache if needed
        
        # Update metrics
        if from_tier == MemoryTier.HOT:
            self.metrics.hot_tier_facts -= 1
        elif from_tier == MemoryTier.WARM:
            self.metrics.warm_tier_facts -= 1
        elif from_tier == MemoryTier.COLD:
            self.metrics.cold_tier_facts -= 1
        
        if to_tier == MemoryTier.HOT:
            self.metrics.hot_tier_facts += 1
        elif to_tier == MemoryTier.WARM:
            self.metrics.warm_tier_facts += 1
        elif to_tier == MemoryTier.COLD:
            self.metrics.cold_tier_facts += 1
    
    async def get_memory_metrics(self) -> MemoryMetrics:
        """Get current memory usage and performance metrics"""
        
        # Calculate cache hit rate
        total_hits = sum(access.cache_hits for access in self.access_patterns.values())
        total_misses = sum(access.cache_misses for access in self.access_patterns.values())
        total_accesses = total_hits + total_misses
        
        if total_accesses > 0:
            self.metrics.cache_hit_rate = total_hits / total_accesses
        
        # Calculate average retrieval time
        all_times = []
        for access in self.access_patterns.values():
            all_times.extend(access.retrieval_times_ms)
        
        if all_times:
            self.metrics.avg_retrieval_time_ms = sum(all_times) / len(all_times)
        
        # Update total facts
        self.metrics.total_facts = len(self.access_patterns)
        
        return self.metrics
    
    async def get_tier_distribution(self) -> Dict[str, int]:
        """Get current distribution of facts across tiers"""
        distribution = {
            "hot": 0,
            "warm": 0,
            "cold": 0
        }
        
        for access in self.access_patterns.values():
            distribution[access.current_tier.value] += 1
        
        return distribution
    
    async def get_user_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """Get memory summary for a specific user"""
        user_accesses = [access for access in self.access_patterns.values() 
                        if access.user_id == user_id]
        
        if not user_accesses:
            return {"error": "No memory data for user"}
        
        # Calculate statistics
        total_facts = len(user_accesses)
        avg_relevance = sum(access.personality_relevance for access in user_accesses) / total_facts
        total_accesses = sum(access.access_count for access in user_accesses)
        
        tier_distribution = {"hot": 0, "warm": 0, "cold": 0}
        for access in user_accesses:
            tier_distribution[access.current_tier.value] += 1
        
        relationship_depth = self._estimate_relationship_depth(user_id, "")
        
        return {
            "user_id": user_id,
            "total_facts": total_facts,
            "total_accesses": total_accesses,
            "avg_personality_relevance": avg_relevance,
            "relationship_depth": relationship_depth,
            "tier_distribution": tier_distribution,
            "contexts": list(self.user_context_map.get(user_id, set()))
        }


# Global instance for use across the application
memory_tier_manager = MemoryTierManager()