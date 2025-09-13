"""
PostgreSQL User Profile Database

This module provides PostgreSQL-based user profile and emotion management
for the Discord bot, replacing the SQLite implementation.
"""

import asyncio
import asyncpg
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Import the shared emotion and user profile classes from emotion_manager
from .emotion_manager import EmotionalState, RelationshipLevel, EmotionProfile, UserProfile

logger = logging.getLogger(__name__)

def _convert_relationship_level_to_int(relationship_level: RelationshipLevel) -> int:
    """Convert RelationshipLevel enum to integer for database storage"""
    mapping = {
        RelationshipLevel.STRANGER: 1,
        RelationshipLevel.ACQUAINTANCE: 2,
        RelationshipLevel.FRIEND: 3,
        RelationshipLevel.CLOSE_FRIEND: 4
    }
    return mapping.get(relationship_level, 1)  # Default to STRANGER


def _convert_legacy_relationship_level(value) -> RelationshipLevel:
    """Convert legacy integer relationship levels to new enum values"""
    if isinstance(value, int):
        # Legacy integer mapping
        mapping = {
            1: RelationshipLevel.STRANGER,
            2: RelationshipLevel.ACQUAINTANCE, 
            3: RelationshipLevel.FRIEND,
            4: RelationshipLevel.CLOSE_FRIEND
        }
        return mapping.get(value, RelationshipLevel.STRANGER)
    elif isinstance(value, str):
        try:
            return RelationshipLevel(value)
        except ValueError:
            logger.warning(f"Unknown relationship level string: {value}, defaulting to STRANGER")
            return RelationshipLevel.STRANGER
    else:
        logger.warning(f"Unknown relationship level type: {type(value)}, defaulting to STRANGER")
        return RelationshipLevel.STRANGER

class PostgreSQLUserDB:
    """PostgreSQL-based user profile database"""
    
    def __init__(self):
        self.pool = None
        self._lock = asyncio.Lock()  # Add async lock for concurrent operations
        
        self._connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'whisper_engine'),
            'user': os.getenv('POSTGRES_USER', 'bot_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'bot_password_change_me'),
            'min_size': 5,  # Minimum connections in pool
            'max_size': 20  # Maximum connections in pool
        }
        
    async def initialize(self):
        """Initialize the database connection pool and create tables"""
        if self.pool is not None:
            return  # Already initialized
            
        try:
            self.pool = await asyncpg.create_pool(**self._connection_params)
            await self._create_tables()
            logger.info("PostgreSQL database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL database: {e}")
            raise
    
    async def _create_tables(self):
        """Create the user profiles table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255),
            relationship_level INTEGER DEFAULT 1,
            current_emotion VARCHAR(50) DEFAULT 'neutral',
            interaction_count INTEGER DEFAULT 0,
            first_interaction TIMESTAMP,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            emotion_history JSONB DEFAULT '[]'::jsonb,
            escalation_count INTEGER DEFAULT 0,
            trust_indicators JSONB DEFAULT '[]'::jsonb
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_profiles_last_interaction 
        ON user_profiles(last_interaction);
        
        CREATE INDEX IF NOT EXISTS idx_user_profiles_relationship_level 
        ON user_profiles(relationship_level);
        """
        
        async with self.pool.acquire() as connection:
            await connection.execute(create_table_sql)
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get a user profile by user_id"""
        if not self.pool:
            await self.initialize()
            
        if not self.pool:
            logger.error("Database pool is not available")
            return None
            
        try:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(
                    "SELECT * FROM user_profiles WHERE user_id = $1", user_id
                )
                
                if row:
                    # Convert JSON emotion history back to EmotionProfile objects
                    emotion_history = []
                    for emotion_data in (row['emotion_history'] or []):
                        if isinstance(emotion_data, dict):
                            emotion_history.append(EmotionProfile(
                                detected_emotion=EmotionalState(emotion_data['emotion']),
                                confidence=emotion_data['confidence'],
                                triggers=emotion_data['triggers'],
                                intensity=emotion_data['intensity'],
                                timestamp=datetime.fromisoformat(emotion_data['timestamp'])
                            ))
                    
                    # Handle trust_indicators type conversion
                    trust_indicators = row['trust_indicators'] or []
                    if isinstance(trust_indicators, str):
                        try:
                            import json
                            trust_indicators = json.loads(trust_indicators)
                        except (json.JSONDecodeError, TypeError):
                            trust_indicators = []
                    elif not isinstance(trust_indicators, list):
                        trust_indicators = []
                    
                    return UserProfile(
                        user_id=row['user_id'],
                        name=row['name'],
                        relationship_level=_convert_legacy_relationship_level(row['relationship_level']),
                        current_emotion=EmotionalState(row['current_emotion']),
                        interaction_count=row['interaction_count'],
                        first_interaction=row['first_interaction'],
                        last_interaction=row['last_interaction'],
                        emotion_history=emotion_history,
                        escalation_count=row['escalation_count'],
                        trust_indicators=trust_indicators
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return None
    
    async def save_user_profile(self, profile: UserProfile):
        """Save or update a user profile with enhanced concurrency handling"""
        if not self.pool:
            await self.initialize()
            
        if not self.pool:
            raise Exception("Database pool is not available")
            
        # Use async lock to prevent concurrent operations
        async with self._lock:
            max_retries = 3
            retry_delay = 0.1
            
            for attempt in range(max_retries):
                connection = None
                try:
                    # Convert EmotionProfile objects to JSON-serializable dicts
                    emotion_history_json = []
                    for emotion in profile.emotion_history or []:
                        emotion_history_json.append({
                            'emotion': emotion.detected_emotion.value,
                            'confidence': emotion.confidence,
                            'triggers': emotion.triggers,
                            'intensity': emotion.intensity,
                            'timestamp': emotion.timestamp.isoformat()
                        })
                    
                    # Get connection with timeout and check for pool health
                    if not self.pool or (hasattr(self.pool, 'is_closing') and self.pool.is_closing()):
                        raise Exception("Database pool is not available or closing")
                        
                    connection = await asyncio.wait_for(self.pool.acquire(), timeout=5.0)
                    
                    await asyncio.wait_for(connection.execute("""
                        INSERT INTO user_profiles (
                            user_id, name, relationship_level, current_emotion,
                            interaction_count, first_interaction, last_interaction,
                            emotion_history, escalation_count, trust_indicators
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (user_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            relationship_level = EXCLUDED.relationship_level,
                            current_emotion = EXCLUDED.current_emotion,
                            interaction_count = EXCLUDED.interaction_count,
                            first_interaction = EXCLUDED.first_interaction,
                            last_interaction = EXCLUDED.last_interaction,
                            emotion_history = EXCLUDED.emotion_history,
                            escalation_count = EXCLUDED.escalation_count,
                            trust_indicators = EXCLUDED.trust_indicators
                    """, 
                        profile.user_id,
                        profile.name,
                        _convert_relationship_level_to_int(profile.relationship_level),
                        profile.current_emotion.value,
                        profile.interaction_count,
                        profile.first_interaction,
                        profile.last_interaction,
                        json.dumps(emotion_history_json),
                        profile.escalation_count,
                        json.dumps(profile.trust_indicators or [])
                    ), timeout=10.0)
                    
                    # If we get here, the operation was successful
                    return
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Database operation timed out for user {profile.user_id}, attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                    else:
                        raise Exception(f"Database operation timed out after {max_retries} attempts")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "another operation is in progress" in error_msg.lower():
                        logger.warning(f"Connection busy for user {profile.user_id}, attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue
                    
                    logger.error(f"Error saving user profile for {profile.user_id}: {e}")
                    raise
                finally:
                    # Always release the connection back to the pool
                    if connection and self.pool:
                        try:
                            # Check if the pool is still available before releasing
                            if not (hasattr(self.pool, 'is_closing') and self.pool.is_closing()):
                                await self.pool.release(connection)
                        except Exception as e:
                            logger.warning(f"Error releasing connection: {e}")
    
    async def get_all_profiles(self) -> Dict[str, UserProfile]:
        """Get all user profiles"""
        if not self.pool:
            await self.initialize()
            
        if not self.pool:
            logger.error("Database pool is not available")
            return {}
            
        try:
            async with self.pool.acquire() as connection:
                rows = await connection.fetch("SELECT * FROM user_profiles")
                
                profiles = {}
                for row in rows:
                    # Convert JSON emotion history back to EmotionProfile objects
                    emotion_history = []
                    for emotion_data in (row['emotion_history'] or []):
                        if isinstance(emotion_data, dict):
                            emotion_history.append(EmotionProfile(
                                detected_emotion=EmotionalState(emotion_data['emotion']),
                                confidence=emotion_data['confidence'],
                                triggers=emotion_data['triggers'],
                                intensity=emotion_data['intensity'],
                                timestamp=datetime.fromisoformat(emotion_data['timestamp'])
                            ))
                    
                    profile = UserProfile(
                        user_id=row['user_id'],
                        name=row['name'],
                        relationship_level=_convert_legacy_relationship_level(row['relationship_level']),
                        current_emotion=EmotionalState(row['current_emotion']),
                        interaction_count=row['interaction_count'],
                        first_interaction=row['first_interaction'],
                        last_interaction=row['last_interaction'],
                        emotion_history=emotion_history,
                        escalation_count=row['escalation_count'],
                        trust_indicators=row['trust_indicators'] or []
                    )
                    profiles[profile.user_id] = profile
                
                return profiles
                
        except Exception as e:
            logger.error(f"Error getting all profiles: {e}")
            return {}
    
    async def delete_user_profile(self, user_id: str):
        """Delete a user profile"""
        if not self.pool:
            await self.initialize()
            
        if not self.pool:
            raise Exception("Database pool is not available")
            
        try:
            async with self.pool.acquire() as connection:
                await connection.execute(
                    "DELETE FROM user_profiles WHERE user_id = $1", user_id
                )
                
        except Exception as e:
            logger.error(f"Error deleting user profile for {user_id}: {e}")
            raise
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL database connection closed")
    
    # Sync compatibility methods (for gradual migration)
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Thread-safe sync wrapper for get_user_profile"""
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to run in a separate thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.get_user_profile(user_id))
                    return future.result()
            else:
                # Loop exists but not running, we can use it
                return loop.run_until_complete(self.get_user_profile(user_id))
        except RuntimeError:
            # No event loop in current thread, create a new one
            return asyncio.run(self.get_user_profile(user_id))
    
    def save_profile(self, profile: UserProfile):
        """Synchronous wrapper - should not be used, raises error"""
        raise RuntimeError("save_profile should not be called synchronously - use async save_user_profile instead")
    
    def get_all_user_profiles(self) -> Dict[str, UserProfile]:
        """Thread-safe sync wrapper for get_all_profiles"""
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to run in a separate thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.get_all_profiles())
                    return future.result()
            else:
                # Loop exists but not running, we can use it
                return loop.run_until_complete(self.get_all_profiles())
        except RuntimeError:
            # No event loop in current thread, create a new one
            return asyncio.run(self.get_all_profiles())
    
    def load_all_profiles(self) -> Dict[str, UserProfile]:
        """Alias for get_all_user_profiles to match expected interface"""
        return self.get_all_user_profiles()
