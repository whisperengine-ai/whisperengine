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
            
            # Step 5: Query database for relevant emoji patterns
            emoji_patterns = await self._query_emoji_patterns(
                character_name=character_name,
                emotion=bot_emotion,
                intensity=bot_emotion_data.get('intensity', 0.5),
                topics=detected_topics or [],
                response_type=response_type
            )
            
            # Step 6: Select emojis from patterns
            if emoji_patterns:
                selected_emojis = self._select_from_patterns(
                    emoji_patterns,
                    intensity=bot_emotion_data.get('intensity', 0.5),
                    combination_style=character_config['emoji_combination']
                )
                source = 'database'
                reasoning = f"bot emotion='{bot_emotion}', patterns={len(emoji_patterns)}, intensity={bot_emotion_data.get('intensity', 0.5):.2f}"
            else:
                # Fallback to taxonomy
                selected_emojis = self._fallback_to_taxonomy(
                    emotion=bot_emotion,
                    character_name=character_name,
                    intensity=bot_emotion_data.get('intensity', 0.5)
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
    
    def _select_from_patterns(
        self,
        patterns: List[Dict],
        intensity: float,
        combination_style: str
    ) -> List[str]:
        """Select individual emojis from pattern sequences based on intensity."""
        if not patterns:
            return []
        
        # Get emoji sequence from first pattern (highest priority)
        emoji_sequence = patterns[0]['emoji_sequence']
        
        # Parse emoji sequence (space-separated or concatenated)
        emojis = self._parse_emoji_sequence(emoji_sequence)
        
        if not emojis:
            return []
        
        # Determine how many emojis to use based on intensity and combination style
        if combination_style == 'minimal_symbolic_emoji':
            count = 1  # Always just one
        elif combination_style == 'text_with_accent_emoji':
            count = 1  # Single accent
        elif combination_style == 'text_plus_emoji':
            # Scale with intensity
            if intensity > 0.8:
                count = min(3, len(emojis))
            elif intensity > 0.5:
                count = min(2, len(emojis))
            else:
                count = 1
        elif combination_style == 'emoji_only':
            count = min(2, len(emojis))  # Can use more for emoji-only
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
        intensity: float
    ) -> List[str]:
        """Fallback to UniversalEmotionTaxonomy when no database patterns found."""
        # Standardize emotion label
        standardized_emotion = self.taxonomy.standardize_emotion_label(emotion)
        
        # Get emoji from taxonomy
        emoji = self.taxonomy.roberta_to_emoji_choice(
            roberta_emotion=standardized_emotion,
            character=character_name,
            confidence=intensity
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
        
        # Only filter if user is in emotional distress
        if user_emotion not in ['sadness', 'fear', 'anger'] or user_intensity <= 0.6:
            return message
        
        # WHITELIST APPROACH: Define ALLOWED emojis for distress contexts
        # Better to remove all emojis except these safe, empathetic ones
        # Keep list minimal - only universal empathy/support emojis
        allowed_empathy_emojis = [
            '💙',  # Blue heart - empathy
            '💔',  # Broken heart - acknowledgment
            '🙏',  # Praying hands - support
            '❤️',  # Red heart - love/care
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
