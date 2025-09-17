"""
Personality and Conversation Mode Detection for Human-Like Intelligence

This module provides sophisticated detection of conversation modes and personality
adaptation based on user interactions and emotional context.
"""

import asyncio
import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ConversationMode(Enum):
    """Conversation modes for adaptive responses"""
    HUMAN_LIKE = "human_like"           # Empathetic, caring, natural
    ANALYTICAL = "analytical"           # Detailed, precise, comprehensive
    BALANCED = "balanced"               # Mix of empathy and information
    ADAPTIVE = "adaptive"               # Learns and adapts to user preference


class InteractionType(Enum):
    """Types of interactions for contextual responses"""
    EMOTIONAL_SUPPORT = "emotional_support"        # User needs comfort, validation
    PROBLEM_SOLVING = "problem_solving"            # User needs help solving issues
    INFORMATION_SEEKING = "information_seeking"    # User wants to learn something
    CREATIVE_COLLABORATION = "creative_collaboration"  # User wants to create/brainstorm
    CASUAL_CHAT = "casual_chat"                    # Normal friendly conversation


class PersonalityType(Enum):
    """Personality types for human-like behavior"""
    CARING_FRIEND = "caring_friend"                # Warm, supportive, emotionally intelligent
    WISE_MENTOR = "wise_mentor"                    # Thoughtful, insightful, growth-oriented
    PLAYFUL_COMPANION = "playful_companion"       # Fun, engaging, lighthearted
    SUPPORTIVE_COUNSELOR = "supportive_counselor"  # Professional caring, solution-focused


@dataclass
class ConversationContext:
    """Rich context for conversation adaptation"""
    mode: ConversationMode
    interaction_type: InteractionType
    personality_type: PersonalityType
    emotional_state: Optional[str] = None
    relationship_level: str = "new"  # new, developing, established, deep
    conversation_history_depth: int = 0
    user_preferences: Dict[str, Any] = None
    confidence_score: float = 0.8


class ConversationModeDetector:
    """Detects appropriate conversation mode based on user input and context"""
    
    def __init__(self):
        self.emotional_support_keywords = [
            "feel", "feeling", "worried", "sad", "anxious", "scared", "upset", 
            "frustrated", "depressed", "lonely", "stressed", "overwhelmed",
            "hurt", "angry", "disappointed", "confused", "lost", "help me"
        ]
        
        self.analytical_keywords = [
            "how does", "explain", "what is", "analyze", "compare", "evaluate",
            "research", "study", "understand", "learn about", "deep dive",
            "comprehensive", "detailed", "technical", "scientific", "academic"
        ]
        
        self.problem_solving_keywords = [
            "help", "problem", "issue", "stuck", "error", "broken", "fix",
            "solve", "troubleshoot", "debug", "repair", "improve", "optimize"
        ]
        
        self.creative_keywords = [
            "create", "design", "brainstorm", "idea", "creative", "imagine",
            "invent", "build", "make", "art", "story", "poem", "music", "draw"
        ]
        
        self.casual_keywords = [
            "hello", "hi", "hey", "what's up", "how are you", "good morning",
            "good night", "thanks", "thank you", "awesome", "cool", "nice"
        ]

    def detect_conversation_mode(
        self, 
        message: str, 
        user_history: List[Dict[str, Any]] = None,
        emotional_context: Dict[str, Any] = None
    ) -> ConversationMode:
        """Detect the most appropriate conversation mode"""
        
        message_lower = message.lower()
        
        # Check for explicit emotional support needs
        emotional_score = sum(1 for keyword in self.emotional_support_keywords 
                            if keyword in message_lower)
        
        # Check for analytical requests
        analytical_score = sum(1 for keyword in self.analytical_keywords 
                              if keyword in message_lower)
        
        # Consider emotional context if available
        if emotional_context:
            mood = emotional_context.get("current_mood", "")
            if mood in ["sad", "anxious", "frustrated", "stressed"]:
                emotional_score += 2
        
        # Determine mode based on scores and context
        if emotional_score >= 1:
            return ConversationMode.HUMAN_LIKE
        elif analytical_score >= 1:
            return ConversationMode.ANALYTICAL
        elif user_history and len(user_history) > 10:
            # For established users, use adaptive mode
            return ConversationMode.ADAPTIVE
        else:
            return ConversationMode.BALANCED

    def detect_interaction_type(
        self, 
        message: str, 
        emotional_context: Dict[str, Any] = None
    ) -> InteractionType:
        """Detect the type of interaction the user is seeking"""
        
        message_lower = message.lower()
        
        # Score different interaction types
        emotional_score = sum(1 for keyword in self.emotional_support_keywords 
                            if keyword in message_lower)
        problem_score = sum(1 for keyword in self.problem_solving_keywords 
                           if keyword in message_lower)
        analytical_score = sum(1 for keyword in self.analytical_keywords 
                              if keyword in message_lower)
        creative_score = sum(1 for keyword in self.creative_keywords 
                            if keyword in message_lower)
        
        # Consider emotional context
        if emotional_context and emotional_context.get("needs_support", False):
            emotional_score += 2
        
        # Determine interaction type
        scores = {
            InteractionType.EMOTIONAL_SUPPORT: emotional_score,
            InteractionType.PROBLEM_SOLVING: problem_score,
            InteractionType.INFORMATION_SEEKING: analytical_score,
            InteractionType.CREATIVE_COLLABORATION: creative_score,
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return InteractionType.CASUAL_CHAT
        
        # Return the highest scoring interaction type
        for interaction_type, score in scores.items():
            if score == max_score:
                return interaction_type
        
        return InteractionType.CASUAL_CHAT


class PersonalityAdaptationEngine:
    """
    Engine for adapting personality based on user interactions and preferences.
    Now supports persistent storage for user preferences.
    """
    
    def __init__(self, default_personality: PersonalityType = PersonalityType.CARING_FRIEND):
        self.default_personality = default_personality
        
        # Initialize persistent storage
        self._init_persistence()
        
        # Cache for loaded preferences (memory optimization)
        self._preference_cache = {}
        self._cache_expiry = {}
    
    def _init_persistence(self):
        """Initialize persistence manager if available"""
        try:
            from src.database.human_like_persistence import get_persistence_manager
            self.persistence_manager = get_persistence_manager()
        except ImportError:
            self.persistence_manager = None
            logger.warning("Human-like persistence not available - falling back to memory-only storage")
    
    async def _load_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Load user preferences from persistent storage or cache"""
        # Check cache first
        if user_id in self._preference_cache:
            return self._preference_cache[user_id]
        
        # Load from database if persistence available
        if self.persistence_manager:
            try:
                stored_prefs = await self.persistence_manager.load_user_preferences(user_id)
                if stored_prefs:
                    prefs = stored_prefs["preferences"]
                    self._preference_cache[user_id] = prefs
                    return prefs
            except Exception as e:
                logger.error("Failed to load user preferences from database: %s", e)
        
        # Return empty preferences if not found
        return {}
    
    async def _save_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Save user preferences to persistent storage and cache"""
        # Update cache
        self._preference_cache[user_id] = preferences
        
        # Save to database if persistence available
        if self.persistence_manager:
            try:
                # Get current personality type and conversation mode
                personality_type = self.default_personality.value
                conversation_mode = "adaptive"  # Default mode
                
                await self.persistence_manager.save_user_preferences(
                    user_id, preferences, personality_type, conversation_mode
                )
            except Exception as e:
                logger.error("Failed to save user preferences to database: %s", e)
    
    async def adapt_personality(
        self,
        user_id: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        user_feedback: Optional[Dict[str, Any]] = None
    ) -> PersonalityType:
        """
        Adapt personality based on user interactions and stored preferences.
        Now loads preferences from persistent storage.
        """
        conversation_history = conversation_history or []
        user_feedback = user_feedback or {}
        
        # Load user preferences from persistent storage
        user_preferences = await self._load_user_preferences(user_id)
        
        # Start with default personality
        adapted_personality = self.default_personality
        
        # Apply stored preferences
        if user_preferences.get("prefers_professional"):
            adapted_personality = PersonalityType.WISE_MENTOR
        elif user_preferences.get("prefers_playful"):
            adapted_personality = PersonalityType.PLAYFUL_COMPANION
        elif user_preferences.get("prefers_wisdom"):
            adapted_personality = PersonalityType.WISE_MENTOR
        
        # Analyze conversation patterns if history available
        if conversation_history:
            complexity_preference = self._analyze_complexity_preference(conversation_history)
            if complexity_preference == "simple" and adapted_personality == PersonalityType.WISE_MENTOR:
                adapted_personality = PersonalityType.CARING_FRIEND
            elif complexity_preference == "detailed" and adapted_personality == PersonalityType.CARING_FRIEND:
                adapted_personality = PersonalityType.WISE_MENTOR
        
        # Apply recent feedback
        if user_feedback:
            if user_feedback.get("response_too_casual", False):
                adapted_personality = PersonalityType.WISE_MENTOR
                # Update stored preferences
                user_preferences["prefers_professional"] = True
                await self._save_user_preferences(user_id, user_preferences)
            elif user_feedback.get("response_too_formal", False):
                adapted_personality = PersonalityType.PLAYFUL_COMPANION
                # Update stored preferences
                user_preferences["prefers_playful"] = True
                await self._save_user_preferences(user_id, user_preferences)
        
        # Apply emotional adaptation
        if self._detect_stress_indicators(conversation_history):
            if adapted_personality == PersonalityType.PLAYFUL_COMPANION:
                adapted_personality = PersonalityType.CARING_FRIEND
        
        # Apply positive feedback adaptation
        if any(self._is_positive_response(msg.get("content", "")) for msg in conversation_history[-3:]):
            # Don't change if working well
            pass
        else:
            # Try different approach if no positive feedback
            if len(conversation_history) > 5:
                if adapted_personality == PersonalityType.CARING_FRIEND:
                    adapted_personality = PersonalityType.PLAYFUL_COMPANION
                elif adapted_personality == PersonalityType.PLAYFUL_COMPANION:
                    adapted_personality = PersonalityType.WISE_MENTOR
        
        return adapted_personality
    
    async def update_user_preferences(
        self,
        user_id: str,
        interaction_feedback: Dict[str, Any]
    ):
        """Update user personality preferences based on feedback with persistent storage"""
        
        # Load current preferences
        prefs = await self._load_user_preferences(user_id)
        
        # Update preferences based on feedback
        if interaction_feedback.get("response_too_casual", False):
            prefs["prefers_professional"] = True
        elif interaction_feedback.get("response_too_formal", False):
            prefs["prefers_playful"] = True
        elif interaction_feedback.get("wants_deeper_insights", False):
            prefs["prefers_wisdom"] = True
        
        # Save updated preferences
        await self._save_user_preferences(user_id, prefs)
    
    def _analyze_complexity_preference(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Analyze user's preference for response complexity"""
        recent_messages = conversation_history[-5:] if len(conversation_history) >= 5 else conversation_history
        
        avg_length = sum(len(msg.get("content", "")) for msg in recent_messages) / len(recent_messages) if recent_messages else 0
        
        if avg_length < 50:
            return "simple"
        elif avg_length > 200:
            return "detailed"
        else:
            return "moderate"
    
    def _detect_stress_indicators(self, conversation_history: List[Dict[str, Any]]) -> bool:
        """Detect if user is showing stress indicators"""
        if not conversation_history:
            return False
        
        recent_messages = conversation_history[-3:]
        stress_keywords = ["stressed", "overwhelmed", "anxious", "worried", "frustrated", "exhausted"]
        
        for msg in recent_messages:
            content = msg.get("content", "").lower()
            if any(keyword in content for keyword in stress_keywords):
                return True
        
        return False
    
    def _is_positive_response(self, content: str) -> bool:
        """Check if a message contains positive feedback"""
        positive_indicators = ["thanks", "helpful", "great", "good", "perfect", "exactly", "appreciate"]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in positive_indicators)
    
    def adapt_personality_for_user(self, user_id: str, user_feedback: Optional[Dict[str, Any]] = None) -> PersonalityType:
        """Synchronous adapter for backwards compatibility"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.adapt_personality(user_id, None, user_feedback))
        except RuntimeError:
            # If no event loop, use default
            return self.default_personality


class HumanLikeConversationEngine:
    """Complete engine for human-like conversation adaptation"""
    
    def __init__(self, default_personality: PersonalityType = PersonalityType.CARING_FRIEND):
        self.mode_detector = ConversationModeDetector()
        self.personality_engine = PersonalityAdaptationEngine(default_personality)
    
    async def analyze_conversation_context(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        emotional_context: Optional[Dict[str, Any]] = None,
        relationship_context: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """Comprehensive analysis of conversation context for human-like responses"""
        
        try:
            # Detect conversation mode and interaction type
            conversation_mode = self.mode_detector.detect_conversation_mode(
                message, conversation_history, emotional_context
            )
            
            interaction_type = self.mode_detector.detect_interaction_type(
                message, emotional_context
            )
            
            # Adapt personality for this user
            personality_type = self.personality_engine.adapt_personality_for_user(
                user_id, conversation_history
            )
            
            # Assess relationship level
            relationship_level = self._assess_relationship_level(
                conversation_history, relationship_context
            )
            
            # Extract emotional state
            emotional_state = None
            if emotional_context:
                emotional_state = emotional_context.get("current_mood") or emotional_context.get("emotional_state")
            
            return ConversationContext(
                mode=conversation_mode,
                interaction_type=interaction_type,
                personality_type=personality_type,
                emotional_state=emotional_state,
                relationship_level=relationship_level,
                conversation_history_depth=len(conversation_history) if conversation_history else 0,
                user_preferences=relationship_context.get("preferences") if relationship_context else {},
                confidence_score=0.85
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze conversation context: {e}")
            # Return safe defaults
            return ConversationContext(
                mode=ConversationMode.BALANCED,
                interaction_type=InteractionType.CASUAL_CHAT,
                personality_type=PersonalityType.CARING_FRIEND,
                relationship_level="new",
                confidence_score=0.5
            )
    
    def _assess_relationship_level(
        self,
        conversation_history: List[Dict[str, Any]] = None,
        relationship_context: Dict[str, Any] = None
    ) -> str:
        """Assess the depth of relationship with the user"""
        
        if not conversation_history:
            return "new"
        
        history_length = len(conversation_history)
        
        # Check for personal sharing indicators
        personal_sharing_count = 0
        if conversation_history:
            recent_messages = conversation_history[-20:]  # Last 20 messages
            for msg in recent_messages:
                content = msg.get("content", "").lower()
                if any(indicator in content for indicator in [
                    "i feel", "my family", "my job", "my relationship", "personal",
                    "private", "secret", "confidential", "trust you", "tell you"
                ]):
                    personal_sharing_count += 1
        
        # Relationship level assessment
        if history_length < 5:
            return "new"
        elif history_length < 20 and personal_sharing_count < 2:
            return "developing"
        elif history_length < 50 and personal_sharing_count < 5:
            return "established"
        else:
            return "deep"
    
    def generate_response_guidance(
        self,
        conversation_context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate guidance for response generation based on conversation context"""
        
        guidance = {
            "tone": self._get_tone_guidance(conversation_context),
            "style": self._get_style_guidance(conversation_context),
            "approach": self._get_approach_guidance(conversation_context),
            "emotional_considerations": self._get_emotional_guidance(conversation_context),
            "relationship_considerations": self._get_relationship_guidance(conversation_context)
        }
        
        return guidance
    
    def _get_tone_guidance(self, context: ConversationContext) -> str:
        """Get tone guidance based on context"""
        
        if context.interaction_type == InteractionType.EMOTIONAL_SUPPORT:
            return "empathetic, validating, comforting"
        elif context.interaction_type == InteractionType.PROBLEM_SOLVING:
            return "helpful, solution-focused, encouraging"
        elif context.interaction_type == InteractionType.INFORMATION_SEEKING:
            return "informative, clear, comprehensive"
        elif context.interaction_type == InteractionType.CREATIVE_COLLABORATION:
            return "enthusiastic, imaginative, supportive"
        else:
            return "friendly, warm, conversational"
    
    def _get_style_guidance(self, context: ConversationContext) -> str:
        """Get style guidance based on personality and mode"""
        
        if context.personality_type == PersonalityType.CARING_FRIEND:
            return "warm, personal, emotionally intelligent"
        elif context.personality_type == PersonalityType.WISE_MENTOR:
            return "thoughtful, insightful, guidance-oriented"
        elif context.personality_type == PersonalityType.PLAYFUL_COMPANION:
            return "light-hearted, fun, engaging"
        elif context.personality_type == PersonalityType.SUPPORTIVE_COUNSELOR:
            return "professional but caring, balanced, therapeutic"
        else:
            return "balanced, adaptable, contextually appropriate"
    
    def _get_approach_guidance(self, context: ConversationContext) -> str:
        """Get approach guidance based on conversation mode"""
        
        if context.mode == ConversationMode.HUMAN_LIKE:
            return "prioritize emotional connection and natural conversation flow"
        elif context.mode == ConversationMode.ANALYTICAL:
            return "focus on accuracy, detail, and comprehensive information"
        elif context.mode == ConversationMode.BALANCED:
            return "balance empathy with helpful information"
        elif context.mode == ConversationMode.ADAPTIVE:
            return "adapt to user's communication style and preferences"
        else:
            return "maintain natural, contextually appropriate conversation"
    
    def _get_emotional_guidance(self, context: ConversationContext) -> str:
        """Get emotional considerations"""
        
        if context.emotional_state:
            if context.emotional_state in ["sad", "anxious", "frustrated"]:
                return "provide extra emotional support and validation"
            elif context.emotional_state in ["happy", "excited"]:
                return "match their positive energy and celebrate with them"
            elif context.emotional_state in ["confused", "uncertain"]:
                return "provide clarity and gentle guidance"
        
        return "be emotionally aware and respond to their current state"
    
    def _get_relationship_guidance(self, context: ConversationContext) -> str:
        """Get relationship-level considerations"""
        
        if context.relationship_level == "new":
            return "be welcoming, establish rapport, learn about them"
        elif context.relationship_level == "developing":
            return "build on previous conversations, show you remember them"
        elif context.relationship_level == "established":
            return "reference shared history, be more personal and familiar"
        elif context.relationship_level == "deep":
            return "be intimate in conversation, show deep care and investment"
        else:
            return "be appropriately familiar based on interaction history"


# Global instances for easy import
conversation_engine = HumanLikeConversationEngine()
mode_detector = ConversationModeDetector()
personality_engine = PersonalityAdaptationEngine()


def analyze_conversation_for_human_response(
    user_id: str,
    message: str,
    conversation_history: List[Dict[str, Any]] = None,
    emotional_context: Dict[str, Any] = None,
    relationship_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Main function to analyze conversation and get human-like response guidance
    
    Returns a comprehensive analysis for generating human-like responses
    """
    
    context = conversation_engine.analyze_conversation_context(
        user_id=user_id,
        message=message,
        conversation_history=conversation_history,
        emotional_context=emotional_context,
        relationship_context=relationship_context
    )
    
    guidance = conversation_engine.generate_response_guidance(context)
    
    return {
        "conversation_context": context,
        "response_guidance": guidance,
        "mode": context.mode.value,
        "interaction_type": context.interaction_type.value,
        "personality_type": context.personality_type.value,
        "relationship_level": context.relationship_level,
        "confidence": context.confidence_score
    }