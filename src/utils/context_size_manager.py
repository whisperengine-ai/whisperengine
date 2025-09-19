"""
Context size management utilities for preventing oversized LLM requests.

This module provides token counting and context truncation to prevent
the massive context sizes that were causing response failures.
"""

import logging
import re
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

# Rough token estimation (more accurate than simple word count)
# Based on OpenAI's tokenization patterns
CHARS_PER_TOKEN = 4  # Conservative estimate
MAX_CONTEXT_TOKENS = 8000  # Safe limit for most models (leaves room for response)
MAX_RESPONSE_TOKENS = 2000  # Reserve tokens for response generation

def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    
    Args:
        text: Input text to estimate
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # More accurate estimation considering tokenization patterns
    # Remove extra whitespace and count meaningful characters
    clean_text = re.sub(r'\s+', ' ', text.strip())
    return max(1, len(clean_text) // CHARS_PER_TOKEN)

def count_context_tokens(conversation_context: List[Dict[str, str]]) -> int:
    """
    Count total tokens in conversation context.
    
    Args:
        conversation_context: List of message dictionaries
        
    Returns:
        Total estimated token count
    """
    total_tokens = 0
    for message in conversation_context:
        content = message.get('content', '')
        total_tokens += estimate_tokens(content)
    
    return total_tokens

def truncate_context(
    conversation_context: List[Dict[str, str]], 
    max_tokens: int = MAX_CONTEXT_TOKENS
) -> Tuple[List[Dict[str, str]], int]:
    """
    Truncate conversation context to fit within token limit.
    
    Strategy:
    1. Always keep system messages (first messages)
    2. Truncate from oldest user/assistant messages
    3. Preserve message alternation
    
    Args:
        conversation_context: Original context
        max_tokens: Maximum token limit
        
    Returns:
        Tuple of (truncated_context, tokens_removed)
    """
    if not conversation_context:
        return conversation_context, 0
    
    # Count current tokens
    current_tokens = count_context_tokens(conversation_context)
    
    if current_tokens <= max_tokens:
        logger.debug(f"Context size OK: {current_tokens} tokens <= {max_tokens}")
        return conversation_context, 0
    
    logger.warning(f"Context too large: {current_tokens} tokens > {max_tokens}, truncating...")
    
    # Separate system messages from conversation
    system_messages = []
    conversation_messages = []
    
    for msg in conversation_context:
        if msg.get('role') == 'system':
            system_messages.append(msg)
        else:
            conversation_messages.append(msg)
    
    # Calculate tokens used by system messages
    system_tokens = count_context_tokens(system_messages)
    available_tokens = max_tokens - system_tokens
    
    if available_tokens <= 0:
        logger.error(f"System messages alone exceed token limit: {system_tokens} > {max_tokens}")
        # Emergency truncation of system messages
        truncated_system = _truncate_system_messages(system_messages, max_tokens)
        return truncated_system, current_tokens - count_context_tokens(truncated_system)
    
    # Truncate conversation messages from the beginning (oldest first)
    truncated_conversation = []
    conversation_tokens = 0
    
    # Add messages from most recent backwards until we hit the limit
    for msg in reversed(conversation_messages):
        msg_tokens = estimate_tokens(msg.get('content', ''))
        if conversation_tokens + msg_tokens <= available_tokens:
            truncated_conversation.insert(0, msg)
            conversation_tokens += msg_tokens
        else:
            logger.debug(f"Truncating message: {msg.get('content', '')[:50]}...")
    
    # Combine system and truncated conversation
    final_context = system_messages + truncated_conversation
    final_tokens = count_context_tokens(final_context)
    tokens_removed = current_tokens - final_tokens
    
    logger.info(f"Context truncated: {current_tokens} -> {final_tokens} tokens ({tokens_removed} removed)")
    
    return final_context, tokens_removed

def _truncate_system_messages(system_messages: List[Dict[str, str]], max_tokens: int) -> List[Dict[str, str]]:
    """
    Emergency truncation of system messages when they exceed limits.
    
    Args:
        system_messages: List of system messages
        max_tokens: Token limit
        
    Returns:
        Truncated system messages
    """
    if not system_messages:
        return []
    
    # Keep the first (main) system message and truncate its content if needed
    main_system = system_messages[0].copy()
    content = main_system.get('content', '')
    
    # Estimate how much to truncate
    current_tokens = estimate_tokens(content)
    if current_tokens > max_tokens:
        # Truncate to fit, keeping beginning which has core personality
        target_chars = max_tokens * CHARS_PER_TOKEN
        truncated_content = content[:target_chars] + "... [system prompt truncated due to size]"
        main_system['content'] = truncated_content
        logger.warning(f"Emergency system prompt truncation: {current_tokens} -> {estimate_tokens(truncated_content)} tokens")
    
    return [main_system]

def optimize_memory_context(relevant_memories: List[Dict], max_memories: int = 10) -> List[Dict]:
    """
    Optimize memory context by limiting and prioritizing memories.
    
    Args:
        relevant_memories: List of memory objects
        max_memories: Maximum number of memories to include
        
    Returns:
        Optimized memory list
    """
    if not relevant_memories or len(relevant_memories) <= max_memories:
        return relevant_memories
    
    # Sort by relevance score if available, otherwise by recency
    sorted_memories = sorted(
        relevant_memories,
        key=lambda m: m.get('score', 0.5),
        reverse=True
    )
    
    truncated = sorted_memories[:max_memories]
    logger.info(f"Memory context optimized: {len(relevant_memories)} -> {len(truncated)} memories")
    
    return truncated

def truncate_recent_messages(recent_messages: List, max_messages: int = 8) -> List:
    """
    Limit the number of recent messages to prevent context explosion.
    
    Args:
        recent_messages: List of recent message objects
        max_messages: Maximum messages to keep
        
    Returns:
        Truncated message list
    """
    if not recent_messages or len(recent_messages) <= max_messages:
        return recent_messages
    
    # Keep most recent messages
    truncated = recent_messages[-max_messages:]
    logger.info(f"Recent messages truncated: {len(recent_messages)} -> {len(truncated)} messages")
    
    return truncated