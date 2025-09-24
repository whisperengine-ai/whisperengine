#!/usr/bin/env python3
"""
Universal Identity Migration Script

Migrates existing Discord memories to Universal Identity system while preserving
all conversation history and user relationships.

This script:
1. Identifies all unique Discord user IDs in existing memories
2. Creates Universal Identity records for each Discord user
3. Updates all memory records to use universal IDs instead of Discord IDs
4. Maintains complete conversation history and relationships

Usage:
    python scripts/migrate_discord_to_universal_identity.py [--dry-run] [--force]
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import asyncpg
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install asyncpg qdrant-client")
    sys.exit(1)

# Import WhisperEngine modules
try:
    from src.identity.universal_identity import (
        create_identity_manager, 
        PlatformIdentity, 
        ChatPlatform,
        UniversalUser
    )
    from src.utils.postgresql_user_db import PostgreSQLUserDB
    from dotenv import load_dotenv
except ImportError as e:
    print(f"WhisperEngine modules not found: {e}")
    print("Make sure you're running from the WhisperEngine root directory")
    sys.exit(1)

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class DiscordToUniversalMigration:
    """Migrates Discord memories to Universal Identity system"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.postgres_pool = None
        self.qdrant_client = None
        self.identity_manager = None
        
        # Migration tracking
        self.discord_to_universal_mapping: Dict[str, str] = {}
        self.total_memories_found = 0
        self.memories_updated = 0
        self.errors = 0
        
    async def initialize(self):
        """Initialize database connections"""
        logger.info("Initializing database connections...")
        
        # Initialize PostgreSQL
        try:
            postgres_db = PostgreSQLUserDB()
            await postgres_db.initialize()
            self.postgres_pool = postgres_db.pool
            logger.info("✅ PostgreSQL connection established")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
        
        # Initialize Qdrant
        try:
            qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
            qdrant_port = int(os.getenv('QDRANT_PORT', '6334'))
            self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
            logger.info(f"✅ Qdrant connection established at {qdrant_host}:{qdrant_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
            
        # Initialize Universal Identity Manager
        self.identity_manager = create_identity_manager(self.postgres_pool)
        logger.info("✅ Universal Identity Manager initialized")
        
        # Create Universal Identity tables if needed
        await self._ensure_universal_identity_tables()
    
    async def _ensure_universal_identity_tables(self):
        """Ensure Universal Identity tables exist"""
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS universal_users (
                        universal_id VARCHAR(255) PRIMARY KEY,
                        primary_username VARCHAR(255) NOT NULL,
                        display_name VARCHAR(255),
                        email VARCHAR(255),
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        preferences TEXT DEFAULT '{}',
                        privacy_settings TEXT DEFAULT '{}'
                    );

                    CREATE TABLE IF NOT EXISTS platform_identities (
                        id SERIAL PRIMARY KEY,
                        universal_id VARCHAR(255) NOT NULL REFERENCES universal_users(universal_id) ON DELETE CASCADE,
                        platform VARCHAR(50) NOT NULL,
                        platform_user_id VARCHAR(255) NOT NULL,
                        username VARCHAR(255) NOT NULL,
                        display_name VARCHAR(255),
                        email VARCHAR(255),
                        verified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(platform, platform_user_id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_platform_identities_universal_id ON platform_identities(universal_id);
                    CREATE INDEX IF NOT EXISTS idx_platform_identities_platform_user ON platform_identities(platform, platform_user_id);
                """)
                logger.info("✅ Universal Identity tables verified/created")
        except Exception as e:
            logger.error(f"Failed to create Universal Identity tables: {e}")
            raise

    async def discover_discord_users(self) -> Set[str]:
        """Discover all unique Discord user IDs in memory system"""
        logger.info("Discovering Discord user IDs in memory system...")
        
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'whisperengine_memory')
        discord_user_ids = set()
        
        try:
            # Scroll through all points to find unique user IDs
            scroll_result = self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=10000,  # Process in large batches
                with_payload=['user_id']
            )
            
            points = scroll_result[0]
            next_page_offset = scroll_result[1]
            
            # Process first batch
            for point in points:
                user_id = point.payload.get('user_id')
                if user_id and user_id.isdigit() and len(user_id) > 15:  # Discord ID pattern
                    discord_user_ids.add(user_id)
            
            # Process remaining batches
            while next_page_offset:
                scroll_result = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    offset=next_page_offset,
                    limit=10000,
                    with_payload=['user_id']
                )
                
                points = scroll_result[0]
                next_page_offset = scroll_result[1]
                
                for point in points:
                    user_id = point.payload.get('user_id')
                    if user_id and user_id.isdigit() and len(user_id) > 15:  # Discord ID pattern
                        discord_user_ids.add(user_id)
            
            logger.info(f"📊 Found {len(discord_user_ids)} unique Discord user IDs")
            logger.info(f"🔍 Sample Discord IDs: {list(discord_user_ids)[:5]}")
            return discord_user_ids
            
        except Exception as e:
            logger.error(f"Failed to discover Discord users: {e}")
            raise

    async def create_universal_identities(self, discord_user_ids: Set[str]) -> Dict[str, str]:
        """Create Universal Identity records for Discord users"""
        logger.info(f"Creating Universal Identity records for {len(discord_user_ids)} Discord users...")
        
        mapping = {}
        
        for discord_id in discord_user_ids:
            try:
                # Check if Universal Identity already exists
                existing_user = await self.identity_manager._load_user_by_platform(
                    ChatPlatform.DISCORD, discord_id
                )
                
                if existing_user:
                    mapping[discord_id] = existing_user.universal_id
                    logger.info(f"✅ Found existing universal ID for Discord {discord_id}: {existing_user.universal_id}")
                    continue
                
                if self.dry_run:
                    # Generate a mock universal ID for dry run
                    mock_universal_id = f"weu_mock_{discord_id[-8:]}"
                    mapping[discord_id] = mock_universal_id
                    logger.info(f"🔄 [DRY RUN] Would create universal ID for Discord {discord_id}: {mock_universal_id}")
                    continue
                
                # Create new Universal Identity
                universal_user = await self.identity_manager.get_or_create_discord_user(
                    discord_user_id=discord_id,
                    username=f"discord_user_{discord_id[-6:]}",  # Use last 6 digits as username
                    display_name=f"Discord User {discord_id[-4:]}"  # Use last 4 digits in display name
                )
                
                mapping[discord_id] = universal_user.universal_id
                logger.info(f"✅ Created universal ID for Discord {discord_id}: {universal_user.universal_id}")
                
            except Exception as e:
                logger.error(f"Failed to create universal identity for Discord {discord_id}: {e}")
                self.errors += 1
                continue
        
        logger.info(f"📋 Discord to Universal ID mapping complete: {len(mapping)} users")
        return mapping

    async def update_memory_records(self, mapping: Dict[str, str]):
        """Update memory records to use universal IDs"""
        logger.info(f"Updating memory records for {len(mapping)} users...")
        
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'whisperengine_memory')
        
        for discord_id, universal_id in mapping.items():
            try:
                logger.info(f"🔄 Updating memories for Discord {discord_id} → Universal {universal_id}")
                
                if self.dry_run:
                    # Count how many memories would be updated
                    count_result = self.qdrant_client.count(
                        collection_name=collection_name,
                        count_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="user_id",
                                    match=MatchValue(value=discord_id)
                                )
                            ]
                        )
                    )
                    count = count_result.count
                    logger.info(f"🔄 [DRY RUN] Would update {count} memories for user {discord_id}")
                    self.total_memories_found += count
                    continue
                
                # Get all points for this Discord user
                scroll_result = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=discord_id)
                            )
                        ]
                    ),
                    limit=10000,
                    with_payload=True
                )
                
                points = scroll_result[0]
                memories_to_update = []
                
                # Prepare updates
                for point in points:
                    # Update payload to use universal ID
                    updated_payload = point.payload.copy()
                    updated_payload['user_id'] = universal_id
                    updated_payload['migrated_from_discord'] = discord_id
                    updated_payload['migration_timestamp'] = datetime.now().isoformat()
                    
                    memories_to_update.append({
                        'id': point.id,
                        'payload': updated_payload,
                        'vector': point.vector
                    })
                
                # Batch update
                if memories_to_update:
                    from qdrant_client.models import PointStruct
                    
                    update_points = [
                        PointStruct(
                            id=mem['id'],
                            payload=mem['payload'],
                            vector=mem['vector']
                        )
                        for mem in memories_to_update
                    ]
                    
                    self.qdrant_client.upsert(
                        collection_name=collection_name,
                        points=update_points
                    )
                    
                    self.memories_updated += len(memories_to_update)
                    logger.info(f"✅ Updated {len(memories_to_update)} memories for user {discord_id}")
                
            except Exception as e:
                logger.error(f"Failed to update memories for Discord {discord_id}: {e}")
                self.errors += 1
                continue

    async def verify_migration(self, mapping: Dict[str, str]):
        """Verify migration completed successfully"""
        logger.info("🔍 Verifying migration results...")
        
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'whisperengine_memory')
        verification_errors = 0
        
        for discord_id, universal_id in mapping.items():
            try:
                # Check that no memories still use the old Discord ID
                discord_count = self.qdrant_client.count(
                    collection_name=collection_name,
                    count_filter=Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=discord_id)
                            )
                        ]
                    )
                ).count
                
                # Check that memories now use the universal ID
                universal_count = self.qdrant_client.count(
                    collection_name=collection_name,
                    count_filter=Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=universal_id)
                            )
                        ]
                    )
                ).count
                
                if discord_count > 0:
                    logger.error(f"❌ Found {discord_count} memories still using Discord ID {discord_id}")
                    verification_errors += 1
                else:
                    logger.info(f"✅ No memories found with old Discord ID {discord_id}")
                
                if universal_count > 0:
                    logger.info(f"✅ Found {universal_count} memories using Universal ID {universal_id}")
                else:
                    logger.warning(f"⚠️ No memories found with Universal ID {universal_id}")
                    
            except Exception as e:
                logger.error(f"Verification failed for {discord_id}: {e}")
                verification_errors += 1
        
        return verification_errors == 0

    async def run_migration(self):
        """Execute the full migration process"""
        logger.info("🚀 Starting Discord to Universal Identity migration...")
        
        try:
            # Step 1: Initialize connections
            await self.initialize()
            
            # Step 2: Discover Discord users
            discord_user_ids = await self.discover_discord_users()
            if not discord_user_ids:
                logger.info("✅ No Discord user IDs found - migration not needed")
                return True
            
            # Step 3: Create Universal Identity records
            self.discord_to_universal_mapping = await self.create_universal_identities(discord_user_ids)
            
            # Step 4: Update memory records
            await self.update_memory_records(self.discord_to_universal_mapping)
            
            # Step 5: Verify migration (skip for dry run)
            if not self.dry_run:
                migration_success = await self.verify_migration(self.discord_to_universal_mapping)
                if not migration_success:
                    logger.error("❌ Migration verification failed")
                    return False
            
            # Step 6: Report results
            self.print_migration_report()
            
            logger.info("✅ Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
        finally:
            # Cleanup connections
            if self.postgres_pool:
                await self.postgres_pool.close()
            if self.qdrant_client:
                self.qdrant_client.close()

    def print_migration_report(self):
        """Print detailed migration report"""
        logger.info("\n" + "="*60)
        logger.info("📊 MIGRATION REPORT")
        logger.info("="*60)
        logger.info(f"🎯 Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        logger.info(f"👥 Discord users found: {len(self.discord_to_universal_mapping)}")
        logger.info(f"📝 Memories processed: {self.total_memories_found if self.dry_run else self.memories_updated}")
        logger.info(f"❌ Errors encountered: {self.errors}")
        
        if self.discord_to_universal_mapping:
            logger.info("\n🔗 User ID Mappings:")
            for discord_id, universal_id in list(self.discord_to_universal_mapping.items())[:10]:
                logger.info(f"   Discord {discord_id} → Universal {universal_id}")
            if len(self.discord_to_universal_mapping) > 10:
                logger.info(f"   ... and {len(self.discord_to_universal_mapping) - 10} more")
        
        logger.info("="*60)
        
        if self.dry_run:
            logger.info("🔄 This was a DRY RUN - no changes were made")
            logger.info("💡 Run without --dry-run to execute the migration")
        else:
            logger.info("✅ Live migration completed!")
            logger.info("💡 Your Discord memories are now accessible via Universal Identity")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Migrate Discord memories to Universal Identity')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview migration without making changes')
    parser.add_argument('--force', action='store_true',
                       help='Force migration even if Universal Identity data exists')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("🔄 Running in DRY RUN mode - no changes will be made")
    
    migration = DiscordToUniversalMigration(dry_run=args.dry_run)
    success = await migration.run_migration()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())