"""
Context size management utilities for preventing oversized LLM requests.

This module provides token counting and context truncation to prevent
the massive context sizes that were causing response failures.
"""

import logging
import re
from typing import Dict, List, Tuple

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
    max_tokens: int = 2000,  # Production data: P90 = 3572 total, minus ~1400 system prompt = 2000 for history
    min_recent_messages: int = 2  # Always keep at least 1 exchange (user + bot)
) -> Tuple[List[Dict[str, str]], int]:
    """
    Adaptive token budget management for conversation context.
    
    Dynamically adjusts message history based on content size:
    - Short messages: Keeps many messages (natural conversation flow)
    - Long messages: Keeps fewer messages (prevents token overflow)
    
    This is ADAPTIVE - it fills the token budget from newest to oldest messages,
    ensuring normal users aren't penalized for using the system correctly.
    
    PRODUCTION BUDGET (based on actual OpenRouter usage data):
    - Average total input: 1,700 tokens
    - P90 total input: 3,572 tokens (90% of requests under this)
    - P95 total input: 4,437 tokens
    
    This function manages ONLY conversation history (~2000 tokens), which when
    combined with CDL system prompts (700-1900 tokens) gives total input of
    2700-3900 tokens - matching production P90 at 3,572 tokens.
    
    Args:
        conversation_context: List of message dicts with 'role' and 'content'
        max_tokens: Maximum total tokens for conversation history (default: 2000)
                   Based on: 3572 (P90 total) - 1400 (avg system prompt) = 2000
        min_recent_messages: Minimum messages to keep regardless of size (default: 2)
                            Guarantees at least 1 exchange (user + assistant) for continuity
    
    Returns:
        Tuple of (truncated_context, tokens_removed_count)
    
    Algorithm:
        1. Count total tokens in conversation
        2. If under budget: Return unchanged
        3. If over budget: 
           - Start with min_recent_messages (most recent)
           - Add older messages one-by-one until budget fills
           - Drop remaining oldest messages
        4. Log truncation events for monitoring
    
    Examples (with 2000 token budget):
        - 10 short messages (800 tokens): All kept ✅
        - 15 long messages (13520 tokens): 3-4 kept, rest dropped ✅
        - Mixed content: Adaptive - fills budget optimally ✅
    """
    if not conversation_context:
        return conversation_context, 0
    
    # Count current tokens
    current_tokens = count_context_tokens(conversation_context)
    
    # If under budget, return as-is
    if current_tokens <= max_tokens:
        logger.debug("Context size OK: %d/%d tokens", current_tokens, max_tokens)
        return conversation_context, 0
    
    logger.warning("⚠️ Context over budget: %d tokens > %d limit - applying adaptive truncation", current_tokens, max_tokens)
    
    # Separate system messages from conversation messages
    system_messages = []
    conversation_messages = []
    
    for msg in conversation_context:
        if msg.get('role') == 'system':
            system_messages.append(msg)
        else:
            conversation_messages.append(msg)
    
    # Calculate tokens used by system messages (NEVER truncate these - character personality is sacred)
    system_tokens = count_context_tokens(system_messages)
    available_tokens = max_tokens - system_tokens
    
    if available_tokens <= 0:
        logger.error("🚨 CRITICAL: System messages alone exceed token limit: %d > %d", system_tokens, max_tokens)
        # Emergency truncation of system messages
        truncated_system = _truncate_system_messages(system_messages, max_tokens)
        return truncated_system, current_tokens - count_context_tokens(truncated_system)
    
    # ADAPTIVE TRUNCATION: Add messages from MOST RECENT backwards until budget fills
    # This naturally keeps MORE messages if they're short, FEWER if they're walls of text
    included_messages = []
    included_tokens = 0
    messages_preserved = 0
    
    # Iterate BACKWARDS from most recent
    for msg in reversed(conversation_messages):
        msg_tokens = estimate_tokens(msg.get('content', ''))
        
        # Always include at least min_recent_messages (even if over budget slightly)
        if messages_preserved < min_recent_messages:
            included_messages.insert(0, msg)
            included_tokens += msg_tokens
            messages_preserved += 1
            logger.debug("Preserving recent message %d (min guarantee): %d tokens", messages_preserved, msg_tokens)
        # After minimum, only add if fits in budget
        elif included_tokens + msg_tokens <= available_tokens:
            included_messages.insert(0, msg)
            included_tokens += msg_tokens
            messages_preserved += 1
            logger.debug("Including message %d (fits budget): %d tokens", messages_preserved, msg_tokens)
        else:
            logger.debug("Dropping older message (budget full): '%.50s...' (%d tokens)", 
                        msg.get('content', ''), msg_tokens)
    
    # Build final context: system + included messages
    final_context = system_messages + included_messages
    final_tokens = count_context_tokens(final_context)
    tokens_removed = current_tokens - final_tokens
    messages_removed = len(conversation_messages) - len(included_messages)
    
    logger.warning("✂️ Adaptive truncation: %d -> %d tokens (%d messages kept, %d removed)", 
                   current_tokens, final_tokens, len(included_messages), messages_removed)
    
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
        logger.warning("Emergency system prompt truncation: %d -> %d tokens", current_tokens, estimate_tokens(truncated_content))
    
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
    logger.info("Memory context optimized: %d -> %d memories", len(relevant_memories), len(truncated))
    
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
    logger.info("Recent messages truncated: %d -> %d messages", len(recent_messages), len(truncated))
    
    return truncated