"""
Advanced Emotion Detector for WhisperEngine Sprint 5

Multi-modal emotion detection leveraging existing RoBERTa analysis and emoji intelligence.
Extends 11-emotion RoBERTa system to 12+ emotions with temporal patterns and cultural adaptation.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import asyncio
from datetime import datetime
import numpy as np

# WhisperEngine imports
from src.intelligence.advanced_emotional_state import AdvancedEmotionalState
from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer, EmotionAnalysisResult
from src.intelligence.emoji_reaction_intelligence import EmojiEmotionMapper, EmotionalReactionType
from src.intelligence.emotion_taxonomy import UniversalEmotionTaxonomy, CoreEmotion
from src.memory.vector_memory_system import VectorMemoryManager
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

class AdvancedEmotionDetector:
    """
    Sprint 5 Advanced Emotion Detection System
    
    Features:
    - Leverages existing RoBERTa 11-emotion analysis as foundation
    - Extends to 12+ emotions through advanced mapping and synthesis
    - Multi-modal analysis using existing emoji intelligence systems  
    - Temporal pattern recognition from conversation history
    - Cultural adaptation framework
    - Zero duplication - builds on existing WhisperEngine systems
    """
    
    # Extended emotion set: 11 RoBERTa core + additional advanced emotions
    CORE_EMOTIONS = {
        # RoBERTa core emotions (11) - Cardiff NLP model
        "anger", "anticipation", "disgust", "fear", "joy", "love", 
        "optimism", "pessimism", "sadness", "surprise", "trust",
        # Extended emotions mapped from RoBERTa patterns
        "contempt", "pride", "shame", "guilt", "awe", "confusion", "disappointment"
    }
    
    # Advanced emotion synthesis rules: Map RoBERTa patterns to extended emotions
    EMOTION_SYNTHESIS_RULES = {
        # Love: High joy + positive context + affection patterns
        "love": {
            "primary_roberta": ["joy"],
            "secondary_roberta": ["joy", "surprise"],
            "confidence_boost": 0.2,
            "text_patterns": ["love", "adore", "cherish", "heart", "amazing", "wonderful"],
            "emoji_types": [EmotionalReactionType.POSITIVE_STRONG]
        },
        
        # Contempt: Disgust + anger patterns + dismissive context
        "contempt": {
            "primary_roberta": ["disgust", "anger"],
            "secondary_roberta": ["anger", "disgust"], 
            "confidence_boost": 0.1,
            "text_patterns": ["ridiculous", "pathetic", "whatever", "seriously", "pfft"],
            "emoji_types": [EmotionalReactionType.NEGATIVE_MILD, EmotionalReactionType.NEUTRAL_THOUGHTFUL]
        },
        
        # Pride: Joy + confidence + achievement patterns
        "pride": {
            "primary_roberta": ["joy"],
            "secondary_roberta": ["surprise", "joy"],
            "confidence_boost": 0.15,
            "text_patterns": ["proud", "accomplished", "achieved", "success", "excellent", "nailed it"],
            "emoji_types": [EmotionalReactionType.POSITIVE_STRONG, EmotionalReactionType.POSITIVE_MILD]
        },
        
        # Awe: Surprise + positive + wonder patterns
        "awe": {
            "primary_roberta": ["surprise", "joy"],
            "secondary_roberta": ["surprise", "joy"],
            "confidence_boost": 0.2,
            "text_patterns": ["amazing", "incredible", "wow", "breathtaking", "stunning", "magnificent"],
            "emoji_types": [EmotionalReactionType.MYSTICAL_WONDER, EmotionalReactionType.POSITIVE_STRONG]
        },
        
        # Confusion: Neutral + uncertainty + questioning patterns
        "confusion": {
            "primary_roberta": ["neutral", "surprise"],
            "secondary_roberta": ["fear", "neutral"],
            "confidence_boost": 0.1,
            "text_patterns": ["confused", "don't understand", "what", "huh", "unclear", "lost"],
            "emoji_types": [EmotionalReactionType.CONFUSION, EmotionalReactionType.NEUTRAL_THOUGHTFUL]
        }
    }
    
    def __init__(self, 
                 enhanced_emotion_analyzer: Optional[EnhancedVectorEmotionAnalyzer] = None,
                 memory_manager: Optional[VectorMemoryManager] = None):
        """Initialize Advanced Emotion Detector leveraging existing WhisperEngine systems."""
        self.logger = logging.getLogger(__name__)
        self.enhanced_analyzer = enhanced_emotion_analyzer
        self.memory_manager = memory_manager
        
        # Initialize existing systems
        self.emoji_mapper = EmojiEmotionMapper()
        self.emotion_taxonomy = UniversalEmotionTaxonomy()
        
        # Cultural adaptation settings
        self.cultural_context = "western"  # Default, can be configured
        self.expression_style = "direct"   # vs indirect
        
        self.logger.info("🧠 Advanced Emotion Detector initialized (Sprint 5)")
        self.logger.info(f"✅ Supporting {len(self.CORE_EMOTIONS)} emotions via RoBERTa + synthesis")
        self.logger.info(f"✅ Multi-modal: RoBERTa + {len(self.emoji_mapper.EMOJI_EMOTION_MAP)} emoji mappings")
        self.logger.info(f"✅ Advanced synthesis: {len(self.EMOTION_SYNTHESIS_RULES)} extended emotions")
    
    # ==================== EMA SMOOTHING FOR TRAJECTORY ANALYSIS ====================
    
    def _calculate_ema(
        self,
        current: float,
        previous_ema: Optional[float] = None,
        alpha: float = 0.3
    ) -> float:
        """
        Calculate Exponential Moving Average for emotion smoothing.
        
        Used for trajectory analysis (not for immediate crisis response).
        Smooths emotional intensity to reveal true trends vs noise from filler messages.
        
        Args:
            current: Current raw emotional intensity (0.0-1.0)
            previous_ema: Previous EMA value (None for first message)
            alpha: Smoothing factor (0.15-0.45)
                - 0.2: Heavy smoothing (support conversations)
                - 0.3: Moderate smoothing (default, general chat)
                - 0.4: Light smoothing (group chats, fast-paced)
        
        Returns:
            Smoothed emotional intensity (0.0-1.0)
        
        Formula:
            EMA = α × I_t + (1 - α) × EMA_(t-1)
        """
        if previous_ema is None:
            # Cold start: First message, EMA = raw intensity
            return np.clip(float(current), 0.0, 1.0)
        
        # Standard EMA calculation
        ema_value = alpha * current + (1 - alpha) * previous_ema
        
        # Ensure value stays within valid range
        return np.clip(float(ema_value), 0.0, 1.0)
    
    async def _get_previous_ema(
        self,
        user_id: str,
        limit: int = 1
    ) -> Optional[float]:
        """
        Retrieve the most recent EMA value for a user from memory.
        
        Used in EMA calculation to get previous smoothed value.
        Gracefully handles cold start (first message) and backward compatibility
        with old payloads that don't have EMA field.
        
        Args:
            user_id: User identifier
            limit: Number of recent records to check (default: 1)
        
        Returns:
            Previous EMA value (0.0-1.0), or None if not found
        """
        try:
            if not self.memory_manager:
                self.logger.debug("Memory manager not available, cannot retrieve previous EMA")
                return None
            
            # Retrieve recent emotional memories
            recent_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="emotion emotional feeling intensity",
                limit=limit
            )
            
            if not recent_memories or len(recent_memories) == 0:
                # No previous memories (first message)
                return None
            
            # Extract EMA from most recent memory
            most_recent = recent_memories[0]
            payload = most_recent.get('payload', {})
            
            # Try EMA field first, fall back to raw intensity for old payloads
            ema = payload.get('emotional_intensity_ema')
            if ema is not None:
                return float(ema)
            
            # Fallback: Use raw intensity if EMA not available (backward compatibility)
            intensity = payload.get('emotional_intensity')
            if intensity is not None:
                self.logger.debug(
                    "No EMA found in payload, using raw intensity as fallback for %s",
                    user_id
                )
                return float(intensity)
            
            # No emotional data found
            return None
            
        except Exception as e:
            self.logger.warning(
                "Could not retrieve previous EMA for %s: %s",
                user_id,
                str(e)
            )
            return None
    
    @handle_errors(category=ErrorCategory.MEMORY_SYSTEM, severity=ErrorSeverity.MEDIUM)
    async def detect_advanced_emotions(self, 
                                     text: str, 
                                     user_id: str,
                                     context: Optional[Dict[str, Any]] = None) -> AdvancedEmotionalState:
        """
        Perform advanced multi-modal emotion detection using existing RoBERTa + emoji systems.
        
        Returns AdvancedEmotionalState with 12+ emotion support and multi-modal analysis.
        """
        try:
            # Step 1: Get RoBERTa analysis (foundation - existing system)
            roberta_result = None
            if self.enhanced_analyzer:
                roberta_result = await self.enhanced_analyzer.analyze_emotion(text, user_id)
                self.logger.debug(f"🤖 RoBERTa foundation: {roberta_result.primary_emotion} ({roberta_result.confidence:.3f})")
            
            # Step 2: Extract emojis and use existing emoji intelligence
            emoji_analysis = self._analyze_emojis_with_existing_system(text)
            
            # Step 3: Advanced emotion synthesis (RoBERTa → 12+ emotions)
            primary_emotion, secondary_emotions = self._synthesize_advanced_emotions(
                roberta_result, emoji_analysis, text
            )
            
            # Step 4: Calculate emotional intensity using RoBERTa data
            intensity = self._calculate_emotional_intensity_from_roberta(
                roberta_result, emoji_analysis, text
            )
            
            # Step 5: Temporal pattern analysis (if memory available)
            temporal_trajectory, pattern_type = await self._analyze_temporal_patterns(user_id, primary_emotion)
            
            # Step 6: Cultural adaptation
            cultural_adaptation = self._apply_cultural_adaptation(primary_emotion, text)
            
            # Create advanced emotional state
            emotional_state = AdvancedEmotionalState(
                primary_emotion=primary_emotion,
                secondary_emotions=secondary_emotions,
                emotional_intensity=intensity,
                text_indicators=self._extract_roberta_indicators(roberta_result),
                emoji_analysis=emoji_analysis,
                punctuation_patterns=self._analyze_punctuation_patterns(text),
                emotional_trajectory=temporal_trajectory,
                pattern_type=pattern_type,
                cultural_context=cultural_adaptation.get("context"),
                expression_style=cultural_adaptation.get("style"),
                timestamp=datetime.utcnow()
            )
            
            self.logger.info(f"🧠 Advanced emotion synthesis: {primary_emotion} (intensity: {intensity:.2f})")
            if secondary_emotions:
                self.logger.info(f"   Secondary emotions: {', '.join(secondary_emotions)}")
            
            return emotional_state
            
        except Exception as e:
            self.logger.error(f"❌ Advanced emotion detection failed: {e}")
            # Fallback to basic emotional state
            return AdvancedEmotionalState(
                primary_emotion="neutral",
                emotional_intensity=0.5,
                timestamp=datetime.utcnow()
            )
    
    @handle_errors(category=ErrorCategory.MEMORY_SYSTEM, severity=ErrorSeverity.MEDIUM)
    async def detect_advanced_emotions_with_roberta_result(self, 
                                                         text: str, 
                                                         user_id: str,
                                                         roberta_result,
                                                         context: Optional[Dict[str, Any]] = None) -> AdvancedEmotionalState:
        """
        Perform advanced multi-modal emotion detection using existing RoBERTa results.
        
        This method is called serially after basic emotion analysis to avoid RoBERTa model race conditions.
        Uses existing RoBERTa analysis results instead of re-analyzing.
        
        Args:
            text: Message text for emoji/pattern analysis
            user_id: User identifier for temporal analysis
            roberta_result: Existing EmotionAnalysisResult from basic analysis
            context: Optional context information
            
        Returns:
            AdvancedEmotionalState with 12+ emotion support and multi-modal analysis
        """
        try:
            self.logger.debug(f"🎭 SERIAL EMOTION: Using existing RoBERTa result: {roberta_result.primary_emotion} ({roberta_result.confidence:.3f})")
            
            # Step 1: Use provided RoBERTa analysis (no re-analysis)
            # roberta_result is already available from basic analysis
            
            # Step 2: Extract emojis and use existing emoji intelligence  
            emoji_analysis = self._analyze_emojis_with_existing_system(text)
            
            # Step 3: Advanced emotion synthesis (RoBERTa → 12+ emotions)
            primary_emotion, secondary_emotions = self._synthesize_advanced_emotions(
                roberta_result, emoji_analysis, text
            )
            
            # Step 4: Calculate emotional intensity using RoBERTa data
            intensity = self._calculate_emotional_intensity_from_roberta(
                roberta_result, emoji_analysis, text
            )
            
            # Step 5: Temporal pattern analysis (if memory available)
            temporal_trajectory, pattern_type = await self._analyze_temporal_patterns(user_id, primary_emotion)
            
            # Step 6: Cultural adaptation
            cultural_adaptation = self._apply_cultural_adaptation(primary_emotion, text)
            
            # Create advanced emotional state
            emotional_state = AdvancedEmotionalState(
                primary_emotion=primary_emotion,
                secondary_emotions=secondary_emotions,
                emotional_intensity=intensity,
                emoji_analysis=emoji_analysis,
                text_indicators=self._extract_roberta_indicators(roberta_result),
                emotional_trajectory=temporal_trajectory,
                pattern_type=pattern_type,
                cultural_context=cultural_adaptation.get('expression_style') if cultural_adaptation else None,
                timestamp=datetime.utcnow()
            )
            
            self.logger.info(f"🎭 SERIAL EMOTION: Advanced synthesis complete: {primary_emotion} (intensity: {intensity:.2f})")
            if secondary_emotions:
                self.logger.info(f"   Secondary emotions: {', '.join(secondary_emotions)}")
            
            return emotional_state
            
        except Exception as e:
            self.logger.error(f"❌ SERIAL EMOTION: Advanced emotion detection failed: {e}")
            # Fallback to basic emotional state using roberta_result
            fallback_emotion = roberta_result.primary_emotion if roberta_result else "neutral"
            fallback_intensity = roberta_result.intensity if roberta_result and hasattr(roberta_result, 'intensity') else 0.5
            return AdvancedEmotionalState(
                primary_emotion=fallback_emotion,
                emotional_intensity=fallback_intensity,
                timestamp=datetime.utcnow()
            )
    
    def _analyze_emojis_with_existing_system(self, text: str) -> Dict[str, float]:
        """Analyze emoji content using existing EmojiEmotionMapper system."""
        emoji_analysis = {}
        
        # Extract individual emojis using regex for Unicode emoji patterns
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]", flags=re.UNICODE  # Removed + to capture individual emojis
        )
        
        emojis_found = emoji_pattern.findall(text)
        
        if not emojis_found:
            return emoji_analysis
        
        # Use existing emoji emotion mapper
        emotion_type_counts = {}
        for emoji in emojis_found:
            if emoji in self.emoji_mapper.EMOJI_EMOTION_MAP:
                emotion_type, confidence = self.emoji_mapper.EMOJI_EMOTION_MAP[emoji]
                emotion_type_name = emotion_type.value
                emotion_type_counts[emotion_type_name] = emotion_type_counts.get(emotion_type_name, 0) + confidence
        
        # Convert to normalized confidence scores
        total_weight = sum(emotion_type_counts.values())
        if total_weight > 0:
            for emotion_type, weight in emotion_type_counts.items():
                emoji_analysis[emotion_type] = weight / total_weight
        
        self.logger.debug(f"😊 Emoji analysis: {len(emojis_found)} emojis → {emoji_analysis}")
        return emoji_analysis
    
    def _synthesize_advanced_emotions(self, 
                                    roberta_result: Optional[EmotionAnalysisResult], 
                                    emoji_analysis: Dict[str, float],
                                    text: str) -> Tuple[str, List[str]]:
        """
        Synthesize advanced emotions (12+) from RoBERTa foundation and context.
        
        Uses emotion synthesis rules to map 7 RoBERTa emotions → 12+ advanced emotions.
        """
        if not roberta_result:
            return "neutral", []
        
        # Start with RoBERTa primary emotion as baseline
        primary_emotion = roberta_result.primary_emotion
        secondary_emotions = []
        
        # Check for advanced emotion patterns
        text_lower = text.lower()
        best_advanced_emotion = None
        best_confidence = 0.0
        
        for advanced_emotion, rules in self.EMOTION_SYNTHESIS_RULES.items():
            confidence = self._calculate_synthesis_confidence(
                advanced_emotion, rules, roberta_result, emoji_analysis, text_lower
            )
            
            if confidence > best_confidence and confidence > 0.3:  # Threshold for advanced emotions
                best_advanced_emotion = advanced_emotion
                best_confidence = confidence
        
        # Use advanced emotion if confidence is high enough
        if best_advanced_emotion and best_confidence > roberta_result.confidence * 0.8:
            primary_emotion = best_advanced_emotion
            # Add original RoBERTa emotion as secondary if different
            if roberta_result.primary_emotion != best_advanced_emotion:
                secondary_emotions.append(roberta_result.primary_emotion)
        
        # Add other high-confidence emotions from RoBERTa mixed emotions
        if hasattr(roberta_result, 'mixed_emotions') and roberta_result.mixed_emotions:
            for emotion, score in roberta_result.mixed_emotions[:2]:  # Top 2 mixed emotions
                if emotion != primary_emotion and score > 0.3:
                    secondary_emotions.append(emotion)
        
        self.logger.debug(f"🔄 Emotion synthesis: {roberta_result.primary_emotion} → {primary_emotion}")
        return primary_emotion, secondary_emotions[:3]  # Limit to top 3 secondary
    
    def _calculate_synthesis_confidence(self, 
                                      advanced_emotion: str, 
                                      rules: Dict[str, Any],
                                      roberta_result: EmotionAnalysisResult,
                                      emoji_analysis: Dict[str, float],
                                      text_lower: str) -> float:
        """Calculate confidence for an advanced emotion synthesis."""
        confidence_factors = []
        
        # RoBERTa primary emotion match
        if roberta_result.primary_emotion in rules["primary_roberta"]:
            confidence_factors.append(roberta_result.confidence * 0.6)  # 60% weight
        
        # RoBERTa secondary emotion support
        if hasattr(roberta_result, 'mixed_emotions') and roberta_result.mixed_emotions:
            for emotion, score in roberta_result.mixed_emotions:
                if emotion in rules["secondary_roberta"]:
                    confidence_factors.append(score * 0.2)  # 20% weight
        
        # Text pattern matching
        pattern_matches = sum(1 for pattern in rules["text_patterns"] if pattern in text_lower)
        if pattern_matches > 0:
            pattern_confidence = min(pattern_matches * 0.15, 0.4)  # Max 40% from text patterns
            confidence_factors.append(pattern_confidence)
        
        # Emoji type alignment
        for emoji_type in rules["emoji_types"]:
            if emoji_type.value in emoji_analysis:
                confidence_factors.append(emoji_analysis[emoji_type.value] * 0.2)  # 20% weight
        
        # Calculate weighted average
        if confidence_factors:
            base_confidence = sum(confidence_factors) / len(confidence_factors)
            return min(base_confidence + rules["confidence_boost"], 1.0)
        
        return 0.0
    
    def _calculate_emotional_intensity_from_roberta(self,
                                                   roberta_result: Optional[EmotionAnalysisResult],
                                                   emoji_analysis: Dict[str, float],
                                                   text: str) -> float:
        """Calculate emotional intensity primarily from RoBERTa confidence scores."""
        if not roberta_result:
            return 0.5
        
        # Start with RoBERTa intensity (primary factor - 70%)
        intensity_factors = [roberta_result.intensity * 0.7]
        
        # RoBERTa confidence contribution (20%)
        intensity_factors.append(roberta_result.confidence * 0.2)
        
        # Emoji intensity (10%)
        if emoji_analysis:
            emoji_intensity = min(sum(emoji_analysis.values()), 1.0)
            intensity_factors.append(emoji_intensity * 0.1)
        
        # Calculate final intensity
        final_intensity = sum(intensity_factors)
        return min(max(final_intensity, 0.1), 1.0)  # Clamp to 0.1-1.0
    
    async def _calculate_emotional_intensity_with_ema(self,
                                                      roberta_result: Optional[EmotionAnalysisResult],
                                                      emoji_analysis: Dict[str, float],
                                                      text: str,
                                                      user_id: str,
                                                      alpha: float = 0.3) -> Dict[str, Any]:
        """
        Calculate emotional intensity with EMA smoothing for trajectory analysis.
        
        Returns both raw intensity (for crisis detection) and smoothed EMA (for trajectory).
        
        Args:
            roberta_result: RoBERTa emotion analysis
            emoji_analysis: Emoji sentiment contributions
            text: Original message text
            user_id: User identifier for retrieving previous EMA
            alpha: EMA smoothing factor (0.3 = default, balanced)
        
        Returns:
            Dict with 'raw' (unsmoothed) and 'ema' (smoothed) intensity values
        """
        # Calculate raw intensity (same as before)
        raw_intensity = self._calculate_emotional_intensity_from_roberta(
            roberta_result, emoji_analysis, text
        )
        
        # Get previous EMA value from memory
        previous_ema = await self._get_previous_ema(user_id)
        
        # Calculate EMA using the formula: EMA = α × I_t + (1 - α) × EMA_prev
        ema_intensity = self._calculate_ema(
            current=raw_intensity,
            previous_ema=previous_ema,
            alpha=alpha
        )
        
        self.logger.debug(
            f"📊 EMA Calculation for {user_id}: raw={raw_intensity:.3f}, "
            f"ema_prev={previous_ema if previous_ema is None else f'{previous_ema:.3f}'}, "
            f"ema_new={ema_intensity:.3f} (α={alpha})"
        )
        
        return {
            'raw': raw_intensity,          # For crisis detection (use unsmoothed)
            'ema': ema_intensity,          # For trajectory analysis (use smoothed)
            'alpha': alpha,                # Alpha factor used
            'previous_ema': previous_ema   # Previous value (for debugging)
        }
    
    def _extract_roberta_indicators(self, roberta_result: Optional[EmotionAnalysisResult]) -> List[str]:
        """Extract text indicators from RoBERTa analysis results."""
        if not roberta_result:
            return []
        
        indicators = [f"roberta:{roberta_result.primary_emotion}:{roberta_result.confidence:.3f}"]
        
        # Add mixed emotions as indicators
        if hasattr(roberta_result, 'mixed_emotions') and roberta_result.mixed_emotions:
            for emotion, score in roberta_result.mixed_emotions:
                indicators.append(f"roberta_mixed:{emotion}:{score:.3f}")
        
        return indicators
    
    def _analyze_punctuation_patterns(self, text: str) -> Dict[str, int]:
        """Analyze punctuation patterns for emotional intensity indicators."""
        patterns = {
            "multiple_exclamation": len(re.findall(r"!{2,}", text)),
            "multiple_question": len(re.findall(r"\?{2,}", text)),
            "multiple_periods": len(re.findall(r"\.{3,}", text)),
            "caps_lock": len(re.findall(r"[A-Z]{3,}", text)),
            "mixed_punctuation": len(re.findall(r"[!?]{2,}", text)),
            "emphasis_dashes": len(re.findall(r"-{2,}", text)),
            "emotional_spacing": len(re.findall(r"\s{2,}", text))
        }
        
        # Special analysis for emotional intensity
        if patterns.get("multiple_exclamation", 0) > 0:
            patterns["excitement_level"] = min(patterns["multiple_exclamation"] * 2, 10)
        
        if patterns.get("caps_lock", 0) > 0:
            patterns["emphasis_level"] = min(len(re.findall(r"[A-Z]+", text)), 10)
        
        self.logger.debug(f"📝 Punctuation analysis: {patterns}")
        return patterns
    
    async def _analyze_temporal_patterns(self, user_id: str, current_emotion: str) -> Tuple[List[float], Optional[str]]:
        """Analyze temporal emotion patterns from conversation history."""
        if not self.memory_manager:
            return [], None
        
        try:
            # Get recent emotional history from memory
            recent_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="emotion emotional feeling",
                limit=10
            )
            
            # Extract emotion trajectory (last 5 measurements)
            emotion_trajectory = []
            for memory in recent_memories[:5]:
                # Memory is dict format from vector system
                if isinstance(memory, dict) and 'payload' in memory and 'emotional_intensity' in memory['payload']:
                    emotion_trajectory.append(memory['payload']['emotional_intensity'])
            
            # Determine pattern type
            pattern_type = None
            if len(emotion_trajectory) >= 3:
                pattern_type = self._classify_emotional_pattern(emotion_trajectory)
            
            self.logger.debug(f"📈 Temporal pattern: {pattern_type}, trajectory: {emotion_trajectory}")
            return emotion_trajectory, pattern_type
            
        except Exception as e:
            self.logger.warning(f"⚠️ Temporal pattern analysis failed: {e}")
            return [], None
    
    def _classify_emotional_pattern(self, trajectory: List[float]) -> str:
        """Classify emotional pattern from trajectory."""
        if len(trajectory) < 3:
            return "insufficient_data"
        
        # Calculate trend
        differences = [trajectory[i+1] - trajectory[i] for i in range(len(trajectory)-1)]
        avg_change = sum(differences) / len(differences)
        variance = sum((d - avg_change) ** 2 for d in differences) / len(differences)
        
        # Classify pattern
        if abs(avg_change) < 0.1 and variance < 0.05:
            return "stable"
        elif avg_change > 0.1:
            return "escalating" 
        elif avg_change < -0.1:
            return "declining"
        elif variance > 0.1:
            return "oscillating"
        else:
            return "variable"
    
    def _apply_cultural_adaptation(self, primary_emotion: str, text: str) -> Dict[str, str]:
        """Apply cultural adaptation to emotion interpretation."""
        adaptation = {
            "context": self.cultural_context,
            "style": self.expression_style
        }
        
        # Cultural adjustment logic could be expanded here
        # For now, return basic settings
        
        return adaptation
    
    def get_emotion_statistics(self) -> Dict[str, Any]:
        """Get statistics about the emotion detection system."""
        return {
            "supported_emotions": len(self.CORE_EMOTIONS),
            "emotion_list": sorted(list(self.CORE_EMOTIONS)),
            "emoji_mappings": len(self.emoji_mapper.EMOJI_EMOTION_MAP),
            "synthesis_rules": len(self.EMOTION_SYNTHESIS_RULES),
            "cultural_context": self.cultural_context,
            "expression_style": self.expression_style,
            "integration_components": {
                "enhanced_analyzer": self.enhanced_analyzer is not None,
                "memory_manager": self.memory_manager is not None,
                "emoji_mapper": self.emoji_mapper is not None,
                "emotion_taxonomy": self.emotion_taxonomy is not None
            }
        }