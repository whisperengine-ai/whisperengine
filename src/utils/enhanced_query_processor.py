"""
Enhanced Query Processing for Memory Retrieval

This module provides optimized query processing for semantic search
to improve memory retrieval relevance and reduce the "forgetting" issue.
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchQuery:
    """Represents an optimized search query"""

    query: str
    weight: float = 1.0
    query_type: str = "general"
    confidence: float = 1.0


@dataclass
class QueryResult:
    """Result of query optimization"""

    primary_queries: list[SearchQuery]
    fallback_query: str
    extracted_entities: list[str]
    intent_classification: str
    emotional_context: str | None = None


class EnhancedQueryProcessor:
    """
    Processes user messages to create optimized search queries for memory retrieval
    """

    def __init__(self):
        # Stop words to filter out
        self.stop_words = {
            "i",
            "me",
            "my",
            "mine",
            "myself",
            "am",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "if",
            "then",
            "else",
            "when",
            "where",
            "how",
            "what",
            "who",
            "why",
            "which",
            "this",
            "that",
            "these",
            "those",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "up",
            "down",
            "out",
            "off",
            "over",
            "under",
            "again",
            "further",
            "do",
            "does",
            "did",
            "doing",
            "will",
            "would",
            "should",
            "could",
            "can",
            "may",
            "might",
            "must",
            "shall",
            "have",
            "has",
            "had",
            "having",
            "today",
            "yesterday",
            "tomorrow",
            "tell",
            "help",
            "please",
            "thanks",
            "thank",
            "you",
            "your",
            "yours",
            "yourself",
            "he",
            "him",
            "his",
            "himself",
            "she",
            "her",
            "hers",
            "herself",
            "it",
            "its",
            "itself",
            "we",
            "us",
            "our",
            "ours",
            "ourselves",
            "they",
            "them",
            "their",
            "theirs",
            "themselves",
            "just",
            "really",
            "very",
            "too",
            "now",
            "here",
            "there",
            "some",
            "any",
            "more",
            "most",
            "other",
            "such",
            "only",
            "own",
            "same",
            "so",
            "than",
            "well",
        }

        # Question words to identify interrogative intent
        self.question_words = {"what", "where", "when", "why", "who", "how", "which", "whose"}

        # Emotional indicators
        self.emotion_indicators = {
            "positive": [
                "happy",
                "excited",
                "joy",
                "love",
                "great",
                "awesome",
                "amazing",
                "fantastic",
            ],
            "negative": [
                "sad",
                "angry",
                "frustrated",
                "annoyed",
                "upset",
                "worried",
                "stressed",
                "anxious",
            ],
            "neutral": ["thinking", "wondering", "considering", "curious", "interested"],
        }

        # Common topic categories
        self.topic_categories = {
            "work": ["work", "job", "career", "office", "boss", "colleague", "meeting", "project"],
            "health": ["health", "doctor", "medicine", "exercise", "sick", "fitness", "diet"],
            "family": ["family", "mom", "dad", "parent", "child", "sibling", "brother", "sister"],
            "relationships": [
                "friend",
                "relationship",
                "dating",
                "partner",
                "boyfriend",
                "girlfriend",
            ],
            "hobbies": [
                "hobby",
                "music",
                "guitar",
                "piano",
                "art",
                "drawing",
                "painting",
                "reading",
            ],
            "cooking": [
                "cook",
                "cooking",
                "recipe",
                "food",
                "meal",
                "kitchen",
                "baking",
                "restaurant",
            ],
            "technology": [
                "computer",
                "software",
                "app",
                "internet",
                "tech",
                "programming",
                "code",
            ],
            "education": ["school", "university", "study", "learn", "course", "class", "homework"],
            "pets": ["dog", "cat", "pet", "animal", "puppy", "kitten"],
            "travel": ["travel", "trip", "vacation", "visit", "journey", "flight", "hotel"],
        }

    def process_message(self, message: str) -> QueryResult:
        """
        Process a user message and return optimized search queries

        Args:
            message: Raw user message

        Returns:
            QueryResult with optimized queries and metadata
        """
        # Clean and normalize the message
        cleaned_message = self._clean_message(message)

        # Extract key entities and terms
        entities = self._extract_entities(cleaned_message)

        # Classify intent
        intent = self._classify_intent(cleaned_message)

        # Extract emotional context
        emotion = self._extract_emotion(cleaned_message)

        # Generate primary queries
        primary_queries = self._generate_primary_queries(entities, intent, emotion, cleaned_message)

        # Create fallback query (cleaned version of original)
        fallback_query = self._create_fallback_query(cleaned_message)

        return QueryResult(
            primary_queries=primary_queries,
            fallback_query=fallback_query,
            extracted_entities=entities,
            intent_classification=intent,
            emotional_context=emotion,
        )

    def _clean_message(self, message: str) -> str:
        """Clean and normalize the message"""
        # Convert to lowercase
        cleaned = message.lower().strip()

        # Remove punctuation except apostrophes
        cleaned = re.sub(r"[^\w\s\']", " ", cleaned)

        # Remove extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned

    def _extract_entities(self, message: str) -> list[str]:
        """Extract key entities and important terms"""
        words = message.split()

        # Remove stop words
        filtered_words = [word for word in words if word not in self.stop_words and len(word) > 2]

        # Group consecutive important words (simple noun phrase detection)
        entities = []
        current_phrase = []

        for word in filtered_words:
            # If it's a significant word, add to current phrase
            if self._is_significant_word(word):
                current_phrase.append(word)
            else:
                # End current phrase if it exists
                if current_phrase:
                    if len(current_phrase) == 1:
                        entities.append(current_phrase[0])
                    else:
                        entities.append(" ".join(current_phrase))
                    current_phrase = []

                # Add single significant word
                if word not in self.stop_words:
                    entities.append(word)

        # Don't forget the last phrase
        if current_phrase:
            if len(current_phrase) == 1:
                entities.append(current_phrase[0])
            else:
                entities.append(" ".join(current_phrase))

        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)

        return unique_entities[:8]  # Limit to top 8 entities

    def _is_significant_word(self, word: str) -> bool:
        """Check if a word is significant for entity extraction"""
        # Nouns are generally more significant
        # This is a simple heuristic - in practice, you'd use POS tagging
        return len(word) > 3 and word not in self.stop_words and word not in self.question_words

    def _classify_intent(self, message: str) -> str:
        """Classify the intent of the message"""
        words = set(message.split())

        # Check for question indicators
        if any(qword in words for qword in self.question_words):
            return "question"

        # Check for help/advice requests
        if any(word in message for word in ["help", "advice", "suggest", "recommend"]):
            return "help_request"

        # Check for sharing/storytelling
        if any(word in message for word in ["went", "did", "happened", "yesterday", "today"]):
            return "sharing"

        # Check for problem statements
        if any(word in message for word in ["problem", "issue", "trouble", "difficulty", "stuck"]):
            return "problem"

        # Check for preferences/opinions
        if any(
            word in message
            for word in ["love", "hate", "like", "dislike", "prefer", "think", "feel"]
        ):
            return "preference"

        return "general"

    def _extract_emotion(self, message: str) -> str | None:
        """Extract emotional context from the message"""
        words = set(message.split())

        for emotion_type, indicators in self.emotion_indicators.items():
            if any(indicator in words for indicator in indicators):
                return emotion_type

        return None

    def _generate_primary_queries(
        self, entities: list[str], intent: str, emotion: str | None, message: str
    ) -> list[SearchQuery]:
        """Generate primary search queries based on extracted information"""
        queries = []

        # 1. Entity-based query (highest weight)
        if entities:
            entity_query = " ".join(entities[:4])  # Top 4 entities
            queries.append(
                SearchQuery(query=entity_query, weight=1.0, query_type="entities", confidence=0.9)
            )

        # 2. Topic-based query
        topic_terms = self._extract_topic_terms(entities, message)
        if topic_terms:
            topic_query = " ".join(topic_terms)
            queries.append(
                SearchQuery(query=topic_query, weight=0.8, query_type="topics", confidence=0.8)
            )

        # 3. Intent-specific query
        if intent != "general" and entities:
            intent_query = f"{intent} {' '.join(entities[:2])}"
            queries.append(
                SearchQuery(query=intent_query, weight=0.7, query_type="intent", confidence=0.7)
            )

        # 4. Emotion-based query (if emotional content detected)
        if emotion and entities:
            emotion_query = f"{emotion} {' '.join(entities[:2])}"
            queries.append(
                SearchQuery(query=emotion_query, weight=0.6, query_type="emotion", confidence=0.6)
            )

        # 5. Contextual combinations
        if len(entities) >= 2:
            # Try combinations of entities
            for i in range(min(3, len(entities) - 1)):
                combo_query = f"{entities[i]} {entities[i+1]}"
                queries.append(
                    SearchQuery(
                        query=combo_query, weight=0.5, query_type="combination", confidence=0.5
                    )
                )

        return queries[:5]  # Limit to top 5 queries

    def _extract_topic_terms(self, entities: list[str], message: str) -> list[str]:
        """Extract topic-specific terms"""
        topic_terms = []

        # Check entities against topic categories
        for entity in entities:
            for category, keywords in self.topic_categories.items():
                if entity in keywords:
                    topic_terms.extend([entity, category])
                    break

        # Add related terms found in message
        message_words = set(message.split())
        for category, keywords in self.topic_categories.items():
            if any(keyword in message_words for keyword in keywords):
                # Add the most relevant keywords from this category
                relevant_keywords = [kw for kw in keywords if kw in message_words]
                topic_terms.extend(relevant_keywords[:2])  # Limit to 2 per category

        # Remove duplicates
        return list(dict.fromkeys(topic_terms))[:6]  # Limit to 6 terms

    def _create_fallback_query(self, cleaned_message: str) -> str:
        """Create a fallback query by cleaning the original message"""
        words = cleaned_message.split()

        # Remove stop words and question words
        filtered_words = [
            word
            for word in words
            if word not in self.stop_words and word not in self.question_words and len(word) > 2
        ]

        # Limit length to avoid noise
        return " ".join(filtered_words[:8])

    def get_search_strategies(self, query_result: QueryResult) -> list[tuple[str, float]]:
        """
        Get search strategies as (query, weight) tuples for use in memory retrieval

        Args:
            query_result: Result from process_message()

        Returns:
            List of (query_string, weight) tuples ordered by priority
        """
        strategies = []

        # Add primary queries
        for query in query_result.primary_queries:
            strategies.append((query.query, query.weight))

        # Add fallback query with lower weight
        strategies.append((query_result.fallback_query, 0.3))

        # Sort by weight (highest first)
        strategies.sort(key=lambda x: x[1], reverse=True)

        return strategies


# Example usage function for testing
def test_query_processor():
    """Test the query processor with example messages"""
    processor = EnhancedQueryProcessor()

    test_messages = [
        "I love playing guitar and music, but I'm having trouble with barre chords",
        "I'm feeling really stressed about work today and need some advice",
        "Can you help me understand how to cook better pasta dishes?",
        "My dog has been acting weird lately and won't eat his food",
        "I went to the park yesterday with my friends and had a great time",
    ]

    for _i, message in enumerate(test_messages, 1):

        result = processor.process_message(message)

        for _j, _query in enumerate(result.primary_queries, 1):
            pass

        strategies = processor.get_search_strategies(result)
        for _j, (_query, _weight) in enumerate(strategies, 1):
            pass


if __name__ == "__main__":
    test_query_processor()
