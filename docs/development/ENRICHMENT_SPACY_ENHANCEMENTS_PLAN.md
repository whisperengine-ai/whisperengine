# Task E.1: Negation-Aware SVO for Enrichment Worker

**Effort:** 2 hours  
**Value:** HIGH  
**Status:** 📋 Planned  
**Dependencies:** Task 2.1 (Dependency Parsing) complete

---

## 🎯 Objective

Enhance `EnrichmentNLPPreprocessor` with negation detection and upgrade SVO extraction to match the quality we just implemented in `UnifiedQueryClassifier`.

---

## 📋 Implementation Steps

### **Step E.1.1: Add Negation Detection Method**

Add to `src/enrichment/nlp_preprocessor.py`:

```python
def detect_negation(self, text: str, max_length: int = 10000) -> Dict[str, Any]:
    """
    Detect negation patterns in text using dependency parsing.
    
    Args:
        text: Input text to analyze
        max_length: Maximum text length to process
        
    Returns:
        Dict with keys:
        - has_negation: bool
        - negated_verbs: List[str] (lemmatized verb forms)
        - negation_tokens: List[str] (e.g., "n't", "not", "never")
    """
    if not self._nlp or not text:
        return {
            "has_negation": False,
            "negated_verbs": [],
            "negation_tokens": []
        }
    
    if len(text) > max_length:
        text = text[:max_length]
    
    doc = self._nlp(text)
    
    negated_verbs = []
    negation_tokens = []
    
    for token in doc:
        # Check if token has negation dependency
        for child in token.children:
            if child.dep_ == "neg":
                negated_verbs.append(token.lemma_)
                negation_tokens.append(child.text)
                
                logger.debug(
                    "🚫 ENRICHMENT NEGATION: '%s' negates '%s'",
                    child.text, token.text
                )
    
    return {
        "has_negation": len(negated_verbs) > 0,
        "negated_verbs": negated_verbs,
        "negation_tokens": negation_tokens
    }
```

---

### **Step E.1.2: Enhance SVO Extraction with Negation & Confidence**

Replace `extract_dependency_relationships()` in `src/enrichment/nlp_preprocessor.py`:

```python
def extract_dependency_relationships(
    self, 
    text: str, 
    max_length: int = 10000
) -> List[Dict[str, Any]]:
    """
    Enhanced SVO extraction with negation detection and confidence scoring.
    
    Args:
        text: Input text to process
        max_length: Maximum text length to process
        
    Returns:
        List of dicts with keys:
        - subject: str
        - verb: str (lemmatized)
        - object: str
        - negated: bool (NEW)
        - confidence: float (NEW: 0.9 for dobj, 0.7 for ccomp/xcomp)
        - sentence: str (NEW: source sentence for context)
    """
    if not self._nlp or not text:
        return []
    
    if len(text) > max_length:
        logger.warning(
            "Text length %d exceeds max %d, truncating for relationship extraction",
            len(text), max_length
        )
        text = text[:max_length]
    
    doc = self._nlp(text)
    relationships: List[Dict[str, Any]] = []
    
    for sent in doc.sents:
        for token in sent:
            # Find candidate verbs (ROOT or conjunctions)
            if token.pos_ == "VERB" and token.dep_ in ("ROOT", "conj"):
                subj = None
                obj = None
                confidence = 0.0
                is_negated = False
                
                # Extract subject, object, and negation from verb's children
                for child in token.children:
                    # Subject
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        subj = child.text
                    
                    # Direct object (high confidence)
                    elif child.dep_ in ("dobj", "obj"):
                        obj = child.text
                        confidence = 0.9
                    
                    # Clausal complement (medium confidence)
                    elif child.dep_ in ("ccomp", "xcomp", "acomp"):
                        # Get the head noun of the complement
                        for comp_child in child.subtree:
                            if comp_child.pos_ in ("NOUN", "PROPN"):
                                obj = comp_child.text
                                confidence = 0.7
                                break
                    
                    # Negation detection
                    elif child.dep_ == "neg":
                        is_negated = True
                
                # Only add if we found both subject and object
                if subj and obj:
                    relationships.append({
                        "subject": subj,
                        "verb": token.lemma_,
                        "object": obj,
                        "negated": is_negated,
                        "confidence": confidence,
                        "sentence": sent.text.strip()
                    })
                    
                    logger.debug(
                        "📝 ENRICHMENT SVO: %s -%s%s-> %s (confidence: %.1f)",
                        subj,
                        "NOT " if is_negated else "",
                        token.lemma_,
                        obj,
                        confidence
                    )
    
    return relationships
```

---

### **Step E.1.3: Update LLM Context Prefix with Negation**

Enhance `build_llm_context_prefix()` in `src/enrichment/nlp_preprocessor.py`:

```python
def build_llm_context_prefix(self, text: str, max_length: int = 10000) -> str:
    """
    Create enhanced context prefix with negation awareness.
    
    Args:
        text: Input text to process
        max_length: Maximum text length to process
        
    Returns:
        Compact string with format:
        "Pre-identified signals (spaCy):\\n
        - Entities: [...]\\n
        - Relationships: [...] (includes negation flags)\\n
        - Negation: [...] (if present)"
    """
    if not self._nlp or not text:
        return ""
    
    # Extract signals
    entities = self.extract_entities(text, max_length=max_length)
    relationships = self.extract_dependency_relationships(text, max_length=max_length)
    negation_info = self.detect_negation(text, max_length=max_length)
    
    # Format entities
    ent_str = ", ".join({f"{e['text']}:{e['label']}" for e in entities[:15]})
    
    # Format relationships with negation indicators
    rel_parts = []
    for r in relationships[:10]:
        neg_prefix = "NOT " if r.get("negated", False) else ""
        confidence = r.get("confidence", 0.0)
        rel_parts.append(
            f"{r['subject']} -{neg_prefix}{r['verb']}-> {r['object']} (conf: {confidence:.1f})"
        )
    rel_str = "; ".join(rel_parts)
    
    # Build prefix
    prefix_parts = [
        "Pre-identified signals (spaCy):",
        f"- Entities: [{ent_str}]",
        f"- Relationships: [{rel_str}]"
    ]
    
    # Add negation summary if present
    if negation_info["has_negation"]:
        negated_verbs = ", ".join(negation_info["negated_verbs"])
        prefix_parts.append(f"- Negation detected: [{negated_verbs}]")
    
    return "\\n".join(prefix_parts) + "\\n\\n"
```

---

### **Step E.1.4: Create Unit Tests**

Create `tests/enrichment/test_negation_aware_svo.py`:

```python
"""Unit tests for negation-aware SVO extraction in enrichment worker."""

import pytest
from src.enrichment.nlp_preprocessor import EnrichmentNLPPreprocessor


class TestNegationDetection:
    """Test negation detection in enrichment preprocessor."""
    
    @pytest.fixture
    def preprocessor(self):
        return EnrichmentNLPPreprocessor()
    
    def test_simple_negation(self, preprocessor):
        if not preprocessor.is_available():
            pytest.skip("spaCy not available")
        
        text = "I don't like spicy food"
        result = preprocessor.detect_negation(text)
        
        assert result["has_negation"] is True
        assert "like" in result["negated_verbs"]
    
    def test_no_negation(self, preprocessor):
        if not preprocessor.is_available():
            pytest.skip("spaCy not available")
        
        text = "I love pizza and pasta"
        result = preprocessor.detect_negation(text)
        
        assert result["has_negation"] is False
        assert len(result["negated_verbs"]) == 0


class TestEnhancedSVO:
    """Test enhanced SVO extraction with negation and confidence."""
    
    @pytest.fixture
    def preprocessor(self):
        return EnrichmentNLPPreprocessor()
    
    def test_svo_with_negation(self, preprocessor):
        if not preprocessor.is_available():
            pytest.skip("spaCy not available")
        
        text = "I don't like spicy food"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        assert len(relationships) > 0
        svo = relationships[0]
        
        assert svo["subject"] == "I"
        assert svo["verb"] == "like"
        assert svo["object"] == "food"
        assert svo["negated"] is True
        assert svo["confidence"] > 0.0
    
    def test_svo_without_negation(self, preprocessor):
        if not preprocessor.is_available():
            pytest.skip("spaCy not available")
        
        text = "Mark loves pizza"
        relationships = preprocessor.extract_dependency_relationships(text)
        
        assert len(relationships) > 0
        svo = relationships[0]
        
        assert svo["subject"] == "Mark"
        assert svo["verb"] == "love"
        assert svo["object"] == "pizza"
        assert svo["negated"] is False
        assert svo["confidence"] == 0.9  # Direct object
    
    def test_confidence_scoring(self, preprocessor):
        if not preprocessor.is_available():
            pytest.skip("spaCy not available")
        
        # Direct object should have higher confidence
        text1 = "I bought a car"
        rel1 = preprocessor.extract_dependency_relationships(text1)[0]
        assert rel1["confidence"] == 0.9
        
        # Complement should have lower confidence
        text2 = "I want to learn Python"
        rel2 = preprocessor.extract_dependency_relationships(text2)
        if len(rel2) > 0:
            assert rel2[0]["confidence"] == 0.7


class TestLLMContextPrefix:
    """Test enhanced LLM context prefix with negation."""
    
    @pytest.fixture
    def preprocessor(self):
        return EnrichmentNLPPreprocessor()
    
    def test_prefix_includes_negation(self, preprocessor):
        if not preprocessor.is_available():
            pytest.skip("spaCy not available")
        
        text = "I don't like spicy food but I love pizza"
        prefix = preprocessor.build_llm_context_prefix(text)
        
        assert "Negation detected" in prefix
        assert "like" in prefix or "NOT like" in prefix
    
    def test_prefix_includes_confidence(self, preprocessor):
        if not preprocessor.is_available():
            pytest.skip("spaCy not available")
        
        text = "Mark loves pizza"
        prefix = preprocessor.build_llm_context_prefix(text)
        
        assert "conf:" in prefix  # Confidence scores present
        assert "love" in prefix


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

### **Step E.1.5: Integration Testing**

Test with real enrichment worker scenarios:

```bash
# Test fact extraction with negation
python tests/integration/test_enrichment_negation_facts.py

# Test conversation summarization with enhanced SVO
python tests/integration/test_enrichment_summary_quality.py
```

---

## 📊 Expected Results

### **Before (Current State)**
```python
# Text: "I don't like spicy food"
# SVO: {"subject": "I", "verb": "like", "object": "food"}
# LLM may extract: "likes spicy food" ❌
```

### **After (Enhanced)**
```python
# Text: "I don't like spicy food"
# SVO: {
#   "subject": "I",
#   "verb": "like",
#   "object": "food",
#   "negated": True,  ✅
#   "confidence": 0.9  ✅
# }
# LLM correctly extracts: "dislikes spicy food" ✅
```

---

## 🎯 Success Criteria

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Negation Detection | >95% | Unit tests with negation variants |
| SVO Confidence Accuracy | >90% | Validate confidence assignment logic |
| Fact Extraction Accuracy | +15% | Compare before/after on test conversations |
| LLM Context Quality | Subjective | Manual review of prefixes |
| Performance | <50ms overhead | Benchmark SVO extraction time |

---

## 🚨 Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing extraction | Comprehensive regression tests |
| Performance degradation | Benchmark and optimize if needed |
| False positive negations | Conservative negation detection (dep_=="neg" only) |
| Confidence scoring errors | Test with diverse sentence structures |

---

**Total Effort:** 2 hours  
**Dependencies:** Task 2.1 complete (code patterns available)  
**Priority:** HIGH - Prevents fact extraction conflicts
