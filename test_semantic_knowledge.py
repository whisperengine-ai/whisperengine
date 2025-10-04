#!/usr/bin/env python3
"""
Quick test script for semantic knowledge integration.
Tests fact storage and retrieval via Elena bot API.
"""

import asyncio
import httpx
import json

ELENA_API = "http://localhost:9091/api/chat"
TEST_USER_ID = "test_user_semantic_001"

async def test_fact_storage_and_retrieval():
    """Test complete flow: store facts, then retrieve them"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("SEMANTIC KNOWLEDGE INTEGRATION TEST")
        print("=" * 60)
        
        # Test 1: Store some facts
        print("\n[TEST 1] Storing facts...")
        facts_to_store = [
            "I love pizza",
            "I really enjoy hiking", 
            "I visited Tokyo last year"
        ]
        
        for fact in facts_to_store:
            print(f"  → Sending: '{fact}'")
            response = await client.post(ELENA_API, json={
                "user_id": TEST_USER_ID,
                "message": fact
            })
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Response: {result.get('response', '')[:100]}...")
            else:
                print(f"  ❌ Failed: {response.status_code}")
        
        # Wait a moment for processing
        await asyncio.sleep(2)
        
        # Test 2: Retrieve facts with factual query
        print("\n[TEST 2] Retrieving facts with factual queries...")
        factual_queries = [
            "What foods do I like?",
            "What do you know about my hobbies?",
            "Where have I traveled?"
        ]
        
        for query in factual_queries:
            print(f"\n  → Query: '{query}'")
            response = await client.post(ELENA_API, json={
                "user_id": TEST_USER_ID,
                "message": query
            })
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                print(f"  ✅ Elena's Response:\n  {response_text[:300]}...")
                
                # Check if response seems to use facts
                if any(keyword in response_text.lower() for keyword in ['pizza', 'hiking', 'tokyo']):
                    print("  ✓ Response appears to include stored facts!")
                else:
                    print("  ⚠️  Response doesn't mention stored facts")
            else:
                print(f"  ❌ Failed: {response.status_code}")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_fact_storage_and_retrieval())
