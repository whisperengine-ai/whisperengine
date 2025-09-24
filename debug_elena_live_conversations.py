#!/usr/bin/env python3
"""
Debug Elena's Conversation Source Problem

This script investigates why Elena's memory contains only meta-questions
instead of substantive marine biology discussions. The issue appears to be
that users are only asking "what did we talk about?" instead of having
real conversations.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.memory.memory_protocol import create_memory_manager

async def investigate_conversation_source():
    """Investigate the source of Elena's conversation data"""
    print("🔍 INVESTIGATION: Elena's Conversation Source Problem")
    
    # Initialize memory manager with Elena's config
    os.environ.setdefault("MEMORY_SYSTEM_TYPE", "vector")
    os.environ.setdefault("BOT_NAME", "elena")
    os.environ.setdefault("QDRANT_COLLECTION_NAME", "whisperengine_memory")
    
    memory_manager = create_memory_manager(memory_type="vector")
    
    print("\n=== THEORY: Users Only Ask Meta-Questions ===")
    print("If Elena's memory contains only questions like 'what did we talk about?',")
    print("it suggests users aren't having substantive marine biology conversations.")
    print("They're only asking Elena to recall non-existent past conversations.")
    
    # Search for different types of content
    test_queries = [
        ("marine biology topics", "marine ocean fish coral biology research"),
        ("general conversation", "conversation discussion talk chat"),
        ("memory questions", "what did talk about remember conversation history"),
        ("user interactions", "user message question answer"),
        ("elena responses", "elena marine biologist research ocean"),
    ]
    
    print("\n=== SEARCHING FOR DIFFERENT CONTENT TYPES ===")
    
    total_memories_found = 0
    
    for query_name, query_text in test_queries:
        print(f"\n📍 Searching for: {query_name}")
        print(f"    Query: '{query_text}'")
        
        try:
            memories = await memory_manager.retrieve_relevant_memories(
                user_id="user_test", # Use a test user ID
                query=query_text,
                limit=10
            )
            
            print(f"    Found: {len(memories)} memories")
            total_memories_found += len(memories)
            
            if memories:
                print("    Sample content:")
                for i, memory in enumerate(memories[:3], 1):
                    content = memory.get("content", "")
                    role = memory.get("metadata", {}).get("role", "unknown")
                    print(f"      {i}. [{role}] '{content[:80]}{'...' if len(content) > 80 else ''}'")
            else:
                print("    No memories found")
                
        except Exception as e:
            print(f"    ❌ Search failed: {e}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total memories found across all searches: {total_memories_found}")
    
    if total_memories_found == 0:
        print("❌ CRITICAL: No memories found with any search query!")
        print("   This suggests Elena's memory system is empty or not working.")
    else:
        print("✅ Memories exist - investigating content patterns...")
        
        # Try to get a broader sample
        print("\n=== BROAD MEMORY SAMPLE ===")
        try:
            broad_memories = await memory_manager.retrieve_relevant_memories(
                user_id="user_test",
                query="anything message content",
                limit=20
            )
            
            if broad_memories:
                print(f"Retrieved {len(broad_memories)} memories for pattern analysis:")
                
                user_msgs = []
                bot_msgs = []
                
                for memory in broad_memories:
                    role = memory.get("metadata", {}).get("role", "unknown")
                    content = memory.get("content", "")
                    
                    if role == "user":
                        user_msgs.append(content)
                    elif role == "bot":
                        bot_msgs.append(content)
                
                print(f"\nUser messages: {len(user_msgs)}")
                print(f"Bot messages: {len(bot_msgs)}")
                
                if user_msgs:
                    print(f"\nSample user messages:")
                    for i, msg in enumerate(user_msgs[:5], 1):
                        print(f"  {i}. '{msg[:100]}{'...' if len(msg) > 100 else ''}'")
                
                if bot_msgs:
                    print(f"\nSample bot messages:")
                    for i, msg in enumerate(bot_msgs[:5], 1):
                        print(f"  {i}. '{msg[:100]}{'...' if len(msg) > 100 else ''}'")
                
                # Check for patterns
                meta_patterns = ["what did we talk", "what are the main topics", "conversation history"]
                meta_count = sum(1 for msg in user_msgs if any(pattern in msg.lower() for pattern in meta_patterns))
                
                marine_patterns = ["marine", "ocean", "fish", "coral", "biology", "research"]
                marine_count = sum(1 for msg in user_msgs + bot_msgs if any(pattern in msg.lower() for pattern in marine_patterns))
                
                print(f"\n🔍 PATTERN ANALYSIS:")
                print(f"   Meta-conversation messages: {meta_count}")
                print(f"   Marine biology messages: {marine_count}")
                print(f"   Total messages analyzed: {len(user_msgs + bot_msgs)}")
                
                if meta_count > marine_count:
                    print("   ⚠️  ROOT CAUSE IDENTIFIED: Users only ask about memory, no real conversations!")
                elif marine_count > 0:
                    print("   ✅ Marine biology content exists - memory integration issue")
                else:
                    print("   ❓ Neither meta nor marine content - investigating further...")
            
        except Exception as e:
            print(f"❌ Broad search failed: {e}")
    
    print("\n=== NEXT STEPS ===")
    if total_memories_found == 0:
        print("1. Check if Elena bot is actually running and storing conversations")
        print("2. Verify Qdrant connection and collection setup")
        print("3. Test memory storage with a real conversation")
    else:
        print("1. Identify why users only ask meta-questions instead of real topics")
        print("2. Check if Elena's character prompts encourage marine biology discussions")
        print("3. Consider adding sample conversation starters about marine biology")

if __name__ == "__main__":
    asyncio.run(investigate_conversation_source())

if __name__ == "__main__":
    asyncio.run(check_elena_recent_activity())