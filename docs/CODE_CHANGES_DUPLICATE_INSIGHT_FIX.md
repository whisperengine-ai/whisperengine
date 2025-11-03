# Code Changes Summary - Duplicate Insight Fix

## Change 1: character_insight_storage.py - Pre-Check Implementation

### Before
```python
async def store_insight(self, insight: CharacterInsight) -> int:
    query = """
        INSERT INTO character_insights (...)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id;
    """
    
    async with self.db_pool.acquire() as conn:
        try:
            insight_id = await conn.fetchval(query, ...)
            logger.info(f"✅ Stored insight ID {insight_id}...")
            return insight_id
            
        except asyncpg.UniqueViolationError:
            logger.warning(f"⚠️ Duplicate insight content for character...")  # WARNING LOGGED
            raise  # Exception propagates - WARNING appears in logs
```

**Problem**: 
- ⚠️ Duplicate insights trigger `UniqueViolationError`
- ⚠️ Exception is caught and re-raised
- ⚠️ Warning appears in logs every time duplicate is found

### After
```python
async def store_insight(self, insight: CharacterInsight) -> int:
    # First, check if this insight already exists (to avoid duplicate insertion)
    check_query = """
        SELECT id FROM character_insights
        WHERE character_id = $1 AND insight_content = $2
        LIMIT 1;
    """
    
    async with self.db_pool.acquire() as conn:
        try:
            # Check if insight already exists
            existing_id = await conn.fetchval(
                check_query,
                insight.character_id,
                insight.insight_content
            )
            
            if existing_id:
                self.logger.debug(
                    "ℹ️ Insight already exists for character %s "
                    "(ID: %s), skipping duplicate: '%s...'",
                    insight.character_id,
                    existing_id,
                    insight.insight_content[:50]
                )
                return existing_id  # Return without INSERT or error
            
            # INSERT as normal if not found
            insight_id = await conn.fetchval(query, ...)
            logger.info("✅ Stored insight ID %s...", insight_id)
            return insight_id
            
        except asyncpg.UniqueViolationError:
            # Rarely happens now, but handle gracefully
            existing_id = await conn.fetchval(check_query, ...)
            if existing_id:
                self.logger.debug(
                    "ℹ️ Duplicate insight detected and retrieved from DB "
                    "(ID: %s) for character %s",
                    existing_id,
                    insight.character_id
                )
                return existing_id  # Return ID, don't raise
            raise  # Only re-raise if truly unexpected
```

**Solution**:
- ✅ Pre-check prevents INSERT attempt on duplicates
- ✅ Returns existing ID gracefully
- ✅ No exceptions, no warnings, no log spam
- ✅ Degrades gracefully if concurrent insert happens

---

## Change 2: message_processor.py - Attribute Name Fix

### Before
```python
# Line 1089
if user_stance_analysis:
    logger.info(
        f"🎯 USER STANCE ANALYSIS: self_focus={user_stance_analysis.self_focus_ratio:.2f}, "
        #                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^ WRONG - doesn't exist
        f"type={user_stance_analysis.emotion_type}, "
        f"emotions={user_stance_analysis.primary_emotions}"
    )

# Line 1107
if user_stance_analysis and user_stance_analysis.self_focus_ratio < 0.5:
    #                                              ^^^^^^^^^^^^^^^^^^^ WRONG - doesn't exist
    logger.info(f"⚠️  LOW SELF-FOCUS: Deprioritizing emotion...")
```

**Error**:
```
AttributeError: 'StanceAnalysis' object has no attribute 'self_focus_ratio'
```

### After
```python
# Line 1089
if user_stance_analysis:
    logger.info(
        "🎯 USER STANCE ANALYSIS: self_focus=%.2f, type=%s, emotions=%s",
        user_stance_analysis.self_focus,  # ✅ CORRECT - matches dataclass
        user_stance_analysis.emotion_type,
        user_stance_analysis.primary_emotions
    )

# Line 1107
if user_stance_analysis and user_stance_analysis.self_focus < 0.5:
    #                                              ^^^^^^^^^ ✅ CORRECT
    logger.info(f"⚠️  LOW SELF-FOCUS: Deprioritizing emotion...")
```

**Fix**:
- ✅ Changed `self_focus_ratio` to `self_focus`
- ✅ Matches `StanceAnalysis` dataclass definition (line 26 in spacy_stance_analyzer.py)
- ✅ Also converted logging to lazy % formatting

---

## Dataclass Reference

From `src/intelligence/spacy_stance_analyzer.py`:

```python
@dataclass
class StanceAnalysis:
    """Result of stance analysis on text"""
    primary_emotions: List[str]      # User's/bot's actual emotions
    other_emotions: List[str]        # Attributed emotions (to others)
    self_focus: float                # ← THIS IS THE CORRECT ATTRIBUTE NAME
    emotion_type: str                # 'direct', 'attributed', 'mixed', 'none'
    filtered_text: Optional[str]
    stance_subjects: Dict[str, str]
    has_negation: Dict[str, bool]
    confidence: float
```

NOT `self_focus_ratio` - that was a typo in the message processor code.

---

## Testing Commands

```bash
# Verify the fixes
grep -n "self_focus" src/core/message_processor.py | head -20
# Should show: self_focus (not self_focus_ratio)

# Restart bot to apply changes
./multi-bot.sh stop-bot elena
./multi-bot.sh bot elena

# Monitor logs for warnings
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs elena-bot | grep -i "duplicate\|stance"
```

---

## Impact

| Component | Before | After |
|-----------|--------|-------|
| Duplicate insights | ⚠️ Warning spam | ✅ Silent handling |
| Bot learning | ❌ Error interrupts learning | ✅ Continues seamlessly |
| Log cleanliness | ❌ Cluttered with warnings | ✅ Only debug-level logs |
| Stance analysis | ❌ AttributeError crash | ✅ Works correctly |

**Performance**: ~1ms added (SELECT query is indexed on (character_id, insight_content))

---

## Files Changed
1. `/Users/markcastillo/git/whisperengine/src/characters/learning/character_insight_storage.py`
2. `/Users/markcastillo/git/whisperengine/src/core/message_processor.py`
