"""
Centralized stop word definitions for WhisperEngine.

This module provides a single source of truth for stop word handling across
all text preprocessing operations. Stop words are grammar words (pronouns,
articles, prepositions, conjunctions) that are rarely meaningful for semantic
analysis, entity extraction, or keyword matching.

Architecture Note: This follows the preprocessing pattern where structural
transformations (stop word removal, lowercasing) are applied BEFORE downstream
analysis, simplifying logic and improving performance.
"""

import re
from typing import List, Set

# Standard English stop words (grammar words that are never meaningful entities)
STOP_WORDS: Set[str] = {
    # Pronouns
    "i", "me", "my", "mine", "myself", "you", "your", "yours", "yourself",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves",
    
    # Articles
    "a", "an", "the",
    
    # Prepositions
    "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "about", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "over", "against", "within",
    
    # Conjunctions
    "and", "or", "but", "if", "then", "else", "nor", "yet", "so",
    
    # Auxiliaries & Verbs
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing", "done",
    "will", "would", "could", "should", "may", "might", "must", "can",
    
    # Demonstratives
    "this", "that", "these", "those",
    
    # Question words
    "what", "when", "where", "how", "why", "which", "who", "whom", "whose",
    
    # Common fillers & adverbs
    "very", "really", "just", "too", "now", "there", "here",
    "such", "even", "also", "still", "more", "most", "less", "much", "many",
    "some", "any", "all", "both", "each", "every", "either", "neither",
    
    # Other function words
    "as", "than", "because", "while", "however", "therefore", "thus",
    "not", "no", "yes", "maybe", "perhaps"
}


def clean_text(text: str, remove_stop_words: bool = True) -> str:
    """
    Centralized text cleaning function with optional stop word removal.
    
    This function performs standard text preprocessing operations:
    1. Lowercase conversion
    2. Punctuation removal (preserving apostrophes)
    3. Whitespace normalization
    4. Optional stop word removal
    
    Args:
        text: Raw text to clean
        remove_stop_words: Whether to remove stop words (default: True)
        
    Returns:
        Cleaned text string
        
    Example:
        >>> clean_text("The cat's name is Max!")
        "cat's name max"
        
        >>> clean_text("What did I do yesterday?", remove_stop_words=False)
        "what did i do yesterday"
    """
    if not text:
        return ""
    
    # Lowercase and strip
    cleaned = text.lower().strip()
    
    # Remove punctuation except apostrophes (for contractions like "don't")
    cleaned = re.sub(r"[^\w\s\']", " ", cleaned)
    
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)
    
    if remove_stop_words:
        words = cleaned.split()
        words = [w for w in words if w not in STOP_WORDS]
        cleaned = " ".join(words)
    
    return cleaned.strip()


def extract_content_words(text: str, min_length: int = 3) -> List[str]:
    """
    Extract content words (non-stop words) from text.
    
    This is the primary function for entity extraction and keyword analysis.
    It removes stop words first (preprocessing), then applies length filtering.
    
    Args:
        text: Input text
        min_length: Minimum word length to keep (default: 3)
        
    Returns:
        List of content words (stop words removed, length filtered)
        
    Example:
        >>> extract_content_words("I have a cat named Max")
        ["have", "cat", "named", "max"]
        
        >>> extract_content_words("The quick brown fox", min_length=5)
        ["quick", "brown"]
    """
    cleaned = clean_text(text, remove_stop_words=True)
    words = cleaned.split()
    return [w for w in words if len(w) >= min_length]


def optimize_query(query: str,
                  remove_stop_words: bool = True,
                  min_word_length: int = 3,
                  max_words: int | None = None) -> str:
    """
    Optimize query text for semantic search and vector operations.
    
    This function is designed for search queries where we want to:
    1. Remove noise (stop words)
    2. Focus on meaningful terms (length filtering)
    3. Limit query size for performance (optional)
    
    Args:
        query: Raw query text
        remove_stop_words: Whether to remove stop words (default: True)
        min_word_length: Minimum word length to keep (default: 3)
        max_words: Optional limit on number of words returned
        
    Returns:
        Optimized query string
        
    Example:
        >>> optimize_query("What did the cat do yesterday?")
        "cat yesterday"
        
        >>> optimize_query("Tell me about machine learning", max_words=2)
        "tell machine"
    """
    cleaned = clean_text(query, remove_stop_words=remove_stop_words)
    words = cleaned.split()
    words = [w for w in words if len(w) >= min_word_length]
    
    if max_words and len(words) > max_words:
        words = words[:max_words]
    
    return " ".join(words)


def get_stop_words() -> Set[str]:
    """
    Get the centralized stop words set.
    
    This function exists for backward compatibility with code that
    expects a method call. New code should use the STOP_WORDS constant directly.
    
    Returns:
        Set of stop words
    """
    return STOP_WORDS


def remove_stop_words_from_list(words: List[str]) -> List[str]:
    """
    Remove stop words from a list of words.
    
    This is useful when you already have tokenized text and want to
    filter stop words without re-tokenizing.
    
    Args:
        words: List of words (should be lowercase)
        
    Returns:
        List with stop words removed
        
    Example:
        >>> remove_stop_words_from_list(["the", "cat", "is", "here"])
        ["cat", "here"]
    """
    return [w for w in words if w not in STOP_WORDS]


def is_stop_word(word: str) -> bool:
    """
    Check if a single word is a stop word.
    
    Args:
        word: Word to check (will be lowercased)
        
    Returns:
        True if word is a stop word, False otherwise
        
    Example:
        >>> is_stop_word("the")
        True
        >>> is_stop_word("Max")
        False
    """
    return word.lower() in STOP_WORDS
