#!/usr/bin/env python3
"""
Simple 3D to 7D Memory Migration
Copies existing memories from 3D collection to 7D collection with basic enhancement
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def migrate_elena_memories():
    """Simple migration for Elena's memories"""
    
    print("🚀 Migrating Elena's memories from 3D to 7D format")
    print("=" * 60)
    
    try:
        # Import after path setup
        import httpx
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct, Distance, VectorParams
        
        # Setup Qdrant client
        client = QdrantClient(host="localhost", port=6334)
        
        source_collection = "whisperengine_memory_elena"
        target_collection = "whisperengine_memory_elena_7d"
        
        # Check source collection
        try:
            source_info = client.get_collection(source_collection)
            source_count = source_info.points_count
            print(f"📊 Found {source_count} memories in source collection")
        except Exception as e:
            print(f"❌ Cannot access source collection: {e}")
            return False
        
        # Create target collection if it doesn't exist
        try:
            client.get_collection(target_collection)
            print(f"✅ Target collection {target_collection} already exists")
        except Exception:
            print(f"� Creating target collection {target_collection}")
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
        
        # Get existing memories from target to avoid duplicates
        try:
            target_info = client.get_collection(target_collection)
            target_count = target_info.points_count
            print(f"📈 Target collection currently has {target_count} memories")
        except Exception:
            target_count = 0
        
        # Scroll through source collection and migrate
        migrated_count = 0
        failed_count = 0
        offset = None
        batch_size = 100
        
        print(f"🔄 Starting migration in batches of {batch_size}...")
        
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
                                continue  # Skip already migrated
                        except:
                            pass  # Point doesn't exist, proceed with migration
                        
                        # Create 7D point
                        migrated_point = create_7d_point(point)
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
                    print(f"📈 Migrated batch: {len(migrated_points)} memories (Total: {migrated_count})")
                
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
        print("🎉 Migration Report")
        print("=" * 60)
        print(f"✅ Successfully migrated: {migrated_count} memories")
        print(f"❌ Failed migrations: {failed_count}")
        
        if migrated_count > 0:
            print(f"\n🎯 Elena now has access to {migrated_count} historical memories in 7D format!")
            print("Users will retain their conversation history and relationships.")
        
        return migrated_count > 0
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def create_7d_point(original_point):
    """Create a 7D point from original 3D point"""
    
    from qdrant_client.models import PointStruct
    
    # Extract original data
    original_vectors = original_point.vector
    original_payload = original_point.payload
    
    # Create 7D vectors
    seven_d_vectors = {}
    
    # Handle original vector format
    if isinstance(original_vectors, dict):
        # Already named vectors
        seven_d_vectors.update(original_vectors)
    elif isinstance(original_vectors, list):
        # Legacy single vector - assume it's content
        seven_d_vectors["content"] = original_vectors
    
    # Generate placeholder vectors for missing dimensions
    # (In a full implementation, these would be generated by the 7D analyzer)
    import random
    
    for vector_name in ["content", "emotion", "semantic", "relationship", "personality", "interaction", "temporal"]:
        if vector_name not in seven_d_vectors:
            # Create placeholder vector (384 dimensions)
            # In production, this would use the actual 7D analyzer
            placeholder_vector = [random.gauss(0, 0.1) for _ in range(384)]
            seven_d_vectors[vector_name] = placeholder_vector
    
    # Enhance payload with migration metadata
    enhanced_payload = original_payload.copy()
    enhanced_payload.update({
        "migrated_from_3d": True,
        "migration_timestamp": time.time(),
        "original_collection": "whisperengine_memory_elena"
    })
    
    return PointStruct(
        id=original_point.id,
        vector=seven_d_vectors,
        payload=enhanced_payload
    )

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "elena":
        success = asyncio.run(migrate_elena_memories())
        sys.exit(0 if success else 1)
    else:
        print("Usage: python migrate_3d_to_7d_memories.py elena")
        sys.exit(1)