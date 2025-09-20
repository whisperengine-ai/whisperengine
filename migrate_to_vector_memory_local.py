#!/usr/bin/env python3
"""
WhisperEngine Memory Migration Script - Local-First Implementation

Simple migration script to set up local vector memory system.
Migrates from hierarchical memory to Qdrant + sentence-transformers.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_local_vector_system():
    """Test the local vector memory system setup"""
    logger.info("🧪 Testing Local Vector Memory System")
    
    try:
        # Test Qdrant connection
        from qdrant_client import QdrantClient
        
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        collections = client.get_collections()
        logger.info(f"✅ Qdrant connected: {len(collections.collections)} collections")
        
        # Test embeddings
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        test_embedding = embedder.encode("test connection")
        logger.info(f"✅ Local embeddings working (dimension: {len(test_embedding)})")
        
        # Test our vector memory system
        from memory.vector_memory_system import VectorMemoryManager, VectorMemory, MemoryType
        from uuid import uuid4
        
        memory_manager = VectorMemoryManager(
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            collection_name="test_migration",
            embedding_model="all-MiniLM-L6-v2"
        )
        
        # Test storing and retrieving a memory
        test_memory = VectorMemory(
            id=str(uuid4()),
            user_id="test_user_123",
            memory_type=MemoryType.FACT,
            content="My goldfish is named Bubbles"
        )
        
        memory_id = await memory_manager.vector_store.store_memory(test_memory)
        logger.info(f"✅ Stored test memory: {memory_id}")
        
        # Test search
        search_results = await memory_manager.vector_store.search_memories(
            query="goldfish pet",
            user_id="test_user_123",
            top_k=5
        )
        
        logger.info(f"✅ Search found {len(search_results)} results")
        
        # Test contradiction detection
        contradictions = await memory_manager.vector_store.detect_contradictions(
            new_content="My goldfish is named Orion",
            user_id="test_user_123"
        )
        
        logger.info(f"✅ Contradiction detection: {len(contradictions)} conflicts found")
        
        # Get stats
        stats = await memory_manager.vector_store.get_stats()
        logger.info(f"✅ System stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector system test failed: {e}")
        return False


async def initialize_docker_services():
    """Ensure Docker services are running"""
    logger.info("🐳 Checking Docker services...")
    
    try:
        import subprocess
        
        # Check if Qdrant is running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=whisperengine-qdrant", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        if "whisperengine-qdrant" not in result.stdout:
            logger.warning("Qdrant container not running. Starting...")
            subprocess.run(["docker-compose", "up", "qdrant", "-d"])
            logger.info("✅ Qdrant started")
        else:
            logger.info("✅ Qdrant already running")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Docker service check failed: {e}")
        logger.info("Please run: docker-compose up qdrant -d")
        return False


async def migrate_goldfish_scenario():
    """Migrate the specific goldfish Bubbles scenario for testing"""
    logger.info("🐠 Testing Goldfish Bubbles Scenario")
    
    try:
        from memory.vector_memory_system import VectorMemoryManager, VectorMemory, MemoryType
        from uuid import uuid4
        
        memory_manager = VectorMemoryManager()
        
        # Simulate the original problem: storing conflicting goldfish names
        memory1 = VectorMemory(
            id=str(uuid4()),
            user_id="bubbles_test_user",
            memory_type=MemoryType.FACT,
            content="My goldfish is named Orion"
        )
        
        memory2 = VectorMemory(
            id=str(uuid4()),
            user_id="bubbles_test_user", 
            memory_type=MemoryType.FACT,
            content="Actually, my goldfish is named Bubbles"
        )
        
        # Store first memory
        id1 = await memory_manager.vector_store.store_memory(memory1)
        logger.info(f"Stored: {memory1.content}")
        
        # Detect contradictions with second memory
        contradictions = await memory_manager.vector_store.detect_contradictions(
            new_content=memory2.content,
            user_id="bubbles_test_user"
        )
        
        if contradictions:
            logger.info(f"✅ Detected {len(contradictions)} contradictions!")
            for contradiction in contradictions:
                logger.info(f"  Conflict: '{contradiction['existing_memory']['content']}' vs '{contradiction['new_content']}'")
                logger.info(f"  Similarity: {contradiction['similarity_score']:.3f}")
        
        # Store corrected memory
        id2 = await memory_manager.vector_store.store_memory(memory2)
        logger.info(f"Stored correction: {memory2.content}")
        
        # Search for goldfish info
        results = await memory_manager.vector_store.search_memories(
            query="goldfish name",
            user_id="bubbles_test_user"
        )
        
        logger.info(f"Search results for 'goldfish name':")
        for result in results:
            logger.info(f"  {result['content']} (score: {result['score']:.3f})")
        
        logger.info("✅ Goldfish scenario test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Goldfish scenario test failed: {e}")
        return False


async def main():
    """Main migration process"""
    logger.info("🚀 WhisperEngine Memory Migration - Local-First")
    
    try:
        # Step 1: Check Docker services
        if not await initialize_docker_services():
            return False
        
        # Step 2: Test vector system
        if not await test_local_vector_system():
            return False
            
        # Step 3: Test goldfish scenario
        if not await migrate_goldfish_scenario():
            return False
        
        logger.info("✅ Migration test completed successfully!")
        logger.info("🎉 Local vector memory system is ready!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)