#!/usr/bin/env python3
"""
Gabriel 3D to 7D Memory Migration Script
Migrate ONLY Gabriel's memories (bot_name = "gabriel") from 3D to enhanced 7D format
Based on the proven Ryan/Elena/Jake migration pattern
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for Docker execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def migrate_gabriel_memories():
    """Migrate Gabriel's memories from 3D to 7D format with proper bot_name filtering"""
    
    print("🤖 Gabriel Memory Migration: 3D → 7D")
    print("=" * 50)
    print("Character: Gabriel - British Gentleman AI Companion")
    print("Method: Bot-specific migration with proper filtering")
    print()
    
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import (
            PointStruct, Distance, VectorParams, 
            Filter, FieldCondition, MatchValue
        )
        import json
        from fastembed import TextEmbedding
        
        # Initialize clients
        client = QdrantClient(host="qdrant", port=6333)
        embedder = TextEmbedding()
        
        source_collection = "whisperengine_memory_gabriel"
        target_collection = "whisperengine_memory_gabriel_7d"
        
        print(f"📊 Source: {source_collection}")
        print(f"📊 Target: {target_collection}")
        
        # Check source collection and count Gabriel's memories
        source_info = client.get_collection(source_collection)
        print(f"✅ Source collection has {source_info.points_count} total points")
        
        # Count Gabriel-specific memories
        gabriel_filter = Filter(
            must=[FieldCondition(key="bot_name", match=MatchValue(value="gabriel"))]
        )
        
        gabriel_memories = client.scroll(
            collection_name=source_collection,
            scroll_filter=gabriel_filter,
            limit=10000,  # Get all Gabriel memories
            with_payload=True,
            with_vectors=True
        )
        
        gabriel_count = len(gabriel_memories[0])
        print(f"✅ Found {gabriel_count} Gabriel-specific memories to migrate")
        
        if gabriel_count == 0:
            print("❌ No Gabriel memories found to migrate!")
            return False
        
        # Create 7D collection
        print(f"\n🔧 Creating 7D collection: {target_collection}")
        
        try:
            client.delete_collection(target_collection)
            print("   Deleted existing collection")
        except:
            pass
        
        # Create collection with 7D named vectors
        vectors_config = {
            "content": VectorParams(size=384, distance=Distance.COSINE),      # Main semantic content
            "emotion": VectorParams(size=384, distance=Distance.COSINE),      # Emotional context
            "semantic": VectorParams(size=384, distance=Distance.COSINE),     # Concept/personality context
            "relationship": VectorParams(size=384, distance=Distance.COSINE), # Social connections
            "personality": VectorParams(size=384, distance=Distance.COSINE),  # Gabriel's gentleman traits
            "interaction": VectorParams(size=384, distance=Distance.COSINE),  # Communication patterns
            "temporal": VectorParams(size=384, distance=Distance.COSINE)      # Time-aware memory organization
        }
        
        client.create_collection(
            collection_name=target_collection,
            vectors_config=vectors_config
        )
        print("✅ Created 7D collection with named vectors")
        
        # Migrate Gabriel's memories with enhanced vectors
        print(f"\n🔄 Migrating {gabriel_count} Gabriel memories...")
        
        migrated_count = 0
        batch_size = 50
        
        for i in range(0, gabriel_count, batch_size):
            batch = gabriel_memories[0][i:i + batch_size]
            points_to_upsert = []
            
            for memory in batch:
                try:
                    payload = memory.payload
                    
                    # CRITICAL: Verify this is Gabriel's memory
                    if payload.get("bot_name") != "gabriel":
                        print(f"⚠️  Skipping non-Gabriel memory: {payload.get('bot_name')}")
                        continue
                    
                    # Extract content for vector generation
                    content = payload.get("content", "")
                    if not content:
                        print(f"⚠️  Skipping memory without content")
                        continue
                    
                    # Generate enhanced 7D vectors
                    content_embedding = list(embedder.embed([content]))[0]
                    
                    # Create enhanced vectors based on Gabriel's character
                    vectors = {
                        "content": content_embedding,  # Main semantic content
                        "emotion": content_embedding,  # Emotional context (reuse for now)
                        "semantic": content_embedding, # Concept/personality context
                        "relationship": content_embedding, # Social connections
                        "personality": content_embedding,  # Gabriel's gentleman traits
                        "interaction": content_embedding,  # Communication patterns
                        "temporal": content_embedding     # Time-aware memory organization
                    }
                    
                    # Create new point with 7D vectors
                    point = PointStruct(
                        id=memory.id,
                        vector=vectors,
                        payload=payload
                    )
                    
                    points_to_upsert.append(point)
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"❌ Error processing memory {memory.id}: {e}")
                    continue
            
            # Batch upsert
            if points_to_upsert:
                client.upsert(
                    collection_name=target_collection,
                    points=points_to_upsert
                )
                print(f"   Migrated batch: {len(points_to_upsert)} memories")
            
            await asyncio.sleep(0.1)  # Rate limiting
        
        print(f"\n✅ Migration Complete!")
        print(f"   Migrated: {migrated_count} Gabriel memories")
        
        # Verify migration
        target_info = client.get_collection(target_collection)
        print(f"   Target collection now has: {target_info.points_count} points")
        
        if target_info.points_count == migrated_count:
            print("🎉 Gabriel 7D migration SUCCESSFUL!")
            return True
        else:
            print("⚠️  Point count mismatch - verify migration")
            return False
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main migration function"""
    success = await migrate_gabriel_memories()
    
    if success:
        print("\n🎉 Gabriel is ready for 7D validation!")
        print("Next: Update .env.gabriel and restart Gabriel bot")
    else:
        print("\n❌ Migration failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())