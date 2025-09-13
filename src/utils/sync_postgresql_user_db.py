"""
Synchronous PostgreSQL User Profile Database

This module provides a synchronous PostgreSQL-based user profile and emotion management
that avoids asyncio event loop conflicts by using psycopg2 instead of asyncpg.
"""

import psycopg2
import psycopg2.pool
import psycopg2.extras
import json
import logging
import os
import threading
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

class SyncPostgreSQLUserDB:
    """Synchronous PostgreSQL-based user profile database using psycopg2"""
    
    def __init__(self):
        self.pool = None
        self._lock = threading.RLock()  # Use threading lock for sync operations
        
        self._connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'whisper_engine'),
            'user': os.getenv('POSTGRES_USER', 'bot_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'bot_password_change_me'),
        }
        
    def initialize(self):
        """Initialize the database connection pool and create tables"""
        if self.pool is not None:
            return  # Already initialized
            
        try:
            # Create connection pool
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                **self._connection_params
            )
            self._create_tables()
            logger.info("Synchronous PostgreSQL database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize synchronous PostgreSQL database: {e}")
            raise
    
    def _create_tables(self):
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
        
        connection = None
        try:
            connection = self.pool.getconn()
            with connection.cursor() as cursor:
                cursor.execute(create_table_sql)
                connection.commit()
        finally:
            if connection:
                self.pool.putconn(connection)
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get a user profile by user_id"""
        if not self.pool:
            self.initialize()
            
        connection = None
        try:
            with self._lock:
                connection = self.pool.getconn()
                with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
                    row = cursor.fetchone()
                    
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
        finally:
            if connection:
                self.pool.putconn(connection)
    
    def save_user_profile(self, profile: UserProfile):
        """Save or update a user profile"""
        if not self.pool:
            self.initialize()
            
        connection = None
        try:
            with self._lock:
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
                
                connection = self.pool.getconn()
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO user_profiles (
                            user_id, name, relationship_level, current_emotion,
                            interaction_count, first_interaction, last_interaction,
                            emotion_history, escalation_count, trust_indicators
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    """, (
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
                    ))
                    connection.commit()
                    
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Error saving user profile for {profile.user_id}: {e}")
            raise
        finally:
            if connection:
                self.pool.putconn(connection)
    
    def get_all_profiles(self) -> Dict[str, UserProfile]:
        """Get all user profiles"""
        if not self.pool:
            self.initialize()
            
        connection = None
        try:
            with self._lock:
                connection = self.pool.getconn()
                with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("SELECT * FROM user_profiles")
                    rows = cursor.fetchall()
                    
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
        finally:
            if connection:
                self.pool.putconn(connection)
    
    def delete_user_profile(self, user_id: str):
        """Delete a user profile"""
        if not self.pool:
            self.initialize()
            
        connection = None
        try:
            with self._lock:
                connection = self.pool.getconn()
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
                    connection.commit()
                    
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Error deleting user profile for {user_id}: {e}")
            raise
        finally:
            if connection:
                self.pool.putconn(connection)
    
    def close(self):
        """Close the database connection pool"""
        if self.pool:
            self.pool.closeall()
            self.pool = None
            logger.info("Synchronous PostgreSQL database connection closed")
    
    # Compatibility methods
    def load_all_profiles(self) -> Dict[str, UserProfile]:
        """Alias for get_all_profiles to match expected interface"""
        return self.get_all_profiles()