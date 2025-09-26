"""
Bot Self-Memory System

Core system for storing and querying bot's personal knowledge, self-reflections,
and evolution tracking. Enables bots to have authentic personal memories and
self-awareness capabilities.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import json

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
    """
    
    def __init__(self, bot_name: str, memory_manager: MemoryManagerProtocol):
        self.bot_name = bot_name
        self.memory_manager = memory_manager
        self.namespace = f"bot_self_{bot_name}"
        
        logger.info(f"🧠 Initialized BotSelfMemorySystem for {bot_name}")
    
    async def import_cdl_knowledge(self, character_file: str) -> int:
        """
        Import personal knowledge from CDL character file into bot's memory.
        
        Args:
            character_file: Path to CDL character JSON file
            
        Returns:
            Number of knowledge entries imported
        """
        try:
            # Handle both full paths and just filenames
            if character_file.startswith('characters/'):
                character_path = Path(character_file)
            else:
                character_path = Path(f"characters/examples/{character_file}")
            
            if not character_path.exists():
                logger.error(f"Character file not found: {character_path}")
                return 0
            
            with open(character_path, 'r', encoding='utf-8') as f:
                character_data = json.load(f)
            
            character_section = character_data.get('character', {})
            imported_count = 0
            
            # Import relationship information
            imported_count += await self._import_relationship_knowledge(character_section)
            
            # Import background and life experiences
            imported_count += await self._import_background_knowledge(character_section)
            
            # Import current goals and projects
            imported_count += await self._import_goals_knowledge(character_section)
            
            # Import daily routine and habits
            imported_count += await self._import_routine_knowledge(character_section)
            
            logger.info(f"✅ Imported {imported_count} knowledge entries for {self.bot_name}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import CDL knowledge for {self.bot_name}: {e}")
            return 0
    
    async def _import_relationship_knowledge(self, character_section: Dict) -> int:
        """Import relationship and romantic status information"""
        background = character_section.get('background', {})
        personality = character_section.get('personality', {})
        
        knowledge_entries = []
        
        # Check for explicit relationship information in background
        social_circle = background.get('social_circle', [])
        if social_circle:
            # Look for relationship indicators
            relationship_info = []
            for person in social_circle:
                if isinstance(person, str):
                    if any(word in person.lower() for word in ['boyfriend', 'girlfriend', 'partner', 'spouse']):
                        relationship_info.append(person)
            
            if relationship_info:
                content = f"Current relationships: {'; '.join(relationship_info)}"
            else:
                content = "Currently single and focused on career. Has close friendships and professional relationships but no current romantic partner."
        else:
            # Default assumption for career-focused characters
            content = "Currently single and focused on career development. Open to meaningful relationships but prioritizing professional goals."
        
        knowledge = PersonalKnowledge(
            category="relationships",
            content=content,
            searchable_queries=[
                "boyfriend", "girlfriend", "partner", "dating", "relationship", "single", 
                "romance", "love life", "romantic", "married", "spouse"
            ]
        )
        knowledge_entries.append(knowledge)
        
        # Store in vector memory
        for knowledge in knowledge_entries:
            await self._store_knowledge(knowledge)
        
        return len(knowledge_entries)
    
    async def _import_background_knowledge(self, character_section: Dict) -> int:
        """Import childhood, family, and life experience information"""
        background = character_section.get('background', {})
        knowledge_entries = []
        
        # Life phases information
        life_phases = background.get('life_phases', [])
        if life_phases:
            for phase in life_phases:
                phase_name = phase.get('name', 'Life Phase')
                age_range = phase.get('age_range', 'Unknown age')
                key_events = phase.get('key_events', [])
                
                if key_events:
                    content = f"{phase_name} ({age_range}): {'; '.join(key_events[:3])}"
                    
                    # Determine search queries based on phase name
                    queries = ["childhood", "background", "growing up", "family", "past", "history"]
                    if "childhood" in phase_name.lower() or "upbringing" in phase_name.lower():
                        queries.extend(["childhood", "young", "kid", "family", "parents", "grandmother"])
                    elif "academic" in phase_name.lower() or "education" in phase_name.lower():
                        queries.extend(["school", "college", "university", "education", "learning", "student"])
                    elif "career" in phase_name.lower():
                        queries.extend(["work", "job", "career", "professional", "early career"])
                    
                    knowledge = PersonalKnowledge(
                        category="background",
                        content=content,
                        searchable_queries=queries
                    )
                    knowledge_entries.append(knowledge)
        
        # Family background
        family_background = background.get('family_background')
        if family_background:
            knowledge = PersonalKnowledge(
                category="background",
                content=f"Family background: {family_background}",
                searchable_queries=["family", "parents", "background", "heritage", "upbringing", "roots"]
            )
            knowledge_entries.append(knowledge)
        
        # Formative experiences
        formative_experiences = background.get('formative_experiences', [])
        if formative_experiences:
            content = f"Key formative experiences: {'; '.join(formative_experiences[:4])}"
            knowledge = PersonalKnowledge(
                category="background",
                content=content,
                searchable_queries=["experiences", "formative", "important events", "memories", "defining moments"]
            )
            knowledge_entries.append(knowledge)
        
        # Store in vector memory
        for knowledge in knowledge_entries:
            await self._store_knowledge(knowledge)
        
        return len(knowledge_entries)
    
    async def _import_goals_knowledge(self, character_section: Dict) -> int:
        """Import current goals, projects, and aspirations"""
        background = character_section.get('background', {})
        knowledge_entries = []
        
        # Current goals
        goals = background.get('goals', [])
        if goals:
            content = f"Current goals: {'; '.join(goals[:4])}"
            knowledge = PersonalKnowledge(
                category="current_projects",
                content=content,
                searchable_queries=["goals", "working on", "projects", "future", "plans", "aspirations", "objectives"]
            )
            knowledge_entries.append(knowledge)
        
        # Current projects
        current_projects = background.get('current_projects', [])
        if current_projects:
            project_descriptions = []
            for project in current_projects:
                if isinstance(project, dict):
                    name = project.get('name', 'Unnamed project')
                    description = project.get('description', '')
                    status = project.get('status', 'active')
                    project_descriptions.append(f"{name}: {description} (status: {status})")
                else:
                    project_descriptions.append(str(project))
            
            content = f"Current projects: {'; '.join(project_descriptions[:3])}"
            knowledge = PersonalKnowledge(
                category="current_projects", 
                content=content,
                searchable_queries=["projects", "working on", "research", "work", "current work", "active projects"]
            )
            knowledge_entries.append(knowledge)
        
        # Store in vector memory
        for knowledge in knowledge_entries:
            await self._store_knowledge(knowledge)
        
        return len(knowledge_entries)
    
    async def _import_routine_knowledge(self, character_section: Dict) -> int:
        """Import daily routine and habit information"""
        background = character_section.get('background', {})
        knowledge_entries = []
        
        # Daily routine
        daily_routine = background.get('daily_routine', {})
        if daily_routine:
            routine_parts = []
            for key, value in daily_routine.items():
                if key != 'habits' and value:
                    routine_parts.append(f"{key.replace('_', ' ')}: {value}")
            
            if routine_parts:
                content = f"Daily routine: {'; '.join(routine_parts[:4])}"
                knowledge = PersonalKnowledge(
                    category="daily_routine",
                    content=content,
                    searchable_queries=["routine", "daily", "schedule", "habits", "typical day", "usually do"]
                )
                knowledge_entries.append(knowledge)
            
            # Specific habits
            habits = daily_routine.get('habits', [])
            if habits:
                content = f"Personal habits: {'; '.join(habits[:5])}"
                knowledge = PersonalKnowledge(
                    category="daily_routine",
                    content=content,
                    searchable_queries=["habits", "routine", "regularly do", "always", "usually", "typically"]
                )
                knowledge_entries.append(knowledge)
        
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