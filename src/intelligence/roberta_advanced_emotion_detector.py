"""
RoBERTa-Enhanced Advanced Emotion Detector

Replaces basic keyword matching with sophisticated RoBERTa-based multi-emotion analysis
for improved emotion detection across WhisperEngine systems.
"""

import logging
import re
from typing import Dict, List, Optional

from src.intelligence.advanced_emotional_state import AdvancedEmotionalState
from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer

logger = logging.getLogger(__name__)


class RobertaAdvancedEmotionDetector:
    """
    RoBERTa-Enhanced Advanced Emotion Detector
    
    Replaces the original keyword-based emotion detector with sophisticated
    transformer-based analysis while maintaining backward compatibility with
    AdvancedEmotionalState output format.
    
    Key Improvements:
    - Multi-emotion detection with intensities
    - Context-aware emotion analysis  
    - Complex emotion handling (mixed, nuanced)
    - Fallback to keyword analysis for reliability
    """
    
    def __init__(self):
        """Initialize the RoBERTa-enhanced emotion detector"""
        # Initialize RoBERTa-based analyzer
        try:
            self.roberta_analyzer = EnhancedVectorEmotionAnalyzer()
            self.use_roberta = True
            logger.info("✅ RoBERTa-Enhanced emotion detection enabled")
        except (ImportError, RuntimeError, OSError) as e:
            logger.warning("⚠️ Could not initialize RoBERTa analyzer: %s", e)
            logger.warning("Falling back to keyword-based emotion detection")
            self.roberta_analyzer = None
            self.use_roberta = False
            
        # Fallback keyword lexicons for reliability
        self.emotion_keywords = {
            "joy": ["happy", "joy", "delighted", "excited", "glad", "😊", ":)", "yay", "wonderful", "amazing"],
            "sadness": ["sad", "down", "unhappy", "depressed", "😢", ":(", "blue", "disappointed", "heartbroken"],
            "anger": ["angry", "mad", "furious", "annoyed", "😠", ">:(", "frustrated", "irritated", "outraged"],
            "fear": ["afraid", "scared", "fear", "terrified", "😨", "nervous", "worried", "anxious", "panic"],
            "surprise": ["surprised", "shocked", "amazed", "wow", "😲", "astonished", "unexpected", "startled"],
            "disgust": ["disgusted", "gross", "eww", "🤢", "revolting", "repulsive", "horrible"],
            "trust": ["trust", "confident", "secure", "reliable", "🤝", "faith", "believe", "depend"],
            "anticipation": ["anticipate", "expect", "hope", "looking forward", "⏳", "eager", "excited"],
            "contempt": ["contempt", "disdain", "smirk", "🙄", "scorn", "mock", "ridicule"],
            "pride": ["proud", "accomplished", "achievement", "🏆", "success", "triumph", "victory"],
            "shame": ["ashamed", "embarrassed", "regret", "😳", "humiliated", "mortified"],
            "guilt": ["guilty", "remorse", "sorry", "😔", "apologetic", "regretful"],
            "love": ["love", "adore", "cherish", "❤️", "💕", "affection", "romantic", "devotion"],
            "gratitude": ["grateful", "thankful", "thanks", "appreciate", "🙏", "blessed"],
            "curiosity": ["curious", "wonder", "interested", "🤔", "intrigued", "questioning"],
            "excitement": ["excited", "thrilled", "pumped", "🎉", "energetic", "enthusiastic"],
            "contentment": ["content", "peaceful", "calm", "satisfied", "serene", "relaxed"],
        }

        self.punctuation_patterns = {
            "exclamation": r"!+",
            "question": r"\?+", 
            "ellipsis": r"\.\.\.",
            "all_caps": r"\b[A-Z]{2,}\b",
            "repeated_chars": r"(.)\1{2,}",  # aaaahhh, noooo, etc.
        }

    async def detect(
        self, 
        text: str, 
        emojis: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> AdvancedEmotionalState:
        """
        Detect emotions using RoBERTa analysis with keyword fallback
        
        Args:
            text: Text to analyze for emotions
            emojis: Optional list of emojis to consider
            user_id: Optional user ID for context
            
        Returns:
            AdvancedEmotionalState with comprehensive emotion analysis
        """
        if self.use_roberta and self.roberta_analyzer:
            try:
                return await self._roberta_enhanced_detection(text, emojis, user_id)
            except (ValueError, RuntimeError, TypeError) as e:
                logger.warning("RoBERTa detection failed: %s, falling back to keywords", e)
                return await self._keyword_fallback_detection(text, emojis)
        else:
            return await self._keyword_fallback_detection(text, emojis)

    async def _roberta_enhanced_detection(
        self, 
        text: str, 
        emojis: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> AdvancedEmotionalState:
        """Enhanced emotion detection using RoBERTa transformer analysis"""
        
        # Get RoBERTa emotion analysis
        roberta_result = await self.roberta_analyzer.analyze_emotion(
            content=text,
            user_id=user_id or "advanced_detector"
        )
        
        # Convert RoBERTa results to AdvancedEmotionalState format
        primary_emotion = roberta_result.primary_emotion
        emotional_intensity = roberta_result.intensity
        
        # Get secondary emotions from all_emotions dict
        secondary_emotions = []
        if roberta_result.all_emotions:
            # Sort by intensity and get top emotions (excluding primary)
            sorted_emotions = sorted(
                roberta_result.all_emotions.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            for emotion, intensity in sorted_emotions:
                if emotion != primary_emotion and intensity > 0.3:  # Threshold for secondary emotions
                    secondary_emotions.append(emotion)
                if len(secondary_emotions) >= 3:  # Limit secondary emotions
                    break
        
        # Enhanced text analysis
        text_indicators = await self._extract_enhanced_text_indicators(text, roberta_result)
        
        # Emoji analysis (enhanced with RoBERTa context)
        emoji_analysis = self._analyze_emojis_with_context(emojis, roberta_result) if emojis else {}
        
        # Punctuation pattern analysis
        punctuation_patterns = self._analyze_punctuation_patterns(text)
        
        # Adjust intensity based on punctuation and emoji
        enhanced_intensity = self._calculate_enhanced_intensity(
            emotional_intensity, 
            punctuation_patterns, 
            emoji_analysis
        )
        
        return AdvancedEmotionalState(
            primary_emotion=primary_emotion,
            secondary_emotions=secondary_emotions,
            emotional_intensity=enhanced_intensity,
            text_indicators=text_indicators,
            emoji_analysis=emoji_analysis,
            punctuation_patterns=punctuation_patterns,
        )

    async def _keyword_fallback_detection(
        self, 
        text: str, 
        emojis: Optional[List[str]] = None
    ) -> AdvancedEmotionalState:
        """Fallback keyword-based emotion detection"""
        
        text_lower = text.lower()
        primary_emotion = None
        secondary_emotions = []
        emotional_intensity = 0.0
        text_indicators = []
        emoji_analysis = {}
        
        # Detect emotions from keywords
        emotion_scores = {}
        for emotion, keywords in self.emotion_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 0.15  # Base keyword score
                    text_indicators.append(keyword)
            
            if score > 0:
                emotion_scores[emotion] = score
                emotional_intensity += score * 0.8  # Contribute to overall intensity

        # Determine primary and secondary emotions
        if emotion_scores:
            # Primary emotion is highest scoring
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            
            # Secondary emotions are other significant emotions
            for emotion, score in emotion_scores.items():
                if emotion != primary_emotion and score >= 0.15:
                    secondary_emotions.append(emotion)
        
        # Emoji analysis
        if emojis:
            for emoji in emojis:
                for emotion, keywords in self.emotion_keywords.items():
                    if emoji in keywords:
                        emoji_analysis[emoji] = emoji_analysis.get(emoji, 0.0) + 0.3
                        if not primary_emotion:
                            primary_emotion = emotion
                        elif emotion != primary_emotion and emotion not in secondary_emotions:
                            secondary_emotions.append(emotion)
                        emotional_intensity += 0.2

        # Punctuation analysis
        punctuation_patterns = self._analyze_punctuation_patterns(text)
        
        # Adjust intensity based on punctuation
        for pattern_type, count in punctuation_patterns.items():
            if pattern_type == "exclamation":
                emotional_intensity += min(count * 0.15, 0.4)
            elif pattern_type == "all_caps":
                emotional_intensity += min(count * 0.1, 0.3)
            elif pattern_type == "repeated_chars":
                emotional_intensity += min(count * 0.05, 0.2)

        # Normalize intensity and set default
        emotional_intensity = min(emotional_intensity, 1.0)
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

    async def _extract_enhanced_text_indicators(
        self, 
        text: str, 
        roberta_result
    ) -> List[str]:
        """Extract enhanced text indicators using RoBERTa context"""
        indicators = []
        
        # Get basic keyword indicators
        text_lower = text.lower()
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    indicators.append(keyword)
        
        # Add RoBERTa-specific indicators
        if roberta_result.all_emotions:
            # Add detected emotion labels as indicators
            for emotion, confidence in roberta_result.all_emotions.items():
                if confidence > 0.5:  # High confidence emotions
                    indicators.append(f"roberta_{emotion}")
        
        # Add intensity indicators
        if roberta_result.intensity > 0.7:
            indicators.append("high_intensity")
        elif roberta_result.intensity > 0.4:
            indicators.append("medium_intensity")
            
        return indicators

    def _analyze_emojis_with_context(
        self, 
        emojis: List[str], 
        roberta_result
    ) -> Dict[str, float]:
        """Analyze emojis with RoBERTa context for enhanced scoring"""
        emoji_analysis = {}
        
        for emoji in emojis:
            base_score = 0.2  # Base emoji emotional score
            
            # Check if emoji matches detected emotions
            for emotion, keywords in self.emotion_keywords.items():
                if emoji in keywords:
                    # Boost score if RoBERTa also detected this emotion
                    if roberta_result.all_emotions and emotion in roberta_result.all_emotions:
                        roberta_intensity = roberta_result.all_emotions[emotion]
                        base_score += roberta_intensity * 0.3  # Context boost
                    
                    emoji_analysis[emoji] = base_score
                    break
            else:
                # Emoji not in keyword lists - use base score
                emoji_analysis[emoji] = base_score
                
        return emoji_analysis

    def _analyze_punctuation_patterns(self, text: str) -> Dict[str, int]:
        """Analyze punctuation patterns for emotional intensity"""
        patterns = {}
        
        for pattern_name, pattern_regex in self.punctuation_patterns.items():
            matches = re.findall(pattern_regex, text)
            if matches:
                patterns[pattern_name] = len(matches)
                
        return patterns

    def _calculate_enhanced_intensity(
        self, 
        base_intensity: float,
        punctuation_patterns: Dict[str, int],
        emoji_analysis: Dict[str, float]
    ) -> float:
        """Calculate enhanced emotional intensity"""
        intensity = base_intensity
        
        # Punctuation boosts
        intensity += min(punctuation_patterns.get("exclamation", 0) * 0.1, 0.3)
        intensity += min(punctuation_patterns.get("all_caps", 0) * 0.05, 0.2)
        intensity += min(punctuation_patterns.get("repeated_chars", 0) * 0.03, 0.15)
        
        # Emoji boosts
        if emoji_analysis:
            avg_emoji_intensity = sum(emoji_analysis.values()) / len(emoji_analysis)
            intensity += min(avg_emoji_intensity * 0.2, 0.25)
        
        return min(intensity, 1.0)  # Cap at 1.0

    # Synchronous wrapper for backward compatibility
    def detect_sync(
        self, 
        text: str, 
        emojis: Optional[List[str]] = None
    ) -> AdvancedEmotionalState:
        """Synchronous wrapper for backward compatibility"""
        import asyncio
        
        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we can't use run_until_complete
                # Fall back to keyword detection synchronously
                logger.warning("Event loop already running, using keyword fallback")
                # Create a dummy coroutine runner for the async method
                async def _run_fallback():
                    return await self._keyword_fallback_detection(text, emojis)
                
                # This won't work in running loop, so do sync fallback
                return self._keyword_fallback_detection_sync(text, emojis)
            else:
                return loop.run_until_complete(self.detect(text, emojis))
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self.detect(text, emojis))

    def _keyword_fallback_detection_sync(
        self, 
        text: str, 
        emojis: Optional[List[str]] = None
    ) -> AdvancedEmotionalState:
        """Synchronous keyword-based emotion detection for compatibility"""
        
        text_lower = text.lower()
        primary_emotion = None
        secondary_emotions = []
        emotional_intensity = 0.0
        text_indicators = []
        emoji_analysis = {}
        
        # Detect emotions from keywords
        emotion_scores = {}
        for emotion, keywords in self.emotion_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 0.15  # Base keyword score
                    text_indicators.append(keyword)
            
            if score > 0:
                emotion_scores[emotion] = score
                emotional_intensity += score * 0.8  # Contribute to overall intensity

        # Determine primary and secondary emotions
        if emotion_scores:
            # Primary emotion is highest scoring
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            
            # Secondary emotions are other significant emotions
            for emotion, score in emotion_scores.items():
                if emotion != primary_emotion and score >= 0.15:
                    secondary_emotions.append(emotion)
        
        # Emoji analysis
        if emojis:
            for emoji in emojis:
                for emotion, keywords in self.emotion_keywords.items():
                    if emoji in keywords:
                        emoji_analysis[emoji] = emoji_analysis.get(emoji, 0.0) + 0.3
                        if not primary_emotion:
                            primary_emotion = emotion
                        elif emotion != primary_emotion and emotion not in secondary_emotions:
                            secondary_emotions.append(emotion)
                        emotional_intensity += 0.2

        # Punctuation analysis
        punctuation_patterns = self._analyze_punctuation_patterns(text)
        
        # Adjust intensity based on punctuation
        for pattern_type, count in punctuation_patterns.items():
            if pattern_type == "exclamation":
                emotional_intensity += min(count * 0.15, 0.4)
            elif pattern_type == "all_caps":
                emotional_intensity += min(count * 0.1, 0.3)
            elif pattern_type == "repeated_chars":
                emotional_intensity += min(count * 0.05, 0.2)

        # Normalize intensity and set default
        emotional_intensity = min(emotional_intensity, 1.0)
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


# Factory function for dependency injection
def create_roberta_advanced_emotion_detector() -> RobertaAdvancedEmotionDetector:
    """Create a RoBERTa advanced emotion detector instance."""
    return RobertaAdvancedEmotionDetector()


# For backward compatibility - create an instance with the original class name
AdvancedEmotionDetector = RobertaAdvancedEmotionDetector