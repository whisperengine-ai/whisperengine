"""
User Preferences Management - Optimized Version
Fast dual-storage system: PostgreSQL for structured preferences + Qdrant for semantic fallback
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Optimized regex patterns for name detection (compiled for speed)
NAME_PATTERNS = [
    re.compile(r"my name is ([a-zA-Z]+)", re.IGNORECASE),
    re.compile(r"i'm ([a-zA-Z]+)", re.IGNORECASE), 
    re.compile(r"i am ([a-zA-Z]+)", re.IGNORECASE),
    re.compile(r"call me ([a-zA-Z]+)", re.IGNORECASE),
    re.compile(r"name's ([a-zA-Z]+)", re.IGNORECASE),
    re.compile(r"you can call me ([a-zA-Z]+)", re.IGNORECASE),
]

# Fast name cache (in-memory for single session)
_name_cache = {}


def detect_name_introduction(message_content: str) -> Optional[str]:
    """
    Fast name detection using compiled regex patterns.
    Returns detected name immediately without async operations.
    
    Args:
        message_content: The user's message text
        
    Returns:
        Detected name if found, None otherwise
    """
    if not message_content:
        return None
        
    content_clean = message_content.strip()
    
    # Try each compiled pattern for fast matching
    for pattern in NAME_PATTERNS:
        match = pattern.search(content_clean)
        if match:
            detected_name = match.group(1).strip().title()
            # Simple validation: name should be 2-20 chars, only letters
            if 2 <= len(detected_name) <= 20 and detected_name.isalpha():
                logger.info(f"Detected name introduction: '{detected_name}' from message: '{content_clean[:50]}...'")
                return detected_name
                
    return None


async def detect_name_introduction_and_store(message_content: str, user_id: str, memory_manager=None) -> Optional[str]:
    """
    Enhanced function that detects names AND stores them immediately.
    Used in message processing pipeline for automatic name capture.
    
    Args:
        message_content: The user's message text
        user_id: User's ID
        memory_manager: Memory manager instance (optional)
        
    Returns:
        Detected name if found, None otherwise
    """
    detected_name = detect_name_introduction(message_content)
    
    if detected_name:
        # Store immediately in PostgreSQL for fast future access
        try:
            from src.utils.postgresql_user_db import PostgreSQLUserDB
            db = PostgreSQLUserDB()
            await db.initialize()
            
            await store_user_preference(user_id, "preferred_name", detected_name, db)
            logger.info(f"Auto-stored preferred name '{detected_name}' for user {user_id}")
            
            # Also cache it for this session
            _name_cache[user_id] = detected_name
            
        except Exception as e:
            logger.error(f"Failed to store detected name: {e}")
            # Continue anyway - we detected the name even if storage failed
            
    return detected_name


async def store_user_preference(user_id: str, preference_type: str, preference_value: str, db=None):
    """
    Store a user preference in PostgreSQL for fast access.
    
    Args:
        user_id: User ID
        preference_type: Type of preference (e.g., 'preferred_name')
        preference_value: Value to store
        db: Optional database instance (will create if not provided)
    """
    if not db:
        from src.utils.postgresql_user_db import PostgreSQLUserDB
        db = PostgreSQLUserDB()
        await db.initialize()
    
    try:
        # Get existing user profile or create new one
        user_profile = await db.get_user_profile(user_id)
        
        if user_profile:
            # Update existing preferences
            preferences = user_profile.preferences or {}
            preferences[preference_type] = preference_value
            
            # Update the profile
            user_profile.preferences = preferences
            await db.update_user_profile(user_profile)
            
        else:
            # Create new user profile with preference
            from src.utils.user_profile import UserProfile
            new_profile = UserProfile(
                user_id=user_id,
                preferences={preference_type: preference_value}
            )
            await db.create_user_profile(new_profile)
            
        logger.info(f"Stored preference {preference_type}={preference_value} for user {user_id}")
        
        # Also cache it
        _name_cache[user_id] = preference_value if preference_type == "preferred_name" else _name_cache.get(user_id)
        
    except Exception as e:
        logger.error(f"Failed to store user preference: {e}")
        raise


async def get_user_preference(user_id: str, preference_type: str, db=None) -> Optional[str]:
    """
    Get a user preference with fast caching.
    
    Args:
        user_id: User ID
        preference_type: Type of preference to retrieve
        db: Optional database instance
        
    Returns:
        Preference value if found, None otherwise
    """
    # Check cache first for preferred_name
    if preference_type == "preferred_name" and user_id in _name_cache:
        return _name_cache[user_id]
    
    if not db:
        from src.utils.postgresql_user_db import PostgreSQLUserDB
        db = PostgreSQLUserDB()
        await db.initialize()
    
    try:
        user_profile = await db.get_user_profile(user_id)
        if user_profile and user_profile.preferences:
            preference_value = user_profile.preferences.get(preference_type)
            
            # Cache preferred names for speed
            if preference_type == "preferred_name" and preference_value:
                _name_cache[user_id] = preference_value
                
            return preference_value
            
    except Exception as e:
        logger.error(f"Failed to get user preference: {e}")
        
    return None


async def get_user_preferred_name(user_id: str, memory_manager=None) -> Optional[str]:
    """
    Get user's preferred name with optimized dual-storage approach.
    
    Priority:
    1. Fast cache (in-memory)
    2. PostgreSQL (structured fast access)
    3. Qdrant vector search (semantic fallback)
    
    Args:
        user_id: User ID
        memory_manager: Optional memory manager for vector fallback
        
    Returns:
        User's preferred name if found, None otherwise
    """
    # 1. Check fast cache first
    if user_id in _name_cache:
        return _name_cache[user_id]
    
    # 2. Try PostgreSQL (fast structured access)
    try:
        from src.utils.postgresql_user_db import PostgreSQLUserDB
        db = PostgreSQLUserDB()
        await db.initialize()
        
        user_profile = await db.get_user_profile(user_id)
        if user_profile and user_profile.preferences:
            preferred_name = user_profile.preferences.get('preferred_name')
            if preferred_name:
                logger.info("Retrieved preferred name from PostgreSQL for user %s: %s", user_id, preferred_name)
                # Cache it for next time
                _name_cache[user_id] = preferred_name
                return preferred_name
                
    except Exception as e:
        logger.warning(f"PostgreSQL lookup failed for user {user_id}: {e}")
    
    # 3. Fallback to vector memory search (slower but semantic)
    if memory_manager:
        try:
            memories = await memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="my name is",
                limit=5
            )
            
            # Look for name introductions in conversation history
            for memory in memories:
                if hasattr(memory, 'user_message'):
                    detected_name = detect_name_introduction(memory.user_message)
                    if detected_name:
                        logger.info(f"Found preferred name in vector memory: {detected_name}")
                        
                        # Store it in PostgreSQL for faster future access
                        try:
                            await store_user_preference(user_id, "preferred_name", detected_name)
                        except Exception as store_e:
                            logger.warning(f"Failed to store found name in PostgreSQL: {store_e}")
                        
                        # Cache it
                        _name_cache[user_id] = detected_name
                        return detected_name
                        
        except Exception as e:
            logger.warning(f"Vector memory fallback failed: {e}")
    
    return None


def clear_cache():
    """Clear the in-memory name cache (useful for testing)"""
    global _name_cache
    _name_cache = {}
    logger.info("Cleared user preferences cache")