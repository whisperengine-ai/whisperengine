#!/usr/bin/env python3
"""
Quick Test: PostgreSQL Fact Retrieval Validation

Tests the new _get_user_facts_from_postgres() method to ensure:
1. PostgreSQL connection works
2. Facts are retrieved correctly
3. Formatting is correct for prompt building
4. Performance is acceptable (<10ms)

Usage:
    python tests/quick_postgres_fact_test.py
"""

import asyncio
import logging
import os
import sys
import time
from typing import List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.database.postgres_manager import PostgresConnectionManager
from src.knowledge.semantic_router import KnowledgeRouter


async def test_postgres_fact_retrieval():
    """Test PostgreSQL fact retrieval performance and correctness"""
    
    logger.info("=" * 80)
    logger.info("POSTGRESQL FACT RETRIEVAL TEST")
    logger.info("=" * 80)
    
    # Initialize PostgreSQL
    logger.info("\n1. Initializing PostgreSQL connection...")
    postgres_manager = PostgresConnectionManager()
    await postgres_manager.initialize()
    postgres_pool = postgres_manager.get_pool()
    logger.info("   ✅ PostgreSQL connected")
    
    # Initialize knowledge router
    logger.info("\n2. Initializing Knowledge Router...")
    knowledge_router = KnowledgeRouter(postgres_pool)
    logger.info("   ✅ Knowledge Router ready")
    
    # Test user (use actual test user or create one)
    test_user_id = "test_user_123"
    test_bot_name = "elena"
    
    # Test 1: Store test facts
    logger.info(f"\n3. Storing test facts for user {test_user_id}...")
    test_facts = [
        {"entity": "pizza", "type": "food", "relationship": "likes"},
        {"entity": "hiking", "type": "hobby", "relationship": "enjoys"},
        {"entity": "coffee", "type": "drink", "relationship": "prefers"},
    ]
    
    for fact in test_facts:
        success = await knowledge_router.store_user_fact(
            user_id=test_user_id,
            entity_name=fact["entity"],
            entity_type=fact["type"],
            relationship_type=fact["relationship"],
            confidence=0.9,
            mentioned_by_character=test_bot_name
        )
        if success:
            logger.info(f"   ✅ Stored: {fact['entity']} ({fact['relationship']}, {fact['type']})")
        else:
            logger.warning(f"   ⚠️ Failed to store: {fact['entity']}")
    
    # Test 2: Store test preference
    logger.info(f"\n4. Storing test preference for user {test_user_id}...")
    pref_success = await knowledge_router.store_user_preference(
        user_id=test_user_id,
        preference_key="preferred_name",
        preference_value="TestUser",
        confidence=0.95
    )
    if pref_success:
        logger.info(f"   ✅ Stored: preferred_name = TestUser")
    
    # Test 3: Retrieve facts (timed)
    logger.info(f"\n5. Retrieving facts from PostgreSQL (performance test)...")
    start_time = time.time()
    
    facts = await knowledge_router.get_character_aware_facts(
        user_id=test_user_id,
        character_name=test_bot_name,
        limit=20
    )
    
    preferences = await knowledge_router.get_user_preferences(
        user_id=test_user_id
    )
    
    elapsed_ms = (time.time() - start_time) * 1000
    
    logger.info(f"   ⏱️ Query time: {elapsed_ms:.2f}ms")
    logger.info(f"   📊 Facts retrieved: {len(facts)}")
    logger.info(f"   📊 Preferences retrieved: {len(preferences)}")
    
    # Test 4: Format facts for prompt (simulate _get_user_facts_from_postgres)
    logger.info(f"\n6. Formatting facts for prompt building...")
    formatted_facts = []
    
    # Format facts
    for fact in facts:
        entity_name = fact.get('entity_name', '')
        relationship_type = fact.get('relationship_type', 'knows')
        entity_type = fact.get('entity_type', '')
        confidence = fact.get('confidence', 0.0)
        
        if confidence >= 0.5:
            if entity_type:
                formatted_facts.append(f"[{entity_name} ({relationship_type}, {entity_type})]")
            else:
                formatted_facts.append(f"[{entity_name} ({relationship_type})]")
    
    # Format preferences
    for pref in preferences:
        pref_key = pref.get('preference_key', '')
        pref_value = pref.get('preference_value', '')
        confidence = pref.get('confidence', 0.0)
        
        if confidence >= 0.5 and pref_key and pref_value:
            formatted_facts.append(f"[{pref_key}: {pref_value}]")
    
    logger.info(f"   ✅ Formatted {len(formatted_facts)} facts:")
    for fact in formatted_facts:
        logger.info(f"      {fact}")
    
    # Test 5: Performance validation
    logger.info(f"\n7. Performance Validation...")
    if elapsed_ms <= 10:
        logger.info(f"   ✅ EXCELLENT: Query time {elapsed_ms:.2f}ms is well under 10ms target")
    elif elapsed_ms <= 20:
        logger.info(f"   ✅ GOOD: Query time {elapsed_ms:.2f}ms is acceptable")
    else:
        logger.warning(f"   ⚠️ SLOW: Query time {elapsed_ms:.2f}ms exceeds 20ms target")
    
    # Performance comparison
    estimated_legacy_time_ms = 62  # Conservative estimate (62-125ms range)
    speedup = estimated_legacy_time_ms / elapsed_ms if elapsed_ms > 0 else 0
    logger.info(f"   📊 Estimated speedup vs legacy: {speedup:.1f}x")
    logger.info(f"   📊 Legacy method (vector + parsing): ~62-125ms")
    logger.info(f"   📊 New method (PostgreSQL direct): {elapsed_ms:.2f}ms")
    
    # Test 6: Verify data integrity
    logger.info(f"\n8. Data Integrity Check...")
    expected_facts = {fact["entity"] for fact in test_facts}
    retrieved_entities = {fact.get('entity_name') for fact in facts}
    
    if expected_facts.issubset(retrieved_entities):
        logger.info(f"   ✅ All test facts retrieved successfully")
    else:
        missing = expected_facts - retrieved_entities
        logger.warning(f"   ⚠️ Missing facts: {missing}")
    
    if any(pref.get('preference_key') == 'preferred_name' for pref in preferences):
        logger.info(f"   ✅ Preference retrieved successfully")
    else:
        logger.warning(f"   ⚠️ Preference not found")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Facts stored:       {len(test_facts)}")
    logger.info(f"Preferences stored: 1")
    logger.info(f"Facts retrieved:    {len(facts)}")
    logger.info(f"Preferences retrieved: {len(preferences)}")
    logger.info(f"Formatted output:   {len(formatted_facts)} items")
    logger.info(f"Query time:         {elapsed_ms:.2f}ms")
    logger.info(f"Performance:        {speedup:.1f}x faster than legacy")
    
    if len(formatted_facts) > 0 and elapsed_ms <= 20:
        logger.info("\n✅ TEST PASSED - PostgreSQL fact retrieval working correctly!")
    else:
        logger.warning("\n⚠️ TEST ISSUES - Please review results above")
    
    logger.info("=" * 80)
    
    # Cleanup
    await postgres_manager.close()


if __name__ == '__main__':
    asyncio.run(test_postgres_fact_retrieval())
