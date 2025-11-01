"""
Template-Based System Prompt Integration Helper

This module provides a simple integration point for adding template-based
system prompts to PromptAssembler. It's designed to be called from
message_processor.py as an alternative to database-driven CDL components.

Usage in message_processor.py:
    from src.prompts.template_integration import add_template_system_prompt_if_available
    
    # Try template system first
    template_loaded = await add_template_system_prompt_if_available(
        assembler=assembler,
        bot_name=bot_name,
        message_context=message_context
    )
    
    # If template not loaded, fall back to database CDL components
    if not template_loaded:
        # ... existing CDL database loading logic ...

Author: WhisperEngine  
Date: November 2025
"""

import logging
from typing import Optional, Any
from src.prompts.template_loader import create_template_loader, is_template_system_enabled
from src.prompts.prompt_components import PromptComponent, PromptComponentType

logger = logging.getLogger(__name__)


async def add_template_system_prompt_if_available(
    assembler: Any,  # PromptAssembler instance
    bot_name: str,
    message_context: Any,  # MessageContext instance
) -> bool:
    """
    Add template-based system prompt to assembler if configured.
    
    This function checks if CHARACTER_SYSTEM_PROMPT_PATH environment variable
    is set and points to a valid template file. If so, it loads and renders
    the template, then adds it as a high-priority component to the assembler.
    
    Args:
        assembler: PromptAssembler instance to add component to
        bot_name: Character name (e.g., "elena", "marcus")
        message_context: MessageContext with user_id, content, metadata
        
    Returns:
        True if template was successfully loaded and added, False otherwise
        
    Example:
        template_loaded = await add_template_system_prompt_if_available(
            assembler=assembler,
            bot_name="elena",
            message_context=message_context
        )
        
        if not template_loaded:
            # Fall back to database CDL loading
            ...
    """
    # Check if template system is enabled
    if not is_template_system_enabled():
        logger.debug(f"Template system not enabled for {bot_name} - will use database CDL")
        return False
    
    logger.info(f"📄 TEMPLATE SYSTEM: Using template-based system prompt for {bot_name}")
    
    try:
        template_loader = create_template_loader()
        
        # TODO Phase 2: Extract dynamic data from ai_components/message_context
        # For now, use placeholder text that will be replaced in future iteration
        user_facts_text = "User context not yet configured in template system."
        recent_memories_text = "Conversation history not yet configured in template system."
        relationship_text = ""  # Optional
        emotional_text = ""  # Optional
        
        # Get timezone from message context metadata if available
        timezone = "America/Los_Angeles"  # Default
        if hasattr(message_context, 'metadata') and message_context.metadata:
            timezone = message_context.metadata.get('timezone', timezone)
        
        # Render template with dynamic data
        system_prompt = await template_loader.render_system_prompt(
            user_facts=user_facts_text,
            recent_memories=recent_memories_text,
            relationship_context=relationship_text,
            emotional_state=emotional_text,
            timezone=timezone
        )
        
        if not system_prompt:
            logger.warning(f"⚠️ TEMPLATE SYSTEM: Failed to render template for {bot_name}")
            return False
        
        # Create component and add to assembler
        template_component = PromptComponent(
            type=PromptComponentType.CHARACTER_IDENTITY,
            content=system_prompt,
            priority=1,  # Highest priority - replaces all CDL database components
            required=True,  # Critical for character personality
            metadata={"source": "template_file", "bot_name": bot_name}
        )
        
        assembler.add_component(template_component)
        
        word_count = len(system_prompt.split())
        char_count = len(system_prompt)
        logger.info(f"✅ TEMPLATE SYSTEM: Loaded system prompt ({char_count} chars, ~{word_count} words)")
        logger.info(f"   Template replaces database CDL components - zero per-message DB overhead!")
        
        return True
        
    except Exception as template_error:
        logger.error(f"❌ TEMPLATE SYSTEM: Error loading template for {bot_name}: {template_error}")
        logger.info("   Falling back to database CDL system...")
        return False


def get_template_system_status() -> dict:
    """
    Get current status of template system for debugging.
    
    Returns:
        Dict with enabled status, template path, file exists
    """
    from src.prompts.template_loader import create_template_loader
    import os
    
    template_path = os.getenv("CHARACTER_SYSTEM_PROMPT_PATH")
    loader = create_template_loader()
    
    return {
        "enabled": is_template_system_enabled(),
        "template_path": template_path,
        "file_exists": loader.is_template_available() if loader else False,
        "metadata": loader.get_template_metadata() if loader else {}
    }
