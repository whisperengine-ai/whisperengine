"""
Discord Status Footer Generator for WhisperEngine

Generates optional intelligence status footers for Discord messages showing:
- Learning moments detected (character intelligence)
- Memory context (vector memory retrieval)
- Relationship status (trust, affection, attunement)
- Emotional state (bot emotion analysis)
- Processing metrics (response time, confidence)

CRITICAL: This footer is for DISPLAY ONLY and NEVER stored in vector memory.
The footer is stripped before any memory storage operations.
"""

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def is_footer_enabled() -> bool:
    """Check if Discord status footer is enabled via environment variable."""
    return os.getenv('DISCORD_STATUS_FOOTER', 'false').lower() == 'true'


def generate_discord_status_footer(
    ai_components: Dict[str, Any],
    processing_time_ms: Optional[int] = None,
    llm_time_ms: Optional[int] = None,
    memory_count: int = 0
) -> str:
    """
    Generate a condensed status footer for Discord messages.
    
    Shows key intelligence insights in a compact, Discord-friendly format:
    - Learning moments (if detected)
    - Memory context
    - Relationship status
    - Emotional state
    - Processing time (total and LLM-specific)
    
    Args:
        ai_components: AI intelligence data from message processing
        processing_time_ms: Total processing time in milliseconds
        llm_time_ms: LLM-specific processing time in milliseconds
        memory_count: Number of relevant memories retrieved
        
    Returns:
        Formatted footer string with Discord markdown, or empty string if disabled
    """
    if not is_footer_enabled():
        return ""
    
    if not ai_components:
        return ""
    
    footer_parts = []
    
    # 1. 🎯 Learning Moments (Character Intelligence)
    try:
        learning_data = ai_components.get('character_learning_moments', {})
        if learning_data and learning_data.get('learning_moments_detected', 0) > 0:
            moment_types = []
            seen_types = set()  # Track seen types to avoid duplicates
            
            # Extract moment types with emoji (deduplicated)
            for moment in learning_data.get('moments', [])[:3]:  # Max 3 types
                moment_type = moment.get('type', '')
                
                # Skip if we've already seen this type
                if moment_type in seen_types:
                    continue
                seen_types.add(moment_type)
                
                if moment_type == 'growth_insight':
                    moment_types.append('🌱Growth')
                elif moment_type == 'user_observation':
                    moment_types.append('👁️Insight')
                elif moment_type == 'memory_surprise':
                    moment_types.append('💡Connection')
                elif moment_type == 'knowledge_evolution':
                    moment_types.append('📚Learning')
                elif moment_type == 'emotional_growth':
                    moment_types.append('💖Emotion')
                elif moment_type == 'relationship_awareness':
                    moment_types.append('🤝Bond')
            
            if moment_types:
                footer_parts.append(f"🎯 **Learning**: {', '.join(moment_types)}")
    except (KeyError, TypeError, AttributeError) as e:
        logger.debug("Could not extract learning moments for footer: %s", str(e))
    
    # 2. 🧠 Memory Context
    if memory_count > 0:
        if memory_count > 10:
            memory_status = f"{memory_count} memories (deep context)"
        elif memory_count > 5:
            memory_status = f"{memory_count} memories (established)"
        else:
            memory_status = f"{memory_count} memories (building)"
        footer_parts.append(f"🧠 **Memory**: {memory_status}")
    
    # 3. 💖 Relationship Status
    try:
        logger.info("🔍 FOOTER: Starting relationship status section")
        # Try to get actual dynamic relationship scores first
        relationship_state = ai_components.get('relationship_state', {}) or {}
        conv_intelligence = ai_components.get('conversation_intelligence', {}) or {}
        
        # DEBUG: Log what we found
        logger.info("🔍 RELATIONSHIP DEBUG: relationship_state exists: %s", bool(relationship_state))
        logger.info("🔍 RELATIONSHIP DEBUG: relationship_state type: %s", type(relationship_state))
        logger.info("🔍 RELATIONSHIP DEBUG: relationship_state content: %s", relationship_state)
        logger.info("🔍 RELATIONSHIP DEBUG: conv_intelligence exists: %s", bool(conv_intelligence))
        logger.info("🔍 RELATIONSHIP DEBUG: conv_intelligence type: %s", type(conv_intelligence))
        logger.info("🔍 RELATIONSHIP DEBUG: conv_intelligence content: %s", conv_intelligence)
        logger.info("🔍 RELATIONSHIP DEBUG: conv_intelligence keys: %s", list(conv_intelligence.keys()) if conv_intelligence else [])
        
        # Get relationship level for emoji and label
        # Try multiple sources for relationship level
        relationship_level = (
            conv_intelligence.get('relationship_level') or 
            relationship_state.get('relationship_depth') or 
            'acquaintance'
        )
        logger.info("🔍 RELATIONSHIP DEBUG: relationship_level: %s", relationship_level)
        
        # Map relationship_depth terms to standard relationship_level terms
        depth_to_level = {
            'initial_contact': 'stranger',
            'building_rapport': 'acquaintance',
            'growing_connection': 'friend',
            'strong_connection': 'close_friend',
            'deep_bond': 'best_friend'
        }
        relationship_level = depth_to_level.get(relationship_level, relationship_level)
        
        # Map relationship level to emoji
        relationship_emoji = {
            'stranger': '🆕',
            'acquaintance': '👋',
            'friend': '😊',
            'close_friend': '💙',
            'best_friend': '💖'
        }
        
        emoji = relationship_emoji.get(relationship_level, '👋')
        
        # Use REAL scores if available, otherwise use approximate mapping
        if relationship_state and 'trust' in relationship_state:
            # Real dynamic scores from database (0.0-1.0 scale, convert to 0-100)
            trust = int(relationship_state['trust'] * 100)
            affection = int(relationship_state['affection'] * 100)
            attunement = int(relationship_state['attunement'] * 100)
            interaction_count = relationship_state.get('interaction_count', 0)
            
            footer_parts.append(
                f"{emoji} **Relationship**: {relationship_level.replace('_', ' ').title()} "
                f"(Trust: {trust}, Affection: {affection}, Attunement: {attunement}) [{interaction_count} interactions]"
            )
        else:
            # Fallback to approximate scores based on level
            relationship_mapping = {
                'stranger': {'affection': 10, 'trust': 15, 'attunement': 20},
                'acquaintance': {'affection': 35, 'trust': 40, 'attunement': 45},
                'friend': {'affection': 65, 'trust': 70, 'attunement': 75},
                'close_friend': {'affection': 85, 'trust': 88, 'attunement': 90},
                'best_friend': {'affection': 95, 'trust': 95, 'attunement': 98}
            }
            
            scores = relationship_mapping.get(relationship_level, relationship_mapping['acquaintance'])
            
            footer_parts.append(
                f"{emoji} **Relationship**: {relationship_level.replace('_', ' ').title()} "
                f"(Trust: {scores['trust']}, Affection: {scores['affection']}, Attunement: {scores['attunement']})"
            )
    except (KeyError, TypeError, AttributeError) as e:
        logger.warning("Could not extract relationship status for footer: %s", str(e), exc_info=True)
    
    # 4. 🔥 Emotional State (Bot Emotion + Trajectory)
    try:
        bot_emotion = ai_components.get('bot_emotion', {})
        if bot_emotion:
            # Get emotion label and intensity (use intensity, not confidence for display)
            emotion_label = bot_emotion.get('primary_emotion') or bot_emotion.get('emotion', 'neutral')
            emotion_intensity = bot_emotion.get('intensity', 0.0)
            
            # Emotion emoji mapping
            emotion_emoji = {
                'joy': '😊',
                'sadness': '😔',
                'anger': '😠',
                'fear': '😨',
                'surprise': '😲',
                'disgust': '🤢',
                'neutral': '😐',
                'love': '❤️',
                'admiration': '🌟',
                'curiosity': '🤔',
                'excitement': '🎉',
                'gratitude': '🙏',
                'pride': '😌',
                'relief': '😌',
                'amusement': '😄',
                'anticipation': '💭',
                'optimism': '✨',
                'disappointment': '😞',
                'nervousness': '😬'
            }
            
            emoji = emotion_emoji.get(emotion_label, '💭')
            intensity_pct = int(emotion_intensity * 100)
            
            # Build emotion display (show intensity, not confidence)
            emotion_parts = [f"{emoji} **Bot Emotion**: {emotion_label.title()} ({intensity_pct}%)"]
            
            # Check for mixed emotions
            mixed_emotions = bot_emotion.get('mixed_emotions', [])
            if mixed_emotions and len(mixed_emotions) > 1:
                # Show primary + top mixed emotion if confidence is close
                secondary_emotion, secondary_intensity = mixed_emotions[1]  # Second emotion (first is primary)
                secondary_pct = int(secondary_intensity * 100)
                
                # Only show mixed if secondary emotion is significant (>30%)
                if secondary_pct >= 30:
                    secondary_emoji = emotion_emoji.get(secondary_emotion, '💭')
                    emotion_parts[0] += f" + {secondary_emoji} {secondary_emotion.title()} ({secondary_pct}%)"
            
            # Add trajectory if available
            trajectory_data = ai_components.get('emotional_trajectory_data', {})
            bot_trajectory = trajectory_data.get('bot_trajectory', [])
            if bot_trajectory and len(bot_trajectory) > 1:
                # Show last 3-4 emotions as compact trajectory
                trajectory_emotions = [e.get('emotion', 'neutral') for e in bot_trajectory[-4:]]
                trajectory_text = " → ".join(trajectory_emotions)
                emotion_parts.append(f"  📊 Bot Trajectory: {trajectory_text}")
                
                # Show pattern if available (show all patterns including stable)
                bot_pattern = trajectory_data.get('bot_trajectory_pattern')
                if bot_pattern:
                    emotion_parts.append(f"  📈 Bot Pattern: {bot_pattern}")
            
            footer_parts.append("\n".join(emotion_parts))
    except (KeyError, TypeError, AttributeError) as e:
        logger.debug("Could not extract bot emotion for footer: %s", str(e))
    
    # 5. 💬 User Emotion (from RoBERTa analysis + Trajectory)
    try:
        user_emotion = ai_components.get('emotion_data', {})
        if user_emotion:
            user_emotion_label = user_emotion.get('primary_emotion', 'neutral')
            # Use intensity field (standard from EmotionAnalysisResult dataclass)
            user_emotion_intensity = user_emotion.get('intensity', 0.0)
            user_emotion_confidence = user_emotion.get('confidence', 0.0)
            
            # Same emotion emoji mapping (with expanded emotions)
            emotion_emoji = {
                'joy': '😊',
                'sadness': '😔',
                'anger': '😠',
                'fear': '😨',
                'surprise': '😲',
                'disgust': '🤢',
                'neutral': '😐',
                'love': '❤️',
                'admiration': '🌟',
                'curiosity': '🤔',
                'excitement': '🎉',
                'gratitude': '🙏',
                'pride': '😌',
                'relief': '😌',
                'amusement': '😄',
                'anticipation': '💭',
                'optimism': '✨',
                'disappointment': '😞',
                'nervousness': '😬'
            }
            
            emoji = emotion_emoji.get(user_emotion_label, '💭')
            intensity_pct = int(user_emotion_intensity * 100)
            
            # Build emotion display
            emotion_parts = [f"{emoji} **User Emotion**: {user_emotion_label.title()} ({intensity_pct}%)"]
            
            # Check for mixed emotions
            mixed_emotions = user_emotion.get('mixed_emotions', [])
            if mixed_emotions and len(mixed_emotions) > 1:
                # Show primary + top mixed emotion if significant
                secondary_emotion, secondary_intensity = mixed_emotions[1]  # Second emotion
                secondary_pct = int(secondary_intensity * 100)
                
                # Only show mixed if secondary emotion is significant (>30%)
                if secondary_pct >= 30:
                    secondary_emoji = emotion_emoji.get(secondary_emotion, '💭')
                    emotion_parts[0] += f" + {secondary_emoji} {secondary_emotion.title()} ({secondary_pct}%)"
            
            # Add trajectory if available
            trajectory_data = ai_components.get('emotional_trajectory_data', {})
            user_trajectory = trajectory_data.get('user_trajectory', [])
            if user_trajectory and len(user_trajectory) > 1:
                # Show last 3-4 emotions as compact trajectory
                trajectory_emotions = [e.get('emotion', 'neutral') for e in user_trajectory[-4:]]
                trajectory_text = " → ".join(trajectory_emotions)
                emotion_parts.append(f"  📊 User Trajectory: {trajectory_text}")
                
                # Show pattern if available (show all patterns including stable)
                user_pattern = trajectory_data.get('user_trajectory_pattern')
                if user_pattern:
                    emotion_parts.append(f"  📈 User Pattern: {user_pattern}")
            
            footer_parts.append("\n".join(emotion_parts))
    except (KeyError, TypeError, AttributeError) as e:
        logger.debug("Could not extract user emotion for footer: %s", str(e))
    
    # 6. ⚡ Processing Metrics
    if processing_time_ms or llm_time_ms:
        timing_parts = []
        
        if processing_time_ms:
            timing_parts.append(f"Total: {processing_time_ms}ms")
        
        if llm_time_ms:
            timing_parts.append(f"LLM: {llm_time_ms}ms")
            
            # Calculate non-LLM processing time (overhead)
            if processing_time_ms:
                overhead_ms = processing_time_ms - llm_time_ms
                if overhead_ms > 0:
                    timing_parts.append(f"Overhead: {overhead_ms}ms")
        
        if timing_parts:
            footer_parts.append(f"⚡ **Performance**: {' | '.join(timing_parts)}")
    
    # 7. 🎯 Workflow/Mode Detection
    try:
        # Check for workflow triggers or mode switches
        workflow_data = ai_components.get('workflow_result')
        if workflow_data and isinstance(workflow_data, dict):
            workflow_action = workflow_data.get('action', '')
            workflow_name = workflow_data.get('workflow_name', '')
            transaction_id = workflow_data.get('transaction_id', '')
            
            if workflow_action or workflow_name:
                workflow_info = []
                if workflow_name:
                    workflow_info.append(f"**{workflow_name}**")
                if workflow_action:
                    workflow_info.append(f"Action: {workflow_action}")
                if transaction_id:
                    workflow_info.append(f"ID: {transaction_id[:8]}")
                
                footer_parts.append(f"🎯 **Workflow**: {' | '.join(workflow_info)}")
    except (KeyError, TypeError, AttributeError) as e:
        logger.debug("Could not extract workflow data for footer: %s", str(e))
    
    # 8. 💬 Conversation Mode & Interaction Type Detection
    try:
        conv_analysis = ai_components.get('conversation_analysis', {})
        conv_intelligence = ai_components.get('conversation_intelligence', {})
        
        # Extract conversation mode and interaction type
        conversation_mode = (conv_analysis.get('mode') or 
                            conv_analysis.get('conversation_mode') or 
                            getattr(conv_intelligence, 'conversation_mode', None))
        
        interaction_type = (conv_analysis.get('interaction_type') or 
                           getattr(conv_intelligence, 'interaction_type', None))
        
        # Only show if non-standard modes detected
        if conversation_mode and conversation_mode != 'standard':
            mode_emoji = {
                'deep_conversation': '🧠',
                'casual_chat': '💬',
                'emotional_support': '💖',
                'educational': '📚',
                'playful': '🎉',
                'serious': '🎯',
                'crisis': '🆘',
                'storytelling': '📖'
            }
            
            emoji = mode_emoji.get(conversation_mode, '💬')
            mode_display = conversation_mode.replace('_', ' ').title()
            
            # Add interaction type if available and different from mode
            if interaction_type and interaction_type != 'general':
                interaction_display = interaction_type.replace('_', ' ').title()
                footer_parts.append(f"{emoji} **Mode**: {mode_display} ({interaction_display})")
            else:
                footer_parts.append(f"{emoji} **Mode**: {mode_display}")
        elif interaction_type and interaction_type != 'general':
            # Show interaction type alone if mode is standard
            interaction_display = interaction_type.replace('_', ' ').title()
            footer_parts.append(f"💬 **Interaction**: {interaction_display}")
    except (KeyError, TypeError, AttributeError) as e:
        logger.debug("Could not extract conversation mode/interaction type for footer: %s", str(e))
    
    # Build final footer
    if not footer_parts:
        return ""
    
    # Discord markdown formatting with horizontal rule separator
    # Each stat on its own line for readability
    footer = "\n\n" + "─" * 50 + "\n"
    footer += "\n".join(footer_parts)  # Each part on new line
    footer += "\n" + "─" * 50
    
    return footer


def strip_footer_from_response(response: str) -> str:
    """
    Strip status footer from bot response before storing in vector memory.
    
    CRITICAL: This ensures debug status information NEVER gets stored in
    conversation memory, preventing pollution of semantic search results.
    
    Args:
        response: Bot response potentially containing status footer
        
    Returns:
        Clean response without footer
    """
    if not response:
        return response
    
    # Look for footer separator pattern (50 dashes)
    separator = "─" * 50
    
    if separator in response:
        # Split on first occurrence of separator
        parts = response.split(separator, 1)
        if len(parts) > 1:
            # Return everything before the footer
            clean_response = parts[0].rstrip()
            logger.debug("Stripped status footer from response before memory storage")
            return clean_response
    
    # No footer found, return original
    return response
