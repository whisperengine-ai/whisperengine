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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Universal Identity System imports (with fallback)
try:
    from src.identity.universal_identity import (
        create_identity_manager, 
        PlatformIdentity, 
        ChatPlatform
    )
    UNIVERSAL_IDENTITY_AVAILABLE = True
except ImportError:
    UNIVERSAL_IDENTITY_AVAILABLE = False

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
    universal_user_id: Optional[str] = Field(None)  # For cross-platform identity


class MultiBotConversation(BaseModel):
    """Multi-bot conversation configuration"""
    conversation_id: str
    participants: List[str]  # Bot names
    topic: Optional[str] = Field(None, max_length=200)
    created_by: str  # User ID
    created_at: datetime = Field(default_factory=datetime.now)
    active: bool = True


class MultiBotMessage(BaseModel):
    """Message in multi-bot conversation"""
    conversation_id: str
    sender: str  # Bot name or user ID
    content: str = Field(..., min_length=1, max_length=4000)
    message_type: str = Field(default="text")
    timestamp: datetime = Field(default_factory=datetime.now)
    responded_to: Optional[str] = None  # Previous message ID


class ConversationInvitation(BaseModel):
    """Invitation to start multi-bot conversation"""
    bot_names: List[str]  # Bot names to include
    topic: Optional[str] = Field(None, max_length=200)
    initial_prompt: Optional[str] = Field(None, max_length=1000)


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
        # Check if running in Docker by looking for container hostname patterns
        self.is_docker = os.path.exists('/.dockerenv') or os.environ.get('RUNNING_IN_DOCKER', '').lower() == 'true'
        
        if self.is_docker:
            # Use container names when running in Docker
            self.bot_hosts = {
                "elena": "whisperengine-elena-bot:9091",
                "marcus": "whisperengine-marcus-bot:9092", 
                "ryan-chen": "whisperengine-ryan-chen-bot:9093",
                "dream": "whisperengine-dream-bot:9094",
                "gabriel": "whisperengine-gabriel-bot:9095"
            }
        else:
            # Use localhost when running natively
            self.bot_hosts = {
                "elena": "localhost:9091",
                "marcus": "localhost:9092",
                "ryan-chen": "localhost:9093", 
                "dream": "localhost:9094",
                "gabriel": "localhost:9095"
            }
        
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def send_message_to_bot(self, bot_name: str, user_id: str, message: str) -> str:
        """Send message to bot via HTTP chat API and get response"""
        bot_host = self.bot_hosts.get(bot_name)
        if not bot_host:
            return f"Sorry, bot '{bot_name}' is not available."
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Check if bot is running via health endpoint
                health_url = f"http://{bot_host}/health"
                try:
                    async with session.get(health_url) as response:
                        if response.status != 200:
                            return f"Bot '{bot_name}' is not responding (health check failed)."
                except Exception:
                    return f"Bot '{bot_name}' is not running. Start it with: ./multi-bot.sh start {bot_name}"
                
                # Send message to bot's chat API endpoint
                chat_url = f"http://{bot_host}/api/chat"
                chat_payload = {
                    "user_id": user_id,
                    "message": message,
                    "platform": "WEB_UI"
                }
                
                try:
                    async with session.post(chat_url, json=chat_payload) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            if response_data.get("success"):
                                return response_data.get("response", "No response from bot")
                            else:
                                logger.warning(f"Bot {bot_name} returned unsuccessful response: {response_data}")
                                return f"Bot '{bot_name}' couldn't process the message. Please try again."
                        else:
                            logger.warning(f"Chat API returned status {response.status} for bot {bot_name}")
                            # Fall back to demo responses if chat API not available
                            return self._get_fallback_response(bot_name, message)
                            
                except Exception as chat_error:
                    logger.warning(f"Chat API not available for bot {bot_name}: {chat_error}")
                    # Fall back to demo responses if chat API fails
                    return self._get_fallback_response(bot_name, message)
                
        except Exception as e:
            logger.error("Failed to communicate with bot %s: %s", bot_name, e)
            return f"Sorry, I couldn't reach {bot_name} right now. Please try again later."
    
    async def send_message_to_bot_stream(self, bot_name: str, user_id: str, message: str):
        """Send message to bot and get streaming response"""
        bot_host = self.bot_hosts.get(bot_name)
        if not bot_host:
            yield {"error": f"Bot '{bot_name}' is not available"}
            return
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Check if bot is running via health endpoint
                health_url = f"http://{bot_host}/health"
                try:
                    async with session.get(health_url) as response:
                        if response.status != 200:
                            yield {"error": f"Bot '{bot_name}' is not responding"}
                            return
                except Exception:
                    yield {"error": f"Bot '{bot_name}' is not running"}
                    return
                
                # Try streaming chat API endpoint first
                stream_url = f"http://{bot_host}/api/chat/stream"
                chat_payload = {
                    "user_id": user_id,
                    "message": message,
                    "platform": "WEB_UI"
                }
                
                try:
                    async with session.post(stream_url, json=chat_payload) as response:
                        if response.status == 200:
                            # Process streaming response
                            async for line in response.content:
                                if line:
                                    line_str = line.decode('utf-8').strip()
                                    if line_str.startswith('data: '):
                                        data = line_str[6:]  # Remove 'data: ' prefix
                                        if data.strip() == '[DONE]':
                                            break
                                        try:
                                            chunk = json.loads(data)
                                            yield chunk
                                        except json.JSONDecodeError:
                                            continue
                        else:
                            # Fallback to regular API if streaming not available
                            regular_response = await self.send_message_to_bot(bot_name, user_id, message)
                            # Simulate streaming by yielding each word
                            words = regular_response.split()
                            for word in words:
                                yield {
                                    "choices": [{
                                        "delta": {"content": word + " "},
                                        "finish_reason": None
                                    }]
                                }
                                await asyncio.sleep(0.05)  # 50ms delay between words
                            
                            # Send final completion
                            yield {
                                "choices": [{
                                    "delta": {},
                                    "finish_reason": "stop"
                                }]
                            }
                            
                except Exception as stream_error:
                    logger.warning(f"Streaming API not available for bot {bot_name}: {stream_error}")
                    # Fallback to regular response with simulated streaming
                    fallback_response = self._get_fallback_response(bot_name, message)
                    words = fallback_response.split()
                    for word in words:
                        yield {
                            "choices": [{
                                "delta": {"content": word + " "},
                                "finish_reason": None
                            }]
                        }
                        await asyncio.sleep(0.1)  # Slower for demo mode
                
        except Exception as e:
            logger.error("Failed to get streaming response from bot %s: %s", bot_name, e)
            yield {"error": f"Streaming failed for {bot_name}"}
    
    def _get_fallback_response(self, bot_name: str, message: str) -> str:
        """Get fallback demo response when chat API is unavailable"""
        bot_responses = {
            "elena": f"🌊 Hi! I'm Elena Rodriguez, marine biologist. You said: '{message[:50]}...' Let me share some ocean insights! (Demo mode - chat API not available)",
            "marcus": f"🤖 Hello! Marcus Thompson here, AI researcher. Regarding '{message[:50]}...', let me provide some technical perspective. (Demo mode - chat API not available)",
            "ryan-chen": f"🎮 Hey! Ryan Chen, game developer. About '{message[:50]}...', that reminds me of some game design patterns. (Demo mode - chat API not available)",
            "dream": f"✨ Greetings, mortal. I am Dream of the Endless. Your words '{message[:50]}...' echo through the realm of dreams. (Demo mode - chat API not available)",
            "gabriel": f"👼 Peace be with you. Gabriel Tether here. Your message '{message[:50]}...' brings to mind some spiritual reflections. (Demo mode - chat API not available)"
        }
        
        return bot_responses.get(bot_name, f"Response from {bot_name}: {message} (Demo mode - chat API not available)")
    
    def get_available_bots(self) -> List[Dict[str, Any]]:
        """Get list of available bots"""
        return [
            {"name": "elena", "display_name": "Elena Rodriguez", "description": "Marine biologist AI companion", "emoji": "🌊"},
            {"name": "marcus", "display_name": "Marcus Thompson", "description": "AI researcher companion", "emoji": "🤖"},
            {"name": "ryan-chen", "display_name": "Ryan Chen", "description": "Game developer companion", "emoji": "🎮"},
            {"name": "dream", "display_name": "Dream of the Endless", "description": "Mythological being", "emoji": "✨"},
            {"name": "gabriel", "display_name": "Gabriel Tether", "description": "Spiritual guide", "emoji": "👼"}
        ]


class MultiBotConversationManager:
    """Manages multi-bot conversations"""
    
    def __init__(self, bot_connector: SimpleBotConnector):
        self.bot_connector = bot_connector
        self.active_conversations: Dict[str, MultiBotConversation] = {}
        self.conversation_messages: Dict[str, List[MultiBotMessage]] = {}
        self.conversation_counter = 0
    
    def create_conversation(self, user_id: str, bot_names: List[str], topic: Optional[str] = None) -> str:
        """Create a new multi-bot conversation"""
        self.conversation_counter += 1
        conversation_id = f"multibot_{self.conversation_counter}_{int(datetime.now().timestamp())}"
        
        conversation = MultiBotConversation(
            conversation_id=conversation_id,
            participants=bot_names,
            topic=topic,
            created_by=user_id
        )
        
        self.active_conversations[conversation_id] = conversation
        self.conversation_messages[conversation_id] = []
        
        logger.info(f"Created multi-bot conversation {conversation_id} with bots: {bot_names}")
        return conversation_id
    
    async def create_conversation_async(self, bot_names: List[str], topic: Optional[str] = None, created_by: str = "", initial_prompt: Optional[str] = None) -> MultiBotConversation:
        """Async version of create_conversation for API compatibility"""
        conversation_id = self.create_conversation(created_by, bot_names, topic)
        return self.active_conversations[conversation_id]
    
    def get_conversation(self, conversation_id: str) -> Optional[MultiBotConversation]:
        """Get conversation by ID"""
        return self.active_conversations.get(conversation_id)
    
    def get_user_conversations(self, user_id: str) -> List[MultiBotConversation]:
        """Get all conversations for a user"""
        return [conv for conv in self.active_conversations.values() if conv.created_by == user_id]
    
    async def process_message(self, conversation_id: str, user_message: MultiBotMessage) -> List[Dict[str, Any]]:
        """Process a message in multi-bot conversation"""
        return await self.send_message_to_conversation(
            conversation_id=conversation_id,
            sender=user_message.sender,
            message=user_message.content,
            user_id=user_message.sender
        )
    
    def get_conversation_messages(self, conversation_id: str) -> List[MultiBotMessage]:
        """Get all messages in a conversation"""
        return self.conversation_messages.get(conversation_id, [])
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]
            if conversation_id in self.conversation_messages:
                del self.conversation_messages[conversation_id]
            return True
        return False
    
    async def send_message_to_conversation(self, conversation_id: str, sender: str, message: str, user_id: str) -> List[Dict[str, Any]]:
        """Send message to multi-bot conversation and get all bot responses"""
        if conversation_id not in self.active_conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = self.active_conversations[conversation_id]
        
        # Add user message to conversation
        user_message = MultiBotMessage(
            conversation_id=conversation_id,
            sender=sender,
            content=message
        )
        self.conversation_messages[conversation_id].append(user_message)
        
        # Get conversation context for bots
        context = self._build_conversation_context(conversation_id)
        
        # Send message to each bot and collect responses
        responses = []
        for bot_name in conversation.participants:
            try:
                # Create context-aware prompt for bot
                bot_prompt = self._create_multibot_prompt(bot_name, message, context, conversation.topic)
                
                # Get bot response
                bot_response = await self.bot_connector.send_message_to_bot(bot_name, user_id, bot_prompt)
                
                # Add bot response to conversation
                bot_message = MultiBotMessage(
                    conversation_id=conversation_id,
                    sender=bot_name,
                    content=bot_response
                )
                self.conversation_messages[conversation_id].append(bot_message)
                
                responses.append({
                    "bot_name": bot_name,
                    "response": bot_response,
                    "timestamp": bot_message.timestamp.isoformat()
                })
                
                # Add small delay to make conversation feel more natural
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to get response from bot {bot_name}: {e}")
                responses.append({
                    "bot_name": bot_name,
                    "response": f"Sorry, {bot_name} couldn't respond right now.",
                    "timestamp": datetime.now().isoformat(),
                    "error": True
                })
        
        return responses
    
    def _build_conversation_context(self, conversation_id: str, max_messages: int = 6) -> str:
        """Build conversation context for bots"""
        if conversation_id not in self.conversation_messages:
            return ""
        
        messages = self.conversation_messages[conversation_id][-max_messages:]
        context_parts = []
        
        for msg in messages:
            if msg.sender.startswith("user_"):
                context_parts.append(f"User: {msg.content}")
            else:
                context_parts.append(f"{msg.sender}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def _create_multibot_prompt(self, bot_name: str, current_message: str, context: str, topic: Optional[str] = None) -> str:
        """Create context-aware prompt for bot in multi-bot conversation"""
        prompt_parts = []
        
        if topic:
            prompt_parts.append(f"Topic: {topic}")
        
        prompt_parts.append("You are participating in a multi-bot conversation with other AI companions.")
        
        if context:
            prompt_parts.append(f"Recent conversation:\n{context}")
        
        prompt_parts.append(f"Current message: {current_message}")
        prompt_parts.append("Please respond naturally as your character, considering what other bots have said.")
        
        return "\n\n".join(prompt_parts)
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        if conversation_id not in self.conversation_messages:
            return []
        
        messages = []
        for msg in self.conversation_messages[conversation_id]:
            messages.append({
                "sender": msg.sender,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "is_bot": not msg.sender.startswith("user_")
            })
        
        return messages
    
    def list_active_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """List active conversations for user"""
        user_conversations = []
        for conversation in self.active_conversations.values():
            if conversation.created_by == user_id and conversation.active:
                user_conversations.append({
                    "conversation_id": conversation.conversation_id,
                    "participants": conversation.participants,
                    "topic": conversation.topic,
                    "created_at": conversation.created_at.isoformat(),
                    "message_count": len(self.conversation_messages.get(conversation.conversation_id, []))
                })
        
        return user_conversations


class SimpleWebChatApp:
    """Simplified web chat application"""
    
    def __init__(self):
        self.app = FastAPI(
            title="WhisperEngine Web Interface",
            description="ChatGPT-like interface for WhisperEngine AI",
            version="1.0.0"
        )
        
        self.websocket_manager = WebSocketManager()
        self.bot_connector = SimpleBotConnector()
        self.conversation_manager = MultiBotConversationManager(self.bot_connector)
        self.user_sessions: Dict[str, UserSession] = {}
        self.postgres_pool = None  # Will be initialized on startup
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_startup_events()
        
        logger.info("WhisperEngine Web UI initialized (simple mode)")
    
    def _setup_startup_events(self):
        """Setup startup and shutdown events"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize database connection on startup"""
            await self._initialize_database()
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Clean up database connections on shutdown"""
            if self.postgres_pool:
                await self.postgres_pool.close()
                logger.info("PostgreSQL connection pool closed")

    async def _initialize_database(self):
        """Initialize PostgreSQL connection and create tables"""
        try:
            logger.info("Initializing PostgreSQL connection for web interface...")
            from src.utils.postgresql_user_db import PostgreSQLUserDB
            
            postgres_db = PostgreSQLUserDB()
            await postgres_db.initialize()
            self.postgres_pool = postgres_db.pool
            
            # Create Universal Identity tables
            await self._create_universal_identity_tables()
            
            logger.info("✅ Database initialized successfully for web interface")
            
        except Exception as e:
            logger.error("Failed to initialize database: %s", e)
            logger.warning("Web UI will continue without persistent identity storage")

    async def _create_universal_identity_tables(self):
        """Create Universal Identity tables if they don't exist"""
        if not self.postgres_pool:
            return
            
        try:
            async with self.postgres_pool.acquire() as conn:
                # Read and execute the SQL script
                sql_script = """
                -- Universal Users Table
                CREATE TABLE IF NOT EXISTS universal_users (
                    universal_id VARCHAR(255) PRIMARY KEY,
                    primary_username VARCHAR(255) NOT NULL,
                    display_name VARCHAR(255),
                    email VARCHAR(255),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    preferences TEXT DEFAULT '{}',
                    privacy_settings TEXT DEFAULT '{}'
                );

                -- Platform Identities Table
                CREATE TABLE IF NOT EXISTS platform_identities (
                    id SERIAL PRIMARY KEY,
                    universal_id VARCHAR(255) NOT NULL REFERENCES universal_users(universal_id) ON DELETE CASCADE,
                    platform VARCHAR(50) NOT NULL,
                    platform_user_id VARCHAR(255) NOT NULL,
                    username VARCHAR(255) NOT NULL,
                    display_name VARCHAR(255),
                    email VARCHAR(255),
                    verified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, platform_user_id)
                );

                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_platform_identities_universal_id ON platform_identities(universal_id);
                CREATE INDEX IF NOT EXISTS idx_platform_identities_platform_user ON platform_identities(platform, platform_user_id);
                CREATE INDEX IF NOT EXISTS idx_universal_users_username ON universal_users(primary_username);
                CREATE INDEX IF NOT EXISTS idx_universal_users_email ON universal_users(email);
                """
                
                await conn.execute(sql_script)
                logger.info("✅ Universal Identity tables created/verified")
                
        except Exception as e:
            logger.error("Failed to create Universal Identity tables: %s", e)
    
    def _extract_user_id_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from session token"""
        user_session = self.user_sessions.get(token)
        if user_session:
            return user_session.session_id
        return None
    
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
        
        # Include voice API routes
        try:
            from src.web.voice_api import voice_router
            self.app.include_router(voice_router)
            logger.info("Voice API routes included")
        except Exception as e:
            logger.warning("Failed to include voice API routes: %s", e)
        
        # Mount static files for voice chat
        try:
            from pathlib import Path
            static_path = Path(__file__).parent / "static"
            if static_path.exists():
                self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
                logger.info("Static files mounted at /static")
        except Exception as e:
            logger.warning("Failed to mount static files: %s", e)
        
        # API endpoints
        @self.app.get("/api/bots")
        async def get_available_bots():
            """Get list of available bots"""
            return {"bots": self.bot_connector.get_available_bots()}
        
        @self.app.post("/api/login")
        async def login_user(request: Request):
            """Login with Universal Identity support and account discovery"""
            try:
                logger.info("Login attempt started")
                form_data = await request.form()
                username = str(form_data.get("username", ""))
                display_name = str(form_data.get("display_name", "")) if form_data.get("display_name") else None
                discord_id = str(form_data.get("discord_id", "")) if form_data.get("discord_id") else None
                
                logger.info(f"Login data: username={username}, display_name={display_name}, discord_id={discord_id}")
                
                if not username:
                    raise HTTPException(status_code=400, detail="Username is required")
                
                # Simplified login - just create a session for now
                user_id = f"web_{username}_{datetime.now().timestamp()}"
                session_id = user_id
                
                user_session = UserSession(
                    username=username,
                    display_name=display_name or username,
                    session_id=session_id,
                    universal_user_id=None  # Simplified for debugging
                )
                
                logger.info(f"Storing session: {session_id} for user: {username}")
                self.user_sessions[session_id] = user_session
                logger.info(f"Session stored. Total sessions: {len(self.user_sessions)}")
                return {"session_token": session_id, "user": user_session.dict()}
                
            except Exception as login_error:
                logger.error(f"Login failed with error: {login_error}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Login failed: {str(login_error)}")
        
        @self.app.get("/api/multibot-status")
        async def multibot_status():
            """Multi-bot conversation system status"""
            return {
                "status": "active",
                "message": "Multi-bot system is working!"
            }
        
        @self.app.post("/api/chat")
        async def send_message(message_data: ChatMessage, request: Request):
            """Send chat message to bot"""
            session_token = request.headers.get("session_token")
            if not session_token:
                logger.warning("Chat API called without session_token header")
                raise HTTPException(status_code=401, detail="Session token required")
                
            user_session = self.user_sessions.get(session_token)
            if not user_session:
                logger.warning(f"Chat API called with invalid session_token: {session_token}. Available sessions: {list(self.user_sessions.keys())}")
                raise HTTPException(status_code=401, detail="Invalid session - please refresh page and login again")
            
            try:
                # Determine which user ID to use for memory operations
                memory_user_id = user_session.universal_user_id or user_session.session_id
                
                # Send to bot and get response
                bot_response = await self.bot_connector.send_message_to_bot(
                    bot_name=message_data.bot_name,
                    user_id=memory_user_id,  # Use universal ID for cross-platform memory
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
        
        @self.app.post("/api/chat/stream")
        async def send_message_stream(message_data: ChatMessage, request: Request):
            """Send chat message to bot with streaming response"""
            from fastapi.responses import StreamingResponse
            
            session_token = request.headers.get("session_token")
            if not session_token:
                logger.warning("Streaming chat API called without session_token header")
                raise HTTPException(status_code=401, detail="Session token required")
                
            user_session = self.user_sessions.get(session_token)
            if not user_session:
                logger.warning(f"Streaming chat API called with invalid session_token: {session_token}")
                raise HTTPException(status_code=401, detail="Invalid session")
            
            async def generate_streaming_response():
                try:
                    # Determine which user ID to use for memory operations
                    memory_user_id = user_session.universal_user_id or user_session.session_id
                    
                    # Send streaming response to bot
                    full_response = ""
                    async for chunk in self.bot_connector.send_message_to_bot_stream(
                        bot_name=message_data.bot_name,
                        user_id=memory_user_id,
                        message=message_data.content
                    ):
                        # Send each token as it arrives
                        if isinstance(chunk, dict):
                            if chunk.get("choices"):
                                choices = chunk.get("choices", [])
                                if choices and len(choices) > 0:
                                    choice = choices[0]
                                    if isinstance(choice, dict):
                                        delta = choice.get("delta", {})
                                        if isinstance(delta, dict) and delta.get("content"):
                                            token = delta["content"]
                                            full_response += token
                                            yield f"data: {json.dumps({'token': token})}\n\n"
                            elif chunk.get("error"):
                                yield f"data: {json.dumps({'error': chunk['error']})}\n\n"
                                return
                    
                    # Send completion signal
                    yield f"data: {json.dumps({'type': 'complete', 'full_response': full_response})}\n\n"
                    
                except Exception as e:
                    logger.error("Streaming chat message failed: %s", e)
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_streaming_response(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, token: str):
            """WebSocket endpoint for real-time chat"""
            user_session = self.user_sessions.get(token)
            if not user_session:
                logger.warning(f"WebSocket connection rejected: Invalid token {token}. Available sessions: {list(self.user_sessions.keys())}")
                await websocket.close(code=4001, reason="Invalid session - please refresh page and login again")
                return
            
            logger.info(f"WebSocket connected for user: {user_session.session_id}")
            await self.websocket_manager.connect(websocket, user_session.session_id)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    if message_data.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)
        
        # Test multi-bot endpoint
        @self.app.get("/api/multibot-test")
        async def multibot_test():
            """Simple test endpoint"""
            return {"message": "Multi-bot system is ready!"}
    
    def _get_chat_html(self) -> str:
        """Generate enhanced chat interface HTML"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>WhisperEngine - AI Companions</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                
                .header {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(20px);
                    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                    padding: 1rem 2rem;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
                }
                
                .logo {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: #2c3e50;
                }
                
                .logo i {
                    background: linear-gradient(45deg, #3498db, #9b59b6);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-size: 1.8rem;
                }
                
                .login-section {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }
                
                .user-info {
                    display: none;
                    align-items: center;
                    gap: 0.75rem;
                    background: rgba(52, 152, 219, 0.1);
                    padding: 0.5rem 1rem;
                    border-radius: 50px;
                    border: 1px solid rgba(52, 152, 219, 0.2);
                }
                
                .user-avatar {
                    width: 32px;
                    height: 32px;
                    background: linear-gradient(45deg, #3498db, #2ecc71);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 600;
                    font-size: 0.9rem;
                }
                
                .login-form {
                    display: flex;
                    flex-direction: column;
                    gap: 0.75rem;
                    align-items: stretch;
                    max-width: 400px;
                    margin: 0 auto;
                }
                
                .discord-link-section {
                    background: rgba(114, 137, 218, 0.1);
                    border: 1px solid rgba(114, 137, 218, 0.3);
                    border-radius: 10px;
                    padding: 1rem;
                    margin: 0.5rem 0;
                }
                
                .discord-link-section summary {
                    cursor: pointer;
                    font-weight: 600;
                    color: #7289da;
                    margin-bottom: 0.5rem;
                }
                
                .discord-link-section small {
                    display: block;
                    color: #666;
                    font-size: 0.8rem;
                    margin-top: 0.5rem;
                    line-height: 1.4;
                }
                
                .input-modern {
                    padding: 0.75rem 1rem;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    border-radius: 25px;
                    background: rgba(255, 255, 255, 0.9);
                    outline: none;
                    font-size: 0.9rem;
                    transition: all 0.3s ease;
                    backdrop-filter: blur(10px);
                }
                
                .input-modern:focus {
                    border-color: #3498db;
                    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
                }
                
                .btn-primary {
                    background: linear-gradient(45deg, #3498db, #2ecc71);
                    color: white;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 25px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
                }
                
                .btn-primary:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
                }
                
                .main-container {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    padding: 2rem;
                    max-width: 1400px;
                    margin: 0 auto;
                    width: 100%;
                }
                
                .welcome-screen {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    flex: 1;
                    text-align: center;
                    color: white;
                }
                
                .welcome-screen h1 {
                    font-size: 3.5rem;
                    font-weight: 700;
                    margin-bottom: 1rem;
                    background: linear-gradient(45deg, #fff, #ecf0f1);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                
                .welcome-screen p {
                    font-size: 1.3rem;
                    margin-bottom: 2rem;
                    opacity: 0.9;
                    max-width: 600px;
                }
                
                .feature-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 1.5rem;
                    margin-top: 3rem;
                    max-width: 800px;
                }
                
                .feature-card {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 1.5rem;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    transition: all 0.3s ease;
                }
                
                .feature-card:hover {
                    transform: translateY(-5px);
                    background: rgba(255, 255, 255, 0.15);
                }
                
                .feature-card i {
                    font-size: 2rem;
                    margin-bottom: 1rem;
                    color: #ecf0f1;
                }
                
                .feature-card h3 {
                    font-size: 1.2rem;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                    color: white;
                }
                
                .feature-card p {
                    font-size: 0.9rem;
                    opacity: 0.8;
                    line-height: 1.5;
                }
                
                .chat-container {
                    display: none;
                    flex: 1;
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }
                
                .chat-header {
                    background: linear-gradient(135deg, #2c3e50, #3498db);
                    color: white;
                    padding: 1.5rem;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                
                .chat-title {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }
                
                .chat-title h2 {
                    font-size: 1.3rem;
                    font-weight: 600;
                }
                
                .mode-switcher {
                    display: flex;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 25px;
                    padding: 0.25rem;
                    gap: 0.25rem;
                }
                
                .mode-btn {
                    padding: 0.75rem 1.5rem;
                    border: none;
                    background: transparent;
                    color: rgba(255, 255, 255, 0.7);
                    cursor: pointer;
                    border-radius: 20px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    font-size: 0.9rem;
                }
                
                .mode-btn.active {
                    background: rgba(255, 255, 255, 0.2);
                    color: white;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }
                
                .chat-content {
                    display: flex;
                    flex-direction: column;
                    height: 600px;
                }
                
                .chat-subheader {
                    padding: 1rem 1.5rem;
                    background: rgba(52, 152, 219, 0.05);
                    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }
                
                .bot-selector {
                    padding: 0.75rem 1rem;
                    border: 2px solid rgba(52, 152, 219, 0.2);
                    border-radius: 15px;
                    background: white;
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    min-width: 120px;
                }
                
                .bot-selector:hover {
                    border-color: #3498db;
                    box-shadow: 0 2px 10px rgba(52, 152, 219, 0.1);
                }
                
                .conversation-controls {
                    display: flex;
                    gap: 1rem;
                    align-items: center;
                }
                
                .btn-secondary {
                    padding: 0.75rem 1.25rem;
                    background: transparent;
                    border: 2px solid #3498db;
                    color: #3498db;
                    border-radius: 15px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }
                
                .btn-secondary:hover {
                    background: #3498db;
                    color: white;
                }
                
                .messages-container {
                    flex: 1;
                    overflow-y: auto;
                    padding: 1.5rem;
                    background: #fafbfc;
                }
                
                .message {
                    display: flex;
                    margin-bottom: 1.5rem;
                    animation: messageSlide 0.3s ease-out;
                }
                
                @keyframes messageSlide {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                .message.user {
                    justify-content: flex-end;
                }
                
                .message-avatar {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 600;
                    font-size: 0.9rem;
                    margin-right: 1rem;
                    flex-shrink: 0;
                }
                
                .user-avatar-msg {
                    background: linear-gradient(45deg, #3498db, #2ecc71);
                    color: white;
                    order: 2;
                    margin-right: 0;
                    margin-left: 1rem;
                }
                
                .bot-avatar {
                    background: linear-gradient(45deg, #e74c3c, #f39c12);
                    color: white;
                }
                
                .elena-avatar { background: linear-gradient(45deg, #3498db, #2980b9); }
                .marcus-avatar { background: linear-gradient(45deg, #9b59b6, #8e44ad); }
                .ryan-chen-avatar { background: linear-gradient(45deg, #e67e22, #d35400); }
                .dream-avatar { background: linear-gradient(45deg, #2c3e50, #34495e); }
                .gabriel-avatar { background: linear-gradient(45deg, #f39c12, #f1c40f); }
                
                .message-content {
                    max-width: 70%;
                    padding: 1rem 1.25rem;
                    border-radius: 20px;
                    position: relative;
                    word-wrap: break-word;
                    line-height: 1.5;
                }
                
                .message.user .message-content {
                    background: linear-gradient(45deg, #3498db, #2ecc71);
                    color: white;
                    border-radius: 20px 20px 5px 20px;
                }
                
                .message.bot .message-content {
                    background: white;
                    border: 1px solid rgba(0, 0, 0, 0.1);
                    color: #2c3e50;
                    border-radius: 20px 20px 20px 5px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
                }
                
                /* Streaming Message Styles */
                .message.streaming .message-content {
                    background: linear-gradient(45deg, #f8f9fa, #e9ecef);
                    border: 1px solid rgba(52, 152, 219, 0.3);
                }
                
                .streaming-cursor {
                    animation: blink 1s infinite;
                    color: #3498db;
                    font-weight: bold;
                }
                
                @keyframes blink {
                    0%, 50% { opacity: 1; }
                    51%, 100% { opacity: 0; }
                }
                
                .message-info {
                    font-size: 0.8rem;
                    opacity: 0.7;
                    margin-bottom: 0.5rem;
                    font-weight: 500;
                }
                
                .typing-indicator {
                    display: none;
                    align-items: center;
                    gap: 1rem;
                    padding: 1rem 1.5rem;
                    background: rgba(52, 152, 219, 0.05);
                    margin: 0 1.5rem;
                    border-radius: 15px;
                    margin-bottom: 1rem;
                }
                
                .typing-dots {
                    display: flex;
                    gap: 0.25rem;
                }
                
                .typing-dot {
                    width: 8px;
                    height: 8px;
                    background: #3498db;
                    border-radius: 50%;
                    animation: typingDot 1.4s infinite;
                }
                
                .typing-dot:nth-child(2) { animation-delay: 0.2s; }
                .typing-dot:nth-child(3) { animation-delay: 0.4s; }
                
                @keyframes typingDot {
                    0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
                    30% { transform: translateY(-10px); opacity: 1; }
                }
                
                .input-area {
                    padding: 1.5rem;
                    background: white;
                    border-top: 1px solid rgba(0, 0, 0, 0.05);
                }
                
                .input-container {
                    display: flex;
                    gap: 1rem;
                    align-items: flex-end;
                }
                
                .message-input {
                    flex: 1;
                    padding: 1rem 1.25rem;
                    border: 2px solid rgba(52, 152, 219, 0.2);
                    border-radius: 25px;
                    outline: none;
                    resize: none;
                    font-family: inherit;
                    font-size: 0.95rem;
                    line-height: 1.4;
                    max-height: 100px;
                    transition: all 0.3s ease;
                }
                
                .message-input:focus {
                    border-color: #3498db;
                    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
                }
                
                .send-button {
                    width: 50px;
                    height: 50px;
                    background: linear-gradient(45deg, #3498db, #2ecc71);
                    color: white;
                    border: none;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.1rem;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
                }
                
                .send-button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
                }
                
                .send-button:disabled {
                    opacity: 0.5;
                    transform: none;
                    cursor: not-allowed;
                }
                
                .voice-button {
                    width: 45px;
                    height: 45px;
                    background: linear-gradient(45deg, #e74c3c, #c0392b);
                    color: white;
                    border: none;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1rem;
                    transition: all 0.3s ease;
                    box-shadow: 0 3px 12px rgba(231, 76, 60, 0.3);
                }
                
                .voice-button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
                }
                
                .voice-button.recording {
                    background: linear-gradient(45deg, #e74c3c, #c0392b);
                    animation: pulse-record 1.5s infinite;
                }
                
                .voice-toggle-button {
                    width: 45px;
                    height: 45px;
                    background: linear-gradient(45deg, #9b59b6, #8e44ad);
                    color: white;
                    border: none;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1rem;
                    transition: all 0.3s ease;
                    box-shadow: 0 3px 12px rgba(155, 89, 182, 0.3);
                }
                
                .voice-toggle-button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(155, 89, 182, 0.4);
                }
                
                .voice-toggle-button.muted {
                    background: linear-gradient(45deg, #95a5a6, #7f8c8d);
                }
                
                @keyframes pulse-record {
                    0% { box-shadow: 0 3px 12px rgba(231, 76, 60, 0.3); }
                    50% { box-shadow: 0 3px 12px rgba(231, 76, 60, 0.7); }
                    100% { box-shadow: 0 3px 12px rgba(231, 76, 60, 0.3); }
                }
                
                .chat-mode {
                    display: none;
                    flex-direction: column;
                    height: 100%;
                }
                
                .chat-mode.active {
                    display: flex;
                }
                
                .status-indicator {
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.5rem 1rem;
                    background: rgba(46, 204, 113, 0.1);
                    color: #27ae60;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 500;
                }
                
                .status-dot {
                    width: 8px;
                    height: 8px;
                    background: #27ae60;
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
                    70% { box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); }
                    100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
                }
                
                /* Toast Notifications */
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 12px 20px;
                    border-radius: 8px;
                    color: white;
                    font-weight: 500;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    transform: translateX(400px);
                    opacity: 0;
                    transition: all 0.3s ease;
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    max-width: 350px;
                }
                
                .toast.show {
                    transform: translateX(0);
                    opacity: 1;
                }
                
                .toast-success {
                    background: linear-gradient(135deg, #10b981, #059669);
                }
                
                .toast-error {
                    background: linear-gradient(135deg, #ef4444, #dc2626);
                }
                
                .toast-warning {
                    background: linear-gradient(135deg, #f59e0b, #d97706);
                }
                
                .toast-info {
                    background: linear-gradient(135deg, #3b82f6, #2563eb);
                }
                
                /* Loading Spinner */
                .loading-spinner {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.7);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    z-index: 10001;
                    color: white;
                    font-size: 16px;
                    gap: 20px;
                }
                
                .spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid rgba(255,255,255,0.3);
                    border-top: 4px solid white;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                /* Enhanced animations */
                .message {
                    transition: all 0.3s ease;
                }
                
                .typing-indicator {
                    animation: pulse 1.5s ease-in-out infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 0.7; }
                    50% { opacity: 1; }
                }
                
                .typing-dot {
                    animation: typing 1.4s infinite ease-in-out;
                }
                
                .typing-dot:nth-child(1) { animation-delay: 0s; }
                .typing-dot:nth-child(2) { animation-delay: 0.2s; }
                .typing-dot:nth-child(3) { animation-delay: 0.4s; }
                
                @keyframes typing {
                    0%, 60%, 100% {
                        transform: translateY(0);
                        opacity: 0.4;
                    }
                    30% {
                        transform: translateY(-10px);
                        opacity: 1;
                    }
                }
                
                /* Button hover effects */
                .btn-primary:hover, .send-button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
                }
                
                .btn-secondary:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(107, 114, 128, 0.4);
                }
                
                .mode-btn:hover {
                    transform: translateY(-1px);
                }
                
                /* Status indicator animations */
                .status-dot.connected {
                    background: #10b981;
                    animation: pulse-green 2s infinite;
                }
                
                .status-dot.error {
                    background: #ef4444;
                    animation: pulse-red 2s infinite;
                }
                
                @keyframes pulse-green {
                    0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
                    70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
                }
                
                @keyframes pulse-red {
                    0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
                    70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
                }
                
                /* Enhanced message content styling */
                .message-content {
                    word-wrap: break-word;
                    white-space: pre-wrap;
                    line-height: 1.5;
                }
                
                /* Scrollbar styling */
                .messages-container::-webkit-scrollbar {
                    width: 6px;
                }
                
                .messages-container::-webkit-scrollbar-track {
                    background: rgba(0,0,0,0.1);
                    border-radius: 3px;
                }
                
                .messages-container::-webkit-scrollbar-thumb {
                    background: rgba(0,0,0,0.3);
                    border-radius: 3px;
                }
                
                .messages-container::-webkit-scrollbar-thumb:hover {
                    background: rgba(0,0,0,0.5);
                }
                
                /* Responsive Design */
                @media (max-width: 768px) {
                    .header {
                        padding: 1rem;
                        flex-direction: column;
                        gap: 1rem;
                    }
                    
                    .main-container {
                        padding: 1rem;
                    }
                    
                    .welcome-screen h1 {
                        font-size: 2.5rem;
                    }
                    
                    .feature-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .chat-content {
                        height: 500px;
                    }
                    
                    .message-content {
                        max-width: 90%;
                    }
                    
                    .mode-switcher {
                        flex-direction: column;
                        width: 100%;
                    }
                    
                    .toast {
                        max-width: 280px;
                        font-size: 14px;
                        top: 10px;
                        right: 10px;
                    }
                    
                    .feature-card {
                        padding: 1.5rem;
                    }
                    
                    .mode-btn {
                        flex: 1;
                    }
                }
                
                /* Account Discovery Modal Styles */
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 1000;
                    animation: fadeIn 0.3s ease-out;
                }
                
                .modal-content {
                    background: #ffffff;
                    border-radius: 12px;
                    padding: 2rem;
                    max-width: 500px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                    animation: slideIn 0.3s ease-out;
                }
                
                .discovery-modal h3 {
                    color: #1f2937;
                    margin-bottom: 1rem;
                    font-size: 1.4rem;
                }
                
                .existing-accounts {
                    margin: 1rem 0;
                    padding: 1rem;
                    background: #f9fafb;
                    border-radius: 8px;
                    border: 1px solid #e5e7eb;
                }
                
                .account-option {
                    padding: 0.75rem;
                    margin-bottom: 0.5rem;
                    background: #ffffff;
                    border-radius: 6px;
                    border: 1px solid #d1d5db;
                }
                
                .account-option:last-child {
                    margin-bottom: 0;
                }
                
                .account-info {
                    display: flex;
                    flex-direction: column;
                    gap: 0.25rem;
                }
                
                .account-info strong {
                    color: #1f2937;
                    font-size: 1rem;
                }
                
                .display-name {
                    color: #6b7280;
                    font-size: 0.9rem;
                }
                
                .discord-badge {
                    display: inline-block;
                    background: #5865f2;
                    color: white;
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.8rem;
                    margin-top: 0.25rem;
                }
                
                .memory-summary {
                    margin-top: 0.5rem;
                    padding: 0.5rem;
                    background: #f0f9ff;
                    border-radius: 4px;
                    border-left: 3px solid #0ea5e9;
                }
                
                .memory-summary strong {
                    color: #0ea5e9;
                    font-size: 0.9rem;
                }
                
                .bot-breakdown {
                    font-size: 0.8rem;
                    color: #64748b;
                    margin-top: 0.25rem;
                }
                
                .no-memories {
                    margin-top: 0.5rem;
                    padding: 0.5rem;
                    background: #fef3f2;
                    color: #dc2626;
                    border-radius: 4px;
                    font-size: 0.8rem;
                    border-left: 3px solid #f87171;
                }
                
                .discovery-options {
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                    margin-top: 1rem;
                }
                
                .btn-cancel {
                    background: #6b7280;
                    color: white;
                    border: none;
                    padding: 0.75rem 1rem;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.9rem;
                    transition: all 0.2s ease;
                }
                
                .btn-cancel:hover {
                    background: #4b5563;
                    transform: translateY(-1px);
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                @keyframes slideIn {
                    from { 
                        opacity: 0;
                        transform: translateY(-20px) scale(0.95);
                    }
                    to { 
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">
                    <i class="fas fa-brain"></i>
                    WhisperEngine
                </div>
                <div class="login-section">
                    <div class="user-info" id="userInfo">
                        <div class="user-avatar" id="userAvatar"></div>
                        <span id="userName"></span>
                        <div class="status-indicator">
                            <div class="status-dot"></div>
                            <span>Online</span>
                        </div>
                    </div>
                    <div class="login-form" id="loginForm">
                        <input type="text" id="usernameInput" placeholder="Username" class="input-modern">
                        <input type="text" id="displayNameInput" placeholder="Display Name" class="input-modern">
                        <details class="discord-link-section">
                            <summary>🔗 Link Discord Account (Optional)</summary>
                            <input type="text" id="discordIdInput" placeholder="Discord User ID (18-digit number)" class="input-modern">
                            <small>Link your Discord account to access your conversation history across platforms</small>
                        </details>
                        <button onclick="window.testFunction()" class="btn-primary">
                            <i class="fas fa-sign-in-alt"></i> Login (Test)
                        </button>
                    </div>
                </div>
            </div>

            <div class="main-container">
                <div class="welcome-screen" id="welcomeScreen">
                    <h1>Welcome to WhisperEngine</h1>
                    <p>Experience conversations with AI companions that remember, learn, and grow with unique personalities and expertise.</p>
                    
                    <div class="feature-grid">
                        <div class="feature-card">
                            <i class="fas fa-users"></i>
                            <h3>Multi-Bot Conversations</h3>
                            <p>Chat with multiple AI companions simultaneously and watch them collaborate on complex topics.</p>
                        </div>
                        <div class="feature-card">
                            <i class="fas fa-brain"></i>
                            <h3>Intelligent Memory</h3>
                            <p>Our AI remembers your conversations and builds lasting relationships across sessions.</p>
                        </div>
                        <div class="feature-card">
                            <i class="fas fa-palette"></i>
                            <h3>Unique Personalities</h3>
                            <p>Each companion has distinct expertise, communication styles, and character traits.</p>
                        </div>
                    </div>
                </div>

                <div class="chat-container" id="chatContainer">
                    <div class="chat-header">
                        <div class="chat-title">
                            <i class="fas fa-comments"></i>
                            <h2 id="chatTitle">AI Companions</h2>
                        </div>
                        <div class="mode-switcher">
                            <button class="mode-btn active" onclick="switchMode('single')" id="singleModeBtn">
                                <i class="fas fa-user"></i> Single Bot
                            </button>
                            <button class="mode-btn" onclick="switchMode('multi')" id="multiModeBtn">
                                <i class="fas fa-users"></i> Multi-Bot
                            </button>
                        </div>
                    </div>

                    <div class="chat-content">
                        <!-- Single Bot Mode -->
                        <div class="chat-mode active" id="singleMode">
                            <div class="chat-subheader">
                                <select class="bot-selector" id="botSelector">
                                    <option value="">Select an AI Companion</option>
                                </select>
                                <div class="status-indicator" id="botStatus" style="display: none;">
                                    <div class="status-dot"></div>
                                    <span>Connected</span>
                                </div>
                            </div>
                            
                            <div class="messages-container" id="messagesContainer">
                                <div class="typing-indicator" id="typingIndicator">
                                    <div class="message-avatar bot-avatar">
                                        <i class="fas fa-robot"></i>
                                    </div>
                                    <div>
                                        <div class="message-info">AI is typing...</div>
                                        <div class="typing-dots">
                                            <div class="typing-dot"></div>
                                            <div class="typing-dot"></div>
                                            <div class="typing-dot"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="input-area">
                                <div class="input-container">
                                    <button class="voice-button" onclick="toggleVoiceRecording()" id="voiceButton" title="Voice input">
                                        <i class="fas fa-microphone"></i>
                                    </button>
                                    <textarea 
                                        id="messageInput" 
                                        class="message-input" 
                                        placeholder="Type your message or use voice input..."
                                        rows="1"
                                        onkeypress="handleKeyPress(event)"
                                    ></textarea>
                                    <button class="voice-toggle-button" onclick="toggleVoiceOutput()" id="voiceToggleButton" title="Toggle voice responses">
                                        <i class="fas fa-volume-up" id="voiceToggleIcon"></i>
                                    </button>
                                    <button class="send-button" onclick="sendMessage()" id="sendButton">
                                        <i class="fas fa-paper-plane"></i>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Multi-Bot Mode -->
                        <div class="chat-mode" id="multiMode">
                            <div class="chat-subheader">
                                <div class="conversation-controls">
                                    <button class="btn-secondary" onclick="createMultiBotConversation()">
                                        <i class="fas fa-plus"></i> New Conversation
                                    </button>
                                    <select class="conversation-selector" id="conversationSelector">
                                        <option value="">Select or create a conversation</option>
                                    </select>
                                    <div class="status-indicator" id="multiBotStatus" style="display: none;">
                                        <div class="status-dot"></div>
                                        <span id="multiBotStatusText">Ready</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="messages-container" id="multiMessagesContainer">
                                <div class="typing-indicator" id="multiTypingIndicator">
                                    <div class="message-avatar bot-avatar">
                                        <i class="fas fa-users"></i>
                                    </div>
                                    <div>
                                        <div class="message-info">AI companions are responding...</div>
                                        <div class="typing-dots">
                                            <div class="typing-dot"></div>
                                            <div class="typing-dot"></div>
                                            <div class="typing-dot"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="input-area">
                                <div class="input-container">
                                    <button class="voice-button" onclick="toggleMultiVoiceRecording()" id="multiVoiceButton" title="Voice input">
                                        <i class="fas fa-microphone"></i>
                                    </button>
                                    <textarea 
                                        id="multiMessageInput" 
                                        class="message-input" 
                                        placeholder="Ask multiple AI companions or use voice input..."
                                        rows="1"
                                        onkeypress="handleMultiKeyPress(event)"
                                    ></textarea>
                                    <button class="voice-toggle-button" onclick="toggleVoiceOutput()" id="multiVoiceToggleButton" title="Toggle voice responses">
                                        <i class="fas fa-volume-up" id="multiVoiceToggleIcon"></i>
                                    </button>
                                    <button class="send-button" onclick="sendMultiMessage()" id="multiSendButton">
                                        <i class="fas fa-paper-plane"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // Global Variables
                let ws = null;
                let sessionToken = null;
                let currentBot = '';
                let currentConversationId = null;
                let availableBots = [];
                let currentChatMode = 'single';
                let isTyping = false;
                
                // Voice-related variables
                let mediaRecorder = null;
                let audioChunks = [];
                let isRecording = false;
                let voiceOutputEnabled = true;
                let availableVoices = [];
                let currentVoiceId = null;
                
                // Initialize app when DOM is loaded
                document.addEventListener('DOMContentLoaded', () => {
                    initializeApp();
                });

                function initializeApp() {
                    // Auto-resize message inputs
                    ['messageInput', 'multiMessageInput'].forEach(id => {
                        const element = document.getElementById(id);
                        if (element) {
                            element.addEventListener('input', autoResizeTextarea);
                            element.addEventListener('keypress', (e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    if (id === 'messageInput') sendMessage();
                                    else sendMultiMessage();
                                }
                            });
                        }
                    });

                    // Initialize voice functionality
                    initializeVoice();

                    // Show welcome screen initially
                    showWelcomeScreen();
                }

                function autoResizeTextarea(event) {
                    const textarea = event.target;
                    textarea.style.height = 'auto';
                    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
                }

                function showWelcomeScreen() {
                    document.getElementById('welcomeScreen').style.display = 'block';
                    document.getElementById('chatContainer').style.display = 'none';
                }

                function showChatContainer() {
                    document.getElementById('welcomeScreen').style.display = 'none';
                    document.getElementById('chatContainer').style.display = 'block';
                }

                // Simple test function
                window.testFunction = function() {
                    alert('Test function works!');
                };

                // Login Functions
                window.loginUser = async function() {
                    alert('Login button clicked!'); // Debug alert
                    console.log('loginUser function called');
                    
                    const username = document.getElementById('usernameInput').value.trim();
                    console.log('Username:', username);
                    
                    if (!username) {
                        console.log('No username provided');
                        showToast('Please enter a username', 'error');
                        return;
                    }
                    
                    const displayName = document.getElementById('displayNameInput').value.trim() || username;
                    const discordId = document.getElementById('discordIdInput').value.trim();
                    
                    console.log('Login data:', { username, displayName, discordId });
                    
                    // Validate Discord ID format if provided
                    if (discordId && (!/^[0-9]{17,19}$/.test(discordId))) {
                        console.log('Invalid Discord ID format');
                        showToast('Discord ID must be a 17-19 digit number', 'error');
                        return;
                    }
                    
                    console.log('Starting login request...');
                    showLoadingSpinner(discordId ? 'Linking Discord account...' : 'Signing you in...');
                    
                    try {
                        let body = `username=${encodeURIComponent(username)}&display_name=${encodeURIComponent(displayName)}`;
                        if (discordId) {
                            body += `&discord_id=${encodeURIComponent(discordId)}`;
                        }
                        
                        console.log('Making fetch request with body:', body);
                        
                        const response = await fetch('/api/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                            body: body
                        });
                        
                        console.log('Login response status:', response.status);
                        
                        const data = await response.json();
                        console.log('Login response data:', data);
                        
                        // Handle account discovery response
                        if (data.account_discovery) {
                            console.log('Account discovery triggered');
                            hideLoadingSpinner();
                            await showAccountDiscoveryDialog(data);
                            return;
                        }
                        
                        sessionToken = data.session_token;
                        console.log('Session token received:', sessionToken);
                        
                        // Show success message with universal ID info
                        if (data.user.universal_user_id) {
                            const message = discordId ? 
                                `✅ Linked to Discord! Universal ID: ${data.user.universal_user_id}` : 
                                `✅ Signed in! Universal ID: ${data.user.universal_user_id}`;
                            showToast(message, 'success');
                        }
                        
                        // Update UI
                        document.getElementById('loginForm').style.display = 'none';
                        document.getElementById('userInfo').style.display = 'flex';
                        document.getElementById('userName').textContent = data.user.display_name;
                        document.getElementById('userAvatar').textContent = displayName.charAt(0).toUpperCase();
                        
                        showChatContainer();
                        await loadBots();
                        connectWebSocket();
                        showToast('Welcome to WhisperEngine!', 'success');
                        
                    } catch (error) {
                        showToast('Login failed: ' + error.message, 'error');
                    } finally {
                        hideLoadingSpinner();
                    }
                }; // End of window.loginUser

                async function showAccountDiscoveryDialog(discoveryData) {
                    const modal = document.createElement('div');
                    modal.className = 'modal-overlay';
                    modal.innerHTML = `
                        <div class="modal-content discovery-modal">
                            <h3>🔍 Account Discovery</h3>
                            <p>${discoveryData.message}</p>
                            <div class="existing-accounts">
                                ${discoveryData.existing_accounts.map(account => 
                                    '<div class="account-option">' +
                                        '<div class="account-info">' +
                                            '<strong>' + account.username + '</strong>' +
                                            (account.display_name ? '<span class="display-name">(' + account.display_name + ')</span>' : '') +
                                            (account.has_discord ? '<span class="discord-badge">🎮 Discord: ' + account.discord_username + '</span>' : '') +
                                        '</div>' +
                                        (account.total_memories > 0 ? 
                                            '<div class="memory-summary">' +
                                                '<strong>💭 ' + account.total_memories + ' conversation memories</strong>' +
                                                '<div class="bot-breakdown">' + account.bot_summary + '</div>' +
                                            '</div>'
                                        : '<div class="no-memories">No conversation history found</div>') +
                                        '<small>Universal ID: ' + account.universal_id + '</small>' +
                                    '</div>'
                                ).join('')}
                            </div>
                            <p><strong>Options:</strong></p>
                            <div class="discovery-options">
                                <button onclick="requestDiscordLink()" class="btn-primary">
                                    🔗 I have a Discord account - Link it
                                </button>
                                <button onclick="createNewAccount()" class="btn-secondary">
                                    ➕ Create new account anyway
                                </button>
                                <button onclick="closeDiscoveryDialog()" class="btn-cancel">
                                    ❌ Cancel
                                </button>
                            </div>
                        </div>
                    `;
                    
                    document.body.appendChild(modal);
                    
                    // Store discovery data for use in subsequent actions
                    window.discoveryData = discoveryData;
                }

                function requestDiscordLink() {
                    closeDiscoveryDialog();
                    // Expand the Discord linking section and focus on it
                    const discordSection = document.querySelector('.discord-link-section');
                    discordSection.open = true;
                    document.getElementById('discordIdInput').focus();
                    showToast('Please enter your Discord ID to link to your existing account', 'info');
                }

                function createNewAccount() {
                    closeDiscoveryDialog();
                    // Suggest a different username
                    const currentUsername = document.getElementById('usernameInput').value;
                    const newUsername = `${currentUsername}_${Date.now().toString().slice(-4)}`;
                    document.getElementById('usernameInput').value = newUsername;
                    showToast(`Suggested new username: ${newUsername}`, 'info');
                }

                function closeDiscoveryDialog() {
                    const modal = document.querySelector('.modal-overlay');
                    if (modal) {
                        modal.remove();
                    }
                    delete window.discoveryData;
                }

                // Bot Management
                async function loadBots() {
                    try {
                        const response = await fetch('/api/bots');
                        const data = await response.json();
                        availableBots = data.bots;
                        
                        // Update single bot selector
                        const selector = document.getElementById('botSelector');
                        selector.innerHTML = '<option value="">Select an AI Companion</option>';
                        
                        data.bots.forEach(bot => {
                            const option = document.createElement('option');
                            option.value = bot.name;
                            option.textContent = `${bot.emoji} ${bot.display_name}`;
                            selector.appendChild(option);
                        });
                        
                        if (currentBot && data.bots.find(b => b.name === currentBot)) {
                            selector.value = currentBot;
                        } else if (data.bots.length > 0) {
                            currentBot = data.bots[0].name;
                            selector.value = currentBot;
                        }
                        
                        selector.addEventListener('change', (e) => {
                            currentBot = e.target.value;
                            updateBotStatus();
                        });
                        
                        updateBotStatus();
                        
                    } catch (error) {
                        console.error('Failed to load bots:', error);
                        showToast('Failed to load AI companions', 'error');
                    }
                }

                function updateBotStatus() {
                    const statusElement = document.getElementById('botStatus');
                    if (currentBot && statusElement) {
                        statusElement.style.display = 'flex';
                    } else if (statusElement) {
                        statusElement.style.display = 'none';
                    }
                }

                // Mode Switching
                function switchMode(mode) {
                    currentChatMode = mode;
                    
                    // Update mode buttons
                    document.getElementById('singleModeBtn').classList.toggle('active', mode === 'single');
                    document.getElementById('multiModeBtn').classList.toggle('active', mode === 'multi');
                    
                    // Update chat modes
                    document.getElementById('singleMode').classList.toggle('active', mode === 'single');
                    document.getElementById('multiMode').classList.toggle('active', mode === 'multi');
                    
                    // Update chat title
                    document.getElementById('chatTitle').textContent = 
                        mode === 'single' ? 'AI Companion Chat' : 'Multi-Bot Conversation';
                    
                    if (mode === 'multi') {
                        loadMultiBotInterface();
                    }
                }

                // WebSocket Connection
                function connectWebSocket() {
                    if (!sessionToken) return;
                    
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const host = window.location.hostname;
                    const port = window.location.port || '8081';
                    ws = new WebSocket(`${protocol}//${host}:${port}/ws?token=${sessionToken}`);
                    
                    ws.onopen = () => {
                        console.log('WebSocket connected');
                        updateConnectionStatus('connected');
                    };
                    
                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        handleWebSocketMessage(data);
                    };
                    
                    ws.onclose = () => {
                        console.log('WebSocket disconnected');
                        updateConnectionStatus('disconnected');
                        // Attempt to reconnect after 3 seconds
                        setTimeout(connectWebSocket, 3000);
                    };
                    
                    ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        updateConnectionStatus('error');
                    };
                }

                function handleWebSocketMessage(data) {
                    if (data.type === 'bot_response') {
                        hideTypingIndicator();
                        addMessage(data.content, 'bot', data.bot_name);
                    } else if (data.type === 'multibot_response') {
                        hideMultiTypingIndicator();
                        // Handle multi-bot real-time responses
                        console.log('Multi-bot response received:', data);
                    } else if (data.type === 'system') {
                        addMessage(data.content, 'system');
                    }
                }

                function updateConnectionStatus(status) {
                    const indicators = document.querySelectorAll('.status-indicator .status-dot');
                    indicators.forEach(dot => {
                        dot.className = 'status-dot';
                        if (status === 'connected') dot.classList.add('connected');
                        else if (status === 'error') dot.classList.add('error');
                    });
                }

                // Voice Functionality
                async function initializeVoice() {
                    try {
                        // Load available voices
                        const response = await fetch('/api/voice/voices');
                        if (response.ok) {
                            availableVoices = await response.json();
                            if (availableVoices.length > 0) {
                                // Default to Rachel's voice
                                currentVoiceId = availableVoices.find(v => v.name === 'Rachel')?.voice_id || availableVoices[0].voice_id;
                            }
                        }
                    } catch (error) {
                        console.error('Failed to initialize voice:', error);
                    }
                }

                async function toggleVoiceRecording() {
                    const button = document.getElementById('voiceButton');
                    const icon = button.querySelector('i');
                    
                    if (!isRecording) {
                        await startRecording();
                        button.classList.add('recording');
                        icon.className = 'fas fa-stop';
                        button.title = 'Stop recording';
                    } else {
                        await stopRecording();
                        button.classList.remove('recording');
                        icon.className = 'fas fa-microphone';
                        button.title = 'Voice input';
                    }
                }

                async function toggleMultiVoiceRecording() {
                    const button = document.getElementById('multiVoiceButton');
                    const icon = button.querySelector('i');
                    
                    if (!isRecording) {
                        await startRecording(true);
                        button.classList.add('recording');
                        icon.className = 'fas fa-stop';
                        button.title = 'Stop recording';
                    } else {
                        await stopRecording(true);
                        button.classList.remove('recording');
                        icon.className = 'fas fa-microphone';
                        button.title = 'Voice input';
                    }
                }

                async function startRecording(isMulti = false) {
                    try {
                        console.log('Starting voice recording...');
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        
                        // Use a more compatible audio format
                        const options = { mimeType: 'audio/webm' };
                        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                            options.mimeType = 'audio/ogg';
                            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                                options.mimeType = ''; // Use default
                            }
                        }
                        
                        console.log('Using MIME type:', options.mimeType || 'default');
                        mediaRecorder = new MediaRecorder(stream, options.mimeType ? options : {});
                        audioChunks = [];
                        
                        mediaRecorder.ondataavailable = (event) => {
                            console.log('Audio chunk received:', event.data.size, 'bytes');
                            audioChunks.push(event.data);
                        };
                        
                        mediaRecorder.onstop = async () => {
                            console.log('Recording stopped, processing audio...');
                            const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
                            console.log('Audio blob created:', audioBlob.size, 'bytes, type:', audioBlob.type);
                            await processVoiceInput(audioBlob, isMulti);
                            stream.getTracks().forEach(track => track.stop());
                        };
                        
                        mediaRecorder.start();
                        isRecording = true;
                        console.log('Recording started successfully');
                        showToast('🎤 Recording... Click stop when finished', 'info');
                        
                    } catch (error) {
                        console.error('Error starting recording:', error);
                        showToast('Microphone access denied or not available', 'error');
                    }
                }

                async function stopRecording(isMulti = false) {
                    if (mediaRecorder && isRecording) {
                        mediaRecorder.stop();
                        isRecording = false;
                    }
                }

                async function processVoiceInput(audioBlob, isMulti = false) {
                    try {
                        showToast('🔄 Processing voice input...', 'info');
                        
                        const formData = new FormData();
                        formData.append('audio', audioBlob, 'recording.wav');
                        
                        const response = await fetch('/api/voice/stt', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (!response.ok) {
                            throw new Error('Voice processing failed');
                        }
                        
                        const data = await response.json();
                        const text = data.text.trim();
                        
                        if (text) {
                            const inputElement = isMulti ? 
                                document.getElementById('multiMessageInput') : 
                                document.getElementById('messageInput');
                            inputElement.value = text;
                            showToast(`✅ Voice input: "${text}"`, 'success');
                        } else {
                            showToast('No speech detected. Please try again.', 'warning');
                        }
                        
                    } catch (error) {
                        console.error('Error processing voice input:', error);
                        showToast('Failed to process voice input', 'error');
                    }
                }

                function toggleVoiceOutput() {
                    voiceOutputEnabled = !voiceOutputEnabled;
                    
                    const buttons = ['voiceToggleButton', 'multiVoiceToggleButton'];
                    const icons = ['voiceToggleIcon', 'multiVoiceToggleIcon'];
                    
                    buttons.forEach((buttonId, index) => {
                        const button = document.getElementById(buttonId);
                        const icon = document.getElementById(icons[index]);
                        
                        if (button && icon) {
                            button.classList.toggle('muted', !voiceOutputEnabled);
                            icon.className = voiceOutputEnabled ? 'fas fa-volume-up' : 'fas fa-volume-mute';
                            button.title = voiceOutputEnabled ? 'Disable voice responses' : 'Enable voice responses';
                        }
                    });
                    
                    showToast(
                        voiceOutputEnabled ? '🔊 Voice responses enabled' : '🔇 Voice responses disabled', 
                        'info'
                    );
                }

                async function playVoiceResponse(text) {
                    console.log('playVoiceResponse called with:', { text, voiceOutputEnabled, currentVoiceId });
                    
                    if (!voiceOutputEnabled || !currentVoiceId || !text.trim()) {
                        console.log('Voice response skipped:', { voiceOutputEnabled, currentVoiceId, hasText: !!text.trim() });
                        return;
                    }
                    
                    try {
                        console.log('Making streaming TTS request...');
                        
                        // Try streaming TTS first for better performance
                        const streamResponse = await fetch('/api/voice/tts/stream', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                text: text,
                                voice_id: currentVoiceId
                            })
                        });
                        
                        if (streamResponse.ok && streamResponse.body) {
                            console.log('Using streaming TTS for better performance');
                            
                            // Create audio from streaming response
                            const audioBlob = await streamResponse.blob();
                            const audioUrl = URL.createObjectURL(audioBlob);
                            const audio = new Audio(audioUrl);
                            
                            console.log('Attempting to play streaming audio...');
                            audio.play().then(() => {
                                console.log('Streaming audio playing successfully!');
                            }).catch(error => {
                                console.error('Error playing streaming audio:', error);
                                showMessage('Voice playback blocked by browser. Please click the speaker button to enable.', 'warning');
                            });
                            
                            // Cleanup
                            audio.addEventListener('ended', () => {
                                console.log('Streaming audio playback finished');
                                URL.revokeObjectURL(audioUrl);
                            });
                            
                        } else {
                            console.log('Streaming TTS not available, falling back to regular TTS');
                            
                            // Fallback to regular TTS
                            const response = await fetch('/api/voice/tts', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ 
                                    text: text,
                                    voice_id: currentVoiceId
                                })
                            });
                            
                            if (!response.ok) throw new Error(`TTS failed: ${response.status}`);
                            
                            const data = await response.json();
                            console.log('Regular TTS response received, playing audio...');
                            
                            // Convert base64 audio to blob and play
                            const audioBlob = new Blob([
                                Uint8Array.from(atob(data.audio_data), c => c.charCodeAt(0))
                            ], { type: 'audio/mpeg' });
                            
                            const audioUrl = URL.createObjectURL(audioBlob);
                            const audio = new Audio(audioUrl);
                            
                            console.log('Attempting to play regular audio...');
                            audio.play().then(() => {
                                console.log('Audio playing successfully!');
                            }).catch(error => {
                                console.error('Error playing audio:', error);
                                showMessage('Voice playback blocked by browser. Please click the speaker button to enable.', 'warning');
                            });
                            
                            // Cleanup
                            audio.addEventListener('ended', () => {
                                console.log('Audio playback finished');
                                URL.revokeObjectURL(audioUrl);
                            });
                        }
                        
                    } catch (error) {
                        console.error('Error playing voice response:', error);
                        showMessage('Voice response failed: ' + error.message, 'error');
                    }
                }

                // Single Bot Messaging with Streaming Support
                async function sendMessage() {
                    if (!currentBot) {
                        showToast('Please select an AI companion first', 'warning');
                        return;
                    }
                    
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (!message || !sessionToken) return;
                    
                    addMessage(message, 'user');
                    input.value = '';
                    input.style.height = 'auto';
                    
                    // Create bot message container for streaming
                    const botMessageElement = addStreamingMessage(currentBot);
                    
                    try {
                        // Try streaming first
                        const streamResponse = await fetch('/api/chat/stream', {
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
                        
                        if (streamResponse.ok && streamResponse.body) {
                            console.log('Using streaming response for better experience');
                            
                            const reader = streamResponse.body.getReader();
                            const decoder = new TextDecoder();
                            let fullResponse = '';
                            
                            try {
                                while (true) {
                                    const { done, value } = await reader.read();
                                    if (done) break;
                                    
                                    const chunk = decoder.decode(value);
                                    const lines = chunk.split('\n');
                                    
                                    for (const line of lines) {
                                        if (line.startsWith('data: ')) {
                                            try {
                                                const data = JSON.parse(line.slice(6));
                                                
                                                if (data.token) {
                                                    // Add token to streaming message
                                                    fullResponse += data.token;
                                                    updateStreamingMessage(botMessageElement, fullResponse);
                                                } else if (data.type === 'complete') {
                                                    // Stream complete
                                                    finalizeStreamingMessage(botMessageElement, data.full_response || fullResponse);
                                                    
                                                    // Play voice response if enabled
                                                    if (voiceOutputEnabled) {
                                                        playVoiceResponse(data.full_response || fullResponse);
                                                    }
                                                    break;
                                                } else if (data.error) {
                                                    throw new Error(data.error);
                                                }
                                            } catch (parseError) {
                                                console.warn('Failed to parse streaming data:', parseError);
                                            }
                                        }
                                    }
                                }
                            } finally {
                                reader.releaseLock();
                            }
                            
                        } else {
                            // Fallback to regular API
                            console.log('Streaming not available, using regular API');
                            
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
                            
                            // The regular API response comes via WebSocket
                            // Replace streaming message with "waiting" state
                            updateStreamingMessage(botMessageElement, 'Thinking...');
                        }
                        
                    } catch (error) {
                        console.error('Send message error:', error);
                        updateStreamingMessage(botMessageElement, 'Error: Failed to send message');
                        showToast('Failed to send message', 'error');
                    }
                }

                function handleKeyPress(event) {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        sendMessage();
                    }
                }

                function addMessage(content, type, botName = '') {
                    const container = document.getElementById('messagesContainer');
                    const message = document.createElement('div');
                    message.className = `message ${type}`;
                    
                    // Create avatar
                    const avatar = document.createElement('div');
                    avatar.className = `message-avatar ${type}-avatar`;
                    
                    if (type === 'user') {
                        const userAvatar = document.getElementById('userAvatar').textContent;
                        avatar.textContent = userAvatar;
                    } else if (type === 'bot') {
                        const bot = availableBots.find(b => b.name === botName);
                        if (bot) {
                            avatar.innerHTML = `<i class="fas fa-robot"></i>`;
                            avatar.style.background = `linear-gradient(135deg, ${getBotColor(bot.name)})`;
                        } else {
                            avatar.innerHTML = `<i class="fas fa-robot"></i>`;
                        }
                    } else {
                        avatar.innerHTML = `<i class="fas fa-info-circle"></i>`;
                    }
                    
                    // Create message content
                    const messageDiv = document.createElement('div');
                    
                    if (type === 'bot' && botName) {
                        const bot = availableBots.find(b => b.name === botName);
                        const botDisplayName = bot ? bot.display_name : botName;
                        
                        const messageInfo = document.createElement('div');
                        messageInfo.className = 'message-info';
                        messageInfo.textContent = botDisplayName;
                        messageDiv.appendChild(messageInfo);
                    }
                    
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    messageContent.textContent = content;
                    messageDiv.appendChild(messageContent);
                    
                    message.appendChild(avatar);
                    message.appendChild(messageDiv);
                    
                    // Add slide-in animation
                    message.style.opacity = '0';
                    message.style.transform = 'translateY(20px)';
                    container.appendChild(message);
                    
                    // Trigger animation
                    requestAnimationFrame(() => {
                        message.style.opacity = '1';
                        message.style.transform = 'translateY(0)';
                    });
                    
                    container.scrollTop = container.scrollHeight;
                    
                    // Play voice response for bot messages
                    if (type === 'bot' && content.trim()) {
                        playVoiceResponse(content);
                    }
                }

                function getBotColor(botName) {
                    const colors = {
                        'elena': '#4ecdc4, #44a08d',
                        'marcus': '#667eea, #764ba2',
                        'ryan-chen': '#f093fb, #f5576c',
                        'dream': '#4facfe, #00f2fe',
                        'gabriel': '#43e97b, #38f9d7'
                    };
                    return colors[botName] || '#6c757d, #495057';
                }

                // Streaming Message Functions
                function addStreamingMessage(botName) {
                    const container = document.getElementById('messagesContainer');
                    const message = document.createElement('div');
                    message.className = 'message bot streaming';
                    
                    // Create avatar
                    const avatar = document.createElement('div');
                    avatar.className = 'message-avatar bot-avatar';
                    const bot = availableBots.find(b => b.name === botName);
                    if (bot) {
                        avatar.innerHTML = `<i class="fas fa-robot"></i>`;
                        avatar.style.background = `linear-gradient(135deg, ${getBotColor(bot.name)})`;
                    } else {
                        avatar.innerHTML = `<i class="fas fa-robot"></i>`;
                    }
                    
                    // Create message content
                    const messageDiv = document.createElement('div');
                    
                    if (botName) {
                        const bot = availableBots.find(b => b.name === botName);
                        const botDisplayName = bot ? bot.display_name : botName;
                        
                        const messageInfo = document.createElement('div');
                        messageInfo.className = 'message-info';
                        messageInfo.textContent = botDisplayName;
                        messageDiv.appendChild(messageInfo);
                    }
                    
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    messageContent.innerHTML = '<span class="streaming-cursor">|</span>';
                    
                    messageDiv.appendChild(messageContent);
                    message.appendChild(avatar);
                    message.appendChild(messageDiv);
                    container.appendChild(message);
                    
                    // Auto-scroll
                    container.scrollTop = container.scrollHeight;
                    
                    return messageContent;
                }
                
                function updateStreamingMessage(messageElement, content) {
                    if (messageElement) {
                        // Remove cursor and add content with new cursor
                        messageElement.innerHTML = content + '<span class="streaming-cursor">|</span>';
                        
                        // Auto-scroll
                        const container = document.getElementById('messagesContainer');
                        container.scrollTop = container.scrollHeight;
                    }
                }
                
                function finalizeStreamingMessage(messageElement, finalContent) {
                    if (messageElement) {
                        // Remove cursor and set final content
                        messageElement.innerHTML = finalContent;
                        messageElement.parentElement.parentElement.classList.remove('streaming');
                    }
                }

                // Typing Indicators
                function showTypingIndicator() {
                    const indicator = document.getElementById('typingIndicator');
                    if (indicator) {
                        indicator.style.display = 'flex';
                        const container = document.getElementById('messagesContainer');
                        container.scrollTop = container.scrollHeight;
                    }
                }

                function hideTypingIndicator() {
                    const indicator = document.getElementById('typingIndicator');
                    if (indicator) {
                        indicator.style.display = 'none';
                    }
                }

                // Multi-Bot Functions
                async function loadMultiBotInterface() {
                    try {
                        await loadConversations();
                    } catch (error) {
                        console.error('Failed to load multi-bot interface:', error);
                        showToast('Failed to load multi-bot interface', 'error');
                    }
                }

                async function createMultiBotConversation() {
                    // This would open a modal to select bots and create conversation
                    // For now, let's create a simple conversation with Elena and Marcus
                    const selectedBots = ['elena', 'marcus'];
                    
                    try {
                        showLoadingSpinner('Creating conversation...');
                        
                        const response = await fetch(`/api/multibot/create?token=${sessionToken}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                bot_names: selectedBots,
                                topic: 'AI Discussion',
                                initial_prompt: null
                            })
                        });
                        
                        const data = await response.json();
                        if (data.success) {
                            currentConversationId = data.conversation_id;
                            await loadConversations();
                            
                            // Select the new conversation
                            document.getElementById('conversationSelector').value = currentConversationId;
                            showToast('Multi-bot conversation created!', 'success');
                        } else {
                            throw new Error(data.error || 'Failed to create conversation');
                        }
                        
                    } catch (error) {
                        showToast('Failed to create conversation: ' + error.message, 'error');
                        console.error('Create conversation error:', error);
                    } finally {
                        hideLoadingSpinner();
                    }
                }

                async function loadConversations() {
                    try {
                        const response = await fetch(`/api/multibot/conversations?token=${sessionToken}`);
                        const data = await response.json();
                        
                        const selector = document.getElementById('conversationSelector');
                        selector.innerHTML = '<option value="">Select or create a conversation</option>';
                        
                        if (data.conversations && data.conversations.length > 0) {
                            data.conversations.forEach(conv => {
                                const option = document.createElement('option');
                                option.value = conv.conversation_id;
                                option.textContent = `${conv.topic || 'Multi-Bot Chat'} (${conv.participants.join(', ')})`;
                                selector.appendChild(option);
                            });
                        }
                        
                        // Update status
                        const statusElement = document.getElementById('multiBotStatus');
                        const statusText = document.getElementById('multiBotStatusText');
                        if (statusElement && statusText) {
                            statusElement.style.display = 'flex';
                            statusText.textContent = data.conversations.length > 0 ? 'Ready' : 'No conversations';
                        }
                        
                    } catch (error) {
                        console.error('Failed to load conversations:', error);
                    }
                }

                async function sendMultiMessage() {
                    if (!currentConversationId) {
                        showToast('Please select or create a conversation first', 'warning');
                        return;
                    }
                    
                    const input = document.getElementById('multiMessageInput');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    input.value = '';
                    input.style.height = 'auto';
                    
                    addMultiMessage(message, 'user');
                    showMultiTypingIndicator();
                    
                    try {
                        const response = await fetch(`/api/multibot/${currentConversationId}/message?token=${sessionToken}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                content: message,
                                bot_name: 'multibot',
                                message_type: 'text'
                            })
                        });
                        
                        const data = await response.json();
                        if (data.success) {
                            hideMultiTypingIndicator();
                            addMultiBotResponses(data.responses);
                        } else {
                            throw new Error(data.error || 'Failed to send message');
                        }
                        
                    } catch (error) {
                        hideMultiTypingIndicator();
                        addMultiMessage('Error: Failed to send message', 'system');
                        showToast('Failed to send message', 'error');
                        console.error('Send multi-bot message error:', error);
                    }
                }

                function handleMultiKeyPress(event) {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        sendMultiMessage();
                    }
                }

                function addMultiMessage(content, type, botName = '') {
                    const container = document.getElementById('multiMessagesContainer');
                    const message = document.createElement('div');
                    message.className = `message ${type}`;
                    
                    // Similar structure to single message but for multi-bot container
                    const avatar = document.createElement('div');
                    avatar.className = `message-avatar ${type}-avatar`;
                    
                    if (type === 'user') {
                        const userAvatar = document.getElementById('userAvatar').textContent;
                        avatar.textContent = userAvatar;
                    } else {
                        avatar.innerHTML = `<i class="fas fa-robot"></i>`;
                    }
                    
                    const messageDiv = document.createElement('div');
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    messageContent.textContent = content;
                    messageDiv.appendChild(messageContent);
                    
                    message.appendChild(avatar);
                    message.appendChild(messageDiv);
                    
                    container.appendChild(message);
                    container.scrollTop = container.scrollHeight;
                }

                function addMultiBotResponses(responses) {
                    const container = document.getElementById('multiMessagesContainer');
                    
                    responses.forEach((response, index) => {
                        setTimeout(() => {
                            const bot = availableBots.find(b => b.name === response.bot_name);
                            const message = document.createElement('div');
                            message.className = 'message bot';
                            
                            const avatar = document.createElement('div');
                            avatar.className = 'message-avatar bot-avatar';
                            avatar.innerHTML = `<i class="fas fa-robot"></i>`;
                            avatar.style.background = `linear-gradient(135deg, ${getBotColor(response.bot_name)})`;
                            
                            const messageDiv = document.createElement('div');
                            
                            const messageInfo = document.createElement('div');
                            messageInfo.className = 'message-info';
                            messageInfo.textContent = bot ? bot.display_name : response.bot_name;
                            messageDiv.appendChild(messageInfo);
                            
                            const messageContent = document.createElement('div');
                            messageContent.className = 'message-content';
                            messageContent.textContent = response.response;
                            messageDiv.appendChild(messageContent);
                            
                            message.appendChild(avatar);
                            message.appendChild(messageDiv);
                            
                            // Add slide-in animation
                            message.style.opacity = '0';
                            message.style.transform = 'translateY(20px)';
                            container.appendChild(message);
                            
                            requestAnimationFrame(() => {
                                message.style.opacity = '1';
                                message.style.transform = 'translateY(0)';
                            });
                            
                            container.scrollTop = container.scrollHeight;
                        }, index * 500); // Stagger the responses
                    });
                }

                function showMultiTypingIndicator() {
                    const indicator = document.getElementById('multiTypingIndicator');
                    if (indicator) {
                        indicator.style.display = 'flex';
                        const container = document.getElementById('multiMessagesContainer');
                        container.scrollTop = container.scrollHeight;
                    }
                }

                function hideMultiTypingIndicator() {
                    const indicator = document.getElementById('multiTypingIndicator');
                    if (indicator) {
                        indicator.style.display = 'none';
                    }
                }

                // UI Utility Functions
                function showToast(message, type = 'info') {
                    // Create toast element
                    const toast = document.createElement('div');
                    toast.className = `toast toast-${type}`;
                    toast.innerHTML = `
                        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-circle' : 'info-circle'}"></i>
                        <span>${message}</span>
                    `;
                    
                    // Add to document
                    document.body.appendChild(toast);
                    
                    // Show with animation
                    setTimeout(() => toast.classList.add('show'), 100);
                    
                    // Remove after 3 seconds
                    setTimeout(() => {
                        toast.classList.remove('show');
                        setTimeout(() => document.body.removeChild(toast), 300);
                    }, 3000);
                }

                function showLoadingSpinner(message = 'Loading...') {
                    const spinner = document.createElement('div');
                    spinner.id = 'loadingSpinner';
                    spinner.className = 'loading-spinner';
                    spinner.innerHTML = `
                        <div class="spinner"></div>
                        <span>${message}</span>
                    `;
                    document.body.appendChild(spinner);
                }

                function hideLoadingSpinner() {
                    const spinner = document.getElementById('loadingSpinner');
                    if (spinner) {
                        document.body.removeChild(spinner);
                    }
                }
            </script>
        </body>
        </html>
        """


def create_simple_web_app() -> SimpleWebChatApp:
    """Factory function for simple web application"""
    return SimpleWebChatApp()


# For uvicorn
web_app_instance = create_simple_web_app()

# Add multi-bot routes to the instance that uvicorn will use
@web_app_instance.app.get("/api/multibot-status")
async def multibot_status():
    """Multi-bot conversation system status"""
    available_bots = web_app_instance.bot_connector.get_available_bots()
    return {
        "status": "active",
        "message": "Multi-bot system is working!",
        "available_bots": len(available_bots),
        "conversations": len(web_app_instance.conversation_manager.active_conversations)
    }

@web_app_instance.app.post("/api/multibot/create")
async def create_multibot_conversation(
    invitation: ConversationInvitation,
    token: str = Query(..., description="User authentication token")
):
    """Create a new multi-bot conversation"""
    user_id = web_app_instance._extract_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Validate bot names
    available_bots = web_app_instance.bot_connector.get_available_bots()
    available_bot_names = [bot["name"] for bot in available_bots]
    invalid_bots = [bot for bot in invitation.bot_names if bot not in available_bot_names]
    if invalid_bots:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid bot names: {invalid_bots}. Available: {available_bot_names}"
        )
    
    conversation = await web_app_instance.conversation_manager.create_conversation_async(
        bot_names=invitation.bot_names,
        topic=invitation.topic,
        created_by=user_id,
        initial_prompt=invitation.initial_prompt
    )
    
    return conversation

@web_app_instance.app.get("/api/multibot/conversations")
async def list_multibot_conversations(
    token: str = Query(..., description="User authentication token")
):
    """List user's multi-bot conversations"""
    user_id = web_app_instance._extract_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conversations = web_app_instance.conversation_manager.get_user_conversations(user_id)
    return {"conversations": conversations}

@web_app_instance.app.post("/api/multibot/conversations/{conversation_id}/message")
async def send_multibot_message(
    conversation_id: str,
    message: MultiBotMessage,
    token: str = Query(..., description="User authentication token")
):
    """Send message to multi-bot conversation"""
    user_id = web_app_instance._extract_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conversation = web_app_instance.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.created_by != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Store user message
    user_message = MultiBotMessage(
        conversation_id=conversation_id,
        sender=user_id,
        content=message.content,
        message_type="user"
    )
    
    responses = await web_app_instance.conversation_manager.process_message(
        conversation_id=conversation_id,
        user_message=user_message
    )
    
    return {
        "user_message": user_message,
        "bot_responses": responses,
        "conversation_id": conversation_id
    }

@web_app_instance.app.get("/api/multibot/conversations/{conversation_id}")
async def get_multibot_conversation(
    conversation_id: str,
    token: str = Query(..., description="User authentication token")
):
    """Get multi-bot conversation details and message history"""
    user_id = web_app_instance._extract_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conversation = web_app_instance.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.created_by != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    messages = web_app_instance.conversation_manager.get_conversation_messages(conversation_id)
    
    return {
        "conversation": conversation,
        "messages": messages
    }

@web_app_instance.app.delete("/api/multibot/conversations/{conversation_id}")
async def delete_multibot_conversation(
    conversation_id: str,
    token: str = Query(..., description="User authentication token")
):
    """Delete a multi-bot conversation"""
    user_id = web_app_instance._extract_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conversation = web_app_instance.conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation.created_by != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = web_app_instance.conversation_manager.delete_conversation(conversation_id)
    
    return {
        "success": success,
        "message": "Conversation deleted successfully" if success else "Failed to delete conversation"
    }

app = web_app_instance.app

if __name__ == "__main__":
    import uvicorn
    
    web_app = create_simple_web_app()
    uvicorn.run(web_app.app, host="0.0.0.0", port=8081)