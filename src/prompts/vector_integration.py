"""
Vector-Native Prompt Integration for WhisperEngine

This shows how to integrate the new vector-native prompt system with the existing
event handler, replacing the legacy template variable system.
"""

import logging
from typing import Dict, Optional, Any
from src.prompts.vector_native_prompt_manager import VectorNativePromptManager

logger = logging.getLogger(__name__)


async def create_vector_native_prompt(
    vector_memory_system,
    base_prompt_path: str,
    user_id: str,
    current_message: str,
    emotional_context: Optional[str] = None,
    personality_engine=None
) -> str:
    """
    Replace legacy template variable system with vector-native prompt creation.
    
    This function replaces the entire helpers.py contextualize_system_prompt_with_context()
    function with CDL character-aware operations.
    
    Args:
        vector_memory_system: The vector memory store instance
        character_file: Path to the CDL character JSON file (e.g., characters/default_assistant.json)
        user_id: Discord user ID
        current_message: Current user message for context
        emotional_context: Current emotional context if available (unused currently)
        personality_engine: Personality engine instance (optional, unused currently)
    
    Returns:
        Fully contextualized prompt ready for LLM using CDL character system
    """
    try:
        # Read the base prompt template
        with open(base_prompt_path, 'r', encoding='utf-8') as f:
            base_prompt = f.read()
        
        # Create vector-native prompt manager
        prompt_manager = VectorNativePromptManager(
            vector_memory_system=vector_memory_system,
            personality_engine=personality_engine
        )
        
        # Generate contextualized prompt using vector memory
        contextualized_prompt = await prompt_manager.create_contextualized_prompt(
            base_prompt=base_prompt,
            user_id=user_id,
            current_message=current_message,
            emotional_context=emotional_context
        )
        
        logger.info("🎭 Vector-native prompt created: %d characters", len(contextualized_prompt))
        return contextualized_prompt
        
    except Exception as e:
        logger.error("❌ Vector-native prompt creation failed: %s", e)
        # 🔥 NO FALLBACK: Don't use legacy system, fix the vector system
        raise e


def should_use_vector_native_prompts() -> bool:
    """
    Determine if vector-native prompts should be used.
    
    Based on the Memory Architecture v2.0, this should ALWAYS return True
    once the vector memory system is active.
    """
    # TODO: Add configuration check for vector memory system status
    return True  # Always use vector-native once implemented


async def integrate_with_events_handler(
    events_handler_instance,
    user_id: str,
    message_content: str,
    emotional_context: Optional[str] = None
) -> str:
    """
    Integration point for the events handler.
    
    This replaces the call to helpers.contextualize_system_prompt_with_context()
    in the events handler with vector-native prompt creation.
    
    Usage in events.py:
    
    # OLD WAY (legacy template variables):
    contextualized_prompt = await helpers.contextualize_system_prompt_with_context(
        system_prompt_template=prompt_template,
        comprehensive_context=comprehensive_context,
        # ... many more parameters
    )
    
    # NEW WAY (vector-native):
    contextualized_prompt = await integrate_with_events_handler(
        events_handler_instance=self,
        user_id=str(message.author.id),
        message_content=message.content,
        emotional_context=current_emotional_context
    )
    """
    try:
        # Check if vector memory system is available
        if not hasattr(events_handler_instance, 'memory_manager'):
            raise ValueError("Vector memory manager not available")
        
        vector_memory = events_handler_instance.memory_manager
        
        # Use CDL character system instead of .md files
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        import os
        
        cdl_integration = CDLAIPromptIntegration(vector_memory)
        default_character = os.getenv('CDL_DEFAULT_CHARACTER', 'characters/default_assistant.json')
        
        # Create character-aware prompt using CDL
        return await cdl_integration.create_character_aware_prompt(
            character_file=default_character,
            user_id=user_id,
            message_content=message_content
        )
        
    except Exception as e:
        logger.error("❌ Vector prompt integration failed: %s", e)
        raise e


# Configuration for migration
VECTOR_NATIVE_CONFIG = {
    "enabled": True,  # Set to True to use CDL character system
    "use_cdl_characters": True,  # Use CDL JSON files instead of .md files
    "fallback_to_legacy": False,  # 🔥 NO FALLBACKS - fix CDL system instead
    "log_prompt_creation": True,
    "validate_memory_access": True
}