"""
Simplified Web Chat Service

A lightweight web interface that communicates with existing WhisperEngine bots
via API calls rather than direct integration. This allows the web UI to be
completely separate from the bot infrastructure.
"""

import json
import logging
import os
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    WEB_AVAILABLE = True
except ImportError:
    FastAPI = None
    WEB_AVAILABLE = False

logger = logging.getLogger(__name__)


# Pydantic models
class ChatMessage(BaseModel):
    """Chat message for web interface"""
    content: str = Field(..., min_length=1, max_length=4000)
    bot_name: str = Field(..., min_length=1, max_length=50)
    message_type: str = Field(default="text")


class UserSession(BaseModel):
    """User session for web interface"""
    username: str = Field(..., min_length=3, max_length=30)
    display_name: Optional[str] = Field(None, max_length=50)
    session_id: str


class WebSocketManager:
    """Manages WebSocket connections for real-time chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_sessions: Dict[str, str] = {}  # websocket_str_id -> user_id
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect user to WebSocket"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        websocket_id = str(id(websocket))
        self.user_sessions[websocket_id] = user_id
        
        logger.info("WebSocket connected for user: %s", user_id)
        
        # Send welcome message
        await self.send_to_user(user_id, {
            "type": "system",
            "content": "Connected to WhisperEngine Web UI",
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect user from WebSocket"""
        websocket_id = str(id(websocket))
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


class SimpleBotConnector:
    """Simple connector to communicate with existing bots"""
    
    def __init__(self):
        self.bot_ports = {
            "elena": 9091,
            "marcus": 9092,
            "marcus-chen": 9093,
            "dream": 9094,
            "gabriel": 9095
        }
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def send_message_to_bot(self, bot_name: str, user_id: str, message: str) -> str:
        """Send message to bot via HTTP and get response"""
        bot_port = self.bot_ports.get(bot_name)
        if not bot_port:
            return f"Sorry, bot '{bot_name}' is not available."
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Try to send to bot's health endpoint first to check if it's running
                health_url = f"http://localhost:{bot_port}/health"
                try:
                    async with session.get(health_url) as response:
                        if response.status != 200:
                            return f"Bot '{bot_name}' is not responding (health check failed)."
                except Exception:
                    return f"Bot '{bot_name}' is not running. Start it with: ./multi-bot.sh start {bot_name}"
                
                # For now, simulate bot response since we don't have HTTP endpoints yet
                # In production, this would call the bot's REST API
                bot_responses = {
                    "elena": f"🌊 Hi! I'm Elena Rodriguez, marine biologist. You said: '{message[:50]}...' Let me share some ocean insights!",
                    "marcus": f"🤖 Hello! Marcus Thompson here, AI researcher. Regarding '{message[:50]}...', let me provide some technical perspective.",
                    "marcus-chen": f"🎮 Hey! Marcus Chen, game developer. About '{message[:50]}...', that reminds me of some game design patterns.",
                    "dream": f"✨ Greetings, mortal. I am Dream of the Endless. Your words '{message[:50]}...' echo through the realm of dreams.",
                    "gabriel": f"👼 Peace be with you. Gabriel Tether here. Your message '{message[:50]}...' brings to mind some spiritual reflections."
                }
                
                response_text = bot_responses.get(bot_name, f"Response from {bot_name}: {message}")
                return response_text
                
        except Exception as e:
            logger.error("Failed to communicate with bot %s: %s", bot_name, e)
            return f"Sorry, I couldn't reach {bot_name} right now. Please try again later."
    
    def get_available_bots(self) -> List[Dict[str, Any]]:
        """Get list of available bots"""
        return [
            {"name": "elena", "display_name": "Elena Rodriguez", "description": "Marine biologist AI companion", "emoji": "🌊"},
            {"name": "marcus", "display_name": "Marcus Thompson", "description": "AI researcher companion", "emoji": "🤖"},
            {"name": "marcus-chen", "display_name": "Marcus Chen", "description": "Game developer companion", "emoji": "🎮"},
            {"name": "dream", "display_name": "Dream of the Endless", "description": "Mythological being", "emoji": "✨"},
            {"name": "gabriel", "display_name": "Gabriel Tether", "description": "Spiritual guide", "emoji": "👼"}
        ]


class SimpleWebChatApp:
    """Simplified web chat application"""
    
    def __init__(self):
        if not WEB_AVAILABLE:
            raise ImportError("FastAPI not available - install web dependencies")
        
        self.app = FastAPI(
            title="WhisperEngine Web Interface",
            description="ChatGPT-like interface for WhisperEngine AI",
            version="1.0.0"
        )
        
        self.websocket_manager = WebSocketManager()
        self.bot_connector = SimpleBotConnector()
        self.user_sessions: Dict[str, UserSession] = {}
        
        self._setup_middleware()
        self._setup_routes()
        
        logger.info("WhisperEngine Web UI initialized (simple mode)")
    
    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            """Health check for container orchestration"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "whisperengine-web-ui"
            }
        
        # Main chat interface
        @self.app.get("/", response_class=HTMLResponse)
        async def chat_interface():
            """Serve main chat interface"""
            return self._get_chat_html()
        
        # API endpoints
        @self.app.get("/api/bots")
        async def get_available_bots():
            """Get list of available bots"""
            return {"bots": self.bot_connector.get_available_bots()}
        
        @self.app.post("/api/login")
        async def login_user(username: str, display_name: Optional[str] = None):
            """Simple login (no authentication for demo)"""
            session_id = f"web_{username}_{datetime.now().timestamp()}"
            user_session = UserSession(
                username=username,
                display_name=display_name or username,
                session_id=session_id
            )
            self.user_sessions[session_id] = user_session
            return {"session_token": session_id, "user": user_session.dict()}
        
        @self.app.post("/api/chat")
        async def send_message(message_data: ChatMessage, session_token: str):
            """Send chat message to bot"""
            user_session = self.user_sessions.get(session_token)
            if not user_session:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            try:
                # Send to bot and get response
                bot_response = await self.bot_connector.send_message_to_bot(
                    bot_name=message_data.bot_name,
                    user_id=user_session.session_id,
                    message=message_data.content
                )
                
                # Send response via WebSocket
                await self.websocket_manager.send_to_user(user_session.session_id, {
                    "type": "bot_response",
                    "content": bot_response,
                    "bot_name": message_data.bot_name,
                    "timestamp": datetime.now().isoformat()
                })
                
                return {"success": True, "response": bot_response}
                
            except Exception as e:
                logger.error("Chat message failed: %s", e)
                raise HTTPException(status_code=500, detail="Message processing failed")
        
        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, token: str):
            """WebSocket endpoint for real-time chat"""
            user_session = self.user_sessions.get(token)
            if not user_session:
                await websocket.close(code=4001, reason="Invalid session")
                return
            
            await self.websocket_manager.connect(websocket, user_session.session_id)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    if message_data.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)
    
    def _get_chat_html(self) -> str:
        """Generate enhanced chat interface HTML"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>WhisperEngine Chat</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    background: #f5f5f5;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                
                .header { 
                    background: #2c3e50; 
                    color: white; 
                    padding: 1rem; 
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center;
                }
                
                .login-form { 
                    background: white; 
                    padding: 2rem; 
                    border-radius: 8px; 
                    max-width: 400px; 
                    margin: 2rem auto;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                
                .chat-container { 
                    display: none; 
                    flex: 1; 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    width: 100%; 
                    background: white;
                    border-radius: 8px 8px 0 0;
                    overflow: hidden;
                }
                
                .chat-header {
                    background: #34495e;
                    color: white;
                    padding: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }
                
                .bot-selector { 
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    cursor: pointer;
                }
                
                .chat-area { 
                    display: flex; 
                    height: 600px; 
                }
                
                .messages { 
                    flex: 1; 
                    padding: 1rem; 
                    overflow-y: auto; 
                    background: #fafafa;
                }
                
                .message { 
                    margin-bottom: 1rem; 
                    display: flex; 
                    gap: 0.5rem;
                }
                
                .message.user { 
                    justify-content: flex-end; 
                }
                
                .message-content { 
                    max-width: 70%; 
                    padding: 0.75rem 1rem; 
                    border-radius: 18px; 
                    word-wrap: break-word;
                }
                
                .message.user .message-content { 
                    background: #3498db; 
                    color: white; 
                }
                
                .message.bot .message-content { 
                    background: white; 
                    border: 1px solid #ddd; 
                    position: relative;
                }
                
                .bot-info {
                    font-size: 0.8rem;
                    color: #666;
                    margin-bottom: 0.25rem;
                }
                
                .input-area { 
                    padding: 1rem; 
                    border-top: 1px solid #ddd; 
                    background: white;
                }
                
                .input-container {
                    display: flex;
                    gap: 0.5rem;
                }
                
                .message-input { 
                    flex: 1;
                    padding: 0.75rem; 
                    border: 1px solid #ddd; 
                    border-radius: 20px; 
                    outline: none;
                }
                
                .send-button { 
                    padding: 0.75rem 1.5rem; 
                    background: #3498db; 
                    color: white; 
                    border: none; 
                    border-radius: 20px; 
                    cursor: pointer;
                }
                
                .status { 
                    padding: 0.5rem; 
                    text-align: center; 
                    font-size: 0.9rem; 
                }
                
                .status.connected { background: #d4edda; color: #155724; }
                .status.disconnected { background: #f8d7da; color: #721c24; }
                
                .form-group { 
                    margin-bottom: 1rem; 
                }
                
                .form-group label { 
                    display: block; 
                    margin-bottom: 0.5rem; 
                    font-weight: bold; 
                }
                
                .form-group input { 
                    width: 100%; 
                    padding: 0.75rem; 
                    border: 1px solid #ddd; 
                    border-radius: 4px; 
                }
                
                .btn { 
                    padding: 0.75rem 1.5rem; 
                    background: #3498db; 
                    color: white; 
                    border: none; 
                    border-radius: 4px; 
                    cursor: pointer; 
                    width: 100%;
                }
                
                .typing-indicator {
                    font-style: italic;
                    color: #666;
                    padding: 0.5rem 1rem;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 WhisperEngine</h1>
                <div id="userInfo"></div>
            </div>
            
            <div id="loginForm" class="login-form">
                <h2>Welcome to WhisperEngine</h2>
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" id="username" placeholder="Enter your username">
                </div>
                <div class="form-group">
                    <label>Display Name (optional):</label>
                    <input type="text" id="displayName" placeholder="Your display name">
                </div>
                <button onclick="login()" class="btn">Start Chatting</button>
            </div>
            
            <div id="chatContainer" class="chat-container">
                <div class="chat-header">
                    <span>Chat with:</span>
                    <select id="botSelector" class="bot-selector">
                        <option value="">Loading bots...</option>
                    </select>
                    <div id="connectionStatus" class="status">Connecting...</div>
                </div>
                
                <div class="chat-area">
                    <div class="messages" id="messages"></div>
                </div>
                
                <div class="input-area">
                    <div class="input-container">
                        <input type="text" id="messageInput" class="message-input" placeholder="Type your message...">
                        <button onclick="sendMessage()" class="send-button">Send</button>
                    </div>
                </div>
            </div>
            
            <script>
                let ws = null;
                let sessionToken = null;
                let currentBot = 'elena';
                let isTyping = false;
                
                async function login() {
                    const username = document.getElementById('username').value.trim();
                    if (!username) {
                        alert('Please enter a username');
                        return;
                    }
                    
                    const displayName = document.getElementById('displayName').value.trim();
                    
                    try {
                        const response = await fetch('/api/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                            body: `username=${encodeURIComponent(username)}&display_name=${encodeURIComponent(displayName)}`
                        });
                        
                        const data = await response.json();
                        sessionToken = data.session_token;
                        
                        document.getElementById('loginForm').style.display = 'none';
                        document.getElementById('chatContainer').style.display = 'flex';
                        document.getElementById('userInfo').textContent = `Logged in as: ${data.user.display_name}`;
                        
                        await loadBots();
                        connectWebSocket();
                        
                    } catch (error) {
                        alert('Login failed: ' + error.message);
                    }
                }
                
                async function loadBots() {
                    try {
                        const response = await fetch('/api/bots');
                        const data = await response.json();
                        
                        const selector = document.getElementById('botSelector');
                        selector.innerHTML = '';
                        
                        data.bots.forEach(bot => {
                            const option = document.createElement('option');
                            option.value = bot.name;
                            option.textContent = `${bot.emoji} ${bot.display_name}`;
                            selector.appendChild(option);
                        });
                        
                        selector.value = currentBot;
                    } catch (error) {
                        console.error('Failed to load bots:', error);
                    }
                }
                
                function connectWebSocket() {
                    if (!sessionToken) return;
                    
                    ws = new WebSocket(`ws://localhost:8080/ws?token=${sessionToken}`);
                    
                    ws.onopen = () => {
                        updateConnectionStatus('connected');
                    };
                    
                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        if (data.type === 'bot_response') {
                            addMessage(data.content, 'bot', data.bot_name);
                        } else if (data.type === 'system') {
                            addMessage(data.content, 'system');
                        }
                    };
                    
                    ws.onclose = () => {
                        updateConnectionStatus('disconnected');
                        setTimeout(connectWebSocket, 3000);
                    };
                    
                    ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        updateConnectionStatus('error');
                    };
                }
                
                function updateConnectionStatus(status) {
                    const statusEl = document.getElementById('connectionStatus');
                    statusEl.className = `status ${status}`;
                    statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                }
                
                function addMessage(content, type, botName = '') {
                    const messages = document.getElementById('messages');
                    const message = document.createElement('div');
                    message.className = `message ${type}`;
                    
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    
                    if (type === 'bot' && botName) {
                        const botInfo = document.createElement('div');
                        botInfo.className = 'bot-info';
                        botInfo.textContent = botName;
                        messageContent.appendChild(botInfo);
                    }
                    
                    const textContent = document.createElement('div');
                    textContent.textContent = content;
                    messageContent.appendChild(textContent);
                    
                    message.appendChild(messageContent);
                    messages.appendChild(message);
                    messages.scrollTop = messages.scrollHeight;
                }
                
                async function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (!message || !sessionToken) return;
                    
                    addMessage(message, 'user');
                    input.value = '';
                    
                    try {
                        const response = await fetch('/api/chat', {
                            method: 'POST',
                            headers: { 
                                'Content-Type': 'application/json',
                                'session_token': sessionToken
                            },
                            body: JSON.stringify({
                                content: message,
                                bot_name: currentBot
                            })
                        });
                        
                        if (!response.ok) {
                            throw new Error('Failed to send message');
                        }
                        
                    } catch (error) {
                        addMessage('Error: Failed to send message', 'system');
                        console.error('Send message error:', error);
                    }
                }
                
                document.getElementById('botSelector').addEventListener('change', (e) => {
                    currentBot = e.target.value;
                });
                
                document.getElementById('messageInput').addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') sendMessage();
                });
                
                document.getElementById('username').addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') login();
                });
            </script>
        </body>
        </html>
        """


def create_simple_web_app() -> SimpleWebChatApp:
    """Factory function for simple web application"""
    return SimpleWebChatApp()


# For uvicorn
app = create_simple_web_app().app

if __name__ == "__main__":
    import uvicorn
    
    web_app = create_simple_web_app()
    uvicorn.run(web_app.app, host="0.0.0.0", port=8080)