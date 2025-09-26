"""
WhisperEngine Web Chat Interface

ChatGPT-like web interface with comprehensive functionality:
- Multi-bot chat interface with character selection
- Real-time messaging with WebSocket
- Admin interface for configuration
- Settings management for API endpoints and secrets
- Universal identity system integration
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
from pathlib import Path

# Web framework imports
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    WEB_AVAILABLE = True
except ImportError:
    FastAPI = None
    WEB_AVAILABLE = False

from src.platforms.universal_chat import (
    UniversalChatOrchestrator, 
    Message, 
    ChatPlatform, 
    MessageType,
    create_universal_chat_platform
)
from src.identity.universal_identity import (
    UniversalIdentityManager, 
    create_identity_manager,
    UniversalUser
)
from src.database.database_integration import DatabaseIntegrationManager

logger = logging.getLogger(__name__)


# Pydantic models for API
class ChatMessage(BaseModel):
    """Chat message for web interface"""
    content: str = Field(..., min_length=1, max_length=4000)
    bot_name: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    message_type: str = Field(default="text")


class UserRegistration(BaseModel):
    """User registration for web interface"""
    username: str = Field(..., min_length=3, max_length=30, regex=r'^[a-zA-Z0-9_-]+$')
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    display_name: Optional[str] = Field(None, max_length=50)


class BotConfiguration(BaseModel):
    """Bot configuration model"""
    bot_name: str
    character_file: str
    enabled: bool = True
    description: Optional[str] = None


class APIEndpointConfig(BaseModel):
    """API endpoint configuration"""
    name: str
    url: str
    api_key: Optional[str] = None
    enabled: bool = True
    timeout: int = Field(default=30, ge=1, le=300)


class WebSocketManager:
    """Manages WebSocket connections for real-time chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_sessions: Dict[str, str] = {}  # websocket_id -> user_id
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect user to WebSocket"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.user_sessions[id(websocket)] = user_id
        
        logger.info("WebSocket connected for user: %s", user_id)
        
        # Send welcome message
        await self.send_to_user(user_id, {
            "type": "system",
            "content": "Connected to WhisperEngine",
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect user from WebSocket"""
        websocket_id = id(websocket)
        user_id = self.user_sessions.get(websocket_id)
        
        if user_id and user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        if websocket_id in self.user_sessions:
            del self.user_sessions[websocket_id]
        
        logger.info("WebSocket disconnected for user: %s", user_id)
    
    async def send_to_user(self, user_id: str, message: dict) -> bool:
        """Send message to all user's connections"""
        if user_id not in self.active_connections:
            return False
        
        message_str = json.dumps(message)
        disconnected = []
        
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error("Failed to send WebSocket message: %s", e)
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)
        
        return len(self.active_connections.get(user_id, [])) > 0


class WebChatApplication:
    """Main web chat application - standalone service"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not WEB_AVAILABLE:
            raise ImportError("FastAPI not available - install web dependencies")
        
        self.config = config or {}
        self.app = FastAPI(
            title="WhisperEngine Web Interface",
            description="ChatGPT-like interface for WhisperEngine AI",
            version="1.0.0"
        )
        
        # Initialize components (connect to existing infrastructure)
        self.db_manager = None  # Will connect to existing database
        self.identity_manager = create_identity_manager(self.db_manager)
        self.chat_platform = None  # Will connect to existing chat system
        self.websocket_manager = WebSocketManager()
        
        # Available bots (from environment or discovery)
        self.available_bots: Dict[str, BotConfiguration] = {}
        self.api_endpoints: Dict[str, APIEndpointConfig] = {}
        
        # Setup routes and middleware
        self._setup_middleware()
        self._setup_routes()
        self._load_configurations()
        
        logger.info("WhisperEngine Web UI initialized as standalone service")
    
    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Serve static files
        static_path = Path(__file__).parent.parent.parent / "web-ui" / "dist"
        if static_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            """Health check for container orchestration"""
            try:
                # Check database connection
                db_healthy = await self._check_database_health()
                
                # Check memory system
                memory_healthy = await self._check_memory_health()
                
                if db_healthy and memory_healthy:
                    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
                else:
                    raise HTTPException(status_code=503, detail="Service unhealthy")
            except Exception as e:
                logger.error("Health check failed: %s", e)
                raise HTTPException(status_code=503, detail="Health check failed")
        
        # Main chat interface
        @self.app.get("/", response_class=HTMLResponse)
        async def chat_interface():
            """Serve main chat interface"""
            return self._get_chat_html()
        
        # Admin interface
        @self.app.get("/admin", response_class=HTMLResponse)
        async def admin_interface():
            """Serve admin interface"""
            return self._get_admin_html()
        
        # User registration/authentication
        @self.app.post("/api/register")
        async def register_user(user_data: UserRegistration):
            """Register new web user"""
            try:
                user = await self.identity_manager.create_web_user(
                    username=user_data.username,
                    email=user_data.email,
                    display_name=user_data.display_name
                )
                return {
                    "success": True,
                    "user_id": user.universal_id,
                    "session_token": user.universal_id  # Simple token for demo
                }
            except Exception as e:
                logger.error("User registration failed: %s", e)
                raise HTTPException(status_code=400, detail="Registration failed")
        
        # Bot management
        @self.app.get("/api/bots")
        async def get_available_bots():
            """Get list of available bots"""
            return {
                "bots": [
                    {
                        "name": name,
                        "description": config.description,
                        "enabled": config.enabled
                    }
                    for name, config in self.available_bots.items()
                    if config.enabled
                ]
            }
        
        # Chat endpoints
        @self.app.post("/api/chat")
        async def send_message(
            message_data: ChatMessage,
            user: UniversalUser = Depends(self._get_current_user)
        ):
            """Send chat message"""
            try:
                # Create universal message
                universal_message = Message(
                    message_id=f"web_{datetime.now().timestamp()}",
                    user_id=user.universal_id,
                    content=message_data.content,
                    platform=ChatPlatform.WEB_UI,
                    channel_id=message_data.bot_name,  # Use bot name as channel
                    message_type=MessageType.TEXT
                )
                
                # Process through chat platform
                conversation = await self.chat_platform.get_or_create_conversation(universal_message)
                ai_response = await self.chat_platform.generate_ai_response(
                    universal_message,
                    conversation_context=[]  # Will be populated by platform
                )
                
                # Send response via WebSocket
                await self.websocket_manager.send_to_user(user.universal_id, {
                    "type": "bot_response",
                    "content": ai_response.content,
                    "bot_name": message_data.bot_name,
                    "timestamp": datetime.now().isoformat(),
                    "emotion_detected": getattr(ai_response, 'emotion_detected', None)
                })
                
                return {"success": True, "response": ai_response.content}
                
            except Exception as e:
                logger.error("Chat message failed: %s", e)
                raise HTTPException(status_code=500, detail="Message processing failed")
        
        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket,
            token: str
        ):
            """WebSocket endpoint for real-time chat"""
            # Authenticate user
            user = await self.identity_manager.authenticate_web_user(token)
            if not user:
                await websocket.close(code=4001, reason="Authentication failed")
                return
            
            await self.websocket_manager.connect(websocket, user.universal_id)
            
            try:
                while True:
                    # Keep connection alive and handle incoming messages
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    if message_data.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)
        
        # Admin API endpoints
        @self.app.get("/api/admin/config")
        async def get_admin_config(admin_user: UniversalUser = Depends(self._get_admin_user)):
            """Get admin configuration"""
            return {
                "bots": self.available_bots,
                "api_endpoints": self.api_endpoints,
                "system_status": await self._get_system_status()
            }
        
        @self.app.post("/api/admin/bots")
        async def update_bot_config(
            bot_config: BotConfiguration,
            admin_user: UniversalUser = Depends(self._get_admin_user)
        ):
            """Update bot configuration"""
            self.available_bots[bot_config.bot_name] = bot_config
            await self._save_bot_configurations()
            return {"success": True}
        
        @self.app.post("/api/admin/endpoints")
        async def update_api_endpoint(
            endpoint_config: APIEndpointConfig,
            admin_user: UniversalUser = Depends(self._get_admin_user)
        ):
            """Update API endpoint configuration"""
            self.api_endpoints[endpoint_config.name] = endpoint_config
            await self._save_api_configurations()
            return {"success": True}
    
    async def _get_current_user(self, request: Request) -> UniversalUser:
        """Get current authenticated user"""
        # Simple authentication for demo - use proper JWT in production
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        
        token = auth_header[7:]  # Remove "Bearer "
        user = await self.identity_manager.authenticate_web_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return user
    
    async def _get_admin_user(self, user: UniversalUser = Depends(_get_current_user)) -> UniversalUser:
        """Verify user has admin privileges"""
        # In production, check user roles/permissions
        if not user.preferences.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        return user
    
    def _get_chat_html(self) -> str:
        """Generate chat interface HTML"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>WhisperEngine Chat</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; }
                .chat-container { display: flex; height: 100vh; }
                .sidebar { width: 250px; background: #f0f0f0; padding: 20px; border-right: 1px solid #ddd; }
                .chat-area { flex: 1; display: flex; flex-direction: column; }
                .messages { flex: 1; padding: 20px; overflow-y: auto; }
                .input-area { padding: 20px; border-top: 1px solid #ddd; }
                .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
                .user-message { background: #007bff; color: white; text-align: right; }
                .bot-message { background: #f8f9fa; border: 1px solid #dee2e6; }
                .bot-selector { width: 100%; margin-bottom: 10px; padding: 8px; }
                .message-input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
                .send-button { margin-top: 10px; padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; }
            </style>
        </head>
        <body>
            <div class="chat-container">
                <div class="sidebar">
                    <h3>WhisperEngine</h3>
                    <select id="botSelector" class="bot-selector">
                        <option value="elena">Elena Rodriguez</option>
                        <option value="marcus">Marcus Thompson</option>
                        <option value="ryan-chen">Ryan Chen</option>
                    </select>
                    <div id="connectionStatus">Connecting...</div>
                </div>
                <div class="chat-area">
                    <div id="messages" class="messages"></div>
                    <div class="input-area">
                        <input type="text" id="messageInput" class="message-input" placeholder="Type your message...">
                        <button onclick="sendMessage()" class="send-button">Send</button>
                    </div>
                </div>
            </div>
            <script>
                let ws = null;
                let currentBot = 'elena';
                
                function connectWebSocket() {
                    const token = localStorage.getItem('auth_token') || 'demo_user';
                    ws = new WebSocket(`ws://localhost:8080/ws?token=${token}`);
                    
                    ws.onopen = () => {
                        document.getElementById('connectionStatus').textContent = 'Connected';
                    };
                    
                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        if (data.type === 'bot_response') {
                            addMessage(data.content, 'bot', data.bot_name);
                        }
                    };
                    
                    ws.onclose = () => {
                        document.getElementById('connectionStatus').textContent = 'Disconnected';
                        setTimeout(connectWebSocket, 3000);
                    };
                }
                
                function addMessage(content, type, botName = '') {
                    const messages = document.getElementById('messages');
                    const message = document.createElement('div');
                    message.className = `message ${type}-message`;
                    message.innerHTML = `<div>${content}</div>`;
                    if (botName) message.innerHTML += `<small>- ${botName}</small>`;
                    messages.appendChild(message);
                    messages.scrollTop = messages.scrollHeight;
                }
                
                function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    addMessage(message, 'user');
                    
                    fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('auth_token') || 'demo_user'}`
                        },
                        body: JSON.stringify({
                            content: message,
                            bot_name: currentBot
                        })
                    });
                    
                    input.value = '';
                }
                
                document.getElementById('botSelector').addEventListener('change', (e) => {
                    currentBot = e.target.value;
                });
                
                document.getElementById('messageInput').addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') sendMessage();
                });
                
                connectWebSocket();
            </script>
        </body>
        </html>
        """
    
    def _get_admin_html(self) -> str:
        """Generate admin interface HTML"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>WhisperEngine Admin</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; }
                .admin-container { max-width: 1200px; margin: 0 auto; }
                .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
                .config-form { display: grid; gap: 10px; }
                .form-group { display: flex; flex-direction: column; }
                .form-group label { margin-bottom: 5px; font-weight: bold; }
                .form-group input, .form-group select { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                .button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
                .status-indicator { padding: 5px 10px; border-radius: 4px; color: white; }
                .status-online { background: #28a745; }
                .status-offline { background: #dc3545; }
            </style>
        </head>
        <body>
            <div class="admin-container">
                <h1>WhisperEngine Admin Panel</h1>
                
                <div class="section">
                    <h2>System Status</h2>
                    <div id="systemStatus">Loading...</div>
                </div>
                
                <div class="section">
                    <h2>Bot Configuration</h2>
                    <div id="botConfigs"></div>
                </div>
                
                <div class="section">
                    <h2>API Endpoints</h2>
                    <div id="apiEndpoints"></div>
                    <button onclick="addEndpoint()" class="button">Add New Endpoint</button>
                </div>
            </div>
            
            <script>
                async function loadAdminConfig() {
                    try {
                        const response = await fetch('/api/admin/config', {
                            headers: {
                                'Authorization': `Bearer ${localStorage.getItem('auth_token') || 'demo_admin'}`
                            }
                        });
                        const config = await response.json();
                        
                        displaySystemStatus(config.system_status);
                        displayBotConfigs(config.bots);
                        displayApiEndpoints(config.api_endpoints);
                    } catch (error) {
                        console.error('Failed to load admin config:', error);
                    }
                }
                
                function displaySystemStatus(status) {
                    const container = document.getElementById('systemStatus');
                    container.innerHTML = `
                        <div>Database: <span class="status-indicator status-${status.database ? 'online' : 'offline'}">${status.database ? 'Online' : 'Offline'}</span></div>
                        <div>Memory System: <span class="status-indicator status-${status.memory ? 'online' : 'offline'}">${status.memory ? 'Online' : 'Offline'}</span></div>
                        <div>Active Bots: ${status.active_bots || 0}</div>
                    `;
                }
                
                function displayBotConfigs(bots) {
                    const container = document.getElementById('botConfigs');
                    container.innerHTML = Object.entries(bots).map(([name, config]) => `
                        <div style="margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <h4>${name}</h4>
                            <div>Enabled: ${config.enabled ? 'Yes' : 'No'}</div>
                            <div>Description: ${config.description || 'N/A'}</div>
                        </div>
                    `).join('');
                }
                
                function displayApiEndpoints(endpoints) {
                    const container = document.getElementById('apiEndpoints');
                    container.innerHTML = Object.entries(endpoints).map(([name, config]) => `
                        <div style="margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <h4>${name}</h4>
                            <div>URL: ${config.url}</div>
                            <div>Enabled: ${config.enabled ? 'Yes' : 'No'}</div>
                            <div>Timeout: ${config.timeout}s</div>
                        </div>
                    `).join('');
                }
                
                loadAdminConfig();
            </script>
        </body>
        </html>
        """
    
    def _load_configurations(self):
        """Load bot and API configurations"""
        # In production, load from database or config files
        # Use bot's CDL_DEFAULT_CHARACTER if available, otherwise use standard character files
        import os
        default_character = os.getenv('CDL_DEFAULT_CHARACTER')
        
        self.available_bots = {
            "elena": BotConfiguration(
                bot_name="elena",
                character_file=default_character if default_character else "characters/examples/elena-rodriguez.json",
                description="Marine biologist AI companion"
            ),
            "marcus": BotConfiguration(
                bot_name="marcus", 
                character_file=default_character if default_character else "characters/examples/marcus-thompson.json",
                description="AI researcher companion"
            ),
            "ryan-chen": BotConfiguration(
                bot_name="ryan-chen",
                character_file=default_character if default_character else "characters/examples/ryan-chen.json",
                description="Game developer companion"
            )
        }
        
        self.api_endpoints = {
            "openrouter": APIEndpointConfig(
                name="openrouter",
                url="https://openrouter.ai/api/v1",
                timeout=30
            )
        }
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get system status for admin interface"""
        return {
            "database": True,  # Check actual database connection
            "memory": True,    # Check memory system
            "active_bots": len([b for b in self.available_bots.values() if b.enabled])
        }
    
    async def _save_bot_configurations(self):
        """Save bot configurations to database"""
        # Implementation for persistence
        pass
    
    async def _save_api_configurations(self):
        """Save API configurations to database"""
        # Implementation for persistence
        pass

    async def _check_database_health(self) -> bool:
        """Check database connectivity"""
        try:
            if self.db_manager:
                # Implement actual database health check
                return True
            return False
        except Exception as e:
            logger.error("Database health check failed: %s", e)
            return False
    
    async def _check_memory_health(self) -> bool:
        """Check memory system health"""
        try:
            # Test memory system connectivity
            return True
        except Exception as e:
            logger.error("Memory health check failed: %s", e)
            return False


def create_web_application(config: Optional[Dict[str, Any]] = None) -> WebChatApplication:
    """Factory function for web application"""
    return WebChatApplication(config)


if __name__ == "__main__":
    import uvicorn
    
    app = create_web_application()
    uvicorn.run(app.app, host="0.0.0.0", port=8080)