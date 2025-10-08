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
        """Build pattern dictionaries for intent classification - ChatGPT-style expanded patterns"""
        return {
            QueryIntent.FACTUAL_RECALL: {
                "keywords": [
                    # Direct questions
                    "what", "which", "list", "show", "tell me about", "give me", "name",
                    # ChatGPT-style natural patterns
                    "do i have", "what are my", "what's my", "remind me", "i have", "my",
                    # Book/collection patterns
                    "books", "collection", "library", "shelf", "titles", "equipment",
                    # Preference patterns
                    "favorite", "preferred", "like", "love", "enjoy", "want", "need"
                ],
                "entities": [
                    "food", "hobby", "place", "person", "book", "art", "music", "movie",
                    "equipment", "tool", "device", "preference", "style", "genre", "author"
                ],
                "verbs": [
                    "like", "love", "prefer", "know", "visit", "own", "want", "need",
                    "collect", "read", "watch", "listen", "use", "practice", "study"
                ]
            },
            QueryIntent.CONVERSATION_STYLE: {
                "keywords": [
                    "how", "when", "where did we", "remember", "conversation", "talked about",
                    "discussed", "mentioned", "said", "told me", "we spoke", "chat"
                ],
                "entities": ["said", "mentioned", "discussed", "spoke about", "conversation"],
                "verbs": ["talk", "say", "mention", "discuss", "speak", "chat", "converse"]
            },
            QueryIntent.TEMPORAL_ANALYSIS: {
                "keywords": [
                    "change", "changed", "evolve", "grow", "trend", "over time", "progress",
                    "development", "history", "timeline", "before", "after", "now vs then"
                ],
                "entities": ["history", "timeline", "progression", "development", "evolution"],
                "verbs": ["become", "grow", "develop", "evolve", "change", "progress", "improve"]
            },
            QueryIntent.RELATIONSHIP_DISCOVERY: {
                "keywords": [
                    "similar", "like", "related", "connected", "alternative", "recommend",
                    "suggest", "compare", "other", "else", "also", "too", "as well"
                ],
                "entities": ["similar to", "like", "alternative", "related", "recommendation"],
                "verbs": ["compare", "relate", "connect", "recommend", "suggest"]
            },
            QueryIntent.ENTITY_SEARCH: {
                "keywords": [
                    "find", "search", "look for", "about", "information", "details",
                    "anything about", "know about", "heard of", "familiar with"
                ],
                "entities": ["information", "details", "data", "facts", "knowledge"],
                "verbs": ["find", "search", "discover", "explore", "locate", "identify"]
            }
        }
    
    async def analyze_query_intent(self, query: str) -> IntentAnalysisResult:
        """
        Analyze query to determine intent and routing strategy with fuzzy matching.
        
        Args:
            query: User's natural language query
            
        Returns:
            IntentAnalysisResult with routing information
        """
        query_lower = query.lower()
        
        # Score each intent type with fuzzy matching
        intent_scores = {}
        for intent_type, patterns in self._intent_patterns.items():
            score = 0.0
            matched_keywords = []
            
            # Check keywords with fuzzy matching
            for keyword in patterns.get("keywords", []):
                # Exact match gets full score
                if keyword in query_lower:
                    score += 2.0
                    matched_keywords.append(keyword)
                # Fuzzy match gets partial score (ChatGPT-style partial matching)
                elif any(word in query_lower for word in keyword.split()):
                    score += 1.0
                    matched_keywords.append(f"~{keyword}")
            
            # Check entities with fuzzy matching
            for entity in patterns.get("entities", []):
                if entity in query_lower:
                    score += 1.5
                    matched_keywords.append(entity)
                # Fuzzy entity matching
                elif any(word in query_lower for word in entity.split()):
                    score += 0.8
                    matched_keywords.append(f"~{entity}")
            
            # Check verbs with fuzzy matching
            for verb in patterns.get("verbs", []):
                if verb in query_lower:
                    score += 1.0
                    matched_keywords.append(verb)
                # Fuzzy verb matching (stem matching)
                elif any(query_lower.find(verb[:4]) != -1 for _ in [verb] if len(verb) > 4):
                    score += 0.5
                    matched_keywords.append(f"~{verb}")
            
            if score > 0:
                intent_scores[intent_type] = (score, matched_keywords)
        
        # Determine primary intent with lower threshold for more liberal matching
        if intent_scores:
            primary_intent = max(intent_scores.items(), key=lambda x: x[1][0])
            intent_type, (confidence, keywords) = primary_intent
            # Normalize confidence to 0-1 range but keep it more liberal
            confidence = min(confidence / 4.0, 1.0)  # Lower divisor = higher confidence
        else:
            # Default to factual recall for unknown queries (ChatGPT-style assumption)
            intent_type = QueryIntent.FACTUAL_RECALL
            confidence = 0.3  # Slightly higher default confidence
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
        """Extract entity type from query - ChatGPT-style expanded categorization"""
        entity_keywords = {
            "food": ["food", "eat", "meal", "restaurant", "cuisine", "dish", "pizza", "pasta", "cooking", "recipe"],
            "hobby": ["hobby", "hobbies", "activity", "activities", "interest", "do for fun", "enjoy doing", "passion"],
            "place": ["place", "location", "city", "country", "visit", "travel", "destination", "live", "been to"],
            "person": ["person", "people", "friend", "family", "colleague", "know", "met", "relationship"],
            "book": ["book", "books", "read", "reading", "author", "novel", "title", "library", "literature"],
            "art": ["art", "artwork", "drawing", "painting", "sketch", "artistic", "creative", "visual", "design"],
            "music": ["music", "song", "album", "artist", "band", "listen", "genre", "sound", "audio"],
            "movie": ["movie", "movies", "film", "cinema", "watch", "director", "actor", "show", "series"],
            "equipment": ["equipment", "tool", "tools", "device", "devices", "gear", "hardware", "machine"],
            "preference": ["like", "prefer", "favorite", "love", "enjoy", "want", "need", "choose"],
            "work": ["work", "job", "career", "profession", "office", "company", "project", "task"],
            "study": ["study", "learn", "education", "school", "course", "class", "subject", "research"],
            "general": ["thing", "stuff", "item", "something", "anything", "everything"]
        }
        
        # Check for entity type keywords with fuzzy matching
        for entity_type, keywords in entity_keywords.items():
            for keyword in keywords:
                if keyword in query:
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
            # Simplified query without character_interactions table (not yet implemented)
            query = """
                SELECT 
                    fe.entity_name,
                    fe.category,
                    ufr.confidence,
                    ufr.relationship_type,
                    ufr.emotional_context,
                    1 as mention_count,
                    ufr.created_at as last_mentioned,
                    CASE WHEN ufr.emotional_context IN ('happy', 'excited', 'joy') THEN 1.0 
                         ELSE 0.5 END as happiness_score
                FROM user_fact_relationships ufr
                JOIN fact_entities fe ON ufr.entity_id = fe.id
                WHERE ufr.user_id = $1
                  AND ($3::TEXT IS NULL OR fe.entity_type = $3)
                  AND (ufr.mentioned_by_character = $2 OR ufr.mentioned_by_character IS NULL)
                ORDER BY ufr.confidence DESC, ufr.created_at DESC
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
            user_id: User identifier (Discord ID or other platform ID)
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
                    # Auto-create user in universal_users if doesn't exist
                    # This ensures FK constraint is satisfied when storing facts
                    await conn.execute("""
                        INSERT INTO universal_users 
                        (universal_id, primary_username, display_name, created_at, last_active)
                        VALUES ($1, $2, $3, NOW(), NOW())
                        ON CONFLICT (universal_id) DO UPDATE SET last_active = NOW()
                    """, user_id, f"user_{user_id[-8:]}", f"User {user_id[-6:]}")
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
    
    async def store_user_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_value: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store user preference in PostgreSQL universal_users.preferences JSONB.
        
        This replaces vector memory preference storage for deterministic, fast retrieval.
        Supports preferred names, timezone, language, communication style, etc.
        
        Args:
            user_id: User identifier (Discord ID or universal ID)
            preference_type: Type of preference ('preferred_name', 'timezone', 'language', etc.)
            preference_value: Value of the preference
            confidence: Confidence score 0-1 (default 1.0 for explicit statements)
            metadata: Optional additional metadata
            
        Returns:
            True if successful
            
        Example:
            await router.store_user_preference(
                user_id="123456789",
                preference_type="preferred_name",
                preference_value="Mark",
                confidence=0.9
            )
        """
        try:
            async with self.postgres.acquire() as conn:
                # Build preference object
                preference_obj = {
                    'value': preference_value,
                    'confidence': confidence,
                    'updated_at': datetime.now().isoformat()
                }
                
                if metadata:
                    preference_obj['metadata'] = metadata
                
                # Auto-create user if doesn't exist (same as store_user_fact)
                await conn.execute("""
                    INSERT INTO universal_users 
                    (universal_id, primary_username, display_name, created_at, last_active, preferences)
                    VALUES ($1, $2, $3, NOW(), NOW(), '{}'::jsonb)
                    ON CONFLICT (universal_id) DO UPDATE SET last_active = NOW()
                """, user_id, f"user_{user_id[-8:]}", f"User {user_id[-6:]}")
                
                # Update preferences JSONB (merge with existing)
                await conn.execute("""
                    UPDATE universal_users
                    SET preferences = COALESCE(preferences::jsonb, '{}'::jsonb) || 
                        jsonb_build_object($2::text, $3::jsonb)
                    WHERE universal_id = $1
                """, user_id, preference_type, json.dumps(preference_obj))
                
                logger.info(f"✅ PREFERENCE: Stored {preference_type}='{preference_value}' for user {user_id} (confidence: {confidence})")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to store user preference: {e}")
            return False
    
    async def get_user_preference(
        self,
        user_id: str,
        preference_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve user preference from PostgreSQL.
        
        Fast, deterministic retrieval (<1ms) vs vector memory search (10-50ms).
        
        Args:
            user_id: User identifier
            preference_type: Type of preference to retrieve
            
        Returns:
            Preference object with 'value', 'confidence', 'updated_at' keys, or None
            
        Example:
            pref = await router.get_user_preference("123456789", "preferred_name")
            if pref:
                name = pref['value']  # "Mark"
                confidence = pref['confidence']  # 0.9
        """
        try:
            async with self.postgres.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT preferences::jsonb -> $2
                    FROM universal_users
                    WHERE universal_id = $1
                """, user_id, preference_type)
                
                if result:
                    # Parse JSON string to dict
                    import json
                    pref_data = json.loads(result) if isinstance(result, str) else result
                    logger.debug(f"🔍 PREFERENCE: Retrieved {preference_type} for user {user_id}: {pref_data.get('value')}")
                    return pref_data
                
                logger.debug(f"🔍 PREFERENCE: No {preference_type} found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve user preference: {e}")
            return None
    
    async def get_all_user_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve all preferences for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of all preferences, empty dict if none found
        """
        try:
            async with self.postgres.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT preferences
                    FROM universal_users
                    WHERE universal_id = $1
                """, user_id)
                
                if result:
                    # Parse if string, return if already dict
                    if isinstance(result, str):
                        import json
                        return json.loads(result) if result else {}
                    return result or {}
                
                return {}
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve all preferences: {e}")
            return {}
    
    async def find_similar_entities(
        self,
        entity_name: str,
        entity_type: Optional[str] = None,
        similarity_threshold: float = 0.3,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find entities similar to the given entity using trigram similarity.
        
        Phase 6: Entity Relationship Discovery
        Uses PostgreSQL trigram matching for fuzzy entity discovery.
        Supports "What's similar to pizza?" type queries.
        
        Args:
            entity_name: Name of entity to find similar matches for
            entity_type: Optional filter by entity type
            similarity_threshold: Minimum similarity score 0-1 (default 0.3)
            limit: Maximum number of results
            
        Returns:
            List of similar entities with similarity scores
            
        Example:
            similar = await router.find_similar_entities("pizza", similarity_threshold=0.4)
            # Returns: [{'entity_name': 'pasta', 'similarity': 0.6}, ...]
        """
        try:
            async with self.postgres.acquire() as conn:
                query = """
                    SELECT 
                        entity_name,
                        entity_type,
                        category,
                        subcategory,
                        similarity(entity_name, $1) as similarity_score
                    FROM fact_entities
                    WHERE 
                        entity_name != $1
                        AND similarity(entity_name, $1) > $2
                        {type_filter}
                    ORDER BY similarity_score DESC
                    LIMIT $3
                """
                
                # Add optional type filter
                if entity_type:
                    query = query.format(type_filter="AND entity_type = $4")
                    results = await conn.fetch(query, entity_name, similarity_threshold, limit, entity_type)
                else:
                    query = query.format(type_filter="")
                    results = await conn.fetch(query, entity_name, similarity_threshold, limit)
                
                similar_entities = [
                    {
                        'entity_name': row['entity_name'],
                        'entity_type': row['entity_type'],
                        'category': row['category'],
                        'subcategory': row['subcategory'],
                        'similarity': float(row['similarity_score'])
                    }
                    for row in results
                ]
                
                logger.info(f"🔍 Found {len(similar_entities)} entities similar to '{entity_name}'")
                return similar_entities
                
        except Exception as e:
            logger.error(f"❌ Failed to find similar entities: {e}")
            return []
    
    async def auto_populate_entity_relationships(
        self,
        entity_id: str,
        entity_name: str,
        entity_type: str,
        similarity_threshold: float = 0.4
    ) -> int:
        """
        Automatically populate entity_relationships table using trigram similarity.
        
        Phase 6: Entity Relationship Discovery
        Called during fact storage to build relationship graph automatically.
        Creates bidirectional 'similar_to' relationships.
        
        Args:
            entity_id: UUID of the entity
            entity_name: Name of the entity
            entity_type: Type of entity
            similarity_threshold: Minimum similarity for relationship creation
            
        Returns:
            Number of relationships created
        """
        try:
            # Find similar entities
            similar_entities = await self.find_similar_entities(
                entity_name=entity_name,
                entity_type=entity_type,
                similarity_threshold=similarity_threshold,
                limit=5  # Top 5 most similar
            )
            
            if not similar_entities:
                return 0
            
            relationships_created = 0
            
            async with self.postgres.acquire() as conn:
                for similar in similar_entities:
                    # Get the similar entity's ID
                    similar_entity_id = await conn.fetchval("""
                        SELECT id FROM fact_entities
                        WHERE entity_name = $1 AND entity_type = $2
                    """, similar['entity_name'], similar['entity_type'])
                    
                    if not similar_entity_id:
                        continue
                    
                    # Create bidirectional relationship
                    await conn.execute("""
                        INSERT INTO entity_relationships 
                            (from_entity_id, to_entity_id, relationship_type, weight, bidirectional)
                        VALUES ($1, $2, 'similar_to', $3, true)
                        ON CONFLICT (from_entity_id, to_entity_id, relationship_type) 
                        DO UPDATE SET weight = EXCLUDED.weight
                    """, entity_id, similar_entity_id, similar['similarity'])
                    
                    relationships_created += 1
            
            logger.info(f"✅ Created {relationships_created} relationships for '{entity_name}'")
            return relationships_created
            
        except Exception as e:
            logger.error(f"❌ Failed to auto-populate relationships: {e}")
            return 0
    
    async def get_related_entities(
        self,
        entity_name: str,
        relationship_type: str = 'similar_to',
        max_hops: int = 1,
        min_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Get entities related to the given entity via graph traversal.
        
        Phase 6: Entity Relationship Discovery
        Supports multi-hop relationship traversal for recommendations.
        
        Args:
            entity_name: Name of starting entity
            relationship_type: Type of relationship to traverse
            max_hops: Maximum hops in graph traversal (1 or 2)
            min_weight: Minimum relationship weight threshold
            
        Returns:
            List of related entities with relationship paths
            
        Example:
            related = await router.get_related_entities("pizza", max_hops=2)
            # Returns entities similar to pizza and entities similar to those
        """
        try:
            async with self.postgres.acquire() as conn:
                # Get starting entity ID
                entity_id = await conn.fetchval("""
                    SELECT id FROM fact_entities WHERE entity_name = $1
                """, entity_name)
                
                if not entity_id:
                    logger.debug(f"🔍 Entity '{entity_name}' not found")
                    return []
                
                if max_hops == 1:
                    # Single-hop query
                    results = await conn.fetch("""
                        SELECT 
                            e.entity_name,
                            e.entity_type,
                            e.category,
                            er.weight,
                            er.relationship_type,
                            1 as hops
                        FROM entity_relationships er
                        JOIN fact_entities e ON e.id = er.to_entity_id
                        WHERE er.from_entity_id = $1
                            AND er.relationship_type = $2
                            AND er.weight >= $3
                        ORDER BY er.weight DESC
                    """, entity_id, relationship_type, min_weight)
                    
                else:
                    # 2-hop query (recursive CTE)
                    results = await conn.fetch("""
                        WITH RECURSIVE entity_graph AS (
                            -- Base case: direct relationships
                            SELECT 
                                e.id,
                                e.entity_name,
                                e.entity_type,
                                e.category,
                                er.weight,
                                er.relationship_type,
                                1 as hops,
                                ARRAY[er.from_entity_id, er.to_entity_id] as path
                            FROM entity_relationships er
                            JOIN fact_entities e ON e.id = er.to_entity_id
                            WHERE er.from_entity_id = $1
                                AND er.relationship_type = $2
                                AND er.weight >= $3
                            
                            UNION
                            
                            -- Recursive case: 2nd hop relationships
                            SELECT 
                                e.id,
                                e.entity_name,
                                e.entity_type,
                                e.category,
                                er.weight * eg.weight as weight,  -- Multiply weights for path strength
                                er.relationship_type,
                                eg.hops + 1 as hops,
                                eg.path || er.to_entity_id as path
                            FROM entity_graph eg
                            JOIN entity_relationships er ON er.from_entity_id = eg.id
                            JOIN fact_entities e ON e.id = er.to_entity_id
                            WHERE eg.hops < $4
                                AND er.relationship_type = $2
                                AND er.weight >= $3
                                AND NOT (er.to_entity_id = ANY(eg.path))  -- Avoid cycles
                        )
                        SELECT DISTINCT ON (entity_name)
                            entity_name,
                            entity_type,
                            category,
                            weight,
                            relationship_type,
                            hops
                        FROM entity_graph
                        WHERE entity_name != $5  -- Exclude starting entity
                        ORDER BY entity_name, weight DESC, hops ASC
                        LIMIT 20
                    """, entity_id, relationship_type, min_weight, max_hops, entity_name)
                
                related_entities = [
                    {
                        'entity_name': row['entity_name'],
                        'entity_type': row['entity_type'],
                        'category': row['category'],
                        'weight': float(row['weight']),
                        'relationship_type': row['relationship_type'],
                        'hops': row['hops']
                    }
                    for row in results
                ]
                
                logger.info(f"🔍 Found {len(related_entities)} related entities for '{entity_name}' ({max_hops}-hop)")
                return related_entities
                
        except Exception as e:
            logger.error(f"❌ Failed to get related entities: {e}")
            return []


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
