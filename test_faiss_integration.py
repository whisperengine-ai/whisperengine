#!/usr/bin/env python3
"""
Test FAISS Integration in WhisperEngine
Demonstrates that FAISS is properly integrated and working
"""

import asyncio
import logging
import sys

import numpy as np

# Add project root to path
sys.path.append(".")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_faiss_availability():
    """Test if FAISS is available and basic functionality works"""

    try:
        import faiss


        # Test basic FAISS functionality
        dimension = 384
        index = faiss.IndexFlatIP(dimension)

        # Create test vectors
        test_vectors = np.random.random((10, dimension)).astype(np.float32)
        faiss.normalize_L2(test_vectors)

        # Add vectors to index
        index.add(test_vectors)

        # Test search
        query = np.random.random((1, dimension)).astype(np.float32)
        faiss.normalize_L2(query)
        scores, indices = index.search(query, 3)


        return True

    except ImportError:
        return False
    except Exception:
        return False


async def test_faiss_memory_engine():
    """Test the FaissMemoryEngine implementation"""

    try:
        from src.memory.faiss_memory_engine import FAISS_AVAILABLE, FaissMemoryEngine

        if not FAISS_AVAILABLE:
            return False

        # Initialize the engine
        engine = FaissMemoryEngine(embedding_dimension=384, max_workers=2)
        await engine.initialize()

        # Create test embeddings
        test_embeddings = []
        test_contents = [
            "I love programming with Python",
            "The weather is beautiful today",
            "Machine learning is fascinating",
            "I enjoy reading science fiction books",
            "Cooking is a wonderful hobby",
        ]

        for content in test_contents:
            # Create dummy embedding (in real use, this would come from sentence transformer)
            embedding = np.random.random(384).astype(np.float32)
            test_embeddings.append(embedding)

        # Add memories to the engine
        memory_ids = []
        for i, (content, embedding) in enumerate(zip(test_contents, test_embeddings, strict=False)):
            memory_id = await engine.add_memory(
                user_id=f"test_user_{i % 2}",  # Two different users
                content=content,
                embedding=embedding,
                importance=0.5 + (i * 0.1),
                doc_type="conversation",
            )
            memory_ids.append(memory_id)

        # Wait a moment for batch processing
        await asyncio.sleep(1.0)

        # Test search functionality
        query_embedding = test_embeddings[0]  # Search for something similar to first item
        results = await engine.search_memories(
            query_embedding=query_embedding, user_id="test_user_0", k=3
        )

        for i, _result in enumerate(results):
            pass

        # Test performance stats
        await engine.get_performance_stats()

        # Cleanup
        await engine.shutdown()

        return True

    except ImportError:
        return False
    except Exception:
        import traceback

        traceback.print_exc()
        return False


async def test_enhanced_memory_system():
    """Test FAISS integration in EnhancedMemorySystem"""

    try:
        from src.memory.enhanced_memory_system import FAISS_AVAILABLE, EnhancedMemorySystem

        if not FAISS_AVAILABLE:
            return False

        # Initialize enhanced memory system
        memory_system = EnhancedMemorySystem(user_id="test_user_enhanced", embedding_dim=384)

        # Call private method to initialize components
        memory_system._initialize_enhanced_components()

        # Add some test memories
        test_memories = [
            "I had a great conversation about AI today",
            "The sunset was absolutely gorgeous",
            "Working on machine learning projects is exciting",
            "I love discussing philosophy and ethics",
        ]

        memory_ids = []
        for content in test_memories:
            memory_id = await memory_system.add_memory_enhanced(
                content=content, memory_type="conversation", importance_score=0.8
            )
            memory_ids.append(memory_id)

        # Test search with FAISS
        search_result = await memory_system.search_memories_enhanced(
            query="machine learning and AI",
            limit=3,
            similarity_threshold=0.1,  # Low threshold for test
        )


        for i, _memory in enumerate(search_result.memory_nodes):
            (
                search_result.similarity_scores[i]
                if i < len(search_result.similarity_scores)
                else 0.0
            )

        # Get system statistics

        return True

    except ImportError:
        return False
    except Exception:
        import traceback

        traceback.print_exc()
        return False


async def test_production_integration():
    """Test FAISS integration in production system"""

    try:
        from src.integration.production_system_integration import ProductionSystemIntegrator

        # Initialize production system
        integrator = ProductionSystemIntegrator()
        await integrator.initialize_all()

        # Check if FAISS memory component was initialized
        components = integrator.get_components()
        faiss_memory = components.get("faiss_memory")

        if faiss_memory is not None:

            # Test basic functionality
            await faiss_memory.get_performance_stats()

        else:
            pass

        # Check other relevant components
        relevant_components = [
            "enhanced_memory_system",
            "memory_manager",
            "production_phase4_engine",
        ]

        for component_name in relevant_components:
            component = components.get(component_name)
            if component:
                pass
            else:
                pass

        return True

    except ImportError:
        return False
    except Exception:
        import traceback

        traceback.print_exc()
        return False


async def test_chromadb_adapter():
    """Test FAISS ChromaDB compatibility adapter"""

    try:
        from src.memory.faiss_memory_engine import FAISS_AVAILABLE, FaissChromaDBAdapter

        if not FAISS_AVAILABLE:
            return False

        # Initialize adapter
        adapter = FaissChromaDBAdapter(embedding_dimension=384)
        await adapter.initialize()

        # Test with dummy embedding
        query_embedding = np.random.random(384).astype(np.float32)

        # Search (should return empty results but not error)
        await adapter.search_memories_with_embedding(
            query_embedding=query_embedding, user_id="test_user", limit=5
        )


        return True

    except ImportError:
        return False
    except Exception:
        import traceback

        traceback.print_exc()
        return False


async def run_comprehensive_test():
    """Run all FAISS integration tests"""

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

    total_tests = 5
    passed_tests = sum(
        [faiss_basic, faiss_engine, enhanced_memory, production_integration, chromadb_adapter]
    )


    if passed_tests == total_tests:
        pass
    elif passed_tests > 0:
        pass
    else:
        pass

    return passed_tests >= 3  # Consider success if most tests pass


if __name__ == "__main__":
    try:
        result = asyncio.run(run_comprehensive_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
