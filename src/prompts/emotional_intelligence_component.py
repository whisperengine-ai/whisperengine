"""
Unified Emotional Intelligence Component for WhisperEngine Prompts.

This module creates a single PromptComponent that combines:
1. User's current emotional state (from RoBERTa analysis)
2. User's emotional trajectory (from InfluxDB time-series data)
3. Bot's current emotional state (from CharacterEmotionalState)
4. Bot's emotional trajectory (from InfluxDB time-series data)

Replaces the hackish trajectory analysis that used Qdrant keyword searches
with proper time-series queries from InfluxDB.

Design Philosophy:
- Single source of truth for emotional context in prompts
- Use InfluxDB for true temporal trajectory analysis
- Only include when emotionally significant (high confidence/intensity)
- Clear, actionable guidance for LLM emotional intelligence
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.prompts.prompt_components import PromptComponent

logger = logging.getLogger(__name__)


async def create_emotional_intelligence_component(
    user_id: str,
    bot_name: str,
    current_user_emotion: Optional[Dict[str, Any]],
    current_bot_emotion: Optional[Dict[str, Any]],
    character_emotional_state: Optional[Any],  # CharacterEmotionalState object
    temporal_client: Optional[Any],  # InfluxDB client for trajectory queries
    priority: int = 9,
    confidence_threshold: float = 0.7,
    intensity_threshold: float = 0.5,
    trajectory_window_minutes: int = 60,  # Last hour by default
    return_metadata: bool = False  # Return trajectory data for footer display
):
    """
    Create unified emotional intelligence component with InfluxDB-powered trajectory analysis.
    
    Args:
        user_id: User identifier
        bot_name: Bot/character name
        current_user_emotion: RoBERTa emotion analysis for current user message
        current_bot_emotion: RoBERTa emotion analysis for bot's last response (if available)
        character_emotional_state: CharacterEmotionalState object with bot's persistent state
        temporal_client: InfluxDB client for time-series trajectory queries
        priority: Component priority in prompt assembly (default: 9)
        confidence_threshold: Minimum emotion confidence to include (default: 0.7)
        intensity_threshold: Minimum emotion intensity to include (default: 0.5)
        trajectory_window_minutes: Time window for trajectory analysis (default: 60)
        return_metadata: If True, return tuple of (PromptComponent, trajectory_metadata)
    
    Returns:
        PromptComponent with emotional intelligence context, or None if no significant emotions
        If return_metadata=True, returns tuple of (PromptComponent, Dict) with trajectory data
    """
    from src.prompts.prompt_components import PromptComponent, PromptComponentType
    
    guidance_parts = []
    has_significant_emotion = False
    
    # Track trajectory data for optional metadata return
    user_trajectory = None
    bot_trajectory = None
    user_trajectory_pattern = None
    bot_trajectory_pattern = None
    
    # ========================================
    # USER EMOTIONAL CONTEXT
    # ========================================
    if current_user_emotion and isinstance(current_user_emotion, dict):
        # Support multiple field name formats (emotion_data vs RoBERTa direct)
        confidence = current_user_emotion.get('roberta_confidence') or current_user_emotion.get('confidence', 0)
        intensity = current_user_emotion.get('emotional_intensity') or current_user_emotion.get('intensity', 0)
        
        logger.info(
            "EMOTIONAL INTELLIGENCE: User emotion - confidence=%.2f (threshold=%.2f), intensity=%.2f (threshold=%.2f)",
            confidence, confidence_threshold, intensity, intensity_threshold
        )
        
        # Only include if significant (confidence > threshold AND intensity > threshold)
        if confidence >= confidence_threshold and intensity >= intensity_threshold:
            has_significant_emotion = True
            emotion = current_user_emotion.get('primary_emotion', 'neutral')
            
            # Build intensity descriptor
            if intensity >= 0.8:
                strength = "strongly"
            elif intensity >= 0.6:
                strength = "noticeably"
            else:
                strength = "somewhat"
            
            user_emotion_parts = [
                f"User is {strength} experiencing **{emotion}** (confidence: {confidence:.0%}, intensity: {intensity:.0%})"
            ]
            
            # Get user emotional trajectory from InfluxDB
            if temporal_client:
                try:
                    user_trajectory = await _get_user_emotion_trajectory_from_influx(
                        temporal_client=temporal_client,
                        user_id=user_id,
                        bot_name=bot_name,
                        window_minutes=trajectory_window_minutes
                    )
                    
                    if user_trajectory and len(user_trajectory) > 1:
                        # Extract emotion labels for trajectory visualization
                        trajectory_emotions = [e.get('emotion', 'neutral') for e in user_trajectory[-5:]]
                        trajectory_text = " → ".join(trajectory_emotions)
                        user_emotion_parts.append(f"User emotional trajectory (last {len(user_trajectory)} messages): {trajectory_text}")
                        
                        # Analyze trajectory pattern
                        user_trajectory_pattern = _analyze_trajectory_pattern(user_trajectory)
                        if user_trajectory_pattern and user_trajectory_pattern != "stable":
                            user_emotion_parts.append(f"Pattern: {user_trajectory_pattern}")
                        
                        logger.info(
                            "📈 USER TRAJECTORY: %s (%d messages over %d min)",
                            trajectory_text, len(user_trajectory), trajectory_window_minutes
                        )
                except (AttributeError, TypeError, KeyError) as e:
                    logger.debug("Could not fetch user emotion trajectory from InfluxDB: %s", str(e))
            
            guidance_parts.append("USER EMOTION:\n" + "\n".join(user_emotion_parts))
    
    # ========================================
    # BOT EMOTIONAL CONTEXT
    # ========================================
    bot_guidance_parts = []
    
    # Prefer CharacterEmotionalState (has rich emotional state tracking)
    if character_emotional_state and hasattr(character_emotional_state, 'get_prompt_guidance'):
        bot_guidance = character_emotional_state.get_prompt_guidance()
        if bot_guidance:
            has_significant_emotion = True
            bot_guidance_parts.append(bot_guidance)
            logger.info(
                "🎭 BOT STATE: Using CharacterEmotionalState guidance - %s",
                character_emotional_state.get_dominant_state()
            )
    # Fallback to current bot emotion from RoBERTa analysis
    elif current_bot_emotion and isinstance(current_bot_emotion, dict):
        bot_emotion = current_bot_emotion.get('primary_emotion', 'neutral')
        # Support multiple field name formats
        bot_intensity = current_bot_emotion.get('emotional_intensity') or current_bot_emotion.get('intensity', 0)
        bot_confidence = current_bot_emotion.get('roberta_confidence') or current_bot_emotion.get('confidence', 0)
        
        if bot_intensity >= intensity_threshold and bot_confidence >= confidence_threshold:
            has_significant_emotion = True
            
            if bot_intensity >= 0.8:
                strength = "strongly"
            elif bot_intensity >= 0.6:
                strength = "noticeably"
            else:
                strength = "somewhat"
            
            bot_guidance_parts.append(
                f"Your recent responses show **{bot_emotion}** (intensity: {bot_intensity:.0%}, confidence: {bot_confidence:.0%})"
            )
    
    # Get bot emotional trajectory from InfluxDB (regardless of which source we used above)
    if temporal_client and bot_guidance_parts:
        try:
            bot_trajectory = await _get_bot_emotion_trajectory_from_influx(
                temporal_client=temporal_client,
                user_id=user_id,
                bot_name=bot_name,
                window_minutes=trajectory_window_minutes
            )
            
            if bot_trajectory and len(bot_trajectory) > 1:
                # Extract emotion labels for trajectory visualization
                trajectory_emotions = [e.get('emotion', 'neutral') for e in bot_trajectory[-5:]]
                trajectory_text = " → ".join(trajectory_emotions)
                bot_guidance_parts.append(f"Your emotional trajectory (last {len(bot_trajectory)} responses): {trajectory_text}")
                
                # Analyze trajectory pattern
                bot_trajectory_pattern = _analyze_trajectory_pattern(bot_trajectory)
                if bot_trajectory_pattern and bot_trajectory_pattern != "stable":
                    bot_guidance_parts.append(f"Pattern: {bot_trajectory_pattern}")
                
                logger.info(
                    "📈 BOT TRAJECTORY: %s (%d responses over %d min)",
                    trajectory_text, len(bot_trajectory), trajectory_window_minutes
                )
        except (AttributeError, TypeError, KeyError) as e:
            logger.debug("Could not fetch bot emotion trajectory from InfluxDB: %s", str(e))
    
    if bot_guidance_parts:
        guidance_parts.append("YOUR EMOTIONAL STATE:\n" + "\n".join(bot_guidance_parts))
    
    # ========================================
    # COMPILE COMPONENT
    # ========================================
    
    # Always prepare trajectory metadata if requested (even if component not created)
    if return_metadata:
        trajectory_metadata = {
            'user_trajectory': user_trajectory,
            'user_trajectory_pattern': user_trajectory_pattern,
            'bot_trajectory': bot_trajectory,
            'bot_trajectory_pattern': bot_trajectory_pattern
        }
    
    # Only create component if emotions are significant
    if not has_significant_emotion or not guidance_parts:
        logger.debug("No significant emotional context - skipping emotional intelligence component")
        if return_metadata:
            # Still return trajectory metadata even if no component
            return None, trajectory_metadata
        return None  # No significant emotional context
    
    content = "🎭 EMOTIONAL INTELLIGENCE CONTEXT:\n\n" + "\n\n".join(guidance_parts)
    content += "\n\n(Respond with emotional attunement while maintaining your authentic personality)"
    
    logger.info(
        "✅ EMOTIONAL INTELLIGENCE: Created component with %d guidance sections",
        len(guidance_parts)
    )
    
    component = PromptComponent(
        type=PromptComponentType.EMOTIONAL_CONTEXT,
        content=content,
        priority=priority,  # Priority 9 - after personality/voice, before knowledge
        required=False,  # Only when emotions are significant
        metadata={
            'user_emotion': current_user_emotion.get('primary_emotion') if current_user_emotion else None,
            'bot_emotion': current_bot_emotion.get('primary_emotion') if current_bot_emotion else None,
            'has_user_trajectory': bool(user_trajectory),
            'has_bot_trajectory': bool(bot_trajectory),
            'trajectory_window_minutes': trajectory_window_minutes
        }
    )
    
    # Return with trajectory metadata if requested
    if return_metadata:
        trajectory_metadata = {
            'user_trajectory': user_trajectory,
            'user_trajectory_pattern': user_trajectory_pattern,
            'bot_trajectory': bot_trajectory,
            'bot_trajectory_pattern': bot_trajectory_pattern
        }
        return component, trajectory_metadata
    
    return component


async def _get_user_emotion_trajectory_from_influx(
    temporal_client: Any,
    user_id: str,
    bot_name: str,
    window_minutes: int = 60
) -> List[Dict[str, Any]]:
    """
    Retrieve user's emotional trajectory from InfluxDB.
    
    Returns list of emotion measurements ordered by time (oldest to newest):
    [
        {'emotion': 'neutral', 'intensity': 0.5, 'confidence': 0.8, 'timestamp': '...'},
        {'emotion': 'joy', 'intensity': 0.7, 'confidence': 0.9, 'timestamp': '...'},
        ...
    ]
    """
    if not temporal_client or not hasattr(temporal_client, 'get_user_emotion_trajectory'):
        return []
    
    try:
        trajectory = await temporal_client.get_user_emotion_trajectory(
            user_id=user_id,
            bot_name=bot_name,
            window_minutes=window_minutes,
            limit=20  # Last 20 measurements max
        )
        return trajectory or []
    except (AttributeError, TypeError, KeyError) as e:
        logger.warning("Failed to retrieve user emotion trajectory from InfluxDB: %s", str(e))
        return []


async def _get_bot_emotion_trajectory_from_influx(
    temporal_client: Any,
    user_id: str,
    bot_name: str,
    window_minutes: int = 60
) -> List[Dict[str, Any]]:
    """
    Retrieve bot's emotional trajectory from InfluxDB.
    
    Returns list of emotion measurements ordered by time (oldest to newest):
    [
        {'emotion': 'neutral', 'intensity': 0.6, 'confidence': 0.85, 'timestamp': '...'},
        {'emotion': 'joy', 'intensity': 0.8, 'confidence': 0.92, 'timestamp': '...'},
        ...
    ]
    """
    if not temporal_client or not hasattr(temporal_client, 'get_bot_emotion_trajectory'):
        return []
    
    try:
        trajectory = await temporal_client.get_bot_emotion_trajectory(
            user_id=user_id,
            bot_name=bot_name,
            window_minutes=window_minutes,
            limit=20  # Last 20 measurements max
        )
        return trajectory or []
    except (AttributeError, TypeError, KeyError) as e:
        logger.warning("Failed to retrieve bot emotion trajectory from InfluxDB: %s", str(e))
        return []


def _analyze_trajectory_pattern(trajectory: List[Dict[str, Any]]) -> Optional[str]:
    """
    Analyze emotional trajectory pattern.
    
    Returns:
        - "escalating" - Intensity increasing over time
        - "de-escalating" - Intensity decreasing over time  
        - "volatile" - High variance in emotions
        - "stable" - Consistent emotional state
        - None if insufficient data
    """
    if not trajectory or len(trajectory) < 3:
        return None
    
    # Extract intensity values
    intensities = [m.get('intensity', 0) for m in trajectory]
    
    if len(intensities) < 3:
        return None
    
    # Calculate trend
    differences = [intensities[i+1] - intensities[i] for i in range(len(intensities)-1)]
    avg_change = sum(differences) / len(differences)
    variance = sum((d - avg_change) ** 2 for d in differences) / len(differences) if differences else 0
    
    # Classify pattern
    if variance > 0.1:
        return "volatile (high emotional variance)"
    elif avg_change > 0.15:
        return "escalating (intensity increasing)"
    elif avg_change < -0.15:
        return "de-escalating (intensity decreasing)"
    else:
        return "stable"
