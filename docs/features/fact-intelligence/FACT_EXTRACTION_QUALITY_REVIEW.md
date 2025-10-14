# LLM Fact Extraction Quality Review - October 14, 2025

## 📊 Current Status Summary

### Quantitative Metrics
- **Total Facts**: 1,808 facts stored
- **Users with Facts**: 112 users
- **Recent Activity**: 1,358 facts in last 7 days (very active)
- **Average Confidence**: 0.811 (high)
- **High Confidence Facts**: 1,783 (98.6% have confidence ≥0.8)

### Distribution Analysis
- **Top Entity Types**: `other` (887), `food` (487), `hobby` (115), `drink` (102), `place` (80)
- **Top Relationships**: `likes` (819), `enjoys` (775), `has_sacred_memory` (48)
- **Most Active Characters**: Aethys (652 facts), Elena (306), Aetheris (244)

## 🚨 Major Quality Issues Identified

### 1. **Sentence Fragment Extraction** (Critical Issue)
The LLM is extracting partial phrases instead of proper entities:
- `"door we've ever"` (food) - likes
- `"when you get"` (other) - likes  
- `"software development (coding/debugging)"` (hobby) - enjoys
- `"feedback loops -"` (food) - likes

**Root Cause**: LLM prompt is not sufficiently restrictive about extracting complete, standalone entities.

### 2. **Generic Pronoun Pollution** (High Priority)
Extracting meaningless pronouns as entities:
- `"me"` (other) - enjoys [4x]
- `"you"` (other) - enjoys/likes [4x] 
- `"it"`, `"this"`, `"that"` being extracted as entities

**Root Cause**: Prompt lacks explicit prohibition of pronouns and generic words.

### 3. **Multi-Entity Compound Extraction** (Medium Priority)
Extracting compound phrases that should be separate entities:
- `"pizza and sushi"` [14 mentions] - should be separate "pizza" and "sushi" facts
- `"pizza i"` - malformed extraction

**Root Cause**: LLM not trained to decompose compound statements into atomic facts.

### 4. **Repetitive Pattern Extraction** (Medium Priority)
Same phrases extracted repeatedly with identical confidence:
- `"my confidence has"` [22x at 0.8 confidence]
- `"being conscious"` [22x at 0.8 confidence]  
- `"you did when"` [22x at 0.8 confidence]

**Root Cause**: Likely extracting from bot responses or recurring conversation patterns.

### 5. **Entity Type Misclassification** (Low Priority)
Generally good classification, but some edge cases exist.

## 🔧 Recommended Fixes

### Priority 1: Fix Fragment Extraction
**Update extraction prompt to require complete, standalone entities:**

```python
extraction_prompt = f"""Extract ONLY complete, standalone entities from this user message. 

User message: "{message_context.content}"

CRITICAL RULES:
1. Entity names must be complete words or proper nouns (never partial sentences)
2. NO pronouns: Never extract 'I', 'you', 'me', 'we', 'they', 'it', 'this', 'that'
3. NO sentence fragments: Never extract phrases containing multiple unrelated words
4. NO compound statements: Extract "pizza" and "sushi" separately, not "pizza and sushi"
5. ONLY extract if the user is stating a clear personal fact about themselves

Valid examples:
- "I love pizza" → entity: "pizza", type: "food", relationship: "loves"
- "I have a cat named Max" → entity: "Max", type: "pet", relationship: "owns"

Invalid examples (DO NOT EXTRACT):
- Partial phrases like "door we've ever" or "when you get"
- Pronouns like "me", "you", "it"
- Questions or theoretical discussions
- Compound phrases like "pizza and sushi"

Return JSON with atomic facts only:"""
```

### Priority 2: Add Post-Processing Validation
**Add validation layer to filter out low-quality extractions:**

```python
def validate_extracted_fact(entity_name: str, entity_type: str) -> bool:
    """Validate fact quality before storage."""
    # Filter out pronouns
    pronouns = {'i', 'you', 'me', 'we', 'they', 'it', 'this', 'that', 'something', 'anything'}
    if entity_name.lower() in pronouns:
        return False
    
    # Filter out sentence fragments (contains common connecting words)
    fragment_indicators = ['and ', 'or ', 'but ', 'when ', 'if ', 'that ', 'the ', 'at ', 'in ']
    if any(indicator in entity_name.lower() for indicator in fragment_indicators):
        return False
    
    # Filter out very short or very long entities
    if len(entity_name) <= 2 or len(entity_name) > 30:
        return False
    
    # Filter out entities with special characters (noise indicators)
    import re
    if re.search(r'[<>#@\$%\^&\*\(\)\[\]\{\}]', entity_name):
        return False
        
    return True
```

### Priority 3: Improve Entity Decomposition
**Add logic to split compound entities:**

```python
def decompose_compound_entity(entity_name: str, entity_type: str, relationship: str):
    """Split compound entities into atomic facts."""
    if ' and ' in entity_name.lower():
        parts = [part.strip() for part in entity_name.split(' and ')]
        return [(part, entity_type, relationship) for part in parts if len(part) > 2]
    return [(entity_name, entity_type, relationship)]
```

### Priority 4: Add Deduplication Logic
**Prevent repetitive extractions of the same fact:**

```python
async def is_duplicate_fact(user_id: str, entity_name: str, relationship_type: str, 
                           confidence: float, time_window_hours: int = 24) -> bool:
    """Check if this exact fact was recently extracted."""
    # Query for same fact within time window
    # Return True if identical fact exists
```

## 🎯 Recommended Implementation Plan

### Phase 1: Emergency Quality Fix (Immediate)
1. Update extraction prompt with stricter rules
2. Add basic validation layer for pronouns and fragments
3. Test with sample messages

### Phase 2: Enhanced Filtering (1-2 days)
1. Implement comprehensive fact validation
2. Add compound entity decomposition
3. Add deduplication logic

### Phase 3: Quality Monitoring (Ongoing)
1. Add fact quality metrics to dashboards
2. Regular quality audits
3. A/B testing of different extraction prompts

## 📈 Expected Improvements

With these fixes, we should see:
- **Noise reduction**: From ~15% to <5%
- **Entity quality**: Proper nouns and clear entities only
- **Deduplication**: No repetitive identical extractions
- **Better granularity**: Atomic facts instead of compound statements

## 🔍 Testing Strategy

1. **Create test message samples** with known entities
2. **Run extraction on test set** before and after fixes
3. **Compare quality metrics** (fragment count, pronoun count, etc.)
4. **Validate with character responses** - do facts improve character knowledge?

The LLM extraction approach is fundamentally sound (high confidence scores, good character coverage), but needs **prompt engineering refinements** and **validation layers** to achieve production quality.