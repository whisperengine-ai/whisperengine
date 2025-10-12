# Prompt Logging Configuration

## Overview

WhisperEngine includes comprehensive prompt logging that captures every prompt sent to the LLM and every response received. This feature is **disabled by default** for production deployments to reduce disk I/O and protect user privacy.

## Configuration

### Environment Variable

```bash
ENABLE_PROMPT_LOGGING=false  # Default: disabled for production
```

### Enabling Prompt Logging

For development and debugging, enable prompt logging:

```bash
# In your .env.botname file
ENABLE_PROMPT_LOGGING=true
```

### Log Location

Prompt logs are stored in:
- **Docker**: `/app/logs/prompts/`
- **Local**: `logs/prompts/` (if volume mounted)

### File Format

**Pattern**: `{BotName}_{YYYYMMDD}_{HHMMSS}_{UserID}.json`

**Example**: `Elena_20251004_205238_672814231002939413.json`

## Log Contents

Each prompt log file contains:

```json
{
  "timestamp": "2025-10-12T14:30:45.123456",
  "bot_name": "Elena",
  "user_id": "672814231002939413",
  "message_count": 12,
  "total_chars": 4523,
  "messages": [
    {
      "role": "system",
      "content": "System prompt with CDL character integration..."
    },
    {
      "role": "user",
      "content": "User message..."
    },
    {
      "role": "assistant",
      "content": "Bot response..."
    }
  ],
  "ai_components": {
    "emotion_analysis": {},
    "phase4_intelligence": {},
    "conversation_patterns": {}
  },
  "llm_response": {
    "content": "Generated response from LLM...",
    "timestamp": "2025-10-12T14:30:46.789012",
    "char_count": 234
  }
}
```

## Use Cases

### Development
- **Debugging conversation issues**: See exactly what context was sent to LLM
- **Validating feature integration**: Confirm new features appear in system prompts
- **Testing CDL integration**: Verify character personality is properly injected
- **Analyzing conversation flow**: Review complete conversation history

### Production
- **Disabled by default**: Reduces disk I/O overhead
- **Privacy protection**: Prevents logging sensitive user conversations
- **Performance**: Eliminates file system operations for each message

## Debugging Workflow

When troubleshooting conversation issues with prompt logging enabled:

```bash
# 1. Check recent logs for a specific bot
ls -la logs/prompts/Elena_* | tail -5

# 2. View a specific conversation
cat logs/prompts/Elena_20251012_143045_672814231002939413.json | jq '.'

# 3. Check system prompt integration
cat logs/prompts/Elena_LATEST.json | jq '.messages[0].content' | head -50

# 4. Verify AI components data
cat logs/prompts/Elena_LATEST.json | jq '.ai_components'

# 5. Compare user message vs LLM response
cat logs/prompts/Elena_LATEST.json | jq '.messages[-1].content, .llm_response.content'
```

## Performance Impact

### With Logging Enabled
- **Disk I/O**: ~1-5KB per message (varies by conversation context size)
- **Latency**: Negligible (<5ms) - async file operations
- **Storage**: Can accumulate quickly (monitor disk usage)

### With Logging Disabled (Default)
- **Disk I/O**: Zero overhead
- **Latency**: No impact
- **Storage**: No accumulation

## Best Practices

### Development Environment
```bash
# Enable for all development bots
ENABLE_PROMPT_LOGGING=true
```

### Staging Environment
```bash
# Enable for testing/debugging specific issues
ENABLE_PROMPT_LOGGING=true  # Set temporarily
```

### Production Environment
```bash
# Keep disabled unless actively debugging
ENABLE_PROMPT_LOGGING=false  # Default
```

### Disk Management

If enabling in production temporarily:

```bash
# Monitor disk usage
du -sh /app/logs/prompts/

# Clean old logs (example: older than 7 days)
find /app/logs/prompts/ -type f -mtime +7 -delete

# Archive before cleaning
tar -czf prompts_archive_$(date +%Y%m%d).tar.gz logs/prompts/
```

## Security Considerations

### Sensitive Data
Prompt logs contain:
- Full conversation history
- User messages (may include personal information)
- System prompts with character configuration
- AI component metadata
- LLM responses

### Recommendations
1. **Disable in production** unless actively debugging
2. **Restrict access** to logs directory (proper file permissions)
3. **Regular cleanup** of old log files
4. **Secure storage** if archiving logs
5. **GDPR compliance**: Consider user consent for logging in production

## Migration Notes

### Upgrading from Previous Versions

Previous versions had prompt logging **always enabled**. After upgrading:

1. **Default behavior changes**: Logging is now OFF by default
2. **Update .env files**: Add `ENABLE_PROMPT_LOGGING=true` if you want logging
3. **Update documentation**: Notify team of new default behavior
4. **Clean existing logs**: Archive or remove old prompt logs as needed

### Backward Compatibility

The change is backward compatible:
- Existing code continues to work
- Log format unchanged
- No breaking changes to log file structure
- Environment variable simply gates the logging calls

## Troubleshooting

### Logs Not Appearing
```bash
# Check environment variable
echo $ENABLE_PROMPT_LOGGING

# Verify it's set to "true" (case-insensitive)
grep ENABLE_PROMPT_LOGGING .env.botname

# Check logs directory exists and is writable
ls -la /app/logs/prompts/
```

### Logs Directory Permission Issues
```bash
# Ensure directory exists and has correct permissions
mkdir -p /app/logs/prompts
chmod 755 /app/logs/prompts
```

### Excessive Disk Usage
```bash
# Check current usage
du -sh /app/logs/prompts/

# Count log files
find /app/logs/prompts/ -type f | wc -l

# Disable logging if not needed
ENABLE_PROMPT_LOGGING=false
```

## Related Documentation

- [WhisperEngine Architecture](../architecture/WHISPERENGINE_ARCHITECTURE_EVOLUTION.md)
- [Message Processing Pipeline](../architecture/MESSAGE_PROCESSING_PIPELINE.md)
- [CDL Integration](../cdl-system/CDL_AI_INTEGRATION.md)
- [Environment Configuration](/.env.template)
