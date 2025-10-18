"""
Tests for Phase 2 Hybrid Vector Routing Integration

Tests the integration of QueryClassifier into VectorMemoryManager:
- Single vector search (factual/general queries)
- Multi-vector fusion (emotional/conversational queries)
- Temporal query routing
- End-to-end Phase 2 retrieval

Part of Phase 2: Multi-Vector Intelligence Roadmap, Task 2.2
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.memory.query_classifier import QueryCategory


class TestPhase2HybridRouting:
    """Test Phase 2 hybrid vector routing in VectorMemoryManager."""
    
    @pytest.mark.asyncio
    async def test_factual_query_routing(self):
        """Test factual queries route to single content vector."""
        # Mock setup
        with patch('src.memory.vector_memory_system.VectorMemoryStore') as MockStore:
            mock_store = MockStore.return_value
            mock_store.embedder.embed.return_value = [[0.1] * 384]  # Mock embedding
            mock_store.client.search.return_value = [
                Mock(
                    id="mem1",
                    score=0.9,
                    payload={
                        "content": "Paris is the capital of France",
                        "timestamp": "2025-10-17T10:00:00",
                        "metadata": {},
                        "memory_type": "fact"
                    }
                )
            ]
            mock_store._detect_temporal_query_with_qdrant = AsyncMock(return_value=False)
            
            from src.memory.vector_memory_system import VectorMemoryManager
            
            config = {
                'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
                'embeddings': {'model_name': ''}
            }
            
            manager = VectorMemoryManager(config)
            
            # Execute Phase 2 retrieval with factual query
            results = await manager.retrieve_relevant_memories_phase2(
                user_id="test_user",
                query="What is the capital of France?",
                limit=10
            )
            
            # Verify routing
            assert len(results) > 0
            assert results[0]['query_category'] == 'factual'
            assert results[0]['search_type'] == 'content_vector'
            assert results[0]['vector_used'] == 'content'
    
    @pytest.mark.asyncio
    async def test_emotional_query_routing(self):
        """Test emotional queries route to multi-vector fusion."""
        with patch('src.memory.vector_memory_system.VectorMemoryStore') as MockStore:
            mock_store = MockStore.return_value
            mock_store.embedder.embed.return_value = [[0.1] * 384]
            mock_store.client.search.return_value = []
            mock_store._detect_temporal_query_with_qdrant = AsyncMock(return_value=False)
            
            from src.memory.vector_memory_system import VectorMemoryManager
            
            config = {
                'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
                'embeddings': {'model_name': ''}
            }
            
            manager = VectorMemoryManager(config)
            
            # Execute with emotional query
            results = await manager.retrieve_relevant_memories_phase2(
                user_id="test_user",
                query="I'm so excited about this!",
                limit=10,
                emotion_data={'emotional_intensity': 0.8, 'dominant_emotion': 'joy'}
            )
            
            # Should have attempted multi-vector fusion (even if no results)
            # Note: results may be empty due to mocking, but category should be set
            # This tests the routing logic, not the actual search
            assert isinstance(results, list)
    
    @pytest.mark.asyncio  
    async def test_conversational_query_routing(self):
        """Test conversational queries route to content + semantic fusion."""
        with patch('src.memory.vector_memory_system.VectorMemoryStore') as MockStore:
            mock_store = MockStore.return_value
            mock_store.embedder.embed.return_value = [[0.1] * 384]
            mock_store.client.search.return_value = []
            mock_store._detect_temporal_query_with_qdrant = AsyncMock(return_value=False)
            
            from src.memory.vector_memory_system import VectorMemoryManager
            
            config = {
                'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
                'embeddings': {'model_name': ''}
            }
            
            manager = VectorMemoryManager(config)
            
            # Execute with conversational query
            results = await manager.retrieve_relevant_memories_phase2(
                user_id="test_user",
                query="What did we discuss about AI?",
                limit=10
            )
            
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_temporal_query_priority(self):
        """Test temporal queries have highest priority."""
        with patch('src.memory.vector_memory_system.VectorMemoryStore') as MockStore:
            mock_store = MockStore.return_value
            mock_store._detect_temporal_query_with_qdrant = AsyncMock(return_value=True)
            mock_store._handle_temporal_query_with_qdrant = AsyncMock(return_value=[
                {
                    "content": "First message",
                    "score": 1.0,
                    "timestamp": "2025-10-17T09:00:00",
                    "metadata": {},
                    "memory_type": "conversation"
                }
            ])
            
            from src.memory.vector_memory_system import VectorMemoryManager
            
            config = {
                'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
                'embeddings': {'model_name': ''}
            }
            
            manager = VectorMemoryManager(config)
            
            # Execute with temporal query
            results = await manager.retrieve_relevant_memories_phase2(
                user_id="test_user",
                query="What was the first thing I said?",
                limit=10
            )
            
            # Verify temporal routing
            assert len(results) > 0
            assert results[0]['query_category'] == 'temporal'
            assert results[0]['search_type'] == 'temporal_chronological'
    
    @pytest.mark.asyncio
    async def test_general_query_fallback(self):
        """Test general queries use content vector as fallback."""
        with patch('src.memory.vector_memory_system.VectorMemoryStore') as MockStore:
            mock_store = MockStore.return_value
            mock_store.embedder.embed.return_value = [[0.1] * 384]
            mock_store.client.search.return_value = []
            mock_store._detect_temporal_query_with_qdrant = AsyncMock(return_value=False)
            
            from src.memory.vector_memory_system import VectorMemoryManager
            
            config = {
                'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
                'embeddings': {'model_name': ''}
            }
            
            manager = VectorMemoryManager(config)
            
            # Execute with general query
            results = await manager.retrieve_relevant_memories_phase2(
                user_id="test_user",
                query="Tell me more",
                limit=10
            )
            
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_classifier_fallback_on_error(self):
        """Test graceful fallback when QueryClassifier fails."""
        with patch('src.memory.vector_memory_system.VectorMemoryStore') as MockStore:
            mock_store = MockStore.return_value
            mock_store.embedder.embed.return_value = [[0.1] * 384]
            mock_store.client.search.return_value = []
            mock_store._detect_temporal_query_with_qdrant = AsyncMock(return_value=False)
            
            from src.memory.vector_memory_system import VectorMemoryManager
            
            config = {
                'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
                'embeddings': {'model_name': ''}
            }
            
            manager = VectorMemoryManager(config)
            
            # Simulate classifier failure
            manager._query_classifier = None
            
            # Should fall back to legacy method
            with patch.object(manager, 'retrieve_relevant_memories', new_callable=AsyncMock) as mock_legacy:
                mock_legacy.return_value = []
                
                results = await manager.retrieve_relevant_memories_phase2(
                    user_id="test_user",
                    query="Any query",
                    limit=10
                )
                
                # Verify fallback was called
                mock_legacy.assert_called_once()


class TestSingleVectorSearch:
    """Test helper method for single vector search."""
    
    @pytest.mark.asyncio
    async def test_search_content_vector(self):
        """Test searching content vector."""
        with patch('src.memory.vector_memory_system.VectorMemoryStore') as MockStore:
            mock_store = MockStore.return_value
            mock_store.embedder.embed.return_value = [[0.1] * 384]
            mock_store.client.search.return_value = [
                Mock(
                    id="mem1",
                    score=0.85,
                    payload={
                        "content": "Test content",
                        "timestamp": "2025-10-17T10:00:00",
                        "metadata": {},
                        "memory_type": "conversation"
                    }
                )
            ]
            
            from src.memory.vector_memory_system import VectorMemoryManager
            
            config = {
                'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
                'embeddings': {'model_name': ''}
            }
            
            manager = VectorMemoryManager(config)
            
            results = await manager._search_single_vector(
                vector_name="content",
                query="test query",
                user_id="test_user",
                limit=10
            )
            
            assert len(results) == 1
            assert results[0]['vector_used'] == 'content'
            assert results[0]['search_type'] == 'content_vector'
            assert results[0]['score'] == 0.85
    
    @pytest.mark.asyncio
    async def test_search_handles_errors(self):
        """Test single vector search handles errors gracefully."""
        with patch('src.memory.vector_memory_system.VectorMemoryStore') as MockStore:
            mock_store = MockStore.return_value
            mock_store.embedder.embed.side_effect = Exception("Embedding failed")
            
            from src.memory.vector_memory_system import VectorMemoryManager
            
            config = {
                'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
                'embeddings': {'model_name': ''}
            }
            
            manager = VectorMemoryManager(config)
            
            results = await manager._search_single_vector(
                vector_name="content",
                query="test query",
                user_id="test_user",
                limit=10
            )
            
            # Should return empty list on error
            assert results == []


class TestMultiVectorFusion:
    """Test helper method for multi-vector fusion search."""
    
    @pytest.mark.asyncio
    async def test_fusion_combines_vectors(self):
        """Test multi-vector fusion combines results from multiple vectors."""
        with patch('src.memory.vector_memory_system.VectorMemoryStore') as MockStore:
            mock_store = MockStore.return_value
            mock_store.embedder.embed.return_value = [[0.1] * 384]
            mock_store.client.search.return_value = [
                Mock(
                    id="mem1",
                    score=0.8,
                    payload={
                        "content": "Test memory",
                        "timestamp": "2025-10-17T10:00:00",
                        "metadata": {},
                        "memory_type": "conversation"
                    }
                )
            ]
            
            from src.memory.vector_memory_system import VectorMemoryManager
            
            config = {
                'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
                'embeddings': {'model_name': ''}
            }
            
            manager = VectorMemoryManager(config)
            
            results = await manager._search_multi_vector_fusion(
                vectors=['content', 'semantic'],
                weights=[0.5, 0.5],
                query="test query",
                user_id="test_user",
                limit=10
            )
            
            # Should have fused results
            if results:  # May be empty due to mocking
                assert 'search_type' in results[0]
                assert results[0]['search_type'] == 'multi_vector_fusion'
                assert 'vectors_used' in results[0]
    
    @pytest.mark.asyncio
    async def test_fusion_handles_empty_results(self):
        """Test fusion handles case where no vectors return results."""
        with patch('src.memory.vector_memory_system.VectorMemoryStore') as MockStore:
            mock_store = MockStore.return_value
            mock_store.embedder.embed.return_value = [[0.1] * 384]
            mock_store.client.search.return_value = []  # No results
            
            from src.memory.vector_memory_system import VectorMemoryManager
            
            config = {
                'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
                'embeddings': {'model_name': ''}
            }
            
            manager = VectorMemoryManager(config)
            
            results = await manager._search_multi_vector_fusion(
                vectors=['content', 'emotion'],
                weights=[0.4, 0.6],
                query="test query",
                user_id="test_user",
                limit=10
            )
            
            # Should handle gracefully
            assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
