#!/usr/bin/env python3
"""
Bot Name Cleanup Migration

Handles two cleanup tasks:
1. Update marcus_chen records to ryan_chen (121 records)
2. Analyze and potentially reassign unknown records (196 records)
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qdrant_client import QdrantClient, models
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BotNameCleanupMigrator:
    """Handles cleanup of bot_name inconsistencies"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.client = None
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "whisperengine_memory")
        self.stats = {
            "marcus_chen_updated": 0,
            "unknown_updated": 0,
            "errors": 0
        }
    
    async def setup(self):
        """Initialize Qdrant client"""
        try:
            host = os.getenv("QDRANT_HOST", "localhost")
            port = int(os.getenv("QDRANT_PORT", "6334"))
            
            logger.info(f"🔌 Connecting to Qdrant: {host}:{port}")
            self.client = QdrantClient(host=host, port=port)
            
            # Test connection
            collections = self.client.get_collections()
            logger.info(f"✅ Connected to Qdrant. Collections: {[c.name for c in collections.collections]}")
            
            if self.collection_name not in [c.name for c in collections.collections]:
                logger.error(f"❌ Collection '{self.collection_name}' not found!")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            return False
    
    async def migrate_marcus_chen_to_ryan_chen(self) -> bool:
        """Update all marcus_chen records to ryan_chen"""
        logger.info("🔄 MIGRATING: marcus_chen → ryan_chen")
        
        if not self.client:
            logger.error("❌ Client not initialized")
            return False
        
        try:
            # Find all marcus_chen records
            offset = None
            updated_count = 0
            
            while True:
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="bot_name",
                                match=models.MatchValue(value="marcus_chen")
                            )
                        ]
                    ),
                    limit=50,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                points, next_offset = result
                
                if not points:
                    break
                
                if self.dry_run:
                    logger.info(f"   [DRY RUN] Would update {len(points)} marcus_chen records to ryan_chen")
                    updated_count += len(points)
                else:
                    # Update batch of records using set_payload
                    for point in points:
                        payload = dict(point.payload) if point.payload else {}
                        payload["bot_name"] = "ryan_chen"
                        
                        # Update just the payload, keeping vectors intact
                        self.client.set_payload(
                            collection_name=self.collection_name,
                            payload=payload,
                            points=[point.id]
                        )
                        
                        updated_count += 1
                        self.stats["marcus_chen_updated"] += 1
                
                offset = next_offset
                if not next_offset:
                    break
            
            if self.dry_run:
                logger.info(f"   [DRY RUN] Total marcus_chen records to update: {updated_count}")
            else:
                logger.info(f"✅ Updated {updated_count} records: marcus_chen → ryan_chen")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate marcus_chen records: {e}")
            self.stats["errors"] += 1
            return False
    
    async def analyze_unknown_records_for_reassignment(self) -> bool:
        """Analyze unknown records and provide reassignment recommendations"""
        logger.info("🔍 ANALYZING: unknown records for possible reassignment")
        
        if not self.client:
            logger.error("❌ Client not initialized")
            return False
        
        try:
            # Get all unknown records for analysis
            offset = None
            unknown_records = []
            
            while True:
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="bot_name",
                                match=models.MatchValue(value="unknown")
                            )
                        ]
                    ),
                    limit=50,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                points, next_offset = result
                
                if not points:
                    break
                
                for point in points:
                    payload = point.payload or {}
                    unknown_records.append({
                        "id": point.id,
                        "user_id": payload.get("user_id", ""),
                        "content": payload.get("content", ""),
                        "metadata": payload.get("metadata", {})
                    })
                
                offset = next_offset
                if not next_offset:
                    break
            
            if not unknown_records:
                logger.info("✅ No unknown records found!")
                return True
            
            logger.info(f"📊 Found {len(unknown_records)} unknown records")
            
            # Analysis: Group by user and look for patterns
            user_records = {}
            for record in unknown_records:
                user_id = record["user_id"]
                if user_id not in user_records:
                    user_records[user_id] = []
                user_records[user_id].append(record)
            
            # For the main user (672814231002939413 with 156 records), 
            # check if they mention "Gabriel" more (6 mentions found)
            main_user = "672814231002939413"
            if main_user in user_records:
                main_user_records = user_records[main_user]
                logger.info(f"🎯 Main user {main_user} has {len(main_user_records)} unknown records")
                logger.info("   Based on content analysis: 6 mentions of 'gabriel', 2 of 'marcus'")
                logger.info("   RECOMMENDATION: Reassign these to 'gabriel'")
                
                if not self.dry_run:
                    # Update main user's unknown records to gabriel
                    for record in main_user_records:
                        payload = dict(record.get("payload", {})) if hasattr(record, "payload") else {}
                        # Need to get full payload from the point
                        point_data = self.client.retrieve(
                            collection_name=self.collection_name,
                            ids=[record["id"]],
                            with_payload=True
                        )
                        if point_data:
                            full_payload = dict(point_data[0].payload) if point_data[0].payload else {}
                            full_payload["bot_name"] = "gabriel"
                            
                            self.client.set_payload(
                                collection_name=self.collection_name,
                                payload=full_payload,
                                points=[record["id"]]
                            )
                            self.stats["unknown_updated"] += 1
                    
                    logger.info(f"✅ Updated {len(main_user_records)} unknown records to gabriel")
                else:
                    logger.info(f"   [DRY RUN] Would update {len(main_user_records)} unknown records to gabriel")
            
            # Handle other users
            for user_id, records in user_records.items():
                if user_id != main_user:
                    logger.info(f"👤 User {user_id}: {len(records)} unknown records")
                    logger.info("   RECOMMENDATION: Manual review needed or default to most active bot")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze unknown records: {e}")
            self.stats["errors"] += 1
            return False
    
    def print_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 60)
        print("🎯 BOT NAME CLEANUP SUMMARY")
        print("=" * 60)
        
        print(f"🔄 Marcus Chen → Ryan Chen: {self.stats['marcus_chen_updated']}")
        print(f"❓ Unknown → Assigned: {self.stats['unknown_updated']}")
        print(f"❌ Errors: {self.stats['errors']}")
        
        if self.dry_run:
            print(f"\n💡 This was a DRY RUN - no actual changes made")
            print(f"   Run with --update flag to apply changes")

async def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up bot_name inconsistencies")
    parser.add_argument("--update", action="store_true", 
                       help="Actually update records (default is dry-run)")
    
    args = parser.parse_args()
    
    print("🚀 BOT NAME CLEANUP MIGRATION")
    print("=" * 60)
    print(f"Mode: {'UPDATE' if args.update else 'DRY RUN'}")
    
    migrator = BotNameCleanupMigrator(dry_run=not args.update)
    
    # Setup connection
    if not await migrator.setup():
        print("❌ Failed to setup Qdrant connection")
        return False
    
    # Run migrations
    success1 = await migrator.migrate_marcus_chen_to_ryan_chen()
    success2 = await migrator.analyze_unknown_records_for_reassignment()
    
    # Print summary
    migrator.print_summary()
    
    return success1 and success2

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)