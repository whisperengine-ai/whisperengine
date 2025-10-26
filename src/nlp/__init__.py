"""
NLP utilities package for WhisperEngine.

Provides shared NLP resources and utilities including:
- Shared spaCy singleton manager
- Future: Custom NLP pipeline components
"""

from src.nlp.spacy_manager import get_spacy_nlp, has_word_vectors, reset_spacy_singleton

__all__ = [
    'get_spacy_nlp',
    'has_word_vectors',
    'reset_spacy_singleton',
]
