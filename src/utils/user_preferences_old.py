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
]

# Fast name cache (in-memory for single session)
_name_cache = {}


async def detect_name_introduction(message_content: str, user_id: str, memory_manager) -> Optional[str]:
    """
    Detect if user is introducing their name and store it as a preference.
    
    Args:
        message_content: The user's message text
        user_id: User's ID
        memory_manager: Memory manager instance
        
    Returns:
        Detected name if found, None otherwise
    """
    if not message_content:
        return None
        
    content_lower = message_content.lower().strip()
    
    # Patterns for name introduction
    import re
    name_patterns = [
        r"my name is ([a-zA-Z]+)",
        r"call me ([a-zA-Z]+)", 
        r"i'm ([a-zA-Z]+)",
        r"i am ([a-zA-Z]+)",
        r"my name's ([a-zA-Z]+)",
        r"you can call me ([a-zA-Z]+)"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, content_lower)
        if match:
            detected_name = match.group(1).title()
            
            # Validate name (reasonable length, alphabetic)
            if 2 <= len(detected_name) <= 20 and detected_name.isalpha():
                try:
                    # Store as a user preference in PostgreSQL
                    await store_user_preference(
                        user_id=user_id,
                        preference_type="preferred_name",
                        preference_value=detected_name
                    )
                    
                    # Also store in vector memory for conversation context
                    if memory_manager:
                        await memory_manager.store_conversation(
                            user_id=user_id,
                            user_message=f"My name is {detected_name}",
                            bot_response=f"Nice to meet you, {detected_name}! I'll remember your name."
                        )
                    
                    logger.info("Detected and stored preferred name for user %s: %s", user_id, detected_name)
                    return detected_name
                    
                except Exception as e:
                    logger.error("Failed to store preferred name: %s", e)
                    
    return None


async def store_user_preference(user_id: str, preference_type: str, preference_value: str):
    """Store a user preference in PostgreSQL for fast access."""
    try:
        from src.utils.postgresql_user_db import PostgreSQLUserDB
        
        # Get the global PostgreSQL instance
        db = PostgreSQLUserDB()
        await db.initialize()
        
        # Store preference as JSONB in user_profiles table
        if not db.pool:
            logger.error("PostgreSQL pool not available")
            return
            
        async with db.pool.acquire() as connection:
            # First ensure user exists
            await connection.execute(
                """
                INSERT INTO user_profiles (user_id, first_interaction) 
                VALUES ($1, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id
            )
            
            # Store preference in a preferences JSONB column
            await connection.execute(
                """
                UPDATE user_profiles 
                SET preferences = COALESCE(preferences, '{}'::jsonb) || $2::jsonb
                WHERE user_id = $1
                """,
                user_id,
                {preference_type: preference_value}
            )
        
        logger.info("Stored user preference: %s - %s = %s", user_id, preference_type, preference_value)
        
    except Exception as e:
        logger.error("Failed to store user preference: %s", e)
        raise


async def get_user_preferred_name(user_id: str, memory_manager=None) -> Optional[str]:
    """
    Retrieve user's preferred name from PostgreSQL (fast) or fallback to vector memory.
    
    Args:
        user_id: User's ID
        memory_manager: Memory manager instance (fallback only)
        
    Returns:
        Preferred name if found, None otherwise
    """
    # Try PostgreSQL first (fast)
    try:
        from src.utils.postgresql_user_db import PostgreSQLUserDB
        
        db = PostgreSQLUserDB()
        await db.initialize()
        
        if db.pool:
            async with db.pool.acquire() as connection:
                result = await connection.fetchrow(
                    "SELECT preferences FROM user_profiles WHERE user_id = $1",
                    user_id
                )
                
                if result and result['preferences']:
                    preferred_name = result['preferences'].get('preferred_name')
                    if preferred_name:
                        logger.info("Retrieved preferred name from PostgreSQL for user %s: %s", user_id, preferred_name)
                        return preferred_name
                        
    except Exception as e:
        logger.debug("Could not retrieve preferred name from PostgreSQL: %s", e)
    
    # Fallback to vector memory search (slower)
    if memory_manager:
        try:
            name_memories = await memory_manager.search_memories_with_qdrant_intelligence(
                user_id=user_id,
                query="my name is preferred name call me",
                limit=5
            )
            
            if name_memories:
                import re
                name_patterns = [
                    r"my name is ([a-zA-Z]+)",
                    r"call me ([a-zA-Z]+)", 
                    r"i'm ([a-zA-Z]+)",
                    r"i am ([a-zA-Z]+)"
                ]
                
                for memory in name_memories:
                    content = memory.get('content', '').lower()
                    
                    for pattern in name_patterns:
                        match = re.search(pattern, content)
                        if match:
                            potential_name = match.group(1).title()
                            if 2 <= len(potential_name) <= 20 and potential_name.isalpha():
                                logger.info("Retrieved preferred name from vector memory for user %s: %s", user_id, potential_name)
                                # Store in PostgreSQL for faster future access
                                await store_user_preference(user_id, "preferred_name", potential_name)
                                return potential_name
                                
        except Exception as e:
            logger.debug("Could not retrieve preferred name from vector memory: %s", e)
        
    return None


async def get_user_preference(user_id: str, preference_type: str) -> Optional[str]:
    """Get a specific user preference from PostgreSQL."""
    try:
        from src.utils.postgresql_user_db import PostgreSQLUserDB
        
        db = PostgreSQLUserDB()
        await db.initialize()
        
        if db.pool:
            async with db.pool.acquire() as connection:
                result = await connection.fetchrow(
                    "SELECT preferences FROM user_profiles WHERE user_id = $1",
                    user_id
                )
                
                if result and result['preferences']:
                    return result['preferences'].get(preference_type)
                    
    except Exception as e:
        logger.debug("Could not retrieve user preference: %s", e)
        
    return None