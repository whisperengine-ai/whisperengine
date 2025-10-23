"""
Phase 2d: Unified Query Classification - Comprehensive Integration Tests

Validates that UnifiedQueryClassifier is properly integrated across:
1. SemanticKnowledgeRouter.analyze_query_intent()
2. VectorMemoryManager.retrieve_relevant_memories_with_classification()
3. MessageProcessor._retrieve_memories_with_multi_vector_intelligence()

Tests ensure single authoritative classification throughout pipeline.
"""

import asyncio
import logging
from typing import Dict, Any

# Test infrastructure
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEST 1: UnifiedQueryClassifier Direct Usage
# ============================================================================

async def test_unified_classifier_direct():
    """Test UnifiedQueryClassifier directly with all 7 intent types."""
    from src.memory.unified_query_classification import (
        UnifiedQueryClassifier,
        QueryIntent,
        VectorStrategy,
    )
    
    logger.info("="*80)
    logger.info("TEST 1: UnifiedQueryClassifier Direct Usage")
    logger.info("="*80)
    
    classifier = UnifiedQueryClassifier()
    
    test_cases = [
        ("What foods do I like?", QueryIntent.FACTUAL_RECALL, "basic factual query"),
        ("How did we talk about philosophy?", QueryIntent.CONVERSATION_STYLE, "conversation recall"),
        ("How have my interests changed?", QueryIntent.TEMPORAL_ANALYSIS, "temporal trends"),
        ("Tell me about Elena's background", QueryIntent.PERSONALITY_KNOWLEDGE, "character info"),
        ("Find something similar to coffee", QueryIntent.RELATIONSHIP_DISCOVERY, "entity discovery"),
        ("Search for Tokyo mentions", QueryIntent.ENTITY_SEARCH, "entity search"),
        ("What do you know about me?", QueryIntent.USER_ANALYTICS, "user analytics"),
    ]
    
    results = []
    for query, expected_intent, description in test_cases:
        result = await classifier.classify(query)
        matches = result.intent_type == expected_intent
        status = "✅" if matches else "⚠️ "
        results.append({
            "query": query[:40],
            "expected": expected_intent.value,
            "actual": result.intent_type.value,
            "confidence": result.intent_confidence,
            "strategy": result.vector_strategy.value,
            "matches": matches,
            "description": description
        })
        logger.info(
            "%s [%s] → %s (confidence: %.2f, strategy: %s)",
            status,
            description,
            result.intent_type.value,
            result.intent_confidence,
            result.vector_strategy.value
        )
    
    # Summary
    matched = sum(1 for r in results if r['matches'])
    total = len(results)
    logger.info("Result: %d/%d intents correctly classified", matched, total)
    
    return matched, total


# ============================================================================
# TEST 2: SemanticKnowledgeRouter Integration
# ============================================================================

async def test_semantic_router_integration():
    """Test that SemanticKnowledgeRouter.analyze_query_intent() uses unified classifier."""
    from src.knowledge.semantic_router import SemanticKnowledgeRouter
    from src.memory.unified_query_classification import QueryIntent
    
    logger.info("="*80)
    logger.info("TEST 2: SemanticKnowledgeRouter Integration")
    logger.info("="*80)
    
    # Initialize router (can pass None for postgres_pool for this test)
    try:
        router = SemanticKnowledgeRouter(postgres_pool=None)
        logger.info("✅ SemanticKnowledgeRouter initialized")
    except Exception as e:
        logger.error("❌ Failed to initialize SemanticKnowledgeRouter: %s", str(e))
        return False
    
    # Test analyze_query_intent with unified classifier
    test_queries = [
        ("What foods do I like?", QueryIntent.FACTUAL_RECALL),
        ("How did we talk about it?", QueryIntent.CONVERSATION_STYLE),
        ("How have things changed recently?", QueryIntent.TEMPORAL_ANALYSIS),
    ]
    
    all_pass = True
    for query, expected_intent in test_queries:
        try:
            result = await router.analyze_query_intent(query)
            matches = result.intent_type.value == expected_intent.value
            status = "✅" if matches else "⚠️ "
            
            if matches:
                logger.info(
                    "%s SemanticRouter correctly classified '%s' as %s",
                    status,
                    query[:30],
                    result.intent_type.value
                )
            else:
                logger.warning(
                    "%s SemanticRouter classified '%s' as %s (expected %s)",
                    status,
                    query[:30],
                    result.intent_type.value,
                    expected_intent.value
                )
                all_pass = False
        except Exception as e:
            logger.error("❌ SemanticRouter.analyze_query_intent() failed: %s", str(e))
            all_pass = False
    
    return all_pass


# ============================================================================
# TEST 3: VectorMemoryManager Integration
# ============================================================================

async def test_vector_memory_manager_integration():
    """Test that VectorMemoryManager uses unified classifier."""
    logger.info("="*80)
    logger.info("TEST 3: VectorMemoryManager Integration")
    logger.info("="*80)
    
    try:
        # Check that VectorMemoryManager initializes unified classifier
        from src.memory.vector_memory_system import VectorMemoryManager
        import inspect
        
        # Read source to check initialization
        source = inspect.getsource(VectorMemoryManager.__init__)
        has_unified = '_unified_query_classifier' in source
        
        if has_unified:
            logger.info("✅ VectorMemoryManager.__init__() initializes unified classifier")
        else:
            logger.error("❌ VectorMemoryManager.__init__() does not initialize unified classifier")
            return False
        
        # Check retrieve method uses unified classifier
        retrieve_source = inspect.getsource(VectorMemoryManager.retrieve_relevant_memories_with_classification)
        uses_unified = 'await self._unified_query_classifier' in retrieve_source
        
        if uses_unified:
            logger.info("✅ VectorMemoryManager.retrieve_relevant_memories_with_classification() uses unified classifier")
            return True
        else:
            logger.error("❌ VectorMemoryManager does not use unified classifier in retrieve method")
            return False
            
    except Exception as e:
        logger.error("❌ Failed to check VectorMemoryManager: %s", str(e))
        return False


# ============================================================================
# TEST 4: MessageProcessor Integration
# ============================================================================

async def test_message_processor_integration():
    """Test that MessageProcessor uses unified classifier."""
    logger.info("="*80)
    logger.info("TEST 4: MessageProcessor Integration")
    logger.info("="*80)
    
    try:
        from src.core.message_processor import MessageProcessor
        import inspect
        
        # Check __init__ initializes unified classifier
        init_source = inspect.getsource(MessageProcessor.__init__)
        has_unified_init = '_unified_query_classifier' in init_source and 'create_unified_query_classifier' in init_source
        
        if has_unified_init:
            logger.info("✅ MessageProcessor.__init__() initializes unified classifier")
        else:
            logger.error("❌ MessageProcessor.__init__() does not initialize unified classifier")
            return False
        
        # Check memory retrieval method uses unified classifier
        memory_source = inspect.getsource(MessageProcessor._retrieve_memories_with_multi_vector_intelligence)
        uses_unified = 'await self._unified_query_classifier.classify' in memory_source
        has_fallback = 'MultiVectorIntelligence' in memory_source and 'FALLBACK' in memory_source
        
        if uses_unified:
            logger.info("✅ MessageProcessor._retrieve_memories uses unified classifier")
        else:
            logger.error("❌ MessageProcessor._retrieve_memories does not use unified classifier")
            return False
        
        if has_fallback:
            logger.info("✅ MessageProcessor has graceful fallback to MultiVectorIntelligence")
        else:
            logger.error("❌ MessageProcessor missing fallback logic")
            return False
        
        return True
            
    except Exception as e:
        logger.error("❌ Failed to check MessageProcessor: %s", str(e))
        return False


# ============================================================================
# TEST 5: Routing Strategy Mapping
# ============================================================================

async def test_routing_strategy_mapping():
    """Test that all VectorStrategy values are properly mapped."""
    logger.info("="*80)
    logger.info("TEST 5: Routing Strategy Mapping")
    logger.info("="*80)
    
    from src.memory.unified_query_classification import VectorStrategy
    from src.core.message_processor import UnifiedVectorStrategy
    
    # Check all UnifiedVectorStrategy values exist
    expected_strategies = [
        'EMOTION_FUSION',
        'SEMANTIC_FUSION',
        'BALANCED_FUSION',
        'TEMPORAL_CHRONOLOGICAL',
        'CONTENT_ONLY',
        'MULTI_CATEGORY'
    ]
    
    all_strategies_present = True
    for strategy_name in expected_strategies:
        if hasattr(UnifiedVectorStrategy, strategy_name):
            logger.info("✅ UnifiedVectorStrategy.%s present", strategy_name)
        else:
            logger.error("❌ UnifiedVectorStrategy.%s missing", strategy_name)
            all_strategies_present = False
    
    return all_strategies_present


# ============================================================================
# TEST 6: Backward Compatibility
# ============================================================================

async def test_backward_compatibility():
    """Test that old code paths still work (fallbacks)."""
    logger.info("="*80)
    logger.info("TEST 6: Backward Compatibility - Fallback Paths")
    logger.info("="*80)
    
    try:
        # Check that MultiVectorIntelligence import still works
        from src.memory.multi_vector_intelligence import VectorStrategy as OldVectorStrategy
        logger.info("✅ Old MultiVectorIntelligence VectorStrategy enum still available")
        
        # Check that old classification adapter works
        from src.memory.query_classifier_adapter import QueryClassifierAdapter
        logger.info("✅ QueryClassifierAdapter available for backward compat")
        
        return True
    except Exception as e:
        logger.error("❌ Backward compatibility issue: %s", str(e))
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all Phase 2d integration tests."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 2d: UNIFIED QUERY CLASSIFICATION - INTEGRATION TEST SUITE")
    logger.info("="*80 + "\n")
    
    results = {}
    
    # Test 1: Direct classifier
    try:
        matched, total = await test_unified_classifier_direct()
        results['test_unified_classifier'] = {'pass': matched == total, 'matched': matched, 'total': total}
    except Exception as e:
        logger.error("Test 1 failed: %s", str(e))
        results['test_unified_classifier'] = {'pass': False, 'error': str(e)}
    
    # Test 2: SemanticKnowledgeRouter
    try:
        passed = await test_semantic_router_integration()
        results['test_semantic_router'] = {'pass': passed}
    except Exception as e:
        logger.error("Test 2 failed: %s", str(e))
        results['test_semantic_router'] = {'pass': False, 'error': str(e)}
    
    # Test 3: VectorMemoryManager
    try:
        passed = await test_vector_memory_manager_integration()
        results['test_vector_memory_manager'] = {'pass': passed}
    except Exception as e:
        logger.error("Test 3 failed: %s", str(e))
        results['test_vector_memory_manager'] = {'pass': False, 'error': str(e)}
    
    # Test 4: MessageProcessor
    try:
        passed = await test_message_processor_integration()
        results['test_message_processor'] = {'pass': passed}
    except Exception as e:
        logger.error("Test 4 failed: %s", str(e))
        results['test_message_processor'] = {'pass': False, 'error': str(e)}
    
    # Test 5: Strategy mapping
    try:
        passed = await test_routing_strategy_mapping()
        results['test_routing_strategy'] = {'pass': passed}
    except Exception as e:
        logger.error("Test 5 failed: %s", str(e))
        results['test_routing_strategy'] = {'pass': False, 'error': str(e)}
    
    # Test 6: Backward compatibility
    try:
        passed = await test_backward_compatibility()
        results['test_backward_compat'] = {'pass': passed}
    except Exception as e:
        logger.error("Test 6 failed: %s", str(e))
        results['test_backward_compat'] = {'pass': False, 'error': str(e)}
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("PHASE 2d TEST SUMMARY")
    logger.info("="*80)
    
    passed_tests = sum(1 for r in results.values() if r.get('pass', False))
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result.get('pass', False) else "❌ FAIL"
        logger.info("%s: %s", status, test_name)
        if 'error' in result:
            logger.info("  Error: %s", result['error'])
    
    logger.info("\n%s: %d/%d tests passed", 
        "✅ SUCCESS" if passed_tests == total_tests else "⚠️  PARTIAL",
        passed_tests,
        total_tests)
    logger.info("="*80 + "\n")
    
    return passed_tests == total_tests


if __name__ == '__main__':
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
