# Alternation Fix Testing Guide

**Date**: October 11, 2025  
**Purpose**: Validate message alternation fixes before implementing structured prompt assembly

## What We Fixed

1. ✅ **message_processor.py** - Consolidated all system content at beginning
2. ✅ **llm_client.py** - Simplified alternation validator (removed message mangling)
3. ✅ **Both bots restarted** - Jake and Elena are running with fixes

## Testing Checklist

### Phase 1: Basic Conversation Testing

**Test with Jake** (minimal personality, good for memory testing):
```bash
# Send a few messages in Discord to Jake bot
# Example conversation:
1. "Hey Jake, remember when we talked about that camera gear?"
2. "What was your favorite location from your travels?"
3. "Tell me about your photography style"
```

**Test with Elena** (rich personality, good for CDL testing):
```bash
# Send a few messages in Discord to Elena bot
# Example conversation:
1. "Hey Elena, what marine species are you studying right now?"
2. "Tell me about bioluminescence in deep sea creatures"
3. "What's the most fascinating ocean discovery recently?"
```

### Phase 2: Prompt Log Inspection

**Check Jake's prompt logs:**
```bash
# Find most recent Jake prompt log
ls -lht logs/prompts/Jake_*672814231002939413.json | head -1

# Inspect message structure (replace with actual filename)
cat logs/prompts/Jake_20251011_XXXXXX_672814231002939413.json | jq '.messages[] | {role: .role, content_preview: .content[:100]}'
```

**Expected structure (CORRECT):**
```json
{"role": "system", "content": "You are Jake Sterling...RELEVANT MEMORIES:...CONVERSATION FLOW:..."}
{"role": "user", "content": "Hey Jake..."}
{"role": "assistant", "content": "Jake's response..."}
{"role": "user", "content": "What was your favorite..."}
{"role": "assistant", "content": "Jake's response..."}
{"role": "user", "content": "Tell me about..."}
```

**What we DON'T want to see (BROKEN):**
```json
{"role": "system", "content": "You are Jake Sterling..."}
{"role": "user", "content": "Hey Jake..."}
{"role": "assistant", "content": "Jake's response..."}
{"role": "system", "content": "RELEVANT MEMORIES:..."}  ← ❌ BREAKS ALTERNATION
{"role": "user", "content": "What was your favorite..."}
```

### Phase 3: Validation Criteria

**✅ PASS Criteria:**
1. **First message is system** - Contains consolidated content
2. **All system content in ONE message** - Memory, conversation flow, guidance all together
3. **No system messages mid-conversation** - Only user/assistant after initial system
4. **Proper alternation** - user → assistant → user → assistant
5. **Last message is user** - Current user message
6. **No lost context** - Memory narrative and conversation summary present in system message
7. **No fake placeholders** - No `[Continuing conversation]` messages
8. **Bot responses natural** - No hallucinations, proper memory context

**❌ FAIL Criteria:**
1. System messages appearing mid-conversation
2. Consecutive same-role messages (user→user or assistant→assistant)
3. Missing memory context in system message
4. Bot responses hallucinating conversations that didn't happen
5. Empty or truncated system messages
6. Placeholder fake messages

### Phase 4: Memory Context Verification

**Check memory context length:**
```bash
# Extract system message content length
cat logs/prompts/Jake_*.json | jq '.messages[0].content | length'

# Should be several hundred to a few thousand characters
# NOT 136 chars like the bug we just fixed!
```

**Expected ranges:**
- Minimum: ~500 chars (core system + guidance, no memory)
- Typical: ~1,000-5,000 chars (core + memory + conversation flow)
- Maximum: ~17,000 chars (full context with lots of history)

### Phase 5: Compare Before/After

**If you have old prompt logs (pre-fix):**
```bash
# Find old prompt logs from before alternation fix
ls -lht logs/prompts/Jake_20251010*.json  # Yesterday's logs

# Compare structure
echo "=== OLD (BROKEN) ===" && \
cat logs/prompts/Jake_20251010*.json | jq '.messages[] | .role' && \
echo "=== NEW (FIXED) ===" && \
cat logs/prompts/Jake_20251011*.json | jq '.messages[] | .role'
```

## Quick Commands

```bash
# Watch for new prompt logs (real-time)
watch -n 2 'ls -lht logs/prompts/ | head -10'

# Check both bots' recent logs
echo "=== JAKE ===" && ls -lht logs/prompts/Jake_* | head -3
echo "=== ELENA ===" && ls -lht logs/prompts/Elena_* | head -3

# Inspect message roles only (quick validation)
cat logs/prompts/Jake_*.json | jq '.messages[] | .role'

# Check system message length
cat logs/prompts/Jake_*.json | jq '.messages[0].content | length'

# Full message inspection with truncated content
cat logs/prompts/Jake_*.json | jq '.messages[] | {role: .role, length: .content|length, preview: .content[:150]}'
```

## Success Indicators

### Immediate Success:
- ✅ Bots respond naturally without errors
- ✅ No LLM API errors in logs
- ✅ Proper message alternation in prompt logs
- ✅ System messages consolidated at beginning

### Long-term Success:
- ✅ No hallucinations about conversations that didn't happen
- ✅ Proper memory context (500-5000 chars typical)
- ✅ Conversation continuity maintained across sessions
- ✅ Character personality intact (CDL working)

## If Tests PASS → Next Steps

1. ✅ Mark alternation fixes as validated
2. 🚀 Begin structured prompt assembly implementation
3. 📋 Create detailed implementation plan
4. 🧪 Set up comprehensive test suite for new architecture

## If Tests FAIL → Rollback Plan

```bash
# Check git history for previous versions
git log --oneline src/core/message_processor.py | head -5
git log --oneline src/llm/llm_client.py | head -5

# Rollback if needed
git checkout <commit_hash> src/core/message_processor.py
git checkout <commit_hash> src/llm/llm_client.py

# Restart bots
./multi-bot.sh restart jake
./multi-bot.sh restart elena
```

## Notes

- **User ID for testing**: 672814231002939413
- **Bots available**: Jake (9097), Elena (9091)
- **Prompt logs location**: `logs/prompts/`
- **Docker logs**: `docker logs jake-bot --tail 50`

---

**Ready to test!** Send messages to Jake and Elena, then inspect the prompt logs to validate proper alternation. 🚀
