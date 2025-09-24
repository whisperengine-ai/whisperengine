#!/usr/bin/env python3
"""
Debug Elena's Empty Memory Issue

Previous investigation found Elena has stored memories, but searches return 0 results.
This suggests a user_id filtering issue - Elena's memories might be stored under 
specific user IDs but our search with test user IDs finds nothing.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.memory.vector_memory_system import VectorMemoryManager

async def debug_elena_empty_memory():
    """Debug why Elena's memory searches return 0 results"""
    print("🔍 DEBUGGING: Elena's Empty Memory Search Results")
    
    # Initialize memory manager directly
    os.environ.setdefault("QDRANT_COLLECTION_NAME", "whisperengine_memory")
    os.environ.setdefault("BOT_NAME", "elena")
    
    try:
        memory_manager = VectorMemoryManager()
        
        print("\n=== DIRECT QDRANT INSPECTION ===")
        
        # Try to get any memories at all from the collection
        print("Attempting direct vector store access...")
        
        # Access the vector store directly
        vector_store = memory_manager.vector_store
        
        # Check collection status
        try:
            # Try a very broad search with minimal filtering
            print("Searching with broad parameters...")
            
            # Use the vector store's search function directly
            results = await vector_store.search_memories(
                query="conversation",
                user_id="*",  # Wildcard user filtering
                memory_types=None,  # No memory type filtering  
                top_k=20,
                min_score=0.0  # Accept any score
            )
            
            print(f"Found {len(results)} total memories in collection")
            
            if results:
                print("\n=== SAMPLE MEMORIES FROM COLLECTION ===")
                for i, result in enumerate(results[:5], 1):
                    content = result.get("content", "")
                    user_id = result.get("user_id", "unknown")
                    metadata = result.get("metadata", {})
                    role = metadata.get("role", "unknown")
                    
                    print(f"{i}. User: {user_id}")
                    print(f"   Role: {role}")
                    print(f"   Content: '{content[:100]}{'...' if len(content) > 100 else ''}'")
                    print(f"   Metadata: {metadata}")
                    print()
                
                # Get unique user IDs
                user_ids = set()
                for result in results:
                    user_ids.add(result.get("user_id", "unknown"))
                
                print(f"=== USER IDS IN COLLECTION ===")
                print(f"Found {len(user_ids)} unique users:")
                for user_id in sorted(user_ids):
                    print(f"  - {user_id}")
                
                # Test search with actual user ID
                if user_ids:
                    real_user_id = next(iter(user_ids))
                    print(f"\n=== TESTING SEARCH WITH REAL USER ID: {real_user_id} ===")
                    
                    user_memories = await memory_manager.retrieve_relevant_memories(
                        user_id=real_user_id,
                        query="conversation",
                        limit=10
                    )
                    
                    print(f"Found {len(user_memories)} memories for user {real_user_id}")
                    
                    if user_memories:
                        print("✅ SUCCESS: Memory search works with correct user ID")
                        for i, memory in enumerate(user_memories[:3], 1):
                            content = memory.get("content", "")
                            role = memory.get("metadata", {}).get("role", "unknown")
                            print(f"   {i}. [{role}] '{content[:80]}{'...' if len(content) > 80 else ''}'")
                    else:
                        print("❌ STILL EMPTY: Even with correct user ID")
            else:
                print("❌ COLLECTION IS COMPLETELY EMPTY")
                print("This means Elena has never stored any conversations.")
                
        except Exception as search_error:
            print(f"❌ Direct search failed: {search_error}")
            import traceback
            traceback.print_exc()
        
        print("\n=== COLLECTION STATISTICS ===")
        try:
            # Get collection info
            client = vector_store.client
            collection_info = client.get_collection("whisperengine_memory")
            print(f"Collection exists: {collection_info.config.status}")
            print(f"Vector count: {collection_info.points_count}")
            print(f"Vector size: {collection_info.config.params.vectors.size}")
            
            if collection_info.points_count == 0:
                print("🔍 ROOT CAUSE: Collection has 0 vectors - Elena never stored memories!")
                print("\nPossible causes:")
                print("1. Elena bot is not running")
                print("2. Memory storage is failing silently")
                print("3. No real conversations have happened")
                print("4. Storage code is not being called")
            else:
                print(f"✅ Collection has {collection_info.points_count} vectors")
                print("🔍 Issue is with search/filtering, not storage")
                
        except Exception as info_error:
            print(f"❌ Could not get collection info: {info_error}")
    
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_elena_empty_memory())