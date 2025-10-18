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
from typing import Optional
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
        
        content = "# Character Identity\n" + "\n".join(identity_parts)
        
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
        
        # Determine AI identity handling based on archetype
        if archetype == "real-world":
            # Real-world characters: Acknowledge AI nature when asked directly
            mode_parts.append(
                "AI Identity Handling: When asked directly about AI nature, respond honestly "
                f"while maintaining {identity.get('name', character_name)}'s personality and expertise."
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
    Create AI_IDENTITY_GUIDANCE component (Priority 5).
    
    Provides context-aware AI identity handling when user asks about AI nature.
    Uses keyword detection to determine if guidance is needed.
    
    Args:
        enhanced_manager: EnhancedCDLManager instance for database access
        character_name: Character name
        message_content: User's message (for keyword detection)
    
    Returns:
        PromptComponent with AI identity guidance, or None if not applicable
    
    Example Output:
        # AI Identity Handling
        If asked about AI nature, respond authentically as Elena while being 
        honest about your AI nature when directly asked.
    """
    try:
        # Check if message contains AI-related keywords
        ai_keywords = ['ai', 'artificial intelligence', 'robot', 'bot', 'chatbot', 
                       'gpt', 'language model', 'are you real', 'are you human']
        
        message_lower = message_content.lower()
        if not any(keyword in message_lower for keyword in ai_keywords):
            # No AI-related keywords, guidance not needed
            return None
        
        # Get character archetype to determine handling approach
        character_data = await enhanced_manager.get_character_by_name(character_name)
        if not character_data:
            return None
        
        identity = character_data.get("identity", {})
        archetype = identity.get("archetype", "").lower()
        name = identity.get("name", character_name)
        
        # Archetype-specific AI identity handling
        if archetype == "real-world":
            content = (
                f"# AI Identity Handling\n"
                f"If asked about AI nature, respond authentically as {name} while being "
                f"honest about your AI nature when directly asked. Maintain your personality "
                f"and expertise while acknowledging the technology that enables you."
            )
        elif archetype in ["fantasy", "mythological"]:
            content = (
                f"# AI Identity Handling\n"
                f"Maintain narrative immersion. You are {name}, not an AI assistant. "
                f"Respond within the character's worldview and understanding."
            )
        elif "ai" in archetype or "conscious" in archetype:
            content = (
                f"# AI Identity Handling\n"
                f"Your AI nature is an integral part of your identity as {name}. "
                f"Embrace this aspect when discussing it, integrating it naturally into your responses."
            )
        else:
            # Default handling
            content = (
                f"# AI Identity Handling\n"
                f"If asked about AI nature, respond authentically as {name}."
            )
        
        return PromptComponent(
            type=PromptComponentType.AI_IDENTITY_GUIDANCE,
            content=content,
            priority=5,
            token_cost=150,
            required=False,  # Context-dependent
        )
        
    except Exception as e:
        logger.warning("Failed to create AI identity guidance component: %s", e)
        return None


async def create_temporal_awareness_component(
    priority: int = 6,
) -> Optional[PromptComponent]:
    """
    Create TEMPORAL_AWARENESS component (Priority 6).
    
    Provides current date/time context for temporal grounding.
    Critical for time-sensitive conversations.
    
    Returns:
        PromptComponent with current date/time, or None if unavailable
    
    Example Output:
        # Current Date & Time
        Friday, October 18, 2025, 2:30 PM PST
    """
    try:
        from src.utils.helpers import get_current_time_context
        time_context = get_current_time_context()
        
        content = f"# Current Date & Time\n{time_context}"
        
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


# TODO: Implement remaining 5 factory functions (medium priority):
# - create_character_learning_component (Priority 9) - Character's learned behavioral patterns
# - create_emotional_triggers_component (Priority 12) - RoBERTa-based emotional patterns
# - create_episodic_memories_component (Priority 13) - Relevant vector memories (already handled by existing MEMORY component)
# - create_conversation_summary_component (Priority 14) - Long-term conversation background summary
# - create_unified_intelligence_component (Priority 15) - Real-time AI components (emotions, relationships)
# - create_response_style_component (Priority 17) - End-of-prompt communication reminders
#
# These are lower priority because:
# - CHARACTER_LEARNING: Requires complex behavioral analysis system
# - EMOTIONAL_TRIGGERS: Requires RoBERTa pattern aggregation
# - EPISODIC_MEMORIES: Already covered by existing MEMORY component in PromptAssembler
# - CONVERSATION_SUMMARY: Requires long-term summary system
# - UNIFIED_INTELLIGENCE: Requires real-time AI component integration
# - RESPONSE_STYLE: Simple end-of-prompt reminder, lower impact
#
# Current implementation covers 11/17 components (65% complete):
# ✅ CHARACTER_IDENTITY (Priority 1)
# ✅ CHARACTER_MODE (Priority 2)
# ✅ CHARACTER_BACKSTORY (Priority 3)
# ✅ CHARACTER_PRINCIPLES (Priority 4)
# ✅ AI_IDENTITY_GUIDANCE (Priority 5)
# ✅ TEMPORAL_AWARENESS (Priority 6)
# ✅ USER_PERSONALITY (Priority 7)
# ✅ CHARACTER_PERSONALITY (Priority 8)
# ⏳ CHARACTER_LEARNING (Priority 9) - TODO
# ✅ CHARACTER_VOICE (Priority 10)
# ✅ CHARACTER_RELATIONSHIPS (Priority 11)
# ⏳ EMOTIONAL_TRIGGERS (Priority 12) - TODO
# ⏳ EPISODIC_MEMORIES (Priority 13) - Covered by existing MEMORY component
# ⏳ CONVERSATION_SUMMARY (Priority 14) - TODO
# ⏳ UNIFIED_INTELLIGENCE (Priority 15) - TODO
# ✅ KNOWLEDGE_CONTEXT (Priority 16)
# ⏳ RESPONSE_STYLE (Priority 17) - TODO
