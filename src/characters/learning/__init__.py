"""
Character Learning Module

Advanced character learning systems for WhisperEngine that leverage existing infrastructure
to provide episodic intelligence, character insights, and memory-enhanced responses.

Components:
- CharacterVectorEpisodicIntelligence: Extract memorable moments from RoBERTa-scored conversations
- Character insights extraction from emotional patterns
- Episodic memory integration for response enhancement
"""

from .character_vector_episodic_intelligence import (
    CharacterVectorEpisodicIntelligence,
    EpisodicMemory,
    CharacterInsight,
    create_character_vector_episodic_intelligence
)

__all__ = [
    'CharacterVectorEpisodicIntelligence',
    'EpisodicMemory', 
    'CharacterInsight',
    'create_character_vector_episodic_intelligence'
]