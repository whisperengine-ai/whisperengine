"""
Memory Aging Engine - Phase 3B Strategic Component

Analyzes memory health and aging patterns for strategic intelligence caching.
Computes memory staleness, retrieval frequency trends, and forgetting risks.

Author: WhisperEngine AI Team
Created: October 31, 2025
Phase: 3B - Strategic Component Engines
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import asyncpg
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

logger = logging.getLogger(__name__)


@dataclass
class MemoryHealthMetrics:
    """Memory health analysis results"""
    user_id: str
    bot_name: str
    memory_snapshot: Dict[str, Any]  # Top stale/fresh memories
    avg_memory_age_hours: float
    retrieval_frequency_trend: str  # 'increasing', 'stable', 'declining'
    forgetting_risk_memories: List[Dict[str, Any]]  # Memories at risk
    total_memories: int
    oldest_memory_age_hours: float
    freshest_memory_age_hours: float


class MemoryAgingEngine:
    """
    Analyzes memory aging patterns and retrieval frequency.
    
    Key Insights:
    - Which memories are getting stale (not retrieved recently)
    - Retrieval frequency trends over time
    - Forgetting risk prediction (old + not retrieved = at risk)
    - Memory health snapshot for strategic response adaptation
    
    Performance Target: <30 seconds per user analysis
    """
    
    def __init__(
        self,
        qdrant_client: QdrantClient,
        postgres_pool: asyncpg.Pool,
        staleness_threshold_hours: float = 168.0,  # 7 days
        forgetting_risk_threshold: float = 0.7  # 0.0-1.0
    ):
        """
        Initialize memory aging engine.
        
        Args:
            qdrant_client: Qdrant client for vector memory access
            postgres_pool: PostgreSQL connection pool
            staleness_threshold_hours: Hours before memory considered stale
            forgetting_risk_threshold: Risk score threshold (0.7 = high risk)
        """
        self.qdrant_client = qdrant_client
        self.db_pool = postgres_pool
        self.staleness_threshold_hours = staleness_threshold_hours
        self.forgetting_risk_threshold = forgetting_risk_threshold
        
        logger.info(
            "MemoryAgingEngine initialized (staleness_threshold: %.1fh, "
            "forgetting_risk: %.2f)",
            staleness_threshold_hours, forgetting_risk_threshold
        )
    
    async def analyze_memory_health(
        self,
        user_id: str,
        bot_name: str,
        collection_name: str
    ) -> Optional[MemoryHealthMetrics]:
        """
        Analyze memory health for a specific user-bot pair.
        
        Computes:
        - Average memory age
        - Retrieval frequency trends (last 7 days vs previous 7 days)
        - Forgetting risk scores (age + retrieval frequency)
        - Memory snapshot (top stale/fresh memories)
        
        Args:
            user_id: User identifier
            bot_name: Bot name (elena, marcus, etc.)
            collection_name: Qdrant collection name
            
        Returns:
            MemoryHealthMetrics or None if no memories found
        """
        try:
            # Scroll through all memories for this user
            memories = await self._fetch_user_memories(collection_name, user_id)
            
            if not memories:
                logger.debug(f"No memories found for {bot_name}/{user_id[:8]}")
                return None
            
            now = datetime.now(timezone.utc)
            
            # Analyze memory ages
            memory_ages = []
            memory_details = []
            
            for memory in memories:
                # Extract timestamp from payload
                timestamp_str = memory.payload.get('timestamp')
                if not timestamp_str:
                    continue
                
                # Parse timestamp (handle both formats)
                try:
                    if isinstance(timestamp_str, str):
                        if 'T' in timestamp_str:
                            # ISO format with timezone
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            # Simple format without timezone - assume UTC
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            if timestamp.tzinfo is None:
                                timestamp = timestamp.replace(tzinfo=timezone.utc)
                    else:
                        # Unix timestamp
                        timestamp = datetime.fromtimestamp(timestamp_str, tz=timezone.utc)
                    
                    # Ensure timezone-aware datetime
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
                    continue
                
                age_hours = (now - timestamp).total_seconds() / 3600
                memory_ages.append(age_hours)
                
                memory_details.append({
                    'memory_id': str(memory.id),
                    'age_hours': age_hours,
                    'content_preview': memory.payload.get('content', '')[:100],
                    'memory_type': memory.payload.get('memory_type', 'unknown'),
                    'timestamp': timestamp.isoformat()
                })
            
            if not memory_ages:
                logger.warning(f"No valid timestamps found for {bot_name}/{user_id[:8]}")
                return None
            
            # Compute age statistics
            avg_age = sum(memory_ages) / len(memory_ages)
            oldest_age = max(memory_ages)
            freshest_age = min(memory_ages)
            
            # Compute retrieval frequency trend
            retrieval_trend = await self._compute_retrieval_trend(
                collection_name, user_id, now
            )
            
            # Identify forgetting risk memories
            forgetting_risks = self._identify_forgetting_risks(
                memory_details, avg_age
            )
            
            # Create memory snapshot (top 5 stale, top 5 fresh)
            sorted_by_age = sorted(memory_details, key=lambda m: m['age_hours'], reverse=True)
            memory_snapshot = {
                'stale_memories': sorted_by_age[:5],
                'fresh_memories': sorted_by_age[-5:] if len(sorted_by_age) > 5 else [],
                'analysis_timestamp': now.isoformat()
            }
            
            logger.info(
                f"Memory health analyzed: {bot_name}/{user_id[:8]} - "
                f"{len(memories)} memories, avg age {avg_age:.1f}h, "
                f"{len(forgetting_risks)} at risk"
            )
            
            return MemoryHealthMetrics(
                user_id=user_id,
                bot_name=bot_name,
                memory_snapshot=memory_snapshot,
                avg_memory_age_hours=avg_age,
                retrieval_frequency_trend=retrieval_trend,
                forgetting_risk_memories=forgetting_risks,
                total_memories=len(memories),
                oldest_memory_age_hours=oldest_age,
                freshest_memory_age_hours=freshest_age
            )
            
        except Exception as e:
            logger.error(
                f"Memory health analysis failed for {bot_name}/{user_id[:8]}: {e}",
                exc_info=True
            )
            return None
    
    async def _fetch_user_memories(
        self,
        collection_name: str,
        user_id: str
    ) -> List[Any]:
        """Fetch all memories for a user from Qdrant."""
        try:
            # Scroll through all points for this user
            records, _ = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=1000,  # Fetch up to 1000 memories per user
                with_payload=True,
                with_vectors=False  # Don't need vectors for aging analysis
            )
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to fetch memories from {collection_name}: {e}")
            return []
    
    async def _compute_retrieval_trend(
        self,
        collection_name: str,
        user_id: str,
        now: datetime
    ) -> str:
        """
        Compute retrieval frequency trend.
        
        Compares last 7 days to previous 7 days to determine if
        user is engaging more, less, or same amount.
        
        Returns: 'increasing', 'stable', or 'declining'
        """
        try:
            # Last 7 days
            week_ago = now - timedelta(days=7)
            recent_memories = await self._count_memories_since(
                collection_name, user_id, week_ago
            )
            
            # Previous 7 days (8-14 days ago)
            two_weeks_ago = now - timedelta(days=14)
            previous_memories = await self._count_memories_between(
                collection_name, user_id, two_weeks_ago, week_ago
            )
            
            # Compare with 20% threshold
            if recent_memories > previous_memories * 1.2:
                return 'increasing'
            elif recent_memories < previous_memories * 0.8:
                return 'declining'
            else:
                return 'stable'
                
        except Exception as e:
            logger.warning(f"Failed to compute retrieval trend: {e}")
            return 'stable'  # Default to stable on error
    
    async def _count_memories_since(
        self,
        collection_name: str,
        user_id: str,
        since: datetime
    ) -> int:
        """Count memories created since a timestamp."""
        try:
            # Convert to Unix timestamp
            since_ts = since.timestamp()
            
            records, _ = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        ),
                        FieldCondition(
                            key="timestamp",
                            range=Range(gte=since_ts)
                        )
                    ]
                ),
                limit=10000,  # Count up to 10k
                with_payload=False,
                with_vectors=False
            )
            
            return len(records)
            
        except Exception:
            return 0
    
    async def _count_memories_between(
        self,
        collection_name: str,
        user_id: str,
        start: datetime,
        end: datetime
    ) -> int:
        """Count memories created between two timestamps."""
        try:
            start_ts = start.timestamp()
            end_ts = end.timestamp()
            
            records, _ = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        ),
                        FieldCondition(
                            key="timestamp",
                            range=Range(gte=start_ts, lt=end_ts)
                        )
                    ]
                ),
                limit=10000,
                with_payload=False,
                with_vectors=False
            )
            
            return len(records)
            
        except Exception:
            return 0
    
    def _identify_forgetting_risks(
        self,
        memory_details: List[Dict[str, Any]],
        avg_age: float
    ) -> List[Dict[str, Any]]:
        """
        Identify memories at risk of being forgotten.
        
        Risk factors:
        - Age > avg_age * 2 (much older than average)
        - Age > staleness_threshold
        
        Risk score = (age / staleness_threshold) * weight
        """
        at_risk = []
        
        for memory in memory_details:
            age = memory['age_hours']
            
            # Compute risk score (0.0-1.0+)
            risk_score = min(1.0, age / self.staleness_threshold_hours)
            
            # Additional risk if much older than average
            if age > avg_age * 2:
                risk_score *= 1.2
            
            if risk_score >= self.forgetting_risk_threshold:
                at_risk.append({
                    'memory_id': memory['memory_id'],
                    'age_hours': age,
                    'risk_score': min(1.0, risk_score),
                    'content_preview': memory['content_preview'],
                    'memory_type': memory['memory_type']
                })
        
        # Sort by risk score (highest first)
        at_risk.sort(key=lambda m: m['risk_score'], reverse=True)
        
        # Return top 10 at-risk memories
        return at_risk[:10]
    
    async def store_memory_health(
        self,
        metrics: MemoryHealthMetrics,
        ttl_minutes: int = 15
    ) -> bool:
        """
        Store memory health metrics in PostgreSQL strategic cache.
        
        Args:
            metrics: Memory health metrics to store
            ttl_minutes: Time-to-live in minutes (default: 15, longer than 11-minute enrichment cycle)
            
        Returns:
            True if stored successfully, False otherwise
        """
        import json
        from datetime import timedelta
        
        try:
            query = """
                INSERT INTO strategic_memory_health 
                (user_id, bot_name, memory_snapshot, avg_memory_age_hours, 
                 retrieval_frequency_trend, forgetting_risk_memories, 
                 computed_at, expires_at)
                VALUES ($1, $2, $3::jsonb, $4, $5, $6::jsonb, NOW(), NOW() + $7)
                ON CONFLICT (user_id, bot_name) 
                DO UPDATE SET 
                    memory_snapshot = EXCLUDED.memory_snapshot,
                    avg_memory_age_hours = EXCLUDED.avg_memory_age_hours,
                    retrieval_frequency_trend = EXCLUDED.retrieval_frequency_trend,
                    forgetting_risk_memories = EXCLUDED.forgetting_risk_memories,
                    computed_at = EXCLUDED.computed_at,
                    expires_at = EXCLUDED.expires_at
                RETURNING id
            """
            
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    query,
                    metrics.user_id,
                    metrics.bot_name,
                    json.dumps(metrics.memory_snapshot),
                    metrics.avg_memory_age_hours,
                    metrics.retrieval_frequency_trend,
                    json.dumps(metrics.forgetting_risk_memories),
                    timedelta(minutes=ttl_minutes)
                )
                
                logger.info(
                    f"Stored memory health for {metrics.bot_name}/{metrics.user_id[:8]} "
                    f"(id={result['id']}, ttl={ttl_minutes}m)"
                )
                return True
                
        except Exception as e:
            logger.error(
                f"Failed to store memory health for {metrics.bot_name}/{metrics.user_id[:8]}: {e}",
                exc_info=True
            )
            return False
