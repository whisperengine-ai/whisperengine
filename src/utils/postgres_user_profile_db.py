"""
PostgreSQL-backed user profile management
This replaces the SQLite approach with PostgreSQL for better concurrent access and scalability
"""

import asyncio
import asyncpg
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict
from contextlib import asynccontextmanager

from src.utils.emotion_manager import UserProfile, EmotionProfile, RelationshipLevel, EmotionalState

logger = logging.getLogger(__name__)

class PostgreSQLUserProfileDatabase:
    """PostgreSQL-backed user profile storage with connection pooling"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "discord_bot",
                 user: str = "bot_user",
                 password: str = "bot_password_change_me",
                 min_size: int = 5,
                 max_size: int = 20):
        """
        Initialize PostgreSQL connection configuration
        
        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Database password
            min_size: Minimum connections in pool
            max_size: Maximum connections in pool
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        self._lock = asyncio.Lock()
        
        logger.info(f"PostgreSQL UserProfileDatabase configured for {host}:{port}/{database}")
    
    async def initialize(self):
        """Initialize the database connection pool"""
        async with self._lock:
            if self._initialized:
                return
                
            try:
                self.pool = await asyncpg.create_pool(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    command_timeout=30
                )
                
                # Test connection
                async with self.pool.acquire() as conn:
                    await conn.execute("SELECT 1")
                
                self._initialized = True
                logger.info("PostgreSQL connection pool initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
                raise
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve a user profile by user_id"""
        try:
            async with self.get_connection() as conn:
                # Get user data
                user_row = await conn.fetchrow(
                    """
                    SELECT user_id, name, relationship_level, current_emotion, 
                           interaction_count, first_interaction, last_interaction,
                           escalation_count, trust_indicators
                    FROM users WHERE user_id = $1
                    """, 
                    user_id
                )
                
                if not user_row:
                    return None
                
                # Get emotion history
                emotion_rows = await conn.fetch(
                    """
                    SELECT detected_emotion, confidence, triggers, intensity, timestamp
                    FROM emotion_history 
                    WHERE user_id = $1 
                    ORDER BY timestamp DESC
                    LIMIT 50
                    """,
                    user_id
                )
                
                # Build emotion history list
                emotion_history = []
                for row in emotion_rows:
                    emotion_profile = EmotionProfile(
                        detected_emotion=EmotionalState(row['detected_emotion']),
                        confidence=row['confidence'],
                        triggers=row['triggers'] if row['triggers'] else [],
                        intensity=row['intensity'],
                        timestamp=row['timestamp']
                    )
                    emotion_history.append(emotion_profile)
                
                # Handle trust_indicators type conversion
                trust_indicators = user_row['trust_indicators'] if user_row['trust_indicators'] else []
                if isinstance(trust_indicators, str):
                    try:
                        import json
                        trust_indicators = json.loads(trust_indicators)
                    except (json.JSONDecodeError, TypeError):
                        trust_indicators = []
                elif not isinstance(trust_indicators, list):
                    trust_indicators = []

                # Build user profile  
                profile = UserProfile(
                    user_id=user_row['user_id'],
                    name=user_row['name'],
                    relationship_level=RelationshipLevel(user_row['relationship_level']),
                    current_emotion=EmotionalState(user_row['current_emotion']),
                    interaction_count=user_row['interaction_count'],
                    first_interaction=user_row['first_interaction'],
                    last_interaction=user_row['last_interaction'],
                    emotion_history=emotion_history,
                    escalation_count=user_row['escalation_count'],
                    trust_indicators=trust_indicators
                )
                
                return profile
                
        except Exception as e:
            logger.error(f"Error retrieving user profile for {user_id}: {e}")
            return None
    
    async def save_user_profile(self, profile: UserProfile) -> bool:
        """Save or update a user profile"""
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    # Upsert user data
                    await conn.execute(
                        """
                        INSERT INTO users (
                            user_id, name, relationship_level, current_emotion,
                            interaction_count, first_interaction, last_interaction,
                            escalation_count, trust_indicators
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (user_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            relationship_level = EXCLUDED.relationship_level,
                            current_emotion = EXCLUDED.current_emotion,
                            interaction_count = EXCLUDED.interaction_count,
                            last_interaction = EXCLUDED.last_interaction,
                            escalation_count = EXCLUDED.escalation_count,
                            trust_indicators = EXCLUDED.trust_indicators,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        profile.user_id,
                        profile.name,
                        profile.relationship_level.value,
                        profile.current_emotion.value,
                        profile.interaction_count,
                        profile.first_interaction,
                        profile.last_interaction,
                        profile.escalation_count,
                        json.dumps(profile.trust_indicators)
                    )
                    
                    # Save recent emotion history (limit to prevent bloat)
                    if profile.emotion_history:
                        # Clear old emotion history for this user (keep only recent)
                        await conn.execute(
                            "DELETE FROM emotion_history WHERE user_id = $1",
                            profile.user_id
                        )
                        
                        # Insert recent emotion history
                        recent_history = profile.emotion_history[:50]  # Keep last 50
                        for emotion_profile in recent_history:
                            await conn.execute(
                                """
                                INSERT INTO emotion_history 
                                (user_id, detected_emotion, confidence, triggers, intensity, timestamp)
                                VALUES ($1, $2, $3, $4, $5, $6)
                                """,
                                profile.user_id,
                                emotion_profile.detected_emotion.value,
                                emotion_profile.confidence,
                                json.dumps(emotion_profile.triggers),
                                emotion_profile.intensity,
                                emotion_profile.timestamp
                            )
                
                logger.debug(f"Saved user profile for {profile.user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving user profile for {profile.user_id}: {e}")
            return False
    
    async def get_all_users(self) -> List[str]:
        """Get list of all user IDs"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch("SELECT user_id FROM users ORDER BY last_interaction DESC")
                return [row['user_id'] for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving all users: {e}")
            return []
    
    async def delete_user_profile(self, user_id: str) -> bool:
        """Delete a user profile and all associated data"""
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    # Delete emotion history first (foreign key constraint)
                    await conn.execute("DELETE FROM emotion_history WHERE user_id = $1", user_id)
                    
                    # Delete interactions
                    await conn.execute("DELETE FROM interactions WHERE user_id = $1", user_id)
                    
                    # Delete user
                    result = await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)
                    
                    deleted = result.split()[-1] == '1'  # Check if one row was deleted
                    if deleted:
                        logger.info(f"Deleted user profile for {user_id}")
                    else:
                        logger.warning(f"No user profile found to delete for {user_id}")
                    
                    return deleted
                    
        except Exception as e:
            logger.error(f"Error deleting user profile for {user_id}: {e}")
            return False
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            async with self.get_connection() as conn:
                stats = {}
                
                # User counts
                stats['total_users'] = await conn.fetchval("SELECT COUNT(*) FROM users")
                stats['active_users_7d'] = await conn.fetchval(
                    "SELECT COUNT(*) FROM users WHERE last_interaction > NOW() - INTERVAL '7 days'"
                )
                stats['active_users_30d'] = await conn.fetchval(
                    "SELECT COUNT(*) FROM users WHERE last_interaction > NOW() - INTERVAL '30 days'"
                )
                
                # Interaction stats
                stats['total_emotion_records'] = await conn.fetchval("SELECT COUNT(*) FROM emotion_history")
                stats['total_interactions'] = await conn.fetchval("SELECT COUNT(*) FROM interactions")
                
                # Relationship distribution
                relationship_dist = await conn.fetch(
                    "SELECT relationship_level, COUNT(*) as count FROM users GROUP BY relationship_level"
                )
                stats['relationship_distribution'] = {row['relationship_level']: row['count'] for row in relationship_dist}
                
                return stats
                
        except Exception as e:
            logger.error(f"Error retrieving database stats: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check if the database connection is healthy"""
        try:
            async with self.get_connection() as conn:
                await conn.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def load_all_profiles(self) -> Dict[str, UserProfile]:
        """Load all user profiles - compatibility method for EmotionManager"""
        try:
            user_ids = await self.get_all_users()
            profiles = {}
            
            for user_id in user_ids:
                profile = await self.get_user_profile(user_id)
                if profile:
                    profiles[user_id] = profile
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error loading all profiles: {e}")
            return {}
    
    async def save_all_profiles(self, profiles: Dict[str, UserProfile]) -> bool:
        """Save all user profiles - compatibility method for EmotionManager"""
        try:
            success_count = 0
            for user_id, profile in profiles.items():
                if await self.save_user_profile(profile):
                    success_count += 1
            
            logger.info(f"Saved {success_count}/{len(profiles)} user profiles")
            return success_count == len(profiles)
            
        except Exception as e:
            logger.error(f"Error saving all profiles: {e}")
            return False


def create_user_profile_db_from_env() -> PostgreSQLUserProfileDatabase:
    """Create UserProfileDatabase from environment variables"""
    return PostgreSQLUserProfileDatabase(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
        database=os.getenv('POSTGRES_DB', 'discord_bot'),
        user=os.getenv('POSTGRES_USER', 'bot_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'bot_password_change_me'),
        min_size=int(os.getenv('POSTGRES_MIN_CONNECTIONS', '5')),
        max_size=int(os.getenv('POSTGRES_MAX_CONNECTIONS', '20'))
    )
