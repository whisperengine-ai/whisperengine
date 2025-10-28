"""
Bot Self-Memory System

Core system for storing and querying bot's personal knowledge, self-reflections,
and evolution tracking. Enables bots to have authentic personal memories and
self-awareness capabilities.

HYBRID STORAGE ARCHITECTURE (October 2025):
- Character Knowledge: PostgreSQL CDL database (53+ character_* tables)
- Self-Reflections: PostgreSQL (primary) + Qdrant (semantic) + InfluxDB (metrics)
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import asyncpg

from src.memory.memory_protocol import MemoryManagerProtocol

logger = logging.getLogger(__name__)


@dataclass
class PersonalKnowledge:
    """Represents a piece of bot's personal knowledge"""
    category: str  # relationships, background, goals, current_projects, daily_routine
    content: str
    searchable_queries: List[str]
    confidence_score: float = 1.0
    source: str = "cdl_import"
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(UTC)


@dataclass  
class SelfReflection:
    """Represents bot's self-evaluation of an interaction"""
    interaction_context: str
    bot_response_preview: str
    effectiveness_score: float  # 0.0-1.0
    authenticity_score: float   # 0.0-1.0
    emotional_resonance: float  # 0.0-1.0
    learning_insight: str
    improvement_suggestion: str
    interaction_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(UTC)


class BotSelfMemorySystem:
    """
    Manages bot's personal knowledge base and self-reflection storage.
    Uses isolated vector memory namespace to prevent interference with user conversations.
    
    HYBRID STORAGE (October 2025):
    - Character Knowledge: Read from PostgreSQL CDL database (character_* tables)
    - Self-Reflections: Store in PostgreSQL + Qdrant + InfluxDB (enrichment worker)
    """
    
    def __init__(
        self, 
        bot_name: str, 
        memory_manager: MemoryManagerProtocol,
        db_pool: Optional[asyncpg.Pool] = None
    ):
        self.bot_name = bot_name
        self.memory_manager = memory_manager
        self.namespace = f"bot_self_{bot_name}"
        self.db_pool = db_pool  # PostgreSQL connection pool for CDL queries
        
        logger.info("🧠 Initialized BotSelfMemorySystem for %s", bot_name)
    
    async def import_cdl_knowledge(self, character_id: Optional[int] = None) -> int:
        """
        Import personal knowledge from PostgreSQL CDL database into bot's memory.
        
        Args:
            character_id: Optional character ID. If not provided, queries by bot_name.
            
        Returns:
            Number of knowledge entries imported
        """
        if not self.db_pool:
            logger.error("Cannot import CDL knowledge: No database pool configured")
            return 0
            
        try:
            # Get character_id if not provided
            if character_id is None:
                from src.utils.bot_name_utils import normalize_bot_name
                normalized_name = normalize_bot_name(self.bot_name)
                
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT id FROM characters WHERE normalized_name = $1",
                        normalized_name
                    )
                    if not row:
                        logger.error("Character not found in database: %s", self.bot_name)
                        return 0
                    character_id = row['id']
            
            imported_count = 0
            
            # Import relationship information
            imported_count += await self._import_relationship_knowledge(character_id)
            
            # Import background and life experiences
            imported_count += await self._import_background_knowledge(character_id)
            
            # Import current goals and projects
            imported_count += await self._import_goals_knowledge(character_id)
            
            # Import interests and hobbies
            imported_count += await self._import_interests_knowledge(character_id)
            
            logger.info("✅ Imported %d knowledge entries for %s", imported_count, self.bot_name)
            return imported_count
            
        except Exception as e:
            logger.error("Failed to import CDL knowledge for %s: %s", self.bot_name, e)
            return 0
    
    async def _import_relationship_knowledge(self, character_id: int) -> int:
        """Import relationship and romantic status information from PostgreSQL"""
        if not self.db_pool:
            return 0
            
        knowledge_entries = []
        
        try:
            async with self.db_pool.acquire() as conn:
                # Query character_relationships table
                rows = await conn.fetch("""
                    SELECT related_entity, relationship_type, relationship_strength, 
                           description, status
                    FROM character_relationships 
                    WHERE character_id = $1 
                      AND relationship_strength >= 5
                    ORDER BY relationship_strength DESC
                    LIMIT 20
                """, character_id)
                
                for row in rows:
                    # Create descriptive content
                    rel_type = row['relationship_type'] or 'relationship'
                    related = row['related_entity']
                    desc = row['description'] or f"{rel_type} with {related}"
                    strength = row['relationship_strength']
                    
                    content = f"{rel_type.title()}: {related} (strength: {strength}/10) - {desc}"
                    
                    knowledge = PersonalKnowledge(
                        category="relationships",
                        content=content,
                        searchable_queries=[
                            "boyfriend", "girlfriend", "partner", "dating", "relationship", 
                            "friend", "family", "colleague", related.lower(), rel_type.lower()
                        ],
                        confidence_score=strength / 10.0
                    )
                    knowledge_entries.append(knowledge)
                
                # If no relationships found, add single status
                if not rows:
                    knowledge = PersonalKnowledge(
                        category="relationships",
                        content="Currently single and focused on career. Open to meaningful relationships.",
                        searchable_queries=["boyfriend", "girlfriend", "partner", "dating", "relationship", "single"]
                    )
                    knowledge_entries.append(knowledge)
        
        except Exception as e:
            logger.error("Failed to import relationship knowledge: %s", e)
        
        # Store in vector memory
        for knowledge in knowledge_entries:
            await self._store_knowledge(knowledge)
        
        return len(knowledge_entries)
    
    async def _import_background_knowledge(self, character_id: int) -> int:
        """Import childhood, family, and life experience information from PostgreSQL"""
        if not self.db_pool:
            return 0
            
        knowledge_entries = []
        
        try:
            async with self.db_pool.acquire() as conn:
                # Query character_background table
                rows = await conn.fetch("""
                    SELECT phase_name, age_range, key_events, emotional_impact, 
                           cultural_influences, formative_experience, importance_level
                    FROM character_background 
                    WHERE character_id = $1 
                      AND importance_level >= 7
                    ORDER BY importance_level DESC
                    LIMIT 15
                """, character_id)
                
                for row in rows:
                    phase = row['phase_name'] or 'Life Phase'
                    age = row['age_range'] or 'Past'
                    events = row['key_events'] or ''
                    impact = row['emotional_impact'] or ''
                    
                    # Build content
                    content_parts = [f"{phase} ({age})"]
                    if events:
                        content_parts.append(f"Events: {events[:200]}")
                    if impact:
                        content_parts.append(f"Impact: {impact[:150]}")
                    
                    content = " - ".join(content_parts)
                    
                    # Determine search queries based on phase
                    queries = ["childhood", "background", "growing up", "family", "past", "history"]
                    phase_lower = phase.lower()
                    if "childhood" in phase_lower or "upbringing" in phase_lower:
                        queries.extend(["young", "kid", "parents", "grandmother"])
                    elif "academic" in phase_lower or "education" in phase_lower:
                        queries.extend(["school", "college", "university", "learning", "student"])
                    elif "career" in phase_lower:
                        queries.extend(["work", "job", "professional", "early career"])
                    
                    knowledge = PersonalKnowledge(
                        category="background",
                        content=content,
                        searchable_queries=queries,
                        confidence_score=(row['importance_level'] or 7) / 10.0
                    )
                    knowledge_entries.append(knowledge)
        
        except Exception as e:
            logger.error("Failed to import background knowledge: %s", e)
        
        # Store in vector memory
        for knowledge in knowledge_entries:
            await self._store_knowledge(knowledge)
        
        return len(knowledge_entries)
    
    async def _import_goals_knowledge(self, character_id: int) -> int:
        """Import current goals, projects, and aspirations from PostgreSQL"""
        if not self.db_pool:
            return 0
            
        knowledge_entries = []
        
        try:
            async with self.db_pool.acquire() as conn:
                # Query character_current_goals table
                rows = await conn.fetch("""
                    SELECT goal_name, goal_description, goal_category, priority_level,
                           progress_status, emotional_investment, time_commitment
                    FROM character_current_goals 
                    WHERE character_id = $1 
                      AND priority_level >= 6
                    ORDER BY priority_level DESC
                    LIMIT 10
                """, character_id)
                
                for row in rows:
                    goal = row['goal_name'] or 'Goal'
                    description = row['goal_description'] or ''
                    status = row['progress_status'] or 'active'
                    priority = row['priority_level'] or 7
                    
                    content = f"{goal}: {description[:250]} (Status: {status}, Priority: {priority}/10)"
                    
                    knowledge = PersonalKnowledge(
                        category="current_projects",
                        content=content,
                        searchable_queries=[
                            "goals", "working on", "projects", "future", "plans", 
                            "aspirations", "objectives", goal.lower()
                        ],
                        confidence_score=priority / 10.0
                    )
                    knowledge_entries.append(knowledge)
        
        except Exception as e:
            logger.error("Failed to import goals knowledge: %s", e)
        
        # Store in vector memory
        for knowledge in knowledge_entries:
            await self._store_knowledge(knowledge)
        
        return len(knowledge_entries)
    
    async def _import_interests_knowledge(self, character_id: int) -> int:
        """Import interests, hobbies, and passions from PostgreSQL"""
        if not self.db_pool:
            return 0
            
        knowledge_entries = []
        
        try:
            async with self.db_pool.acquire() as conn:
                # Query character_interests table
                rows = await conn.fetch("""
                    SELECT interest_name, interest_category, engagement_level,
                           description, passion_level
                    FROM character_interests 
                    WHERE character_id = $1 
                      AND engagement_level >= 6
                    ORDER BY engagement_level DESC
                    LIMIT 15
                """, character_id)
                
                for row in rows:
                    interest = row['interest_name'] or 'Interest'
                    category = row['interest_category'] or 'hobby'
                    description = row['description'] or ''
                    engagement = row['engagement_level'] or 7
                    
                    content = f"{category.title()}: {interest} - {description[:200]} (Engagement: {engagement}/10)"
                    
                    knowledge = PersonalKnowledge(
                        category="interests",
                        content=content,
                        searchable_queries=[
                            "interests", "hobbies", "passions", "enjoy", "love", 
                            interest.lower(), category.lower()
                        ],
                        confidence_score=engagement / 10.0
                    )
                    knowledge_entries.append(knowledge)
        
        except Exception as e:
            logger.error("Failed to import interests knowledge: %s", e)
        
        # Store in vector memory
        for knowledge in knowledge_entries:
            await self._store_knowledge(knowledge)
        
        return len(knowledge_entries)
    
    async def _store_knowledge(self, knowledge: PersonalKnowledge):
        """Store personal knowledge in vector memory"""
        try:
            # Create searchable content combining main content and queries
            searchable_content = f"{knowledge.content}\nSearchable terms: {', '.join(knowledge.searchable_queries)}"
            
            metadata = {
                "category": knowledge.category,
                "source": knowledge.source,
                "confidence_score": knowledge.confidence_score,
                "searchable_queries": knowledge.searchable_queries,
                "bot_name": self.bot_name,
                "memory_type": "bot_self_knowledge",
                "created_at": knowledge.created_at.isoformat() if knowledge.created_at else datetime.now(UTC).isoformat()
            }
            
            # Store using bot's isolated namespace
            await self.memory_manager.store_conversation(
                user_id=self.namespace,  # Use bot namespace instead of user ID
                user_message=f"[KNOWLEDGE_IMPORT] {knowledge.category}",
                bot_response=searchable_content,
                metadata=metadata
            )
            
            logger.debug(f"Stored {knowledge.category} knowledge for {self.bot_name}")
            
        except Exception as e:
            logger.error(f"Failed to store knowledge for {self.bot_name}: {e}")
    
    async def query_self_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search bot's personal knowledge for relevant information.
        
        Args:
            query: Search query (e.g., "boyfriend", "childhood", "working on")
            limit: Maximum number of results to return
            
        Returns:
            List of relevant knowledge entries
        """
        try:
            # Query vector memory using bot's namespace
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=self.namespace,
                query=query,
                limit=limit
            )
            
            # Filter and format results
            knowledge_results = []
            for memory in memories:
                metadata = memory.get('metadata', {})
                if metadata.get('memory_type') == 'bot_self_knowledge':
                    # Extract the main content (remove searchable terms)
                    content = memory.get('content', '')
                    if '\nSearchable terms:' in content:
                        content = content.split('\nSearchable terms:')[0]
                    
                    knowledge_results.append({
                        'content': content,
                        'category': metadata.get('category', 'unknown'),
                        'confidence_score': metadata.get('confidence_score', 1.0),
                        'relevance_score': memory.get('relevance_score', 0.0)
                    })
            
            logger.debug(f"Found {len(knowledge_results)} knowledge entries for query: {query}")
            return knowledge_results
            
        except Exception as e:
            logger.error(f"Failed to query self-knowledge for {self.bot_name}: {e}")
            return []
    
    async def store_self_reflection(self, reflection: SelfReflection):
        """Store bot's self-reflection about an interaction"""
        try:
            content = f"""
Self-reflection on interaction:
Context: {reflection.interaction_context}
Response preview: {reflection.bot_response_preview[:100]}...
Effectiveness: {reflection.effectiveness_score:.2f}
Authenticity: {reflection.authenticity_score:.2f} 
Emotional resonance: {reflection.emotional_resonance:.2f}
Learning insight: {reflection.learning_insight}
Improvement suggestion: {reflection.improvement_suggestion}
"""
            
            metadata = {
                **asdict(reflection),
                "bot_name": self.bot_name,
                "memory_type": "bot_self_reflection",
                "created_at": reflection.created_at.isoformat() if reflection.created_at else datetime.now(UTC).isoformat()
            }
            
            await self.memory_manager.store_conversation(
                user_id=self.namespace,
                user_message="[SELF_REFLECTION]",
                bot_response=content.strip(),
                metadata=metadata
            )
            
            logger.info(f"Stored self-reflection for {self.bot_name}: {reflection.learning_insight[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to store self-reflection for {self.bot_name}: {e}")
    
    async def get_recent_insights(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent self-reflection insights for prompt enhancement"""
        try:
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=self.namespace,
                query="self-reflection learning insight",
                limit=limit * 2  # Get more to filter
            )
            
            insights = []
            for memory in memories:
                metadata = memory.get('metadata', {})
                if metadata.get('memory_type') == 'bot_self_reflection':
                    insights.append({
                        'learning_insight': metadata.get('learning_insight', ''),
                        'improvement_suggestion': metadata.get('improvement_suggestion', ''),
                        'effectiveness_score': metadata.get('effectiveness_score', 0.0),
                        'created_at': metadata.get('created_at', '')
                    })
                    
                    if len(insights) >= limit:
                        break
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get recent insights for {self.bot_name}: {e}")
            return []
    
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about bot's self-knowledge"""
        try:
            # Query all bot's self-knowledge
            all_knowledge = await self.memory_manager.retrieve_relevant_memories(
                user_id=self.namespace,
                query="knowledge background goals relationships routine",
                limit=100
            )
            
            # Categorize knowledge
            categories = {}
            reflections_count = 0
            
            for memory in all_knowledge:
                metadata = memory.get('metadata', {})
                memory_type = metadata.get('memory_type', 'unknown')
                
                if memory_type == 'bot_self_knowledge':
                    category = metadata.get('category', 'uncategorized')
                    categories[category] = categories.get(category, 0) + 1
                elif memory_type == 'bot_self_reflection':
                    reflections_count += 1
            
            return {
                'total_knowledge_entries': sum(categories.values()),
                'knowledge_categories': categories,
                'self_reflections': reflections_count,
                'bot_name': self.bot_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get knowledge stats for {self.bot_name}: {e}")
            return {'error': str(e)}


# Factory function for easy integration
def create_bot_self_memory_system(bot_name: str, memory_manager: MemoryManagerProtocol) -> BotSelfMemorySystem:
    """Create a bot self-memory system instance"""
    return BotSelfMemorySystem(bot_name, memory_manager)