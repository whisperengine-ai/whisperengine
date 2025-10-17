# Token Budget Fixes - Implementation Summary
**Date:** October 16, 2025  
**Branch:** fix/probabilistic-emotion-framing  
**Status:** ✅ Phase 1 Complete

## What Was Fixed

### Problem
System prompt truncation was using the wrong token budget:
- **PromptAssembler** creates system prompts with 6,000 token budget
- **Emergency truncation** was using the 2,000 token **conversation** budget
- Result: System prompts were being chopped at 2K when they should go up to 6K

### Root Cause
In `context_size_manager.py`, the `truncate_context()` function has two responsibilities:
1. Manage conversation history (max 2,000 tokens)
2. Emergency truncate system prompts if needed

But it was using the same `max_tokens` parameter (2,000) for both! System prompts need 6,000.

---

## Changes Made

### 1. Added Token Budget Constants (`context_size_manager.py`)
```python
# NEW: Explicit budget alignment
SYSTEM_PROMPT_MAX_TOKENS = 6000  # Matches PromptAssembler
CONVERSATION_HISTORY_MAX_TOKENS = 2000  # For message history only
```

**Why:** Makes budget limits explicit and aligned across stages.

### 2. Fixed Emergency Truncation Budget (`context_size_manager.py:138`)
**Before:**
```python
truncated_system = _truncate_system_messages(system_messages, max_tokens)
# Used conversation budget (2000) for system truncation ❌
```

**After:**
```python
truncated_system = _truncate_system_messages(system_messages, SYSTEM_PROMPT_MAX_TOKENS)
# Uses correct system budget (6000) ✅
```

### 3. Improved Truncation Intelligence (`context_size_manager.py:179`)
**Old behavior:**
- Brutal mid-sentence chop
- Bland `"... [system prompt truncated due to size]"` notice
- No context about what was removed

**New behavior:**
- Keeps first 60% (core personality/identity)
- Keeps last 20% (response instructions)
- Removes middle section (examples, less critical memories)
- Adds graceful notice explaining truncation
- Preserves character voice better

### 4. Added Intelligent Truncation to PromptAssembler (`prompt_assembler.py:227`)
**Old behavior:**
```python
if required_tokens > self.max_tokens:
    logger.error("Required components exceed budget")
    return required  # Returns oversized components anyway! ❌
```

**New behavior:**
```python
if required_tokens > self.max_tokens:
    logger.error("Required components exceed budget - applying intelligent truncation")
    return self._intelligently_truncate_required(required, self.max_tokens) ✅
```

**New method:** `_intelligently_truncate_required()` (133 lines)
- Fits components into budget priority-order
- Truncates oversized components (50% beginning + 30% end)
- Adds clear truncation notices per component
- Logs detailed truncation metrics

---

## Files Modified

1. **`src/utils/context_size_manager.py`**
   - Added `SYSTEM_PROMPT_MAX_TOKENS` and `CONVERSATION_HISTORY_MAX_TOKENS` constants
   - Fixed emergency truncation to use correct budget
   - Improved truncation intelligence (60/20 split)

2. **`src/prompts/prompt_assembler.py`**
   - Added `_intelligently_truncate_required()` method
   - Changed budget overflow handling to truncate instead of bypass

3. **`docs/architecture/TOKEN_BUDGET_ANALYSIS.md`** (NEW)
   - Comprehensive audit of all token limits
   - Problem analysis and recommendations
   - Phase 1/2/3 implementation plan

4. **`docs/architecture/TOKEN_BUDGET_FIXES_SUMMARY.md`** (THIS FILE)
   - Implementation summary
   - Before/after comparisons
   - Testing checklist

---

## Token Budget Flow (After Fixes)

```
📝 PromptAssembler (Stage 1)
│  Budget: 6,000 tokens (system components)
│  ├─ Core personality: REQUIRED, priority 1
│  ├─ User facts: optional, priority 3
│  ├─ Memory narrative: optional, priority 5
│  └─ If required > 6K: Intelligent truncation (NEW!)
│
↓ Outputs system message (~1,400 avg, 3,500 P90)
│
📏 Context Size Manager (Stage 2)
│  Budget: 2,000 tokens (conversation history)
│  ├─ System message: NEVER truncated (personality sacred)
│  ├─ Conversation: Adaptive truncation (drops oldest)
│  └─ If system alone > 6K: Emergency truncation at 6K (FIXED!)
│
↓ Outputs full context array
│
🤖 LLM
   Receives: System (~1.4K) + History (~2K) = ~3.5K total
   Available: 128K context window (Claude/GPT-4/Mistral)
   Utilization: ~3% 😅
```

---

## Testing Checklist

### ✅ Unit Tests Needed
- [ ] Test `_truncate_system_messages()` with 6K budget (not 2K)
- [ ] Test `_intelligently_truncate_required()` preserves priority components
- [ ] Verify 60/20 split for emergency truncation
- [ ] Confirm truncation notices are character-neutral

### ✅ Integration Tests Needed
- [ ] Generate 8K+ token system prompt, verify truncates at 6K (not 2K)
- [ ] Test wall-of-text user messages with rich character personalities
- [ ] Verify conversation history truncation still works (2K limit)
- [ ] Test with Aetheris character (known for large prompts)

### ✅ Production Validation
- [ ] Enable `ENABLE_PROMPT_LOGGING=true` in test environment
- [ ] Review logged prompts for truncation events
- [ ] Monitor character personality preservation in truncated cases
- [ ] Check OpenRouter token usage for cost impact

---

## Known Limitations

### 1. Still Conservative Budgets
- **Current:** 6K system + 2K history = 8K total
- **Model Capacity:** 128K-200K tokens
- **Utilization:** ~6% of available context
- **Next Phase:** Increase to 16K system + 8K history = 24K total

### 2. Character-Agnostic Truncation
- Truncation doesn't understand character personality nuances
- Same 60/20 split for all characters
- **Future:** Character-specific truncation strategies

### 3. No Model-Specific Token Counting
- Uses generic `CHARS_PER_TOKEN = 4` estimate
- Different models have different tokenization
  - GPT-4: ~3.5 chars/token
  - Claude: ~4.5 chars/token
  - Mistral: ~4.0 chars/token
- **Future:** Model-aware token estimation

---

## Next Steps (Phase 2 - Future)

### Budget Increases (Requires Stakeholder Approval)
```python
# Proposed increases for modern models
SYSTEM_PROMPT_MAX_TOKENS = 16_000  # Up from 6,000 (2.7×)
CONVERSATION_HISTORY_MAX_TOKENS = 8_000  # Up from 2,000 (4×)
TOTAL_CONTEXT_BUDGET = 24_000  # Up from 8,000 (3×)
```

**Benefits:**
- Richer character personalities
- Deeper conversation memory (20-40 messages vs 10-15)
- More user facts and preferences
- Room for future AI intelligence features

**Costs:**
- 2-3× token usage increase
- Still only 18% of model capacity (conservative)

### Advanced Features (Phase 3)
- [ ] Model-aware token estimation
- [ ] Character-specific truncation strategies
- [ ] Dynamic budget scaling based on model
- [ ] Token usage monitoring and alerts
- [ ] A/B testing different budget configurations

---

## Success Metrics

### Before Fixes
- ❌ System prompts truncated at 2K (wrong budget)
- ❌ Abrupt mid-sentence chops
- ❌ No explanation of what was removed
- ❌ Required components bypassed all limits

### After Fixes
- ✅ System prompts truncate at correct 6K budget
- ✅ Intelligent 60/20 split preserves critical sections
- ✅ Clear truncation notices
- ✅ Required components fit within budget via intelligent truncation

### Expected Impact
- 📈 Better character personality preservation in edge cases
- 📉 Fewer emergency truncation events (3× more headroom)
- 📊 More predictable prompt behavior
- 🎭 Character voice maintained even when truncated

---

## References

- **Token Budget Analysis:** `docs/architecture/TOKEN_BUDGET_ANALYSIS.md`
- **PromptAssembler Design:** `docs/architecture/STRUCTURED_PROMPT_ASSEMBLY_ENHANCEMENT.md`
- **Pipeline Flow:** `docs/architecture/MESSAGE_PIPELINE_INTELLIGENCE_FLOW.md`
- **Edge Case Tests:** `tests/automated/test_wall_of_text_token_management.py`

---

**Review Status:** ✅ Phase 1 Complete - Ready for Testing  
**Approver:** @markcastillo  
**Next Review:** After production validation with test characters
