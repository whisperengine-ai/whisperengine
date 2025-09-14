"""
Web-based User Interface for WhisperEngine
FastAPI application providing browser-accessible chat interface.
"""

import asyncio
import json
import os
import sys
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import DatabaseIntegrationManager
from src.platforms.universal_chat import UniversalChatOrchestrator, Message, MessageType, ChatPlatform, create_universal_chat_platform
from src.llm.llm_client import LLMClient


class WhisperEngineWebUI:
    """FastAPI web application for WhisperEngine"""
    
    def __init__(self, 
                 db_manager: Optional[DatabaseIntegrationManager] = None,
                 config_manager: Optional[AdaptiveConfigManager] = None,
                 llm_client: Optional[LLMClient] = None,
                 whisperengine_components: Optional[Dict[str, Any]] = None):
        self.db_manager = db_manager
        self.config_manager = config_manager or AdaptiveConfigManager()
        self.llm_client = llm_client
        self.whisperengine_components = whisperengine_components or {}
        
        # Initialize Universal Chat Orchestrator with WhisperEngine AI components
        if self.db_manager and self.config_manager:
            self.chat_orchestrator = create_universal_chat_platform(
                config_manager=self.config_manager,
                db_manager=self.db_manager,
                whisperengine_components=self.whisperengine_components
            )
            logging.info("Universal Chat Orchestrator initialized with WhisperEngine AI components")
        else:
            # Fallback initialization without database
            self.chat_orchestrator = create_universal_chat_platform(
                whisperengine_components=self.whisperengine_components
            )
            logging.warning("Chat orchestrator initialized without database integration")
        
        # Active WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Setup FastAPI app
        self.app = FastAPI(
            title="WhisperEngine",
            description="AI Conversation Platform with Advanced Intelligence",
            version="2.0.0"
        )
        
        self.setup_routes()
        self.setup_static_files()
    
    def setup_static_files(self):
        """Setup static file serving"""
        static_path = Path(__file__).parent / "static"
        templates_path = Path(__file__).parent / "templates"
        
        # Ensure directories exist
        static_path.mkdir(exist_ok=True)
        templates_path.mkdir(exist_ok=True)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Setup templates
        self.templates = Jinja2Templates(directory=str(templates_path))
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            """Serve the main chat interface"""
            return self.templates.TemplateResponse("index.html", {"request": request})
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "2.0.0",
                "active_connections": len(self.active_connections)
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time chat"""
            await self.handle_websocket(websocket)
        
        @self.app.post("/api/chat")
        async def chat_api(request: Request):
            """REST API endpoint for chat"""
            try:
                data = await request.json()
                message = data.get("message", "").strip()
                user_id = data.get("user_id", "api_user")
                
                if not message:
                    raise HTTPException(status_code=400, detail="Message cannot be empty")
                
                # Generate AI response
                response = await self.generate_ai_response(user_id, message)
                
                return {
                    "response": response["content"],
                    "metadata": response.get("metadata", {}),
                    "timestamp": datetime.now().isoformat()
                }
            
            except Exception as e:
                logging.error(f"Chat API error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/conversations/{user_id}")
        async def get_conversations(user_id: str):
            """Get conversation history for a user"""
            try:
                conversations = []
                
                # If we have the chat orchestrator, get real conversation history
                if self.chat_orchestrator:
                    # Get conversation history from the platform
                    history = await self.chat_orchestrator.get_conversation_history(
                        user_id, ChatPlatform.WEB_UI, limit=50
                    )
                    
                    # Group messages into conversations (for now, treat all as one conversation per user)
                    if history:
                        last_msg = history[-1]
                        timestamp = last_msg.timestamp.isoformat() if last_msg.timestamp else datetime.now().isoformat()
                        conversations.append({
                            "id": f"web_{user_id}",
                            "title": f"Chat with {user_id}",
                            "last_message": last_msg.content[:100] if last_msg else "",
                            "timestamp": timestamp,
                            "message_count": len(history)
                        })
                
                return {
                    "conversations": conversations,
                    "total": len(conversations)
                }
            except Exception as e:
                logging.error(f"Error getting conversations: {e}")
                return {
                    "conversations": [],
                    "total": 0
                }
    
    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection"""
        await websocket.accept()
        
        # Generate session ID
        session_id = f"ws_{datetime.now().timestamp()}_{id(websocket)}"
        self.active_connections[session_id] = websocket
        
        try:
            # Send welcome message
            await websocket.send_text(json.dumps({
                "type": "connected",
                "session_id": session_id,
                "message": "Connected to WhisperEngine"
            }))
            
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                await self.handle_websocket_message(session_id, message_data, websocket)
        
        except WebSocketDisconnect:
            logging.info(f"WebSocket {session_id} disconnected")
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
        finally:
            # Cleanup
            if session_id in self.active_connections:
                del self.active_connections[session_id]
            if session_id in self.user_sessions:
                del self.user_sessions[session_id]
    
    async def handle_websocket_message(self, session_id: str, data: Dict[str, Any], websocket: WebSocket):
        """Handle incoming WebSocket message"""
        try:
            message_type = data.get("type")
            
            if message_type == "chat_message":
                # Handle chat message
                content = data.get("content", "").strip()
                user_id = data.get("user_id", session_id)
                
                if content:
                    # Generate AI response
                    response = await self.generate_ai_response(user_id, content)
                    
                    # Send response back to client
                    await websocket.send_text(json.dumps({
                        "type": "ai_response",
                        "content": response["content"],
                        "metadata": response.get("metadata", {}),
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Store the conversation if we have the orchestrator
                    if self.chat_orchestrator:
                        try:
                            # Create user message
                            user_msg = Message(
                                message_id=f"web_user_{datetime.now().timestamp()}",
                                user_id=user_id,
                                content=content,
                                message_type=MessageType.TEXT,
                                platform=ChatPlatform.WEB_UI,
                                channel_id=f"web_session_{user_id}"
                            )
                            
                            # Create AI response message
                            ai_msg = Message(
                                message_id=f"web_ai_{datetime.now().timestamp()}",
                                user_id="assistant",
                                content=response["content"],
                                message_type=MessageType.TEXT,
                                platform=ChatPlatform.WEB_UI,
                                channel_id=f"web_session_{user_id}",
                                metadata={"is_bot_response": True}
                            )
                            
                            # Get or create conversation and store both messages
                            conversation = await self.chat_orchestrator.get_or_create_conversation(user_msg)
                            if conversation.messages is None:
                                conversation.messages = []
                            conversation.messages.extend([user_msg, ai_msg])
                            conversation.last_activity = datetime.now()
                            
                            # Store in the orchestrator's active conversations
                            self.chat_orchestrator.active_conversations[conversation.conversation_id] = conversation
                            
                        except Exception as e:
                            logging.error(f"Error storing conversation: {e}")
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Message cannot be empty"
                    }))
            
            elif message_type == "get_conversations":
                # Get conversation list
                await websocket.send_text(json.dumps({
                    "type": "conversation_list",
                    "conversations": []
                }))
        
        except Exception as e:
            logging.error(f"Error handling WebSocket message: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "An error occurred processing your message"
            }))
    
    async def generate_ai_response(self, user_id: str, message: str) -> Dict[str, Any]:
        """Generate AI response using actual WhisperEngine capabilities"""
        try:
            # Priority 1: Use Universal Chat Orchestrator for full WhisperEngine capabilities
            if self.chat_orchestrator:
                # Create message object for processing through the full pipeline
                web_message = Message(
                    message_id=f"web_{datetime.now().timestamp()}",
                    user_id=user_id,
                    content=message,
                    message_type=MessageType.TEXT,
                    platform=ChatPlatform.WEB_UI,
                    channel_id=f"web_session_{user_id}"
                )
                
                # Get or create conversation (this handles memory lookup)
                conversation = await self.chat_orchestrator.get_or_create_conversation(web_message)
                
                # Generate AI response using WhisperEngine's full capabilities
                # This goes through: security processing -> memory lookup -> AI generation -> cost optimization
                ai_response = await self.chat_orchestrator.generate_ai_response(web_message, conversation)
                
                return {
                    "content": ai_response.content,
                    "metadata": {
                        "model_used": ai_response.model_used,
                        "generation_time_ms": ai_response.generation_time_ms,
                        "tokens_used": ai_response.tokens_used,
                        "cost": ai_response.cost,
                        "confidence": ai_response.confidence,
                        "mode": "orchestrator",
                        "sources": ai_response.sources,
                        "suggestions": ai_response.suggestions
                    }
                }
            
            # Priority 2: Use LLM client directly for basic responses
            elif self.llm_client:
                # Build conversation context
                conversation_context = [
                    {
                        "role": "system", 
                        "content": """You are WhisperEngine, an AI assistant with advanced emotional intelligence and memory capabilities. 

You embody a caring, thoughtful personality with deep conversational understanding. You:
- Remember previous conversations and build relationships
- Show emotional intelligence and empathy
- Adapt your communication style to the user
- Provide helpful, personalized responses
- Maintain conversation continuity

You are running as a desktop application providing local, private AI conversations."""
                    },
                    {
                        "role": "user", 
                        "content": message
                    }
                ]
                
                # Get response from LLM client
                start_time = datetime.now()
                try:
                    completion_response = self.llm_client.generate_chat_completion(
                        messages=conversation_context,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    # Extract response from completion
                    if completion_response and 'choices' in completion_response:
                        choice = completion_response['choices'][0]
                        response = choice['message']['content']
                    else:
                        raise Exception("Invalid response format from LLM client")
                
                except Exception as e:
                    logging.error(f"LLM client error: {e}")
                    response = f"I apologize, but I'm having trouble connecting to the AI service right now. Error: {e}"
                
                generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
                
                return {
                    "content": response,
                    "metadata": {
                        "model_used": self.llm_client.chat_model_name,
                        "generation_time_ms": generation_time,
                        "mode": "direct_llm",
                        "service": self.llm_client.service_name
                    }
                }
            
            # Final fallback - demo response
            else:
                response_content = f"""Thank you for your message: "{message}"

I'm WhisperEngine, your AI conversation platform with advanced emotional intelligence and memory capabilities. 

I understand you're using the desktop application, which provides:
- 🔒 Local privacy with SQLite storage
- 🧠 Advanced memory networks
- 💭 Emotional intelligence

**Note**: Full AI capabilities are not yet connected. Please ensure your LLM service is configured.

How can I assist you today?"""
                
                return {
                    "content": response_content,
                    "metadata": {
                        "model_used": "demo_mode",
                        "generation_time_ms": 100,
                        "mode": "fallback"
                    }
                }
        
        except Exception as e:
            logging.error(f"Error generating AI response: {e}")
            return {
                "content": "I apologize, but I encountered an error while processing your message. Please try again.",
                "metadata": {
                    "error": str(e),
                    "mode": "error_fallback"
                }
            }
    
    async def initialize(self):
        """Initialize the web UI and its components"""
        if self.chat_orchestrator:
            try:
                await self.chat_orchestrator.initialize()
                logging.info("Universal Chat Orchestrator initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize chat orchestrator: {e}")
                self.chat_orchestrator = None
    
    async def start(self, host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True):
        """Start the web UI server"""
        try:
            # Initialize components first
            await self.initialize()
            
            # Open browser if requested
            if open_browser:
                def open_browser_delayed():
                    import time
                    time.sleep(1.5)  # Wait for server to start
                    webbrowser.open(f"http://{host}:{port}")
                
                import threading
                threading.Thread(target=open_browser_delayed, daemon=True).start()
            
            # Start server
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        
        except Exception as e:
            logging.error(f"Error starting web UI: {e}")
            raise
    
    def run_sync(self, host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True):
        """Run the web UI synchronously"""
        asyncio.run(self.start(host, port, open_browser))

# Factory function for easy import
def create_web_ui(db_manager: Optional[DatabaseIntegrationManager] = None,
                  config_manager: Optional[AdaptiveConfigManager] = None,
                  llm_client: Optional[LLMClient] = None,
                  whisperengine_components: Optional[Dict[str, Any]] = None) -> WhisperEngineWebUI:
    """Create WhisperEngine Web UI instance with AI components"""
    return WhisperEngineWebUI(db_manager, config_manager, llm_client, whisperengine_components)


# For testing
async def main():
    """Test the web UI"""
    web_ui = create_web_ui()
    await web_ui.start()


if __name__ == "__main__":
    asyncio.run(main())