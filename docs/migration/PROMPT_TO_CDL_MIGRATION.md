# Prompt to CDL Migration Guide

This guide helps you migrate from the legacy markdown-based prompt system to the new Character Definition Language (CDL) system.

## Overview

WhisperEngine has evolved from simple prompt files to structured character definitions:

**Old System (Deprecated)**:
- Markdown files in `prompts/` directory
- `BOT_SYSTEM_PROMPT_FILE` environment variable
- Simple text-based personality definitions

**New System (Current)**:
- JSON/YAML files in `characters/` directory  
- `CDL_DEFAULT_CHARACTER` environment variable
- Structured character definitions with rich metadata

## Quick Migration Steps

### 1. Update Environment Variables

**Replace this:**
```bash
BOT_SYSTEM_PROMPT_FILE=./prompts/default.md
```

**With this:**
```bash
CDL_DEFAULT_CHARACTER=characters/default_assistant.json
```

### 2. Update Docker Compose Files

**Replace this:**
```yaml
volumes:
  - ./prompts:/app/prompts:ro
environment:
  - BOT_SYSTEM_PROMPT_FILE=/app/prompts/default.md
```

**With this:**
```yaml
volumes:
  - ./characters:/app/characters:ro
environment:
  - CDL_DEFAULT_CHARACTER=characters/default_assistant.json
```

### 3. Update Dockerfile (if custom)

**Replace this:**
```dockerfile
COPY prompts/ ./prompts/
```

**With this:**
```dockerfile
COPY characters/ ./characters/
```

## Character Mapping

| Legacy Prompt File | CDL Character Equivalent |
|-------------------|-------------------------|
| `prompts/default.md` | `characters/default_assistant.json` |
| `prompts/dream_ai_enhanced.md` | `characters/examples/dream_of_the_endless.json` |
| `prompts/empathetic_companion_template.md` | `characters/examples/elena-rodriguez.json` |
| `prompts/professional_ai_template.md` | `characters/examples/marcus-chen.json` |

## Converting Custom Prompts

### 1. Extract Core Information

From your markdown prompt, identify:
- Character name and description
- Core personality traits
- Communication style preferences
- Behavioral patterns
- Relationship approach

### 2. Create CDL Structure

Start with the default template:

```json
{
  "cdl_version": "1.0",
  "format": "json",
  "description": "Your character description",
  "character": {
    "metadata": {
      "character_id": "your-character-id",
      "name": "Character Name",
      "version": "1.0.0",
      "created_by": "Your Name",
      "created_date": "2025-09-21T00:00:00Z",
      "license": "open",
      "tags": ["assistant", "helpful", "custom"]
    },
    "core_personality": {
      "primary_traits": [
        "Extract traits from your prompt"
      ],
      "values_and_beliefs": [
        "Extract values from your prompt"
      ]
    }
  }
}
```

### 3. Map Prompt Content

**Markdown Prompt Example:**
```markdown
You are Dream, the anthropomorphic personification of dreams...
You speak in a formal, archaic manner...
You are both caring and distant...
```

**CDL Equivalent:**
```json
{
  "character": {
    "metadata": {
      "name": "Dream of the Endless"
    },
    "core_personality": {
      "primary_traits": ["formal", "archaic", "mysterious"]
    },
    "communication_style": {
      "tone": "formal and archaic",
      "formality_level": "high"
    },
    "relationship_dynamics": {
      "approach": "caring yet distant"
    }
  }
}
```

## Validation

After creating your CDL character:

1. **Syntax Check**: Validate JSON syntax
2. **Test Load**: Set `CDL_DEFAULT_CHARACTER` and restart bot
3. **Behavior Test**: Interact with the bot to verify personality
4. **Refinement**: Adjust character definition as needed

## Advanced Features

CDL provides features not available in markdown prompts:

### Memory Integration
```json
"memory_integration": {
  "importance_weighting": {
    "emotional_moments": 0.9,
    "personal_details": 0.8,
    "casual_conversation": 0.3
  }
}
```

### Contextual Adaptability
```json
"contextual_adaptability": {
  "conversation_starters": {
    "first_interaction": "Welcome message for new users",
    "returning_user": "Greeting for known users"
  }
}
```

### Relationship Dynamics
```json
"relationship_dynamics": {
  "relationship_building": {
    "approach": "gradual",
    "trust_development": "through consistent interactions"
  }
}
```

## Troubleshooting

### Character Not Loading
1. Check JSON syntax with a validator
2. Verify file path in `CDL_DEFAULT_CHARACTER`
3. Ensure characters directory is mounted in Docker
4. Check bot logs for parsing errors

### Personality Not Matching
1. Review `core_personality` section
2. Adjust `communication_style` parameters
3. Test with small conversation samples
4. Iterate on character definition

### Performance Issues
1. Keep character files under 50KB
2. Avoid deeply nested structures
3. Use concise descriptions
4. Cache frequently accessed characters

## Migration Checklist

- [ ] Update environment variables
- [ ] Update docker-compose files
- [ ] Create CDL character files
- [ ] Update custom Dockerfiles
- [ ] Test character loading
- [ ] Verify personality behavior
- [ ] Update documentation
- [ ] Remove old prompt dependencies

## Support

For migration assistance:
- Review existing CDL examples in `characters/examples/`
- Check the [CDL specification](../characters/CHARACTER_DESIGN_LANGUAGE_PROPOSAL.md)
- Test with the provided default characters
- Use the [character validation tools](../scripts/validate_cdl.py)

## Future Deprecation Timeline

- **Phase 1** (Current): CDL system available, prompts deprecated but functional
- **Phase 2** (Future): Prompt system marked for removal, warnings added
- **Phase 3** (Future): Prompt system removed, CDL only

Migrate now to ensure compatibility with future WhisperEngine versions.