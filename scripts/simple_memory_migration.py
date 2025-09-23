#!/usr/bin/env python3
"""
Simple Memory Migration Script

A lightweight script to migrate existing Discord user IDs to Universal IDs in memory system.
This version focuses on the core migration without complex verification.

Usage:
    python scripts/simple_memory_migration.py [--dry-run]
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Set
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct
except ImportError as e:
    print(f"Missing qdrant-client: {e}")
    print("Install with: pip install qdrant-client")
    sys.exit(1)

try:
    from src.identity.universal_identity import create_identity_manager, ChatPlatform
    from src.utils.postgresql_user_db import PostgreSQLUserDB
    from dotenv import load_dotenv
except ImportError as e:
    print(f"WhisperEngine modules not found: {e}")
    sys.exit(1)

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main migration process"""
    parser = argparse.ArgumentParser(description='Migrate Discord memories to Universal Identity')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying them')
    args = parser.parse_args()
    
    logger.info("🚀 Starting Discord to Universal ID migration...")
    if args.dry_run:
        logger.info("🔄 DRY RUN MODE - No changes will be made")
    
    # Initialize connections
    logger.info("Initializing connections...")
    
    # PostgreSQL
    postgres_db = PostgreSQLUserDB()
    await postgres_db.initialize()
    postgres_pool = postgres_db.pool
    
    # Qdrant
    qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
    qdrant_port = int(os.getenv('QDRANT_PORT', '6334'))
    qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
    collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'whisperengine_memory')
    
    # Identity Manager
    identity_manager = create_identity_manager(postgres_pool)
    
    logger.info("✅ Connections established")
    
    # Discover Discord user IDs
    logger.info("🔍 Discovering Discord user IDs...")
    
    discord_user_ids = set()
    scroll_result = qdrant_client.scroll(
        collection_name=collection_name,
        limit=10000,
        with_payload=['user_id']
    )
    
    points = scroll_result[0]
    for point in points:
        user_id = point.payload.get('user_id', '')
        if user_id and user_id.isdigit() and len(user_id) > 15:  # Discord ID pattern
            discord_user_ids.add(user_id)
    
    logger.info(f"📊 Found {len(discord_user_ids)} unique Discord user IDs")
    if discord_user_ids:
        logger.info(f"🔍 Sample IDs: {list(discord_user_ids)[:3]}")
    
    if not discord_user_ids:
        logger.info("✅ No Discord user IDs found - migration not needed")
        return
    
    # Create Universal Identities
    logger.info("🔄 Creating Universal Identity mappings...")
    
    mapping = {}
    for discord_id in discord_user_ids:
        try:
            # Check if already exists
            existing_user = await identity_manager._load_user_by_platform(
                ChatPlatform.DISCORD, discord_id
            )
            
            if existing_user:
                mapping[discord_id] = existing_user.universal_id
                logger.info(f"✅ Found existing: {discord_id} → {existing_user.universal_id}")
                continue
            
            if args.dry_run:
                mock_id = f"weu_mock_{discord_id[-8:]}"
                mapping[discord_id] = mock_id
                logger.info(f"🔄 [DRY RUN] Would create: {discord_id} → {mock_id}")
                continue
            
            # Create new Universal Identity
            universal_user = await identity_manager.get_or_create_discord_user(
                discord_user_id=discord_id,
                username=f"user_{discord_id[-6:]}",
                display_name=f"Discord User {discord_id[-4:]}"
            )
            
            mapping[discord_id] = universal_user.universal_id
            logger.info(f"✅ Created: {discord_id} → {universal_user.universal_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {discord_id}: {e}")
            continue
    
    logger.info(f"🗺️  Created {len(mapping)} ID mappings")
    
    # Update memories
    logger.info("📝 Updating memory records...")
    
    total_updated = 0
    for discord_id, universal_id in mapping.items():
        try:
            if args.dry_run:
                # Count memories for this user
                count_result = qdrant_client.count(
                    collection_name=collection_name,
                    count_filter=Filter(
                        must=[FieldCondition(key="user_id", match=MatchValue(value=discord_id))]
                    )
                )
                logger.info(f"🔄 [DRY RUN] Would update {count_result.count} memories for {discord_id}")
                total_updated += count_result.count
                continue
            
            # Get all memories for this Discord user
            scroll_result = qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=discord_id))]
                ),
                limit=10000,
                with_payload=True
            )
            
            points = scroll_result[0]
            if not points:
                continue
            
            # Update all points
            updated_points = []
            for point in points:
                updated_payload = point.payload.copy()
                updated_payload['user_id'] = universal_id
                updated_payload['migrated_from_discord'] = discord_id
                
                updated_points.append(PointStruct(
                    id=point.id,
                    payload=updated_payload,
                    vector=point.vector
                ))
            
            # Batch update
            if updated_points:
                qdrant_client.upsert(
                    collection_name=collection_name,
                    points=updated_points
                )
                
                total_updated += len(updated_points)
                logger.info(f"✅ Updated {len(updated_points)} memories: {discord_id} → {universal_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update memories for {discord_id}: {e}")
            continue
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 MIGRATION SUMMARY")
    logger.info("="*60)
    logger.info(f"🎯 Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    logger.info(f"👥 Discord users: {len(discord_user_ids)}")
    logger.info(f"🔗 ID mappings: {len(mapping)}")
    logger.info(f"📝 Memories updated: {total_updated}")
    
    if mapping:
        logger.info("\n🔗 Sample mappings:")
        for discord_id, universal_id in list(mapping.items())[:5]:
            logger.info(f"   {discord_id} → {universal_id}")
    
    logger.info("="*60)
    
    if args.dry_run:
        logger.info("💡 Run without --dry-run to execute the migration")
    else:
        logger.info("✅ Migration completed!")
        logger.info("💡 Your Discord memories are now accessible via Universal Identity")
    
    # Cleanup
    await postgres_pool.close()
    qdrant_client.close()


if __name__ == "__main__":
    asyncio.run(main())