"""
LLM-Powered Query Breakdown for Enhanced Memory Search

This module uses LLM analysis to intelligently break down user messages
into optimized search queries for better memory retrieval.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMSearchQuery:
    """Represents an LLM-optimized search query"""

    query: str
    weight: float = 1.0
    query_type: str = "general"  # "entity", "topic", "context", "emotion", "intent"
    confidence: float = 1.0
    reasoning: str = ""


@dataclass
class LLMQueryBreakdown:
    """Result of LLM query breakdown"""

    primary_queries: list[LLMSearchQuery]
    fallback_query: str
    extracted_entities: list[str]
    main_topics: list[str]
    intent_classification: str
    emotional_context: str | None = None
    search_strategy: str = "standard"  # "broad", "specific", "contextual"


class LLMQueryProcessor:
    """
    Uses LLM to intelligently break down user messages into optimized search queries
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def analyze_message_for_search(
        self, message: str, conversation_context: str | None = None
    ) -> LLMQueryBreakdown:
        """
        Use LLM to break down a user message into optimized search queries

        Args:
            message: The user message to analyze
            conversation_context: Optional context from recent conversation

        Returns:
            LLMQueryBreakdown with optimized search queries
        """
        try:
            # Prepare context if available
            context_prompt = ""
            if conversation_context:
                context_prompt = f"\nRecent conversation context:\n{conversation_context}\n"

            response = await self._call_llm_for_query_breakdown(message, context_prompt)

            if not response or "queries" not in response:
                # Fallback to simple processing
                return self._create_fallback_breakdown(message)

            # Parse LLM response into structured breakdown
            return self._parse_llm_response(response, message)

        except Exception as e:
            logger.warning(f"LLM query breakdown failed, using fallback: {e}")
            return self._create_fallback_breakdown(message)

    async def _call_llm_for_query_breakdown(
        self, message: str, context_prompt: str
    ) -> dict[str, Any]:
        """Call LLM to analyze message and generate search queries"""

        system_prompt = """You are an expert at analyzing user messages to create optimal memory search queries. Your goal is to break down user messages into focused search terms that will find relevant past conversations and memories.

TASK: Analyze the user's message and create 2-4 focused search queries that would best retrieve relevant memories from past conversations.

GUIDELINES:
1. Extract key entities (people, places, objects, concepts)
2. Identify main topics and themes
3. Consider emotional context and intent
4. Create specific, focused queries (not the entire message)
5. Prioritize nouns and meaningful concepts over common words
6. Consider what the user might have discussed before related to this topic

QUERY TYPES:
- "entity": Specific people, places, things mentioned
- "topic": Main subject areas or themes
- "context": Situational or emotional context
- "intent": What the user is trying to accomplish
- "emotion": Emotional state or feeling-related terms

SEARCH STRATEGIES:
- "specific": User mentioned very specific things (use exact terms)
- "broad": User message is vague (use related concepts)
- "contextual": Message references previous conversations (use context clues)"""

        user_prompt = f"""Analyze this message and create optimized search queries for memory retrieval:

MESSAGE: "{message}"{context_prompt}

Return ONLY valid JSON in this exact format:
{{
    "queries": [
        {{
            "query": "specific search terms",
            "weight": 1.0,
            "query_type": "entity|topic|context|intent|emotion",
            "confidence": 0.9,
            "reasoning": "why this query is useful"
        }}
    ],
    "entities": ["entity1", "entity2"],
    "main_topics": ["topic1", "topic2"],
    "intent": "user's main intent",
    "emotional_context": "emotional tone if present",
    "search_strategy": "specific|broad|contextual"
}}

IMPORTANT:
- Create 2-4 focused queries maximum
- Avoid repeating the entire message as a query
- Focus on searchable terms that would match past conversations
- Higher weight (1.0-1.5) for more important queries
- Lower weight (0.5-0.8) for supplementary queries"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = await self.llm_client.generate_response_async(
                messages=messages,
                max_tokens=400,
                temperature=0.3,  # Lower temperature for more consistent analysis
            )

            # Parse JSON response
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            return json.loads(response_text.strip())

        except Exception as e:
            logger.error(f"LLM query breakdown call failed: {e}")
            raise

    def _parse_llm_response(
        self, response: dict[str, Any], original_message: str
    ) -> LLMQueryBreakdown:
        """Parse LLM response into structured breakdown"""

        # Extract queries
        primary_queries = []
        for query_data in response.get("queries", []):
            query = LLMSearchQuery(
                query=query_data.get("query", ""),
                weight=float(query_data.get("weight", 1.0)),
                query_type=query_data.get("query_type", "general"),
                confidence=float(query_data.get("confidence", 1.0)),
                reasoning=query_data.get("reasoning", ""),
            )
            if query.query.strip():  # Only add non-empty queries
                primary_queries.append(query)

        # Ensure we have at least one query
        if not primary_queries:
            primary_queries = [
                LLMSearchQuery(
                    query=self._clean_message_for_fallback(original_message),
                    weight=1.0,
                    query_type="fallback",
                )
            ]

        return LLMQueryBreakdown(
            primary_queries=primary_queries,
            fallback_query=self._clean_message_for_fallback(original_message),
            extracted_entities=response.get("entities", []),
            main_topics=response.get("main_topics", []),
            intent_classification=response.get("intent", "unknown"),
            emotional_context=response.get("emotional_context"),
            search_strategy=response.get("search_strategy", "standard"),
        )

    def _create_fallback_breakdown(self, message: str) -> LLMQueryBreakdown:
        """Create a basic breakdown when LLM analysis fails"""

        # Simple keyword extraction as fallback
        cleaned_message = self._clean_message_for_fallback(message)

        return LLMQueryBreakdown(
            primary_queries=[
                LLMSearchQuery(query=cleaned_message, weight=1.0, query_type="fallback")
            ],
            fallback_query=cleaned_message,
            extracted_entities=[],
            main_topics=[],
            intent_classification="unknown",
            search_strategy="broad",
        )

    def _clean_message_for_fallback(self, message: str) -> str:
        """Clean message for fallback query (remove common words)"""

        # Basic stop words to remove
        stop_words = {
            "i",
            "me",
            "my",
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
            "when",
            "how",
            "what",
            "why",
            "do",
            "does",
            "did",
            "will",
            "would",
            "can",
            "could",
            "should",
            "just",
            "really",
            "tell",
            "help",
            "please",
            "thanks",
            "you",
            "your",
            "today",
            "now",
        }

        words = message.lower().split()
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 2]

        return " ".join(meaningful_words[:8])  # Limit to 8 most meaningful words


class HybridQueryProcessor:
    """
    Combines LLM-powered and rule-based query processing for optimal results
    """

    def __init__(self, llm_client, enable_llm: bool = True):
        self.llm_processor = LLMQueryProcessor(llm_client) if enable_llm else None
        self.enable_llm = enable_llm

    async def process_message(
        self, message: str, conversation_context: str | None = None
    ) -> LLMQueryBreakdown:
        """
        Process message using LLM analysis with rule-based fallback
        """

        if self.enable_llm and self.llm_processor:
            try:
                # Try LLM-powered analysis first
                result = await self.llm_processor.analyze_message_for_search(
                    message, conversation_context
                )

                # Validate that we got meaningful queries
                if result.primary_queries and any(
                    len(q.query.strip()) > 3 for q in result.primary_queries
                ):
                    logger.debug(
                        f"LLM query breakdown successful: {len(result.primary_queries)} queries generated"
                    )
                    return result
                else:
                    logger.warning("LLM returned insufficient queries, using fallback")

            except Exception as e:
                logger.warning(f"LLM query processing failed: {e}")

        # Fallback to rule-based processing
        return self._rule_based_fallback(message)

    def _rule_based_fallback(self, message: str) -> LLMQueryBreakdown:
        """Rule-based fallback when LLM is unavailable or fails"""

        # Simple entity extraction
        entities = self._extract_simple_entities(message)

        # Create focused queries
        queries = []

        # Add entity-based queries
        for entity in entities[:3]:  # Top 3 entities
            queries.append(
                LLMSearchQuery(query=entity, weight=1.2, query_type="entity", confidence=0.8)
            )

        # Add cleaned message query
        cleaned = self._clean_message_simple(message)
        if cleaned and cleaned not in [q.query for q in queries]:
            queries.append(
                LLMSearchQuery(query=cleaned, weight=1.0, query_type="general", confidence=0.7)
            )

        return LLMQueryBreakdown(
            primary_queries=queries or [LLMSearchQuery(query=message[:50], weight=1.0)],
            fallback_query=cleaned or message,
            extracted_entities=entities,
            main_topics=[],
            intent_classification="unknown",
            search_strategy="broad",
        )

    def _extract_simple_entities(self, message: str) -> list[str]:
        """Simple rule-based entity extraction"""
        import re

        # Look for capitalized words (potential proper nouns)
        capitalized = re.findall(r"\b[A-Z][a-zA-Z]+\b", message)

        # Look for quoted terms
        quoted = re.findall(r'"([^"]+)"', message)

        # Combine and deduplicate
        entities = list(set(capitalized + quoted))

        return [e for e in entities if len(e) > 2][:5]  # Max 5 entities

    def _clean_message_simple(self, message: str) -> str:
        """Simple message cleaning for fallback"""
        import re

        # Remove common phrases
        message = re.sub(
            r"\b(can you|could you|please|help me|tell me|what about|how about)\b",
            "",
            message,
            flags=re.IGNORECASE,
        )

        # Extract meaningful words
        words = re.findall(r"\b\w{3,}\b", message.lower())

        # Remove common stop words
        stop_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "her",
            "was",
            "one",
            "our",
            "had",
            "what",
            "were",
            "they",
            "said",
            "each",
            "which",
            "she",
            "their",
            "time",
            "will",
            "about",
            "if",
            "up",
            "out",
            "many",
            "then",
            "them",
            "these",
            "so",
            "some",
            "would",
            "other",
            "into",
            "has",
            "more",
            "go",
            "no",
            "way",
            "could",
            "my",
            "than",
            "first",
            "been",
            "call",
            "who",
            "its",
            "now",
            "find",
            "long",
            "down",
            "day",
            "did",
            "get",
            "come",
            "made",
            "may",
            "part",
        }

        meaningful_words = [w for w in words if w not in stop_words]

        return " ".join(meaningful_words[:6])  # Max 6 words
