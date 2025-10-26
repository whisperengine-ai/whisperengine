"""
Shared spaCy NLP Manager - Singleton Pattern

Provides a single spaCy model instance that can be reused across the application
to avoid loading the model multiple times (which is expensive and wasteful).

Usage:
    from src.nlp.spacy_manager import get_spacy_nlp
    
    nlp = get_spacy_nlp()
    if nlp:
        doc = nlp("Your text here")
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Global singleton instance
_spacy_nlp: Optional[Any] = None
_spacy_has_vectors = False
_spacy_initialized = False


def get_spacy_nlp() -> Optional[Any]:
    """
    Get shared spaCy NLP instance (singleton pattern).
    
    Returns the same spaCy model instance across all calls, avoiding
    expensive repeated model loading.
    
    Returns:
        spaCy Language object, or None if spaCy unavailable
    """
    global _spacy_nlp, _spacy_has_vectors, _spacy_initialized
    
    # Return cached instance if already initialized
    if _spacy_initialized:
        return _spacy_nlp
    
    # Initialize on first call
    _spacy_initialized = True
    
    try:
        import spacy
        
        # Try loading medium model (has 300D word vectors for semantic matching)
        try:
            _spacy_nlp = spacy.load("en_core_web_md")
            _spacy_has_vectors = _spacy_nlp.vocab.vectors.size > 0
            
            if _spacy_has_vectors:
                logger.info(
                    "✅ Shared spaCy NLP initialized (en_core_web_md, 300D, %d vectors)",
                    _spacy_nlp.vocab.vectors.size
                )
            else:
                logger.warning("⚠️ en_core_web_md loaded but no word vectors found")
                
        except OSError:
            # Fallback to small model (no word vectors)
            try:
                _spacy_nlp = spacy.load("en_core_web_sm")
                _spacy_has_vectors = False
                logger.warning(
                    "⚠️ Shared spaCy NLP initialized (en_core_web_sm - no word vectors). "
                    "Install en_core_web_md for semantic matching: "
                    "python -m spacy download en_core_web_md"
                )
            except OSError:
                _spacy_nlp = None
                logger.warning("⚠️ No spaCy models found - NLP features disabled")
                
    except ImportError:
        _spacy_nlp = None
        logger.warning(
            "⚠️ spaCy not installed - NLP features disabled. "
            "Install: pip install spacy && python -m spacy download en_core_web_md"
        )
    
    return _spacy_nlp


def has_word_vectors() -> bool:
    """
    Check if loaded spaCy model has word vectors.
    
    Returns:
        True if word vectors available, False otherwise
    """
    global _spacy_has_vectors, _spacy_initialized
    
    # Ensure initialized
    if not _spacy_initialized:
        get_spacy_nlp()
    
    return _spacy_has_vectors


def reset_spacy_singleton():
    """
    Reset singleton state (mainly for testing).
    
    Forces reinitialization on next get_spacy_nlp() call.
    """
    global _spacy_nlp, _spacy_has_vectors, _spacy_initialized
    
    _spacy_nlp = None
    _spacy_has_vectors = False
    _spacy_initialized = False
    
    logger.info("🔄 spaCy singleton reset")
