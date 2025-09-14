#!/usr/bin/env python3
"""
Simple WebSocket client without env_manager interference
"""
import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://127.0.0.1:8082/test"
    
    try:
        print("Connecting to test server...")
        async with websockets.connect(uri) as websocket:
            print("Connected! Sending test message...")
            
            test_message = {
                "content": "Hello test from WebSocket client"
            }
            
            await websocket.send(json.dumps(test_message))
            print("Message sent, waiting for response...")
            
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"Response type: {response_data.get('type')}")
            print(f"Response content: {response_data.get('content', response_data.get('message'))}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())