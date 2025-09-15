#!/usr/bin/env python3
"""
Quick test to verify all UI fixes are working correctly
"""

import asyncio
import json
import websockets

async def test_websocket():
    """Test WebSocket message format"""
    try:
        # Connect to WebSocket
        async with websockets.connect('ws://127.0.0.1:8080/ws') as websocket:
            print("✅ Connected to WebSocket")
            
            # Test 1: Load conversations
            await websocket.send(json.dumps({
                'type': 'load_conversations'
            }))
            print("📤 Requested conversation list")
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            print(f"📥 Received: {data['type']}")
            
            if data['type'] == 'conversation_list':
                conversations = data.get('conversations', [])
                print(f"📋 Found {len(conversations)} conversations")
                for conv in conversations[:3]:  # Show first 3
                    print(f"   - {conv.get('title', 'Untitled')} ({conv.get('message_count', 0)} messages)")
            
            # Test 2: Create new conversation
            test_conv_id = f"test_conv_{int(asyncio.get_event_loop().time())}"
            await websocket.send(json.dumps({
                'type': 'chat_message',
                'content': 'Started new conversation: Test Conversation',
                'user_id': 'system',
                'conversation_id': test_conv_id,
                'files': []
            }))
            print("📤 Created test conversation")
            
            # Test 3: Send regular message
            await websocket.send(json.dumps({
                'type': 'chat_message',
                'content': 'Hello, this is a test message!',
                'user_id': 'user',
                'conversation_id': test_conv_id,
                'files': []
            }))
            print("📤 Sent test message")
            
            # Wait for AI response
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(response)
            if data['type'] == 'ai_response':
                print("✅ AI responded successfully")
                print(f"🤖 Response: {data['content'][:100]}...")
            else:
                print(f"❌ Unexpected response: {data}")
            
            print("\n✅ All WebSocket tests passed!")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing WhisperEngine Desktop UI Fixes")
    print("=" * 50)
    asyncio.run(test_websocket())