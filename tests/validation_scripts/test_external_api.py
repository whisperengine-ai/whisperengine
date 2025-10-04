#!/usr/bin/env python3
"""
Test script for WhisperEngine External Chat API.

This script demonstrates how to interact with the external chat API endpoints
that reuse the same message processing pipeline as Discord.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

import aiohttp

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperEngineAPIClient:
    """Client for interacting with WhisperEngine External Chat API."""

    def __init__(self, base_url: str = "http://localhost:9091"):
        """Initialize the API client."""
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy."""
        if self.session is None:
            raise RuntimeError("Session not initialized")
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()

    async def get_status(self) -> Dict[str, Any]:
        """Get detailed status information."""
        if self.session is None:
            raise RuntimeError("Session not initialized")
        async with self.session.get(f"{self.base_url}/status") as response:
            return await response.json()

    async def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information."""
        if self.session is None:
            raise RuntimeError("Session not initialized")
        async with self.session.get(f"{self.base_url}/api/bot-info") as response:
            return await response.json()

    async def send_message(self, user_id: str, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a single message to the bot."""
        if self.session is None:
            raise RuntimeError("Session not initialized")
            
        payload: Dict[str, Any] = {
            "user_id": user_id,
            "message": message
        }
        
        if context:
            payload["context"] = context

        async with self.session.post(
            f"{self.base_url}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            result = await response.json()
            result["status_code"] = response.status
            return result

    async def send_batch_messages(self, messages: list) -> Dict[str, Any]:
        """Send multiple messages in a batch."""
        if self.session is None:
            raise RuntimeError("Session not initialized")
            
        payload = {"messages": messages}

        async with self.session.post(
            f"{self.base_url}/api/chat/batch",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            result = await response.json()
            result["status_code"] = response.status
            return result


async def test_api_endpoints():
    """Test all API endpoints."""
    print("🧪 Testing WhisperEngine External Chat API")
    print("=" * 50)

    # Test different bot ports (Elena, Marcus, Jake, etc.)
    bot_ports = [9091, 9092, 9093, 9094, 9095, 9096, 9097]
    
    for port in bot_ports:
        base_url = f"http://localhost:{port}"
        print(f"\n🤖 Testing bot on port {port}")
        print("-" * 30)
        
        try:
            async with WhisperEngineAPIClient(base_url) as client:
                # Test 1: Health check
                print("1. Health check...")
                health = await client.health_check()
                print(f"   Status: {health.get('status', 'unknown')}")
                
                # Test 2: Bot info
                print("2. Bot info...")
                bot_info = await client.get_bot_info()
                bot_name = bot_info.get('bot_name', 'Unknown')
                character = bot_info.get('character_info', {}).get('character_name', 'Unknown')
                print(f"   Bot: {bot_name}")
                print(f"   Character: {character}")
                
                # Test 3: Single message
                print("3. Single message...")
                test_user_id = f"test_user_{port}"
                test_message = "Hello! I'm testing the external API. Can you tell me about yourself?"
                
                chat_result = await client.send_message(
                    user_id=test_user_id,
                    message=test_message,
                    context={
                        "channel_type": "dm",
                        "platform": "api",
                        "metadata": {"test": True}
                    }
                )
                
                if chat_result.get("success", False):
                    response = chat_result.get("response", "")
                    processing_time = chat_result.get("processing_time_ms", 0)
                    memory_stored = chat_result.get("memory_stored", False)
                    
                    print(f"   ✅ Success (took {processing_time}ms, memory: {memory_stored})")
                    print(f"   Response: {response[:150]}{'...' if len(response) > 150 else ''}")
                else:
                    print(f"   ❌ Failed: {chat_result.get('error', 'Unknown error')}")
                
                # Test 4: Batch messages (smaller test)
                print("4. Batch messages...")
                batch_messages = [
                    {
                        "user_id": f"test_user_{port}_batch",
                        "message": "What's your name?",
                        "context": {"channel_type": "dm"}
                    },
                    {
                        "user_id": f"test_user_{port}_batch",
                        "message": "What do you like to do?",
                        "context": {"channel_type": "dm"}
                    }
                ]
                
                batch_result = await client.send_batch_messages(batch_messages)
                
                if batch_result.get("status_code") == 200:
                    results = batch_result.get("results", [])
                    successful = sum(1 for r in results if r.get("success"))
                    print(f"   ✅ Batch: {successful}/{len(results)} messages successful")
                    
                    for result in results:
                        if result.get("success"):
                            response = result.get("response", "")
                            print(f"   Response {result.get('index', '?')}: {response[:100]}{'...' if len(response) > 100 else ''}")
                else:
                    print(f"   ❌ Batch failed: {batch_result.get('error', 'Unknown error')}")

        except aiohttp.ClientConnectorError:
            print(f"   ⚠️  Bot not running on port {port}")
        except Exception as e:
            print(f"   ❌ Error testing port {port}: {e}")


async def interactive_chat():
    """Interactive chat session with a bot."""
    print("\n🗣️  Interactive Chat Session")
    print("=" * 50)
    print("Available ports: 9091 (Elena), 9092 (Marcus), 9093 (Ryan), etc.")
    
    try:
        port = input("Enter bot port (default 9091): ").strip() or "9091"
        port = int(port)
        base_url = f"http://localhost:{port}"
        
        user_id = input("Enter your user ID (default: interactive_user): ").strip() or "interactive_user"
        
        print(f"\n🤖 Connecting to bot on port {port}...")
        
        async with WhisperEngineAPIClient(base_url) as client:
            # Get bot info
            bot_info = await client.get_bot_info()
            bot_name = bot_info.get('bot_name', 'Unknown Bot')
            character = bot_info.get('character_info', {}).get('character_name', 'Unknown Character')
            
            print(f"✅ Connected to {bot_name} ({character})")
            print("Type 'quit' to exit\n")
            
            while True:
                message = input(f"{user_id}: ").strip()
                
                if message.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not message:
                    continue
                
                print("🤔 Thinking...", end="", flush=True)
                
                try:
                    result = await client.send_message(
                        user_id=user_id,
                        message=message,
                        context={"channel_type": "dm", "platform": "api"}
                    )
                    
                    print("\r", end="")  # Clear the "Thinking..." message
                    
                    if result.get("success"):
                        response = result.get("response", "")
                        processing_time = result.get("processing_time_ms", 0)
                        print(f"{bot_name}: {response}")
                        print(f"   (took {processing_time}ms)\n")
                    else:
                        print(f"❌ Error: {result.get('error', 'Unknown error')}\n")
                        
                except Exception as e:
                    print(f"\r❌ Connection error: {e}\n")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Main test function."""
    print("WhisperEngine External Chat API Test Client")
    print("=" * 50)
    
    mode = input("Choose mode:\n1. Test all endpoints\n2. Interactive chat\nEnter choice (1 or 2): ").strip()
    
    if mode == "1":
        await test_api_endpoints()
    elif mode == "2":
        await interactive_chat()
    else:
        print("Invalid choice. Running endpoint tests...")
        await test_api_endpoints()


if __name__ == "__main__":
    asyncio.run(main())