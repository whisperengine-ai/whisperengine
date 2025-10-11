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
    """Types of prompt components for structured assembly.
    
    Components are assembled in priority order (lower number = higher priority).
    This enum provides semantic names for component types while allowing
    flexible priority assignment at runtime.
    """
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
    CHARACTER_VOICE = "character_voice"
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
    
    Args:
        bot_name: Name of the bot/character
        priority: Priority (default: 6)
        metadata: Optional metadata dict
        
    Returns:
        PromptComponent configured for communication guidance
    """
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
