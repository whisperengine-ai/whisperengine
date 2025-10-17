#!/usr/bin/env python3
"""
Simple test of Phase 2 QueryClassifier (no database required).

Tests the QueryClassifier logic directly to verify query categorization.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

from src.memory.query_classifier import create_query_classifier, QueryCategory


class Phase2ClassifierTester:
    """Test QueryClassifier without database dependencies."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.classifier = None
        
    async def setup(self):
        """Initialize classifier."""
        print("🔧 Setting up QueryClassifier...")
        self.classifier = create_query_classifier()
        print("✅ Setup complete!\n")
    
    async def test_classification(
        self,
        query: str,
        expected_category: QueryCategory,
        emotion_data: Dict[str, Any] = None,
        is_temporal: bool = False
    ):
        """Test query classification."""
        self.total_tests += 1
        
        print(f"\n{'='*80}")
        print(f"TEST {self.total_tests}: {expected_category.value.upper()} Query")
        print(f"{'='*80}")
        print(f"📝 Query: {query}")
        print(f"🎯 Expected: {expected_category.value}")
        
        # Classify the query
        actual_category = await self.classifier.classify_query(
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
        if emotion_data:
            print(f"  • Emotion Intensity: {emotion_data.get('emotional_intensity', 0.0):.2f}")
            print(f"  • Dominant Emotion: {emotion_data.get('dominant_emotion', 'N/A')}")
        
        # Get expected routing strategy
        strategy = self.classifier.get_vector_strategy(actual_category)
        print(f"  • Vector Strategy: {strategy['description']}")
        print(f"  • Vectors to Use: {strategy['vectors']}")
        print(f"  • Use Fusion: {strategy['use_fusion']}")
        
        result = {
            "test": self.total_tests,
            "query": query,
            "expected_category": expected_category.value,
            "actual_category": actual_category.value,
            "classification_correct": classification_correct,
            "vector_description": strategy['description'],
            "vectors": strategy['vectors'],
            "use_fusion": strategy['use_fusion'],
            "is_temporal": is_temporal,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(result)
        return result
    
    async def run_comprehensive_tests(self):
        """Run comprehensive classification test suite."""
        
        print(f"\n{'#'*80}")
        print(f"# PHASE 2 QUERY CLASSIFIER TEST SUITE")
        print(f"# Testing Query Categorization & Vector Strategy Mapping")
        print(f"{'#'*80}\n")
        
        await self.setup()
        
        print(f"\n{'*'*80}")
        print(f"FACTUAL QUERY TESTS")
        print(f"{'*'*80}")
        
        # Test 1: Factual queries
        await self.test_classification(
            query="What is 2+2?",
            expected_category=QueryCategory.FACTUAL
        )
        
        await self.test_classification(
            query="Define photosynthesis",
            expected_category=QueryCategory.FACTUAL
        )
        
        await self.test_classification(
            query="Explain how to calculate area",
            expected_category=QueryCategory.FACTUAL
        )
        
        await self.test_classification(
            query="What are the main causes of climate change?",
            expected_category=QueryCategory.FACTUAL
        )
        
        print(f"\n{'*'*80}")
        print(f"CONVERSATIONAL QUERY TESTS")
        print(f"{'*'*80}")
        
        # Test 2: Conversational queries
        await self.test_classification(
            query="What did we discuss earlier?",
            expected_category=QueryCategory.CONVERSATIONAL
        )
        
        await self.test_classification(
            query="Remember when we talked about marine biology?",
            expected_category=QueryCategory.CONVERSATIONAL
        )
        
        await self.test_classification(
            query="You mentioned coral reefs before",
            expected_category=QueryCategory.CONVERSATIONAL
        )
        
        await self.test_classification(
            query="We were talking about ocean conservation",
            expected_category=QueryCategory.CONVERSATIONAL
        )
        
        print(f"\n{'*'*80}")
        print(f"EMOTIONAL QUERY TESTS")
        print(f"{'*'*80}")
        
        # Test 3: Emotional queries (with high emotional intensity)
        await self.test_classification(
            query="How are you feeling today?",
            expected_category=QueryCategory.EMOTIONAL,
            emotion_data={
                'emotional_intensity': 0.45,
                'dominant_emotion': 'curiosity'
            }
        )
        
        await self.test_classification(
            query="I'm so excited about this project!",
            expected_category=QueryCategory.EMOTIONAL,
            emotion_data={
                'emotional_intensity': 0.78,
                'dominant_emotion': 'joy'
            }
        )
        
        await self.test_classification(
            query="This is really frustrating me",
            expected_category=QueryCategory.EMOTIONAL,
            emotion_data={
                'emotional_intensity': 0.65,
                'dominant_emotion': 'anger'
            }
        )
        
        # Test 4: Low emotional intensity (should not classify as emotional)
        await self.test_classification(
            query="How are you?",
            expected_category=QueryCategory.GENERAL,  # Low intensity → GENERAL
            emotion_data={
                'emotional_intensity': 0.15,  # Below 0.3 threshold
                'dominant_emotion': 'neutral'
            }
        )
        
        print(f"\n{'*'*80}")
        print(f"TEMPORAL QUERY TESTS")
        print(f"{'*'*80}")
        
        # Test 5: Temporal queries
        await self.test_classification(
            query="What was the first thing I asked you?",
            expected_category=QueryCategory.TEMPORAL,
            is_temporal=True
        )
        
        await self.test_classification(
            query="Show me our earliest conversation",
            expected_category=QueryCategory.TEMPORAL,
            is_temporal=True
        )
        
        print(f"\n{'*'*80}")
        print(f"GENERAL QUERY TESTS")
        print(f"{'*'*80}")
        
        # Test 6: General queries
        await self.test_classification(
            query="Tell me about coral reefs",
            expected_category=QueryCategory.GENERAL
        )
        
        await self.test_classification(
            query="What do you think about ocean conservation?",
            expected_category=QueryCategory.GENERAL
        )
        
        await self.test_classification(
            query="I love marine biology",
            expected_category=QueryCategory.GENERAL
        )
        
        print(f"\n{'*'*80}")
        print(f"PRIORITY TESTS (Factual overrides conversational patterns)")
        print(f"{'*'*80}")
        
        # Test 7: Priority tests (factual should win)
        await self.test_classification(
            query="What is the definition we discussed earlier?",  # Has "discussed" but also "what is definition"
            expected_category=QueryCategory.FACTUAL  # Factual has higher priority
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
        
        # Group results by category
        by_category = {}
        for result in self.results:
            expected = result['expected_category']
            if expected not in by_category:
                by_category[expected] = {'total': 0, 'passed': 0}
            by_category[expected]['total'] += 1
            if result['classification_correct']:
                by_category[expected]['passed'] += 1
        
        print("Results by Category:")
        for category, stats in sorted(by_category.items()):
            success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status = "✅" if stats['passed'] == stats['total'] else "⚠️"
            print(f"  {status} {category.upper()}: {stats['passed']}/{stats['total']} ({success_rate:.0f}%)")
        
        print("\nDetailed Results:")
        for result in self.results:
            status = "✅" if result['classification_correct'] else "❌"
            query_preview = result['query'][:60] + "..." if len(result['query']) > 60 else result['query']
            print(f"{status} {query_preview}")
            print(f"    Expected: {result['expected_category']}, Got: {result['actual_category']}")
            print(f"    Strategy: {result['vector_description']}")
            print(f"    Vectors: {result['vectors']}, Fusion: {result['use_fusion']}")


async def main():
    """Main test runner."""
    tester = Phase2ClassifierTester()
    
    try:
        await tester.run_comprehensive_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0 if tester.passed_tests == tester.total_tests else 1)


if __name__ == "__main__":
    asyncio.run(main())
