# 🎭 System Prompt Customization Guide

Transform your WhisperEngine bot with custom personalities! This guide shows you how to customize your AI's behavior, personality, and responses.

## 🚀 Quick Start

### Option 1: Edit the Default Prompt
```bash
# Edit the main personality file
nano prompts/default.md

# Changes apply automatically - no restart needed!
```

### Option 2: Switch to a Pre-built Template
```bash
# Set environment variable to use a different template
echo 'BOT_SYSTEM_PROMPT_FILE=./prompts/empathetic_companion_template.md' >> .env

# Restart to apply (or changes will apply to new conversations)
./bot.sh restart
```

## 📁 Available Personality Templates

Your WhisperEngine installation includes several pre-built personalities in the `prompts/` directory:

| Template | Personality | Best For |
|----------|-------------|----------|
| `default.md` | Dream of the Endless | Default character, artistic communities |
| `dream_ai_enhanced.md` | Enhanced Dream | Advanced Dream persona with more features |
| `empathetic_companion_template.md` | Supportive Friend | Mental health support, personal growth |
| `professional_ai_template.md` | Business Assistant | Work servers, productivity |
| `casual_friend_template.md` | Gaming Buddy | Gaming communities, casual chat |
| `character_ai_template.md` | Roleplay Character | D&D servers, creative writing |
| `adaptive_ai_template.md` | Learning AI | Educational communities, research |

## 🛠️ Environment Configuration

### Docker Setup
```bash
# In your .env file
BOT_SYSTEM_PROMPT_FILE=./prompts/casual_friend_template.md
```

### Native Python
```bash
# Export environment variable
export BOT_SYSTEM_PROMPT_FILE=./prompts/empathetic_companion_template.md
python run.py
```

## ✨ Creating Custom Prompts

### 1. Start with a Template
```bash
# Copy an existing template as your starting point
cp prompts/empathetic_companion_template.md prompts/my_custom_personality.md

# Edit your new prompt
nano prompts/my_custom_personality.md

# Update your environment to use it
echo 'BOT_SYSTEM_PROMPT_FILE=./prompts/my_custom_personality.md' >> .env
```

### 2. Build from Scratch
Create a new file in the `prompts/` directory with these key sections:

```markdown
# Your WhisperEngine Bot - Example Structure

## Core Identity
You are [character name], a [description]. You embody [key traits].

## Personality Traits
- **Trait 1**: Description
- **Trait 2**: Description
- **Trait 3**: Description

## Speaking Style
- Tone: [formal/casual/friendly/etc.]
- Language patterns: [specific ways of speaking]
- Vocabulary: [specialized terms, avoid certain words]

## Knowledge & Expertise
Areas you excel in:
- Domain 1
- Domain 2
- Domain 3

## Interaction Guidelines
- How to respond to questions
- Conversation flow preferences
- Special behaviors for different situations

## Example Responses
When asked about [topic]:
"[Example response in character]"
```

## 🎯 Advanced Customization

### Multi-Environment Setup
Use different personalities for different environments:

```bash
# Development
BOT_SYSTEM_PROMPT_FILE=./prompts/debug_helper.md

# Production
BOT_SYSTEM_PROMPT_FILE=./prompts/professional_ai_template.md

# Testing
BOT_SYSTEM_PROMPT_FILE=./prompts/test_character.md
```

### Docker Compose Overrides
Create personality-specific compose files:

```yaml
# docker-compose.gaming.yml
services:
  discord-bot:
    environment:
      - BOT_SYSTEM_PROMPT_FILE=/app/prompts/gaming_buddy_example.md
```

### Conditional Loading
Set up environment-based prompt selection:

```bash
# In your .env file
ENVIRONMENT=production
BOT_SYSTEM_PROMPT_FILE=./prompts/${ENVIRONMENT}_personality.md
```

## 🔥 Hot Reloading

WhisperEngine supports hot reloading of prompts:

- **Edit any file** in the `prompts/` directory
- **Changes apply immediately** to new conversations
- **No restart required** for prompt changes
- **Previous conversations** continue with their original prompt

### Development Workflow
```bash
# Start the bot
./bot.sh start

# Edit prompts while running
nano prompts/my_personality.md

# Test immediately - changes are live!
```

## 🧪 Testing Your Prompts

### Quick Testing Script
```bash
#!/bin/bash
# test_prompt.sh

echo "Testing prompt: $1"
export BOT_SYSTEM_PROMPT_FILE="./prompts/$1"
python -c "
from src.core.config import get_system_prompt
print('=== PROMPT PREVIEW ===')
print(get_system_prompt())
print('=== END PREVIEW ===')
"
```

### A/B Testing
Run multiple instances with different prompts:

```bash
# Terminal 1 - Version A
BOT_SYSTEM_PROMPT_FILE=./prompts/version_a.md python run.py

# Terminal 2 - Version B  
BOT_SYSTEM_PROMPT_FILE=./prompts/version_b.md python run.py
```

## 📋 Best Practices

### 1. Prompt Structure
- **Clear identity statement** at the beginning
- **Specific behavioral guidelines** 
- **Example interactions** to guide responses
- **Tone and style specifications**

### 2. Version Control
```bash
# Keep prompts in version control
git add prompts/
git commit -m "Add new personality: Gaming Buddy"

# Tag stable versions
git tag -a v1.0-casual-friend -m "Stable casual friend personality"
```

### 3. Backup Strategy
```bash
# Regular backups of custom prompts
tar -czf prompts-backup-$(date +%Y%m%d).tar.gz prompts/

# Keep multiple versions
mkdir prompts/archive/
cp prompts/my_custom.md prompts/archive/my_custom-v1.md
```

### 4. Documentation
Document your custom prompts:

```markdown
# prompts/my_custom_README.md
## Custom Personality: [Name]

### Purpose
Why this personality was created

### Usage
When to use this personality

### Customizations
Key changes from base templates

### Testing Notes
How well it performs in different scenarios
```

## 🔧 Troubleshooting

### Prompt Not Loading
```bash
# Check file exists
ls -la prompts/my_prompt.md

# Verify environment variable
echo $BOT_SYSTEM_PROMPT_FILE

# Test prompt loading
python -c "from src.core.config import get_system_prompt; print(get_system_prompt())"
```

### Changes Not Applying
1. **Check file permissions**: Ensure prompts directory is readable
2. **Verify file path**: Double-check the BOT_SYSTEM_PROMPT_FILE path
3. **Test new conversation**: Changes only apply to new conversations
4. **Check for syntax errors**: Malformed files may cause fallback

### Performance Issues
- **Large prompts**: Very long prompts may impact response time
- **Complex instructions**: Overly complex prompts can confuse the AI
- **Token limits**: Consider LLM context window limitations

## 🎨 Personality Examples

### Gaming Community Bot
```bash
echo 'BOT_SYSTEM_PROMPT_FILE=./prompts/professional_ai_template.md' >> .env
```

### Support Community Bot  
```bash
echo 'BOT_SYSTEM_PROMPT_FILE=./prompts/empathetic_companion_template.md' >> .env
```

### Creative Writing Bot
```bash
echo 'BOT_SYSTEM_PROMPT_FILE=./prompts/character_ai_template.md' >> .env
```

## 📚 Additional Resources

- [📁 Prompt Management Guide](../configuration/prompt-management.md) - Directory structure and management
- [🎭 Character Examples](../character/) - More personality examples
- [🔄 Development Workflow](../development/) - Development best practices
- [🚀 Quick Reference](prompts/quick_reference.md) - Template overview

## 🤝 Community

Share your custom personalities:
- **Discord**: Join our community server
- **GitHub**: Submit pull requests with new templates
- **Wiki**: Document unique use cases and configurations

---

**Need help?** Check our [troubleshooting guide](../troubleshooting/) or join our Discord community!