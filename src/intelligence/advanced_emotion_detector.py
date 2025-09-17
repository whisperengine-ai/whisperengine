"""
Advanced Emotion Detector for WhisperEngine

Detects primary and nuanced emotions from text, emoji, and punctuation. Supports multi-modal input and outputs AdvancedEmotionalState.
"""
from typing import List, Dict, Optional
from src.intelligence.advanced_emotional_state import AdvancedEmotionalState
import re

# Example emotion lexicons (expand for production)
EMOTION_KEYWORDS = {
    "joy": ["happy", "joy", "delighted", "excited", "glad", "😊", ":)", "yay"],
    "sadness": ["sad", "down", "unhappy", "depressed", "😢", ":(", "blue"],
    "anger": ["angry", "mad", "furious", "annoyed", "😠", ">:("],
    "fear": ["afraid", "scared", "fear", "terrified", "😨", "nervous"],
    "surprise": ["surprised", "shocked", "amazed", "wow", "😲"],
    "disgust": ["disgusted", "gross", "eww", "🤢"],
    "trust": ["trust", "confident", "secure", "reliable", "🤝"],
    "anticipation": ["anticipate", "expect", "hope", "looking forward", "⏳"],
    "contempt": ["contempt", "disdain", "smirk", "🙄"],
    "pride": ["proud", "accomplished", "achievement", "🏆"],
    "shame": ["ashamed", "embarrassed", "regret", "😳"],
    "guilt": ["guilty", "remorse", "sorry", "😔"],
}

PUNCTUATION_PATTERNS = {
    "exclamation": r"!+",
    "question": r"\?+",
    "ellipsis": r"\.\.\.",
    "all_caps": r"\b[A-Z]{2,}\b",
}

class AdvancedEmotionDetector:
    def __init__(self):
        pass

    def detect(self, text: str, emojis: Optional[List[str]] = None) -> AdvancedEmotionalState:
        text_lower = text.lower()
        primary_emotion = None
        secondary_emotions = []
        emotional_intensity = 0.0
        text_indicators = []
        emoji_analysis = {}
        punctuation_patterns = {}

        # Detect primary and secondary emotions
        for emotion, keywords in EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    if not primary_emotion:
                        primary_emotion = emotion
                    elif emotion != primary_emotion and emotion not in secondary_emotions:
                        secondary_emotions.append(emotion)
                    text_indicators.append(kw)
                    emotional_intensity += 0.1
        # Emoji analysis
        if emojis:
            for emoji in emojis:
                for emotion, keywords in EMOTION_KEYWORDS.items():
                    if emoji in keywords:
                        emoji_analysis[emoji] = emoji_analysis.get(emoji, 0.0) + 0.2
                        if not primary_emotion:
                            primary_emotion = emotion
                        elif emotion != primary_emotion and emotion not in secondary_emotions:
                            secondary_emotions.append(emotion)
                        emotional_intensity += 0.1
        # Punctuation patterns
        for name, pattern in PUNCTUATION_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                punctuation_patterns[name] = len(matches)
                emotional_intensity += 0.05 * len(matches)
        # Normalize intensity
        emotional_intensity = min(emotional_intensity, 1.0)
        # Fallback if no emotion detected
        if not primary_emotion:
            primary_emotion = "neutral"
        return AdvancedEmotionalState(
            primary_emotion=primary_emotion,
            secondary_emotions=secondary_emotions,
            emotional_intensity=emotional_intensity,
            text_indicators=text_indicators,
            emoji_analysis=emoji_analysis,
            punctuation_patterns=punctuation_patterns,
        )
