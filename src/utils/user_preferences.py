"""
LLM Tool Calling - User Preferences Management
Vector-native user preference detection and storage using LLM tool calling system.
"""

import logging
import re
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def get_user_preferred_name(user_id: str, memory_manager=None, discord_username: str = None) -> Optional[str]:
    """
    Get user's preferred name using vector memory search.
    
    Args:
        user_id: The user's ID
        memory_manager: Memory manager for vector search
        discord_username: Discord username as fallback if no stored name found
        
    Returns:
        Preferred name if found, discord_username as fallback, or None
    """
    if not memory_manager:
        logger.debug("No memory manager available for preferred name lookup")
        return discord_username
    
    try:
        # Use vector search to find name-related memories and facts
        search_queries = [
            "my name is, call me, I am, preferred name, introduce",
            "name fact user preferred",
            "user name introduction"
        ]
        
        all_memories = []
        for query in search_queries:
            memories = await memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=query,
                limit=15
            )
            all_memories.extend(memories)
        
        # Also search for facts specifically
        if hasattr(memory_manager, 'retrieve_facts'):
            try:
                facts = await memory_manager.retrieve_facts(
                    user_id=user_id,
                    query="name preferred user",
                    limit=10
                )
                all_memories.extend(facts)
            except Exception as e:
                logger.debug("Facts retrieval failed: %s", e)
        
        if not all_memories:
            logger.debug("No name-related memories found for user %s, using Discord username: %s", 
                        user_id, discord_username)
            return discord_username
        
        # Look for the most recent/relevant name information
        # Sort memories by timestamp (most recent first) for conflict resolution
        sorted_memories = _sort_memories_by_timestamp(all_memories)
        
        detected_names = []
        for memory in sorted_memories:
            # Check user messages for name patterns
            if hasattr(memory, 'user_message') and memory.user_message:
                detected_name = _extract_name_from_text(memory.user_message)
                if detected_name:
                    timestamp = _get_memory_timestamp(memory)
                    detected_names.append({
                        'name': detected_name,
                        'timestamp': timestamp,
                        'source': 'user_message',
                        'raw_text': memory.user_message[:100]
                    })
            
            # Check metadata for stored name information
            if hasattr(memory, 'metadata') and memory.metadata:
                if isinstance(memory.metadata, dict):
                    stored_name = memory.metadata.get('preferred_name') or memory.metadata.get('user_name')
                    if stored_name:
                        timestamp = _get_memory_timestamp(memory)
                        detected_names.append({
                            'name': stored_name,
                            'timestamp': timestamp,
                            'source': 'metadata',
                            'raw_text': str(memory.metadata)[:100]
                        })
        
        # Return most recent name, with conflict detection logging
        if detected_names:
            most_recent = detected_names[0]  # Already sorted by timestamp
            
            # Log potential conflicts for LLM resolution
            if len(detected_names) > 1:
                other_names = [n['name'] for n in detected_names[1:] if n['name'] != most_recent['name']]
                if other_names:
                    logger.warning("Name conflict detected for user %s: Current='%s', Previous=%s. Using most recent", 
                                 user_id, most_recent['name'], other_names)
            
            logger.info("Found preferred name '%s' for user %s from %s", 
                       most_recent['name'], user_id, most_recent['source'])
            return most_recent['name']
        
        logger.debug("No preferred name found in vector memories for user %s, using Discord username: %s", 
                    user_id, discord_username)
        return discord_username
        
    except (ValueError, RuntimeError, OSError) as e:
        logger.warning("Failed to retrieve preferred name from vector memory for user %s: %s", user_id, e)
        return discord_username


def _extract_name_from_text(text: str) -> Optional[str]:
    """
    Extract name from text using improved pattern matching.
    
    NOTE: This method uses basic patterns as a fallback while maintaining compatibility.
    For production use, consider replacing with LLM-based name extraction for better accuracy.
    """
    if not text:
        return None
    
    # Improved name introduction detection with fewer hardcoded patterns
    text_lower = text.lower().strip()
    
    # Look for explicit name introductions
    if "my name is" in text_lower:
        # Find the part after "my name is"
        name_part = text_lower.split("my name is", 1)[1].strip()
        # Extract first word that looks like a name
        words = name_part.split()
        if words:
            potential_name = words[0].strip('.,!?').title()
            if _is_valid_name(potential_name):
                return potential_name
    
    elif text_lower.startswith("i'm ") or text_lower.startswith("i am "):
        # Handle "I'm John" or "I am John"
        words = text_lower.split()
        if len(words) >= 2:
            potential_name = words[1].strip('.,!?').title()
            if _is_valid_name(potential_name):
                return potential_name
    
    elif "call me " in text_lower:
        # Find the part after "call me"
        name_part = text_lower.split("call me ", 1)[1].strip()
        words = name_part.split()
        if words:
            potential_name = words[0].strip('.,!?').title()
            if _is_valid_name(potential_name):
                return potential_name
    
    return None


def _is_valid_name(name: str) -> bool:
    """Validate if a string looks like a valid name."""
    if not name or not isinstance(name, str):
        return False
    
    # Basic validation: 2-20 chars, mostly letters
    if not (2 <= len(name) <= 20):
        return False
    
    # Must be mostly alphabetic (allow for names like "Mary-Ann" or "O'Connor")
    alpha_chars = sum(1 for c in name if c.isalpha())
    if alpha_chars < len(name) * 0.7:  # At least 70% alphabetic
        return False
    
    # Avoid common non-name words
    non_names = {'and', 'the', 'but', 'you', 'not', 'yes', 'can', 'will', 'that', 'this'}
    if name.lower() in non_names:
        return False
    
    return True


def _sort_memories_by_timestamp(memories):
    """Sort memories by timestamp, most recent first."""
    def get_sort_key(memory):
        timestamp = _get_memory_timestamp(memory)
        if timestamp is None:
            return 0  # Put memories without timestamps at the end
        if isinstance(timestamp, str):
            try:
                from datetime import datetime
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
            except:
                return 0
        elif isinstance(timestamp, (int, float)):
            return timestamp
        else:
            return 0
    
    return sorted(memories, key=get_sort_key, reverse=True)


def _get_memory_timestamp(memory):
    """Extract timestamp from memory object."""
    # Try different timestamp locations
    if hasattr(memory, 'timestamp') and memory.timestamp:
        return memory.timestamp
    elif hasattr(memory, 'metadata') and memory.metadata:
        if isinstance(memory.metadata, dict):
            return memory.metadata.get('timestamp') or memory.metadata.get('created_at')
    elif isinstance(memory, dict):
        return memory.get('timestamp') or memory.get('created_at')
    return None


# TODO: Implement LLM tool calling for automatic preference detection and storage
async def detect_and_store_preferences_via_llm(
    user_id: str,
    message_content: str,
    memory_manager=None,
    llm_client=None
) -> Dict[str, Any]:
    """
    Future implementation: Use LLM tool calling to automatically detect and store preferences.
    
    This will solve the conflict resolution problem by using LLM intelligence to:
    
    CONFLICT RESOLUTION EXAMPLES:
    
    Scenario 1 - Name Correction:
    User: "My name is Alice"  
    [LLM stores: store_semantic_memory("User's name is Alice")]
    
    User: "Actually, my name is Bob, not Alice"
    [LLM detects correction and calls: update_memory_context(
        search_query="user name Alice", 
        correction="User's actual name is Bob, Alice was incorrect",
        merge_strategy="replace"
    )]
    
    Scenario 2 - Name Change:
    User: "My name is Alice"
    [stored in memory]
    
    User: "I go by Bob now" 
    [LLM detects name change and calls: store_semantic_memory(
        "User now prefers to be called Bob (changed from Alice)",
        importance=9,
        tags=["name_change", "preference_update"]
    )]
    
    Scenario 3 - Context-Aware Resolution:
    User: "My name is Dr. Smith but call me John"
    [LLM stores both: formal_name="Dr. Smith", preferred_name="John"]
    
    INTELLIGENT FEATURES:
    - Detects corrections vs. changes vs. context
    - Maintains history while prioritizing current preference
    - Cross-references with conversation context
    - Automatic conflict resolution based on temporal and semantic cues
    - Learning from user feedback patterns
    
    Args:
        user_id: User ID
        message_content: The user's message content  
        memory_manager: Memory manager instance
        llm_client: LLM client for intelligent analysis
        
    Returns:
        Dictionary containing detected preferences and actions taken
    """
    # TODO: Implement when LLM tool calling Phase 2 (Character Evolution Tools) is ready
    # This will use the intelligent memory manager and vector memory tool manager
    # to automatically detect, resolve conflicts, and store user preferences
    logger.debug("LLM-based preference detection not yet implemented - using Phase 1 tools")
    return {}
