#!/usr/bin/env python3
"""
Direct test of Phase 2 Hybrid Vector Routing (bypasses Discord).

Tests QueryClassifier and routing logic directly against Elena's
vector memory system using the Python environment.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

# Set required environment variables
os.environ['FASTEMBED_CACHE_PATH'] = '/tmp/fastembed_cache'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['DISCORD_BOT_NAME'] = 'elena'

from src.memory.memory_protocol import create_memory_manager
from src.memory.query_classifier import create_query_classifier, QueryCategory


class Phase2DirectTester:
    """Direct test of Phase 2 routing without Discord."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.memory_manager = None
        self.query_classifier = None
        
    async def setup(self):
        """Initialize components."""
        print("🔧 Setting up test environment...")
        
        # Initialize memory manager via factory
        self.memory_manager = create_memory_manager(memory_type="vector")
        
        # Initialize query classifier
        self.query_classifier = create_query_classifier()
        
        print("✅ Setup complete!\n")
    
    async def test_query_classification(
        self,
        query: str,
        expected_category: QueryCategory,
        emotion_data: Dict[str, Any] = None
    ):
        """Test query classification."""
        self.total_tests += 1
        
        print(f"\n{'='*80}")
        print(f"TEST {self.total_tests}: {expected_category.value.upper()} Query Classification")
        print(f"{'='*80}")
        print(f"📝 Query: {query}")
        print(f"🎯 Expected: {expected_category.value}")
        
        # Classify the query
        is_temporal = await self.memory_manager.vector_store._detect_temporal_query_with_qdrant(
            query, "test_user"
        )
        
        actual_category = await self.query_classifier.classify_query(
            query=query,
            emotion_data=emotion_data,
            is_temporal=is_temporal
        )
        
        # Check if classification is correct
        classification_correct = (actual_category == expected_category)
        
        if classification_correct:
            self.passed_tests += 1
            print(f"✅ PASS - Classification correct!")
        else:
            print(f"❌ FAIL - Expected {expected_category.value}, got {actual_category.value}")
        
        print(f"📊 Details:")
        print(f"  • Actual Category: {actual_category.value}")
        print(f"  • Is Temporal: {is_temporal}")
        print(f"  • Emotion Data: {emotion_data if emotion_data else 'None'}")
        
        result = {
            "test": self.total_tests,
            "query": query,
            "expected_category": expected_category.value,
            "actual_category": actual_category.value,
            "classification_correct": classification_correct,
            "is_temporal": is_temporal,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(result)
        return result
    
    async def test_phase2_routing(
        self,
        query: str,
        expected_category: str,
        user_id: str = "phase2_test_user"
    ):
        """Test Phase 2 routing with actual vector search."""
        self.total_tests += 1
        
        print(f"\n{'='*80}")
        print(f"TEST {self.total_tests}: {expected_category.upper()} Routing")
        print(f"{'='*80}")
        print(f"📝 Query: {query}")
        print(f"🎯 Expected Routing: {expected_category}")
        
        # Analyze emotion for emotional queries
        emotion_data = None
        if "emotion" in expected_category.lower() or "feeling" in query.lower():
            emotion_analysis = await self.emotion_analyzer.analyze_with_vectors(
                query, user_id
            )
            emotion_data = {
                'emotional_intensity': emotion_analysis.get('emotional_intensity', 0.0),
                'dominant_emotion': emotion_analysis.get('dominant_emotion', 'neutral')
            }
            print(f"🎭 Emotion Analysis: intensity={emotion_data['emotional_intensity']:.2f}, emotion={emotion_data['dominant_emotion']}")
        
        # Test Phase 2 routing
        try:
            memories = await self.memory_manager.retrieve_relevant_memories_phase2(
                user_id=user_id,
                query=query,
                limit=10,
                emotion_data=emotion_data
            )
            
            # Extract routing metadata
            search_type = "unknown"
            vectors_used = []
            
            if memories and len(memories) > 0:
                first_memory = memories[0]
                search_type = first_memory.get('search_type', 'unknown')
                vectors_used = first_memory.get('vectors_used', [])
            
            # Validate routing
            routing_correct = self._validate_routing(expected_category, search_type, vectors_used)
            
            if routing_correct:
                self.passed_tests += 1
                print(f"✅ PASS - Routing correct!")
            else:
                print(f"❌ FAIL - Routing mismatch!")
            
            print(f"📊 Routing Details:")
            print(f"  • Search Type: {search_type}")
            print(f"  • Vectors Used: {vectors_used}")
            print(f"  • Memories Found: {len(memories)}")
            
            result = {
                "test": self.total_tests,
                "query": query,
                "expected_category": expected_category,
                "search_type": search_type,
                "vectors_used": vectors_used,
                "routing_correct": routing_correct,
                "memory_count": len(memories),
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(result)
            return result
            
        except Exception as e:
            print(f"❌ Error during routing: {e}")
            import traceback
            traceback.print_exc()
            
            result = {
                "test": self.total_tests,
                "query": query,
                "expected_category": expected_category,
                "error": str(e),
                "routing_correct": False,
                "timestamp": datetime.now().isoformat()
            }
            
            self.results.append(result)
            return result
    
    def _validate_routing(
        self,
        expected_category: str,
        search_type: str,
        vectors_used: List[str]
    ) -> bool:
        """Validate routing matches expected category."""
        
        # FACTUAL → content_vector or single vector
        if expected_category == "factual":
            return "content" in search_type or search_type == "content_vector"
        
        # EMOTIONAL → multi_vector_fusion with emotion
        elif expected_category == "emotional":
            return (search_type == "multi_vector_fusion" and 
                    "emotion" in vectors_used)
        
        # CONVERSATIONAL → multi_vector_fusion with semantic
        elif expected_category == "conversational":
            return (search_type == "multi_vector_fusion" and 
                    "semantic" in vectors_used)
        
        # TEMPORAL → temporal_scroll
        elif expected_category == "temporal":
            return "temporal" in search_type or "scroll" in search_type
        
        # GENERAL → content_vector
        elif expected_category == "general":
            return "content" in search_type or search_type == "content_vector"
        
        return False
    
    async def run_all_tests(self):
        """Run comprehensive test suite."""
        
        print(f"\n{'#'*80}")
        print(f"# PHASE 2 HYBRID VECTOR ROUTING - DIRECT TEST")
        print(f"# Testing QueryClassifier + VectorMemoryManager Integration")
        print(f"# Bot: Elena | Database: Qdrant localhost:6334")
        print(f"{'#'*80}\n")
        
        await self.setup()
        
        print(f"\n{'*'*80}")
        print(f"PART 1: QUERY CLASSIFICATION TESTS")
        print(f"{'*'*80}")
        
        # Test 1: Factual classification
        await self.test_query_classification(
            query="What is 2+2?",
            expected_category=QueryCategory.FACTUAL
        )
        
        await self.test_query_classification(
            query="Define photosynthesis",
            expected_category=QueryCategory.FACTUAL
        )
        
        # Test 2: Conversational classification
        await self.test_query_classification(
            query="What did we discuss earlier?",
            expected_category=QueryCategory.CONVERSATIONAL
        )
        
        await self.test_query_classification(
            query="Remember when we talked about marine biology?",
            expected_category=QueryCategory.CONVERSATIONAL
        )
        
        # Test 3: Emotional classification (with emotion data)
        await self.test_query_classification(
            query="How are you feeling?",
            expected_category=QueryCategory.EMOTIONAL,
            emotion_data={'emotional_intensity': 0.45, 'dominant_emotion': 'curiosity'}
        )
        
        # Test 4: General classification
        await self.test_query_classification(
            query="Tell me about coral reefs",
            expected_category=QueryCategory.GENERAL
        )
        
        print(f"\n{'*'*80}")
        print(f"PART 2: ROUTING TESTS (with actual vector searches)")
        print(f"{'*'*80}")
        
        # Test routing with real vector searches
        await self.test_phase2_routing(
            query="What is marine biology?",
            expected_category="factual"
        )
        
        await self.test_phase2_routing(
            query="How are you feeling today?",
            expected_category="emotional"
        )
        
        await self.test_phase2_routing(
            query="What did we talk about?",
            expected_category="conversational"
        )
        
        await self.test_phase2_routing(
            query="Tell me about ocean conservation",
            expected_category="general"
        )
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print test summary."""
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print(f"{'='*80}\n")
        
        # Group results by type
        classification_tests = [r for r in self.results if 'actual_category' in r]
        routing_tests = [r for r in self.results if 'search_type' in r]
        
        if classification_tests:
            print(f"Classification Tests: {len(classification_tests)}")
            for result in classification_tests:
                status = "✅" if result.get('classification_correct') else "❌"
                print(f"  {status} {result['query'][:50]}... → {result['actual_category']}")
        
        if routing_tests:
            print(f"\nRouting Tests: {len(routing_tests)}")
            for result in routing_tests:
                status = "✅" if result.get('routing_correct') else "❌"
                print(f"  {status} {result['query'][:50]}... → {result.get('search_type', 'unknown')}")


async def main():
    """Main test runner."""
    tester = Phase2DirectTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0 if tester.passed_tests == tester.total_tests else 1)


if __name__ == "__main__":
    asyncio.run(main())
