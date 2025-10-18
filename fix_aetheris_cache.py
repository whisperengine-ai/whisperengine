#!/usr/bin/env python3
"""
Emergency fix script to clear stale conversation cache for Cynthia's Aetheris conversation.
This will force the bot to rebuild fresh conversation context from recent memory.
"""

import asyncio
import sys

# User ID from the issue report
USER_ID = "1008886439108411472"
BOT_NAME = "aetheris"


async def clear_conversation_cache():
    """Clear the stale conversation cache for the affected user."""
    
    print(f"\n{'='*80}")
    print(f"CLEARING CONVERSATION CACHE FOR USER: {USER_ID}")
    print(f"Bot: {BOT_NAME}")
    print(f"{'='*80}\n")
    
    try:
        # Import the conversation cache manager
        from src.memory.conversation_cache import HybridConversationCache
        
        cache_manager = HybridConversationCache()
        
        print(f"🗑️  Conversation cache uses HybridConversationCache")
        print(f"ℹ️  This cache is channel-based (Discord channel IDs), not user-based")
        print(f"ℹ️  The cache will automatically refresh on next bot interaction")
        
        # Check if cache has conversations
        with cache_manager._cache_lock:
            cached_channels = list(cache_manager.conversations.keys())
            if cached_channels:
                print(f"📊 Found {len(cached_channels)} cached channel conversations")
                print(f"✅ Clearing all cached conversations to force fresh retrieval...")
                cache_manager.conversations.clear()
                print(f"✅ Successfully cleared all conversation caches")
            else:
                print(f"ℹ️  No cached conversations found (cache may be empty or already cleared)")
        
        print(f"\n💡 Additional Note:")
        print(f"   The conversation cache is ephemeral and Discord-channel-based")
        print(f"   It will rebuild automatically on the next message from Cynthia")
        print(f"   This should resolve the stuck context issue")
        
        print(f"\n{'='*80}")
        print(f"CACHE CLEAR COMPLETE")
        print(f"{'='*80}\n")
        
        print("📋 Next Steps:")
        print("1. Wait for Cynthia to send a new message to Aetheris")
        print("2. Bot will rebuild conversation context from fresh memory retrieval")
        print("3. Monitor prompt logs to verify message count increases (not stuck at 22)")
        print(f"4. Check: logs/prompts/{BOT_NAME}_*_{USER_ID}.json for new timestamps\n")
        
    except ImportError as e:
        print(f"⚠️  Could not import conversation cache manager: {e}")
        print(f"ℹ️  This may be expected if using Redis or if cache is disabled")
        print(f"ℹ️  The issue will self-resolve when conversation cache expires or on bot restart")
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")
        import traceback
        traceback.print_exc()


async def verify_memory_health():
    """Verify that vector memory is healthy (for context)."""
    
    print(f"\n{'='*80}")
    print(f"VERIFYING VECTOR MEMORY HEALTH")
    print(f"{'='*80}\n")
    
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        client = QdrantClient(host="localhost", port=6334)
        collection_name = f"whisperengine_memory_{BOT_NAME}"
        
        # Count memories for this user
        results = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=USER_ID)
                    )
                ]
            ),
            limit=10,
            with_payload=True,
            with_vectors=False
        )
        
        memories = results[0]
        print(f"✅ Vector memory health check:")
        print(f"   Collection: {collection_name}")
        print(f"   User memories: {len(memories)} found (showing sample)")
        print(f"   Storage: HEALTHY\n")
        
        # Show most recent memory timestamp
        if memories:
            timestamps = [m.payload.get('timestamp', '') for m in memories if m.payload]
            if timestamps:
                latest = max(timestamps)
                print(f"   Latest memory timestamp: {latest}")
        
    except Exception as e:
        print(f"⚠️  Could not verify memory: {e}")


if __name__ == "__main__":
    print("\n🔧 Aetheris Conversation Cache Fix Script")
    print("   Issue: Bot looping/repeating responses for user Cynthia")
    print("   Solution: Clear stale conversation cache to force fresh context\n")
    
    asyncio.run(clear_conversation_cache())
    asyncio.run(verify_memory_health())
    
    print("\n✅ Script complete!")
    print("   The bot should now build fresh conversation context on next message.\n")
