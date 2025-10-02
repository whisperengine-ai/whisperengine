#!/usr/bin/env python3
"""
Ryan's 3D to 7D Memory Migration
Migrates Ryan's memories from 3D to 7D collection format
Enhanced migration script based on Jake's successful pattern
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def migrate_ryan_memories():
    """Migrate Ryan's memories from 3D to 7D format"""
    
    print("🎮 Migrating Ryan's Memories from 3D to 7D Format")
    print("=" * 60)
    print("Character: Ryan Chen - Indie Game Developer")
    print()
    
    try:
        # Import after path setup
        import httpx
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct, Distance, VectorParams
        
        # Setup Qdrant client
        client = QdrantClient(host="localhost", port=6334)
        
        source_collection = "whisperengine_memory_ryan"
        target_collection = "whisperengine_memory_ryan_7d"
        
        # Check source collection
        try:
            source_info = client.get_collection(source_collection)
            source_count = source_info.points_count
            print(f"📊 Found {source_count} memories in Ryan's 3D collection")
        except Exception as e:
            print(f"❌ Cannot access source collection: {e}")
            return False
        
        # Create target 7D collection if it doesn't exist
        collection_created = False
        try:
            client.get_collection(target_collection)
            print(f"✅ Target collection {target_collection} already exists")
        except Exception:
            print(f"🔧 Creating Ryan's 7D collection: {target_collection}")
            client.create_collection(
                collection_name=target_collection,
                vectors_config={
                    "content": VectorParams(size=384, distance=Distance.COSINE),
                    "emotion": VectorParams(size=384, distance=Distance.COSINE),
                    "semantic": VectorParams(size=384, distance=Distance.COSINE),
                    "relationship": VectorParams(size=384, distance=Distance.COSINE),
                    "personality": VectorParams(size=384, distance=Distance.COSINE),
                    "interaction": VectorParams(size=384, distance=Distance.COSINE),
                    "temporal": VectorParams(size=384, distance=Distance.COSINE),
                }
            )
            print("✅ 7D collection created with all dimensional vectors")
            collection_created = True
        
        # Create payload indexes (critical for temporal queries)
        if collection_created:
            from qdrant_client.models import PayloadSchemaType
            print(f"\n🔧 Creating payload indexes for temporal queries...")
            indexes = [
                ('user_id', PayloadSchemaType.KEYWORD),
                ('timestamp_unix', PayloadSchemaType.FLOAT),  # CRITICAL for order_by
                ('emotional_context', PayloadSchemaType.KEYWORD),
                ('semantic_key', PayloadSchemaType.KEYWORD),
                ('content_hash', PayloadSchemaType.INTEGER),
                ('bot_name', PayloadSchemaType.KEYWORD),
                ('memory_type', PayloadSchemaType.KEYWORD),
            ]
            
            for field_name, schema_type in indexes:
                try:
                    client.create_payload_index(
                        collection_name=target_collection,
                        field_name=field_name,
                        field_schema=schema_type
                    )
                    print(f"  ✅ Created index: {field_name}")
                except Exception as e:
                    print(f"  ⚠️  Index {field_name} may already exist: {e}")
            
            print("✅ All payload indexes created")
        
        # Get existing memories from target to avoid duplicates
        try:
            target_info = client.get_collection(target_collection)
            target_count = target_info.points_count
            print(f"📈 Target collection currently has {target_count} memories")
        except Exception:
            target_count = 0
        
        # Migration counters
        migrated_count = 0
        skipped_count = 0
        failed_count = 0
        offset = None
        batch_size = 100
        
        print(f"\n🔄 Starting migration in batches of {batch_size}...")
        print()
        
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
                
                # Process batch
                migrated_points = []
                for point in points:
                    try:
                        # Check if already migrated
                        try:
                            existing = client.retrieve(
                                collection_name=target_collection,
                                ids=[point.id]
                            )
                            if existing:
                                skipped_count += 1
                                continue  # Skip already migrated
                        except:
                            pass  # Point doesn't exist, proceed with migration
                        
                        # Create 7D point from 3D point
                        migrated_point = create_7d_point(point, character_name="ryan")
                        migrated_points.append(migrated_point)
                        
                    except Exception as e:
                        print(f"⚠️  Failed to process point {point.id}: {e}")
                        failed_count += 1
                        continue
                
                # Upsert batch to target collection
                if migrated_points:
                    client.upsert(
                        collection_name=target_collection,
                        points=migrated_points
                    )
                    migrated_count += len(migrated_points)
                    print(f"📦 Batch {migrated_count // batch_size}: Migrated {len(migrated_points)} memories (Total: {migrated_count})")
                
                offset = scroll_result[1]
                if offset is None:
                    break
                    
                # Brief pause to avoid overwhelming
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Batch migration error: {e}")
                failed_count += batch_size
                break
        
        # Final report
        print("\n" + "=" * 60)
        print("🎉 Ryan's Migration Report")
        print("=" * 60)
        print(f"✅ Successfully migrated: {migrated_count} memories")
        print(f"⏭️  Skipped (already migrated): {skipped_count}")
        print(f"❌ Failed migrations: {failed_count}")
        print()
        
        if migrated_count > 0:
            print(f"🎯 Ryan now has {migrated_count} historical memories in 7D format!")
            print("🎮 Game development context and user relationships preserved")
            print("💻 Ready for enhanced personality and interaction intelligence")
            print()
            print("Next steps:")
            print("  1. Update .env.ryan to use: QDRANT_COLLECTION_NAME=whisperengine_memory_ryan_7d")
            print("  2. Restart Ryan: ./multi-bot.sh restart ryan")
            print("  3. Test with Discord messages to verify 7D intelligence")
        
        return migrated_count > 0
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_7d_point(original_point, character_name: str = "ryan"):
    """Create a 7D point from original 3D point with Ryan-specific enhancements"""
    
    from qdrant_client.models import PointStruct
    
    # Extract original data
    original_vectors = original_point.vector
    original_payload = original_point.payload
    
    # Create 7D vectors
    seven_d_vectors = {}
    
    # Handle original vector format
    if isinstance(original_vectors, dict):
        # Already named vectors (3D: content, emotion, semantic)
        seven_d_vectors.update(original_vectors)
    elif isinstance(original_vectors, list):
        # Legacy single vector - assume it's content
        seven_d_vectors["content"] = original_vectors
    
    # Generate placeholder vectors for missing 7D dimensions
    # In production, these will be generated by Enhanced7DVectorAnalyzer
    import random
    
    for vector_name in ["content", "emotion", "semantic", "relationship", "personality", "interaction", "temporal"]:
        if vector_name not in seven_d_vectors:
            # Create placeholder vector (384 dimensions)
            # Uses small random values centered at 0
            placeholder_vector = [random.gauss(0, 0.1) for _ in range(384)]
            seven_d_vectors[vector_name] = placeholder_vector
    
    # Enhance payload with migration metadata
    enhanced_payload = original_payload.copy()
    enhanced_payload.update({
        "migrated_from_3d": True,
        "migration_timestamp": time.time(),
        "original_collection": "whisperengine_memory_ryan",
        "character_name": character_name,
        "migration_notes": "3D→7D migration with placeholder 7D vectors (will be regenerated on next storage)"
    })
    
    return PointStruct(
        id=original_point.id,
        vector=seven_d_vectors,
        payload=enhanced_payload
    )


if __name__ == "__main__":
    print()
    success = asyncio.run(migrate_ryan_memories())
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n📝 Remember to update Ryan's environment:")
        print("   Edit .env.ryan:")
        print("   QDRANT_COLLECTION_NAME=whisperengine_memory_ryan_7d")
        print("\n🔄 Then restart Ryan:")
        print("   ./multi-bot.sh restart ryan")
        sys.exit(0)
    else:
        print("\n❌ Migration failed - check logs above")
        sys.exit(1)
