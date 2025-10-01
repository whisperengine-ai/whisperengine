"""
Optional Async File I/O Enhancements
====================================

This module provides async versions of file I/O operations for the emotion manager
and memory manager. These are optional optimizations for better concurrent performance.

Install aiofiles first: pip install aiofiles
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)


class AsyncFileManager:
    """Async file operations for profile management"""

    @staticmethod
    async def load_json_file(file_path: str) -> dict[str, Any]:
        """Async JSON file loading"""
        try:
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            logger.warning(f"File {file_path} not found, returning empty dict")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return {}

    @staticmethod
    async def save_json_file(file_path: str, data: dict[str, Any], indent: int = 2) -> bool:
        """Async JSON file saving"""
        try:
            json_content = json.dumps(data, indent=indent, ensure_ascii=False)
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(json_content)
            return True
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
            return False


class AsyncEmotionProfileManager:
    """
    Async wrapper for emotion profile file operations

    Usage:
        # Replace sync calls with async calls
        profiles = await async_emotion_manager.load_profiles()
        success = await async_emotion_manager.save_profiles(profiles_data)
    """

    def __init__(self, persist_file: str = "./user_profiles.json"):
        self.persist_file = persist_file
        self.file_manager = AsyncFileManager()
        self._save_lock = asyncio.Lock()  # Prevent concurrent saves

    async def load_profiles(self) -> dict[str, Any]:
        """Async version of profile loading"""
        logger.debug(f"Loading profiles from {self.persist_file}")

        data = await self.file_manager.load_json_file(self.persist_file)

        # Process the loaded data (convert strings back to proper types)
        processed_profiles = {}
        for user_id, profile_data in data.items():
            try:
                # Convert datetime strings back to datetime objects
                if profile_data.get("first_interaction"):
                    profile_data["first_interaction"] = datetime.fromisoformat(
                        profile_data["first_interaction"]
                    )
                if profile_data.get("last_interaction"):
                    profile_data["last_interaction"] = datetime.fromisoformat(
                        profile_data["last_interaction"]
                    )

                # Convert emotion history timestamps
                for emotion_data in profile_data.get("emotion_history", []):
                    if emotion_data.get("timestamp"):
                        emotion_data["timestamp"] = datetime.fromisoformat(
                            emotion_data["timestamp"]
                        )

                processed_profiles[user_id] = profile_data
            except Exception as e:
                logger.warning(f"Error processing profile for user {user_id}: {e}")
                continue

        logger.debug(f"Loaded {len(processed_profiles)} user profiles")
        return processed_profiles

    async def save_profiles(self, profiles_data: dict[str, Any]) -> bool:
        """Async version of profile saving with write lock"""
        async with self._save_lock:  # Prevent concurrent saves
            logger.debug(f"Saving {len(profiles_data)} profiles to {self.persist_file}")

            # Prepare data for JSON serialization
            serializable_data = {}
            for user_id, profile_data in profiles_data.items():
                try:
                    profile_dict = dict(profile_data)

                    # Convert datetime objects to strings
                    if profile_dict.get("first_interaction"):
                        profile_dict["first_interaction"] = profile_dict[
                            "first_interaction"
                        ].isoformat()
                    if profile_dict.get("last_interaction"):
                        profile_dict["last_interaction"] = profile_dict[
                            "last_interaction"
                        ].isoformat()

                    # Convert emotion history timestamps
                    emotion_history = []
                    for emotion in profile_dict.get("emotion_history", []):
                        emotion_copy = dict(emotion)
                        if emotion_copy.get("timestamp"):
                            emotion_copy["timestamp"] = emotion_copy["timestamp"].isoformat()
                        emotion_history.append(emotion_copy)

                    profile_dict["emotion_history"] = emotion_history
                    serializable_data[user_id] = profile_dict

                except Exception as e:
                    logger.warning(f"Error serializing profile for user {user_id}: {e}")
                    continue

            success = await self.file_manager.save_json_file(self.persist_file, serializable_data)
            if success:
                logger.debug(f"Successfully saved profiles to {self.persist_file}")
            else:
                logger.error(f"Failed to save profiles to {self.persist_file}")

            return success


class AsyncSystemPromptLoader:
    """Async system prompt loading (optional optimization)"""

    @staticmethod
    async def load_system_prompt() -> str:
        """Async version of system prompt loading using CDL character system"""
        import os

        try:
            # Use CDL character system instead of .md files
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            
            cdl_integration = CDLAIPromptIntegration()
            default_character = os.getenv('CDL_DEFAULT_CHARACTER', 'characters/default_assistant.json')
            
            # Create a basic character-aware prompt
            prompt = await cdl_integration.create_unified_character_prompt(
                character_file=character_file,
                user_id=user_id,
                message_content=content
            )
            return prompt
            
        except (ImportError, FileNotFoundError, AttributeError) as e:
            logger.warning("CDL character loading failed: %s, using fallback", e)
            return """You are a helpful and friendly Discord bot assistant. You have the following personality traits:

- You are knowledgeable, helpful, and patient
- You respond in a conversational and friendly tone
- You can help with various tasks including answering questions, providing explanations, and general assistance
- You maintain context from previous conversations
- You can process and analyze images when provided"""


# Example usage in your emotion manager:
"""
# In emotion_manager.py, you could replace sync file operations:

class EmotionManager:
    def __init__(self, persist_file: str = "./user_profiles.json", llm_client=None, memory_manager=None):
        # ... existing init code ...
        self.async_file_manager = AsyncEmotionProfileManager(persist_file)

    async def async_load_profiles(self):
        \"\"\"Async version of load_profiles\"\"\"
        profiles_data = await self.async_file_manager.load_profiles()
        # Process into UserProfile objects...
        return profiles_data

    async def async_save_profiles(self):
        \"\"\"Async version of save_profiles\"\"\"
        # Prepare profiles data...
        success = await self.async_file_manager.save_profiles(profiles_data)
        return success
"""
