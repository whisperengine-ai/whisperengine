"""
LLM Tool Calling - User Preferences Management
Vector-native user preference detection and storage using LLM tool calling system.
"""

import logging
import re
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def get_user_preferred_name(user_id: str, memory_manager=None) -> Optional[str]:
    """Get user's preferred name using vector memory search."""
    if not memory_manager:
        logger.debug("No memory manager available for preferred name lookup")
        return None
    
    try:
        # Use vector search to find name-related memories
        name_memories = await memory_manager.retrieve_relevant_memories(
            user_id=user_id,
            query="my name is, call me, I am, preferred name, introduce",
            limit=10
        )
        
        if not name_memories:
            logger.debug(f"No name-related memories found for user {user_id}")
            return None
        
        # Look for the most recent/relevant name information
        # Sort memories by timestamp (most recent first) for conflict resolution
        sorted_memories = _sort_memories_by_timestamp(name_memories)
        
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
                    logger.warning(f"Name conflict detected for user {user_id}: "
                                 f"Current='{most_recent['name']}', Previous={other_names}. "
                                 f"Using most recent. LLM conflict resolution needed.")
            
            logger.info(f"Found preferred name '{most_recent['name']}' for user {user_id} "
                       f"from {most_recent['source']} (timestamp: {most_recent['timestamp']})")
            return most_recent['name']
        
        logger.debug(f"No preferred name found in vector memories for user {user_id}")
        return None
        
    except Exception as e:
        logger.warning(f"Failed to retrieve preferred name from vector memory for user {user_id}: {e}")
        return None


def _extract_name_from_text(text: str) -> Optional[str]:
    """Extract name from text using pattern matching."""
    if not text:
        return None
    
    # Common name introduction patterns
    patterns = [
        r"my name is ([a-zA-Z]+)",
        r"i'm ([a-zA-Z]+)",
        r"i am ([a-zA-Z]+)", 
        r"call me ([a-zA-Z]+)",
        r"name's ([a-zA-Z]+)",
        r"you can call me ([a-zA-Z]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip().title()
            # Basic validation: 2-20 chars, letters only
            if 2 <= len(name) <= 20 and name.isalpha():
                return name
    
    return None


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
