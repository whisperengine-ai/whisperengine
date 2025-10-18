#!/usr/bin/env python3
"""
Debug script to examine Aetheris memory for user Cynthia (1008886439108411472)
Check for repetitive content, looping patterns, and memory quality issues.
"""

import asyncio
import os
import sys
from datetime import datetime
from collections import Counter

# Set up environment
os.environ["FASTEMBED_CACHE_PATH"] = "/tmp/fastembed_cache"
os.environ["QDRANT_HOST"] = "localhost"
os.environ["QDRANT_PORT"] = "6334"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5433"
os.environ["DISCORD_BOT_NAME"] = "aetheris"

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue


async def analyze_aetheris_memories():
    """Analyze Aetheris memory for looping/repetitive content."""
    
    user_id = "1008886439108411472"
    collection_name = "whisperengine_memory_aetheris"
    
    print(f"\n{'='*80}")
    print(f"AETHERIS MEMORY ANALYSIS FOR USER: {user_id}")
    print(f"Collection: {collection_name}")
    print(f"{'='*80}\n")
    
    # Connect to Qdrant
    client = QdrantClient(host="localhost", port=6334)
    
    # Query all memories for this user
    try:
        results = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            ),
            limit=200,  # Get last 200 memories
            with_payload=True,
            with_vectors=False
        )
        
        memories = results[0]
        print(f"✅ Found {len(memories)} memories for user {user_id}\n")
        
        if not memories:
            print("❌ No memories found!")
            return
        
        # Analyze for repetitive content
        print(f"\n{'='*80}")
        print("ANALYZING FOR REPETITIVE PATTERNS")
        print(f"{'='*80}\n")
        
        user_messages = []
        bot_responses = []
        content_fragments = []
        timestamps = []
        
        for point in memories:
            payload = point.payload
            content = payload.get('content', '')
            user_msg = payload.get('user_message', '')
            bot_resp = payload.get('bot_response', '')
            timestamp = payload.get('timestamp', '')
            
            if user_msg:
                user_messages.append(user_msg)
            if bot_resp:
                bot_responses.append(bot_resp)
            if content:
                # Extract key phrases (5+ words)
                words = content.split()
                if len(words) >= 5:
                    content_fragments.append(' '.join(words[:10]))  # First 10 words
            if timestamp:
                timestamps.append(timestamp)
        
        # Check for duplicate user messages
        print("\n📨 USER MESSAGE PATTERNS:")
        user_msg_counts = Counter(user_messages)
        duplicates = [(msg, count) for msg, count in user_msg_counts.items() if count > 1]
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} duplicate user messages:")
            for msg, count in sorted(duplicates, key=lambda x: x[1], reverse=True)[:10]:
                print(f"   [{count}x] {msg[:100]}...")
        else:
            print("✅ No duplicate user messages found")
        
        # Check for repetitive bot responses
        print("\n🤖 BOT RESPONSE PATTERNS:")
        bot_resp_counts = Counter([resp[:100] for resp in bot_responses if resp])  # First 100 chars
        repetitive = [(msg, count) for msg, count in bot_resp_counts.items() if count > 2]
        if repetitive:
            print(f"⚠️  Found {len(repetitive)} repetitive bot response patterns:")
            for msg, count in sorted(repetitive, key=lambda x: x[1], reverse=True)[:10]:
                print(f"   [{count}x] {msg[:80]}...")
        else:
            print("✅ No highly repetitive bot responses detected")
        
        # Check for common phrases in bot responses
        print("\n🔍 COMMON PHRASES IN BOT RESPONSES:")
        phrase_fragments = []
        for resp in bot_responses:
            if len(resp) > 20:
                # Look for common starting phrases
                if resp.startswith("*"):
                    first_part = resp.split('\n')[0][:50]
                    phrase_fragments.append(first_part)
        
        phrase_counts = Counter(phrase_fragments)
        common_phrases = [(phrase, count) for phrase, count in phrase_counts.items() if count > 3]
        if common_phrases:
            print(f"⚠️  Found {len(common_phrases)} commonly repeated opening phrases:")
            for phrase, count in sorted(common_phrases, key=lambda x: x[1], reverse=True)[:10]:
                print(f"   [{count}x] {phrase}...")
        else:
            print("✅ No excessive phrase repetition detected")
        
        # Show recent memories (last 20)
        print(f"\n{'='*80}")
        print("RECENT MEMORY SAMPLES (Last 20)")
        print(f"{'='*80}\n")
        
        recent_memories = sorted(
            [(p.payload.get('timestamp', ''), p.payload) for p in memories],
            key=lambda x: x[0],
            reverse=True
        )[:20]
        
        for i, (ts, payload) in enumerate(recent_memories, 1):
            print(f"\n--- Memory {i} ---")
            print(f"Timestamp: {ts}")
            print(f"User: {payload.get('user_message', 'N/A')[:150]}")
            print(f"Bot: {payload.get('bot_response', 'N/A')[:150]}...")
            
            # Show emotion metadata if available
            if 'roberta_emotion' in payload:
                print(f"Emotion: {payload['roberta_emotion']} (conf: {payload.get('roberta_confidence', 'N/A')})")
        
        # Specific analysis for name confusion issue
        print(f"\n{'='*80}")
        print("NAME CONFUSION ANALYSIS")
        print(f"{'='*80}\n")
        
        cynthia_mentions = 0
        liln_mentions = 0
        name_confusion = []
        
        for point in memories:
            payload = point.payload
            bot_resp = payload.get('bot_response', '')
            user_msg = payload.get('user_message', '')
            
            # Check for name confusion in bot responses
            if 'cynthia' in bot_resp.lower():
                cynthia_mentions += 1
                if 'when you call me cynthia' in bot_resp.lower() or 'call me cynthia' in bot_resp.lower():
                    name_confusion.append({
                        'timestamp': payload.get('timestamp', ''),
                        'user': user_msg[:100],
                        'bot': bot_resp[:200]
                    })
            
            if 'liln' in bot_resp.lower():
                liln_mentions += 1
        
        print(f"📊 Name mentions in bot responses:")
        print(f"   'Cynthia': {cynthia_mentions} times")
        print(f"   'Liln': {liln_mentions} times")
        
        if name_confusion:
            print(f"\n⚠️  Found {len(name_confusion)} instances of potential name confusion:")
            for conf in name_confusion[:5]:
                print(f"\n   Timestamp: {conf['timestamp']}")
                print(f"   User: {conf['user']}")
                print(f"   Bot: {conf['bot']}...")
        
        print(f"\n{'='*80}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Error querying Qdrant: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(analyze_aetheris_memories())
