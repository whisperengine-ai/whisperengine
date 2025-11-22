import os
from typing import Optional, Dict
from pydantic import BaseModel
from loguru import logger

class Character(BaseModel):
    name: str
    system_prompt: str
    # We can add more fields here later if needed, but for now, the prompt is key

class CharacterManager:
    def __init__(self, characters_dir: str = "characters"):
        self.characters_dir = characters_dir
        self.characters: Dict[str, Character] = {}

    def load_character(self, name: str) -> Optional[Character]:
        """
        Loads a character from the characters directory.
        Expected structure: characters/{name}/character.md
        """
        char_path = os.path.join(self.characters_dir, name, "character.md")
        
        if not os.path.exists(char_path):
            logger.warning(f"Character file not found: {char_path}")
            return None

        try:
            with open(char_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Simple parsing: The whole file is the system prompt for now.
            # In the future, we can parse frontmatter (YAML) for metadata.
            character = Character(
                name=name,
                system_prompt=content
            )
            self.characters[name] = character
            logger.info(f"Loaded character: {name}")
            return character
        except Exception as e:
            logger.error(f"Failed to load character {name}: {e}")
            return None

    def get_character(self, name: str) -> Optional[Character]:
        if name not in self.characters:
            return self.load_character(name)
        return self.characters[name]

# Global character manager
character_manager = CharacterManager()
