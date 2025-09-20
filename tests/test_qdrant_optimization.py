#!/usr/bin/env python3
"""
Test suite for Qdrant query optimization features.
Tests query preprocessing, adaptive thresholds, chunking, hybrid search, and re-ranking.
"""

import asyncio
import pytest
import unittest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from src.memory.vector_memory_system import VectorMemoryManager, MemoryType


class TestQdrantQueryOptimization(unittest.TestCase):
    """Test cases for Qdrant query optimization features."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'collection_name': 'test_memory',
                'vector_size': 384
            },
            'embeddings': {
                'model_name': 'snowflake/snowflake-arctic-embed-xs',
                'device': 'cpu'
            }
        }
        
        # Mock the vector memory manager to avoid actual Qdrant calls
        self.memory_manager = Mock(spec=VectorMemoryManager)
        self.memory_manager.config = self.config
        
    def test_query_preprocessing_basic(self):
        """Test basic query preprocessing functionality."""
        from src.memory.qdrant_optimization import QdrantQueryOptimizer
        
        optimizer = QdrantQueryOptimizer()
        
        # Test stop word removal
        query = "the quick brown fox and the lazy dog"
        processed = optimizer.preprocess_query(query)
        
        # Should remove common stop words
        self.assertNotIn("the", processed.lower())
        self.assertNotIn("and", processed.lower())
        self.assertIn("quick", processed.lower())
        self.assertIn("brown", processed.lower())
        self.assertIn("fox", processed.lower())
        
    def test_adaptive_thresholds(self):
        """Test adaptive threshold calculation."""
        from src.memory.qdrant_optimization import QdrantQueryOptimizer
        
        optimizer = QdrantQueryOptimizer()
        
        # Test different query types
        conversation_threshold = optimizer.get_adaptive_threshold(
            query_type='conversation_recall',
            user_history={'conversational_user': True}
        )
        
        fact_threshold = optimizer.get_adaptive_threshold(
            query_type='fact_lookup',
            user_history={'prefers_precise_answers': True}
        )
        
        # Conversation queries should have lower thresholds
        self.assertLess(conversation_threshold, fact_threshold)
        
        # Precise users should get higher thresholds
        self.assertGreater(fact_threshold, 0.7)
        
    def test_content_chunking(self):
        """Test content chunking for better embeddings."""
        from src.memory.qdrant_optimization import QdrantQueryOptimizer
        
        optimizer = QdrantQueryOptimizer()
        
        # Test short content (should not be chunked)
        short_content = "This is a short message."
        short_chunks = optimizer.chunk_content(short_content)
        self.assertEqual(len(short_chunks), 1)
        self.assertEqual(short_chunks[0], short_content)
        
        # Test long content (should be chunked)
        long_content = "This is a very long conversation. " * 20
        long_chunks = optimizer.chunk_content(long_content)
        self.assertGreater(len(long_chunks), 1)
        
        # Each chunk should be under the maximum length
        for chunk in long_chunks:
            self.assertLessEqual(len(chunk), 300)
            
    @patch('src.memory.vector_memory_system.VectorMemoryManager')
    async def test_hybrid_search(self, mock_manager):
        """Test hybrid search combining vector and metadata filtering."""
        from src.memory.qdrant_optimization import QdrantQueryOptimizer
        
        # Mock search results
        mock_results = [
            {
                'content': 'Recent conversation about cats',
                'score': 0.9,
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'channel_id': 'channel1',
                    'topics': ['pets', 'animals']
                }
            },
            {
                'content': 'Old conversation about dogs',
                'score': 0.8,
                'metadata': {
                    'timestamp': (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    'channel_id': 'channel2',
                    'topics': ['pets', 'training']
                }
            },
            {
                'content': 'Programming discussion',
                'score': 0.7,
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'channel_id': 'channel1',
                    'topics': ['technology', 'coding']
                }
            }
        ]
        
        mock_manager.return_value.vector_search = AsyncMock(return_value=mock_results)
        
        optimizer = QdrantQueryOptimizer(mock_manager.return_value)
        
        # Test time-based filtering
        time_filters = {
            'time_range': {
                'start': datetime.utcnow() - timedelta(days=7),
                'end': datetime.utcnow()
            }
        }
        
        filtered_results = await optimizer.hybrid_search(
            query="pets",
            user_id="user123",
            filters=time_filters
        )
        
        # Should only return recent results
        self.assertEqual(len(filtered_results), 2)  # Recent cat and programming
        
        # Test topic filtering
        topic_filters = {'topics': ['pets']}
        topic_results = await optimizer.hybrid_search(
            query="animals",
            user_id="user123", 
            filters=topic_filters
        )
        
        # Should only return pet-related results
        self.assertEqual(len(topic_results), 2)  # Both pet conversations
        
    def test_result_reranking(self):
        """Test result re-ranking with multiple factors."""
        from src.memory.qdrant_optimization import QdrantQueryOptimizer
        
        optimizer = QdrantQueryOptimizer()
        
        # Mock results with different characteristics
        results = [
            {
                'content': 'High quality recent content',
                'score': 0.7,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {'quality_score': 0.9}
            },
            {
                'content': 'Old low quality content',
                'score': 0.9,  # High semantic score
                'timestamp': (datetime.utcnow() - timedelta(days=60)).isoformat(),
                'metadata': {'quality_score': 0.3}
            },
            {
                'content': 'Medium quality medium age',
                'score': 0.8,
                'timestamp': (datetime.utcnow() - timedelta(days=7)).isoformat(),
                'metadata': {'quality_score': 0.6}
            }
        ]
        
        user_context = {'prefers_recent': True}
        
        reranked = optimizer.rerank_results(results, "test query", user_context)
        
        # Should have reranked_score for each result
        for result in reranked:
            self.assertIn('reranked_score', result)
            
        # Results should be sorted by reranked score
        scores = [r['reranked_score'] for r in reranked]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
    @patch('src.memory.vector_memory_system.VectorMemoryManager')
    async def test_end_to_end_optimization(self, mock_manager):
        """Test the complete optimization pipeline."""
        from src.memory.qdrant_optimization import QdrantQueryOptimizer
        
        # Mock the vector manager
        mock_results = [
            {
                'content': 'Luna is my cat and she loves to play',
                'score': 0.85,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {'memory_type': 'conversation', 'channel_id': 'dm'}
            },
            {
                'content': 'Programming in Python is fun',
                'score': 0.75,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {'memory_type': 'conversation', 'channel_id': 'guild'}
            }
        ]
        
        mock_manager.return_value.retrieve_relevant_memories = AsyncMock(return_value=mock_results)
        
        optimizer = QdrantQueryOptimizer(mock_manager.return_value)
        
        # Test complete optimized search
        results = await optimizer.optimized_search(
            query="tell me about my pet cat",
            user_id="user123",
            query_type="conversation_recall",
            user_history={'conversational_user': True}
        )
        
        # Should return results with optimization applied
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Should have reranked scores
        for result in results:
            self.assertIn('reranked_score', result)


class TestQdrantOptimizationMetrics(unittest.TestCase):
    """Test the optimization metrics and monitoring."""
    
    def test_metrics_initialization(self):
        """Test metrics tracking initialization."""
        from src.memory.qdrant_optimization import QdrantOptimizationMetrics
        
        metrics = QdrantOptimizationMetrics()
        
        self.assertIsInstance(metrics.query_performance, dict)
        self.assertIsInstance(metrics.user_satisfaction, dict)
        self.assertEqual(metrics.embedding_cache_hits, 0)
        
    def test_search_quality_recording(self):
        """Test recording search quality metrics."""
        from src.memory.qdrant_optimization import QdrantOptimizationMetrics
        
        metrics = QdrantOptimizationMetrics()
        
        # Record a search result
        test_results = [
            {'score': 0.9, 'content': 'result1'},
            {'score': 0.8, 'content': 'result2'}
        ]
        
        metrics.record_search_quality(
            query="test query",
            results=test_results,
            user_feedback="relevant"
        )
        
        # Check that metrics were recorded
        self.assertIn("test query", metrics.query_performance)
        perf = metrics.query_performance["test query"]
        
        self.assertEqual(perf['result_count'], 2)
        self.assertEqual(perf['avg_score'], 0.85)  # (0.9 + 0.8) / 2
        self.assertEqual(perf['user_feedback'], "relevant")
        
    def test_optimization_recommendations(self):
        """Test generation of optimization recommendations."""
        from src.memory.qdrant_optimization import QdrantOptimizationMetrics
        
        metrics = QdrantOptimizationMetrics()
        
        # Record queries with few results (threshold too high)
        for i in range(5):
            metrics.record_search_quality(f"query{i}", [], None)
            
        recommendations = metrics.get_optimization_recommendations()
        self.assertIn('threshold', recommendations)
        self.assertIn('lowering', recommendations['threshold'])
        
        # Clear and test with too many results (threshold too low)
        metrics.query_performance = {}
        for i in range(3):
            many_results = [{'score': 0.1} for _ in range(25)]
            metrics.record_search_quality(f"query{i}", many_results, None)
            
        recommendations = metrics.get_optimization_recommendations()
        self.assertIn('threshold', recommendations)
        self.assertIn('raising', recommendations['threshold'])


class TestQdrantOptimizationIntegration(unittest.TestCase):
    """Test integration with existing vector memory system."""
    
    @patch('src.memory.vector_memory_system.VectorMemoryStore')
    def test_integration_with_vector_manager(self, mock_store):
        """Test integration with existing VectorMemoryManager."""
        from src.memory.qdrant_optimization import OptimizedVectorMemoryManager
        
        # Create optimized manager
        config = {
            'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
            'embeddings': {'model_name': 'test-model'}
        }
        
        manager = OptimizedVectorMemoryManager(config)
        
        # Should have optimization features
        self.assertTrue(hasattr(manager, 'optimizer'))
        self.assertTrue(hasattr(manager, 'metrics'))
        
    @patch('src.memory.vector_memory_system.VectorMemoryStore')  
    async def test_optimized_retrieval(self, mock_store):
        """Test optimized memory retrieval."""
        from src.memory.qdrant_optimization import OptimizedVectorMemoryManager
        
        config = {
            'qdrant': {'host': 'localhost', 'port': 6333, 'collection_name': 'test'},
            'embeddings': {'model_name': 'test-model'}
        }
        
        manager = OptimizedVectorMemoryManager(config)
        
        # Mock the underlying retrieval
        mock_results = [
            {'content': 'test', 'score': 0.8, 'timestamp': datetime.utcnow().isoformat()}
        ]
        manager.vector_store.search_memories = AsyncMock(return_value=mock_results)
        
        # Test optimized retrieval
        results = await manager.retrieve_relevant_memories_optimized(
            user_id="user123",
            query="what's my cat's name?",
            query_type="conversation_recall"
        )
        
        # Should return optimized results
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)