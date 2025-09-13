# Prompts Directory

This directory contains all system prompts for the WhisperEngine Discord bot. When running in Docker, this entire directory is mounted into the container, allowing you to easily manage and modify prompts without rebuilding the image.

## Available Prompts

- `default.md` - The default Dream of the Endless persona (production ready)
- `dream_ai_enhanced.md` - Enhanced Dream persona with additional features
- `character_ai_template.md` - Template for character-based AI interactions
- `empathetic_companion_template.md` - Compassionate companion mode
- `professional_ai_template.md` - Professional assistant mode
- `casual_friend_template.md` - Casual, friendly conversational mode
- `adaptive_ai_template.md` - Adaptive personality system template

## Usage

### Docker Environment

When running with Docker, set the `BOT_SYSTEM_PROMPT_FILE` environment variable to specify which prompt to use:

```bash
# In your .env file
BOT_SYSTEM_PROMPT_FILE=/app/prompts/dream_ai_enhanced.md
```

Or via Docker Compose override:

```yaml
services:
  whisperengine-bot:
    environment:
      - BOT_SYSTEM_PROMPT_FILE=/app/prompts/empathetic_companion_template.md
```

### Native Python

When running natively, use relative paths:

```bash
BOT_SYSTEM_PROMPT_FILE=./prompts/casual_friend_template.md python run.py
```

## Creating Custom Prompts

1. Create a new `.md` file in this directory
2. Use existing templates as reference
3. Update your environment configuration to point to the new file
4. Restart the bot (Docker will hot-reload the new file)

## Hot Reloading

The bot reloads the prompt file on each conversation, so you can edit prompts while the bot is running and see changes immediately without restarting the container.