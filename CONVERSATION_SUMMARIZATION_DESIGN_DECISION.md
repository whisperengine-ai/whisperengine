# Conversation Summarization Design Decision

**Date:** October 7, 2025  
**Context:** Elena response optimization and memory hierarchy improvements

## The Question

Should WhisperEngine use `AdvancedConversationSummarizer` (LLM-powered) for summarizing older conversation history in prompt engineering?

## The Answer

**NO** - We intentionally use lightweight keyword-based summarization instead.

## Why AdvancedConversationSummarizer Exists But Isn't Used

### Current State
- `AdvancedConversationSummarizer` is **imported and initialized** in `OptimizedPromptBuilder`
- But it's **NEVER CALLED** in the prompt building pipeline
- Instead, we use `_create_intelligence_enhanced_summary()` (keyword-based, no LLM calls)

### Performance Impact of LLM Summarization

**AdvancedConversationSummarizer.create_conversation_summary()** makes **2 LLM API calls**:
1. **Topic extraction** (~200 tokens, 200-500ms)
2. **Natural summary generation** (~150 tokens, 200-500ms)

**Total cost per message:**
- ⏱️ **+500ms to 2s latency** (depends on LLM provider)
- 💰 **2x token costs** (extra 350 tokens per message)
- 🔄 **Triggered on EVERY message** where conversation history > 10 messages

### Why This Matters

The prompt building pipeline is **performance-critical**:
- Called on **every single user message**
- Users expect **<2s response times**
- Adding 500ms-2s to every response is **unacceptable UX**

### Current Lightweight Approach

`_create_intelligence_enhanced_summary()`:
- ✅ **Zero LLM calls** - pure Python keyword extraction
- ✅ **<1ms execution time** - near-instant
- ✅ **Zero additional API costs**
- ✅ **"Good enough" quality** for prompt context compression
- ✅ **Intelligence-enhanced** with emotional context and significance scoring

## When to Reconsider

Consider enabling LLM-powered summarization IF:

1. **Very long conversations** (>50 messages) show quality degradation
2. **Implement caching** - summarize once per session, reuse across messages
3. **Background summarization** - async summarization doesn't block responses
4. **User explicitly requests** higher quality conversation understanding

## Implementation Strategy for Future

If we ever enable LLM summarization:

```python
# Option 1: Cached summarization (RECOMMENDED)
if len(older_messages) >= 50 and not self._has_cached_summary(user_id):
    summary_obj = await self.conversation_summarizer.create_conversation_summary(...)
    self._cache_summary(user_id, summary_obj.summary_text)
    return summary_obj.summary_text
else:
    return self._cached_summary or self._create_intelligence_enhanced_summary(...)

# Option 2: Background summarization
# Summarize asynchronously, use previous summary for current response
asyncio.create_task(self._background_summarize(older_messages))
return self._get_last_summary() or self._create_intelligence_enhanced_summary(...)

# Option 3: Threshold-based
if len(older_messages) >= 50:
    # Use LLM for very long histories where quality matters
    return await self.conversation_summarizer.create_conversation_summary(...)
else:
    # Use keyword-based for shorter histories
    return self._create_intelligence_enhanced_summary(...)
```

## Related Files

- `src/prompts/optimized_prompt_builder.py` - Contains commented explanations
- `src/memory/conversation_summarizer.py` - The unused AdvancedConversationSummarizer
- `src/memory/processors/conversation_summarizer.py` - Alternative ConversationSummarizer (also unused)

## Key Takeaway

**Speed > Sophistication** for prompt engineering in real-time conversation.

The keyword-based approach is **intentionally lightweight** and **good enough** for context compression. LLM-powered summarization exists as infrastructure for **future archival/analysis features**, not real-time prompt building.

## Related Decisions

- ✅ Intelligent named vector selection (emotion/pattern/content routing)
- ✅ Memory hierarchy with real summaries (not topic labels)
- ✅ Fidelity-first prompt building (full context → graduated optimization)
- ✅ **Lightweight summarization** (this document)

---

**Priority:** Architecture documentation  
**Status:** Design decision documented  
**Next Review:** When conversation quality issues reported for long histories
