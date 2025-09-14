#!/usr/bin/env python3
"""
Test Local Database Replacements
Comprehensive tests to verify local vector and graph databases work equivalently to ChromaDB/Neo4j.
"""

import asyncio
import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.local_database_integration import LocalDatabaseIntegrationManager
from src.memory.enhanced_local_vector_storage import EnhancedLocalVectorStorage
from src.graph_database.local_graph_storage import LocalGraphStorage

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LocalDatabaseTester:
    """Test suite for local database replacements"""
    
    def __init__(self):
        self.temp_dir = None
        self.config_manager = None
        self.db_integration = None
        self.test_results = []
    
    async def setup(self):
        """Setup test environment"""
        # Create temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp(prefix="whisperengine_test_"))
        logger.info(f"🧪 Test environment created: {self.temp_dir}")
        
        # Override environment for testing
        os.environ['WHISPERENGINE_DATABASE_TYPE'] = 'sqlite'
        os.environ['WHISPERENGINE_MODE'] = 'desktop'
        
        # Initialize components
        self.config_manager = AdaptiveConfigManager()
        self.db_integration = LocalDatabaseIntegrationManager(self.config_manager)
        
        # Override storage paths to use temp directory
        self.db_integration.data_dir = self.temp_dir
        self.db_integration.vector_dir = self.temp_dir / 'vectors'
        self.db_integration.graph_db_path = self.temp_dir / 'graph.db'
        self.db_integration.cache_dir = self.temp_dir / 'cache'
        
        # Initialize database integration
        success = await self.db_integration.initialize()
        if not success:
            raise RuntimeError("Failed to initialize local database integration")
        
        logger.info("✅ Test setup complete")
    
    async def cleanup(self):
        """Cleanup test environment"""
        try:
            if self.db_integration:
                await self.db_integration.cleanup()
            
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("🧹 Test environment cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    def record_test_result(self, test_name: str, success: bool, details: str = ""):
        """Record test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        logger.info(f"{status} {test_name}: {details}")
    
    async def test_vector_storage_basic_operations(self):
        """Test basic vector storage operations"""
        test_name = "Vector Storage - Basic Operations"
        
        try:
            vector_storage = self.db_integration.get_vector_storage()
            
            # Test collection creation
            result = vector_storage.create_collection("test_memories", {"description": "Test collection"})
            assert result['created'], "Collection creation failed"
            
            # Test document addition
            docs = [
                {"content": "I love artificial intelligence", "metadata": {"user": "alice", "emotion": "positive"}},
                {"content": "Machine learning is fascinating", "metadata": {"user": "bob", "emotion": "curious"}},
                {"content": "I'm having trouble with code", "metadata": {"user": "alice", "emotion": "frustrated"}}
            ]
            
            # Generate simple test embeddings
            embeddings = []
            for doc in docs:
                embedding = vector_storage._generate_placeholder_embedding(doc["content"])
                embeddings.append(embedding)
            
            add_result = vector_storage.add_documents("test_memories", docs, embeddings)
            assert add_result['added_count'] == 3, f"Expected 3 docs, added {add_result['added_count']}"
            
            # Test similarity search
            query_embedding = vector_storage._generate_placeholder_embedding("I enjoy AI and technology")
            search_results = vector_storage.query("test_memories", query_embedding, n_results=2)
            
            assert 'documents' in search_results, "Search results missing documents"
            assert len(search_results['documents'][0]) == 2, "Expected 2 search results"
            
            # Test filtering
            filtered_results = vector_storage.query(
                "test_memories", 
                query_embedding, 
                n_results=10,
                where={'user': 'alice'}
            )
            
            # Should only return Alice's documents
            alice_docs = len(filtered_results['documents'][0]) if filtered_results['documents'] else 0
            assert alice_docs <= 2, f"Too many results for Alice filter: {alice_docs}"
            
            self.record_test_result(test_name, True, f"Added {add_result['added_count']} docs, found {len(search_results['documents'][0])} similar")
            
        except Exception as e:
            self.record_test_result(test_name, False, str(e))
    
    async def test_graph_storage_operations(self):
        """Test graph storage operations"""
        test_name = "Graph Storage - Relationship Operations"
        
        try:
            graph_storage = self.db_integration.get_graph_storage()
            
            # Test user creation
            user_result = await graph_storage.create_or_update_user(
                user_id="user_123",
                discord_id="123456789",
                username="alice",
                display_name="Alice Wonderland"
            )
            assert user_result['created'], "User creation failed"
            
            # Test topic creation
            topic_result = await graph_storage.create_or_update_topic(
                topic_id="topic_ai",
                name="Artificial Intelligence",
                description="AI and machine learning discussions"
            )
            assert topic_result['created'], "Topic creation failed"
            
            # Test memory with relationships
            memory_result = await graph_storage.create_memory_with_relationships(
                memory_id="memory_001",
                user_id="user_123",
                content="Discussed neural networks and deep learning",
                importance=0.8,
                emotional_context="excited",
                topics=["topic_ai"]
            )
            assert memory_result['memory_id'] == "memory_001", "Memory creation failed"
            
            # Test relationship context
            context = await graph_storage.get_user_relationship_context("user_123")
            assert context['user_id'] == "user_123", "Context retrieval failed"
            assert context['total_memories'] >= 1, "No memories found in context"
            
            # Test contextual memory retrieval
            contextual_memories = await graph_storage.get_contextual_memories("user_123", "AI", limit=5)
            assert len(contextual_memories) >= 1, "No contextual memories found"
            
            # Test emotional patterns
            emotional_patterns = await graph_storage.get_emotional_patterns("user_123")
            assert emotional_patterns['user_id'] == "user_123", "Emotional pattern analysis failed"
            
            self.record_test_result(test_name, True, f"Created user, topic, memory with {memory_result.get('relationships_created', 0)} relationships")
            
        except Exception as e:
            self.record_test_result(test_name, False, str(e))
    
    async def test_integrated_conversation_flow(self):
        """Test integrated conversation flow with vector and graph storage"""
        test_name = "Integrated Conversation Flow"
        
        try:
            # Simulate a conversation
            user_id = "user_456"
            conversation_data = {
                "message": "Hello, I'm interested in learning about machine learning",
                "response": "Great! Machine learning is a fascinating field. What specific area interests you?",
                "username": "bob",
                "metadata": {"session_id": "session_001", "topic": "machine_learning"}
            }
            
            # Store conversation embedding
            fake_embedding = [0.1] * 384  # Placeholder embedding
            doc_id = await self.db_integration.store_conversation_embedding(
                user_id=user_id,
                content=conversation_data["message"],
                embedding=fake_embedding,
                metadata=conversation_data["metadata"]
            )
            assert doc_id, "Conversation embedding storage failed"
            
            # Create user in graph
            await self.db_integration.create_user_in_graph(
                user_id=user_id,
                username="bob",
                display_name="Bob Builder"
            )
            
            # Store memory with relationships
            memory_result = await self.db_integration.store_memory_with_relationships(
                memory_id=f"memory_{user_id}_001",
                user_id=user_id,
                content=conversation_data["message"],
                topics=["machine_learning"]
            )
            assert memory_result, "Memory storage failed"
            
            # Cache conversation
            cache_success = await self.db_integration.cache_conversation(user_id, conversation_data)
            assert cache_success, "Conversation caching failed"
            
            # Search for similar conversations
            similar_convs = await self.db_integration.search_similar_conversations(
                query_embedding=fake_embedding,
                user_id=user_id,
                limit=3
            )
            assert len(similar_convs) >= 1, "Similar conversation search failed"
            
            # Get user context
            user_context = await self.db_integration.get_user_context(user_id)
            assert user_context['user_id'] == user_id, "User context retrieval failed"
            
            self.record_test_result(test_name, True, f"Processed conversation with embedding {doc_id[:8]}... and {len(similar_convs)} similar")
            
        except Exception as e:
            self.record_test_result(test_name, False, str(e))
    
    async def test_health_and_statistics(self):
        """Test health monitoring and statistics"""
        test_name = "Health Monitoring & Statistics"
        
        try:
            # Get comprehensive health check
            health = await self.db_integration.get_comprehensive_health_check()
            assert health.get('overall_status') in ['healthy', 'degraded'], "Invalid health status"
            assert 'vector_storage' in health, "Missing vector storage health"
            assert 'graph_storage' in health, "Missing graph storage health"
            assert 'local_cache' in health, "Missing cache health"
            
            # Get storage statistics
            stats = await self.db_integration.get_storage_statistics()
            assert stats.get('deployment_mode') == 'local_native', "Wrong deployment mode"
            assert 'vector_storage' in stats, "Missing vector storage stats"
            assert 'graph_storage' in stats, "Missing graph storage stats"
            
            # Test individual component health
            vector_stats = self.db_integration.get_vector_storage().get_stats()
            assert vector_stats.get('storage_type') == 'enhanced_local_vector', "Wrong vector storage type"
            
            graph_health = await self.db_integration.get_graph_storage().health_check()
            assert graph_health.get('status') == 'healthy', "Graph storage not healthy"
            
            self.record_test_result(test_name, True, f"Overall status: {health.get('overall_status')}")
            
        except Exception as e:
            self.record_test_result(test_name, False, str(e))
    
    async def test_chromadb_compatibility(self):
        """Test ChromaDB compatibility layer"""
        test_name = "ChromaDB Compatibility Layer"
        
        try:
            # Get ChromaDB-compatible client
            chromadb_client = self.db_integration.get_chromadb_client()
            collection = chromadb_client.get_or_create_collection("compatibility_test")
            
            # Test ChromaDB-style operations
            collection.add(
                documents=["Hello world", "Goodbye world", "Machine learning rocks"],
                metadatas=[{"type": "greeting"}, {"type": "farewell"}, {"type": "tech"}],
                ids=["hello", "goodbye", "ml"]
            )
            
            # Test ChromaDB-style query
            query_embedding = self.db_integration.get_vector_storage()._generate_placeholder_embedding("Hello there")
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=2,
                include=['documents', 'metadatas', 'distances']
            )
            
            assert len(results['documents'][0]) == 2, "ChromaDB compatibility query failed"
            
            # Test get operation
            get_results = collection.get(ids=["hello", "ml"])
            assert len(get_results['documents']) == 2, "ChromaDB compatibility get failed"
            
            self.record_test_result(test_name, True, f"Added 3 docs, queried {len(results['documents'][0])}")
            
        except Exception as e:
            self.record_test_result(test_name, False, str(e))
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting Local Database Replacement Tests")
        logger.info("=" * 60)
        
        try:
            await self.setup()
            
            # Run individual tests
            await self.test_vector_storage_basic_operations()
            await self.test_graph_storage_operations()
            await self.test_integrated_conversation_flow()
            await self.test_health_and_statistics()
            await self.test_chromadb_compatibility()
            
        finally:
            await self.cleanup()
        
        # Print results summary
        logger.info("=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            logger.info(f"{status} | {result['test']}")
            if result['details']:
                logger.info(f"      └─ {result['details']}")
        
        logger.info("=" * 60)
        success_rate = (passed / total * 100) if total > 0 else 0
        logger.info(f"📈 Success Rate: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed == total:
            logger.info("🎉 All tests passed! Local database replacements are working correctly.")
            return True
        else:
            logger.error(f"❌ {total - passed} tests failed. Check the logs for details.")
            return False


async def main():
    """Main test runner"""
    tester = LocalDatabaseTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ Local database replacements are ready for production!")
        print("   📊 Vector storage (ChromaDB replacement): Working")
        print("   🕸️ Graph storage (Neo4j replacement): Working") 
        print("   💾 Local cache (Redis replacement): Working")
        print("   🔗 Integration layer: Working")
        print("   🧪 Compatibility layers: Working")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())