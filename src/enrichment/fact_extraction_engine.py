"""
Fact Extraction Engine for Async Enrichment Worker

This module provides conversation-level fact extraction with:
- Multi-message context analysis (vs. single message inline extraction)
- Conflict detection and resolution
- Knowledge graph relationship building
- Temporal fact evolution tracking
- Holistic fact organization and classification

Key advantages over inline extraction:
1. Conversation context: Analyzes 5-10 message windows for confirmation patterns
2. Higher confidence: Multi-message validation increases accuracy
3. Better quality: Can use Claude 3.5 Sonnet (not time-critical)
4. Conflict detection: Identifies contradictory facts and resolves them
5. Graph building: Creates semantic relationships between facts
6. No blocking: Runs in background, zero user-facing latency
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractedFact:
    """Structured fact with metadata"""
    entity_name: str
    entity_type: str  # food, drink, hobby, place, pet, skill, goal, etc.
    relationship_type: str  # likes, dislikes, owns, does, visited, etc.
    confidence: float
    confirmation_count: int = 1  # How many times confirmed in conversation
    related_facts: List[str] = None
    temporal_context: str = None  # "recent", "long-term", "past", etc.
    reasoning: str = None
    source_messages: List[str] = None  # Message IDs that support this fact
    
    def __post_init__(self):
        if self.related_facts is None:
            self.related_facts = []
        if self.source_messages is None:
            self.source_messages = []


@dataclass
class FactConflict:
    """Detected conflict between facts"""
    fact1: ExtractedFact
    fact2: ExtractedFact
    conflict_type: str  # "direct_contradiction", "preference_change", "temporal_conflict"
    resolution: str  # How to resolve: "keep_recent", "merge", "flag_for_review"
    reasoning: str


class FactExtractionEngine:
    """
    Conversation-level fact extraction with conflict detection and graph building.
    
    This engine provides SUPERIOR fact extraction compared to inline extraction:
    - Analyzes conversation windows (5-10 messages) instead of single messages
    - Detects confirmation patterns across messages
    - Identifies and resolves conflicting facts
    - Builds knowledge graph relationships
    - Tracks temporal fact evolution
    """
    
    def __init__(self, llm_client, model: str = "anthropic/claude-3.5-sonnet"):
        """
        Initialize fact extraction engine
        
        Args:
            llm_client: LLM client for fact extraction
            model: Model to use (default: Claude 3.5 Sonnet for quality)
        """
        self.llm_client = llm_client
        self.model = model
        
    async def extract_facts_from_conversation_window(
        self,
        messages: List[Dict],
        user_id: str,
        bot_name: str
    ) -> List[ExtractedFact]:
        """
        Extract facts from conversation window with multi-message context.
        
        This provides SUPERIOR quality compared to single-message extraction:
        - Confirmation patterns: "I love pizza" + "pepperoni is my favorite" = high confidence
        - Context understanding: Follow-up clarifications improve accuracy
        - Related facts: Links "loves pizza" → "makes dough" → "cooking skills"
        
        Args:
            messages: List of message dicts with content, timestamp, memory_type
            user_id: User ID
            bot_name: Bot name
            
        Returns:
            List of extracted facts with metadata
        """
        if not messages:
            return []
        
        # Build conversation context from window
        conversation_text = self._format_conversation_window(messages)
        
        # Build extraction prompt
        extraction_prompt = f"""Analyze this conversation and extract clear, confirmed personal facts about the user.

Conversation:
{conversation_text}

Instructions:
- Look for facts CONFIRMED across multiple messages (higher confidence)
- Link related facts together (e.g., "loves pizza" + "makes dough" = "cooking skills")
- Note temporal patterns (e.g., preferences that emerged recently vs. long-term)
- Extract: preferences, skills, possessions, relationships, goals, experiences
- Higher confidence for facts mentioned multiple times or with follow-up clarification
- Detect meta-facts: If user mentions "hiking every weekend" + "trail running" → "outdoor lifestyle"

Return JSON:
{{
    "facts": [
        {{
            "entity_name": "pizza",
            "entity_type": "food",
            "relationship_type": "loves",
            "confidence": 0.95,
            "confirmation_count": 3,
            "related_facts": ["makes homemade pizza", "baking skills"],
            "temporal_context": "long-term preference, mentioned across conversations",
            "reasoning": "User mentioned loving pizza, specified pepperoni, and revealed making own dough - high confidence"
        }}
    ]
}}

Valid entity_types: food, drink, hobby, place, pet, skill, goal, occupation, relationship, experience, possession, other
Valid relationship_types:
- Preferences: likes, loves, dislikes, hates, prefers, enjoys
- Possessions: owns, has, bought, sold, lost
- Actions: does, practices, plays, visited, traveled_to, went_to
- Skills: good_at, excels_at, learning, skilled_in
- Aspirations: wants, needs, plans_to, hopes_to, dreams_of
- Experiences: tried, learned, studied, worked_at, lived_in
- Relationships: knows, friends_with, family_of, works_with
"""
        
        try:
            # Call LLM for fact extraction
            result = await self._call_llm(extraction_prompt)
            
            # Parse and structure results
            facts = self._parse_fact_extraction_result(result, messages)
            
            logger.info(
                "Extracted %s facts from %s-message conversation window for user %s",
                len(facts), len(messages), user_id
            )
            
            return facts
            
        except Exception as e:
            logger.error("Fact extraction failed for user %s: %s", user_id, e)
            return []
    
    async def detect_fact_conflicts(
        self,
        new_facts: List[ExtractedFact],
        existing_facts: List[Dict]
    ) -> List[FactConflict]:
        """
        Detect conflicts between new facts and existing facts.
        
        Conflict types:
        1. Direct contradiction: "loves pizza" vs "hates pizza"
        2. Preference change: "lived in NYC" (2023) vs "lives in LA" (2024)
        3. Temporal conflict: "owns dog" vs "sold dog"
        
        Args:
            new_facts: Newly extracted facts
            existing_facts: Facts already in database
            
        Returns:
            List of detected conflicts with resolution strategies
        """
        conflicts = []
        
        for new_fact in new_facts:
            for existing in existing_facts:
                # Check for conflicts on same entity
                if new_fact.entity_name.lower() == existing.get('entity_name', '').lower():
                    conflict = self._analyze_potential_conflict(new_fact, existing)
                    if conflict:
                        conflicts.append(conflict)
        
        logger.info("Detected %s fact conflicts", len(conflicts))
        return conflicts
    
    async def resolve_fact_conflicts(
        self,
        conflicts: List[FactConflict]
    ) -> List[Dict]:
        """
        Resolve fact conflicts using intelligent strategies.
        
        Resolution strategies:
        1. Temporal: Keep most recent for time-sensitive facts (location, ownership)
        2. Preference evolution: Track changes over time (used to hate X, now loves X)
        3. Merge: Combine compatible facts (loves pizza + loves Italian food)
        4. Flag: Mark contradictions for manual review if unclear
        
        Returns:
            List of resolution actions to apply
        """
        resolutions = []
        
        for conflict in conflicts:
            resolution_action = None
            
            if conflict.resolution == "keep_recent":
                # Temporal conflict - keep newer fact, archive older
                resolution_action = {
                    'action': 'update',
                    'fact_to_keep': conflict.fact2,  # Assuming fact2 is newer
                    'fact_to_archive': conflict.fact1,
                    'reasoning': conflict.reasoning
                }
            
            elif conflict.resolution == "merge":
                # Compatible facts - merge into richer fact
                resolution_action = {
                    'action': 'merge',
                    'facts': [conflict.fact1, conflict.fact2],
                    'reasoning': conflict.reasoning
                }
            
            elif conflict.resolution == "flag_for_review":
                # Unclear conflict - flag for manual review
                resolution_action = {
                    'action': 'flag',
                    'conflict': conflict,
                    'reasoning': conflict.reasoning
                }
            
            if resolution_action:
                resolutions.append(resolution_action)
        
        return resolutions
    
    async def build_knowledge_graph_relationships(
        self,
        facts: List[ExtractedFact],
        user_id: str,
        bot_name: str
    ) -> List[Dict]:
        """
        Build knowledge graph relationships between facts.
        
        Relationship types:
        1. Semantic: "loves pizza" → "Italian food preference"
        2. Temporal: "started hiking" → "moved to Colorado" (motivated move)
        3. Causal: "has cooking skills" ← "makes homemade pizza"
        4. Hierarchical: "plays guitar" → "musical skills" → "artistic interests"
        
        This enables:
        - Richer fact queries: "What outdoor activities does user enjoy?"
        - Pattern detection: User has multiple "outdoor" interests
        - Inference: If loves hiking + camping + biking → "outdoor lifestyle"
        
        Args:
            facts: Extracted facts
            user_id: User ID
            bot_name: Bot name
            
        Returns:
            List of relationship edges for knowledge graph
        """
        relationships = []
        
        # Build semantic relationships
        for i, fact1 in enumerate(facts):
            for fact2 in facts[i+1:]:
                relationship = self._identify_relationship(fact1, fact2)
                if relationship:
                    relationships.append({
                        'source_fact': fact1,
                        'target_fact': fact2,
                        'relationship_type': relationship['type'],
                        'confidence': relationship['confidence'],
                        'reasoning': relationship['reasoning']
                    })
        
        # Build hierarchical classifications
        for fact in facts:
            category = self._classify_fact_category(fact)
            if category:
                relationships.append({
                    'fact': fact,
                    'category': category,
                    'relationship_type': 'belongs_to_category',
                    'confidence': 0.9
                })
        
        logger.info(
            "Built %s knowledge graph relationships for %s facts",
            len(relationships), len(facts)
        )
        
        return relationships
    
    async def organize_and_classify_facts(
        self,
        facts: List[ExtractedFact]
    ) -> Dict[str, List[ExtractedFact]]:
        """
        Organize facts into structured categories for better retrieval.
        
        Categories:
        - Personal preferences (foods, drinks, hobbies)
        - Skills and abilities
        - Possessions and ownership
        - Relationships and connections
        - Goals and aspirations
        - Experiences and history
        - Lifestyle and habits
        
        This enables:
        - Efficient fact queries by category
        - Pattern detection within categories
        - Holistic user profiling
        
        Returns:
            Dictionary of categorized facts
        """
        organized = {
            'preferences': [],
            'skills': [],
            'possessions': [],
            'relationships': [],
            'goals': [],
            'experiences': [],
            'lifestyle': []
        }
        
        for fact in facts:
            # Classify into primary category
            if fact.relationship_type in ['likes', 'loves', 'dislikes', 'hates', 'prefers', 'enjoys']:
                organized['preferences'].append(fact)
            elif fact.relationship_type in ['good_at', 'excels_at', 'skilled_in', 'learning']:
                organized['skills'].append(fact)
            elif fact.relationship_type in ['owns', 'has', 'bought']:
                organized['possessions'].append(fact)
            elif fact.relationship_type in ['knows', 'friends_with', 'family_of', 'works_with']:
                organized['relationships'].append(fact)
            elif fact.relationship_type in ['wants', 'needs', 'plans_to', 'hopes_to', 'dreams_of']:
                organized['goals'].append(fact)
            elif fact.relationship_type in ['tried', 'learned', 'studied', 'worked_at', 'lived_in']:
                organized['experiences'].append(fact)
            elif fact.relationship_type in ['does', 'practices', 'plays']:
                organized['lifestyle'].append(fact)
        
        return organized
    
    # Helper methods
    
    def _format_conversation_window(self, messages: List[Dict]) -> str:
        """Format messages into conversation context"""
        formatted = []
        for msg in messages:
            memory_type = msg.get('memory_type', '')
            content = msg.get('content', '')
            
            if memory_type == 'user_message':
                formatted.append(f"User: {content}")
            elif memory_type == 'bot_response':
                formatted.append(f"Bot: {content}")
        
        return "\n".join(formatted)
    
    async def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call LLM for fact extraction"""
        try:
            # Use better model for enrichment (not time-critical)
            response = await asyncio.to_thread(
                self.llm_client.get_chat_response,
                [
                    {
                        "role": "system",
                        "content": "You are a precise fact extraction specialist. Extract clear, verifiable facts from conversations. Return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.2,  # Low temperature for consistency
                max_tokens=max_tokens
            )
            
            return response
            
        except Exception as e:
            logger.error("LLM call failed: %s", e)
            raise
    
    def _parse_fact_extraction_result(
        self,
        llm_response: str,
        messages: List[Dict]
    ) -> List[ExtractedFact]:
        """Parse LLM response into structured facts"""
        try:
            # Handle markdown code blocks
            if '```json' in llm_response:
                llm_response = llm_response.split('```json')[1].split('```')[0].strip()
            elif '```' in llm_response:
                llm_response = llm_response.split('```')[1].split('```')[0].strip()
            
            data = json.loads(llm_response)
            facts = []
            
            for fact_data in data.get('facts', []):
                fact = ExtractedFact(
                    entity_name=fact_data.get('entity_name', ''),
                    entity_type=fact_data.get('entity_type', 'other'),
                    relationship_type=fact_data.get('relationship_type', ''),
                    confidence=float(fact_data.get('confidence', 0.5)),
                    confirmation_count=int(fact_data.get('confirmation_count', 1)),
                    related_facts=fact_data.get('related_facts', []),
                    temporal_context=fact_data.get('temporal_context'),
                    reasoning=fact_data.get('reasoning'),
                    source_messages=[msg.get('id') for msg in messages if msg.get('id')]
                )
                facts.append(fact)
            
            return facts
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse fact extraction result: %s", e)
            return []
    
    def _analyze_potential_conflict(
        self,
        new_fact: ExtractedFact,
        existing_fact: Dict
    ) -> Optional[FactConflict]:
        """Analyze if two facts conflict"""
        # Direct contradiction: opposite relationships
        opposite_relationships = {
            'likes': 'dislikes',
            'loves': 'hates',
            'owns': 'sold',
            'has': 'lost'
        }
        
        new_rel = new_fact.relationship_type
        existing_rel = existing_fact.get('relationship_type', '')
        
        if opposite_relationships.get(new_rel) == existing_rel or \
           opposite_relationships.get(existing_rel) == new_rel:
            return FactConflict(
                fact1=new_fact,
                fact2=existing_fact,
                conflict_type="direct_contradiction",
                resolution="keep_recent",
                reasoning=f"Direct contradiction: {new_rel} vs {existing_rel} - keeping more recent"
            )
        
        # Temporal conflict: Same relationship but might be outdated
        if new_rel == existing_rel and new_fact.temporal_context == "recent":
            return FactConflict(
                fact1=new_fact,
                fact2=existing_fact,
                conflict_type="preference_change",
                resolution="keep_recent",
                reasoning="Preference may have evolved - keeping recent fact"
            )
        
        return None
    
    def _identify_relationship(
        self,
        fact1: ExtractedFact,
        fact2: ExtractedFact
    ) -> Optional[Dict]:
        """Identify semantic relationship between two facts"""
        # Example: "loves pizza" + "makes homemade pizza" → causal relationship
        if fact1.entity_name.lower() in fact2.entity_name.lower() or \
           fact2.entity_name.lower() in fact1.entity_name.lower():
            return {
                'type': 'semantic_link',
                'confidence': 0.8,
                'reasoning': f"Related entities: {fact1.entity_name} and {fact2.entity_name}"
            }
        
        # Example: "hiking" + "camping" + "biking" → lifestyle category
        outdoor_activities = ['hiking', 'camping', 'biking', 'climbing', 'trail running']
        if fact1.entity_name.lower() in outdoor_activities and \
           fact2.entity_name.lower() in outdoor_activities:
            return {
                'type': 'lifestyle_pattern',
                'confidence': 0.9,
                'reasoning': "Both are outdoor activities - suggests outdoor lifestyle"
            }
        
        return None
    
    def _classify_fact_category(self, fact: ExtractedFact) -> Optional[str]:
        """Classify fact into hierarchical category"""
        # Food preferences
        food_types = ['food', 'drink', 'cuisine', 'meal']
        if fact.entity_type in food_types:
            return 'culinary_preferences'
        
        # Outdoor activities
        outdoor_activities = ['hiking', 'camping', 'biking', 'climbing', 'trail running', 'skiing']
        if fact.entity_name.lower() in outdoor_activities:
            return 'outdoor_lifestyle'
        
        # Creative skills
        creative_skills = ['music', 'art', 'writing', 'photography', 'painting', 'drawing']
        if fact.entity_type == 'skill' and any(s in fact.entity_name.lower() for s in creative_skills):
            return 'creative_arts'
        
        return None
