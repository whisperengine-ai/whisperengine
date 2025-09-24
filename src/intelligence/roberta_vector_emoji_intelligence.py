"""
🚀 RoBERTa-Enhanced Vector Emoji Intelligence System

Advanced emoji reaction system that combines RoBERTa's contextual understanding
with vector similarity search for intelligent emoji selection.

Key Features:
- RoBERTa-powered emotion detection for precise emoji matching
- Vector similarity search for historical emoji pattern recognition  
- Multi-emotion emoji combinations for complex emotional states
- Context-aware emoji timing and appropriateness
- Character personality integration for emoji style adaptation
- Fallback systems for reliability

Integration Points:
- Enhances existing VectorEmojiIntelligence system
- Uses EnhancedVectorEmotionAnalyzer for emotion detection
- Integrates with vector memory for pattern learning
- Works with security validation for content filtering

Author: WhisperEngine AI Team
Created: 2024-09-23
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Core WhisperEngine imports
from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer
from src.intelligence.emoji_reaction_intelligence import EmojiEmotionMapper

logger = logging.getLogger(__name__)

class EmojiComplexity(Enum):
    """Levels of emoji reaction complexity"""
    SIMPLE = "simple"           # Single emoji 😊
    COMPOUND = "compound"       # Two related emojis 😊💖
    COMPLEX = "complex"         # Multiple emotions 😊😰💪
    NARRATIVE = "narrative"     # Story-like sequence 😢➡️💪➡️😊

class EmojiStyle(Enum):
    """Different emoji expression styles"""
    MINIMALIST = "minimalist"     # Less is more
    EXPRESSIVE = "expressive"     # Rich emotional display
    PLAYFUL = "playful"          # Fun and lighthearted  
    PROFESSIONAL = "professional" # Subtle and appropriate
    MYSTICAL = "mystical"        # Ethereal and magical
    TECHNICAL = "technical"      # Precise and analytical

@dataclass
class EmojiRecommendation:
    """Enhanced emoji recommendation with RoBERTa intelligence"""
    # Core recommendation
    primary_emoji: str
    confidence: float
    
    # Multi-emotion support
    secondary_emojis: List[str]
    emotion_map: Dict[str, str]  # emotion -> emoji
    complexity: EmojiComplexity
    
    # Context intelligence  
    appropriateness_score: float
    timing_recommendation: str  # "immediate", "delayed", "optional"
    character_alignment: float
    
    # RoBERTa insights
    detected_emotions: Dict[str, float]
    roberta_confidence: float
    contextual_relevance: float
    
    # Metadata
    reasoning: str
    fallback_options: List[str]

@dataclass
class EmojiPatternMatch:
    """Historical emoji pattern matching result"""
    pattern_similarity: float
    historical_emojis: List[str]
    success_rate: float
    usage_context: str

class RoBERTaVectorEmojiIntelligence:
    """
    Advanced emoji intelligence using RoBERTa + vector similarity
    """
    
    def __init__(self, memory_manager=None, character_style: EmojiStyle = EmojiStyle.EXPRESSIVE):
        self.memory_manager = memory_manager
        self.character_style = character_style
        self.emotion_analyzer = EnhancedVectorEmotionAnalyzer(memory_manager)
        self.emoji_mapper = EmojiEmotionMapper()
        
        # Enhanced emoji mappings with RoBERTa insights
        self._initialize_enhanced_mappings()
        
        # Initialize style config in __init__
        self.style_config = {}  # Will be set by _apply_character_style_mappings
        
        # Statistics tracking
        self.stats = {
            "recommendations_generated": 0,
            "roberta_successes": 0,
            "multi_emotion_detections": 0,
            "pattern_matches": 0,
            "average_confidence": 0.0
        }
        
        logger.info("RoBERTa Vector Emoji Intelligence initialized with %s style", 
                   character_style.value)
    
    def _initialize_enhanced_mappings(self):
        """Initialize enhanced emoji mappings for RoBERTa emotions"""
        # Core emotion → emoji mappings
        self.emotion_emoji_map = {
            # Primary emotions
            'joy': ['😊', '😄', '🌟', '✨', '🎉', '💖'],
            'sadness': ['😢', '😞', '💔', '🌧️', '😔', '🥺'],
            'anger': ['😠', '😡', '💢', '🔥', '⚡', '😤'],
            'fear': ['😰', '😨', '😱', '🌪️', '⚠️', '😟'],
            'disgust': ['🤢', '😵‍💫', '🙄', '😬', '🤐', '😒'],
            'surprise': ['😲', '🤯', '😮', '✨', '🎆', '🔥'],
            'anticipation': ['🤔', '🔮', '⏳', '🚀', '🌅', '✨'],
            'trust': ['🤝', '💙', '🛡️', '🕊️', '💎', '⭐'],
            
            # Complex emotions (RoBERTa specialty)
            'excitement': ['🚀', '⚡', '🎆', '🔥', '🌟', '💥'],
            'confusion': ['🤔', '😵‍💫', '🌀', '❓', '🤷', '😅'],
            'determination': ['💪', '⚡', '🔥', '🎯', '🚀', '⭐'],
            'relief': ['😌', '💨', '🌤️', '✨', '😊', '🙏'],
            'nostalgia': ['🌅', '📸', '💭', '🕰️', '🌸', '✨'],
            'curiosity': ['🔍', '🤔', '❓', '🌟', '🔮', '👀'],
            'empathy': ['💙', '🤗', '🌺', '🕊️', '💖', '✨'],
            'gratitude': ['🙏', '💖', '🌟', '✨', '🌺', '💎']
        }
        
        # Character-specific style adjustments
        self._apply_character_style_mappings()
        
        # Multi-emotion combination patterns
        self.combination_patterns = {
            ('joy', 'anticipation'): ['😊🚀', '🌟✨', '💖🎉'],
            ('sadness', 'hope'): ['😢🌅', '💔➡️💖', '🌧️🌈'],
            ('fear', 'determination'): ['😰💪', '⚠️🔥', '😟➡️💪'],
            ('anger', 'resolve'): ['😠⚡', '💢🎯', '😡➡️💪'],
            ('confusion', 'curiosity'): ['🤔🔍', '😵‍💫❓', '🌀🔮'],
            ('gratitude', 'joy'): ['🙏😊', '💖🌟', '✨💙'],
            ('surprise', 'delight'): ['😲✨', '🤯🎉', '😮💖'],
            ('trust', 'warmth'): ['🤝💙', '🛡️🌺', '💎💖']
        }
    
    def _apply_character_style_mappings(self):
        """Apply character-specific emoji style preferences"""
        style_preferences = {
            EmojiStyle.MINIMALIST: {
                'preferred_count': 1,
                'avoid_patterns': ['🎉', '💥', '🔥'],
                'prefer_simple': True
            },
            EmojiStyle.EXPRESSIVE: {
                'preferred_count': 2,
                'boost_emotions': ['joy', 'excitement', 'love'],
                'prefer_vivid': True
            },
            EmojiStyle.PLAYFUL: {
                'preferred_count': 2,
                'boost_patterns': ['✨', '🌟', '🎉', '🦄'],
                'prefer_fun': True
            },
            EmojiStyle.PROFESSIONAL: {
                'preferred_count': 1,
                'avoid_patterns': ['🦄', '👻', '🤪'],
                'prefer_subtle': True
            },
            EmojiStyle.MYSTICAL: {
                'preferred_count': 2,
                'boost_patterns': ['🔮', '✨', '🌟', '🌙', '⭐'],
                'prefer_ethereal': True
            },
            EmojiStyle.TECHNICAL: {
                'preferred_count': 1,
                'boost_patterns': ['⚡', '🔧', '⚙️', '🎯', '📊'],
                'prefer_precise': True
            }
        }
        
        self.style_config = style_preferences.get(self.character_style, 
                                                style_preferences[EmojiStyle.EXPRESSIVE])
    
    async def generate_emoji_recommendation(
        self,
        message: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[str]] = None  # Reserved for future context analysis
    ) -> EmojiRecommendation:
        """
        Generate intelligent emoji recommendation using RoBERTa + vector analysis
        
        Args:
            message: The message to generate emoji reaction for
            user_id: User identifier for personalization
            context: Additional context information
            conversation_history: Recent conversation for context
            
        Returns:
            EmojiRecommendation with RoBERTa-powered insights
        """
        try:
            logger.debug("Generating RoBERTa emoji recommendation for message: %s", 
                        message[:50] + "..." if len(message) > 50 else message)
            
            # Step 1: RoBERTa emotion analysis
            emotion_result = await self.emotion_analyzer.analyze_emotion(
                message, user_id=user_id
            )
            
            # Step 2: Vector similarity search for patterns
            pattern_match = await self._find_similar_emoji_patterns(
                message, user_id, conversation_history
            )
            
            # Step 3: Multi-emotion detection and mapping
            emoji_candidates = await self._generate_emotion_based_emojis(
                emotion_result, pattern_match
            )
            
            # Step 4: Context and appropriateness analysis
            appropriateness = self._analyze_context_appropriateness(
                message, context, emoji_candidates
            )
            
            # Step 5: Character style adaptation
            final_recommendation = self._apply_character_style_filtering(
                emoji_candidates, emotion_result, appropriateness
            )
            
            # Step 6: Generate comprehensive recommendation
            recommendation = self._create_emoji_recommendation(
                final_recommendation, emotion_result, pattern_match, appropriateness
            )
            
            self._update_stats(recommendation)
            
            return recommendation
            
        except (ImportError, RuntimeError, ValueError) as e:
            logger.warning("RoBERTa emoji analysis failed, using fallback: %s", str(e))
            return await self._fallback_emoji_recommendation(message, user_id)
    
    async def _find_similar_emoji_patterns(
        self,
        message: str,
        user_id: str,
        conversation_history: Optional[List[str]] = None
    ) -> Optional[EmojiPatternMatch]:
        """
        Find similar historical emoji patterns using vector similarity
        """
        try:
            if not self.memory_manager:
                return None
            
            # Search for similar messages and their emoji reactions
            similar_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=message,
                limit=10
            )
            
            # Extract emoji patterns from similar conversations
            emoji_patterns = []
            for memory in similar_memories:
                content = memory.get('content', '')
                # Look for emoji patterns in historical responses
                emojis = self._extract_emojis_from_text(content)
                if emojis:
                    emoji_patterns.append({
                        'emojis': emojis,
                        'similarity': memory.get('similarity_score', 0.0),
                        'context': content
                    })
            
            if not emoji_patterns:
                return None
            
            # Find the best pattern match
            best_match = max(emoji_patterns, key=lambda x: x['similarity'])
            
            return EmojiPatternMatch(
                pattern_similarity=best_match['similarity'],
                historical_emojis=best_match['emojis'],
                success_rate=0.8,  # Could track actual success rates
                usage_context=best_match['context'][:100]
            )
            
        except (ImportError, RuntimeError, ValueError) as e:
            logger.warning("Vector pattern search failed: %s", str(e))
            return None
    
    async def _generate_emotion_based_emojis(
        self,
        emotion_result: Any,  # EmotionAnalysisResult
        pattern_match: Optional[EmojiPatternMatch]
    ) -> Dict[str, Any]:
        """
        Generate emoji candidates based on RoBERTa emotion analysis
        """
        candidates = {
            'primary_emojis': [],
            'secondary_emojis': [],
            'combination_emojis': [],
            'pattern_emojis': []
        }
        
        # Primary emotion mapping
        primary_emotion = emotion_result.primary_emotion
        if primary_emotion in self.emotion_emoji_map:
            candidates['primary_emojis'] = self.emotion_emoji_map[primary_emotion][:3]
        
        # Multi-emotion analysis
        all_emotions = emotion_result.all_emotions
        if len(all_emotions) > 1:
            # Get top 3 emotions
            sorted_emotions = sorted(
                all_emotions.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            
            for emotion, intensity in sorted_emotions[1:]:  # Skip primary
                if emotion in self.emotion_emoji_map and intensity > 0.3:
                    candidates['secondary_emojis'].extend(
                        self.emotion_emoji_map[emotion][:2]
                    )
            
            # Check for emotion combinations
            emotion_pair = (sorted_emotions[0][0], sorted_emotions[1][0])
            if emotion_pair in self.combination_patterns:
                candidates['combination_emojis'] = self.combination_patterns[emotion_pair]
        
        # Historical pattern integration
        if pattern_match and pattern_match.pattern_similarity > 0.7:
            candidates['pattern_emojis'] = pattern_match.historical_emojis
        
        return candidates
    
    def _analyze_context_appropriateness(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        candidates: Dict[str, Any]  # Reserved for future candidate-specific analysis
    ) -> float:
        """
        Analyze appropriateness of emoji reactions in context
        """
        base_score = 0.8
        
        # Message length considerations
        if len(message) > 500:
            base_score -= 0.1  # Long messages might need less emoji
        
        # Emotional intensity considerations
        high_intensity_indicators = ['!!!', 'VERY', 'EXTREMELY', 'SO']
        if any(indicator in message.upper() for indicator in high_intensity_indicators):
            base_score += 0.1  # High intensity messages welcome emoji reactions
        
        # Question vs statement
        if '?' in message:
            base_score -= 0.05  # Questions might need more thoughtful responses
        
        # Context-specific adjustments
        if context:
            conversation_type = context.get('conversation_type', 'casual')
            if conversation_type == 'serious':
                base_score -= 0.2
            elif conversation_type == 'playful':
                base_score += 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def _apply_character_style_filtering(
        self,
        candidates: Dict[str, Any],
        emotion_result: Any,
        appropriateness: float  # Reserved for future appropriateness-based filtering
    ) -> Dict[str, Any]:
        """
        Apply character-specific style filtering to emoji candidates
        """
        filtered = {
            'primary': [],
            'secondary': [],
            'combinations': []
        }
        
        style_config = self.style_config
        
        # Filter primary emojis by style
        primary_candidates = candidates.get('primary_emojis', [])
        for emoji in primary_candidates:
            if self._emoji_matches_style(emoji, style_config):
                filtered['primary'].append(emoji)
        
        # Handle multi-emotion based on complexity preference
        if emotion_result.confidence > 0.7 and len(emotion_result.all_emotions) > 1:
            # Multi-emotion scenario
            secondary_candidates = candidates.get('secondary_emojis', [])
            combination_candidates = candidates.get('combination_emojis', [])
            
            if style_config.get('preferred_count', 1) > 1:
                # Character likes expressive emojis
                filtered['secondary'] = [
                    emoji for emoji in secondary_candidates[:2] 
                    if self._emoji_matches_style(emoji, style_config)
                ]
                filtered['combinations'] = combination_candidates[:1]
        
        return filtered
    
    def _emoji_matches_style(self, emoji: str, style_config: Dict[str, Any]) -> bool:
        """Check if emoji matches character style preferences"""
        avoid_patterns = style_config.get('avoid_patterns', [])
        boost_patterns = style_config.get('boost_patterns', [])
        
        # Avoid certain emojis for this style
        if emoji in avoid_patterns:
            return False
        
        # Boost preferred emojis
        if emoji in boost_patterns:
            return True
        
        # Default acceptance
        return True
    
    def _create_emoji_recommendation(
        self,
        filtered_candidates: Dict[str, Any],
        emotion_result: Any,
        pattern_match: Optional[EmojiPatternMatch],
        appropriateness: float
    ) -> EmojiRecommendation:
        """Create comprehensive emoji recommendation"""
        
        # Select primary emoji
        primary_candidates = filtered_candidates.get('primary', [])
        if primary_candidates:
            primary_emoji = primary_candidates[0]
            confidence = emotion_result.confidence * 0.8 + appropriateness * 0.2
        else:
            primary_emoji = "😊"  # Fallback
            confidence = 0.5
        
        # Select secondary emojis
        secondary_emojis = []
        if len(emotion_result.all_emotions) > 1:
            secondary_candidates = filtered_candidates.get('secondary', [])
            combination_candidates = filtered_candidates.get('combinations', [])
            
            if combination_candidates and confidence > 0.7:
                # Use combination for high confidence multi-emotion
                combo = combination_candidates[0]
                secondary_emojis = combo.split()[1:] if ' ' in combo else list(combo[1:])
            elif secondary_candidates:
                secondary_emojis = secondary_candidates[:1]
        
        # Determine complexity
        complexity = EmojiComplexity.SIMPLE
        if secondary_emojis:
            if len(secondary_emojis) > 1:
                complexity = EmojiComplexity.COMPLEX
            else:
                complexity = EmojiComplexity.COMPOUND
        
        # Create emotion mapping
        emotion_map = {emotion_result.primary_emotion: primary_emoji}
        if secondary_emojis and len(emotion_result.all_emotions) > 1:
            sorted_emotions = sorted(
                emotion_result.all_emotions.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for i, emoji in enumerate(secondary_emojis):
                if i + 1 < len(sorted_emotions):
                    emotion_map[sorted_emotions[i + 1][0]] = emoji
        
        # Determine timing
        timing = "immediate"
        if confidence < 0.5:
            timing = "optional"
        elif appropriateness < 0.6:
            timing = "delayed"
        
        # Character alignment score
        character_alignment = self._calculate_character_alignment(
            primary_emoji, secondary_emojis, emotion_result
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            emotion_result, pattern_match, confidence, complexity
        )
        
        # Create fallback options
        fallback_options = self._generate_fallback_options(emotion_result)
        
        return EmojiRecommendation(
            primary_emoji=primary_emoji,
            confidence=confidence,
            secondary_emojis=secondary_emojis,
            emotion_map=emotion_map,
            complexity=complexity,
            appropriateness_score=appropriateness,
            timing_recommendation=timing,
            character_alignment=character_alignment,
            detected_emotions=dict(emotion_result.all_emotions),
            roberta_confidence=emotion_result.confidence,
            contextual_relevance=pattern_match.pattern_similarity if pattern_match else 0.0,
            reasoning=reasoning,
            fallback_options=fallback_options
        )
    
    def _calculate_character_alignment(
        self,
        primary_emoji: str,
        secondary_emojis: List[str],
        emotion_result: Any
    ) -> float:
        """Calculate how well emojis align with character style"""
        base_alignment = 0.7
        
        # Boost for style-preferred emojis
        boost_patterns = self.style_config.get('boost_patterns', [])
        if primary_emoji in boost_patterns:
            base_alignment += 0.2
        
        for emoji in secondary_emojis:
            if emoji in boost_patterns:
                base_alignment += 0.1
        
        # Adjust for emotion confidence
        if emotion_result.confidence > 0.8:
            base_alignment += 0.1
        
        return min(1.0, base_alignment)
    
    def _generate_reasoning(
        self,
        emotion_result: Any,
        pattern_match: Optional[EmojiPatternMatch],
        confidence: float,
        complexity: EmojiComplexity  # Reserved for future complexity-based reasoning
    ) -> str:
        """Generate human-readable reasoning for emoji recommendation"""
        reasons = []
        
        # Emotion-based reasoning
        primary_emotion = emotion_result.primary_emotion
        reasons.append(f"Primary emotion '{primary_emotion}' detected with {emotion_result.confidence:.1%} confidence")
        
        if len(emotion_result.all_emotions) > 1:
            reasons.append(f"Multi-emotion state detected ({len(emotion_result.all_emotions)} emotions)")
        
        # Pattern-based reasoning
        if pattern_match and pattern_match.pattern_similarity > 0.7:
            reasons.append(f"Similar historical pattern found (similarity: {pattern_match.pattern_similarity:.1%})")
        
        # Style reasoning
        reasons.append(f"Adapted for {self.character_style.value} character style")
        
        # Confidence reasoning
        if confidence > 0.8:
            reasons.append("High confidence recommendation")
        elif confidence < 0.5:
            reasons.append("Low confidence, consider fallback options")
        
        return "; ".join(reasons)
    
    def _generate_fallback_options(self, emotion_result: Any) -> List[str]:
        """Generate fallback emoji options"""
        fallbacks = []
        
        # Always include neutral options
        fallbacks.extend(['😊', '👍', '💙'])
        
        # Add emotion-specific fallbacks
        primary_emotion = emotion_result.primary_emotion
        if primary_emotion in self.emotion_emoji_map:
            fallbacks.extend(self.emotion_emoji_map[primary_emotion][1:3])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_fallbacks = []
        for emoji in fallbacks:
            if emoji not in seen:
                seen.add(emoji)
                unique_fallbacks.append(emoji)
        
        return unique_fallbacks[:5]  # Limit to 5 fallback options
    
    def _extract_emojis_from_text(self, text: str) -> List[str]:
        """Extract emojis from text (simplified implementation)"""
        import re
        # This is a simplified emoji extraction - could be enhanced
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+", flags=re.UNICODE
        )
        return emoji_pattern.findall(text)
    
    def _update_stats(self, recommendation: EmojiRecommendation):
        """Update emoji intelligence statistics"""
        self.stats["recommendations_generated"] += 1
        
        if recommendation.roberta_confidence > 0.7:
            self.stats["roberta_successes"] += 1
        
        if len(recommendation.detected_emotions) > 1:
            self.stats["multi_emotion_detections"] += 1
        
        if recommendation.contextual_relevance > 0.7:
            self.stats["pattern_matches"] += 1
        
        # Update rolling average confidence
        current_avg = self.stats["average_confidence"]
        total = self.stats["recommendations_generated"]
        self.stats["average_confidence"] = (
            current_avg * (total - 1) + recommendation.confidence
        ) / total
    
    async def _fallback_emoji_recommendation(
        self,
        message: str,
        user_id: str
    ) -> EmojiRecommendation:
        """Fallback emoji recommendation using simple keyword analysis"""
        logger.warning("Using fallback emoji recommendation for user %s", user_id)
        
        # Simple keyword-based emotion detection
        fallback_emotions = {
            'happy': ['😊', 'joy'],
            'sad': ['😢', 'sadness'], 
            'angry': ['😠', 'anger'],
            'excited': ['🎉', 'excitement'],
            'confused': ['🤔', 'confusion'],
            'thanks': ['🙏', 'gratitude']
        }
        
        message_lower = message.lower()
        detected_emotion = 'neutral'
        primary_emoji = '😊'
        
        for keyword, (emoji, emotion) in fallback_emotions.items():
            if keyword in message_lower:
                detected_emotion = emotion
                primary_emoji = emoji
                break
        
        return EmojiRecommendation(
            primary_emoji=primary_emoji,
            confidence=0.4,
            secondary_emojis=[],
            emotion_map={detected_emotion: primary_emoji},
            complexity=EmojiComplexity.SIMPLE,
            appropriateness_score=0.7,
            timing_recommendation="optional",
            character_alignment=0.6,
            detected_emotions={detected_emotion: 0.5},
            roberta_confidence=0.0,
            contextual_relevance=0.0,
            reasoning="Fallback keyword-based detection",
            fallback_options=['👍', '💙', '✨']
        )
    
    # Utility methods
    async def get_emoji_statistics(self) -> Dict[str, Any]:
        """Get emoji intelligence statistics"""
        return {
            **self.stats,
            "character_style": self.character_style.value,
            "roberta_success_rate": (
                self.stats["roberta_successes"] / max(1, self.stats["recommendations_generated"])
            ),
            "multi_emotion_rate": (
                self.stats["multi_emotion_detections"] / max(1, self.stats["recommendations_generated"])
            )
        }
    
    async def suggest_emoji_for_conversation_summary(
        self,
        conversation_summary: str,
        emotional_arc: Dict[str, Any]
    ) -> List[str]:
        """
        Suggest emojis for conversation summaries using emotional arc data
        """
        try:
            # Analyze summary emotions
            emotion_result = await self.emotion_analyzer.analyze_emotion(
                conversation_summary, user_id="summary_emoji_generator"
            )
            
            # Get dominant emotions from arc
            timeline = emotional_arc.get('timeline', [])
            if timeline:
                start_emotion = timeline[0].get('primary', 'neutral')
                end_emotion = timeline[-1].get('primary', 'neutral')
                
                # Create progression emojis
                start_emoji = self.emotion_emoji_map.get(start_emotion, ['😐'])[0]
                end_emoji = self.emotion_emoji_map.get(end_emotion, ['😐'])[0]
                
                if start_emotion != end_emotion:
                    return [start_emoji, '➡️', end_emoji]
                else:
                    # Consistent emotion throughout
                    primary_emojis = self.emotion_emoji_map.get(start_emotion, ['😐'])
                    return primary_emojis[:2]
            
            # Fallback to primary emotion
            primary_emotion = emotion_result.primary_emotion
            return self.emotion_emoji_map.get(primary_emotion, ['😊'])[:2]
            
        except (ImportError, RuntimeError, ValueError) as e:
            logger.warning("Summary emoji suggestion failed: %s", str(e))
            return ['📝', '💭']  # Default summary emojis

# Factory function for easy integration
def create_roberta_vector_emoji_intelligence(
    memory_manager=None,
    character_style: EmojiStyle = EmojiStyle.EXPRESSIVE
) -> RoBERTaVectorEmojiIntelligence:
    """Factory function to create RoBERTa vector emoji intelligence"""
    return RoBERTaVectorEmojiIntelligence(memory_manager, character_style)