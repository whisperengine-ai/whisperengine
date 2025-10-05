# WhisperEngine Health Check API

**⚠️ IMPORTANT: WhisperEngine is a Discord-only bot system. Chat functionality requires Discord messages sent directly to the bots.**

This document describes the HTTP health check endpoints used for container orchestration and debugging. These endpoints do NOT provide chat functionality - they are for monitoring bot health only.

## Overview

The health check API provides HTTP endpoints for:

- **Container orchestration** - Docker health monitoring
- **Bot status validation** - Verify bots are running
- **Development debugging** - Check bot initialization
- **Monitoring systems** - Integration with external monitoring

⚠️ **No Chat Endpoints**: WhisperEngine removed all HTTP chat APIs. All conversation features require Discord messages sent directly to the character bots.

## Key Features

✅ **Health Monitoring**: Container health status for Docker orchestration  
✅ **Bot Status**: Verify bot initialization and readiness  
✅ **Development Tools**: Debug endpoints for development  
❌ **No Chat Functionality**: Discord messages required for conversations  
❌ **No Memory Endpoints**: Memory access only via Discord interactions  
❌ **No Character APIs**: Character responses only via Discord  

## API Endpoints

### Base URL
The health endpoints are served on each bot's designated port:

- **Elena** (Marine Biologist): `http://localhost:9091`
- **Marcus** (AI Researcher): `http://localhost:9092` 
- **Ryan** (Indie Game Developer): `http://localhost:9093`
- **Gabriel** (British Gentleman): `http://localhost:9095`
- **Sophia** (Marketing Executive): `http://localhost:9096`
- **And all other configured bots...**

### 1. Health Check

**Endpoint**: `GET /health`

Check if the bot container is running and initialized properly.

**Response**:
```json
{
  "status": "healthy",
  "bot_name": "Elena Rodriguez [AI DEMO]",
  "timestamp": "2025-10-04T10:30:00Z",
  "uptime_seconds": 3600,
  "components": {
    "memory_manager": "initialized",
    "llm_client": "connected",
    "character_system": "loaded"
  }
}
```

**Example**:
```bash
curl http://localhost:9091/health
```

### 2. Bot Status

**Endpoint**: `GET /status`

Get detailed information about bot configuration and status.

**Response**:
```json
{
  "bot_name": "Elena Rodriguez [AI DEMO]",
  "character_file": "elena.json", 
  "discord_status": "connected",
  "memory_system": "vector",
  "environment": "development",
  "version": "2025.10.4"
}
```

## Discord Integration

### **How to Test Conversation Features**

Since WhisperEngine is Discord-only, testing conversation features requires Discord messages:

1. **Join Discord Server**: Get access to the Discord server where bots are deployed
2. **Send Direct Messages**: Send DMs to Elena, Marcus, Ryan, etc.
3. **Test in Channels**: Use bots in Discord channels where they're invited

### **Example Discord Interactions**:

```
# Direct message to Elena bot
You: "Hello Elena! Can you tell me about marine biology?"

Elena: "¡Ay! *adjusts diving mask* You've come to the right marine biologist! 
Ocean science is like exploring an alien world right here on Earth. From the 
calcium carbonate structures in coral reefs to the bioluminescent creatures 
in the deep sea - ¡Dios mío!, there's so much to discover! 

What aspect interests you most? The ecosystem dynamics? Conservation efforts? 
Or maybe the fascinating chemistry of seawater itself? 🌊🐠"
```

## Development and Testing

### **Bot Logs for Debugging**:
```bash
# View Elena bot logs
docker logs whisperengine-elena-bot --tail 50

# View Marcus bot logs  
docker logs whisperengine-marcus-bot --tail 50

# Follow logs in real-time
docker logs whisperengine-elena-bot -f
```

### **Multi-Bot Management**:
```bash
# Start specific bot
./multi-bot.sh start elena

# Check all bot status
./multi-bot.sh status

# Restart after code changes
./multi-bot.sh restart elena
```

## Migration from HTTP Chat APIs

**Previous Architecture** (REMOVED):
- HTTP chat endpoints (`POST /api/chat`)
- External web interfaces  
- Webhook integrations
- Platform-agnostic chat APIs

**Current Architecture** (ACTIVE):
- Discord-first bot system
- Health check endpoints only
- Container orchestration support
- Direct Discord message processing

### **Why Discord-Only?**

1. **Simplified Architecture**: Single platform focus reduces complexity
2. **Rich Discord Features**: Native Discord integrations (reactions, threads, embeds)
3. **Community Focus**: Discord provides natural community interaction patterns  
4. **Development Velocity**: Faster iteration without multi-platform abstractions

---

**For conversation features, send Discord messages directly to the character bots. HTTP endpoints are for monitoring and health checks only.**
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
---

**For conversation features, send Discord messages directly to the character bots. HTTP endpoints are for monitoring and health checks only.**
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