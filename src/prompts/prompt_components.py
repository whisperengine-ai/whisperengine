"""
Prompt Component System - Core Data Structures

This module defines the core data structures for structured prompt assembly:
- PromptComponentType: Enumeration of component types
- PromptComponent: Individual prompt components with metadata
- Component priority system for dynamic ordering
- Conditional inclusion logic for context-aware assembly

Phase 1: Core Infrastructure
Status: ACTIVE IMPLEMENTATION
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Dict, Any


class PromptComponentType(Enum):
    """Types of prompt components for structured prompt assembly.
    
    Components are assembled in priority order (lower number = higher priority).
    This enum provides semantic names for component types while allowing
    flexible priority assignment at runtime.
    
    Phase 2 (Oct 2025): Added CDL (Character Definition Language) component types
    for unified prompt assembly. This eliminates dual prompt paths by merging
    CDL character data directly into PromptAssembler components.
    
    Status: 12/18 implemented (67% complete). See cdl_component_factories.py line 995 for full TODO list.
    ✅ CHARACTER_COMMUNICATION_PATTERNS implemented Nov 4, 2025
    """
    # ==========================================
    # CDL CHARACTER COMPONENTS (Priority 1-17+)
    # ==========================================
    # These replace the legacy CDL enhancement system that previously
    # built prompts separately and replaced the system message.
    # Current status: 12/18 implemented (67% complete)
    
    # Character foundation (Priority 1-6)
    CHARACTER_IDENTITY = "character_identity"           # Priority 1: Name, occupation, description
    CHARACTER_MODE = "character_mode"                   # Priority 2: Trigger-based interaction mode
    CHARACTER_BACKSTORY = "character_backstory"         # Priority 3: Professional/personal history
    CHARACTER_PRINCIPLES = "character_principles"       # Priority 4: Values, beliefs, motivations
    AI_IDENTITY_GUIDANCE = "ai_identity_guidance"       # Priority 5: AI disclosure handling
    CHARACTER_COMMUNICATION_PATTERNS = "character_communication_patterns"  # Priority 5.5: ✅ IMPLEMENTED - Communication patterns (emoji, speech, behavioral triggers)
    TEMPORAL_AWARENESS = "temporal_awareness"           # Priority 6: Current date/time
    
    # User and character personality (Priority 7-10)
    USER_PERSONALITY = "user_personality"               # Priority 7: User facts, preferences
    CHARACTER_PERSONALITY = "character_personality"     # Priority 8: Big Five traits
    CHARACTER_LEARNING = "character_learning"           # Priority 9: Self-discoveries, insights
    CHARACTER_VOICE = "character_voice"                 # Priority 10: Speech patterns, style
    
    # Relationships and emotions (Priority 11-12)
    CHARACTER_RELATIONSHIPS = "character_relationships" # Priority 11: NPC relationships
    EMOTIONAL_TRIGGERS = "emotional_triggers"           # Priority 12: Emotion response guidance
    
    # Memory and intelligence (Priority 13-15)
    EPISODIC_MEMORIES = "episodic_memories"            # Priority 13: Memorable moments
    CONVERSATION_SUMMARY = "conversation_summary"       # Priority 14: Long-term conversation themes
    UNIFIED_INTELLIGENCE = "unified_intelligence"       # Priority 15: Coordinated AI intelligence
    
    # Emotional intelligence (Priority 9 - NEW)
    EMOTIONAL_CONTEXT = "emotional_context"             # Priority 9: User/bot emotional state + InfluxDB trajectory
    
    # Context and style (Priority 16-17)
    KNOWLEDGE_CONTEXT = "knowledge_context"             # Priority 16: Intent-based facts
    RESPONSE_STYLE = "response_style"                   # Priority 17: Final style reminder
    
    # ==========================================
    # LEGACY COMPONENTS (Phase 1)
    # ==========================================
    # Kept for backward compatibility. These are gradually being
    # replaced by the CDL component system above.
    
    # Core system components (highest priority)
    CORE_SYSTEM = "core_system"
    TIME_CONTEXT = "time_context"
    ATTACHMENT_GUARD = "attachment_guard"
    
    # Memory and context components
    MEMORY = "memory"
    CONVERSATION_FLOW = "conversation_flow"
    USER_FACTS = "user_facts"
    RECENT_CONTEXT = "recent_context"
    
    # Guidance and behavior components
    GUIDANCE = "guidance"
    COMMUNICATION_STYLE = "communication_style"
    
    # AI intelligence components
    AI_INTELLIGENCE = "ai_intelligence"
    EMOTION_CONTEXT = "emotion_context"
    RELATIONSHIP_STATE = "relationship_state"
    CONFIDENCE_GUIDANCE = "confidence_guidance"
    
    # Adaptive learning components
    TRENDWISE_ADAPTATION = "trendwise_adaptation"
    LEARNING_INSIGHTS = "learning_insights"
    
    # Safety and validation components
    ANTI_HALLUCINATION = "anti_hallucination"
    RESPONSE_CONSTRAINTS = "response_constraints"
    
    # Custom components
    CUSTOM = "custom"


@dataclass
class PromptComponent:
    """A discrete component of a system prompt with metadata.
    
    Each component represents a logical piece of the prompt that can be:
    - Ordered by priority (lower number = higher priority)
    - Conditionally included based on context
    - Token-budget managed for optimization
    - Deduplicated to prevent redundancy
    
    Example:
        ```python
        memory_component = PromptComponent(
            type=PromptComponentType.MEMORY,
            content=memory_narrative,
            priority=4,
            required=False,
            token_cost=500,
            condition=lambda: memory_narrative is not None
        )
        ```
    """
    type: PromptComponentType
    content: str
    priority: int
    required: bool = False
    condition: Optional[Callable[[], bool]] = None
    token_cost: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def should_include(self) -> bool:
        """Determine if this component should be included in the final prompt.
        
        Returns:
            bool: True if component should be included, False otherwise
        """
        # Empty content should not be included
        if not self.content or not self.content.strip():
            return False
        
        # Check conditional inclusion
        if self.condition:
            try:
                return self.condition()
            except Exception:
                # If condition fails, exclude non-required components
                return self.required
        
        return True
    
    def estimate_token_cost(self) -> int:
        """Estimate token cost if not explicitly provided.
        
        Uses simple heuristic: ~4 chars per token (GPT-style tokenization).
        
        Returns:
            int: Estimated token count
        """
        if self.token_cost is not None:
            return self.token_cost
        
        # Simple estimation: 4 chars per token
        return len(self.content) // 4
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"PromptComponent(type={self.type.value}, "
            f"priority={self.priority}, "
            f"required={self.required}, "
            f"length={len(self.content)}, "
            f"tokens~{self.estimate_token_cost()})"
        )


def create_core_system_component(
    content: str,
    priority: int = 1,
    metadata: Optional[Dict[str, Any]] = None
) -> PromptComponent:
    """Create a core system prompt component.
    
    Args:
        content: System prompt content
        priority: Priority (default: 1 - highest)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent configured for core system prompt
    """
    return PromptComponent(
        type=PromptComponentType.CORE_SYSTEM,
        content=content,
        priority=priority,
        required=True,
        metadata=metadata or {}
    )


def create_memory_component(
    content: str,
    priority: int = 4,
    required: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> PromptComponent:
    """Create a memory narrative component.
    
    Args:
        content: Memory narrative content
        priority: Priority (default: 4)
        required: Whether component is required (default: False)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent configured for memory narrative
    """
    return PromptComponent(
        type=PromptComponentType.MEMORY,
        content=content,
        priority=priority,
        required=required,
        condition=lambda: bool(content and content.strip()),
        metadata=metadata or {}
    )


def create_anti_hallucination_component(
    priority: int = 4,
    metadata: Optional[Dict[str, Any]] = None
) -> PromptComponent:
    """Create an anti-hallucination warning component.
    
    Used when no memory is available to prevent LLM from inventing conversations.
    
    Args:
        priority: Priority (default: 4 - same as memory)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent configured for anti-hallucination warning
    """
    content = (
        "⚠️ MEMORY STATUS: No previous conversation history found. "
        "If asked about past conversations, politely say you don't have "
        "specific memories of those discussions yet. DO NOT invent or "
        "hallucinate conversation details."
    )
    
    return PromptComponent(
        type=PromptComponentType.ANTI_HALLUCINATION,
        content=content,
        priority=priority,
        required=True,
        metadata=metadata or {}
    )


def create_guidance_component(
    bot_name: str,
    priority: int = 6,
    metadata: Optional[Dict[str, Any]] = None
) -> PromptComponent:
    """Create a communication guidance component.
    
    ⚠️ DEPRECATED: This function uses hardcoded generic text for all characters.
    Use create_response_style_component() from cdl_component_factories.py instead,
    which pulls character-specific guidance from the CDL database.
    
    This function violates WhisperEngine's NO HARDCODED CHARACTER LOGIC constraint
    by applying the same generic guidance to Elena (marine biologist) as Gabriel
    (British gentleman) as Aria (starship AI), completely ignoring their unique
    CDL personality data stored in character_response_style table.
    
    Args:
        bot_name: Name of the bot/character
        priority: Priority (default: 6)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent configured for communication guidance
        
    See Also:
        create_response_style_component() in cdl_component_factories.py (Priority 17)
    """
    import warnings
    warnings.warn(
        "create_guidance_component() is deprecated. Use create_response_style_component() "
        "from cdl_component_factories.py for character-specific guidance from CDL database.",
        DeprecationWarning,
        stacklevel=2
    )
    
    content = (
        f"Communication style: Respond naturally and authentically as {bot_name} - "
        f"be warm, genuine, and conversational. No meta-analysis, breakdowns, "
        f"bullet summaries, or section headings. Stay in character and speak "
        f"like a real person would."
    )
    
    return PromptComponent(
        type=PromptComponentType.GUIDANCE,
        content=content,
        priority=priority,
        required=True,
        metadata=metadata or {}
    )


def create_user_facts_component(
    facts_content: str,
    priority: int = 3,
    required: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> PromptComponent:
    """Create a user facts component for conversation context.
    
    Args:
        facts_content: Formatted user facts and preferences
        priority: Priority (default: 3, between core system and memory)
        required: Whether component is required (default: False)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent configured for user facts
    """
    return PromptComponent(
        type=PromptComponentType.USER_FACTS,
        content=facts_content,
        priority=priority,
        required=required,
        condition=lambda: bool(facts_content and facts_content.strip()),
        metadata=metadata or {}
    )


def create_ai_intelligence_component(
    content: str,
    priority: int = 7,
    required: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> PromptComponent:
    """Create an AI intelligence guidance component.
    
    Args:
        content: AI intelligence guidance content
        priority: Priority (default: 7)
        required: Whether component is required (default: False)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent configured for AI intelligence guidance
    """
    return PromptComponent(
        type=PromptComponentType.AI_INTELLIGENCE,
        content=content,
        priority=priority,
        required=required,
        condition=lambda: bool(content and content.strip()),
        metadata=metadata or {}
    )
