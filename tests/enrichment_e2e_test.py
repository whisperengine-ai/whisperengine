#!/usr/bin/env python3
"""
End-to-End Enrichment Worker Test

Tests the complete flow:
1. Send HTTP chat messages to Elena bot
2. Wait for enrichment worker to process
3. Verify conversation summaries created
4. Verify facts extracted (if any)
"""

import asyncio
import requests
import json
import time
from datetime import datetime
import psycopg2

# Test configuration
ELENA_PORT = 9091
ELENA_BOT_NAME = "elena"
TEST_USER_ID = f"enrichment_test_{int(time.time())}"

# Conversation designed to trigger fact extraction
TEST_CONVERSATION = [
    {
        "message": "Hi Elena! I'm really excited to chat with you today.",
        "expected_facts": []
    },
    {
        "message": "I love marine biology! I've been fascinated by ocean life since I was a kid.",
        "expected_facts": ["loves marine biology", "interested in ocean life"]
    },
    {
        "message": "My favorite marine animal is the octopus - they're so intelligent!",
        "expected_facts": ["favorite animal is octopus", "thinks octopuses are intelligent"]
    },
    {
        "message": "I also really enjoy scuba diving. I've been diving for about 5 years now.",
        "expected_facts": ["enjoys scuba diving", "has been diving for 5 years"]
    },
    {
        "message": "I'm planning to visit the Great Barrier Reef next summer!",
        "expected_facts": ["planning to visit Great Barrier Reef", "traveling next summer"]
    },
    {
        "message": "Do you have any recommendations for the best dive sites there?",
        "expected_facts": []
    },
]

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "whisperengine",
    "user": "whisperengine",
    "password": "whisperengine_password"
}


def send_chat_message(user_id: str, message: str) -> dict:
    """Send a chat message to Elena via HTTP API"""
    url = f"http://localhost:{ELENA_PORT}/api/chat"
    payload = {
        "user_id": user_id,
        "message": message,
        "metadata": {
            "platform": "enrichment_e2e_test",
            "channel_type": "dm"
        }
    }
    
    print(f"📤 Sending: {message[:60]}...")
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    print(f"✅ Response: {result.get('response', '')[:80]}...")
    return result


def check_conversation_summaries(user_id: str, bot_name: str) -> list:
    """Check if conversation summaries exist for this user"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, summary_text, message_count, key_topics, 
               emotional_tone, created_at
        FROM conversation_summaries
        WHERE user_id = %s AND bot_name = %s
        ORDER BY created_at DESC
    """, (user_id, bot_name))
    
    summaries = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return summaries


def check_extracted_facts(user_id: str) -> list:
    """Check if facts were extracted for this user"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT fe.entity_name, fe.entity_type, fe.category,
               ufr.relationship_type, ufr.confidence,
               ufr.context_metadata->>'extraction_method' as extraction_method,
               ufr.created_at
        FROM user_fact_relationships ufr
        JOIN fact_entities fe ON ufr.entity_id = fe.id
        WHERE ufr.user_id = %s
        ORDER BY ufr.created_at DESC
    """, (user_id,))
    
    facts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return facts


def main():
    print("=" * 80)
    print("🧪 ENRICHMENT WORKER END-TO-END TEST")
    print("=" * 80)
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Bot: {ELENA_BOT_NAME} (Port {ELENA_PORT})")
    print(f"Messages to send: {len(TEST_CONVERSATION)}")
    print("=" * 80)
    
    # Step 1: Send conversation messages
    print("\n📝 STEP 1: Sending conversation messages...")
    print("-" * 80)
    
    for i, turn in enumerate(TEST_CONVERSATION, 1):
        print(f"\n[{i}/{len(TEST_CONVERSATION)}]")
        try:
            send_chat_message(TEST_USER_ID, turn["message"])
            time.sleep(2)  # Brief pause between messages
        except Exception as e:
            print(f"❌ ERROR sending message: {e}")
            return 1
    
    print("\n✅ All messages sent successfully!")
    
    # Step 2: Check for inline fact extraction (immediate)
    print("\n" + "=" * 80)
    print("🔍 STEP 2: Checking inline fact extraction (immediate)...")
    print("-" * 80)
    
    inline_facts = check_extracted_facts(TEST_USER_ID)
    print(f"\n📊 Found {len(inline_facts)} facts from inline extraction:")
    
    for fact in inline_facts[:10]:  # Show first 10
        entity_name, entity_type, category, rel_type, confidence, method, created = fact
        print(f"  • {entity_name} ({entity_type}) - {rel_type} - "
              f"confidence={confidence:.2f} - method={method or 'inline'}")
    
    if len(inline_facts) > 10:
        print(f"  ... and {len(inline_facts) - 10} more facts")
    
    # Step 3: Wait for enrichment worker cycle
    print("\n" + "=" * 80)
    print("⏳ STEP 3: Waiting for enrichment worker to process...")
    print("-" * 80)
    print("Enrichment worker runs every 5 minutes (300 seconds)")
    print("We'll check every 30 seconds for up to 6 minutes...")
    
    max_wait_time = 360  # 6 minutes
    check_interval = 30  # Check every 30 seconds
    elapsed = 0
    
    summaries_found = False
    
    while elapsed < max_wait_time:
        time.sleep(check_interval)
        elapsed += check_interval
        
        print(f"\n⏱️  Elapsed: {elapsed}s / {max_wait_time}s - Checking for summaries...")
        
        summaries = check_conversation_summaries(TEST_USER_ID, ELENA_BOT_NAME)
        
        if summaries:
            summaries_found = True
            print(f"✅ Found {len(summaries)} conversation summaries!")
            break
        else:
            print("⏳ No summaries yet, waiting...")
    
    # Step 4: Verify results
    print("\n" + "=" * 80)
    print("📊 STEP 4: FINAL RESULTS")
    print("=" * 80)
    
    # Check summaries
    summaries = check_conversation_summaries(TEST_USER_ID, ELENA_BOT_NAME)
    print(f"\n📝 Conversation Summaries: {len(summaries)}")
    
    if summaries:
        for i, summary in enumerate(summaries, 1):
            summary_id, text, msg_count, topics, tone, created = summary
            print(f"\n  Summary #{i}:")
            print(f"    ID: {summary_id}")
            print(f"    Messages: {msg_count}")
            print(f"    Topics: {topics}")
            print(f"    Tone: {tone}")
            print(f"    Summary: {text[:200]}...")
            print(f"    Created: {created}")
    else:
        print("  ❌ No summaries found!")
        print("  This might mean:")
        print("    - Enrichment worker hasn't run yet (runs every 5 minutes)")
        print("    - Not enough messages for summary (min 5 messages)")
        print("    - User ID mismatch or configuration issue")
    
    # Check all facts (inline + enrichment)
    all_facts = check_extracted_facts(TEST_USER_ID)
    print(f"\n🧠 Total Facts Extracted: {len(all_facts)}")
    
    # Separate by extraction method
    inline_facts = [f for f in all_facts if f[5] != 'enrichment_worker']
    enrichment_facts = [f for f in all_facts if f[5] == 'enrichment_worker']
    
    print(f"  • Inline extraction: {len(inline_facts)} facts")
    print(f"  • Enrichment worker: {len(enrichment_facts)} facts")
    
    if all_facts:
        print("\n  📋 All extracted facts:")
        for fact in all_facts:
            entity_name, entity_type, category, rel_type, confidence, method, created = fact
            source = "🔧 ENRICHMENT" if method == 'enrichment_worker' else "⚡ INLINE"
            print(f"    {source} | {entity_name} ({entity_type}) - {rel_type} - "
                  f"confidence={confidence:.2f}")
    
    # Step 5: Summary
    print("\n" + "=" * 80)
    print("🎯 TEST SUMMARY")
    print("=" * 80)
    
    success = True
    
    print(f"\n✅ Messages sent: {len(TEST_CONVERSATION)}/{len(TEST_CONVERSATION)}")
    
    if inline_facts:
        print(f"✅ Inline fact extraction: {len(inline_facts)} facts")
    else:
        print("⚠️  Inline fact extraction: No facts extracted")
    
    if summaries:
        print(f"✅ Conversation summaries: {len(summaries)} summaries created")
    else:
        print("❌ Conversation summaries: No summaries found")
        success = False
    
    if enrichment_facts:
        print(f"✅ Enrichment fact extraction: {len(enrichment_facts)} facts")
    else:
        print("⚠️  Enrichment fact extraction: No new facts (inline extraction may have covered everything)")
    
    print("\n" + "=" * 80)
    
    if success:
        print("🎉 TEST PASSED - Enrichment worker is processing messages!")
    else:
        print("⚠️  TEST INCOMPLETE - Summaries not generated yet")
        print("   Try running again or wait for next enrichment cycle")
    
    print("=" * 80)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
