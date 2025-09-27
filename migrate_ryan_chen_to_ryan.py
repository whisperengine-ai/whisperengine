#!/usr/bin/env python3
"""
Ryan Chen to Ryan Migration

Updates ryan_chen records to ryan in the vector store.
"""

import asyncio
import os
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qdrant_client import QdrantClient, models
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RyanChenToRyanMigrator:
    """Handles migration of ryan_chen to ryan"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.client = None
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "whisperengine_memory")
        self.stats = {
            "ryan_chen_updated": 0,
            "errors": 0
        }
    
    async def setup(self):
        """Initialize Qdrant client"""
        try:
            host = os.getenv("QDRANT_HOST", "localhost")
            port = int(os.getenv("QDRANT_PORT", "6334"))
            
            logger.info("🔌 Connecting to Qdrant: %s:%s", host, port)
            self.client = QdrantClient(host=host, port=port)
            
            # Test connection
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            logger.info("✅ Connected to Qdrant. Collections: %s", collection_names)
            
            if self.collection_name not in collection_names:
                logger.error("❌ Collection '%s' not found!", self.collection_name)
                return False
                
            return True
            
        except Exception as e:
            logger.error("❌ Failed to connect to Qdrant: %s", e)
            return False
    
    async def migrate_ryan_chen_to_ryan(self) -> bool:
        """Update all ryan_chen records to ryan"""
        logger.info("🔄 MIGRATING: ryan_chen → ryan")
        
        if not self.client:
            logger.error("❌ Client not initialized")
            return False
        
        try:
            # Find all ryan_chen records
            offset = None
            updated_count = 0
            
            while True:
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="bot_name",
                                match=models.MatchValue(value="ryan_chen")
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
                    logger.info("   [DRY RUN] Would update %d ryan_chen records to ryan", len(points))
                    updated_count += len(points)
                else:
                    # Update batch of records using set_payload
                    for point in points:
                        payload = dict(point.payload) if point.payload else {}
                        payload["bot_name"] = "ryan"
                        
                        # Update just the payload, keeping vectors intact
                        self.client.set_payload(
                            collection_name=self.collection_name,
                            payload=payload,
                            points=[point.id]
                        )
                        
                        updated_count += 1
                        self.stats["ryan_chen_updated"] += 1
                
                offset = next_offset
                if not next_offset:
                    break
            
            if self.dry_run:
                logger.info("   [DRY RUN] Total ryan_chen records to update: %d", updated_count)
            else:
                logger.info("✅ Updated %d records: ryan_chen → ryan", updated_count)
            
            return True
            
        except Exception as e:
            logger.error("❌ Failed to migrate ryan_chen records: %s", e)
            self.stats["errors"] += 1
            return False
    
    def print_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 60)
        print("🎯 RYAN CHEN → RYAN MIGRATION SUMMARY")
        print("=" * 60)
        
        print("🔄 Ryan Chen → Ryan: %d", self.stats['ryan_chen_updated'])
        print("❌ Errors: %d", self.stats['errors'])
        
        if self.dry_run:
            print("\n💡 This was a DRY RUN - no actual changes made")
            print("   Run with --update flag to apply changes")

async def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate ryan_chen to ryan")
    parser.add_argument("--update", action="store_true", 
                       help="Actually update records (default is dry-run)")
    
    args = parser.parse_args()
    
    print("🚀 RYAN CHEN → RYAN MIGRATION")
    print("=" * 60)
    print("Mode: %s", 'UPDATE' if args.update else 'DRY RUN')
    
    migrator = RyanChenToRyanMigrator(dry_run=not args.update)
    
    # Setup connection
    if not await migrator.setup():
        print("❌ Failed to setup Qdrant connection")
        return False
    
    # Run migration
    success = await migrator.migrate_ryan_chen_to_ryan()
    
    # Print summary
    migrator.print_summary()
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)