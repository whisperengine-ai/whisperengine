# ⚠️ DEPRECATION NOTICE

This directory (`config/system_prompts/`) is now **legacy** and will be deprecated in future versions.

## 🆕 New Location: `prompts/` Directory

WhisperEngine has moved to a unified `prompts/` directory structure for better organization and management.

### Quick Migration
```bash
# New installations: Use prompts/ automatically
# Existing users: Update your environment variable

# Old
BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/empathetic_companion_template.md

# New
BOT_SYSTEM_PROMPT_FILE=./prompts/empathetic_companion_template.md
```

## 📚 Migration Guide

For complete migration instructions, see:
- **[Migration Guide](../../docs/migration/PROMPT_DIRECTORY_MIGRATION.md)**
- **[Prompt Management Guide](../../docs/configuration/prompt-management.md)**

## 🔄 Backward Compatibility

This directory continues to work during the transition period, but we recommend migrating to the new structure for:
- Better organization
- Hot reloading support
- Improved Docker mounting
- Enhanced documentation

## 🎯 New Features Available in `prompts/`

- **Built-in documentation** (`prompts/README.md`)
- **Hot reloading** - no restart needed for changes
- **Better examples** - including gaming buddy, enhanced Dream persona
- **Unified management** - all prompts in one location
- **Version control friendly** - easier to manage custom prompts

---

**Start using the new `prompts/` directory today!** 🚀