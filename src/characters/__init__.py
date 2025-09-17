"""
Characters package initialization

This package contains the autonomous character system implementation.
"""

from .models.character import Character, CharacterMetadata, CharacterIdentity
from .cdl.parser import CDLParser, load_character, save_character

__all__ = [
    'Character',
    'CharacterMetadata', 
    'CharacterIdentity',
    'CDLParser',
    'load_character',
    'save_character'
]