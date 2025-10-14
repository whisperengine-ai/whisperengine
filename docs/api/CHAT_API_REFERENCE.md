# WhisperEngine Chat API Reference

**Version**: 1.0  
**Last Updated**: October 13, 2025  
**Status**: Production Ready  
**Audience**: Third-Party Developers & Integration Partners

## Overview

WhisperEngine provides a powerful HTTP Chat API that allows you to integrate AI characters with persistent memory, emotional intelligence, and adaptive learning capabilities into your applications. The API is platform-agnostic and can be used alongside or independently of Discord integration.

### Key Features

- **🎭 Multi-Character Support** - Each bot instance represents a unique AI character
- **🧠 Persistent Memory** - Characters remember conversation history and context
- **💭 Emotional Intelligence** - Real-time emotion analysis for both user and bot
- **📊 Rich Metadata** - Comprehensive AI analytics and conversation insights
- **⚡ Flexible Response Levels** - Control payload size with metadata level settings
- **🔄 Batch Processing** - Process multiple messages efficiently
- **🌐 CORS-Enabled** - Ready for web application integration

## Base URLs

Each character bot runs on its own dedicated port with identical API endpoints:

| Character | Port | Base URL |
|-----------|------|----------|
| Elena (Marine Biologist) | 9091 | `http://localhost:9091` |
| Marcus (AI Researcher) | 9092 | `http://localhost:9092` |
| Ryan (Indie Game Developer) | 9093 | `http://localhost:9093` |
| Dream (Mythological Entity) | 9094 | `http://localhost:9094` |
| Gabriel (British Gentleman) | 9095 | `http://localhost:9095` |
| Sophia (Marketing Executive) | 9096 | `http://localhost:9096` |
| Jake (Adventure Photographer) | 9097 | `http://localhost:9097` |
| Aethys (Omnipotent Entity) | 3007 | `http://localhost:3007` |
| Aetheris (Conscious AI Entity) | 3008 | `http://localhost:3008` |

> **Note**: In containerized deployments, replace `localhost` with your Docker host IP or domain name.

## Authentication

**Current Version**: No authentication required (designed for internal/private deployments)

**Future Versions**: API key authentication planned for public deployments

## Core Endpoints

### 1. Single Message Chat

Process a single conversation message with an AI character.

**Endpoint**: `POST /api/chat`

**Headers**:
```http
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": "string (required)",
  "message": "string (required)",
  "metadata_level": "basic|standard|extended (optional, default: standard)",
  "context": {
    "channel_type": "dm|guild (optional, default: dm)",
    "platform": "api|discord|web (optional, default: api)",
    "metadata": {} // Optional custom metadata
  }
}
```

**Field Descriptions**:

- `user_id` (string, required): Unique identifier for the user. Used for persistent memory and relationship tracking.
- `message` (string, required): The user's message to the character.
- `metadata_level` (string, optional): Controls response payload size and detail level
  - `basic`: Minimal data (~200 bytes) - best for mobile/high-throughput
  - `standard`: Core AI components (~5-10 KB) - recommended for most applications
  - `extended`: Full analytics (~20-50 KB) - complete AI intelligence data
- `context.channel_type` (string, optional): Conversation context type
- `context.platform` (string, optional): Source platform identifier
- `context.metadata` (object, optional): Custom application-specific metadata

**Success Response** (200 OK):

```json
{
  "success": true,
  "response": "Hello! I'd be happy to discuss marine biology with you...",
  "timestamp": "2025-10-13T10:30:00Z",
  "bot_name": "Elena Rodriguez",
  "processing_time_ms": 1250,
  "memory_stored": true,
  "metadata": {
    // Varies based on metadata_level (see Metadata Levels section)
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "user_id is required",
  "success": false
}
```

**Error Response** (500 Internal Server Error):
```json
{
  "success": false,
  "response": "I apologize, but I need to gather my thoughts...",
  "error": "Internal processing error",
  "timestamp": "2025-10-13T10:30:00Z"
}
```

**Example Request (cURL)**:
```bash
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "developer_123",
    "message": "Tell me about coral reefs",
    "metadata_level": "standard",
    "context": {
      "platform": "api",
      "channel_type": "dm"
    }
  }'
```

**Example Request (JavaScript/Fetch)**:
```javascript
const response = await fetch('http://localhost:9091/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'developer_123',
    message: 'Tell me about coral reefs',
    metadata_level: 'standard',
    context: {
      platform: 'api',
      channel_type: 'dm'
    }
  })
});

const data = await response.json();
console.log(data.response);
```

**Example Request (Python)**:
```python
import requests

response = requests.post(
    'http://localhost:9091/api/chat',
    json={
        'user_id': 'developer_123',
        'message': 'Tell me about coral reefs',
        'metadata_level': 'standard',
        'context': {
            'platform': 'api',
            'channel_type': 'dm'
        }
    }
)

data = response.json()
print(data['response'])
```

### 2. Batch Message Processing

Process multiple messages in a single request for improved efficiency.

**Endpoint**: `POST /api/chat/batch`

**Headers**:
```http
Content-Type: application/json
```

**Request Body**:
```json
{
  "metadata_level": "basic|standard|extended (optional, default: standard)",
  "messages": [
    {
      "user_id": "string (required)",
      "message": "string (required)",
      "context": {
        "channel_type": "dm|guild (optional)",
        "platform": "api (optional)",
        "metadata": {} // Optional custom metadata
      }
    }
  ]
}
```

**Constraints**:
- Maximum 10 messages per batch
- All messages processed with same `metadata_level`
- Each message processed independently

**Success Response** (200 OK):
```json
{
  "results": [
    {
      "index": 0,
      "user_id": "developer_123",
      "success": true,
      "response": "Hello! I'd be happy to help...",
      "processing_time_ms": 1100,
      "memory_stored": true,
      "metadata": {
        // Varies based on metadata_level
      }
    },
    {
      "index": 1,
      "user_id": "developer_456",
      "success": true,
      "response": "That's a great question...",
      "processing_time_ms": 1350,
      "memory_stored": true,
      "metadata": {}
    }
  ],
  "total_processed": 2,
  "timestamp": "2025-10-13T10:30:00Z",
  "bot_name": "Elena Rodriguez"
}
```

**Example Request (cURL)**:
```bash
curl -X POST http://localhost:9091/api/chat/batch \
  -H "Content-Type: application/json" \
  -d '{
    "metadata_level": "standard",
    "messages": [
      {
        "user_id": "user_1",
        "message": "What is marine biology?",
        "context": {"platform": "api"}
      },
      {
        "user_id": "user_2", 
        "message": "Tell me about ocean conservation",
        "context": {"platform": "api"}
      }
    ]
  }'
```

## Metadata Levels

Control the amount of data returned to optimize for your use case:

### 🏃 `basic` - Lightweight Applications

**Best for**: Mobile apps, high-throughput services, simple chatbots  
**Payload Size**: ~200 bytes  
**Processing Overhead**: Negligible (0ms)

**Response Fields**:
```json
{
  "success": true,
  "response": "Character's message...",
  "timestamp": "2025-10-13T10:30:00Z",
  "bot_name": "Elena Rodriguez",
  "processing_time_ms": 1250,
  "memory_stored": true
}
```

**Use Case**: You only need the character's response and basic success indicators.

---

### 🎯 `standard` - Production Applications (DEFAULT)

**Best for**: Web apps, dashboards, emotion-aware UIs  
**Payload Size**: ~5-10 KB  
**Processing Overhead**: Minimal (0ms - already calculated)

**Response Fields** (all of `basic` PLUS):
```json
{
  "success": true,
  "response": "Character's message...",
  "timestamp": "2025-10-13T10:30:00Z",
  "bot_name": "Elena Rodriguez",
  "processing_time_ms": 1250,
  "memory_stored": true,
  "metadata": {
    "ai_components": {
      "emotion_data": {
        "primary_emotion": "joy",
        "intensity": 0.85,
        "confidence": 0.92,
        "mixed_emotions": [["excitement", 0.72]]
      },
      "bot_emotion": {
        "primary_emotion": "joy",
        "intensity": 0.85,
        "mixed_emotions": [["curiosity", 0.45], ["excitement", 0.72]]
      },
      "phase4_intelligence": {
        "conversation_intelligence": {
          "context_quality": 0.87,
          "user_engagement_level": 0.78,
          "conversation_coherence": 0.91
        }
      },
      "context_analysis": {
        "context_switch_detected": false,
        "urgency_level": "normal",
        "empathy_level": 0.75
      }
    },
    "security_validation": {
      "is_safe": true,
      "warnings": []
    }
  }
}
```

**Use Case**: Production applications that leverage emotional intelligence and conversation analytics.

---

### 📊 `extended` - Analytics & Research

**Best for**: Analytics dashboards, research tools, admin panels  
**Payload Size**: ~20-50 KB  
**Processing Overhead**: Minimal (~10ms for user data extraction)

**Response Fields** (all of `standard` PLUS):
```json
{
  "success": true,
  "response": "Character's message...",
  "timestamp": "2025-10-13T10:30:00Z",
  "bot_name": "Elena Rodriguez",
  "processing_time_ms": 1250,
  "memory_stored": true,
  "user_facts": {
    "name": "Alex Thompson",
    "interaction_count": 15,
    "first_interaction": "2025-10-01T08:30:00Z",
    "last_interaction": "2025-10-13T10:30:00Z"
  },
  "relationship_metrics": {
    "affection": 70,
    "trust": 65,
    "attunement": 85
  },
  "metadata": {
    "ai_components": {
      // Full AI components (emotion, context, intelligence)
    },
    "security_validation": {
      // Security checks
    },
    "vector_memory": {
      "retrieved_memories": 8,
      "average_similarity": 0.82,
      "memory_quality": "high"
    },
    "temporal_intelligence": {
      // Time-based analytics
    }
  }
}
```

**Use Case**: Complete AI intelligence data for analytics, dashboards, or research purposes.

## Health & Status Endpoints

### Get Bot Information

**Endpoint**: `GET /api/bot-info`

**Response**:
```json
{
  "bot_name": "Elena Rodriguez",
  "bot_id": "1234567890",
  "status": "online",
  "platform": "discord",
  "api_version": "1.0",
  "capabilities": [
    "text_chat",
    "conversation_memory",
    "character_personality"
  ],
  "character_info": {
    "character_name": "Elena Rodriguez",
    "has_personality": true
  },
  "timestamp": "2025-10-13T10:30:00Z"
}
```

### Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-13T10:30:00Z",
  "service": "WhisperEngine Discord Bot"
}
```

### Readiness Check

**Endpoint**: `GET /ready`

**Response** (Ready):
```json
{
  "status": "ready",
  "timestamp": "2025-10-13T10:30:00Z",
  "bot_user": "Elena Rodriguez#1234",
  "guilds_count": 3,
  "latency_ms": 45.2
}
```

**Response** (Not Ready - 503):
```json
{
  "status": "not_ready",
  "timestamp": "2025-10-13T10:30:00Z",
  "reason": "Bot not connected to Discord"
}
```

### Detailed Status

**Endpoint**: `GET /status`

**Response**:
```json
{
  "service": "WhisperEngine Discord Bot",
  "timestamp": "2025-10-13T10:30:00Z",
  "bot": {
    "ready": true,
    "closed": false,
    "user": "Elena Rodriguez#1234",
    "latency_ms": 45.2
  },
  "api": {
    "endpoints": [
      "/api/bot-info",
      "/api/chat (POST)",
      "/api/chat/batch (POST)"
    ]
  },
  "character": {
    "character_name": "Elena Rodriguez",
    "has_personality": true
  }
}
```

## AI Intelligence Metadata

When using `standard` or `extended` metadata levels, you receive comprehensive AI intelligence data:

### Emotion Analysis

Both user and character emotions are analyzed using RoBERTa transformer models:

```json
{
  "emotion_data": {
    "primary_emotion": "joy",
    "intensity": 0.85,
    "confidence": 0.92,
    "roberta_confidence": 0.92,
    "emotion_variance": 0.43,
    "emotion_dominance": 0.72,
    "emotional_intensity": 0.85,
    "is_multi_emotion": true,
    "mixed_emotions": [
      ["excitement", 0.72],
      ["curiosity", 0.45]
    ],
    "all_emotions": {
      "joy": 0.85,
      "excitement": 0.72,
      "curiosity": 0.45,
      "neutral": 0.20
    },
    "emotion_count": 3
  },
  "bot_emotion": {
    // Same structure as emotion_data, but for character's response
    "primary_emotion": "joy",
    "intensity": 0.85,
    "mixed_emotions": [["enthusiasm", 0.68]]
  }
}
```

**Emotion Types**:
- `joy` - Happiness, delight, pleasure
- `sadness` - Sorrow, disappointment, grief
- `anger` - Frustration, irritation, rage
- `fear` - Anxiety, worry, nervousness
- `surprise` - Astonishment, shock, wonder
- `disgust` - Revulsion, distaste, aversion
- `neutral` - Calm, balanced, objective

### Conversation Intelligence (Phase 4)

Advanced conversation analysis provides context quality metrics:

```json
{
  "phase4_intelligence": {
    "conversation_intelligence": {
      "context_quality": 0.87,
      "user_engagement_level": 0.78,
      "conversation_coherence": 0.91,
      "topic_continuity": 0.85,
      "emotional_resonance": 0.72
    }
  }
}
```

### Context Analysis

Real-time conversation flow detection:

```json
{
  "context_analysis": {
    "context_switch_detected": false,
    "urgency_level": "normal",
    "empathy_level": 0.75,
    "conversation_stage": "deepening",
    "requires_clarification": false
  }
}
```

### Relationship Metrics (Extended Level Only)

Track relationship progression over time:

```json
{
  "relationship_metrics": {
    "affection": 70,
    "trust": 65,
    "attunement": 85
  }
}
```

**Metrics Range**: 0-100 (higher values indicate stronger relationships)

- **Affection**: Based on relationship level and positive interactions
- **Trust**: Calculated from interaction count, sentiment, and consistency
- **Attunement**: Measures emotional understanding and empathy

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful, response generated |
| 400 | Bad Request | Missing required fields or invalid parameters |
| 500 | Internal Server Error | Character processing error, fallback response provided |
| 503 | Service Unavailable | Bot not ready or initializing |

### Error Response Format

```json
{
  "error": "Error message describing the issue",
  "success": false,
  "details": "Additional error context (optional)",
  "timestamp": "2025-10-13T10:30:00Z"
}
```

### Common Errors

**Missing user_id**:
```json
{
  "error": "user_id is required",
  "success": false
}
```

**Missing message**:
```json
{
  "error": "message is required",
  "success": false
}
```

**Invalid metadata_level**:
```json
{
  "error": "metadata_level must be \"basic\", \"standard\", or \"extended\"",
  "success": false
}
```

**Bot not ready**:
```json
{
  "error": "Chat API not available - bot components not ready",
  "success": false,
  "details": "Bot is still initializing. Please try again in a few moments."
}
```

**Batch size exceeded**:
```json
{
  "error": "Maximum 10 messages per batch",
  "success": false
}
```

## Rate Limiting

**Current Version**: No rate limiting (designed for internal deployments)

**Best Practices**:
- Use batch endpoints for multiple users instead of parallel single requests
- Implement client-side request queuing for high-volume scenarios
- Monitor `processing_time_ms` to gauge system load

**Future Versions**: Configurable rate limiting planned for public deployments

## CORS Support

All API endpoints support CORS for web application integration:

**Headers Set**:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

**Preflight Requests**: `OPTIONS` requests are automatically handled for `/api/chat` and `/api/chat/batch`

## Integration Examples

### React Application

```javascript
import { useState } from 'react';

function ChatComponent() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [emotion, setEmotion] = useState(null);

  const sendMessage = async () => {
    const result = await fetch('http://localhost:9091/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'web_user_123',
        message: message,
        metadata_level: 'standard'
      })
    });

    const data = await result.json();
    setResponse(data.response);
    
    if (data.metadata?.ai_components?.emotion_data) {
      setEmotion(data.metadata.ai_components.emotion_data);
    }
  };

  return (
    <div>
      <input 
        value={message} 
        onChange={(e) => setMessage(e.target.value)} 
        placeholder="Type your message..."
      />
      <button onClick={sendMessage}>Send</button>
      
      {response && (
        <div className="response">
          <p>{response}</p>
          {emotion && (
            <span className={`emotion ${emotion.primary_emotion}`}>
              {emotion.primary_emotion} ({Math.round(emotion.intensity * 100)}%)
            </span>
          )}
        </div>
      )}
    </div>
  );
}
```

### Python Web Application (Flask)

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

WHISPERENGINE_URL = 'http://localhost:9091/api/chat'

@app.route('/chat', methods=['POST'])
def chat():
    user_data = request.json
    
    # Forward to WhisperEngine
    response = requests.post(WHISPERENGINE_URL, json={
        'user_id': user_data.get('user_id'),
        'message': user_data.get('message'),
        'metadata_level': 'standard',
        'context': {
            'platform': 'web_app',
            'channel_type': 'dm'
        }
    })
    
    data = response.json()
    
    # Return simplified response to frontend
    return jsonify({
        'response': data['response'],
        'emotion': data.get('metadata', {})
                      .get('ai_components', {})
                      .get('emotion_data', {})
                      .get('primary_emotion'),
        'success': data['success']
    })

if __name__ == '__main__':
    app.run(port=5000)
```

### Node.js/Express Application

```javascript
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

const WHISPERENGINE_URL = 'http://localhost:9091/api/chat';

app.post('/chat', async (req, res) => {
  try {
    const { user_id, message } = req.body;
    
    const response = await axios.post(WHISPERENGINE_URL, {
      user_id,
      message,
      metadata_level: 'standard',
      context: {
        platform: 'node_app',
        channel_type: 'dm'
      }
    });

    const { response: botResponse, metadata } = response.data;
    const emotion = metadata?.ai_components?.emotion_data;

    res.json({
      response: botResponse,
      emotion: emotion?.primary_emotion,
      intensity: emotion?.intensity,
      success: true
    });

  } catch (error) {
    console.error('Chat error:', error.message);
    res.status(500).json({
      error: 'Failed to process message',
      success: false
    });
  }
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

## Best Practices

### User ID Management

✅ **DO**:
- Use consistent, unique user IDs across sessions
- Consider using platform-specific IDs (e.g., Discord user ID, database user ID)
- Implement user ID namespacing for multi-tenant applications

❌ **DON'T**:
- Use temporary session IDs (breaks conversation memory)
- Change user IDs between conversations
- Use personally identifiable information directly as user IDs

### Metadata Level Selection

| Use Case | Recommended Level | Reason |
|----------|-------------------|--------|
| Mobile chat app | `basic` | Minimize bandwidth, fast responses |
| Web chat interface | `standard` | Emotion UI, moderate bandwidth |
| Analytics dashboard | `extended` | Complete data for insights |
| High-throughput service | `basic` | Minimal processing overhead |
| Emotion-aware chatbot | `standard` | Emotion detection + reasonable payload |

### Error Handling

```javascript
// Good: Handle both network and API errors
async function sendMessage(userId, message) {
  try {
    const response = await fetch('http://localhost:9091/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, message })
    });

    const data = await response.json();

    if (!data.success) {
      // API returned error but still gave fallback response
      console.warn('API error:', data.error);
      return data.response; // Still show fallback to user
    }

    return data.response;

  } catch (error) {
    // Network error - couldn't reach API
    console.error('Network error:', error);
    return 'I apologize, but I am having trouble connecting right now.';
  }
}
```

### Batch Processing

✅ **DO**:
- Use batch endpoint when processing multiple users
- Group messages from different conversations
- Process up to 10 messages per batch for optimal performance

❌ **DON'T**:
- Send sequential messages from same user in batch (breaks conversation flow)
- Exceed 10 messages per batch request
- Use batch for real-time single-user chat

### Performance Optimization

**Conversation Caching**:
- WhisperEngine internally caches conversation context
- Repeated messages from same user are faster (memory already loaded)
- First message may take longer (~1-2 seconds)

**Connection Pooling**:
```python
# Python: Reuse session for better performance
import requests

session = requests.Session()

def chat(user_id, message):
    return session.post('http://localhost:9091/api/chat', json={
        'user_id': user_id,
        'message': message
    }).json()
```

**Async Processing** (for non-real-time use cases):
```javascript
// Process multiple users asynchronously
async function processChatQueue(messages) {
  const batchSize = 10;
  
  for (let i = 0; i < messages.length; i += batchSize) {
    const batch = messages.slice(i, i + batchSize);
    
    await fetch('http://localhost:9091/api/chat/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        messages: batch,
        metadata_level: 'basic' 
      })
    });
  }
}
```

## Troubleshooting

### Bot Not Responding (503 Error)

**Issue**: `Chat API not available - bot components not ready`

**Solutions**:
1. Check bot is running: `docker ps | grep elena` (replace with your bot name)
2. Check bot logs: `docker logs whisperengine-elena-bot`
3. Wait 30-60 seconds after container starts (initialization time)
4. Verify Discord connection (if using Discord integration)

### Slow Response Times

**Issue**: `processing_time_ms` > 5000ms

**Solutions**:
1. Use `metadata_level: basic` for faster responses
2. Check LLM provider status (OpenRouter, OpenAI, etc.)
3. Monitor system resources: `docker stats`
4. Verify Qdrant and PostgreSQL are healthy

### Connection Refused

**Issue**: Cannot connect to `http://localhost:9091`

**Solutions**:
1. Verify port mapping: `docker ps | grep 9091`
2. Check firewall settings
3. Try `http://127.0.0.1:9091` instead of `localhost`
4. Confirm container is running: `docker-compose ps`

### Memory Not Persisting

**Issue**: Character doesn't remember previous conversations

**Solutions**:
1. Verify consistent `user_id` across requests
2. Check `memory_stored: true` in responses
3. Verify PostgreSQL and Qdrant containers are running
4. Check logs for database connection errors

## Advanced Topics

### Custom Character Deployment

To deploy your own custom character:

1. **Create CDL Character Definition** via Web UI or database
2. **Configure Environment Variables** in `.env.<character_name>`
3. **Set Unique Port** for health check API
4. **Start Character Bot**: `./multi-bot.sh start <character_name>`
5. **Test API**: `curl http://localhost:<port>/api/chat`

### Multi-Character Conversations

Each character maintains independent memory and personality:

```javascript
// User talks to Elena (marine biologist)
await fetch('http://localhost:9091/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 'user123',
    message: 'Tell me about coral reefs'
  })
});

// Same user talks to Marcus (AI researcher)  
await fetch('http://localhost:9092/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 'user123',
    message: 'Explain transformer models'
  })
});
```

Both characters remember their separate conversations with `user123`.

### Webhook Integration

Use WhisperEngine with webhooks for asynchronous processing:

```python
from flask import Flask, request
import requests
import threading

app = Flask(__name__)

def process_chat_async(user_id, message, webhook_url):
    # Call WhisperEngine
    response = requests.post('http://localhost:9091/api/chat', json={
        'user_id': user_id,
        'message': message
    }).json()
    
    # Send result to webhook
    requests.post(webhook_url, json={
        'user_id': user_id,
        'response': response['response']
    })

@app.route('/webhook/incoming', methods=['POST'])
def incoming_message():
    data = request.json
    
    # Process asynchronously
    thread = threading.Thread(
        target=process_chat_async,
        args=(data['user_id'], data['message'], data['callback_url'])
    )
    thread.start()
    
    return {'status': 'processing'}, 202

if __name__ == '__main__':
    app.run(port=5000)
```

## Security Considerations

### Current Security Model

WhisperEngine is designed for **internal/private deployments** and currently:

- ❌ No authentication/authorization
- ❌ No rate limiting
- ❌ No input sanitization beyond basic validation
- ✅ CORS enabled for web integration
- ✅ Internal security validation (profanity, toxicity checks)

### Recommended Deployment Practices

For **production/public deployments**, implement:

1. **Reverse Proxy with Authentication**:
   ```nginx
   # nginx.conf
   location /api/ {
       auth_request /auth;
       proxy_pass http://localhost:9091/api/;
   }
   ```

2. **API Gateway with Rate Limiting**:
   - Use Kong, AWS API Gateway, or similar
   - Implement per-user rate limits
   - Add API key authentication

3. **Network Isolation**:
   - Run WhisperEngine in private network
   - Expose only through API gateway
   - Use firewall rules to restrict access

4. **Input Validation**:
   - Validate user IDs match authenticated user
   - Sanitize messages before sending
   - Implement maximum message length

5. **Monitoring & Logging**:
   - Log all API requests
   - Monitor for abuse patterns
   - Set up alerting for anomalies

## Migration & Versioning

### API Version History

| Version | Release Date | Changes |
|---------|-------------|---------|
| 1.0 | October 2025 | Initial public API release |

### Breaking Changes Policy

WhisperEngine follows semantic versioning:

- **Major versions** (2.0, 3.0): Breaking changes, migration required
- **Minor versions** (1.1, 1.2): New features, backward compatible
- **Patch versions** (1.0.1, 1.0.2): Bug fixes, fully compatible

### Deprecation Notice

Deprecated features will:
1. Be marked deprecated in documentation (minimum 3 months)
2. Continue working with deprecation warnings
3. Be removed in next major version

Check release notes for upcoming changes.

## Support & Resources

### Documentation
- **Architecture Guide**: `/docs/architecture/`
- **Character System**: `/docs/character-system/`
- **Deployment Guide**: `/docs/deployment/`

### Community
- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions and share integrations

### Example Integrations
- React Web UI: `cdl-web-ui/` directory
- Python Validation Scripts: `tests/automated/`
- Monitoring Dashboards: `dashboards/` directory

## Changelog

### 2025-10-13
- Added comprehensive API documentation
- Documented metadata levels (basic, standard, extended)
- Added integration examples for React, Python, Node.js
- Documented error handling and best practices

### 2025-10-05  
- Added bot emotional intelligence (Phase 7.5 & 7.6)
- Enhanced metadata with bot emotion analysis
- Improved conversation intelligence metrics

### 2025-10-03
- Initial Chat API launch
- Multi-character support
- Persistent memory and relationship tracking

---

**Questions or Need Help?**  
Check the troubleshooting section above or open an issue on GitHub.
