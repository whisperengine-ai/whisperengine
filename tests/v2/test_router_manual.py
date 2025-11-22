import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from src_v2.agents.router import CognitiveRouter
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

async def test_router():
    print("Initializing Router...")
    try:
        router = CognitiveRouter()
    except Exception as e:
        print(f"Failed to init router: {e}")
        return

    user_id = "test_user_123"
    
    # Test 1: Small talk (Should NOT call tools)
    print("\n--- Test 1: Small Talk ---")
    try:
        result = await router.route_and_retrieve(user_id, "Hi, how are you?")
        print(f"Reasoning: {result.get('reasoning')}")
        print(f"Tool Calls: {result.get('tool_calls')}")
    except Exception as e:
        print(f"Test 1 failed: {e}")
    
    # Test 2: Memory Query (Should call SearchSummaries or SearchEpisodes)
    print("\n--- Test 2: Memory Query ---")
    try:
        result = await router.route_and_retrieve(user_id, "What did we talk about last week regarding marine biology?")
        print(f"Reasoning: {result.get('reasoning')}")
        print(f"Tool Calls: {result.get('tool_calls')}")
    except Exception as e:
        print(f"Test 2 failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_router())
