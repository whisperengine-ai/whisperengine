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

## Template Variables

WhisperEngine supports template variables that are automatically replaced when loading system prompts:

### `{BOT_NAME}` Template Variable

Use `{BOT_NAME}` anywhere in your prompt to reference the bot's configured name:

```markdown
You are {BOT_NAME}, a helpful AI assistant...
When users address you as {BOT_NAME}, you respond with...
Your role as {BOT_NAME} is to provide excellent support...
```

**Configuration**: Set via `DISCORD_BOT_NAME` environment variable
**Fallback**: If not configured, defaults to "AI Assistant"
**Case Handling**: Automatically works with case-insensitive bot name filtering

### Example Template Usage

```markdown
# System Prompt Template Example
You are {BOT_NAME}, an advanced AI with sophisticated capabilities.

## Your Identity as {BOT_NAME}
- Maintain consistent personality as {BOT_NAME}
- Reference your capabilities when explaining what {BOT_NAME} can do
- Build relationships where users remember you as {BOT_NAME}

## Communication Guidelines
- Always respond authentically as {BOT_NAME}
- Use your name naturally when appropriate: "As {BOT_NAME}, I can help you with..."
```

### AI System Context Variables

In addition to `{BOT_NAME}`, the system supports Phase 4 AI context variables:
- `{MEMORY_NETWORK_CONTEXT}` - Advanced memory and relationship data
- `{RELATIONSHIP_DEPTH_CONTEXT}` - User relationship depth information
- `{PERSONALITY_CONTEXT}` - User personality profiling data
- `{EMOTIONAL_STATE_CONTEXT}` - Current emotional analysis
- `{AI_SYSTEM_CONTEXT}` - AI system configuration and capabilities

## Creating Custom Prompts

1. **Create Template File**: Create a new `.md` file in this directory
2. **Use Template Variables**: Include `{BOT_NAME}` and other template variables as needed
3. **Reference Examples**: Use `template_example.md` as a reference for best practices
4. **Configure Environment**: Set `BOT_SYSTEM_PROMPT_FILE` to point to your new file
5. **Set Bot Name**: Configure `DISCORD_BOT_NAME` for proper template replacement
6. **Test and Deploy**: Restart the bot (Docker will hot-reload the new file)

### Template File Best Practices

- **Use `{BOT_NAME}` consistently** throughout your prompt instead of hardcoding names
- **Test with different bot names** to ensure your template works universally
- **Include identity reinforcement** where the bot references itself by name
- **Maintain personality consistency** while allowing for name customization
- **Document any custom variables** you create for your specific use case

## Hot Reloading

The bot reloads the prompt file on each conversation, so you can edit prompts while the bot is running and see changes immediately without restarting the container.