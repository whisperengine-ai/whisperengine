# WhisperEngine Prompt Management Guide

## Overview

WhisperEngine now uses a dedicated `prompts/` directory for managing AI personality files. This provides a much more flexible approach than mounting individual files, allowing you to:

- Easily switch between different personalities
- Create and test custom prompts without rebuilding containers
- Manage multiple prompt variations for different use cases
- Hot-reload prompts while the bot is running

## Directory Structure

```
prompts/
├── README.md                           # This documentation
├── default.md                          # Default Dream of the Endless persona
├── dream_ai_enhanced.md               # Enhanced Dream with additional features
├── empathetic_companion_template.md   # Supportive companion mode
├── professional_ai_template.md        # Business/professional assistant
├── casual_friend_template.md          # Casual, friendly conversations
├── character_ai_template.md           # Template for roleplay characters
└── adaptive_ai_template.md            # Self-adapting personality system
```

## Usage Examples

### Docker Environment

Set the environment variable in your `.env` file:

```bash
# Use the enhanced Dream personality
BOT_SYSTEM_PROMPT_FILE=/app/prompts/dream_ai_enhanced.md

# Use professional mode for business Discord servers
BOT_SYSTEM_PROMPT_FILE=/app/prompts/professional_ai_template.md

# Use casual friend mode for gaming servers
BOT_SYSTEM_PROMPT_FILE=/app/prompts/casual_friend_template.md
```

### Docker Compose Override

Create a `docker-compose.override.yml` for temporary personality switching:

```yaml
services:
  discord-bot:
    environment:
      - BOT_SYSTEM_PROMPT_FILE=/app/prompts/empathetic_companion_template.md
```

### Native Python Development

```bash
BOT_SYSTEM_PROMPT_FILE=./prompts/casual_friend_template.md python run.py
```

## Creating Custom Prompts

1. **Create a new file** in the `prompts/` directory:
   ```bash
   touch prompts/my_custom_bot.md
   ```

2. **Use existing templates** as reference. Each prompt should define:
   - Core personality traits
   - Speaking style and tone
   - Knowledge domain focus
   - Interaction preferences

3. **Test your prompt** by updating your environment configuration:
   ```bash
   BOT_SYSTEM_PROMPT_FILE=./prompts/my_custom_bot.md
   ```

4. **Hot-reload** - The bot automatically reloads the prompt file for each conversation

## Advanced Usage

### Conditional Prompts

You can use environment variables in your Docker setup to dynamically select prompts:

```bash
# In your .env file
ENVIRONMENT=development
BOT_SYSTEM_PROMPT_FILE=/app/prompts/${ENVIRONMENT:-default}.md
```

### Per-Server Personalities

Run multiple bot instances with different personalities:

```yaml
# docker-compose.multi-personality.yml
services:
  bot-professional:
    extends:
      file: docker-compose.yml
      service: discord-bot
    environment:
      - BOT_SYSTEM_PROMPT_FILE=/app/prompts/professional_ai_template.md
      - DISCORD_BOT_TOKEN=${PROFESSIONAL_BOT_TOKEN}
    container_name: whisperengine-professional

  bot-casual:
    extends:
      file: docker-compose.yml
      service: discord-bot
    environment:
      - BOT_SYSTEM_PROMPT_FILE=/app/prompts/casual_friend_template.md
      - DISCORD_BOT_TOKEN=${CASUAL_BOT_TOKEN}
    container_name: whisperengine-casual
```

### Development Workflow

For prompt development, use the development compose setup:

```bash
# Start in development mode with prompt hot-reloading
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Edit prompts in your editor
code prompts/my_new_personality.md

# Test immediately - no restart needed!
```

## Migration from Old Setup

If you were previously using the root `system_prompt.md` file:

1. Your existing `system_prompt.md` has been copied to `prompts/default.md`
2. Update your `.env` file to point to the new location:
   ```bash
   # Old
   BOT_SYSTEM_PROMPT_FILE=./system_prompt.md
   
   # New
   BOT_SYSTEM_PROMPT_FILE=./prompts/default.md
   ```
3. The old file mounting still works for backward compatibility, but the new approach is recommended

## Troubleshooting

### Prompt Not Loading
- Check that the file path in `BOT_SYSTEM_PROMPT_FILE` is correct
- Verify the prompts directory is properly mounted in Docker
- Check the container logs for file loading errors

### Permission Issues
- Ensure the prompts directory has read permissions
- In Docker, the directory should be mounted as read-only (`:ro`)

### Hot Reloading Not Working
- Verify you're editing the mounted directory, not a copy
- Check that the file modification time is updating
- The bot reloads prompts per conversation, not per message

## Best Practices

1. **Version Control**: Keep your custom prompts in version control
2. **Backup**: Regularly backup your custom personality files
3. **Testing**: Test prompts in a development environment first
4. **Documentation**: Document your custom prompts with comments
5. **Naming**: Use descriptive filenames that indicate the personality type

## Examples Repository

Check the `examples/` directory for more advanced prompt configurations and integration patterns.