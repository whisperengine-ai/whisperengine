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
        """Generate AI response"""
        try:
            # Use default model
            selected_model = "openai/gpt-4o-mini"
            
            # For demo purposes, return a mock response
            # In a real implementation, this would call the LLM API
            response_content = f"""Thank you for your message: "{message}"

I'm WhisperEngine, your AI conversation platform with advanced emotional intelligence and memory capabilities. 

I understand you're using the desktop application, which provides:
- 🔒 Local privacy with SQLite storage
- 🧠 Advanced memory networks
- 💭 Emotional intelligence

How can I assist you today?"""
            
            return {
                "content": response_content,
                "metadata": {
                    "model_used": selected_model,
                    "generation_time_ms": 500
                }
            }
        
        except Exception as e:
            logging.error(f"Error generating AI response: {e}")
            return {
                "content": "I apologize, but I encountered an error while processing your message. Please try again.",
                "metadata": {
                    "error": str(e)
                }
            }
    
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