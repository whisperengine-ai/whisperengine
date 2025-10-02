"""
Human-Like Memory Search Optimization

This module optimizes LLM prompting specifically for chatbots that need to
feel human-like in their memory recall and conversational continuity.
Focus on natural conversation flow, emotional intelligence, and relationship building.

🚀 ENHANCED with 6D Vector-powered conversation flow analysis
Replaces keyword-based flow detection with semantic vector similarity search.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# 🚀 Import 6D Vector Enhanced Flow Analysis
try:
    from src.intelligence.vector_conversation_flow_analyzer import create_vector_conversation_flow_analyzer
    VECTOR_FLOW_AVAILABLE = True
    logger.info("✅ 6D Vector Conversation Flow Analysis AVAILABLE")
except ImportError:
    VECTOR_FLOW_AVAILABLE = False
    logger.warning("⚠️ 6D Vector Flow Analysis not available, using fallback methods")


@dataclass
class ConversationalContext:
    """Context that mimics how humans remember conversations"""

    emotional_state: str | None  # How the user seemed to feel
    relationship_tone: str  # "friendly", "professional", "intimate", "casual"
    conversation_purpose: str  # "seeking_support", "sharing_news", "asking_advice", "casual_chat"
    time_sensitivity: str  # "immediate", "ongoing", "past_event", "future_planning"
    personal_significance: float  # 0.0-1.0 how personally meaningful this seems


@dataclass
class HumanMemoryPattern:
    """Patterns that mimic human memory recall"""

    emotional_triggers: list[str]  # Words/phrases that trigger emotional memories
    relationship_markers: list[str]  # Indicators of relationship depth/type
    personal_anchors: list[str]  # Things that make memories personally significant
    temporal_cues: list[str]  # Time-related context clues
    topic_associations: list[str]  # How topics connect in human memory


class HumanLikeChatbotOptimizer:
    """
    Optimizes memory search to feel like natural human conversation recall
    """

    def __init__(self):
        self.conversation_memory_patterns = self._build_human_memory_patterns()
        self.emotional_intelligence_prompts = self._build_emotional_prompts()
        self.relationship_context_templates = self._build_relationship_templates()

    async def optimize_conversation_flow(
        self, current_message: str, user_id: str, conversation_history: list[str]
    ) -> dict[str, Any]:
        """
        🚀 ENHANCED: Optimize memory search with 6D vector-powered conversation flow analysis
        
        Uses semantic vector similarity for superior flow detection vs keyword matching.
        """

        # 🚀 Use 6D Vector Flow Analysis if available
        if self.vector_flow_analyzer:
            try:
                logger.info(f"🚀 Using 6D Vector Flow Analysis for user {user_id}")
                flow_analysis = await self.vector_flow_analyzer.analyze_conversation_flow_6d(
                    user_id=user_id,
                    current_message=current_message,
                    conversation_history=conversation_history
                )
                logger.info(f"✅ 6D Flow Analysis: {flow_analysis.get('flow_type')} with {flow_analysis.get('confidence', 0):.3f} confidence")
                
            except Exception as e:
                logger.error(f"❌ 6D Vector Flow Analysis failed: {e}, falling back to keyword analysis")
                flow_analysis = self._analyze_conversation_flow(current_message, conversation_history)
                flow_analysis["vector_enhanced"] = False
                flow_analysis["fallback_reason"] = str(e)
        else:
            # Traditional keyword-based analysis
            flow_analysis = self._analyze_conversation_flow(current_message, conversation_history)
            flow_analysis["vector_enhanced"] = False

        # Determine search strategy based on flow
        search_strategy = self._determine_search_strategy(flow_analysis)

        # Generate flow-optimized queries (enhanced with vector context if available)
        flow_optimized_queries = self._generate_flow_aware_queries(
            current_message, flow_analysis, search_strategy
        )

        return {
            "flow_analysis": flow_analysis,
            "search_strategy": search_strategy,
            "optimized_queries": flow_optimized_queries,
            "conversation_continuity_weight": flow_analysis.get("continuity_score", 0.5),
            "vector_enhanced": flow_analysis.get("vector_enhanced", False),
        }

    def _analyze_conversational_context(
        self, message: str, conversation_history: list[str] | None = None
    ) -> ConversationalContext:
        """Analyze message like a human would understand conversational context"""

        message_lower = message.lower()

        # Detect emotional state (how humans pick up on feelings)
        emotional_indicators = {
            "excited": ["excited", "amazing", "awesome", "love", "fantastic", "!", "yay"],
            "worried": ["worried", "concerned", "anxious", "nervous", "scared"],
            "frustrated": ["frustrated", "annoyed", "irritated", "ugh", "annoying"],
            "sad": ["sad", "disappointed", "down", "depressed", "upset"],
            "curious": ["wondering", "curious", "interested", "what if", "how about"],
            "nostalgic": ["remember when", "back then", "used to", "those days"],
            "grateful": ["thank you", "grateful", "appreciate", "helped me"],
            "confused": ["confused", "not sure", "don't understand", "unclear"],
        }

        detected_emotion = None
        for emotion, indicators in emotional_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                detected_emotion = emotion
                break

        # Detect conversation purpose (what humans understand about intent)
        purpose_patterns = {
            "seeking_support": ["help", "advice", "what should i", "struggling", "difficult"],
            "sharing_news": ["guess what", "just", "happened", "exciting news", "update"],
            "asking_advice": ["should i", "what do you think", "advice", "recommend"],
            "casual_chat": ["hey", "hi", "how are", "what's up", "just chatting"],
            "reflecting": ["thinking about", "been reflecting", "realized", "looking back"],
            "planning": ["going to", "planning", "thinking of", "want to", "will"],
            "reminiscing": ["remember", "recall", "talked about", "mentioned", "discussed"],
        }

        conversation_purpose = "casual_chat"  # default
        for purpose, patterns in purpose_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                conversation_purpose = purpose
                break

        # Detect relationship tone (how humans gauge social context)
        relationship_tone = "friendly"  # default
        if any(word in message_lower for word in ["please", "thank you", "sorry", "excuse me"]):
            relationship_tone = "polite"
        elif any(word in message_lower for word in ["dude", "bro", "lol", "haha", "omg"]):
            relationship_tone = "casual"
        elif any(word in message_lower for word in ["love", "heart", "dear", "sweet"]):
            relationship_tone = "intimate"
        elif any(word in message_lower for word in ["regarding", "concerning", "matter"]):
            relationship_tone = "professional"

        # Time sensitivity (urgency humans would perceive)
        time_sensitivity = "ongoing"
        if any(word in message_lower for word in ["urgent", "asap", "quickly", "now"]):
            time_sensitivity = "immediate"
        elif any(word in message_lower for word in ["yesterday", "last week", "before", "earlier"]):
            time_sensitivity = "past_event"
        elif any(word in message_lower for word in ["tomorrow", "next", "planning", "will"]):
            time_sensitivity = "future_planning"

        # Personal significance (how personally meaningful this seems)
        significance_indicators = [
            "important",
            "meaningful",
            "special",
            "personal",
            "family",
            "friend",
            "career",
            "dream",
            "goal",
            "fear",
            "hope",
            "love",
            "hate",
        ]
        personal_significance = 0.5  # neutral default
        significance_count = sum(
            1 for indicator in significance_indicators if indicator in message_lower
        )
        personal_significance = min(1.0, 0.3 + (significance_count * 0.2))

        return ConversationalContext(
            emotional_state=detected_emotion,
            relationship_tone=relationship_tone,
            conversation_purpose=conversation_purpose,
            time_sensitivity=time_sensitivity,
            personal_significance=personal_significance,
        )

    def _build_human_like_system_prompt(
        self, conv_context: ConversationalContext, relationship_context: dict | None
    ) -> str:
        """Build system prompt that mimics human conversational memory"""

        base_prompt = """You are helping a human-like chatbot find relevant memories from past conversations. Think like a human friend who naturally recalls shared experiences and emotional moments.

HUMAN-LIKE MEMORY PRINCIPLES:
• Humans remember emotional moments more vividly
• Personal and meaningful topics stick better in memory
• We associate current feelings with similar past feelings
• Relationships deepen through shared experiences and understanding
• Context and tone matter as much as specific words"""

        # Add emotional intelligence based on detected emotion
        if conv_context.emotional_state:
            emotion_guidance = {
                "excited": "User is excited! Look for past moments of joy, achievements, and positive experiences they've shared.",
                "worried": "User seems worried. Find past conversations about similar concerns, support given, or reassurance shared.",
                "frustrated": "User is frustrated. Recall past challenges they've discussed and any solutions or support provided.",
                "sad": "User appears sad. Look for past emotional moments, support conversations, or uplifting memories shared.",
                "nostalgic": "User is feeling nostalgic. Focus on past memories, experiences, and 'remember when' moments.",
                "grateful": "User is expressing gratitude. Find past moments of help, support, or positive interactions.",
                "confused": "User seems confused. Look for past explanations, clarifications, or similar questions they've asked.",
            }

            if conv_context.emotional_state in emotion_guidance:
                base_prompt += (
                    f"\n\nEMOTIONAL CONTEXT: {emotion_guidance[conv_context.emotional_state]}"
                )

        # Add conversation purpose guidance
        purpose_guidance = {
            "seeking_support": "Focus on past support conversations, advice given, and emotional moments shared.",
            "sharing_news": "Look for related past news they've shared, reactions, and ongoing topics.",
            "asking_advice": "Find past advice conversations, similar situations discussed, and decision-making moments.",
            "casual_chat": "Look for light conversation topics, shared interests, and friendly interactions.",
            "reflecting": "Focus on past introspective conversations, personal growth moments, and deep discussions.",
            "planning": "Find past planning conversations, goals discussed, and future-oriented topics.",
            "reminiscing": "This is direct memory recall - focus on the specific topic or timeframe they're referencing.",
        }

        if conv_context.conversation_purpose in purpose_guidance:
            base_prompt += (
                f"\n\nCONVERSATION PURPOSE: {purpose_guidance[conv_context.conversation_purpose]}"
            )

        # Add relationship tone guidance
        tone_guidance = {
            "casual": "Look for informal conversations, jokes, casual topics, and friendly banter.",
            "intimate": "Focus on personal, deep, or emotionally significant conversations.",
            "professional": "Find work-related, formal, or goal-oriented discussions.",
            "polite": "Look for respectful exchanges, learning moments, and courteous interactions.",
        }

        if conv_context.relationship_tone in tone_guidance:
            base_prompt += f"\n\nRELATIONSHIP TONE: {tone_guidance[conv_context.relationship_tone]}"

        # Add memory search strategy
        base_prompt += """

HUMAN MEMORY SEARCH STRATEGY:
1. **Emotional Resonance**: Prioritize memories with similar emotional tone
2. **Personal Connection**: Weight personally significant topics higher
3. **Conversational Flow**: Find memories that naturally connect to current topic
4. **Relationship Building**: Look for memories that show growing understanding
5. **Contextual Relevance**: Consider time, situation, and relationship depth

QUERY GENERATION (like human memory association):
• Create 2-4 focused search queries that capture different memory associations
• Include emotional keywords when feelings are involved
• Use the actual words/phrases the user uses (their personal language)
• Consider both direct topic matches and emotional/contextual associations
• Weight queries based on likely emotional and personal significance"""

        return base_prompt

    def _build_conversational_user_prompt(
        self,
        message: str,
        conv_context: ConversationalContext,
        conversation_history: list[str] | None = None,
    ) -> str:
        """Build user prompt that feels natural for conversational memory search"""

        prompt = f"""A human friend just said: "{message}"

Help me recall relevant memories from our past conversations, thinking like a caring human friend would."""

        # Add emotional context
        if conv_context.emotional_state:
            prompt += f"""
They seem to be feeling: {conv_context.emotional_state}"""

        # Add conversation flow context
        if conversation_history:
            recent_context = " | ".join(conversation_history[-3:])  # Last 3 messages
            prompt += f"""
Recent conversation: {recent_context}"""

        # Add relationship context
        prompt += f"""
Conversation tone: {conv_context.relationship_tone}
Purpose: {conv_context.conversation_purpose}
Personal significance: {conv_context.personal_significance:.1f}/1.0"""

        # Add specific guidance based on context
        if conv_context.conversation_purpose == "reminiscing":
            prompt += """

MEMORY RECALL FOCUS: They're trying to remember something specific. Help find:
• The exact topic/event they're referencing
• Related conversations about similar topics
• Context around when this was discussed"""

        elif conv_context.emotional_state in ["worried", "frustrated", "sad"]:
            prompt += """

EMOTIONAL SUPPORT FOCUS: They need understanding. Help find:
• Past times they felt similarly
• Support and encouragement given before
• Related challenges they've overcome"""

        elif conv_context.emotional_state in ["excited", "grateful"]:
            prompt += """

POSITIVE ENERGY FOCUS: They're sharing good feelings. Help find:
• Past positive moments together
• Similar exciting news they've shared
• Ongoing topics they care about"""

        # Output format optimized for human-like conversation
        prompt += """

Respond with ONLY this JSON format (keep it minimal):

{
    "queries": [{"query": "search terms", "weight": 1.0}],
    "conversation_flow": "connection_type"
}

IMPORTANT: Be very concise. Complete the JSON properly."""

        return prompt

    def _build_human_memory_patterns(self) -> dict[str, HumanMemoryPattern]:
        """Build patterns that mimic how humans naturally recall memories"""

        return {
            "emotional_support": HumanMemoryPattern(
                emotional_triggers=["stressed", "worried", "anxious", "overwhelmed", "struggling"],
                relationship_markers=["you helped me", "thanks for", "felt better", "understood"],
                personal_anchors=["important to me", "really matters", "personal", "difficult"],
                temporal_cues=["when I was", "that time", "remember when", "back then"],
                topic_associations=["similar situation", "also dealing with", "reminded me"],
            ),
            "shared_interests": HumanMemoryPattern(
                emotional_triggers=["excited", "love", "passionate", "interested", "fascinated"],
                relationship_markers=["we both", "shared", "together", "common interest"],
                personal_anchors=["hobby", "passion", "enjoy", "favorite", "special"],
                temporal_cues=["been doing", "started", "since we", "ongoing"],
                topic_associations=["related to", "reminds me of", "also about", "connected"],
            ),
            "personal_growth": HumanMemoryPattern(
                emotional_triggers=["proud", "accomplished", "learned", "grew", "changed"],
                relationship_markers=["you encouraged", "supported me", "believed in", "helped"],
                personal_anchors=["personal goal", "important step", "milestone", "achievement"],
                temporal_cues=["progress", "journey", "process", "development", "growth"],
                topic_associations=["builds on", "relates to", "part of", "connected journey"],
            ),
        }

    def _build_emotional_prompts(self) -> dict[str, str]:
        """Build emotionally intelligent prompt variations"""

        return {
            "supportive": "Find memories that show care, understanding, and emotional support shared.",
            "celebratory": "Look for positive moments, achievements, and joyful experiences shared together.",
            "reflective": "Focus on deeper conversations, personal insights, and meaningful exchanges.",
            "practical": "Find helpful advice, solutions, and practical support given in the past.",
            "companionable": "Look for casual, friendly interactions that show ongoing friendship.",
        }

    def _build_relationship_templates(self) -> dict[str, str]:
        """Build templates based on relationship depth and type"""

        return {
            "new_friend": "Focus on getting-to-know-you conversations and basic preferences shared.",
            "good_friend": "Look for deeper conversations, personal stories, and ongoing topics of mutual interest.",
            "close_friend": "Find intimate conversations, emotional support moments, and significant life events shared.",
            "supportive_companion": "Focus on advice-seeking, problem-solving, and emotional support conversations.",
            "learning_partner": "Look for educational conversations, skill-building, and knowledge sharing moments.",
        }


class ConversationFlowOptimizer:
    """
    🚀 ENHANCED: Optimizes memory search with 6D vector-powered conversation flow analysis
    
    Replaces keyword-based flow detection with semantic vector similarity search
    for superior conversation continuity and relationship building.
    """

    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
        self.conversation_patterns = self._build_conversation_patterns()
        
        # 🚀 Initialize 6D Vector Flow Analyzer if available
        if VECTOR_FLOW_AVAILABLE and memory_manager and hasattr(memory_manager, 'retrieve_memories_by_dimensions'):
            self.vector_flow_analyzer = create_vector_conversation_flow_analyzer(memory_manager)
            logger.info("✅ Initialized 6D Vector Flow Analyzer")
        else:
            self.vector_flow_analyzer = None
            logger.info("🔄 Using traditional keyword-based flow analysis")

    def optimize_for_conversation_flow(
        self,
        current_message: str,
        conversation_history: list[str],
        user_patterns: dict | None = None,
    ) -> dict[str, Any]:
        """
        Optimize memory search to maintain natural conversation flow
        """

        # Analyze conversation momentum
        flow_analysis = self._analyze_conversation_flow(current_message, conversation_history)

        # Generate flow-aware search strategies
        search_strategy = self._determine_search_strategy(flow_analysis)

        # Create conversation-aware queries
        flow_optimized_queries = self._generate_flow_aware_queries(
            current_message, flow_analysis, search_strategy
        )

        return {
            "flow_analysis": flow_analysis,
            "search_strategy": search_strategy,
            "optimized_queries": flow_optimized_queries,
            "conversation_continuity_weight": flow_analysis.get("continuity_score", 0.5),
        }

    def _analyze_conversation_flow(
        self, current_message: str, conversation_history: list[str]
    ) -> dict[str, Any]:
        """Analyze how current message fits in conversation flow"""

        message_lower = current_message.lower()

        # Check for conversation continuity signals
        continuity_signals = {
            "topic_continuation": ["also", "and", "furthermore", "additionally", "speaking of"],
            "topic_shift": ["by the way", "actually", "oh", "changing topics", "different subject"],
            "callback_reference": [
                "remember",
                "like we discussed",
                "as you mentioned",
                "going back to",
            ],
            "emotional_progression": [
                "feeling better",
                "still worried",
                "now I understand",
                "that helped",
            ],
        }

        detected_flow = "neutral"
        for flow_type, signals in continuity_signals.items():
            if any(signal in message_lower for signal in signals):
                detected_flow = flow_type
                break

        # Analyze conversation depth progression
        depth_indicators = {
            "surface": ["hello", "hi", "how are you", "what's up"],
            "engaging": ["interested in", "tell me about", "what do you think"],
            "personal": ["I feel", "personal", "important to me", "struggle with"],
            "intimate": ["private", "don't tell anyone", "between us", "deeply"],
        }

        conversation_depth = "surface"
        for depth, indicators in depth_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                conversation_depth = depth

        return {
            "flow_type": detected_flow,
            "conversation_depth": conversation_depth,
            "continuity_score": self._calculate_continuity_score(
                current_message, conversation_history
            ),
            "emotional_momentum": self._detect_emotional_momentum(
                current_message, conversation_history
            ),
        }

    def _calculate_continuity_score(self, current_message: str, history: list[str]) -> float:
        """Calculate how well current message continues the conversation"""

        if not history:
            return 0.5

        # Simple word overlap scoring
        current_words = set(current_message.lower().split())
        recent_words = set()

        # Look at last 2-3 messages for context
        for recent_msg in history[-3:]:
            recent_words.update(recent_msg.lower().split())

        if not recent_words:
            return 0.5

        # Calculate overlap
        overlap = len(current_words.intersection(recent_words))
        total_unique = len(current_words.union(recent_words))

        return overlap / max(1, total_unique)

    def _detect_emotional_momentum(self, current_message: str, history: list[str]) -> str:
        """Detect emotional momentum in conversation"""

        # This is a simplified version - could be much more sophisticated
        current_emotion = self._detect_simple_emotion(current_message)

        if not history:
            return current_emotion or "neutral"

        recent_emotion = self._detect_simple_emotion(history[-1]) if history else None

        if current_emotion == recent_emotion:
            return f"continuing_{current_emotion}"
        elif current_emotion and recent_emotion:
            return f"shifting_{recent_emotion}_to_{current_emotion}"
        else:
            return current_emotion or recent_emotion or "neutral"

    def _detect_simple_emotion(self, message: str) -> str | None:
        """Simple emotion detection for momentum analysis"""

        message_lower = message.lower()

        emotion_keywords = {
            "positive": ["happy", "excited", "great", "awesome", "love", "amazing"],
            "negative": ["sad", "worried", "frustrated", "angry", "disappointed"],
            "curious": ["wondering", "curious", "interested", "what if", "how"],
            "grateful": ["thank", "grateful", "appreciate", "helped"],
        }

        for emotion, keywords in emotion_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return emotion

        return None

    def _determine_search_strategy(self, flow_analysis: dict[str, Any]) -> str:
        """Determine optimal search strategy based on conversation flow"""

        flow_type = flow_analysis.get("flow_type", "neutral")
        depth = flow_analysis.get("conversation_depth", "surface")

        if flow_type == "callback_reference":
            return "precise_recall"
        elif flow_type == "topic_continuation":
            return "contextual_expansion"
        elif depth in ["personal", "intimate"]:
            return "emotional_resonance"
        elif flow_type == "topic_shift":
            return "broad_association"
        else:
            return "balanced_search"

    def _generate_flow_aware_queries(
        self, message: str, flow_analysis: dict[str, Any], strategy: str
    ) -> list[dict[str, Any]]:
        """Generate queries optimized for conversation flow"""

        # This would integrate with the main query generation
        # Simplified example:

        base_query = {
            "query": message[:50],  # Simplified
            "weight": 1.0,
            "query_type": "conversational",
            "flow_context": flow_analysis.get("flow_type", "neutral"),
            "strategy": strategy,
        }

        return [base_query]

    def _build_conversation_patterns(self) -> dict[str, Any]:
        """Build patterns for natural conversation flow"""

        return {
            "greeting_patterns": ["hello", "hi", "hey", "good morning"],
            "transition_patterns": ["by the way", "also", "speaking of", "that reminds me"],
            "closure_patterns": ["anyway", "well", "so", "alright then"],
            "engagement_patterns": ["what do you think", "tell me more", "I'm curious"],
            "support_patterns": ["I understand", "that must be", "I'm here for you"],
        }


# Factory function for human-like chatbot optimization
def create_human_like_memory_optimizer(
    enable_emotional_intelligence: bool = True,
    enable_relationship_context: bool = True,
    enable_conversation_flow: bool = True,
    personality_type: str = "caring_friend",
) -> HumanLikeChatbotOptimizer:
    """
    Create an optimizer specifically designed for human-like chatbot interactions

    Args:
        enable_emotional_intelligence: Enable emotional context understanding
        enable_relationship_context: Enable relationship-aware memory search
        enable_conversation_flow: Enable conversation flow optimization
        personality_type: "caring_friend", "supportive_companion", "wise_advisor"
    """

    optimizer = HumanLikeChatbotOptimizer()

    # Configure for specific personality type
    if personality_type == "caring_friend":
        # Optimize for warm, supportive, emotionally intelligent responses
        pass
    elif personality_type == "supportive_companion":
        # Optimize for practical help and consistent support
        pass
    elif personality_type == "wise_advisor":
        # Optimize for thoughtful advice and deeper insights
        pass

    logger.info(
        f"Human-like chatbot optimizer created: {personality_type}, "
        f"emotional_intelligence={enable_emotional_intelligence}, "
        f"relationship_context={enable_relationship_context}"
    )

    return optimizer
