# WhisperEngine Token Budget Analysis & Optimization
**Date:** October 16, 2025  
**Status:** 🚨 NEEDS REVIEW - Misaligned limits detected  
**Branch:** fix/probabilistic-emotion-framing

## Executive Summary

WhisperEngine uses a **multi-stage token management pipeline** with different limits at each stage. This document audits all token/character limits, identifies misalignments, and proposes optimizations for modern LLM context windows.

## 🎯 Current Model Context Windows (2025)

### Production Models (via OpenRouter)
| Model | Context Window | Output Tokens | Notes |
|-------|----------------|---------------|-------|
| **x-ai/grok-4-fast** | 131,072 tokens | 32,768 tokens | Primary (Gabriel) |
| **anthropic/claude-3.5-sonnet** | 200,000 tokens | 8,192 tokens | High-quality responses |
| **mistral/mistral-large** | 128,000 tokens | 32,000 tokens | CDL mode testing |
| **openai/gpt-4o** | 128,000 tokens | 16,384 tokens | Vision support |
| **openai/gpt-4o-mini** | 128,000 tokens | 16,384 tokens | Fact extraction |

### Key Insight
🚨 **We're targeting 8,000 token contexts when models support 128K-200K!**

---

## 🔍 Current Token Management Pipeline

### Stage 1: PromptAssembler (System Prompt Components)
**File:** `src/prompts/prompt_assembler.py`  
**Location:** Line 2096 in `message_processor.py`

```python
assembler = create_prompt_assembler(max_tokens=6000)
```

**Purpose:** Assembles system prompt from components (personality, memories, instructions)  
**Budget:** 6,000 tokens (~24,000 chars)  
**Behavior:**
- Drops *optional* components if over budget
- **KEEPS required components even if they exceed limit** ⚠️
- No intelligent truncation of oversized components

**Components:**
1. Core system prompt (priority 1) - REQUIRED
2. Attachment guard (priority 2) - REQUIRED if images
3. User facts/preferences (priority 3) - optional
4. Memory narrative (priority 5) - optional
5. CDL enhancements (various priorities)

---

### Stage 2: Context Size Manager (Full Conversation)
**File:** `src/utils/context_size_manager.py`  
**Location:** Line 4689 in `message_processor.py`

```python
truncate_context(
    final_context, 
    max_tokens=2000,  # For conversation history only
    min_recent_messages=2
)
```

**Purpose:** Manage FULL conversation array (system + user/bot messages)  
**Budget:** 2,000 tokens for conversation history  
**Total Budget Logic:**
- Production P90: 3,572 tokens total input
- System prompt: ~1,400 tokens (average)
- Conversation history: 2,000 tokens (3,572 - 1,400)

**Behavior:**
- Separates system messages from conversation
- NEVER truncates system messages (personality sacred)
- Adaptively drops oldest conversation messages
- **Emergency truncation** if system alone exceeds limits

---

### Stage 3: Emergency System Truncation
**File:** `src/utils/context_size_manager.py:173`  
**Function:** `_truncate_system_messages()`

**Triggered:** When system prompt alone exceeds `max_tokens` limit  
**Old Behavior:** Brutal mid-sentence chop + bland notice  
**New Behavior (Just Fixed):**
- Keeps first 60% (core personality/identity)
- Keeps last 20% (response instructions)
- Removes middle section with graceful notice

---

## 🚨 PROBLEMS IDENTIFIED

### Problem 1: Stage Misalignment
```
PromptAssembler: 6,000 tokens (system only)
  ↓
Context Manager: 2,000 tokens (conversation only)
  ↓
Emergency Truncation: Uses context_manager's 2,000 limit
```

**Issue:** Emergency truncation sees 6,000 token system prompt but tries to fit it in 2,000 tokens!

### Problem 2: Undersized Budgets for Modern Models
- **Current Total:** 8,000 tokens (Stage 1 limit)
- **Model Capacity:** 128K-200K tokens
- **Utilization:** ~6% of available context! 🤦

### Problem 3: Required Components Can't Be Truncated
**PromptAssembler lines 200-204:**
```python
if required_tokens > self.max_tokens:
    logger.error("Required components exceed token budget: %d > %d")
    # Return all required components anyway (system needs them)
    return required
```

**Result:** Required components bypass all limits, trigger emergency truncation

### Problem 4: Inconsistent Token Conversion
- **Context Manager:** `CHARS_PER_TOKEN = 4` (conservative)
- **PromptAssembler:** Uses token estimates directly
- **Reality:** Varies by model (GPT-4: ~3.5, Claude: ~4.5)

---

## 💡 PROPOSED FIXES

### Fix 1: Align Emergency Truncation Budget
**Current:**
```python
# Line 131 in context_size_manager.py
truncated_system = _truncate_system_messages(system_messages, max_tokens)
# Uses the CONVERSATION max_tokens (2000) for SYSTEM truncation! ❌
```

**Proposed:**
```python
# Emergency truncation should use SYSTEM budget, not conversation budget
SYSTEM_MESSAGE_MAX_TOKENS = 6000  # Match PromptAssembler
truncated_system = _truncate_system_messages(system_messages, SYSTEM_MESSAGE_MAX_TOKENS)
```

### Fix 2: Upgrade Budgets for Modern Models
**Recommended Budgets (based on 128K context models):**

```python
# Phase 1: PromptAssembler (system components)
SYSTEM_PROMPT_MAX_TOKENS = 16_000  # Up from 6,000
# Allows rich personalities, memories, and instructions

# Phase 2: Conversation History
CONVERSATION_HISTORY_MAX_TOKENS = 8_000  # Up from 2,000
# Allows 20-40 messages of context

# Total Input Budget
TOTAL_CONTEXT_BUDGET = 24_000  # System + Conversation
# Leaves 104K tokens for model to work with (128K - 24K)
```

**Rationale:**
- Modern models handle 24K input easily
- Preserves 80% of context window for model intelligence
- Still conservative (only 18% of 128K capacity)

### Fix 3: Make PromptAssembler Truncate Required Components
**Add intelligent truncation for oversized required components:**

```python
def _apply_token_budget(self, components):
    # ... existing code ...
    
    if required_tokens > self.max_tokens:
        logger.error("Required components exceed budget - applying intelligent truncation")
        return self._intelligently_truncate_required(required, self.max_tokens)
```

**Strategy for required component truncation:**
1. Preserve core identity (first 50%)
2. Preserve response instructions (last 30%)
3. Truncate middle sections (memories, examples)
4. Add graceful transition notice

### Fix 4: Standardize Token Estimation
**Create shared token estimation utility:**

```python
# src/utils/token_estimator.py (NEW)
class TokenEstimator:
    """Model-aware token estimation"""
    
    CHARS_PER_TOKEN = {
        'openai': 3.5,
        'anthropic': 4.5,
        'mistral': 4.0,
        'default': 4.0
    }
    
    @classmethod
    def estimate_tokens(cls, text: str, model_family: str = 'default') -> int:
        chars = len(text)
        ratio = cls.CHARS_PER_TOKEN.get(model_family, 4.0)
        return int(chars / ratio)
```

---

## 📊 PRODUCTION DATA ANALYSIS

**From comment in context_size_manager.py:**
```python
PRODUCTION BUDGET (based on actual OpenRouter usage data):
- Average total input: 1,700 tokens
- P90 total input: 3,572 tokens (90% of requests under this)
- P95 total input: 4,437 tokens
```

**Current Limits vs Production:**
| Metric | Production | Current Limit | Headroom |
|--------|------------|---------------|----------|
| P90 Total | 3,572 | 8,000 | 224% ✅ |
| P95 Total | 4,437 | 8,000 | 180% ✅ |
| System Avg | ~1,400 | 6,000 | 428% ✅ |

**Observation:** Current limits are ADEQUATE for production usage, but:
- Leave no room for feature growth
- Don't leverage modern model capabilities
- Force emergency truncation on edge cases

---

## 🎯 RECOMMENDED IMPLEMENTATION PLAN

### Phase 1: Critical Fixes (Immediate)
- [x] Fix emergency truncation to be less abrupt (DONE)
- [ ] **Align emergency truncation budget to use system limit (6000) not conversation limit (2000)**
- [ ] Add intelligent truncation to PromptAssembler for required components

### Phase 2: Budget Optimization (Next Sprint)
- [ ] Increase PromptAssembler budget: 6K → 16K tokens
- [ ] Increase conversation history budget: 2K → 8K tokens
- [ ] Update context size manager constants

### Phase 3: Advanced Features (Future)
- [ ] Implement model-aware token estimation
- [ ] Add dynamic budget scaling based on model context window
- [ ] Implement token usage monitoring and alerts
- [ ] Create budget presets for different model tiers

---

## 🔧 CONFIGURATION VARIABLES TO UPDATE

### Environment Variables (.env files)
```bash
# Character-level LLM config (database: character_llm_config table)
LLM_MAX_TOKENS_CHAT=4000  # Response generation limit
MAX_TOKENS_PER_CHUNK=500  # Chunking for long-form generation
```

### Python Constants
```python
# src/utils/context_size_manager.py
CHARS_PER_TOKEN = 4
MAX_CONTEXT_TOKENS = 8000  # Should increase to 24000

# src/prompts/prompt_assembler.py
# Line 2096 in message_processor.py
max_tokens=6000  # Should increase to 16000

# src/core/message_processor.py
# Line 4691
max_tokens=2000  # Should increase to 8000
```

### Database Schema
```sql
-- character_llm_config table
llm_max_tokens INTEGER DEFAULT 4000  -- Response limit (separate from context)
```

---

## 🧪 TESTING REQUIREMENTS

Before increasing budgets:
1. **Load test with large system prompts** (10K+ tokens)
2. **Verify emergency truncation preserves character voice**
3. **Test conversation history truncation** (wall-of-text scenarios)
4. **Monitor token usage costs** (OpenRouter billing)
5. **Validate all models handle increased context**

Test cases:
- ✅ Normal conversation (~1,700 tokens total)
- ✅ Rich personality character (~3,500 tokens system)
- ⚠️ Wall-of-text user messages (10K+ chars)
- ⚠️ Deep conversation history (50+ messages)
- ❌ Emergency truncation scenarios (>6K system prompt)

---

## 📈 EXPECTED IMPROVEMENTS

### With Aligned Emergency Truncation
- ✅ System prompts truncate at correct budget (6K not 2K)
- ✅ Better personality preservation in edge cases
- ✅ Clearer error messages about why truncation occurred

### With Increased Budgets (16K system + 8K history = 24K total)
- ✅ Support richer character personalities
- ✅ Longer conversation memory (20-40 messages)
- ✅ More user facts and preferences
- ✅ Deeper memory narratives
- ✅ Room for future AI intelligence features

### Cost Impact
- **Current:** ~1,700 avg × $X per 1K tokens
- **Proposed:** ~3,500 avg × $X per 1K tokens (2× increase)
- **Mitigation:** Still only 18% of model capacity, models already support this

---

## 🚨 IMMEDIATE ACTION ITEMS

1. **Fix Emergency Truncation Budget Mismatch** (HIGH PRIORITY)
   - File: `src/utils/context_size_manager.py:131`
   - Change: Use `SYSTEM_MESSAGE_MAX_TOKENS` instead of `max_tokens` parameter
   
2. **Add Intelligent Truncation to PromptAssembler** (HIGH PRIORITY)
   - File: `src/prompts/prompt_assembler.py:~200`
   - Add: `_intelligently_truncate_required()` method

3. **Document Current Behavior** (DONE)
   - This file serves as documentation

4. **Plan Budget Increase** (NEXT SPRINT)
   - Get stakeholder approval for 2× token budget increase
   - Cost analysis and projections

---

## 📚 RELATED DOCUMENTATION

- `docs/architecture/STRUCTURED_PROMPT_ASSEMBLY_ENHANCEMENT.md` - PromptAssembler design
- `docs/architecture/MESSAGE_PIPELINE_INTELLIGENCE_FLOW.md` - Full pipeline flow
- `tests/automated/test_wall_of_text_token_management.py` - Edge case tests
- `.github/copilot-instructions.md` - Development constraints and anti-patterns

---

**Review Status:** 🔴 Needs immediate attention  
**Owner:** @markcastillo  
**Next Steps:** Implement Phase 1 critical fixes, then plan Phase 2 budget optimization
