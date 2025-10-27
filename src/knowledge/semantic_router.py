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

# Import unified query classifier for intent analysis
from src.memory.unified_query_classification import (
    create_unified_query_classifier,
    UnifiedQueryClassifier,
    QueryIntent as UnifiedQueryIntent,
)

# Import spaCy for lemmatization
from src.nlp.spacy_manager import get_spacy_nlp

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
        
        # Use shared spaCy instance for entity extraction (optional - graceful fallback)
        from src.nlp.spacy_manager import get_spacy_nlp
        
        self.nlp = get_spacy_nlp()
        if self.nlp:
            logger.info("✅ SemanticKnowledgeRouter using shared spaCy instance for entity extraction")
        else:
            logger.warning("⚠️ SemanticKnowledgeRouter: spaCy unavailable (will use keyword patterns)")
        
        # Phase 2b: Initialize unified query classifier for intent analysis
        try:
            self._unified_query_classifier = create_unified_query_classifier()
            logger.info("✅ UNIFIED: SemanticKnowledgeRouter using UnifiedQueryClassifier for intent analysis")
        except Exception as e:
            logger.warning("⚠️  UNIFIED: Failed to initialize UnifiedQueryClassifier: %s", str(e))
            self._unified_query_classifier = None
        
        # Intent patterns for analysis (fallback if unified classifier unavailable)
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
    
    def _get_opposing_relationships(self) -> Dict[str, List[str]]:
        """
        Define opposing relationship mappings for conflict detection.
        
        Returns:
            Dictionary mapping relationship types to their opposing types
        """
        return {
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
    
    def _get_similar_relationship_groups(self) -> Dict[str, List[str]]:
        """
        Define similar/redundant relationship groupings for deduplication.
        When storing a fact, if similar relationships already exist for the same entity,
        keep the highest confidence one and discard duplicates.
        
        Returns:
            Dictionary mapping relationship types to groups of similar relationships
        """
        return {
            # Positive preferences - all are similar positive expressions
            'likes': ['likes', 'loves', 'enjoys', 'prefers'],
            'loves': ['likes', 'loves', 'enjoys', 'prefers'],
            'enjoys': ['likes', 'loves', 'enjoys', 'prefers'],
            'prefers': ['likes', 'loves', 'enjoys', 'prefers'],
            
            # Negative preferences
            'dislikes': ['dislikes', 'hates', 'avoids'],
            'hates': ['dislikes', 'hates', 'avoids'],
            'avoids': ['dislikes', 'hates', 'avoids'],
            
            # Action/activity relationships
            'does': ['does', 'plays', 'practices'],
            'plays': ['does', 'plays', 'practices'],
            'practices': ['does', 'plays', 'practices'],
            
            # Possession relationships
            'owns': ['owns', 'has'],
            'has': ['owns', 'has'],
        }
    
    async def _detect_opposing_relationships(self, conn, user_id: str, entity_id: str, 
                                           new_relationship: str, new_confidence: float) -> Optional[str]:
        """
        Detect and resolve opposing relationship conflicts.
        
        Args:
            conn: Database connection
            user_id: User identifier
            entity_id: Entity identifier
            new_relationship: New relationship type being added
            new_confidence: Confidence of new relationship
            
        Returns:
            'keep_existing', 'resolved', or None if no conflicts
        """
        opposing_relationships = self._get_opposing_relationships()
        
        if new_relationship not in opposing_relationships:
            return None
            
        # Check for existing opposing relationships
        opposing_types = opposing_relationships[new_relationship]
        conflicts = await conn.fetch("""
            SELECT relationship_type, confidence, updated_at, mentioned_by_character
            FROM user_fact_relationships 
            WHERE user_id = $1 AND entity_id = $2 
            AND relationship_type = ANY($3)
            ORDER BY confidence DESC, updated_at DESC
        """, user_id, entity_id, opposing_types)
        
        if not conflicts:
            return None
            
        for conflict in conflicts:
            conflict_confidence = float(conflict['confidence'])
            
            if conflict_confidence > new_confidence:
                # Keep stronger existing opposing relationship
                logger.info(f"⚠️ CONFLICT DETECTED: Keeping stronger existing '{conflict['relationship_type']}' "
                           f"(confidence: {conflict_confidence:.2f}) over new '{new_relationship}' "
                           f"(confidence: {new_confidence:.2f}) for entity {entity_id}")
                return 'keep_existing'
            else:
                # Replace weaker opposing relationship with stronger new one
                await conn.execute("""
                    DELETE FROM user_fact_relationships 
                    WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
                """, user_id, entity_id, conflict['relationship_type'])
                
                logger.info(f"🔄 CONFLICT RESOLVED: Replaced weaker '{conflict['relationship_type']}' "
                           f"(confidence: {conflict_confidence:.2f}) with stronger '{new_relationship}' "
                           f"(confidence: {new_confidence:.2f}) for entity {entity_id}")
        
        return 'resolved'
    
    async def _consolidate_similar_relationships(
        self, conn, user_id: str, entity_id: str,
        new_relationship: str, new_confidence: float
    ) -> None:
        """
        Consolidate similar/redundant relationships for the same entity.
        
        When storing a fact, check if similar relationships already exist (e.g., "likes" vs "enjoys").
        Keep only the highest confidence relationship and remove duplicates to avoid redundancy.
        
        Args:
            conn: Database connection
            user_id: User identifier
            entity_id: Entity identifier
            new_relationship: New relationship type being added
            new_confidence: Confidence of new relationship
        """
        similar_groups = self._get_similar_relationship_groups()
        
        if new_relationship not in similar_groups:
            return
        
        # Get similar relationships that already exist for this entity
        similar_types = similar_groups[new_relationship]
        existing = await conn.fetch("""
            SELECT relationship_type, confidence, updated_at
            FROM user_fact_relationships 
            WHERE user_id = $1 AND entity_id = $2 
            AND relationship_type = ANY($3)
            ORDER BY confidence DESC, updated_at DESC
        """, user_id, entity_id, similar_types)
        
        if not existing:
            return
        
        # Find if there's a stronger existing relationship
        strongest_existing = existing[0]
        existing_confidence = float(strongest_existing['confidence'])
        existing_relationship = strongest_existing['relationship_type']
        
        # If we're trying to add a weaker relationship, skip it and remove duplicates
        if new_confidence <= existing_confidence:
            logger.debug(
                f"🔄 DEDUP: Skipping weaker '{new_relationship}' (confidence: {new_confidence:.2f}) "
                f"for {entity_id} - stronger '{existing_relationship}' exists "
                f"(confidence: {existing_confidence:.2f})"
            )
            
            # Remove any other weaker similar relationships
            for other in existing[1:]:
                await conn.execute("""
                    DELETE FROM user_fact_relationships 
                    WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
                """, user_id, entity_id, other['relationship_type'])
                logger.debug(f"🗑️ Removed redundant '{other['relationship_type']}' relationship")
            
            # Don't store the new weaker one
            raise Exception('skip_insert')
        else:
            # New relationship is stronger - remove all existing weaker ones
            logger.info(
                f"🔄 DEDUP: Replacing weaker '{existing_relationship}' (confidence: {existing_confidence:.2f}) "
                f"with stronger '{new_relationship}' (confidence: {new_confidence:.2f}) for entity {entity_id}"
            )
            for other in existing:
                await conn.execute("""
                    DELETE FROM user_fact_relationships 
                    WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
                """, user_id, entity_id, other['relationship_type'])
                logger.debug(f"🗑️ Removed redundant '{other['relationship_type']}' relationship")
    
    async def analyze_query_intent(self, query: str) -> IntentAnalysisResult:
        """
        Analyze query to determine intent and routing strategy using unified classifier.
        
        Phase 2b: Integrated UnifiedQueryClassifier for authoritative intent analysis.
        Maps unified intents back to SemanticKnowledgeRouter's QueryIntent for backward compatibility.
        
        Args:
            query: User's natural language query
            
        Returns:
            IntentAnalysisResult with routing information
        """
        # Phase 2b: Use unified classifier for intent analysis
        if self._unified_query_classifier is not None:
            try:
                # Get unified classification result using async classify method
                unified_result = await self._unified_query_classifier.classify(query)
                
                # Map UnifiedQueryIntent to SemanticKnowledgeRouter's QueryIntent (both have identical 7 values)
                intent_mapping = {
                    UnifiedQueryIntent.FACTUAL_RECALL: QueryIntent.FACTUAL_RECALL,
                    UnifiedQueryIntent.CONVERSATION_STYLE: QueryIntent.CONVERSATION_STYLE,
                    UnifiedQueryIntent.TEMPORAL_ANALYSIS: QueryIntent.TEMPORAL_ANALYSIS,
                    UnifiedQueryIntent.PERSONALITY_KNOWLEDGE: QueryIntent.PERSONALITY_KNOWLEDGE,
                    UnifiedQueryIntent.RELATIONSHIP_DISCOVERY: QueryIntent.RELATIONSHIP_DISCOVERY,
                    UnifiedQueryIntent.ENTITY_SEARCH: QueryIntent.ENTITY_SEARCH,
                    UnifiedQueryIntent.USER_ANALYTICS: QueryIntent.USER_ANALYTICS,
                }
                
                mapped_intent = intent_mapping.get(
                    unified_result.intent_type,
                    QueryIntent.FACTUAL_RECALL
                )
                
                # Extract entity and relationship types (fallback to old extractors for backward compat)
                query_lower = query.lower()
                entity_type = self._extract_entity_type(query_lower)
                relationship_type = self._extract_relationship_type(query_lower)
                
                logger.debug(
                    "✅ UNIFIED: SemanticRouter intent=%s (unified=%s, confidence=%.2f)",
                    mapped_intent.value,
                    unified_result.intent_type.value,
                    unified_result.intent_confidence
                )
                
                return IntentAnalysisResult(
                    intent_type=mapped_intent,
                    entity_type=entity_type,
                    relationship_type=relationship_type,
                    confidence=unified_result.intent_confidence,
                    keywords=unified_result.keywords
                )
            except TypeError as e:
                logger.warning(
                    "⚠️  UNIFIED: analyze_query_intent failed: %s. Falling back to fuzzy matching.",
                    str(e)
                )
                # Fall through to legacy implementation below
        
        # Fallback: Legacy fuzzy matching (used if unified classifier unavailable)
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
        
        logger.debug("⚠️  FALLBACK: Intent analysis using fuzzy matching: %s (confidence: %.2f)", intent_type.value, confidence)
        
        return IntentAnalysisResult(
            intent_type=intent_type,
            entity_type=entity_type,
            relationship_type=relationship_type,
            confidence=confidence,
            keywords=keywords
        )
    
    def _extract_entity_type(self, query: str) -> Optional[str]:
        """
        Extract entity type from query using spaCy NER + keyword fallback.
        
        Prioritizes spaCy entity extraction for better accuracy, falls back
        to keyword matching if spaCy unavailable.
        """
        # Try spaCy entity extraction first (if available)
        if self.nlp:
            try:
                doc = self.nlp(query)
                
                # Map spaCy entity labels to our entity types
                # Comprehensive mapping for all major spaCy entity types
                entity_label_mapping = {
                    # People and characters
                    "PERSON": "person",
                    
                    # Organizations and businesses
                    "ORG": "work",
                    
                    # Locations (geo-political entities, locations, facilities)
                    "GPE": "place",          # Countries, cities, states
                    "LOC": "place",          # Non-GPE locations (mountains, bodies of water)
                    "FAC": "place",          # Facilities (buildings, airports, highways)
                    
                    # Products and objects
                    "PRODUCT": "equipment",  # Objects, vehicles, foods, etc.
                    
                    # Creative works
                    "WORK_OF_ART": "art",    # Titles of books, songs, etc.
                    
                    # Events and time
                    "EVENT": "general",      # Named events (concerts, wars, etc.)
                    "DATE": "general",       # Absolute or relative dates
                    "TIME": "general",       # Times smaller than a day
                    
                    # Legal and political
                    "LAW": "general",        # Named laws, treaties, etc.
                    "NORP": "general",       # Nationalities, religious/political groups
                    
                    # Miscellaneous
                    "LANGUAGE": "study",     # Named languages
                    "QUANTITY": "general",   # Measurements with units
                    "ORDINAL": "general",    # "first", "second", etc.
                    "CARDINAL": "general",   # Numerals not covered by other types
                    "MONEY": "general",      # Monetary values
                    "PERCENT": "general",    # Percentage values
                }
                
                # Return first recognized entity type
                for ent in doc.ents:
                    if ent.label_ in entity_label_mapping:
                        logger.debug("🔍 spaCy entity extracted: %s (%s)", ent.text, ent.label_)
                        return entity_label_mapping[ent.label_]
            except Exception as e:
                logger.warning("⚠️ spaCy entity extraction failed: %s", str(e))
        
        # Fallback: Keyword-based entity detection with lemmatization (ChatGPT-style expanded categorization)
        # Lemmatize query for normalized matching
        lemmatized_query = self._lemmatize_for_entity_detection(query)
        
        # Entity keyword patterns (using lemmatized base forms)
        entity_keywords = {
            "food": ["food", "eat", "meal", "restaurant", "cuisine", "dish", "cook", "recipe"],
            "hobby": ["hobby", "activity", "interest", "enjoy", "passion"],
            "place": ["place", "location", "city", "country", "visit", "travel", "destination", "live"],
            "person": ["person", "people", "friend", "family", "colleague", "know", "relationship"],
            "book": ["book", "read", "author", "novel", "title", "library", "literature"],
            "art": ["art", "artwork", "draw", "paint", "sketch", "artistic", "creative", "visual", "design"],
            "music": ["music", "song", "album", "artist", "band", "listen", "genre", "sound", "audio"],
            "movie": ["movie", "film", "cinema", "watch", "director", "actor", "show", "series"],
            "equipment": ["equipment", "tool", "device", "gear", "hardware", "machine"],
            "preference": ["like", "prefer", "favorite", "love", "enjoy", "want", "need", "choose"],
            "work": ["work", "job", "career", "profession", "office", "company", "project", "task"],
            "study": ["study", "learn", "education", "school", "course", "class", "subject", "research"],
            "general": ["thing", "stuff", "item", "something", "anything", "everything"]
        }
        
        # Check for entity type keywords in lemmatized query
        for entity_type, keywords in entity_keywords.items():
            for keyword in keywords:
                if keyword in lemmatized_query:
                    logger.debug(f"✅ Semantic Router: Matched entity type '{entity_type}' via lemmatized keyword '{keyword}'")
                    return entity_type
        
        return None
    
    def _lemmatize_for_entity_detection(self, query: str) -> str:
        """
        Lemmatize query for entity type detection with advanced spaCy features.
        
        Normalizes word variations (eating→eat, visited→visit, etc.) and filters
        to content words only (NOUN/VERB/ADJ/ADV) to reduce noise from articles,
        pronouns, and auxiliary verbs.
        
        ADVANCED FEATURES USED:
        1. Lemmatization - Word form normalization
        2. POS Tagging - Content-word filtering (NOUN/VERB/ADJ/ADV)
        3. Named Entity Recognition - Context awareness via entity spans
        4. Noun Chunks - Multi-word entity grouping (e.g., "Italian restaurant")
        5. Dependency Parsing - Subject-verb-object relationships
        6. Negation Detection - Track negation to flip sentiment (don't like → hate)
        
        Uses pattern from: Hybrid Context Detector + Character Learning Detector
        
        Args:
            query: Query string to lemmatize
            
        Returns:
            Lemmatized content words as space-separated string
        """
        try:
            nlp = get_spacy_nlp()
            if not nlp:
                return query.lower()
            
            doc = nlp(query.lower())
            
            # Track negations via dependency parsing (negation detection feature #6)
            negation_heads = set()
            for token in doc:
                if token.dep_ == "neg":  # Negation marker (no, not, never, neither, nobody, nowhere)
                    negation_heads.add(token.head.i)  # Mark the head verb as negated
            
            # Extract content words with negation awareness
            content_lemmas = []
            for token in doc:
                if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']:
                    lemma = token.lemma_
                    
                    # NEGATION FEATURE: If this verb is negated, flip sentiment
                    if token.i in negation_heads and token.pos_ == 'VERB':
                        # Mark negation with prefix for pattern matching later
                        lemma = f"not_{lemma}"
                    
                    content_lemmas.append(lemma)
            
            # Fallback to all lemmas if no content words found
            if not content_lemmas:
                content_lemmas = [token.lemma_ for token in doc if not token.is_punct]
            
            return ' '.join(content_lemmas)
        except Exception as e:
            logger.warning(f"⚠️ Semantic Router lemmatization failed: {e}")
            return query.lower()
    
    def _extract_relationship_type(self, query: str) -> Optional[str]:
        """
        Extract relationship type from query using advanced spaCy features.
        
        ADVANCED FEATURES USED:
        1. Lemmatization - Match all tense forms
        2. POS Tagging - Identify verbs and their modifiers
        3. Dependency Parsing - Extract subject-verb-object chains
        4. Named Entity Recognition - Context from detected entities
        5. Negation Detection - Track negations to flip sentiment
        
        Example: "I don't like pizza" → relationship: "dislikes" (not "likes")
        Example: "I want to visit France" → relationships: "wants" + "visited" (via dependency parsing)
        """
        try:
            nlp = get_spacy_nlp()
            if nlp:
                doc = nlp(query.lower())
                
                # Relationship patterns (using lemmatized base forms)
                relationship_keywords = {
                    "likes": ["like", "love", "enjoy", "favorite", "prefer"],
                    "dislikes": ["dislike", "hate", "avoid"],
                    "knows": ["know", "familiar", "aware"],
                    "visited": ["visit", "travel", "go", "trip"],
                    "wants": ["want", "wish", "desire", "hope"],
                    "owns": ["own", "have", "possess"]
                }
                
                # FEATURE 5: Negation-aware relationship detection via dependency parsing
                negation_verbs = set()
                for token in doc:
                    if token.dep_ == "neg":
                        negation_verbs.add(token.head.lemma_)
                
                # FEATURE 3: Dependency parsing for multi-clause extraction
                # Extract main verbs and their complements
                main_verbs = []
                for token in doc:
                    if token.pos_ == "VERB":
                        is_negated = token.lemma_ in negation_verbs
                        main_verbs.append((token.lemma_, is_negated))
                        
                        # Extract xcomp/ccomp (complement clauses - like AI Ethics)
                        for child in token.children:
                            if child.dep_ in ["xcomp", "ccomp"] and child.pos_ == "VERB":
                                child_negated = child.lemma_ in negation_verbs
                                main_verbs.append((child.lemma_, child_negated))
                
                # Check verbs for relationship types (with negation awareness)
                for verb, is_negated in main_verbs:
                    for rel_type, keywords in relationship_keywords.items():
                        if verb in keywords:
                            # NEGATION FEATURE: If negated and it's a like/prefer verb, flip to dislikes
                            if is_negated and rel_type in ["likes", "wants"]:
                                return "dislikes" if rel_type == "likes" else "owns"  # opposite relationship
                            return rel_type
                
                # FEATURE 2: Lemmatized fallback if no verb extraction worked
                lemmatized_query = self._lemmatize_for_entity_detection(query)
                
                for rel_type, keywords in relationship_keywords.items():
                    if any(kw in lemmatized_query for kw in keywords):
                        # Check if negated via "not_" prefix from lemmatization
                        if any(f"not_{kw}" in lemmatized_query for kw in keywords) and rel_type in ["likes", "wants"]:
                            return "dislikes" if rel_type == "likes" else "owns"
                        return rel_type
        except Exception as e:
            logger.warning(f"⚠️ Advanced relationship extraction failed, falling back: {e}")
        
        # Fallback: Simple lemmatized matching
        lemmatized_query = self._lemmatize_for_entity_detection(query)
        relationship_keywords = {
            "likes": ["like", "love", "enjoy", "favorite", "prefer"],
            "dislikes": ["dislike", "hate", "avoid"],
            "knows": ["know", "familiar", "aware"],
            "visited": ["visit", "travel", "go"],
            "wants": ["want", "wish", "desire", "hope"],
            "owns": ["own", "have", "possess"]
        }
        
        for rel_type, keywords in relationship_keywords.items():
            if any(kw in lemmatized_query for kw in keywords):
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
                  AND fe.entity_type != '_processing_marker'
                  AND ufr.relationship_type NOT LIKE '_enrichment%'
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
                    fe.entity_type,
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
                  AND fe.entity_type != '_processing_marker'
                  AND ufr.relationship_type NOT LIKE '_enrichment%'
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
                    "entity_type": row["entity_type"],
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
    
    async def get_temporally_relevant_facts(
        self, 
        user_id: str, 
        lookback_days: int = 90,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user facts with temporal relevance weighting.
        Recent facts are weighted higher, and potentially outdated facts are flagged.
        
        Args:
            user_id: User identifier
            lookback_days: How many days back to consider (default 90)
            limit: Maximum number of results
            
        Returns:
            List of facts with temporal relevance scoring
        """
        async with self.postgres.acquire() as conn:
            query = """
                SELECT 
                    ufr.*,
                    fe.entity_name,
                    fe.entity_type,
                    fe.category,
                    fe.attributes,
                    
                    -- Temporal relevance scoring (0.4 to 1.0)
                    CASE 
                        WHEN ufr.updated_at > NOW() - INTERVAL '30 days' THEN 1.0
                        WHEN ufr.updated_at > NOW() - INTERVAL '60 days' THEN 0.8
                        WHEN ufr.updated_at > NOW() - INTERVAL '90 days' THEN 0.6
                        ELSE 0.4
                    END as temporal_relevance,
                    
                    -- Fact age in days
                    EXTRACT(days FROM NOW() - ufr.updated_at) as fact_age_days,
                    
                    -- Detect potentially outdated facts based on relationship type
                    CASE 
                        WHEN ufr.relationship_type IN ('works_at', 'lives_in', 'studies_at') 
                        AND ufr.updated_at < NOW() - INTERVAL '180 days' THEN true
                        
                        WHEN ufr.relationship_type IN ('wants', 'plans', 'intends', 'dreams_of')
                        AND ufr.updated_at < NOW() - INTERVAL '60 days' THEN true
                        
                        WHEN ufr.relationship_type IN ('dating', 'in_relationship_with')
                        AND ufr.updated_at < NOW() - INTERVAL '120 days' THEN true
                        
                        WHEN ufr.relationship_type IN ('feels', 'currently_feeling')
                        AND ufr.updated_at < NOW() - INTERVAL '7 days' THEN true
                        
                        ELSE false
                    END as potentially_outdated,
                    
                    -- Weighted confidence combining original confidence with temporal relevance
                    (ufr.confidence * 
                     CASE 
                        WHEN ufr.updated_at > NOW() - INTERVAL '30 days' THEN 1.0
                        WHEN ufr.updated_at > NOW() - INTERVAL '60 days' THEN 0.8
                        WHEN ufr.updated_at > NOW() - INTERVAL '90 days' THEN 0.6
                        ELSE 0.4
                     END
                    ) as weighted_confidence
                    
                FROM user_fact_relationships ufr
                JOIN fact_entities fe ON ufr.entity_id = fe.id
                WHERE ufr.user_id = $1
                AND fe.entity_type != '_processing_marker'
                AND ufr.relationship_type NOT LIKE '_enrichment%'
                AND ufr.updated_at > NOW() - ($2 || ' days')::INTERVAL
                ORDER BY 
                    weighted_confidence DESC,
                    ufr.updated_at DESC
                LIMIT $3
            """
            
            rows = await conn.fetch(query, user_id, str(lookback_days), limit)
            
            facts = []
            for row in rows:
                facts.append({
                    "entity_name": row["entity_name"],
                    "entity_type": row["entity_type"],
                    "category": row["category"],
                    "relationship_type": row["relationship_type"],
                    "confidence": float(row["confidence"]),
                    "weighted_confidence": float(row["weighted_confidence"]),
                    "temporal_relevance": float(row["temporal_relevance"]),
                    "fact_age_days": int(row["fact_age_days"]) if row["fact_age_days"] else 0,
                    "potentially_outdated": bool(row["potentially_outdated"]),
                    "emotional_context": row["emotional_context"],
                    "mentioned_by_character": row["mentioned_by_character"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "context_metadata": row["context_metadata"]
                })
            
            logger.info(f"⏰ Retrieved {len(facts)} temporally-weighted facts for user {user_id} "
                       f"(lookback: {lookback_days} days)")
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
        # Validate and fix null relationship_type
        if relationship_type is None or relationship_type == "":
            relationship_type = "mentions"  # Default fallback
            logger.warning(f"⚠️ NULL relationship_type detected for entity '{entity_name}', using default 'mentions'")
        
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
                    
                    # Check for opposing relationship conflicts before storing
                    conflict_result = await self._detect_opposing_relationships(
                        conn, user_id, entity_id, relationship_type, confidence
                    )
                    
                    if conflict_result == 'keep_existing':
                        # Don't store the new relationship, existing opposing one is stronger
                        logger.info(f"🚫 CONFLICT: Skipped storing '{relationship_type}' for {entity_name} - "
                                   f"stronger opposing relationship exists")
                        return True
                    
                    # Check for similar/redundant relationships and keep only highest confidence
                    try:
                        await self._consolidate_similar_relationships(
                            conn, user_id, entity_id, relationship_type, confidence
                        )
                    except Exception as e:
                        if str(e) == 'skip_insert':
                            # Weaker relationship - skip storing it
                            return True
                        raise
                    
                    # Insert or update user-fact relationship (conflicts already resolved)
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

    async def get_user_recommendations(
        self,
        user_id: str,
        recommendation_type: str = "interests",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations based on user's existing facts and graph relationships.
        
        Uses the entity relationship graph to suggest new interests, activities, or items
        based on what the user already likes or enjoys.
        
        Args:
            user_id: User identifier
            recommendation_type: Type of recommendations ('interests', 'activities', 'food', etc.)
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended entities with reasons and confidence scores
            
        Example:
            recommendations = await router.get_user_recommendations(
                user_id="123456789",
                recommendation_type="interests",
                limit=3
            )
            # Returns: [
            #   {
            #     'entity_name': 'photography', 
            #     'entity_type': 'hobby',
            #     'reason': 'Similar to hiking (liked)',
            #     'confidence': 0.75,
            #     'similarity_score': 0.68
            #   }
            # ]
        """
        try:
            async with self.postgres.acquire() as conn:
                # Get user's highly-rated interests as recommendation seeds
                user_seeds = await conn.fetch("""
                    SELECT fe.entity_name, fe.entity_type, fe.category,
                           ufr.relationship_type, ufr.confidence
                    FROM user_fact_relationships ufr
                    JOIN fact_entities fe ON ufr.entity_id = fe.id
                    WHERE ufr.user_id = $1
                      AND ufr.relationship_type IN ('likes', 'enjoys', 'loves')
                      AND ufr.confidence >= 0.7
                      AND ($2 = 'all' OR fe.entity_type = $2 OR fe.category = $2)
                    ORDER BY ufr.confidence DESC
                    LIMIT 10
                """, user_id, recommendation_type)
                
                if not user_seeds:
                    logger.info(f"🤷 No high-confidence user preferences found for recommendations")
                    return []
                
                recommendations = {}  # Use dict to avoid duplicates
                
                # For each seed interest, find similar entities
                for seed in user_seeds:
                    seed_name = seed['entity_name']
                    seed_type = seed['entity_type']
                    seed_confidence = seed['confidence']
                    
                    # Find similar entities using trigram similarity and explicit relationships
                    similar_entities = await conn.fetch("""
                        WITH similar_by_name AS (
                            -- Find entities with similar names
                            SELECT fe.entity_name, fe.entity_type, fe.category,
                                   similarity(fe.entity_name, $1) as similarity_score,
                                   'name_similarity' as reason_type
                            FROM fact_entities fe
                            WHERE fe.entity_name != $1
                              AND similarity(fe.entity_name, $1) > 0.3
                              AND fe.entity_type = $2
                        ),
                        similar_by_graph AS (
                            -- Find entities connected by explicit relationships
                            SELECT fe2.entity_name, fe2.entity_type, fe2.category,
                                   er.weight as similarity_score,
                                   'graph_connection' as reason_type
                            FROM fact_entities fe1
                            JOIN entity_relationships er ON fe1.id = er.from_entity_id
                            JOIN fact_entities fe2 ON er.to_entity_id = fe2.id
                            WHERE fe1.entity_name = $1 
                              AND fe1.entity_type = $2
                              AND er.weight > 0.3
                        ),
                        combined_similar AS (
                            SELECT * FROM similar_by_name
                            UNION ALL
                            SELECT * FROM similar_by_graph
                        )
                        SELECT entity_name, entity_type, category, 
                               MAX(similarity_score) as best_similarity,
                               reason_type
                        FROM combined_similar
                        WHERE entity_name NOT IN (
                            -- Exclude things user already has relationship with
                            SELECT fe.entity_name 
                            FROM user_fact_relationships ufr2
                            JOIN fact_entities fe ON ufr2.entity_id = fe.id
                            WHERE ufr2.user_id = $3
                        )
                        GROUP BY entity_name, entity_type, category, reason_type
                        ORDER BY best_similarity DESC
                        LIMIT 5
                    """, seed_name, seed_type, user_id)
                    
                    # Add recommendations with context
                    for similar in similar_entities:
                        entity_name = similar['entity_name']
                        if entity_name not in recommendations:
                            # Calculate confidence based on similarity and seed confidence
                            base_confidence = float(similar['best_similarity']) * seed_confidence
                            
                            recommendations[entity_name] = {
                                'entity_name': entity_name,
                                'entity_type': similar['entity_type'],
                                'category': similar['category'],
                                'reason': f"Similar to {seed_name} ({seed['relationship_type']})",
                                'confidence': min(base_confidence, 0.9),  # Cap at 0.9
                                'similarity_score': float(similar['best_similarity']),
                                'reason_type': similar['reason_type'],
                                'seed_entity': seed_name,
                                'seed_confidence': seed_confidence
                            }
                
                # Sort by confidence and return top recommendations
                sorted_recommendations = sorted(
                    recommendations.values(), 
                    key=lambda x: x['confidence'], 
                    reverse=True
                )[:limit]
                
                logger.info(f"💡 Generated {len(sorted_recommendations)} recommendations for user {user_id}")
                return sorted_recommendations
                
        except Exception as e:
            logger.error(f"❌ Failed to generate recommendations: {e}")
            return []
    
    async def deprecate_outdated_facts(self, dry_run: bool = True) -> Dict[str, int]:
        """
        Actively deprecate facts that are likely outdated based on their age and type.
        
        This method:
        1. Identifies facts that are likely stale based on relationship type and age
        2. Gradually reduces confidence for aging facts
        3. Soft-deletes facts that are very likely obsolete
        4. Preserves all original data (reversible operations)
        
        Args:
            dry_run: If True, only reports what would be changed without making changes
            
        Returns:
            Dictionary with counts of deprecated and confidence-reduced facts
        """
        try:
            # Define staleness rules: relationship_type -> max_days_before_suspicious
            staleness_rules = {
                # Career/Work facts (change frequently)
                'works_at': 365,          # Jobs change yearly
                'employed_by': 365,
                'job_title': 365,
                
                # Location facts (change occasionally)  
                'lives_in': 730,          # Address changes every 2 years
                'resides_in': 730,
                'located_in': 730,
                
                # Education facts (longer-term but do change)
                'studies_at': 1460,       # Education programs are multi-year
                'enrolled_in': 1460,
                'attends': 1460,
                
                # Short-term intentions/plans
                'wants': 90,              # Desires change seasonally
                'plans': 30,              # Plans are short-term
                'intends': 60,            # Intentions are medium-term
                'thinking_about': 14,     # Thoughts change quickly
                'considering': 30,
                
                # Relationship status (changes occasionally)
                'dating': 180,            # Relationship status changes
                'in_relationship_with': 180,
                'married_to': 1095,       # Marriage more stable
                
                # Feelings/emotional states (very short-term)
                'feels': 7,               # Feelings change weekly
                'feeling': 7,
                'currently_feeling': 3,   # Current feelings change quickly
                'mood': 1,                # Moods change daily
                
                # Possessions/ownership (longer-term)
                'owns': 1095,             # Possessions are longer-term (3 years)
                'has': 365,               # General "has" relationship
                
                # Travel/experiences (medium-term relevance)
                'visited': 1095,          # Travel experiences stay relevant longer
                'been_to': 1095,
                'traveled_to': 1095
            }
            
            deprecated_count = 0
            confidence_reduced_count = 0
            facts_processed = 0
            
            async with self.postgres.acquire() as conn:
                for relationship_type, max_days in staleness_rules.items():
                    
                    # Find potentially outdated facts for this relationship type
                    outdated_facts = await conn.fetch("""
                        SELECT 
                            ufr.user_id, 
                            ufr.entity_id, 
                            ufr.confidence, 
                            ufr.updated_at,
                            fe.entity_name,
                            EXTRACT(days FROM NOW() - ufr.updated_at) as days_old
                        FROM user_fact_relationships ufr
                        JOIN fact_entities fe ON ufr.entity_id = fe.id
                        WHERE ufr.relationship_type = $1
                        AND ufr.updated_at < NOW() - ($2 || ' days')::INTERVAL
                        AND ufr.confidence > 0.2
                        ORDER BY ufr.updated_at ASC
                    """, relationship_type, str(max_days))
                    
                    for fact in outdated_facts:
                        facts_processed += 1
                        days_old = float(fact['days_old'])
                        
                        # Calculate degradation factor based on how overdue the fact is
                        overdue_days = days_old - max_days
                        degradation_factor = max(0.2, 1.0 - (overdue_days / (max_days * 1.5)))
                        new_confidence = float(fact['confidence']) * degradation_factor
                        
                        if new_confidence < 0.3:
                            # Mark for soft deprecation (very low confidence + metadata flag)
                            if not dry_run:
                                await conn.execute("""
                                    UPDATE user_fact_relationships 
                                    SET 
                                        confidence = 0.1,
                                        context_metadata = COALESCE(context_metadata, '{}'::jsonb) || 
                                                         jsonb_build_object(
                                                             'deprecated', true,
                                                             'reason', 'temporal_staleness',
                                                             'original_confidence', $4,
                                                             'deprecated_at', $5
                                                         )
                                    WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
                                """, fact['user_id'], fact['entity_id'], relationship_type, 
                                float(fact['confidence']), datetime.now().isoformat())
                            deprecated_count += 1
                            
                            logger.info(f"🗑️ DEPRECATED: {fact['entity_name']} ({relationship_type}) "
                                       f"for user {fact['user_id'][-6:]} - {days_old:.0f} days old")
                        else:
                            # Gradually reduce confidence
                            if not dry_run:
                                await conn.execute("""
                                    UPDATE user_fact_relationships 
                                    SET confidence = $4
                                    WHERE user_id = $1 AND entity_id = $2 AND relationship_type = $3
                                """, fact['user_id'], fact['entity_id'], relationship_type, new_confidence)
                            confidence_reduced_count += 1
                            
                            logger.info(f"📉 CONFIDENCE REDUCED: {fact['entity_name']} ({relationship_type}) "
                                       f"from {fact['confidence']:.2f} to {new_confidence:.2f} "
                                       f"- {days_old:.0f} days old")
            
            result = {
                'facts_processed': facts_processed,
                'deprecated': deprecated_count,
                'confidence_reduced': confidence_reduced_count,
                'dry_run': dry_run
            }
            
            logger.info(f"📊 FACT DEPRECATION {'SIMULATION' if dry_run else 'COMPLETED'}: "
                       f"{facts_processed} facts processed, "
                       f"{deprecated_count} deprecated, "
                       f"{confidence_reduced_count} confidence reduced")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to deprecate outdated facts: {e}")
            return {
                'facts_processed': 0,
                'deprecated': 0,
                'confidence_reduced': 0,
                'error': str(e),
                'dry_run': dry_run
            }
    
    async def restore_deprecated_facts(self, user_id: Optional[str] = None) -> int:
        """
        Restore facts that were deprecated by the deprecation system.
        
        Args:
            user_id: If provided, only restore facts for this user. If None, restore all.
            
        Returns:
            Number of facts restored
        """
        try:
            async with self.postgres.acquire() as conn:
                if user_id:
                    query = """
                        UPDATE user_fact_relationships 
                        SET 
                            confidence = COALESCE((context_metadata->>'original_confidence')::float, 0.8),
                            context_metadata = context_metadata - 'deprecated' - 'reason' - 'original_confidence' - 'deprecated_at'
                        WHERE user_id = $1 
                        AND context_metadata->>'deprecated' = 'true'
                    """
                    result = await conn.execute(query, user_id)
                else:
                    query = """
                        UPDATE user_fact_relationships 
                        SET 
                            confidence = COALESCE((context_metadata->>'original_confidence')::float, 0.8),
                            context_metadata = context_metadata - 'deprecated' - 'reason' - 'original_confidence' - 'deprecated_at'
                        WHERE context_metadata->>'deprecated' = 'true'
                    """
                    result = await conn.execute(query)
                
                # Extract the number of affected rows from the result
                affected_rows = int(result.split()[-1]) if result else 0
                
                logger.info(f"🔄 RESTORED {affected_rows} deprecated facts" + 
                           (f" for user {user_id}" if user_id else ""))
                
                return affected_rows
                
        except Exception as e:
            logger.error(f"❌ Failed to restore deprecated facts: {e}")
            return 0
    
    # ========================================================================
    # LLM TOOL CALLING - Week 1 Hybrid Routing Integration
    # ========================================================================
    
    async def execute_tools(
        self,
        query: str,
        user_id: str,
        character_name: str,
        llm_client=None
    ) -> Dict[str, Any]:
        """
        Execute LLM tool calling for structured data retrieval.
        
        This method integrates with the UnifiedQueryClassifier's TOOL_ASSISTED
        intent to provide LLM-assisted multi-source data aggregation.
        
        Migrated from src/intelligence/tool_executor.py as part of Week 1
        hybrid routing refactoring.
        
        Args:
            query: User's query string
            user_id: User's unique identifier
            character_name: Current character name
            llm_client: Optional LLM client (will create if not provided)
        
        Returns:
            Dict with tool execution results:
                {
                    "tool_results": List[Dict],  # Raw tool results
                    "enriched_context": str,  # Formatted context for LLM
                    "tools_used": List[str],  # Names of tools executed
                    "execution_time_ms": float
                }
        """
        start_time = datetime.now()
        
        # Get tool definitions
        tools = self._get_tool_definitions()
        
        # Create LLM client if not provided
        if llm_client is None:
            from src.llm.llm_protocol import create_llm_client
            llm_client = create_llm_client(llm_client_type="openrouter")
        
        try:
            # Use LLM tool calling to determine which tools to execute
            tool_response = await llm_client.generate_chat_completion_with_tools(
                messages=[{
                    "role": "user",
                    "content": f"For the query: '{query}' - determine which data retrieval tools to use."
                }],
                tools=tools,
                tool_choice="auto"
            )
            
            # Execute called tools
            tool_results = []
            tools_used = []
            
            if hasattr(tool_response, 'tool_calls') and tool_response.tool_calls:
                for tool_call in tool_response.tool_calls:
                    tool_name = tool_call.function.name
                    
                    # Parse arguments (handle both string and dict)
                    if isinstance(tool_call.function.arguments, str):
                        import json
                        tool_arguments = json.loads(tool_call.function.arguments)
                    else:
                        tool_arguments = tool_call.function.arguments
                    
                    # Add required arguments
                    if tool_name == "query_user_facts":
                        tool_arguments["user_id"] = user_id
                    elif tool_name == "recall_conversation_context":
                        tool_arguments["user_id"] = user_id
                    elif tool_name == "query_character_backstory":
                        tool_arguments["character_name"] = character_name
                    elif tool_name == "summarize_user_relationship":
                        tool_arguments["user_id"] = user_id
                    elif tool_name == "query_temporal_trends":
                        tool_arguments["user_id"] = user_id
                    
                    # Execute tool
                    result = await self._execute_single_tool(
                        tool_name=tool_name,
                        arguments=tool_arguments
                    )
                    
                    tool_results.append(result)
                    tools_used.append(tool_name)
            
            # Format results for LLM consumption
            enriched_context = self._format_tool_results(tool_results)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(
                "🔧 TOOL EXECUTION: query='%s...' → %d tools used (%s) | Time: %.2fms",
                query[:40],
                len(tools_used),
                ', '.join(tools_used),
                execution_time
            )
            
            return {
                "tool_results": tool_results,
                "enriched_context": enriched_context,
                "tools_used": tools_used,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(
                "❌ TOOL EXECUTION FAILED: %s | Time: %.2fms",
                str(e),
                execution_time,
                exc_info=True
            )
            
            return {
                "tool_results": [],
                "enriched_context": "",
                "tools_used": [],
                "execution_time_ms": execution_time,
                "error": str(e)
            }
    
    async def _execute_single_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single tool and return results.
        
        Routes to the appropriate tool execution method based on tool_name.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of tool arguments
        
        Returns:
            Dict with tool results
        """
        start_time = datetime.now()
        
        try:
            # Route to appropriate tool method
            if tool_name == "query_user_facts":
                data = await self._tool_query_user_facts(**arguments)
            elif tool_name == "recall_conversation_context":
                data = await self._tool_recall_conversation_context(**arguments)
            elif tool_name == "query_character_backstory":
                data = await self._tool_query_character_backstory(**arguments)
            elif tool_name == "summarize_user_relationship":
                data = await self._tool_summarize_user_relationship(**arguments)
            elif tool_name == "query_temporal_trends":
                data = await self._tool_query_temporal_trends(**arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "tool_name": tool_name,
                "data": data,
                "error": None,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            logger.error(
                "Tool execution failed: %s | Error: %s | Time: %.2fms",
                tool_name,
                error_msg,
                execution_time
            )
            
            return {
                "success": False,
                "tool_name": tool_name,
                "data": None,
                "error": error_msg,
                "execution_time_ms": execution_time
            }
    
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get LLM tool calling definitions for all 5 core tools.
        
        Returns:
            List of tool definitions in OpenAI function calling format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_user_facts",
                    "description": "Query structured user facts and preferences from PostgreSQL (pets, hobbies, family, preferences, location, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fact_type": {
                                "type": "string",
                                "enum": ["all", "pet", "hobby", "family", "preference", "location"],
                                "description": "Type of facts to query (default: 'all')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of facts to return (default: 10)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recall_conversation_context",
                    "description": "Retrieve relevant conversation history using semantic search on Qdrant vector memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Semantic search query to find relevant conversations"
                            },
                            "time_window": {
                                "type": "string",
                                "enum": ["24h", "7d", "30d", "all"],
                                "description": "Time window filter (default: 'all')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of memories to return (default: 5)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_character_backstory",
                    "description": "Query PostgreSQL CDL database for character backstory, personality, and designer-defined facts",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What to query about the character's background"
                            },
                            "source": {
                                "type": "string",
                                "enum": ["cdl_database", "self_memory", "both"],
                                "description": "Data source to query (default: 'both')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "summarize_user_relationship",
                    "description": "Generate comprehensive relationship summary by aggregating user facts and conversation history",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "include_facts": {
                                "type": "boolean",
                                "description": "Include user facts from PostgreSQL (default: true)"
                            },
                            "include_conversations": {
                                "type": "boolean",
                                "description": "Include conversation history from Qdrant (default: true)"
                            },
                            "time_window": {
                                "type": "string",
                                "enum": ["24h", "7d", "30d", "all"],
                                "description": "Time window for conversations (default: 'all')"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_temporal_trends",
                    "description": "Query InfluxDB for conversation quality metrics over time (engagement, satisfaction, coherence)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metric": {
                                "type": "string",
                                "enum": ["all", "engagement_score", "satisfaction_score", "coherence_score"],
                                "description": "Metric to query (default: 'all')"
                            },
                            "time_window": {
                                "type": "string",
                                "enum": ["24h", "7d", "30d"],
                                "description": "Time window for trends (default: '7d')"
                            }
                        }
                    }
                }
            }
        ]
    
    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """
        Format tool results into enriched context string for LLM.
        
        Args:
            tool_results: List of tool execution results
        
        Returns:
            Formatted context string
        """
        if not tool_results:
            return ""
        
        context_parts = ["=== TOOL RESULTS ==="]
        
        for result in tool_results:
            if not result.get("success"):
                continue
            
            tool_name = result["tool_name"]
            data = result["data"]
            
            context_parts.append(f"\n--- {tool_name} ---")
            
            if isinstance(data, list) and data:
                context_parts.append(f"Found {len(data)} items:")
                for item in data[:5]:  # Limit to first 5 for context
                    context_parts.append(f"  • {json.dumps(item, indent=2)}")
            elif isinstance(data, dict):
                context_parts.append(json.dumps(data, indent=2))
            else:
                context_parts.append(str(data))
        
        context_parts.append("\n===================")
        
        return "\n".join(context_parts)
    
    # Tool 1: Query User Facts
    async def _tool_query_user_facts(
        self,
        user_id: str,
        fact_type: str = "all",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Tool 1: Query PostgreSQL for user facts and preferences.
        
        Migrated from src/intelligence/tool_executor.py
        """
        if not self.postgres:
            raise RuntimeError("PostgreSQL connection pool not available")
        
        # Build query based on fact_type filter
        if fact_type == "all":
            type_filter = "AND fe.entity_type != '_processing_marker'"
        else:
            type_filter = f"AND fe.entity_type = '{fact_type}'"
        
        query = f"""
            SELECT 
                ufr.relationship_type,
                fe.entity_type,
                fe.entity_name,
                fe.category,
                ufr.confidence,
                ufr.mentioned_by_character,
                ufr.created_at
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE ufr.user_id = $1
                {type_filter}
                AND ufr.relationship_type NOT LIKE '_enrichment%'
            ORDER BY ufr.created_at DESC
            LIMIT $2
        """
        
        async with self.postgres.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit)
        
        facts = [
            {
                "relationship_type": row["relationship_type"],
                "entity_type": row["entity_type"],
                "entity_name": row["entity_name"],
                "category": row["category"],
                "confidence": float(row["confidence"]) if row["confidence"] else 1.0,
                "mentioned_by_character": row["mentioned_by_character"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
            for row in rows
        ]
        
        logger.debug(
            "query_user_facts | User: %s | Type: %s | Found: %d facts",
            user_id,
            fact_type,
            len(facts)
        )
        
        return facts
    
    # Tool 2: Recall Conversation Context
    async def _tool_recall_conversation_context(
        self,
        user_id: str,
        query: str,
        time_window: str = "all",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Tool 2: Query Qdrant for relevant conversation history.
        
        Migrated from src/intelligence/tool_executor.py
        """
        if not self.qdrant:
            raise RuntimeError("Qdrant client not available")
        
        # Calculate time filter if needed
        time_filter = None
        if time_window != "all":
            window_hours = {
                "24h": 24,
                "7d": 24 * 7,
                "30d": 24 * 30
            }
            hours = window_hours.get(time_window, 24 * 365)
            time_filter = datetime.now() - timedelta(hours=hours)
        
        # Use existing vector memory retrieval
        # Note: This requires VectorMemorySystem instance - TODO: integrate properly
        logger.warning(
            "_tool_recall_conversation_context requires VectorMemorySystem integration"
        )
        
        return []
    
    # Tool 3: Query Character Backstory
    async def _tool_query_character_backstory(
        self,
        character_name: str,
        query: str,
        source: str = "both"
    ) -> Dict[str, Any]:
        """
        Tool 3: Query PostgreSQL CDL database for character backstory.
        
        Migrated from src/intelligence/tool_executor.py (placeholder)
        """
        if not self.postgres:
            raise RuntimeError("PostgreSQL connection pool not available")
        
        # TODO: Implement CDL database queries
        logger.warning(
            "query_character_backstory NOT FULLY IMPLEMENTED | "
            "Character: %s | Query: '%s' | Source: %s",
            character_name,
            query[:50],
            source
        )
        
        return {
            "character_name": character_name,
            "query": query,
            "background": {},
            "identity": {},
            "interests": [],
            "source": source,
            "note": "Full implementation pending - requires CDL table schema analysis"
        }
    
    # Tool 4: Summarize User Relationship
    async def _tool_summarize_user_relationship(
        self,
        user_id: str,
        include_facts: bool = True,
        include_conversations: bool = True,
        time_window: str = "all"
    ) -> Dict[str, Any]:
        """
        Tool 4: Generate comprehensive user relationship summary.
        
        Migrated from src/intelligence/tool_executor.py
        """
        summary = {
            "user_id": user_id,
            "facts": [],
            "conversation_summary": {},
            "relationship_duration": None,
            "total_interactions": 0,
            "most_discussed_topics": []
        }
        
        # Get user facts if requested
        if include_facts and self.postgres:
            summary["facts"] = await self._tool_query_user_facts(
                user_id=user_id,
                fact_type="all",
                limit=20
            )
        
        # Get conversation summary if requested
        if include_conversations and self.qdrant:
            memories = await self._tool_recall_conversation_context(
                user_id=user_id,
                query="general conversation",
                time_window=time_window,
                limit=10
            )
            
            if memories:
                summary["conversation_summary"] = {
                    "recent_conversations": len(memories),
                    "time_window": time_window,
                    "sample_interactions": memories[:3]
                }
                summary["total_interactions"] = len(memories)
        
        logger.debug(
            "summarize_user_relationship | User: %s | Facts: %d | "
            "Conversations: %d | Window: %s",
            user_id,
            len(summary["facts"]),
            summary["total_interactions"],
            time_window
        )
        
        return summary
    
    # Tool 5: Query Temporal Trends
    async def _tool_query_temporal_trends(
        self,
        user_id: str,
        metric: str = "all",
        time_window: str = "7d"
    ) -> Dict[str, Any]:
        """
        Tool 5: Query InfluxDB for conversation quality metrics.
        
        Migrated from src/intelligence/tool_executor.py (placeholder)
        """
        if not self.influx:
            logger.warning(
                "query_temporal_trends | InfluxDB not available | "
                "User: %s | Metric: %s",
                user_id,
                metric
            )
            return {
                "user_id": user_id,
                "metric": metric,
                "time_window": time_window,
                "data_points": [],
                "summary": {},
                "note": "InfluxDB client not available"
            }
        
        # TODO: Implement InfluxDB queries
        logger.warning(
            "query_temporal_trends NOT FULLY IMPLEMENTED | "
            "User: %s | Metric: %s | Window: %s",
            user_id,
            metric,
            time_window
        )
        
        return {
            "user_id": user_id,
            "metric": metric,
            "time_window": time_window,
            "data_points": [],
            "summary": {},
            "note": "Full implementation pending - requires InfluxDB schema analysis"
        }


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
