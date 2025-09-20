#!/usr/bin/env python3
"""
Advanced Intent Classification and Fact Extraction System

Uses the existing NLP infrastructure (spaCy, embeddings, topic extractor) 
to intelligently classify user intents and extract factual information.

This replaces manual pattern matching with semantic understanding.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import spacy
from datetime import datetime

# Import existing infrastructure
from src.analysis.advanced_topic_extractor import AdvancedTopicExtractor


logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """User intent classifications"""
    INTRODUCING_SELF = "introducing_self"          # "My name is...", "I am..."
    SHARING_FACT = "sharing_fact"                  # "I have a pet", "I live in..."
    ASKING_QUESTION = "asking_question"            # "What's my name?", "Do you remember...?"
    CORRECTING_INFO = "correcting_info"            # "Actually, my name is...", "No, I meant..."
    GREETING = "greeting"                          # "Hi", "Hello"
    SEEKING_HELP = "seeking_help"                  # "Can you help me...", "I need..."
    EXPRESSING_PREFERENCE = "expressing_preference" # "I like...", "I prefer..."
    GENERAL_CONVERSATION = "general_conversation"   # Everything else


@dataclass
class ExtractedFact:
    """Represents a fact extracted from user message"""
    subject: str           # What the fact is about ("name", "pet", "location")
    predicate: str         # The relationship ("is", "has", "lives in")
    object: str            # The value ("Mark", "dog named Buddy", "New York")
    confidence: float      # How confident we are (0-1)
    source_text: str       # Original text that contained this fact
    intent: UserIntent     # The intent that led to this fact


@dataclass
class IntentClassificationResult:
    """Result of intent classification"""
    primary_intent: UserIntent
    confidence: float
    extracted_facts: List[ExtractedFact]
    entities: List[Dict[str, Any]]
    key_phrases: List[str]
    is_correction: bool
    requires_memory_lookup: bool


class AdvancedIntentClassifier:
    """
    Advanced intent classification using existing NLP infrastructure
    
    This system uses semantic understanding instead of pattern matching
    to classify user intents and extract facts.
    """
    
    def __init__(self):
        self.nlp = None
        self.topic_extractor = None
        self._initialized = False
        
        # Semantic intent patterns (using embeddings would be even better)
        self.intent_keywords = {
            UserIntent.INTRODUCING_SELF: {
                "patterns": ["my name is", "i am", "i'm", "call me", "i am called"],
                "entities": ["PERSON"],
                "pos_patterns": ["PRON ADJ NOUN", "PRON VERB NOUN"]
            },
            UserIntent.SHARING_FACT: {
                "patterns": ["i have", "i own", "i live", "i work", "my", "i like", "i love", "i prefer"],
                "entities": ["PERSON", "ORG", "GPE", "PRODUCT"],
                "pos_patterns": ["PRON VERB", "PRON ADJ"]
            },
            UserIntent.ASKING_QUESTION: {
                "patterns": ["what", "who", "when", "where", "why", "how", "do you", "can you", "?"],
                "entities": [],
                "pos_patterns": ["ADV", "PRON"]
            },
            UserIntent.CORRECTING_INFO: {
                "patterns": ["actually", "no", "not", "wrong", "correction", "i meant", "i mean"],
                "entities": [],
                "pos_patterns": ["ADV", "INTJ"]
            }
        }
    
    async def initialize(self):
        """Initialize the NLP components"""
        if self._initialized:
            return
            
        try:
            # Load spaCy model
            try:
                self.nlp = spacy.load("en_core_web_lg")
            except OSError:
                logger.warning("en_core_web_lg not found, falling back to en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
            
            # Initialize topic extractor
            self.topic_extractor = AdvancedTopicExtractor()
            await self.topic_extractor.initialize()
            
            self._initialized = True
            logger.info("✅ Advanced Intent Classifier initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Advanced Intent Classifier: {e}")
            raise
    
    async def classify_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> IntentClassificationResult:
        """
        Classify user intent and extract facts using advanced NLP
        
        Args:
            message: User message to analyze
            context: Optional conversation context
            
        Returns:
            IntentClassificationResult with intent, facts, and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use advanced topic extraction for deep analysis
            topic_analysis = await self.topic_extractor.extract_topics_enhanced(message)
            
            # Process with spaCy for linguistic features
            doc = self.nlp(message)
            
            # Classify primary intent
            primary_intent, intent_confidence = self._classify_primary_intent(
                message, doc, topic_analysis
            )
            
            # Extract facts based on intent and entities
            extracted_facts = await self._extract_facts_semantic(
                message, doc, topic_analysis, primary_intent
            )
            
            # Determine if this is a correction
            is_correction = self._detect_correction(message, doc)
            
            # Check if we need memory lookup
            requires_memory_lookup = primary_intent in [
                UserIntent.ASKING_QUESTION, 
                UserIntent.CORRECTING_INFO
            ]
            
            return IntentClassificationResult(
                primary_intent=primary_intent,
                confidence=intent_confidence,
                extracted_facts=extracted_facts,
                entities=topic_analysis.get("entities", []),
                key_phrases=topic_analysis.get("key_phrases", []),
                is_correction=is_correction,
                requires_memory_lookup=requires_memory_lookup
            )
            
        except Exception as e:
            logger.error(f"Error in intent classification: {e}")
            # Fallback to basic classification
            return IntentClassificationResult(
                primary_intent=UserIntent.GENERAL_CONVERSATION,
                confidence=0.5,
                extracted_facts=[],
                entities=[],
                key_phrases=[],
                is_correction=False,
                requires_memory_lookup=False
            )
    
    def _classify_primary_intent(self, message: str, doc, topic_analysis: Dict[str, Any]) -> tuple[UserIntent, float]:
        """Classify the primary intent using multiple signals"""
        message_lower = message.lower()
        
        # Check for questions first (strongest signal)
        if (message.endswith("?") or 
            any(token.text.lower() in ["what", "who", "when", "where", "why", "how"] 
                for token in doc if token.pos_ in ["ADV", "PRON"])):
            return UserIntent.ASKING_QUESTION, 0.9
        
        # Check for corrections
        correction_signals = ["actually", "no", "not", "wrong", "i meant", "correction"]
        if any(signal in message_lower for signal in correction_signals):
            return UserIntent.CORRECTING_INFO, 0.85
        
        # Check for self-introduction using entities and patterns
        entities = topic_analysis.get("entities", [])
        person_entities = [e for e in entities if e.get("type") == "PERSON"]
        
        if (any(pattern in message_lower for pattern in ["my name is", "i am", "call me"]) and 
            person_entities):
            return UserIntent.INTRODUCING_SELF, 0.9
        
        # Check for fact sharing using possession/relationship patterns
        fact_patterns = ["i have", "i own", "i live", "i work", "my"]
        if any(pattern in message_lower for pattern in fact_patterns):
            return UserIntent.SHARING_FACT, 0.8
        
        # Check for preferences
        pref_patterns = ["i like", "i love", "i prefer", "i enjoy"]
        if any(pattern in message_lower for pattern in pref_patterns):
            return UserIntent.EXPRESSING_PREFERENCE, 0.75
        
        # Greeting detection
        greeting_tokens = [token.text.lower() for token in doc]
        if any(greeting in greeting_tokens for greeting in ["hi", "hello", "hey", "greetings"]):
            return UserIntent.GREETING, 0.85
        
        # Help seeking
        help_patterns = ["help", "can you", "could you", "assist", "support"]
        if any(pattern in message_lower for pattern in help_patterns):
            return UserIntent.SEEKING_HELP, 0.8
        
        return UserIntent.GENERAL_CONVERSATION, 0.6
    
    async def _extract_facts_semantic(
        self, message: str, doc, topic_analysis: Dict[str, Any], intent: UserIntent
    ) -> List[ExtractedFact]:
        """Extract facts using semantic understanding instead of patterns"""
        facts = []
        
        if intent not in [UserIntent.INTRODUCING_SELF, UserIntent.SHARING_FACT, UserIntent.EXPRESSING_PREFERENCE]:
            return facts
        
        entities = topic_analysis.get("entities", [])
        
        # Extract name facts
        if intent == UserIntent.INTRODUCING_SELF:
            person_entities = [e for e in entities if e.get("type") == "PERSON"]
            for entity in person_entities:
                facts.append(ExtractedFact(
                    subject="name",
                    predicate="is",
                    object=entity["text"],
                    confidence=entity.get("confidence", 0.8),
                    source_text=message,
                    intent=intent
                ))
        
        # Extract other facts using dependency parsing
        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                # Find subject and object relationships
                subjects = [child for child in token.children if child.dep_ in ["nsubj", "nsubjpass"]]
                objects = [child for child in token.children if child.dep_ in ["dobj", "pobj", "attr"]]
                
                if subjects and objects:
                    subject_text = " ".join([t.text for t in subjects])
                    object_text = " ".join([t.text for t in objects])
                    
                    # Only extract if subject refers to the user
                    if any(pronoun in subject_text.lower() for pronoun in ["i", "my", "me"]):
                        facts.append(ExtractedFact(
                            subject=self._normalize_subject(token.lemma_),
                            predicate=token.lemma_,
                            object=object_text,
                            confidence=0.7,
                            source_text=message,
                            intent=intent
                        ))
        
        return facts
    
    def _normalize_subject(self, verb: str) -> str:
        """Normalize verb to subject category"""
        verb_to_subject = {
            "have": "possession",
            "own": "possession", 
            "live": "location",
            "work": "occupation",
            "like": "preference",
            "love": "preference",
            "prefer": "preference",
            "be": "attribute"
        }
        return verb_to_subject.get(verb, "general")
    
    def _detect_correction(self, message: str, doc) -> bool:
        """Detect if this message is correcting previous information"""
        correction_signals = ["actually", "no", "not", "wrong", "i meant", "correction"]
        return any(signal in message.lower() for signal in correction_signals)


# Integration function for the event handler
async def classify_user_intent(message: str, context: Optional[Dict[str, Any]] = None) -> IntentClassificationResult:
    """
    Convenience function for intent classification
    
    Usage in event handler:
        intent_result = await classify_user_intent(message.content)
        if intent_result.extracted_facts:
            # Store facts in memory
        if intent_result.requires_memory_lookup:
            # Retrieve relevant memories
    """
    classifier = AdvancedIntentClassifier()
    return await classifier.classify_intent(message, context)


# Example usage and testing
async def test_intent_classification():
    """Test the intent classification system"""
    test_messages = [
        "My name is Mark",
        "What's my name?",
        "I have a dog named Buddy",
        "Actually, my name is Marcus, not Mark",
        "I live in San Francisco",
        "Do you remember where I live?",
        "I like pizza",
        "Can you help me with something?"
    ]
    
    classifier = AdvancedIntentClassifier()
    
    for message in test_messages:
        print(f"\nTesting: '{message}'")
        result = await classifier.classify_intent(message)
        print(f"Intent: {result.primary_intent.value} (confidence: {result.confidence:.2f})")
        if result.extracted_facts:
            for fact in result.extracted_facts:
                print(f"  Fact: {fact.subject} {fact.predicate} {fact.object}")
        if result.entities:
            print(f"  Entities: {[e['text'] for e in result.entities]}")


if __name__ == "__main__":
    asyncio.run(test_intent_classification())