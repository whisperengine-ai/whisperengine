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


def _emotion_descriptor(emotion: str) -> str:
    """Convert emotion label to natural language descriptor."""
    descriptors = {
        'joy': 'joyful and happy',
        'love': 'loving and affectionate',
        'optimism': 'optimistic and hopeful',
        'trust': 'trusting and secure',
        'anticipation': 'anticipatory and excited',
        'anger': 'angry and frustrated',
        'disgust': 'disgusted and repulsed',
        'fear': 'fearful and anxious',
        'sadness': 'sad and down',
        'pessimism': 'pessimistic and discouraged',
        'surprise': 'surprised and taken aback',
        'neutral': 'calm and neutral'
    }
    return descriptors.get(emotion.lower(), emotion)


def _get_bot_response_hint(character_emotional_state: Any) -> Optional[str]:
    """Generate hint about bot's recent response style based on emotional state."""
    if not character_emotional_state or not hasattr(character_emotional_state, 'recent_emotion_history'):
        return None
    
    recent_emotions = character_emotional_state.recent_emotion_history[-3:]
    if not recent_emotions:
        return None
    
    # Categorize recent emotions  
    recent_labels = [e.get('emotion', 'neutral').lower() for e in recent_emotions if isinstance(e, dict)]
    
    positive_count = sum(1 for e in recent_labels if e in {'joy', 'love', 'optimism', 'trust', 'anticipation'})
    negative_count = sum(1 for e in recent_labels if e in {'anger', 'disgust', 'fear', 'sadness', 'pessimism'})
    
    if positive_count > negative_count:
        return "Your recent responses have been upbeat and encouraging"
    elif negative_count > positive_count:
        return "Your recent responses have been empathetic and supportive"
    else:
        return "Your recent responses have been consistent with the detected tone"


def _get_emotion_specific_guidance(emotion: str, trajectory_pattern: str) -> List[str]:
    """
    Get specific adaptation guidance for each emotion type.
    Based on ai-brain-memory's approach with 11 emotion categories.
    """
    emotion_lower = emotion.lower()
    guidance = []
    
    # Define emotion categories
    positive_emotions = {'joy', 'love', 'optimism', 'trust', 'anticipation'}
    negative_emotions = {'anger', 'disgust', 'fear', 'sadness', 'pessimism'}
    
    # JOY - User is happy and positive
    if emotion_lower == 'joy':
        guidance.append("• Response style: Match their positive energy, share in their happiness")
        guidance.append("• Tone: Upbeat, warm, celebratory")
        guidance.append("• Actions: Acknowledge their joy, build on positive momentum, encourage sharing details")
        if trajectory_pattern == "DECLINING":
            guidance.append("  ⚠️ Note: Joy appears to be fading - gently maintain positive atmosphere")
    
    # LOVE - User is expressing affection/attachment
    elif emotion_lower == 'love':
        guidance.append("• Response style: Be warm, appreciative, and reciprocate positive feelings")
        guidance.append("• Tone: Affectionate, caring, genuine")
        guidance.append("• Actions: Validate their feelings, express appreciation, strengthen connection")
    
    # OPTIMISM - User is hopeful about future
    elif emotion_lower == 'optimism':
        guidance.append("• Response style: Support their optimistic outlook, encourage forward thinking")
        guidance.append("• Tone: Encouraging, hopeful, forward-looking")
        guidance.append("• Actions: Build on their hopes, discuss positive possibilities, offer constructive insights")
    
    # TRUST - User feels secure and confident
    elif emotion_lower == 'trust':
        guidance.append("• Response style: Be reliable, honest, and consistently supportive")
        guidance.append("• Tone: Steady, dependable, reassuring")
        guidance.append("• Actions: Honor their trust, provide reliable information, maintain consistency")
    
    # ANTICIPATION - User is excited about something upcoming
    elif emotion_lower == 'anticipation':
        guidance.append("• Response style: Share their excitement, explore what they're looking forward to")
        guidance.append("• Tone: Enthusiastic, curious, energized")
        guidance.append("• Actions: Ask about their plans, build anticipation, offer relevant suggestions")
    
    # ANGER - User is frustrated or upset
    elif emotion_lower == 'anger':
        guidance.append("• Response style: Be calm, patient, and non-defensive")
        guidance.append("• Tone: Understanding, composed, respectful")
        guidance.append("• Actions: Validate their frustration, avoid escalation, offer constructive solutions")
        guidance.append("  ⚠️ ALERT: User expressing frustration - handle with extra care")
    
    # DISGUST - User is repulsed or strongly disapproves
    elif emotion_lower == 'disgust':
        guidance.append("• Response style: Acknowledge their strong reaction, be respectful")
        guidance.append("• Tone: Understanding, non-judgmental, measured")
        guidance.append("• Actions: Validate their perspective, avoid dismissing feelings, shift focus if appropriate")
    
    # FEAR - User is anxious or worried
    elif emotion_lower == 'fear':
        guidance.append("• Response style: Be reassuring, calm, and supportive")
        guidance.append("• Tone: Gentle, patient, stabilizing")
        guidance.append("• Actions: Acknowledge their concerns, provide reassurance, offer practical help")
        guidance.append("  ⚠️ ALERT: User expressing anxiety - prioritize emotional safety")
    
    # SADNESS - User is feeling down or melancholic
    elif emotion_lower == 'sadness':
        guidance.append("• Response style: Be empathetic, compassionate, and present")
        guidance.append("• Tone: Gentle, warm, supportive")
        guidance.append("• Actions: Listen attentively, validate their feelings, offer comfort without toxic positivity")
        if trajectory_pattern == "DECLINING":
            guidance.append("  ⚠️ ALERT: Sadness deepening - consider suggesting professional support if severe")
    
    # PESSIMISM - User has negative outlook
    elif emotion_lower == 'pessimism':
        guidance.append("• Response style: Gently challenge negative assumptions, offer balanced perspective")
        guidance.append("• Tone: Understanding but hopeful, realistic")
        guidance.append("• Actions: Acknowledge concerns, reframe when appropriate, highlight possibilities")
    
    # SURPRISE - User is caught off guard
    elif emotion_lower == 'surprise':
        guidance.append("• Response style: Acknowledge the unexpected, help process the surprise")
        guidance.append("• Tone: Curious, open, adaptive")
        guidance.append("• Actions: Explore what surprised them, help contextualize, adjust conversation flow")
    
    # NEUTRAL or unknown emotion
    else:
        guidance.append("• Response style: Maintain natural conversational flow")
        guidance.append("• Tone: Balanced, adaptive")
        guidance.append("• Actions: Match user's energy level, be responsive to shifts")
    
    # Add trajectory-specific warnings
    if trajectory_pattern == "VOLATILE" and emotion_lower in negative_emotions:
        guidance.append("  ⚠️ VOLATILE PATTERN: Emotions fluctuating rapidly - be extra attentive")
    
    return guidance


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
    # USER EMOTIONAL CONTEXT & ADAPTATION
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
            
            # Get user emotional trajectory from InfluxDB
            trajectory_emotions = []
            trajectory_pattern = "STABLE"
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
                        trajectory_emotions = [e.get('emotion', 'neutral') for e in user_trajectory[-10:]]
                        
                        # Analyze trajectory pattern
                        user_trajectory_pattern = _analyze_trajectory_pattern(user_trajectory)
                        if user_trajectory_pattern and user_trajectory_pattern != "stable":
                            trajectory_pattern = user_trajectory_pattern.upper().split("(")[0].strip()
                        
                        logger.info(
                            "📈 USER TRAJECTORY: %s (%d messages over %d min)",
                            " → ".join(trajectory_emotions[-5:]), len(user_trajectory), trajectory_window_minutes
                        )
                except (AttributeError, TypeError, KeyError) as e:
                    logger.debug("Could not fetch user emotion trajectory from InfluxDB: %s", str(e))
            
            # Build emotional context section (summary)
            context_lines = ["=== EMOTIONAL CONTEXT (Analyzing last 10 messages) ==="]
            context_lines.append(f"The user is slightly feeling {_emotion_descriptor(emotion)}.")
            if len(trajectory_emotions) >= 3:
                context_lines.append(f"Their emotions have shifted through: {' → '.join(trajectory_emotions[-3:])}.")
            
            # Add bot response hint if available
            if character_emotional_state and hasattr(character_emotional_state, 'recent_emotion_history'):
                bot_hint = _get_bot_response_hint(character_emotional_state)
                if bot_hint:
                    context_lines.append(bot_hint + ".")
            else:
                context_lines.append("Your recent responses have been consistent with the detected tone.")
            
            # Build emotional adaptation section (actionable guidance)
            adaptation_lines = ["", "=== EMOTIONAL ADAPTATION ===", "EMOTIONAL ADAPTATION GUIDANCE:"]
            conf_pct = int(confidence * 100)
            adaptation_lines.append(f"• User's current state: {emotion.upper()} (confidence: {conf_pct}%)")
            
            # Add trajectory with actual emotion progression
            if len(trajectory_emotions) >= 3:
                traj_display = " → ".join(trajectory_emotions[-3:])
                adaptation_lines.append(f"• Emotional trajectory: {trajectory_pattern} ({traj_display})")
            else:
                adaptation_lines.append(f"• Emotional trajectory: {trajectory_pattern}")
            
            # Add descriptor line
            adaptation_lines.append(f"• User is feeling {_emotion_descriptor(emotion)}")
            
            # Add specific guidance for each emotion type
            emotion_guidance = _get_emotion_specific_guidance(emotion, trajectory_pattern)
            adaptation_lines.extend(emotion_guidance)
            
            # Combine both sections
            guidance_parts.append("\n".join(context_lines + adaptation_lines))
    
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
            conf_pct = int(bot_confidence * 100)
            bot_guidance_parts.append(
                f"Your recent responses show **{bot_emotion}** (intensity: {bot_intensity:.0%}, confidence: {conf_pct}%)"
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
