"""
Character Memory System

Provides personal memory management for autonomous characters,
including self-memory storage and integration with conversation systems.
"""

from .self_memory import (
    CharacterSelfMemoryManager,
    PersonalMemory,
    MemoryType,
    EmotionalWeight,
    MemoryCluster
)

from .integration import (
    CharacterMemoryIntegrator,
    CharacterMemoryContextProvider
)

__all__ = [
    'CharacterSelfMemoryManager',
    'PersonalMemory', 
    'MemoryType',
    'EmotionalWeight',
    'MemoryCluster',
    'CharacterMemoryIntegrator',
    'CharacterMemoryContextProvider'
]