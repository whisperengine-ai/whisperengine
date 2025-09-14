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
from src.platforms.universal_chat import (
    UniversalChatOrchestrator, 
    WebUIChatAdapter, 
    Message, 
    ChatPlatform, 
    MessageType,
    User
)


class WhisperEngineWebUI:
    """FastAPI web application for WhisperEngine"""
    
    def __init__(self, 
                 db_manager: Optional[DatabaseIntegrationManager] = None,
                 config_manager: Optional[AdaptiveConfigManager] = None):
        self.db_manager = db_manager
        self.config_manager = config_manager or AdaptiveConfigManager()
        
        # Active WebSocket connections
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize Universal Chat System
        self.setup_universal_chat()
        
        # Setup FastAPI app
        self.app = FastAPI(
            title="WhisperEngine",
            description="AI Conversation Platform with Advanced Intelligence",
            version="2.0.0"
        )
        
        self.setup_routes()
        self.setup_static_files()
    
    def setup_universal_chat(self):
        """Initialize the universal chat orchestrator"""
        try:
            # Check if we're using local database integration
            using_local_db = (self.db_manager and 
                            hasattr(self.db_manager, '__class__') and
                            'Local' in self.db_manager.__class__.__name__)
            
            if using_local_db:
                # Create orchestrator with local DB manager, but disable enhanced core
                self.chat_orchestrator = UniversalChatOrchestrator(
                    config_manager=self.config_manager,
                    db_manager=self.db_manager,
                    bot_core=None,
                    use_enhanced_core=False  # Disable enhanced core for local DB mode
                )
                logging.info("✅ Universal chat system initialized with local database integration")
            else:
                # Create orchestrator with enhanced core for full Discord mode
                self.chat_orchestrator = UniversalChatOrchestrator(
                    config_manager=self.config_manager,
                    db_manager=self.db_manager or DatabaseIntegrationManager(self.config_manager)
                )
                logging.info("✅ Universal chat system initialized with enhanced core")
            
        except Exception as e:
            logging.error(f"Failed to initialize universal chat system: {e}")
            # Fallback to basic mode
            self.chat_orchestrator = None
    
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
        
        # Initialize setup guidance manager
        from src.ui.setup_guidance import add_setup_guidance_routes
        self.setup_guidance_manager = add_setup_guidance_routes(self.app, self.templates)
    
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
                # In a real implementation, this would query the database
                return {
                    "conversations": [],
                    "total": 0
                }
            except Exception as e:
                logging.error(f"Error getting conversations: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
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
        """Generate AI response using the universal chat system"""
        try:
            if self.chat_orchestrator:
                # Initialize the chat orchestrator if not already done
                if not hasattr(self.chat_orchestrator, 'adapters') or not self.chat_orchestrator.adapters:
                    await self.chat_orchestrator.initialize()
                
                # Create a universal message object
                message_obj = Message(
                    message_id=f"web_{user_id}_{int(datetime.now().timestamp())}",
                    user_id=user_id,
                    content=message,
                    platform=ChatPlatform.WEB_UI,
                    channel_id=f"web_session_{user_id}",
                    message_type=MessageType.TEXT
                )
                
                # Get or create conversation
                conversation = await self.chat_orchestrator.get_or_create_conversation(message_obj)
                
                # Generate AI response through the orchestrator
                ai_response = await self.chat_orchestrator.generate_ai_response(message_obj, conversation)
                
                return {
                    "content": ai_response.content,
                    "metadata": {
                        "model_used": ai_response.model_used,
                        "tokens_used": ai_response.tokens_used,
                        "cost": ai_response.cost,
                        "generation_time_ms": ai_response.generation_time_ms,
                        "confidence": ai_response.confidence,
                        "user_id": user_id,
                        "platform": "universal_chat",
                        "status": "real_ai" if ai_response.model_used != "fallback" else "fallback_error"
                    }
                }
            else:
                # Fallback to basic response
                return await self._generate_fallback_response(user_id, message)
        
        except Exception as e:
            logging.error(f"Error generating AI response: {e}")
            return await self._generate_fallback_response(user_id, message)
    
    async def _generate_fallback_response(self, user_id: str, message: str) -> Dict[str, Any]:
        """Fallback response when universal chat system is not available"""
        try:
            # Import LLM client directly as fallback
            from src.llm.llm_client import LLMClient
            
            # Initialize LLM client if not already done
            if not hasattr(self, 'llm_client'):
                self.llm_client = LLMClient()
            
            # Create conversation messages
            messages = [
                {
                    "role": "system", 
                    "content": """You are WhisperEngine, an advanced AI conversation platform with emotional intelligence and memory capabilities. 

You are running in desktop app mode, providing:
- 🔒 Local privacy with SQLite storage  
- 🧠 Advanced memory networks
- 💭 Emotional intelligence
- 🖥️ Native macOS integration

Be helpful, engaging, and demonstrate your advanced capabilities. Keep responses conversational but informative."""
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
            
            # Generate response using LLM client
            response_text = self.llm_client.get_chat_response(messages)
            
            return {
                "content": response_text,
                "metadata": {
                    "model_used": self.llm_client.chat_model_name,
                    "service": self.llm_client.service_name,
                    "user_id": user_id,
                    "platform": "fallback_direct",
                    "status": "direct_llm"
                }
            }
        
        except Exception as e:
            logging.error(f"Fallback response failed: {e}")
            
            # Check if this is a dependency issue
            dependency_issue = "requests" in str(e) or "ModuleNotFoundError" in str(e)
            
            if dependency_issue:
                error_content = """⚠️ **Missing Dependencies Detected**

I'm currently running in fallback mode because some required Python packages are missing. To enable full AI capabilities:

1. **Install missing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
2. **Or install specific packages:**
   ```bash
   pip install requests fastapi uvicorn aiohttp
   ```

3. **If using macOS with homebrew Python:**
   ```bash
   pip install --user -r requirements.txt
   ```

**Current Status:** Architecture is working correctly, but LLM client can't make API calls due to missing `requests` module.

For technical details, check the console logs."""
            else:
                error_content = f"I apologize, but I'm experiencing technical difficulties. The chat system is currently unavailable. Error: {str(e)}"
            
            return {
                "content": error_content,
                "metadata": {
                    "error": str(e),
                    "user_id": user_id,
                    "platform": "error_fallback",
                    "status": "dependency_error" if dependency_issue else "system_error"
                }
            }
    
    def set_setup_guidance(self, guidance_data: Dict[str, Any]):
        """Set setup guidance data for display in UI"""
        if hasattr(self, 'setup_guidance_manager'):
            self.setup_guidance_manager.set_setup_guidance(guidance_data)
            logging.info("Setup guidance set for web UI display")
        else:
            logging.warning("Setup guidance manager not available")
    
    def clear_setup_guidance(self):
        """Clear setup guidance when LLM is configured"""
        if hasattr(self, 'setup_guidance_manager'):
            self.setup_guidance_manager.clear_setup_guidance()
            logging.info("Setup guidance cleared from web UI")
    
    async def start(self, host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True):
        """Start the web UI server"""
        try:
            # Open browser if requested
            if open_browser:
                def open_browser_delayed():
                    import time
                    time.sleep(1.5)  # Wait for server to start
                    webbrowser.open(f"http://{host}:{port}")
                
                import threading
                threading.Thread(target=open_browser_delayed, daemon=True).start()
            
            # Start server with proper signal handling
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info",
                access_log=False  # Reduce noise in desktop app
            )
            server = uvicorn.Server(config)
            
            # Handle shutdown gracefully
            try:
                await server.serve()
            except KeyboardInterrupt:
                logging.info("Web UI shutting down...")
                await server.shutdown()
        
        except Exception as e:
            logging.error(f"Error starting web UI: {e}")
            raise
    
    def run_sync(self, host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True):
        """Run the web UI synchronously"""
        asyncio.run(self.start(host, port, open_browser))

# Factory function for easy import
def create_web_ui(db_manager: Optional[DatabaseIntegrationManager] = None,
                  config_manager: Optional[AdaptiveConfigManager] = None) -> WhisperEngineWebUI:
    """Create WhisperEngine Web UI instance"""
    return WhisperEngineWebUI(db_manager, config_manager)


# For testing
async def main():
    """Test the web UI"""
    web_ui = create_web_ui()
    await web_ui.start()


if __name__ == "__main__":
    asyncio.run(main())