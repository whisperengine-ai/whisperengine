#!/usr/bin/env python3
"""
Backfill latest_message_timestamp for existing facts.

PROBLEM:
- Old facts (before Oct 20, 2025) don't have latest_message_timestamp in context_metadata
- Enrichment worker falls back to created_at, causing re-processing of same conversations
- Wastes API calls and database queries (hundreds of unnecessary Qdrant scroll requests per cycle)

SOLUTION:
- For each fact without latest_message_timestamp:
  1. Find the user's messages in Qdrant for that bot
  2. Determine the latest message timestamp at the time the fact was created
  3. Update context_metadata with latest_message_timestamp + backfilled_at metadata

USAGE:
    # Test first (recommended)
    python scripts/backfill_fact_message_timestamps.py --dry-run
    
    # Execute backfill
    python scripts/backfill_fact_message_timestamps.py
    
    # Then restart enrichment worker
    docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart enrichment-worker

DEPLOYMENT:
    For any WhisperEngine instance with enrichment worker making excessive scroll requests:
    1. Run this script (--dry-run first to preview)
    2. Restart enrichment worker
    3. Monitor logs to verify fix (~90% reduction in processing)
    
    See: docs/maintenance/ENRICHMENT_BACKFILL_GUIDE.md for full deployment guide

SAFETY:
    - Idempotent (safe to run multiple times)
    - Dry-run mode for testing
    - No data deletion (only adds timestamps)
    - Continues on individual failures
"""

import asyncio
import asyncpg
import argparse
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range


# Qdrant connection
QDRANT_HOST = "localhost"
QDRANT_PORT = 6334

# PostgreSQL connection
DB_HOST = "localhost"
DB_PORT = 5433
DB_NAME = "whisperengine"
DB_USER = "whisperengine"
DB_PASSWORD = "postgres"

# Bot name to collection mapping
BOT_COLLECTIONS = {
    'elena': 'whisperengine_memory_elena_7d',
    'marcus': 'whisperengine_memory_marcus_7d',
    'gabriel': 'whisperengine_memory_gabriel_7d',
    'sophia': 'whisperengine_memory_sophia_7d',
    'jake': 'whisperengine_memory_jake_7d',
    'ryan': 'whisperengine_memory_ryan_7d',
    'dream': 'whisperengine_memory_dream_7d',
    'aethys': 'whisperengine_memory_aethys',
    'aetheris': 'whisperengine_memory_aetheris',
    'dotty': 'whisperengine_memory_dotty',
}


async def get_facts_missing_timestamp(conn: asyncpg.Connection) -> List[Dict]:
    """Get all facts that are missing latest_message_timestamp."""
    query = """
    SELECT 
        ufr.id,
        ufr.user_id,
        ufr.mentioned_by_character as bot_name,
        ufr.context_metadata,
        ufr.created_at
    FROM user_fact_relationships ufr
    WHERE 
        ufr.mentioned_by_character IS NOT NULL
        AND (
            ufr.context_metadata IS NULL 
            OR ufr.context_metadata->>'latest_message_timestamp' IS NULL
        )
    ORDER BY ufr.mentioned_by_character, ufr.user_id, ufr.created_at
    """
    
    rows = await conn.fetch(query)
    
    facts = []
    for row in rows:
        context_metadata = row['context_metadata']
        if isinstance(context_metadata, str):
            try:
                context_metadata = json.loads(context_metadata)
            except (json.JSONDecodeError, TypeError):
                context_metadata = {}
        elif not isinstance(context_metadata, dict):
            context_metadata = {}
        
        facts.append({
            'id': row['id'],
            'user_id': row['user_id'],
            'bot_name': row['bot_name'],
            'context_metadata': context_metadata,
            'created_at': row['created_at']
        })
    
    return facts


def get_latest_message_timestamp_from_qdrant(
    qdrant_client: QdrantClient,
    collection_name: str,
    user_id: str,
    before_timestamp: datetime
) -> Optional[datetime]:
    """
    Find the latest message timestamp in Qdrant for a user BEFORE a given timestamp.
    
    This represents "what was the latest message we could have seen when creating this fact?"
    """
    try:
        # Convert to Unix timestamp for Qdrant query
        before_unix = before_timestamp.timestamp()
        
        # Get all messages for this user before the fact creation time
        results, _ = qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key='user_id', match=MatchValue(value=user_id)),
                    FieldCondition(key='timestamp_unix', range=Range(lte=before_unix))
                ]
            ),
            limit=10000,  # Get all messages
            with_payload=True,
            with_vectors=False
        )
        
        if not results:
            return None
        
        # Find the maximum timestamp
        timestamps = []
        for point in results:
            if 'timestamp' in point.payload:
                ts_str = point.payload['timestamp']
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                # Make timezone-naive for consistency
                if ts.tzinfo is not None:
                    ts = ts.replace(tzinfo=None)
                timestamps.append(ts)
        
        if not timestamps:
            return None
        
        return max(timestamps)
    
    except Exception as e:
        print(f"Error querying Qdrant for user {user_id} in {collection_name}: {e}")
        return None


async def update_fact_timestamp(
    conn: asyncpg.Connection,
    fact_id: str,
    latest_message_timestamp: datetime,
    context_metadata: Dict,
    dry_run: bool = False
) -> bool:
    """Update a fact's context_metadata with latest_message_timestamp."""
    
    # Add the timestamp to context_metadata
    updated_metadata = context_metadata.copy()
    updated_metadata['latest_message_timestamp'] = latest_message_timestamp.isoformat()
    updated_metadata['backfilled_at'] = datetime.utcnow().isoformat()
    updated_metadata['backfill_reason'] = 'missing_timestamp_fix_oct2025'
    
    if dry_run:
        print(f"  [DRY RUN] Would update fact {fact_id} with timestamp {latest_message_timestamp}")
        return True
    
    try:
        await conn.execute("""
            UPDATE user_fact_relationships
            SET 
                context_metadata = $1,
                updated_at = NOW()
            WHERE id = $2
        """, json.dumps(updated_metadata), fact_id)
        return True
    except Exception as e:
        print(f"  ❌ Error updating fact {fact_id}: {e}")
        return False


async def backfill_timestamps(dry_run: bool = False, batch_size: int = 100):
    """Main backfill logic."""
    
    print("🔧 Starting fact timestamp backfill process...")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print()
    
    # Connect to PostgreSQL
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    # Connect to Qdrant
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    try:
        # Get facts missing timestamp
        print("📊 Fetching facts missing latest_message_timestamp...")
        facts = await get_facts_missing_timestamp(conn)
        print(f"Found {len(facts)} facts to process\n")
        
        if not facts:
            print("✅ No facts need updating!")
            return
        
        # Group by bot for better reporting
        by_bot = {}
        for fact in facts:
            bot_name = fact['bot_name']
            if bot_name not in by_bot:
                by_bot[bot_name] = []
            by_bot[bot_name].append(fact)
        
        print("📋 Facts by bot:")
        for bot_name, bot_facts in sorted(by_bot.items()):
            print(f"  {bot_name}: {len(bot_facts)} facts")
        print()
        
        # Process each bot
        total_updated = 0
        total_failed = 0
        total_no_messages = 0
        
        for bot_name, bot_facts in sorted(by_bot.items()):
            print(f"🤖 Processing {bot_name} ({len(bot_facts)} facts)...")
            
            collection_name = BOT_COLLECTIONS.get(bot_name)
            if not collection_name:
                print(f"  ⚠️  Unknown bot: {bot_name}, skipping")
                continue
            
            # Check if collection exists
            try:
                collections = qdrant_client.get_collections().collections
                if not any(c.name == collection_name for c in collections):
                    print(f"  ⚠️  Collection {collection_name} not found, skipping")
                    continue
            except Exception as e:
                print(f"  ❌ Error checking collection: {e}")
                continue
            
            # Process facts in batches
            bot_updated = 0
            bot_failed = 0
            bot_no_messages = 0
            
            for i, fact in enumerate(bot_facts, 1):
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(bot_facts)}...")
                
                # Get latest message timestamp from Qdrant
                latest_msg_ts = get_latest_message_timestamp_from_qdrant(
                    qdrant_client,
                    collection_name,
                    fact['user_id'],
                    fact['created_at']
                )
                
                if latest_msg_ts is None:
                    # No messages found - user might have been deleted or data cleaned up
                    bot_no_messages += 1
                    continue
                
                # Update the fact
                success = await update_fact_timestamp(
                    conn,
                    fact['id'],
                    latest_msg_ts,
                    fact['context_metadata'],
                    dry_run
                )
                
                if success:
                    bot_updated += 1
                else:
                    bot_failed += 1
            
            print(f"  ✅ Updated: {bot_updated}, ❌ Failed: {bot_failed}, ⚠️  No messages: {bot_no_messages}")
            print()
            
            total_updated += bot_updated
            total_failed += bot_failed
            total_no_messages += bot_no_messages
        
        # Final summary
        print("=" * 60)
        print("📊 BACKFILL SUMMARY")
        print("=" * 60)
        print(f"Total facts processed: {len(facts)}")
        print(f"✅ Successfully updated: {total_updated}")
        print(f"❌ Failed: {total_failed}")
        print(f"⚠️  No messages found: {total_no_messages}")
        print()
        
        if dry_run:
            print("🔍 This was a DRY RUN - no changes were made")
            print("Run without --dry-run to apply changes")
        else:
            print("✅ Backfill complete!")
            print()
            print("Next steps:")
            print("1. Restart enrichment worker: docker compose restart enrichment-worker")
            print("2. Monitor logs to verify no re-processing of old conversations")
    
    finally:
        await conn.close()
        qdrant_client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Backfill latest_message_timestamp for facts missing this field"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of facts to process in each batch (default: 100)'
    )
    
    args = parser.parse_args()
    
    asyncio.run(backfill_timestamps(
        dry_run=args.dry_run,
        batch_size=args.batch_size
    ))


if __name__ == '__main__':
    main()
