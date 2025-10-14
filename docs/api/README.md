# WhisperEngine API Documentation

This directory contains comprehensive API documentation for integrating WhisperEngine into your applications.

## 📚 Documentation Index

### Quick Start

**⚡ [Quick Reference Guide](./QUICK_REFERENCE.md)** (NEW)  
30-second integration guide with minimal examples - perfect for developers who want to start coding immediately.

### For Third-Party Developers

**🎯 Start Here: [Chat API Reference](./CHAT_API_REFERENCE.md)** (NEW - October 13, 2025)  
Complete integration guide for the WhisperEngine Chat API, including:
- All endpoints and request/response schemas
- Metadata level configurations (basic, standard, extended)
- Error handling and best practices
- Integration examples (React, Python, Node.js)
- Troubleshooting guide
- Security considerations

### Supplementary Documentation

**[Enriched Metadata API](./ENRICHED_METADATA_API.md)**  
Detailed metadata structure and field descriptions for AI intelligence data returned by the API.

**[Enhanced API Features](./ENHANCED_API_FEATURES.md)**  
Quick overview of user facts and relationship metrics (available in extended metadata level).

**[API Metadata Levels Audit](./API_METADATA_LEVELS_AUDIT_COMPLETE.md)**  
Internal audit documentation for metadata level implementation.

## 🚀 Quick Start

### 1. Start WhisperEngine

```bash
# Using Docker (recommended)
docker-compose up -d

# Or start specific character
./multi-bot.sh start elena
```

### 2. Test API Connection

```bash
# Check if Elena bot is ready
curl http://localhost:9091/health

# Send a test message
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Hello! Tell me about yourself."
  }'
```

### 3. Integrate into Your App

See **[Chat API Reference](./CHAT_API_REFERENCE.md)** for complete integration examples in React, Python, Node.js, and more.

## 📖 Key Concepts

### Character Bots

Each WhisperEngine character runs on a dedicated port with identical API endpoints:

| Character | Port | Specialty |
|-----------|------|-----------|
| Elena | 9091 | Marine Biology Education |
| Marcus | 9092 | AI Research & Technology |
| Ryan | 9093 | Indie Game Development |
| Dream | 9094 | Mythological Entity |
| Gabriel | 9095 | British Gentleman |
| Sophia | 9096 | Marketing Executive |
| Jake | 9097 | Adventure Photography |

### Metadata Levels

Control response payload size and detail:

- **`basic`**: Minimal data (~200 bytes) - mobile apps, high-throughput
- **`standard`**: Core AI components (~5-10 KB) - production apps (DEFAULT)
- **`extended`**: Full analytics (~20-50 KB) - dashboards, research

See [Chat API Reference](./CHAT_API_REFERENCE.md#metadata-levels) for detailed comparison.

### Persistent Memory

WhisperEngine automatically:
- Stores conversation history per user
- Tracks relationships and user facts
- Maintains character-specific memory isolation
- Uses consistent `user_id` for memory continuity

## 🔧 Integration Patterns

### Simple Chat Interface

```javascript
// Standard metadata level - emotion detection + core AI
const response = await fetch('http://localhost:9091/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user_123',
    message: 'What are coral reefs?',
    metadata_level: 'standard'
  })
});

const data = await response.json();
console.log(data.response);
console.log(data.metadata.ai_components.emotion_data);
```

### Multi-Character Support

```javascript
// User talks to different characters
await fetch('http://localhost:9091/api/chat', { /* Elena */ });
await fetch('http://localhost:9092/api/chat', { /* Marcus */ });
```

Each character maintains independent memory and personality.

### Batch Processing

```javascript
// Process multiple users efficiently
await fetch('http://localhost:9091/api/chat/batch', {
  method: 'POST',
  body: JSON.stringify({
    metadata_level: 'basic',
    messages: [
      { user_id: 'user1', message: 'Hello' },
      { user_id: 'user2', message: 'Hi there' }
    ]
  })
});
```

## 🛡️ Security & Deployment

### Current Security Model

WhisperEngine is designed for **internal/private deployments**:
- No authentication (add via reverse proxy/API gateway)
- No rate limiting (implement at infrastructure level)
- CORS enabled for web integration

### Production Deployment

For public deployments, implement:
1. API Gateway with authentication
2. Rate limiting per user/IP
3. Network isolation
4. Input validation/sanitization
5. Request logging & monitoring

See [Chat API Reference - Security Section](./CHAT_API_REFERENCE.md#security-considerations) for details.

## 📊 Response Examples

### Basic Level (Lightweight)

```json
{
  "success": true,
  "response": "Marine biology is the study of ocean ecosystems...",
  "processing_time_ms": 1250,
  "memory_stored": true
}
```

### Standard Level (Production)

```json
{
  "success": true,
  "response": "Marine biology is the study of ocean ecosystems...",
  "metadata": {
    "ai_components": {
      "emotion_data": {
        "primary_emotion": "curiosity",
        "intensity": 0.75
      },
      "bot_emotion": {
        "primary_emotion": "joy",
        "intensity": 0.82
      }
    }
  }
}
```

### Extended Level (Analytics)

```json
{
  "success": true,
  "response": "Marine biology is the study of ocean ecosystems...",
  "user_facts": {
    "name": "Alex",
    "interaction_count": 15
  },
  "relationship_metrics": {
    "affection": 70,
    "trust": 65,
    "attunement": 85
  },
  "metadata": {
    // Complete AI intelligence data
  }
}
```

## 🐛 Troubleshooting

### Common Issues

**Bot Not Responding (503)**
```bash
# Check if bot is running
docker ps | grep elena

# Check bot logs
docker logs whisperengine-elena-bot

# Wait for initialization (30-60 seconds)
```

**Slow Responses**
```bash
# Use basic metadata level
{ "metadata_level": "basic" }

# Check system resources
docker stats
```

**Memory Not Persisting**
- Ensure consistent `user_id` across requests
- Verify `memory_stored: true` in responses
- Check Qdrant/PostgreSQL containers are running

See [Full Troubleshooting Guide](./CHAT_API_REFERENCE.md#troubleshooting)

## 📞 Support

- **Documentation**: [Chat API Reference](./CHAT_API_REFERENCE.md)
- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions and share integrations

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 2025 | Initial public API release |
| - | Oct 2025 | Bot emotional intelligence (Phase 7.5/7.6) |
| - | Oct 2025 | Metadata level controls added |
| - | Oct 2025 | Multi-character support |

---

**Ready to integrate?** Start with the **[Chat API Reference](./CHAT_API_REFERENCE.md)** for complete documentation.
