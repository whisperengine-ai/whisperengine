"""
Emoji Reaction Intelligence System
=================================

Captures and analyzes emoji reactions to bot messages for multimodal emotional intelligence.
Provides real-time emotional feedback, pattern recognition, and memory enrichment.
"""

import logging
import discord
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EmotionalReactionType(Enum):
    """Categories of emotional reactions from emoji feedback."""
    POSITIVE_STRONG = "positive_strong"      # 😍, ❤️, 🥰, 🤩
    POSITIVE_MILD = "positive_mild"          # 😊, 👍, ✨, 🙂
    NEUTRAL_THOUGHTFUL = "neutral_thoughtful" # 🤔, 🧐, 💭, 🤨
    NEGATIVE_MILD = "negative_mild"          # 😕, 👎, 😬, 🤷
    NEGATIVE_STRONG = "negative_strong"      # 😠, 😡, 💔, 😤
    SADNESS = "sadness"                      # 😢, 😭, 😔, 😞 - Added for better emotion taxonomy alignment
    SURPRISE = "surprise"                    # 😲, 🤯, 😱, 🎉
    CONFUSION = "confusion"                  # 😵, 🤪, 🙃, ❓
    MYSTICAL_WONDER = "mystical_wonder"      # 🔮, ✨, 🌟, 🪄
    TECHNICAL_APPRECIATION = "tech_appreciation" # 🤖, 💻, ⚡, 🔧


@dataclass
class EmojiReactionData:
    """Data structure for emoji reaction analysis."""
    emoji: str
    user_id: str
    message_id: str
    bot_message_content: str
    reaction_type: EmotionalReactionType
    confidence_score: float
    timestamp: datetime
    character_context: Optional[str] = None
    conversation_context: Optional[str] = None


class EmojiEmotionMapper:
    """Maps emojis to emotional reaction types with confidence scoring."""
    
    # Comprehensive emoji mapping with confidence scores
    EMOJI_EMOTION_MAP = {
        # Strong Positive
        "❤️": (EmotionalReactionType.POSITIVE_STRONG, 0.95),
        "♥️": (EmotionalReactionType.POSITIVE_STRONG, 0.95),  # Heart suit variant
        "😍": (EmotionalReactionType.POSITIVE_STRONG, 0.95),
        "🥰": (EmotionalReactionType.POSITIVE_STRONG, 0.90),
        "🤩": (EmotionalReactionType.POSITIVE_STRONG, 0.90),
        "💖": (EmotionalReactionType.POSITIVE_STRONG, 0.88),
        "💕": (EmotionalReactionType.POSITIVE_STRONG, 0.85),
        "💗": (EmotionalReactionType.POSITIVE_STRONG, 0.83),  # Growing heart
        "💘": (EmotionalReactionType.POSITIVE_STRONG, 0.80),  # Heart with arrow
        "💙": (EmotionalReactionType.POSITIVE_MILD, 0.75),    # Blue heart
        "💚": (EmotionalReactionType.POSITIVE_MILD, 0.75),    # Green heart
        "💛": (EmotionalReactionType.POSITIVE_MILD, 0.75),    # Yellow heart
        "💜": (EmotionalReactionType.POSITIVE_MILD, 0.75),    # Purple heart
        
        # Mild Positive
        "😊": (EmotionalReactionType.POSITIVE_MILD, 0.80),
        "😁": (EmotionalReactionType.POSITIVE_MILD, 0.80),
        "😄": (EmotionalReactionType.POSITIVE_MILD, 0.75),
        "👍": (EmotionalReactionType.POSITIVE_MILD, 0.75),
        "🙂": (EmotionalReactionType.POSITIVE_MILD, 0.70),
        "✨": (EmotionalReactionType.POSITIVE_MILD, 0.70),
        "👏": (EmotionalReactionType.POSITIVE_MILD, 0.75),
        
        # Neutral/Thoughtful
        "🤔": (EmotionalReactionType.NEUTRAL_THOUGHTFUL, 0.85),
        "🧐": (EmotionalReactionType.NEUTRAL_THOUGHTFUL, 0.80),
        "💭": (EmotionalReactionType.NEUTRAL_THOUGHTFUL, 0.75),
        "🤨": (EmotionalReactionType.NEUTRAL_THOUGHTFUL, 0.70),
        "🙄": (EmotionalReactionType.NEUTRAL_THOUGHTFUL, 0.60),
        "😐": (EmotionalReactionType.NEUTRAL_THOUGHTFUL, 0.80),
        "😑": (EmotionalReactionType.NEUTRAL_THOUGHTFUL, 0.75),
        "😶": (EmotionalReactionType.NEUTRAL_THOUGHTFUL, 0.70),
        
        # Mild Negative
        "😕": (EmotionalReactionType.NEGATIVE_MILD, 0.75),
        "😬": (EmotionalReactionType.NEGATIVE_MILD, 0.70),
        "🤷": (EmotionalReactionType.NEGATIVE_MILD, 0.65),
        "👎": (EmotionalReactionType.NEGATIVE_MILD, 0.80),
        
        # Strong Negative (Anger, frustration)
        "😠": (EmotionalReactionType.NEGATIVE_STRONG, 0.90),
        "😡": (EmotionalReactionType.NEGATIVE_STRONG, 0.95),
        "😤": (EmotionalReactionType.NEGATIVE_STRONG, 0.80),
        "😒": (EmotionalReactionType.NEGATIVE_STRONG, 0.70),
        
        # Sadness (Added via Unicode to avoid encoding issues)
        "😿": (EmotionalReactionType.SADNESS, 0.80),
        
        # Surprise
        "😲": (EmotionalReactionType.SURPRISE, 0.85),
        "🤯": (EmotionalReactionType.SURPRISE, 0.90),
        "😱": (EmotionalReactionType.SURPRISE, 0.80),
        "🎉": (EmotionalReactionType.SURPRISE, 0.75),
        "🔥": (EmotionalReactionType.SURPRISE, 0.70),
        
        # Confusion
        "😵": (EmotionalReactionType.CONFUSION, 0.85),
        "🤪": (EmotionalReactionType.CONFUSION, 0.75),
        "🙃": (EmotionalReactionType.CONFUSION, 0.70),
        "❓": (EmotionalReactionType.CONFUSION, 0.80),
        "❔": (EmotionalReactionType.CONFUSION, 0.75),
        
        # Mystical Wonder (for Dream/Elena)
        "🔮": (EmotionalReactionType.MYSTICAL_WONDER, 0.95),
        "🌟": (EmotionalReactionType.MYSTICAL_WONDER, 0.85),
        "🪄": (EmotionalReactionType.MYSTICAL_WONDER, 0.90),
        "⭐": (EmotionalReactionType.MYSTICAL_WONDER, 0.80),
        "🌙": (EmotionalReactionType.MYSTICAL_WONDER, 0.85),
        
        # Technical Appreciation (for Marcus bots)
        "🤖": (EmotionalReactionType.TECHNICAL_APPRECIATION, 0.90),
        "💻": (EmotionalReactionType.TECHNICAL_APPRECIATION, 0.85),
        "⚡": (EmotionalReactionType.TECHNICAL_APPRECIATION, 0.80),
        "🔧": (EmotionalReactionType.TECHNICAL_APPRECIATION, 0.80),
        "🚀": (EmotionalReactionType.TECHNICAL_APPRECIATION, 0.85),
        "💡": (EmotionalReactionType.TECHNICAL_APPRECIATION, 0.75),
    }
    
    @classmethod
    def _initialize_unicode_emojis(cls):
        """Add problematic emojis using Unicode code points to avoid encoding issues."""
        if not hasattr(cls, '_unicode_initialized'):
            # Add sadness emojis using Unicode code points
            cls.EMOJI_EMOTION_MAP[chr(0x1F622)] = (EmotionalReactionType.SADNESS, 0.90)  # 😢
            cls.EMOJI_EMOTION_MAP[chr(0x1F62D)] = (EmotionalReactionType.SADNESS, 0.95)  # 😭
            cls.EMOJI_EMOTION_MAP[chr(0x1F614)] = (EmotionalReactionType.SADNESS, 0.85)  # 😔
            cls.EMOJI_EMOTION_MAP[chr(0x1F61E)] = (EmotionalReactionType.SADNESS, 0.75)  # 😞
            cls.EMOJI_EMOTION_MAP[chr(0x1F494)] = (EmotionalReactionType.SADNESS, 0.85)  # 💔
            cls._unicode_initialized = True
    
    @classmethod
    def map_emoji_to_emotion(cls, emoji: str) -> tuple[EmotionalReactionType, float]:
        """
        Map emoji to emotional reaction type with confidence score.
        
        Args:
            emoji: Unicode emoji string
            
        Returns:
            Tuple of (reaction_type, confidence_score)
        """
        # Initialize Unicode emojis if not done yet
        cls._initialize_unicode_emojis()
        
        # Direct mapping
        if emoji in cls.EMOJI_EMOTION_MAP:
            return cls.EMOJI_EMOTION_MAP[emoji]
        
        # Handle custom Discord emojis (fall back to neutral)
        if emoji.startswith('<:') or emoji.startswith('<a:'):
            logger.debug(f"Custom Discord emoji detected: {emoji}")
            return EmotionalReactionType.NEUTRAL_THOUGHTFUL, 0.30
        
        # Unknown emoji fallback
        logger.debug(f"Unknown emoji for emotion mapping: {emoji}")
        return EmotionalReactionType.NEUTRAL_THOUGHTFUL, 0.20


class EmojiReactionIntelligence:
    """
    Main system for capturing and analyzing emoji reactions for emotional intelligence.
    """
    
    def __init__(self, memory_manager=None, emotion_manager=None):
        """Initialize emoji reaction intelligence system."""
        self.memory_manager = memory_manager
        self.emotion_manager = emotion_manager
        self.reaction_history: Dict[str, List[EmojiReactionData]] = {}
        
        logger.info("🎭 Emoji Reaction Intelligence initialized")
    
    async def process_reaction_add(
        self, 
        reaction: discord.Reaction, 
        user: discord.User,
        bot_user_id: str
    ) -> Optional[EmojiReactionData]:
        """
        Process when a user adds a reaction to a bot message.
        
        Args:
            reaction: Discord reaction object
            user: User who added the reaction
            bot_user_id: ID of the bot user
            
        Returns:
            EmojiReactionData if successfully processed, None otherwise
        """
        # Only process reactions on bot messages
        if str(reaction.message.author.id) != bot_user_id:
            return None
        
        # Skip if bot added the reaction
        if user.bot:
            return None
        
        try:
            emoji_str = str(reaction.emoji)
            user_id = str(user.id)
            message_id = str(reaction.message.id)
            bot_message_content = reaction.message.content
            
            # Map emoji to emotional reaction
            reaction_type, confidence = EmojiEmotionMapper.map_emoji_to_emotion(emoji_str)
            
            # Create reaction data
            reaction_data = EmojiReactionData(
                emoji=emoji_str,
                user_id=user_id,
                message_id=message_id,
                bot_message_content=bot_message_content,
                reaction_type=reaction_type,
                confidence_score=confidence,
                timestamp=datetime.utcnow(),
                character_context=self._determine_character_context(bot_message_content),
                conversation_context=self._extract_conversation_context(bot_message_content)
            )
            
            logger.info(f"🎭 Emoji reaction processed: {emoji_str} → {reaction_type.value} (confidence: {confidence:.2f}) from user {user_id}")
            
            # Store in memory system
            await self._store_reaction_in_memory(reaction_data)
            
            # Update reaction history
            if user_id not in self.reaction_history:
                self.reaction_history[user_id] = []
            self.reaction_history[user_id].append(reaction_data)
            
            # Keep only recent reactions (last 50 per user)
            if len(self.reaction_history[user_id]) > 50:
                self.reaction_history[user_id] = self.reaction_history[user_id][-50:]
            
            return reaction_data
            
        except Exception as e:
            logger.error(f"Error processing emoji reaction: {e}")
            return None
    
    async def _store_reaction_in_memory(self, reaction_data: EmojiReactionData):
        """Store emoji reaction in the memory system as emotional feedback."""
        if not self.memory_manager:
            logger.debug("No memory manager available for storing emoji reactions")
            return
        
        try:
            # Map reaction to standardized emotion using universal taxonomy
            from src.intelligence.emotion_taxonomy import map_reaction_to_emotion
            
            standardized_emotion = map_reaction_to_emotion(reaction_data.reaction_type.value)
            
            # Create memory content for the reaction
            memory_content = f"User emotional reaction: {reaction_data.emoji} ({reaction_data.reaction_type.value}) to bot message about '{reaction_data.conversation_context}'"
            
            # Store as a special type of conversation memory with standardized emotion
            await self.memory_manager.store_conversation(
                user_id=reaction_data.user_id,
                user_message=f"[EMOJI_REACTION] {reaction_data.emoji}",
                bot_response=f"[EMOTIONAL_FEEDBACK] {standardized_emotion} (confidence: {reaction_data.confidence_score:.2f})",
                metadata={
                    "interaction_type": "emoji_reaction",
                    "emotion_type": reaction_data.reaction_type.value,  # Keep original for debugging
                    "standardized_emotion": standardized_emotion,  # Add standardized version
                    "confidence_score": reaction_data.confidence_score,
                    "original_bot_message": reaction_data.bot_message_content[:200],
                    "character_context": reaction_data.character_context,
                    "reaction_timestamp": reaction_data.timestamp.isoformat()
                }
            )
            
            logger.debug(f"🎭 Stored emoji reaction in memory: {reaction_data.emoji} → {standardized_emotion}")
            
        except Exception as e:
            logger.error(f"Error storing emoji reaction in memory: {e}")
    
    def _determine_character_context(self, bot_message: str) -> str:
        """Determine character context from bot message content."""
        # Simple character detection based on message content
        content_lower = bot_message.lower()
        
        if any(word in content_lower for word in ['ocean', 'marine', 'sea', 'whale', 'coral']):
            return "elena"
        elif any(word in content_lower for word in ['ai', 'algorithm', 'code', 'neural', 'computing']):
            return "marcus"
        elif any(word in content_lower for word in ['dream', 'realm', 'endless', 'morpheus', 'nightmare']):
            return "dream"
        else:
            return "general"
    
    def _extract_conversation_context(self, bot_message: str) -> str:
        """Extract conversation context from bot message."""
        # Return first 50 words as context
        words = bot_message.split()[:50]
        return ' '.join(words)
    
    def get_user_emotional_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get user's emotional reaction patterns."""
        if user_id not in self.reaction_history:
            return {"total_reactions": 0, "patterns": {}, "insights": "No reaction history"}
        
        reactions = self.reaction_history[user_id]
        total = len(reactions)
        
        # Count reactions by type
        patterns = {}
        for reaction in reactions:
            reaction_type = reaction.reaction_type.value
            patterns[reaction_type] = patterns.get(reaction_type, 0) + 1
        
        # Generate insights
        if total > 0:
            most_common = max(patterns.items(), key=lambda x: x[1])
            insights = f"Most common reaction: {most_common[0]} ({most_common[1]}/{total} times)"
        else:
            insights = "No patterns yet"
        
        return {
            "total_reactions": total,
            "patterns": patterns,
            "insights": insights,
            "recent_reactions": [r.emoji for r in reactions[-5:]]  # Last 5 emojis
        }
    
    async def get_emotional_context_for_response(self, user_id: str) -> Dict[str, Any]:
        """Get emotional context to influence bot response."""
        if user_id not in self.reaction_history:
            return {"emotional_state": "neutral", "confidence": 0.0}
        
        # Get recent reactions (last 10)
        recent_reactions = self.reaction_history[user_id][-10:]
        
        if not recent_reactions:
            return {"emotional_state": "neutral", "confidence": 0.0}
        
        # Calculate weighted emotional state
        emotion_scores = {}
        total_weight = 0
        
        for reaction in recent_reactions:
            # Map to standardized emotion
            from src.intelligence.emotion_taxonomy import map_reaction_to_emotion
            standardized = map_reaction_to_emotion(reaction.reaction_type.value)
            
            weight = reaction.confidence_score
            emotion_scores[standardized] = emotion_scores.get(standardized, 0) + weight
            total_weight += weight
        
        if total_weight > 0:
            # Normalize scores
            for emotion in emotion_scores:
                emotion_scores[emotion] /= total_weight
            
            # Get dominant emotion
            dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            
            return {
                "emotional_state": dominant_emotion[0],
                "confidence": dominant_emotion[1],
                "all_emotions": emotion_scores,
                "recent_emoji_count": len(recent_reactions)
            }
        
        return {"emotional_state": "neutral", "confidence": 0.0}