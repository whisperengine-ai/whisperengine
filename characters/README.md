# Characters Directory

This directory contains all Character Definition Language (CDL) files for the WhisperEngine Discord bot. When running in Docker, this entire directory is mounted into the container, allowing you to easily manage and modify characters without rebuilding the image.

## Available Characters

### 🤖 **Default Assistant** (`default_assistant.json`)
A helpful, adaptive AI assistant that provides balanced support and information.

### ✨ **Dream of the Endless** (`examples/dream_of_the_endless.json`)  
The mysterious and enigmatic Dream from Neil Gaiman's The Sandman series.

### 📁 **Examples Directory**
- **Elena Rodriguez** (`examples/elena-rodriguez.json`) - Supportive companion with emotional intelligence
- **Marcus Chen** (`examples/marcus-chen.json`) - Professional business assistant

## Configuration

When running with Docker, set the `CDL_DEFAULT_CHARACTER` environment variable to specify which character to use:

```bash
# Use Dream character
CDL_DEFAULT_CHARACTER=characters/examples/dream_of_the_endless.json

# Use supportive companion
CDL_DEFAULT_CHARACTER=characters/examples/elena-rodriguez.json
```

### Docker Compose Example

```yaml
environment:
  - CDL_DEFAULT_CHARACTER=characters/examples/elena-rodriguez.json
```

### Native Python

```bash
CDL_DEFAULT_CHARACTER=./characters/examples/marcus-chen.json python run.py
```

## Character Definition Language (CDL)

WhisperEngine uses a structured JSON format for character definitions that includes:

- **Metadata** - Character identity, version, and licensing information
- **Core Personality** - Primary traits, values, and behavioral patterns  
- **Communication Style** - Language patterns, tone, and interaction preferences
- **Behavioral Patterns** - Response strategies and adaptive behaviors
- **Memory Integration** - How the character processes and recalls information
- **Relationship Dynamics** - How the character builds and maintains relationships
- **Contextual Adaptability** - Situation-aware response modifications

### Template Variables

CDL characters support automatic template variable replacement:

- `{BOT_NAME}` - Replaced with the Discord bot's display name
- `{USER_NAME}` - Replaced with the user's name (context-dependent)
- `{CURRENT_DATE}` - Replaced with current date
- `{CURRENT_TIME}` - Replaced with current time

## Creating Custom Characters

1. **Start with a Template**: Copy `default_assistant.json` or an example character
2. **Modify Metadata**: Update character_id, name, and description
3. **Customize Personality**: Adjust traits, values, and communication style
4. **Configure Environment**: Set `CDL_DEFAULT_CHARACTER` to point to your new file
5. **Test and Iterate**: Characters reload automatically for real-time testing

### Character Schema

```json
{
  "cdl_version": "1.0",
  "format": "json", 
  "character": {
    "metadata": { ... },
    "core_personality": { ... },
    "communication_style": { ... },
    "behavioral_patterns": { ... },
    "memory_integration": { ... },
    "relationship_dynamics": { ... },
    "contextual_adaptability": { ... }
  }
}
```

## Hot Reload Support

The bot reloads character files dynamically, so you can edit characters while the bot is running and see changes immediately without restarting the container.

## Legacy Prompt System (DEPRECATED)

The old markdown-based prompt system (`prompts/` directory) is deprecated. While still functional, new deployments should use CDL characters for:

- ✅ Structured, validated character definitions
- ✅ Rich personality modeling capabilities  
- ✅ Better maintainability and version control
- ✅ Enhanced relationship dynamics
- ✅ Contextual adaptability features

To migrate from prompts to CDL characters, see the [CDL Migration Guide](../docs/migration/PROMPT_TO_CDL_MIGRATION.md).

## Support Formats

WhisperEngine supports both JSON and YAML formats for CDL characters:

- **JSON**: `character_name.json` (recommended for production)
- **YAML**: `character_name.yaml` (human-friendly for development)

Both formats are automatically detected and parsed correctly.