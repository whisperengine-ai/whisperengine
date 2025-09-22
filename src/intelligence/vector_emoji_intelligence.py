"""
Intelligent Emoji Response System with Vector-Powered Context Awareness

This system combines:
- Qdrant vector similarity search for historical emoji patterns
- Security validation integration for inappropriate content responses
- Character-aware emoji selection using personality vectors
- Emotional intelligence from existing emoji reaction system
- Context-aware decision making for when to use emoji vs text responses

Architecture:
1. Vector Context Analysis: Uses Qdrant to find similar past conversations and their emoji patterns
2. Emotional Pattern Matching: Leverages existing emoji reaction intelligence for output selection
3. Security Integration: Automatically uses emoji responses for inappropriate/filtered content
4. Character Awareness: Selects emojis that match bot personality (mystical vs technical)
5. Adaptive Learning: Learns from successful emoji interactions to improve future selections
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum

# Import existing systems
from src.intelligence.emoji_reaction_intelligence import EmojiEmotionMapper
from src.security.input_validator import validate_user_input
from src.memory.memory_protocol import MemoryManagerProtocol

logger = logging.getLogger(__name__)


class EmojiResponseContext(Enum):
    """Context types that determine emoji response appropriateness"""
    INAPPROPRIATE_CONTENT = "inappropriate_content"  # Security filtered content
    EMOTIONAL_OVERWHELM = "emotional_overwhelm"     # High emotional intensity 
    SIMPLE_ACKNOWLEDGMENT = "simple_acknowledgment" # Brief confirmations
    PLAYFUL_INTERACTION = "playful_interaction"     # Fun, light conversations
    TECHNICAL_APPRECIATION = "technical_appreciation" # Code/tech discussions
    MYSTICAL_WONDER = "mystical_wonder"             # Spiritual/mystical topics
    REPEATED_PATTERN = "repeated_pattern"           # User has pattern of emoji preferences
    CONVERSATION_CLOSER = "conversation_closer"     # Natural conversation endings


@dataclass
class EmojiResponseDecision:
    """Decision result for emoji vs text response"""
    should_use_emoji: bool
    emoji_choice: Optional[str]
    confidence_score: float
    context_reason: EmojiResponseContext
    fallback_text: Optional[str]
    supporting_evidence: Dict[str, Any]


@dataclass
class ConversationPattern:
    """Pattern analysis from vector similarity search"""
    similar_conversations: List[Dict[str, Any]]
    emoji_success_rate: float
    preferred_emojis: List[Tuple[str, float]]  # (emoji, frequency)
    emotional_context: str
    personality_match: float
    communication_patterns: Optional[Dict[str, Any]] = None  # Added for enhanced analysis


class VectorEmojiIntelligence:
    """
    🧠 Vector-Powered Emoji Response Intelligence System
    
    Uses Qdrant vector similarity to analyze:
    - Historical conversation patterns and emoji usage
    - User emotional preferences from reaction history
    - Similar context situations and their successful responses
    - Character personality alignment for emoji selection
    """
    
    def __init__(
        self, 
        memory_manager: MemoryManagerProtocol,
        emoji_mapper: Optional[EmojiEmotionMapper] = None
    ):
        self.memory_manager = memory_manager
        self.emoji_mapper = emoji_mapper or EmojiEmotionMapper()
        
        # Read emoji configuration from environment
        self.emoji_enabled = os.getenv("EMOJI_ENABLED", "true").lower() == "true"
        self.base_threshold = float(os.getenv("EMOJI_BASE_THRESHOLD", "0.4"))
        self.new_user_threshold = float(os.getenv("EMOJI_NEW_USER_THRESHOLD", "0.3"))
        self.visual_reaction_enabled = os.getenv("VISUAL_REACTION_ENABLED", "true").lower() == "true"
        
        # Character-specific emoji sets
        self.character_emoji_sets = {
            "mystical": {
                "wonder": ["🔮", "✨", "🌟", "🪄", "🌙", "⭐"],
                "positive": ["💫", "🌈", "🦋", "🌸", "🍃"],
                "acknowledgment": ["🙏", "✨", "🔮"],
                "playful": ["🪄", "✨", "🌟", "💫"],
                "negative": ["🌧️", "🥀", "🌫️"]
            },
            "technical": {
                "wonder": ["🤖", "⚡", "💻", "🔧", "⚙️", "🛠️"],
                "positive": ["💡", "🚀", "⚡", "🔥", "💪"],
                "acknowledgment": ["👍", "✅", "🤖"],
                "playful": ["🤖", "🔧", "⚡", "🚀"],
                "negative": ["⚠️", "🔴", "❌"]
            },
            "general": {
                "wonder": ["😍", "🤩", "😲", "✨", "🌟"],
                "positive": ["😊", "❤️", "👍", "🎉", "😄"],
                "acknowledgment": ["👍", "✅", "😊"],
                "playful": ["😄", "😉", "🎉", "😆"],
                "negative": ["😕", "😔", "💔", "😞"]
            }
        }
        
        logger.info("🧠 VectorEmojiIntelligence initialized with character-aware emoji sets")
        logger.info("🎯 Emoji config: enabled=%s, base_threshold=%.2f, new_user_threshold=%.2f", 
                   self.emoji_enabled, self.base_threshold, self.new_user_threshold)
    
    async def should_respond_with_emoji(
        self,
        user_id: str,
        user_message: str,
        bot_character: str = "general",
        security_validation_result: Optional[Dict[str, Any]] = None,
        emotional_context: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> EmojiResponseDecision:
        """
        🎯 MAIN DECISION ENGINE: Determine if emoji response is appropriate
        
        Uses comprehensive multi-factor analysis:
        1. Security validation (inappropriate content = emoji response)
        2. Vector similarity search for historical patterns
        3. User personality profile analysis
        4. Current emotional state assessment
        5. Conversation history patterns
        6. Character personality alignment
        7. Communication style preferences
        8. Relationship context (rapport, conversation depth)
        """
        try:
            logger.info(f"🎯 Analyzing emoji response appropriateness for user {user_id}")
            
            # 1. Security-First: Check for inappropriate content
            if security_validation_result and not security_validation_result.get("is_safe", True):
                return await self._handle_inappropriate_content(
                    user_id, user_message, bot_character, security_validation_result
                )
            
            # 2. User Personality Profile Analysis
            personality_context = await self._analyze_user_personality_context(user_id)
            
            # 3. Current Emotional State Assessment
            emotional_state = await self._analyze_current_emotional_state(
                user_id, user_message, emotional_context
            )
            
            # 4. Conversation History Pattern Analysis
            conversation_patterns = await self._analyze_comprehensive_conversation_patterns(
                user_id, user_message, bot_character
            )
            
            # 5. Communication Style Preference Analysis
            communication_style = await self._analyze_communication_style_preferences(
                user_id, conversation_patterns, personality_context
            )
            
            # 6. Relationship Context Assessment
            relationship_context = await self._assess_relationship_context(
                user_id, conversation_patterns, personality_context
            )
            
            # 7. Character Personality Alignment
            personality_alignment = self._calculate_enhanced_personality_alignment(
                user_message, bot_character, personality_context
            )
            
            # 8. Conversation Context Assessment
            context_score = self._assess_enhanced_conversation_context(
                user_message, conversation_context, emotional_state, personality_context
            )
            
            # 9. Synthesize Enhanced Decision
            decision = await self._synthesize_enhanced_emoji_decision(
                user_id=user_id,
                user_message=user_message,
                bot_character=bot_character,
                personality_context=personality_context,
                emotional_state=emotional_state,
                conversation_patterns=conversation_patterns,
                communication_style=communication_style,
                relationship_context=relationship_context,
                personality_alignment=personality_alignment,
                context_score=context_score
            )
            
            logger.info(f"🎯 Enhanced emoji decision: {decision.should_use_emoji} (confidence: {decision.confidence_score:.2f})")
            return decision
            
        except Exception as e:
            logger.error(f"Error in enhanced emoji response analysis: {e}")
            # Safe fallback: never use emoji if there's an error
            return EmojiResponseDecision(
                should_use_emoji=False,
                emoji_choice=None,
                confidence_score=0.0,
                context_reason=EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT,
                fallback_text=None,
                supporting_evidence={"error": str(e)}
            )
    
    async def _handle_inappropriate_content(
        self,
        user_id: str,
        user_message: str,
        bot_character: str,
        security_result: Dict[str, Any]
    ) -> EmojiResponseDecision:
        """Handle inappropriate content with contextually appropriate emoji response"""
        logger.warning(f"🚫 Inappropriate content detected from user {user_id}, using emoji response")
        
        # Choose character-appropriate emoji for inappropriate content
        if bot_character == "mystical":
            emoji_choice = "🌫️"  # Mystical way of expressing "that's not clear/appropriate"
        elif bot_character == "technical":
            emoji_choice = "⚠️"  # Technical warning symbol
        else:
            emoji_choice = "😐"  # General neutral expression
        
        return EmojiResponseDecision(
            should_use_emoji=True,
            emoji_choice=emoji_choice,
            confidence_score=0.95,  # High confidence for security reasons
            context_reason=EmojiResponseContext.INAPPROPRIATE_CONTENT,
            fallback_text="I can't respond to that appropriately.",
            supporting_evidence={
                "security_blocked_patterns": security_result.get("blocked_patterns", []),
                "security_warnings": security_result.get("warnings", [])
            }
        )
    
    async def _analyze_conversation_patterns(
        self,
        user_id: str,
        user_message: str,
        bot_character: str
    ) -> ConversationPattern:
        """
        🔍 VECTOR ANALYSIS: Use Qdrant to find similar conversations and emoji patterns
        """
        try:
            # Search for similar conversations using vector similarity
            similar_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=user_message,
                limit=20  # Get more results for pattern analysis
            )
            
            # Extract emoji usage patterns from similar conversations
            emoji_interactions = []
            for memory in similar_memories:
                metadata = memory.get("metadata", {})
                
                # Look for emoji reaction data in metadata
                if "emoji_reaction" in metadata:
                    emoji_interactions.append({
                        "emoji": metadata["emoji_reaction"],
                        "context": memory.get("content", ""),
                        "score": memory.get("score", 0.0),
                        "timestamp": memory.get("timestamp")
                    })
            
            # Calculate emoji success patterns
            emoji_frequency = {}
            total_interactions = len(emoji_interactions)
            
            for interaction in emoji_interactions:
                emoji = interaction["emoji"]
                emoji_frequency[emoji] = emoji_frequency.get(emoji, 0) + 1
            
            # Sort by frequency and calculate success rate
            preferred_emojis = [
                (emoji, count / total_interactions) 
                for emoji, count in sorted(emoji_frequency.items(), key=lambda x: x[1], reverse=True)
            ]
            
            # Calculate overall emoji success rate
            emoji_success_rate = min(len(emoji_interactions) / max(len(similar_memories), 1), 1.0)
            
            # Determine dominant emotional context from similar conversations
            emotional_context = self._extract_dominant_emotion(similar_memories)
            
            # Calculate personality match score
            personality_match = self._calculate_conversation_personality_match(
                similar_memories, bot_character
            )
            
            return ConversationPattern(
                similar_conversations=similar_memories,
                emoji_success_rate=emoji_success_rate,
                preferred_emojis=preferred_emojis,
                emotional_context=emotional_context,
                personality_match=personality_match
            )
            
        except Exception as e:
            logger.error(f"Error analyzing conversation patterns: {e}")
            return ConversationPattern(
                similar_conversations=[],
                emoji_success_rate=0.0,
                preferred_emojis=[],
                emotional_context="neutral",
                personality_match=0.5
            )
    
    def _analyze_message_emotions(self, user_message: str) -> List[str]:
        """Simple emotion analysis by keyword detection"""
        message_lower = user_message.lower()
        emotions = []
        
        # Positive emotions
        if any(word in message_lower for word in ["happy", "joy", "great", "awesome", "love", "excited"]):
            emotions.append("joy")
        if any(word in message_lower for word in ["thank", "grateful", "appreciate"]):
            emotions.append("gratitude")
        if any(word in message_lower for word in ["amazing", "incredible", "wow", "fantastic"]):
            emotions.append("wonder")
        
        # Negative emotions
        if any(word in message_lower for word in ["sad", "upset", "disappointed", "frustrated"]):
            emotions.append("sadness")
        if any(word in message_lower for word in ["angry", "mad", "annoyed", "irritated"]):
            emotions.append("anger")
        
        return emotions
    
    async def _analyze_user_personality_context(self, user_id: str) -> Dict[str, Any]:
        """
        🧠 PERSONALITY ANALYSIS: Get comprehensive user personality context
        """
        try:
            # Try to get personality profile from dynamic personality profiler
            personality_context = {
                "communication_style": "neutral",
                "emotional_expressiveness": 0.5,
                "formality_preference": 0.5,
                "detail_preference": 0.5,
                "social_engagement": 0.5,
                "humor_appreciation": 0.5,
                "response_preference": "balanced",
                "emoji_comfort_level": 0.5
            }
            
            # Search for personality-related memories
            personality_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="personality traits communication style preferences",
                limit=15
            )
            
            # Analyze personality patterns from conversation history
            if personality_memories:
                formality_scores = []
                emoji_usage_count = 0
                total_messages = len(personality_memories)
                
                for memory in personality_memories:
                    content = memory.get("content", "")
                    metadata = memory.get("metadata", {})
                    
                    # Analyze formality
                    formality_score = self._analyze_message_formality(content)
                    formality_scores.append(formality_score)
                    
                    # Count emoji usage
                    if any(char in content for char in "😀😁😂😃😄😅😆😇😈😉😊😋😌😍😎😏"):
                        emoji_usage_count += 1
                
                # Calculate personality metrics
                if formality_scores:
                    personality_context["formality_preference"] = sum(formality_scores) / len(formality_scores)
                
                personality_context["emoji_comfort_level"] = emoji_usage_count / max(total_messages, 1)
                
                # Determine communication style based on patterns
                if personality_context["formality_preference"] > 0.7:
                    personality_context["communication_style"] = "formal"
                elif personality_context["formality_preference"] < 0.3:
                    personality_context["communication_style"] = "casual"
                else:
                    personality_context["communication_style"] = "balanced"
            
            logger.debug(f"🧠 Personality context for user {user_id}: {personality_context}")
            return personality_context
            
        except Exception as e:
            logger.error(f"Error analyzing personality context: {e}")
            return {
                "communication_style": "neutral",
                "emotional_expressiveness": 0.5,
                "emoji_comfort_level": 0.5
            }
    
    def _analyze_message_formality(self, content: str) -> float:
        """Analyze formality level of a message (0=casual, 1=formal)"""
        content_lower = content.lower()
        
        formal_indicators = [
            "please", "thank you", "could you", "would you", "may i", 
            "i would like", "i appreciate", "sincerely", "regards"
        ]
        
        casual_indicators = [
            "hey", "hi", "yo", "sup", "lol", "haha", "omg", "btw", 
            "gonna", "wanna", "yeah", "yep", "nah", "cool", "awesome"
        ]
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in content_lower)
        casual_count = sum(1 for indicator in casual_indicators if indicator in content_lower)
        
        total_indicators = formal_count + casual_count
        if total_indicators == 0:
            return 0.5  # Neutral
        
        return formal_count / total_indicators
    
    async def _analyze_current_emotional_state(
        self, 
        user_id: str, 
        user_message: str, 
        emotional_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        💗 EMOTIONAL STATE ANALYSIS: Assess user's current emotional state
        """
        try:
            emotional_state = {
                "current_emotion": "neutral",
                "intensity": 0.5,
                "emotional_trajectory": "stable",
                "needs_emotional_support": False,
                "prefers_emoji_comfort": False
            }
            
            # Analyze current message emotions
            current_emotions = self._analyze_message_emotions(user_message)
            
            # Get recent emotional pattern from memory
            recent_emotional_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="emotional feeling mood",
                limit=10
            )
            
            # Analyze emotional trajectory from recent conversations
            if recent_emotional_memories:
                recent_emotions = []
                for memory in recent_emotional_memories:
                    content = memory.get("content", "")
                    metadata = memory.get("metadata", {})
                    
                    # Extract emotional context from metadata
                    if "emotional_context" in metadata:
                        recent_emotions.append(metadata["emotional_context"])
                    
                    # Analyze content for emotions
                    content_emotions = self._analyze_message_emotions(content)
                    recent_emotions.extend(content_emotions)
                
                # Determine emotional trajectory
                if recent_emotions:
                    positive_emotions = ["joy", "gratitude", "excitement", "wonder"]
                    negative_emotions = ["sadness", "anger", "frustration", "disappointment"]
                    
                    positive_count = sum(1 for emotion in recent_emotions if emotion in positive_emotions)
                    negative_count = sum(1 for emotion in recent_emotions if emotion in negative_emotions)
                    
                    if positive_count > negative_count * 1.5:
                        emotional_state["emotional_trajectory"] = "improving"
                    elif negative_count > positive_count * 1.5:
                        emotional_state["emotional_trajectory"] = "declining"
                        emotional_state["needs_emotional_support"] = True
                        emotional_state["prefers_emoji_comfort"] = True
            
            # Set current emotion based on message analysis
            if current_emotions:
                emotional_state["current_emotion"] = current_emotions[0]
                
                # Calculate intensity based on message patterns
                intensity_indicators = ["very", "really", "so", "extremely", "incredibly", "!!", "!!!"]
                message_lower = user_message.lower()
                intensity_score = sum(1 for indicator in intensity_indicators if indicator in message_lower)
                emotional_state["intensity"] = min(0.5 + (intensity_score * 0.2), 1.0)
            
            logger.debug(f"💗 Emotional state for user {user_id}: {emotional_state}")
            return emotional_state
            
        except Exception as e:
            logger.error(f"Error analyzing emotional state: {e}")
            return {
                "current_emotion": "neutral",
                "intensity": 0.5,
                "emotional_trajectory": "stable",
                "needs_emotional_support": False,
                "prefers_emoji_comfort": False
            }
    
    async def _analyze_comprehensive_conversation_patterns(
        self,
        user_id: str,
        user_message: str,
        bot_character: str
    ) -> ConversationPattern:
        """
        🔍 ENHANCED VECTOR ANALYSIS: Comprehensive conversation pattern analysis
        """
        try:
            # Get broader conversation history for pattern analysis
            similar_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=user_message,
                limit=30  # Increased for better pattern analysis
            )
            
            # Also get general conversation history for this user
            recent_conversations = await self.memory_manager.get_conversation_history(
                user_id=user_id,
                limit=20
            )
            
            # Combine and analyze all conversation data
            all_conversations = similar_memories + recent_conversations
            
            # Extract emoji patterns and communication preferences
            emoji_interactions = []
            communication_patterns = {
                "avg_message_length": 0,
                "question_frequency": 0,
                "emoji_in_messages": 0,
                "response_types": {"text": 0, "emoji": 0, "mixed": 0}
            }
            
            total_messages = len(all_conversations)
            total_length = 0
            question_count = 0
            emoji_message_count = 0
            
            for memory in all_conversations:
                content = memory.get("content", "")
                metadata = memory.get("metadata", {})
                
                # Track message patterns
                total_length += len(content)
                if "?" in content:
                    question_count += 1
                if any(char in content for char in "😀😁😂😃😄😅😆😇😈😉😊😋😌😍😎😏"):
                    emoji_message_count += 1
                
                # Look for emoji reaction data
                if "emoji_reaction" in metadata:
                    emoji_interactions.append({
                        "emoji": metadata["emoji_reaction"],
                        "context": content,
                        "score": memory.get("score", 0.0),
                        "timestamp": memory.get("timestamp")
                    })
                
                # Analyze response types
                if metadata.get("response_type") == "emoji":
                    communication_patterns["response_types"]["emoji"] += 1
                elif content and any(char in content for char in "😀😁😂😃😄😅😆😇😈😉😊😋😌😍😎😏"):
                    communication_patterns["response_types"]["mixed"] += 1
                else:
                    communication_patterns["response_types"]["text"] += 1
            
            # Calculate communication metrics
            if total_messages > 0:
                communication_patterns["avg_message_length"] = total_length / total_messages
                communication_patterns["question_frequency"] = question_count / total_messages
                communication_patterns["emoji_in_messages"] = emoji_message_count / total_messages
            
            # Calculate emoji success patterns
            emoji_frequency = {}
            for interaction in emoji_interactions:
                emoji = interaction["emoji"]
                emoji_frequency[emoji] = emoji_frequency.get(emoji, 0) + 1
            
            preferred_emojis = [
                (emoji, count / len(emoji_interactions)) 
                for emoji, count in sorted(emoji_frequency.items(), key=lambda x: x[1], reverse=True)
            ] if emoji_interactions else []
            
            # Enhanced emoji success rate calculation
            emoji_success_rate = 0.0
            if total_messages > 0:
                emoji_preference_score = communication_patterns["emoji_in_messages"]
                emoji_response_score = communication_patterns["response_types"]["emoji"] / total_messages
                emoji_success_rate = (emoji_preference_score + emoji_response_score) / 2
            
            emotional_context = self._extract_dominant_emotion(all_conversations)
            personality_match = self._calculate_conversation_personality_match(all_conversations, bot_character)
            
            pattern = ConversationPattern(
                similar_conversations=all_conversations,
                emoji_success_rate=emoji_success_rate,
                preferred_emojis=preferred_emojis,
                emotional_context=emotional_context,
                personality_match=personality_match
            )
            
            # Add communication patterns as additional data
            pattern.communication_patterns = communication_patterns
            
            return pattern
            
        except Exception as e:
            logger.error(f"Error in comprehensive conversation analysis: {e}")
            return ConversationPattern(
                similar_conversations=[],
                emoji_success_rate=0.0,
                preferred_emojis=[],
                emotional_context="neutral",
                personality_match=0.5
            )
    
    async def _analyze_communication_style_preferences(
        self,
        user_id: str,
        conversation_patterns: ConversationPattern,
        personality_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        💬 COMMUNICATION STYLE: Analyze user's preferred communication style
        """
        communication_style = {
            "prefers_brief_responses": False,
            "emoji_comfort_level": 0.5,
            "formality_preference": "balanced",
            "visual_communication_preference": 0.5,
            "emotional_expression_style": "moderate"
        }
        
        try:
            # Use conversation patterns to determine preferences
            patterns = getattr(conversation_patterns, 'communication_patterns', {})
            
            if patterns:
                # Brief response preference
                avg_length = patterns.get("avg_message_length", 50)
                communication_style["prefers_brief_responses"] = avg_length < 30
                
                # Emoji comfort level
                emoji_usage = patterns.get("emoji_in_messages", 0)
                communication_style["emoji_comfort_level"] = emoji_usage
                
                # Visual communication preference
                emoji_vs_text = patterns.get("response_types", {})
                total_responses = sum(emoji_vs_text.values()) or 1
                emoji_responses = emoji_vs_text.get("emoji", 0) + emoji_vs_text.get("mixed", 0)
                communication_style["visual_communication_preference"] = emoji_responses / total_responses
            
            # Use personality context
            communication_style["formality_preference"] = personality_context.get("communication_style", "balanced")
            
            # Determine emotional expression style
            emoji_comfort = communication_style["emoji_comfort_level"]
            if emoji_comfort > 0.7:
                communication_style["emotional_expression_style"] = "expressive"
            elif emoji_comfort < 0.3:
                communication_style["emotional_expression_style"] = "reserved"
            else:
                communication_style["emotional_expression_style"] = "moderate"
            
            return communication_style
            
        except Exception as e:
            logger.error(f"Error analyzing communication style: {e}")
            return communication_style
    
    async def _assess_relationship_context(
        self,
        user_id: str,
        conversation_patterns: ConversationPattern,
        personality_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        🤝 RELATIONSHIP CONTEXT: Assess relationship depth and rapport
        """
        relationship_context = {
            "conversation_count": 0,
            "rapport_level": "new",
            "comfort_level": 0.5,
            "shared_experiences": 0,
            "communication_familiarity": 0.5
        }
        
        try:
            # Count total conversations
            conversation_count = len(conversation_patterns.similar_conversations)
            relationship_context["conversation_count"] = conversation_count
            
            # Determine rapport level based on conversation count and patterns
            if conversation_count < 5:
                relationship_context["rapport_level"] = "new"
                relationship_context["comfort_level"] = 0.3
            elif conversation_count < 20:
                relationship_context["rapport_level"] = "developing"
                relationship_context["comfort_level"] = 0.6
            else:
                relationship_context["rapport_level"] = "established"
                relationship_context["comfort_level"] = 0.8
            
            # Assess communication familiarity
            emoji_success_rate = conversation_patterns.emoji_success_rate
            personality_match = conversation_patterns.personality_match
            
            familiarity_score = (emoji_success_rate + personality_match) / 2
            relationship_context["communication_familiarity"] = familiarity_score
            
            # Count shared emotional experiences
            shared_experiences = 0
            for conversation in conversation_patterns.similar_conversations:
                metadata = conversation.get("metadata", {})
                if "emotional_context" in metadata or "emoji_reaction" in metadata:
                    shared_experiences += 1
            
            relationship_context["shared_experiences"] = shared_experiences
            
            return relationship_context
            
        except Exception as e:
            logger.error(f"Error assessing relationship context: {e}")
            return relationship_context
    
    def _calculate_enhanced_personality_alignment(
        self, 
        user_message: str, 
        bot_character: str, 
        personality_context: Dict[str, Any]
    ) -> float:
        """Enhanced personality alignment calculation using user personality data"""
        base_alignment = self._calculate_personality_alignment(user_message, bot_character)
        
        # Enhance with user personality context
        user_communication_style = personality_context.get("communication_style", "neutral")
        emoji_comfort = personality_context.get("emoji_comfort_level", 0.5)
        
        # Adjust alignment based on user's emoji comfort level
        if emoji_comfort > 0.7:  # User loves emojis
            enhanced_alignment = base_alignment * 1.2
        elif emoji_comfort < 0.3:  # User avoids emojis
            enhanced_alignment = base_alignment * 0.7
        else:
            enhanced_alignment = base_alignment
        
        # Consider communication style match
        if bot_character == "mystical" and user_communication_style == "expressive":
            enhanced_alignment *= 1.1
        elif bot_character == "technical" and user_communication_style == "formal":
            enhanced_alignment *= 1.1
        
        return min(enhanced_alignment, 1.0)
    
    def _assess_enhanced_conversation_context(
        self, 
        user_message: str, 
        conversation_context: Optional[Dict[str, Any]], 
        emotional_state: Dict[str, Any],
        personality_context: Dict[str, Any]
    ) -> float:
        """Enhanced conversation context assessment"""
        base_score = self._assess_conversation_context(user_message, conversation_context)
        
        # Enhance with emotional state
        if emotional_state.get("needs_emotional_support", False):
            base_score *= 1.3  # Higher emoji likelihood for emotional support
        
        if emotional_state.get("prefers_emoji_comfort", False):
            base_score *= 1.2
        
        # Enhance with personality preferences
        if personality_context.get("prefers_brief_responses", False):
            base_score *= 1.2  # Brief responses favor emojis
        
        visual_pref = personality_context.get("visual_communication_preference", 0.5)
        base_score *= (0.8 + visual_pref * 0.4)  # Scale by visual preference
        
        return min(base_score, 1.0)
    
    async def _synthesize_enhanced_emoji_decision(
        self,
        user_id: str,
        user_message: str,
        bot_character: str,
        personality_context: Dict[str, Any],
        emotional_state: Dict[str, Any],
        conversation_patterns: ConversationPattern,
        communication_style: Dict[str, Any],
        relationship_context: Dict[str, Any],
        personality_alignment: float,
        context_score: float
    ) -> EmojiResponseDecision:
        """
        🧩 ENHANCED DECISION SYNTHESIS: Combine all comprehensive factors
        """
        # Enhanced weight system based on relationship depth and user preferences
        rapport_level = relationship_context.get("rapport_level", "new")
        emoji_comfort = communication_style.get("emoji_comfort_level", 0.5)
        
        # Adaptive weights based on relationship context
        if rapport_level == "established":
            weights = {
                "pattern_success": 0.25,      # Historical success
                "personality_context": 0.20,  # User personality insights
                "emotional_state": 0.20,      # Current emotional needs
                "communication_style": 0.15,  # Preferred communication style
                "relationship_context": 0.10, # Rapport and familiarity
                "personality_alignment": 0.10  # Character alignment
            }
        elif rapport_level == "developing":
            weights = {
                "pattern_success": 0.30,
                "personality_context": 0.15,
                "emotional_state": 0.25,
                "communication_style": 0.15,
                "relationship_context": 0.05,
                "personality_alignment": 0.10
            }
        else:  # new relationship
            weights = {
                "pattern_success": 0.15,      # Less historical data
                "personality_context": 0.10,  # Limited personality data
                "emotional_state": 0.30,      # Focus on emotional needs
                "communication_style": 0.20,  # User communication preferences
                "relationship_context": 0.05, # Building rapport
                "personality_alignment": 0.20  # Character consistency important
            }
        
        # Calculate component scores
        pattern_score = conversation_patterns.emoji_success_rate
        
        # Personality context score
        personality_score = (
            personality_context.get("emoji_comfort_level", 0.5) * 0.5 +
            (1.0 if personality_context.get("communication_style") == "casual" else 0.3) * 0.3 +
            personality_context.get("emotional_expressiveness", 0.5) * 0.2
        )
        
        # Emotional state score
        emotional_score = 0.5
        if emotional_state.get("needs_emotional_support", False):
            emotional_score = 0.8
        elif emotional_state.get("prefers_emoji_comfort", False):
            emotional_score = 0.7
        elif emotional_state.get("intensity", 0.5) > 0.7:
            emotional_score = 0.75
        
        # Communication style score
        comm_style_score = (
            communication_style.get("emoji_comfort_level", 0.5) * 0.4 +
            communication_style.get("visual_communication_preference", 0.5) * 0.3 +
            (0.8 if communication_style.get("prefers_brief_responses", False) else 0.4) * 0.3
        )
        
        # Relationship context score
        relationship_score = (
            relationship_context.get("comfort_level", 0.5) * 0.5 +
            relationship_context.get("communication_familiarity", 0.5) * 0.5
        )
        
        # Calculate weighted confidence score
        confidence_score = (
            pattern_score * weights["pattern_success"] +
            personality_score * weights["personality_context"] +
            emotional_score * weights["emotional_state"] +
            comm_style_score * weights["communication_style"] +
            relationship_score * weights["relationship_context"] +
            personality_alignment * weights["personality_alignment"]
        )
        
        # Enhanced context-aware threshold
        # Use configurable thresholds instead of hardcoded values
        if personality_context.get("interaction_count", 0) <= 3:
            # New user - use lower threshold for better engagement
            base_threshold = self.new_user_threshold
        else:
            # Established user - use normal threshold
            base_threshold = self.base_threshold
        
        # Adjust threshold based on user's emoji comfort
        if emoji_comfort > 0.8:
            emoji_threshold = base_threshold - 0.1  # More emoji-friendly
        elif emoji_comfort < 0.2:
            emoji_threshold = base_threshold + 0.15  # More conservative
        else:
            emoji_threshold = base_threshold
        
        # Final decision
        should_use_emoji = confidence_score >= emoji_threshold
        
        # Select optimal emoji with enhanced context
        emoji_choice = None
        context_reason = EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        
        if should_use_emoji:
            emoji_choice, context_reason = self._select_enhanced_optimal_emoji(
                user_message, bot_character, conversation_patterns, 
                emotional_state, personality_context, communication_style
            )
        
        return EmojiResponseDecision(
            should_use_emoji=should_use_emoji,
            emoji_choice=emoji_choice,
            confidence_score=confidence_score,
            context_reason=context_reason,
            fallback_text=None,
            supporting_evidence={
                "pattern_success_rate": pattern_score,
                "personality_score": personality_score,
                "emotional_score": emotional_score,
                "communication_style_score": comm_style_score,
                "relationship_score": relationship_score,
                "personality_alignment": personality_alignment,
                "preferred_emojis": conversation_patterns.preferred_emojis[:3],
                "rapport_level": rapport_level,
                "emoji_comfort_level": emoji_comfort,
                "conversation_count": relationship_context.get("conversation_count", 0),
                "emotional_state": emotional_state.get("current_emotion", "neutral"),
                "threshold_used": emoji_threshold
            }
        )
    
    def _select_enhanced_optimal_emoji(
        self, 
        user_message: str, 
        bot_character: str,
        conversation_patterns: ConversationPattern,
        emotional_state: Dict[str, Any],
        personality_context: Dict[str, Any],
        communication_style: Dict[str, Any]
    ) -> Tuple[str, EmojiResponseContext]:
        """Enhanced emoji selection with comprehensive context"""
        
        # Priority 1: User's historical preferences (if established relationship)
        if conversation_patterns.preferred_emojis and len(conversation_patterns.similar_conversations) > 10:
            preferred_emoji = conversation_patterns.preferred_emojis[0][0]
            character_emojis = self.character_emoji_sets.get(bot_character, self.character_emoji_sets["general"])
            all_character_emojis = [emoji for emoji_list in character_emojis.values() for emoji in emoji_list]
            
            if preferred_emoji in all_character_emojis:
                return preferred_emoji, EmojiResponseContext.REPEATED_PATTERN
        
        # Priority 2: Emotional support needs
        if emotional_state.get("needs_emotional_support", False):
            if bot_character == "mystical":
                return "🙏", EmojiResponseContext.EMOTIONAL_OVERWHELM
            elif bot_character == "technical":
                return "👍", EmojiResponseContext.EMOTIONAL_OVERWHELM
            else:
                return "❤️", EmojiResponseContext.EMOTIONAL_OVERWHELM
        
        # Priority 3: High emotional intensity
        if emotional_state.get("intensity", 0.5) > 0.7:
            current_emotion = emotional_state.get("current_emotion", "neutral")
            character_emojis = self.character_emoji_sets.get(bot_character, self.character_emoji_sets["general"])
            
            if current_emotion in ["joy", "excitement", "wonder"]:
                return character_emojis["wonder"][0], EmojiResponseContext.EMOTIONAL_OVERWHELM
            elif current_emotion in ["gratitude"]:
                return character_emojis["acknowledgment"][0], EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        
        # Priority 4: Context-based selection (enhanced)
        message_lower = user_message.lower()
        character_emojis = self.character_emoji_sets.get(bot_character, self.character_emoji_sets["general"])
        
        # Enhanced context detection
        if any(word in message_lower for word in ["amazing", "incredible", "fantastic", "mind-blowing", "wow"]):
            return character_emojis["wonder"][0], EmojiResponseContext.EMOTIONAL_OVERWHELM
        
        if any(word in message_lower for word in ["thanks", "thank you", "appreciate", "grateful"]):
            return character_emojis["acknowledgment"][0], EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        
        if any(word in message_lower for word in ["fun", "funny", "lol", "haha", "hilarious", "😄"]):
            return character_emojis["playful"][0], EmojiResponseContext.PLAYFUL_INTERACTION
        
        # Technical appreciation for technical characters
        if bot_character == "technical" and any(word in message_lower for word in ["code", "algorithm", "system", "data", "tech"]):
            return character_emojis["positive"][0], EmojiResponseContext.TECHNICAL_APPRECIATION
        
        # Mystical wonder for mystical characters
        if bot_character == "mystical" and any(word in message_lower for word in ["magic", "energy", "spiritual", "mystical", "dream"]):
            return character_emojis["wonder"][0], EmojiResponseContext.MYSTICAL_WONDER
        
        # Default based on communication style preference
        if communication_style.get("prefers_brief_responses", False):
            return character_emojis["acknowledgment"][0], EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        else:
            return character_emojis["positive"][0], EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT

    async def _analyze_emotional_appropriateness(
        self,
        user_id: str,
        user_message: str,
        emotional_context: Optional[Dict[str, Any]]
    ) -> float:
        """Analyze if the emotional context supports emoji response"""
        try:
            # Get recent emotional feedback from emoji reactions
            recent_emotions = await self._get_recent_emotional_feedback(user_id)
            
            # Analyze current message emotion using existing emoji mapper
            # Use simplified emotion analysis - look for emotional keywords
            message_emotions = self._analyze_message_emotions(user_message)
            
            # Check for emotional overwhelm (very high intensity emotions)
            if emotional_context:
                emotional_intensity = emotional_context.get("intensity", 0.0)
                if emotional_intensity > 0.8:  # High emotional intensity
                    return 0.85  # High score for emoji response
            
            # Check for simple, positive emotions that work well with emojis
            simple_positive_emotions = ["joy", "gratitude", "excitement", "wonder"]
            for emotion in simple_positive_emotions:
                if emotion in message_emotions:
                    return 0.75
            
            # Default moderate score
            return 0.5
            
        except Exception as e:
            logger.error(f"Error analyzing emotional appropriateness: {e}")
            return 0.3  # Low score if analysis fails
    
    async def _get_recent_emotional_feedback(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent emoji reaction feedback for emotional pattern analysis"""
        try:
            # Search for recent memories with emoji reaction metadata
            recent_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="emoji reaction emotional feedback",
                limit=10
            )
            
            # Filter for memories with emoji reaction data
            emotional_feedback = []
            for memory in recent_memories:
                metadata = memory.get("metadata", {})
                if "emoji_reaction" in metadata:
                    emotional_feedback.append({
                        "emoji": metadata["emoji_reaction"],
                        "emotion": metadata.get("emotion_detected", "neutral"),
                        "timestamp": memory.get("timestamp"),
                        "context": memory.get("content", "")
                    })
            
            return emotional_feedback
            
        except Exception as e:
            logger.error(f"Error getting emotional feedback: {e}")
            return []
    
    def _calculate_personality_alignment(self, user_message: str, bot_character: str) -> float:
        """Calculate how well emoji response aligns with bot personality"""
        message_lower = user_message.lower()
        
        if bot_character == "mystical":
            # Look for mystical/spiritual keywords
            mystical_keywords = [
                "magic", "mystical", "spiritual", "energy", "universe", "crystal", 
                "meditation", "chakra", "aura", "dream", "vision", "intuition"
            ]
            if any(keyword in message_lower for keyword in mystical_keywords):
                return 0.9  # High alignment
            return 0.6  # Moderate alignment
            
        elif bot_character == "technical":
            # Look for technical keywords
            technical_keywords = [
                "code", "programming", "algorithm", "data", "system", "computer",
                "software", "hardware", "network", "database", "api", "tech"
            ]
            if any(keyword in message_lower for keyword in technical_keywords):
                return 0.9  # High alignment
            return 0.6  # Moderate alignment
            
        else:  # general character
            return 0.7  # Always moderate alignment for general character
    
    def _assess_conversation_context(
        self, 
        user_message: str, 
        conversation_context: Optional[Dict[str, Any]]
    ) -> float:
        """Assess conversation context for emoji appropriateness"""
        message_lower = user_message.lower()
        
        # Short messages are often good for emoji responses
        if len(user_message.strip()) < 20:
            return 0.8
        
        # Questions often work well with emoji responses
        if "?" in user_message:
            return 0.7
        
        # Greetings and casual expressions
        casual_expressions = ["hi", "hello", "hey", "thanks", "wow", "cool", "nice", "awesome"]
        if any(expr in message_lower for expr in casual_expressions):
            return 0.8
        
        # Complex technical discussions might be less suitable
        if len(user_message.split()) > 30:  # Long messages
            return 0.3
        
        return 0.5  # Default moderate score
    
    def _extract_dominant_emotion(self, similar_memories: List[Dict[str, Any]]) -> str:
        """Extract the dominant emotional context from similar conversations"""
        emotion_counts = {}
        
        for memory in similar_memories:
            metadata = memory.get("metadata", {})
            emotion_data = metadata.get("emotion_data", {})
            
            if emotion_data and "primary_emotion" in emotion_data:
                emotion = emotion_data["primary_emotion"]
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        if emotion_counts:
            return max(emotion_counts.items(), key=lambda x: x[1])[0]
        
        return "neutral"
    
    def _calculate_conversation_personality_match(
        self, 
        similar_memories: List[Dict[str, Any]], 
        bot_character: str
    ) -> float:
        """Calculate how well the conversation history matches the bot's personality"""
        if not similar_memories:
            return 0.5
        
        personality_indicators = 0
        total_memories = len(similar_memories)
        
        for memory in similar_memories:
            content = memory.get("content", "").lower()
            
            if bot_character == "mystical":
                mystical_words = ["magic", "spiritual", "energy", "mystical", "dream"]
                if any(word in content for word in mystical_words):
                    personality_indicators += 1
            elif bot_character == "technical":
                technical_words = ["code", "tech", "programming", "system", "data"]
                if any(word in content for word in technical_words):
                    personality_indicators += 1
        
        return personality_indicators / total_memories if total_memories > 0 else 0.5
    
    async def _synthesize_emoji_decision(
        self,
        user_id: str,
        user_message: str,
        bot_character: str,
        conversation_patterns: ConversationPattern,
        emotion_score: float,
        personality_alignment: float,
        context_score: float
    ) -> EmojiResponseDecision:
        """
        🧩 DECISION SYNTHESIS: Combine all factors to make final emoji decision
        """
        # Weight the different factors
        weights = {
            "pattern_success": 0.3,      # Historical emoji success rate
            "emotion_appropriateness": 0.25,  # Emotional context
            "personality_alignment": 0.25,    # Character alignment
            "context_suitability": 0.2       # Conversation context
        }
        
        # Calculate weighted confidence score
        confidence_score = (
            conversation_patterns.emoji_success_rate * weights["pattern_success"] +
            emotion_score * weights["emotion_appropriateness"] +
            personality_alignment * weights["personality_alignment"] +
            context_score * weights["context_suitability"]
        )
        
        # Decision threshold - adjusted for demo/new users
        EMOJI_THRESHOLD = 0.55  # Lowered from 0.6 to be more responsive for new users
        should_use_emoji = confidence_score >= EMOJI_THRESHOLD
        
        # Select appropriate emoji if decision is positive
        emoji_choice = None
        context_reason = EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        
        if should_use_emoji:
            emoji_choice, context_reason = self._select_optimal_emoji(
                user_message, bot_character, conversation_patterns, emotion_score
            )
        
        return EmojiResponseDecision(
            should_use_emoji=should_use_emoji,
            emoji_choice=emoji_choice,
            confidence_score=confidence_score,
            context_reason=context_reason,
            fallback_text=None,
            supporting_evidence={
                "pattern_success_rate": conversation_patterns.emoji_success_rate,
                "emotion_score": emotion_score,
                "personality_alignment": personality_alignment,
                "context_score": context_score,
                "preferred_emojis": conversation_patterns.preferred_emojis[:3],  # Top 3
                "similar_conversation_count": len(conversation_patterns.similar_conversations)
            }
        )
    
    def _select_optimal_emoji(
        self, 
        user_message: str, 
        bot_character: str,
        conversation_patterns: ConversationPattern,
        emotion_score: float
    ) -> Tuple[str, EmojiResponseContext]:
        """Select the best emoji based on context and character"""
        message_lower = user_message.lower()
        
        # Get character-specific emoji set
        character_emojis = self.character_emoji_sets.get(bot_character, self.character_emoji_sets["general"])
        
        # Prioritize user's historical preferences if available
        if conversation_patterns.preferred_emojis:
            preferred_emoji = conversation_patterns.preferred_emojis[0][0]  # Most frequent
            # Verify it matches character personality
            all_character_emojis = [emoji for emoji_list in character_emojis.values() for emoji in emoji_list]
            if preferred_emoji in all_character_emojis:
                return preferred_emoji, EmojiResponseContext.REPEATED_PATTERN
        
        # Context-based selection
        if any(word in message_lower for word in ["amazing", "awesome", "incredible", "wow"]):
            return character_emojis["wonder"][0], EmojiResponseContext.EMOTIONAL_OVERWHELM
        
        if any(word in message_lower for word in ["thanks", "thank you", "appreciate"]):
            return character_emojis["acknowledgment"][0], EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        
        if any(word in message_lower for word in ["fun", "funny", "lol", "haha", "😄"]):
            return character_emojis["playful"][0], EmojiResponseContext.PLAYFUL_INTERACTION
        
        if emotion_score > 0.7:  # High emotional content
            return character_emojis["positive"][0], EmojiResponseContext.EMOTIONAL_OVERWHELM
        
        # Default to acknowledgment
        return character_emojis["acknowledgment"][0], EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT


class EmojiResponseIntegration:
    """
    🔧 INTEGRATION LAYER: Connects emoji intelligence with Discord bot events
    """
    
    def __init__(self, memory_manager: MemoryManagerProtocol):
        self.vector_emoji_intelligence = VectorEmojiIntelligence(memory_manager)
        logger.info("🔧 EmojiResponseIntegration initialized")
    
    async def evaluate_emoji_response(
        self,
        user_id: str,
        user_message: str,
        bot_character: str = "general",
        security_validation_result: Optional[Dict[str, Any]] = None,
        emotional_context: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> EmojiResponseDecision:
        """
        Main integration point for evaluating emoji responses
        Called from Discord event handlers
        """
        return await self.vector_emoji_intelligence.should_respond_with_emoji(
            user_id=user_id,
            user_message=user_message,
            bot_character=bot_character,
            security_validation_result=security_validation_result,
            emotional_context=emotional_context,
            conversation_context=conversation_context
        )
    
    async def apply_emoji_response(self, message, decision: EmojiResponseDecision):
        """
        Apply the emoji response decision to a Discord message
        Either adds emoji reaction or sends emoji as response
        """
        try:
            if decision.should_use_emoji and decision.emoji_choice:
                logger.info(f"🎭 Applying emoji response: {decision.emoji_choice} (reason: {decision.context_reason.value})")
                
                if decision.context_reason == EmojiResponseContext.INAPPROPRIATE_CONTENT:
                    # For inappropriate content, send emoji as message
                    await message.reply(decision.emoji_choice, mention_author=False)
                else:
                    # For other contexts, add as reaction
                    await message.add_reaction(decision.emoji_choice)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying emoji response: {e}")
            return False