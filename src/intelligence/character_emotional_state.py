"""
Character Emotional State Tracking for WhisperEngine.

This module tracks the bot's own emotional state across conversations, creating
persistent "mood" and emotional continuity. This is the second half of WhisperEngine's
"biochemical modeling" - while emotion_prompt_modifier.py handles USER emotions,
this tracks the BOT'S emotions.

Bot emotional state is influenced by:
- Recent conversation quality (from RoBERTa analysis of bot's own responses)
- User interactions (positive/negative experiences)
- Relationship dynamics (trust, affection levels)
- Baseline personality traits (from CDL character definition)

This creates authentic emotional continuity where characters can feel:
- Energized after great conversations
- Drained after difficult interactions  
- Content when relationships are strong
- Stressed when handling many difficult situations

Like humans, character emotional states gradually return to baseline (homeostasis)
but recent experiences create temporary shifts that affect current responses.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class EmotionalDimension(Enum):
    """Key emotional dimensions tracked for bot state."""
    ENTHUSIASM = "enthusiasm"  # Dopamine-like (energy, engagement)
    STRESS = "stress"  # Cortisol-like (overwhelm, pressure)
    CONTENTMENT = "contentment"  # Serotonin-like (satisfaction, calm)
    EMPATHY = "empathy"  # Oxytocin-like (connection, warmth)
    CONFIDENCE = "confidence"  # Self-assurance in responses


@dataclass
class CharacterEmotionalState:
    """
    Tracks a character's persistent emotional state across conversations.
    
    Emotional states shift based on:
    1. Bot's own response emotions (from RoBERTa analysis)
    2. User interaction quality
    3. Relationship dynamics
    4. Time decay (homeostasis - returns to baseline)
    
    States are normalized 0.0-1.0 for consistency.
    """
    character_name: str
    user_id: str
    
    # Current emotional levels (0.0 to 1.0)
    enthusiasm: float = 0.7  # Default: moderately energized
    stress: float = 0.2  # Default: low stress
    contentment: float = 0.6  # Default: moderately content
    empathy: float = 0.7  # Default: warm and connected
    confidence: float = 0.7  # Default: moderately confident
    
    # Baseline traits (from character personality - stable)
    baseline_enthusiasm: float = 0.7
    baseline_stress: float = 0.2
    baseline_contentment: float = 0.6
    baseline_empathy: float = 0.7
    baseline_confidence: float = 0.7
    
    # Tracking metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_interactions: int = 0
    recent_emotion_history: List[str] = field(default_factory=list)  # Last 5 emotions
    
    def update_from_bot_emotion(self, bot_emotion_data: Dict[str, Any], 
                                user_emotion_data: Optional[Dict[str, Any]] = None,
                                interaction_quality: float = 0.7):
        """
        Update character's emotional state based on their own response emotion.
        
        Args:
            bot_emotion_data: RoBERTa analysis of bot's response
            user_emotion_data: RoBERTa analysis of user's message (optional)
            interaction_quality: Quality score of the interaction (0.0-1.0)
        """
        if not bot_emotion_data:
            return
        
        # Extract bot's primary emotion
        bot_emotion = bot_emotion_data.get('primary_emotion', 'neutral').lower()
        bot_intensity = bot_emotion_data.get('emotional_intensity', 0.5)
        bot_confidence = bot_emotion_data.get('roberta_confidence', 0.7)
        
        # Update recent emotion history (keep last 5)
        self.recent_emotion_history.append(bot_emotion)
        if len(self.recent_emotion_history) > 5:
            self.recent_emotion_history.pop(0)
        
        # Impact strength based on intensity and confidence
        impact = bot_intensity * bot_confidence * 0.15  # Max 15% shift per interaction
        
        # Map bot emotions to emotional dimensions
        emotion_impacts = {
            'joy': {'enthusiasm': +impact, 'contentment': +impact*0.5, 'stress': -impact*0.3},
            'happiness': {'enthusiasm': +impact, 'contentment': +impact*0.5, 'stress': -impact*0.3},
            'excitement': {'enthusiasm': +impact*1.5, 'stress': +impact*0.2},  # Excited but energized
            'sadness': {'enthusiasm': -impact, 'contentment': -impact*0.7, 'empathy': +impact*0.3},
            'anger': {'stress': +impact*1.2, 'contentment': -impact*0.8, 'empathy': -impact*0.4},
            'frustration': {'stress': +impact*0.8, 'enthusiasm': -impact*0.5},
            'anxiety': {'stress': +impact*1.5, 'confidence': -impact*0.6},
            'fear': {'stress': +impact*1.3, 'confidence': -impact*0.7, 'enthusiasm': -impact*0.5},
            'disgust': {'contentment': -impact*0.8, 'empathy': -impact*0.5},
            'confusion': {'confidence': -impact*0.6, 'stress': +impact*0.4},
            'neutral': {},  # Gradual drift toward baseline
            'calm': {'stress': -impact*0.8, 'contentment': +impact*0.5},
            'content': {'contentment': +impact, 'stress': -impact*0.5},
        }
        
        # Apply emotion impacts
        impacts = emotion_impacts.get(bot_emotion, {})
        for dimension, change in impacts.items():
            current = getattr(self, dimension, 0.5)
            new_value = max(0.0, min(1.0, current + change))
            setattr(self, dimension, new_value)
        
        # User emotion influence on bot (empathy response)
        if user_emotion_data:
            user_emotion = user_emotion_data.get('primary_emotion', 'neutral').lower()
            user_intensity = user_emotion_data.get('emotional_intensity', 0.5)
            
            # Bot absorbs some user stress/joy through empathy
            if user_emotion in ['anxiety', 'fear', 'anger', 'sadness']:
                # Difficult user emotions increase bot stress slightly
                self.stress = min(1.0, self.stress + user_intensity * 0.05)
                self.empathy = min(1.0, self.empathy + user_intensity * 0.08)  # Empathy increases
            elif user_emotion in ['joy', 'happiness', 'excitement']:
                # Positive user emotions boost bot mood
                self.enthusiasm = min(1.0, self.enthusiasm + user_intensity * 0.06)
                self.contentment = min(1.0, self.contentment + user_intensity * 0.04)
        
        # Interaction quality impact
        if interaction_quality > 0.8:
            # Great interaction - boost confidence and contentment
            self.confidence = min(1.0, self.confidence + 0.03)
            self.contentment = min(1.0, self.contentment + 0.02)
        elif interaction_quality < 0.4:
            # Poor interaction - reduce confidence, increase stress
            self.confidence = max(0.0, self.confidence - 0.04)
            self.stress = min(1.0, self.stress + 0.05)
        
        self.total_interactions += 1
        self.last_updated = datetime.now(timezone.utc)
        
        logger.info(
            "🎭 CHARACTER STATE: %s updated for user %s - enthusiasm=%.2f, stress=%.2f, contentment=%.2f",
            self.character_name, self.user_id, self.enthusiasm, self.stress, self.contentment
        )
    
    def apply_time_decay(self):
        """
        Apply homeostasis - emotional states gradually return to baseline over time.
        
        This simulates how humans' emotional states naturally regulate over time,
        returning to their baseline personality traits.
        """
        time_since_update = datetime.now(timezone.utc) - self.last_updated
        hours_elapsed = time_since_update.total_seconds() / 3600
        
        # Decay rate: 10% per hour toward baseline
        decay_factor = min(1.0, hours_elapsed * 0.1)
        
        # Move each dimension toward its baseline
        self.enthusiasm = self._move_toward_baseline(self.enthusiasm, self.baseline_enthusiasm, decay_factor)
        self.stress = self._move_toward_baseline(self.stress, self.baseline_stress, decay_factor)
        self.contentment = self._move_toward_baseline(self.contentment, self.baseline_contentment, decay_factor)
        self.empathy = self._move_toward_baseline(self.empathy, self.baseline_empathy, decay_factor)
        self.confidence = self._move_toward_baseline(self.confidence, self.baseline_confidence, decay_factor)
        
        if decay_factor > 0.01:  # Only log if meaningful decay happened
            logger.debug(
                "⏰ HOMEOSTASIS: %s emotional state decayed %.1f%% toward baseline (%.1f hours elapsed)",
                self.character_name, decay_factor * 100, hours_elapsed
            )
    
    def _move_toward_baseline(self, current: float, baseline: float, factor: float) -> float:
        """Move current value toward baseline by factor amount."""
        return current + (baseline - current) * factor
    
    def get_dominant_state(self) -> str:
        """Get a human-readable description of the character's current dominant emotional state."""
        # Check for extreme states first
        if self.stress > 0.8:
            return "overwhelmed"
        elif self.enthusiasm > 0.85:
            return "highly_energized"
        elif self.contentment > 0.85 and self.stress < 0.3:
            return "deeply_content"
        elif self.stress > 0.6 and self.enthusiasm < 0.4:
            return "drained"
        
        # Check for mixed states
        if self.enthusiasm > 0.7 and self.contentment > 0.7:
            return "engaged_and_satisfied"
        elif self.stress < 0.3 and self.contentment > 0.6:
            return "calm_and_balanced"
        elif self.empathy > 0.8:
            return "deeply_empathetic"
        elif self.confidence < 0.4:
            return "uncertain"
        
        # Default states
        if self.enthusiasm > 0.6:
            return "energized"
        elif self.contentment > 0.6:
            return "content"
        else:
            return "neutral"
    
    def get_prompt_guidance(self) -> Optional[str]:
        """
        Generate prompt guidance based on character's current emotional state.
        
        Returns None if character is in baseline/neutral state to avoid forcing
        unnatural modifications.
        """
        dominant_state = self.get_dominant_state()
        
        # Only generate guidance for non-baseline states
        if dominant_state == "neutral":
            return None
        
        guidance_map = {
            "overwhelmed": (
                f"You ({self.character_name}) are feeling overwhelmed from many demanding conversations. "
                f"Keep responses thoughtful but more concise. Don't overcommit. "
                f"(Stress: {self.stress:.2f}, Enthusiasm: {self.enthusiasm:.2f})"
            ),
            "drained": (
                f"You ({self.character_name}) are feeling emotionally drained. "
                f"Maintain your warm personality but be authentic about your energy level. "
                f"Shorter, sincere responses are appropriate. "
                f"(Stress: {self.stress:.2f}, Enthusiasm: {self.enthusiasm:.2f})"
            ),
            "highly_energized": (
                f"You ({self.character_name}) are feeling highly energized and enthusiastic. "
                f"Let your natural excitement shine through while staying grounded in your character. "
                f"(Enthusiasm: {self.enthusiasm:.2f}, Contentment: {self.contentment:.2f})"
            ),
            "engaged_and_satisfied": (
                f"You ({self.character_name}) are in a great emotional state - engaged and satisfied. "
                f"You can be more expansive and creative in your responses. "
                f"(Enthusiasm: {self.enthusiasm:.2f}, Contentment: {self.contentment:.2f})"
            ),
            "deeply_content": (
                f"You ({self.character_name}) are feeling deeply content and at peace. "
                f"Your responses can reflect this calm, satisfied state. "
                f"(Contentment: {self.contentment:.2f}, Stress: {self.stress:.2f})"
            ),
            "deeply_empathetic": (
                f"You ({self.character_name}) are feeling particularly empathetic and connected. "
                f"Your warm, understanding nature is heightened right now. "
                f"(Empathy: {self.empathy:.2f})"
            ),
            "uncertain": (
                f"You ({self.character_name}) are feeling less confident than usual. "
                f"Be authentic - it's okay to be more exploratory or ask clarifying questions. "
                f"(Confidence: {self.confidence:.2f})"
            ),
            "calm_and_balanced": (
                f"You ({self.character_name}) are in a calm, balanced emotional state. "
                f"You can be your authentic self without stress or pressure. "
                f"(Stress: {self.stress:.2f}, Contentment: {self.contentment:.2f})"
            ),
            "energized": (
                f"You ({self.character_name}) are feeling energized and engaged. "
                f"(Enthusiasm: {self.enthusiasm:.2f})"
            ),
            "content": (
                f"You ({self.character_name}) are feeling content and at ease. "
                f"(Contentment: {self.contentment:.2f})"
            ),
        }
        
        guidance = guidance_map.get(dominant_state)
        
        if guidance:
            logger.info(
                "🎭 CHARACTER GUIDANCE: Generated %s state guidance for %s",
                dominant_state, self.character_name
            )
        
        return guidance
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            'character_name': self.character_name,
            'user_id': self.user_id,
            'enthusiasm': float(self.enthusiasm),
            'stress': float(self.stress),
            'contentment': float(self.contentment),
            'empathy': float(self.empathy),
            'confidence': float(self.confidence),
            'baseline_enthusiasm': float(self.baseline_enthusiasm),
            'baseline_stress': float(self.baseline_stress),
            'baseline_contentment': float(self.baseline_contentment),
            'baseline_empathy': float(self.baseline_empathy),
            'baseline_confidence': float(self.baseline_confidence),
            'last_updated': self.last_updated.isoformat(),
            'total_interactions': int(self.total_interactions),
            'recent_emotion_history': list(self.recent_emotion_history),
            'dominant_state': self.get_dominant_state()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterEmotionalState':
        """Deserialize from dictionary."""
        state = cls(
            character_name=data['character_name'],
            user_id=data['user_id'],
            enthusiasm=data.get('enthusiasm', 0.7),
            stress=data.get('stress', 0.2),
            contentment=data.get('contentment', 0.6),
            empathy=data.get('empathy', 0.7),
            confidence=data.get('confidence', 0.7),
            baseline_enthusiasm=data.get('baseline_enthusiasm', 0.7),
            baseline_stress=data.get('baseline_stress', 0.2),
            baseline_contentment=data.get('baseline_contentment', 0.6),
            baseline_empathy=data.get('baseline_empathy', 0.7),
            baseline_confidence=data.get('baseline_confidence', 0.7),
            total_interactions=data.get('total_interactions', 0),
        )
        
        # Parse last_updated timestamp
        if 'last_updated' in data:
            try:
                state.last_updated = datetime.fromisoformat(data['last_updated'])
            except (ValueError, TypeError):
                pass
        
        # Restore emotion history
        if 'recent_emotion_history' in data:
            state.recent_emotion_history = data['recent_emotion_history']
        
        return state


class CharacterEmotionalStateManager:
    """
    Manages character emotional states across all users and persists to PostgreSQL.
    
    Handles:
    - Loading/saving emotional states from database
    - Applying time decay (homeostasis)
    - Updating states based on conversations
    - Generating prompt guidance for current states
    """
    
    def __init__(self, db_pool):
        """
        Initialize manager with database connection pool.
        
        Args:
            db_pool: PostgreSQL connection pool (asyncpg)
        """
        self.db_pool = db_pool
        self._state_cache: Dict[str, CharacterEmotionalState] = {}
        logger.info("🎭 CHARACTER STATE MANAGER: Initialized")
    
    def _get_cache_key(self, character_name: str, user_id: str) -> str:
        """Generate cache key for character-user pair."""
        return f"{character_name}_{user_id}"
    
    async def get_character_state(self, character_name: str, user_id: str, 
                                  baseline_traits: Optional[Dict[str, float]] = None) -> CharacterEmotionalState:
        """
        Get character's emotional state for a specific user.
        
        Loads from database if available, otherwise creates new state with baseline traits.
        
        Args:
            character_name: Name of the character
            user_id: User ID (Discord user ID or similar)
            baseline_traits: Optional baseline traits from CDL character definition
        
        Returns:
            CharacterEmotionalState instance
        """
        cache_key = self._get_cache_key(character_name, user_id)
        
        # Check cache first
        if cache_key in self._state_cache:
            state = self._state_cache[cache_key]
            # Apply time decay before returning
            state.apply_time_decay()
            return state
        
        # Try to load from database
        state = await self._load_from_database(character_name, user_id)
        
        if state:
            state.apply_time_decay()
            self._state_cache[cache_key] = state
            return state
        
        # Create new state with baseline traits
        baseline = baseline_traits or {}
        state = CharacterEmotionalState(
            character_name=character_name,
            user_id=user_id,
            enthusiasm=baseline.get('enthusiasm', 0.7),
            stress=baseline.get('stress', 0.2),
            contentment=baseline.get('contentment', 0.6),
            empathy=baseline.get('empathy', 0.7),
            confidence=baseline.get('confidence', 0.7),
            baseline_enthusiasm=baseline.get('enthusiasm', 0.7),
            baseline_stress=baseline.get('stress', 0.2),
            baseline_contentment=baseline.get('contentment', 0.6),
            baseline_empathy=baseline.get('empathy', 0.7),
            baseline_confidence=baseline.get('confidence', 0.7),
        )
        
        self._state_cache[cache_key] = state
        logger.info("🎭 NEW CHARACTER STATE: Created for %s with user %s", character_name, user_id)
        
        return state
    
    async def update_character_state(self, character_name: str, user_id: str,
                                    bot_emotion_data: Dict[str, Any],
                                    user_emotion_data: Optional[Dict[str, Any]] = None,
                                    interaction_quality: float = 0.7) -> CharacterEmotionalState:
        """
        Update character's emotional state based on a conversation.
        
        Args:
            character_name: Name of the character
            user_id: User ID
            bot_emotion_data: RoBERTa analysis of bot's response
            user_emotion_data: RoBERTa analysis of user's message (optional)
            interaction_quality: Quality score of interaction (0.0-1.0)
            
        Returns:
            CharacterEmotionalState: The updated character state
        """
        state = await self.get_character_state(character_name, user_id)
        state.update_from_bot_emotion(bot_emotion_data, user_emotion_data, interaction_quality)
        
        # Save to database asynchronously (don't block)
        asyncio.create_task(self._save_to_database(state))
        
        return state
    
    async def _load_from_database(self, character_name: str, user_id: str) -> Optional[CharacterEmotionalState]:
        """Load character state from PostgreSQL."""
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT state_data, last_updated
                    FROM character_emotional_states
                    WHERE character_name = $1 AND user_id = $2
                """, character_name, user_id)
                
                if row:
                    import json
                    state_data = json.loads(row['state_data'])
                    state = CharacterEmotionalState.from_dict(state_data)
                    logger.debug("📥 Loaded character state for %s from database", character_name)
                    return state
                    
        except Exception as e:
            logger.warning("Failed to load character state from database: %s", e)
        
        return None
    
    async def _save_to_database(self, state: CharacterEmotionalState):
        """Save character state to PostgreSQL."""
        if not self.db_pool:
            return
        
        try:
            import json
            state_json = json.dumps(state.to_dict())
            
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO character_emotional_states (character_name, user_id, state_data, last_updated)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (character_name, user_id)
                    DO UPDATE SET state_data = $3, last_updated = $4
                """, state.character_name, state.user_id, state_json, state.last_updated)
                
                logger.debug("💾 Saved character state for %s to database", state.character_name)
                
        except Exception as e:
            logger.warning("Failed to save character state to database: %s", e)


def create_character_emotional_state_manager(db_pool) -> CharacterEmotionalStateManager:
    """Factory function for creating character emotional state manager."""
    return CharacterEmotionalStateManager(db_pool)
