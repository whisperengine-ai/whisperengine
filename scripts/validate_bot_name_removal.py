#!/usr/bin/env python3
"""
Validation script to verify bot_name field removal from vector collections.
"""

import os
import logging
from qdrant_client import QdrantClient, models

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_collection(client: QdrantClient, collection_name: str) -> dict:
    """Validate that bot_name fields have been removed from collection."""
    try:
        # Get total point count
        collection_info = client.get_collection(collection_name)
        total_points = collection_info.points_count
        
        # Check more points for a thorough validation
        bot_name_count = 0
        points_checked = 0
        batch_size = 250  # Larger batch for more comprehensive checking
        
        # Use offset for pagination
        offset = None
        max_points_to_check = 1000  # Check up to this many points
        
        while points_checked < max_points_to_check:
            # Sample points to check for bot_name field
            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                with_payload=True,
                offset=offset
            )
            
            points = scroll_result[0]
            if not points:
                break
                
            for point in points:
                points_checked += 1
                if 'bot_name' in point.payload:
                    bot_name_count += 1
            
            # Update offset for next batch
            offset = scroll_result[1]
            if offset is None:
                break
        
        return {
            'collection': collection_name,
            'total_points': total_points,
            'points_sampled': points_checked,
            'bot_name_fields_found': bot_name_count,
            'migration_successful': bot_name_count == 0
        }
        
    except Exception as e:
        logger.error(f"Error validating {collection_name}: {e}")
        return {
            'collection': collection_name,
            'error': str(e),
            'migration_successful': False
        }

def main():
    """Validate bot_name removal across all collections."""
    # Connect to Qdrant
    client = QdrantClient(
        host=os.getenv('QDRANT_HOST', 'localhost'),
        port=int(os.getenv('QDRANT_PORT', '6334'))
    )
    
    # Get all collections
    collections = client.get_collections()
    target_collections = [
        col.name for col in collections.collections 
        if col.name.startswith('whisperengine_memory_') or col.name.startswith('chat_memories_')
    ]
    
    logger.info(f"🔍 Validating bot_name removal from {len(target_collections)} collections")
    
    results = []
    total_points = 0
    successful_collections = 0
    
    for collection_name in target_collections:
        result = validate_collection(client, collection_name)
        results.append(result)
        
        if 'total_points' in result:
            total_points += result['total_points']
            
        if result.get('migration_successful', False):
            successful_collections += 1
            logger.info(f"✅ {collection_name}: {result['total_points']} points, no bot_name fields found")
        else:
            if 'bot_name_fields_found' in result:
                logger.warning(f"⚠️  {collection_name}: {result['bot_name_fields_found']} bot_name fields still present")
            else:
                logger.error(f"❌ {collection_name}: {result.get('error', 'Unknown error')}")
    
    # Summary
    logger.info(f"\n🎯 VALIDATION SUMMARY:")
    logger.info(f"  📊 Total collections checked: {len(target_collections)}")
    logger.info(f"  ✅ Successfully migrated: {successful_collections}")
    logger.info(f"  📈 Total points across all collections: {total_points:,}")
    
    if successful_collections == len(target_collections):
        logger.info(f"  🚀 MIGRATION COMPLETE: All collections successfully migrated!")
    else:
        failed = len(target_collections) - successful_collections
        logger.warning(f"  ⚠️  {failed} collections may need attention")
    
    # Detailed results
    logger.info(f"\n📋 DETAILED RESULTS:")
    for result in results:
        if result.get('migration_successful'):
            logger.info(f"  ✅ {result['collection']}: {result['total_points']} points")
        else:
            logger.info(f"  ❌ {result['collection']}: {result.get('error', 'Migration incomplete')}")

if __name__ == "__main__":
    main()