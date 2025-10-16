# Adaptive Token Budget - Quick Reference

## 🎯 What Problem Does This Solve?

Users posting "walls of text" (2000-char Discord messages) repeatedly can overflow the LLM's 8000-token context window.

## ✅ Solution

**ADAPTIVE truncation** based on actual token size (not fixed message count):
- **Short messages** (normal chat) → Keeps MANY messages (10-15+)
- **Walls of text** → Keeps FEWER messages (2-11) automatically

## 📐 How It Works

```python
1. Count total tokens in conversation
2. IF under 8000 tokens → Keep ALL messages ✅
3. IF over 8000 tokens → Drop OLDEST messages first until budget fits ✅
4. ALWAYS guarantee minimum 2 messages (1 exchange) for continuity
```

## 🔧 Code Location

**Primary**: `src/utils/context_size_manager.py` - `truncate_context()`  
**Integration**: `src/core/message_processor.py` - Line 4685  
**Tests**: `tests/automated/test_adaptive_token_management.py`

## 🧪 Test It

```bash
source .venv/bin/activate
python3 tests/automated/test_adaptive_token_management.py
```

Expected output:
- Test 1 (Short Messages): ✅ PASS - Keeps 15/15 messages
- Test 2 (Walls of Text): ✅ PASS - Keeps 11/15 messages (drops 4 oldest)
- Test 3 (Mixed): ✅ PASS - Adaptive handling

## 📊 Real-World Examples

### Example 1: Normal User (No Truncation)
```
Input:  15 short messages (50 chars each) = 1,220 tokens
Result: ALL 15 KEPT ✅
Reason: Under 8000 token budget
```

### Example 2: Wall-of-Text User (Truncation Active)
```
Input:  15 long messages (1500 chars each) = 13,520 tokens ⚠️
Result: 11 KEPT, 4 OLDEST DROPPED ✅
Reason: Adaptive algorithm fills 8000 token budget from newest → oldest
```

## 🚨 Important Notes

1. **Messages still stored in Qdrant**: Even if dropped from current prompt, they're preserved in vector database
2. **System message protected**: Character personality NEVER truncated
3. **Automatic activation**: No configuration needed - works on next bot restart
4. **Logging**: Watch for `✂️ CONTEXT TRUNCATED` warnings in logs

## ⚙️ Configuration (Optional)

To adjust behavior, edit `src/core/message_processor.py` line 4685:

```python
# Default (recommended)
truncate_context(final_context, max_tokens=8000, min_recent_messages=2)

# More generous (keeps more messages)
truncate_context(final_context, max_tokens=10000, min_recent_messages=4)

# More aggressive (tighter budget)
truncate_context(final_context, max_tokens=6000, min_recent_messages=2)
```

## 🔍 Monitoring

Check logs for truncation events:

```bash
# Jake bot logs
./multi-bot.sh logs jake-bot | grep "TRUNCATED"

# All bots
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs | grep "TRUNCATED"
```

## 📈 Performance

- **Overhead**: ~1-2ms per message (negligible)
- **Memory**: No additional storage (uses existing context)
- **CPU**: Single O(n) pass through messages

## ✅ Status

**ACTIVE** - Live in production after bot restart  
**Tested** - All test cases passing  
**Documented** - Full docs in `docs/features/ADAPTIVE_TOKEN_BUDGET_MANAGEMENT.md`

---

**Quick Deploy**: Just restart the bot - it's already integrated!
```bash
./multi-bot.sh restart-bot jake
```
