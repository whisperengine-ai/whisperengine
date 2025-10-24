"""
Enrichment NLP Preprocessor (optional spaCy integration)

Provides lightweight, local NLP signals to augment enrichment tasks:
- Entity extraction (PERSON, GPE, ORG, etc.)
- Simple dependency-based relationship candidates (SVO)
- Preference indicators (names, locations, pronoun usage, Q&A cues)
- Summary scaffolding (entities, key verbs, noun phrases)

This module is SAFE even when spaCy isn't installed. If spaCy or the model
is missing, all methods degrade gracefully and return empty signals.

Rationale:
- Avoid feature flags for local code: works by default if spaCy available
- Keep bots lean: enrichment worker can optionally include spaCy
- Reduce LLM token usage by pre-identifying candidates locally
"""
from __future__ import annotations

from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)

try:
    import spacy  # type: ignore
    _SPACY_AVAILABLE = True
except ImportError:
    spacy = None  # type: ignore
    _SPACY_AVAILABLE = False


class EnrichmentNLPPreprocessor:
    """Optional spaCy-powered NLP preprocessor for enrichment worker."""

    def __init__(self, model_name: str = "en_core_web_md") -> None:
        self.model_name = model_name
        self._nlp = None

        if _SPACY_AVAILABLE:
            try:
                self._nlp = spacy.load(model_name)  # type: ignore
                logger.info("✅ spaCy model loaded for enrichment: %s", model_name)
            except (OSError, IOError, RuntimeError) as e:
                logger.warning("⚠️  spaCy model '%s' not available: %s. Preprocessor will be inactive.", model_name, e)
        else:
            logger.info("spaCy not installed - enrichment preprocessor inactive (fallback to pure LLM)")

    def is_available(self) -> bool:
        return self._nlp is not None

    # ---------------------------------------------------------------------
    # Entity and Relationship Extraction
    # ---------------------------------------------------------------------
    def extract_entities(self, text: str, max_length: int = 10000) -> List[Dict[str, Any]]:
        """Extract named entities using spaCy NER.
        
        Args:
            text: Input text to process
            max_length: Maximum text length to process (default 10000 chars)
            
        Returns:
            List of dicts: {'text': str, 'label': str, 'start': int, 'end': int}
            
        Note:
            Relies on spaCy's default NER which has high accuracy for:
            - PERSON, GPE, ORG, DATE, TIME, MONEY (>85% accuracy)
            Lower accuracy for PRODUCT, EVENT, WORK_OF_ART (~60-70% accuracy)
        """
        if not self._nlp or not text:
            return []
        if len(text) > max_length:
            logger.warning("Text length %d exceeds max %d, truncating for entity extraction", len(text), max_length)
            text = text[:max_length]
        doc = self._nlp(text)
        entities = [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            for ent in doc.ents
        ]
        return entities

    def extract_dependency_relationships(self, text: str, max_length: int = 10000) -> List[Dict[str, str]]:
        """Heuristic SVO (subject-verb-object) candidates using dependency parse.
        
        Args:
            text: Input text to process
            max_length: Maximum text length to process (default 10000 chars)
            
        Returns:
            List of dicts: {'subject': str, 'verb': str, 'object': str}
        """
        if not self._nlp or not text:
            return []
        if len(text) > max_length:
            logger.warning("Text length %d exceeds max %d, truncating for relationship extraction", len(text), max_length)
            text = text[:max_length]
        doc = self._nlp(text)
        relationships: List[Dict[str, str]] = []
        for sent in doc.sents:
            for token in sent:
                # Find candidate verbs
                if token.pos_ == "VERB" and token.dep_ in ("ROOT", "conj"):
                    subj = None
                    dobj = None
                    # Find subject and object tied to this verb
                    for child in token.children:
                        if child.dep_ in ("nsubj", "nsubjpass"):
                            subj = child.text
                        if child.dep_ in ("dobj", "obj"):
                            dobj = child.text
                    if subj and dobj:
                        relationships.append({"subject": subj, "verb": token.lemma_, "object": dobj})
        return relationships

    # ---------------------------------------------------------------------
    # Preference Indicators
    # ---------------------------------------------------------------------
    def extract_preference_indicators(self, text: str, max_length: int = 10000) -> Dict[str, Any]:
        """Extract signals helpful for preference extraction prompts.
        
        Args:
            text: Input text to process
            max_length: Maximum text length to process (default 10000 chars)
            
        Returns:
            Dict with keys: names, locations, pronoun_counts, question_sentences
        """
        if not self._nlp or not text:
            return {
                "names": [],
                "locations": [],
                "pronoun_counts": {},
                "question_sentences": [],
            }
        if len(text) > max_length:
            logger.warning("Text length %d exceeds max %d, truncating for preference extraction", len(text), max_length)
            text = text[:max_length]
        doc = self._nlp(text)
        names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        locations = [ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
        pronoun_counts: Dict[str, int] = {}
        for tok in doc:
            if tok.pos_ == "PRON":
                key = tok.text.lower()
                pronoun_counts[key] = pronoun_counts.get(key, 0) + 1
        question_sentences = [s.text.strip() for s in doc.sents if s.text.strip().endswith("?")]
        return {
            "names": names,
            "locations": locations,
            "pronoun_counts": pronoun_counts,
            "question_sentences": question_sentences,
        }

    # ---------------------------------------------------------------------
    # Summary Scaffolding
    # ---------------------------------------------------------------------
    def build_summary_scaffold(self, text: str, max_length: int = 10000) -> Dict[str, Any]:
        """Produce structured summary scaffolding from entities, verbs, and noun phrases.
        
        Args:
            text: Input text to process
            max_length: Maximum text length to process (default 10000 chars)
            
        Returns:
            Dict with keys: entities (grouped by label), main_actions, topics
        """
        if not self._nlp or not text:
            return {
                "entities": {},
                "main_actions": [],
                "topics": [],
            }
        if len(text) > max_length:
            logger.warning("Text length %d exceeds max %d, truncating for scaffold generation", len(text), max_length)
            text = text[:max_length]
        doc = self._nlp(text)
        # Entities grouped by label
        entities: Dict[str, List[str]] = {}
        for ent in doc.ents:
            entities.setdefault(ent.label_, []).append(ent.text)
        # Main actions (root/conj verbs)
        main_actions = [tok.lemma_ for tok in doc if tok.pos_ == "VERB" and tok.dep_ in ("ROOT", "conj")]
        # Topics (noun chunks longer than one token)
        topics: List[str] = []
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) > 1:
                topics.append(chunk.text)
        return {
            "entities": entities,
            "main_actions": list(dict.fromkeys(main_actions)),  # de-dup preserve order
            "topics": list(dict.fromkeys(topics[:15])),
        }

    def build_scaffold_string(self, scaffold: Dict[str, Any]) -> str:
        """Render scaffold dict into a compact, LLM-friendly string."""
        if not scaffold:
            return ""
        entities = scaffold.get("entities", {})
        people = entities.get("PERSON", [])
        places = entities.get("GPE", [])
        orgs = entities.get("ORG", [])
        actions = scaffold.get("main_actions", [])
        topics = scaffold.get("topics", [])
        parts = [
            f"Key People: {people[:5]}",
            f"Places Mentioned: {places[:5]}",
            f"Organizations: {orgs[:5]}",
            f"Main Actions: {actions[:8]}",
            f"Topics: {topics[:8]}",
        ]
        return "\n".join(parts)

    # ---------------------------------------------------------------------
    # LLM Context Augmentation
    # ---------------------------------------------------------------------
    def build_llm_context_prefix(self, text: str, max_length: int = 10000) -> str:
        """Create a short preface string listing entities and SVO relationships.
        
        Intended to prefix fact extraction prompts to reduce token usage.
        
        Args:
            text: Input text to process
            max_length: Maximum text length to process (default 10000 chars)
            
        Returns:
            Compact string with format:
            "Pre-identified signals (spaCy):\\n- Entities: [...]\\n- Relationships: [...]"
        """
        if not self._nlp or not text:
            return ""
        # Pass max_length to extraction methods
        entities = self.extract_entities(text, max_length=max_length)
        relationships = self.extract_dependency_relationships(text, max_length=max_length)
        ent_str = ", ".join({f"{e['text']}:{e['label']}" for e in entities})
        rel_str = "; ".join({f"{r['subject']} -{r['verb']}-> {r['object']}" for r in relationships})
        prefix = (
            "Pre-identified signals (spaCy):\n"
            f"- Entities: [{ent_str}]\n"
            f"- Relationships: [{rel_str}]\n\n"
        )
        return prefix
