"""
CDL Integration with AI Pipeline Prompt System
"""

import logging
from typing import Dict, Optional
from pathlib import Path

from src.characters.models.character import Character
from src.characters.cdl.parser import load_character

logger = logging.getLogger(__name__)


class CDLAIPromptIntegration:
    """Integrates CDL character definitions with AI pipeline results."""

    def __init__(self, vector_memory_manager=None):
        self.memory_manager = vector_memory_manager
        self.characters_cache = {}

    async def create_character_aware_prompt(
        self,
        character_file: str,
        user_id: str,
        message_content: str,
        pipeline_result=None
    ) -> str:
        """Create a character-aware prompt."""
        try:
            character = await self.load_character(character_file)
            logger.info(f"Loaded CDL character: {character.identity.name}")

            prompt = f"""You are {character.identity.name}, {character.identity.description}

CHARACTER DETAILS:
- Age: {character.identity.age}
- Occupation: {character.identity.occupation}
- Location: {character.identity.location}

IMPORTANT: You must respond as {character.identity.name}, not as Dream. Stay in character.

User Message: "{message_content}"

Respond as {character.identity.name}:"""

            return prompt

        except Exception as e:
            logger.error(f"CDL integration failed: {e}")
            raise

    async def load_character(self, character_file: str) -> Character:
        """Load a character from CDL file."""
        try:
            if character_file in self.characters_cache:
                return self.characters_cache[character_file]

            character_path = Path("characters") / character_file
            if not character_path.exists():
                character_path = Path(character_file)

            character = load_character(character_path)
            self.characters_cache[character_file] = character
            return character

        except Exception as e:
            logger.error(f"Failed to load character {character_file}: {e}")
            raise


async def load_character_definitions(characters_dir: str = "characters") -> Dict[str, Character]:
    """Load all character definitions from directory."""
    characters = {}
    characters_path = Path(characters_dir)

    if not characters_path.exists():
        logger.warning(f"Characters directory not found: {characters_dir}")
        return characters

    for file_path in characters_path.rglob("*.json"):
        try:
            character_name = file_path.stem
            character = load_character(file_path)
            characters[character_name] = character
            logger.info(f"Loaded character: {character_name}")
        except Exception as e:
            logger.error(f"Failed to load character from {file_path}: {e}")

    return characters