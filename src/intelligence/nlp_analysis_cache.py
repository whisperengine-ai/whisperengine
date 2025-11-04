"""
NLP Analysis Cache - Unified spaCy parsing and pre-computed NLP features.

This module provides a centralized cache for spaCy parsing results to eliminate
redundant parsing across multiple analyzers (stance, emotion, intensity, trajectory).

Design Philosophy:
- Parse once: Single spaCy.Doc creation per message
- Pre-compute common features: lemmas, POS tags, entities, emotion keywords
- Backward compatible: Optional parameter pattern, graceful fallback
- Zero breaking changes: Existing code works without cache

Performance Impact:
- Eliminates 3x redundant spaCy parsing (stance + emotion + intensity)
- Reduces keyword matching from 600+ substring checks to O(1) lemma lookups
- Target: 28% faster message processing

Author: WhisperEngine Team
Created: November 2025
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set, TYPE_CHECKING
import spacy
from spacy.tokens import Doc

if TYPE_CHECKING:
    from spacy.tokens import Token


@dataclass
class NLPAnalysisCache:
    """
    Unified cache for spaCy parsing results and pre-computed NLP features.
    
    This class stores the results of a single spaCy parsing operation and
    provides convenient access to commonly needed NLP features across
    multiple analyzer modules.
    
    Usage:
        # Parse once
        nlp = get_spacy_nlp()
        doc = nlp(message)
        cache = NLPAnalysisCache.from_doc(doc, message)
        
        # Use everywhere
        stance_result = await stance_analyzer.analyze_user_stance(message, nlp_cache=cache)
        emotion_result = await emotion_analyzer.analyze_emotion(message, nlp_cache=cache)
    
    Attributes:
        original_text: Raw input message text
        doc: spaCy Doc object (full parsed document)
        lemmas: List of lemmatized tokens (lowercase)
        pos_tags: List of POS tags for each token
        lemma_set: Set of unique lemmas for O(1) lookup
        tokens: List of Token objects
        entities: List of named entities (text, label)
        dependency_tree: Dependency parse information
        emotion_keywords: Pre-computed emotion keyword matches (emotion → matched lemmas)
    """
    
    # Core parsing results
    original_text: str
    doc: Doc
    
    # Token-level features
    lemmas: List[str] = field(default_factory=list)
    pos_tags: List[str] = field(default_factory=list)
    tokens: List["Token"] = field(default_factory=list)
    
    # Optimized lookups
    lemma_set: Set[str] = field(default_factory=set)
    
    # Higher-level features
    entities: List[tuple] = field(default_factory=list)  # (text, label) tuples
    dependency_tree: Dict = field(default_factory=dict)
    
    # Pre-computed emotion features
    emotion_keywords: Dict[str, List[str]] = field(default_factory=dict)
    
    @classmethod
    def from_doc(cls, doc: Doc, original_text: str) -> "NLPAnalysisCache":
        """
        Create NLPAnalysisCache from a spaCy Doc object.
        
        This method extracts all commonly needed NLP features from the parsed
        document in a single pass, avoiding repeated iteration.
        
        Args:
            doc: spaCy Doc object (result of nlp(text))
            original_text: Original message text (before spaCy processing)
        
        Returns:
            NLPAnalysisCache with all features populated
        """
        # Extract token-level features in single pass
        lemmas = []
        pos_tags = []
        tokens = []
        
        for token in doc:
            lemmas.append(token.lemma_.lower())
            pos_tags.append(token.pos_)
            tokens.append(token)
        
        # Create optimized lemma set for O(1) lookups
        lemma_set = set(lemmas)
        
        # Extract named entities
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        # Build dependency tree (for stance analysis)
        dependency_tree = cls._build_dependency_tree(doc)
        
        # Pre-compute emotion keywords (reduces 600+ substring checks to set lookups)
        emotion_keywords = cls._precompute_emotion_keywords(lemma_set)
        
        return cls(
            original_text=original_text,
            doc=doc,
            lemmas=lemmas,
            pos_tags=pos_tags,
            tokens=tokens,
            lemma_set=lemma_set,
            entities=entities,
            dependency_tree=dependency_tree,
            emotion_keywords=emotion_keywords
        )
    
    @staticmethod
    def _build_dependency_tree(doc: Doc) -> Dict:
        """
        Build simplified dependency tree for stance analysis.
        
        Args:
            doc: spaCy Doc object
        
        Returns:
            Dictionary with dependency parse information
        """
        tree = {
            'root': None,
            'subjects': [],
            'objects': [],
            'negations': [],
            'aux_verbs': []
        }
        
        for token in doc:
            if token.dep_ == 'ROOT':
                tree['root'] = token
            elif token.dep_ in ('nsubj', 'nsubjpass'):
                tree['subjects'].append(token)
            elif token.dep_ in ('dobj', 'pobj', 'iobj'):
                tree['objects'].append(token)
            elif token.dep_ == 'neg':
                tree['negations'].append(token)
            elif token.pos_ == 'AUX':
                tree['aux_verbs'].append(token)
        
        return tree
    
    @staticmethod
    def _precompute_emotion_keywords(lemma_set: Set[str]) -> Dict[str, List[str]]:
        """
        Pre-compute emotion keyword matches using lemma-based lookup.
        
        This replaces 600+ substring checks with O(1) set lookups, dramatically
        improving keyword matching performance.
        
        Args:
            lemma_set: Set of lemmas from the message
        
        Returns:
            Dictionary mapping emotion names to matched lemmas
        """
        # Emotion keyword definitions (lemma-based)
        # Note: These use BASE LEMMA FORMS that spaCy reduces words to
        # e.g., "worried" → "worry", "scared" → "scare", "running" → "run"
        # This handles all tense/form variations automatically
        emotion_keyword_map = {
            'joy': {'happy', 'excite', 'delight', 'thrill', 'wonderful', 'amazing', 'fantastic', 'great', 'love', 'enjoy'},
            'sadness': {'sad', 'depressed', 'miserable', 'unhappy', 'disappoint', 'heartbroken', 'tearful', 'cry', 'upset', 'hurt'},
            'anger': {'angry', 'furious', 'enrage', 'irritate', 'frustrate', 'annoy', 'outrage', 'mad', 'piss', 'hate'},
            'fear': {'afraid', 'scare', 'terrify', 'anxious', 'worry', 'nervous', 'frighten', 'panic', 'dread', 'phobia'},
            'surprise': {'surprise', 'shock', 'astonish', 'amaze', 'stun', 'startle', 'unexpected', 'sudden', 'wow'},
            'disgust': {'disgust', 'revolt', 'repulse', 'gross', 'sick', 'nasty', 'vile', 'repugnant', 'offensive'},
            'trust': {'trust', 'believe', 'confident', 'reliable', 'dependable', 'faithful', 'loyal', 'honest', 'safe'},
            'anticipation': {'expect', 'anticipate', 'hope', 'look forward', 'await', 'eager', 'excite', 'impatient', 'can\'t wait'},
            'neutral': {'okay', 'fine', 'alright', 'sure', 'whatever', 'maybe', 'perhaps', 'possibly', 'might'},
        }
        
        # Find matches (O(1) per keyword instead of O(n) substring matching)
        matches = {}
        for emotion, keywords in emotion_keyword_map.items():
            matched = [kw for kw in keywords if kw in lemma_set]
            if matched:
                matches[emotion] = matched
        
        return matches
    
    def has_lemma(self, lemma: str) -> bool:
        """
        Check if lemma exists in cached lemmas (O(1) lookup).
        
        Args:
            lemma: Base form to check (e.g., "worry")
            
        Returns:
            True if lemma exists in document
            
        Example:
            >>> cache.has_lemma("worry")  # True if "worried"/"worrying"/"worries" in text
            True
        """
        return lemma in self.lemmas
    
    def has_emotion_keyword(self, emotion: str) -> bool:
        """
        Check if any keywords for emotion exist in cached keywords (O(1) lookup).
        
        Args:
            emotion: Emotion name (e.g., "joy", "fear", "anger")
            
        Returns:
            True if emotion has keywords detected in document
            
        Example:
            >>> cache.has_emotion_keyword("joy")  # True if "happy"/"excited"/etc in text
            True
        """
        return emotion in self.emotion_keywords and len(self.emotion_keywords[emotion]) > 0
    
    def get_tokens_with_pos(self, pos_tag: str) -> List["Token"]:
        """
        Get all tokens with specific POS tag.
        
        Useful for finding intensifiers (ADV), verbs (VERB), etc.
        
        Args:
            pos_tag: POS tag to filter (ADV, VERB, NOUN, etc.)
        
        Returns:
            List of tokens with matching POS tag
        """
        return [token for token, pos in zip(self.tokens, self.pos_tags) if pos == pos_tag]
    
    def get_intensifier_count(self) -> int:
        """
        Count intensifier words (very, extremely, really, etc.).
        
        Useful for emotional intensity analysis.
        
        Returns:
            Number of intensifier tokens
        """
        intensifier_lemmas = {'very', 'extremely', 'really', 'so', 'absolutely', 'completely', 'totally', 'utterly'}
        return sum(1 for lemma in self.lemmas if lemma in intensifier_lemmas)
    
    def has_negation(self) -> bool:
        """
        Check if message contains negation (not, never, no, etc.).
        
        Returns:
            True if negation is present
        """
        return len(self.dependency_tree.get('negations', [])) > 0
    
    def get_emotion_keyword_matches(self, emotion: str) -> List[str]:
        """
        Get matched emotion keywords for specific emotion.
        
        Args:
            emotion: Emotion name (joy, sadness, anger, etc.)
        
        Returns:
            List of matched lemmas for this emotion
        """
        return self.emotion_keywords.get(emotion, [])
    
    def get_all_emotion_matches(self) -> Dict[str, List[str]]:
        """
        Get all emotion keyword matches.
        
        Returns:
            Dictionary mapping emotion names to matched lemmas
        """
        return self.emotion_keywords.copy()
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"NLPAnalysisCache(text='{self.original_text[:50]}...', "
            f"lemmas={len(self.lemmas)}, entities={len(self.entities)}, "
            f"emotion_matches={list(self.emotion_keywords.keys())})"
        )
