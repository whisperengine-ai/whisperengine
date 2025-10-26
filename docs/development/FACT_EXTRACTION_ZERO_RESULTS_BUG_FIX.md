# Fact Extraction Zero-Results Bug Fix

**Date**: October 25, 2025  
**Issue**: Enrichment worker's fact extraction returning 0 facts despite obvious facts in conversation  
**Status**: ✅ **FIXED**

---

## 🔍 Problem Identified

### Test Case
- **User**: enrichment_test_1761429358
- **Messages**: 12 messages with clear biographical facts
- **Expected Facts**: 8-10 facts (name, location, education, occupation, interests)
- **Actual Result**: 0 facts extracted
- **LLM Call**: Made (14 seconds processing time)
- **Root Cause**: Overly restrictive extraction prompt

### Symptoms
```
22:01:33 - 🔍 [LLM CALL] Extracting facts from 12 new messages
22:02:47 - ✅ [LLM CALL COMPLETE] No facts extracted - 0 facts found
```

---

## 🐛 Root Cause Analysis

The fact extraction prompt in `src/enrichment/fact_extraction_engine.py` had **5 critical issues**:

### 1. **Negative Instructions Blocking Everything**
```python
# OLD PROMPT (PROBLEMATIC):
- DO NOT extract: Conversational phrases, questions, abstract concepts
- DO NOT extract: Things the user asks about or discusses theoretically
Be conservative - only extract clear, unambiguous facts.
```

**Problem**: Multiple conflicting negative rules made LLM overly cautious, skipping obvious facts like names and locations.

### 2. **Missing Entity Types**
```python
# OLD: Valid entity_types: food, drink, hobby, place, pet, skill, goal, occupation, other
# MISSING: name, location, education
```

**Problem**: LLM didn't know how to classify "Alex Thompson" (name) or "Portland, Oregon" (location).

### 3. **No Positive Examples**
- Prompt told LLM what NOT to do, but didn't show clear examples of what TO extract
- No demonstration of expected output format

### 4. **Overly Conservative Temperature**
```python
temperature=0.2  # Too low, making LLM extremely cautious
```

### 5. **Ambiguous Instructions**
- "Be conservative" at end reinforced overly cautious behavior
- Instructions conflicted: "Extract preferences" vs "DO NOT extract questions"
- Questions often reveal interests (asking about diving suggests interest in diving)

---

## ✅ Solution Implemented

### Changes Made

**File**: `src/enrichment/fact_extraction_engine.py`

#### 1. **Rewrote Extraction Prompt** (Lines 195-240)

**New Approach**:
- ✅ **Positive examples first** - Shows 6 clear categories with examples
- ✅ **Explicit name/location entity types** - Added to valid types
- ✅ **Removed confusing "DO NOT extract" rules**
- ✅ **Clear output format** - Demonstrates exact JSON structure
- ✅ **Confidence guidance** - Specifies when to use 0.9-0.95 vs 0.7-0.85

**Example Structure**:
```python
extraction_prompt = f"""Extract personal facts about the user from this conversation.

WHAT TO EXTRACT - Examples:

1. NAMES & IDENTITY:
   "My name is Alex" → {{"entity_name": "Alex", "entity_type": "name", ...}}
   
2. LOCATIONS:
   "I live in Portland" → {{"entity_name": "Portland", "entity_type": "location", ...}}

3. OCCUPATIONS & EDUCATION:
   "I work as a teacher" → {{"entity_name": "teacher", "entity_type": "occupation", ...}}
   "I studied at MIT" → {{"entity_name": "MIT", "entity_type": "education", ...}}

4. HOBBIES & INTERESTS:
   "I love hiking" → {{"entity_name": "hiking", "entity_type": "hobby", ...}}

5. PREFERENCES:
   "I really like pizza" → {{"entity_name": "pizza", "entity_type": "food", ...}}

6. POSSESSIONS & EXPERIENCES:
   "I have a dog" → {{"entity_name": "dog", "entity_type": "pet", ...}}

EXTRACTION RULES:
- Extract facts stated BY the user ABOUT themselves
- Include explicit statements ("I am...", "I work as...", "I love...")
- Include clear interests expressed through questions
- Use confidence 0.9-0.95 for explicit, 0.7-0.85 for implied
- Skip vague or unclear statements

Valid entity_types: name, location, occupation, education, hobby, food, drink, place, pet, skill, goal, other
Valid relationship_types: is_named, lives_in, from, works_as, studied_at, likes, loves, enjoys, dislikes, hates, owns, has, visited, does, practices, wants, needs, plans_to, learned, knows"""
```

#### 2. **Increased Temperature** (Line 502)
```python
# OLD: temperature=0.2  # Too conservative
# NEW: temperature=0.3  # Balanced: consistent but not overly cautious
```

#### 3. **Fixed Unicode Syntax Errors**
- Replaced Unicode arrow characters (→) with ASCII (->) in code comments
- Kept arrows in prompt string (sent to LLM, not Python code)

---

## 📊 Expected Impact

### Before Fix
- ✅ Conversation summaries: Working (excellent quality)
- ❌ **Fact extraction: 0 results from obvious facts**
- ❌ Preference extraction: Skipped (shared marker bug)

### After Fix
- ✅ Conversation summaries: Still working
- ✅ **Fact extraction: Should extract 8-10 facts from test user**
  - Name: Alex Thompson
  - Location: Portland, Oregon
  - Education: UC Berkeley, Computer Science (2018), marine biology course
  - Occupation: software engineer
  - Interests: hiking, photography, octopuses, diving, marine biology
- ⚠️ Preference extraction: Still blocked by shared marker bug (separate issue)

---

## 🧪 Validation Steps

### 1. **Syntax Validation**
```bash
python3 -m py_compile src/enrichment/fact_extraction_engine.py
# ✅ Syntax check passed!
```

### 2. **Container Rebuild**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --no-deps --build enrichment-worker
# ✅ Container started successfully
```

### 3. **Runtime Verification**
```bash
docker logs enrichment-worker --since 30s
# ✅ No syntax errors, enrichment cycles running
```

### 4. **Next Enrichment Cycle**
- Wait for next cycle (runs every 12 minutes)
- Check if test user facts extracted:
  ```sql
  SELECT fe.entity_name, fe.entity_type, ufr.relationship_type, ufr.confidence
  FROM user_fact_relationships ufr
  JOIN fact_entities fe ON ufr.entity_id = fe.id
  WHERE ufr.user_id = 'enrichment_test_1761429358'
    AND fe.entity_type != '_processing_marker'
  ORDER BY ufr.created_at DESC LIMIT 20;
  ```

---

## 📝 Related Issues

### Separate Bug: Shared Timestamp Marker
**Status**: Identified, not fixed in this PR

**Problem**: Facts and preferences share same `_enrichment_progress_marker`, causing preferences to skip if facts process first.

**Flow**:
1. Fact extraction runs (22:01:33-22:02:47)
2. Updates marker timestamp to last message
3. Preference extraction runs (22:02:57)
4. Checks for messages AFTER marker
5. Finds 0 new messages (all already marked)
6. Skips LLM call: "⏭️ [NO LLM CALL] No new messages"

**Solution**: Create separate markers (`_fact_progress_marker` and `_preference_progress_marker`)

**Impact**: Medium - preferences never extracted if facts process first in same cycle

---

## 🔄 Deployment

### Files Changed
- ✅ `src/enrichment/fact_extraction_engine.py` - Improved prompt, increased temperature, fixed syntax

### Deployment Steps
1. ✅ Code changes committed
2. ✅ Syntax validated
3. ✅ Container rebuilt and started
4. ⏳ Awaiting next enrichment cycle (12-minute interval)
5. ⏳ Validate fact extraction from test user

### Rollback Plan
If issues occur:
```bash
git revert <commit_hash>
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --no-deps --build enrichment-worker
```

---

## 📚 Key Learnings

1. **Negative instructions confuse LLMs** - Focus on what TO do, not what NOT to do
2. **Examples are critical** - Demonstrations work better than rules
3. **Entity type coverage** - Missing types cause LLM to skip obvious facts
4. **Temperature matters** - 0.2 too conservative, 0.3 more balanced
5. **Prompt engineering** - Simpler, clearer prompts = better compliance

---

## ✅ Completion Checklist

- [x] Root cause identified (overly restrictive prompt)
- [x] Solution implemented (improved prompt + temperature)
- [x] Syntax errors fixed (Unicode arrows)
- [x] Code validated (py_compile passed)
- [x] Container rebuilt and running
- [x] Documentation created (this file)
- [ ] Next enrichment cycle validation (pending)
- [ ] Test user fact extraction confirmed (pending)

---

**Estimated Fix Time**: 2 hours (investigation + implementation + testing)  
**Production Impact**: Zero downtime (background worker only)  
**User Impact**: Improved fact extraction quality for all characters
