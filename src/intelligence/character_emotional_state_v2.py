"""
Character Emotional State Tracking (Full-Spectrum RoBERTa) for WhisperEngine.

This module tracks the bot's emotional state using the complete 11-emotion RoBERTa
spectrum, providing symmetric emotional intelligence with user emotion tracking.

**REDESIGN (v2)**: Migrated from 5-dimension compression to full 11-emotion fidelity.
- Old: enthusiasm, stress, contentment, empathy, confidence (lossy abstraction)
- New: anger, anticipation, disgust, fear, joy, love, optimism, pessimism, sadness, surprise, trust

**Why Full-Spectrum**:
- Symmetric intelligence: User emotions tracked with 11 emotions, bot should be too
- No information loss: Store exactly what RoBERTa detects
- Richer memory: Character can reflect on nuanced emotions ("I was both optimistic and anxious")
- EMA-ready: Prerequisite for trajectory smoothing enhancement

Bot emotional state is influenced by:
- Bot's own response emotions (from RoBERTa analysis)
- User interactions (empathy absorption)
- Interaction quality (positive/negative experiences)
- Time decay (homeostasis - returns to CDL-defined baseline)

Like humans, character emotional states gradually return to baseline traits
but recent experiences create temporary shifts that affect responses.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)


@dataclass
class CharacterEmotionalState:
    """
    Tracks a character's persistent emotional state using full RoBERTa 11-emotion spectrum.
    
    NO MORE dimension compression - we track what RoBERTa actually detects.
    
    Emotional states shift based on:
    1. Bot's own response emotions (from RoBERTa analysis)
    2. User emotional influence (empathy absorption)
    3. Interaction quality
    4. Time decay (homeostasis - returns to CDL-defined baseline)
    
    All emotion values normalized 0.0-1.0 for consistency.
    """
    character_name: str
    user_id: str
    
    # === CURRENT EMOTIONAL STATE (0.0-1.0) ===
    # Primary emotions (from RoBERTa model: cardiffnlp/twitter-roberta-base-emotion-multilabel-latest)
    anger: float = 0.1           # Frustration, irritation, annoyance
    anticipation: float = 0.4    # Looking forward, expectant, eager
    disgust: float = 0.05        # Revulsion, disapproval, distaste
    fear: float = 0.1            # Anxiety, worry, concern, apprehension
    joy: float = 0.7             # Happiness, delight, pleasure
    love: float = 0.6            # Affection, warmth, care, fondness
    optimism: float = 0.6        # Hopeful, positive outlook, encouraged
    pessimism: float = 0.2       # Doubtful, negative outlook, discouraged
    sadness: float = 0.15        # Sorrow, melancholy, grief
    surprise: float = 0.2        # Unexpected, astonished, taken aback
    trust: float = 0.7           # Confidence in user, security, faith
    
    # === BASELINE TRAITS (from CDL personality) ===
    # Character's natural emotional tendencies when at rest
    # These are character-specific and come from CDL Big Five → emotion mapping
    baseline_anger: float = 0.1
    baseline_anticipation: float = 0.4
    baseline_disgust: float = 0.05
    baseline_fear: float = 0.1
    baseline_joy: float = 0.7
    baseline_love: float = 0.6
    baseline_optimism: float = 0.6
    baseline_pessimism: float = 0.2
    baseline_sadness: float = 0.15
    baseline_surprise: float = 0.2
    baseline_trust: float = 0.7
    
    # === TRACKING METADATA ===
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_interactions: int = 0
    recent_emotion_history: List[Dict[str, float]] = field(default_factory=list)  # Last 5 full emotion profiles
    
    # === COMPUTED PROPERTIES ===
    
    @property
    def dominant_emotion(self) -> str:
        """Primary emotion currently expressed."""
        emotions = {
            'anger': self.anger,
            'anticipation': self.anticipation,
            'disgust': self.disgust,
            'fear': self.fear,
            'joy': self.joy,
            'love': self.love,
            'optimism': self.optimism,
            'pessimism': self.pessimism,
            'sadness': self.sadness,
            'surprise': self.surprise,
            'trust': self.trust
        }
        return max(emotions.items(), key=lambda x: x[1])[0]
    
    @property
    def emotional_intensity(self) -> float:
        """
        Overall emotional activation level (0.0-1.0).
        
        Measures how far emotions deviate from neutral baseline (0.3).
        Higher intensity = more emotionally activated state.
        """
        emotions = [
            self.anger, self.anticipation, self.disgust, self.fear,
            self.joy, self.love, self.optimism, self.pessimism,
            self.sadness, self.surprise, self.trust
        ]
        # Intensity = average distance from neutral (0.3)
        return sum(abs(e - 0.3) for e in emotions) / len(emotions)
    
    @property
    def emotional_valence(self) -> float:
        """
        Overall positive vs negative emotional tone (-1.0 to +1.0).
        
        Positive emotions vs negative emotions balance.
        +1.0 = completely positive, -1.0 = completely negative, 0.0 = balanced
        """
        positive = self.joy + self.love + self.optimism + self.trust + self.anticipation
        negative = self.anger + self.disgust + self.fear + self.pessimism + self.sadness
        total = positive + negative
        
        if total == 0:
            return 0.0
        
        return (positive - negative) / total
    
    @property
    def emotional_complexity(self) -> float:
        """
        How many emotions are simultaneously active (0.0-1.0).
        
        Measures emotional complexity - higher values indicate mixed/nuanced feelings.
        0.0 = one dominant emotion, 1.0 = all emotions equally active
        """
        emotions = [
            self.anger, self.anticipation, self.disgust, self.fear,
            self.joy, self.love, self.optimism, self.pessimism,
            self.sadness, self.surprise, self.trust
        ]
        # Count emotions above threshold (0.3 = meaningful activation)
        active_count = sum(1 for e in emotions if e > 0.3)
        return active_count / len(emotions)
    
    def get_all_emotions(self) -> Dict[str, float]:
        """Get all current emotion values as dictionary."""
        return {
            'anger': self.anger,
            'anticipation': self.anticipation,
            'disgust': self.disgust,
            'fear': self.fear,
            'joy': self.joy,
            'love': self.love,
            'optimism': self.optimism,
            'pessimism': self.pessimism,
            'sadness': self.sadness,
            'surprise': self.surprise,
            'trust': self.trust
        }
    
    def get_top_emotions(self, limit: int = 3, threshold: float = 0.3) -> List[tuple[str, float]]:
        """
        Get top N emotions above threshold.
        
        Args:
            limit: Maximum number of emotions to return
            threshold: Minimum intensity for emotion to be considered active
            
        Returns:
            List of (emotion_name, intensity) tuples sorted by intensity
        """
        emotions = self.get_all_emotions()
        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)
        return [(name, val) for name, val in sorted_emotions[:limit] if val > threshold]
    
    # === STATE UPDATE METHODS ===
    
    def update_from_bot_emotion(self, 
                                bot_emotion_data: Dict[str, Any],
                                user_emotion_data: Optional[Dict[str, Any]] = None,
                                interaction_quality: float = 0.7) -> None:
        """
        Update character emotional state from RoBERTa analysis of bot response.
        
        NEW APPROACH (v2): Direct application with smoothing, not dimension mapping.
        Applies emotions directly from RoBERTa analysis with adaptive weighting.
        
        Args:
            bot_emotion_data: RoBERTa analysis of bot's response (must include 'all_emotions')
            user_emotion_data: RoBERTa analysis of user's message (optional)
            interaction_quality: Quality score of the interaction (0.0-1.0)
        """
        if not bot_emotion_data:
            return
        
        # Extract full emotion profile from RoBERTa
        all_emotions = bot_emotion_data.get('all_emotions', {})
        if not all_emotions:
            logger.warning(
                "⚠️ Bot emotion data missing 'all_emotions' field - cannot update %s state",
                self.character_name
            )
            return
        
        bot_intensity = bot_emotion_data.get('emotional_intensity', 0.5)
        bot_confidence = bot_emotion_data.get('roberta_confidence', 0.7)
        
        # Calculate impact strength (how much this response shifts state)
        # Higher intensity + confidence = stronger impact
        # Max 20% shift per interaction (prevents whiplash)
        impact_strength = bot_intensity * bot_confidence * 0.20
        
        # Apply emotions DIRECTLY with adaptive smoothing
        # This is essentially EMA with dynamic alpha based on intensity
        for emotion_name, detected_value in all_emotions.items():
            if not hasattr(self, emotion_name):
                continue  # Skip if emotion not in our model (forward compatibility)
            
            current_value = getattr(self, emotion_name)
            
            # Adaptive update: Move toward detected emotion, weighted by impact strength
            # alpha = impact_strength (0.0-0.2 range, i.e., 0-20% weight to new emotion)
            new_value = impact_strength * detected_value + (1 - impact_strength) * current_value
            
            # Clamp to valid range
            new_value = max(0.0, min(1.0, new_value))
            
            setattr(self, emotion_name, new_value)
        
        # Update emotion history (store full profile, not just primary emotion)
        emotion_snapshot = self.get_all_emotions()
        self.recent_emotion_history.append(emotion_snapshot)
        if len(self.recent_emotion_history) > 5:
            self.recent_emotion_history.pop(0)
        
        # User emotion influence (empathy absorption)
        # Character absorbs ~5% of user's emotional state through empathy
        if user_emotion_data:
            user_emotions = user_emotion_data.get('all_emotions', {})
            user_intensity = user_emotion_data.get('emotional_intensity', 0.5)
            
            # Empathy factor: 5% absorption scaled by user emotional intensity
            empathy_factor = 0.05 * user_intensity
            
            for emotion_name, user_value in user_emotions.items():
                if hasattr(self, emotion_name):
                    current = getattr(self, emotion_name)
                    # Slight drift toward user's emotion (empathic resonance)
                    new_value = current + (user_value - current) * empathy_factor
                    new_value = max(0.0, min(1.0, new_value))
                    setattr(self, emotion_name, new_value)
        
        # Interaction quality influence on specific emotions
        if interaction_quality > 0.8:
            # Great interaction: Boost positive emotions slightly
            self.joy = min(1.0, self.joy + 0.03)
            self.trust = min(1.0, self.trust + 0.02)
            self.optimism = min(1.0, self.optimism + 0.02)
        elif interaction_quality < 0.4:
            # Poor interaction: Slight negative shift
            self.sadness = min(1.0, self.sadness + 0.03)
            self.fear = min(1.0, self.fear + 0.02)
            self.pessimism = min(1.0, self.pessimism + 0.02)
        
        self.total_interactions += 1
        self.last_updated = datetime.now(timezone.utc)
        
        logger.info(
            "🎭 CHARACTER STATE: %s updated - dominant=%s, intensity=%.2f, valence=%+.2f",
            self.character_name, self.dominant_emotion, self.emotional_intensity, self.emotional_valence
        )
    
    def apply_time_decay(self) -> None:
        """
        Apply homeostasis - emotional states gradually return to CDL-defined baseline.
        
        This simulates how humans' emotional states naturally regulate over time,
        returning to their baseline personality traits defined in CDL.
        
        Decay rate: 10% per hour toward baseline.
        """
        time_since_update = datetime.now(timezone.utc) - self.last_updated
        hours_elapsed = time_since_update.total_seconds() / 3600
        
        # Decay factor: 10% per hour toward baseline (capped at 100%)
        decay_factor = min(1.0, hours_elapsed * 0.1)
        
        # Move each emotion toward its CDL-defined baseline
        emotion_names = [
            'anger', 'anticipation', 'disgust', 'fear', 'joy', 'love',
            'optimism', 'pessimism', 'sadness', 'surprise', 'trust'
        ]
        
        for emotion in emotion_names:
            current = getattr(self, emotion)
            baseline = getattr(self, f'baseline_{emotion}')
            new_value = self._move_toward_baseline(current, baseline, decay_factor)
            setattr(self, emotion, new_value)
        
        if decay_factor > 0.01:  # Only log if meaningful decay happened
            logger.debug(
                "⏰ HOMEOSTASIS: %s emotional state decayed %.1f%% toward baseline (%.1f hours elapsed)",
                self.character_name, decay_factor * 100, hours_elapsed
            )
    
    def _move_toward_baseline(self, current: float, baseline: float, factor: float) -> float:
        """Move current value toward baseline by factor amount."""
        return current + (baseline - current) * factor
    
    # === PROMPT GUIDANCE GENERATION ===
    
    def get_prompt_guidance(self) -> Optional[str]:
        """
        Generate rich emotional guidance from full 11-emotion profile.
        
        Returns None if character is in baseline/neutral state to avoid forcing
        unnatural modifications.
        
        Returns:
            Formatted prompt guidance string with emotional context, or None if neutral
        """
        # Get top 3 active emotions
        top_emotions = self.get_top_emotions(limit=3, threshold=0.3)
        
        if not top_emotions:
            return None  # Neutral state, no guidance needed
        
        # Build guidance from actual emotional state
        primary_emotion, primary_intensity = top_emotions[0]
        
        guidance_parts = [
            f"YOUR CURRENT EMOTIONAL STATE ({self.character_name}):",
            f"• Dominant feeling: {primary_emotion.upper()} (intensity: {primary_intensity:.2f})"
        ]
        
        # Add secondary emotions if significant
        if len(top_emotions) > 1:
            secondary = [f"{name} ({val:.2f})" for name, val in top_emotions[1:]]
            guidance_parts.append(f"• Also feeling: {', '.join(secondary)}")
        
        # Add emotional context
        guidance_parts.append(
            f"• Overall intensity: {self.emotional_intensity:.2f} "
            f"(0=calm, 1=highly activated)"
        )
        guidance_parts.append(f"• Emotional tone: {self._describe_valence()}")
        
        # Add recent trajectory if available
        if len(self.recent_emotion_history) >= 2:
            trajectory = self._describe_emotional_trajectory()
            guidance_parts.append(f"• Recent emotional arc: {trajectory}")
        
        # Add context-specific guidance based on primary emotion
        emotion_guidance = self._get_emotion_specific_guidance(primary_emotion, primary_intensity)
        if emotion_guidance:
            guidance_parts.append(f"\n{emotion_guidance}")
        
        logger.info(
            "🎭 CHARACTER GUIDANCE: Generated %s state guidance for %s",
            primary_emotion, self.character_name
        )
        
        return "\n".join(guidance_parts)
    
    def _describe_valence(self) -> str:
        """Describe emotional valence in human terms."""
        valence = self.emotional_valence
        if valence > 0.5:
            return "very positive"
        elif valence > 0.2:
            return "moderately positive"
        elif valence > -0.2:
            return "neutral/mixed"
        elif valence > -0.5:
            return "moderately negative"
        else:
            return "quite negative"
    
    def _describe_emotional_trajectory(self) -> str:
        """Describe how emotions have been changing over recent interactions."""
        if len(self.recent_emotion_history) < 2:
            return "stable"
        
        # Compare current state to 5 messages ago
        recent = self.recent_emotion_history[-1]
        oldest = self.recent_emotion_history[0]
        
        # Calculate valence change
        def calc_valence(emotions: Dict[str, float]) -> float:
            positive = (
                emotions.get('joy', 0) + emotions.get('love', 0) + 
                emotions.get('optimism', 0) + emotions.get('trust', 0) + 
                emotions.get('anticipation', 0)
            )
            negative = (
                emotions.get('anger', 0) + emotions.get('fear', 0) + 
                emotions.get('sadness', 0) + emotions.get('pessimism', 0) + 
                emotions.get('disgust', 0)
            )
            return positive - negative
        
        valence_change = calc_valence(recent) - calc_valence(oldest)
        
        if valence_change > 0.3:
            return "becoming more positive"
        elif valence_change < -0.3:
            return "becoming more negative"
        else:
            return "relatively stable"
    
    def _get_emotion_specific_guidance(self, emotion: str, intensity: float) -> Optional[str]:
        """
        Context-aware guidance based on specific emotion and its intensity.
        
        Provides tailored advice for how the character should express each emotion
        authentically while maintaining their core personality.
        """
        guidance_map = {
            'joy': (
                "Your joyful state comes through naturally in your responses. "
                "Share your positive energy authentically."
            ),
            'love': (
                "You're feeling particularly warm and affectionate toward this user. "
                "Let your care show through your words and tone."
            ),
            'optimism': (
                "You're feeling hopeful and positive about this conversation. "
                "Your encouraging perspective is a strength right now."
            ),
            'anticipation': (
                "You're feeling engaged and looking forward to where this goes. "
                "Your curiosity and interest are authentic - let them show."
            ),
            'trust': (
                "You feel secure and confident in this interaction. "
                "Your sense of trust creates a safe space for authentic conversation."
            ),
            'fear': (
                "You're feeling some concern or anxiety. This is valid - you can "
                "acknowledge uncertainty while still being helpful and present."
            ),
            'sadness': (
                "You're experiencing some melancholy or sorrow. It's okay to show "
                "vulnerability - authentic emotion strengthens connection."
            ),
            'anger': (
                "You're feeling frustrated or irritated. Take a breath and respond "
                "with composure while being honest about any boundaries needed."
            ),
            'pessimism': (
                "You're feeling doubtful or negative. Balance realistic concerns "
                "with openness to positive possibilities."
            ),
            'disgust': (
                "You're feeling disapproval or revulsion. Express your perspective "
                "respectfully while maintaining boundaries."
            ),
            'surprise': (
                "You're caught off guard or surprised. It's natural - respond "
                "authentically to the unexpected while staying grounded."
            )
        }
        
        base_guidance = guidance_map.get(emotion)
        if not base_guidance:
            return None
        
        # Adjust guidance based on intensity
        if intensity > 0.8:
            intensity_note = " (This feeling is quite strong right now - honor its intensity.)"
        elif intensity < 0.5:
            intensity_note = " (This is a subtle feeling - let it inform your tone without dominating.)"
        else:
            intensity_note = ""
        
        return base_guidance + intensity_note
    
    # === SERIALIZATION ===
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage/transmission."""
        return {
            'character_name': self.character_name,
            'user_id': self.user_id,
            # Current state
            'anger': float(self.anger),
            'anticipation': float(self.anticipation),
            'disgust': float(self.disgust),
            'fear': float(self.fear),
            'joy': float(self.joy),
            'love': float(self.love),
            'optimism': float(self.optimism),
            'pessimism': float(self.pessimism),
            'sadness': float(self.sadness),
            'surprise': float(self.surprise),
            'trust': float(self.trust),
            # Baselines
            'baseline_anger': float(self.baseline_anger),
            'baseline_anticipation': float(self.baseline_anticipation),
            'baseline_disgust': float(self.baseline_disgust),
            'baseline_fear': float(self.baseline_fear),
            'baseline_joy': float(self.baseline_joy),
            'baseline_love': float(self.baseline_love),
            'baseline_optimism': float(self.baseline_optimism),
            'baseline_pessimism': float(self.baseline_pessimism),
            'baseline_sadness': float(self.baseline_sadness),
            'baseline_surprise': float(self.baseline_surprise),
            'baseline_trust': float(self.baseline_trust),
            # Metadata
            'last_updated': self.last_updated.isoformat(),
            'total_interactions': int(self.total_interactions),
            'recent_emotion_history': list(self.recent_emotion_history),
            # Derived states
            'dominant_emotion': self.dominant_emotion,
            'emotional_intensity': float(self.emotional_intensity),
            'emotional_valence': float(self.emotional_valence),
            'emotional_complexity': float(self.emotional_complexity)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterEmotionalState':
        """Deserialize from dictionary."""
        state = cls(
            character_name=data['character_name'],
            user_id=data['user_id'],
            # Current emotions
            anger=data.get('anger', 0.1),
            anticipation=data.get('anticipation', 0.4),
            disgust=data.get('disgust', 0.05),
            fear=data.get('fear', 0.1),
            joy=data.get('joy', 0.7),
            love=data.get('love', 0.6),
            optimism=data.get('optimism', 0.6),
            pessimism=data.get('pessimism', 0.2),
            sadness=data.get('sadness', 0.15),
            surprise=data.get('surprise', 0.2),
            trust=data.get('trust', 0.7),
            # Baselines
            baseline_anger=data.get('baseline_anger', 0.1),
            baseline_anticipation=data.get('baseline_anticipation', 0.4),
            baseline_disgust=data.get('baseline_disgust', 0.05),
            baseline_fear=data.get('baseline_fear', 0.1),
            baseline_joy=data.get('baseline_joy', 0.7),
            baseline_love=data.get('baseline_love', 0.6),
            baseline_optimism=data.get('baseline_optimism', 0.6),
            baseline_pessimism=data.get('baseline_pessimism', 0.2),
            baseline_sadness=data.get('baseline_sadness', 0.15),
            baseline_surprise=data.get('baseline_surprise', 0.2),
            baseline_trust=data.get('baseline_trust', 0.7),
            # Metadata
            total_interactions=data.get('total_interactions', 0),
        )
        
        # Parse last_updated timestamp
        if 'last_updated' in data:
            try:
                state.last_updated = datetime.fromisoformat(data['last_updated'])
            except (ValueError, TypeError):
                pass
        
        # Restore emotion history (now full profiles, not just strings)
        if 'recent_emotion_history' in data:
            state.recent_emotion_history = data['recent_emotion_history']
        
        return state


class CharacterEmotionalStateManager:
    """
    Manages character emotional states across conversations in memory.
    
    Handles:
    - Applying time decay (homeostasis)
    - Updating states based on conversations  
    - Generating prompt guidance for current states
    
    Note: Currently stores states in memory per session. For database persistence,
    see migration roadmap: docs/roadmaps/CHARACTER_EMOTIONAL_STATE_FULL_SPECTRUM_REDESIGN.md
    """
    
    def __init__(self) -> None:
        """Initialize manager with in-memory cache."""
        self._state_cache: Dict[str, CharacterEmotionalState] = {}
        logger.info("🎭 CHARACTER STATE MANAGER (v2): Initialized with full-spectrum tracking")
    
    def _get_cache_key(self, character_name: str, user_id: str) -> str:
        """Generate cache key for character-user pair."""
        return f"{character_name}_{user_id}"
    
    async def get_character_state(
        self,
        character_name: str,
        user_id: str,
        baseline_traits: Optional[Dict[str, float]] = None
    ) -> CharacterEmotionalState:
        """
        Get character's emotional state for a specific user.
        
        Returns cached state if available, otherwise creates new state with
        baseline traits from CDL character definition.
        
        Args:
            character_name: Name of the character
            user_id: User ID (Discord user ID or similar)
            baseline_traits: Optional baseline emotion values from CDL
                           (should include all 11 emotions)
        
        Returns:
            CharacterEmotionalState instance with full 11-emotion profile
        """
        cache_key = self._get_cache_key(character_name, user_id)
        
        # Check cache first
        if cache_key in self._state_cache:
            state = self._state_cache[cache_key]
            # Apply time decay before returning
            state.apply_time_decay()
            return state
        
        # Create new state with CDL baseline traits
        baseline = baseline_traits or {}
        
        # Extract 11 emotions from baseline (with sensible defaults)
        state = CharacterEmotionalState(
            character_name=character_name,
            user_id=user_id,
            # Current emotions (start at baseline)
            anger=baseline.get('anger', 0.1),
            anticipation=baseline.get('anticipation', 0.4),
            disgust=baseline.get('disgust', 0.05),
            fear=baseline.get('fear', 0.1),
            joy=baseline.get('joy', 0.7),
            love=baseline.get('love', 0.6),
            optimism=baseline.get('optimism', 0.6),
            pessimism=baseline.get('pessimism', 0.2),
            sadness=baseline.get('sadness', 0.15),
            surprise=baseline.get('surprise', 0.2),
            trust=baseline.get('trust', 0.7),
            # Baseline traits (CDL-defined)
            baseline_anger=baseline.get('anger', 0.1),
            baseline_anticipation=baseline.get('anticipation', 0.4),
            baseline_disgust=baseline.get('disgust', 0.05),
            baseline_fear=baseline.get('fear', 0.1),
            baseline_joy=baseline.get('joy', 0.7),
            baseline_love=baseline.get('love', 0.6),
            baseline_optimism=baseline.get('optimism', 0.6),
            baseline_pessimism=baseline.get('pessimism', 0.2),
            baseline_sadness=baseline.get('sadness', 0.15),
            baseline_surprise=baseline.get('surprise', 0.2),
            baseline_trust=baseline.get('trust', 0.7),
        )
        
        self._state_cache[cache_key] = state
        logger.info(
            "🎭 NEW CHARACTER STATE (v2): Created for %s with user %s - dominant=%s",
            character_name, user_id, state.dominant_emotion
        )
        
        return state
    
    async def update_character_state(
        self,
        character_name: str,
        user_id: str,
        bot_emotion_data: Dict[str, Any],
        user_emotion_data: Optional[Dict[str, Any]] = None,
        interaction_quality: float = 0.7
    ) -> CharacterEmotionalState:
        """
        Update character's emotional state based on a conversation.
        
        Args:
            character_name: Name of the character
            user_id: User ID
            bot_emotion_data: RoBERTa analysis of bot's response (requires 'all_emotions')
            user_emotion_data: RoBERTa analysis of user's message (optional)
            interaction_quality: Quality score of interaction (0.0-1.0)
            
        Returns:
            CharacterEmotionalState: The updated character state
        """
        state = await self.get_character_state(character_name, user_id)
        state.update_from_bot_emotion(bot_emotion_data, user_emotion_data, interaction_quality)
        
        return state


def create_character_emotional_state_manager() -> CharacterEmotionalStateManager:
    """
    Factory function for creating character emotional state manager.
    
    Returns v2 manager with full-spectrum 11-emotion tracking.
    """
    return CharacterEmotionalStateManager()
