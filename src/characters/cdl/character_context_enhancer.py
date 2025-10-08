"""
Character Context Enhancer - Proactive Context Injection

Detects topics in user messages and proactively injects relevant character 
knowledge into system prompts for natural, contextually-aware responses.

STEP 5 Implementation: CDL Graph Intelligence Roadmap
"""

import logging
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

logger = logging.getLogger(__name__)


class TopicRelevance(Enum):
    """Relevance levels for topic matching"""
    HIGH = "high"          # Direct expertise match (0.8-1.0)
    MEDIUM = "medium"      # Related experience (0.5-0.8)
    LOW = "low"           # Tangential connection (0.2-0.5)
    NONE = "none"         # No connection (0.0-0.2)


@dataclass
class ContextInjectionResult:
    """Result of context injection analysis"""
    detected_topics: List[str]
    relevant_background: List[Dict]
    relevant_abilities: List[Dict]
    relevant_memories: List[Dict]
    injection_score: float
    enhanced_prompt: str
    debug_info: Dict


class CharacterContextEnhancer:
    """
    Detects topics in user messages and proactively injects relevant 
    character knowledge into system prompts.
    
    Key Features:
    - Topic detection from user messages
    - Relevance scoring for character knowledge
    - Automatic system prompt enhancement
    - Character-agnostic design via CDL database
    """
    
    def __init__(self, character_graph_manager, postgres_pool=None):
        """
        Initialize character context enhancer.
        
        Args:
            character_graph_manager: CharacterGraphManager instance
            postgres_pool: Optional AsyncPG connection pool
        """
        self.character_graph_manager = character_graph_manager
        self.postgres = postgres_pool
        
        # Topic detection patterns
        self._topic_patterns = self._build_topic_patterns()
        
        logger.info("🎯 CharacterContextEnhancer initialized for proactive context injection")
    
    def _build_topic_patterns(self) -> Dict[str, List[str]]:
        """Build topic detection patterns for common subjects"""
        return {
            # Professional/Career topics
            "marine_biology": [
                "ocean", "marine", "coral", "reef", "fish", "diving", "underwater",
                "sea", "scuba", "research", "aquatic", "biology", "ecosystem",
                "conservation", "marine life", "oceanography"
            ],
            "photography": [
                "photo", "photography", "camera", "lens", "shot", "capture", 
                "image", "picture", "landscape", "portrait", "composition",
                "lighting", "exposure", "aperture", "iso"
            ],
            "ai_research": [
                "ai", "artificial intelligence", "machine learning", "deep learning",
                "neural network", "algorithm", "model", "training", "data science",
                "ethics", "alignment", "safety", "automation"
            ],
            "game_development": [
                "game", "gaming", "development", "programming", "indie", "unity",
                "unreal", "coding", "software", "design", "pixel art", "mechanics"
            ],
            "marketing": [
                "marketing", "brand", "campaign", "social media", "advertising",
                "promotion", "strategy", "content", "audience", "engagement"
            ],
            
            # Personal/Lifestyle topics
            "travel": [
                "travel", "trip", "vacation", "adventure", "explore", "journey",
                "destination", "flight", "hotel", "culture", "country"
            ],
            "food": [
                "food", "cooking", "recipe", "restaurant", "cuisine", "meal",
                "dinner", "lunch", "breakfast", "taste", "flavor", "chef"
            ],
            "fitness": [
                "fitness", "workout", "exercise", "gym", "running", "yoga",
                "health", "training", "muscle", "cardio", "strength"
            ],
            "music": [
                "music", "song", "band", "artist", "album", "concert", "guitar",
                "piano", "singing", "melody", "rhythm", "genre"
            ],
            "books": [
                "book", "reading", "novel", "author", "story", "literature",
                "fiction", "non-fiction", "chapter", "library", "kindle"
            ],
            
            # Technical topics
            "technology": [
                "tech", "technology", "computer", "software", "hardware", "app",
                "internet", "digital", "device", "innovation", "startup"
            ],
            "science": [
                "science", "research", "experiment", "discovery", "theory",
                "hypothesis", "data", "analysis", "study", "scientific"
            ],
            "education": [
                "education", "school", "university", "college", "learning",
                "study", "student", "teacher", "class", "degree", "academic"
            ]
        }
    
    async def detect_and_inject_context(
        self,
        user_message: str,
        character_name: str,
        base_system_prompt: str,
        relevance_threshold: float = 0.5
    ) -> ContextInjectionResult:
        """
        Detect topics in user message and inject relevant character context.
        
        Process:
        1. Extract topics/entities from user message
        2. Query CharacterGraphManager for matching background/abilities
        3. Calculate relevance scores  
        4. Inject high-relevance context into system prompt
        
        Args:
            user_message: User's message content
            character_name: Character to enhance context for
            base_system_prompt: Original system prompt
            relevance_threshold: Minimum relevance score (0.0-1.0)
            
        Returns:
            ContextInjectionResult with enhanced prompt and metadata
        """
        try:
            # Step 1: Detect topics in user message
            detected_topics = self._detect_topics(user_message)
            
            if not detected_topics:
                return ContextInjectionResult(
                    detected_topics=[],
                    relevant_background=[],
                    relevant_abilities=[],
                    relevant_memories=[],
                    injection_score=0.0,
                    enhanced_prompt=base_system_prompt,
                    debug_info={"reason": "No topics detected"}
                )
            
            logger.info("🎯 CONTEXT INJECTION: Detected topics for %s: %s", 
                       character_name, detected_topics)
            
            # Step 2: Query character knowledge for each topic
            relevant_knowledge = await self._query_relevant_knowledge(
                character_name, detected_topics
            )
            
            # Step 3: Calculate relevance scores
            scored_knowledge = self._score_knowledge_relevance(
                relevant_knowledge, detected_topics
            )
            
            # Step 4: Filter by relevance threshold
            high_relevance = {
                'background': [k for k in scored_knowledge['background'] 
                              if k.get('relevance_score', 0.0) >= relevance_threshold],
                'abilities': [k for k in scored_knowledge['abilities'] 
                             if k.get('relevance_score', 0.0) >= relevance_threshold],
                'memories': [k for k in scored_knowledge['memories'] 
                            if k.get('relevance_score', 0.0) >= relevance_threshold]
            }
            
            # Step 5: Inject context into system prompt
            enhanced_prompt = self._inject_context_into_prompt(
                base_system_prompt, high_relevance, detected_topics
            )
            
            # Calculate overall injection score
            all_scores = []
            for category in high_relevance.values():
                all_scores.extend([k.get('relevance_score', 0.0) for k in category])
            
            injection_score = max(all_scores) if all_scores else 0.0
            
            logger.info("🎯 CONTEXT INJECTION: Enhanced prompt for %s with score %.2f",
                       character_name, injection_score)
            
            return ContextInjectionResult(
                detected_topics=detected_topics,
                relevant_background=high_relevance['background'],
                relevant_abilities=high_relevance['abilities'],
                relevant_memories=high_relevance['memories'],
                injection_score=injection_score,
                enhanced_prompt=enhanced_prompt,
                debug_info={
                    "topics_detected": len(detected_topics),
                    "background_injected": len(high_relevance['background']),
                    "abilities_injected": len(high_relevance['abilities']),
                    "memories_injected": len(high_relevance['memories'])
                }
            )
            
        except KeyError as e:
            logger.error("❌ Error in context injection for %s: %s", character_name, e)
            return ContextInjectionResult(
                detected_topics=[],
                relevant_background=[],
                relevant_abilities=[],
                relevant_memories=[],
                injection_score=0.0,
                enhanced_prompt=base_system_prompt,
                debug_info={"error": str(e)}
            )
    
    def _detect_topics(self, user_message: str) -> List[str]:
        """
        Detect topics in user message using keyword matching.
        
        Returns list of detected topic categories.
        """
        detected = []
        message_lower = user_message.lower()
        
        for topic_category, keywords in self._topic_patterns.items():
            # Check if any keywords match
            for keyword in keywords:
                if keyword in message_lower:
                    if topic_category not in detected:
                        detected.append(topic_category)
                    break  # Found match for this category
        
        return detected
    
    def detect_topics_public(self, user_message: str) -> List[str]:
        """
        Public method to detect topics in user message.
        
        Returns list of detected topic categories.
        """
        return self._detect_topics(user_message)
    
    async def _query_relevant_knowledge(
        self,
        character_name: str,
        topics: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Query CharacterGraphManager for knowledge relevant to detected topics.
        """
        if not self.character_graph_manager:
            return {"background": [], "abilities": [], "memories": []}
        
        try:
            # Query character knowledge with general intent
            from src.characters.cdl.character_graph_manager import CharacterKnowledgeIntent
            
            knowledge_result = await self.character_graph_manager.query_character_knowledge(
                character_name=character_name,
                intent=CharacterKnowledgeIntent.GENERAL,
                query_text=" ".join(topics),  # Combine topics as query
                limit=20,  # Get more results for relevance scoring
                user_id=None  # No user-specific context needed
            )
            
            return {
                "background": knowledge_result.background,
                "abilities": knowledge_result.abilities,
                "memories": knowledge_result.memories
            }
            
        except (KeyError, AttributeError) as e:
            logger.error("❌ Error querying character knowledge: %s", e)
            return {"background": [], "abilities": [], "memories": []}
    
    def _score_knowledge_relevance(
        self,
        knowledge: Dict[str, List[Dict]],
        detected_topics: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Score knowledge entries for relevance to detected topics.
        
        Returns knowledge with relevance_score added to each entry.
        """
        scored_knowledge = {"background": [], "abilities": [], "memories": []}
        
        for category, entries in knowledge.items():
            for entry in entries:
                score = self._calculate_relevance_score(entry, detected_topics)
                entry_with_score = {**entry, "relevance_score": score}
                scored_knowledge[category].append(entry_with_score)
        
        # Sort by relevance score (highest first)
        for category in scored_knowledge:
            scored_knowledge[category].sort(
                key=lambda x: x.get('relevance_score', 0.0), 
                reverse=True
            )
        
        return scored_knowledge
    
    def _calculate_relevance_score(
        self,
        knowledge_entry: Dict,
        detected_topics: List[str]
    ) -> float:
        """
        Calculate relevance score (0.0-1.0) for knowledge entry vs topics.
        """
        # Extract text content from knowledge entry
        text_fields = []
        for field in ['title', 'description', 'category', 'skill_name', 'proficiency_area']:
            if field in knowledge_entry and knowledge_entry[field]:
                text_fields.append(str(knowledge_entry[field]).lower())
        
        if not text_fields:
            return 0.0
        
        combined_text = " ".join(text_fields)
        
        # Score based on topic keyword matches
        max_score = 0.0
        
        for topic in detected_topics:
            topic_keywords = self._topic_patterns.get(topic, [])
            topic_score = 0.0
            keyword_matches = 0
            
            for keyword in topic_keywords:
                if keyword in combined_text:
                    keyword_matches += 1
            
            if keyword_matches > 0:
                # Base score from keyword density
                topic_score = min(1.0, keyword_matches / len(topic_keywords))
                
                # Boost for exact topic match
                if topic.replace("_", " ") in combined_text:
                    topic_score = min(1.0, topic_score + 0.3)
                
                # Boost for multiple keyword matches
                if keyword_matches >= 3:
                    topic_score = min(1.0, topic_score + 0.2)
            
            max_score = max(max_score, topic_score)
        
        return max_score
    
    def _inject_context_into_prompt(
        self,
        base_prompt: str,
        relevant_knowledge: Dict[str, List[Dict]],
        detected_topics: List[str]
    ) -> str:
        """
        Inject relevant character knowledge into system prompt.
        """
        if not any(relevant_knowledge.values()):
            return base_prompt
        
        # Build context injection sections
        injection_parts = []
        
        # Background context
        if relevant_knowledge['background']:
            background_text = self._format_background_context(
                relevant_knowledge['background'][:3]  # Top 3 most relevant
            )
            if background_text:
                injection_parts.append(f"RELEVANT BACKGROUND: {background_text}")
        
        # Abilities context
        if relevant_knowledge['abilities']:
            abilities_text = self._format_abilities_context(
                relevant_knowledge['abilities'][:2]  # Top 2 most relevant
            )
            if abilities_text:
                injection_parts.append(f"RELEVANT EXPERTISE: {abilities_text}")
        
        # Memories context (if any)
        if relevant_knowledge['memories']:
            memories_text = self._format_memories_context(
                relevant_knowledge['memories'][:2]  # Top 2 most relevant
            )
            if memories_text:
                injection_parts.append(f"RELEVANT EXPERIENCE: {memories_text}")
        
        if not injection_parts:
            return base_prompt
        
        # Inject context before character personality section
        context_injection = "\n\n" + "\n\n".join(injection_parts)
        context_injection += f"\n\n[Context auto-injected based on user topics: {', '.join(detected_topics)}]"
        
        # Insert after system prompt introduction but before personality
        enhanced_prompt = base_prompt + context_injection
        
        logger.info("🎯 CONTEXT INJECTION: Added %d context sections for topics: %s",
                   len(injection_parts), detected_topics)
        
        return enhanced_prompt
    
    def _format_background_context(self, background_entries: List[Dict]) -> str:
        """Format background entries for prompt injection"""
        if not background_entries:
            return ""
        
        formatted_parts = []
        for entry in background_entries:
            if entry.get('description'):
                formatted_parts.append(entry['description'])
        
        return " ".join(formatted_parts) if formatted_parts else ""
    
    def _format_abilities_context(self, abilities_entries: List[Dict]) -> str:
        """Format abilities entries for prompt injection"""
        if not abilities_entries:
            return ""
        
        formatted_parts = []
        for entry in abilities_entries:
            skill_name = entry.get('skill_name', '')
            proficiency = entry.get('proficiency_level', '')
            area = entry.get('proficiency_area', '')
            
            if skill_name:
                ability_text = skill_name
                if proficiency and area:
                    ability_text += f" ({proficiency} level in {area})"
                elif proficiency:
                    ability_text += f" ({proficiency} level)"
                
                formatted_parts.append(ability_text)
        
        return ", ".join(formatted_parts) if formatted_parts else ""
    
    def _format_memories_context(self, memories_entries: List[Dict]) -> str:
        """Format memories entries for prompt injection"""
        if not memories_entries:
            return ""
        
        formatted_parts = []
        for entry in memories_entries:
            if entry.get('description'):
                # Summarize memory for context (keep it concise)
                memory_desc = entry['description']
                if len(memory_desc) > 150:
                    memory_desc = memory_desc[:147] + "..."
                formatted_parts.append(memory_desc)
        
        return " ".join(formatted_parts) if formatted_parts else ""


def create_character_context_enhancer(character_graph_manager, postgres_pool=None) -> CharacterContextEnhancer:
    """
    Factory function to create CharacterContextEnhancer instance.
    
    Args:
        character_graph_manager: CharacterGraphManager instance
        postgres_pool: Optional AsyncPG connection pool
        
    Returns:
        CharacterContextEnhancer instance
    """
    return CharacterContextEnhancer(character_graph_manager, postgres_pool)