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

# Import enhanced emotion analysis
try:
    from src.intelligence.enhanced_vector_emotion_analyzer import (
        EnhancedVectorEmotionAnalyzer,
        create_enhanced_emotion_analyzer
    )
    ENHANCED_EMOTION_ANALYZER_AVAILABLE = True
except ImportError as e:
    logger.warning("Enhanced Vector Emotion Analyzer not available: %s", e)
    ENHANCED_EMOTION_ANALYZER_AVAILABLE = False
    EnhancedVectorEmotionAnalyzer = None
    create_enhanced_emotion_analyzer = None

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
        emoji_mapper: Optional[EmojiEmotionMapper] = None,
        cdl_database_manager=None  # Optional CDLDatabaseManager for connection pooling
    ):
        self.memory_manager = memory_manager
        self.emoji_mapper = emoji_mapper or EmojiEmotionMapper()
        self.cdl_database = cdl_database_manager  # Store CDL database manager
        
        # Initialize Enhanced Vector Emotion Analyzer if available
        self.enhanced_emotion_analyzer = None
        if ENHANCED_EMOTION_ANALYZER_AVAILABLE:
            try:
                self.enhanced_emotion_analyzer = create_enhanced_emotion_analyzer(memory_manager)
                logger.info("✅ Enhanced Vector Emotion Analyzer initialized successfully")
            except Exception as e:
                logger.warning("Failed to initialize Enhanced Vector Emotion Analyzer: %s", e)
                self.enhanced_emotion_analyzer = None
        
        # Read emoji configuration from environment - always enabled in development!
        self.emoji_enabled = True  # Always enabled in development
        self.base_threshold = float(os.getenv("EMOJI_BASE_THRESHOLD", "0.4"))
        self.new_user_threshold = float(os.getenv("EMOJI_NEW_USER_THRESHOLD", "0.3"))
        self.visual_reaction_enabled = True  # Always enabled in development
        
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
        
        # Character emoji frequency cache
        self._emoji_frequency_cache: Dict[str, str] = {}
    
    async def _get_character_emoji_frequency(self, bot_character: str) -> str:
        """
        Fetch character's emoji_frequency setting from database using connection pool.
        
        Returns one of: 'none', 'minimal', 'low', 'moderate', 'high', 'selective_symbolic'
        Defaults to 'moderate' if not found.
        """
        # Check cache first
        if bot_character in self._emoji_frequency_cache:
            return self._emoji_frequency_cache[bot_character]
        
        try:
            # Use CDL database manager's connection pool if available
            if self.cdl_database and self.cdl_database.pool:
                async with self.cdl_database.pool.acquire() as conn:
                    # Query by normalized_name (e.g., "jake" → "Jake Sterling")
                    result = await conn.fetchrow(
                        'SELECT emoji_frequency FROM characters WHERE LOWER(normalized_name) = LOWER($1)',
                        bot_character
                    )
                    
                    if result and result['emoji_frequency']:
                        frequency = result['emoji_frequency']
                        self._emoji_frequency_cache[bot_character] = frequency
                        logger.info("📊 Character '%s' emoji_frequency: %s", bot_character, frequency)
                        return frequency
                    else:
                        logger.warning("⚠️ Character '%s' not found in database, using 'moderate'", bot_character)
                        self._emoji_frequency_cache[bot_character] = 'moderate'
                        return 'moderate'
            else:
                # Fallback: create temporary connection (not recommended for production)
                logger.warning("⚠️ CDL database manager not available, using temporary connection")
                import asyncpg
                
                conn = await asyncpg.connect(
                    host=os.getenv('POSTGRES_HOST', 'localhost'),
                    port=int(os.getenv('POSTGRES_PORT', '5432')),
                    user=os.getenv('POSTGRES_USER', 'whisperengine'),
                    password=os.getenv('POSTGRES_PASSWORD', 'whisperengine_dev'),
                    database=os.getenv('POSTGRES_DB', 'whisperengine')
                )
                
                # Query by normalized_name (e.g., "jake" → "Jake Sterling")
                result = await conn.fetchrow(
                    'SELECT emoji_frequency FROM characters WHERE LOWER(normalized_name) = LOWER($1)',
                    bot_character
                )
                
                await conn.close()
                
                if result and result['emoji_frequency']:
                    frequency = result['emoji_frequency']
                    self._emoji_frequency_cache[bot_character] = frequency
                    logger.info("📊 Character '%s' emoji_frequency: %s", bot_character, frequency)
                    return frequency
                else:
                    logger.warning("⚠️ Character '%s' not found in database, using 'moderate'", bot_character)
                    self._emoji_frequency_cache[bot_character] = 'moderate'
                    return 'moderate'
                
        except Exception as e:
            logger.error("Error fetching character emoji frequency: %s", str(e))
            # Fallback to moderate
            return 'moderate'
    
    def _apply_emoji_frequency_modifier(
        self,
        emoji_frequency: str,
        confidence_score: float,
        base_threshold: float
    ) -> Tuple[float, float]:
        """
        Apply emoji frequency setting to adjust confidence score and threshold.
        
        Frequency probabilities:
        - none: 0% (never use emoji)
        - minimal: 10%
        - low: 30%
        - moderate: 60%
        - high: 90%
        - selective_symbolic: 20% (but meaningful)
        
        Returns: (adjusted_threshold, probability_modifier)
        """
        frequency_config = {
            'none': {'threshold': 1.0, 'probability': 0.0},  # Impossible threshold
            'minimal': {'threshold': base_threshold + 0.4, 'probability': 0.10},
            'low': {'threshold': base_threshold + 0.2, 'probability': 0.30},
            'moderate': {'threshold': base_threshold, 'probability': 0.60},
            'high': {'threshold': base_threshold - 0.15, 'probability': 0.90},
            'selective_symbolic': {'threshold': base_threshold + 0.25, 'probability': 0.20}
        }
        
        config = frequency_config.get(emoji_frequency, frequency_config['moderate'])
        adjusted_threshold = config['threshold']
        probability = config['probability']
        
        logger.info(f"🎚️ Emoji frequency '{emoji_frequency}': threshold={adjusted_threshold:.2f}, target_probability={probability:.0%}")
        
        return adjusted_threshold, probability
    
    def _is_celebratory_emoji(self, emoji: str) -> bool:
        """
        Check if emoji is appropriate for distress contexts (WHITELIST approach).
        
        Returns False if emoji is in the ALLOWED list for empathy/distress.
        Returns True if emoji should be filtered out.
        
        During distress, ONLY allow empathetic/neutral emojis.
        """
        # WHITELIST: Emojis that ARE appropriate during distress
        # Includes: support emojis + empathy-mirroring emojis (sad faces OK for sad users)
        allowed_empathy_emojis = [
            # Support & care emojis
            '💙',  # Blue heart - empathy
            '💔',  # Broken heart - acknowledgment
            '🙏',  # Praying hands - support
            '❤️',  # Red heart - love/care
            '🫂',  # Hugging face - comfort
            '👍',  # Thumbs up - simple acknowledgment
            '✅',  # Check mark - simple acknowledgment
            # Empathy-mirroring emojis (reflect user's emotion back)
            '😢',  # Crying face - mirrors sadness
            '😔',  # Pensive face - mirrors contemplation/sadness
            '😞',  # Disappointed face - mirrors disappointment
            '🥺',  # Pleading face - mirrors vulnerability
            '😟',  # Worried face - mirrors concern/worry
            '😥',  # Sad but relieved - mirrors mixed emotions
        ]
        
        # If emoji is in allowed list, it's NOT celebratory (return False)
        # If emoji is NOT in allowed list, filter it out (return True)
        return emoji not in allowed_empathy_emojis
    
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
    
    async def _analyze_message_emotions(self, user_id: str, user_message: str) -> List[str]:
        """
        Analyze message emotions using Enhanced Vector Emotion Analyzer.
        Falls back to keyword detection if enhanced analyzer is unavailable.
        """
        try:
            # Use Enhanced Vector Emotion Analyzer if available
            if self.enhanced_emotion_analyzer is not None:
                emotion_result = await self.enhanced_emotion_analyzer.analyze_emotion(
                    content=user_message,
                    user_id=user_id
                )
                emotions = [emotion_result.primary_emotion]
                
                # Add secondary emotions based on confidence
                if emotion_result.all_emotions:
                    secondary_emotions = [
                        emotion for emotion, confidence in emotion_result.all_emotions.items()
                        if emotion != emotion_result.primary_emotion and confidence > 0.3
                    ]
                    emotions.extend(secondary_emotions[:2])  # Add up to 2 secondary emotions
                    
                return emotions
            
            # Fallback to simple keyword detection using standardized taxonomy
            from src.intelligence.emotion_taxonomy import standardize_emotion
            
            emotion_keywords = {
                "joy": ["happy", "excited", "great", "awesome", "amazing", "wonderful", "fantastic", "love", "😀", "😁", "😂", "😃", "😄", "😆", "🤩", "❤️"],
                "sadness": ["sad", "crying", "upset", "down", "depressed", "😢", "😭", "😔", "💔", "😞"],
                "anger": ["angry", "mad", "furious", "annoyed", "frustrated", "😠", "😡", "🤬"],
                "fear": ["scared", "afraid", "worried", "anxious", "nervous", "😰", "😱", "😨"],
                "surprise": ["surprised", "shocked", "wow", "omg", "😲", "😱", "🤯"],
                "neutral": ["okay", "sure", "maybe", "alright", "fine", "🤔"],
                "disgust": ["gross", "disgusting", "awful", "terrible", "yuck", "🤢"]
                # Note: Extended emotions like gratitude, excitement map to core emotions via taxonomy
            }
            
            message_lower = user_message.lower()
            detected_emotions = []
            
            for emotion, keywords in emotion_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    # Standardize emotion to core taxonomy
                    standardized_emotion = standardize_emotion(emotion)
                    if standardized_emotion not in detected_emotions:
                        detected_emotions.append(standardized_emotion)
            
            return detected_emotions if detected_emotions else ["neutral"]
            
        except Exception as e:
            logger.error("Error analyzing message emotions: %s", e)
            return ["neutral"]
    
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
    
    async def _get_user_emoji_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        🎯 PERSONALIZATION: Retrieve user's emoji preferences from history.
        
        Priority 5 Enhancement: User-personalized character emoji sets
        
        Queries memory system and personality analysis to build a comprehensive
        emoji preference profile including:
        - Positive reactions (emojis user has reacted positively to)
        - Negative reactions (emojis user disliked)
        - Emoji comfort level (0.0=minimal, 1.0=loves emojis)
        - Successful emojis (historically effective)
        
        Returns:
            Dict with keys:
            - 'positive_reactions': List[str] - Emojis user liked
            - 'negative_reactions': List[str] - Emojis user disliked
            - 'emoji_comfort_level': float - 0.0 to 1.0
            - 'successful_emojis': List[str] - Historically effective emojis
        """
        try:
            preferences = {
                "positive_reactions": [],
                "negative_reactions": [],
                "emoji_comfort_level": 0.5,  # Default moderate
                "successful_emojis": []
            }
            
            # Get emoji comfort level from personality analysis
            personality_context = await self._analyze_user_personality_context(user_id)
            preferences["emoji_comfort_level"] = personality_context.get("emoji_comfort_level", 0.5)
            
            # Query memory system for emoji reaction history
            # Look for stored emoji reactions (stored with [EMOJI_REACTION] prefix)
            emoji_reaction_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="[EMOJI_REACTION] [EMOTIONAL_FEEDBACK]",
                limit=50  # Get last 50 emoji reactions
            )
            
            # Analyze emoji reactions to build preference profile
            positive_emojis = []
            negative_emojis = []
            successful_emojis = []
            
            for memory in emoji_reaction_memories:
                metadata = memory.get("metadata", {})
                
                # Check if this was an emoji reaction
                if metadata.get("interaction_type") == "emoji_reaction":
                    emoji = metadata.get("emoji", "")
                    reaction_type = metadata.get("emotion_type", "")
                    confidence = metadata.get("confidence_score", 0.5)
                    
                    # High confidence positive reactions
                    if confidence > 0.7 and reaction_type in ["positive", "love", "joy", "excitement"]:
                        if emoji and emoji not in positive_emojis:
                            positive_emojis.append(emoji)
                            successful_emojis.append(emoji)
                    
                    # High confidence negative reactions
                    elif confidence > 0.7 and reaction_type in ["negative", "dislike", "anger", "frustration"]:
                        if emoji and emoji not in negative_emojis:
                            negative_emojis.append(emoji)
            
            preferences["positive_reactions"] = positive_emojis
            preferences["negative_reactions"] = negative_emojis
            preferences["successful_emojis"] = successful_emojis
            
            logger.debug(f"🎯 User {user_id} emoji preferences: comfort={preferences['emoji_comfort_level']:.2f}, "
                        f"positive={len(positive_emojis)}, negative={len(negative_emojis)}")
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error retrieving user emoji preferences: {e}")
            return {
                "positive_reactions": [],
                "negative_reactions": [],
                "emoji_comfort_level": 0.5,
                "successful_emojis": []
            }
    
    async def _get_personalized_character_emojis(
        self,
        user_id: str,
        bot_character: str,
        emotion_category: str
    ) -> List[str]:
        """
        🎨 PERSONALIZATION: Select character emojis based on user history.
        
        Priority 5 Enhancement: Character emoji sets become personalized
        
        Instead of using static character emoji sets, this dynamically adjusts
        the emoji selection based on:
        1. User's past emoji reactions (prioritize ones they liked)
        2. Emoji comfort level (simple vs elaborate)
        3. Historical success patterns
        
        Args:
            user_id: User identifier
            bot_character: Character archetype (mystical, technical, general)
            emotion_category: Category of emotion (wonder, positive, acknowledgment, playful, negative)
        
        Returns:
            List[str] of personalized emojis filtered and prioritized for this user
        """
        try:
            # Get base character emoji set
            character_emojis = self.character_emoji_sets.get(
                bot_character, 
                self.character_emoji_sets["general"]
            )
            
            # Get emojis for this emotion category
            base_emojis = character_emojis.get(emotion_category, character_emojis.get("positive", ["😊"]))
            
            if not base_emojis:
                logger.warning(f"No emojis found for character={bot_character}, category={emotion_category}")
                return ["😊"]  # Fallback to smile
            
            # Retrieve user's emoji preferences
            emoji_preferences = await self._get_user_emoji_preferences(user_id)
            
            # Strategy 1: Filter for user-preferred emojis (if they have history)
            positive_reactions = emoji_preferences.get("positive_reactions", [])
            if positive_reactions:
                # Prioritize emojis the user has reacted positively to
                preferred_emojis = [emoji for emoji in base_emojis if emoji in positive_reactions]
                if preferred_emojis:
                    logger.debug(f"🎨 Using user-preferred emojis: {preferred_emojis}")
                    return preferred_emojis
            
            # Strategy 2: Adjust for emoji comfort level (if no explicit preferences)
            emoji_comfort = emoji_preferences.get("emoji_comfort_level", 0.5)
            
            if emoji_comfort < 0.3:
                # User prefers minimal emojis - use first 2 (usually simplest)
                result = base_emojis[:2]
                logger.debug(f"🎨 Low emoji comfort ({emoji_comfort:.2f}): using {result}")
                return result
            
            elif emoji_comfort > 0.7:
                # User loves emojis - use full set
                logger.debug(f"🎨 High emoji comfort ({emoji_comfort:.2f}): using full set ({len(base_emojis)} emojis)")
                return base_emojis
            
            else:
                # Moderate comfort - use 3 emojis
                result = base_emojis[:3]
                logger.debug(f"🎨 Moderate emoji comfort ({emoji_comfort:.2f}): using {result}")
                return result
            
        except Exception as e:
            logger.error(f"Error getting personalized character emojis: {e}")
            # Fallback to base character emojis
            character_emojis = self.character_emoji_sets.get(
                bot_character, 
                self.character_emoji_sets["general"]
            )
            return character_emojis.get(emotion_category, ["😊"])
    
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
            current_emotions = await self._analyze_message_emotions(user_id, user_message)
            
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
                    content_emotions = await self._analyze_message_emotions(user_id, content)
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
        
        # 🎯 Apply character-specific emoji frequency from database
        logger.info("🔍 DEBUG: About to call _get_character_emoji_frequency for bot_character='%s'", bot_character)
        character_emoji_frequency = await self._get_character_emoji_frequency(bot_character)
        logger.info("🔍 DEBUG: Got emoji frequency: '%s'", character_emoji_frequency)
        adjusted_threshold, target_probability = self._apply_emoji_frequency_modifier(
            character_emoji_frequency,
            confidence_score,
            base_threshold
        )
        logger.info("🔍 DEBUG: Applied frequency modifier - adjusted_threshold=%.2f, target=%.0f%%", 
                   adjusted_threshold, target_probability)
        
        # Use the adjusted threshold from character settings
        emoji_threshold = adjusted_threshold
        
        # Adjust threshold based on user's emoji comfort (minor adjustments only)
        if emoji_comfort > 0.8:
            emoji_threshold = emoji_threshold - 0.05  # Slight adjustment for emoji-friendly users
        elif emoji_comfort < 0.2:
            emoji_threshold = emoji_threshold + 0.05  # Slight adjustment for conservative users
        
        # Special case: 'none' frequency means never use emoji
        if character_emoji_frequency == 'none':
            should_use_emoji = False
            emoji_threshold = 1.0  # Impossible threshold
        else:
            # Final decision based on adjusted threshold
            should_use_emoji = confidence_score >= emoji_threshold
        
        # Select optimal emoji with enhanced context
        emoji_choice = None
        context_reason = EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        
        if should_use_emoji:
            emoji_choice, context_reason = await self._select_enhanced_optimal_emoji(
                user_id, user_message, bot_character, conversation_patterns, 
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
                "threshold_used": emoji_threshold,
                "character_emoji_frequency": character_emoji_frequency,
                "target_probability": target_probability,
                "base_threshold": base_threshold
            }
        )
    
    def _select_emotion_aware_empathy_emoji(
        self,
        emotional_state: Dict[str, Any],
        bot_character: str
    ) -> str:
        """
        🎯 EMOTION-AWARE EMPATHY: Select empathy emoji based on user's actual emotion.
        
        Replaces hard-coded "💙" with intelligent selection based on:
        - User's primary emotion (sadness, fear, anger, disappointment)
        - Emotional intensity (mild concern vs deep distress)
        - Character archetype (mystical uses 🙏, others use hearts/faces)
        
        Args:
            emotional_state: Complete emotional analysis with primary_emotion and intensity
            bot_character: Character type for archetype-specific empathy
        
        Returns:
            Appropriate empathy emoji string
        """
        primary_emotion = emotional_state.get("current_emotion", "neutral")
        intensity = emotional_state.get("intensity", 0.5)
        
        # MYSTICAL characters use prayer hands for empathy
        if bot_character == "mystical":
            return "🙏"
        
        # EMOTION-SPECIFIC EMPATHY SELECTION
        # 🚨 CRITICAL FIX: For emoji REACTIONS, NEVER mirror distress emotions
        # Mirroring sadness/fear/anger feels tone-deaf and insensitive
        # Use SUPPORTIVE emojis only (�, 🫂) for all distress emotions
        
        # Sadness → ALWAYS use supportive blue heart (no mirroring)
        if primary_emotion in ['sadness', 'grief', 'melancholy']:
            # All intensities → blue heart (gentle support, not mirroring)
            logger.debug("💙 Empathy: Sadness (%.2f) → blue heart (supportive, not mirroring)", intensity)
            return "💙"
        
        # Fear/Anxiety → ALWAYS use supportive blue heart (no worried faces)
        if primary_emotion in ['fear', 'anxiety', 'nervousness', 'worry']:
            # All intensities → blue heart (reassurance, not mirroring)
            logger.debug("💙 Empathy: Fear (%.2f) → blue heart (supportive, not mirroring)", intensity)
            return "💙"
        
        # Anger/Frustration → ALWAYS use supportive blue heart (no angry/disappointed faces)
        if primary_emotion in ['anger', 'frustration', 'irritation', 'annoyance']:
            # All intensities → blue heart (understanding, not mirroring)
            logger.debug("💙 Empathy: Anger (%.2f) → blue heart (supportive, not mirroring)", intensity)
            return "�"
        
        # Disappointment → Disappointed face OR pleading face
        if primary_emotion in ['disappointment', 'regret', 'shame']:
            if intensity > 0.6:
                # High disappointment → pleading face (vulnerability)
                logger.debug("💙 Empathy: High disappointment (%.2f) → pleading face", intensity)
                return "🥺"
            else:
                # Moderate disappointment → disappointed face
                logger.debug("💙 Empathy: Moderate disappointment (%.2f) → disappointed face", intensity)
                return "😞"
        
        # Mixed/Complex negative emotions → Sad but relieved
        if primary_emotion in ['confusion', 'overwhelm', 'conflicted']:
            logger.debug("💙 Empathy: Complex emotion (%s) → sad but relieved", primary_emotion)
            return "😥"
        
        # DEFAULT: Blue heart for general empathy (safe fallback)
        logger.debug("💙 Empathy: Default for %s → blue heart", primary_emotion)
        return "💙"
    
    def _select_trajectory_aware_emoji(
        self,
        emotional_state: Dict[str, Any],
        bot_character: str,
        user_in_distress: bool
    ) -> Optional[Tuple[str, EmojiResponseContext]]:
        """
        🎯 TRAJECTORY-AWARE SELECTION: Select emoji based on emotional trajectory, not keywords.
        
        Replaces hard-coded keyword matching with intelligent analysis of:
        - Emotional trajectory (rising, falling, stable)
        - Primary emotion + intensity
        - RoBERTa confidence
        - User distress context
        
        Args:
            emotional_state: Complete emotional analysis with trajectory
            bot_character: Character type for emoji selection
            user_in_distress: Whether user is in emotional distress
        
        Returns:
            Tuple of (emoji, context) or None to fall through
        """
        # Extract trajectory data
        trajectory = emotional_state.get("emotional_trajectory", "stable")
        primary_emotion = emotional_state.get("current_emotion", "neutral")
        intensity = emotional_state.get("intensity", 0.5)
        confidence = emotional_state.get("confidence", 0.5)
        
        # Only use trajectory logic for high confidence emotions (>0.65)
        if confidence < 0.65:
            logger.debug(
                "🎯 Trajectory skip: Low confidence (%.2f) - falling through",
                confidence
            )
            return None
        
        character_emojis = self.character_emoji_sets.get(bot_character, self.character_emoji_sets["general"])
        
        # SKIP celebratory trajectory responses if user in distress
        if user_in_distress:
            logger.debug("🎯 Trajectory skip: User in distress - being conservative")
            return None
        
        # TRAJECTORY 1: Rising positive emotions → Enthusiastic response
        if trajectory == "rising" and primary_emotion in ['joy', 'excitement', 'hope', 'contentment'] and intensity > 0.6:
            logger.info(
                "🎯 Trajectory match: Rising %s (intensity=%.2f) → enthusiastic",
                primary_emotion, intensity
            )
            return character_emojis["wonder"][0], EmojiResponseContext.EMOTIONAL_OVERWHELM
        
        # TRAJECTORY 2: Stable positive emotions → Warm acknowledgment
        if trajectory == "stable" and primary_emotion in ['joy', 'contentment', 'gratitude'] and intensity > 0.5:
            logger.info(
                "🎯 Trajectory match: Stable %s (intensity=%.2f) → warm",
                primary_emotion, intensity
            )
            return character_emojis["positive"][0], EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        
        # TRAJECTORY 3: Rising negative emotions → DO NOT USE celebratory
        # Just fall through - let other logic handle it
        if trajectory == "rising" and primary_emotion in ['sadness', 'anger', 'fear', 'anxiety']:
            logger.debug(
                "🎯 Trajectory skip: Rising negative %s - avoiding celebratory",
                primary_emotion
            )
            return None
        
        # TRAJECTORY 4: Falling negative emotions (improving) → Supportive encouragement
        if trajectory == "falling" and primary_emotion in ['sadness', 'fear', 'anxiety'] and intensity < 0.7:
            logger.info(
                "🎯 Trajectory match: Falling %s (improving) → emotion-aware empathy",
                primary_emotion
            )
            # Use emotion-aware empathy selection for improving negative emotions
            empathy_emoji = self._select_emotion_aware_empathy_emoji(
                emotional_state=emotional_state,
                bot_character=bot_character
            )
            return empathy_emoji, EmojiResponseContext.EMOTIONAL_OVERWHELM
        
        # TRAJECTORY 5: Excitement-based emotions → Playful response
        if primary_emotion in ['excitement', 'surprise'] and intensity > 0.7 and confidence > 0.7:
            logger.info(
                "🎯 Trajectory match: High %s (intensity=%.2f, confidence=%.2f) → playful",
                primary_emotion, intensity, confidence
            )
            return character_emojis["playful"][0], EmojiResponseContext.PLAYFUL_INTERACTION
        
        # No trajectory-based match, fall through to other logic
        logger.debug(
            "🎯 Trajectory fall-through: emotion=%s, trajectory=%s, intensity=%.2f",
            primary_emotion, trajectory, intensity
        )
        return None
    
    async def _select_enhanced_optimal_emoji(
        self,
        user_id: str,
        user_message: str, 
        bot_character: str,
        conversation_patterns: ConversationPattern,
        emotional_state: Dict[str, Any],
        personality_context: Dict[str, Any],
        communication_style: Dict[str, Any]
    ) -> Tuple[str, EmojiResponseContext]:
        """Enhanced emoji selection with comprehensive context and emotion mirroring"""
        
        # CRITICAL: Check for user emotional distress FIRST
        # Prevent celebration/excitement emojis when user is sad/anxious/angry
        user_in_distress = False
        current_emotion = emotional_state.get("current_emotion", "neutral")
        emotional_intensity = emotional_state.get("intensity", 0.0)
        emotional_confidence = emotional_state.get("confidence", 0.0)
        
        # 🎭 PRIORITY 0: EMOTION MIRRORING (highest priority when conditions are met)
        # Mirror user's emotion if detected with high confidence AND high intensity
        # ⚠️ CRITICAL FIX: Do NOT mirror distress emotions (sadness, fear, anger) - use support instead
        if emotional_confidence > 0.7 and emotional_intensity > 0.6:
            # Skip mirroring for distress emotions - it's tone-deaf to add 😢 to a sad message
            if current_emotion not in ["sadness", "fear", "anger"]:
                mirroring_emoji = self._get_emotion_mirroring_emoji(current_emotion, emotional_intensity)
                if mirroring_emoji:
                    logger.info(
                        "🎭 Emotion mirroring activated: emotion=%s, intensity=%.2f, confidence=%.2f, emoji=%s",
                        current_emotion, emotional_intensity, emotional_confidence, mirroring_emoji
                    )
                    return mirroring_emoji, EmojiResponseContext.EMOTIONAL_OVERWHELM
            else:
                logger.info(
                    "🎭 Emotion mirroring SKIPPED for distress emotion: emotion=%s (would be inappropriate for reaction)",
                    current_emotion
                )
        
        if current_emotion in ["sadness", "fear", "anger"] and emotional_intensity > 0.6:
            user_in_distress = True
            logger.debug(
                "⚠️ User in emotional distress: %s (intensity: %.2f) - filtering celebratory emojis",
                current_emotion, emotional_intensity
            )
        
        # Priority 1: User's historical preferences (if established relationship)
        if conversation_patterns.preferred_emojis and len(conversation_patterns.similar_conversations) > 10:
            preferred_emoji = conversation_patterns.preferred_emojis[0][0]
            # 🎨 PRIORITY 5: Use personalized character emoji sets
            character_emojis_list = await self._get_personalized_character_emojis(
                user_id=user_id,
                bot_character=bot_character,
                emotion_category="positive"  # Get positive emojis for fallback
            )
            all_character_emojis = character_emojis_list
            
            # Filter out inappropriate emojis if user in distress
            if user_in_distress and self._is_celebratory_emoji(preferred_emoji):
                logger.debug("Filtered preferred emoji %s due to user distress", preferred_emoji)
            elif preferred_emoji in all_character_emojis:
                return preferred_emoji, EmojiResponseContext.REPEATED_PATTERN
        
        # Priority 2: Emotional support needs OR user in distress
        if emotional_state.get("needs_emotional_support", False) or user_in_distress:
            # Use emotion-aware empathy emoji selection
            empathy_emoji = self._select_emotion_aware_empathy_emoji(
                emotional_state=emotional_state,
                bot_character=bot_character
            )
            return empathy_emoji, EmojiResponseContext.EMOTIONAL_OVERWHELM
        
        # Priority 3: High emotional intensity - use universal taxonomy
        if emotional_state.get("intensity", 0.5) > 0.7:
            current_emotion = emotional_state.get("current_emotion", "neutral")
            
            # FILTER: Don't use celebratory emojis if user is in distress
            if user_in_distress:
                # For distress, use emotion-aware empathy emoji
                empathy_emoji = self._select_emotion_aware_empathy_emoji(
                    emotional_state=emotional_state,
                    bot_character=bot_character
                )
                return empathy_emoji, EmojiResponseContext.EMOTIONAL_OVERWHELM
            
            # Import universal taxonomy for character-aware emoji selection
            from src.intelligence.emotion_taxonomy import get_emoji_for_roberta_emotion
            
            taxonomy_emoji = get_emoji_for_roberta_emotion(
                current_emotion, 
                character=bot_character, 
                confidence=emotional_state.get("intensity", 0.5)
            )
            
            # Filter celebratory taxonomy emoji if it exists
            if taxonomy_emoji and not self._is_celebratory_emoji(taxonomy_emoji):
                return taxonomy_emoji, EmojiResponseContext.EMOTIONAL_OVERWHELM
            
            # 🎨 PRIORITY 5: Use personalized character emojis for fallback
            if current_emotion in ["joy", "excitement", "wonder"]:
                personalized_emojis = await self._get_personalized_character_emojis(
                    user_id=user_id, bot_character=bot_character, emotion_category="wonder"
                )
                return personalized_emojis[0] if personalized_emojis else "✨", EmojiResponseContext.EMOTIONAL_OVERWHELM
            elif current_emotion in ["gratitude"]:
                personalized_emojis = await self._get_personalized_character_emojis(
                    user_id=user_id, bot_character=bot_character, emotion_category="acknowledgment"
                )
                return personalized_emojis[0] if personalized_emojis else "🙏", EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        
        # Priority 4: Trajectory-aware context selection (replaces keyword matching)
        # Use emotional trajectory data instead of hard-coded keywords
        trajectory_emoji = self._select_trajectory_aware_emoji(
            emotional_state=emotional_state,
            bot_character=bot_character,
            user_in_distress=user_in_distress
        )
        if trajectory_emoji:
            emoji, context = trajectory_emoji
            return emoji, context
        
        # Priority 5: Fallback keyword detection for gratitude (works in all contexts)
        message_lower = user_message.lower()
        if any(word in message_lower for word in ["thanks", "thank you", "appreciate", "grateful"]):
            # Use emotion-aware empathy emoji for acknowledgment
            empathy_emoji = self._select_emotion_aware_empathy_emoji(
                emotional_state=emotional_state,
                bot_character=bot_character
            )
            return empathy_emoji, EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        
        # If user in distress, DON'T use character-specific emojis
        # Better to skip than to use potentially inappropriate ones
        if user_in_distress:
            # Already handled empathy emojis above - if we get here, use emotion-aware selection
            logger.debug("Using emotion-aware empathy for distressed user - safe fallback")
            empathy_emoji = self._select_emotion_aware_empathy_emoji(
                emotional_state=emotional_state,
                bot_character=bot_character
            )
            return empathy_emoji, EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        
        # 🎨 PRIORITY 5: Use personalized character emojis for character-specific contexts
        # Technical appreciation for technical characters (NOT in distress)
        if bot_character == "technical" and any(word in message_lower for word in ["code", "algorithm", "system", "data", "tech"]):
            personalized_emojis = await self._get_personalized_character_emojis(
                user_id=user_id, bot_character=bot_character, emotion_category="positive"
            )
            return personalized_emojis[0] if personalized_emojis else "💡", EmojiResponseContext.TECHNICAL_APPRECIATION
        
        # Mystical wonder for mystical characters (NOT in distress)
        if bot_character == "mystical" and any(word in message_lower for word in ["magic", "energy", "spiritual", "mystical", "dream"]):
            personalized_emojis = await self._get_personalized_character_emojis(
                user_id=user_id, bot_character=bot_character, emotion_category="wonder"
            )
            return personalized_emojis[0] if personalized_emojis else "🔮", EmojiResponseContext.MYSTICAL_WONDER
        
        # Default based on communication style preference (NOT in distress)
        if communication_style.get("prefers_brief_responses", False):
            personalized_emojis = await self._get_personalized_character_emojis(
                user_id=user_id, bot_character=bot_character, emotion_category="acknowledgment"
            )
            return personalized_emojis[0] if personalized_emojis else "👍", EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT
        else:
            personalized_emojis = await self._get_personalized_character_emojis(
                user_id=user_id, bot_character=bot_character, emotion_category="positive"
            )
            return personalized_emojis[0] if personalized_emojis else "😊", EmojiResponseContext.SIMPLE_ACKNOWLEDGMENT

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
            message_emotions = await self._analyze_message_emotions(user_id, user_message)
            
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
    
    def _get_emotion_mirroring_emoji(self, emotion: str, intensity: float) -> Optional[str]:
        """
        🎭 EMOTION MIRRORING: Select emoji that mirrors user's detected emotion.
        
        Returns emoji that reflects the user's emotional state back to them,
        providing empathetic acknowledgment and emotional validation.
        
        Args:
            emotion: Primary emotion detected (sadness, joy, fear, anger, etc.)
            intensity: Emotion intensity (0.0-1.0)
            
        Returns:
            Mirroring emoji if appropriate, None otherwise
        """
        # Emotion → Mirroring Emoji Map (intensity-aware)
        EMOTION_MIRROR_MAP = {
            'sadness': {
                'high': '😢',      # Crying face for intense sadness
                'medium': '😔',    # Pensive face for moderate sadness
                'low': '🙁'        # Slightly frowning for mild sadness
            },
            'joy': {
                'high': '😄',      # Beaming smile for intense joy
                'medium': '😊',    # Smiling face for moderate joy
                'low': '🙂'        # Slightly smiling for mild joy
            },
            'fear': {
                'high': '😰',      # Anxious face for intense fear
                'medium': '😟',    # Worried face for moderate fear
                'low': '😕'        # Confused face for mild fear
            },
            'anger': {
                'high': '😤',      # Face with steam for intense anger
                'medium': '😠',    # Angry face for moderate anger
                'low': '😒'        # Unamused face for mild anger
            },
            'surprise': {
                'high': '😲',      # Astonished face for intense surprise
                'medium': '😮',    # Open mouth for moderate surprise
                'low': '😯'        # Hushed face for mild surprise
            },
            'disgust': {
                'high': '🤢',      # Nauseated face for intense disgust
                'medium': '😖',    # Confounded face for moderate disgust
                'low': '😑'        # Expressionless for mild disgust
            },
            'neutral': None,    # Don't mirror neutral emotions
        }
        
        # Map intensity to category
        if intensity > 0.8:
            intensity_level = 'high'
        elif intensity > 0.6:
            intensity_level = 'medium'
        else:
            intensity_level = 'low'
        
        # Get mirroring emoji for this emotion
        emotion_map = EMOTION_MIRROR_MAP.get(emotion)
        if emotion_map and isinstance(emotion_map, dict):
            return emotion_map.get(intensity_level)
        
        return None
    
    def _select_optimal_emoji(
        self, 
        user_message: str, 
        bot_character: str,
        conversation_patterns: ConversationPattern,
        emotion_score: float,
        user_emotion_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, EmojiResponseContext]:
        """
        Select the best emoji based on context and character.
        
        NEW: Supports emotionally intelligent mirroring when user emotion is detected
        with high confidence and intensity.
        """
        message_lower = user_message.lower()
        
        # Get character-specific emoji set
        character_emojis = self.character_emoji_sets.get(bot_character, self.character_emoji_sets["general"])
        
        # 🎯 EMOTION MIRRORING: Mirror user's emotion if detected with high confidence
        if user_emotion_data:
            user_emotion = user_emotion_data.get('primary_emotion')
            user_intensity = user_emotion_data.get('intensity', 0)
            user_confidence = user_emotion_data.get('confidence', 0)
            
            # Only mirror if BOTH confidence and intensity are high (emotionally intelligent)
            if user_confidence > 0.7 and user_intensity > 0.6:
                mirroring_emoji = self._get_emotion_mirroring_emoji(user_emotion, user_intensity)
                if mirroring_emoji:
                    logger.info(
                        "🎭 Emotion mirroring: user_emotion=%s, intensity=%.2f, confidence=%.2f, emoji=%s",
                        user_emotion, user_intensity, user_confidence, mirroring_emoji
                    )
                    return mirroring_emoji, EmojiResponseContext.EMOTIONAL_OVERWHELM
        
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
    
    def __init__(self, memory_manager: MemoryManagerProtocol, cdl_database_manager=None):
        self.vector_emoji_intelligence = VectorEmojiIntelligence(
            memory_manager, 
            cdl_database_manager=cdl_database_manager
        )
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