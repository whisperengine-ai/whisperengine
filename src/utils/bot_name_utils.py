#!/usr/bin/env python3
"""
Bot Name Normalization Utilities

Centralized utilities for consistent bot name handling across WhisperEngine.
This prevents memory isolation failures and ensures consistent character identification.
"""

import re
import os
from typing import Optional


def normalize_bot_name(bot_name: str) -> str:
    """
    Normalize bot name for consistent character identification across all systems.
    
    CRITICAL: This function prevents character identification failures due to:
    - Case sensitivity: "Elena" vs "elena" 
    - Space handling: "Marcus Chen" vs "marcus_chen"
    - Special characters and inconsistent formatting
    - Bot prefix handling: "bot_elena" vs "elena_bot" vs "elena"
    
    Rules:
    - Convert to lowercase for case-insensitive matching
    - Replace spaces with underscores for system compatibility
    - Remove special characters except underscore/hyphen/alphanumeric
    - Strip "bot_" prefix and "_bot" suffix for canonical form
    - Handle empty/None values gracefully
    
    Examples:
    - "Elena" -> "elena"
    - "Marcus Chen" -> "marcus_chen" 
    - "Dream of the Endless" -> "dream_of_the_endless"
    - "bot_elena" -> "elena"
    - "elena_bot" -> "elena"
    - "Bot_Elena" -> "elena"
    - "ELENA_BOT" -> "elena"
    - None -> "unknown"
    """
    if not bot_name or not isinstance(bot_name, str):
        return "unknown"
    
    # Step 1: Trim and lowercase
    normalized = bot_name.strip().lower()
    
    # Step 2: Remove bot prefixes and suffixes for canonical form
    if normalized.startswith('bot_'):
        normalized = normalized[4:]  # Remove "bot_" prefix
    if normalized.endswith('_bot'):
        normalized = normalized[:-4]  # Remove "_bot" suffix
    
    # Step 3: Replace spaces with underscores
    normalized = re.sub(r'\s+', '_', normalized)
    
    # Step 4: Remove special characters except underscore/hyphen/alphanumeric
    normalized = re.sub(r'[^a-z0-9_-]', '', normalized)
    
    # Step 5: Collapse multiple underscores/hyphens
    normalized = re.sub(r'[_-]+', '_', normalized)
    
    # Step 6: Remove leading/trailing underscores
    normalized = normalized.strip('_-')
    
    return normalized if normalized else "unknown"


def get_normalized_bot_name_from_env() -> str:
    """
    Get normalized bot name from environment variables with fallback.
    
    Checks multiple environment variables in order of preference:
    1. DISCORD_BOT_NAME (preferred)
    2. BOT_NAME (fallback)
    3. "unknown" (default)
    
    Returns:
        Normalized bot name string
    """
    raw_bot_name = (
        os.getenv("DISCORD_BOT_NAME") or 
        os.getenv("BOT_NAME") or 
        "unknown"
    )
    return normalize_bot_name(raw_bot_name.strip())


def get_collection_name_for_bot(bot_name: Optional[str] = None) -> str:
    """
    Generate the standardized Qdrant collection name for a bot.
    
    Args:
        bot_name: Optional bot name. If None, uses environment variables.
        
    Returns:
        Standardized collection name in format: whisperengine_memory_{normalized_name}
        
    Examples:
        - "elena" -> "whisperengine_memory_elena"
        - "Marcus Chen" -> "whisperengine_memory_marcus_chen"
        - None (with DISCORD_BOT_NAME=elena) -> "whisperengine_memory_elena"
    """
    if bot_name is None:
        bot_name = get_normalized_bot_name_from_env()
    else:
        bot_name = normalize_bot_name(bot_name)
    
    return f"whisperengine_memory_{bot_name}"


def extract_bot_name_from_collection(collection_name: str) -> str:
    """
    Extract bot name from WhisperEngine collection name.
    
    Handles both current format and legacy format with _7d suffix:
    - whisperengine_memory_elena -> elena
    - whisperengine_memory_elena_7d -> elena
    
    Args:
        collection_name: Full Qdrant collection name
        
    Returns:
        Normalized bot name extracted from collection name
    """
    if not collection_name or not isinstance(collection_name, str):
        return "unknown"
    
    # Remove the standard prefix
    if collection_name.startswith('whisperengine_memory_'):
        bot_name = collection_name[21:]  # Remove "whisperengine_memory_" prefix
        
        # Remove legacy _7d suffix if present
        if bot_name.endswith('_7d'):
            bot_name = bot_name[:-3]
            
        return bot_name if bot_name else "unknown"
    
    # If it doesn't match our format, try to normalize it anyway
    return normalize_bot_name(collection_name)