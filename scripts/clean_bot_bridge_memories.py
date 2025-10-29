#!/usr/bin/env python3
"""
Clean Contaminated Bot-Bridge Memories

Deletes all bot-bridge conversation memories between two specified bots.
This is needed when the bot bridge script had reversed identities, causing
memory contamination where each bot stored messages with wrong user_id mappings.

Usage:
    python scripts/clean_bot_bridge_memories.py dotty nottaylor
    python scripts/clean_bot_bridge_memories.py --dry-run dotty nottaylor
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Bot collection mapping
BOT_COLLECTIONS = {
    "elena": "whisperengine_memory_elena",
    "marcus": "whisperengine_memory_marcus",
    "ryan": "whisperengine_memory_ryan",
    "dream": "whisperengine_memory_dream",
    "gabriel": "whisperengine_memory_gabriel",
    "sophia": "whisperengine_memory_sophia",
    "jake": "whisperengine_memory_jake",
    "dotty": "whisperengine_memory_dotty",
    "aetheris": "whisperengine_memory_aetheris",
    "nottaylor": "whisperengine_memory_nottaylor",
    "assistant": "whisperengine_memory_assistant",
    "aethys": "whisperengine_memory_aethys",
}


async def count_memories(client: QdrantClient, collection_name: str, user_id: str) -> int:
    """Count memories for a specific user_id in a collection"""
    try:
        # Just filter by user_id - don't filter by platform since it might not be stored
        result = client.count(
            collection_name=collection_name,
            count_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
        )
        return result.count
    except Exception as e:
        print(f"⚠️  Error counting memories in {collection_name}: {e}")
        return 0


async def delete_memories(client: QdrantClient, collection_name: str, user_id: str, dry_run: bool = False) -> int:
    """Delete all bot-bridge memories for a specific user_id in a collection"""
    try:
        # First, count what we're about to delete
        count = await count_memories(client, collection_name, user_id)
        
        if count == 0:
            return 0
        
        if dry_run:
            print(f"   [DRY RUN] Would delete {count} memories from {collection_name} with user_id='{user_id}'")
            return count
        
        # Actually delete - just filter by user_id (bot-to-bot conversations)
        client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
        )
        
        print(f"   ✅ Deleted {count} memories from {collection_name} with user_id='{user_id}'")
        return count
        
    except Exception as e:
        print(f"   ❌ Error deleting from {collection_name}: {e}")
        return 0


async def clean_bot_bridge_memories(bot1_name: str, bot2_name: str, dry_run: bool = False):
    """
    Clean contaminated bot-bridge memories between two bots
    
    Args:
        bot1_name: First bot name (e.g., 'dotty')
        bot2_name: Second bot name (e.g., 'nottaylor')
        dry_run: If True, only report what would be deleted without actually deleting
    """
    # Validate bot names
    if bot1_name not in BOT_COLLECTIONS:
        print(f"❌ Unknown bot: {bot1_name}")
        print(f"Available bots: {', '.join(BOT_COLLECTIONS.keys())}")
        return
    
    if bot2_name not in BOT_COLLECTIONS:
        print(f"❌ Unknown bot: {bot2_name}")
        print(f"Available bots: {', '.join(BOT_COLLECTIONS.keys())}")
        return
    
    # Get collection names
    bot1_collection = BOT_COLLECTIONS[bot1_name]
    bot2_collection = BOT_COLLECTIONS[bot2_name]
    
    # Connect to Qdrant
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6334"))
    
    print(f"🔗 Connecting to Qdrant at {qdrant_host}:{qdrant_port}")
    client = QdrantClient(host=qdrant_host, port=qdrant_port)
    
    mode = "DRY RUN" if dry_run else "DELETION"
    print(f"\n🧹 [{mode}] Cleaning bot-bridge memories between '{bot1_name}' and '{bot2_name}'")
    print(f"=" * 80)
    
    total_deleted = 0
    
    # Delete memories from bot1's collection where user_id = bot2_name
    print(f"\n📦 Collection: {bot1_collection}")
    count = await delete_memories(client, bot1_collection, bot2_name, dry_run)
    total_deleted += count
    
    # Delete memories from bot2's collection where user_id = bot1_name
    print(f"\n📦 Collection: {bot2_collection}")
    count = await delete_memories(client, bot2_collection, bot1_name, dry_run)
    total_deleted += count
    
    print(f"\n" + "=" * 80)
    if dry_run:
        print(f"✨ [DRY RUN] Would delete {total_deleted} total contaminated memories")
        print(f"\n💡 Run without --dry-run to actually delete these memories")
    else:
        print(f"✨ Deleted {total_deleted} total contaminated memories")
        print(f"✅ Bot-bridge memories cleaned successfully!")
        print(f"\n💡 You can now run fresh conversations between {bot1_name} and {bot2_name}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean contaminated bot-bridge memories between two bots"
    )
    parser.add_argument(
        "bot1",
        help="First bot name (e.g., dotty)"
    )
    parser.add_argument(
        "bot2",
        help="Second bot name (e.g., nottaylor)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    args = parser.parse_args()
    
    # Run the cleanup
    asyncio.run(clean_bot_bridge_memories(args.bot1, args.bot2, args.dry_run))


if __name__ == "__main__":
    main()
