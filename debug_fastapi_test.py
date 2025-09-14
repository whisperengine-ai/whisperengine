#!/usr/bin/env python3
"""
Minimal test to see if FastAPI/Uvicorn context causes 404 errors
"""
import asyncio
import json
import logging
import uvicorn
from datetime import datetime
from fastapi import FastAPI, WebSocket
from env_manager import load_environment
from src.llm.llm_client import LLMClient

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

class TestWebServer:
    def __init__(self):
        load_environment()
        self.app = FastAPI()
        self.llm_client = LLMClient()
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.websocket("/test")
        async def test_websocket(websocket: WebSocket):
            await websocket.accept()
            print("WebSocket connected")
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    content = message_data.get("content", "")
                    
                    print(f"Received: {content}")
                    
                    # Test LLM call in WebSocket context
                    conversation_context = [
                        {"role": "system", "content": "You are a test assistant."},
                        {"role": "user", "content": content}
                    ]
                    
                    try:
                        print("Making LLM call from WebSocket context...")
                        completion_response = self.llm_client.generate_chat_completion(
                            messages=conversation_context,
                            temperature=0.7,
                            max_tokens=100
                        )
                        
                        if completion_response and 'choices' in completion_response:
                            response = completion_response['choices'][0]['message']['content']
                            print(f"LLM SUCCESS: {response}")
                            
                            await websocket.send_text(json.dumps({
                                "type": "success",
                                "content": response
                            }))
                        else:
                            print(f"LLM FAILED: Invalid response format")
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": "Invalid response format"
                            }))
                            
                    except Exception as e:
                        print(f"LLM EXCEPTION: {e}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": str(e)
                        }))
                        
            except Exception as e:
                print(f"WebSocket error: {e}")
    
    def run(self):
        print("Starting test server on http://127.0.0.1:8082")
        print("Test by connecting to ws://127.0.0.1:8082/test and sending:")
        print('{"content": "Hello test"}')
        uvicorn.run(self.app, host="127.0.0.1", port=8082)

if __name__ == "__main__":
    server = TestWebServer()
    server.run()