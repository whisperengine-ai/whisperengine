"""
Vector-Native Prompt Integration Patch for WhisperEngine Events Handler

This provides the exact integration points to replace legacy template variables
with vector-native memory operations in the events handler.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def create_vector_native_system_prompt(
    events_handler_instance,
    message,
    emotional_context: Optional[str] = None
) -> str:
    """
    Vector-native replacement for the current prompt creation logic in events.py.
    
    This replaces lines 1193-1228 in events.py with vector-native operations.
    
    Args:
        events_handler_instance: The EventsHandler instance (self)
        message: Discord message object
        emotional_context: Current emotional context if available
        
    Returns:
        Vector-contextualized system prompt ready for LLM
    """
    try:
        user_id = str(message.author.id)
        message_content = message.content or "[Discord interaction]"
        
        # 🚀 VECTOR-NATIVE: Use vector memory instead of template variables
        if hasattr(events_handler_instance, 'memory_manager') and events_handler_instance.memory_manager:
            logger.info("🎭 Using vector-native prompt system")
            
            # Import the vector integration
            from src.prompts.vector_integration import integrate_with_events_handler
            
            # Create vector-native prompt
            system_prompt_content = await integrate_with_events_handler(
                events_handler_instance=events_handler_instance,
                user_id=user_id,
                message_content=message_content,
                emotional_context=emotional_context
            )
            
            logger.debug("✅ Vector-native system prompt created")
            return system_prompt_content
            
        else:
            # 🔥 NO FALLBACK: Vector memory must be available
            raise ValueError("Vector memory manager not available - vector system required")
            
    except Exception as e:
        logger.error("❌ Vector-native prompt creation failed: %s", e)
        # 🔥 NO FALLBACK: Fix vector system instead of using legacy
        raise e


# Integration instructions for events.py:
INTEGRATION_INSTRUCTIONS = """
INTEGRATION STEPS for src/handlers/events.py:

1. Add import at the top:
   from src.prompts.events_integration import create_vector_native_system_prompt

2. Replace lines 1193-1228 (the current prompt creation logic) with:

   # Vector-native system prompt creation
   try:
       system_prompt_content = await create_vector_native_system_prompt(
           events_handler_instance=self,
           message=message,
           emotional_context=emotion_context  # If available
       )
       logger.debug("✅ Using vector-native system prompt")
   
   except Exception as e:
       logger.error("❌ Vector-native prompt failed: %s", e)
       # 🔥 NO FALLBACK: Fix vector system, don't mask errors
       raise e

3. Remove the old template system imports:
   - Remove: get_contextualized_system_prompt import
   - Remove: helpers.contextualize_system_prompt_with_context calls
   - Remove: All template variable building logic

4. Update the base prompt system:
   - Use: CDL character system with JSON files (characters/default_assistant.json)
   - Remove: All {CONTEXT_VARIABLE} placeholders from .md files

This migration eliminates:
- ❌ All template variable replacement ({MEMORY_NETWORK_CONTEXT}, etc.)
- ❌ Legacy hierarchical memory lookups  
- ❌ Complex context building in helpers.py
- ❌ Multiple memory system synchronization

And replaces with:
- ✅ Direct vector memory queries
- ✅ Real-time semantic context retrieval
- ✅ Natural fact checking and contradiction detection
- ✅ Single source of truth (vector store)
"""

# Configuration check
def validate_vector_integration() -> bool:
    """Validate that vector integration is properly configured."""
    try:
        # Check if vector memory system exists
        from src.memory.vector_memory_system import VectorMemorySystem
        
        # Check if prompt manager exists
        from src.prompts.vector_native_prompt_manager import VectorNativePromptManager
        
        # Check if integration exists
        from src.prompts.vector_integration import integrate_with_events_handler
        
        logger.info("✅ Vector integration validation passed")
        return True
        
    except ImportError as e:
        logger.error("❌ Vector integration validation failed: %s", e)
        return False