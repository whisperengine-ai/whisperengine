#!/usr/bin/env python3
"""
Test script for recall detection feature.

Tests that "we talked about X" queries:
1. Are detected as recall queries
2. Get routed to TEMPORAL_ANALYSIS intent
3. Use SEMANTIC_FUSION strategy
4. Get extended 7-day temporal window (not 24 hours)

Usage:
    source .venv/bin/activate && \
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
    export QDRANT_HOST="localhost" && \
    export QDRANT_PORT="6334" && \
    export POSTGRES_HOST="localhost" && \
    export POSTGRES_PORT="5433" && \
    export DISCORD_BOT_NAME=elena && \
    python tests/automated/test_recall_detection.py
"""

import asyncio
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_recall_detection():
    """Test recall detection for 'we talked about X' queries."""
    
    # Lazy imports after environment setup
    from src.memory.unified_query_classification import (
        UnifiedQueryClassifier,
        QueryIntent,
        VectorStrategy
    )
    
    logger.info("🧪 TEST: Recall Detection Feature")
    logger.info("=" * 80)
    
    # Initialize classifier
    classifier = UnifiedQueryClassifier()
    logger.info("✅ Classifier initialized")
    
    # Test cases
    test_cases = [
        {
            "query": "we talked about prompt engineering",
            "expected_recall": True,
            "expected_intent": QueryIntent.TEMPORAL_ANALYSIS,
            "expected_strategy": VectorStrategy.SEMANTIC_FUSION,
            "expected_window": 7,
            "description": "Basic recall query"
        },
        {
            "query": "we discussed memory architecture",
            "expected_recall": True,
            "expected_intent": QueryIntent.TEMPORAL_ANALYSIS,
            "expected_strategy": VectorStrategy.SEMANTIC_FUSION,
            "expected_window": 7,
            "description": "Recall with 'discussed'"
        },
        {
            "query": "we were talking about vector embeddings",
            "expected_recall": True,
            "expected_intent": QueryIntent.TEMPORAL_ANALYSIS,
            "expected_strategy": VectorStrategy.SEMANTIC_FUSION,
            "expected_window": 7,
            "description": "Recall with 'were talking about'"
        },
        {
            "query": "we talked about this today",
            "expected_recall": False,
            "expected_intent": None,  # Should use normal classification
            "expected_strategy": None,
            "expected_window": 1,
            "description": "Not recall - has recent temporal marker 'today'"
        },
        {
            "query": "we discussed this earlier",
            "expected_recall": False,
            "expected_intent": None,
            "expected_strategy": None,
            "expected_window": 1,
            "description": "Not recall - has recent temporal marker 'earlier'"
        },
        {
            "query": "what is prompt engineering",
            "expected_recall": False,
            "expected_intent": QueryIntent.FACTUAL_RECALL,
            "expected_strategy": VectorStrategy.SEMANTIC_FUSION,
            "expected_window": 1,
            "description": "Not recall - informational query"
        },
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info("\n" + "="*80)
        logger.info("Test Case %d/%d: %s", i, len(test_cases), test_case['description'])
        logger.info("Query: '%s'", test_case['query'])
        logger.info("Expected recall: %s", test_case['expected_recall'])
        logger.info("-" * 80)
        
        try:
            # Classify query
            result = await classifier.classify(
                query=test_case['query'],
                user_id="test_user_recall"
            )
            
            # Check recall detection
            logger.info("✓ is_recall_query: %s", result.is_recall_query)
            logger.info("✓ temporal_window_days: %d", result.temporal_window_days)
            logger.info("✓ intent_type: %s", result.intent_type)
            logger.info("✓ vector_strategy: %s", result.vector_strategy)
            logger.info("✓ intent_confidence: %.2f", result.intent_confidence)
            logger.info("✓ strategy_confidence: %.2f", result.strategy_confidence)
            
            # Validate expectations
            errors = []
            
            if result.is_recall_query != test_case['expected_recall']:
                errors.append(f"is_recall_query: expected {test_case['expected_recall']}, got {result.is_recall_query}")
            
            if result.temporal_window_days != test_case['expected_window']:
                errors.append(f"temporal_window_days: expected {test_case['expected_window']}, got {result.temporal_window_days}")
            
            if test_case['expected_intent'] and result.intent_type != test_case['expected_intent']:
                errors.append(f"intent_type: expected {test_case['expected_intent']}, got {result.intent_type}")
            
            if test_case['expected_strategy'] and result.vector_strategy != test_case['expected_strategy']:
                errors.append(f"vector_strategy: expected {test_case['expected_strategy']}, got {result.vector_strategy}")
            
            if errors:
                logger.error("❌ FAILED: %s", test_case['description'])
                for error in errors:
                    logger.error("   - %s", error)
                failed += 1
            else:
                logger.info("✅ PASSED: %s", test_case['description'])
                passed += 1
                
        except Exception as exc:
            logger.error("❌ EXCEPTION: %s", test_case['description'])
            logger.error("   Error: %s", str(exc))
            import traceback
            logger.error(traceback.format_exc())
            failed += 1
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    logger.info("Total: %d", len(test_cases))
    logger.info("Passed: %d ✅", passed)
    logger.info("Failed: %d ❌", failed)
    logger.info("Success Rate: %.1f%%", (passed/len(test_cases)*100))
    
    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! Recall detection working correctly.")
        return 0
    else:
        logger.error("\n⚠️ SOME TESTS FAILED. Review output above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_recall_detection())
    exit(exit_code)
