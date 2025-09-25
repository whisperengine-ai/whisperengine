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
            # Handle both dictionary and object memory formats
            if isinstance(memory, dict):
                # Dictionary format (current vector memory system)
                content = memory.get('content', '')
                user_message = memory.get('user_message', '')
                metadata = memory.get('metadata', {})
                
                # Check content field for name patterns (primary location in dict format)
                if content:
                    detected_name = _extract_name_from_text(content)
                    if detected_name:
                        timestamp = _get_memory_timestamp(memory)
                        detected_names.append({
                            'name': detected_name,
                            'timestamp': timestamp,
                            'source': 'content',
                            'raw_text': content[:100]
                        })
                
                # Check user_message field for name patterns
                if user_message:
                    detected_name = _extract_name_from_text(user_message)
                    if detected_name:
                        timestamp = _get_memory_timestamp(memory)
                        detected_names.append({
                            'name': detected_name,
                            'timestamp': timestamp,
                            'source': 'user_message',
                            'raw_text': user_message[:100]
                        })
                
                # Check metadata for stored name information
                if isinstance(metadata, dict):
                    stored_name = metadata.get('preferred_name') or metadata.get('user_name')
                    if stored_name:
                        timestamp = _get_memory_timestamp(memory)
                        detected_names.append({
                            'name': stored_name,
                            'timestamp': timestamp,
                            'source': 'metadata',
                            'raw_text': str(metadata)[:100]
                        })
            else:
                # Object format (legacy compatibility)
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
            potential_name = words[0].strip('.,!?"').title()
            if _is_valid_name(potential_name):
                return potential_name
    
    elif "my preferred name is" in text_lower or "my prefered name is" in text_lower:
        # Handle "My preferred name is Mark" (with or without typo)
        if "my preferred name is" in text_lower:
            name_part = text_lower.split("my preferred name is", 1)[1].strip()
        else:
            name_part = text_lower.split("my prefered name is", 1)[1].strip()
        words = name_part.split()
        if words:
            potential_name = words[0].strip('.,!?"').title()
            if _is_valid_name(potential_name):
                return potential_name
    
    elif "prefer to be called" in text_lower:
        # Handle "prefer to be called Mark"
        name_part = text_lower.split("prefer to be called", 1)[1].strip()
        words = name_part.split()
        if words:
            potential_name = words[0].strip('.,!?"').title()
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
    """Extract timestamp from memory object or dictionary."""
    # Handle dictionary format (current vector memory system)
    if isinstance(memory, dict):
        timestamp = memory.get('timestamp') or memory.get('created_at')
        if timestamp:
            return timestamp
        # Check metadata for timestamp
        metadata = memory.get('metadata', {})
        if isinstance(metadata, dict):
            return metadata.get('timestamp') or metadata.get('created_at')
    
    # Handle object format (legacy compatibility)
    if hasattr(memory, 'timestamp') and memory.timestamp:
        return memory.timestamp
    elif hasattr(memory, 'metadata') and memory.metadata:
        if isinstance(memory.metadata, dict):
            return memory.metadata.get('timestamp') or memory.metadata.get('created_at')
    
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
