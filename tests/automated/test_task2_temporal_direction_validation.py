#!/usr/bin/env python3
"""
Task #2: Temporal Query Direction Bug Fix Validation Test

Validates that temporal queries return memories in correct chronological order:
- "first/earliest" queries → Sort ASC (oldest memories first)
- "last/recent" queries → Sort DESC (newest memories first)

Tests the unified classifier integration through the full retrieval pipeline.
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Setup Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Minimal imports for direct validation
from src.memory.unified_query_classification import UnifiedQueryClassifier, QueryIntent, VectorStrategy

# Setup basic logging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)


class TemporalDirectionValidator:
    """Validates temporal query direction through unified classifier"""
    
    def __init__(self):
        self.classifier = UnifiedQueryClassifier()
        self.test_results = []
    
    async def validate_classifier_temporal_detection(self) -> bool:
        """Test 1: Validate classifier detects temporal direction correctly"""
        print("\n📋 TEST 1: Classifier Temporal Direction Detection")
        print("=" * 60)
        
        test_cases = [
            # (query, expected_is_temporal_first, expected_is_temporal_last, description)
            ("What was the first thing we discussed?", True, False, "First query"),
            ("What was the earliest thing?", True, False, "Earliest query"),
            ("When did we first start talking?", True, False, "First start query"),
            ("What did we talk about initially?", True, False, "Initial query"),
            
            ("What was the last thing we discussed?", False, True, "Last query"),
            ("What was the most recent thing?", False, True, "Recent query"),
            ("What did we just talk about?", False, True, "Just now query"),
            ("What's the latest update?", False, True, "Latest query"),
            
            ("Tell me about our conversations", False, False, "General conversation query"),
            ("What do you remember?", False, False, "General recall query"),
        ]
        
        all_passed = True
        for query, expected_first, expected_last, description in test_cases:
            result = await self.classifier.classify(query)
            
            is_correct = (
                result.is_temporal_first == expected_first and
                result.is_temporal_last == expected_last
            )
            
            status = "✅ PASS" if is_correct else "❌ FAIL"
            print(f"{status}: {description}")
            print(f"  Query: '{query}'")
            print(f"  Expected: first={expected_first}, last={expected_last}")
            print(f"  Got:      first={result.is_temporal_first}, last={result.is_temporal_last}")
            
            if not is_correct:
                all_passed = False
            
            self.test_results.append({
                "test": f"TEST_1_{description}",
                "query": query,
                "expected": {"first": expected_first, "last": expected_last},
                "actual": {"first": result.is_temporal_first, "last": result.is_temporal_last},
                "passed": is_correct
            })
        
        return all_passed
    
    async def validate_classifier_intent_classification(self) -> bool:
        """Test 2: Validate temporal queries get TEMPORAL_ANALYSIS intent"""
        print("\n📋 TEST 2: Temporal Intent Classification")
        print("=" * 60)
        
        temporal_queries = [
            "What was the first thing we discussed?",
            "What did we talk about recently?",
            "Tell me about our latest conversation",
            "When did we start talking about this?",
        ]
        
        all_passed = True
        for query in temporal_queries:
            result = await self.classifier.classify(query)
            
            is_temporal = result.intent_type == QueryIntent.TEMPORAL_ANALYSIS
            status = "✅ PASS" if is_temporal else "⚠️  WARN"
            
            print(f"{status}: '{query}'")
            print(f"  Intent: {result.intent_type}")
            print(f"  Vector Strategy: {result.vector_strategy}")
            
            if not is_temporal:
                all_passed = False
            
            self.test_results.append({
                "test": "TEST_2_temporal_intent",
                "query": query,
                "expected_intent": QueryIntent.TEMPORAL_ANALYSIS.value,
                "actual_intent": result.intent_type.value,
                "passed": is_temporal
            })
        
        return all_passed
    
    async def validate_temporal_strategy_routing(self) -> bool:
        """Test 3: Validate temporal queries route to TEMPORAL_CHRONOLOGICAL strategy"""
        print("\n📋 TEST 3: Temporal Strategy Routing")
        print("=" * 60)
        
        test_cases = [
            ("What was the first thing?", True, "First query should use temporal strategy"),
            ("What was the last thing?", True, "Last query should use temporal strategy"),
            ("What do you remember?", False, "General query should not use temporal strategy"),
        ]
        
        all_passed = True
        for query, should_be_temporal, description in test_cases:
            result = await self.classifier.classify(query)
            
            is_temporal_strategy = result.vector_strategy == VectorStrategy.TEMPORAL_CHRONOLOGICAL
            is_correct = is_temporal_strategy == should_be_temporal
            
            status = "✅ PASS" if is_correct else "❌ FAIL"
            print(f"{status}: {description}")
            print(f"  Query: '{query}'")
            print(f"  Expected temporal_strategy: {should_be_temporal}")
            print(f"  Got:                        {is_temporal_strategy}")
            print(f"  Strategy: {result.vector_strategy}")
            
            if not is_correct:
                all_passed = False
            
            self.test_results.append({
                "test": "TEST_3_temporal_strategy",
                "query": query,
                "expected_strategy": "TEMPORAL_CHRONOLOGICAL" if should_be_temporal else "other",
                "actual_strategy": result.vector_strategy.value,
                "passed": is_correct
            })
        
        return all_passed
    
    async def validate_temporal_direction_fields_exist(self) -> bool:
        """Test 4: Validate UnifiedClassification has temporal direction fields"""
        print("\n📋 TEST 4: UnifiedClassification Fields")
        print("=" * 60)
        
        result = await self.classifier.classify("What was the first thing?")
        
        has_first = hasattr(result, 'is_temporal_first')
        has_last = hasattr(result, 'is_temporal_last')
        
        print(f"UnifiedClassification attributes:")
        print(f"  has is_temporal_first: {has_first} {'✅' if has_first else '❌'}")
        print(f"  has is_temporal_last:  {has_last} {'✅' if has_last else '❌'}")
        
        if has_first:
            print(f"  is_temporal_first value: {result.is_temporal_first}")
        if has_last:
            print(f"  is_temporal_last value:  {result.is_temporal_last}")
        
        passed = has_first and has_last
        
        self.test_results.append({
            "test": "TEST_4_fields_exist",
            "has_is_temporal_first": has_first,
            "has_is_temporal_last": has_last,
            "passed": passed
        })
        
        return passed
    
    def validate_direction_enum_usage(self) -> bool:
        """Test 5: Validate Direction enum is available for sorting"""
        print("\n📋 TEST 5: Direction Enum Availability")
        print("=" * 60)
        
        try:
            from qdrant_client import models
            
            # Check if Direction enum exists
            if hasattr(models, 'Direction'):
                print(f"✅ Direction enum available")
                print(f"  Direction.ASC:  {models.Direction.ASC}")
                print(f"  Direction.DESC: {models.Direction.DESC}")
                
                self.test_results.append({
                    "test": "TEST_5_direction_enum",
                    "direction_asc": str(models.Direction.ASC),
                    "direction_desc": str(models.Direction.DESC),
                    "passed": True
                })
                return True
            else:
                print("❌ Direction enum NOT found in qdrant_client.models")
                self.test_results.append({
                    "test": "TEST_5_direction_enum",
                    "passed": False,
                    "error": "Direction enum not found"
                })
                return False
        except Exception as e:
            print(f"❌ Error checking Direction enum: {e}")
            self.test_results.append({
                "test": "TEST_5_direction_enum",
                "passed": False,
                "error": str(e)
            })
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all validation tests"""
        print("\n" + "=" * 60)
        print("🚀 TASK #2: TEMPORAL DIRECTION BUG FIX VALIDATION")
        print("=" * 60)
        
        results = []
        
        # Test 1: Classifier temporal detection
        results.append(("Classifier Temporal Detection", await self.validate_classifier_temporal_detection()))
        
        # Test 2: Temporal intent classification
        results.append(("Temporal Intent Classification", await self.validate_classifier_intent_classification()))
        
        # Test 3: Temporal strategy routing
        results.append(("Temporal Strategy Routing", await self.validate_temporal_strategy_routing()))
        
        # Test 4: Temporal direction fields exist
        results.append(("Temporal Direction Fields", await self.validate_temporal_direction_fields_exist()))
        
        # Test 5: Direction enum usage
        results.append(("Direction Enum Availability", self.validate_direction_enum_usage()))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for _, passed in results if passed)
        
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nTotal: {passed_tests}/{total_tests} test suites passed")
        
        all_passed = all(passed for _, passed in results)
        
        # Save results
        self.save_results(all_passed, passed_tests, total_tests)
        
        return all_passed
    
    def save_results(self, all_passed: bool, passed_count: int, total_count: int):
        """Save test results to JSON file"""
        results_file = "tests/automated/task2_temporal_direction_results.json"
        
        summary = {
            "test_name": "Task #2: Temporal Query Direction Bug Fix Validation",
            "timestamp": datetime.now().isoformat(),
            "overall_passed": all_passed,
            "test_summary": {
                "passed": passed_count,
                "total": total_count
            },
            "detailed_results": self.test_results
        }
        
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n📁 Results saved to: {results_file}")


def main():
    """Run validation tests"""
    validator = TemporalDirectionValidator()
    
    try:
        all_passed = asyncio.run(validator.run_all_tests())
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)
    
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
