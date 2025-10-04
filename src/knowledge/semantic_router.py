"""
Semantic Knowledge Router - Multi-Modal Data Intelligence

Routes queries to optimal data stores based on semantic intent analysis:
- PostgreSQL: Structured facts and relationships
- Qdrant: Conversation semantic similarity
- InfluxDB: Temporal trends and evolution
- CDL: Character personality interpretation

Maintains WhisperEngine's personality-first design while providing
structured factual intelligence.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Types of query intents for routing decisions"""
    FACTUAL_RECALL = "factual_recall"  # "What foods do I like?"
    CONVERSATION_STYLE = "conversation_style"  # "How did we talk about X?"
    TEMPORAL_ANALYSIS = "temporal_analysis"  # "How have my preferences changed?"
    PERSONALITY_KNOWLEDGE = "personality_knowledge"  # CDL character background
    RELATIONSHIP_DISCOVERY = "relationship_discovery"  # "What's similar to X?"
    ENTITY_SEARCH = "entity_search"  # "Find entities about Y"
    USER_ANALYTICS = "user_analytics"  # "What do you know about me?"


@dataclass
class IntentAnalysisResult:
    """Result of query intent analysis"""
    intent_type: QueryIntent
    entity_type: Optional[str] = None  # 'food', 'hobby', etc.
    relationship_type: Optional[str] = None  # 'likes', 'knows', etc.
    category: Optional[str] = None
    confidence: float = 0.0
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class SemanticKnowledgeRouter:
    """
    Smart query router that directs requests to optimal data stores
    based on query intent and data characteristics.
    
    Integrates:
    - PostgreSQL for structured facts and graph queries
    - Qdrant for semantic conversation similarity
    - InfluxDB for temporal trends
    - CDL for character personality
    """
    
    def __init__(self, postgres_pool, qdrant_client=None, influx_client=None):
        """
        Initialize the semantic knowledge router.
        
        Args:
            postgres_pool: AsyncPG connection pool
            qdrant_client: Optional Qdrant client for semantic search
            influx_client: Optional InfluxDB client for temporal data
        """
        self.postgres = postgres_pool
        self.qdrant = qdrant_client
        self.influx = influx_client
        
        # Intent patterns for analysis
        self._intent_patterns = self._build_intent_patterns()
        
        logger.info("🎯 SemanticKnowledgeRouter initialized with multi-modal intelligence")
    
    def _build_intent_patterns(self) -> Dict[QueryIntent, Dict[str, List[str]]]:
        """Build pattern dictionaries for intent classification"""
        return {
            QueryIntent.FACTUAL_RECALL: {
                "keywords": ["what", "which", "list", "show", "tell me about"],
                "entities": ["food", "hobby", "place", "person", "like", "prefer", "favorite"],
                "verbs": ["like", "love", "prefer", "know", "visit", "own", "want"]
            },
            QueryIntent.CONVERSATION_STYLE: {
                "keywords": ["how", "when", "where did we", "remember", "conversation", "talked about"],
                "entities": ["said", "mentioned", "discussed", "spoke about"],
                "verbs": ["talk", "say", "mention", "discuss", "speak"]
            },
            QueryIntent.TEMPORAL_ANALYSIS: {
                "keywords": ["change", "changed", "evolve", "grow", "trend", "over time"],
                "entities": ["history", "timeline", "progression", "development"],
                "verbs": ["become", "grow", "develop", "evolve", "change"]
            },
            QueryIntent.RELATIONSHIP_DISCOVERY: {
                "keywords": ["similar", "like", "related", "connected", "alternative"],
                "entities": ["similar to", "like", "alternative", "related"],
                "verbs": ["compare", "relate", "connect"]
            },
            QueryIntent.ENTITY_SEARCH: {
                "keywords": ["find", "search", "look for", "about"],
                "entities": ["information", "details", "data"],
                "verbs": ["find", "search", "discover", "explore"]
            }
        }
    
    async def analyze_query_intent(self, query: str) -> IntentAnalysisResult:
        """
        Analyze query to determine intent and routing strategy.
        
        Args:
            query: User's natural language query
            
        Returns:
            IntentAnalysisResult with routing information
        """
        query_lower = query.lower()
        
        # Score each intent type
        intent_scores = {}
        for intent_type, patterns in self._intent_patterns.items():
            score = 0.0
            matched_keywords = []
            
            # Check keywords
            for keyword in patterns.get("keywords", []):
                if keyword in query_lower:
                    score += 2.0
                    matched_keywords.append(keyword)
            
            # Check entities
            for entity in patterns.get("entities", []):
                if entity in query_lower:
                    score += 1.5
                    matched_keywords.append(entity)
            
            # Check verbs
            for verb in patterns.get("verbs", []):
                if verb in query_lower:
                    score += 1.0
                    matched_keywords.append(verb)
            
            if score > 0:
                intent_scores[intent_type] = (score, matched_keywords)
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores.items(), key=lambda x: x[1][0])
            intent_type, (confidence, keywords) = primary_intent
        else:
            # Default to factual recall for unknown queries
            intent_type = QueryIntent.FACTUAL_RECALL
            confidence = 0.3
            keywords = []
        
        # Extract entity type if present
        entity_type = self._extract_entity_type(query_lower)
        
        # Extract relationship type if present
        relationship_type = self._extract_relationship_type(query_lower)
        
        logger.debug(f"🎯 Intent analysis: {intent_type.value} (confidence: {confidence:.2f})")
        
        return IntentAnalysisResult(
            intent_type=intent_type,
            entity_type=entity_type,
            relationship_type=relationship_type,
            confidence=confidence,
            keywords=keywords
        )
    
    def _extract_entity_type(self, query: str) -> Optional[str]:
        """Extract entity type from query"""
        entity_keywords = {
            "food": ["food", "eat", "meal", "restaurant", "cuisine", "dish", "pizza", "pasta"],
            "hobby": ["hobby", "hobbies", "activity", "activities", "interest", "do for fun"],
            "place": ["place", "location", "city", "country", "visit", "travel", "destination"],
            "person": ["person", "people", "friend", "family", "know", "met"],
            "media": ["movie", "film", "show", "series", "book", "music", "game"],
            "activity": ["activity", "activities", "do", "doing", "play", "playing"]
        }
        
        for entity_type, keywords in entity_keywords.items():
            if any(kw in query for kw in keywords):
                return entity_type
        
        return None
    
    def _extract_relationship_type(self, query: str) -> Optional[str]:
        """Extract relationship type from query"""
        relationship_keywords = {
            "likes": ["like", "love", "enjoy", "favorite", "prefer"],
            "dislikes": ["dislike", "hate", "don't like", "avoid"],
            "knows": ["know", "familiar", "aware"],
            "visited": ["visited", "been to", "went to", "traveled to"],
            "wants": ["want", "wish", "desire", "hope"],
            "owns": ["own", "have", "possess", "got"]
        }
        
        for rel_type, keywords in relationship_keywords.items():
            if any(kw in query for kw in keywords):
                return rel_type
        
        return "likes"  # Default
    
    async def get_user_facts(
        self, 
        user_id: str, 
        intent: IntentAnalysisResult,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user facts from PostgreSQL based on intent.
        
        Args:
            user_id: User identifier
            intent: Analyzed query intent
            limit: Maximum number of results
            
        Returns:
            List of fact dictionaries
        """
        async with self.postgres.acquire() as conn:
            query = """
                SELECT 
                    fe.entity_name,
                    fe.entity_type,
                    fe.category,
                    ufr.relationship_type,
                    ufr.confidence,
                    ufr.emotional_context,
                    ufr.mentioned_by_character,
                    ufr.updated_at,
                    ufr.context_metadata
                FROM user_fact_relationships ufr
                JOIN fact_entities fe ON ufr.entity_id = fe.id
                WHERE ufr.user_id = $1
                  AND ($2::TEXT IS NULL OR fe.entity_type = $2)
                  AND ($3::TEXT IS NULL OR ufr.relationship_type = $3)
                  AND ufr.confidence > 0.5
                ORDER BY ufr.confidence DESC, ufr.updated_at DESC
                LIMIT $4
            """
            
            rows = await conn.fetch(
                query, 
                user_id, 
                intent.entity_type, 
                intent.relationship_type,
                limit
            )
            
            facts = []
            for row in rows:
                facts.append({
                    "entity_name": row["entity_name"],
                    "entity_type": row["entity_type"],
                    "category": row["category"],
                    "relationship_type": row["relationship_type"],
                    "confidence": row["confidence"],
                    "emotional_context": row["emotional_context"],
                    "mentioned_by_character": row["mentioned_by_character"],
                    "updated_at": row["updated_at"],
                    "context_metadata": row["context_metadata"]
                })
            
            logger.info(f"📊 Retrieved {len(facts)} facts for user {user_id}")
            return facts
    
    async def get_character_aware_facts(
        self,
        user_id: str,
        character_name: str,
        entity_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get facts with character-specific context.
        
        Args:
            user_id: User identifier
            character_name: Character name (e.g., "elena", "marcus")
            entity_type: Optional entity type filter
            limit: Maximum results
            
        Returns:
            List of character-aware facts
        """
        async with self.postgres.acquire() as conn:
            query = """
                SELECT 
                    fe.entity_name,
                    fe.category,
                    ufr.confidence,
                    ufr.relationship_type,
                    ufr.emotional_context,
                    COUNT(ci.id) as mention_count,
                    MAX(ci.created_at) as last_mentioned,
                    AVG(CASE WHEN ufr.emotional_context = 'happy' THEN 1.0 
                             WHEN ufr.emotional_context = 'excited' THEN 1.0
                             ELSE 0.5 END) as happiness_score
                FROM user_fact_relationships ufr
                JOIN fact_entities fe ON ufr.entity_id = fe.id
                LEFT JOIN character_interactions ci ON ci.user_id = ufr.user_id 
                    AND ci.character_name = $2
                    AND ci.entity_references @> jsonb_build_array(fe.entity_name::text)
                WHERE ufr.user_id = $1
                  AND ($3::TEXT IS NULL OR fe.entity_type = $3)
                  AND (ufr.mentioned_by_character = $2 OR ci.id IS NOT NULL)
                GROUP BY fe.entity_name, fe.category, ufr.confidence, 
                         ufr.relationship_type, ufr.emotional_context
                ORDER BY mention_count DESC, ufr.confidence DESC
                LIMIT $4
            """
            
            rows = await conn.fetch(query, user_id, character_name, entity_type, limit)
            
            facts = []
            for row in rows:
                facts.append({
                    "entity_name": row["entity_name"],
                    "category": row["category"],
                    "confidence": row["confidence"],
                    "relationship_type": row["relationship_type"],
                    "emotional_context": row["emotional_context"],
                    "mention_count": row["mention_count"],
                    "last_mentioned": row["last_mentioned"],
                    "happiness_score": float(row["happiness_score"])
                })
            
            logger.info(f"🎭 Retrieved {len(facts)} character-aware facts for {character_name}")
            return facts
    
    async def store_user_fact(
        self,
        user_id: str,
        entity_name: str,
        entity_type: str,
        relationship_type: str = "likes",
        confidence: float = 0.8,
        emotional_context: Optional[str] = None,
        mentioned_by_character: Optional[str] = None,
        source_conversation_id: Optional[str] = None,
        category: Optional[str] = None,
        attributes: Optional[Dict] = None
    ) -> bool:
        """
        Store a user fact in PostgreSQL with automatic relationship discovery.
        
        Args:
            user_id: User identifier
            entity_name: Name of the entity (e.g., "pizza")
            entity_type: Type of entity (e.g., "food")
            relationship_type: Type of relationship (e.g., "likes")
            confidence: Confidence score 0-1
            emotional_context: Optional emotional context
            mentioned_by_character: Character who learned this fact
            source_conversation_id: Source conversation reference
            category: Optional category
            attributes: Optional JSONB attributes
            
        Returns:
            True if successful
        """
        try:
            async with self.postgres.acquire() as conn:
                async with conn.transaction():
                    # Insert or update entity
                    entity_id = await conn.fetchval("""
                        INSERT INTO fact_entities (entity_type, entity_name, category, attributes)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (entity_type, entity_name) 
                        DO UPDATE SET 
                            category = COALESCE($3, fact_entities.category),
                            attributes = fact_entities.attributes || COALESCE($4, '{}'::jsonb),
                            updated_at = NOW()
                        RETURNING id
                    """, entity_type, entity_name, category, json.dumps(attributes or {}))
                    
                    # Insert or update user-fact relationship
                    await conn.execute("""
                        INSERT INTO user_fact_relationships 
                        (user_id, entity_id, relationship_type, confidence, emotional_context, 
                         mentioned_by_character, source_conversation_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (user_id, entity_id, relationship_type)
                        DO UPDATE SET
                            confidence = GREATEST(user_fact_relationships.confidence, $4),
                            emotional_context = COALESCE($5, user_fact_relationships.emotional_context),
                            mentioned_by_character = COALESCE($6, user_fact_relationships.mentioned_by_character),
                            updated_at = NOW()
                    """, user_id, entity_id, relationship_type, confidence, 
                         emotional_context, mentioned_by_character, source_conversation_id)
                    
                    # Auto-discover similar entities using trigram similarity
                    similar_entities = await conn.fetch("""
                        SELECT id, entity_name, 
                               similarity(entity_name, $1) as sim_score
                        FROM fact_entities
                        WHERE entity_type = $2
                          AND id != $3
                          AND similarity(entity_name, $1) > 0.3
                        ORDER BY sim_score DESC
                        LIMIT 5
                    """, entity_name, entity_type, entity_id)
                    
                    # Create entity relationships for similar entities
                    for similar in similar_entities:
                        await conn.execute("""
                            INSERT INTO entity_relationships 
                            (from_entity_id, to_entity_id, relationship_type, weight)
                            VALUES ($1, $2, 'similar_to', $3)
                            ON CONFLICT (from_entity_id, to_entity_id, relationship_type) 
                            DO UPDATE SET weight = GREATEST(entity_relationships.weight, $3)
                        """, entity_id, similar["id"], min(float(similar["sim_score"]), 0.9))
                    
                    logger.info(f"✅ Stored fact: {entity_name} ({entity_type}) for user {user_id}, "
                              f"found {len(similar_entities)} similar entities")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Failed to store user fact: {e}")
            return False
    
    async def search_entities(
        self,
        search_query: str,
        entity_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Full-text search for entities using PostgreSQL.
        
        Args:
            search_query: Search query string
            entity_type: Optional entity type filter
            limit: Maximum results
            
        Returns:
            List of matching entities
        """
        async with self.postgres.acquire() as conn:
            query = """
                SELECT 
                    entity_name,
                    entity_type,
                    category,
                    subcategory,
                    attributes,
                    ts_rank(search_vector, plainto_tsquery('english', $1)) as relevance
                FROM fact_entities
                WHERE search_vector @@ plainto_tsquery('english', $1)
                  AND ($2::TEXT IS NULL OR entity_type = $2)
                ORDER BY relevance DESC
                LIMIT $3
            """
            
            rows = await conn.fetch(query, search_query, entity_type, limit)
            
            entities = []
            for row in rows:
                entities.append({
                    "entity_name": row["entity_name"],
                    "entity_type": row["entity_type"],
                    "category": row["category"],
                    "subcategory": row["subcategory"],
                    "attributes": row["attributes"],
                    "relevance": float(row["relevance"])
                })
            
            logger.info(f"🔍 Found {len(entities)} entities matching '{search_query}'")
            return entities


# Factory function for easy integration
def create_semantic_knowledge_router(
    postgres_pool, 
    qdrant_client=None, 
    influx_client=None
) -> SemanticKnowledgeRouter:
    """
    Factory function to create SemanticKnowledgeRouter.
    
    Args:
        postgres_pool: AsyncPG connection pool
        qdrant_client: Optional Qdrant client
        influx_client: Optional InfluxDB client
        
    Returns:
        Configured SemanticKnowledgeRouter instance
    """
    return SemanticKnowledgeRouter(
        postgres_pool=postgres_pool,
        qdrant_client=qdrant_client,
        influx_client=influx_client
    )
