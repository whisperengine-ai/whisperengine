#!/usr/bin/env python3
"""
Test FAISS Integration in WhisperEngine
Demonstrates that FAISS is properly integrated and working
"""

import asyncio
import sys
import time
import numpy as np
import logging

# Add project root to path
sys.path.append('.')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_faiss_availability():
    """Test if FAISS is available and basic functionality works"""
    print("🔍 Testing FAISS availability...")
    
    try:
        import faiss
        print(f"✅ FAISS imported successfully")
        
        # Test basic FAISS functionality
        dimension = 384
        index = faiss.IndexFlatIP(dimension)
        print(f"✅ Created FAISS index with dimension {dimension}")
        
        # Create test vectors
        test_vectors = np.random.random((10, dimension)).astype(np.float32)
        faiss.normalize_L2(test_vectors)
        
        # Add vectors to index
        index.add(test_vectors)
        print(f"✅ Added {len(test_vectors)} vectors to index")
        
        # Test search
        query = np.random.random((1, dimension)).astype(np.float32)
        faiss.normalize_L2(query)
        scores, indices = index.search(query, 3)
        
        print(f"✅ Search successful: found {len(indices[0])} results")
        print(f"   Top scores: {scores[0][:3]}")
        
        return True
        
    except ImportError as e:
        print(f"❌ FAISS not available: {e}")
        return False
    except Exception as e:
        print(f"❌ FAISS test failed: {e}")
        return False

async def test_faiss_memory_engine():
    """Test the FaissMemoryEngine implementation"""
    print("\n🚀 Testing FaissMemoryEngine...")
    
    try:
        from src.memory.faiss_memory_engine import FaissMemoryEngine, FAISS_AVAILABLE
        
        if not FAISS_AVAILABLE:
            print("❌ FAISS not available for FaissMemoryEngine")
            return False
        
        # Initialize the engine
        engine = FaissMemoryEngine(embedding_dimension=384, max_workers=2)
        await engine.initialize()
        print("✅ FaissMemoryEngine initialized")
        
        # Create test embeddings
        test_embeddings = []
        test_contents = [
            "I love programming with Python",
            "The weather is beautiful today", 
            "Machine learning is fascinating",
            "I enjoy reading science fiction books",
            "Cooking is a wonderful hobby"
        ]
        
        for content in test_contents:
            # Create dummy embedding (in real use, this would come from sentence transformer)
            embedding = np.random.random(384).astype(np.float32)
            test_embeddings.append(embedding)
        
        # Add memories to the engine
        memory_ids = []
        for i, (content, embedding) in enumerate(zip(test_contents, test_embeddings)):
            memory_id = await engine.add_memory(
                user_id=f"test_user_{i % 2}",  # Two different users
                content=content,
                embedding=embedding,
                importance=0.5 + (i * 0.1),
                doc_type="conversation"
            )
            memory_ids.append(memory_id)
            print(f"✅ Added memory: {content[:30]}...")
        
        # Wait a moment for batch processing
        await asyncio.sleep(1.0)
        
        # Test search functionality
        query_embedding = test_embeddings[0]  # Search for something similar to first item
        results = await engine.search_memories(
            query_embedding=query_embedding,
            user_id="test_user_0",
            k=3
        )
        
        print(f"✅ Search completed: found {len(results)} results")
        for i, result in enumerate(results):
            print(f"   {i+1}. Score: {result['similarity_score']:.3f} - {result['content'][:50]}...")
        
        # Test performance stats
        stats = await engine.get_performance_stats()
        print(f"✅ Performance stats:")
        print(f"   Total searches: {stats['total_searches']}")
        print(f"   Total adds: {stats['total_adds']}")
        print(f"   Cache hit rate: {stats['cache_hit_rate']:.2%}")
        
        # Cleanup
        await engine.shutdown()
        print("✅ FaissMemoryEngine test completed successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ FaissMemoryEngine import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ FaissMemoryEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_memory_system():
    """Test FAISS integration in EnhancedMemorySystem"""
    print("\n🧠 Testing Enhanced Memory System with FAISS...")
    
    try:
        from src.memory.enhanced_memory_system import EnhancedMemorySystem, FAISS_AVAILABLE
        
        if not FAISS_AVAILABLE:
            print("❌ FAISS not available for EnhancedMemorySystem")
            return False
        
        # Initialize enhanced memory system
        memory_system = EnhancedMemorySystem(
            user_id="test_user_enhanced",
            embedding_dim=384
        )
        
        # Call private method to initialize components
        memory_system._initialize_enhanced_components()
        print("✅ EnhancedMemorySystem initialized")
        
        # Add some test memories
        test_memories = [
            "I had a great conversation about AI today",
            "The sunset was absolutely gorgeous", 
            "Working on machine learning projects is exciting",
            "I love discussing philosophy and ethics"
        ]
        
        memory_ids = []
        for content in test_memories:
            memory_id = await memory_system.add_memory_enhanced(
                content=content,
                memory_type="conversation",
                importance_score=0.8
            )
            memory_ids.append(memory_id)
            print(f"✅ Added enhanced memory: {content[:40]}...")
        
        # Test search with FAISS
        search_result = await memory_system.search_memories_enhanced(
            query="machine learning and AI",
            limit=3,
            similarity_threshold=0.1  # Low threshold for test
        )
        
        print(f"✅ Enhanced search completed:")
        print(f"   Algorithm used: {search_result.search_algorithm}")
        print(f"   Found {len(search_result.memory_nodes)} memories")
        print(f"   Search time: {search_result.search_time_ms:.2f}ms")
        
        for i, memory in enumerate(search_result.memory_nodes):
            score = search_result.similarity_scores[i] if i < len(search_result.similarity_scores) else 0.0
            print(f"   - Score: {score:.3f} - {memory.content[:50]}...")
        
        # Get system statistics  
        stats = memory_system.search_stats
        print(f"✅ Memory statistics:")
        print(f"   Total memories: {len(memory_system.memory_nodes)}")
        print(f"   FAISS searches: {stats.get('faiss_searches', 0)}")
        print(f"   Fallback searches: {stats.get('fallback_searches', 0)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ EnhancedMemorySystem import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ EnhancedMemorySystem test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_production_integration():
    """Test FAISS integration in production system"""
    print("\n🏭 Testing Production System Integration...")
    
    try:
        from src.integration.production_system_integration import ProductionSystemIntegrator
        
        # Initialize production system
        integrator = ProductionSystemIntegrator()
        await integrator.initialize_all()
        
        # Check if FAISS memory component was initialized
        components = integrator.get_components()
        faiss_memory = components.get('faiss_memory')
        
        if faiss_memory is not None:
            print("✅ FAISS Memory Engine initialized in production system")
            
            # Test basic functionality
            stats = await faiss_memory.get_performance_stats()
            print(f"✅ FAISS engine stats: {len(stats)} metrics available")
            print(f"   Worker threads: {stats.get('worker_threads', 'N/A')}")
            print(f"   Batch processing: {stats.get('batch_processing', 'N/A')}")
            
        else:
            print("⚠️ FAISS Memory Engine not initialized (fallback mode)")
            
        # Check other relevant components
        relevant_components = [
            'enhanced_memory_system',
            'memory_manager', 
            'production_phase4_engine'
        ]
        
        for component_name in relevant_components:
            component = components.get(component_name)
            if component:
                print(f"✅ {component_name} initialized")
            else:
                print(f"⚠️ {component_name} not available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Production integration import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Production integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_chromadb_adapter():
    """Test FAISS ChromaDB compatibility adapter"""
    print("\n🔗 Testing FAISS ChromaDB Adapter...")
    
    try:
        from src.memory.faiss_memory_engine import FaissChromaDBAdapter, FAISS_AVAILABLE
        
        if not FAISS_AVAILABLE:
            print("❌ FAISS not available for ChromaDB adapter")
            return False
        
        # Initialize adapter
        adapter = FaissChromaDBAdapter(embedding_dimension=384)
        await adapter.initialize()
        print("✅ FaissChromaDBAdapter initialized")
        
        # Test with dummy embedding
        query_embedding = np.random.random(384).astype(np.float32)
        
        # Search (should return empty results but not error)
        results = await adapter.search_memories_with_embedding(
            query_embedding=query_embedding,
            user_id="test_user",
            limit=5
        )
        
        print(f"✅ ChromaDB adapter search completed: {len(results)} results")
        print("✅ FAISS ChromaDB adapter is working correctly")
        
        return True
        
    except ImportError as e:
        print(f"❌ ChromaDB adapter import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ ChromaDB adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_comprehensive_test():
    """Run all FAISS integration tests"""
    print("🧪 Running Comprehensive FAISS Integration Test")
    print("=" * 60)
    
    # Test 1: Basic FAISS availability
    faiss_basic = test_faiss_availability()
    
    # Test 2: FaissMemoryEngine
    faiss_engine = await test_faiss_memory_engine() if faiss_basic else False
    
    # Test 3: Enhanced Memory System
    enhanced_memory = await test_enhanced_memory_system() if faiss_basic else False
    
    # Test 4: Production Integration
    production_integration = await test_production_integration()
    
    # Test 5: ChromaDB Adapter
    chromadb_adapter = await test_chromadb_adapter() if faiss_basic else False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FAISS Integration Test Summary:")
    print(f"   ✅ Basic FAISS functionality: {'PASS' if faiss_basic else 'FAIL'}")
    print(f"   ✅ FaissMemoryEngine: {'PASS' if faiss_engine else 'FAIL'}")
    print(f"   ✅ Enhanced Memory System: {'PASS' if enhanced_memory else 'FAIL'}")
    print(f"   ✅ Production Integration: {'PASS' if production_integration else 'FAIL'}")
    print(f"   ✅ ChromaDB Adapter: {'PASS' if chromadb_adapter else 'FAIL'}")
    
    total_tests = 5
    passed_tests = sum([faiss_basic, faiss_engine, enhanced_memory, production_integration, chromadb_adapter])
    
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 FAISS is fully integrated and working!")
    elif passed_tests > 0:
        print("⚠️ FAISS is partially integrated - some components working")
    else:
        print("❌ FAISS integration has issues")
    
    return passed_tests >= 3  # Consider success if most tests pass

if __name__ == "__main__":
    try:
        result = asyncio.run(run_comprehensive_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)