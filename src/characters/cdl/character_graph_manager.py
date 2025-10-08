"""
Character Graph Manager - PostgreSQL Graph Intelligence for CDL

Provides graph-aware queries for character knowledge with:
- Importance-weighted background entries
- Trigger-based memory activation
- Strength-weighted relationships
- Proficiency-filtered abilities

Mirrors SemanticKnowledgeRouter architecture for user facts,
but applied to character personal knowledge.
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CharacterKnowledgeIntent(Enum):
    """Types of character knowledge queries"""
    FAMILY = "family"
    RELATIONSHIPS = "relationships"
    CAREER = "career"
    EDUCATION = "education"
    SKILLS = "skills"
    MEMORIES = "memories"
    BACKGROUND = "background"
    HOBBIES = "hobbies"
    GENERAL = "general"


@dataclass
class CharacterKnowledgeResult:
    """Result of character knowledge graph query"""
    background: List[Dict[str, Any]]
    memories: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    abilities: List[Dict[str, Any]]
    total_results: int
    intent: CharacterKnowledgeIntent
    
    def is_empty(self) -> bool:
        """Check if result has any data"""
        return self.total_results == 0
    
    def get_summary(self) -> str:
        """Get summary of results"""
        return (
            f"Background: {len(self.background)} entries, "
            f"Memories: {len(self.memories)} entries, "
            f"Relationships: {len(self.relationships)} entries, "
            f"Abilities: {len(self.abilities)} entries"
        )


class CharacterGraphManager:
    """
    PostgreSQL graph intelligence for CDL character data.
    
    Provides intelligent, graph-aware queries for character knowledge
    with importance weighting, trigger-based activation, and relationship
    graph traversal.
    
    Mirrors SemanticKnowledgeRouter architecture but for character data.
    """
    
    def __init__(self, postgres_pool, semantic_router=None):
        """
        Initialize character graph manager.
        
        Args:
            postgres_pool: AsyncPG connection pool
            semantic_router: Optional SemanticKnowledgeRouter for user facts integration
        """
        self.postgres = postgres_pool
        self.semantic_router = semantic_router
        
        # Intent patterns for query routing
        self._intent_patterns = self._build_intent_patterns()
        
        logger.info("🎭 CharacterGraphManager initialized with graph intelligence")
    
    def _build_intent_patterns(self) -> Dict[CharacterKnowledgeIntent, List[str]]:
        """Build pattern dictionaries for intent classification"""
        return {
            CharacterKnowledgeIntent.FAMILY: [
                "family", "parents", "mother", "father", "mom", "dad",
                "sibling", "sister", "brother", "children", "kids", "relatives"
            ],
            CharacterKnowledgeIntent.RELATIONSHIPS: [
                "relationship", "partner", "dating", "married", "spouse",
                "friend", "friends", "close to", "important people"
            ],
            CharacterKnowledgeIntent.CAREER: [
                "career", "job", "work", "professional", "profession",
                "occupation", "experience", "position", "role"
            ],
            CharacterKnowledgeIntent.EDUCATION: [
                "education", "school", "college", "university", "degree",
                "study", "studied", "learning", "training", "certification"
            ],
            CharacterKnowledgeIntent.SKILLS: [
                "skill", "skills", "good at", "expertise", "expert",
                "ability", "abilities", "talented", "proficient"
            ],
            CharacterKnowledgeIntent.MEMORIES: [
                "remember", "memory", "memories", "experience", "happened",
                "past", "story", "stories", "recall"
            ],
            CharacterKnowledgeIntent.HOBBIES: [
                "hobby", "hobbies", "interest", "interests", "enjoy",
                "fun", "free time", "leisure", "passion"
            ]
        }
    
    def detect_intent(self, query_text: str) -> CharacterKnowledgeIntent:
        """
        Detect query intent from text.
        
        Args:
            query_text: User query or message content
            
        Returns:
            Detected intent
        """
        query_lower = query_text.lower()
        
        # Check each intent pattern
        for intent, keywords in self._intent_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent
        
        return CharacterKnowledgeIntent.GENERAL
    
    async def query_character_knowledge(
        self,
        character_name: str,
        query_text: str,
        intent: Optional[CharacterKnowledgeIntent] = None,
        limit: int = 3,
        user_id: Optional[str] = None
    ) -> CharacterKnowledgeResult:
        """
        Graph-aware character knowledge retrieval.
        
        Args:
            character_name: Character name (e.g., "elena", "jake")
            query_text: User query text
            intent: Optional explicit intent (auto-detected if None)
            limit: Maximum results per category
            user_id: Optional user ID for cross-referencing user facts
            
        Returns:
            CharacterKnowledgeResult with weighted, prioritized data
        """
        # Detect intent if not provided
        if intent is None:
            intent = self.detect_intent(query_text)
        
        logger.info("🔍 Querying character knowledge: %s, intent=%s", character_name, intent.value)
        
        # Get character_id
        character_id = await self._get_character_id(character_name)
        if character_id is None:
            logger.warning("⚠️ Character not found: %s", character_name)
            return CharacterKnowledgeResult(
                background=[], memories=[], relationships=[], abilities=[],
                total_results=0, intent=intent
            )
        
        # Query based on intent
        background = await self._query_background(character_id, intent, limit)
        memories = await self._query_memories(character_id, intent, query_text, limit, user_id)
        relationships = await self._query_relationships(character_id, intent, limit)
        abilities = await self._query_abilities(character_id, intent, limit)
        
        # Add cross-pollination if user_id is provided and semantic_router is available
        user_related_knowledge = {}
        if user_id and self.semantic_router:
            try:
                user_related_knowledge = await self.query_cross_pollination(
                    character_id=character_id,
                    user_id=user_id,
                    limit=limit
                )
                
                # Enrich results with user-related knowledge
                if user_related_knowledge.get('shared_interests'):
                    background.extend([
                        {**interest, 'cross_pollinated': True}
                        for interest in user_related_knowledge.get('shared_interests', [])[:2]
                    ])
                    
                if user_related_knowledge.get('character_knowledge_about_user_facts'):
                    memories.extend([
                        {**memory, 'cross_pollinated': True}
                        for memory in user_related_knowledge.get('character_knowledge_about_user_facts', [])[:2]
                    ])
                    
                if user_related_knowledge.get('relevant_abilities'):
                    abilities.extend([
                        {**ability, 'cross_pollinated': True}
                        for ability in user_related_knowledge.get('relevant_abilities', [])[:2]
                    ])
                    
            except Exception as e:
                logger.error("Error in cross-pollination: %s", str(e))
                # Continue without cross-pollination
        
        total = len(background) + len(memories) + len(relationships) + len(abilities)
        
        result = CharacterKnowledgeResult(
            background=background,
            memories=memories,
            relationships=relationships,
            abilities=abilities,
            total_results=total,
            intent=intent
        )
        
        logger.info("✅ Retrieved character knowledge: %s", result.get_summary())
        return result
    
    async def _get_character_id(self, character_name: str) -> Optional[int]:
        """Get character ID from name"""
        async with self.postgres.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM characters WHERE name = $1",
                character_name.lower()
            )
            return row['id'] if row else None
    
    async def _query_background(
        self,
        character_id: int,
        intent: CharacterKnowledgeIntent,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Query character background with importance weighting.
        
        Returns top entries sorted by importance_level.
        """
        async with self.postgres.acquire() as conn:
            # Determine category filter based on intent
            category_filter = self._get_background_category_filter(intent)
            
            if category_filter:
                query = """
                    SELECT 
                        category,
                        period,
                        title,
                        description,
                        date_range,
                        importance_level,
                        created_date
                    FROM character_background
                    WHERE character_id = $1
                      AND description IS NOT NULL
                      AND description != ''
                      AND category = ANY($2::TEXT[])
                    ORDER BY importance_level DESC, created_date DESC
                    LIMIT $3
                """
                rows = await conn.fetch(query, character_id, category_filter, limit)
            else:
                query = """
                    SELECT 
                        category,
                        period,
                        title,
                        description,
                        date_range,
                        importance_level,
                        created_date
                    FROM character_background
                    WHERE character_id = $1
                      AND description IS NOT NULL
                      AND description != ''
                    ORDER BY importance_level DESC, created_date DESC
                    LIMIT $2
                """
                rows = await conn.fetch(query, character_id, limit)
            
            results = []
            for row in rows:
                results.append({
                    'category': row['category'],
                    'period': row['period'],
                    'title': row['title'],
                    'description': row['description'],
                    'date_range': row['date_range'],
                    'importance_level': row['importance_level'],
                    'created_date': row['created_date']
                })
            
            return results
    
    async def _query_memories(
        self,
        character_id: int,
        intent: CharacterKnowledgeIntent,
        query_text: str,
        limit: int,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query character memories with trigger-based activation.
        
        Returns memories triggered by:
        1. Direct query keywords from message
        2. User fact entities from knowledge base (if user_id provided)
        
        ENHANCEMENT: This implementation includes the memory trigger enhancement
        that activates character memories when user facts match memory triggers.
        For example, if the user has mentioned "diving" as a hobby,
        Elena's diving-related memories will automatically surface.
        """
        async with self.postgres.acquire() as conn:
            # Extract potential trigger keywords from query
            trigger_keywords = self._extract_trigger_keywords(query_text, intent)
            
            # ENHANCEMENT: Add user fact entities as additional triggers
            user_fact_triggers = []
            if user_id and self.semantic_router:
                try:
                    # Get user facts and extract entity names as additional triggers
                    from src.knowledge.semantic_router import IntentAnalysisResult, QueryIntent
                    
                    # Create a general intent for fact retrieval
                    general_intent = IntentAnalysisResult(
                        intent_type=QueryIntent.FACTUAL_RECALL,
                        entity_type=None,  # Get all entity types
                        relationship_type=None,  # Get all relationships
                        confidence=0.9,
                        keywords=[]
                    )
                    
                    # Get user facts and extract entity names as triggers
                    user_facts = await self.semantic_router.get_user_facts(user_id, intent=general_intent, limit=10)
                    user_fact_triggers = [fact['entity_name'].lower() for fact in user_facts if 'entity_name' in fact]
                    
                    if user_fact_triggers:
                        logger.info("🔍 Memory triggering: Using %d user fact entities as additional memory triggers", 
                                    len(user_fact_triggers))
                except Exception as e:
                    logger.error("❌ Error getting user facts for memory triggering: %s", e)
            
            # Combine query triggers and user fact triggers
            combined_triggers = list(set(trigger_keywords + user_fact_triggers))  # Deduplicate
            
            if not combined_triggers:
                return []
            
            query = """
                SELECT 
                    memory_type,
                    title,
                    description,
                    emotional_impact,
                    time_period,
                    importance_level,
                    triggers,
                    created_date
                FROM character_memories
                WHERE character_id = $1
                  AND triggers && $2::TEXT[]
                ORDER BY importance_level DESC, emotional_impact DESC
                LIMIT $3
            """
            
            rows = await conn.fetch(query, character_id, combined_triggers, limit)
            
            results = []
            for row in rows:
                results.append({
                    'memory_type': row['memory_type'],
                    'title': row['title'],
                    'description': row['description'],
                    'emotional_impact': row['emotional_impact'],
                    'time_period': row['time_period'],
                    'importance_level': row['importance_level'],
                    'triggers': row['triggers'],
                    'created_date': row['created_date']
                })
            
            return results
    
    async def _query_relationships(
        self,
        character_id: int,
        intent: CharacterKnowledgeIntent,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Query character relationships with strength weighting.
        
        Returns relationships sorted by relationship_strength.
        """
        async with self.postgres.acquire() as conn:
            # Determine relationship type filter based on intent
            relationship_types = self._get_relationship_type_filter(intent)
            
            if relationship_types:
                query = """
                    SELECT 
                        related_entity,
                        relationship_type,
                        relationship_strength,
                        description,
                        status,
                        created_date
                    FROM character_relationships
                    WHERE character_id = $1
                      AND status = 'active'
                      AND relationship_type = ANY($2::TEXT[])
                    ORDER BY relationship_strength DESC, created_date DESC
                    LIMIT $3
                """
                rows = await conn.fetch(query, character_id, relationship_types, limit)
            else:
                query = """
                    SELECT 
                        related_entity,
                        relationship_type,
                        relationship_strength,
                        description,
                        status,
                        created_date
                    FROM character_relationships
                    WHERE character_id = $1
                      AND status = 'active'
                    ORDER BY relationship_strength DESC, created_date DESC
                    LIMIT $2
                """
                rows = await conn.fetch(query, character_id, limit)
            
            results = []
            for row in rows:
                results.append({
                    'related_entity': row['related_entity'],
                    'relationship_type': row['relationship_type'],
                    'relationship_strength': row['relationship_strength'],
                    'description': row['description'],
                    'status': row['status'],
                    'created_date': row['created_date']
                })
            
            return results
    
    async def _query_abilities(
        self,
        character_id: int,
        intent: CharacterKnowledgeIntent,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Query character abilities with proficiency filtering.
        
        Returns abilities sorted by proficiency_level.
        """
        async with self.postgres.acquire() as conn:
            # Determine category filter based on intent
            category_filter = self._get_ability_category_filter(intent)
            
            if category_filter:
                query = """
                    SELECT 
                        category,
                        ability_name,
                        proficiency_level,
                        description,
                        development_method,
                        usage_frequency
                    FROM character_abilities
                    WHERE character_id = $1
                      AND category = ANY($2::TEXT[])
                    ORDER BY proficiency_level DESC, usage_frequency DESC
                    LIMIT $3
                """
                rows = await conn.fetch(query, character_id, category_filter, limit)
            else:
                query = """
                    SELECT 
                        category,
                        ability_name,
                        proficiency_level,
                        description,
                        development_method,
                        usage_frequency
                    FROM character_abilities
                    WHERE character_id = $1
                    ORDER BY proficiency_level DESC, usage_frequency DESC
                    LIMIT $2
                """
                rows = await conn.fetch(query, character_id, limit)
            
            results = []
            for row in rows:
                results.append({
                    'category': row['category'],
                    'ability_name': row['ability_name'],
                    'proficiency_level': row['proficiency_level'],
                    'description': row['description'],
                    'development_method': row['development_method'],
                    'usage_frequency': row['usage_frequency']
                })
            
            return results
    
    def _get_background_category_filter(
        self,
        intent: CharacterKnowledgeIntent
    ) -> Optional[List[str]]:
        """Get background category filter based on intent"""
        filters = {
            CharacterKnowledgeIntent.FAMILY: ['personal', 'family'],
            CharacterKnowledgeIntent.CAREER: ['career', 'professional'],
            CharacterKnowledgeIntent.EDUCATION: ['education', 'academic'],
            CharacterKnowledgeIntent.BACKGROUND: None,  # All categories
            CharacterKnowledgeIntent.GENERAL: None  # All categories
        }
        return filters.get(intent, ['personal', 'career', 'education'])
    
    def _get_relationship_type_filter(
        self,
        intent: CharacterKnowledgeIntent
    ) -> Optional[List[str]]:
        """Get relationship type filter based on intent"""
        filters = {
            CharacterKnowledgeIntent.FAMILY: ['family', 'parent', 'sibling', 'child'],
            CharacterKnowledgeIntent.RELATIONSHIPS: None,  # All types
            CharacterKnowledgeIntent.CAREER: ['colleague', 'mentor', 'professional']
        }
        return filters.get(intent)
    
    def _get_ability_category_filter(
        self,
        intent: CharacterKnowledgeIntent
    ) -> Optional[List[str]]:
        """Get ability category filter based on intent"""
        filters = {
            CharacterKnowledgeIntent.CAREER: ['professional', 'technical'],
            CharacterKnowledgeIntent.SKILLS: None,  # All categories
            CharacterKnowledgeIntent.HOBBIES: ['hobby', 'recreational', 'social']
        }
        return filters.get(intent)
    
    def _extract_trigger_keywords(
        self,
        query_text: str,
        intent: CharacterKnowledgeIntent
    ) -> List[str]:
        """
        Extract trigger keywords from query text.
        
        Returns keywords that might match memory triggers array.
        """
        query_lower = query_text.lower()
        
        # Start with intent keywords
        keywords = set(self._intent_patterns.get(intent, []))
        
        # Add words from query (filter common words)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
                       'for', 'of', 'with', 'by', 'about', 'tell', 'me', 'your',
                       'what', 'how', 'when', 'where', 'why', 'who', 'is', 'are',
                       'was', 'were', 'do', 'does', 'did', 'have', 'has', 'had'}
        
        words = query_lower.split()
        for word in words:
            # Remove punctuation
            word = word.strip('.,!?;:')
            if word and word not in common_words and len(word) > 2:
                keywords.add(word)
        
        return list(keywords)
    
    async def find_related_memories(
        self,
        character_name: str,
        trigger_keywords: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find memories activated by specific trigger keywords.
        
        Args:
            character_name: Character name
            trigger_keywords: List of trigger keywords
            limit: Maximum results
            
        Returns:
            List of memories with matching triggers
        """
        character_id = await self._get_character_id(character_name)
        if character_id is None:
            return []
        
        async with self.postgres.acquire() as conn:
            query = """
                SELECT 
                    memory_type,
                    title,
                    description,
                    emotional_impact,
                    importance_level,
                    triggers
                FROM character_memories
                WHERE character_id = $1
                  AND triggers && $2::TEXT[]
                ORDER BY importance_level DESC, emotional_impact DESC
                LIMIT $3
            """
            
            rows = await conn.fetch(query, character_id, trigger_keywords, limit)
            
            results = []
            for row in rows:
                results.append({
                    'memory_type': row['memory_type'],
                    'title': row['title'],
                    'description': row['description'],
                    'emotional_impact': row['emotional_impact'],
                    'importance_level': row['importance_level'],
                    'triggers': row['triggers']
                })
            
            return results
    
    async def get_relationship_graph(
        self,
        character_name: str,
        relationship_types: Optional[List[str]] = None,
        min_strength: int = 5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get character's relationship network with strength weighting.
        
        Args:
            character_name: Character name
            relationship_types: Optional list of relationship types to filter
            min_strength: Minimum relationship strength (1-10)
            limit: Maximum results
            
        Returns:
            List of relationships sorted by strength
        """
        character_id = await self._get_character_id(character_name)
        if character_id is None:
            return []
        
        async with self.postgres.acquire() as conn:
            query = """
                SELECT 
                    related_entity,
                    relationship_type,
                    relationship_strength,
                    description,
                    status
                FROM character_relationships
                WHERE character_id = $1
                  AND relationship_strength >= $2
                  AND status = 'active'
                  AND ($3::TEXT[] IS NULL OR relationship_type = ANY($3::TEXT[]))
                ORDER BY relationship_strength DESC
                LIMIT $4
            """
            
            rows = await conn.fetch(
                query, character_id, min_strength, relationship_types, limit
            )
            
            results = []
            for row in rows:
                results.append({
                    'related_entity': row['related_entity'],
                    'relationship_type': row['relationship_type'],
                    'relationship_strength': row['relationship_strength'],
                    'description': row['description'],
                    'status': row['status']
                })
            
            return results
    
    async def query_abilities_by_context(
        self,
        character_name: str,
        context: str,
        min_proficiency: int = 5,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query abilities filtered by usage context and proficiency.
        
        Args:
            character_name: Character name
            context: Context keyword (e.g., 'professional', 'hobby', 'social')
            min_proficiency: Minimum proficiency level (1-10)
            limit: Maximum results
            
        Returns:
            List of abilities sorted by proficiency
        """
        character_id = await self._get_character_id(character_name)
        if character_id is None:
            return []
        
        async with self.postgres.acquire() as conn:
            query = """
                SELECT 
                    category,
                    ability_name,
                    proficiency_level,
                    description,
                    usage_frequency
                FROM character_abilities
                WHERE character_id = $1
                  AND proficiency_level >= $2
                  AND (category ILIKE '%' || $3 || '%' 
                       OR ability_name ILIKE '%' || $3 || '%'
                       OR description ILIKE '%' || $3 || '%')
                ORDER BY proficiency_level DESC
                LIMIT $4
            """
            
            rows = await conn.fetch(
                query, character_id, min_proficiency, context, limit
            )
            
            results = []
            for row in rows:
                results.append({
                    'category': row['category'],
                    'ability_name': row['ability_name'],
                    'proficiency_level': row['proficiency_level'],
                    'description': row['description'],
                    'usage_frequency': row['usage_frequency']
                })
            
            return results


    async def query_cross_pollination(
        self,
        character_id: int,
        user_id: str,
        limit: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Cross-reference character knowledge with user facts.
        
        Enables:
        - Finding shared interests between character and user
        - Connecting character abilities to user mentioned entities
        - Discovering character knowledge relevant to user facts
        
        Args:
            character_id: Character ID
            user_id: User ID
            limit: Maximum results
            
        Returns:
            Dictionary of cross-pollinated knowledge
        """
        # Skip if semantic router isn't available
        if not self.semantic_router:
            return {
                'shared_interests': [],
                'relevant_abilities': [],
                'character_knowledge_about_user_facts': []
            }
            
        try:
            # Step 1: Get user facts from semantic router
            user_facts = await self._get_user_facts(user_id)
            
            if not user_facts:
                return {
                    'shared_interests': [],
                    'relevant_abilities': [],
                    'character_knowledge_about_user_facts': []
                }
                
            # Step 2: Find character interests that match user facts
            shared_interests = await self._find_shared_interests(character_id, user_facts, limit)
            
            # Step 3: Find character abilities related to user facts
            relevant_abilities = await self._find_relevant_abilities(character_id, user_facts, limit)
            
            # Step 4: Find character knowledge about user-mentioned entities
            character_knowledge = await self._find_character_knowledge_about_user_facts(
                character_id, user_facts, limit
            )
            
            return {
                'shared_interests': shared_interests,
                'relevant_abilities': relevant_abilities,
                'character_knowledge_about_user_facts': character_knowledge
            }
            
        except Exception as e:
            logger.error("Error in cross-pollination query: %s", e)
            return {
                'shared_interests': [],
                'relevant_abilities': [],
                'character_knowledge_about_user_facts': []
            }
    
    async def _get_user_facts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user facts from semantic router"""
        if not self.semantic_router:
            return []
            
        try:
            # Create a general intent for fact retrieval
            from src.knowledge.semantic_router import IntentAnalysisResult, QueryIntent
            general_intent = IntentAnalysisResult(
                intent_type=QueryIntent.FACTUAL_RECALL,
                entity_type=None,  # Get all entity types
                relationship_type=None,  # Get all relationships
                confidence=0.9,
                keywords=[]
            )
            
            # Use the semantic router to get user facts
            user_facts = await self.semantic_router.get_user_facts(user_id, intent=general_intent, limit=10)
            return user_facts
        except Exception as e:
            logger.error("Error getting user facts: %s", e)
            return []
    
    async def _find_shared_interests(
        self,
        character_id: int,
        user_facts: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Find shared interests between character and user"""
        if not user_facts:
            return []
            
        # Extract entity names from user facts
        entity_names = [fact.get('entity_name', '') for fact in user_facts]
        entity_names = [name for name in entity_names if name]
        
        if not entity_names:
            return []
            
        async with self.postgres.acquire() as conn:
            # Query character interests that match user fact entities
            shared_interests = []
            
            # Check character_background (hobbies, interests)
            interests_query = """
                SELECT 
                    title,
                    category,
                    description,
                    importance_level
                FROM character_background
                WHERE character_id = $1
                  AND category IN ('interests', 'hobbies')
                  AND (
                      title ILIKE ANY($2::TEXT[])
                      OR description ILIKE ANY($3::TEXT[])
                  )
                ORDER BY importance_level DESC
                LIMIT $4
            """
            
            # Format entity names for LIKE queries
            like_patterns = [f"%{name}%" for name in entity_names]
            
            rows = await conn.fetch(
                interests_query,
                character_id,
                entity_names,
                like_patterns,
                limit
            )
            
            for row in rows:
                shared_interests.append({
                    'title': row['title'],
                    'category': row['category'],
                    'description': row['description'],
                    'importance_level': row['importance_level'],
                    'source': 'background'
                })
                
            return shared_interests
    
    async def _find_relevant_abilities(
        self,
        character_id: int,
        user_facts: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Find character abilities related to user facts"""
        if not user_facts:
            return []
            
        # Extract entity names from user facts
        entity_names = [fact.get('entity_name', '') for fact in user_facts]
        entity_names = [name for name in entity_names if name]
        
        if not entity_names:
            return []
            
        async with self.postgres.acquire() as conn:
            # Query character abilities related to user facts
            abilities_query = """
                SELECT 
                    ability_name,
                    category,
                    description,
                    proficiency_level,
                    usage_frequency
                FROM character_abilities
                WHERE character_id = $1
                  AND (
                      ability_name ILIKE ANY($2::TEXT[])
                      OR description ILIKE ANY($3::TEXT[])
                      OR category ILIKE ANY($3::TEXT[])
                  )
                ORDER BY proficiency_level DESC
                LIMIT $4
            """
            
            # Format entity names for LIKE queries
            like_patterns = [f"%{name}%" for name in entity_names]
            
            rows = await conn.fetch(
                abilities_query,
                character_id,
                entity_names,
                like_patterns,
                limit
            )
            
            relevant_abilities = []
            for row in rows:
                relevant_abilities.append({
                    'ability_name': row['ability_name'],
                    'category': row['category'],
                    'description': row['description'],
                    'proficiency_level': row['proficiency_level'],
                    'usage_frequency': row['usage_frequency']
                })
                
            return relevant_abilities
    
    async def _find_character_knowledge_about_user_facts(
        self,
        character_id: int,
        user_facts: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Find character knowledge about user-mentioned entities"""
        if not user_facts:
            return []
            
        # Extract entity names from user facts
        entity_names = [fact.get('entity_name', '') for fact in user_facts]
        entity_names = [name for name in entity_names if name]
        
        if not entity_names:
            return []
            
        async with self.postgres.acquire() as conn:
            # Query character memories related to user facts
            memories_query = """
                SELECT 
                    title,
                    description,
                    memory_type,
                    emotional_impact,
                    importance_level
                FROM character_memories
                WHERE character_id = $1
                  AND (
                      title ILIKE ANY($2::TEXT[])
                      OR description ILIKE ANY($2::TEXT[])
                  )
                ORDER BY importance_level DESC
                LIMIT $3
            """
            
            # Format entity names for LIKE queries
            like_patterns = [f"%{name}%" for name in entity_names]
            
            rows = await conn.fetch(
                memories_query,
                character_id,
                like_patterns,
                limit
            )
            
            character_knowledge = []
            for row in rows:
                character_knowledge.append({
                    'title': row['title'],
                    'description': row['description'],
                    'memory_type': row['memory_type'],
                    'emotional_impact': row['emotional_impact'],
                    'importance_level': row['importance_level'],
                    'source': 'memory'
                })
                
            return character_knowledge


def create_character_graph_manager(postgres_pool, semantic_router=None) -> CharacterGraphManager:
    """
    Factory function to create CharacterGraphManager instance.
    
    Args:
        postgres_pool: AsyncPG connection pool
        semantic_router: Optional SemanticKnowledgeRouter for user facts integration
        
    Returns:
        CharacterGraphManager instance
    """
    return CharacterGraphManager(postgres_pool, semantic_router)
