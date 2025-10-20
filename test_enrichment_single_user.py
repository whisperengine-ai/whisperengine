#!/usr/bin/env python3
"""
Test fact extraction with single user to diagnose 468-token mystery.
Calls fact extraction engine directly to see debug output.
"""
import asyncio
import os
import sys

# Set up environment
os.environ['FASTEMBED_CACHE_PATH'] = '/tmp/fastembed_cache'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['DISCORD_BOT_NAME'] = 'elena'
os.environ['LLM_MAX_TOKENS_CHAT'] = '3000'
os.environ['LLM_API_KEY'] = os.getenv('OPENROUTER_API_KEY', '')
os.environ['LLM_API_URL'] = 'https://openrouter.ai/api/v1'

# Add src to path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

from src.enrichment.fact_extraction_engine import FactExtractionEngine
from src.llm.llm_protocol import create_llm_client
from qdrant_client import QdrantClient
import logging

# Configure logging to see ALL output including WARNING level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_fact_extraction():
    """Test fact extraction with ONE user's messages"""
    
    print("=" * 80)
    print("🔍 TESTING FACT EXTRACTION - SINGLE USER")
    print("=" * 80)
    
    # Initialize LLM client
    llm_client = create_llm_client(
        llm_client_type="openrouter",
        api_url='https://openrouter.ai/api/v1',
        api_key=os.getenv('OPENROUTER_API_KEY')
    )
    
    # Initialize fact extraction engine
    extractor = FactExtractionEngine(
        llm_client=llm_client,
        model='anthropic/claude-3.5-sonnet'
    )
    
    # Get messages from Qdrant for ONE user
    qdrant = QdrantClient(host='localhost', port=6334)
    
    collection_name = 'whisperengine_memory_elena'
    
    # Get ONE user with some messages
    scroll_result = qdrant.scroll(
        collection_name=collection_name,
        scroll_filter={
            "must": [
                {"key": "memory_type", "match": {"value": "user_message"}}
            ]
        },
        limit=1,
        with_payload=True
    )
    
    if not scroll_result[0]:
        print("❌ No messages found")
        return
    
    user_id = scroll_result[0][0].payload.get('user_id')
    print(f"\n📊 Test User: {user_id}")
    
    # Get last 10 messages for this user
    scroll_result = qdrant.scroll(
        collection_name=collection_name,
        scroll_filter={
            "must": [
                {"key": "user_id", "match": {"value": user_id}}
            ]
        },
        limit=10,
        with_payload=True,
        order_by={"key": "timestamp", "direction": "desc"}
    )
    
    messages = []
    for point in scroll_result[0]:
        messages.append({
            'memory_type': point.payload.get('memory_type'),
            'content': point.payload.get('content'),
            'timestamp': point.payload.get('timestamp')
        })
    
    messages.reverse()  # Chronological order
    
    print(f"📊 Retrieved {len(messages)} messages")
    print(f"\n🚀 Starting fact extraction with aggressive debug logging...\n")
    
    # Extract facts - this should show all our 🔍 debug output
    facts = await extractor.extract_facts_from_conversation_window(
        messages=messages,
        user_id=user_id,
        bot_name='elena'
    )
    
    print("\n" + "=" * 80)
    print(f"✅ Extraction complete: {len(facts)} facts found")
    print("=" * 80)
    print("\n📋 Check logs above for 🔍 debug output showing:")
    print("  1. Message count entering _format_conversation_window()")
    print("  2. Sample message structure")
    print("  3. Formatted conversation length and preview")
    print("  4. Final prompt size vs conversation size")
    print("  5. LLM response preview")

if __name__ == '__main__':
    asyncio.run(test_fact_extraction())

