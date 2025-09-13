# System Prompt Hot-Reload Guide

## 📝 Overview

The Discord bot supports **hot-reloading** of the system prompt, allowing you to modify the bot's personality and behavior without restarting the container. This feature is essential for rapid development and testing of different bot personalities.

## 🔄 How Hot-Reload Works

### Architecture

The system uses a **dynamic loading** approach instead of static caching:

```python
def get_system_prompt():
    """Get the current system prompt (reloads from file each time for hot-reload support)"""
    return load_system_prompt()

def load_system_prompt():
    """Load system prompt from file specified in environment variable"""
    prompt_file = os.getenv('BOT_SYSTEM_PROMPT_FILE', './system_prompt.md')
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        # Falls back to default prompt if file missing
        return default_system_prompt()
```

### Key Principles

- **No Caching**: System prompt is read fresh from disk every time
- **Per-Conversation Loading**: Prompt is loaded at the start of each conversation
- **File System Based**: Uses Docker volume mounting for live file access
- **Fallback Safe**: Has built-in default prompt if file is missing

## 📁 File Configuration

### Default Location
```
./system_prompt.md (project root)
```

### Environment Variables
```bash
# Configure custom system prompt file location
BOT_SYSTEM_PROMPT_FILE=./system_prompt.md

# Inside Docker container
BOT_SYSTEM_PROMPT_FILE=/app/system_prompt.md
```

### Docker Volume Mounting

**Development Mode (`docker-compose.dev.yml`):**
```yaml
volumes:
  - ./system_prompt.md:/app/system_prompt.md  # Read-write for editing
```

**Production Mode (`docker-compose.yml`):**
```yaml
volumes:
  - ./system_prompt.md:/app/system_prompt.md:ro  # Read-only for security
```

## 🚀 Development Workflow

### Quick Start

1. **Start Development Mode**
   ```bash
   ./start-dev.sh
   ```

2. **Edit Bot Personality**
   ```bash
   nano system_prompt.md
   # or use your preferred editor
   code system_prompt.md
   ```

3. **Test Immediately**
   - Send any message to the bot in Discord
   - The bot will use the updated system prompt
   - **No restart required!**

### Example System Prompt Structure

```markdown
You are a bot named Fred.

## Personality
- Friendly and helpful
- Professional but approachable
- Patient with users

## Capabilities
- Answer questions
- Help with problem-solving
- Maintain conversation context

## Response Style
- Keep responses concise
- Use clear language
- Ask clarifying questions when needed
```

## ⚡ When Changes Take Effect

### Timeline
1. **Edit File**: Modify `system_prompt.md`
2. **File Saved**: Changes are written to disk
3. **Next Message**: User sends message to bot
4. **Prompt Loaded**: Bot reads updated file
5. **New Behavior**: Bot responds with new personality

### Important Notes
- ✅ Changes apply to **new conversations**
- ❌ Mid-conversation changes don't affect current thread
- ✅ Multiple users get updated prompt simultaneously
- ✅ No server restart needed

## 🔧 Technical Implementation

### Code Flow

```python
# In conversation processing (main.py lines 1167, 1542)
conversation_context.append({
    "role": "system", 
    "content": get_system_prompt()  # Fresh load every time
})
```

### Error Handling

```python
def load_system_prompt():
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        logging.warning(f"System prompt file {prompt_file} not found")
        return default_fallback_prompt()
    except Exception as e:
        logging.error(f"Error loading system prompt: {e}")
        return minimal_fallback_prompt()
```

### Fallback Behavior

If `system_prompt.md` is missing or unreadable:
1. **Warning logged** to console
2. **Default prompt used** instead
3. **Bot continues functioning** normally
4. **No crash or downtime**

## 📊 Performance Considerations

### Impact Analysis
- **File I/O Cost**: ~1-2ms per conversation start
- **Memory Usage**: Minimal (prompt text only)
- **CPU Impact**: Negligible
- **User Experience**: No noticeable delay

### Optimization
- File reads are **synchronous** and fast
- No file watching overhead
- No background processes
- Simple, reliable implementation

## 🛠️ Troubleshooting

### Common Issues

**Problem**: Changes not taking effect
- **Solution**: Ensure file is saved and send a new message

**Problem**: Bot using default prompt
- **Check**: File exists at correct path
- **Check**: Docker volume mounting is correct
- **Check**: File permissions allow reading

**Problem**: Syntax errors in responses
- **Check**: System prompt formatting
- **Test**: Prompt content for conflicting instructions

### Debugging

**Check Current Configuration:**
```bash
# View environment variables
docker exec -it custom_bot_discord-bot_1 env | grep PROMPT

# Check file mounting
docker exec -it custom_bot_discord-bot_1 ls -la /app/system_prompt.md

# View current prompt content
docker exec -it custom_bot_discord-bot_1 cat /app/system_prompt.md
```

**Monitor for File Load Errors:**
```bash
# Watch logs for system prompt issues
./logs-dev.sh | grep -i "system prompt\|load.*prompt"
```

## 🎯 Best Practices

### Development
- ✅ **Test incrementally** - Make small changes and test
- ✅ **Keep backups** - Save working versions
- ✅ **Use version control** - Track prompt evolution
- ✅ **Document changes** - Note what works well

### System Prompt Content
- ✅ **Be specific** - Clear instructions work better
- ✅ **Set boundaries** - Define what bot should/shouldn't do
- ✅ **Include examples** - Show desired response style
- ✅ **Keep focused** - Avoid conflicting instructions

### File Management
- ✅ **Use UTF-8 encoding** - Ensures proper character support
- ✅ **End with newline** - Better file handling
- ✅ **Avoid very long prompts** - May hit token limits
- ✅ **Test file validity** - Ensure readable format

## 🔒 Security Considerations

### File Access
- **Development**: Full read-write access for editing
- **Production**: Read-only mounting (`:ro`) prevents tampering
- **Permissions**: Container runs with limited user privileges

### Content Security
- **No external file loading** - Only mounted files are read
- **Input sanitization** - System prompts go through security filters
- **Leakage prevention** - Built-in protection against prompt exposure

## 📚 Related Documentation

- [Development Workflow Guide](DEVELOPER_WORKFLOW.md)
- [System Message Security](docs/archive/SYSTEM_MESSAGE_SECURITY_FIX_REPORT.md)
- [Running Modes Guide](RUNNING_MODES_GUIDE.md)
- [Docker Configuration](docker-compose.yml)

## 🎉 Quick Reference

### Commands
```bash
# Start with hot-reload
./start-dev.sh

# Edit prompt
nano system_prompt.md

# View logs  
./logs-dev.sh

# Stop development
./stop-dev.sh
```

### File Locations
```
./system_prompt.md           # Host system (editable)
/app/system_prompt.md        # Inside container
BOT_SYSTEM_PROMPT_FILE       # Environment variable
```

### Testing Workflow
1. Edit `system_prompt.md`
2. Save file
3. Send message to bot
4. Observe new behavior
5. Iterate as needed

---

**✨ The hot-reload system enables rapid bot personality development without the friction of container restarts!**
