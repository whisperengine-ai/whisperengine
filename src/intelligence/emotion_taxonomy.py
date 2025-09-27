"""
Universal Emotion Taxonomy for WhisperEngine
==============================================

Provides a single source of truth for emotion mapping across all systems.
Surgical approach: Maps between existing taxonomies without breaking current code.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CoreEmotion(Enum):
    """
    7 core emotions from RoBERTa model - our canonical standard.
    All other emotion systems map to these.
    """
    ANGER = "anger"
    DISGUST = "disgust" 
    FEAR = "fear"
    JOY = "joy"
    NEUTRAL = "neutral"
    SADNESS = "sadness"
    SURPRISE = "surprise"


@dataclass
class EmotionMapping:
    """Mapping configuration for an emotion across all systems."""
    core_emotion: CoreEmotion
    roberta_label: str
    confidence_threshold: float
    emoji_reactions: List[str]  # User reaction types that map to this emotion
    bot_emoji_choices: List[str]  # Default emoji choices for bot
    character_emojis: Dict[str, List[str]]  # Character-specific emoji variants


class UniversalEmotionTaxonomy:
    """
    Central mapping system between all emotion taxonomies.
    Provides translation methods without modifying existing code.
    """
    
    # Core mappings - RoBERTa emotions to everything else
    EMOTION_MAPPINGS = {
        CoreEmotion.JOY: EmotionMapping(
            core_emotion=CoreEmotion.JOY,
            roberta_label="joy",
            confidence_threshold=0.6,
            emoji_reactions=["positive_strong", "positive_mild"],
            bot_emoji_choices=["😊", "😄", "❤️", "✨"],
            character_emojis={}  # Use CDL files instead of hardcoded mappings
        ),
        
        CoreEmotion.ANGER: EmotionMapping(
            core_emotion=CoreEmotion.ANGER,
            roberta_label="anger", 
            confidence_threshold=0.7,  # Higher threshold for negative emotions
            emoji_reactions=["negative_strong"],
            bot_emoji_choices=["😠", "💢", "😤"],
            character_emojis={}  # Use CDL files instead of hardcoded mappings
        ),
        
        CoreEmotion.SADNESS: EmotionMapping(
            core_emotion=CoreEmotion.SADNESS,
            roberta_label="sadness",
            confidence_threshold=0.6, 
            emoji_reactions=["sadness", "negative_mild"],  # Added sadness reaction type
            bot_emoji_choices=["😢", "😔", "💔"],
            character_emojis={}  # Use CDL files instead of hardcoded mappings
        ),
        
        CoreEmotion.FEAR: EmotionMapping(
            core_emotion=CoreEmotion.FEAR,
            roberta_label="fear",
            confidence_threshold=0.7,
            emoji_reactions=["negative_mild", "confusion"],  # Fear often shows as confusion
            bot_emoji_choices=["😰", "😨", "😱"],
            character_emojis={}  # Use CDL files instead of hardcoded mappings
        ),
        
        CoreEmotion.SURPRISE: EmotionMapping(
            core_emotion=CoreEmotion.SURPRISE,
            roberta_label="surprise",
            confidence_threshold=0.6,
            emoji_reactions=["surprise", "mystical_wonder", "tech_appreciation"],  # Include mystical and tech reactions
            bot_emoji_choices=["😲", "🤯", "😱"],
            character_emojis={}  # Use CDL files instead of hardcoded mappings
        ),
        
        CoreEmotion.DISGUST: EmotionMapping(
            core_emotion=CoreEmotion.DISGUST,
            roberta_label="disgust",
            confidence_threshold=0.7,
            emoji_reactions=["negative_strong", "negative_mild"],
            bot_emoji_choices=["🤢", "😒", "🙄"],
            character_emojis={}  # Use CDL files instead of hardcoded mappings
        ),
        
        CoreEmotion.NEUTRAL: EmotionMapping(
            core_emotion=CoreEmotion.NEUTRAL,
            roberta_label="neutral",
            confidence_threshold=0.5,
            emoji_reactions=["neutral_thoughtful"],
            bot_emoji_choices=["😐", "🤔", "💭"],  # Truly neutral expressions
            character_emojis={}  # Use CDL files instead of hardcoded mappings
        )
    }
    
    @classmethod
    def roberta_to_emoji_choice(
        cls, 
        roberta_emotion: str, 
        character: str = "general",
        confidence: float = 0.8
    ) -> Optional[str]:
        """
        Convert RoBERTa emotion detection to appropriate emoji choice.
        Uses CDL character definitions when available, falls back to defaults.
        
        Args:
            roberta_emotion: RoBERTa emotion label (anger, joy, etc.)
            character: Bot character name (elena, marcus, dream, general)
            confidence: RoBERTa confidence score
            
        Returns:
            Appropriate emoji string or None
        """
        # Find matching core emotion
        core_emotion = None
        for emotion, mapping in cls.EMOTION_MAPPINGS.items():
            if mapping.roberta_label == roberta_emotion.lower():
                core_emotion = emotion
                break
        
        if not core_emotion:
            return None
            
        mapping = cls.EMOTION_MAPPINGS[core_emotion]
        
        # Check confidence threshold
        if confidence < mapping.confidence_threshold:
            return None
            
        # Return default bot choices (character-specific emojis handled by CDLEmojiGenerator)
        return mapping.bot_emoji_choices[0] if mapping.bot_emoji_choices else None
    
    @classmethod  
    def emoji_reaction_to_core_emotion(cls, reaction_type: str) -> Optional[CoreEmotion]:
        """
        Map user emoji reaction type to core emotion.
        
        Args:
            reaction_type: EmotionalReactionType value (positive_strong, etc.)
            
        Returns:
            Core emotion or None
        """
        reaction_lower = reaction_type.lower()
        
        for emotion, mapping in cls.EMOTION_MAPPINGS.items():
            if reaction_lower in [r.lower() for r in mapping.emoji_reactions]:
                return emotion
                
        return None
    
    @classmethod
    def get_character_emoji_for_emotion(
        cls, 
        emotion: str, 
        character: str = "general"
    ) -> List[str]:
        """
        Get character-specific emoji choices for an emotion.
        
        Note: This method returns default emojis since character-specific 
        emoji selection should be handled by CDLEmojiGenerator directly.
        
        Args:
            emotion: Core emotion name or RoBERTa label
            character: Character name (ignored - returns defaults)
            
        Returns:
            List of default emoji choices for the emotion
        """
        # Find matching mapping
        core_emotion = None
        emotion_lower = emotion.lower()
        
        for emo, mapping in cls.EMOTION_MAPPINGS.items():
            if (mapping.roberta_label == emotion_lower or 
                emo.value == emotion_lower):
                core_emotion = emo
                break
                
        if not core_emotion:
            return ["🙂"]  # Neutral fallback
            
        mapping = cls.EMOTION_MAPPINGS[core_emotion]
        return mapping.bot_emoji_choices
    
    @classmethod
    def standardize_emotion_label(cls, emotion: str) -> str:
        """
        Standardize any emotion label to RoBERTa format.
        
        Args:
            emotion: Emotion in any format
            
        Returns:
            Standardized RoBERTa emotion label
        """
        emotion_lower = emotion.lower()
        
        # Direct RoBERTa match
        roberta_labels = [m.roberta_label for m in cls.EMOTION_MAPPINGS.values()]
        if emotion_lower in roberta_labels:
            return emotion_lower
            
        # Extended emotion mapping
        extended_mappings = {
            "excitement": "joy",
            "excited": "joy",  # Common form
            "contentment": "joy", 
            "gratitude": "joy",
            "grateful": "joy",  # Common form
            "love": "joy",
            "hope": "joy",
            "happy": "joy",  # Critical basic form
            "frustration": "anger",
            "frustrated": "anger",  # Common form
            "angry": "anger",  # Critical basic form
            "anxiety": "fear",
            "worried": "fear",  # Common form
            "anxious": "fear",  # Common form
            "scared": "fear",  # Critical basic form
            "afraid": "fear",  # Common form
            "curiosity": "surprise",
            "surprised": "surprise",  # Critical basic form
            "disgusted": "disgust",  # Critical basic form
            "disappointed": "sadness",
            "disappointment": "sadness",
            "upset": "sadness",  # Common form
            "distressed": "sadness",  # Common form
            "sad": "sadness",  # Critical mapping
            "positive_strong": "joy",
            "positive_mild": "joy", 
            "negative_strong": "anger",
            "negative_mild": "sadness",
            "neutral_thoughtful": "neutral",
            "confusion": "fear",
            "confused": "fear",  # Common form
            "mystical_wonder": "surprise",
            "technical_appreciation": "joy"
        }
        
        return extended_mappings.get(emotion_lower, "neutral")


# Convenience functions for existing code integration
def get_emoji_for_roberta_emotion(emotion: str, character: str = "general", confidence: float = 0.8) -> Optional[str]:
    """Surgical integration: Get emoji for RoBERTa emotion without changing existing code."""
    return UniversalEmotionTaxonomy.roberta_to_emoji_choice(emotion, character, confidence)

def standardize_emotion(emotion: str) -> str:
    """Surgical integration: Standardize emotion label without changing existing code.""" 
    return UniversalEmotionTaxonomy.standardize_emotion_label(emotion)

def map_reaction_to_emotion(reaction_type: str) -> str:
    """Surgical integration: Map emoji reaction to standard emotion."""
    core_emotion = UniversalEmotionTaxonomy.emoji_reaction_to_core_emotion(reaction_type)
    return core_emotion.value if core_emotion else "neutral"