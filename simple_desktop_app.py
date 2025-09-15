#!/usr/bin/env python3
"""
Simple WhisperEngine Desktop App - Minimal Working Version
"""

import asyncio
import json
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from env_manager import load_environment
if not load_environment():
    print("❌ Failed to load environment configuration")
    sys.exit(1)

# Simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleWhisperEngineApp:
    """Minimal WhisperEngine desktop app"""
    
    def __init__(self):
        self.app = FastAPI(title="WhisperEngine Simple Desktop App")
        self.active_connections: Dict[str, WebSocket] = {}
        self.setup_routes()
        self.shutdown_event = asyncio.Event()
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        # Static files
        static_path = project_root / "src" / "ui" / "static"
        if static_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Templates
        template_path = project_root / "src" / "ui" / "templates"
        if template_path.exists():
            templates = Jinja2Templates(directory=str(template_path))
        
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            if template_path.exists():
                return templates.TemplateResponse("index.html", {"request": request})
            else:
                return HTMLResponse("""
                <html>
                    <head><title>WhisperEngine Simple Test</title></head>
                    <body>
                        <h1>🤖 WhisperEngine Simple Test</h1>
                        <div id="messages"></div>
                        <input type="text" id="messageInput" placeholder="Type a message...">
                        <button onclick="sendMessage()">Send</button>
                        
                        <script>
                            const ws = new WebSocket('ws://localhost:8080/ws');
                            const messages = document.getElementById('messages');
                            
                            ws.onopen = () => {
                                console.log('Connected to WebSocket');
                                addMessage('✅ Connected to WhisperEngine');
                            };
                            
                            ws.onmessage = (event) => {
                                const data = JSON.parse(event.data);
                                addMessage(`🤖 ${data.content || data.message || JSON.stringify(data)}`);
                            };
                            
                            ws.onclose = () => {
                                addMessage('❌ Connection lost');
                            };
                            
                            function sendMessage() {
                                const input = document.getElementById('messageInput');
                                const message = input.value.trim();
                                if (message) {
                                    ws.send(JSON.stringify({
                                        type: 'chat_message',
                                        content: message,
                                        user_id: 'test_user'
                                    }));
                                    addMessage(`👤 ${message}`);
                                    input.value = '';
                                }
                            }
                            
                            function addMessage(text) {
                                const div = document.createElement('div');
                                div.textContent = text;
                                messages.appendChild(div);
                                messages.scrollTop = messages.scrollHeight;
                            }
                            
                            document.getElementById('messageInput').addEventListener('keypress', (e) => {
                                if (e.key === 'Enter') sendMessage();
                            });
                        </script>
                    </body>
                </html>
                """)
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.handle_websocket(websocket)
    
    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections"""
        await websocket.accept()
        session_id = f"session_{datetime.now().timestamp()}"
        self.active_connections[session_id] = websocket
        
        try:
            # Send welcome message
            await websocket.send_text(json.dumps({
                "type": "connected",
                "message": "Connected to WhisperEngine Simple Test",
                "session_id": session_id
            }))
            
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Simple echo response for testing
                content = message_data.get("content", "")
                await websocket.send_text(json.dumps({
                    "type": "ai_response",
                    "content": f"Echo: {content} (Simple test mode - AI integration disabled for testing)",
                    "timestamp": datetime.now().isoformat()
                }))
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket {session_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            if session_id in self.active_connections:
                del self.active_connections[session_id]
    
    async def start_server(self):
        """Start the server with proper signal handling"""
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        config = uvicorn.Config(
            self.app,
            host="127.0.0.1",
            port=8080,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Start server in background
        server_task = asyncio.create_task(server.serve())
        
        print("🤖 Simple WhisperEngine Test App")
        print("🌐 Server running at http://127.0.0.1:8080")
        print("🔗 WebSocket endpoint: ws://127.0.0.1:8080/ws")
        print("⚡ Press Ctrl+C to stop")
        
        # Wait for shutdown signal
        await self.shutdown_event.wait()
        
        print("🛑 Shutting down server...")
        server.should_exit = True
        await server_task
        print("✅ Server stopped")


async def main():
    """Main entry point"""
    app = SimpleWhisperEngineApp()
    await app.start_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)