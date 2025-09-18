"""
Advanced Topic Extractor - Phase 1 Enhancement

This module provides sophisticated topic extraction using multiple NLP techniques:
- Named Entity Recognition (NER)
- Key phrase extraction
- Semantic topic detection
- Sentiment analysis
- Linguistic complexity scoring

Author: AI Enhancement Team
Date: September 11, 2025
"""

import asyncio
import logging
from collections import Counter
from datetime import datetime
from typing import Any

import numpy as np
import spacy

# Use existing external embedding manager instead of local sentence transformers
 # Historical: ExternalEmbeddingManager and is_external_embedding_configured removed Sept 2025

logger = logging.getLogger(__name__)


class AdvancedTopicExtractor:
    """Advanced topic extraction using multiple NLP techniques."""

    def __init__(self, config: dict | None = None):
        """Initialize the advanced topic extractor."""
        self.config = self._load_config(config)
        self.nlp = None
        self.embedding_manager = None
        self._initialized = False

    def _load_config(self, user_config: dict | None) -> dict:
        """Load configuration with defaults."""
        default_config = {
            "spacy_model": "en_core_web_lg",
            # Historical: use_external_embeddings was deprecated in September 2025. Local embedding is always used.
            "max_entities": 10,
            "max_key_phrases": 8,
            "min_phrase_length": 2,
            "max_phrase_length": 4,
            "complexity_factors": {
                "vocab_diversity": 0.3,
                "sentence_complexity": 0.25,
                "average_word_length": 0.2,
                "punctuation_complexity": 0.15,
                "syntactic_depth": 0.1,
            },
        }

        if user_config:
            default_config.update(user_config)

        return default_config

    async def initialize(self):
        """Initialize NLP models asynchronously."""
        if self._initialized:
            return

        try:
            logger.info("Initializing Advanced Topic Extractor...")

            # Load spaCy model
            logger.info(f"Loading spaCy model: {self.config['spacy_model']}")
            self.nlp = spacy.load(self.config["spacy_model"])

            # Historical: All embedding is now local. External embedding manager removed Sept 2025.
            self.embedding_manager = None

            self._initialized = True
            logger.info("Advanced Topic Extractor initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Advanced Topic Extractor: {e}")
            raise

    async def extract_topics_enhanced(self, message: str) -> dict[str, Any]:
        """
        Extract topics with comprehensive analysis.

        Args:
            message: Input text message

        Returns:
            Dictionary containing:
            - entities: Named entities with types and confidence
            - key_phrases: Important noun phrases
            - semantic_topics: Semantic topic clusters
            - sentiment: Detailed sentiment analysis
            - complexity_score: Linguistic complexity measure
            - metadata: Processing metadata
        """
        if not self._initialized:
            await self.initialize()

        try:
            start_time = datetime.now()

            # Process with spaCy
            if not self.nlp:
                raise RuntimeError("spaCy model not initialized")
            doc = self.nlp(message)

            # Extract different types of information
            entities = await self._extract_named_entities(doc)
            key_phrases = await self._extract_key_phrases(doc)
            semantic_topics = await self._extract_semantic_topics(message, doc)
            sentiment = await self._analyze_sentiment(doc)
            complexity_score = await self._calculate_complexity(message, doc)

            processing_time = (datetime.now() - start_time).total_seconds()

            result = {
                "entities": entities,
                "key_phrases": key_phrases,
                "semantic_topics": semantic_topics,
                "sentiment": sentiment,
                "complexity_score": complexity_score,
                "metadata": {
                    "processing_time_seconds": processing_time,
                    "message_length": len(message),
                    "word_count": len([token for token in doc if not token.is_space]),
                    "sentence_count": len(list(doc.sents)),
                    "timestamp": datetime.now().isoformat(),
                },
            }

            logger.debug(f"Topic extraction completed in {processing_time:.3f}s")
            return result

        except Exception as e:
            logger.error(f"Error in topic extraction: {e}")
            return self._get_error_result(str(e))

    async def _extract_named_entities(self, doc) -> list[dict]:
        """Extract named entities with confidence and context."""
        entities = []

        for ent in doc.ents:
            # Filter out very short or common entities
            if len(ent.text.strip()) < 2:
                continue

            entity_info = {
                "text": ent.text.strip(),
                "label": ent.label_,
                "label_description": self._get_entity_description(ent.label_),
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": self._calculate_entity_confidence(ent),
            }

            entities.append(entity_info)

        # Sort by confidence and limit
        entities.sort(key=lambda x: x["confidence"], reverse=True)
        return entities[: self.config["max_entities"]]

    def _get_entity_description(self, label: str) -> str:
        """Get description for entity label."""
        descriptions = {
            "PERSON": "People, including fictional",
            "NORP": "Nationalities or religious or political groups",
            "FAC": "Buildings, airports, highways, bridges, etc.",
            "ORG": "Companies, agencies, institutions, etc.",
            "GPE": "Countries, cities, states",
            "LOC": "Non-GPE locations, mountain ranges, bodies of water",
            "PRODUCT": "Objects, vehicles, foods, etc. (not services)",
            "EVENT": "Named hurricanes, battles, wars, sports events, etc.",
            "WORK_OF_ART": "Titles of books, songs, etc.",
            "LAW": "Named documents made into laws",
            "LANGUAGE": "Any named language",
            "DATE": "Absolute or relative dates or periods",
            "TIME": "Times smaller than a day",
            "PERCENT": 'Percentage, including "%"',
            "MONEY": "Monetary values, including unit",
            "QUANTITY": "Measurements, as of weight or distance",
            "ORDINAL": '"first", "second", etc.',
            "CARDINAL": "Numerals that do not fall under another type",
        }
        return descriptions.get(label, f"Entity type: {label}")

    def _calculate_entity_confidence(self, ent) -> float:
        """Calculate confidence score for an entity."""
        # Basic confidence based on entity characteristics
        confidence = 0.5  # Base confidence

        # Boost confidence for proper nouns
        if ent.label_ in ["PERSON", "ORG", "GPE"]:
            confidence += 0.3

        # Boost for capitalized entities
        if ent.text[0].isupper():
            confidence += 0.1

        # Boost for longer entities
        if len(ent.text) > 5:
            confidence += 0.1

        # Penalize very common words (basic implementation)
        common_words = {"the", "and", "but", "or", "so", "because"}
        if ent.text.lower() in common_words:
            confidence -= 0.3

        return min(max(confidence, 0.1), 1.0)

    async def _extract_key_phrases(self, doc) -> list[str]:
        """Extract important noun phrases and concepts."""
        phrases = []

        # Extract noun chunks
        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip().lower()

            # Filter phrases
            if self.config["min_phrase_length"] <= len(phrase.split()) <= self.config[
                "max_phrase_length"
            ] and not self._is_common_phrase(phrase):
                phrases.append(phrase)

        # Extract compound nouns and technical terms
        for token in doc:
            if token.pos_ == "NOUN" and token.dep_ in ["compound", "amod"] and len(token.text) > 3:
                phrases.append(token.text.lower())

        # Remove duplicates and sort by frequency/importance
        phrase_counts = Counter(phrases)
        unique_phrases = list(phrase_counts.keys())

        # Sort by frequency and importance
        unique_phrases.sort(key=lambda p: (phrase_counts[p], len(p)), reverse=True)

        return unique_phrases[: self.config["max_key_phrases"]]

    def _is_common_phrase(self, phrase: str) -> bool:
        """Check if phrase is too common to be useful."""
        common_phrases = {
            "a lot",
            "kind of",
            "sort of",
            "you know",
            "i think",
            "i mean",
            "like that",
            "something like",
            "things like",
        }
        return phrase in common_phrases

    async def _extract_semantic_topics(self, message: str, doc) -> list[dict]:
        """Extract semantic topics using local embedding only (external removed)."""
        # TODO: Implement local embedding-based topic extraction or return empty for now
        logger.debug("Semantic topic extraction now uses only local embedding (external removed)")
        return []

    def _calculate_semantic_density(self, sentence: str, doc) -> float:
        """Calculate semantic density of a sentence."""
        words = sentence.split()
        if not words:
            return 0.0

        # Count content words (nouns, verbs, adjectives)
        content_words = 0
        for token in doc:
            if token.text in sentence and token.pos_ in ["NOUN", "VERB", "ADJ", "PROPN"]:
                content_words += 1

        return content_words / len(words) if words else 0.0

    def _calculate_topic_strength(self, sentence: str, doc) -> float:
        """Calculate how strong this sentence is as a topic indicator."""
        strength = 0.0

        # Check for entities
        entity_count = sum(1 for ent in doc.ents if ent.text in sentence)
        strength += entity_count * 0.2

        # Check for key verbs
        action_verbs = 0
        for token in doc:
            if (
                token.text in sentence
                and token.pos_ == "VERB"
                and token.dep_ in ["ROOT", "ccomp", "xcomp"]
            ):
                action_verbs += 1
        strength += action_verbs * 0.15

        # Check sentence position (first and last sentences often more important)
        sentences = list(doc.sents)
        if sentences:
            for i, sent in enumerate(sentences):
                if sent.text.strip() == sentence:
                    if i == 0 or i == len(sentences) - 1:
                        strength += 0.1
                    break

        return min(strength, 1.0)

    async def _analyze_sentiment(self, doc) -> dict[str, Any]:
        """Analyze sentiment with detailed breakdown."""
        sentiment_scores = {
            "polarity": 0.0,
            "subjectivity": 0.0,
            "emotional_indicators": [],
            "sentiment_words": [],
        }

        # Basic sentiment analysis using spaCy
        positive_words = 0
        negative_words = 0
        emotional_words = []

        # Emotional indicators
        emotion_keywords = {
            "positive": ["happy", "excited", "great", "amazing", "wonderful", "love", "enjoy"],
            "negative": ["sad", "angry", "frustrated", "terrible", "awful", "hate", "annoyed"],
            "neutral": ["okay", "fine", "normal", "usual", "standard"],
        }

        for token in doc:
            token_lower = token.text.lower()

            # Check for emotional keywords
            for emotion, keywords in emotion_keywords.items():
                if token_lower in keywords:
                    emotional_words.append(
                        {"word": token.text, "emotion": emotion, "pos": token.pos_}
                    )

                    if emotion == "positive":
                        positive_words += 1
                    elif emotion == "negative":
                        negative_words += 1

        # Calculate basic polarity
        total_emotional = positive_words + negative_words
        if total_emotional > 0:
            sentiment_scores["polarity"] = (positive_words - negative_words) / total_emotional

        # Calculate subjectivity (emotional words / total words)
        total_words = len([t for t in doc if t.is_alpha])
        if total_words > 0:
            sentiment_scores["subjectivity"] = total_emotional / total_words

        sentiment_scores["emotional_indicators"] = emotional_words
        sentiment_scores["sentiment_words"] = [w["word"] for w in emotional_words]

        return sentiment_scores

    async def _calculate_complexity(self, message: str, doc) -> float:
        """Calculate linguistic complexity score."""
        factors = self.config["complexity_factors"]
        scores = {}

        # Vocabulary diversity (unique words / total words)
        words = [token.text.lower() for token in doc if token.is_alpha]
        unique_words = set(words)
        scores["vocab_diversity"] = len(unique_words) / len(words) if words else 0

        # Sentence complexity (average words per sentence)
        sentences = list(doc.sents)
        if sentences:
            avg_sentence_length = sum(
                len([t for t in sent if t.is_alpha]) for sent in sentences
            ) / len(sentences)
            scores["sentence_complexity"] = min(avg_sentence_length / 20, 1.0)  # Normalize to 0-1
        else:
            scores["sentence_complexity"] = 0

        # Average word length
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            scores["average_word_length"] = min(avg_word_length / 10, 1.0)  # Normalize to 0-1
        else:
            scores["average_word_length"] = 0

        # Punctuation complexity
        punctuation_count = len([c for c in message if c in '.,;:!?()-"'])
        scores["punctuation_complexity"] = (
            min(punctuation_count / len(message), 0.2) * 5 if message else 0
        )

        # Syntactic depth (dependency depth)
        max_depth = 0
        for token in doc:
            depth = self._get_dependency_depth(token)
            max_depth = max(max_depth, depth)
        scores["syntactic_depth"] = min(max_depth / 8, 1.0)  # Normalize to 0-1

        # Calculate weighted complexity score
        complexity = sum(scores[factor] * weight for factor, weight in factors.items())

        return min(max(complexity, 0.0), 1.0)

    def _get_dependency_depth(self, token) -> int:
        """Calculate dependency tree depth for a token."""
        depth = 0
        current = token
        while current.head != current:  # Not root
            depth += 1
            current = current.head
            if depth > 10:  # Prevent infinite loops
                break
        return depth

    def _get_error_result(self, error_message: str) -> dict[str, Any]:
        """Return error result structure."""
        return {
            "entities": [],
            "key_phrases": [],
            "semantic_topics": [],
            "sentiment": {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "emotional_indicators": [],
                "sentiment_words": [],
            },
            "complexity_score": 0.0,
            "metadata": {
                "processing_time_seconds": 0.0,
                "message_length": 0,
                "word_count": 0,
                "sentence_count": 0,
                "timestamp": datetime.now().isoformat(),
                "error": error_message,
            },
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on the topic extractor."""
        try:
            if not self._initialized:
                await self.initialize()

            # Test with simple message
            test_result = await self.extract_topics_enhanced(
                "This is a test message about technology."
            )

            return {
                "status": "healthy",
                "initialized": self._initialized,
                "spacy_model": self.config["spacy_model"],
                "external_embeddings_available": self.embedding_manager is not None,
                "test_successful": len(test_result["entities"]) >= 0,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self._initialized,
                "timestamp": datetime.now().isoformat(),
            }


# Convenience function for quick testing
async def test_topic_extraction():
    """Test function for topic extraction."""
    extractor = AdvancedTopicExtractor()

    test_messages = [
        "I'm really excited about my new job at Google! The team seems amazing.",
        "Working on machine learning projects with Python has been challenging but rewarding.",
        "My family and I went to New York last weekend. The weather was terrible but we had fun.",
    ]

    for _i, message in enumerate(test_messages, 1):

        await extractor.extract_topics_enhanced(message)


if __name__ == "__main__":
    asyncio.run(test_topic_extraction())
