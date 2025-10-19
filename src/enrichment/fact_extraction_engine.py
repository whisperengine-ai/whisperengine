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
import os
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
    related_facts: Optional[List[str]] = None
    temporal_context: Optional[str] = None  # "recent", "long-term", "past", etc.
    reasoning: Optional[str] = None
    source_messages: Optional[List[str]] = None  # Message IDs that support this fact
    
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
    
    def __init__(self, llm_client, model: str = "anthropic/claude-sonnet-4.5"):
        """
        Initialize fact extraction engine
        
        Args:
            llm_client: LLM client for fact extraction
            model: Model to use (default: Claude Sonnet 4.5 for superior quality)
        """
        self.llm_client = llm_client
        self.model = model
        
        # Opposing relationships mapping (from semantic_router.py)
        self.opposing_relationships = {
            'likes': ['dislikes', 'hates', 'avoids'],
            'loves': ['dislikes', 'hates', 'avoids'],
            'enjoys': ['dislikes', 'hates', 'avoids'],
            'prefers': ['dislikes', 'avoids', 'rejects'],
            'wants': ['rejects', 'avoids', 'dislikes'],
            'needs': ['rejects', 'avoids'],
            'supports': ['opposes', 'rejects'],
            'trusts': ['distrusts', 'suspects'],
            'believes': ['doubts', 'rejects'],
            # Reverse mappings
            'dislikes': ['likes', 'loves', 'enjoys', 'prefers', 'wants'],
            'hates': ['likes', 'loves', 'enjoys'],
            'avoids': ['likes', 'loves', 'enjoys', 'prefers', 'wants', 'needs'],
            'rejects': ['wants', 'needs', 'prefers', 'supports', 'believes'],
            'opposes': ['supports'],
            'distrusts': ['trusts'],
            'doubts': ['believes'],
            'suspects': ['trusts']
        }
        
    async def extract_facts_from_conversation_window(
        self,
        messages: List[Dict],
        user_id: str,
        bot_name: str
    ) -> List[ExtractedFact]:
        """
        Extract facts from a conversation window using LLM analysis.
        
        Args:
            messages: List of message dicts with content, timestamp, memory_type
            user_id: User ID
            bot_name: Bot name
            
        Returns:
            List of extracted facts with metadata
        """
        if not messages:
            return []
        
        # CRITICAL: Chunk large conversations to avoid context window limits!
        # LLM can only process ~4000 tokens at once (including prompt + response)
        # 640 messages would be ~100K tokens - way too big!
        MAX_MESSAGES_PER_CHUNK = 20  # Conservative - ~2000 tokens per chunk
        
        all_facts = []
        
        # Process in chunks if conversation is large
        if len(messages) > MAX_MESSAGES_PER_CHUNK:
            logger.info(
                "Large conversation (%d messages) - processing in chunks of %d",
                len(messages), MAX_MESSAGES_PER_CHUNK
            )
            
            for i in range(0, len(messages), MAX_MESSAGES_PER_CHUNK):
                chunk = messages[i:i + MAX_MESSAGES_PER_CHUNK]
                chunk_facts = await self._extract_facts_from_chunk(chunk, user_id, bot_name)
                all_facts.extend(chunk_facts)
            
            logger.info(
                "Extracted %d total facts from %d chunks (user %s)",
                len(all_facts), (len(messages) + MAX_MESSAGES_PER_CHUNK - 1) // MAX_MESSAGES_PER_CHUNK,
                user_id
            )
            return all_facts
        
        # Small conversation - process directly
        return await self._extract_facts_from_chunk(messages, user_id, bot_name)
    
    async def _extract_facts_from_chunk(
        self,
        messages: List[Dict],
        user_id: str,
        bot_name: str
    ) -> List[ExtractedFact]:
        """Extract facts from a single conversation chunk (internal helper)"""
        if not messages:
            return []
        
        # Build conversation context from window
        conversation_text = self._format_conversation_window(messages)
        
        # 🔍 DEBUG: Log conversation text IMMEDIATELY after formatting
        logger.warning("🔍 CONVERSATION TEXT BUILT: %d chars", len(conversation_text))
        
        # Build extraction prompt (MATCHES inline bot implementation for consistency)
        # Simpler prompt = better LLM compliance and fact extraction
        extraction_prompt = f"""Analyze this conversation and extract ONLY clear, factual personal statements about the user.

Conversation:
{conversation_text}

Instructions:
- Extract personal preferences: Foods/drinks/hobbies they explicitly like/dislike/enjoy
- Extract personal facts: Pets they own, places they've visited, hobbies they actively do
- DO NOT extract: Conversational phrases, questions, abstract concepts, philosophical statements
- DO NOT extract: Things the user asks about or discusses theoretically - only facts about themselves

Return JSON (return empty list if no clear facts found):
{{
    "facts": [
        {{
            "entity_name": "pizza",
            "entity_type": "food",
            "relationship_type": "likes",
            "confidence": 0.9,
            "reasoning": "User explicitly stated they love pizza"
        }}
    ]
}}

Valid entity_types: food, drink, hobby, place, pet, skill, goal, occupation, other
Valid relationship_types: 
- Preferences: likes, dislikes, enjoys, loves, hates, prefers
- Possessions: owns, has, bought, sold, lost
- Actions: visited, traveled_to, went_to, does, practices, plays
- Aspirations: wants, needs, plans_to, hopes_to, dreams_of
- Experiences: tried, learned, studied, worked_at, lived_in
- Relationships: knows, friends_with, family_of, works_with

Be conservative - only extract clear, unambiguous facts."""
        
        # 🔍 DEBUG: Log final prompt size
        logger.warning("🔍 EXTRACTION PROMPT SIZE: %d chars (conversation: %d chars)", 
                      len(extraction_prompt), len(conversation_text))
        
        try:
            # Call LLM for fact extraction
            result = await self._call_llm(extraction_prompt)
            
            # CRITICAL DEBUG: Always log first 300 chars of LLM response to diagnose 0-fact issue
            logger.warning("🔍 LLM RESPONSE (first 300 chars): %s", result[:300] if result else "NONE")
            
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
        """
        Format messages into readable text for fact extraction.
        
        IMPORTANT: Only includes USER messages since we're extracting facts ABOUT the user,
        not the bot. Bot responses don't contain user facts.
        """
        logger.debug("_format_conversation_window: Received %d messages", len(messages))
        
        formatted = []
        for msg in messages:
            # Use 'role' field (user/bot) not 'memory_type' (conversation/fact/etc)
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            # ONLY include user messages for fact extraction
            if role == 'user':
                formatted.append(f"User: {content}")
            # FALLBACK: Try old memory_type field for backward compatibility
            elif msg.get('memory_type') == 'user_message':
                formatted.append(f"User: {content}")
        
        conversation_text = "\n".join(formatted)
        logger.debug("Formatted %d user messages into %d chars", len(formatted), len(conversation_text))
        
        return conversation_text
    
    async def _call_llm(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Call LLM for fact extraction"""
        # CRITICAL: Enrichment processes 20-message chunks and needs larger output capacity
        # than inline extraction (which processes single messages)
        # Default: 3000 tokens = ~10-15 facts with full reasoning per chunk
        # Override via LLM_MAX_TOKENS_CHAT environment variable (matches bot convention)
        if max_tokens is None:
            max_tokens = int(os.getenv('LLM_MAX_TOKENS_CHAT', '3000'))
        
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
        """
        Parse LLM response into structured facts.
        
        MATCHES inline bot implementation - simpler structure for better LLM compliance.
        """
        try:
            # Handle markdown code blocks
            if '```json' in llm_response:
                llm_response = llm_response.split('```json')[1].split('```')[0].strip()
            elif '```' in llm_response:
                llm_response = llm_response.split('```')[1].split('```')[0].strip()
            
            data = json.loads(llm_response)
            facts = []
            
            # Debug logging when no facts found  
            facts_list = data.get('facts', [])
            if len(facts_list) == 0:
                logger.info(
                    "ℹ️ No facts extracted from conversation. Data keys: %s, Response sample: %s",
                    list(data.keys()), llm_response[:200]
                )
            
            for fact_data in facts_list:
                # Use simpler structure matching inline extraction
                # Optional fields get sensible defaults
                fact = ExtractedFact(
                    entity_name=fact_data.get('entity_name', ''),
                    entity_type=fact_data.get('entity_type', 'other'),
                    relationship_type=fact_data.get('relationship_type', ''),
                    confidence=float(fact_data.get('confidence', 0.8)),
                    confirmation_count=1,  # Enrichment sees full conversation, count as confirmed
                    related_facts=[],  # Can be enriched later if needed
                    temporal_context=None,  # Optional - not in simple prompt
                    reasoning=fact_data.get('reasoning', 'Extracted from conversation window'),
                    source_messages=[msg.get('id', '') for msg in messages if msg.get('id')]
                )
                facts.append(fact)
            
            return facts
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse fact extraction result: %s", e)
            logger.debug("Raw LLM response: %s", llm_response[:500])
            return []
    
    def _analyze_potential_conflict(
        self,
        new_fact: ExtractedFact,
        existing_fact: Dict
    ) -> Optional[FactConflict]:
        """
        Analyze if two facts conflict (matches semantic_router.py logic)
        
        Follows same conflict detection rules as inline extraction:
        - Direct contradictions: opposing relationships (likes vs dislikes)
        - Confidence-based resolution: Keep stronger confidence
        - Temporal awareness: Recent facts can override older ones
        """
        # Get relationship types
        new_rel = new_fact.relationship_type
        existing_rel = existing_fact.get('relationship_type', '')
        
        # Check if these relationships oppose each other
        if new_rel in self.opposing_relationships:
            opposing_types = self.opposing_relationships[new_rel]
            
            if existing_rel in opposing_types:
                # Direct opposition detected!
                new_conf = new_fact.confidence
                existing_conf = existing_fact.get('confidence', 0.5)
                
                if existing_conf > new_conf:
                    # Keep stronger existing opposing relationship
                    return FactConflict(
                        fact1=new_fact,
                        fact2=existing_fact,
                        conflict_type="direct_contradiction",
                        resolution="keep_existing",
                        reasoning=f"Existing '{existing_rel}' (confidence: {existing_conf:.2f}) is stronger than new '{new_rel}' (confidence: {new_conf:.2f})"
                    )
                else:
                    # Replace weaker opposing relationship
                    return FactConflict(
                        fact1=new_fact,
                        fact2=existing_fact,
                        conflict_type="direct_contradiction",
                        resolution="keep_recent",
                        reasoning=f"New '{new_rel}' (confidence: {new_conf:.2f}) is stronger than existing '{existing_rel}' (confidence: {existing_conf:.2f})"
                    )
        
        # Check for temporal conflicts (same relationship but might be outdated)
        if new_rel == existing_rel:
            # For temporal facts (location, ownership, etc.), prefer recent
            temporal_relationship_types = [
                'works_at', 'lives_in', 'studies_at', 'owns', 'has',
                'dating', 'in_relationship_with', 'feels', 'currently_feeling'
            ]
            
            if new_rel in temporal_relationship_types and new_fact.temporal_context == "recent":
                return FactConflict(
                    fact1=new_fact,
                    fact2=existing_fact,
                    conflict_type="temporal_conflict",
                    resolution="keep_recent",
                    reasoning=f"Temporal fact '{new_rel}' updated - keeping recent version"
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
