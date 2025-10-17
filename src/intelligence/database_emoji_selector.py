"""
Database-Driven Emoji Selector for WhisperEngine
=================================================

Intelligent emoji selection using:
- Character personality from PostgreSQL database (frequency, style, placement)
- RoBERTa bot emotion analysis (Phase 7.5 - what bot feels in response)
- User emotion context (Phase 2 - appropriateness filter)
- Universal Emotion Taxonomy for consistent mapping
- Character-specific emoji patterns from database
- Sentiment analysis and topic detection

Design Principles:
1. Emojis express BOT emotion (primary), moderated by user context
2. All character logic from database (no hardcoded personalities)
3. Handles RoBERTa neutral bias for long text (>500 chars)
4. Uses UniversalEmotionTaxonomy for emotion→emoji mapping

Pipeline Integration:
- Phase 7.6 in message_processor.py
- Post-LLM emoji decoration (after bot emotion analysis)
- Before memory storage (decorated response is what gets stored)
"""

import logging
import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from src.intelligence.emotion_taxonomy import UniversalEmotionTaxonomy

logger = logging.getLogger(__name__)


@dataclass
class EmojiSelection:
    """Result of emoji selection process."""
    emojis: List[str]  # Selected emojis (1-3 perfect choices)
    placement: str  # Where to place: end_of_message, integrated_throughout, etc.
    should_use: bool  # Whether to use emojis (respects frequency dial)
    reasoning: str  # Debug info: why these emojis were selected
    source: str  # 'database', 'taxonomy', 'fallback'


class DatabaseEmojiSelector:
    """
    Intelligent emoji selection using database-driven character personalities
    and RoBERTa emotion analysis.
    """
    
    # Emotion → emoji pattern category mapping
    EMOTION_TO_CATEGORY_MAP = {
        'joy': ['excitement_level', 'celebration', 'affection_warmth'],
        'sadness': ['concern', 'affection_warmth'],
        'anger': ['concern'],
        'fear': ['concern'],
        'surprise': ['excitement_level'],
        'disgust': ['concern'],
        'neutral': [],  # No specific category - use defaults or topics
        # Extended emotions (mapped to core)
        'love': ['affection_warmth', 'celebration'],
        'excitement': ['excitement_level', 'celebration'],
        'concern': ['concern', 'affection_warmth'],
        'empathy': ['affection_warmth', 'concern'],
        'hope': ['celebration', 'affection_warmth'],
    }
    
    # Frequency → probability mapping
    FREQUENCY_PROBABILITY = {
        'none': 0.0,
        'minimal': 0.10,
        'low': 0.30,
        'moderate': 0.60,
        'high': 0.90,
        'selective_symbolic': 0.20,  # Rare but meaningful
    }
    
    def __init__(self, db_pool):
        """Initialize emoji selector with database connection pool."""
        self.db_pool = db_pool
        self.taxonomy = UniversalEmotionTaxonomy()
    
    def _should_mirror_user_emotion(
        self, 
        user_emotion_data: Dict, 
        bot_emotion_data: Dict
    ) -> bool:
        """
        Determine if we should mirror the user's emotion.
        
        Criteria:
        - User emotion confidence > 0.7 (high confidence detection)
        - User emotion intensity > 0.6 (strong emotional state)
        - Bot emotion similar or empathetic to user emotion
        
        Returns True if emotion mirroring is appropriate.
        """
        user_emotion = user_emotion_data.get('primary_emotion')
        user_confidence = user_emotion_data.get('confidence', 0.0)
        user_intensity = user_emotion_data.get('intensity', 0.0)
        bot_emotion = bot_emotion_data.get('primary_emotion')
        
        # Require high confidence and intensity
        if user_confidence <= 0.7 or user_intensity <= 0.6:
            return False
        
        # Mirror if emotions align or bot is responding empathetically
        empathetic_pairs = {
            ('sadness', 'concern'),
            ('sadness', 'sadness'),  # Bot shares user's sadness
            ('fear', 'concern'),
            ('fear', 'fear'),        # Bot acknowledges user's fear
            ('anger', 'concern'),
            ('anger', 'anger'),      # Bot validates user's anger
            ('joy', 'joy'),          # Bot shares user's joy
            ('excitement', 'joy'),
            ('excitement', 'excitement'),
        }
        
        return (user_emotion, bot_emotion) in empathetic_pairs or user_emotion == bot_emotion
    
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
            'excitement': {
                'high': '🤩',      # Star-struck for intense excitement
                'medium': '😃',    # Grinning face for moderate excitement
                'low': '🙂'        # Slightly smiling for mild excitement
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
    
    async def select_emojis(
        self,
        character_name: str,
        bot_emotion_data: Dict,
        user_emotion_data: Optional[Dict] = None,
        detected_topics: Optional[List[str]] = None,
        response_type: Optional[str] = None,
        message_content: str = "",
        sentiment: Optional[float] = None
    ) -> EmojiSelection:
        """
        Select perfect emojis for bot response using intelligent multi-factor analysis.
        
        Args:
            character_name: Normalized character name (e.g., 'elena', 'dream')
            bot_emotion_data: RoBERTa analysis of bot's response emotion (Phase 7.5)
            user_emotion_data: RoBERTa analysis of user's message emotion (Phase 2)
            detected_topics: Keyword matches from message (e.g., ['ocean_marine_life'])
            response_type: Type of response (greeting, teaching, concern, celebration)
            message_content: The bot's response text
            sentiment: Sentiment score (-1 to 1)
        
        Returns:
            EmojiSelection with emojis, placement, and selection reasoning
        """
        try:
            # Step 1: Get character emoji personality from database
            character_config = await self._get_character_emoji_config(character_name)
            
            if not character_config:
                logger.warning(f"No emoji config found for character: {character_name}")
                return EmojiSelection(
                    emojis=[],
                    placement='end_of_message',
                    should_use=False,
                    reasoning="Character not found in database",
                    source='none'
                )
            
            # Step 2: Check frequency dial (should we use emojis at all?)
            frequency = character_config['emoji_frequency']
            probability = self.FREQUENCY_PROBABILITY.get(frequency, 0.6)
            
            # For selective_symbolic, higher intensity = higher probability
            if frequency == 'selective_symbolic' and bot_emotion_data:
                intensity = bot_emotion_data.get('intensity', 0.5)
                if intensity > 0.7:
                    probability = 0.6  # Boost for high intensity moments
            
            if random.random() > probability:
                return EmojiSelection(
                    emojis=[],
                    placement=character_config['emoji_placement'],
                    should_use=False,
                    reasoning=f"Frequency dial '{frequency}' - not using emojis this time",
                    source='frequency_skip'
                )
            
            # Step 3: Handle RoBERTa neutral bias (long text defaults to neutral)
            bot_emotion = bot_emotion_data.get('primary_emotion', 'neutral')
            is_false_neutral = (
                bot_emotion == 'neutral' 
                and len(message_content) > 500
                and bot_emotion_data.get('confidence', 1.0) < 0.6
            )
            
            if is_false_neutral:
                logger.debug(f"Detected false neutral (length: {len(message_content)} chars) - using fallback strategy")
                # Use sentiment + response_type + topics instead
                bot_emotion = await self._infer_emotion_from_context(
                    sentiment=sentiment,
                    response_type=response_type,
                    user_emotion_data=user_emotion_data,
                    detected_topics=detected_topics
                )
            
            # Step 4: Check user emotion for appropriateness filter
            # CRITICAL: Prevent celebratory/excited emojis when user is in emotional distress
            if user_emotion_data:
                user_emotion = user_emotion_data.get('primary_emotion')
                user_intensity = user_emotion_data.get('intensity', 0.5)
                
                # Detect user in distress: high intensity negative emotions
                if user_emotion in ['sadness', 'fear', 'anger'] and user_intensity > 0.6:
                    logger.debug(
                        "⚠️ User in emotional distress: %s (intensity: %.2f)",
                        user_emotion, user_intensity
                    )
                    
                    # Switch bot emotion from upbeat → empathetic
                    if bot_emotion in ['joy', 'excitement', 'surprise']:
                        logger.debug(
                            "Filtering out %s emojis - switching to concern",
                            bot_emotion
                        )
                        bot_emotion = 'concern'  # Switch to empathetic emojis
                    
                    # Filter out upbeat topics/response_types that would inject celebration emojis
                    if response_type in ['celebration', 'greeting']:
                        logger.debug(
                            "Neutralizing response_type '%s' due to user distress",
                            response_type
                        )
                        response_type = 'concern'  # Override to empathetic response
                    
                    # Filter out upbeat topics (spanish_expressions, science_discovery)
                    upbeat_topics = ['spanish_expressions', 'science_discovery', 'celebration']
                    detected_topics = [t for t in (detected_topics or []) if t not in upbeat_topics]
            
            # 🎭 EMOTION MIRRORING: If bot emotion matches user emotion with high confidence, mirror it
            # This provides empathetic validation and emotional resonance
            if user_emotion_data and self._should_mirror_user_emotion(user_emotion_data, bot_emotion_data):
                user_emotion = user_emotion_data.get('primary_emotion')
                user_intensity = user_emotion_data.get('intensity', 0.5)
                user_confidence = user_emotion_data.get('confidence', 0.0)
                
                mirroring_emoji = self._get_emotion_mirroring_emoji(user_emotion, user_intensity)
                if mirroring_emoji:
                    logger.info(
                        "🎭 LLM Response Emotion Mirroring: user_emotion=%s, intensity=%.2f, confidence=%.2f, emoji=%s",
                        user_emotion, user_intensity, user_confidence, mirroring_emoji
                    )
                    # Return mirroring emoji directly - highest priority
                    return EmojiSelection(
                        emojis=[mirroring_emoji],
                        placement=character_config['emoji_placement'],
                        should_use=True,
                        reasoning=f"emotion_mirroring: user={user_emotion}, intensity={user_intensity:.2f}, confidence={user_confidence:.2f}",
                        source='emotion_mirroring'
                    )
            
            # Step 5: Query database for relevant emoji patterns
            emoji_patterns = await self._query_emoji_patterns(
                character_name=character_name,
                emotion=bot_emotion,
                intensity=bot_emotion_data.get('intensity', 0.5),
                topics=detected_topics or [],
                response_type=response_type
            )
            
            # Step 6: Select emojis from patterns with multi-factor intelligence
            if emoji_patterns:
                selected_emojis = self._select_from_patterns(
                    emoji_patterns,
                    intensity=bot_emotion_data.get('intensity', 0.5),
                    combination_style=character_config['emoji_combination'],
                    bot_emotion_data=bot_emotion_data,
                    user_emotion_data=user_emotion_data
                )
                source = 'database'
                reasoning = f"bot emotion='{bot_emotion}', patterns={len(emoji_patterns)}, intensity={bot_emotion_data.get('intensity', 0.5):.2f}"
            else:
                # Fallback to taxonomy with proper confidence
                selected_emojis = self._fallback_to_taxonomy(
                    emotion=bot_emotion,
                    character_name=character_name,
                    bot_emotion_data=bot_emotion_data
                )
                source = 'taxonomy'
                reasoning = f"bot emotion='{bot_emotion}' (taxonomy fallback)"
            
            return EmojiSelection(
                emojis=selected_emojis,
                placement=character_config['emoji_placement'],
                should_use=True,
                reasoning=reasoning,
                source=source
            )
        
        except Exception as e:
            logger.error(f"Error selecting emojis for {character_name}: {e}", exc_info=True)
            return EmojiSelection(
                emojis=[],
                placement='end_of_message',
                should_use=False,
                reasoning=f"Error: {str(e)}",
                source='error'
            )
    
    async def _get_character_emoji_config(self, character_name: str) -> Optional[Dict]:
        """Get character's emoji personality configuration from database."""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT 
                        emoji_frequency,
                        emoji_style,
                        emoji_combination,
                        emoji_placement,
                        emoji_age_demographic,
                        emoji_cultural_influence
                    FROM characters
                    WHERE normalized_name = $1
                """, character_name)
                
                if result:
                    return dict(result)
                return None
        except Exception as e:
            logger.error(f"Error fetching character emoji config: {e}")
            return None
    
    async def _query_emoji_patterns(
        self,
        character_name: str,
        emotion: str,
        intensity: float,
        topics: List[str],
        response_type: Optional[str]
    ) -> List[Dict]:
        """Query database for relevant emoji patterns."""
        try:
            async with self.db_pool.acquire() as conn:
                # Get character ID first
                char_result = await conn.fetchrow(
                    "SELECT id FROM characters WHERE normalized_name = $1",
                    character_name
                )
                
                if not char_result:
                    return []
                
                character_id = char_result['id']
                
                # Map emotion to categories
                categories = self.EMOTION_TO_CATEGORY_MAP.get(emotion, [])
                
                # Build query for matching patterns
                patterns = []
                
                # Priority 1: response_type match
                if response_type:
                    result = await conn.fetch("""
                        SELECT emoji_sequence, pattern_name, pattern_category, usage_context
                        FROM character_emoji_patterns
                        WHERE character_id = $1
                        AND pattern_category = 'response_type'
                        AND pattern_name = $2
                        LIMIT 1
                    """, character_id, response_type)
                    patterns.extend([dict(r) for r in result])
                
                # Priority 2: topic_specific match
                if topics:
                    result = await conn.fetch("""
                        SELECT emoji_sequence, pattern_name, pattern_category, usage_context
                        FROM character_emoji_patterns
                        WHERE character_id = $1
                        AND pattern_category = 'topic_specific'
                        AND pattern_name = ANY($2::text[])
                        LIMIT 2
                    """, character_id, topics)
                    patterns.extend([dict(r) for r in result])
                
                # Priority 3: excitement_level based on intensity
                if categories and 'excitement_level' in categories:
                    # Map intensity to excitement level
                    if intensity > 0.7:
                        level_name = 'excitement_high'
                    elif intensity > 0.4:
                        level_name = 'excitement_medium'
                    else:
                        level_name = 'excitement_low'
                    
                    result = await conn.fetch("""
                        SELECT emoji_sequence, pattern_name, pattern_category, usage_context
                        FROM character_emoji_patterns
                        WHERE character_id = $1
                        AND pattern_category = 'excitement_level'
                        AND pattern_name = $2
                        LIMIT 1
                    """, character_id, level_name)
                    patterns.extend([dict(r) for r in result])
                
                # Priority 4: Other emotion-based categories
                for category in categories:
                    if category != 'excitement_level':
                        result = await conn.fetch("""
                            SELECT emoji_sequence, pattern_name, pattern_category, usage_context
                            FROM character_emoji_patterns
                            WHERE character_id = $1
                            AND pattern_category = $2
                            LIMIT 1
                        """, character_id, category)
                        patterns.extend([dict(r) for r in result])
                
                return patterns
        
        except Exception as e:
            logger.error(f"Error querying emoji patterns: {e}")
            return []
    
    def _calculate_emotionally_intelligent_emoji_count(
        self,
        intensity: float,
        combination_style: str,
        bot_emotion_data: Dict,
        user_emotion_data: Optional[Dict] = None
    ) -> int:
        """
        🎯 EMOTIONAL INTELLIGENCE: Multi-factor emoji count selection.
        
        Considers:
        - Emotional intensity (how strong the emotion)
        - RoBERTa confidence (how certain we are)
        - Emotional variance (emotion stability)
        - User preferences (would be integrated when available)
        - Character personality (combination_style)
        
        Args:
            intensity: Bot emotion intensity (0.0-1.0)
            combination_style: Character's emoji combination preference
            bot_emotion_data: Full RoBERTa analysis with confidence, variance, etc.
            user_emotion_data: Optional user emotion data for context
        
        Returns:
            Optimal emoji count (1-3)
        """
        # Factor 1: Base count from intensity (existing logic)
        if intensity > 0.8:
            base_count = 3
        elif intensity > 0.5:
            base_count = 2
        else:
            base_count = 1
        
        # Factor 2: Confidence boost
        # High confidence in emotion detection = more expressive
        confidence = bot_emotion_data.get('confidence', 0.5)
        if confidence > 0.85 and base_count < 3:
            base_count += 1
            logger.debug(
                "🎯 Emoji count boost: high confidence (%.2f) increased count to %d",
                confidence, base_count
            )
        
        # Factor 3: Emotional stability (low variance = consistent emotion)
        # If emotion is stable and strong, we can be more expressive
        variance = bot_emotion_data.get('emotional_variance', 0.5)
        if variance < 0.3 and intensity > 0.7 and base_count < 3:
            base_count += 1
            logger.debug(
                "🎯 Emoji count boost: stable strong emotion (variance=%.2f, intensity=%.2f) increased count to %d",
                variance, intensity, base_count
            )
        
        # Factor 4: High variance = reduce expressiveness
        # Unstable emotion = be more conservative
        elif variance > 0.7 and base_count > 1:
            base_count -= 1
            logger.debug(
                "🎯 Emoji count reduction: high variance (%.2f) decreased count to %d",
                variance, base_count
            )
        
        # Factor 5: User emotion context
        # If user in distress with high intensity, be more conservative
        if user_emotion_data:
            user_emotion = user_emotion_data.get('primary_emotion', 'neutral')
            user_intensity = user_emotion_data.get('intensity', 0.5)
            
            if user_emotion in ['sadness', 'fear', 'anger'] and user_intensity > 0.7:
                # High distress = more conservative emoji usage
                base_count = min(base_count, 1)
                logger.debug(
                    "🎯 Emoji count reduction: user in distress (%s, intensity=%.2f) decreased count to %d",
                    user_emotion, user_intensity, base_count
                )
        
        # Factor 6: Character personality constraints (ALWAYS enforced)
        if combination_style == 'minimal_symbolic_emoji':
            return 1  # Override: always minimal
        elif combination_style == 'text_with_accent_emoji':
            return 1  # Override: always single accent
        elif combination_style == 'emoji_only':
            return min(base_count, 2)  # Cap at 2 for emoji-only
        
        # Final cap at 3 emojis maximum
        return min(base_count, 3)
    
    def _select_from_patterns(
        self,
        patterns: List[Dict],
        intensity: float,
        combination_style: str,
        bot_emotion_data: Optional[Dict] = None,
        user_emotion_data: Optional[Dict] = None
    ) -> List[str]:
        """
        Select individual emojis from pattern sequences using multi-factor intelligence.
        
        Enhanced to use emotional confidence, variance, and context rather than
        just raw intensity thresholds.
        """
        if not patterns:
            return []
        
        # Get emoji sequence from first pattern (highest priority)
        emoji_sequence = patterns[0]['emoji_sequence']
        
        # Parse emoji sequence (space-separated or concatenated)
        emojis = self._parse_emoji_sequence(emoji_sequence)
        
        if not emojis:
            return []
        
        # 🎯 NEW: Use multi-factor intelligence for emoji count
        if bot_emotion_data:
            count = self._calculate_emotionally_intelligent_emoji_count(
                intensity=intensity,
                combination_style=combination_style,
                bot_emotion_data=bot_emotion_data,
                user_emotion_data=user_emotion_data
            )
        else:
            # Fallback to original logic if no emotion data
            if combination_style == 'minimal_symbolic_emoji':
                count = 1
            elif combination_style == 'text_with_accent_emoji':
                count = 1
            elif combination_style == 'text_plus_emoji':
                if intensity > 0.8:
                    count = min(3, len(emojis))
                elif intensity > 0.5:
                    count = min(2, len(emojis))
                else:
                    count = 1
            elif combination_style == 'emoji_only':
                count = min(2, len(emojis))
            else:
                count = 1
        
        return emojis[:count]
    
    def _parse_emoji_sequence(self, emoji_sequence: str) -> List[str]:
        """Parse emoji sequence string into individual emojis."""
        # Remove whitespace
        clean_sequence = emoji_sequence.replace(' ', '')
        
        # Extract individual emojis (Unicode emoji characters)
        # This regex matches emoji sequences
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F]|"  # Emoticons
            "[\U0001F300-\U0001F5FF]|"  # Symbols & pictographs
            "[\U0001F680-\U0001F6FF]|"  # Transport & map symbols
            "[\U0001F1E0-\U0001F1FF]|"  # Flags
            "[\U00002702-\U000027B0]|"  # Dingbats
            "[\U000024C2-\U0001F251]"   # Enclosed characters
        )
        
        emojis = emoji_pattern.findall(clean_sequence)
        return emojis
    
    def _fallback_to_taxonomy(
        self,
        emotion: str,
        character_name: str,
        bot_emotion_data: Dict
    ) -> List[str]:
        """
        🎯 CONFIDENCE FIX: Fallback to UniversalEmotionTaxonomy with proper confidence.
        
        BEFORE: Passed intensity as confidence (mislabeled)
        AFTER: Uses actual roberta_confidence + variance adjustment
        
        Args:
            emotion: Emotion label to look up in taxonomy
            character_name: Character name for emoji selection
            bot_emotion_data: Complete emotion analysis with confidence + variance
        
        Returns:
            List of emoji strings (0-1 emojis)
        """
        # Standardize emotion label
        standardized_emotion = self.taxonomy.standardize_emotion_label(emotion)
        
        # Extract actual confidence (not intensity!)
        confidence = bot_emotion_data.get('roberta_confidence', 0.5)
        variance = bot_emotion_data.get('emotional_variance', 0.5)
        
        # Adjust confidence based on emotional variance
        # Low variance (stable emotion) → boost confidence
        # High variance (unstable emotion) → reduce confidence
        adjusted_confidence = confidence
        if variance < 0.3:  # Stable emotion
            adjusted_confidence = min(confidence * 1.1, 1.0)
            logger.debug(
                "📊 Taxonomy: Stable emotion (variance=%.2f) → confidence boosted %.2f → %.2f",
                variance, confidence, adjusted_confidence
            )
        elif variance > 0.7:  # Unstable emotion
            adjusted_confidence = confidence * 0.9
            logger.debug(
                "📊 Taxonomy: Unstable emotion (variance=%.2f) → confidence reduced %.2f → %.2f",
                variance, confidence, adjusted_confidence
            )
        else:
            logger.debug(
                "📊 Taxonomy: Normal variance (%.2f) → confidence unchanged %.2f",
                variance, confidence
            )
        
        # Get emoji from taxonomy with properly adjusted confidence
        emoji = self.taxonomy.roberta_to_emoji_choice(
            roberta_emotion=standardized_emotion,
            character=character_name,
            confidence=adjusted_confidence  # ✅ Now using actual confidence!
        )
        
        if emoji:
            return [emoji]
        
        return []  # No fallback available
    
    async def _infer_emotion_from_context(
        self,
        sentiment: Optional[float],
        response_type: Optional[str],
        user_emotion_data: Optional[Dict],
        detected_topics: Optional[List[str]]
    ) -> str:
        """
        Infer emotion when RoBERTa returns false neutral (due to text length).
        
        Uses: sentiment, response_type, user emotion, and topics to guess
        what emotion the bot is likely expressing.
        """
        # Strategy 1: Use sentiment
        if sentiment is not None:
            if sentiment > 0.3:
                return 'joy'
            elif sentiment < -0.3:
                return 'sadness'
        
        # Strategy 2: Use response_type
        if response_type:
            response_emotion_map = {
                'greeting': 'joy',
                'celebration': 'joy',
                'teaching': 'joy',
                'concern': 'concern',
                'farewell': 'neutral',
            }
            if response_type in response_emotion_map:
                return response_emotion_map[response_type]
        
        # Strategy 3: Mirror user emotion with empathy
        if user_emotion_data:
            user_emotion = user_emotion_data.get('primary_emotion')
            if user_emotion in ['sadness', 'fear', 'anger']:
                return 'concern'  # Empathetic response
            elif user_emotion == 'joy':
                return 'joy'  # Share happiness
        
        # Strategy 4: Default to neutral (real neutral, not false)
        return 'neutral'
    
    def filter_inappropriate_emojis(
        self,
        message: str,
        user_emotion_data: Optional[Dict] = None
    ) -> str:
        """
        Filter out inappropriate emojis from LLM-generated response.
        
        This handles emojis that the LLM itself added (not our decoration).
        Removes celebration/excitement emojis when user is in emotional distress.
        
        Args:
            message: The LLM's response text (may contain emojis)
            user_emotion_data: RoBERTa analysis of user's emotion
        
        Returns:
            Message with inappropriate emojis removed
        """
        if not user_emotion_data:
            return message
        
        user_emotion = user_emotion_data.get('primary_emotion')
        user_intensity = user_emotion_data.get('intensity', 0.5)
        
        # DISABLED: LLM emoji usage is part of personality expression
        # Only emoji REACTIONS are filtered (via vector_emoji_intelligence.py)
        return message
        
        # Original filtering logic kept for reference but disabled:
        # if user_emotion not in ['sadness', 'fear', 'anger'] or user_intensity <= 0.6:
        #     return message
        
        # WHITELIST APPROACH: Define ALLOWED emojis for distress contexts
        # Better to remove celebratory emojis, but ALLOW empathy-mirroring emojis
        # Includes: support emojis + emotion-mirroring emojis (sad faces OK for sad users)
        allowed_empathy_emojis = [
            # Support & care emojis
            '💙',  # Blue heart - empathy
            '💔',  # Broken heart - acknowledgment
            '🙏',  # Praying hands - support
            '❤️',  # Red heart - love/care
            '🫂',  # Hugging face - comfort
            # Empathy-mirroring emojis (reflect user's emotion back)
            '😢',  # Crying face - mirrors sadness
            '😔',  # Pensive face - mirrors contemplation/sadness
            '😞',  # Disappointed face - mirrors disappointment
            '🥺',  # Pleading face - mirrors vulnerability
            '😟',  # Worried face - mirrors concern/worry
            '😥',  # Sad but relieved - mirrors mixed emotions
        ]
        
        # Extract all emojis from message
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F]|"  # Emoticons
            "[\U0001F300-\U0001F5FF]|"  # Symbols & pictographs
            "[\U0001F680-\U0001F6FF]|"  # Transport & map symbols
            "[\U0001F1E0-\U0001F1FF]|"  # Flags
            "[\U00002702-\U000027B0]|"  # Dingbats
            "[\U000024C2-\U0001F251]"   # Enclosed characters
        )
        
        found_emojis = emoji_pattern.findall(message)
        
        # Remove any emoji that's NOT in the allowed list
        filtered_message = message
        for emoji in found_emojis:
            if emoji not in allowed_empathy_emojis:
                filtered_message = filtered_message.replace(emoji, '')
        
        # Clean up extra spaces left by removed emojis
        filtered_message = re.sub(r'\s{2,}', ' ', filtered_message)
        filtered_message = re.sub(r'\s+([,.!?])', r'\1', filtered_message)
        
        if filtered_message != message:
            logger.debug(
                "Filtered inappropriate emojis from LLM response (user in distress: %s, intensity: %.2f)",
                user_emotion, user_intensity
            )
        
        return filtered_message.strip()
    
    def apply_emojis(
        self,
        message: str,
        emojis: List[str],
        placement: str
    ) -> str:
        """
        Apply selected emojis to message based on placement strategy.
        
        Args:
            message: Original bot response text
            emojis: Selected emojis to apply
            placement: Where to place ('end_of_message', 'integrated_throughout', etc.)
        
        Returns:
            Message with emojis applied
        """
        if not emojis:
            return message
        
        emoji_str = ''.join(emojis)
        
        if placement == 'end_of_message':
            # Simple append
            return f"{message} {emoji_str}"
        
        elif placement == 'integrated_throughout':
            # Sprinkle emojis at sentence boundaries
            sentences = message.split('. ')
            if len(sentences) > 1 and len(emojis) > 1:
                # Add first emoji after first sentence
                sentences[0] = f"{sentences[0]} {emojis[0]}"
                # Add remaining emojis at end
                sentences[-1] = f"{sentences[-1]} {''.join(emojis[1:])}"
                return '. '.join(sentences)
            else:
                # Just append
                return f"{message} {emoji_str}"
        
        elif placement in ['sparse_meaningful', 'ceremonial_meaningful']:
            # Only at end for special moments
            return f"{message} {emoji_str}"
        
        else:
            # Default: append at end
            return f"{message} {emoji_str}"


# Factory function for dependency injection
def create_database_emoji_selector(db_pool) -> DatabaseEmojiSelector:
    """Factory function to create DatabaseEmojiSelector instance."""
    return DatabaseEmojiSelector(db_pool)
