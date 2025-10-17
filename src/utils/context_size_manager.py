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

# 🚀 PHASE 2A: MODERN MODEL CONTEXT BUDGETS (October 2025)
# Upgraded from conservative 8K to leverage modern 128K-200K context windows
# Target utilization: ~18% (24K of 131K for Grok-4-Fast)
# See: docs/architecture/TOKEN_BUDGET_ANALYSIS.md for rationale
MAX_CONTEXT_TOKENS = 24000  # Total input budget (system + conversation)
MAX_RESPONSE_TOKENS = 4000  # Reserve tokens for response generation (increased for richer responses)

# Token budget alignment between stages
# These must match the budgets used in PromptAssembler and MessageProcessor
SYSTEM_PROMPT_MAX_TOKENS = 16000  # Up from 6K - supports rich personalities, full CDL, deep memories (message_processor.py:2096)
CONVERSATION_HISTORY_MAX_TOKENS = 8000  # Up from 2K - supports 30-40 messages of context (~15-20 full exchanges)

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
    max_tokens: int = 8000,  # Phase 2A: Upgraded from 2000 to 8000 for deeper conversation history
    min_recent_messages: int = 2  # Always keep at least 1 exchange (user + bot)
) -> Tuple[List[Dict[str, str]], int]:
    """
    Adaptive token budget management for conversation context.
    
    Dynamically adjusts message history based on content size:
    - Short messages: Keeps many messages (natural conversation flow)
    - Long messages: Keeps fewer messages (prevents token overflow)
    
    This is ADAPTIVE - it fills the token budget from newest to oldest messages,
    ensuring normal users aren't penalized for using the system correctly.
    
    PRODUCTION BUDGET (Phase 2A - October 2025):
    - Average total input: 1,700 tokens (baseline)
    - P90 total input: 3,572 tokens (90% of requests under this)
    - P95 total input: 4,437 tokens
    - NEW TARGET: 24,000 tokens total (16K system + 8K conversation)
    - Models support: 128K-200K tokens (Grok-4/Claude/GPT-4o)
    
    This function manages ONLY conversation history (~8000 tokens), which when
    combined with CDL system prompts (up to 16K) gives total input of
    up to 24K tokens - utilizing ~18% of modern model capacity while leaving
    plenty of headroom for sophisticated character interactions.
    
    Args:
        conversation_context: List of message dicts with 'role' and 'content'
        max_tokens: Maximum total tokens for conversation history (default: 8000)
                   Based on: New budget for deep conversation memory (30-40 messages)
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
    
    Examples (with 8000 token budget):
        - 20 short messages (3200 tokens): All kept ✅
        - 40 normal messages (16000 tokens): ~20 kept, rest dropped ✅
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
        # Use SYSTEM_PROMPT_MAX_TOKENS (6000) not the conversation max_tokens (2000) parameter
        truncated_system = _truncate_system_messages(system_messages, SYSTEM_PROMPT_MAX_TOKENS)
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
    
    Intelligently truncates the middle sections while preserving:
    - Core personality/identity (beginning)
    - Response instructions and reminders (end)
    
    Args:
        system_messages: List of system messages
        max_tokens: Token limit
        
    Returns:
        Truncated system messages with graceful continuation instructions
    """
    if not system_messages:
        return []
    
    # Keep the first (main) system message and truncate its content if needed
    main_system = system_messages[0].copy()
    content = main_system.get('content', '')
    
    # Estimate how much to truncate
    current_tokens = estimate_tokens(content)
    if current_tokens > max_tokens:
        # Reserve tokens for beginning (core identity) and ending (instructions)
        target_chars = max_tokens * CHARS_PER_TOKEN
        
        # Strategy: Keep first 60% and last 20% of available space, truncate middle
        beginning_chars = int(target_chars * 0.60)
        ending_chars = int(target_chars * 0.20)
        
        # Extract beginning and ending sections
        beginning_section = content[:beginning_chars]
        ending_section = content[-ending_chars:] if ending_chars > 0 else ""
        
        # Create graceful truncation notice that maintains conversational flow
        truncation_notice = (
            "\n\n[Note: Full character context exceeds size limits. "
            "Core personality, relationships, and response guidelines preserved. "
            "Continue conversation naturally with available context.]\n\n"
        )
        
        # Assemble truncated content: beginning + notice + ending
        truncated_content = beginning_section + truncation_notice + ending_section
        
        main_system['content'] = truncated_content
        logger.warning(
            "🎭 Emergency system prompt truncation: %d -> %d tokens "
            "(preserved: beginning %d chars + ending %d chars, removed middle section)",
            current_tokens, estimate_tokens(truncated_content), 
            beginning_chars, ending_chars
        )
    
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