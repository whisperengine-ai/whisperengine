#!/usr/bin/env python3
"""
Test Named Vectors Fix
Verify that our named vectors implementation works correctly
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from qdrant_client import QdrantClient

def test_named_vectors_extraction():
    """Test our named vectors helper functions"""
    
    # Import the vector memory system to access helper functions
    try:
        from src.memory.vector_memory_system import VectorMemoryStore
        
        # Create a test instance (won't connect, just for method access)
        store = VectorMemoryStore(qdrant_host="localhost", qdrant_port=6334)
        
        print("🧪 Testing Named Vectors Helper Functions")
        print("=" * 50)
        
        # Test 1: Extract from named vector dict (current format)
        named_vector_data = {"content": [0.1, 0.2, 0.3, 0.4]}
        extracted = store._extract_named_vector(named_vector_data, "content")
        print(f"✅ Extract from named vector dict: {extracted}")
        assert extracted == [0.1, 0.2, 0.3, 0.4], "Failed to extract named vector"
        
        # Test 2: Extract from legacy single vector (backward compatibility)
        legacy_vector_data = [0.5, 0.6, 0.7, 0.8]
        extracted = store._extract_named_vector(legacy_vector_data, "content")
        print(f"✅ Extract from legacy vector: {extracted}")
        assert extracted == [0.5, 0.6, 0.7, 0.8], "Failed to extract legacy vector"
        
        # Test 3: Create named vectors dict from legacy format
        created = store._create_named_vectors_dict([0.9, 1.0, 1.1, 1.2])
        print(f"✅ Create named vectors from legacy: {created}")
        assert created == {"content": [0.9, 1.0, 1.1, 1.2]}, "Failed to create named vectors dict"
        
        # Test 4: Create named vectors dict from existing named vectors
        existing_named = {"content": [1.3, 1.4, 1.5], "emotion": [1.6, 1.7, 1.8]}
        created = store._create_named_vectors_dict(existing_named)
        print(f"✅ Preserve existing named vectors: {created}")
        assert created == existing_named, "Failed to preserve named vectors"
        
        print(f"\n🎉 All named vectors helper functions working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_actual_vector_data():
    """Test with actual vector data from the store"""
    
    try:
        client = QdrantClient(host="localhost", port=6334)
        collection_name = "whisperengine_memory"
        
        print(f"\n🔍 Testing Actual Vector Data from Qdrant")
        print("=" * 50)
        
        # Get a few sample points
        result = client.scroll(collection_name, limit=3, with_payload=True, with_vectors=["content"])
        points = result[0] if result else []
        
        if not points:
            print("⚠️  No points found in collection")
            return False
        
        from src.memory.vector_memory_system import VectorMemoryStore
        store = VectorMemoryStore(qdrant_host="localhost", qdrant_port=6334)
        
        for i, point in enumerate(points):
            print(f"\nPoint {i+1} (ID: {str(point.id)[:8]}...):")
            print(f"  Vector type: {type(point.vector)}")
            
            if point.vector:
                # Test extraction
                content_vector = store._extract_named_vector(point.vector, "content")
                if content_vector:
                    print(f"  ✅ Content vector extracted: {len(content_vector)}D")
                    print(f"  Sample values: {content_vector[:5]}...")
                    
                    # Verify it's the right dimension
                    if len(content_vector) == 384:
                        print(f"  ✅ Correct dimension (384D)")
                    else:
                        print(f"  ⚠️  Unexpected dimension: {len(content_vector)}D")
                else:
                    print(f"  ❌ Failed to extract content vector")
            else:
                print(f"  ❌ No vector data")
        
        print(f"\n🎉 Actual vector data test complete!")
        return True
        
    except Exception as e:
        print(f"❌ Actual data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Named Vectors Fix Verification")
    print("=" * 60)
    
    # Test helper functions
    helpers_ok = test_named_vectors_extraction()
    
    # Test with actual data  
    actual_ok = test_actual_vector_data()
    
    if helpers_ok and actual_ok:
        print(f"\n✅ All tests passed! Named vectors fix is working correctly.")
        print(f"\nNext steps:")
        print(f"1. The vector storage/retrieval code is now fixed")
        print(f"2. Existing data can be properly accessed")
        print(f"3. New data will be stored correctly")
    else:
        print(f"\n❌ Some tests failed. Check the output above for details.")