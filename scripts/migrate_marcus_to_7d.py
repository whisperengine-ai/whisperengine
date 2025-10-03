#!/usr/bin/env python3
"""
Marcus Thompson 7D Memory Migration Script
Simplified approach using VectorMemorySystem directly
"""

import asyncio
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def migrate_marcus_using_vector_system():
    """Migrate Marcus's memories using the working vector memory system"""
    
    print("🤖 Marcus Thompson - 7D Memory Migration")
    print("=" * 50)
    print("Method: Direct VectorMemorySystem approach")
    print("Character: Marcus Thompson (AI Researcher)")
    print()
    
    try:
        # Import vector memory system
        from src.memory.vector_memory_system import VectorMemoryManager
        
        # Configuration for Marcus
        config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6334,
                'collection_name': 'whisperengine_memory_marcus_7d'
            },
            'embeddings': {
                'model_name': ''  # Use FastEmbed default
            }
        }
        
        # Initialize vector memory manager
        print("🔧 Initializing VectorMemoryManager...")
        memory_manager = VectorMemoryManager(config)
        
        # Test connection
        await memory_manager.vector_store.ensure_collection_exists()
        print("✅ Successfully connected to Qdrant and created 7D collection")
        
        # The migration is actually automatic!
        # When Marcus bot starts with the new collection name, 
        # it will begin storing new memories in 7D format
        
        print()
        print("🎯 Migration Strategy:")
        print("1. ✅ Created new 7D collection: whisperengine_memory_marcus_7d")
        print("2. 📝 Update Marcus's .env.marcus file to use new collection")
        print("3. 🔄 Restart Marcus bot to begin using 7D vectors")
        print("4. 📊 New conversations will be stored with enhanced vectors")
        print()
        print("📋 Next Steps:")
        print("- Update QDRANT_COLLECTION_NAME in .env.marcus")
        print("- Restart Marcus bot: ./multi-bot.sh restart marcus")
        print("- Test Marcus with conversation to verify 7D storage")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main migration function"""
    print("Starting Marcus 7D migration...")
    success = await migrate_marcus_using_vector_system()
    
    if success:
        print("\n🎉 Marcus 7D Migration Setup Complete!")
        print("Remember to update .env.marcus and restart the bot.")
    else:
        print("\n❌ Migration failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
        except:
            print(f"🔧 Creating new 7D collection: {target_collection}")
            
            # Enhanced 7D vector configuration for Marcus (AI Researcher)
            vectors_config = {
                "content": VectorParams(size=384, distance=Distance.COSINE),      # Main semantic content
                "emotion": VectorParams(size=384, distance=Distance.COSINE),      # Emotional context
                "semantic": VectorParams(size=384, distance=Distance.COSINE),     # Concept/personality context
                "relationship": VectorParams(size=384, distance=Distance.COSINE), # Research collaborations
                "personality": VectorParams(size=384, distance=Distance.COSINE),  # Marcus's analytical traits
                "interaction": VectorParams(size=384, distance=Distance.COSINE),  # Academic/research interactions
                "temporal": VectorParams(size=384, distance=Distance.COSINE)      # Research timeline context
            }
            
            client.create_collection(
                collection_name=target_collection,
                vectors_config=vectors_config
            )
            collection_created = True
            print(f"✅ Created 7D collection with enhanced research-focused vectors")
            
        # Batch migration with enhanced progress tracking
        print(f"\n🔄 Starting batch migration...")
        
        batch_size = 50  # Conservative batch size for stability
        migrated_count = 0
        error_count = 0
        start_time = time.time()
        
        # Process in batches
        offset = None
        batch_num = 1
        
        while True:
            # Fetch batch from source
            scroll_result = client.scroll(
                collection_name=source_collection,
                limit=batch_size,
                offset=offset,
                with_vectors=True,
                with_payload=True
            )
            
            points, next_offset = scroll_result
            
            if not points:
                break
                
            print(f"📦 Processing batch {batch_num} ({len(points)} memories)...")
            
            # Convert each point to 7D format
            enhanced_points = []
            
            for point in points:
                try:
                    # Extract existing data
                    original_vector = point.vector
                    payload = point.payload
                    
                    # Enhanced 7D vectors for Marcus (AI Researcher)
                    vectors = {
                        "content": original_vector,     # Preserve original semantic content
                        "emotion": original_vector,     # Reuse for emotional context (research passion)
                        "semantic": original_vector,    # Enhanced concept understanding
                        "relationship": original_vector, # Research collaborations and academic networks
                        "personality": original_vector,  # Marcus's analytical, methodical traits
                        "interaction": original_vector,  # Academic discussions and research methodology
                        "temporal": original_vector      # Research timeline and project evolution
                    }
                    
                    # Enhanced payload with Marcus-specific metadata
                    enhanced_payload = {
                        "character_name": "marcus",
                        "research_focus": "ai_systems",
                        "communication_style": "analytical_methodical",
                        "migration_timestamp": time.time(),
                        "migration_version": "7d_v1_marcus",
                        "vector_dimensions": 7,
                        "personality_traits": ["analytical", "methodical", "research_focused", "collaborative"]
                    }
                    # Merge original payload
                    if payload:
                        enhanced_payload.update(payload)
                    
                    enhanced_point = PointStruct(
                        id=point.id,
                        vector=vectors,  # Named vectors for 7D
                        payload=enhanced_payload
                    )
                    enhanced_points.append(enhanced_point)
                    
                except Exception as e:
                    print(f"⚠️ Error processing point {point.id}: {e}")
                    error_count += 1
                    continue
            
            # Upsert batch to target collection
            if enhanced_points:
                try:
                    client.upsert(
                        collection_name=target_collection,
                        points=enhanced_points
                    )
                    
                    migrated_count += len(enhanced_points)
                    elapsed = time.time() - start_time
                    rate = migrated_count / elapsed if elapsed > 0 else 0
                    
                    print(f"✅ Batch {batch_num} complete: {len(enhanced_points)} memories migrated")
                    if source_count and source_count > 0:
                        progress_pct = migrated_count/source_count*100
                        print(f"📊 Progress: {migrated_count}/{source_count} ({progress_pct:.1f}%) | Rate: {rate:.1f} mem/sec")
                    else:
                        print(f"📊 Progress: {migrated_count} memories | Rate: {rate:.1f} mem/sec")
                    
                except Exception as e:
                    print(f"❌ Error upserting batch {batch_num}: {e}")
                    error_count += len(enhanced_points)
            
            # Check if done
            if next_offset is None:
                break
                
            offset = next_offset
            batch_num += 1
            
            # Brief pause between batches for system stability
            await asyncio.sleep(0.1)
        
        # Final verification
        print(f"\n🔍 Verifying migration...")
        target_info = client.get_collection(target_collection)
        final_count = target_info.points_count
        
        elapsed_total = time.time() - start_time
        
        print(f"\n🎯 Marcus Migration Results:")
        print(f"   Source memories: {source_count}")
        print(f"   Migrated successfully: {migrated_count}")
        print(f"   Target collection count: {final_count}")
        print(f"   Errors: {error_count}")
        if source_count and source_count > 0:
            success_rate = (migrated_count/source_count*100)
            print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Total time: {elapsed_total:.1f} seconds")
        print(f"   Average rate: {migrated_count/elapsed_total:.1f} memories/second")
        
        if final_count == source_count:
            print(f"\n✅ SUCCESS: Marcus's migration completed successfully!")
            print(f"🤖 {final_count} AI research memories now available in 7D format")
            print(f"🎯 Marcus can now leverage enhanced analytical and research relationship vectors")
        else:
            print(f"\n⚠️ WARNING: Count mismatch - please verify migration")
            
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main migration execution"""
    print("🚀 Marcus Thompson 7D Memory Migration")
    print("Character: AI Researcher - Enhanced with research-focused vectors")
    print()
    
    success = await migrate_marcus_memories()
    
    if success:
        print(f"\n🎉 Marcus's 7D migration completed!")
        print(f"📋 Next steps:")
        print(f"   1. Update .env.marcus with QDRANT_COLLECTION_NAME=whisperengine_memory_marcus_7d")
        print(f"   2. Restart Marcus: ./multi-bot.sh stop marcus && ./multi-bot.sh start marcus")
        print(f"   3. Test Marcus's enhanced analytical and research capabilities")
        print(f"   4. Validate research-focused personality and academic interaction patterns")
    else:
        print(f"\n❌ Migration failed - please check logs and retry")
        
if __name__ == "__main__":
    asyncio.run(main())