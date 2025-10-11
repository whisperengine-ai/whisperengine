# LLM Fact Extraction Temperature Configuration ✅

**Date**: January 2025
**Status**: Implemented - Separate Temperature for Fact Extraction
**Issue**: Using chat temperature (0.6) for fact extraction causes inconsistency

## Problem

Using the same temperature setting for both conversational responses and fact extraction creates inconsistencies:

### Chat Temperature (e.g., 0.6):
- ✅ Good for conversation: Natural, varied, engaging responses
- ❌ Bad for facts: Inconsistent extraction, different results for same input
- ❌ May extract different facts from identical messages

### Fact Extraction Needs:
- ✅ Deterministic results
- ✅ Consistent entity recognition
- ✅ Reliable JSON formatting
- ✅ Accurate fact categorization

## Solution Implemented

### 1. Separate Temperature Parameter

**Location**: `src/core/message_processor.py` lines 4327-4331

```python
# CRITICAL: Use lower temperature for fact extraction (consistency over creativity)
# Fact extraction requires deterministic, consistent results - not creative responses
fact_extraction_temperature = float(os.getenv('LLM_FACT_EXTRACTION_TEMPERATURE', '0.2'))

# Run LLM call in thread to avoid blocking
# Pass model override and temperature for fact extraction
response = await asyncio.to_thread(
    self.llm_client.get_chat_response,
    extraction_context,
    model=fact_model,
    temperature=fact_extraction_temperature
)
```

**Key Changes**:
- ✅ Separate `LLM_FACT_EXTRACTION_TEMPERATURE` environment variable
- ✅ Default value: `0.2` (low for consistency)
- ✅ Passed to LLM client via `temperature=` parameter
- ✅ Independent from chat temperature (`LLM_TEMPERATURE`)

### 2. Environment Configuration

**Template**: `.env.template` lines 37-44

```bash
# Fact Extraction Temperature (optional - default: 0.2)
# Lower temperature = more consistent, deterministic fact extraction
# DO NOT use same temperature as chat (LLM_TEMPERATURE) - fact extraction needs consistency
# Recommended: 0.1-0.3 for factual accuracy
# Leave empty to use default 0.2
LLM_FACT_EXTRACTION_TEMPERATURE=0.2
```

**Elena Bot**: `.env.elena` line 39

```bash
LLM_CHAT_MODEL=mistralai/mistral-medium-3.1
LLM_TEMPERATURE=0.6  # Chat: Natural, engaging conversation
LLM_FACT_EXTRACTION_MODEL=openai/gpt-3.5-turbo  # Fact extraction: Fast, cheap
LLM_FACT_EXTRACTION_TEMPERATURE=0.2  # Fact extraction: Consistent, deterministic
```

## Temperature Recommendations

### Fact Extraction Temperature Range

**0.0 - Completely Deterministic**:
- ✅ Maximum consistency
- ✅ Same facts every time
- ❌ May miss edge cases
- ❌ Too rigid for nuanced language

**0.1-0.2 - Recommended (DEFAULT: 0.2)**:
- ✅ High consistency
- ✅ Handles language variations well
- ✅ Reliable JSON formatting
- ✅ Good balance of accuracy and flexibility

**0.3-0.5 - Moderate**:
- ⚠️ Some variation in results
- ⚠️ May extract slightly different facts from similar inputs
- ⚠️ Less predictable JSON structure

**0.6+ - Not Recommended**:
- ❌ Too much variation
- ❌ Inconsistent extraction
- ❌ Unreliable for fact storage

### Chat Temperature for Reference

**Elena Bot Example**:
- Chat: `0.6` - Natural, engaging marine biology discussions
- Facts: `0.2` - Consistent extraction of user preferences

**Why Different**:
- Chat needs personality expression
- Facts need consistent categorization
- Chat can be creative with metaphors
- Facts must be deterministic and reliable

## Testing Strategy

### 1. Consistency Test

Send same message multiple times, verify identical fact extraction:

```bash
# Message 1: "I love pizza and hiking"
# Expected: SAME facts extracted every time
# - entity_name: "pizza", entity_type: "food", relationship_type: "likes"
# - entity_name: "hiking", entity_type: "hobby", relationship_type: "enjoys"

# Message 2: "I love pizza and hiking" (identical)
# Expected: IDENTICAL extraction as Message 1
```

### 2. Variation Test

Send similar messages, verify appropriate variation:

```bash
# Message A: "I love Italian food"
# Expected: entity_name: "Italian food", entity_type: "food"

# Message B: "I really enjoy Italian cuisine"
# Expected: entity_name: "Italian cuisine", entity_type: "food"
# Note: Slight variation OK (Italian food vs Italian cuisine)
# But: relationship_type should be consistent: "likes" or "enjoys"
```

### 3. Edge Case Test

Test with ambiguous language:

```bash
# Message: "I kind of like sushi, maybe"
# Low temperature (0.2): Consistent confidence score (e.g., 0.6)
# High temperature (0.6): Variable confidence (0.5-0.8)
```

## PostgreSQL Impact

### Before (Using Chat Temperature 0.6)

```sql
-- Same message sent twice might produce:
-- First time:
INSERT INTO user_fact_relationships (entity_name, relationship_type, confidence)
VALUES ('pizza', 'likes', 0.95);

-- Second time (inconsistent!):
INSERT INTO user_fact_relationships (entity_name, relationship_type, confidence)
VALUES ('pizza', 'enjoys', 0.88);  -- Different relationship_type!
```

### After (Using Fact Extraction Temperature 0.2)

```sql
-- Same message sent twice produces:
-- First time:
INSERT INTO user_fact_relationships (entity_name, relationship_type, confidence)
VALUES ('pizza', 'likes', 0.95);

-- Second time (consistent!):
INSERT INTO user_fact_relationships (entity_name, relationship_type, confidence)
VALUES ('pizza', 'likes', 0.95);  -- SAME extraction!
```

## Cost Optimization Benefit

**Combined Strategy**:
- Use cheaper model for fact extraction: `gpt-3.5-turbo`
- Use lower temperature for consistency: `0.2`
- Result: Cheaper + more consistent than using chat model

**Elena Bot Configuration**:
- Chat Model: `mistralai/mistral-medium-3.1` (higher quality, more expensive)
- Fact Model: `openai/gpt-3.5-turbo` (fast, cheap, consistent)
- Chat Temp: `0.6` (creative, engaging)
- Fact Temp: `0.2` (deterministic, reliable)

## Configuration Best Practices

### Per-Bot Customization

Different bots can use different settings:

```bash
# Elena (Marine Biologist) - Educational character
LLM_CHAT_MODEL=mistralai/mistral-medium-3.1  # High quality responses
LLM_TEMPERATURE=0.6  # Natural, engaging teaching
LLM_FACT_EXTRACTION_MODEL=openai/gpt-3.5-turbo  # Fast fact extraction
LLM_FACT_EXTRACTION_TEMPERATURE=0.2  # Consistent extraction

# Marcus (AI Researcher) - Technical character  
LLM_CHAT_MODEL=anthropic/claude-3.5-sonnet  # High analytical quality
LLM_TEMPERATURE=0.5  # Precise technical discussion
LLM_FACT_EXTRACTION_MODEL=openai/gpt-3.5-turbo  # Fast fact extraction
LLM_FACT_EXTRACTION_TEMPERATURE=0.15  # Very deterministic (research precision)

# Dream (Mythological) - Creative character
LLM_CHAT_MODEL=anthropic/claude-3.5-sonnet  # Creative storytelling
LLM_TEMPERATURE=0.8  # High creativity for mythology
LLM_FACT_EXTRACTION_MODEL=openai/gpt-3.5-turbo  # Fast fact extraction
LLM_FACT_EXTRACTION_TEMPERATURE=0.2  # Still consistent (facts are facts)
```

**Key Insight**: Character personality affects chat temperature, but fact extraction temperature should remain consistent (0.1-0.3) across all bots.

## Monitoring

### Log Messages to Watch

**Successful Extraction**:
```
✅ LLM FACT EXTRACTION: Stored 'pizza' (food, likes) - User explicitly stated they love pizza
✅ LLM FACT EXTRACTION: Stored 2/2 facts for user 123456789
```

**Temperature in Action**:
```
🔧 FACT EXTRACTION: Using temperature 0.2 (deterministic mode)
🔧 FACT EXTRACTION: Model: openai/gpt-3.5-turbo
```

**Consistency Check**:
```sql
-- Query for duplicate detection
SELECT entity_name, relationship_type, COUNT(*) as occurrences
FROM user_fact_relationships
WHERE user_id = '123456789'
GROUP BY entity_name, relationship_type
HAVING COUNT(*) > 1;

-- Should show CONSISTENT relationship types
-- Good: pizza -> likes (all entries)
-- Bad: pizza -> likes (some entries), pizza -> enjoys (other entries)
```

## Summary

✅ **Implemented**: Separate temperature for fact extraction
✅ **Default**: 0.2 (deterministic, consistent)
✅ **Configurable**: Per-bot via `LLM_FACT_EXTRACTION_TEMPERATURE`
✅ **Independent**: Not affected by chat temperature
✅ **Documented**: Template includes recommendations
✅ **Elena Bot**: Configured with 0.2 for testing

**Key Benefit**: Fact extraction is now consistent and reliable, while chat maintains natural personality expression through higher temperature settings.

**Ready for Testing**: Elena bot configured with separate model and temperature for fact extraction! 🎉
