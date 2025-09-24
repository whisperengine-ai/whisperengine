#!/usr/bin/env python3
"""
Debug Elena's Memory - Use Same Method as Earlier Success

Earlier debug found 10 memories, but now searches return 0.
Let's use the exact same approach that worked before.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.memory.vector_memory_system import VectorMemoryStore

async def debug_with_successful_method():
    """Use the same method that found 10 memories earlier"""
    print("🔍 DEBUGGING: Using Previously Successful Method")
    
    # Set environment like Elena bot
    os.environ.setdefault("QDRANT_COLLECTION_NAME", "whisperengine_memory")
    
    try:
        # Initialize VectorMemoryStore directly (like earlier script)
        memory_store = VectorMemoryStore()
        await memory_store.initialize()
        
        print("\n=== DIRECT COLLECTION ACCESS ===")
        
        # Get collection info
        collection_info = memory_store.client.get_collection("whisperengine_memory")
        print(f"Collection status: {collection_info.config.status}")
        print(f"Total points: {collection_info.points_count}")
        
        if collection_info.points_count == 0:
            print("❌ CRITICAL: Collection is empty - no memories stored!")
            return
        
        print(f"✅ Collection has {collection_info.points_count} memories")
        
        # Use the same search approach that worked before
        print("\n=== SEARCHING WITH SUCCESSFUL METHOD ===")
        
        # Search for any conversation content
        from qdrant_client import models
        
        # Search with minimal filtering
        results = memory_store.client.search(
            collection_name="whisperengine_memory",
            query_vector=models.NamedVector(name="content", vector=[0.0] * 384),  # Dummy vector
            limit=20,
            with_payload=True,
            score_threshold=0.0  # Accept all scores
        )
        
        print(f"Found {len(results)} memories with direct search")
        
        if results:
            print("\n=== ANALYZING FOUND MEMORIES ===")
            
            user_memories = {}
            for point in results:
                payload = point.payload
                if payload:
                    user_id = payload.get('user_id', 'unknown')
                    content = payload.get('content', '')
                    role = payload.get('metadata', {}).get('role', 'unknown')
                    bot_name = payload.get('bot_name', 'unknown')
                    
                    if user_id not in user_memories:
                        user_memories[user_id] = []
                    
                    user_memories[user_id].append({
                        'content': content,
                        'role': role,
                        'bot_name': bot_name,
                        'point_id': str(point.id)
                    })
            
            print(f"Found memories from {len(user_memories)} users:")
            
            for user_id, memories in user_memories.items():
                print(f"\n👤 User: {user_id}")
                print(f"   Memories: {len(memories)}")
                
                # Check which bot these memories belong to
                bot_names = set(m['bot_name'] for m in memories)
                print(f"   Bot(s): {', '.join(bot_names)}")
                
                # Show sample memories
                for i, memory in enumerate(memories[:3], 1):
                    role = memory['role']
                    content = memory['content']
                    print(f"   {i}. [{role}] '{content[:80]}{'...' if len(content) > 80 else ''}'")
            
            # Check if Elena's memories exist
            elena_memories = []
            for user_id, memories in user_memories.items():
                for memory in memories:
                    if memory['bot_name'] == 'elena':
                        elena_memories.append(memory)
            
            print(f"\n🧬 ELENA-SPECIFIC MEMORIES: {len(elena_memories)}")
            
            if elena_memories:
                print("Elena's memories found:")
                for i, memory in enumerate(elena_memories[:5], 1):
                    role = memory['role']
                    content = memory['content']
                    print(f"   {i}. [{role}] '{content[:100]}{'...' if len(content) > 100 else ''}'")
            else:
                print("❌ No memories specifically from Elena bot!")
                print("This explains why Elena can't find her own memories.")
                print("Memories in collection belong to other bots:")
                all_bots = set()
                for memories in user_memories.values():
                    for memory in memories:
                        all_bots.add(memory['bot_name'])
                print(f"   Bots in collection: {', '.join(all_bots)}")
        
        else:
            print("❌ No memories found even with direct search")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_with_successful_method())