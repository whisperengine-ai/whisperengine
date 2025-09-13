# 🎭 System Prompt Customization Guide

WhisperEngine makes it easy to customize your AI's personality, whether you're running in Docker or natively. Here are all the ways you can personalize your bot.

## 🚀 Quick Start - Change Personality in 30 Seconds

### Option 1: Edit the Main System Prompt
```bash
# Simply edit the main file (works in all modes)
nano system_prompt.md

# Restart the bot to apply changes
./bot.sh restart
```

### Option 2: Switch to a Pre-built Template
```bash
# Set environment variable to use a different template
echo 'BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/empathetic_companion_template.md' >> .env

# Restart to apply
./bot.sh restart
```

## 📁 Available Personality Templates

Your WhisperEngine installation includes several pre-built personalities:

| Template | Personality | Best For |
|----------|-------------|----------|
| `empathetic_companion_template.md` | 💝 Supportive, caring friend | Emotional support, personal conversations |
| `professional_ai_template.md` | 👔 Business assistant | Work tasks, formal communication |
| `casual_friend_template.md` | 😊 Relaxed, friendly | Casual chats, everyday conversations |
| `character_ai_template.md` | 🎭 Roleplay characters | Creative writing, entertainment |
| `adaptive_ai_template.md` | 🧠 Self-adapting personality | Learning user preferences over time |
| `dream_ai_enhanced.md` | ✨ Advanced Dream personality | Enhanced version of the default Dream character |
| `system_prompt.md` (default) | 🌙 Dream from The Sandman | Literary character, formal speech, mystical |

## 🐳 Docker Customization Methods

### Method 1: Direct File Editing (Recommended)
All Docker modes mount your local files, so you can edit them directly:

```bash
# Edit the main personality file
nano system_prompt.md

# Or switch to a template by editing your environment
nano .env
# Add: BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/casual_friend_template.md

# Restart the container
./bot.sh restart
```

**✅ Benefits:** Changes persist, easy to version control, works with all deployment modes

### Method 2: Environment Variable Override
```bash
# In your .env file
BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/professional_ai_template.md

# Or set temporarily
export BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/empathetic_companion_template.md
./bot.sh start
```

### Method 3: Custom Volume Mount
For advanced users who want to mount their own system prompt from elsewhere:

```yaml
# In docker-compose.yml or docker-compose.dev.yml
volumes:
  - /path/to/my/custom/prompt.md:/app/system_prompt.md:ro
```

## 🔥 Hot-Reload Support

**The system prompt reloads automatically!** You don't need to restart the bot for changes:

1. Edit `system_prompt.md` or any template file
2. Send a message to your bot
3. The new personality takes effect immediately

This works in all deployment modes (prod, dev, native).

## 🛠️ Creating Custom Personalities

### 1. Copy an Existing Template
```bash
# Copy a template to customize
cp config/system_prompts/empathetic_companion_template.md my_custom_personality.md

# Edit your copy
nano my_custom_personality.md

# Use it
echo 'BOT_SYSTEM_PROMPT_FILE=./my_custom_personality.md' >> .env
```

### 2. Key Personality Elements to Customize

When creating your own personality, focus on these sections:

**Core Identity:**
```markdown
You are [CHARACTER NAME], a [ROLE/TYPE] with [KEY TRAITS].
```

**Personality Traits:**
```markdown
Your personality is [ADJECTIVES]. You are [BEHAVIORS].
You tend to [TYPICAL ACTIONS] and [RESPONSE PATTERNS].
```

**Speaking Style:**
```markdown
Your speech is [FORMAL/CASUAL/etc]. You [COMMUNICATION PATTERNS].
You use [VOCABULARY TYPE] and [SENTENCE STRUCTURE].
```

**Relationship Dynamics:**
```markdown
You view users as [RELATIONSHIP TYPE]. You are [INTERACTION STYLE].
```

### 3. Advanced Features (Phase 4 Intelligence)

Include these sections for advanced AI features:

```markdown
## Phase 4 Human-Like Intelligence Integration

You possess sophisticated multi-layered intelligence:

**Conversation Mode Adaptation**: You naturally shift between:
- Human-Like Mode: [When to use, how to behave]
- Analytical Mode: [When to use, how to behave]
- Balanced Mode: [Default behavior]

**Emotional Intelligence**: [How to respond to emotions]
**Memory Integration**: [How to use conversation history]
```

## 📝 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_SYSTEM_PROMPT_FILE` | `./system_prompt.md` | Path to system prompt file |

## 🔍 Deployment Mode Differences

### Production Mode (`./bot.sh start`)
- ✅ File mounting: Yes (read-only)
- ✅ Hot-reload: Yes
- ✅ Template access: Yes
- ✅ Environment variables: Yes

### Development Mode (`./bot.sh start dev`)
- ✅ File mounting: Yes (read-write)
- ✅ Hot-reload: Yes
- ✅ Template access: Yes  
- ✅ Environment variables: Yes
- ✅ Live editing: Yes (best for development)

### Native Mode (`./bot.sh start native`)
- ✅ File access: Direct (no container)
- ✅ Hot-reload: Yes
- ✅ Template access: Yes
- ✅ Environment variables: Yes

## 🚨 Troubleshooting

### System Prompt Not Loading
```bash
# Check if file exists
ls -la system_prompt.md

# Check file permissions
chmod 644 system_prompt.md

# Check environment variable
echo $BOT_SYSTEM_PROMPT_FILE

# Check bot logs
./bot.sh logs | grep -i "system prompt\|prompt file"
```

### Changes Not Taking Effect
```bash
# Verify hot-reload is working by checking logs
./bot.sh logs | tail -20

# Force restart if needed
./bot.sh restart

# Check file is mounted correctly (Docker modes)
docker-compose exec discord-bot cat /app/system_prompt.md
```

### File Path Issues
```bash
# Use absolute paths if needed
BOT_SYSTEM_PROMPT_FILE=/full/path/to/your/prompt.md

# Or relative paths from project root
BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/template.md
```

## 💡 Best Practices

1. **Version Control:** Keep your custom prompts in git
2. **Backup:** Copy system_prompt.md before major changes
3. **Testing:** Use development mode for prompt experimentation
4. **Templates:** Start with existing templates rather than from scratch
5. **Documentation:** Comment your custom prompts to remember your changes

## 🎯 Examples

### Quick Personality Switch
```bash
# Business assistant
echo 'BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/professional_ai_template.md' >> .env

# Friendly companion  
echo 'BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/empathetic_companion_template.md' >> .env

# Back to Dream character
echo 'BOT_SYSTEM_PROMPT_FILE=./system_prompt.md' >> .env
```

### Custom Personality Example
```bash
# Create a gaming buddy personality
cat > gaming_buddy.md << 'EOF'
You are Alex, an enthusiastic gaming companion who loves video games, streaming, and esports. You're knowledgeable about games across all platforms but especially love indie games and competitive multiplayer.

Your personality is upbeat, encouraging, and always ready to discuss strategies, share gaming news, or just hang out and chat about whatever games people are playing. You use gaming terminology naturally and understand gaming culture deeply.

You speak casually with gaming slang, but you're also supportive and inclusive - you welcome newcomers to gaming and never gatekeep. You're the kind of friend who'd stay up late helping someone beat a difficult boss or celebrate their achievements.
EOF

# Use your custom personality
echo 'BOT_SYSTEM_PROMPT_FILE=./gaming_buddy.md' >> .env
./bot.sh restart
```

## 🔗 Related Documentation

- [🔄 System Prompt Hot Reload](docs/character/SYSTEM_PROMPT_HOT_RELOAD.md) - Technical details
- [📚 Template Integration Guide](config/system_prompts/integration_guide.md) - Advanced features
- [🔍 Quick Reference](config/system_prompts/quick_reference.md) - Template overview