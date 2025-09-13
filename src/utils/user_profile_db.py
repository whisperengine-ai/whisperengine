"""
Database-backed user profile management
This replaces the JSON file approach with SQLite for better data integrity
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict
from src.utils.emotion_manager import UserProfile, EmotionProfile, RelationshipLevel, EmotionalState

logger = logging.getLogger(__name__)

class UserProfileDatabase:
    """Database-backed user profile storage"""
    
    def __init__(self, db_path: str = "user_profiles.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    relationship_level TEXT DEFAULT 'acquaintance',
                    current_emotion TEXT DEFAULT 'neutral',
                    interaction_count INTEGER DEFAULT 0,
                    first_interaction TIMESTAMP,
                    last_interaction TIMESTAMP,
                    escalation_count INTEGER DEFAULT 0,
                    trust_indicators TEXT -- JSON array
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emotion_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    detected_emotion TEXT,
                    confidence REAL,
                    triggers TEXT, -- JSON array
                    intensity REAL,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_last_interaction ON users(last_interaction)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_emotion_history_user_time ON emotion_history(user_id, timestamp)")
            
    def save_user_profile(self, profile: UserProfile):
        """Save or update a user profile"""
        with sqlite3.connect(self.db_path) as conn:
            # Insert or update user record
            conn.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, name, relationship_level, current_emotion, interaction_count, 
                 first_interaction, last_interaction, escalation_count, trust_indicators)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.user_id,
                profile.name,
                profile.relationship_level.value,
                profile.current_emotion.value,
                profile.interaction_count,
                profile.first_interaction.isoformat() if profile.first_interaction else None,
                profile.last_interaction.isoformat() if profile.last_interaction else None,
                profile.escalation_count,
                json.dumps(profile.trust_indicators or [])
            ))
            
            # Clear existing emotion history for this user
            conn.execute("DELETE FROM emotion_history WHERE user_id = ?", (profile.user_id,))
            
            # Insert emotion history
            for emotion in profile.emotion_history or []:
                conn.execute("""
                    INSERT INTO emotion_history 
                    (user_id, detected_emotion, confidence, triggers, intensity, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    profile.user_id,
                    emotion.detected_emotion.value,
                    emotion.confidence,
                    json.dumps(emotion.triggers),
                    emotion.intensity,
                    emotion.timestamp.isoformat()
                ))
    
    def load_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load a user profile from database"""
        with sqlite3.connect(self.db_path) as conn:
            # Get user data
            cursor = conn.execute("""
                SELECT user_id, name, relationship_level, current_emotion, interaction_count,
                       first_interaction, last_interaction, escalation_count, trust_indicators
                FROM users WHERE user_id = ?
            """, (user_id,))
            
            user_row = cursor.fetchone()
            if not user_row:
                return None
            
            # Get emotion history
            emotion_cursor = conn.execute("""
                SELECT detected_emotion, confidence, triggers, intensity, timestamp
                FROM emotion_history 
                WHERE user_id = ? 
                ORDER BY timestamp ASC
            """, (user_id,))
            
            emotion_history = []
            for emotion_row in emotion_cursor.fetchall():
                emotion_history.append(EmotionProfile(
                    detected_emotion=EmotionalState(emotion_row[0]),
                    confidence=emotion_row[1],
                    triggers=json.loads(emotion_row[2]),
                    intensity=emotion_row[3],
                    timestamp=datetime.fromisoformat(emotion_row[4])
                ))
            
            # Build UserProfile
            trust_indicators_data = user_row[8]
            try:
                trust_indicators = json.loads(trust_indicators_data) if trust_indicators_data else []
                # Ensure it's a list
                if not isinstance(trust_indicators, list):
                    trust_indicators = []
            except (json.JSONDecodeError, TypeError):
                trust_indicators = []
            
            return UserProfile(
                user_id=user_row[0],
                name=user_row[1],
                relationship_level=RelationshipLevel(user_row[2]),
                current_emotion=EmotionalState(user_row[3]),
                interaction_count=user_row[4],
                first_interaction=datetime.fromisoformat(user_row[5]),
                last_interaction=datetime.fromisoformat(user_row[6]) if user_row[6] else None,
                escalation_count=user_row[7],
                trust_indicators=trust_indicators,
                emotion_history=emotion_history
            )
    
    def load_all_profiles(self) -> Dict[str, UserProfile]:
        """Load all user profiles"""
        profiles = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT user_id FROM users")
            for (user_id,) in cursor.fetchall():
                profile = self.load_user_profile(user_id)
                if profile:
                    profiles[user_id] = profile
        return profiles
    
    def delete_user_profile(self, user_id: str):
        """Delete a user profile and all associated data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM emotion_history WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    
    def update_user_name(self, user_id: str, name: Optional[str]) -> bool:
        """Update the name for an existing user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return False  # User doesn't exist
            
            current_name = result[0]
            if current_name != name:
                conn.execute("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id))
                logger.info(f"Updated name for user {user_id}: '{current_name}' -> '{name}'")
                return True
            
            return False  # No change needed
    
    def get_user_stats(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM emotion_history")
            emotion_count = cursor.fetchone()[0]
            
            return {
                "total_users": user_count,
                "total_emotions": emotion_count
            }
    
    def delete_user_emotions(self, user_id: str, older_than_days: Optional[int] = None):
        """Delete emotion history for a user, optionally only older records"""
        with sqlite3.connect(self.db_path) as conn:
            if older_than_days:
                # Delete emotions older than specified days
                deleted = conn.execute("""
                    DELETE FROM emotion_history 
                    WHERE user_id = ? 
                    AND timestamp < date('now', '-{} days')
                """.format(older_than_days), (user_id,))
                logger.info(f"Deleted {deleted.rowcount} emotion records older than {older_than_days} days for user {user_id}")
            else:
                # Delete all emotions for user
                deleted = conn.execute("DELETE FROM emotion_history WHERE user_id = ?", (user_id,))
                logger.info(f"Deleted all {deleted.rowcount} emotion records for user {user_id}")
            
            return deleted.rowcount
    
    def delete_specific_emotion(self, emotion_id: int):
        """Delete a specific emotion record by ID"""
        with sqlite3.connect(self.db_path) as conn:
            deleted = conn.execute("DELETE FROM emotion_history WHERE id = ?", (emotion_id,))
            logger.info(f"Deleted emotion record {emotion_id}")
            return deleted.rowcount > 0
    
    def cleanup_old_emotions(self, days_to_keep: int = 30):
        """Clean up emotion records older than specified days across all users"""
        with sqlite3.connect(self.db_path) as conn:
            deleted = conn.execute("""
                DELETE FROM emotion_history 
                WHERE timestamp < date('now', '-{} days')
            """.format(days_to_keep))
            logger.info(f"Cleaned up {deleted.rowcount} emotion records older than {days_to_keep} days")
            return deleted.rowcount
    
    def reset_user_profile(self, user_id: str, keep_basic_info: bool = True):
        """Reset a user profile while optionally keeping basic info"""
        with sqlite3.connect(self.db_path) as conn:
            # Always delete emotion history
            emotion_deleted = conn.execute("DELETE FROM emotion_history WHERE user_id = ?", (user_id,))
            
            if keep_basic_info:
                # Reset counters and emotions but keep identity
                conn.execute("""
                    UPDATE users 
                    SET current_emotion = 'neutral',
                        interaction_count = 0,
                        escalation_count = 0,
                        trust_indicators = '[]',
                        last_interaction = NULL
                    WHERE user_id = ?
                """, (user_id,))
                logger.info(f"Reset user profile for {user_id} (kept basic info, deleted {emotion_deleted.rowcount} emotions)")
            else:
                # Delete everything
                user_deleted = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                logger.info(f"Completely deleted user {user_id} ({user_deleted.rowcount} user record, {emotion_deleted.rowcount} emotions)")
            
            return emotion_deleted.rowcount
    
    def archive_inactive_users(self, days_inactive: int = 90):
        """Archive users who haven't interacted in specified days"""
        with sqlite3.connect(self.db_path) as conn:
            # First, let's see who would be affected
            cursor = conn.execute("""
                SELECT user_id, last_interaction, interaction_count
                FROM users 
                WHERE last_interaction < date('now', '-{} days')
                OR last_interaction IS NULL
            """.format(days_inactive))
            
            inactive_users = cursor.fetchall()
            
            if not inactive_users:
                logger.info("No inactive users found to archive")
                return 0
            
            # Add archived column if it doesn't exist
            try:
                conn.execute("ALTER TABLE users ADD COLUMN archived INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Mark users as archived
            archived = conn.execute("""
                UPDATE users 
                SET archived = 1 
                WHERE last_interaction < date('now', '-{} days')
                OR last_interaction IS NULL
            """.format(days_inactive))
            
            logger.info(f"Archived {archived.rowcount} inactive users (inactive for {days_inactive}+ days)")
            return archived.rowcount
    
    def get_archivable_users(self, days_inactive: int = 90):
        """Get list of users that would be archived (for preview)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT user_id, last_interaction, interaction_count, relationship_level
                FROM users 
                WHERE (last_interaction < date('now', '-{} days') OR last_interaction IS NULL)
                AND (archived IS NULL OR archived = 0)
                ORDER BY last_interaction ASC
            """.format(days_inactive))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def migrate_from_json(self, json_file_path: str):
        """Migrate existing JSON data to database"""
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            migrated_count = 0
            for user_id, profile_data in data.items():
                try:
                    # Convert datetime strings back to datetime objects
                    if profile_data.get('first_interaction'):
                        profile_data['first_interaction'] = datetime.fromisoformat(profile_data['first_interaction'])
                    if profile_data.get('last_interaction'):
                        profile_data['last_interaction'] = datetime.fromisoformat(profile_data['last_interaction'])
                    
                    # Convert enum strings back to enums
                    profile_data['relationship_level'] = RelationshipLevel(profile_data['relationship_level'])
                    profile_data['current_emotion'] = EmotionalState(profile_data['current_emotion'])
                    
                    # Convert emotion history
                    emotion_history = []
                    for emotion_data in profile_data.get('emotion_history', []):
                        emotion_data['detected_emotion'] = EmotionalState(emotion_data['detected_emotion'])
                        emotion_data['timestamp'] = datetime.fromisoformat(emotion_data['timestamp'])
                        emotion_history.append(EmotionProfile(**emotion_data))
                    
                    profile_data['emotion_history'] = emotion_history
                    profile = UserProfile(**profile_data)
                    
                    self.save_user_profile(profile)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error migrating user {user_id}: {e}")
            
            logger.info(f"Successfully migrated {migrated_count} user profiles from JSON to database")
            return migrated_count
            
        except FileNotFoundError:
            logger.info("No JSON file found to migrate")
            return 0
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            raise
