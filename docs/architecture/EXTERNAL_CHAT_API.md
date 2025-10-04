# WhisperEngine External Chat API

This document describes the external HTTP API endpoints that allow external systems to interact with WhisperEngine AI characters using the same sophisticated processing pipeline as Discord.

## Overview

The external chat API provides HTTP endpoints that abstract the complex Discord message processing logic into platform-agnostic endpoints. This allows:

- **External applications** to integrate with WhisperEngine characters
- **Webhooks and bots** to interact with the AI system  
- **Web interfaces** to provide chat functionality
- **Testing and development** with the same processing pipeline

## Key Features

✅ **Shared Processing Pipeline**: Uses the exact same message processing logic as Discord handlers  
✅ **Memory Continuity**: Maintains conversation memory across sessions  
✅ **Character Personalities**: Full CDL (Character Definition Language) integration  
✅ **Security Validation**: Same security scanning as Discord messages  
✅ **Emotion Intelligence**: Advanced emotion analysis and context  
✅ **Platform Agnostic**: Works with any HTTP client  

## API Endpoints

### Base URL
The API endpoints are served on the same port as the health server for each bot:

- **Elena** (Marine Biologist): `http://localhost:9091`
- **Marcus** (AI Researcher): `http://localhost:9092` 
- **Ryan** (Indie Game Developer): `http://localhost:9093`
- **Gabriel** (British Gentleman): `http://localhost:9095`
- **Sophia** (Marketing Executive): `http://localhost:9096`
- And so on...

### 1. Single Message Chat

**Endpoint**: `POST /api/chat`

Send a single message to the AI character and receive a response.

**Request Body**:
```json
{
  "user_id": "string",
  "message": "string",
  "context": {
    "channel_type": "dm|guild",
    "platform": "api", 
    "metadata": {}
  }
}
```

**Response**:
```json
{
  "success": true,
  "response": "AI character response text",
  "processing_time_ms": 1250,
  "memory_stored": true,
  "timestamp": "2024-01-15T10:30:00Z",
  "bot_name": "Elena Rodriguez",
  "metadata": {
    "memory_count": 5,
    "ai_components": {...}
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "message": "Hello! Can you tell me about marine biology?",
    "context": {
      "channel_type": "dm",
      "platform": "api"
    }
  }'
```

### 2. Batch Message Processing

**Endpoint**: `POST /api/chat/batch`

Send multiple messages in a single request (up to 10 messages).

**Request Body**:
```json
{
  "messages": [
    {
      "user_id": "string",
      "message": "string",
      "context": {}
    }
  ]
}
```

**Response**:
```json
{
  "results": [
    {
      "index": 0,
      "user_id": "test_user",
      "success": true,
      "response": "Response text",
      "processing_time_ms": 800,
      "memory_stored": true
    }
  ],
  "total_processed": 1,
  "timestamp": "2024-01-15T10:30:00Z",
  "bot_name": "Elena Rodriguez"
}
```

### 3. Health and Status

**Health Check**: `GET /health`
- Basic health status

**Readiness Check**: `GET /ready`  
- Bot connection status

**Bot Information**: `GET /api/bot-info`
- Bot name, character info, capabilities

**Detailed Status**: `GET /status`
- Complete system status including API endpoints

## Implementation Details

### Message Processing Pipeline

The external API uses the same sophisticated processing pipeline as Discord:

1. **Security Validation** - Content scanning and sanitization
2. **Name Detection** - Automatic user name storage  
3. **Memory Retrieval** - Context-aware memory search
4. **AI Component Processing** - Emotion analysis, context switching
5. **CDL Character Enhancement** - Personality integration
6. **Response Generation** - LLM processing with character context
7. **Response Validation** - Character consistency and security
8. **Memory Storage** - Conversation storage for future context

### Memory Continuity

- **User-specific memory**: Each `user_id` maintains separate conversation history
- **Bot-specific isolation**: Elena's memories stay with Elena, Marcus's with Marcus
- **Cross-session persistence**: Memory persists across API calls
- **Vector-based retrieval**: Semantic search for relevant context

### Character Personalities

Each bot maintains its full CDL personality:

- **Elena Rodriguez**: Marine biologist with warm, educational communication style
- **Marcus Thompson**: AI researcher with analytical, precise responses  
- **Ryan Chen**: Indie game developer with creative, technical expertise
- **Gabriel**: British gentleman with formal, courteous manner
- **Sophia Blake**: Marketing executive with professional, strategic insights

## Usage Examples

### Python with aiohttp
```python
import aiohttp
import asyncio

async def chat_with_elena():
    async with aiohttp.ClientSession() as session:
        payload = {
            "user_id": "python_user",
            "message": "What's the most fascinating marine creature you've studied?",
            "context": {"channel_type": "dm", "platform": "api"}
        }
        
        async with session.post(
            "http://localhost:9091/api/chat",
            json=payload
        ) as response:
            result = await response.json()
            print(f"Elena: {result['response']}")

asyncio.run(chat_with_elena())
```

### JavaScript with fetch
```javascript
async function chatWithMarcus() {
    const response = await fetch('http://localhost:9092/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: 'js_user',
            message: 'What are your thoughts on the latest developments in AI research?',
            context: { channel_type: 'dm', platform: 'api' }
        })
    });
    
    const result = await response.json();
    console.log(`Marcus: ${result.response}`);
}
```

### Testing Script

Use the included test script for interactive testing:

```bash
# Run the test script
python test_external_api.py

# Choose option 1 for endpoint testing
# Choose option 2 for interactive chat
```

## Error Handling

### Common HTTP Status Codes

- **200**: Success - message processed successfully
- **400**: Bad Request - invalid JSON or missing required fields
- **500**: Internal Server Error - processing failed
- **503**: Service Unavailable - bot components not ready

### Error Response Format
```json
{
  "success": false,
  "error": "Error description",
  "message": "Detailed error message",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

Currently no rate limiting is implemented, but consider:

- Reasonable request intervals for production use
- Batch processing for multiple messages
- Monitor bot performance and memory usage

## Security Considerations

- **Input Validation**: All messages go through the same security validation as Discord
- **System Leakage Protection**: Response scanning prevents system information disclosure  
- **Memory Isolation**: User conversations are isolated by user_id and bot instance
- **CORS**: Basic CORS headers are included for web client access

## Integration with Existing Discord Bots

The external API runs alongside existing Discord functionality:

- **Shared Components**: Uses the same memory manager, LLM client, and AI components
- **No Interference**: API calls don't affect Discord message processing
- **Memory Continuity**: API conversations are stored in the same memory system
- **Character Consistency**: Same personality and behavior as Discord interactions

## Development and Testing

1. **Start a bot** using the multi-bot system:
   ```bash
   ./multi-bot.sh start elena
   ```

2. **Test the API** using curl, Postman, or the test script:
   ```bash
   python test_external_api.py
   ```

3. **Check logs** for debugging:
   ```bash
   docker logs whisperengine-elena-bot --tail 50
   ```

## Future Enhancements

- Authentication and API keys
- Rate limiting and quotas  
- WebSocket support for real-time chat
- Streaming responses for long messages
- User session management
- Advanced analytics and metrics