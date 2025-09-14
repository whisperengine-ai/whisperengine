#!/usr/bin/env python3
"""
Simple Local Database Test
Quick test to verify the core local database components are working.
"""

import asyncio
import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.adaptive_config import AdaptiveConfigManager
from src.memory.enhanced_local_vector_storage import EnhancedLocalVectorStorage
from src.graph_database.local_graph_storage import LocalGraphStorage

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_vector_storage():
    """Test vector storage basic functionality"""
    logger.info("🔍 Testing Vector Storage...")
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="vector_test_"))
    
    try:
        # Initialize vector storage
        vector_storage = EnhancedLocalVectorStorage(storage_dir=temp_dir, embedding_dim=384)
        
        # Create collection
        result = vector_storage.create_collection("test_collection", {"description": "Test"})
        assert result['created'], "Failed to create collection"
        logger.info("✅ Collection created")
        
        # Add documents
        docs = [
            {"content": "Hello world", "metadata": {"type": "greeting"}},
            {"content": "Goodbye world", "metadata": {"type": "farewell"}},
            {"content": "Python programming", "metadata": {"type": "tech"}}
        ]
        
        # Generate embeddings
        embeddings = [vector_storage._generate_placeholder_embedding(doc["content"]) for doc in docs]
        
        add_result = vector_storage.add_documents("test_collection", docs, embeddings)
        assert add_result['added_count'] == 3, f"Expected 3, got {add_result['added_count']}"
        logger.info("✅ Documents added")
        
        # Test search
        query_embedding = vector_storage._generate_placeholder_embedding("Hello there")
        search_results = vector_storage.query("test_collection", query_embedding, n_results=2)
        
        assert search_results['documents'], "No search results"
        assert len(search_results['documents'][0]) == 2, "Wrong number of results"
        logger.info("✅ Search working")
        
        # Test stats
        stats = vector_storage.get_stats()
        assert stats['total_documents'] == 3, "Wrong document count in stats"
        logger.info("✅ Stats working")
        
        logger.info("🎉 Vector Storage: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector Storage Error: {e}")
        return False
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


async def test_graph_storage():
    """Test graph storage basic functionality"""
    logger.info("🕸️ Testing Graph Storage...")
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="graph_test_"))
    
    try:
        # Initialize graph storage
        graph_storage = LocalGraphStorage(db_path=temp_dir / "test_graph.db")
        await graph_storage.connect()
        
        # Create user
        user_result = await graph_storage.create_or_update_user(
            user_id="test_user",
            discord_id="123456789",
            username="testuser"
        )
        assert user_result['created'], "Failed to create user"
        logger.info("✅ User created")
        
        # Create topic
        topic_result = await graph_storage.create_or_update_topic(
            topic_id="test_topic",
            name="Test Topic",
            description="A test topic"
        )
        assert topic_result['created'], "Failed to create topic"
        logger.info("✅ Topic created")
        
        # Create memory with relationships
        memory_result = await graph_storage.create_memory_with_relationships(
            memory_id="test_memory",
            user_id="test_user",
            content="This is a test memory",
            topics=["test_topic"]
        )
        assert memory_result['memory_id'] == "test_memory", "Failed to create memory"
        logger.info("✅ Memory with relationships created")
        
        # Test user context
        context = await graph_storage.get_user_relationship_context("test_user")
        assert context['user_id'] == "test_user", "Failed to get user context"
        assert context['total_memories'] >= 1, "No memories in context"
        logger.info("✅ User context working")
        
        # Test health check
        health = await graph_storage.health_check()
        assert health['status'] == 'healthy', "Graph storage not healthy"
        logger.info("✅ Health check working")
        
        await graph_storage.disconnect()
        logger.info("🎉 Graph Storage: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Graph Storage Error: {e}")
        return False
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


async def test_desktop_app_integration():
    """Test desktop app integration"""
    logger.info("🖥️ Testing Desktop App Integration...")
    
    try:
        # Override environment
        os.environ['WHISPERENGINE_DATABASE_TYPE'] = 'sqlite'
        os.environ['WHISPERENGINE_MODE'] = 'desktop'
        
        # Test config manager
        config_manager = AdaptiveConfigManager()
        deployment_info = config_manager.get_deployment_info()
        assert deployment_info['platform'], "No platform detected"
        logger.info(f"✅ Config manager working - Platform: {deployment_info['platform']}")
        
        logger.info("🎉 Desktop Integration: BASIC TESTS PASSED")
        return True
        
    except Exception as e:
        logger.error(f"❌ Desktop Integration Error: {e}")
        return False


async def main():
    """Run all simple tests"""
    logger.info("🚀 Starting Simple Local Database Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Vector Storage", test_vector_storage),
        ("Graph Storage", test_graph_storage),
        ("Desktop Integration", test_desktop_app_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} Test...")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} | {test_name}")
        if success:
            passed += 1
    
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    logger.info(f"\n📈 Success Rate: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed == total:
        logger.info("🎉 ALL CORE TESTS PASSED!")
        logger.info("✅ Local database replacements are working correctly")
        logger.info("✅ Ready for desktop app integration")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✅ Local database components are ready!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)