#!/usr/bin/env python3
"""
Gabriel Data Migration Script - 3D to 7D Collection
Migrates Gabriel's existing 2,897 memories to enhanced 7D format
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path for Docker execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def migrate_gabriel_data():
    """Migrate Gabriel's memories from 3D to 7D collection"""
    
    print("🤖 Gabriel Data Migration - 3D to 7D Collection")
    print("=" * 55)
    print("Character: Gabriel - Archangel & Divine Messenger")
    print("Source: whisperengine_memory_gabriel (3D)")
    print("Target: whisperengine_memory_gabriel_7d (Enhanced 7D)")
    print()
    
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct, Distance, VectorParams
        from src.memory.vector_memory_system import VectorMemoryManager
        
        # Setup Qdrant client
        client = QdrantClient(host="qdrant", port=6333)
        
        source_collection = "whisperengine_memory_gabriel"
        target_collection = "whisperengine_memory_gabriel_7d"
        
        # Check source collection
        try:
            source_info = client.get_collection(source_collection)
            source_count = source_info.points_count
            print(f"📊 Found {source_count} memories in Gabriel's 3D collection")
        except Exception as e:
            print(f"❌ Cannot access source collection: {e}")
            return False
        
        # Initialize target collection with VectorMemoryManager
        print("🔧 Initializing target 7D collection...")
        config = {
            'qdrant': {
                'host': 'qdrant',
                'port': 6333,
                'collection_name': target_collection
            },
            'embeddings': {
                'model_name': ''
            }
        }
        
        memory_manager = VectorMemoryManager(config)
        
        # Ensure target collection exists
        try:
            client.get_collection(target_collection)
            print(f"✅ Target collection {target_collection} ready")
        except:
            print(f"❌ Target collection {target_collection} not found")
            return False
        
        # Batch migration
        batch_size = 50
        migrated_count = 0
        failed_count = 0
        
        print(f"\n🔄 Starting batch migration ({batch_size} memories per batch)")
        print("📋 Processing Gabriel's spiritual conversations...")
        
        # Scroll through source collection
        offset = None
        while True:
            try:
                # Get batch from source
                scroll_result = client.scroll(
                    collection_name=source_collection,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )
                
                points = scroll_result[0]
                if not points:
                    break
                
                offset = scroll_result[1]
                
                print(f"📦 Processing batch of {len(points)} memories...")
                
                # Process each memory in the batch
                for point in points:
                    try:
                        payload = point.payload
                        
                        # Extract conversation data
                        user_id = payload.get('user_id', 'unknown_user')
                        user_message = payload.get('user_message', '')
                        bot_response = payload.get('bot_response', '')
                        timestamp = payload.get('timestamp', datetime.now().isoformat())
                        
                        # Skip if essential data is missing
                        if not user_message and not bot_response:
                            failed_count += 1
                            continue
                        
                        # Create user metadata from existing payload
                        user_metadata = {
                            'migrated_from_3d': True,
                            'original_timestamp': timestamp,
                            'migration_date': datetime.now().isoformat(),
                            'character': 'gabriel',
                            'migration_batch': f"batch_{migrated_count // batch_size + 1}"
                        }
                        
                        # Add any additional metadata from original
                        for key, value in payload.items():
                            if key not in ['user_id', 'user_message', 'bot_response', 'timestamp', 'bot_name']:
                                user_metadata[key] = value
                        
                        # Store in 7D collection using VectorMemoryManager
                        await memory_manager.store_conversation(
                            user_id=user_id,
                            user_message=user_message,
                            bot_response=bot_response,
                            user_metadata=user_metadata
                        )
                        
                        migrated_count += 1
                        
                        if migrated_count % 100 == 0:
                            print(f"   ✅ Migrated {migrated_count} memories...")
                        
                    except Exception as e:
                        print(f"   ⚠️  Failed to migrate memory {point.id}: {e}")
                        failed_count += 1
                        continue
                
                # Small delay between batches
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Batch processing error: {e}")
                break
        
        # Final verification
        try:
            target_info = client.get_collection(target_collection)
            final_count = target_info.points_count
            print(f"\n📊 Migration Summary:")
            print(f"   Source memories: {source_count}")
            print(f"   Successfully migrated: {migrated_count}")
            print(f"   Failed migrations: {failed_count}")
            print(f"   Target collection total: {final_count}")
            
            success_rate = (migrated_count / source_count) * 100 if source_count > 0 else 0
            print(f"   Migration success rate: {success_rate:.1f}%")
            
            if success_rate >= 95:
                print("\n🎉 Gabriel data migration SUCCESSFUL!")
                print("   Gabriel's spiritual memories preserved with 7D enhancement")
            else:
                print("\n⚠️  Gabriel migration completed with some issues")
                print("   Review failed migrations for data integrity")
            
            return success_rate >= 90
            
        except Exception as e:
            print(f"❌ Final verification failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main migration function"""
    print("Starting Gabriel data migration...")
    success = await migrate_gabriel_data()
    
    if success:
        print("\n🎉 Gabriel Data Migration Complete!")
        print("Gabriel's memories now enhanced with 7D vector system.")
    else:
        print("\n❌ Migration failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())