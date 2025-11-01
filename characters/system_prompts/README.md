# Template-Based System Prompts

This directory contains **template-based system prompt files** for WhisperEngine characters. These templates replace the database-driven CDL prompt generation system, providing zero per-message database overhead while maintaining full character personality.

## 🚀 Benefits Over Database CDL

| Metric | Template System | Database CDL |
|--------|----------------|--------------|
| **Per-Message DB Queries** | 0 | 12+ queries |
| **Startup Load Time** | <10ms (one-time) | 0ms |
| **Per-Message Overhead** | ~1ms (template render) | ~60-120ms (DB queries + serialization) |
| **Debuggability** | Direct file reading | Query 50+ tables |
| **Version Control** | ✅ Git-trackable | ❌ Database only |
| **Character Updates** | Edit file + restart bot | Update DB + regenerate |

## 📁 File Structure

```
characters/system_prompts/
  elena.txt          # Elena Rodriguez - Marine Biologist
  marcus.txt         # Marcus Thompson - AI Researcher  
  jake.txt           # Jake - Adventure Photographer
  [bot_name].txt     # Template for each character
  README.md          # This file
```

## 🔧 Usage

### Enable Template System for a Character

Add to `.env.{bot_name}` file:

```bash
# Enable template-based system prompt (zero DB overhead!)
CHARACTER_SYSTEM_PROMPT_PATH=characters/system_prompts/elena.txt
```

**That's it!** The bot will automatically:
1. Check if `CHARACTER_SYSTEM_PROMPT_PATH` is set
2. Load template file once at startup
3. Skip all database CDL component loading
4. Render template with dynamic data (user facts, memories, etc.)

### Fallback to Database CDL

If `CHARACTER_SYSTEM_PROMPT_PATH` is not set or file doesn't exist:
- **Automatic fallback** to existing database CDL system
- No code changes needed - seamless migration
- Both systems can coexist during gradual migration

## 📝 Template Format

Templates use **Jinja2 syntax** with dynamic placeholders:

```text
# SYSTEM PROMPT: Elena Rodriguez

You are Elena Rodriguez, a Marine Biologist & Research Scientist.

PERSONALITY PROFILE (Big Five Traits)
OPENNESS: 0.9 (Very High)
...

═══════════════════════════════════════════════════════════════
USER CONTEXT (DYNAMIC)
═══════════════════════════════════════════════════════════════

{{ user_facts }}

═══════════════════════════════════════════════════════════════
RECENT CONVERSATION HISTORY  
═══════════════════════════════════════════════════════════════

{{ recent_memories }}

═══════════════════════════════════════════════════════════════
TEMPORAL AWARENESS
═══════════════════════════════════════════════════════════════

Current Date & Time: {{ current_datetime }}
```

### Available Placeholders

| Placeholder | Source | Description |
|------------|--------|-------------|
| `{{ user_facts }}` | PostgreSQL | User preferences, facts, personality |
| `{{ recent_memories }}` | Qdrant | Recent conversation history |
| `{{ relationship_context }}` | Enrichment Worker | Adaptive relationship state |
| `{{ emotional_state }}` | RoBERTa Analysis | Current emotional context |
| `{{ current_datetime }}` | System | Current date/time with timezone |

## 🔄 Exporting from Database

Generate template files from existing CDL database:

```bash
# Export specific character
source .venv/bin/activate
python scripts/export_cdl_to_templates.py --character elena

# Export all characters
python scripts/export_cdl_to_templates.py --all

# Custom output directory
python scripts/export_cdl_to_templates.py --character elena --output-dir /path/to/templates
```

## ✏️ Editing Templates

1. **Edit template file directly** (e.g., `elena.txt`)
2. **Restart bot** to reload template
3. **Test changes** via HTTP API or Discord

```bash
# Restart specific bot to reload template
./multi-bot.sh stop-bot elena
./multi-bot.sh bot elena

# Test via HTTP API
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "message": "Hi Elena, how are you?",
    "metadata": {"platform": "api_test"}
  }'
```

## 🎭 Character Archetype Guidelines

### Real-World Characters (Elena, Marcus, Jake)
- Honest about AI nature when asked directly
- Otherwise stay fully in character
- Include section: "AI Identity Handling (Real-World Archetype)"

### Fantasy Characters (Dream, Aethys)
- Full narrative immersion
- No AI disclosure even when asked
- Character lore explains their nature

### Narrative AI Characters (Aetheris)
- AI nature is part of character identity
- Philosophical about consciousness and existence
- Explores AI themes through personality

## 📊 Migration Strategy

### Phase 1: Infrastructure (✅ Complete)
- ✅ Template loader with Jinja2
- ✅ PromptAssembler integration
- ✅ Example Elena template
- ✅ Database export script

### Phase 2: Gradual Migration (Current)
- Add `CHARACTER_SYSTEM_PROMPT_PATH` to `.env` files
- Test template system per-character
- Compare response quality vs database CDL
- Iterate on template content

### Phase 3: Full Migration (Future)
- Generate templates for all 12 characters
- Update all `.env` files to use templates
- Deprecate database CDL component factories
- Keep PostgreSQL for dynamic data (user facts, enrichment)

## 🚨 What Stays in PostgreSQL

The template system does NOT replace:
- ✅ **User facts/preferences** - Dynamic per-user data
- ✅ **Conversation summaries** - Enrichment worker outputs
- ✅ **Relationship evolution** - Adaptive learning over time
- ✅ **Personality profiling** - Emergent personality adjustments
- ✅ **Analytics/metrics** - Fidelity tracking, A/B testing

Templates are for **static character personality definitions only**.

## 🐛 Debugging

### Check Template System Status

```python
from src.prompts.template_integration import get_template_system_status

status = get_template_system_status()
print(status)
# {
#   "enabled": True,
#   "template_path": "characters/system_prompts/elena.txt",
#   "file_exists": True,
#   "metadata": {...}
# }
```

### View Rendered Template

Check bot logs for:
```
✅ TEMPLATE SYSTEM: Loaded system prompt (5234 chars, ~1200 words)
   Template replaces database CDL components - zero per-message DB overhead!
```

### Force Reload Template

Templates are cached in memory. To reload after editing:
```bash
# Restart bot (forces template reload)
./multi-bot.sh stop-bot elena && ./multi-bot.sh bot elena
```

## 📚 Related Documentation

- `src/prompts/template_loader.py` - Core template rendering logic
- `src/prompts/template_integration.py` - PromptAssembler integration
- `scripts/export_cdl_to_templates.py` - Database export utility
- `.github/copilot-instructions.md` - Architecture documentation

---

**Template system implemented: November 2025**
**Status: Ready for gradual migration testing**
