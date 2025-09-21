"""
Final Integration Guide: AI Pipeline + Vector Memory System

This shows exactly how to modify the events handler to use the AI pipeline
with vector memory storage instead of template variables.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


async def create_ai_pipeline_vector_native_prompt(
    events_handler_instance,
    message,
    recent_messages: List[Dict[str, Any]],
    emotional_context: Optional[str] = None
) -> str:
    """
    Create prompt using AI pipeline results stored in vector memory.
    
    This replaces the template variable system with:
    1. AI pipeline processing (Phases 1-4) - KEPT
    2. Vector storage of results - NEW
    3. Vector-based prompt context - NEW
    
    Integration for events.py lines ~1193-1228:
    
    OLD:
    system_prompt_content = get_contextualized_system_prompt(
        personality_metadata=personality_metadata, 
        user_id=user_id
    )
    
    NEW:
    system_prompt_content = await create_ai_pipeline_vector_native_prompt(
        events_handler_instance=self,
        message=message,
        recent_messages=recent_messages,
        emotional_context=emotion_context
    )
    """
    try:
        user_id = str(message.author.id)
        message_content = message.content or "[Discord interaction]"
        
        # Import the AI pipeline integration
        from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineIntegration
        
        # Create integration instance
        pipeline_integration = VectorAIPipelineIntegration(
            vector_memory_system=events_handler_instance.memory_manager,
            phase2_integration=getattr(events_handler_instance, 'phase2_integration', None),
            phase4_integration=getattr(events_handler_instance.bot, 'phase4_integration', None)
        )
        
        # 🚀 AI PIPELINE: Process message through existing Phase 1-4 system
        logger.info("🧠 Running AI pipeline with vector storage for user %s", user_id)
        
        pipeline_result = await pipeline_integration.process_message_with_ai_pipeline(
            user_id=user_id,
            message_content=message_content,
            discord_message=message,
            recent_messages=recent_messages or []
        )
        
        # 🎭 VECTOR-NATIVE PROMPT: Create conversational prompt with vector enhancement
        prompt = await pipeline_integration.create_conversational_prompt_with_vector_enhancement(
            user_id=user_id,
            message_content=message_content,
            pipeline_result=pipeline_result
        )
        
        logger.info("✅ AI pipeline + vector prompt created: %d characters", len(prompt))
        return prompt
        
    except Exception as e:
        logger.error("❌ AI pipeline vector prompt creation failed: %s", e)
        # ALWAYS fallback to conversational prompt  
        return await _create_conversational_fallback_prompt(
            user_id=str(message.author.id),
            message_content=message.content or "[Discord interaction]"
        )


async def _create_conversational_fallback_prompt(user_id: str, message_content: str) -> str:
    """
    Emergency fallback prompt that requires no external dependencies or systems.
    
    This ensures the bot remains conversational even when all systems fail.
    """
    return f"You are a helpful AI assistant. User said: \"{message_content}\". Respond naturally and helpfully."


async def _build_prompt_from_ai_pipeline_vectors(
    vector_memory,
    user_id: str,
    current_message: str,
    pipeline_result
) -> str:
    """
    Build prompt using AI pipeline results stored as vectors.
    
    This is the key innovation: Instead of template variables, we use
    the AI pipeline's actual insights stored as semantic vectors.
    """
    try:
        # Base AI assistant prompt (no hardcoded character)
        base_prompt = "You are a helpful AI assistant. Respond naturally and conversationally."
        
        # 🧠 PERSONALITY CONTEXT: From Phase 1 AI pipeline results
        personality_context = ""
        if pipeline_result.personality_profile:
            personality_context = f"You notice their {pipeline_result.communication_style} communication style"
            if pipeline_result.personality_traits:
                personality_context += f" and recognize traits of {', '.join(pipeline_result.personality_traits[:3])}"
        
        # 💭 EMOTIONAL CONTEXT: From Phase 2 AI pipeline results  
        emotional_context = ""
        if pipeline_result.emotional_state:
            emotional_context = f"You sense their current emotional state: {pipeline_result.emotional_state}"
            if pipeline_result.stress_level:
                emotional_context += f" with {pipeline_result.stress_level} stress level"
            if pipeline_result.emotional_triggers:
                emotional_context += f". You're aware of triggers: {', '.join(pipeline_result.emotional_triggers[:2])}"
        
        # 🧠 RELATIONSHIP CONTEXT: From Phase 3 vector memory
        relationship_context = ""
        if pipeline_result.relationship_depth:
            relationship_context = f"Your relationship with the user is {pipeline_result.relationship_depth}"
            if pipeline_result.conversation_patterns:
                relationship_context += f", marked by patterns of {', '.join(pipeline_result.conversation_patterns[:2])}"
        
        # 🎭 PHASE 4 CONTEXT: From human-like intelligence
        interaction_context = ""
        if pipeline_result.interaction_type and pipeline_result.conversation_mode:
            interaction_context = f"This is a {pipeline_result.interaction_type} interaction in {pipeline_result.conversation_mode} mode"
        
        # 🎯 VECTOR MEMORY CONTEXT: Recent relevant memories
        memory_context = await _get_relevant_memory_context(vector_memory, user_id, current_message)
        
        # Build final prompt with AI pipeline insights
        context_parts = [
            personality_context,
            emotional_context, 
            relationship_context,
            interaction_context,
            memory_context
        ]
        
        # Filter out empty contexts
        active_contexts = [ctx for ctx in context_parts if ctx.strip()]
        
        if active_contexts:
            full_context = ". ".join(active_contexts)
            final_prompt = f"{base_prompt}. {full_context}"
        else:
            final_prompt = f"{base_prompt}"
        
        # 🔍 DEBUG: Print final prompt before sending to LLM
        logger.debug("🔍 FINAL INTEGRATION PROMPT DEBUG for user %s:\n%s\n%s\n%s", 
                    user_id, "-"*50, final_prompt, "-"*50)
        
        return final_prompt
        
    except Exception as e:
        logger.error("❌ Failed to build prompt from AI pipeline vectors: %s", e)
        raise e


async def _get_relevant_memory_context(vector_memory, user_id: str, current_message: str) -> str:
    """Get relevant memory context using vector search."""
    try:
        # Search for relevant memories
        relevant_memories = await vector_memory.search_memories(
            user_id=user_id,
            query=current_message,
            limit=5
        )
        
        if relevant_memories:
            memory_count = len(relevant_memories)
            memory_context = f"You remember {memory_count} relevant interactions with the user"
            
            # Add specific memory hints
            if relevant_memories:
                recent_memory = relevant_memories[0]
                memory_content = recent_memory.get("content", "")
                if memory_content:
                    memory_context += f", particularly recalling: {memory_content[:100]}..."
            
            return memory_context
        
        return ""
        
    except Exception as e:
        logger.error("❌ Failed to get relevant memory context: %s", e)
        return ""


# INTEGRATION INSTRUCTIONS FOR EVENTS.PY
EVENTS_INTEGRATION_CODE = '''
# Replace the current prompt creation in events.py (lines ~1193-1228) with:

# OLD CODE TO REPLACE:
# if enhanced_system_prompt:
#     system_prompt_content = enhanced_system_prompt
# else:
#     system_prompt_content = get_contextualized_system_prompt(
#         personality_metadata=personality_metadata, 
#         user_id=user_id
#     )

# NEW CODE:
if enhanced_system_prompt:
    # Use Phase 4 enhanced prompt if available
    system_prompt_content = enhanced_system_prompt
    logger.debug("Using Phase 4 enhanced system prompt")
else:
    # Use AI pipeline + vector memory system
    from src.prompts.final_integration import create_ai_pipeline_vector_native_prompt
    
    try:
        system_prompt_content = await create_ai_pipeline_vector_native_prompt(
            events_handler_instance=self,
            message=message,
            recent_messages=recent_messages,
            emotional_context=getattr(self, '_current_emotional_context', None)
        )
        logger.debug("✅ Using AI pipeline + vector-native system prompt")
    
    except Exception as e:
        logger.error("❌ AI pipeline vector prompt failed: %s", e)
        # 🔥 NO FALLBACK: Fix AI pipeline instead of masking errors
        raise e
'''

# CONFIGURATION FOR MIGRATION
AI_PIPELINE_VECTOR_CONFIG = {
    "enabled": True,
    "keep_existing_pipeline": True,  # ✅ Keep Phase 1-4 AI pipeline
    "store_results_as_vectors": True,  # ✅ Store AI insights in vector memory
    "use_vector_prompts": True,  # ✅ Use vector-based prompt context
    "eliminate_template_variables": True,  # ✅ Remove {CONTEXT} variables
    "log_pipeline_performance": True,
    "parallel_processing": True  # ✅ Keep existing parallel processing
}