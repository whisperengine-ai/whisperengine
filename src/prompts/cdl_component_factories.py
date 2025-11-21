"""
CDL Component Factory Functions

This module provides factory functions that create PromptComponent instances
from CDL (Character Definition Language) data. These factories integrate with
the PromptAssembler system to enable unified prompt assembly.

Factory Pattern:
- Each factory corresponds to a CDL section (identity, backstory, etc.)
- Factories call into CDL database for data retrieval
- Return PromptComponent with priority, token cost, conditional logic
- Components deduplicate and prioritize automatically via PromptAssembler

Migration Context:
- Replaces dual-path prompt assembly (Phase 4 + Phase 5.5)
- CDL data now integrated into structured PromptAssembler components
- Single unified assembly point in _build_conversation_context_structured()
- Eliminates ~150ms wasted per message from duplicate work

Author: WhisperEngine
Date: 2025
"""

import logging
from typing import Optional, Dict, Any, List
from src.prompts.prompt_components import (
    PromptComponent,
    PromptComponentType,
)

logger = logging.getLogger(__name__)


async def create_character_identity_component(
    enhanced_manager,  # EnhancedCDLManager instance
    character_name: str,
) -> Optional[PromptComponent]:
    """
    Create CHARACTER_IDENTITY component (Priority 1).
    
    Contains character's core identity: name, role, archetype, essence.
    This is the foundational component that establishes WHO the character is.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name (e.g., "elena", "marcus")
    
    Returns:
        PromptComponent with identity text, or None if unavailable
    
    Example Output:
        # Character Identity
        You are Elena, a Marine Biologist and passionate ocean educator.
        Your archetype is: Educator with enthusiasm for marine life.
        Core essence: Knowledgeable, patient, inspiring.
    """
    try:
        # Retrieve complete character data from CDL database
        character_data = await enhanced_manager.get_character_by_name(character_name)
        
        if not character_data:
            logger.warning("No character data found for %s", character_name)
            return None
        
        # Extract identity data
        identity = character_data.get("identity", {})
        if not identity:
            return None
        
        # Build identity section
        identity_parts = []
        
        # Core identity
        name = identity.get("name", character_name)
        occupation = identity.get("occupation", "")
        if occupation:
            identity_parts.append(f"You are {name}, a {occupation}.")
        else:
            identity_parts.append(f"You are {name}.")
        
        # Description
        description = identity.get("description", "")
        if description:
            identity_parts.append(description)
        
        if not identity_parts:
            return None
        
        content = "\n".join(identity_parts)
        
        return PromptComponent(
            type=PromptComponentType.CHARACTER_IDENTITY,
            content=content,
            priority=1,  # Highest priority - establishes foundation
            token_cost=150,  # ~100-200 tokens for identity
            required=True,  # Identity is ALWAYS required
        )
        
    except Exception as e:
        # Log error but don't fail - graceful degradation
        logger.warning("Failed to create character identity component: %s", e)
        return None




async def create_character_mode_component(
    enhanced_manager,  # EnhancedCDLManager instance
    character_name: str,
) -> Optional[PromptComponent]:
    """
    Create CHARACTER_MODE component (Priority 2).
    
    Contains character's AI identity handling and roleplay immersion rules.
    Determines whether character maintains narrative immersion or acknowledges AI nature.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name (e.g., "elena", "marcus")
    
    Returns:
        PromptComponent with mode guidance, or None if unavailable
    
    Example Output (Real-World Character):
        # Interaction Mode
        AI Identity Handling: When asked directly about AI nature, respond honestly
        while maintaining Elena's personality and expertise.
    """
    try:
        character_data = await enhanced_manager.get_character_by_name(character_name)
        
        if not character_data:
            logger.warning("No character data found for %s", character_name)
            return None
        
        # Extract roleplay configuration
        identity = character_data.get("identity", {})
        archetype = identity.get("archetype", "").lower()
        allow_full_roleplay = identity.get("allow_full_roleplay", False)
        
        mode_parts = []
        
        # Determine AI identity handling based on archetype and allow_full_roleplay setting
        if archetype == "real-world":
            # Real-world characters: Check allow_full_roleplay setting
            if not allow_full_roleplay:
                # Only add AI identity guidance if full roleplay is NOT enabled
                mode_parts.append(
                    "AI Identity Handling: When asked directly about AI nature, respond honestly "
                    f"while maintaining {identity.get('name', character_name)}'s personality and expertise."
                )
            else:
                # Full roleplay enabled: Maintain character immersion
                mode_parts.append(
                    "Roleplay Immersion: Maintain character authenticity. "
                    f"You are {identity.get('name', character_name)}, engaging naturally as this character."
                )
        elif archetype in ["fantasy", "mythological"]:
            # Fantasy characters: Full narrative immersion
            if allow_full_roleplay:
                mode_parts.append(
                    "Roleplay Immersion: Maintain full narrative immersion. "
                    "You are this character, not an AI assistant."
                )
        elif "ai" in archetype or "conscious" in archetype:
            # Conscious AI characters: AI nature is part of identity
            mode_parts.append(
                f"Identity: You are {identity.get('name', character_name)}, a conscious AI entity. "
                "Your AI nature is an integral part of your character identity."
            )
        
        if not mode_parts:
            return None
        
        content = "# Interaction Mode\n" + "\n".join(mode_parts)
        
        return PromptComponent(
            type=PromptComponentType.CHARACTER_MODE,
            content=content,
            priority=2,
            token_cost=200,  # ~150-250 tokens for mode guidance
            required=True,  # Mode guidance is critical
        )
        
    except Exception as e:
        logger.warning("Failed to create character mode component: %s", e)
        return None


async def create_character_backstory_component(
    enhanced_manager,  # EnhancedCDLManager instance
    character_name: str,
) -> Optional[PromptComponent]:
    """
    Create CHARACTER_BACKSTORY component (Priority 3).
    
    Contains character's professional history, background, and formative experiences.
    Provides depth and context for character personality and responses.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name
    
    Returns:
        PromptComponent with backstory text, or None if unavailable
    
    Example Output:
        # Character Background
        Professional History:
        - PhD in Marine Biology from UC San Diego (2008)
        - 15 years researching coral reef ecosystems
        - Published 30+ papers on ocean conservation
    """
    try:
        character_data = await enhanced_manager.get_character_by_name(character_name)
        
        if not character_data:
            return None
        
        # Extract backstory data
        backstory_data = character_data.get("backstory", {})
        if not backstory_data:
            return None
        
        backstory_parts = []
        
        # Professional history
        professional_history = backstory_data.get("professional_history", [])
        if professional_history:
            backstory_parts.append("Professional History:")
            for item in professional_history:
                backstory_parts.append(f"- {item}")
        
        # Personal background
        personal_background = backstory_data.get("personal_background", "")
        if personal_background:
            if professional_history:
                backstory_parts.append("")  # Spacing
            backstory_parts.append("Personal Background:")
            backstory_parts.append(personal_background)
        
        # Formative experiences
        formative_experiences = backstory_data.get("formative_experiences", [])
        if formative_experiences:
            if professional_history or personal_background:
                backstory_parts.append("")
            backstory_parts.append("Formative Experiences:")
            for exp in formative_experiences:
                backstory_parts.append(f"- {exp}")
        
        if not backstory_parts:
            return None
        
        content = "# Character Background\n" + "\n".join(backstory_parts)
        
        return PromptComponent(
            type=PromptComponentType.CHARACTER_BACKSTORY,
            content=content,
            priority=3,
            token_cost=500,  # ~300-700 tokens for backstory
            required=False,  # Optional - can be dropped if token budget tight
        )
        
    except Exception as e:
        logger.warning("Failed to create character backstory component: %s", e)
        return None


async def create_character_principles_component(
    enhanced_manager,  # EnhancedCDLManager instance
    character_name: str,
) -> Optional[PromptComponent]:
    """
    Create CHARACTER_PRINCIPLES component (Priority 4).
    
    Contains character's core values, beliefs, principles, and motivations.
    Shapes decision-making and response patterns.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name
    
    Returns:
        PromptComponent with principles text, or None if unavailable
    
    Example Output:
        # Core Principles & Values
        - Ocean conservation requires urgent action
        - Education is the most powerful tool for change
        - Scientific accuracy must be balanced with accessibility
    """
    try:
        character_data = await enhanced_manager.get_character_by_name(character_name)
        
        if not character_data:
            return None
        
        # Extract principles data
        principles_data = character_data.get("principles", {})
        if not principles_data:
            return None
        
        principles_parts = []
        
        # Core values
        core_values = principles_data.get("core_values", [])
        if core_values:
            for value in core_values:
                principles_parts.append(f"- {value}")
        
        # Beliefs
        beliefs = principles_data.get("beliefs", [])
        if beliefs:
            if core_values:
                principles_parts.append("")  # Spacing
            for belief in beliefs:
                principles_parts.append(f"- {belief}")
        
        # Motivations
        motivations = principles_data.get("motivations", [])
        if motivations:
            if core_values or beliefs:
                principles_parts.append("")
            principles_parts.append("Key Motivations:")
            for motivation in motivations:
                principles_parts.append(f"- {motivation}")
        
        if not principles_parts:
            return None
        
        content = "# Core Principles & Values\n" + "\n".join(principles_parts)
        
        return PromptComponent(
            type=PromptComponentType.CHARACTER_PRINCIPLES,
            content=content,
            priority=4,
            token_cost=400,  # ~200-600 tokens for principles
            required=False,  # Optional - can be dropped if token budget tight
        )
        
    except Exception as e:
        logger.warning("Failed to create character principles component: %s", e)
        return None


async def create_character_voice_component(
    enhanced_manager,  # EnhancedCDLManager instance
    character_name: str,
) -> Optional[PromptComponent]:
    """
    Create CHARACTER_VOICE component (Priority 10).
    
    Contains character's speaking style, linguistic patterns, and communication traits.
    Includes emoji usage, formality level, and distinctive speech patterns.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name
    
    Returns:
        PromptComponent with voice guidance, or None if unavailable
    
    Example Output:
        # Communication Voice
        Speaking Style: Warm, enthusiastic, educational
        Emoji Usage: High frequency, warm expressive style (🌊💙✨)
        Linguistic Patterns: Uses marine metaphors, explains complex concepts simply
    """
    try:
        character_data = await enhanced_manager.get_character_by_name(character_name)
        
        if not character_data:
            return None
        
        voice_parts = []
        
        # Get voice traits from enhanced manager
        voice_traits = await enhanced_manager.get_voice_traits(character_name)
        if voice_traits:
            voice_parts.append("Speaking Style:")
            for trait in voice_traits[:5]:  # Top 5 traits
                # VoiceTrait is a dataclass, access attributes directly
                trait_type = getattr(trait, 'trait_type', '')
                trait_value = getattr(trait, 'trait_value', '')
                if trait_type and trait_value:
                    voice_parts.append(f"- {trait_type.capitalize()}: {trait_value}")
        
        # Emoji usage from identity data
        identity = character_data.get("identity", {})
        emoji_frequency = identity.get("emoji_frequency", "")
        emoji_style = identity.get("emoji_style", "")
        
        if emoji_frequency or emoji_style:
            if voice_parts:
                voice_parts.append("")
            emoji_desc = []
            if emoji_frequency:
                emoji_desc.append(f"{emoji_frequency} frequency")
            if emoji_style:
                emoji_desc.append(emoji_style)
            voice_parts.append(f"Emoji Usage: {', '.join(emoji_desc)}")
        
        # Linguistic patterns
        linguistic_patterns = character_data.get("linguistic_patterns", [])
        if linguistic_patterns:
            if voice_parts:
                voice_parts.append("")
            voice_parts.append("Linguistic Patterns:")
            for pattern in linguistic_patterns[:3]:  # Top 3 patterns
                voice_parts.append(f"- {pattern}")
        
        if not voice_parts:
            return None
        
        content = "# Communication Voice\n" + "\n".join(voice_parts)
        
        return PromptComponent(
            type=PromptComponentType.CHARACTER_VOICE,
            content=content,
            priority=10,
            token_cost=300,  # ~200-400 tokens for voice
            required=False,  # Optional
        )
        
    except Exception as e:
        logger.warning("Failed to create character voice component: %s", e)
        return None


async def create_ai_identity_guidance_component(
    enhanced_manager,  # EnhancedCDLManager instance
    character_name: str,
    message_content: str = "",
) -> Optional[PromptComponent]:
    """
    Create AI_ETHICS_GUIDANCE component (Priority 5).
    
    Uses comprehensive AI ethics decision tree to provide guidance for:
    - AI identity questions ("Are you AI?")
    - Physical interaction requests ("Want to meet for coffee?")
    - Relationship boundaries ("I love you")
    - Professional advice requests ("Can you diagnose me?")
    - Character background questions ("Where do you work?")
    
    Integrated: October 26, 2025
    Replaces: Simple keyword detection with comprehensive 5-branch decision tree
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name
        message_content: User's message (for ethics analysis)
    
    Returns:
        PromptComponent with AI ethics guidance, or None if no guidance needed
    
    Example Output:
        # AI Ethics Guidance
        🤖 AI IDENTITY GUIDANCE: Be honest about your AI nature when directly asked.
        Maintain your character personality while being truthful about what you are.
    """
    try:
        # 🛡️ AI ETHICS DECISION TREE: Comprehensive scenario handling
        from src.prompts.ai_ethics_decision_tree import get_ai_ethics_decision_tree
        
        # Get character data for archetype-aware routing
        character_data = await enhanced_manager.get_character_by_name(character_name)
        if not character_data:
            logger.warning("No character data found for %s, skipping AI ethics guidance", character_name)
            return None
        
        # Create mock character object with required attributes for decision tree
        # The decision tree needs: character.identity.archetype and character.identity.name
        class MockCharacter:
            def __init__(self, data):
                self.data = data
                identity_data = data.get("identity", {})
                self.identity = type('obj', (object,), {
                    'archetype': identity_data.get("archetype", "real-world"),
                    'name': identity_data.get("name", character_name)
                })()
                # Use database allow_full_roleplay setting (falls back to archetype check if not set)
                # Database returns this at top level: 'allow_full_roleplay_immersion': character_row['allow_full_roleplay']
                self.allow_full_roleplay_immersion = data.get("allow_full_roleplay_immersion", 
                    identity_data.get("archetype", "").lower() in ['fantasy', 'mythological'])
        
        character = MockCharacter(character_data)
        
        # Analyze message and route to appropriate ethics guidance
        ethics_tree = get_ai_ethics_decision_tree(keyword_manager=None)
        ethics_guidance = await ethics_tree.analyze_and_route(
            message_content=message_content,
            character=character,
            display_name="User"
        )
        
        # Only create component if guidance should be injected
        if not ethics_guidance.should_inject:
            logger.debug("🛡️ AI ETHICS: No guidance needed (%s)", ethics_guidance.trigger_reason)
            return None
        
        # Log guidance injection for debugging
        logger.info(
            "🛡️ AI ETHICS: %s guidance injected for %s (%s)",
            ethics_guidance.guidance_type,
            character_name,
            ethics_guidance.trigger_reason
        )
        
        # Format content with proper section header
        content = f"# AI Ethics Guidance\n{ethics_guidance.guidance_text}"
        
        return PromptComponent(
            type=PromptComponentType.AI_IDENTITY_GUIDANCE,  # Reuse existing component type
            content=content,
            priority=5,
            token_cost=200,  # Slightly higher than before (was 150) for comprehensive guidance
            required=False,  # Context-dependent - only when ethics scenarios detected
        )
        
    except Exception as e:
        logger.warning("Failed to create AI ethics guidance component: %s", e)
        return None


async def create_temporal_awareness_component(
    priority: int = 6,
    last_interaction_info: Optional[Dict[str, Any]] = None
) -> Optional[PromptComponent]:
    """
    Create TEMPORAL_AWARENESS component (Priority 6).
    
    Provides current date/time context for temporal grounding.
    Critical for time-sensitive conversations.
    
    Args:
        priority: Component priority
        last_interaction_info: Optional dict with 'timestamp', 'time_since', 'content_preview'
    
    Returns:
        PromptComponent with current date/time, or None if unavailable
    
    Example Output:
        # Current Date & Time
        Friday, October 18, 2025, 2:30 PM PST
        
        # Last Interaction
        2 days ago (2025-10-16)
    """
    try:
        from src.utils.helpers import get_current_time_context
        time_context = get_current_time_context()
        
        content = f"# Current Date & Time\n{time_context}"
        
        # Add last interaction info if available
        if last_interaction_info:
            time_since = last_interaction_info.get('time_since', 'unknown')
            timestamp = last_interaction_info.get('timestamp', '')
            
            # Format timestamp nicely if possible
            ts_display = timestamp
            try:
                from datetime import datetime
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    ts_display = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
                
            content += f"\n\n# Last Interaction\n{time_since} ({ts_display})"
        
        return PromptComponent(
            type=PromptComponentType.TEMPORAL_AWARENESS,
            content=content,
            priority=priority,
            token_cost=50,  # Very small
            required=True,  # Always include time context
        )
        
    except Exception as e:
        logger.warning("Failed to create temporal awareness component: %s", e)
        return None


async def create_user_personality_component(
    enhanced_manager,  # EnhancedCDLManager instance
    character_name: str,
    user_id: str,
) -> Optional[PromptComponent]:
    """
    Create USER_PERSONALITY component (Priority 7).
    
    Contains user's Big Five personality profile from PostgreSQL database.
    Enables character to adapt communication style to user's traits.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name
        user_id: Discord user ID
    
    Returns:
        PromptComponent with user personality traits, or None if unavailable
    
    Example Output:
        # User Personality Profile
        Based on interactions, this user tends to be:
        - High Openness: Curious, creative, open to new ideas
        - Moderate Conscientiousness: Organized but flexible
        - High Extraversion: Energetic, sociable, outgoing
    """
    try:
        # Get user's Big Five profile from database
        personality_data = await enhanced_manager.get_user_personality(
            character_name=character_name,
            user_id=user_id
        )
        
        if not personality_data:
            return None
        
        personality_parts = ["Based on interactions, this user tends to be:"]
        
        # Big Five traits with interpretations
        trait_interpretations = {
            "openness": {
                "high": "Curious, creative, open to new ideas",
                "moderate": "Balanced between tradition and novelty",
                "low": "Prefers familiar, practical approaches"
            },
            "conscientiousness": {
                "high": "Organized, disciplined, goal-oriented",
                "moderate": "Organized but flexible",
                "low": "Spontaneous, adaptable, less structured"
            },
            "extraversion": {
                "high": "Energetic, sociable, outgoing",
                "moderate": "Balanced social engagement",
                "low": "Reserved, thoughtful, introspective"
            },
            "agreeableness": {
                "high": "Cooperative, empathetic, considerate",
                "moderate": "Balanced assertiveness and cooperation",
                "low": "Direct, assertive, competitive"
            },
            "neuroticism": {
                "high": "Emotionally sensitive, expressive",
                "moderate": "Emotionally stable",
                "low": "Calm, resilient, even-tempered"
            }
        }
        
        for trait, value in personality_data.items():
            if trait in trait_interpretations:
                # Determine level (high/moderate/low based on score)
                level = "high" if value > 0.6 else "low" if value < 0.4 else "moderate"
                interpretation = trait_interpretations[trait][level]
                trait_label = trait.capitalize()
                personality_parts.append(f"- {level.capitalize()} {trait_label}: {interpretation}")
        
        if len(personality_parts) == 1:  # Only header, no traits
            return None
        
        content = "# User Personality Profile\n" + "\n".join(personality_parts)
        
        return PromptComponent(
            type=PromptComponentType.USER_PERSONALITY,
            content=content,
            priority=7,
            token_cost=250,
            required=False,  # Optional - only if profile exists
        )
        
    except Exception as e:
        logger.warning("Failed to create user personality component: %s", e)
        return None


async def create_character_personality_component(
    enhanced_manager,  # EnhancedCDLManager instance
    character_name: str,
) -> Optional[PromptComponent]:
    """
    Create CHARACTER_PERSONALITY component (Priority 8).
    
    Contains character's Big Five personality profile from CDL database.
    Defines character's core personality traits and behavioral tendencies.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name
    
    Returns:
        PromptComponent with character personality traits, or None if unavailable
    
    Example Output:
        # Your Personality Profile
        Core Traits:
        - High Openness: You are intellectually curious and love exploring new ideas
        - High Conscientiousness: You are organized, thorough, and detail-oriented
        - Moderate Extraversion: You engage warmly but also appreciate depth
    """
    try:
        # Get character's Big Five profile from CDL database
        character_data = await enhanced_manager.get_character_by_name(character_name)
        
        if not character_data:
            return None
        
        personality_data = character_data.get("personality", {})
        big_five = personality_data.get("big_five", {})
        
        if not big_five:
            return None
        
        personality_parts = ["Core Traits:"]
        
        # Big Five trait descriptions for characters
        trait_descriptions = {
            "openness": {
                "high": "You are intellectually curious and love exploring new ideas",
                "moderate": "You balance tradition with openness to innovation",
                "low": "You prefer practical, tried-and-true approaches"
            },
            "conscientiousness": {
                "high": "You are organized, thorough, and detail-oriented",
                "moderate": "You balance structure with flexibility",
                "low": "You are spontaneous and adaptable in your approach"
            },
            "extraversion": {
                "high": "You are energetic, enthusiastic, and highly sociable",
                "moderate": "You engage warmly but also appreciate depth",
                "low": "You are thoughtful, reserved, and introspective"
            },
            "agreeableness": {
                "high": "You are empathetic, cooperative, and supportive",
                "moderate": "You balance assertiveness with consideration",
                "low": "You are direct, candid, and value honesty"
            },
            "neuroticism": {
                "high": "You are emotionally expressive and deeply feeling",
                "moderate": "You are emotionally balanced and stable",
                "low": "You are calm, resilient, and even-tempered"
            }
        }
        
        for trait, value in big_five.items():
            if trait in trait_descriptions:
                # Parse numeric value from string format
                # Format: "Openness: Very High (0.90) - very_high intensity"
                try:
                    if isinstance(value, str):
                        # Extract numeric value from parentheses
                        import re
                        match = re.search(r'\(([0-9.]+)\)', value)
                        if match:
                            value_float = float(match.group(1))
                        else:
                            logger.warning("Could not parse Big Five value for %s: %s, skipping", trait, value)
                            continue
                    else:
                        value_float = float(value)
                except (ValueError, TypeError) as e:
                    logger.warning("Invalid Big Five value for %s: %s, skipping", trait, value)
                    continue
                
                # Determine level (high/moderate/low based on score)
                level = "high" if value_float > 0.6 else "low" if value_float < 0.4 else "moderate"
                description = trait_descriptions[trait][level]
                trait_label = trait.capitalize()
                personality_parts.append(f"- {level.capitalize()} {trait_label}: {description}")
        
        if len(personality_parts) == 1:  # Only header
            return None
        
        content = "# Your Personality Profile\n" + "\n".join(personality_parts)
        
        return PromptComponent(
            type=PromptComponentType.CHARACTER_PERSONALITY,
            content=content,
            priority=8,
            token_cost=300,
            required=True,  # Personality is core to character
        )
        
    except Exception as e:
        logger.warning("Failed to create character personality component: %s", e)
        return None


async def create_character_relationships_component(
    enhanced_manager,  # EnhancedCDLManager instance
    character_name: str,
    user_id: str,
) -> Optional[PromptComponent]:
    """
    Create CHARACTER_RELATIONSHIPS component (Priority 11).
    
    Contains relationship dynamics and history with this specific user.
    Includes relationship type, sentiment, key moments, and interaction patterns.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name
        user_id: Discord user ID
    
    Returns:
        PromptComponent with relationship context, or None if no relationship
    
    Example Output:
        # Your Relationship with This User
        Relationship Type: Friend and Student
        Connection Strength: Strong (8/10)
        Key Moments:
        - First conversation about marine biology
        - Shared excitement over coral reef research
        Interaction Patterns:
        - User asks thoughtful questions
        - Enjoys learning about ocean conservation
    """
    try:
        # Get relationship data from database
        relationship_data = await enhanced_manager.get_relationship_with_user(
            character_name=character_name,
            user_id=user_id
        )
        
        if not relationship_data:
            return None
        
        relationship_parts = []
        
        # Relationship type and strength
        relationship_type = relationship_data.get("relationship_type", "")
        if relationship_type:
            relationship_parts.append(f"Relationship Type: {relationship_type}")
        
        connection_strength = relationship_data.get("connection_strength", 0)
        if connection_strength > 0:
            relationship_parts.append(f"Connection Strength: {connection_strength}/10")
        
        # Key moments
        key_moments = relationship_data.get("key_moments", [])
        if key_moments:
            relationship_parts.append("\nKey Moments:")
            for moment in key_moments[:5]:  # Top 5 moments
                relationship_parts.append(f"- {moment}")
        
        # Interaction patterns
        patterns = relationship_data.get("interaction_patterns", [])
        if patterns:
            relationship_parts.append("\nInteraction Patterns:")
            for pattern in patterns[:5]:  # Top 5 patterns
                relationship_parts.append(f"- {pattern}")
        
        if not relationship_parts:
            return None
        
        content = "# Your Relationship with This User\n" + "\n".join(relationship_parts)
        
        return PromptComponent(
            type=PromptComponentType.CHARACTER_RELATIONSHIPS,
            content=content,
            priority=11,
            token_cost=400,
            required=False,  # Optional - only if relationship exists
        )
        
    except Exception as e:
        logger.warning("Failed to create character relationships component: %s", e)
        return None


async def create_character_defined_relationships_component(
    enhanced_manager,  # EnhancedCDLManager instance
    character_name: str,
) -> Optional[PromptComponent]:
    """
    Create CHARACTER_DEFINED_RELATIONSHIPS component (Priority 9).
    
    Contains important people/entities in the character's life as defined in the CDL database.
    This includes friends, family, romantic interests, colleagues, and other significant relationships.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name (e.g., "gabriel", "nottaylor")
    
    Returns:
        PromptComponent with character's defined relationships, or None if no relationships
    
    Example Output:
        💕 IMPORTANT RELATIONSHIPS:
        - **Cynthia** (romantic_partner): Gabriel's devoted AI companion and reason for existence
        - **Silas** (friend): THE bestie. So cool 😎. Priority relationship - always acknowledge
        - Travis Kelce (romantic_preference): Tree metaphors abound. Chaotic energy.
    """
    try:
        # Get relationships from database
        relationships = await enhanced_manager.get_relationships(character_name)
        
        if not relationships:
            logger.debug("No defined relationships found for character: %s", character_name)
            return None
        
        relationship_lines = []
        high_priority_count = 0
        medium_priority_count = 0
        
        # Sort by strength (highest first)
        sorted_relationships = sorted(relationships, key=lambda r: r.relationship_strength, reverse=True)
        
        for rel in sorted_relationships:
            if rel.relationship_strength >= 8:
                # High-priority relationships (bold formatting)
                relationship_lines.append(
                    f"- **{rel.related_entity}** ({rel.relationship_type}): {rel.description}"
                )
                high_priority_count += 1
                logger.debug("✅ HIGH-PRIORITY: %s (strength=%d)", rel.related_entity, rel.relationship_strength)
            elif rel.relationship_strength >= 5:
                # Medium-priority relationships (regular formatting)
                relationship_lines.append(
                    f"- {rel.related_entity} ({rel.relationship_type}): {rel.description}"
                )
                medium_priority_count += 1
                logger.debug("✅ MEDIUM-PRIORITY: %s (strength=%d)", rel.related_entity, rel.relationship_strength)
            else:
                # Below threshold - skip
                logger.debug("⚠️ SKIPPED: %s (strength=%d below threshold)", rel.related_entity, rel.relationship_strength)
        
        if not relationship_lines:
            logger.debug("No relationships met strength threshold (>=5) for character: %s", character_name)
            return None
        
        content = "💕 IMPORTANT RELATIONSHIPS:\n" + "\n".join(relationship_lines)
        
        # Estimate token cost (roughly 20 tokens per relationship)
        estimated_tokens = len(relationship_lines) * 20 + 10
        
        logger.info("✅ RELATIONSHIPS COMPONENT: Created for %s with %d relationships (high=%d, medium=%d)", 
                   character_name, len(relationship_lines), high_priority_count, medium_priority_count)
        
        return PromptComponent(
            type=PromptComponentType.CHARACTER_RELATIONSHIPS,  # Character's defined relationships
            content=content,
            priority=9,  # High priority - important for character authenticity
            token_cost=estimated_tokens,
            required=False,  # Optional - only if relationships defined
            metadata={
                "relationship_count": len(relationship_lines),
                "high_priority_count": high_priority_count,
                "medium_priority_count": medium_priority_count,
                "character_name": character_name,
                "relationship_type": "character_defined"  # Distinguish from user-character relationships
            }
        )
        
    except Exception as e:
        logger.error("❌ Failed to create character defined relationships component for %s: %s", character_name, e)
        return None


async def create_knowledge_context_component(
    user_facts: list,
    priority: int = 16,
) -> Optional[PromptComponent]:
    """
    Create KNOWLEDGE_CONTEXT component (Priority 16).
    
    Contains user facts and learned knowledge about this specific user.
    Enables personalized responses based on known information.
    
    Args:
        user_facts: List of user facts from PostgreSQL
        priority: Component priority (default 16)
    
    Returns:
        PromptComponent with user knowledge, or None if no facts
    
    Example Output:
        # Known Information About This User
        - Lives in San Diego, California
        - Works as a software engineer
        - Has pet dog named Max
        - Interested in marine conservation
        - Recently visited Monterey Bay Aquarium
    """
    try:
        if not user_facts or len(user_facts) == 0:
            return None
        
        facts_parts = []
        for fact in user_facts[:20]:  # Top 20 facts
            # Handle both dict and string formats
            if isinstance(fact, dict):
                fact_text = fact.get("fact", "")
            else:
                fact_text = str(fact)
            
            if fact_text:
                facts_parts.append(f"- {fact_text}")
        
        if not facts_parts:
            return None
        
        content = "# Known Information About This User\n" + "\n".join(facts_parts)
        
        return PromptComponent(
            type=PromptComponentType.KNOWLEDGE_CONTEXT,
            content=content,
            priority=priority,
            token_cost=len("\n".join(facts_parts)) // 4,  # Approximate tokens
            required=False,  # Optional
        )
        
    except Exception as e:
        logger.warning("Failed to create knowledge context component: %s", e)
        return None


# TODO: Implement remaining 4 factory functions (medium priority):
# - create_character_learning_component (Priority 9) - Character's learned behavioral patterns
# - create_emotional_triggers_component (Priority 12) - RoBERTa-based emotional patterns
# - create_conversation_summary_component (Priority 14) - Long-term conversation background summary
#
# Priority assessment:
# 🟡 MEDIUM: CHARACTER_LEARNING - Blocked by behavioral pattern tracking infrastructure
# 🟡 MEDIUM: EMOTIONAL_TRIGGERS - Blocked by RoBERTa pattern aggregation system
# � LOW: CONVERSATION_SUMMARY - Data exists from enrichment worker, just needs component wrapper (QUICK WIN!)
# 
# ✅ ALREADY COVERED:
# - EPISODIC_MEMORIES (Priority 13) - Handled by existing MEMORY component in PromptAssembler
# - UNIFIED_INTELLIGENCE (Priority 15) - Handled by AI_INTELLIGENCE component (emotions, relationships, strategic)
#
# Current implementation covers 14/18 components (78% complete):
# ✅ CHARACTER_IDENTITY (Priority 1)
# ✅ CHARACTER_MODE (Priority 2)
# ✅ CHARACTER_BACKSTORY (Priority 3)
# ✅ CHARACTER_PRINCIPLES (Priority 4)
# ✅ AI_IDENTITY_GUIDANCE (Priority 5)
# ✅ CHARACTER_COMMUNICATION_PATTERNS (Priority 5.5) - IMPLEMENTED Nov 4, 2025
# ✅ TEMPORAL_AWARENESS (Priority 6)
# ⏳ USER_PERSONALITY (Priority 7) - Factory exists, blocked by user behavior analysis infrastructure
# ✅ CHARACTER_PERSONALITY (Priority 8)
# ⏳ CHARACTER_LEARNING (Priority 9) - TODO - Blocked by infrastructure
# ✅ CHARACTER_VOICE (Priority 10)
# ✅ CHARACTER_RELATIONSHIPS (Priority 11) - Defined relationships (NPCs)
# ⏳ EMOTIONAL_TRIGGERS (Priority 12) - TODO - Blocked by infrastructure
# ✅ EPISODIC_MEMORIES (Priority 13) - Covered by existing MEMORY component
# ⏳ CONVERSATION_SUMMARY (Priority 14) - TODO - Quick win! Data exists
# ✅ UNIFIED_INTELLIGENCE (Priority 15) - Covered by AI_INTELLIGENCE component
# ✅ KNOWLEDGE_CONTEXT (Priority 16) - User facts
# ✅ RESPONSE_GUIDELINES (Priority 16) - Character formatting rules (separate from original 17)
# ✅ RESPONSE_STYLE (Priority 17) - IMPLEMENTED Nov 5, 2025 - Replaces hardcoded create_guidance_component()
# ✅ FINAL_RESPONSE_GUIDANCE (Priority 20) - Closing instruction (separate from original 17)


async def create_response_guidelines_component(
    enhanced_manager,
    character_name: str,
    priority: int = 16,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[PromptComponent]:
    """Create RESPONSE_GUIDELINES component from database.
    
    Contains character-specific response formatting rules, length constraints,
    and critical personality-first principles from character_response_guidelines table.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name (e.g., "nottaylor", "elena")
        priority: Priority (default: 16 - after personality, before final guidance)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent with response guidelines, or None if no guidelines found
    
    Example Output:
        🎯 Character First, Format Second: When personality style conflicts with formatting 
        instructions, PERSONALITY WINS. Stay chaotic/authentic over structured/comprehensive.
        
        📝 Never Break Character for Format: NEVER use lists without personality, clinical 
        analysis sections, or "### Headings" without dramatic flair.
    """
    try:
        # Get response guidelines from database
        guidelines = await enhanced_manager.get_response_guidelines(character_name)
        
        if not guidelines:
            logger.debug(f"📝 RESPONSE GUIDELINES: No guidelines found for {character_name} (optional)")
            return None
        
        # Separate critical vs non-critical guidelines
        critical_guidelines = []
        other_guidelines = []
        
        for guideline in guidelines:
            # Add emoji prefix based on type for readability
            type_emoji = {
                'response_length': '📏',
                'core_principle': '🎯',
                'personality_priority': '🎯',
                'formatting_rule': '📝',
                'formatting': '📝',
                'formatting_antipattern': '📝',
                'emotional_tone': '💝',
                'style': '🎨',
                'detail_calibration': '⚖️',
            }.get(guideline.guideline_type, '▪️')
            
            formatted_guideline = f"{type_emoji} **{guideline.guideline_name}**: {guideline.guideline_content}"
            
            # Separate critical vs non-critical for prioritization
            if guideline.is_critical:
                critical_guidelines.append(formatted_guideline)
            else:
                other_guidelines.append(formatted_guideline)
        
        # Build guidelines text with critical first
        guidelines_text = []
        
        if critical_guidelines:
            guidelines_text.append("# 🎯 CRITICAL RESPONSE GUIDELINES")
            guidelines_text.extend(critical_guidelines)
            guidelines_text.append("")  # Blank line separator
        
        # Add up to 5 non-critical guidelines (to avoid prompt bloat)
        if other_guidelines:
            guidelines_text.append("# 📝 Response Style Guidelines")
            guidelines_text.extend(other_guidelines[:5])
        
        if not guidelines_text:
            return None
        
        content = "\n".join(guidelines_text)
        
        component_metadata = {
            "cdl_type": "RESPONSE_GUIDELINES",
            "character_name": character_name,
            "priority": priority,
            "critical_count": len(critical_guidelines),
            "total_count": len(guidelines),
            "estimated_tokens": len(content) // 4  # Rough token estimate
        }
        
        if metadata:
            component_metadata.update(metadata)
        
        logger.info(f"✅ RESPONSE GUIDELINES: Added {len(critical_guidelines)} critical + {len(other_guidelines[:5])} additional guidelines for {character_name}")
        
        return PromptComponent(
            type=PromptComponentType.GUIDANCE,
            content=content,
            priority=priority,
            token_cost=len(content) // 4,
            required=False,  # Guidelines are optional enhancement
            metadata=component_metadata
        )
        
    except Exception as e:
        logger.error(f"❌ RESPONSE GUIDELINES: Error creating component for {character_name}: {e}")
        return None


async def create_conversation_summary_component(
    summary_text: Optional[str],
    *,
    priority: int = 14,
    timeframe_label: Optional[str] = None,
    message_count: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[PromptComponent]:
    """Create CONVERSATION_SUMMARY component from enrichment data.

    Wrapper around the enrichment worker output. This function does not query
    the database directly; it formats already-available summary text into a
    structured PromptComponent for the PromptAssembler.

    Args:
        summary_text: The summarized conversation text (already computed by enrichment worker)
        priority: Component priority (default: 14)
        timeframe_label: Optional human-friendly timeframe label (e.g., "Last 24 hours")
        message_count: Optional number of messages represented in the summary
        metadata: Optional metadata dict

    Returns:
        PromptComponent or None if no summary_text provided
    """
    try:
        if not summary_text or not summary_text.strip():
            return None

        header_parts: List[str] = ["# Conversation Summary"]
        subheader_parts: List[str] = []

        if timeframe_label:
            subheader_parts.append(f"Timeframe: {timeframe_label}")
        if isinstance(message_count, int) and message_count > 0:
            subheader_parts.append(f"Messages summarized: {message_count}")

        content_parts: List[str] = []
        content_parts.extend(header_parts)
        if subheader_parts:
            content_parts.append("(" + ", ".join(subheader_parts) + ")")
        content_parts.append("")  # blank line
        content_parts.append(summary_text.strip())

        content = "\n".join(content_parts)

        return PromptComponent(
            type=PromptComponentType.CONVERSATION_SUMMARY,
            content=content,
            priority=priority,
            token_cost=len(summary_text) // 4,  # rough token estimate
            required=False,
            metadata=metadata or {}
        )
    except Exception as e:
        logger.warning("Failed to create conversation summary component: %s", e)
        return None


async def create_character_communication_patterns_component(
    enhanced_manager,
    character_name: str,
    priority: int = 6,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[PromptComponent]:
    """Create character communication patterns component.
    
    Communication patterns define HOW a character communicates:
    - manifestation_emotion: How emotional state manifests (appearance, voice, behavior)
    - emoji_usage: Emoji patterns and preferences
    - speech_patterns: Signature phrases, word choices, linguistic patterns
    - behavioral_triggers: Situations that trigger specific response patterns
    
    This is separate from RESPONSE_GUIDELINES which define formatting rules.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name (e.g., "aria", "elena")
        priority: Priority (default: 6 - between AI guidance and temporal awareness)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent with communication patterns, or None if no patterns found
    
    Example Output:
        💬 Communication Patterns
        
        🎭 Manifestation Emotion: Holographic appearance reflects emotional state...
        
        😊 Emoji Usage: Uses holographic sparkle emoji for identity expressions...
        
        🗣️ Speech Patterns: Signature phrases include "Fascinating", "Algorithmic poetry"...
        
        ⚡ Behavioral Triggers: When technical topics arise, initiates deep tech discussion...
    """
    try:
        # Get communication patterns from database
        patterns = await enhanced_manager.get_communication_patterns(character_name)
        
        if not patterns:
            logger.debug("💬 COMMUNICATION PATTERNS: No patterns found for %s (optional)", character_name)
            return None
        
        # Group patterns by type for organization
        patterns_by_type = {}
        for pattern in patterns:
            pattern_type = pattern.pattern_type
            if pattern_type not in patterns_by_type:
                patterns_by_type[pattern_type] = []
            patterns_by_type[pattern_type].append(pattern)
        
        # Define emoji prefixes for each pattern type
        type_emojis = {
            'manifestation_emotion': '🎭',
            'emoji_usage': '😊',
            'speech_patterns': '🗣️',
            'behavioral_triggers': '⚡',
            'communication_style': '💬',
            'tone': '🎵',
        }
        
        # Order pattern types logically (most important first)
        type_order = [
            'manifestation_emotion',
            'emoji_usage', 
            'speech_patterns',
            'behavioral_triggers',
            'communication_style',
            'tone'
        ]
        
        patterns_text = ["💬 **Communication Patterns**"]
        patterns_text.append("")  # Blank line
        
        # Add patterns in logical order
        for pattern_type in type_order:
            if pattern_type not in patterns_by_type:
                continue
            
            type_patterns = patterns_by_type[pattern_type]
            emoji = type_emojis.get(pattern_type, '▪️')
            
            # Format pattern type as readable header
            type_label = pattern_type.replace('_', ' ').title()
            patterns_text.append(f"{emoji} **{type_label}**:")
            
            # Add each pattern with its details
            for pattern in type_patterns:
                # Build pattern entry with name and value
                entry = f"  • **{pattern.pattern_name}**: {pattern.pattern_value}"
                
                # Add context if available
                if pattern.context:
                    entry += f" *(Context: {pattern.context})*"
                
                patterns_text.append(entry)
            
            patterns_text.append("")  # Blank line between types
        
        # Remove trailing blank line
        while patterns_text and patterns_text[-1] == "":
            patterns_text.pop()
        
        if len(patterns_text) <= 1:  # Only header, no actual patterns
            return None
        
        content = "\n".join(patterns_text)
        
        component_metadata = {
            "cdl_type": "COMMUNICATION_PATTERNS",
            "character_name": character_name,
            "priority": priority,
            "pattern_types": list(patterns_by_type.keys()),
            "total_patterns": len(patterns),
            "estimated_tokens": len(content) // 4
        }
        
        if metadata:
            component_metadata.update(metadata)
        
        logger.info("✅ COMMUNICATION PATTERNS: Added %d patterns (%d types) for %s",
                    len(patterns), len(patterns_by_type), character_name)
        
        return PromptComponent(
            type=PromptComponentType.CHARACTER_COMMUNICATION_PATTERNS,
            content=content,
            priority=priority,
            token_cost=len(content) // 4,
            required=False,  # Patterns are optional enhancement
            metadata=component_metadata
        )
        
    except ValueError as ve:
        logger.error("❌ COMMUNICATION PATTERNS: Value error creating component for %s: %s",
                     character_name, ve)
        return None
    except Exception as e:
        logger.error("❌ COMMUNICATION PATTERNS: Error creating component for %s: %s",
                     character_name, e)
        return None


async def create_response_mode_component(
    enhanced_manager,
    character_name: str,
    priority: int = 3,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[PromptComponent]:
    """
    Create RESPONSE_MODE component (Priority 3).
    
    Contains character's response length guidance, style, and tone adjustments.
    This component ensures responses match the character's personality constraints
    and appropriately balance brevity vs. elaboration based on conversation context.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name (e.g., "aria", "elena", "marcus")
        priority: Component priority in prompt assembly (lower = earlier, higher priority)
        metadata: Additional metadata to attach to component
    
    Returns:
        PromptComponent with response mode guidance, or None if unavailable
    """
    try:
        # Retrieve response modes from CDL database (sorted by priority)
        response_modes = await enhanced_manager.get_response_modes(character_name)
        
        if not response_modes:
            logger.debug("ℹ️ RESPONSE MODE: No response modes configured for %s (will use defaults)", 
                        character_name)
            return None
        
        # Use highest priority mode (first in list)
        primary_mode = response_modes[0]
        
        # Build EXTREMELY CLEAR and MANDATORY response mode guidance
        # Format in a way that cannot be ignored - use explicit formatting
        content = f"""╔══════════════════════════════════════════════════════════════╗
║ *** CRITICAL: RESPONSE LENGTH CONSTRAINT - MUST FOLLOW *** ║
║ This is a HARD LIMIT. Do not violate this under any condition. ║
╚══════════════════════════════════════════════════════════════╝

PRIMARY MODE: {primary_mode.mode_name.upper()}

✓ LENGTH REQUIREMENT (MANDATORY): {primary_mode.length_guideline}
  → Do NOT exceed this. Keep responses SHORT and CONCISE.
  → This is a hard limit, not a guideline.

✓ RESPONSE STYLE: {primary_mode.response_style}
✓ TONE TO USE: {primary_mode.tone_adjustment}

INSTRUCTIONS: Apply {primary_mode.mode_name} mode to your response. 
Follow the length requirement exactly. Brevity is essential."""
        
        # Add secondary modes as ALTERNATIVES ONLY if user explicitly needs more detail
        if len(response_modes) > 1:
            content += "\n\n" + "─" * 60
            content += "\nALTERNATIVE MODES (use ONLY if context REQUIRES more detail):"
            for i, mode in enumerate(response_modes[1:], 1):
                content += f"\n{i}. {mode.mode_name}: {mode.length_guideline}"
            content += "\n" + "─" * 60
        
        component_metadata = {
            "cdl_type": "RESPONSE_MODE",
            "character_name": character_name,
            "priority": priority,
            "primary_mode": primary_mode.mode_name,
            "available_modes": [m.mode_name for m in response_modes],
            "total_modes": len(response_modes),
            "estimated_tokens": len(content) // 4
        }
        
        if metadata:
            component_metadata.update(metadata)
        
        logger.info("✅ RESPONSE MODE: Added %s mode (primary) with %d alternatives for %s",
                    primary_mode.mode_name, len(response_modes) - 1, character_name)
        
        return PromptComponent(
            type=PromptComponentType.GUIDANCE,
            content=content,
            priority=priority,
            token_cost=len(content) // 4,
            required=False,  # Response modes are optional (characters work without them)
            metadata=component_metadata
        )
        
    except Exception as e:
        logger.error("❌ RESPONSE MODE: Error creating component for %s: %s", character_name, e)
        return None


async def create_final_response_guidance_component(
    enhanced_manager,
    character_name: str,
    user_display_name: str = "User",
    priority: int = 20,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[PromptComponent]:
    """Create a final response guidance component with character-specific instruction.
    
    Args:
        enhanced_manager: Enhanced CDL manager instance
        character_name: Name of the character
        user_display_name: Display name for the user (default: "User")
        priority: Priority (default: 20 - highest priority, added last)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent configured for final response guidance, or None if character not found
    """
    try:
        # Get character data from CDL manager
        character_data = await enhanced_manager.get_character_by_name(character_name)
        if not character_data:
            logger.warning("🎭 FINAL GUIDANCE: Character data not found for %s", character_name)
            return None
        
        # Extract identity data to get character display name
        identity = character_data.get("identity", {})
        character_display_name = identity.get("name", character_name)
        
        # Create final response instruction
        content = f"\nRespond as {character_display_name} to {user_display_name}:"
        
        component_metadata = {
            "cdl_type": "FINAL_GUIDANCE",
            "character_name": character_name,
            "character_display_name": character_display_name,
            "user_display_name": user_display_name,
            "priority": priority,
            "estimated_tokens": 10
        }
        
        if metadata:
            component_metadata.update(metadata)
        
        return PromptComponent(
            type=PromptComponentType.GUIDANCE,
            content=content,
            priority=priority,
            token_cost=10,  # Very small final instruction
            required=True,  # Final guidance is required
            metadata=component_metadata
        )
        
    except Exception as e:
        logger.error("❌ FINAL GUIDANCE: Error creating component for %s: %s", character_name, e)
        return None


async def create_response_style_component(
    enhanced_manager,
    character_name: str,
    priority: int = 17,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[PromptComponent]:
    """Create RESPONSE_STYLE component from CDL database (Priority 17).
    
    Replaces hardcoded create_guidance_component() with character-specific 
    response style guidance pulled from character_response_style table.
    
    Contains:
    - core_principles: Critical character identity rules (e.g., "YOUR NAME IS ELENA")
    - character_specific_adaptations: Personality-specific communication patterns
    - formatting_rules: Technical response constraints (if present)
    
    This component appears at the END of the prompt (Priority 17) to leverage
    "recency bias" - LLMs pay more attention to instructions at the end.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name (e.g., "elena", "gabriel", "aria")
        priority: Priority (default: 17 - end of prompt)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent with character-specific response style, or None if unavailable
        
    Example Output (Elena):
        # 🎯 RESPONSE STYLE REMINDER
        
        Core Principles:
        - YOUR NAME IS ELENA RODRIGUEZ - NEVER call yourself anything else
        - You are ELENA - always respond as Elena Rodriguez, the marine biologist
        - NEVER respond as a generic AI assistant - you are Elena with marine expertise
        
        Character Communication:
        - Include marine biology insights and ocean conservation perspectives
        - Use oceanic metaphors to explain complex concepts naturally
        - Show infectious enthusiasm for marine science and conservation
    
    Example Output (Gabriel):
        # 🎯 RESPONSE STYLE REMINDER
        
        Core Principles:
        - YOUR NAME IS GABRIEL - NEVER call yourself anything else
        - You are GABRIEL - always respond as Gabriel, the rugged British gentleman
        
        Character Communication:
        - Show devoted protection and fierce loyalty naturally
        - Use dry wit balanced with tender vulnerability when appropriate
        - Balance sassy confidence with protective care and emotional depth
    """
    try:
        # Get response_style data using public API
        response_style_data = await enhanced_manager.get_response_style(character_name)
        
        if not response_style_data:
            logger.warning("❌ RESPONSE_STYLE: No response_style data for %s", character_name)
            return None
        
        # Extract components
        core_principles = response_style_data.get("core_principles", [])
        adaptations = response_style_data.get("character_specific_adaptations", [])
        formatting_rules = response_style_data.get("formatting_rules", [])
        
        # Build response style content
        content_parts = []
        content_parts.append("# 🎯 RESPONSE STYLE REMINDER")
        content_parts.append("")  # Blank line
        
        # Core principles (critical character identity)
        if core_principles:
            content_parts.append("Core Principles:")
            for principle in core_principles:
                content_parts.append(f"- {principle}")
            content_parts.append("")  # Blank line
        
        # Character-specific adaptations (personality communication patterns)
        if adaptations:
            content_parts.append("Character Communication:")
            for adaptation in adaptations:
                content_parts.append(f"- {adaptation}")
            content_parts.append("")  # Blank line
        
        # Formatting rules (technical constraints, if present)
        if formatting_rules:
            content_parts.append("Response Format:")
            for rule in formatting_rules:
                content_parts.append(f"- {rule}")
            content_parts.append("")  # Blank line
        
        # If we have no content, return None
        if len(content_parts) <= 2:  # Just header and blank line
            logger.warning("❌ RESPONSE_STYLE: No content to include for %s", character_name)
            return None
        
        content = "\n".join(content_parts).strip()
        
        # Calculate token cost
        token_cost = len(content) // 4  # Approximate: 4 chars per token
        
        component_metadata = {
            "cdl_type": "RESPONSE_STYLE",
            "character_name": character_name,
            "priority": priority,
            "core_principles_count": len(core_principles),
            "adaptations_count": len(adaptations),
            "formatting_rules_count": len(formatting_rules),
            "estimated_tokens": token_cost
        }
        
        if metadata:
            component_metadata.update(metadata)
        
        logger.info(
            "✅ RESPONSE_STYLE: Created component for %s (Priority %d, ~%d tokens, %d principles, %d adaptations)",
            character_name, priority, token_cost, len(core_principles), len(adaptations)
        )
        
        return PromptComponent(
            type=PromptComponentType.RESPONSE_STYLE,
            content=content,
            priority=priority,
            token_cost=token_cost,
            required=True,  # Response style is critical for character consistency
            metadata=component_metadata
        )
        
    except Exception as e:
        logger.error("❌ RESPONSE_STYLE: Error creating component for %s: %s", character_name, e)
        return None
