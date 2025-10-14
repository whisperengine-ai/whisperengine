# WhisperEngine API Quick Reference

**TL;DR**: Send POST requests to character bots, get AI responses with emotional intelligence and persistent memory.

## 30-Second Integration

```javascript
// Send a message to Elena (Marine Biologist)
const response = await fetch('http://localhost:9091/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'your_user_123',
    message: 'Tell me about coral reefs'
  })
});

const data = await response.json();
console.log(data.response);  // Elena's response about coral reefs
```

**That's it!** Character remembers the conversation for future messages from same `user_id`.

## Character Endpoints

| Character | Port | URL |
|-----------|------|-----|
| Elena (Marine Biologist) | 9091 | `http://localhost:9091/api/chat` |
| Marcus (AI Researcher) | 9092 | `http://localhost:9092/api/chat` |
| Ryan (Game Dev) | 9093 | `http://localhost:9093/api/chat` |
| Dream (Mythological) | 9094 | `http://localhost:9094/api/chat` |
| Gabriel (Gentleman) | 9095 | `http://localhost:9095/api/chat` |
| Sophia (Marketing) | 9096 | `http://localhost:9096/api/chat` |
| Jake (Photographer) | 9097 | `http://localhost:9097/api/chat` |

## Request Format

```json
{
  "user_id": "unique_user_identifier",  // REQUIRED - for memory
  "message": "Your message text",       // REQUIRED
  "metadata_level": "basic|standard|extended"  // OPTIONAL (default: standard)
}
```

## Response Format

### Basic Response (default)
```json
{
  "success": true,
  "response": "Character's reply...",
  "processing_time_ms": 1250,
  "memory_stored": true
}
```

### With Emotion Data (`metadata_level: "standard"`)
```json
{
  "success": true,
  "response": "Character's reply...",
  "metadata": {
    "ai_components": {
      "emotion_data": {
        "primary_emotion": "joy",
        "intensity": 0.85
      },
      "bot_emotion": {
        "primary_emotion": "curiosity", 
        "intensity": 0.72
      }
    }
  }
}
```

## Metadata Levels

| Level | Size | Use Case |
|-------|------|----------|
| `basic` | ~200 bytes | Mobile apps, webhooks |
| `standard` | ~5-10 KB | Production apps (DEFAULT) |
| `extended` | ~20-50 KB | Analytics dashboards |

## Common Patterns

### Multi-Character Conversation
```javascript
// User talks to Elena about ocean
await fetch('http://localhost:9091/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 'user_123',
    message: 'Tell me about dolphins'
  })
});

// Same user talks to Marcus about AI  
await fetch('http://localhost:9092/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 'user_123',
    message: 'Explain neural networks'
  })
});
```

Each character has independent memory of the user.

### Batch Processing
```javascript
// Process multiple users at once
await fetch('http://localhost:9091/api/chat/batch', {
  method: 'POST',
  body: JSON.stringify({
    metadata_level: 'basic',
    messages: [
      { user_id: 'user1', message: 'Hello' },
      { user_id: 'user2', message: 'Hi' },
      { user_id: 'user3', message: 'Hey' }
    ]
  })
});
```

Max 10 messages per batch.

## Error Handling

```javascript
try {
  const response = await fetch('http://localhost:9091/api/chat', {
    method: 'POST',
    body: JSON.stringify({ user_id: 'user123', message: 'Hello' })
  });
  
  const data = await response.json();
  
  if (data.success) {
    console.log(data.response);
  } else {
    console.error('API error:', data.error);
    // data.response still contains fallback message
    console.log('Fallback:', data.response);
  }
  
} catch (error) {
  console.error('Network error:', error);
}
```

## Testing

```bash
# Check if bot is ready
curl http://localhost:9091/health

# Send test message
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"Hello"}'
```

## Key Concepts

### User ID
- **Must be unique per user** - used for memory/relationships
- **Must be consistent** - same user_id across sessions
- Recommend: platform user ID, database ID, UUID

### Memory
- Automatically stored per conversation
- Character-specific (Elena's memories ≠ Marcus's memories)  
- Persists across sessions with same user_id

### Character Personalities
- Each bot has unique personality (CDL system)
- Responds according to their expertise/personality
- Elena = marine biology, Marcus = AI research, etc.

## Common Mistakes

❌ **DON'T**:
- Use random/temporary user IDs (breaks memory)
- Send messages without user_id
- Mix up character ports
- Expect instant responses (1-2s processing time)

✅ **DO**:
- Use consistent, unique user_ids
- Handle both success and error cases
- Choose appropriate metadata_level
- Wait for bot initialization (30-60s after start)

## Next Steps

**Need more details?** See [Complete API Reference](./CHAT_API_REFERENCE.md)

**Need help?** See [Troubleshooting Guide](./CHAT_API_REFERENCE.md#troubleshooting)

**Want examples?** See [Integration Examples](./CHAT_API_REFERENCE.md#integration-examples)

---

**That's all you need to get started!** 🚀
