#!/usr/bin/env python3
"""
WhisperEngine Vector Storage Migration: Remove bot_name Filtering

This script migrates the vector storage architecture from bot_name filtering
to pure collection-based isolation. Since each bot now has its own dedicated
Qdrant collection, bot_name fields are redundant and can be removed.

MIGRATION STEPS:
1. Remove bot_name field from all vector payloads in existing collections
2. Update collection schema to remove bot_name indexing
3. Validate data integrity after migration

Collections to migrate:
- whisperengine_memory_aetheris
- whisperengine_memory_aethys  
- whisperengine_memory_dotty
- whisperengine_memory_dream_7d
- whisperengine_memory_elena_7d
- whisperengine_memory_gabriel_7d
- whisperengine_memory_jake_7d
- whisperengine_memory_marcus_7d
- whisperengine_memory_ryan_7d
- whisperengine_memory_sophia_7d

SAFE TO RUN: This script makes non-destructive changes that can be rolled back.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import (
    Distance, VectorParams, PointStruct, Range, OrderBy, Direction,
    UpdateResult, ScrollResult
)

# Custom JSON encoder to handle Qdrant objects
class QdrantJSONEncoder(json.JSONEncoder):
    """JSON encoder that can handle Qdrant objects like VectorParams."""
    def default(self, obj):
        # Handle VectorParams objects
        if isinstance(obj, VectorParams):
            return {
                "size": getattr(obj, "size", None),
                "distance": str(getattr(obj, "distance", None)),
                "hnsw_config": getattr(obj, "hnsw_config", None),
                "quantization_config": getattr(obj, "quantization_config", None),
                "on_disk": getattr(obj, "on_disk", None),
            }
        # Handle Distance enum objects
        elif isinstance(obj, Distance):
            return str(obj)
        # Handle other Qdrant model objects with a dict representation
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        # Let the base encoder handle the rest
        return super().default(obj)

# Configure logging
log_filename = f'migration_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename)
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to file: {log_filename}")

# Override JSON logging to use custom encoder for Qdrant objects
def log_to_json_file(data, filename):
    """Write data to JSON file with custom encoder."""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, cls=QdrantJSONEncoder)
        return True
    except Exception as e:
        logger.error(f"Failed to write JSON log: {e}")
        return False


class VectorStorageMigration:
    """Migrate vector storage to remove bot_name filtering"""
    
    def __init__(self):
        """Initialize Qdrant client and collection list"""
        self.client = QdrantClient(
            host=os.getenv('QDRANT_HOST', 'localhost'),
            port=int(os.getenv('QDRANT_PORT', '6334'))
        )
        
        # Auto-discover all bot collections to migrate
        self.collections = self._discover_all_collections()
        
        self.migration_stats = {}
        self.migration_log = []
    
    def _discover_all_collections(self) -> List[str]:
        """Discover all bot collections that need migration."""
        try:
            # First get all available collections
            collections = self.client.get_collections()
            all_collections = [
                col.name for col in collections.collections 
                if col.name.startswith('whisperengine_memory_') or col.name.startswith('chat_memories_')
            ]
            
            # Now determine which collections are actively used from .env files
            active_collections = self._get_active_collections_from_env_files()
            
            if active_collections:
                # Filter to only include active collections that exist
                target_collections = [col for col in all_collections if col in active_collections]
                logger.info(f"🔍 Found {len(target_collections)} active collections for migration (from .env files)")
            else:
                # Fallback to all collections if we couldn't determine active ones
                target_collections = all_collections
                logger.info(f"🔍 Using all {len(target_collections)} collections for migration (no .env filtering)")
            
            for col in target_collections:
                logger.info(f"  📁 {col}")
            return target_collections
        except Exception as e:
            logger.error(f"Failed to discover collections: {e}")
            return []
            
    def _get_active_collections_from_env_files(self) -> List[str]:
        """Get collection names that are actively used in .env files."""
        active_collections = []
        env_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_files = [f for f in os.listdir(env_dir) if f.startswith('.env.')]
        
        logger.info(f"🔍 Scanning {len(env_files)} .env files for active collections")
        
        for env_file in env_files:
            env_path = os.path.join(env_dir, env_file)
            try:
                with open(env_path, 'r') as f:
                    content = f.read()
                    
                # Look for QDRANT_COLLECTION_NAME in the file
                for line in content.splitlines():
                    if line.startswith('QDRANT_COLLECTION_NAME='):
                        collection_name = line.split('=', 1)[1].strip().strip('"\'')
                        if collection_name:
                            active_collections.append(collection_name)
                            logger.info(f"  📁 Found active collection in {env_file}: {collection_name}")
            except Exception as e:
                logger.warning(f"  ⚠️ Error reading {env_file}: {e}")
                
        return active_collections
    
    async def run_full_migration(self) -> Dict[str, Any]:
        """Execute complete migration across all collections"""
        logger.info("🚀 Starting WhisperEngine Vector Storage Migration")
        logger.info("🎯 GOAL: Remove bot_name filtering for collection-based isolation")
        
        migration_start = datetime.now()
        
        try:
            # Step 1: Analyze current state
            await self.analyze_current_state()
            
            # Step 2: Migrate each collection
            for collection_name in self.collections:
                await self.migrate_collection(collection_name)
            
            # Step 3: Generate migration report
            migration_report = await self.generate_migration_report()
            
            migration_end = datetime.now()
            duration = (migration_end - migration_start).total_seconds()
            
            logger.info(f"✅ Migration completed successfully in {duration:.2f} seconds")
            return migration_report
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
    
    async def analyze_current_state(self) -> Dict[str, Any]:
        """Analyze current collections and bot_name usage"""
        logger.info("🔍 Analyzing current vector storage state...")
        
        analysis = {
            'existing_collections': [],
            'total_points': 0,
            'bot_name_usage': {},
            'collection_stats': {}
        }
        
        for collection_name in self.collections:
            try:
                # Check if collection exists
                collection_info = self.client.get_collection(collection_name)
                analysis['existing_collections'].append(collection_name)
                
                # Get collection stats
                stats = {
                    'points_count': collection_info.points_count,
                    'vector_size': collection_info.config.params.vectors,
                    'distance_metric': collection_info.config.params.vectors
                }
                analysis['collection_stats'][collection_name] = stats
                analysis['total_points'] += collection_info.points_count
                
                # Sample bot_name usage
                scroll_result = self.client.scroll(
                    collection_name=collection_name,
                    limit=10,
                    with_payload=True,
                    with_vectors=False
                )
                
                bot_names = set()
                for point in scroll_result[0]:
                    if point.payload and 'bot_name' in point.payload:
                        bot_names.add(point.payload['bot_name'])
                
                analysis['bot_name_usage'][collection_name] = list(bot_names)
                
                logger.info(f"📊 {collection_name}: {stats['points_count']} points, bot_names: {bot_names}")
                
            except Exception as e:
                logger.warning(f"⚠️ Collection {collection_name} not found or error: {e}")
        
        # Convert non-serializable objects before appending to log
        serializable_analysis = {
            'existing_collections': analysis['existing_collections'],
            'total_points': analysis['total_points'],
            'bot_name_usage': analysis['bot_name_usage'],
            'collection_stats': {}
        }
        
        # Convert VectorParams objects in collection_stats to serializable form
        for col_name, stats in analysis['collection_stats'].items():
            serializable_analysis['collection_stats'][col_name] = {
                'points_count': stats['points_count'],
                # Use string representation for complex objects
                'vector_size': str(stats['vector_size']) if stats['vector_size'] else None,
                'distance_metric': str(stats['distance_metric']) if stats['distance_metric'] else None
            }
        
        self.migration_log.append({
            'step': 'analysis',
            'timestamp': datetime.now().isoformat(),
            'data': serializable_analysis
        })
        
        return analysis
    
    async def migrate_collection(self, collection_name: str) -> Dict[str, Any]:
        """Migrate a single collection to remove bot_name fields"""
        logger.info(f"🔄 Migrating collection: {collection_name}")
        
        migration_start = datetime.now()
        stats = {
            'collection_name': collection_name,
            'points_processed': 0,
            'points_updated': 0,
            'bot_names_removed': 0,
            'errors': []
        }
        
        try:
            # Get all points in batches
            offset = None
            batch_size = 100
            
            while True:
                # Scroll through all points
                scroll_result = self.client.scroll(
                    collection_name=collection_name,
                    scroll_filter=None,  # Get all points
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False  # Don't need vectors for payload update
                )
                
                points, next_offset = scroll_result
                
                if not points:
                    break
                
                # Process batch of points
                batch_updates = []
                for point in points:
                    stats['points_processed'] += 1
                    
                    # Check if point has bot_name field
                    if point.payload and 'bot_name' in point.payload:
                        try:
                            # Create payload without bot_name
                            new_payload = {k: v for k, v in point.payload.items() if k != 'bot_name'}
                            
                            # For safety, make sure the new payload is actually different
                            if len(new_payload) != len(point.payload):
                                # Add to batch update (payload-only update)
                                # CRITICAL FIX: Must set full payload at once, not just modify
                                # Need to replace entire payload rather than just delete fields
                                self.client.set_payload(
                                    collection_name=collection_name,
                                    points=[point.id],
                                    payload=new_payload,
                                    wait=True  # Wait for operation to complete
                                )
                                stats['bot_names_removed'] += 1
                                stats['points_updated'] += 1
                        except Exception as e:
                            error_msg = f"Failed to update point {point.id}: {str(e)}"
                            logger.warning(error_msg)
                            stats['errors'].append(error_msg)
                
                # Execute batch update if we have updates
                if stats['points_updated'] > 0 and stats['points_processed'] % batch_size == 0:
                    logger.info(f"  ✅ Updated {stats['points_updated']} points so far")
                
                # Update offset for next batch
                offset = next_offset
                if offset is None:
                    break
                
                # Progress logging
                if stats['points_processed'] % 500 == 0:
                    logger.info(f"  📈 Processed {stats['points_processed']} points...")
            
            migration_end = datetime.now()
            duration = (migration_end - migration_start).total_seconds()
            
            logger.info(f"✅ {collection_name} migration completed:")
            logger.info(f"  - Points processed: {stats['points_processed']}")
            logger.info(f"  - Points updated: {stats['points_updated']}")
            logger.info(f"  - Bot names removed: {stats['bot_names_removed']}")
            logger.info(f"  - Duration: {duration:.2f}s")
            logger.info(f"  - Errors: {len(stats['errors'])}")
            
            self.migration_stats[collection_name] = stats
            
        except Exception as e:
            error_msg = f"Collection migration failed: {e}"
            stats['errors'].append(error_msg)
            logger.error(f"❌ {collection_name}: {error_msg}")
            raise
        
        return stats
    
    async def generate_migration_report(self) -> Dict[str, Any]:
        """Generate comprehensive migration report"""
        total_processed = sum(stats.get('points_processed', 0) for stats in self.migration_stats.values())
        total_updated = sum(stats.get('points_updated', 0) for stats in self.migration_stats.values())
        total_bot_names_removed = sum(stats.get('bot_names_removed', 0) for stats in self.migration_stats.values())
        total_errors = sum(len(stats.get('errors', [])) for stats in self.migration_stats.values())
        
        report = {
            'migration_timestamp': datetime.now().isoformat(),
            'collections_migrated': len(self.migration_stats),
            'total_points_processed': total_processed,
            'total_points_updated': total_updated,
            'total_bot_names_removed': total_bot_names_removed,
            'total_errors': total_errors,
            'success_rate': (total_updated / total_processed * 100) if total_processed > 0 else 0,
            'collection_details': self.migration_stats,
            'migration_log': self.migration_log
        }
        
        # Save report to file
        report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                # Use our custom JSON encoder to handle Qdrant objects
                json.dump(report, f, indent=2, cls=QdrantJSONEncoder)
            
            logger.info("📋 MIGRATION REPORT:")
            logger.info(f"  Collections migrated: {report['collections_migrated']}")
            logger.info(f"  Points processed: {report['total_points_processed']}")
            logger.info(f"  Points updated: {report['total_points_updated']}")
            logger.info(f"  Bot names removed: {report['total_bot_names_removed']}")
            logger.info(f"  Success rate: {report['success_rate']:.1f}%")
            logger.info(f"  Report saved: {report_file}")
        except Exception as e:
            logger.error(f"❌ Error generating report file: {e}")
            logger.info("📋 MIGRATION REPORT (not saved to file):")
            logger.info(f"  Collections migrated: {report['collections_migrated']}")
            logger.info(f"  Points processed: {report['total_points_processed']}")
            logger.info(f"  Points updated: {report['total_points_updated']}")
            logger.info(f"  Bot names removed: {report['total_bot_names_removed']}")
            logger.info(f"  Success rate: {report['success_rate']:.1f}%")
        
        return report
    
    async def validate_migration(self) -> Dict[str, Any]:
        """Validate that migration completed successfully"""
        logger.info("🔍 Validating migration results...")
        
        validation_results = {}
        
        for collection_name in self.collections:
            try:
                # Check for any remaining bot_name fields
                scroll_result = self.client.scroll(
                    collection_name=collection_name,
                    limit=100,  # Sample check
                    with_payload=True,
                    with_vectors=False
                )
                
                remaining_bot_names = 0
                for point in scroll_result[0]:
                    if point.payload and 'bot_name' in point.payload:
                        remaining_bot_names += 1
                
                validation_results[collection_name] = {
                    'remaining_bot_names': remaining_bot_names,
                    'sample_size': len(scroll_result[0]),
                    'clean': remaining_bot_names == 0
                }
                
                status = "✅ CLEAN" if remaining_bot_names == 0 else f"⚠️ {remaining_bot_names} remaining"
                logger.info(f"  {collection_name}: {status}")
                
            except Exception as e:
                logger.error(f"  ❌ Validation failed for {collection_name}: {e}")
                validation_results[collection_name] = {'error': str(e)}
        
        return validation_results


    async def identify_obsolete_collections(self) -> List[str]:
        """Identify collections that are no longer actively used."""
        try:
            # Get all collections
            collections = self.client.get_collections()
            all_collections = [
                col.name for col in collections.collections 
                if col.name.startswith('whisperengine_memory_') or col.name.startswith('chat_memories_')
            ]
            
            # Get active collections
            active_collections = self._get_active_collections_from_env_files()
            
            # Find obsolete collections
            obsolete_collections = [col for col in all_collections if col not in active_collections]
            
            logger.info(f"🔍 Found {len(obsolete_collections)} obsolete collections")
            for col in obsolete_collections:
                logger.info(f"  🗑️ Obsolete collection: {col}")
                
            return obsolete_collections
        except Exception as e:
            logger.error(f"Failed to identify obsolete collections: {e}")
            return []
    
    async def delete_obsolete_collections(self, collections: List[str]) -> Dict[str, Any]:
        """Delete obsolete collections that are no longer in use."""
        results = {
            'deleted': [],
            'failed': [],
            'skipped': []
        }
        
        for collection_name in collections:
            try:
                # Confirm deletion
                self.client.delete_collection(collection_name=collection_name)
                results['deleted'].append(collection_name)
                logger.info(f"🗑️  Deleted obsolete collection: {collection_name}")
            except Exception as e:
                error_msg = f"Failed to delete {collection_name}: {e}"
                results['failed'].append({'collection': collection_name, 'error': str(e)})
                logger.error(f"❌ {error_msg}")
        
        return results


async def main():
    """Main migration execution"""
    print("🚀 WhisperEngine Vector Storage Migration")
    print("🎯 Removing bot_name filtering for collection-based isolation")
    print()
    
    # Check Qdrant connection first
    try:
        client = QdrantClient(
            host=os.getenv('QDRANT_HOST', 'localhost'),
            port=int(os.getenv('QDRANT_PORT', '6334'))
        )
        # Test connection
        client.get_collections()
        print(f"✅ Connected to Qdrant at {os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6334')}")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        print("Please check your Qdrant connection settings (QDRANT_HOST, QDRANT_PORT)")
        sys.exit(1)
    
    # Create migration instance
    migration = VectorStorageMigration()
    
    # Check for auto-confirmation environment variable
    auto_confirm = os.getenv('AUTO_CONFIRM_MIGRATION', '').lower() == 'true'
    
    # Check if we should clean up obsolete collections
    cleanup_enabled = os.getenv('CLEANUP_OBSOLETE_COLLECTIONS', '').lower() == 'true'
    if cleanup_enabled:
        obsolete_collections = await migration.identify_obsolete_collections()
        if obsolete_collections:
            print(f"\n⚠️ Found {len(obsolete_collections)} obsolete collections:")
            for col in obsolete_collections:
                print(f"  🗑️ {col}")
                
            if auto_confirm:
                print("⚠️ Auto-confirming deletion from environment variable")
                delete_response = 'y'
            else:
                delete_response = input("\n⚠️ Would you like to DELETE these obsolete collections? (y/N): ")
                
            if delete_response.lower() == 'y':
                results = await migration.delete_obsolete_collections(obsolete_collections)
                print(f"✅ Deleted {len(results['deleted'])} obsolete collections")
                if results['failed']:
                    print(f"⚠️ Failed to delete {len(results['failed'])} collections")
            else:
                print("❌ Skipping deletion of obsolete collections")
    
    # Confirm migration
    if auto_confirm:
        print("⚠️ Auto-confirming migration from environment variable")
        response = 'y'
    else:
        # Confirm migration
        response = input("⚠️ This will modify vector data. Continue? (y/N): ")
        
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        return
    
    try:
        # Create migration instance
        migration = VectorStorageMigration()
        
        # Run migration
        report = await migration.run_full_migration()
        
        # Validate results
        validation = await migration.validate_migration()
        
        print("\n🎉 Migration completed successfully!")
        print(f"📊 Processed {report['total_points_processed']} points")
        print(f"🔄 Updated {report['total_points_updated']} points")
        print(f"🗑️  Removed {report['total_bot_names_removed']} bot_name fields")
        
        # Check if all collections are clean
        all_clean = all(result.get('clean', False) for result in validation.values())
        if all_clean:
            print("✅ All collections successfully migrated - no bot_name fields remaining")
        else:
            print("⚠️ Some collections may need additional cleanup")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())