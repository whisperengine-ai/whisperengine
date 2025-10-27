"""
Hybrid Query Router - Intelligent routing between semantic search and LLM tool calling.

This module implements the HybridQueryRouter class that analyzes user queries and decides
whether to use fast semantic routing (10-50ms) or LLM tool calling (1500-3500ms) based
on query complexity.

Architecture:
- 80% of queries route to semantic search (simple, fast)
- 20% of queries route to LLM tool calling (complex, multi-source)
- Configurable complexity threshold (default: 0.3)

Core Tools (5):
1. query_user_facts - Query PostgreSQL user_fact_relationships
2. recall_conversation_context - Query Qdrant conversation history
3. query_character_backstory - Query PostgreSQL CDL database
4. summarize_user_relationship - Aggregate multi-source data
5. query_temporal_trends - Query InfluxDB metrics

Design Document: docs/architecture/hybrid-routing-initiative/HYBRID_QUERY_ROUTING_DESIGN.md
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComplexityAssessment:
    """Result of query complexity analysis."""
    
    complexity_score: float  # 0.0 to 1.0
    sentence_length_score: float  # 0.0 to 1.0
    question_word_score: float  # 0.0 to 1.0
    entity_reference_score: float  # 0.0 to 1.0
    use_tools: bool  # Whether to route to LLM tool calling
    reasoning: str  # Human-readable explanation
    detected_entities: List[str]  # Entities detected in query
    detected_question_words: List[str]  # Question words detected


class HybridQueryRouter:
    """
    Intelligent query router that decides between semantic search and LLM tool calling.
    
    Uses a complexity assessment algorithm to analyze user queries and route them
    to the optimal data retrieval strategy:
    - Simple queries → semantic search (fast, 10-50ms)
    - Complex queries → LLM tool calling (slower, 1500-3500ms, but more accurate)
    
    Complexity Assessment Algorithm:
    - Sentence length (10+ words = higher complexity)
    - Question words (what, when, where, how, why, etc.)
    - Entity references (user, character, temporal, relationships)
    - Configurable threshold (default: 0.3)
    
    Example:
        router = HybridQueryRouter(complexity_threshold=0.3)
        assessment = router.assess_query_complexity(
            user_message="What do you remember about me?",
            user_id="user123",
            character_name="elena"
        )
        
        if assessment.use_tools:
            # Route to LLM tool calling
            result = await router.route_to_tools(...)
        else:
            # Use semantic search
            result = await memory_system.retrieve_relevant_memories(...)
    """
    
    # Question words that indicate information-seeking queries
    QUESTION_WORDS = [
        "what", "when", "where", "who", "why", "how",
        "which", "whose", "whom", "tell", "explain",
        "describe", "summarize", "list", "show", "find",
        "remember", "recall", "know", "learned", "understand"
    ]
    
    # Entity reference patterns
    ENTITY_PATTERNS = {
        "user_reference": [
            r"\b(me|my|mine|i|myself)\b",
            r"\b(about\s+me|remember\s+me|know\s+about\s+me)\b"
        ],
        "character_reference": [
            r"\b(you|your|yourself|yours)\b",
            r"\b(tell\s+me\s+about\s+you|who\s+are\s+you)\b"
        ],
        "temporal_reference": [
            r"\b(last|yesterday|today|recent|lately|before|ago|earlier)\b",
            r"\b(when|time|date|day|week|month|year)\b"
        ],
        "relationship_reference": [
            r"\b(our|us|we|together|between\s+us)\b",
            r"\b(relationship|connection|friendship|bond)\b"
        ]
    }
    
    def __init__(
        self,
        complexity_threshold: float = 0.3,
        enable_tool_calling: bool = True,
        log_assessments: bool = True
    ):
        """
        Initialize the HybridQueryRouter.
        
        Args:
            complexity_threshold: Score above which to use tool calling (0.0-1.0)
            enable_tool_calling: Master switch for tool calling (for A/B testing)
            log_assessments: Whether to log complexity assessments
        """
        self.complexity_threshold = complexity_threshold
        self.enable_tool_calling = enable_tool_calling
        self.log_assessments = log_assessments
        
        logger.info(
            f"HybridQueryRouter initialized: "
            f"threshold={complexity_threshold}, "
            f"tool_calling={'enabled' if enable_tool_calling else 'disabled'}"
        )
    
    def assess_query_complexity(
        self,
        user_message: str,
        user_id: str,
        character_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ComplexityAssessment:
        """
        Analyze query complexity to determine routing strategy.
        
        Complexity Assessment Algorithm:
        1. Sentence Length (weight: 0.3)
           - Short (< 5 words): 0.0
           - Medium (5-10 words): 0.5
           - Long (10+ words): 1.0
        
        2. Question Words (weight: 0.4)
           - No question words: 0.0
           - 1 question word: 0.5
           - 2+ question words: 1.0
        
        3. Entity References (weight: 0.3)
           - No entities: 0.0
           - 1-2 entity types: 0.5
           - 3+ entity types: 1.0
        
        Final Score: weighted_sum / 3
        Use Tools: score >= complexity_threshold
        
        Args:
            user_message: The user's query text
            user_id: User identifier
            character_name: Current character name
            context: Optional context (recent messages, user facts, etc.)
        
        Returns:
            ComplexityAssessment with score, reasoning, and routing decision
        """
        message_lower = user_message.lower()
        
        # 1. Sentence Length Score (weight: 0.3)
        word_count = len(user_message.split())
        if word_count < 5:
            sentence_length_score = 0.0
        elif word_count < 10:
            sentence_length_score = 0.5
        else:
            sentence_length_score = 1.0
        
        # 2. Question Words Score (weight: 0.4)
        detected_question_words = [
            word for word in self.QUESTION_WORDS
            if word in message_lower
        ]
        question_word_count = len(detected_question_words)
        if question_word_count == 0:
            question_word_score = 0.0
        elif question_word_count == 1:
            question_word_score = 0.5
        else:
            question_word_score = 1.0
        
        # 3. Entity References Score (weight: 0.3)
        detected_entities = []
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    detected_entities.append(entity_type)
                    break  # Only count each entity type once
        
        entity_count = len(detected_entities)
        if entity_count == 0:
            entity_reference_score = 0.0
        elif entity_count <= 2:
            entity_reference_score = 0.5
        else:
            entity_reference_score = 1.0
        
        # Calculate weighted complexity score
        complexity_score = (
            (sentence_length_score * 0.3) +
            (question_word_score * 0.4) +
            (entity_reference_score * 0.3)
        )
        
        # Routing decision
        use_tools = (
            self.enable_tool_calling and
            complexity_score >= self.complexity_threshold
        )
        
        # Build reasoning string
        reasoning_parts = [
            f"Length: {word_count} words ({sentence_length_score:.1f})",
            f"Questions: {question_word_count} ({question_word_score:.1f})",
            f"Entities: {entity_count} ({entity_reference_score:.1f})",
            f"Score: {complexity_score:.3f}",
            f"Threshold: {self.complexity_threshold}",
            f"→ {'TOOL CALLING' if use_tools else 'SEMANTIC SEARCH'}"
        ]
        reasoning = " | ".join(reasoning_parts)
        
        assessment = ComplexityAssessment(
            complexity_score=complexity_score,
            sentence_length_score=sentence_length_score,
            question_word_score=question_word_score,
            entity_reference_score=entity_reference_score,
            use_tools=use_tools,
            reasoning=reasoning,
            detected_entities=detected_entities,
            detected_question_words=detected_question_words
        )
        
        if self.log_assessments:
            logger.info(
                f"Query complexity assessment | User: {user_id} | "
                f"Character: {character_name} | {reasoning}"
            )
        
        return assessment
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get the list of available tools for LLM tool calling.
        
        Returns the OpenAI function calling schema for all 5 core tools:
        1. query_user_facts
        2. recall_conversation_context
        3. query_character_backstory
        4. summarize_user_relationship
        5. query_temporal_trends
        
        Returns:
            List of tool definitions in OpenAI function calling format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_user_facts",
                    "description": (
                        "Query the PostgreSQL database for facts and preferences about a user. "
                        "Returns structured information like pets, hobbies, family, location, "
                        "communication preferences, etc. with confidence scores."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The user's unique identifier"
                            },
                            "fact_type": {
                                "type": "string",
                                "enum": ["pet", "hobby", "family", "preference", "location", "all"],
                                "description": "Type of facts to query (optional, defaults to 'all')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of facts to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recall_conversation_context",
                    "description": (
                        "Search the Qdrant vector database for relevant conversation history "
                        "using semantic search. Returns contextually relevant past messages "
                        "with emotion analysis and timestamps."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The user's unique identifier"
                            },
                            "query": {
                                "type": "string",
                                "description": "The semantic search query"
                            },
                            "time_window": {
                                "type": "string",
                                "enum": ["24h", "7d", "30d", "all"],
                                "description": "Time window for search (optional, defaults to 'all')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of memories to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["user_id", "query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_character_backstory",
                    "description": (
                        "Query the PostgreSQL CDL database for character backstory, personality traits, "
                        "background, interests, relationships, and identity details. Shared with bot "
                        "self-memory system."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "character_name": {
                                "type": "string",
                                "description": "The character's name (e.g., 'elena', 'marcus')"
                            },
                            "query": {
                                "type": "string",
                                "description": "What to query about the character (e.g., 'workplace', 'hobbies')"
                            },
                            "source": {
                                "type": "string",
                                "enum": ["cdl_database", "self_memory", "both"],
                                "description": "Data source: designer-defined facts (CDL) or bot self-reflections",
                                "default": "both"
                            }
                        },
                        "required": ["character_name", "query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "summarize_user_relationship",
                    "description": (
                        "Generate a comprehensive summary of the relationship with a user by "
                        "aggregating user facts, conversation history, and interaction patterns. "
                        "Multi-source aggregation tool."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The user's unique identifier"
                            },
                            "include_facts": {
                                "type": "boolean",
                                "description": "Include user facts from PostgreSQL (default: true)",
                                "default": True
                            },
                            "include_conversations": {
                                "type": "boolean",
                                "description": "Include conversation history from Qdrant (default: true)",
                                "default": True
                            },
                            "time_window": {
                                "type": "string",
                                "enum": ["24h", "7d", "30d", "all"],
                                "description": "Time window for conversation history (optional)",
                                "default": "all"
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_temporal_trends",
                    "description": (
                        "Query InfluxDB for conversation quality metrics over time. Returns temporal "
                        "trend data for engagement scores, satisfaction scores, coherence scores, etc."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The user's unique identifier"
                            },
                            "metric": {
                                "type": "string",
                                "enum": [
                                    "engagement_score",
                                    "satisfaction_score",
                                    "coherence_score",
                                    "emotional_resonance",
                                    "all"
                                ],
                                "description": "Metric to query (default: 'all')",
                                "default": "all"
                            },
                            "time_window": {
                                "type": "string",
                                "enum": ["24h", "7d", "30d"],
                                "description": "Time window for trend analysis (default: '7d')",
                                "default": "7d"
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            }
        ]
    
    async def route_to_tools(
        self,
        user_message: str,
        user_id: str,
        character_name: str,
        llm_client,  # LLMClient instance
        tool_executor,  # ToolExecutor instance (to be implemented)
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route query to LLM tool calling system.
        
        This method:
        1. Gets available tools
        2. Calls LLM with tools to determine which tool(s) to use
        3. Executes the tool calls via ToolExecutor
        4. Returns tool results for inclusion in conversation context
        
        Args:
            user_message: The user's query
            user_id: User identifier
            character_name: Current character name
            llm_client: LLMClient instance for tool calling
            tool_executor: ToolExecutor instance for executing tool calls
            context: Optional context
        
        Returns:
            Dict with tool results and metadata
        """
        # TODO: Implement in next step
        # This will use llm_client.generate_chat_completion_with_tools()
        # and tool_executor.execute_tool_call()
        raise NotImplementedError(
            "route_to_tools() will be implemented after tool executors are created"
        )
    
    def should_use_tools(
        self,
        user_message: str,
        user_id: str,
        character_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, ComplexityAssessment]:
        """
        Convenience method: assess complexity and return routing decision.
        
        Args:
            user_message: The user's query
            user_id: User identifier
            character_name: Current character name
            context: Optional context
        
        Returns:
            Tuple of (should_use_tools: bool, assessment: ComplexityAssessment)
        """
        assessment = self.assess_query_complexity(
            user_message=user_message,
            user_id=user_id,
            character_name=character_name,
            context=context
        )
        return assessment.use_tools, assessment
