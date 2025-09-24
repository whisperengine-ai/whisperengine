"""
RoBERTa-Enhanced Human-Like Conversation Engine

Enhanced version that replaces basic keyword detection with sophisticated RoBERTa-based
emotion analysis for superior conversation mode detection and personality adaptation.
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer

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
    secondary_emotions: Optional[List[str]] = None
    emotional_intensity: float = 0.5
    emotion_complexity: str = "simple"
    relationship_level: str = "new"  # new, developing, established, deep
    conversation_history_depth: int = 0
    user_preferences: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.8
    roberta_confidence: float = 0.0


class RobertaConversationModeDetector:
    """RoBERTa-Enhanced conversation mode detector using sophisticated emotion analysis"""
    
    def __init__(self):
        """Initialize with RoBERTa emotion analysis capability"""
        
        # Initialize RoBERTa emotion analyzer
        try:
            self.emotion_analyzer = EnhancedVectorEmotionAnalyzer()
            self.use_roberta = True
            logger.info("✅ RoBERTa-Enhanced conversation mode detection enabled")
        except (ImportError, RuntimeError, OSError) as e:
            logger.warning("⚠️ Could not initialize RoBERTa analyzer: %s", e)
            logger.warning("Falling back to keyword-based conversation mode detection")
            self.emotion_analyzer = None
            self.use_roberta = False
        
        # Enhanced mapping from emotions to conversation modes
        self.emotion_to_mode_mapping = {
            "fear": ConversationMode.HUMAN_LIKE,      # Need empathy and support
            "anger": ConversationMode.HUMAN_LIKE,     # Need understanding and validation
            "sadness": ConversationMode.HUMAN_LIKE,   # Need comfort and empathy
            "joy": ConversationMode.BALANCED,         # Share excitement but stay informative
            "surprise": ConversationMode.BALANCED,    # Balance curiosity with information
            "disgust": ConversationMode.ANALYTICAL,   # May need objective analysis
            "neutral": ConversationMode.ADAPTIVE,     # Adapt to context clues
        }
        
        # Emotion to interaction type mapping
        self.emotion_to_interaction_mapping = {
            "fear": InteractionType.EMOTIONAL_SUPPORT,
            "anger": InteractionType.EMOTIONAL_SUPPORT,
            "sadness": InteractionType.EMOTIONAL_SUPPORT,
            "joy": InteractionType.CASUAL_CHAT,
            "surprise": InteractionType.INFORMATION_SEEKING,
            "disgust": InteractionType.PROBLEM_SOLVING,
            "neutral": InteractionType.CASUAL_CHAT,
        }
        
        # Fallback keyword patterns for when RoBERTa is unavailable
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

    async def detect_conversation_mode(
        self, 
        message: str, 
        user_id: str = "conversation_detector",
        user_history: Optional[List[Dict[str, Any]]] = None,  # Reserved for future history analysis
        emotional_context: Optional[Dict[str, Any]] = None   # Reserved for future context integration
    ) -> ConversationMode:
        """Detect the most appropriate conversation mode using RoBERTa analysis"""
        
        if self.use_roberta and self.emotion_analyzer:
            try:
                # Get sophisticated emotion analysis
                emotion_result = await self.emotion_analyzer.analyze_emotion(
                    content=message,
                    user_id=user_id
                )
                
                # Use RoBERTa-based mode detection
                return self._roberta_mode_detection(emotion_result, message)
                
            except (ValueError, RuntimeError, TypeError) as e:
                logger.warning("RoBERTa mode detection failed: %s", e)
                # Fall back to keyword detection
                return self._keyword_mode_detection(message)
        else:
            # Use keyword detection
            return self._keyword_mode_detection(message)

    def _roberta_mode_detection(self, emotion_result, message: str) -> ConversationMode:
        """Detect conversation mode using RoBERTa emotion analysis"""
        
        primary_emotion = emotion_result.primary_emotion
        emotional_intensity = emotion_result.intensity
        
        # High intensity negative emotions → Human-like empathy mode
        if primary_emotion in ["fear", "anger", "sadness"] and emotional_intensity > 0.6:
            return ConversationMode.HUMAN_LIKE
        
        # Check for analytical request patterns (overrides emotion)
        message_lower = message.lower()
        analytical_score = sum(1 for keyword in self.analytical_keywords 
                             if keyword in message_lower)
        if analytical_score >= 2:
            return ConversationMode.ANALYTICAL
        
        # Use emotion-to-mode mapping
        if primary_emotion in self.emotion_to_mode_mapping:
            base_mode = self.emotion_to_mode_mapping[primary_emotion]
            
            # Adjust based on intensity and complexity
            if emotion_result.all_emotions and len(emotion_result.all_emotions) > 1:
                # Complex emotions often need human-like handling
                if base_mode == ConversationMode.ANALYTICAL:
                    return ConversationMode.BALANCED
                else:
                    return base_mode
            else:
                return base_mode
        
        # Default to adaptive mode
        return ConversationMode.ADAPTIVE

    def _keyword_mode_detection(self, message: str) -> ConversationMode:
        """Fallback keyword-based mode detection"""
        
        message_lower = message.lower()
        
        # Count keyword matches for each mode
        emotional_score = sum(1 for keyword in self.emotional_support_keywords 
                            if keyword in message_lower)
        analytical_score = sum(1 for keyword in self.analytical_keywords 
                             if keyword in message_lower)
        
        # Strong emotional indicators → Human-like mode
        if emotional_score >= 2:
            return ConversationMode.HUMAN_LIKE
        
        # Strong analytical indicators → Analytical mode
        if analytical_score >= 2:
            return ConversationMode.ANALYTICAL
        
        # Single indicators suggest balanced approach
        if emotional_score > 0 or analytical_score > 0:
            return ConversationMode.BALANCED
        
        # Default to adaptive
        return ConversationMode.ADAPTIVE

    async def detect_interaction_type(
        self, 
        message: str,
        user_id: str = "conversation_detector",
        conversation_mode: Optional[ConversationMode] = None  # Reserved for future mode-based refinement
    ) -> InteractionType:
        """Detect interaction type using RoBERTa-enhanced analysis"""
        
        if self.use_roberta and self.emotion_analyzer:
            try:
                # Get emotion analysis
                emotion_result = await self.emotion_analyzer.analyze_emotion(
                    content=message,
                    user_id=user_id
                )
                
                # Use emotion-based interaction detection
                primary_emotion = emotion_result.primary_emotion
                if primary_emotion in self.emotion_to_interaction_mapping:
                    emotion_based_type = self.emotion_to_interaction_mapping[primary_emotion]
                else:
                    emotion_based_type = InteractionType.CASUAL_CHAT
                
            except (ValueError, RuntimeError, TypeError):
                emotion_based_type = InteractionType.CASUAL_CHAT
        else:
            emotion_based_type = InteractionType.CASUAL_CHAT
        
        # Enhanced keyword-based detection
        message_lower = message.lower()
        
        # Problem solving indicators
        problem_score = sum(1 for keyword in self.problem_solving_keywords 
                          if keyword in message_lower)
        if problem_score >= 2:
            return InteractionType.PROBLEM_SOLVING
        
        # Creative collaboration indicators  
        creative_score = sum(1 for keyword in self.creative_keywords 
                           if keyword in message_lower)
        if creative_score >= 2:
            return InteractionType.CREATIVE_COLLABORATION
        
        # Information seeking indicators
        info_patterns = ["what", "how", "why", "when", "where", "tell me about", "explain"]
        info_score = sum(1 for pattern in info_patterns if pattern in message_lower)
        if info_score >= 2:
            return InteractionType.INFORMATION_SEEKING
        
        # Use emotion-based type if no strong keyword indicators
        return emotion_based_type

    async def detect_personality_type(
        self, 
        message: str,
        user_id: str = "conversation_detector",
        interaction_type: Optional[InteractionType] = None,
        emotional_context: Optional[Dict[str, Any]] = None  # Reserved for future context integration
    ) -> PersonalityType:
        """Detect appropriate personality type using emotional intelligence"""
        
        if self.use_roberta and self.emotion_analyzer:
            try:
                emotion_result = await self.emotion_analyzer.analyze_emotion(
                    content=message,
                    user_id=user_id
                )
                
                # Use emotion and intensity to select personality
                primary_emotion = emotion_result.primary_emotion
                intensity = emotion_result.intensity
                
                # High-intensity negative emotions need supportive counselor
                if primary_emotion in ["fear", "anger", "sadness"] and intensity > 0.7:
                    return PersonalityType.SUPPORTIVE_COUNSELOR
                
                # Moderate emotional states need caring friend
                elif primary_emotion in ["fear", "anger", "sadness"] and intensity > 0.4:
                    return PersonalityType.CARING_FRIEND
                
                # Positive emotions can be more playful
                elif primary_emotion == "joy" and intensity > 0.6:
                    return PersonalityType.PLAYFUL_COMPANION
                
                # Complex or learning situations need wise mentor
                elif len(emotion_result.all_emotions) > 2 or interaction_type == InteractionType.INFORMATION_SEEKING:
                    return PersonalityType.WISE_MENTOR
                
            except (ValueError, RuntimeError, TypeError):
                pass
        
        # Default personality based on interaction type
        personality_mapping = {
            InteractionType.EMOTIONAL_SUPPORT: PersonalityType.CARING_FRIEND,
            InteractionType.PROBLEM_SOLVING: PersonalityType.WISE_MENTOR,
            InteractionType.INFORMATION_SEEKING: PersonalityType.WISE_MENTOR,
            InteractionType.CREATIVE_COLLABORATION: PersonalityType.PLAYFUL_COMPANION,
            InteractionType.CASUAL_CHAT: PersonalityType.CARING_FRIEND,
        }
        
        return personality_mapping.get(interaction_type or InteractionType.CASUAL_CHAT, PersonalityType.CARING_FRIEND)


class RobertaHumanLikeConversationEngine:
    """RoBERTa-Enhanced conversation engine with human-like personality adaptation"""
    
    def __init__(self):
        """Initialize the enhanced conversation engine"""
        self.mode_detector = RobertaConversationModeDetector()
        
        # Conversation style templates enhanced with emotional intelligence
        self.conversation_templates = {
            ConversationMode.HUMAN_LIKE: {
                "greeting": "I'm really glad you reached out. How are you feeling about everything?",
                "support": "That sounds really {emotion}. I can understand why you'd feel that way.",
                "validation": "Your feelings about this are completely valid and understandable.",
                "encouragement": "You're handling this really well, and I'm here to support you through it."
            },
            ConversationMode.ANALYTICAL: {
                "greeting": "I'd be happy to help you analyze this situation thoroughly.",
                "analysis": "Let me break this down systematically for you.",
                "explanation": "The key factors to consider are:",
                "conclusion": "Based on this analysis, here are the main insights:"
            },
            ConversationMode.BALANCED: {
                "greeting": "I understand this is important to you. Let's explore this together.",
                "empathy": "I can see why this {emotion} you, and here's what we might consider:",
                "solution": "Given how you're feeling, here are some thoughtful approaches:",
                "summary": "So to summarize both the emotional and practical aspects:"
            }
        }

    async def generate_conversation_context(
        self, 
        message: str,
        user_id: str = "conversation_engine",
        user_history: Optional[List[Dict[str, Any]]] = None,
        emotional_context: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """Generate comprehensive conversation context using RoBERTa analysis"""
        
        # Detect conversation mode
        conversation_mode = await self.mode_detector.detect_conversation_mode(
            message, user_id, user_history, emotional_context
        )
        
        # Detect interaction type
        interaction_type = await self.mode_detector.detect_interaction_type(
            message, user_id, conversation_mode
        )
        
        # Detect personality type
        personality_type = await self.mode_detector.detect_personality_type(
            message, user_id, interaction_type, emotional_context
        )
        
        # Get detailed emotional context if using RoBERTa
        emotional_state = None
        secondary_emotions = None
        emotional_intensity = 0.5
        emotion_complexity = "simple"
        roberta_confidence = 0.0
        
        if self.mode_detector.use_roberta and self.mode_detector.emotion_analyzer:
            try:
                emotion_result = await self.mode_detector.emotion_analyzer.analyze_emotion(
                    content=message,
                    user_id=user_id
                )
                
                emotional_state = emotion_result.primary_emotion
                emotional_intensity = emotion_result.intensity
                roberta_confidence = emotion_result.confidence
                
                # Get secondary emotions
                if emotion_result.all_emotions:
                    primary = emotion_result.primary_emotion
                    secondary_emotions = [
                        emotion for emotion, intensity in emotion_result.all_emotions.items()
                        if emotion != primary and intensity > 0.3
                    ][:3]
                
                # Determine complexity
                if len(emotion_result.all_emotions) > 2:
                    emotion_complexity = "complex"
                elif len(emotion_result.all_emotions) > 1:
                    emotion_complexity = "mixed"
                
            except (ValueError, RuntimeError, TypeError) as e:
                logger.warning("Failed to get detailed emotional context: %s", e)
        
        # Determine relationship level (simplified)
        relationship_level = "new"  # Could be enhanced with user history analysis
        
        # Calculate confidence score
        confidence_score = min(0.9, 0.6 + (roberta_confidence * 0.3))
        
        return ConversationContext(
            mode=conversation_mode,
            interaction_type=interaction_type,
            personality_type=personality_type,
            emotional_state=emotional_state,
            secondary_emotions=secondary_emotions,
            emotional_intensity=emotional_intensity,
            emotion_complexity=emotion_complexity,
            relationship_level=relationship_level,
            conversation_history_depth=len(user_history) if user_history else 0,
            user_preferences=emotional_context,
            confidence_score=confidence_score,
            roberta_confidence=roberta_confidence
        )

    def get_conversation_template(
        self, 
        context: ConversationContext,
        template_type: str = "greeting"
    ) -> str:
        """Get appropriate conversation template based on context"""
        
        mode_templates = self.conversation_templates.get(context.mode, {})
        template = mode_templates.get(template_type, "I'm here to help you with whatever you need.")
        
        # Personalize template with emotional context
        if context.emotional_state and "{emotion}" in template:
            emotion_verb_map = {
                "fear": "worries",
                "anger": "frustrates", 
                "sadness": "saddens",
                "joy": "excites",
                "surprise": "surprises",
                "disgust": "bothers"
            }
            
            emotion_verb = emotion_verb_map.get(context.emotional_state, "affects")
            template = template.format(emotion=emotion_verb)
        
        return template

    def generate_response_guidelines(self, context: ConversationContext) -> Dict[str, str]:
        """Generate response guidelines based on conversation context"""
        
        guidelines = {
            "tone": "neutral",
            "approach": "balanced",
            "focus": "user_needs",
            "style": "natural"
        }
        
        # Adjust based on conversation mode
        if context.mode == ConversationMode.HUMAN_LIKE:
            guidelines.update({
                "tone": "warm and empathetic",
                "approach": "supportive",
                "focus": "emotional_validation",
                "style": "conversational"
            })
        elif context.mode == ConversationMode.ANALYTICAL:
            guidelines.update({
                "tone": "professional and clear",
                "approach": "systematic",
                "focus": "information_accuracy", 
                "style": "structured"
            })
        
        # Adjust based on emotional state
        if context.emotional_state in ["fear", "anger", "sadness"]:
            guidelines["sensitivity"] = "high"
            guidelines["validation"] = "prioritize"
        elif context.emotional_state == "joy":
            guidelines["enthusiasm"] = "match_user_energy"
        
        # Adjust based on intensity
        if context.emotional_intensity > 0.7:
            guidelines["urgency"] = "acknowledge_intensity"
        
        return guidelines


# Backward compatibility aliases
ConversationModeDetector = RobertaConversationModeDetector
HumanLikeConversationEngine = RobertaHumanLikeConversationEngine