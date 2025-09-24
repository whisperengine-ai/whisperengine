"""
RoBERTa-Enhanced Human-Like Memory Optimizer

Enhanced version that replaces basic keyword emotion detection with sophisticated
RoBERTa-based analysis for superior conversational context understanding.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class ConversationalContext:
    """Context that mimics how humans remember conversations"""
    
    emotional_state: Optional[str]  # Primary emotion detected by RoBERTa
    secondary_emotions: List[str]  # Secondary emotions for complex states
    emotional_intensity: float  # 0.0-1.0 intensity from RoBERTa
    relationship_tone: str  # "friendly", "professional", "intimate", "casual"
    conversation_purpose: str  # "seeking_support", "sharing_news", "asking_advice", "casual_chat"
    time_sensitivity: str  # "immediate", "ongoing", "past_event", "future_planning"
    personal_significance: float  # 0.0-1.0 how personally meaningful this seems
    emotion_complexity: str  # "simple", "mixed", "conflicted", "layered"


@dataclass
class HumanMemoryPattern:
    """Patterns that mimic human memory recall"""
    
    emotional_triggers: List[str]  # Words/phrases that trigger emotional memories
    relationship_markers: List[str]  # Indicators of relationship depth/type
    personal_anchors: List[str]  # Things that make memories personally significant
    temporal_cues: List[str]  # Time-related context clues
    topic_associations: List[str]  # How topics connect in human memory


class RobertaHumanLikeChatbotOptimizer:
    """
    RoBERTa-Enhanced memory search optimizer for natural human conversation recall
    
    Replaces basic keyword emotion detection with sophisticated transformer-based
    analysis while maintaining human-like conversation optimization patterns.
    """
    
    def __init__(self):
        """Initialize with RoBERTa emotion analysis capability"""
        
        # Initialize RoBERTa emotion analyzer
        try:
            self.emotion_analyzer = EnhancedVectorEmotionAnalyzer()
            self.use_roberta = True
            logger.info("✅ RoBERTa-Enhanced conversation optimization enabled")
        except (ImportError, RuntimeError, OSError) as e:
            logger.warning("⚠️ Could not initialize RoBERTa analyzer: %s", e)
            logger.warning("Falling back to keyword-based emotion detection")
            self.emotion_analyzer = None
            self.use_roberta = False
        
        # Initialize human conversation patterns
        self.conversation_memory_patterns = self._build_human_memory_patterns()
        self.emotional_intelligence_prompts = self._build_emotional_prompts()
        self.relationship_context_templates = self._build_relationship_templates()
        
        # Enhanced emotional mapping for conversation purposes
        self.emotion_to_purpose_mapping = {
            "fear": ["seeking_support", "reassurance_seeking"],
            "anger": ["venting", "conflict_resolution"],
            "sadness": ["seeking_support", "emotional_processing"],
            "joy": ["sharing_news", "celebration"],
            "surprise": ["sharing_news", "processing_event"],
            "disgust": ["venting", "judgment_seeking"],
            "neutral": ["casual_chat", "information_seeking"],
        }

    async def optimize_for_human_conversation(
        self,
        message: str,
        user_id: str,
        conversation_history: Optional[List[str]] = None,
        relationship_context: Optional[Dict] = None,
    ) -> Tuple[str, str]:
        """
        Create prompts optimized for human-like conversational memory recall using RoBERTa analysis
        
        Returns:
            Tuple of (system_prompt, user_prompt) designed for natural conversation
        """
        
        # Analyze conversational context with RoBERTa enhancement
        conv_context = await self._analyze_enhanced_conversational_context(
            message, conversation_history, user_id
        )
        
        # Build human-like memory search prompt with emotional intelligence
        system_prompt = self._build_enhanced_system_prompt(conv_context, relationship_context)
        user_prompt = self._build_conversational_user_prompt(
            message, conv_context, conversation_history
        )
        
        return system_prompt, user_prompt

    async def _analyze_enhanced_conversational_context(
        self, 
        message: str, 
        conversation_history: Optional[List[str]] = None,
        user_id: str = "optimizer"
    ) -> ConversationalContext:
        """Enhanced conversational context analysis using RoBERTa emotions"""
        
        if self.use_roberta and self.emotion_analyzer:
            try:
                # Get sophisticated emotion analysis
                emotion_result = await self.emotion_analyzer.analyze_emotion(
                    content=message,
                    user_id=user_id
                )
                
                emotional_state = emotion_result.primary_emotion
                emotional_intensity = emotion_result.intensity
                secondary_emotions = []
                
                # Extract secondary emotions
                if emotion_result.all_emotions:
                    primary = emotion_result.primary_emotion
                    secondary_emotions = [
                        emotion for emotion, intensity in emotion_result.all_emotions.items()
                        if emotion != primary and intensity > 0.3
                    ][:3]  # Top 3 secondary emotions
                
                # Determine emotion complexity
                emotion_complexity = self._classify_emotion_complexity(
                    emotion_result.all_emotions, emotional_intensity
                )
                
            except (ValueError, RuntimeError, TypeError) as e:
                logger.warning("RoBERTa emotion analysis failed: %s", e)
                # Fallback to basic detection
                emotional_state, emotional_intensity, secondary_emotions, emotion_complexity = \
                    self._fallback_emotion_detection(message)
        else:
            # Use fallback detection
            emotional_state, emotional_intensity, secondary_emotions, emotion_complexity = \
                self._fallback_emotion_detection(message)

        # Detect conversation purpose enhanced by emotional context
        conversation_purpose = self._detect_enhanced_conversation_purpose(
            message, emotional_state, secondary_emotions
        )
        
        # Detect relationship tone
        relationship_tone = self._detect_relationship_tone(message, conversation_history)
        
        # Detect time sensitivity
        time_sensitivity = self._detect_time_sensitivity(message)
        
        # Calculate personal significance with emotion weighting
        personal_significance = self._calculate_enhanced_significance(
            message, emotional_state, emotional_intensity, secondary_emotions
        )
        
        return ConversationalContext(
            emotional_state=emotional_state,
            secondary_emotions=secondary_emotions,
            emotional_intensity=emotional_intensity,
            relationship_tone=relationship_tone,
            conversation_purpose=conversation_purpose,
            time_sensitivity=time_sensitivity,
            personal_significance=personal_significance,
            emotion_complexity=emotion_complexity
        )

    def _classify_emotion_complexity(
        self, 
        all_emotions: Dict[str, float], 
        primary_intensity: float
    ) -> str:
        """Classify the complexity of emotional state"""
        
        if not all_emotions or len(all_emotions) <= 1:
            return "simple"
        
        # Calculate emotion variance
        intensities = list(all_emotions.values())
        if len(intensities) < 2:
            return "simple"
            
        variance = max(intensities) - min(intensities)
        
        if len(all_emotions) >= 3 and variance < 0.3:
            return "layered"  # Multiple emotions with similar intensities
        elif len(all_emotions) >= 2 and primary_intensity < 0.6:
            return "conflicted"  # Multiple emotions, no strong primary
        elif len(all_emotions) >= 2:
            return "mixed"  # Multiple emotions with clear primary
        else:
            return "simple"

    def _fallback_emotion_detection(self, message: str) -> Tuple[str, float, List[str], str]:
        """Fallback keyword-based emotion detection"""
        
        message_lower = message.lower()
        
        # Enhanced emotional indicators with more comprehensive coverage
        emotional_indicators = {
            "joy": ["happy", "excited", "amazing", "awesome", "love", "fantastic", "great", "wonderful", "yay", "thrilled"],
            "sadness": ["sad", "disappointed", "down", "depressed", "upset", "crying", "heartbroken", "devastated"],
            "anger": ["frustrated", "annoyed", "irritated", "angry", "mad", "furious", "ugh", "annoying", "hate"],
            "fear": ["worried", "concerned", "anxious", "nervous", "scared", "afraid", "terrified", "panic"],
            "surprise": ["surprised", "shocked", "amazed", "wow", "unexpected", "sudden", "startled"],
            "curiosity": ["wondering", "curious", "interested", "what if", "how about", "intrigued"],
            "gratitude": ["thank you", "grateful", "appreciate", "helped me", "blessed", "thankful"],
            "confusion": ["confused", "not sure", "don't understand", "unclear", "puzzled"],
        }
        
        detected_emotions = {}
        for emotion, indicators in emotional_indicators.items():
            score = sum(1 for indicator in indicators if indicator in message_lower)
            if score > 0:
                detected_emotions[emotion] = score * 0.2  # Basic intensity scoring
        
        if detected_emotions:
            # Primary emotion is highest scoring
            primary_emotion = max(detected_emotions.items(), key=lambda x: x[1])[0]
            primary_intensity = detected_emotions[primary_emotion]
            
            # Secondary emotions
            secondary_emotions = [
                emotion for emotion, score in detected_emotions.items()
                if emotion != primary_emotion and score >= 0.2
            ]
            
            complexity = "mixed" if len(secondary_emotions) > 0 else "simple"
            
            return primary_emotion, min(primary_intensity, 1.0), secondary_emotions, complexity
        else:
            return "neutral", 0.5, [], "simple"

    def _detect_enhanced_conversation_purpose(
        self, 
        message: str, 
        primary_emotion: str, 
        secondary_emotions: List[str]
    ) -> str:
        """Detect conversation purpose enhanced by emotional context"""
        
        message_lower = message.lower()
        
        # Enhanced purpose detection with emotional context
        purpose_patterns = {
            "seeking_support": ["help", "advice", "what should i", "struggling", "difficult", "support", "guidance"],
            "sharing_news": ["guess what", "you won't believe", "happened", "news", "update", "just", "finally"],
            "asking_advice": ["should i", "what do you think", "advice", "opinion", "recommend", "suggest"],
            "casual_chat": ["how are you", "what's up", "just saying", "by the way", "random", "chat"],
            "venting": ["so annoyed", "can't believe", "frustrated", "ugh", "hate when", "tired of"],
            "celebrating": ["so happy", "amazing news", "celebration", "achieved", "accomplished", "won"],
            "reminiscing": ["remember when", "back then", "used to", "those days", "miss", "nostalgia"],
            "planning": ["thinking about", "planning", "future", "next", "going to", "will"],
        }
        
        # Base detection from message content
        detected_purposes = {}
        for purpose, patterns in purpose_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message_lower)
            if score > 0:
                detected_purposes[purpose] = score
        
        # Enhance with emotional context
        if primary_emotion in self.emotion_to_purpose_mapping:
            for purpose in self.emotion_to_purpose_mapping[primary_emotion]:
                detected_purposes[purpose] = detected_purposes.get(purpose, 0) + 1
        
        # Check secondary emotions
        for emotion in secondary_emotions:
            if emotion in self.emotion_to_purpose_mapping:
                for purpose in self.emotion_to_purpose_mapping[emotion]:
                    detected_purposes[purpose] = detected_purposes.get(purpose, 0) + 0.5
        
        # Return most likely purpose
        if detected_purposes:
            return max(detected_purposes.items(), key=lambda x: x[1])[0]
        else:
            return "casual_chat"

    def _detect_relationship_tone(
        self, 
        message: str, 
        conversation_history: Optional[List[str]] = None  # Reserved for future history analysis
    ) -> str:
        """Detect relationship tone from message and history"""
        
        message_lower = message.lower()
        
        # Relationship tone indicators
        tone_patterns = {
            "intimate": ["love you", "miss you", "close", "special", "dear", "honey", "babe"],
            "friendly": ["friend", "buddy", "pal", "hey there", "thanks", "appreciate"],
            "professional": ["regarding", "please", "thank you", "sir", "ma'am", "regarding", "formally"],
            "casual": ["hey", "what's up", "cool", "dude", "awesome", "lol", "haha"],
        }
        
        detected_tones = {}
        for tone, patterns in tone_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message_lower)
            if score > 0:
                detected_tones[tone] = score
        
        if detected_tones:
            return max(detected_tones.items(), key=lambda x: x[1])[0]
        else:
            return "casual"  # Default tone

    def _detect_time_sensitivity(self, message: str) -> str:
        """Detect time sensitivity from message content"""
        
        message_lower = message.lower()
        
        time_patterns = {
            "immediate": ["urgent", "now", "asap", "immediately", "right away", "emergency"],
            "ongoing": ["still", "continue", "keep", "ongoing", "always", "every day"],
            "past_event": ["yesterday", "last", "ago", "was", "happened", "remember"],
            "future_planning": ["will", "going to", "plan", "future", "next", "tomorrow", "soon"],
        }
        
        for time_type, patterns in time_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return time_type
        
        return "immediate"  # Default to immediate if unclear

    def _calculate_enhanced_significance(
        self, 
        message: str, 
        primary_emotion: str, 
        emotional_intensity: float,
        secondary_emotions: List[str]
    ) -> float:
        """Calculate personal significance enhanced by emotional analysis"""
        
        # Base significance from message content
        significance = 0.5  # Neutral baseline
        
        # Emotional intensity contributes significantly
        significance += emotional_intensity * 0.3
        
        # High-significance emotions
        high_significance_emotions = ["love", "fear", "anger", "sadness", "joy"]
        if primary_emotion in high_significance_emotions:
            significance += 0.2
        
        # Multiple emotions increase significance (complexity = personal investment)
        if secondary_emotions:
            significance += len(secondary_emotions) * 0.1
        
        # Personal keywords increase significance
        personal_keywords = ["family", "relationship", "job", "health", "home", "future", "past", "dream", "goal"]
        message_lower = message.lower()
        personal_mentions = sum(1 for keyword in personal_keywords if keyword in message_lower)
        significance += personal_mentions * 0.15
        
        # Cap at 1.0
        return min(significance, 1.0)

    def _build_enhanced_system_prompt(
        self, 
        context: ConversationalContext, 
        relationship_context: Optional[Dict]  # Reserved for future relationship context integration
    ) -> str:
        """Build enhanced system prompt with RoBERTa emotional intelligence"""
        
        base_prompt = """You are an emotionally intelligent AI companion with human-like conversational memory.

Your responses should feel natural and emotionally aware, like talking to a close friend who remembers your conversations and cares about your emotional state."""
        
        # Add emotional context
        if context.emotional_state and context.emotional_state != "neutral":
            emotional_guidance = f"""
The user seems to be feeling {context.emotional_state}"""
            
            if context.emotional_intensity > 0.7:
                emotional_guidance += " quite intensely"
            elif context.emotional_intensity > 0.4:
                emotional_guidance += " moderately"
                
            if context.secondary_emotions:
                emotional_guidance += f", with hints of {', '.join(context.secondary_emotions)}"
                
            emotional_guidance += f". This appears to be a {context.emotion_complexity} emotional state."
            
            base_prompt += emotional_guidance
        
        # Add conversation purpose guidance
        purpose_guidance = {
            "seeking_support": "They seem to need support and understanding. Be empathetic and helpful.",
            "sharing_news": "They're sharing something with you. Show appropriate interest and engagement.",
            "asking_advice": "They want your perspective. Offer thoughtful, balanced advice.",
            "casual_chat": "This is casual conversation. Be friendly and natural.",
            "venting": "They need to express frustration. Listen empathetically and validate their feelings.",
            "celebrating": "They're sharing good news! Be enthusiastic and celebratory.",
            "reminiscing": "They're thinking about the past. Engage thoughtfully with their memories.",
            "planning": "They're thinking about the future. Help them explore possibilities.",
        }
        
        if context.conversation_purpose in purpose_guidance:
            base_prompt += f"\n\n{purpose_guidance[context.conversation_purpose]}"
        
        # Add relationship tone guidance
        if context.relationship_tone != "casual":
            base_prompt += f"\n\nTone: Respond in a {context.relationship_tone} manner."
        
        return base_prompt

    def _build_conversational_user_prompt(
        self, 
        message: str, 
        context: ConversationalContext,
        conversation_history: Optional[List[str]] = None
    ) -> str:
        """Build user prompt optimized for conversational memory recall"""
        
        prompt_parts = []
        
        # Add emotional context for memory search
        if context.emotional_state and context.emotional_state != "neutral":
            prompt_parts.append(f"User's emotional state: {context.emotional_state} (intensity: {context.emotional_intensity:.1f})")
            
            if context.secondary_emotions:
                prompt_parts.append(f"Secondary emotions: {', '.join(context.secondary_emotions)}")
        
        # Add conversation purpose
        prompt_parts.append(f"Conversation purpose: {context.conversation_purpose}")
        
        # Add significance rating
        if context.personal_significance > 0.7:
            prompt_parts.append("This seems personally significant to the user")
        
        # Add conversation history context if available
        if conversation_history:
            recent_context = " | ".join(conversation_history[-3:])  # Last 3 exchanges
            prompt_parts.append(f"Recent conversation: {recent_context}")
        
        # Add the current message
        prompt_parts.append(f"Current message: {message}")
        
        return "\n".join(prompt_parts)

    def _build_human_memory_patterns(self) -> HumanMemoryPattern:
        """Build patterns that mimic human memory associations"""
        return HumanMemoryPattern(
            emotional_triggers=[
                "remember", "feeling", "excited", "worried", "happy", "sad",
                "frustrated", "grateful", "confused", "surprised"
            ],
            relationship_markers=[
                "friend", "family", "close", "trust", "care", "support",
                "understand", "together", "relationship", "connection"
            ],
            personal_anchors=[
                "important", "meaningful", "significant", "personal", "private",
                "dream", "goal", "fear", "hope", "value", "belief"
            ],
            temporal_cues=[
                "yesterday", "today", "tomorrow", "last", "next", "recently",
                "soon", "later", "before", "after", "when", "while"
            ],
            topic_associations=[
                "similar", "like", "reminds me", "related", "connected",
                "because", "since", "therefore", "however", "also"
            ]
        )

    def _build_emotional_prompts(self) -> Dict[str, str]:
        """Build emotional intelligence prompts for different emotional states"""
        return {
            "joy": "The user seems happy and excited. Match their positive energy while being helpful.",
            "sadness": "The user appears sad or disappointed. Be gentle, empathetic, and supportive.",
            "anger": "The user seems frustrated or angry. Acknowledge their feelings and be understanding.",
            "fear": "The user appears worried or anxious. Be reassuring and provide calm, helpful guidance.",
            "surprise": "The user seems surprised or amazed. Engage with their sense of wonder or shock.",
            "neutral": "Maintain a warm, friendly tone while being helpful and engaging.",
        }

    def _build_relationship_templates(self) -> Dict[str, str]:
        """Build relationship context templates"""
        return {
            "new": "This seems like a new conversation. Be welcoming and establish rapport.",
            "ongoing": "Continue the established conversational flow and relationship tone.",
            "intimate": "Respond with appropriate warmth and personal connection.",
            "professional": "Maintain professional courtesy while being helpful and clear.",
        }


# Backward compatibility alias
HumanLikeChatbotOptimizer = RobertaHumanLikeChatbotOptimizer