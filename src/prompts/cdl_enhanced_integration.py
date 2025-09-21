"""
Updated AI Pipeline Integration with CDL Character Support

This bridges the CDL character system with the existing AI pipeline
for dynamic character-aware prompts.
"""

import logging
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineIntegration

logger = logging.getLogger(__name__)

async def create_cdl_enhanced_prompt(
    events_handler_instance,
    message,
    recent_messages,
    character_file: str = None
) -> str:
    """
    Create AI pipeline prompt enhanced with CDL character definition.
    
    This is the new evolution:
    1. AI pipeline analyzes user/conversation (Phases 1-4) - SAME
    2. CDL character provides personality foundation - NEW
    3. Dynamic prompt combines both for character-aware intelligence - NEW
    
    Usage in events.py:
    
    OLD:
    system_prompt_content = await create_ai_pipeline_vector_native_prompt(...)
    
    NEW:
    system_prompt_content = await create_cdl_enhanced_prompt(
        events_handler_instance=self,
        message=message,
        recent_messages=recent_messages,
        character_file=None,  # No hardcoded character - use CDL system
        emotional_context=emotion_context
    )
    """
    try:
        user_id = str(message.author.id)
        message_content = message.content or "[Discord interaction]"
        
        # 1. RUN AI PIPELINE (existing system)
        vector_ai_integration = VectorAIPipelineIntegration(
            vector_memory_system=events_handler_instance.bot.memory_manager.vector_store,
            phase2_integration=getattr(events_handler_instance.bot, 'phase2_integration', None),
            phase4_integration=getattr(events_handler_instance.bot, 'phase4_integration', None)
        )
        
        pipeline_result = await vector_ai_integration.process_message_with_ai_pipeline(
            user_id=user_id,
            message_content=message_content,
            discord_message=message,
            recent_messages=recent_messages
        )
        
        # 2. ADD CDL CHARACTER AWARENESS (new system)
        if character_file:
            cdl_integration = CDLAIPromptIntegration(
                vector_memory_system=events_handler_instance.bot.memory_manager.vector_store,
                ai_pipeline_integration=vector_ai_integration
            )
            
            return await cdl_integration.create_character_aware_prompt(
                character_file=character_file,
                user_id=user_id,
                message_content=message_content,
                pipeline_result=pipeline_result
            )
        
        # 3. FALLBACK TO VECTOR-NATIVE (existing system)
        else:
            return await vector_ai_integration.create_conversational_prompt_with_vector_enhancement(
                user_id=user_id,
                message_content=message_content,
                pipeline_result=pipeline_result
            )
            
    except (ImportError, AttributeError, KeyError, FileNotFoundError) as e:
        logger.error("❌ CDL enhanced prompt creation failed: %s", e)
        # Ultimate fallback - exit without further processing
        raise RuntimeError(f"CDL integration system failed: {e}") from e


# Example CDL Character Configuration
CDL_CHARACTER_CONFIGS = {
    "elena": "elena_rodriguez.yaml",
    "luna": "luna_hartwell.yaml", 
    "companion": "generic_companion.yaml"
}

async def get_character_for_bot(bot_name: str) -> str:
    """Get CDL character file for bot name."""
    bot_lower = bot_name.lower()
    
    # Map bot names to CDL characters
    if "dream" in bot_lower:
        return CDL_CHARACTER_CONFIGS["dream"]
    elif "elena" in bot_lower:
        return CDL_CHARACTER_CONFIGS["elena"]
    elif "luna" in bot_lower:
        return CDL_CHARACTER_CONFIGS["luna"]
    else:
        return CDL_CHARACTER_CONFIGS["companion"]