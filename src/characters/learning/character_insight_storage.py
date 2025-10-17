"""
Character Insight Storage - PostgreSQL Layer 1 Implementation

Provides CRUD operations for character learning persistence using PostgreSQL.
Part of the hybrid storage architecture (PostgreSQL primary + Qdrant semantic + InfluxDB analytics).

Database Tables:
- character_insights: Core insight records
- character_insight_relationships: Graph connections between insights
- character_learning_timeline: Learning evolution history
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class CharacterInsight:
    """Represents a single character self-discovery insight"""
    character_id: int
    insight_type: str  # 'emotional_pattern', 'preference', 'memory_formation', 'relationship_evolution'
    insight_content: str
    confidence_score: float
    importance_level: int = 5  # 1-10 scale
    discovery_date: Optional[datetime] = None
    conversation_context: Optional[str] = None
    emotional_valence: Optional[float] = None  # -1.0 to 1.0
    triggers: Optional[List[str]] = None  # Keywords that activate this insight
    supporting_evidence: Optional[List[str]] = None  # Examples/quotes
    id: Optional[int] = None  # Populated after storage
    
    def __post_init__(self):
        """Validate fields after initialization"""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(f"confidence_score must be 0.0-1.0, got {self.confidence_score}")
        if not 1 <= self.importance_level <= 10:
            raise ValueError(f"importance_level must be 1-10, got {self.importance_level}")
        if self.emotional_valence is not None and not -1.0 <= self.emotional_valence <= 1.0:
            raise ValueError(f"emotional_valence must be -1.0 to 1.0, got {self.emotional_valence}")


@dataclass
class InsightRelationship:
    """Represents a relationship between two character insights"""
    from_insight_id: int
    to_insight_id: int
    relationship_type: str  # 'leads_to', 'contradicts', 'supports', 'builds_on'
    strength: float = 0.5  # 0.0-1.0
    created_date: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class LearningTimelineEvent:
    """Represents a character learning evolution event"""
    character_id: int
    learning_event: str
    learning_type: str  # 'self_discovery', 'preference_evolution', 'emotional_growth'
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    trigger_conversation: Optional[str] = None
    learning_date: Optional[datetime] = None
    significance_score: Optional[float] = None  # 0.0-1.0
    id: Optional[int] = None


class CharacterInsightStorage:
    """
    PostgreSQL storage layer for character learning persistence.
    
    Provides CRUD operations for insights, relationships, and timeline events.
    Part of Layer 1 (PostgreSQL primary storage) in the hybrid architecture.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize storage with database connection pool.
        
        Args:
            db_pool: asyncpg connection pool
        """
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)
    
    # ========== CHARACTER INSIGHTS OPERATIONS ==========
    
    async def store_insight(self, insight: CharacterInsight) -> int:
        """
        Store a character insight in PostgreSQL.
        
        Args:
            insight: CharacterInsight object to store
            
        Returns:
            int: PostgreSQL primary key ID of stored insight
            
        Raises:
            asyncpg.UniqueViolationError: If insight_content already exists for character
        """
        query = """
            INSERT INTO character_insights (
                character_id, insight_type, insight_content, confidence_score,
                importance_level, conversation_context, emotional_valence,
                triggers, supporting_evidence
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id;
        """
        
        async with self.db_pool.acquire() as conn:
            try:
                insight_id = await conn.fetchval(
                    query,
                    insight.character_id,
                    insight.insight_type,
                    insight.insight_content,
                    insight.confidence_score,
                    insight.importance_level,
                    insight.conversation_context,
                    insight.emotional_valence,
                    insight.triggers or [],
                    insight.supporting_evidence or []
                )
                
                self.logger.info(
                    f"✅ Stored insight ID {insight_id} for character {insight.character_id} "
                    f"(type: {insight.insight_type}, confidence: {insight.confidence_score:.2f})"
                )
                return insight_id
                
            except asyncpg.UniqueViolationError:
                self.logger.warning(
                    f"⚠️ Duplicate insight content for character {insight.character_id}: "
                    f"'{insight.insight_content[:50]}...'"
                )
                raise
    
    async def get_insight_by_id(self, insight_id: int) -> Optional[CharacterInsight]:
        """
        Retrieve a single insight by ID.
        
        Args:
            insight_id: PostgreSQL primary key
            
        Returns:
            CharacterInsight object or None if not found
        """
        query = """
            SELECT id, character_id, insight_type, insight_content, confidence_score,
                   discovery_date, conversation_context, importance_level,
                   emotional_valence, triggers, supporting_evidence
            FROM character_insights
            WHERE id = $1;
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, insight_id)
            if row:
                return CharacterInsight(
                    id=row['id'],
                    character_id=row['character_id'],
                    insight_type=row['insight_type'],
                    insight_content=row['insight_content'],
                    confidence_score=row['confidence_score'],
                    discovery_date=row['discovery_date'],
                    conversation_context=row['conversation_context'],
                    importance_level=row['importance_level'],
                    emotional_valence=row['emotional_valence'],
                    triggers=row['triggers'],
                    supporting_evidence=row['supporting_evidence']
                )
            return None
    
    async def get_insights_by_triggers(
        self,
        character_id: int,
        triggers: List[str],
        limit: int = 10
    ) -> List[CharacterInsight]:
        """
        Retrieve insights matching any of the provided trigger keywords.
        
        This is a PostgreSQL keyword-based retrieval (fast but imprecise).
        For semantic similarity, use Layer 2 (Qdrant) when implemented.
        
        Args:
            character_id: Character to query
            triggers: List of trigger keywords to match
            limit: Maximum results to return
            
        Returns:
            List of CharacterInsight objects ordered by importance/confidence
        """
        query = """
            SELECT id, character_id, insight_type, insight_content, confidence_score,
                   discovery_date, conversation_context, importance_level,
                   emotional_valence, triggers, supporting_evidence
            FROM character_insights
            WHERE character_id = $1
            AND (
                triggers && $2::text[]  -- Array overlap operator
                OR insight_content ILIKE ANY($3)  -- Text matching as fallback
            )
            ORDER BY importance_level DESC, confidence_score DESC
            LIMIT $4;
        """
        
        # Create ILIKE patterns for text search
        ilike_patterns = [f'%{trigger}%' for trigger in triggers]
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, character_id, triggers, ilike_patterns, limit)
            
            insights = [
                CharacterInsight(
                    id=row['id'],
                    character_id=row['character_id'],
                    insight_type=row['insight_type'],
                    insight_content=row['insight_content'],
                    confidence_score=row['confidence_score'],
                    discovery_date=row['discovery_date'],
                    conversation_context=row['conversation_context'],
                    importance_level=row['importance_level'],
                    emotional_valence=row['emotional_valence'],
                    triggers=row['triggers'],
                    supporting_evidence=row['supporting_evidence']
                )
                for row in rows
            ]
            
            self.logger.info(
                f"📋 Retrieved {len(insights)} insights for character {character_id} "
                f"matching triggers: {triggers}"
            )
            return insights
    
    async def get_recent_insights(
        self,
        character_id: int,
        days_back: int = 30,
        limit: int = 20
    ) -> List[CharacterInsight]:
        """
        Get recent insights for a character ordered chronologically.
        
        Args:
            character_id: Character to query
            days_back: How many days of history to retrieve
            limit: Maximum results to return
            
        Returns:
            List of CharacterInsight objects ordered by discovery_date DESC
        """
        query = """
            SELECT id, character_id, insight_type, insight_content, confidence_score,
                   discovery_date, conversation_context, importance_level,
                   emotional_valence, triggers, supporting_evidence
            FROM character_insights
            WHERE character_id = $1
            AND discovery_date >= NOW() - INTERVAL '%s days'
            ORDER BY discovery_date DESC
            LIMIT $2;
        """ % days_back
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, character_id, limit)
            
            insights = [
                CharacterInsight(
                    id=row['id'],
                    character_id=row['character_id'],
                    insight_type=row['insight_type'],
                    insight_content=row['insight_content'],
                    confidence_score=row['confidence_score'],
                    discovery_date=row['discovery_date'],
                    conversation_context=row['conversation_context'],
                    importance_level=row['importance_level'],
                    emotional_valence=row['emotional_valence'],
                    triggers=row['triggers'],
                    supporting_evidence=row['supporting_evidence']
                )
                for row in rows
            ]
            
            self.logger.info(
                f"📋 Retrieved {len(insights)} recent insights (last {days_back} days) "
                f"for character {character_id}"
            )
            return insights
    
    async def update_insight_confidence(
        self,
        insight_id: int,
        new_confidence: float
    ) -> bool:
        """
        Update the confidence score of an existing insight.
        
        Useful when insight is reinforced or contradicted by new conversations.
        
        Args:
            insight_id: PostgreSQL primary key
            new_confidence: New confidence score (0.0-1.0)
            
        Returns:
            True if updated, False if insight not found
        """
        if not 0.0 <= new_confidence <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {new_confidence}")
        
        query = """
            UPDATE character_insights
            SET confidence_score = $1
            WHERE id = $2;
        """
        
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(query, new_confidence, insight_id)
            updated = result.split()[-1] == '1'
            
            if updated:
                self.logger.info(
                    f"✅ Updated insight {insight_id} confidence to {new_confidence:.2f}"
                )
            return updated
    
    # ========== INSIGHT RELATIONSHIPS OPERATIONS ==========
    
    async def create_relationship(
        self,
        relationship: InsightRelationship
    ) -> int:
        """
        Create a relationship between two insights.
        
        Args:
            relationship: InsightRelationship object
            
        Returns:
            int: PostgreSQL primary key ID of relationship
            
        Raises:
            asyncpg.UniqueViolationError: If relationship already exists
        """
        query = """
            INSERT INTO character_insight_relationships (
                from_insight_id, to_insight_id, relationship_type, strength
            ) VALUES ($1, $2, $3, $4)
            RETURNING id;
        """
        
        async with self.db_pool.acquire() as conn:
            relationship_id = await conn.fetchval(
                query,
                relationship.from_insight_id,
                relationship.to_insight_id,
                relationship.relationship_type,
                relationship.strength
            )
            
            self.logger.info(
                f"✅ Created relationship {relationship_id}: "
                f"{relationship.from_insight_id} --[{relationship.relationship_type}]--> "
                f"{relationship.to_insight_id}"
            )
            return relationship_id
    
    async def get_related_insights(
        self,
        insight_id: int,
        relationship_types: Optional[List[str]] = None
    ) -> List[CharacterInsight]:
        """
        Get insights related to a specific insight (graph traversal).
        
        Args:
            insight_id: Source insight ID
            relationship_types: Filter by relationship types (e.g., ['supports', 'builds_on'])
                              If None, returns all relationships
            
        Returns:
            List of related CharacterInsight objects
        """
        if relationship_types:
            query = """
                SELECT ci.id, ci.character_id, ci.insight_type, ci.insight_content,
                       ci.confidence_score, ci.discovery_date, ci.conversation_context,
                       ci.importance_level, ci.emotional_valence, ci.triggers,
                       ci.supporting_evidence, cir.relationship_type, cir.strength
                FROM character_insights ci
                JOIN character_insight_relationships cir ON ci.id = cir.to_insight_id
                WHERE cir.from_insight_id = $1
                AND cir.relationship_type = ANY($2)
                ORDER BY cir.strength DESC, ci.importance_level DESC;
            """
            params = [insight_id, relationship_types]
        else:
            query = """
                SELECT ci.id, ci.character_id, ci.insight_type, ci.insight_content,
                       ci.confidence_score, ci.discovery_date, ci.conversation_context,
                       ci.importance_level, ci.emotional_valence, ci.triggers,
                       ci.supporting_evidence, cir.relationship_type, cir.strength
                FROM character_insights ci
                JOIN character_insight_relationships cir ON ci.id = cir.to_insight_id
                WHERE cir.from_insight_id = $1
                ORDER BY cir.strength DESC, ci.importance_level DESC;
            """
            params = [insight_id]
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            insights = [
                CharacterInsight(
                    id=row['id'],
                    character_id=row['character_id'],
                    insight_type=row['insight_type'],
                    insight_content=row['insight_content'],
                    confidence_score=row['confidence_score'],
                    discovery_date=row['discovery_date'],
                    conversation_context=row['conversation_context'],
                    importance_level=row['importance_level'],
                    emotional_valence=row['emotional_valence'],
                    triggers=row['triggers'],
                    supporting_evidence=row['supporting_evidence']
                )
                for row in rows
            ]
            
            self.logger.info(
                f"📋 Found {len(insights)} related insights for insight {insight_id}"
            )
            return insights
    
    # ========== LEARNING TIMELINE OPERATIONS ==========
    
    async def record_learning_event(
        self,
        event: LearningTimelineEvent
    ) -> int:
        """
        Record a learning evolution event in the timeline.
        
        Args:
            event: LearningTimelineEvent object
            
        Returns:
            int: PostgreSQL primary key ID of timeline event
        """
        query = """
            INSERT INTO character_learning_timeline (
                character_id, learning_event, learning_type, before_state,
                after_state, trigger_conversation, significance_score
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id;
        """
        
        async with self.db_pool.acquire() as conn:
            event_id = await conn.fetchval(
                query,
                event.character_id,
                event.learning_event,
                event.learning_type,
                event.before_state,
                event.after_state,
                event.trigger_conversation,
                event.significance_score
            )
            
            self.logger.info(
                f"✅ Recorded learning event {event_id} for character {event.character_id} "
                f"(type: {event.learning_type})"
            )
            return event_id
    
    async def get_learning_timeline(
        self,
        character_id: int,
        days_back: int = 30,
        limit: int = 50
    ) -> List[LearningTimelineEvent]:
        """
        Get character learning timeline ordered chronologically.
        
        Args:
            character_id: Character to query
            days_back: How many days of history to retrieve
            limit: Maximum events to return
            
        Returns:
            List of LearningTimelineEvent objects ordered by learning_date DESC
        """
        query = """
            SELECT id, character_id, learning_event, learning_type, before_state,
                   after_state, trigger_conversation, learning_date, significance_score
            FROM character_learning_timeline
            WHERE character_id = $1
            AND learning_date >= NOW() - INTERVAL '%s days'
            ORDER BY learning_date DESC
            LIMIT $2;
        """ % days_back
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, character_id, limit)
            
            events = [
                LearningTimelineEvent(
                    id=row['id'],
                    character_id=row['character_id'],
                    learning_event=row['learning_event'],
                    learning_type=row['learning_type'],
                    before_state=row['before_state'],
                    after_state=row['after_state'],
                    trigger_conversation=row['trigger_conversation'],
                    learning_date=row['learning_date'],
                    significance_score=row['significance_score']
                )
                for row in rows
            ]
            
            self.logger.info(
                f"📋 Retrieved {len(events)} learning events (last {days_back} days) "
                f"for character {character_id}"
            )
            return events
    
    # ========== ANALYTICS QUERIES ==========
    
    async def get_insight_stats(self, character_id: int) -> Dict[str, Any]:
        """
        Get statistics about a character's insights.
        
        Args:
            character_id: Character to analyze
            
        Returns:
            Dictionary with insight statistics
        """
        query = """
            SELECT 
                COUNT(*) as total_insights,
                AVG(confidence_score) as avg_confidence,
                AVG(importance_level) as avg_importance,
                COUNT(DISTINCT insight_type) as unique_types,
                MAX(discovery_date) as last_discovery
            FROM character_insights
            WHERE character_id = $1;
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, character_id)
            
            stats = {
                'total_insights': row['total_insights'],
                'avg_confidence': float(row['avg_confidence']) if row['avg_confidence'] else 0.0,
                'avg_importance': float(row['avg_importance']) if row['avg_importance'] else 0.0,
                'unique_insight_types': row['unique_types'],
                'last_discovery': row['last_discovery']
            }
            
            self.logger.info(
                f"📊 Character {character_id} stats: {stats['total_insights']} insights, "
                f"avg confidence {stats['avg_confidence']:.2f}"
            )
            return stats


# ========== FACTORY FUNCTION ==========

async def create_character_insight_storage(
    postgres_host: str = "localhost",
    postgres_port: int = 5433,
    postgres_db: str = "whisperengine",
    postgres_user: str = "whisperengine",
    postgres_password: str = "whisperengine"
) -> CharacterInsightStorage:
    """
    Create CharacterInsightStorage with database connection pool.
    
    Args:
        postgres_host: PostgreSQL host
        postgres_port: PostgreSQL port
        postgres_db: Database name
        postgres_user: Database user
        postgres_password: Database password
        
    Returns:
        CharacterInsightStorage instance
    """
    db_pool = await asyncpg.create_pool(
        host=postgres_host,
        port=postgres_port,
        database=postgres_db,
        user=postgres_user,
        password=postgres_password,
        min_size=2,
        max_size=10
    )
    
    logger.info(f"✅ Created database connection pool for {postgres_host}:{postgres_port}/{postgres_db}")
    return CharacterInsightStorage(db_pool)
