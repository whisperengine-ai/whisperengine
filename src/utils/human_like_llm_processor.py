"""
Human-Like LLM Query Processor

This module combines advanced prompt engineering with human-like conversation
optimization specifically for chatbots that need to feel natural and emotionally intelligent.
"""

import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

from .human_like_memory_optimizer import (
    HumanLikeChatbotOptimizer,
    ConversationalMemoryOptimizer,
    create_human_like_memory_optimizer,
)

logger = logging.getLogger(__name__)


@dataclass
class HumanLikeSearchQuery:
    """Search query optimized for human-like conversation"""

    query: str
    weight: float = 1.0
    query_type: str = (
        "conversational"  # "emotional", "personal", "topical", "contextual", "relational"
    )
    confidence: float = 1.0
    reasoning: str = ""
    emotional_resonance: float = 0.5  # How emotionally relevant this query is
    relationship_relevance: float = 0.5  # How relevant to ongoing relationship
    conversation_flow_score: float = 0.5  # How well this continues the conversation


@dataclass
class HumanLikeQueryResult:
    """Result optimized for natural conversation flow"""

    primary_queries: List[HumanLikeSearchQuery]
    fallback_query: str
    emotional_context: Optional[str]
    conversation_purpose: str
    relationship_tone: str
    memory_priority: str  # What type of memory would be most helpful right now
    human_association: str  # How a caring friend would naturally recall this


class HumanLikeLLMProcessor:
    """
    LLM processor optimized specifically for human-like chatbot conversations
    """

    def __init__(self, llm_client, personality_type: str = "caring_friend"):
        self.llm_client = llm_client
        self.personality_type = personality_type
        self.human_optimizer = create_human_like_memory_optimizer(personality_type=personality_type)
        self.conversation_optimizer = ConversationalMemoryOptimizer()

        logger.info(f"Human-like LLM processor initialized with personality: {personality_type}")

    async def process_for_human_conversation(
        self,
        message: str,
        user_id: str,
        conversation_history: Optional[List[str]] = None,
        relationship_context: Optional[Dict] = None,
        emotional_state: Optional[str] = None,
    ) -> HumanLikeQueryResult:
        """
        Process message for human-like conversational memory search
        """

        try:
            # Get human-like optimized prompts
            system_prompt, user_prompt = self.human_optimizer.optimize_for_human_conversation(
                message=message,
                user_id=user_id,
                conversation_history=conversation_history,
                relationship_context=relationship_context,
            )

            # Optimize for conversation flow
            flow_optimization = self.conversation_optimizer.optimize_for_conversation_flow(
                current_message=message,
                conversation_history=conversation_history or [],
                user_patterns=relationship_context,
            )

            # Call LLM with optimized prompts
            response = await self._call_human_optimized_llm(
                system_prompt, user_prompt, flow_optimization
            )

            # Parse and enhance response for human-like interaction
            return self._parse_human_like_response(response, message, flow_optimization)

        except Exception as e:
            logger.warning(f"Human-like LLM processing failed: {e}")
            return self._create_human_fallback(message, conversation_history)

    async def _call_human_optimized_llm(
        self, system_prompt: str, user_prompt: str, flow_optimization: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call LLM with human-optimized prompts"""

        # Enhance user prompt with conversation flow context
        enhanced_user_prompt = user_prompt

        if flow_optimization.get("conversation_continuity_weight", 0) > 0.7:
            enhanced_user_prompt += f"""

CONVERSATION FLOW: High continuity detected. Focus on memories that naturally continue this conversation thread.
Flow analysis: {flow_optimization.get('flow_analysis', {})}"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": enhanced_user_prompt},
            ]

            response = await self.llm_client.generate_response_async(
                messages=messages,
                max_tokens=500,  # Slightly more tokens for human-like reasoning
                temperature=0.4,  # Balanced creativity for natural responses
            )

            # Parse JSON response
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            return json.loads(response_text.strip())

        except Exception as e:
            logger.error(f"Human-optimized LLM call failed: {e}")
            raise

    def _parse_human_like_response(
        self, response: Dict[str, Any], original_message: str, flow_optimization: Dict[str, Any]
    ) -> HumanLikeQueryResult:
        """Parse LLM response into human-like query result"""

        # Extract and enhance queries
        primary_queries = []
        for query_data in response.get("queries", []):

            # Calculate human-like scores
            emotional_resonance = self._calculate_emotional_resonance(
                query_data.get("query", ""), query_data.get("query_type", "general")
            )

            relationship_relevance = self._calculate_relationship_relevance(
                query_data.get("query", ""), flow_optimization
            )

            conversation_flow_score = flow_optimization.get("conversation_continuity_weight", 0.5)

            query = HumanLikeSearchQuery(
                query=query_data.get("query", ""),
                weight=float(query_data.get("weight", 1.0)),
                query_type=query_data.get("query_type", "conversational"),
                confidence=float(query_data.get("confidence", 1.0)),
                reasoning=query_data.get("reasoning", ""),
                emotional_resonance=emotional_resonance,
                relationship_relevance=relationship_relevance,
                conversation_flow_score=conversation_flow_score,
            )

            if query.query.strip():
                primary_queries.append(query)

        # Ensure we have at least one query
        if not primary_queries:
            primary_queries = [
                HumanLikeSearchQuery(
                    query=self._create_safe_fallback_query(original_message),
                    weight=1.0,
                    query_type="fallback_conversational",
                )
            ]

        return HumanLikeQueryResult(
            primary_queries=primary_queries,
            fallback_query=self._create_safe_fallback_query(original_message),
            emotional_context=response.get("emotional_keywords"),
            conversation_purpose=response.get("conversation_flow", "continuing_chat"),
            relationship_tone=response.get("memory_priority", "friendly"),
            memory_priority=response.get("memory_priority", "contextual_relevance"),
            human_association=response.get("human_association", "natural conversation flow"),
        )

    def _calculate_emotional_resonance(self, query: str, query_type: str) -> float:
        """Calculate how emotionally resonant a query is"""

        emotional_keywords = [
            "feeling",
            "emotion",
            "happy",
            "sad",
            "excited",
            "worried",
            "love",
            "fear",
            "joy",
            "anger",
            "frustrated",
            "grateful",
            "proud",
            "disappointed",
            "hopeful",
        ]

        query_lower = query.lower()
        emotional_score = sum(1 for keyword in emotional_keywords if keyword in query_lower)

        # Boost score for explicitly emotional query types
        if query_type in ["emotional", "personal", "relational"]:
            emotional_score += 2

        return min(1.0, emotional_score * 0.2)

    def _calculate_relationship_relevance(
        self, query: str, flow_optimization: Dict[str, Any]
    ) -> float:
        """Calculate how relevant a query is to the ongoing relationship"""

        relationship_keywords = [
            "we",
            "us",
            "our",
            "together",
            "shared",
            "both",
            "remember",
            "discussed",
            "talked",
            "mentioned",
            "told",
            "asked",
            "helped",
            "supported",
        ]

        query_lower = query.lower()
        relationship_score = sum(1 for keyword in relationship_keywords if keyword in query_lower)

        # Factor in conversation flow
        flow_bonus = flow_optimization.get("conversation_continuity_weight", 0.0) * 0.3

        return min(1.0, (relationship_score * 0.25) + flow_bonus)

    def _create_safe_fallback_query(self, message: str) -> str:
        """Create a safe fallback query that feels natural"""

        # Extract meaningful words for fallback
        stop_words = {
            "i",
            "me",
            "my",
            "you",
            "your",
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "is",
            "are",
            "was",
            "were",
            "will",
            "would",
            "can",
            "could",
            "should",
            "do",
            "does",
            "did",
            "have",
            "has",
            "had",
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "just",
            "really",
            "very",
            "so",
            "too",
            "now",
            "then",
        }

        words = [word.lower() for word in message.split() if word.lower() not in stop_words]
        meaningful_words = [word for word in words if len(word) > 2][:5]

        return " ".join(meaningful_words) if meaningful_words else message[:30]

    def _create_human_fallback(
        self, message: str, conversation_history: Optional[List[str]]
    ) -> HumanLikeQueryResult:
        """Create human-like fallback when LLM processing fails"""

        fallback_query = self._create_safe_fallback_query(message)

        # Try to maintain human-like understanding even in fallback
        emotional_context = self._detect_basic_emotion(message)
        conversation_purpose = self._detect_basic_purpose(message)

        return HumanLikeQueryResult(
            primary_queries=[
                HumanLikeSearchQuery(
                    query=fallback_query,
                    weight=1.0,
                    query_type="fallback_human",
                    emotional_resonance=0.3 if emotional_context else 0.1,
                    relationship_relevance=0.5,
                    conversation_flow_score=0.4,
                )
            ],
            fallback_query=fallback_query,
            emotional_context=emotional_context,
            conversation_purpose=conversation_purpose,
            relationship_tone="friendly",
            memory_priority="stay_connected",
            human_association="maintaining conversation flow",
        )

    def _detect_basic_emotion(self, message: str) -> Optional[str]:
        """Basic emotion detection for fallback"""

        message_lower = message.lower()

        if any(word in message_lower for word in ["happy", "excited", "great", "awesome"]):
            return "positive"
        elif any(word in message_lower for word in ["sad", "worried", "frustrated", "upset"]):
            return "concerned"
        elif any(word in message_lower for word in ["thank", "grateful", "appreciate"]):
            return "grateful"

        return None

    def _detect_basic_purpose(self, message: str) -> str:
        """Basic purpose detection for fallback"""

        message_lower = message.lower()

        if any(word in message_lower for word in ["help", "advice", "should i"]):
            return "seeking_guidance"
        elif any(word in message_lower for word in ["remember", "recall", "mentioned"]):
            return "recalling_memory"
        elif any(word in message_lower for word in ["excited", "guess what", "news"]):
            return "sharing_excitement"
        else:
            return "casual_conversation"


class HumanLikeMemorySearch:
    """
    Complete human-like memory search system
    """

    def __init__(self, base_memory_manager, llm_client, personality_type: str = "caring_friend"):
        self.base_memory_manager = base_memory_manager
        self.llm_processor = HumanLikeLLMProcessor(llm_client, personality_type)
        self.personality_type = personality_type

    async def search_like_human_friend(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[str]] = None,
        relationship_context: Optional[Dict] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Search memories the way a caring human friend would naturally recall shared experiences
        """

        try:
            # Process message with human-like understanding
            human_result = await self.llm_processor.process_for_human_conversation(
                message=message,
                user_id=user_id,
                conversation_history=conversation_history,
                relationship_context=relationship_context,
            )

            # Execute searches with human-like priorities
            all_memories = []
            search_performance = {
                "queries_executed": 0,
                "emotional_relevance": 0.0,
                "relationship_continuity": 0.0,
                "conversation_flow": 0.0,
            }

            for query in human_result.primary_queries:
                try:
                    memories = await self.base_memory_manager.retrieve_relevant_memories(
                        user_id=user_id,
                        query=query.query,
                        limit=max(3, limit // len(human_result.primary_queries)),
                    )

                    # Enhance memories with human-like context
                    for memory in memories:
                        memory["human_relevance_score"] = self._calculate_human_relevance(
                            memory, query, human_result
                        )
                        memory["emotional_connection"] = query.emotional_resonance
                        memory["relationship_value"] = query.relationship_relevance
                        memory["conversation_continuity"] = query.conversation_flow_score
                        memory["source_query"] = query.query
                        memory["human_reasoning"] = query.reasoning

                    all_memories.extend(memories)
                    search_performance["queries_executed"] += 1

                except Exception as e:
                    logger.warning(f"Human-like query '{query.query}' failed: {e}")
                    continue

            # Rank memories like a human would prioritize them
            final_memories = self._rank_memories_like_human(all_memories, human_result, limit)

            # Calculate human-like performance metrics
            if final_memories:
                search_performance["emotional_relevance"] = sum(
                    m.get("emotional_connection", 0) for m in final_memories
                ) / len(final_memories)

                search_performance["relationship_continuity"] = sum(
                    m.get("relationship_value", 0) for m in final_memories
                ) / len(final_memories)

                search_performance["conversation_flow"] = sum(
                    m.get("conversation_continuity", 0) for m in final_memories
                ) / len(final_memories)

            return {
                "memories": final_memories,
                "human_context": {
                    "emotional_understanding": human_result.emotional_context,
                    "conversation_purpose": human_result.conversation_purpose,
                    "relationship_tone": human_result.relationship_tone,
                    "memory_priority": human_result.memory_priority,
                    "human_association": human_result.human_association,
                },
                "search_performance": search_performance,
                "processing_method": f"human_like_{self.personality_type}",
            }

        except Exception as e:
            logger.error(f"Human-like memory search failed: {e}")
            # Fallback to caring but simple search
            return await self._caring_fallback_search(user_id, message, limit)

    def _calculate_human_relevance(
        self,
        memory: Dict[str, Any],
        query: HumanLikeSearchQuery,
        human_result: HumanLikeQueryResult,
    ) -> float:
        """Calculate relevance the way a human would judge importance"""

        base_score = memory.get("similarity_score", 0.5)

        # Weight factors like a human would
        emotional_weight = query.emotional_resonance * 0.3
        relationship_weight = query.relationship_relevance * 0.3
        conversation_weight = query.conversation_flow_score * 0.2
        personal_weight = 0.2  # Base personal connection

        human_score = (
            base_score
            + emotional_weight
            + relationship_weight
            + conversation_weight
            + personal_weight
        ) / 2.0  # Normalize

        return min(1.0, human_score)

    def _rank_memories_like_human(
        self, memories: List[Dict[str, Any]], human_result: HumanLikeQueryResult, limit: int
    ) -> List[Dict[str, Any]]:
        """Rank memories the way a caring human friend would prioritize them"""

        # Remove duplicates while keeping best human relevance scores
        unique_memories = {}
        for memory in memories:
            memory_id = memory.get("id") or memory.get("content", "")[:100]

            if memory_id not in unique_memories:
                unique_memories[memory_id] = memory
            else:
                existing_score = unique_memories[memory_id].get("human_relevance_score", 0)
                new_score = memory.get("human_relevance_score", 0)

                if new_score > existing_score:
                    unique_memories[memory_id] = memory

        # Sort by human relevance (combination of emotional, relational, and conversational value)
        sorted_memories = sorted(
            unique_memories.values(),
            key=lambda m: (
                m.get("human_relevance_score", 0),
                m.get("emotional_connection", 0),
                m.get("relationship_value", 0),
                m.get("similarity_score", 0),
            ),
            reverse=True,
        )

        return sorted_memories[:limit]

    async def _caring_fallback_search(
        self, user_id: str, message: str, limit: int
    ) -> Dict[str, Any]:
        """Caring fallback when human-like processing fails"""

        try:
            # Simple but caring search
            memories = await self.base_memory_manager.retrieve_relevant_memories(
                user_id=user_id, query=message, limit=limit
            )

            return {
                "memories": memories,
                "human_context": {
                    "emotional_understanding": "staying_connected",
                    "conversation_purpose": "maintain_relationship",
                    "relationship_tone": "caring",
                    "memory_priority": "continue_conversation",
                    "human_association": "keeping our connection alive",
                },
                "search_performance": {
                    "emotional_relevance": 0.5,
                    "relationship_continuity": 0.7,
                    "conversation_flow": 0.6,
                },
                "processing_method": "caring_fallback",
            }

        except Exception as e:
            logger.error(f"Even caring fallback failed: {e}")
            return {
                "memories": [],
                "human_context": {"emotional_understanding": "still_here_for_you"},
                "search_performance": {},
                "processing_method": "error_but_caring",
            }


# Factory function for complete human-like memory system
def create_human_like_memory_system(
    base_memory_manager,
    llm_client,
    personality_type: str = "caring_friend",
    enable_emotional_intelligence: bool = True,
    enable_relationship_awareness: bool = True,
) -> HumanLikeMemorySearch:
    """
    Create a complete human-like memory search system

    Personality types:
    - "caring_friend": Warm, supportive, emotionally intelligent
    - "wise_mentor": Thoughtful, insightful, growth-oriented
    - "playful_companion": Fun, engaging, lighthearted
    - "supportive_counselor": Professional caring, solution-focused
    """

    return HumanLikeMemorySearch(
        base_memory_manager=base_memory_manager,
        llm_client=llm_client,
        personality_type=personality_type,
    )
