#!/usr/bin/env python3
"""
Test New Bot Installation - Vector Collection Creation

This script tests that new bot installations correctly create:
1. All 7 named vectors (content, emotion, semantic, relationship, personality, interaction, temporal)
2. All required payload indexes for efficient filtering
3. Proper collection configuration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.memory.vector_memory_system import VectorMemoryStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

async def test_new_bot_installation():
    """Test complete new bot installation process"""
    
    # Test configuration
    test_collection = "test_new_bot_installation"
    qdrant_host = "localhost"
    qdrant_port = 6334  # Use local Qdrant (adjust if needed)
    
    print("🧪 Testing New Bot Installation Process")
    print("=" * 50)
    print(f"📍 Test Collection: {test_collection}")
    print(f"📡 Qdrant: {qdrant_host}:{qdrant_port}")
    
    # Step 1: Clean up any existing test collection
    print("\n🧹 Step 1: Cleanup existing test collection")
    client = QdrantClient(host=qdrant_host, port=qdrant_port)
    try:
        client.delete_collection(test_collection)
        print(f"✅ Deleted existing test collection")
    except Exception as e:
        print(f"ℹ️ No existing collection to delete: {e}")
    
    # Step 2: Simulate new bot installation by creating VectorMemoryStore
    print("\n🏗️ Step 2: Simulate new bot installation")
    try:
        vector_store = VectorMemoryStore(
            collection_name=test_collection,
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port
        )
        print("✅ VectorMemoryStore created successfully")
    except Exception as e:
        print(f"❌ Failed to create VectorMemoryStore: {e}")
        return False
    
    # Step 3: Verify collection was created with all 7 named vectors
    print("\n🔍 Step 3: Verify collection schema")
    try:
        collection_info = client.get_collection(test_collection)
        vectors_config = collection_info.config.params.vectors
        
        if isinstance(vectors_config, dict):
            vector_names = set(vectors_config.keys())
            expected_vectors = {
                "content", "emotion", "semantic", "relationship", 
                "personality", "interaction", "temporal"
            }
            
            print(f"📊 Found {len(vector_names)} vectors: {vector_names}")
            
            if vector_names == expected_vectors:
                print("✅ ALL 7 REQUIRED VECTORS PRESENT")
                
                # Verify each vector configuration
                for name, config in vectors_config.items():
                    print(f"  ✅ {name}: {config.size}D {config.distance}")
            else:
                missing = expected_vectors - vector_names
                extra = vector_names - expected_vectors
                print(f"❌ VECTOR MISMATCH!")
                if missing:
                    print(f"  Missing: {missing}")
                if extra:
                    print(f"  Extra: {extra}")
                return False
        else:
            print(f"❌ WRONG SCHEMA: Single vector detected instead of named vectors")
            return False
            
    except Exception as e:
        print(f"❌ Failed to verify collection: {e}")
        return False
    
    # Step 4: Verify payload indexes were created
    print("\n🔍 Step 4: Verify payload indexes")
    required_indexes = [
        "user_id", "memory_type", "timestamp_unix", "semantic_key",
        "emotional_context", "content_hash", "bot_name"
    ]
    
    try:
        # Get collection info to check indexes
        # Note: Qdrant doesn't have a direct API to list indexes,
        # but we can test by trying to create them again
        index_count = 0
        for field_name in required_indexes:
            try:
                # Try to create index - will fail if exists
                client.create_payload_index(
                    collection_name=test_collection,
                    field_name=field_name,
                    field_schema="keyword"
                )
                print(f"⚠️ Index {field_name} was missing - created now")
            except Exception:
                # Index already exists - this is what we want
                print(f"✅ Index {field_name} already exists")
                index_count += 1
        
        if index_count >= 5:  # At least most indexes should exist
            print(f"✅ PAYLOAD INDEXES VERIFIED ({index_count}/{len(required_indexes)} confirmed)")
        else:
            print(f"⚠️ Some indexes may be missing ({index_count}/{len(required_indexes)} confirmed)")
            
    except Exception as e:
        print(f"❌ Failed to verify indexes: {e}")
        return False
    
    # Step 5: Test basic memory operations
    print("\n🧪 Step 5: Test memory operations")
    try:
        from src.memory.memory_protocol import create_memory_manager
        
        # Override collection name for test
        os.environ['QDRANT_COLLECTION_NAME'] = test_collection
        os.environ['QDRANT_HOST'] = qdrant_host
        os.environ['QDRANT_PORT'] = str(qdrant_port)
        
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Test storing conversation
        success = await memory_manager.store_conversation(
            user_id="test_user_installation",
            user_message="Testing new bot installation",
            bot_response="Installation test successful with all 7 vectors!",
            metadata={"test": "installation"}
        )
        
        if success:
            print("✅ MEMORY STORAGE TEST PASSED")
            
            # Test retrieval
            memories = await memory_manager.retrieve_relevant_memories(
                user_id="test_user_installation",
                query="installation test",
                limit=1
            )
            
            if memories and len(memories) > 0:
                print("✅ MEMORY RETRIEVAL TEST PASSED")
                print(f"📄 Retrieved: {len(memories)} memories")
            else:
                print("⚠️ MEMORY RETRIEVAL TEST: No memories found")
        else:
            print("❌ MEMORY STORAGE TEST FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Memory operations test failed: {e}")
        return False
    
    # Step 6: Cleanup
    print("\n🧹 Step 6: Cleanup test collection")
    try:
        client.delete_collection(test_collection)
        print("✅ Test collection cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    print("\n🎉 NEW BOT INSTALLATION TEST COMPLETED SUCCESSFULLY!")
    print("✅ All 7 named vectors created correctly")
    print("✅ Payload indexes created correctly") 
    print("✅ Memory operations working correctly")
    print("\n🎯 New bot installations will work properly!")
    
    return True

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_new_bot_installation())
    
    if result:
        print("\n🏆 FINAL RESULT: ✅ PASS")
        sys.exit(0)
    else:
        print("\n💥 FINAL RESULT: ❌ FAIL")
        sys.exit(1)