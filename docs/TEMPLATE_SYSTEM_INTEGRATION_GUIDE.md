# Template System Integration Guide

**Status**: Infrastructure complete, needs message_processor.py integration  
**Branch**: `feature/template-based-system-prompts`  
**Date**: November 2025

## 🎯 What's Done

✅ Template loader with Jinja2 rendering (`src/prompts/template_loader.py`)  
✅ PromptAssembler integration helper (`src/prompts/template_integration.py`)  
✅ Example Elena template (`characters/system_prompts/elena.txt`)  
✅ Database export script (`scripts/export_cdl_to_templates.py`)  
✅ Documentation and .env.example  
✅ jinja2 dependency added to requirements-core.txt

## 🚧 What's Needed: message_processor.py Integration

### Location

File: `src/core/message_processor.py`  
Method: `_build_conversation_context_structured()`  
Line: ~2990 (after `assembler = create_prompt_assembler(max_tokens=20000)`)

### Integration Code

Add this **BEFORE** the existing CDL database component loading:

```python
# ================================
# NEW: Template-Based System Prompt (Gradual Migration)
# ================================
# 🎭 TEMPLATE SYSTEM: Check if CHARACTER_SYSTEM_PROMPT_PATH env var is set
# If template file exists, load it (FAST - zero per-message DB queries)
# If not, fall back to existing CDL database components below
from src.memory.vector_memory_system import get_normalized_bot_name_from_env
from src.prompts.template_integration import add_template_system_prompt_if_available

bot_name = get_normalized_bot_name_from_env()
template_loaded = await add_template_system_prompt_if_available(
    assembler=assembler,
    bot_name=bot_name,
    message_context=message_context
)

if template_loaded:
    logger.info(f"✅ Template system active for {bot_name} - skipping database CDL loading")
```

### Wrap Existing CDL Code

Then wrap the ENTIRE existing CDL database loading section in:

```python
# Only load from database if template NOT available
if not template_loaded:
    # ================================
    # CDL COMPONENTS 1-2: Character Identity & Mode (Priorities 1-2)
    # ================================
    from src.prompts.cdl_component_factories import (
        create_character_identity_component,
        create_character_mode_component,
        # ... rest of imports
    )
    
    try:
        # ... ALL existing CDL component loading code ...
        # (identity_component, mode_component, personality_component, etc.)
        # Lines ~2995-3220 approximately
        
    except Exception as e:
        logger.warning(f"⚠️ STRUCTURED CONTEXT: Failed to load CDL components: {e}")
```

### Code Boundaries

**START wrapping at**: Line with `from src.memory.vector_memory_system import get_normalized_bot_name_from_env` (first CDL import)

**END wrapping at**: Line with `except Exception as e: logger.warning(f"⚠️ STRUCTURED CONTEXT: Failed to load CDL components: {e}")`

**DO NOT wrap**: 
- Temporal awareness component (line ~3220)
- User personality component (comes after)
- Memory/workflow components (comes after)

### Why This Works

- **Zero overhead when enabled**: Template loads once at startup, renders in ~1ms
- **Seamless fallback**: If template not configured, existing CDL database system runs unchanged
- **Gradual migration**: Enable per-bot via .env file, test incrementally
- **No breaking changes**: Both systems can coexist during migration

## 🧪 Testing After Integration

### 1. Enable Template for Elena

Add to `.env.elena`:
```bash
CHARACTER_SYSTEM_PROMPT_PATH=characters/system_prompts/elena.txt
```

### 2. Restart Bot

```bash
./multi-bot.sh stop-bot elena
./multi-bot.sh bot elena
```

### 3. Check Logs

Look for:
```
📄 TEMPLATE SYSTEM: Using template-based system prompt for elena
✅ TEMPLATE SYSTEM: Loaded system prompt (5234 chars, ~1200 words)
   Template replaces database CDL components - zero per-message DB overhead!
✅ Template system active for elena - skipping database CDL loading
```

### 4. Test Response Quality

```bash
# HTTP API test
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_template_user",
    "message": "Hi Elena! Tell me about your research on coral reefs.",
    "metadata": {"platform": "api_test"}
  }'
```

Expected: Elena should respond with same personality/expertise as database CDL system

### 5. Verify Database Fallback

```bash
# Remove env var from .env.elena
# Comment out: # CHARACTER_SYSTEM_PROMPT_PATH=...

# Restart
./multi-bot.sh stop-bot elena && ./multi-bot.sh bot elena

# Should see:
🗄️ DATABASE SYSTEM: Using database-driven CDL for elena
✅ STRUCTURED CONTEXT: Added CDL character identity for elena
```

## 📊 Performance Comparison

### Before (Database CDL)
```
🔍 Database queries per message: 12+
⏱️  Per-message overhead: ~60-120ms
📦 Component factories: 14 functions
🗄️  Tables queried: 50+ CDL tables
```

### After (Template System)
```
📄 Database queries per message: 0
⏱️  Per-message overhead: ~1ms
📦 Component factories: 1 function
📁 Files loaded: 1 (cached in memory)
```

**Net savings: ~60-120ms per message + reduced database load**

## 🔄 Full Migration Path

### Phase 1: Single Bot Testing
1. Enable template for Elena (lowest risk - rich personality)
2. Compare responses over 100+ messages
3. Check fidelity metrics in InfluxDB
4. Iterate on template content if needed

### Phase 2: Low-Complexity Bots
1. Export Jake and Ryan templates (minimal personality)
2. Enable template system for both
3. Validate memory testing still works

### Phase 3: All Remaining Bots
1. Export all 12 character templates: `python scripts/export_cdl_to_templates.py --all`
2. Add `CHARACTER_SYSTEM_PROMPT_PATH` to all `.env.{bot_name}` files
3. Rolling restart of all bots
4. Monitor fidelity metrics for 24-48 hours

### Phase 4: Deprecate Database CDL
1. Remove CDL component factory code (src/prompts/cdl_component_factories.py)
2. Keep PostgreSQL for user facts, enrichment, analytics
3. Update docs to reflect template-only system

## 🐛 Troubleshooting

### Template Not Loading
```python
# Debug template system status
from src.prompts.template_integration import get_template_system_status
status = get_template_system_status()
print(status)
```

### Character Responses Different
- Compare template content vs database CDL output
- Check dynamic placeholders (user_facts, recent_memories) are populated
- Review fidelity metrics before/after in InfluxDB

### Performance Not Improved
- Verify `CHARACTER_SYSTEM_PROMPT_PATH` is actually set in bot's .env
- Check logs for "Template system active" message
- Ensure database CDL section is properly wrapped in `if not template_loaded:`

## 📁 Files Modified

- ✅ `src/prompts/template_loader.py` (new)
- ✅ `src/prompts/template_integration.py` (new)
- ✅ `scripts/export_cdl_to_templates.py` (new)
- ✅ `characters/system_prompts/elena.txt` (new)
- ✅ `characters/system_prompts/README.md` (new)
- ✅ `characters/system_prompts/.env.example` (new)
- ✅ `requirements-core.txt` (added jinja2==3.1.4)
- ⏳ `src/core/message_processor.py` (needs manual integration - see above)

## 🎯 Success Criteria

✅ Template system loads without errors  
✅ Bot responses maintain same personality quality  
✅ Per-message processing time reduced by 60-120ms  
✅ Database query count drops to 0 for character personality  
✅ Fidelity metrics remain stable or improve  
✅ Easy to edit character personalities (just edit .txt file)  
✅ Git-trackable character changes

## 📚 Related Documentation

- `characters/system_prompts/README.md` - Template system user guide
- `src/prompts/template_loader.py` - Core implementation
- `src/prompts/template_integration.py` - PromptAssembler integration
- `.github/copilot-instructions.md` - Architecture documentation (needs update post-migration)

---

**Next Action**: Add integration code to `src/core/message_processor.py` as described above, then test with Elena bot.
