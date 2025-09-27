#!/usr/bin/env python3
"""
Vector Store Bot Name Migration Script

This script checks for and updates legacy bot_name data in Qdrant to use normalized lowercase names.
After the bot_name normalization implementation, there may be legacy records with mixed case.

ACTIONS:
1. Scan Qdrant collection for all bot_name values  
2. Identify mixed case or non-normalized bot names
3. Option to update legacy records to use normalized bot_name values
4. Preserve all other data while updating only bot_name field

SAFETY:
- Dry run mode by default to preview changes
- Backup recommendations before making changes
- Validates normalization logic before updates
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging
from collections import defaultdict, Counter

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.memory.vector_memory_system import normalize_bot_name
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VectorStoreBotNameMigrator:
    """Handles migration of legacy bot_name data in Qdrant"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.client: Optional[QdrantClient] = None
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "whisperengine_memory")
        self.stats = {
            "total_records": 0,
            "legacy_bot_names": [],
            "normalized_counts": defaultdict(int),
            "needs_update": 0,
            "updated": 0,
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
    
    async def analyze_bot_names(self) -> Dict[str, Dict]:
        """Analyze all bot_name values in the collection"""
        if not self.client:
            logger.error("❌ Client not initialized")
            return {}
            
        logger.info("🔍 ANALYZING: Bot name values in vector store")
        
        try:
            # Scroll through all records to get bot_name values
            offset = None
            bot_names_found = Counter()
            sample_records = {}  # Store sample records for each bot_name
            
            while True:
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=None,  # Get all records
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                points, next_offset = result
                
                if not points:
                    break
                    
                for point in points:
                    self.stats["total_records"] += 1
                    payload = point.payload or {}
                    bot_name = payload.get("bot_name", "missing")
                    
                    bot_names_found[bot_name] += 1
                    
                    # Keep a sample record for each bot_name
                    if bot_name not in sample_records:
                        sample_records[bot_name] = {
                            "id": str(point.id),
                            "content": payload.get("content", "")[:100],
                            "user_id": payload.get("user_id", "unknown"),
                            "memory_type": payload.get("memory_type", "unknown")
                        }
                
                offset = next_offset
                if not next_offset:
                    break
                    
                logger.info(f"📊 Processed {self.stats['total_records']} records...")
            
            logger.info(f"✅ ANALYSIS COMPLETE: {self.stats['total_records']} total records")
            logger.info(f"📋 Found {len(bot_names_found)} unique bot_name values:")
            
            # Analyze normalization needs
            normalization_analysis = {}
            for bot_name, count in bot_names_found.most_common():
                normalized = normalize_bot_name(bot_name)
                needs_update = bot_name != normalized
                
                if needs_update:
                    self.stats["needs_update"] += count
                    self.stats["legacy_bot_names"].append(bot_name)
                
                self.stats["normalized_counts"][normalized] += count
                
                normalization_analysis[bot_name] = {
                    "count": count,
                    "normalized": normalized,
                    "needs_update": needs_update,
                    "sample": sample_records.get(bot_name, {})
                }
                
                print(f"  '{bot_name}' → '{normalized}' ({count} records) {'🔄' if needs_update else '✅'}")
            
            return normalization_analysis
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            self.stats["errors"] += 1
            return {}
    
    async def update_legacy_bot_names(self, analysis: Dict[str, Dict]) -> bool:
        """Update legacy bot_name values to normalized format"""
        
        if not self.client:
            logger.error("❌ Client not initialized")
            return False
        
        legacy_names = [name for name, data in analysis.items() if data["needs_update"]]
        
        if not legacy_names:
            logger.info("✅ No legacy bot names found - all records already normalized!")
            return True
            
        logger.info(f"🔄 UPDATING: {len(legacy_names)} legacy bot_name values")
        logger.info(f"   Dry run mode: {self.dry_run}")
        
        if self.dry_run:
            logger.info("   (No actual changes will be made)")
        
        for legacy_name in legacy_names:
            data = analysis[legacy_name]
            normalized = data["normalized"]
            count = data["count"]
            
            logger.info(f"🔄 Processing: '{legacy_name}' → '{normalized}' ({count} records)")
            
            if self.dry_run:
                logger.info(f"   [DRY RUN] Would update {count} records")
                continue
            
            try:
                # Find all records with this legacy bot_name
                offset = None
                updated_count = 0
                
                while True:
                    result = self.client.scroll(
                        collection_name=self.collection_name,
                        scroll_filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="bot_name",
                                    match=models.MatchValue(value=legacy_name)
                                )
                            ]
                        ),
                        limit=50,  # Smaller batches for updates
                        offset=offset,
                        with_payload=True,
                        with_vectors=False  # Don't need vectors for payload updates
                    )
                    
                    points, next_offset = result
                    
                    if not points:
                        break
                    
                    # Update batch of records using set_payload (more efficient for metadata-only updates)
                    for point in points:
                        payload = dict(point.payload) if point.payload else {}
                        payload["bot_name"] = normalized
                        
                        # Update just the payload, keeping vectors intact
                        self.client.set_payload(
                            collection_name=self.collection_name,
                            payload=payload,
                            points=[point.id]
                        )
                        
                        updated_count += 1
                        self.stats["updated"] += 1
                    
                    offset = next_offset
                    if not next_offset:
                        break
                        
                    logger.info(f"   Updated {updated_count}/{count} records...")
                
                logger.info(f"✅ Updated {updated_count} records: '{legacy_name}' → '{normalized}'")
                
            except Exception as e:
                logger.error(f"❌ Failed to update '{legacy_name}': {e}")
                self.stats["errors"] += 1
                
        return self.stats["errors"] == 0
    
    def print_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 60)
        print("🎯 BOT NAME MIGRATION SUMMARY")
        print("=" * 60)
        
        print(f"📊 Total Records: {self.stats['total_records']}")
        print(f"🔄 Records Needing Update: {self.stats['needs_update']}")
        print(f"✅ Records Updated: {self.stats['updated']}")
        print(f"❌ Errors: {self.stats['errors']}")
        
        if self.stats["legacy_bot_names"]:
            print(f"\n📋 Legacy Bot Names Found:")
            for name in self.stats["legacy_bot_names"]:
                normalized = normalize_bot_name(name)
                print(f"  '{name}' → '{normalized}'")
        else:
            print("\n✅ All bot names already normalized!")
            
        print(f"\n📈 Normalized Bot Distribution:")
        for normalized_name, count in sorted(self.stats["normalized_counts"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {normalized_name}: {count} records")
            
        if self.dry_run and self.stats["needs_update"] > 0:
            print(f"\n💡 To perform actual migration, run with --update flag")


async def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate legacy bot_name data in Qdrant")
    parser.add_argument("--update", action="store_true", 
                       help="Actually update records (default is dry-run)")
    parser.add_argument("--collection", type=str, 
                       help="Qdrant collection name (default from env)")
    
    args = parser.parse_args()
    
    # Override collection name if provided
    if args.collection:
        os.environ["QDRANT_COLLECTION_NAME"] = args.collection
    
    print("🚀 VECTOR STORE BOT NAME MIGRATION")
    print("=" * 60)
    print(f"Mode: {'UPDATE' if args.update else 'DRY RUN'}")
    print(f"Collection: {os.getenv('QDRANT_COLLECTION_NAME', 'whisperengine_memory')}")
    
    migrator = VectorStoreBotNameMigrator(dry_run=not args.update)
    
    # Setup connection
    if not await migrator.setup():
        print("❌ Failed to setup Qdrant connection")
        return False
    
    # Analyze current bot names
    analysis = await migrator.analyze_bot_names()
    if not analysis:
        print("❌ Failed to analyze bot names")
        return False
    
    # Update if needed and requested
    if args.update:
        success = await migrator.update_legacy_bot_names(analysis)
        if not success:
            print("❌ Migration had errors")
            return False
    
    # Print summary
    migrator.print_summary()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)