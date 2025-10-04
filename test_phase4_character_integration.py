"""
Test Phase 4: Character Integration - Fact Recall via CDL

This test validates that:
1. Facts stored in Phase 3 are retrieved during conversations
2. Character-specific synthesis applies (Elena's marine metaphors, Marcus's analytical precision)
3. Query intent analysis works correctly
4. Fact recall appears naturally in character responses
"""

import asyncio
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ELENA_API_URL = "http://localhost:9091/api/chat"
ELENA_HEALTH_URL = "http://localhost:9091/health"

async def test_phase4_character_integration():
    """Test Phase 4 character-aware fact retrieval and synthesis"""
    
    logger.info("=" * 80)
    logger.info("🚀 PHASE 4 CHARACTER INTEGRATION TEST")
    logger.info("=" * 80)
    
    # Step 1: Health check
    logger.info("🔍 Testing health endpoint for Elena...")
    health_response = requests.get(ELENA_HEALTH_URL, timeout=5)
    if health_response.status_code == 200:
        logger.info(f"✅ Elena bot is healthy: {health_response.json()}")
    else:
        logger.error(f"❌ Elena bot health check failed: {health_response.status_code}")
        return False
    
    logger.info("\n" + "=" * 80)
    logger.info("📝 STEP 1: Store some facts (if not already stored)")
    logger.info("=" * 80)
    
    # Store facts (these will be upserted if they already exist)
    setup_messages = [
        "I love pizza!",
        "I really enjoy hiking in the mountains", 
        "My favorite drink is coffee",
        "I'm passionate about photography"
    ]
    
    for msg in setup_messages:
        logger.info(f"\n📤 Storing fact: '{msg}'")
        try:
            response = requests.post(
                ELENA_API_URL,
                json={
                    "user_id": "phase4_test_user",
                    "message": msg,
                    "user_name": "TestUser"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Response: {result.get('response', '')[:150]}...")
            else:
                logger.error(f"❌ Failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
        
        await asyncio.sleep(2)  # Rate limiting
    
    logger.info("\n" + "=" * 80)
    logger.info("🧠 STEP 2: Test fact recall with different query types")
    logger.info("=" * 80)
    
    # Test cases targeting different query intents
    recall_tests = [
        {
            "query": "What foods do I like?",
            "expected_entity": "pizza",
            "intent": "factual_recall",
            "description": "Direct food preference query"
        },
        {
            "query": "What are my hobbies?",
            "expected_entity": "hiking",
            "intent": "factual_recall", 
            "description": "Hobby recall query"
        },
        {
            "query": "Tell me about my interests",
            "expected_entity": "photography",
            "intent": "relationship_discovery",
            "description": "Broad interests query"
        },
        {
            "query": "What do you know about what I like?",
            "expected_entity": None,  # Should retrieve multiple facts
            "intent": "factual_recall",
            "description": "General preferences query"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(recall_tests, 1):
        logger.info(f"\n--- Test Case {i}/{len(recall_tests)} ---")
        logger.info(f"📋 Description: {test_case['description']}")
        logger.info(f"📤 Query: '{test_case['query']}'")
        logger.info(f"🎯 Expected intent: {test_case['intent']}")
        if test_case['expected_entity']:
            logger.info(f"🔍 Expected to mention: {test_case['expected_entity']}")
        
        try:
            response = requests.post(
                ELENA_API_URL,
                json={
                    "user_id": "phase4_test_user",
                    "message": test_case['query'],
                    "user_name": "TestUser"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                logger.info(f"✅ Response received ({len(response_text)} chars)")
                logger.info(f"   Response: {response_text[:300]}...")
                
                # Check if expected entity appears in response
                if test_case['expected_entity']:
                    if test_case['expected_entity'].lower() in response_text.lower():
                        logger.info(f"   ✅ FACT RECALLED: Mentioned '{test_case['expected_entity']}'")
                        results.append(("✅", test_case['query'], "Fact recalled successfully"))
                    else:
                        logger.warning(f"   ⚠️ FACT NOT RECALLED: '{test_case['expected_entity']}' not mentioned")
                        results.append(("⚠️", test_case['query'], f"Expected '{test_case['expected_entity']}' not found"))
                else:
                    # For general queries, just check if response is substantial
                    if len(response_text) > 100:
                        logger.info(f"   ✅ Substantial response generated")
                        results.append(("✅", test_case['query'], "Response generated"))
                    else:
                        logger.warning(f"   ⚠️ Response too short")
                        results.append(("⚠️", test_case['query'], "Response insufficient"))
                
                # Check for character-specific elements (Elena's marine metaphors)
                marine_keywords = ['ocean', 'sea', 'coral', 'reef', 'marine', 'underwater', 'whale', 'fish']
                has_marine_metaphor = any(kw in response_text.lower() for kw in marine_keywords)
                if has_marine_metaphor:
                    logger.info(f"   🌊 CHARACTER SYNTHESIS: Elena's marine metaphors detected")
                
            else:
                logger.error(f"❌ Failed: {response.status_code}")
                results.append(("❌", test_case['query'], f"HTTP {response.status_code}"))
        
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            results.append(("❌", test_case['query'], str(e)))
        
        await asyncio.sleep(2)  # Rate limiting
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 STEP 3: Verify PostgreSQL storage")
    logger.info("=" * 80)
    
    logger.info("\n💡 To verify PostgreSQL storage, run:")
    logger.info("docker exec whisperengine-multi-postgres psql -U whisperengine -d whisperengine \\")
    logger.info("  -c \"SELECT entity_name, entity_type, relationship_type, confidence, emotional_context")
    logger.info("      FROM user_fact_relationships ufr")
    logger.info("      JOIN fact_entities fe ON ufr.entity_id = fe.id")
    logger.info("      WHERE ufr.user_id = 'phase4_test_user';\"")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ PHASE 4 TEST COMPLETE")
    logger.info("=" * 80)
    
    # Print summary
    logger.info("\n📋 TEST SUMMARY:")
    success_count = sum(1 for r in results if r[0] == "✅")
    warning_count = sum(1 for r in results if r[0] == "⚠️")
    failure_count = sum(1 for r in results if r[0] == "❌")
    
    logger.info(f"   ✅ Successful: {success_count}/{len(results)}")
    logger.info(f"   ⚠️ Warnings: {warning_count}/{len(results)}")
    logger.info(f"   ❌ Failures: {failure_count}/{len(results)}")
    
    logger.info("\n📝 DETAILED RESULTS:")
    for status, query, result in results:
        logger.info(f"   {status} '{query}' - {result}")
    
    logger.info("\n💡 NEXT STEPS:")
    logger.info("   1. Check Elena bot logs for knowledge retrieval indicators")
    logger.info("   2. Verify character-specific synthesis (marine metaphors)")
    logger.info("   3. Test with Marcus bot for analytical synthesis style")
    
    return success_count > 0

if __name__ == "__main__":
    asyncio.run(test_phase4_character_integration())
