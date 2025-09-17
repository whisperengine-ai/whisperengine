"""
Characters package initialization

This package contains the autonomous character system implementation including
memory management, CDL parsing, and conversation integration.
"""

from .models.character import Character, CharacterMetadata, CharacterIdentity
from .cdl.parser import CDLParser, load_character, save_character
from .memory import CharacterSelfMemoryManager, CharacterMemoryIntegrator
from .bridge import CharacterSystemBridge, ConversationCharacterEnhancer, get_character_bridge, create_conversation_enhancer

__all__ = [
    'Character',
    'CharacterMetadata', 
    'CharacterIdentity',
    'CDLParser',
    'load_character',
    'save_character',
    'CharacterSelfMemoryManager',
    'CharacterMemoryIntegrator', 
    'CharacterSystemBridge',
    'ConversationCharacterEnhancer',
    'get_character_bridge',
    'create_conversation_enhancer'
]