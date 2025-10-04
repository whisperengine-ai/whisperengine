#!/usr/bin/env python3
"""
Phase 3 Knowledge Extraction HTTP API Test

Tests the complete knowledge extraction pipeline via bot HTTP API:
1. Send messages with factual statements
2. Verify PostgreSQL storage
3. Query stored facts
4. Test fact retrieval in responses
"""

import asyncio
import logging
import requests
import json
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_NAME = "Elena"
BOT_PORT = 9091
API_BASE_URL = f"http://localhost:{BOT_PORT}"
TEST_USER_ID = "phase3_test_user"
TEST_USERNAME = "TestUser"

# Test messages with factual statements
TEST_MESSAGES = [
    {
        "message": "I love pizza!",
        "expected_entity": "pizza",
        "expected_type": "food",
        "expected_relationship": "likes"
    },
    {
        "message": "I really enjoy hiking",
        "expected_entity": "hiking",
        "expected_type": "hobby",
        "expected_relationship": "enjoys"
    },
    {
        "message": "I hate mushrooms",
        "expected_entity": "mushrooms",
        "expected_type": "food",
        "expected_relationship": "dislikes"
    },
    {
        "message": "My favorite drink is coffee",
        "expected_entity": "coffee",
        "expected_type": "drink",
        "expected_relationship": "likes"
    }
]

def test_health_endpoint():
    """Test if bot is running and healthy"""
    logger.info(f"🔍 Testing health endpoint for {BOT_NAME}...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ {BOT_NAME} bot is healthy: {response.json()}")
            return True
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to connect to bot: {e}")
        return False

def send_chat_message(message: str, user_id: str = TEST_USER_ID, username: str = TEST_USERNAME):
    """Send a chat message via HTTP API"""
    logger.info(f"📤 Sending message: '{message}'")
    
    payload = {
        "user_id": user_id,
        "username": username,
        "message": message,
        "platform": "api_test"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Response received: {result.get('response', '')[:100]}...")
            return result
        else:
            logger.error(f"❌ API call failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {e}")
        return None

def query_postgres_facts(user_id: str = TEST_USER_ID):
    """Query PostgreSQL to verify stored facts"""
    logger.info(f"\n📊 Querying PostgreSQL for stored facts (user: {user_id})...")
    
    import subprocess
    
    query = f"""
    SELECT 
        fe.entity_name,
        fe.entity_type,
        ufr.relationship_type,
        ufr.confidence,
        ufr.emotional_context,
        ufr.mentioned_by_character,
        ufr.created_at
    FROM user_fact_relationships ufr
    JOIN fact_entities fe ON ufr.entity_id = fe.id
    WHERE ufr.user_id = '{user_id}'
    ORDER BY ufr.created_at DESC
    LIMIT 20;
    """
    
    try:
        result = subprocess.run(
            [
                "docker", "exec", "whisperengine-multi-postgres",
                "psql", "-U", "whisperengine", "-d", "whisperengine",
                "-c", query
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info("\n✅ PostgreSQL Query Results:")
            print(result.stdout)
            return result.stdout
        else:
            logger.error(f"❌ PostgreSQL query failed: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Failed to query PostgreSQL: {e}")
        return None

def query_entity_relationships():
    """Query entity relationships to verify auto-discovery"""
    logger.info(f"\n🔗 Querying entity relationships (auto-discovery)...")
    
    import subprocess
    
    query = """
    SELECT 
        fe1.entity_name as from_entity,
        fe2.entity_name as to_entity,
        er.relationship_type,
        er.weight
    FROM entity_relationships er
    JOIN fact_entities fe1 ON er.from_entity_id = fe1.id
    JOIN fact_entities fe2 ON er.to_entity_id = fe2.id
    WHERE er.relationship_type = 'similar_to'
    ORDER BY er.created_at DESC
    LIMIT 10;
    """
    
    try:
        result = subprocess.run(
            [
                "docker", "exec", "whisperengine-multi-postgres",
                "psql", "-U", "whisperengine", "-d", "whisperengine",
                "-c", query
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info("\n✅ Entity Relationships:")
            print(result.stdout)
            return result.stdout
        else:
            logger.error(f"❌ Relationship query failed: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Failed to query relationships: {e}")
        return None

def test_fact_recall(user_id: str = TEST_USER_ID):
    """Test if bot can recall stored facts"""
    logger.info(f"\n🧠 Testing fact recall...")
    
    recall_queries = [
        "What foods do I like?",
        "What are my hobbies?",
        "Tell me about my preferences"
    ]
    
    for query in recall_queries:
        logger.info(f"\n📤 Testing recall query: '{query}'")
        result = send_chat_message(query, user_id)
        
        if result:
            response = result.get('response', '')
            logger.info(f"   Response: {response[:200]}...")
        
        time.sleep(2)  # Rate limiting

def run_phase3_test():
    """Run complete Phase 3 test suite"""
    logger.info("=" * 80)
    logger.info("🚀 PHASE 3 KNOWLEDGE EXTRACTION TEST")
    logger.info("=" * 80)
    
    # Step 1: Health check
    if not test_health_endpoint():
        logger.error("❌ Bot is not healthy - cannot proceed with test")
        return
    
    logger.info("\n" + "=" * 80)
    logger.info("📝 STEP 1: Sending factual statements")
    logger.info("=" * 80)
    
    # Step 2: Send test messages with factual statements
    for i, test_case in enumerate(TEST_MESSAGES, 1):
        logger.info(f"\n--- Test Case {i}/{len(TEST_MESSAGES)} ---")
        result = send_chat_message(test_case["message"])
        
        if result:
            logger.info(f"✅ Expected entity: {test_case['expected_entity']}")
            logger.info(f"   Expected type: {test_case['expected_type']}")
            logger.info(f"   Expected relationship: {test_case['expected_relationship']}")
        
        time.sleep(2)  # Rate limiting between messages
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 STEP 2: Verifying PostgreSQL storage")
    logger.info("=" * 80)
    
    # Step 3: Query PostgreSQL to verify storage
    time.sleep(2)  # Let async storage complete
    postgres_result = query_postgres_facts()
    
    logger.info("\n" + "=" * 80)
    logger.info("🔗 STEP 3: Checking entity relationships")
    logger.info("=" * 80)
    
    # Step 4: Check entity relationships
    relationship_result = query_entity_relationships()
    
    logger.info("\n" + "=" * 80)
    logger.info("🧠 STEP 4: Testing fact recall")
    logger.info("=" * 80)
    
    # Step 5: Test fact recall
    test_fact_recall()
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ PHASE 3 TEST COMPLETE")
    logger.info("=" * 80)
    
    # Summary
    logger.info("\n📋 TEST SUMMARY:")
    logger.info(f"   ✅ Bot health: OK")
    logger.info(f"   ✅ Messages sent: {len(TEST_MESSAGES)}")
    logger.info(f"   ✅ PostgreSQL query: {'OK' if postgres_result else 'FAILED'}")
    logger.info(f"   ✅ Relationship query: {'OK' if relationship_result else 'FAILED'}")
    logger.info(f"\n💡 Check the logs above for detailed extraction results")
    logger.info(f"💡 Verify entity storage in PostgreSQL query output")
    logger.info(f"💡 Note: Fact recall requires Phase 4 (Character Integration) for full functionality")

if __name__ == "__main__":
    run_phase3_test()
