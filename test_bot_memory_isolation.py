#!/usr/bin/env python3
"""
Test Bot Memory Isolation

This script tests that each bot only sees its own memories by:
1. Setting different bot names in environment
2. Storing test memories for each bot
3. Verifying that searches only return bot-specific memories

Usage:
    python test_bot_memory_isolation.py
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List

# Add src to path
sys.path.insert(0, 'src')

from memory.memory_protocol import create_memory_manager
from memory.vector_memory_system import MemoryType, VectorMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotMemoryIsolationTester:
    """Test bot memory isolation"""
    
    def __init__(self):
        self.test_user_id = "test_user_12345"
        self.test_bots = ["Elena", "Marcus", "Gabriel"]
        self.test_memories = {
            "Elena": [
                "Elena loves helping with emotional support",
                "Elena prefers warm and caring conversations",
                "Elena remembers user's feelings very well"
            ],
            "Marcus": [
                "Marcus excels at analytical thinking",
                "Marcus provides strategic advice",
                "Marcus focuses on logical problem solving"
            ],
            "Gabriel": [
                "Gabriel explores consciousness and philosophy", 
                "Gabriel discusses the nature of awareness",
                "Gabriel contemplates existence and meaning"
            ]
        }
    
    async def store_bot_memories(self, bot_name: str) -> int:
        """Store test memories for a specific bot"""
        # Set bot name in environment
        os.environ["DISCORD_BOT_NAME"] = bot_name
        
        # Create memory manager for this bot
        memory_manager = create_memory_manager(memory_type="vector")
        
        memories_stored = 0
        for memory_text in self.test_memories[bot_name]:
            try:
                # Create a test memory
                memory = VectorMemory(
                    user_id=self.test_user_id,
                    content=memory_text,
                    memory_type=MemoryType.FACT,
                    timestamp=datetime.utcnow(),
                    confidence=0.9,
                    source=f"test_bot_isolation_{bot_name}"
                )
                
                # Store using the vector memory store directly
                if hasattr(memory_manager, 'vector_store'):
                    await memory_manager.vector_store.store_memory(memory)
                    memories_stored += 1
                    logger.info(f"✅ Stored memory for {bot_name}: {memory_text[:50]}...")
                else:
                    logger.error(f"❌ Memory manager doesn't have vector_store attribute")
                    
            except Exception as e:
                logger.error(f"❌ Failed to store memory for {bot_name}: {e}")
        
        return memories_stored
    
    async def search_bot_memories(self, bot_name: str) -> List[Dict]:
        """Search memories as a specific bot"""
        # Set bot name in environment
        os.environ["DISCORD_BOT_NAME"] = bot_name
        
        # Create memory manager for this bot
        memory_manager = create_memory_manager(memory_type="vector")
        
        try:
            # Search for all memories for the test user
            if hasattr(memory_manager, 'vector_store'):
                results = await memory_manager.vector_store.search_memories_with_qdrant_intelligence(
                    query="test memories",
                    user_id=self.test_user_id,
                    top_k=20,
                    min_score=0.0  # Get all memories regardless of score
                )
                return results
            else:
                logger.error(f"❌ Memory manager doesn't have vector_store attribute")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to search memories for {bot_name}: {e}")
            return []
    
    async def test_isolation(self):
        """Run the complete isolation test"""
        print("🧪 Testing Bot Memory Isolation")
        print("=" * 50)
        
        # Step 1: Store memories for each bot
        print("\n📝 Step 1: Storing test memories for each bot...")
        storage_results = {}
        
        for bot_name in self.test_bots:
            print(f"\n🤖 Storing memories for {bot_name}...")
            count = await self.store_bot_memories(bot_name)
            storage_results[bot_name] = count
            print(f"   ✅ Stored {count} memories for {bot_name}")
        
        # Small delay to ensure all memories are indexed
        await asyncio.sleep(2)
        
        # Step 2: Test that each bot only sees its own memories
        print("\n🔍 Step 2: Testing memory isolation...")
        isolation_results = {}
        
        for bot_name in self.test_bots:
            print(f"\n🔎 Searching as {bot_name}...")
            memories = await self.search_bot_memories(bot_name)
            isolation_results[bot_name] = memories
            
            print(f"   📊 Found {len(memories)} memories")
            
            # Check if only this bot's memories are returned
            bot_specific_count = 0
            other_bot_count = 0
            
            for memory in memories:
                content = memory.get('content', '')
                if any(phrase in content for phrase in self.test_memories[bot_name]):
                    bot_specific_count += 1
                else:
                    # Check if it belongs to another bot
                    for other_bot, other_memories in self.test_memories.items():
                        if other_bot != bot_name and any(phrase in content for phrase in other_memories):
                            other_bot_count += 1
                            break
            
            print(f"   ✅ Own memories found: {bot_specific_count}")
            print(f"   ❌ Other bot memories found: {other_bot_count}")
            
            if other_bot_count == 0:
                print(f"   🎉 {bot_name} isolation: PASSED")
            else:
                print(f"   ⚠️  {bot_name} isolation: FAILED - seeing other bot's memories!")
        
        # Step 3: Summary
        print("\n📊 Test Summary")
        print("=" * 30)
        
        total_stored = sum(storage_results.values())
        print(f"📝 Total memories stored: {total_stored}")
        
        all_isolated = True
        for bot_name in self.test_bots:
            memories = isolation_results[bot_name]
            other_bot_count = 0
            
            for memory in memories:
                content = memory.get('content', '')
                for other_bot, other_memories in self.test_memories.items():
                    if other_bot != bot_name and any(phrase in content for phrase in other_memories):
                        other_bot_count += 1
                        break
            
            if other_bot_count > 0:
                all_isolated = False
            
            print(f"🤖 {bot_name}: {len(memories)} memories, isolation {'✅ PASSED' if other_bot_count == 0 else '❌ FAILED'}")
        
        print(f"\n🎯 Overall Test Result: {'✅ ALL BOTS PROPERLY ISOLATED' if all_isolated else '❌ ISOLATION FAILED'}")
        
        return all_isolated


async def main():
    """Run the bot memory isolation test"""
    tester = BotMemoryIsolationTester()
    
    try:
        success = await tester.test_isolation()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())