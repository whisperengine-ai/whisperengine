"""
Enhanced EmotionManager that can work with either JSON files or database storage
"""

import logging
from typing import Dict, Optional
from src.utils.emotion_manager import EmotionManager as BaseEmotionManager, UserProfile
from user_profile_db import UserProfileDatabase

logger = logging.getLogger(__name__)


class DatabaseEmotionManager(BaseEmotionManager):
    """EmotionManager with database backend support"""

    def __init__(
        self,
        llm_client=None,
        enable_llm_analysis: bool = True,
        persist_file: str = "user_profiles.json",
        use_database: bool = True,
    ):

        self.use_database = use_database
        self.persist_file = persist_file

        if use_database:
            # Initialize database backend
            self.db = UserProfileDatabase()
            # Don't call parent init to avoid JSON file setup
            self.llm_client = llm_client
            self.enable_llm_analysis = enable_llm_analysis
            self.user_profiles: Dict[str, UserProfile] = {}
            self.load_profiles()
        else:
            # Use traditional JSON file approach
            super().__init__(llm_client, enable_llm_analysis, persist_file)

    def load_profiles(self):
        """Load user profiles from database or JSON file"""
        if self.use_database:
            try:
                self.user_profiles = self.db.load_all_profiles()
                logger.info(f"Loaded {len(self.user_profiles)} user profiles from database")
            except Exception as e:
                logger.error(f"Error loading profiles from database: {e}")
                self.user_profiles = {}
        else:
            super().load_profiles()

    def save_profiles(self):
        """Save user profiles to database or JSON file"""
        if self.use_database:
            try:
                saved_count = 0
                for profile in self.user_profiles.values():
                    self.db.save_user_profile(profile)
                    saved_count += 1
                logger.debug(f"Saved {saved_count} profiles to database")
            except Exception as e:
                logger.error(f"Error saving profiles to database: {e}")
        else:
            super().save_profiles()

    def get_database_stats(self) -> Optional[Dict]:
        """Get database statistics (only available in database mode)"""
        if self.use_database:
            return self.db.get_user_stats()
        return None

    def delete_user_profile(self, user_id: str):
        """Delete a user profile completely"""
        if user_id in self.user_profiles:
            del self.user_profiles[user_id]

        if self.use_database:
            self.db.delete_user_profile(user_id)
            logger.info(f"Deleted user profile from database: {user_id}")
        else:
            # For JSON mode, just save without the profile
            self.save_profiles()
            logger.info(f"Deleted user profile from JSON: {user_id}")

    def migrate_to_database(self, json_file_path: Optional[str] = None):
        """Migrate from JSON file to database (if not already using database)"""
        if self.use_database:
            logger.info("Already using database backend")
            return False

        try:
            # Initialize database
            self.db = UserProfileDatabase()

            # Migrate existing data
            json_path = json_file_path or self.persist_file
            migrated_count = self.db.migrate_from_json(json_path)

            # Switch to database mode
            self.use_database = True
            self.load_profiles()  # Reload from database

            logger.info(f"Successfully migrated {migrated_count} profiles to database")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
