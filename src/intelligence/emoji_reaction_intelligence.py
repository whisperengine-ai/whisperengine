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
        "😍": (EmotionalReactionType.POSITIVE_STRONG, 0.95),
        "🥰": (EmotionalReactionType.POSITIVE_STRONG, 0.90),
        "🤩": (EmotionalReactionType.POSITIVE_STRONG, 0.90),
        "💖": (EmotionalReactionType.POSITIVE_STRONG, 0.88),
        "💕": (EmotionalReactionType.POSITIVE_STRONG, 0.85),
        
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
        
        # Mild Negative
        "😕": (EmotionalReactionType.NEGATIVE_MILD, 0.75),
        "😬": (EmotionalReactionType.NEGATIVE_MILD, 0.70),
        "🤷": (EmotionalReactionType.NEGATIVE_MILD, 0.65),
        "👎": (EmotionalReactionType.NEGATIVE_MILD, 0.80),
        "😐": (EmotionalReactionType.NEGATIVE_MILD, 0.60),
        
        # Strong Negative
        "😠": (EmotionalReactionType.NEGATIVE_STRONG, 0.90),
        "😡": (EmotionalReactionType.NEGATIVE_STRONG, 0.95),
        "💔": (EmotionalReactionType.NEGATIVE_STRONG, 0.85),
        "😤": (EmotionalReactionType.NEGATIVE_STRONG, 0.80),
        "😒": (EmotionalReactionType.NEGATIVE_STRONG, 0.70),
        
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
    def map_emoji_to_emotion(cls, emoji: str) -> tuple[EmotionalReactionType, float]:
        """
        Map emoji to emotional reaction type with confidence score.
        
        Args:
            emoji: Unicode emoji string
            
        Returns:
            Tuple of (reaction_type, confidence_score)
        """
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
        logger.info("🎭 Emoji Reaction Intelligence System initialized")
    
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
            # Create memory content for the reaction
            memory_content = f"User emotional reaction: {reaction_data.emoji} ({reaction_data.reaction_type.value}) to bot message about '{reaction_data.conversation_context}'"
            
            # Store as a special type of conversation memory
            await self.memory_manager.store_conversation(
                user_id=reaction_data.user_id,
                user_message=f"[EMOJI_REACTION] {reaction_data.emoji}",
                bot_response=f"[EMOTIONAL_FEEDBACK] {reaction_data.reaction_type.value} (confidence: {reaction_data.confidence_score:.2f})",
                metadata={
                    "interaction_type": "emoji_reaction",
                    "emotion_type": reaction_data.reaction_type.value,
                    "confidence_score": reaction_data.confidence_score,
                    "original_bot_message": reaction_data.bot_message_content[:200],
                    "character_context": reaction_data.character_context,
                    "reaction_timestamp": reaction_data.timestamp.isoformat()
                }
            )
            
            logger.debug(f"✅ Stored emoji reaction in memory: {reaction_data.emoji} → {reaction_data.reaction_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to store emoji reaction in memory: {e}")
    
    def _determine_character_context(self, bot_message_content: str) -> Optional[str]:
        """Determine which character context based on message content."""
        content_lower = bot_message_content.lower()
        
        # Mystical language patterns (Dream/Elena)
        mystical_patterns = ["behold", "thy", "doth", "ethereal", "cosmic", "threads of", "whisper"]
        if any(pattern in content_lower for pattern in mystical_patterns):
            return "mystical_character"
        
        # Technical patterns (Marcus bots)
        tech_patterns = ["algorithm", "code", "system", "technology", "programming", "database"]
        if any(pattern in content_lower for pattern in tech_patterns):
            return "technical_character"
        
        # Marine biology patterns (Elena)
        marine_patterns = ["ocean", "whale", "marine", "sea", "coral", "dolphins"]
        if any(pattern in content_lower for pattern in marine_patterns):
            return "marine_biologist"
        
        return "general"
    
    def _extract_conversation_context(self, bot_message_content: str) -> str:
        """Extract key context from bot message for memory storage."""
        # Take first sentence or first 100 characters, whichever is shorter
        first_sentence = bot_message_content.split('.')[0]
        if len(first_sentence) <= 100:
            return first_sentence.strip()
        return bot_message_content[:100].strip() + "..."
    
    def get_user_emotional_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze emotional patterns for a user based on their reaction history.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Dictionary of emotional patterns and insights
        """
        if user_id not in self.reaction_history:
            return {"patterns": {}, "insights": "No reaction history available"}
        
        reactions = self.reaction_history[user_id]
        
        # Count reaction types
        reaction_counts = {}
        total_reactions = len(reactions)
        
        for reaction in reactions:
            reaction_type = reaction.reaction_type.value
            reaction_counts[reaction_type] = reaction_counts.get(reaction_type, 0) + 1
        
        # Calculate percentages
        reaction_percentages = {
            reaction_type: (count / total_reactions) * 100
            for reaction_type, count in reaction_counts.items()
        }
        
        # Determine dominant emotional pattern
        dominant_emotion = max(reaction_percentages.items(), key=lambda x: x[1]) if reaction_percentages else None
        
        # Generate insights
        insights = []
        if dominant_emotion:
            insights.append(f"Primarily reacts with {dominant_emotion[0]} ({dominant_emotion[1]:.1f}%)")
        
        if reaction_percentages.get("positive_strong", 0) > 30:
            insights.append("Shows strong positive engagement")
        elif reaction_percentages.get("negative_strong", 0) > 20:
            insights.append("Shows some negative reactions - may need response adjustment")
        
        if reaction_percentages.get("mystical_wonder", 0) > 15:
            insights.append("Appreciates mystical/spiritual content")
        
        if reaction_percentages.get("tech_appreciation", 0) > 15:
            insights.append("Engaged with technical content")
        
        return {
            "total_reactions": total_reactions,
            "reaction_percentages": reaction_percentages,
            "dominant_emotion": dominant_emotion[0] if dominant_emotion else None,
            "insights": " | ".join(insights) if insights else "Mixed emotional patterns"
        }
    
    async def get_emotional_context_for_response(self, user_id: str) -> Dict[str, Any]:
        """
        Get emotional context from recent reactions to inform response generation.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Emotional context for response generation
        """
        if user_id not in self.reaction_history:
            return {"emotional_context": "neutral", "confidence": 0.0}
        
        # Get recent reactions (last 10)
        recent_reactions = self.reaction_history[user_id][-10:]
        
        if not recent_reactions:
            return {"emotional_context": "neutral", "confidence": 0.0}
        
        # Weight recent reactions more heavily
        weighted_scores = {}
        total_weight = 0
        
        for i, reaction in enumerate(recent_reactions):
            # More recent reactions get higher weight
            weight = (i + 1) * reaction.confidence_score
            emotion_type = reaction.reaction_type.value
            
            if emotion_type not in weighted_scores:
                weighted_scores[emotion_type] = 0
            weighted_scores[emotion_type] += weight
            total_weight += weight
        
        if total_weight == 0:
            return {"emotional_context": "neutral", "confidence": 0.0}
        
        # Normalize scores
        normalized_scores = {
            emotion: score / total_weight
            for emotion, score in weighted_scores.items()
        }
        
        # Get dominant emotion
        dominant_emotion = max(normalized_scores.items(), key=lambda x: x[1])
        
        return {
            "emotional_context": dominant_emotion[0],
            "confidence": dominant_emotion[1],
            "recent_patterns": normalized_scores,
            "sample_size": len(recent_reactions)
        }