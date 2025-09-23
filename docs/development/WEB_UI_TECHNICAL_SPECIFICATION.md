# Web UI Technical Specification

## Overview

**Document Purpose**: Comprehensive technical specification for WhisperEngine Web UI implementation  
**Status**: Foundation complete, production features in development  
**Last Updated**: September 23, 2025

---

## 🏗 **System Architecture**

### **High-Level Components**
```
┌─────────────────────────────────────────────────────────────┐
│                     Web UI Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │    Chat     │  │    Admin    │  │    API      │          │
│  │ Interface   │  │ Dashboard   │  │ Endpoints   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────────────────┐
│                Integration Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Bot Connector│  │ Identity   │  │ Message     │          │
│  │             │  │ Manager    │  │ Persistence │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────────────────┐
│                WhisperEngine Core                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Multi-Bot   │  │ Vector      │  │ Character   │          │
│  │ System      │  │ Memory      │  │ System      │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### **Technology Stack**
- **Backend**: FastAPI (Python 3.11+) with async/await
- **Frontend**: Server-side rendered HTML with vanilla JavaScript
- **WebSocket**: Real-time bidirectional communication
- **Database**: PostgreSQL (shared with multi-bot system)
- **Memory**: Qdrant vector database integration
- **Authentication**: Session-based with secure tokens
- **Container**: Docker with multi-bot infrastructure integration

---

## 📁 **File Structure**

### **Current Implementation**
```
src/web/
├── simple_chat_app.py       # Main web application (FastAPI)
├── chat_interface.py        # Advanced chat interface (future)
└── __init__.py

docker/
├── Dockerfile.web           # Web UI container definition
└── docker-compose.multi-bot.yml  # Integrated deployment

web-ui.sh                    # Management script
requirements-web.txt         # Web-specific dependencies
```

### **Planned Expansion**
```
src/web/
├── app/
│   ├── main.py             # FastAPI application factory
│   ├── config.py           # Configuration management
│   └── dependencies.py     # Dependency injection
├── api/
│   ├── chat.py            # Chat endpoints
│   ├── admin.py           # Admin endpoints
│   └── auth.py            # Authentication endpoints
├── core/
│   ├── bot_connector.py   # Bot API integration
│   ├── message_handler.py # Message processing
│   └── websocket_manager.py # WebSocket management
├── models/
│   ├── chat.py           # Pydantic models for chat
│   ├── user.py           # User data models
│   └── admin.py          # Admin data models
├── services/
│   ├── conversation.py   # Conversation persistence
│   ├── identity.py       # User identity management
│   └── monitoring.py     # System monitoring
├── static/
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript modules
│   └── assets/          # Images, icons
└── templates/
    ├── chat.html        # Main chat interface
    ├── admin.html       # Admin dashboard
    └── components/      # Reusable UI components
```

---

## 🔌 **API Specification**

### **Chat Endpoints**

#### **GET /** - Chat Interface
```http
GET /
Content-Type: text/html

Returns: HTML chat interface
```

#### **POST /api/login** - User Authentication
```http
POST /api/login
Content-Type: application/json

Request:
{
    "username": "string (3-30 chars)",
    "display_name": "string (optional, max 50 chars)"
}

Response:
{
    "session_token": "string",
    "user_id": "string",
    "username": "string",
    "display_name": "string"
}
```

#### **GET /api/bots** - Available Bots
```http
GET /api/bots

Response:
{
    "bots": [
        {
            "name": "elena",
            "display_name": "Elena Rodriguez",
            "description": "Marine biologist AI companion",
            "emoji": "🌊",
            "status": "online|offline|busy"
        }
    ]
}
```

#### **POST /api/chat** - Send Message
```http
POST /api/chat
Content-Type: application/json
Authorization: Bearer {session_token}

Request:
{
    "content": "string (1-4000 chars)",
    "bot_name": "string",
    "message_type": "text|voice|image"
}

Response:
{
    "message_id": "string",
    "response": "string",
    "timestamp": "ISO8601",
    "bot_name": "string",
    "processing_time": "float (seconds)"
}
```

#### **WebSocket /ws/{token}** - Real-time Chat
```
Connection: /ws/{session_token}

Inbound Messages:
{
    "type": "message",
    "data": {
        "content": "string",
        "bot_name": "string"
    }
}

{
    "type": "typing_start",
    "bot_name": "string"
}

Outbound Messages:
{
    "type": "message",
    "data": {
        "content": "string",
        "bot_name": "string",
        "timestamp": "ISO8601",
        "message_id": "string"
    }
}

{
    "type": "bot_typing",
    "bot_name": "string",
    "is_typing": boolean
}

{
    "type": "error",
    "message": "string"
}
```

### **Admin Endpoints**

#### **GET /admin** - Admin Dashboard
```http
GET /admin
Authorization: Bearer {admin_token}

Returns: HTML admin interface
```

#### **GET /api/admin/status** - System Status
```http
GET /api/admin/status
Authorization: Bearer {admin_token}

Response:
{
    "system": {
        "status": "healthy|degraded|critical",
        "uptime": "string",
        "version": "string"
    },
    "services": {
        "postgres": {"status": "healthy", "response_time": 0.05},
        "redis": {"status": "healthy", "response_time": 0.02},
        "qdrant": {"status": "healthy", "response_time": 0.15}
    },
    "bots": {
        "elena": {"status": "online", "health_check": "healthy", "port": 9091},
        "marcus": {"status": "online", "health_check": "healthy", "port": 9092}
    }
}
```

#### **POST /api/admin/bots/{bot_name}/restart** - Bot Management
```http
POST /api/admin/bots/{bot_name}/restart
Authorization: Bearer {admin_token}

Response:
{
    "success": true,
    "message": "Bot restart initiated",
    "estimated_downtime": "30 seconds"
}
```

---

## 🗄 **Database Schema**

### **Web User Sessions**
```sql
CREATE TABLE web_user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    username VARCHAR(30) NOT NULL,
    display_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_web_sessions_token ON web_user_sessions(session_token);
CREATE INDEX idx_web_sessions_user ON web_user_sessions(user_id);
```

### **Web Conversations**
```sql
CREATE TABLE web_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    bot_name VARCHAR(50) NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time FLOAT,
    message_type VARCHAR(20) DEFAULT 'text',
    metadata JSONB
);

CREATE INDEX idx_web_conversations_user_bot ON web_conversations(user_id, bot_name);
CREATE INDEX idx_web_conversations_timestamp ON web_conversations(timestamp);
```

### **Integration with Existing Schema**
- **Universal Users**: Links to existing `src/identity/universal_identity.py`
- **Vector Memory**: Integrates with existing Qdrant collections
- **Bot Configuration**: Uses existing multi-bot `.env.*` files

---

## 🔧 **Core Components**

### **BotConnector Implementation**
```python
# src/web/core/bot_connector.py
class BotConnector:
    """Handles communication with WhisperEngine bots"""
    
    def __init__(self):
        self.bot_ports = {
            "elena": 9091,
            "marcus": 9092, 
            "marcus-chen": 9093,
            "dream": 9094,
            "gabriel": 9095
        }
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.session = None
    
    async def initialize(self):
        """Initialize HTTP session with connection pooling"""
        connector = aiohttp.TCPConnector(
            limit=100,          # Total connection pool size
            limit_per_host=20,  # Connections per bot
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True
        )
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout
        )
    
    async def send_message_to_bot(self, bot_name: str, user_id: str, 
                                message: str) -> Dict[str, Any]:
        """Send message to specific bot and return response"""
        if bot_name not in self.bot_ports:
            raise ValueError(f"Unknown bot: {bot_name}")
        
        port = self.bot_ports[bot_name]
        url = f"http://localhost:{port}/api/chat"
        
        payload = {
            "user_id": user_id,
            "message": message,
            "platform": "WEB_UI",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    processing_time = time.time() - start_time
                    
                    return {
                        "success": True,
                        "response": result.get("response", ""),
                        "processing_time": processing_time,
                        "bot_name": bot_name
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Bot returned {response.status}: {error_text}",
                        "bot_name": bot_name
                    }
                    
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Timeout communicating with {bot_name}",
                "bot_name": bot_name
            }
        except Exception as e:
            return {
                "success": False, 
                "error": f"Connection error: {str(e)}",
                "bot_name": bot_name
            }
    
    async def get_bot_status(self, bot_name: str) -> Dict[str, Any]:
        """Check if bot is healthy and responsive"""
        if bot_name not in self.bot_ports:
            return {"status": "unknown", "error": "Bot not configured"}
        
        port = self.bot_ports[bot_name]
        url = f"http://localhost:{port}/health"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    health_data = await response.json()
                    return {
                        "status": "online",
                        "health": health_data,
                        "port": port
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"Health check failed: {response.status}",
                        "port": port
                    }
        except Exception as e:
            return {
                "status": "offline",
                "error": str(e),
                "port": port
            }
    
    async def cleanup(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
```

### **WebSocket Manager Implementation**
```python
# src/web/core/websocket_manager.py
class WebSocketManager:
    """Manages WebSocket connections for real-time chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
        
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Accept WebSocket connection and register user"""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        # Handle reconnections - close previous connection
        if user_id in self.user_connections:
            old_connection_id = self.user_connections[user_id]
            await self._disconnect(old_connection_id)
        
        self.user_connections[user_id] = connection_id
        
        logger.info(f"WebSocket connected: user_id={user_id}, connection_id={connection_id}")
        return connection_id
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Handle WebSocket disconnection"""
        connection_id = None
        for conn_id, ws in self.active_connections.items():
            if ws == websocket:
                connection_id = conn_id
                break
        
        if connection_id:
            await self._disconnect(connection_id)
    
    async def _disconnect(self, connection_id: str) -> None:
        """Internal disconnect handler"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            
            # Remove from user mapping
            user_id = None
            for uid, conn_id in self.user_connections.items():
                if conn_id == connection_id:
                    user_id = uid
                    break
            
            if user_id:
                del self.user_connections[user_id]
            
            del self.active_connections[connection_id]
            
            try:
                await websocket.close()
            except Exception:
                pass  # Connection already closed
            
            logger.info(f"WebSocket disconnected: connection_id={connection_id}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific user"""
        if user_id not in self.user_connections:
            return False
        
        connection_id = self.user_connections[user_id]
        if connection_id not in self.active_connections:
            return False
        
        websocket = self.active_connections[connection_id]
        
        try:
            await websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending WebSocket message to {user_id}: {e}")
            await self._disconnect(connection_id)
            return False
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """Broadcast message to all connected users"""
        message_json = json.dumps(message)
        successful_sends = 0
        
        for connection_id in list(self.active_connections.keys()):
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(message_json)
                successful_sends += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                await self._disconnect(connection_id)
        
        return successful_sends
```

---

## 🔐 **Security Considerations**

### **Authentication & Authorization**
- **Session Tokens**: Cryptographically secure random tokens
- **Token Expiration**: Configurable session timeouts
- **Admin Access**: Role-based permissions for administrative functions
- **Rate Limiting**: Prevent abuse of API endpoints
- **Input Validation**: Comprehensive request data validation

### **Implementation Details**
```python
# src/web/core/security.py
class SecurityManager:
    def __init__(self):
        self.secret_key = os.getenv("WEB_UI_SECRET_KEY", self._generate_secret())
        self.session_timeout = timedelta(hours=24)
        self.admin_session_timeout = timedelta(hours=8)
    
    def generate_session_token(self, user_id: str, is_admin: bool = False) -> str:
        """Generate cryptographically secure session token"""
        payload = {
            "user_id": user_id,
            "is_admin": is_admin,
            "issued_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + (
                self.admin_session_timeout if is_admin else self.session_timeout
            )).isoformat()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    async def validate_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate and decode session token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.now() > expires_at:
                return None  # Token expired
            
            return payload
        except jwt.InvalidTokenError:
            return None
```

---

## 📊 **Performance Specifications**

### **Response Time Targets**
- **Page Load**: <2 seconds initial load
- **Message Send**: <1 second for UI feedback
- **Bot Response**: <5 seconds for AI processing
- **WebSocket Latency**: <100ms for real-time updates
- **Admin Dashboard**: <3 seconds for status loading

### **Scalability Targets**
- **Concurrent Users**: 100+ simultaneous conversations
- **Message Throughput**: 1000+ messages per minute
- **WebSocket Connections**: 500+ concurrent connections
- **Database Queries**: <50ms average response time
- **Memory Usage**: <1GB RAM for web service

### **Optimization Strategies**
- **Connection Pooling**: Reuse HTTP connections to bots
- **Database Indexing**: Optimize conversation history queries
- **Caching**: Redis cache for frequently accessed data
- **Compression**: Gzip compression for HTTP responses
- **CDN**: Static asset delivery optimization (future)

---

## 🧪 **Testing Strategy**

### **Unit Tests**
```python
# tests/web/test_bot_connector.py
class TestBotConnector:
    async def test_successful_message_send(self):
        """Test successful message delivery to bot"""
        
    async def test_bot_unavailable_handling(self):
        """Test graceful handling of offline bots"""
        
    async def test_timeout_handling(self):
        """Test timeout scenarios"""

# tests/web/test_websocket_manager.py  
class TestWebSocketManager:
    async def test_connection_management(self):
        """Test WebSocket connection lifecycle"""
        
    async def test_user_reconnection(self):
        """Test handling of user reconnections"""
```

### **Integration Tests**
- **Full Conversation Flow**: User login → bot selection → message exchange
- **Multi-Bot Switching**: Conversation continuity across character changes
- **Admin Functions**: System status monitoring and bot management
- **WebSocket Reliability**: Connection handling under various scenarios

### **Load Testing**
- **Concurrent Users**: Simulate 100+ simultaneous conversations
- **Message Volume**: Test high-frequency message exchange
- **Long-Running Sessions**: Multi-hour conversation stability
- **Resource Usage**: Monitor memory and CPU under load

---

## 🚀 **Deployment Configuration**

### **Environment Variables**
```bash
# Web UI Configuration
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=8080
WEB_UI_SECRET_KEY=<cryptographically-secure-key>

# Database Integration
DATABASE_URL=postgresql://whisperengine:password@postgres:5432/whisperengine
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333

# Bot Integration
BOT_API_TIMEOUT=30
BOT_HEALTH_CHECK_INTERVAL=60

# Security
SESSION_TIMEOUT_HOURS=24
ADMIN_SESSION_TIMEOUT_HOURS=8
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Performance
MAX_CONCURRENT_CONNECTIONS=500
CONNECTION_POOL_SIZE=100
DATABASE_POOL_SIZE=20
```

### **Docker Integration**
```yaml
# docker-compose.multi-bot.yml excerpt
whisperengine-web:
  build:
    context: .
    dockerfile: Dockerfile.web
  container_name: whisperengine-web-interface
  restart: unless-stopped
  ports:
    - "8080:8080"
  environment:
    - DATABASE_URL=postgresql://whisperengine:whisperengine_password@postgres:5432/whisperengine
    - REDIS_URL=redis://redis:6379/0
    - QDRANT_URL=http://qdrant:6333
    - WEB_UI_HOST=0.0.0.0
    - WEB_UI_PORT=8080
    - PYTHONPATH=/app
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_started
    qdrant:
      condition: service_started
  networks:
    - bot_network
  volumes:
    - ./characters:/app/characters:ro
    - ./logs:/app/logs
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

## 📈 **Monitoring & Observability**

### **Health Checks**
- **Application Health**: `/health` endpoint with service status
- **Dependency Health**: PostgreSQL, Redis, Qdrant connectivity
- **Bot Health**: Real-time status of all WhisperEngine bots
- **Performance Metrics**: Response times, error rates, throughput

### **Logging Strategy**
```python
# Structured logging for observability
logger.info("Message sent", extra={
    "user_id": user_id,
    "bot_name": bot_name,
    "message_length": len(message),
    "processing_time": processing_time,
    "success": success
})
```

### **Metrics Collection**
- **Request Metrics**: HTTP request count, duration, status codes
- **WebSocket Metrics**: Connection count, message frequency, errors
- **Bot Integration**: API call success rate, response times
- **User Engagement**: Session duration, message frequency, bot preferences

---

## 🔮 **Future Enhancements**

### **Short-term (Next Sprint)**
- **Real Bot Integration**: Replace demo responses with live API calls
- **Message Persistence**: PostgreSQL conversation storage
- **Admin Dashboard**: Basic system monitoring and bot management

### **Medium-term (Next Month)**  
- **Advanced Chat Features**: File uploads, emoji reactions, message editing
- **Memory Integration**: Conversation context and history
- **Performance Optimization**: Caching, connection pooling, CDN

### **Long-term (Next Quarter)**
- **Multi-modal Support**: Voice input, image sharing, rich media
- **Advanced Admin**: User management, analytics, system configuration
- **API Gateway**: Public API for third-party integrations

**Next Implementation Priority**: Complete `BotConnector` real API integration to enable live conversations with WhisperEngine bots.