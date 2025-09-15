#!/usr/bin/env python3
"""
Simple WebSocket test server to verify the basic functionality works
"""

import asyncio
import json
import signal
import sys
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Simple HTML for testing
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple WebSocket Test</title>
</head>
<body>
    <h1>WebSocket Test</h1>
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="Type a message...">
    <button onclick="sendMessage()">Send</button>
    <button onclick="testUpload()">Test File Upload</button>

    <script>
        const ws = new WebSocket('ws://localhost:8080/ws');
        const messages = document.getElementById('messages');
        
        ws.onopen = function(event) {
            addMessage('Connected to server');
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            addMessage('Server: ' + data.content);
        };
        
        ws.onclose = function(event) {
            addMessage('Connection closed');
        };
        
        ws.onerror = function(error) {
            addMessage('Error: ' + error);
        };
        
        function addMessage(message) {
            const div = document.createElement('div');
            div.textContent = new Date().toLocaleTimeString() + ' - ' + message;
            messages.appendChild(div);
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            if (input.value.trim()) {
                ws.send(JSON.stringify({
                    type: 'chat_message',
                    content: input.value,
                    user_id: 'test_user'
                }));
                addMessage('You: ' + input.value);
                input.value = '';
            }
        }
        
        function testUpload() {
            addMessage('File upload test clicked');
        }
        
        // Send message on Enter key
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

app = FastAPI()

# Store active connections
connections = set()

@app.get("/")
async def get():
    return HTMLResponse(HTML_CONTENT)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "system",
            "content": "Connected to simple test server"
        }))
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Echo back with simple processing
            response = {
                "type": "response",
                "content": f"Echo: {message_data.get('content', 'No content')}",
                "original": message_data
            }
            
            await websocket.send_text(json.dumps(response))
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connections.discard(websocket)

def signal_handler(signum, frame):
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🧪 Starting simple WebSocket test server...")
    print("📱 Open http://127.0.0.1:8080 to test")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
    except KeyboardInterrupt:
        print("\n✅ Server stopped cleanly")