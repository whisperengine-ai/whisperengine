"""
Advanced Prompt Engineering for LLM Memory Search

This module implements sophisticated prompt engineering techniques to optimize
LLM performance for memory search query generation, including few-shot learning,
dynamic examples, user profiling, and adaptive prompting strategies.
"""

import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """Profile of user's communication patterns and interests"""

    common_topics: List[str]
    communication_style: str  # "casual", "formal", "technical", "emotional"
    typical_entities: List[str]
    emotional_patterns: List[str]
    interaction_frequency: str  # "frequent", "occasional", "new"


@dataclass
class PromptContext:
    """Rich context for prompt engineering"""

    user_profile: Optional[UserProfile]
    conversation_history: List[str]
    current_emotion: Optional[str]
    time_context: str  # "morning", "afternoon", "evening", "night"
    recent_topics: List[str]
    message_complexity: str  # "simple", "moderate", "complex"


class AdvancedPromptEngineer:
    """
    Advanced prompt engineering system for LLM memory search optimization
    """

    def __init__(self):
        self.few_shot_examples = self._build_few_shot_examples()
        self.dynamic_templates = self._build_dynamic_templates()
        self.user_profiles = {}  # Cache user profiles

    def optimize_prompt_for_user(
        self, message: str, user_id: str, context: Optional[PromptContext] = None
    ) -> Tuple[str, str]:
        """
        Create optimized system and user prompts based on user profile and context

        Returns:
            Tuple of (system_prompt, user_prompt)
        """

        # Get or create user profile
        user_profile = self._get_user_profile(user_id, message)

        # Analyze message complexity and type
        message_analysis = self._analyze_message(message)

        # Build context-aware prompts
        system_prompt = self._build_optimized_system_prompt(user_profile, message_analysis, context)

        user_prompt = self._build_optimized_user_prompt(
            message, user_profile, message_analysis, context
        )

        return system_prompt, user_prompt

    def _analyze_message(self, message: str) -> Dict[str, Any]:
        """Analyze message characteristics for prompt optimization"""

        message_lower = message.lower()
        word_count = len(message.split())

        # Complexity analysis
        complexity = "simple"
        if word_count > 20:
            complexity = "complex"
        elif word_count > 10:
            complexity = "moderate"

        # Message type detection
        message_type = "general"
        if any(word in message_lower for word in ["?", "what", "how", "why", "when", "where"]):
            message_type = "question"
        elif any(
            word in message_lower
            for word in ["feel", "emotion", "sad", "happy", "angry", "excited"]
        ):
            message_type = "emotional"
        elif any(
            word in message_lower for word in ["remember", "recall", "mentioned", "talked about"]
        ):
            message_type = "recall"
        elif any(word in message_lower for word in ["help", "advice", "suggestion", "tip"]):
            message_type = "seeking_help"

        # Technical level
        technical_indicators = ["api", "code", "function", "algorithm", "database", "programming"]
        is_technical = any(word in message_lower for word in technical_indicators)

        # Urgency indicators
        urgent_indicators = ["urgent", "asap", "quickly", "immediately", "emergency"]
        is_urgent = any(word in message_lower for word in urgent_indicators)

        return {
            "complexity": complexity,
            "type": message_type,
            "word_count": word_count,
            "is_technical": is_technical,
            "is_urgent": is_urgent,
            "contains_entities": bool(re.findall(r"\b[A-Z][a-zA-Z]+\b", message)),
            "has_quotes": '"' in message or "'" in message,
            "has_numbers": bool(re.findall(r"\d+", message)),
        }

    def _build_optimized_system_prompt(
        self,
        user_profile: Optional[UserProfile],
        message_analysis: Dict[str, Any],
        context: Optional[PromptContext],
    ) -> str:
        """Build optimized system prompt based on user and message characteristics"""

        base_prompt = """You are an expert memory search query optimizer. Your task is to analyze user messages and generate the most effective search queries to find relevant memories from past conversations."""

        # Add user-specific instructions
        if user_profile:
            if user_profile.communication_style == "technical":
                base_prompt += "\n\nThis user typically discusses technical topics and uses precise terminology. Focus on technical entities and specific concepts."
            elif user_profile.communication_style == "emotional":
                base_prompt += "\n\nThis user often expresses emotions and personal experiences. Pay attention to emotional context and feeling-related terms."
            elif user_profile.communication_style == "casual":
                base_prompt += "\n\nThis user communicates casually and informally. Look for colloquial terms and everyday topics."

        # Add message-specific guidance
        if message_analysis["is_technical"]:
            base_prompt += "\n\nCURRENT MESSAGE CONTEXT: Technical discussion - prioritize precise technical terms and avoid general language."
        elif message_analysis["type"] == "emotional":
            base_prompt += "\n\nCURRENT MESSAGE CONTEXT: Emotional expression - include emotional keywords and feeling-related terms."
        elif message_analysis["type"] == "recall":
            base_prompt += "\n\nCURRENT MESSAGE CONTEXT: Memory recall request - focus on specific entities and time references."

        # Add complexity-specific instructions
        if message_analysis["complexity"] == "complex":
            base_prompt += "\n\nMESSAGE COMPLEXITY: Complex - extract multiple distinct concepts and create several focused queries."
        elif message_analysis["complexity"] == "simple":
            base_prompt += "\n\nMESSAGE COMPLEXITY: Simple - create 1-2 precise queries avoiding over-analysis."

        # Add optimization strategies
        base_prompt += f"""

OPTIMIZATION STRATEGIES:
1. **Entity Priority**: Extract proper nouns, technical terms, and specific concepts first
2. **Semantic Grouping**: Group related concepts into focused queries  
3. **Noise Reduction**: Eliminate filler words, question markers, and conversational fluff
4. **Context Preservation**: Maintain important contextual and emotional information
5. **Query Diversity**: Create queries that capture different aspects of the message

QUERY GENERATION RULES:
- Generate 1-4 queries maximum (adjust based on message complexity)
- Each query should be 2-6 meaningful terms
- Prioritize nouns and specific concepts over verbs and adjectives
- Include emotional context only when relevant to memory retrieval
- Use exact terms mentioned by user when they're specific entities"""

        # Add few-shot examples based on message type
        examples = self._get_relevant_examples(message_analysis["type"])
        if examples:
            base_prompt += f"\n\nEXAMPLES:\n{examples}"

        return base_prompt

    def _build_optimized_user_prompt(
        self,
        message: str,
        user_profile: Optional[UserProfile],
        message_analysis: Dict[str, Any],
        context: Optional[PromptContext],
    ) -> str:
        """Build optimized user prompt with enhanced context"""

        # Start with core analysis request
        user_prompt = f"""Analyze this message and generate optimal memory search queries:

MESSAGE: "{message}\""""

        # Add user context if available
        if user_profile and user_profile.common_topics:
            user_prompt += f"""
USER CONTEXT: This user commonly discusses: {', '.join(user_profile.common_topics[:5])}"""

        # Add conversation context if available
        if context and context.recent_topics:
            user_prompt += f"""
RECENT TOPICS: {', '.join(context.recent_topics[:3])}"""

        # Add emotional context
        if context and context.current_emotion:
            user_prompt += f"""
CURRENT EMOTIONAL STATE: {context.current_emotion}"""

        # Add time context for relevance
        if context and context.time_context:
            user_prompt += f"""
TIME CONTEXT: {context.time_context}"""

        # Provide specific instructions based on message analysis
        instructions = self._get_message_specific_instructions(message_analysis)
        user_prompt += f"""

SPECIFIC INSTRUCTIONS FOR THIS MESSAGE:
{instructions}"""

        # Add output format with validation
        user_prompt += f"""

OUTPUT FORMAT (return ONLY valid JSON):
{{
    "queries": [
        {{
            "query": "focused search terms",
            "weight": 1.0,
            "query_type": "entity|topic|context|intent|emotion",
            "confidence": 0.9,
            "reasoning": "why this specific query will find relevant memories"
        }}
    ],
    "entities": ["extracted entities"],
    "main_topics": ["core topics"],
    "intent": "user's primary intent",
    "emotional_context": "emotional tone if relevant",
    "search_strategy": "specific|broad|contextual|technical",
    "optimization_notes": "brief explanation of query optimization choices"
}}

VALIDATION CHECKLIST:
✓ Queries are focused and searchable
✓ No duplicate or overly similar queries  
✓ Reasoning explains memory retrieval value
✓ Entities are actual mentioned items
✓ Search strategy matches message characteristics"""

        return user_prompt

    def _get_message_specific_instructions(self, message_analysis: Dict[str, Any]) -> str:
        """Get specific instructions based on message analysis"""

        instructions = []

        if message_analysis["type"] == "question":
            instructions.append(
                "• Focus on the subject matter of the question, not the questioning itself"
            )
            instructions.append("• Extract the core topic being asked about")

        if message_analysis["type"] == "emotional":
            instructions.append(
                "• Include emotional keywords that would match past emotional discussions"
            )
            instructions.append("• Balance emotion terms with factual content")

        if message_analysis["type"] == "recall":
            instructions.append("• Prioritize specific entities and time references mentioned")
            instructions.append(
                "• Create queries that would match the remembered content, not the act of remembering"
            )

        if message_analysis["is_technical"]:
            instructions.append("• Preserve technical terminology exactly as mentioned")
            instructions.append("• Create separate queries for different technical concepts")

        if message_analysis["complexity"] == "complex":
            instructions.append(
                "• Break down into multiple focused queries covering different aspects"
            )
            instructions.append("• Ensure each query captures a distinct concept or theme")

        if message_analysis["contains_entities"]:
            instructions.append("• Extract proper nouns and specific entity names")
            instructions.append("• Create entity-focused queries with high weight")

        if message_analysis["has_numbers"]:
            instructions.append("• Include relevant numbers in queries (dates, quantities, etc.)")

        if not instructions:
            instructions.append(
                "• Create focused queries that capture the main themes and concepts"
            )
            instructions.append("• Avoid including question words or conversational filler")

        return "\n".join(instructions)

    def _get_user_profile(self, user_id: str, message: str) -> Optional[UserProfile]:
        """Get or create user profile for prompt optimization"""

        # For now, create a basic profile based on message analysis
        # In production, this would load from user interaction history

        if user_id not in self.user_profiles:
            # Analyze current message for initial profile
            message_lower = message.lower()

            # Detect communication style
            style = "casual"
            if any(word in message_lower for word in ["function", "api", "algorithm", "code"]):
                style = "technical"
            elif any(word in message_lower for word in ["feel", "emotion", "heart", "soul"]):
                style = "emotional"
            elif len(message.split()) > 20 and "." in message:
                style = "formal"

            # Extract potential topics
            topics = []
            topic_indicators = {
                "programming": ["code", "function", "api", "programming", "algorithm"],
                "music": ["guitar", "song", "music", "chord", "instrument"],
                "cooking": ["recipe", "cooking", "food", "ingredient", "kitchen"],
                "work": ["job", "work", "project", "deadline", "boss", "meeting"],
                "gaming": ["game", "gaming", "play", "level", "character"],
                "health": ["health", "exercise", "fitness", "diet", "medical"],
            }

            for topic, keywords in topic_indicators.items():
                if any(keyword in message_lower for keyword in keywords):
                    topics.append(topic)

            profile = UserProfile(
                common_topics=topics,
                communication_style=style,
                typical_entities=[],
                emotional_patterns=[],
                interaction_frequency="new",
            )

            self.user_profiles[user_id] = profile

        return self.user_profiles[user_id]

    def _build_few_shot_examples(self) -> Dict[str, str]:
        """Build few-shot examples for different message types"""

        return {
            "question": """
Example - Question Message:
INPUT: "How do I fix that guitar tuning issue we talked about last week?"
OUTPUT: {
    "queries": [
        {"query": "guitar tuning problems", "weight": 1.2, "query_type": "topic", "confidence": 0.9},
        {"query": "guitar maintenance issues", "weight": 0.8, "query_type": "context", "confidence": 0.7}
    ],
    "intent": "seeking_solution",
    "search_strategy": "specific"
}""",
            "emotional": """
Example - Emotional Message:
INPUT: "I'm feeling so overwhelmed with work stress lately, just like last month"
OUTPUT: {
    "queries": [
        {"query": "work stress overwhelmed", "weight": 1.3, "query_type": "emotion", "confidence": 0.9},
        {"query": "workplace pressure feelings", "weight": 1.0, "query_type": "context", "confidence": 0.8}
    ],
    "emotional_context": "overwhelmed and stressed",
    "search_strategy": "contextual"
}""",
            "recall": """
Example - Recall Message:
INPUT: "What was that recipe you helped me with? Something with chocolate chips?"
OUTPUT: {
    "queries": [
        {"query": "chocolate chip recipe", "weight": 1.4, "query_type": "entity", "confidence": 0.9},
        {"query": "baking recipe help", "weight": 1.0, "query_type": "topic", "confidence": 0.8}
    ],
    "intent": "memory_recall",
    "search_strategy": "specific"
}""",
        }

    def _get_relevant_examples(self, message_type: str) -> Optional[str]:
        """Get relevant few-shot examples for message type"""
        return self.few_shot_examples.get(message_type)

    def _build_dynamic_templates(self) -> Dict[str, str]:
        """Build dynamic prompt templates for different scenarios"""

        return {
            "high_confidence": "Focus on precise, specific queries with high confidence scores.",
            "low_confidence": "Create broader, more inclusive queries to cast a wider search net.",
            "technical_user": "Prioritize technical terminology and specific implementation details.",
            "emotional_user": "Include emotional context and feeling-related search terms.",
            "frequent_user": "Leverage knowledge of user's common topics and communication patterns.",
            "new_user": "Focus on explicit content without assumptions about user preferences.",
        }


class TokenOptimizer:
    """
    Optimize prompts for token efficiency while maintaining effectiveness
    """

    def __init__(self, max_tokens: int = 800):
        self.max_tokens = max_tokens

    def optimize_prompt_length(self, system_prompt: str, user_prompt: str) -> Tuple[str, str]:
        """Optimize prompt length while preserving key information"""

        # Estimate token count (rough approximation: 1 token ≈ 3-4 chars)
        total_chars = len(system_prompt) + len(user_prompt)
        estimated_tokens = total_chars // 3

        if estimated_tokens <= self.max_tokens:
            return system_prompt, user_prompt

        # Aggressive optimization needed
        logger.warning(f"Prompt too long ({estimated_tokens} tokens), optimizing...")

        # Optimize system prompt
        optimized_system = self._compress_system_prompt(system_prompt)

        # Optimize user prompt
        optimized_user = self._compress_user_prompt(user_prompt)

        return optimized_system, optimized_user

    def _compress_system_prompt(self, prompt: str) -> str:
        """Compress system prompt while preserving key instructions"""

        # Keep core instructions, remove verbose explanations
        lines = prompt.split("\n")
        essential_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Keep core instruction lines
            if any(
                keyword in line.lower()
                for keyword in [
                    "analyze",
                    "generate",
                    "extract",
                    "focus",
                    "prioritize",
                    "rules:",
                    "format:",
                ]
            ):
                essential_lines.append(line)
            # Keep examples but compress them
            elif "example" in line.lower():
                essential_lines.append(line[:100] + "...")

        return "\n".join(essential_lines)

    def _compress_user_prompt(self, prompt: str) -> str:
        """Compress user prompt while preserving essential information"""

        # Extract essential components
        message_match = re.search(r'MESSAGE: "(.*?)"', prompt, re.DOTALL)
        message = message_match.group(1) if message_match else ""

        # Build minimal prompt
        compressed = f"""Analyze: "{message}"
Return JSON with optimized search queries:
{{"queries": [{{"query": "terms", "weight": 1.0, "query_type": "type", "confidence": 0.9}}], "entities": [], "main_topics": [], "intent": "", "search_strategy": ""}}"""

        return compressed


class AdaptivePromptManager:
    """
    Manages adaptive prompting based on LLM performance and user feedback
    """

    def __init__(self):
        self.performance_history = {}
        self.prompt_variations = {}

    def select_optimal_prompt_strategy(
        self, user_id: str, message_type: str, recent_performance: Optional[Dict] = None
    ) -> str:
        """Select the best prompt strategy based on historical performance"""

        # Default strategy
        strategy = "standard"

        # Check historical performance for this user/message type
        key = f"{user_id}_{message_type}"
        if key in self.performance_history:
            history = self.performance_history[key]

            # If recent performance is poor, try alternative strategy
            if history.get("avg_confidence", 0) < 0.7:
                strategy = "enhanced_examples"
            elif history.get("query_relevance", 0) < 0.8:
                strategy = "focused_instructions"

        return strategy

    def update_performance_feedback(
        self, user_id: str, message_type: str, performance_metrics: Dict[str, float]
    ):
        """Update performance history for adaptive improvement"""

        key = f"{user_id}_{message_type}"

        if key not in self.performance_history:
            self.performance_history[key] = {
                "samples": 0,
                "avg_confidence": 0.0,
                "query_relevance": 0.0,
                "memory_recall_success": 0.0,
            }

        history = self.performance_history[key]
        history["samples"] += 1

        # Update running averages
        for metric, value in performance_metrics.items():
            if metric in history:
                current_avg = history[metric]
                new_avg = ((current_avg * (history["samples"] - 1)) + value) / history["samples"]
                history[metric] = new_avg


# Factory function for easy integration
def create_optimized_prompt_engineer(
    enable_user_profiling: bool = True,
    enable_few_shot_examples: bool = True,
    enable_adaptive_prompting: bool = True,
    max_prompt_tokens: int = 800,
) -> AdvancedPromptEngineer:
    """
    Factory function to create an optimized prompt engineer with specified features
    """

    engineer = AdvancedPromptEngineer()

    if not enable_user_profiling:
        engineer.user_profiles = {}

    if not enable_few_shot_examples:
        engineer.few_shot_examples = {}

    # Add token optimizer if needed
    if max_prompt_tokens < 1000:
        engineer.token_optimizer = TokenOptimizer(max_prompt_tokens)

    logger.info(
        f"Advanced prompt engineer created with features: "
        f"user_profiling={enable_user_profiling}, "
        f"few_shot={enable_few_shot_examples}, "
        f"adaptive={enable_adaptive_prompting}"
    )

    return engineer
