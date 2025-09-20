"""
Character Memory Integration

This module integrates character personal memories with the main WhisperEngine
memory and conversation system. It bridges character self-memories with user
conversations and existing memory management.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json

from src.characters.memory.self_memory import CharacterSelfMemoryManager, PersonalMemory, MemoryType, EmotionalWeight
from src.characters.models.character import Character
from src.memory.core.memory_interface import MemoryManagerProtocol

logger = logging.getLogger(__name__)


class CharacterMemoryIntegrator:
    """
    Integrates character personal memories with the main memory system.
    
    This class ensures character memories are properly contextualized within
    conversations while maintaining separation from user memories.
    """
    
    def __init__(self, 
                 character: Character,
                 user_memory_manager: Optional[MemoryManagerProtocol] = None):
        self.character = character
        self.character_id = character.metadata.character_id
        self.logger = logging.getLogger(__name__)
        
        # Character's personal memory system
        self.self_memory = CharacterSelfMemoryManager(self.character_id)
        
        # Connection to user/conversation memory system
        self.user_memory_manager = user_memory_manager
        
        # Integration settings
        self.max_context_memories = 5
        self.memory_relevance_threshold = 0.4
        self.daily_reflection_enabled = True
        
        # Mark that we need to initialize character memories
        self._initialized = False
    
    async def ensure_initialized(self):
        """Ensure character memories are initialized"""
        if not self._initialized:
            await self._initialize_character_memories()
            self._initialized = True
    
    async def _initialize_character_memories(self):
        """Initialize character with their background memories"""
        try:
            # Check if character already has memories
            existing_stats = self.self_memory.get_memory_statistics()
            if existing_stats.get('total_memories', 0) > 0:
                self.logger.debug("Character %s already has %d memories", 
                                self.character_id, existing_stats['total_memories'])
                return
            
            # Create initial memories from character background
            await self._create_background_memories()
            
            self.logger.info("Initialized character memories for %s", self.character.identity.name)
            
        except (ValueError, TypeError, OSError) as e:
            self.logger.error("Failed to initialize character memories: %s", e)
    
    async def _create_background_memories(self):
        """Create initial memories from character definition"""
        try:
            # Extract memories from character background
            background_memories = self._extract_background_memories()
            
            # Store each memory
            for memory_data in background_memories:
                memory = PersonalMemory(
                    memory_id=memory_data['id'],
                    character_id=self.character_id,
                    content=memory_data['content'],
                    memory_type=memory_data['type'],
                    emotional_weight=memory_data['weight'],
                    formative_impact=memory_data['impact'],
                    themes=memory_data['themes'],
                    created_date=memory_data.get('date', datetime.now()),
                    age_when_formed=memory_data.get('age'),
                    location=memory_data.get('location'),
                    related_people=memory_data.get('people', [])
                )
                
                self.self_memory.store_memory(memory)
            
            self.logger.info("Created %d background memories for %s", 
                           len(background_memories), self.character.identity.name)
            
        except (ValueError, TypeError) as e:
            self.logger.error("Failed to create background memories: %s", e)
    
    def _extract_background_memories(self) -> List[Dict[str, Any]]:
        """Extract memories from character background text"""
        import uuid
        
        memories = []
        
        # Parse background for memory-worthy events
        # Combine various background elements
        background_text = []
        if self.character.backstory.family_background:
            background_text.append(self.character.backstory.family_background)
        if self.character.backstory.cultural_background:
            background_text.append(self.character.backstory.cultural_background)
        background_text.extend(self.character.backstory.major_life_events)
        
        background = " ".join(background_text).lower()
        
        # Example memory extraction (simplified - could use NLP)
        if "childhood" in background or self.character.backstory.childhood.key_events:
            memories.append({
                'id': str(uuid.uuid4()),
                'content': f"Childhood experiences that shaped {self.character.identity.name}",
                'type': MemoryType.CHILDHOOD,
                'weight': EmotionalWeight.HIGH.value,
                'impact': 'high',
                'themes': ['childhood', 'formative'],
                'age': 8
            })
        
        if "education" in background.lower() or "school" in background.lower():
            memories.append({
                'id': str(uuid.uuid4()),
                'content': "Educational experiences and learning journey",
                'type': MemoryType.EDUCATION,
                'weight': EmotionalWeight.MEDIUM.value,
                'impact': 'medium',
                'themes': ['education', 'learning'],
                'age': 16
            })
        
        if "work" in background.lower() or "career" in background.lower():
            memories.append({
                'id': str(uuid.uuid4()),
                'content': "Career development and professional experiences",
                'type': MemoryType.CAREER,
                'weight': EmotionalWeight.MEDIUM.value,
                'impact': 'medium',
                'themes': ['career', 'professional'],
                'age': 25
            })
        
        # Add core personality memory
        memories.append({
            'id': str(uuid.uuid4()),
            'content': f"Core personality traits and behavioral patterns: {self.character.personality}",
            'type': MemoryType.REFLECTION,
            'weight': EmotionalWeight.PROFOUND.value,
            'impact': 'high',
            'themes': ['personality', 'identity', 'self-awareness'],
            'age': self.character.identity.age
        })
        
        return memories
    
    def _create_basic_memories_sync(self):
        """Create basic character memories synchronously"""
        try:
            # Create a simple background memory
            import uuid
            from datetime import datetime
            
            basic_memory = PersonalMemory(
                memory_id=str(uuid.uuid4()),
                character_id=self.character_id,
                content=f"Core identity: I am {self.character.identity.name}, {self.character.identity.occupation}",
                memory_type=MemoryType.REFLECTION,
                emotional_weight=EmotionalWeight.MEDIUM.value,
                formative_impact="medium",
                themes=["identity", "core_self"],
                created_date=datetime.now()
            )
            
            self.self_memory.store_memory(basic_memory)
            
        except Exception as e:
            self.logger.error("Failed to create basic memories: %s", e)
    
    async def get_relevant_memories_for_conversation(self, 
                                                   themes: Optional[List[str]] = None) -> List[PersonalMemory]:
        """
        Get character memories relevant to current conversation context.
        
        This method finds character memories that should influence their
        responses in the current conversation.
        """
        await self.ensure_initialized()
        
        try:
            # Start with theme-based recall if themes provided
            relevant_memories = []
            
            if themes:
                relevant_memories.extend(
                    self.self_memory.recall_memories(
                        themes=themes,
                        limit=self.max_context_memories,
                        boost_recall=True
                    )
                )
            
            # Always include most formative memories for personality consistency
            formative_memories = self.self_memory.get_formative_memories(limit=2)
            relevant_memories.extend(formative_memories)
            
            # Add recent reflections for character development
            recent_reflections = self.self_memory.get_memories_by_type(
                MemoryType.REFLECTION, limit=1
            )
            relevant_memories.extend(recent_reflections)
            
            # Remove duplicates and limit total
            seen_ids = set()
            unique_memories = []
            for memory in relevant_memories:
                if memory.memory_id not in seen_ids:
                    unique_memories.append(memory)
                    seen_ids.add(memory.memory_id)
                    
                if len(unique_memories) >= self.max_context_memories:
                    break
            
            self.logger.debug("Retrieved %d relevant memories for conversation", 
                            len(unique_memories))
            return unique_memories
            
        except (ValueError, TypeError) as e:
            self.logger.error("Failed to get relevant memories: %s", e)
            return []
    
    async def create_conversation_memory(self, 
                                       conversation_content: str,
                                       user_message: str,
                                       character_response: str,
                                       emotional_context: Optional[Dict] = None) -> Optional[PersonalMemory]:
        """
        Create a character memory from a significant conversation.
        
        Not all conversations become memories - only emotionally significant
        or character-developing interactions.
        """
        try:
            # Analyze if conversation warrants a memory
            should_remember, memory_type, emotional_weight = self._analyze_conversation_significance(
                user_message, character_response, emotional_context
            )
            
            if not should_remember:
                return None
            
            # Create memory content
            memory_content = self._format_conversation_memory(
                user_message, character_response, emotional_context
            )
            
            # Extract themes from conversation
            themes = self.extract_conversation_themes(conversation_content)
            
            # Create memory
            import uuid
            memory = PersonalMemory(
                memory_id=str(uuid.uuid4()),
                character_id=self.character_id,
                content=memory_content,
                memory_type=memory_type,
                emotional_weight=emotional_weight,
                formative_impact=self._determine_formative_impact(emotional_weight),
                themes=themes,
                created_date=datetime.now(),
                metadata={
                    'conversation_type': 'user_interaction',
                    'emotional_context': emotional_context,
                    'user_triggered': True
                }
            )
            
            # Store memory
            if self.self_memory.store_memory(memory):
                self.logger.info("Created conversation memory for character %s", self.character.identity.name)
                return memory
            
            return None
            
        except (ValueError, TypeError) as e:
            self.logger.error("Failed to create conversation memory: %s", e)
            return None
    
    async def add_daily_reflection(self, reflection_themes: Optional[List[str]] = None) -> Optional[PersonalMemory]:
        """Add a daily reflection based on recent experiences"""
        if not self.daily_reflection_enabled:
            return None
        
        try:
            # Get recent memories to reflect on
            recent_memories = self.self_memory.get_recent_memories(days=1, limit=5)
            
            if not recent_memories:
                return None
            
            # Generate reflection content
            reflection_content = self._generate_reflection_content(recent_memories)
            
            # Determine themes
            if not reflection_themes:
                reflection_themes = self._extract_reflection_themes(recent_memories)
            
            # Create reflection memory
            reflection = self.self_memory.add_daily_reflection(
                reflection_content, reflection_themes
            )
            
            self.logger.info("Added daily reflection for character %s", self.character.identity.name)
            return reflection
            
        except (ValueError, TypeError) as e:
            self.logger.error("Failed to add daily reflection: %s", e)
            return None
    
    def format_memories_for_prompt(self, memories: List[PersonalMemory]) -> str:
        """
        Format character memories for inclusion in conversation prompts.
        
        This creates a natural language summary of relevant memories that
        helps maintain character consistency and depth.
        """
        if not memories:
            return ""
        
        try:
            # Group memories by type
            memory_groups = {}
            for memory in memories:
                mem_type = memory.memory_type.value
                if mem_type not in memory_groups:
                    memory_groups[mem_type] = []
                memory_groups[mem_type].append(memory)
            
            # Format each group
            sections = []
            
            # Formative memories first
            formative_types = ['childhood', 'education', 'career', 'trauma']
            for mem_type in formative_types:
                if mem_type in memory_groups:
                    memories_text = ' '.join([
                        mem.content[:200] for mem in memory_groups[mem_type]
                    ])
                    sections.append(f"**{mem_type.title()}**: {memories_text}")
            
            # Recent experiences
            if 'daily_event' in memory_groups or 'reflection' in memory_groups:
                recent_memories = memory_groups.get('daily_event', []) + memory_groups.get('reflection', [])
                if recent_memories:
                    recent_text = ' '.join([
                        mem.content[:150] for mem in recent_memories[-2:]  # Last 2 recent memories
                    ])
                    sections.append(f"**Recent Experiences**: {recent_text}")
            
            # Join sections
            formatted = '\n'.join(sections)
            
            return f"\n## {self.character.identity.name}'s Relevant Memories\n{formatted}\n"
            
        except (ValueError, TypeError) as e:
            self.logger.error("Failed to format memories for prompt: %s", e)
            return ""
    
    def get_character_memory_context(self, conversation_themes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comprehensive character memory context for conversation.
        
        Returns both formatted memory text and structured data for
        advanced prompt engineering.
        """
        try:
            # Get relevant memories (sync version for non-async contexts)
            memories = []
            
            # Simple sync initialization check
            stats = self.self_memory.get_memory_statistics()
            if stats.get('total_memories', 0) == 0:
                # Initialize synchronously with basic memories
                self._create_basic_memories_sync()
            
            # Get memories based on themes
            if conversation_themes:
                memories = self.self_memory.recall_memories(
                    themes=conversation_themes,
                    limit=self.max_context_memories,
                    boost_recall=False  # Don't boost for context retrieval
                )
            
            # Always include some formative memories
            formative_memories = self.self_memory.get_formative_memories(limit=2)
            memories.extend(formative_memories)
            
            # Remove duplicates
            seen_ids = set()
            unique_memories = []
            for memory in memories:
                if memory.memory_id not in seen_ids:
                    unique_memories.append(memory)
                    seen_ids.add(memory.memory_id)
            
            # Get memory statistics
            stats = self.self_memory.get_memory_statistics()
            
            return {
                'memories': unique_memories,
                'formatted_memories': self.format_memories_for_prompt(unique_memories),
                'memory_count': len(unique_memories),
                'total_memories': stats.get('total_memories', 0),
                'average_emotional_weight': stats.get('average_emotional_weight', 0.0),
                'dominant_themes': self._get_dominant_themes(unique_memories),
                'character_development_level': self._calculate_development_level(stats)
            }
            
        except (ValueError, TypeError) as e:
            self.logger.error("Failed to get character memory context: %s", e)
            return {
                'memories': [],
                'formatted_memories': '',
                'memory_count': 0,
                'total_memories': 0,
                'average_emotional_weight': 0.0,
                'dominant_themes': [],
                'character_development_level': 'basic'
            }
    
    def _analyze_conversation_significance(self, 
                                         user_message: str, 
                                         character_response: str,
                                         emotional_context: Optional[Dict]) -> Tuple[bool, MemoryType, float]:
        """Analyze if a conversation should become a character memory"""
        
        # Check emotional intensity
        emotional_weight = 0.2  # Default low significance
        
        if emotional_context:
            # Use emotional AI data if available
            emotion_intensity = emotional_context.get('intensity', 0.5)
            emotional_weight = max(emotional_weight, emotion_intensity * 0.8)
        
        # Check for significant topics
        significant_keywords = [
            'love', 'hate', 'fear', 'dream', 'goal', 'family', 'death',
            'success', 'failure', 'memory', 'childhood', 'future', 'hope'
        ]
        
        combined_text = (user_message + ' ' + character_response).lower()
        keyword_matches = sum(1 for keyword in significant_keywords if keyword in combined_text)
        
        if keyword_matches > 0:
            emotional_weight += keyword_matches * 0.1
        
        # Determine memory type
        memory_type = MemoryType.DAILY_EVENT
        if any(word in combined_text for word in ['feel', 'emotion', 'think', 'realize']):
            memory_type = MemoryType.EMOTIONAL_MOMENT
        if any(word in combined_text for word in ['learn', 'understand', 'discover']):
            memory_type = MemoryType.LEARNING
        if any(word in combined_text for word in ['goal', 'plan', 'future', 'want']):
            memory_type = MemoryType.GOAL
        
        # Decision threshold
        should_remember = emotional_weight >= self.memory_relevance_threshold
        
        return should_remember, memory_type, min(emotional_weight, 1.0)
    
    def _format_conversation_memory(self, 
                                  user_message: str, 
                                  character_response: str,
                                  emotional_context: Optional[Dict]) -> str:
        """Format conversation into memory content"""
        
        # Summarize key points
        memory_content = f"Conversation memory: User said '{user_message[:100]}...', "
        memory_content += f"I responded with thoughts about {character_response[:100]}..."
        
        if emotional_context:
            emotions = emotional_context.get('emotions', {})
            if emotions:
                top_emotion = max(emotions.items(), key=lambda x: x[1])
                memory_content += f" I felt primarily {top_emotion[0]} during this exchange."
        
        return memory_content
    
    def extract_conversation_themes(self, conversation_content: str) -> List[str]:
        """Extract thematic elements from conversation"""
        
        # Simple keyword-based theme extraction
        # In production, this could use more sophisticated NLP
        
        theme_keywords = {
            'relationships': ['friend', 'love', 'family', 'relationship', 'partner'],
            'work': ['job', 'career', 'work', 'profession', 'business'],
            'personal_growth': ['learn', 'grow', 'develop', 'improve', 'change'],
            'emotions': ['feel', 'emotion', 'happy', 'sad', 'angry', 'afraid'],
            'goals': ['goal', 'dream', 'aspiration', 'plan', 'future'],
            'memories': ['remember', 'memory', 'past', 'childhood', 'before']
        }
        
        content_lower = conversation_content.lower()
        extracted_themes = []
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                extracted_themes.append(theme)
        
        return extracted_themes[:3]  # Limit to top 3 themes
    
    def _determine_formative_impact(self, emotional_weight: float) -> str:
        """Determine formative impact level based on emotional weight"""
        if emotional_weight >= 0.8:
            return 'high'
        elif emotional_weight >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _generate_reflection_content(self, recent_memories: List[PersonalMemory]) -> str:
        """Generate reflection content based on recent memories"""
        
        if not recent_memories:
            return "Reflection: A quiet day with time to think about my journey and growth."
        
        # Summarize recent experiences
        memory_themes = []
        for memory in recent_memories:
            memory_themes.extend(memory.themes)
        
        # Count theme frequency
        theme_counts = {}
        for theme in memory_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Generate reflection based on dominant themes
        if theme_counts:
            dominant_theme = max(theme_counts.items(), key=lambda x: x[1])[0]
            reflection = f"Reflection: Today I've been thinking a lot about {dominant_theme}. "
            reflection += "The conversations and experiences around this topic have made me realize "
            reflection += "how much it shapes my perspective and responses."
        else:
            reflection = "Reflection: Today brought new experiences that added to my understanding of myself and others."
        
        return reflection
    
    def _extract_reflection_themes(self, recent_memories: List[PersonalMemory]) -> List[str]:
        """Extract themes for reflection from recent memories"""
        
        all_themes = []
        for memory in recent_memories:
            all_themes.extend(memory.themes)
        
        # Count and return most frequent themes
        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Sort by frequency and return top themes
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes[:3]] + ['reflection', 'self-awareness']
    
    def _get_dominant_themes(self, memories: List[PersonalMemory]) -> List[str]:
        """Get dominant themes from a set of memories"""
        
        theme_counts = {}
        for memory in memories:
            for theme in memory.themes:
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Return top 3 themes
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes[:3]]
    
    def _calculate_development_level(self, stats: Dict[str, Any]) -> str:
        """Calculate character development level based on memory statistics"""
        
        total_memories = stats.get('total_memories', 0)
        avg_weight = stats.get('average_emotional_weight', 0.0)
        
        if total_memories >= 50 and avg_weight >= 0.6:
            return 'advanced'
        elif total_memories >= 20 and avg_weight >= 0.4:
            return 'intermediate'
        elif total_memories >= 5:
            return 'developing'
        else:
            return 'basic'


class CharacterMemoryContextProvider:
    """
    Provides character memory context for prompt engineering workflows.
    
    This class integrates with the existing prompt engineering system to
    inject character memories at appropriate points in conversations.
    """
    
    def __init__(self, integrator: CharacterMemoryIntegrator):
        self.integrator = integrator
        self.logger = logging.getLogger(__name__)
    
    async def get_system_prompt_addition(self, conversation_themes: Optional[List[str]] = None) -> str:
        """
        Get character memory content for system prompt enhancement.
        
        This adds character memories to the system prompt to maintain
        character consistency and depth throughout conversations.
        """
        try:
            context = self.integrator.get_character_memory_context(conversation_themes)
            
            if not context['formatted_memories']:
                return ""
            
            prompt_addition = f"""
## Character Memory Context

You are {self.integrator.character.identity.name}, and the following are your personal memories that influence your responses:

{context['formatted_memories']}

**Character Development**: Your memory system contains {context['total_memories']} memories with {context['character_development_level']} development level.

**Current Focus**: Based on recent experiences, you are particularly mindful of: {', '.join(context['dominant_themes'])}

Remember to draw from these personal experiences naturally in your responses, showing growth and consistency with your established character.
"""
            
            return prompt_addition
            
        except (ValueError, TypeError) as e:
            self.logger.error("Failed to get system prompt addition: %s", e)
            return ""
    
    async def get_response_context_hints(self, user_message: str) -> Dict[str, Any]:
        """
        Get context hints for character response generation.
        
        Returns structured data that can guide response generation
        based on character memories and personality.
        """
        try:
            # Extract themes from user message  
            themes = self.integrator.extract_conversation_themes(user_message)
            
            # Get relevant memories
            memories = await self.integrator.get_relevant_memories_for_conversation(
                themes
            )
            
            # Analyze emotional context from memories
            avg_emotional_weight = sum(m.emotional_weight for m in memories) / len(memories) if memories else 0.0
            
            return {
                'relevant_memories': memories,
                'suggested_emotional_tone': self._suggest_emotional_tone(avg_emotional_weight),
                'personality_reminders': self._get_personality_reminders(memories),
                'conversation_themes': themes,
                'memory_influenced_response': len(memories) > 0
            }
            
        except (ValueError, TypeError) as e:
            self.logger.error("Failed to get response context hints: %s", e)
            return {
                'relevant_memories': [],
                'suggested_emotional_tone': 'neutral',
                'personality_reminders': [],
                'conversation_themes': [],
                'memory_influenced_response': False
            }
    
    def _suggest_emotional_tone(self, avg_emotional_weight: float) -> str:
        """Suggest emotional tone based on memory emotional weight"""
        
        if avg_emotional_weight >= 0.8:
            return 'deeply_emotional'
        elif avg_emotional_weight >= 0.6:
            return 'emotionally_engaged'
        elif avg_emotional_weight >= 0.4:
            return 'thoughtful'
        elif avg_emotional_weight >= 0.2:
            return 'casual'
        else:
            return 'neutral'
    
    def _get_personality_reminders(self, memories: List[PersonalMemory]) -> List[str]:
        """Get personality reminders based on relevant memories"""
        
        reminders = []
        
        # Extract personality-relevant themes
        personality_themes = []
        for memory in memories:
            personality_themes.extend([
                theme for theme in memory.themes 
                if theme in ['personality', 'identity', 'relationships', 'emotional']
            ])
        
        # Generate reminders based on character personality and memories
        if 'relationships' in personality_themes:
            reminders.append("Consider how your past relationships influence your perspective")
        
        if 'emotional' in personality_themes:
            reminders.append("Your emotional experiences shape your empathy and responses")
        
        if 'identity' in personality_themes:
            reminders.append("Stay true to your core identity and values")
        
        return reminders