# Runtime Extraction Feature Flags Summary

**Date:** October 20, 2025  
**Branch:** feature/async-enrichment-worker  
**Status:** ✅ Both feature flags present and documented

---

## Overview

The feature branch adds **TWO feature flags** to control runtime extraction in the message pipeline:

1. `ENABLE_RUNTIME_FACT_EXTRACTION` (Phase 9b)
2. `ENABLE_RUNTIME_PREFERENCE_EXTRACTION` (Phase 9c)

Both default to `true` for **backward compatibility**, allowing gradual migration to enrichment-only extraction.

---

## Feature Flag #1: ENABLE_RUNTIME_FACT_EXTRACTION

### Configuration

**Environment Variable:** `ENABLE_RUNTIME_FACT_EXTRACTION`  
**Default Value:** `true` (backward compatible)  
**Phase:** 9b (Knowledge Extraction)  
**Location:** `src/core/message_processor.py:820`

### Usage

```python
# Phase 9b: Knowledge extraction and storage (PostgreSQL)
# FEATURE FLAG: Runtime fact extraction (enabled by default for backward compatibility)
# Runtime extraction uses REGEX/KEYWORD patterns (lightweight, no LLM calls)
# Enrichment worker provides better quality with LLM analysis + conversation context
# TODO: Migrate to enrichment-only after gradual rollout (set to 'false' after migration)
knowledge_stored = False
if os.getenv('ENABLE_RUNTIME_FACT_EXTRACTION', 'true').lower() == 'true':
    # Extract facts from USER message about the user
    knowledge_stored = await self._extract_and_store_knowledge(
        message_context, ai_components, extract_from='user'
    )
else:
    logger.debug("⏭️ RUNTIME FACT EXTRACTION: Disabled (enrichment worker handles fact extraction)")
```

### What It Controls

**When ENABLED (true - default):**
- Runtime regex/keyword fact extraction runs in Phase 9b
- Detects patterns like:
  - "I love pizza" → food preference
  - "I hate broccoli" → food preference
  - "I enjoy coffee" → drink preference
  - "I visited Paris" → place visited
  - "My hobby is photography" → hobby preference
- **No LLM calls** - pure local regex matching
- Lower confidence (0.7)
- User facts only (bot self-facts not supported)

**When DISABLED (false):**
- Runtime extraction skipped
- Enrichment worker handles fact extraction via LLM
- Background processing only (11-minute intervals)
- Higher quality, higher confidence (0.9+)
- Both user and bot facts supported

### Implementation Method

**Method:** `_extract_and_store_knowledge()`  
**Lines:** 5850-5975 in `message_processor.py`  
**Approach:** Regex pattern matching on message content

**Example Patterns:**
```python
factual_patterns = {
    # Food preferences
    'food_preference': [
        ('love', 'likes'), ('like', 'likes'), ('enjoy', 'likes'),
        ('favorite', 'likes'), ('prefer', 'likes'),
        ('hate', 'dislikes'), ('dislike', 'dislikes'), ("don't like", 'dislikes')
    ],
    # Drink preferences  
    'drink_preference': [
        ('love', 'likes'), ('like', 'likes'), ('enjoy', 'likes'),
        # ... more patterns
    ],
    # Hobbies, places, etc.
}
```

---

## Feature Flag #2: ENABLE_RUNTIME_PREFERENCE_EXTRACTION

### Configuration

**Environment Variable:** `ENABLE_RUNTIME_PREFERENCE_EXTRACTION`  
**Default Value:** `true` (backward compatible)  
**Phase:** 9c (User Preference Extraction)  
**Location:** `src/core/message_processor.py:839`

### Usage

```python
# Phase 9c: User preference extraction and storage (PostgreSQL)
# FEATURE FLAG: Runtime preference extraction (enabled by default for backward compatibility)
# Runtime extraction uses regex patterns (brittle, limited to 4 types)
# Enrichment worker provides better quality with LLM analysis + conversation context
# TODO: Migrate to enrichment-only after gradual rollout (set to 'false' after migration)
preference_stored = False
if os.getenv('ENABLE_RUNTIME_PREFERENCE_EXTRACTION', 'true').lower() == 'true':
    preference_stored = await self._extract_and_store_user_preferences(
        message_context
    )
else:
    logger.debug("⏭️ RUNTIME PREFERENCE EXTRACTION: Disabled (enrichment worker handles preference extraction)")
```

### What It Controls

**When ENABLED (true - default):**
- Runtime regex preference extraction runs in Phase 9c
- Detects **4 preference types**:
  1. **Preferred Name** - "My name is Mark", "Call me Mark"
  2. **Timezone** - "I'm in EST", "My timezone is PST"
  3. **Location** - "I live in Seattle", "I'm from Chicago"
  4. **Communication Style** - "I prefer short responses", "Keep it brief"
- **No LLM calls** - pure regex pattern matching
- Stored in `universal_users.preferences` JSONB column
- Fast <1ms retrieval

**When DISABLED (false):**
- Runtime extraction skipped
- Enrichment worker handles preference extraction
- Better context understanding
- Higher quality detection

### Implementation Method

**Method:** `_extract_and_store_user_preferences()`  
**Lines:** 5983-6140+ in `message_processor.py`  
**Approach:** Regex pattern matching with validation

**Preference Types & Patterns:**

#### 1. Preferred Name (confidence: 0.95)
```python
name_patterns = [
    r"(?:my|My)\s+name\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"(?:call|Call)\s+me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"(?:i|I)\s+prefer\s+(?:to\s+be\s+called\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"(?:i|I)\s+go\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"(?:you|You)\s+can\s+call\s+me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"(?:just|Just)\s+call\s+me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"(?:i|I)[''']m\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
]
```

**Examples:**
- "My name is Mark" → Mark
- "Call me Sarah" → Sarah
- "I go by Alex" → Alex
- "You can call me Dr. Smith" → Dr. Smith

#### 2. Timezone (confidence: 0.90)
```python
timezone_patterns = [
    r"(?:i|I)[''']?m\s+in\s+([A-Z]{2,4}|Pacific|Eastern|Central|Mountain|GMT|UTC)(?:\s+time)?",
    r"(?:my|My)\s+(?:timezone|time\s+zone)\s+is\s+([A-Z]{2,4}|Pacific|Eastern|Central|Mountain|GMT|UTC)",
    r"(?:i|I)\s+(?:live\s+in|am\s+on|use)\s+([A-Z]{2,4}|Pacific|Eastern|Central|Mountain|GMT|UTC)(?:\s+time)?",
]
```

**Examples:**
- "I'm in EST" → EST
- "My timezone is PST" → PST
- "I'm on Pacific time" → PACIFIC
- "I use GMT" → GMT

#### 3. Location (confidence: 0.85)
```python
location_patterns = [
    r"(?:i|I)\s+(?:live\s+in|am\s+from|reside\s+in)\s+([A-Z][a-zA-Z\s]{2,30})",
    r"(?:i|I)[''']?m\s+(?:in|located\s+in)\s+([A-Z][a-zA-Z\s]{2,30})",
    r"(?:my|My)\s+location\s+is\s+([A-Z][a-zA-Z\s]{2,30})",
]
```

**Examples:**
- "I live in Seattle" → Seattle
- "I'm from Chicago" → Chicago
- "I'm in New York" → New York
- "My location is Boston" → Boston

#### 4. Communication Style (confidence: 0.80)
```python
comm_style_patterns = [
    r"(?:i|I)\s+(?:prefer|like)\s+(short|brief|long|detailed|simple|technical)\s+(?:responses|answers|explanations)",
    r"(?:keep\s+it|make\s+it)\s+(brief|short|detailed|simple|technical)",
    r"(?:i|I)\s+want\s+(concise|brief|detailed|thorough)\s+(?:answers|responses)",
]
```

**Examples:**
- "I prefer short responses" → short
- "Keep it brief" → brief
- "I like detailed explanations" → detailed
- "I want concise answers" → concise

---

## Migration Strategy

### Current State (Both Enabled)

```bash
# .env configuration (current default)
ENABLE_RUNTIME_FACT_EXTRACTION=true
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=true
```

**Behavior:**
- ✅ Runtime regex extraction runs in Phases 9b and 9c
- ✅ Enrichment worker ALSO runs (background)
- ✅ Both systems extract facts/preferences
- ✅ Provides redundancy during migration
- ✅ Backward compatible with existing setup

### Phase 1: Test Enrichment Worker (Recommendation)

```bash
# Test enrichment-only mode on staging
ENABLE_RUNTIME_FACT_EXTRACTION=false
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=false
```

**Behavior:**
- ⏭️ Runtime extraction skipped
- ✅ Enrichment worker handles all extraction
- ✅ Higher quality (LLM-based)
- ✅ No user-facing latency
- ⚠️ 11-minute delay for extraction (background)

### Phase 2: Gradual Rollout (Production)

**Option A: Disable one at a time**
```bash
# Disable facts first, keep preferences
ENABLE_RUNTIME_FACT_EXTRACTION=false
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=true
```

**Option B: Disable both at once**
```bash
# Full enrichment-only mode
ENABLE_RUNTIME_FACT_EXTRACTION=false
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=false
```

### Phase 3: Remove Runtime Code (Future)

Once enrichment worker is proven stable:
1. Set both flags to `false` in production
2. Monitor for 1-2 weeks
3. Remove runtime extraction methods from `message_processor.py`
4. Remove feature flag checks (enrichment-only)

---

## Comparison: Runtime vs Enrichment

| Feature | Runtime (Regex) | Enrichment (LLM) |
|---------|----------------|------------------|
| **Phase** | 9b (facts), 9c (preferences) | Background worker |
| **Method** | Regex/keyword patterns | LLM (Claude Sonnet 4.5) |
| **LLM Calls** | ❌ None | ✅ Yes |
| **Speed** | ⚡ Instant | 🕐 11-minute intervals |
| **Quality** | 📊 Basic | 🎯 High |
| **Confidence** | 0.7-0.95 | 0.9+ |
| **Coverage** | Limited patterns | Full context understanding |
| **User Latency** | None (synchronous) | None (async background) |
| **API Costs** | Free (local) | LLM API costs |
| **Fact Types** | User only | User + Bot |
| **Preference Types** | 4 types (name, timezone, location, style) | Unlimited (LLM discovers) |
| **Backward Compat** | ✅ Default enabled | N/A |

---

## Feature Flag Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    RUNTIME EXTRACTION CONTROL                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FLAG #1: ENABLE_RUNTIME_FACT_EXTRACTION                       │
│  ├─ Default: true (backward compatible)                        │
│  ├─ Phase: 9b (Knowledge Extraction)                           │
│  ├─ Method: Regex pattern matching                             │
│  ├─ Types: Food, drinks, hobbies, places                       │
│  └─ Migration: Disable after enrichment proven                 │
│                                                                 │
│  FLAG #2: ENABLE_RUNTIME_PREFERENCE_EXTRACTION                 │
│  ├─ Default: true (backward compatible)                        │
│  ├─ Phase: 9c (User Preference Extraction)                     │
│  ├─ Method: Regex pattern matching                             │
│  ├─ Types: Name, timezone, location, comm style (4 total)      │
│  └─ Migration: Disable after enrichment proven                 │
│                                                                 │
│  MIGRATION PATH:                                                │
│  ├─ Current: Both enabled (runtime + enrichment)               │
│  ├─ Testing: Both disabled (enrichment-only)                   │
│  └─ Future: Remove runtime code entirely                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration Examples

### Development (Default)
```bash
# .env.elena (or any bot)
ENABLE_RUNTIME_FACT_EXTRACTION=true
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=true
```

### Staging (Test Enrichment)
```bash
ENABLE_RUNTIME_FACT_EXTRACTION=false
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=false
```

### Production (Gradual Rollout)
```bash
# Week 1: Disable facts, keep preferences
ENABLE_RUNTIME_FACT_EXTRACTION=false
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=true

# Week 2: Disable both if week 1 successful
ENABLE_RUNTIME_FACT_EXTRACTION=false
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=false
```

---

## Logging Output

### When Enabled
```
✅ REGEX FACT EXTRACTION: Stored 'pizza' (food, likes) for user 123456
✅ PREFERENCE: Stored preferred_name='Mark' for user 123456
✅ PREFERENCE: Stored timezone='EST' for user 123456
```

### When Disabled
```
⏭️ RUNTIME FACT EXTRACTION: Disabled (enrichment worker handles fact extraction)
⏭️ RUNTIME PREFERENCE EXTRACTION: Disabled (enrichment worker handles preference extraction)
```

---

## Documentation References

- **Fact Extraction Implementation:** `src/core/message_processor.py:5850-5975`
- **Preference Extraction Implementation:** `src/core/message_processor.py:5983-6140+`
- **Phase 9b Location:** `src/core/message_processor.py:814-832`
- **Phase 9c Location:** `src/core/message_processor.py:833-850`
- **Enrichment Worker:** `src/enrichment/fact_extraction_engine.py`

---

**Summary:** Both feature flags present, documented, and ready for gradual migration to enrichment-only extraction.

**Status:** ✅ **COMPLETE**  
**Default:** Both `true` (backward compatible)  
**Migration:** Set both to `false` after enrichment worker proven stable  
**Date:** October 20, 2025
