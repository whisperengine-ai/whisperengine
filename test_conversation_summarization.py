#!/usr/bin/env python3
"""
Test conversation summarization for messages beyond keepalive timeout.
Checks if summaries are being generated and stored in Qdrant.
"""
import os
import sys
from datetime import datetime, timedelta
from qdrant_client import QdrantClient
from qdrant_client import models

# Jake's configuration
BOT_NAME = "jake"
COLLECTION_NAME = "whisperengine_memory_jake_7d"
USER_ID = "672814231002939413"  # User with conversation history

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6334)

print(f"🔍 Testing conversation summarization for {BOT_NAME}\n")
print("=" * 80)

# 1. Check for conversation summary memories
print("\n📋 TEST 1: Conversation Summary Storage")
print("-" * 80)

summary_result = client.scroll(
    collection_name=COLLECTION_NAME,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=USER_ID)),
            models.FieldCondition(key="memory_type", match=models.MatchValue(value="conversation_summary"))
        ]
    ),
    limit=50,
    with_payload=True,
    with_vectors=False
)

summaries = summary_result[0]

if summaries:
    print(f"✅ Found {len(summaries)} conversation summaries")
    print("\nSummary details:")
    for i, summary in enumerate(summaries[:5], 1):
        payload = summary.payload if summary.payload else {}
        content = payload.get("content", "")[:150]
        ts = payload.get("timestamp", "unknown")
        print(f"\n  Summary {i}:")
        print(f"    Timestamp: {ts}")
        print(f"    Content: {content}...")
else:
    print("❌ NO conversation summaries found!")
    print("   This means summarization is not working or hasn't been triggered yet")

# 2. Check conversation messages grouped by session
print("\n\n📋 TEST 2: Conversation Session Analysis")
print("-" * 80)

# Get all conversation messages sorted by timestamp
conversation_result = client.scroll(
    collection_name=COLLECTION_NAME,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=USER_ID)),
            models.FieldCondition(key="memory_type", match=models.MatchValue(value="conversation"))
        ]
    ),
    limit=100,
    with_payload=True,
    with_vectors=False
)

messages = conversation_result[0]
sorted_messages = sorted(messages, key=lambda p: p.payload.get("timestamp_unix", 0) if p.payload else 0)

print(f"✅ Found {len(sorted_messages)} total conversation messages")

# Group messages into sessions (15-minute keepalive window)
KEEPALIVE_SECONDS = 15 * 60
sessions = []
current_session = []

for i, msg in enumerate(sorted_messages):
    if not msg.payload:
        continue
    
    ts_unix = msg.payload.get("timestamp_unix", 0)
    
    if not current_session:
        current_session.append(msg)
    else:
        prev_ts = current_session[-1].payload.get("timestamp_unix", 0)
        gap = ts_unix - prev_ts
        
        if gap <= KEEPALIVE_SECONDS:
            # Same session
            current_session.append(msg)
        else:
            # New session - save old one and start new
            sessions.append(current_session)
            current_session = [msg]

# Don't forget the last session
if current_session:
    sessions.append(current_session)

print(f"\n📊 Detected {len(sessions)} conversation sessions (using 15-min keepalive)")
print("\nSession breakdown:")

for i, session in enumerate(sessions, 1):
    session_start = session[0].payload.get("timestamp", "unknown") if session[0].payload else "unknown"
    session_end = session[-1].payload.get("timestamp", "unknown") if session[-1].payload else "unknown"
    message_count = len(session)
    
    # Calculate session duration
    if session[0].payload and session[-1].payload:
        start_ts = session[0].payload.get("timestamp_unix", 0)
        end_ts = session[-1].payload.get("timestamp_unix", 0)
        duration_min = (end_ts - start_ts) / 60
        print(f"\n  Session {i}:")
        print(f"    Messages: {message_count}")
        print(f"    Duration: {duration_min:.1f} minutes")
        print(f"    Start: {session_start}")
        print(f"    End: {session_end}")
        
        # Show message preview
        if message_count > 0:
            first_msg = session[0].payload.get("content", "")[:60] if session[0].payload else ""
            last_msg = session[-1].payload.get("content", "")[:60] if session[-1].payload else ""
            print(f"    First: {first_msg}...")
            print(f"    Last: {last_msg}...")

# 3. Check if sessions that should be summarized have summaries
print("\n\n📋 TEST 3: Summary Coverage Analysis")
print("-" * 80)

# Sessions with 3+ messages should ideally have summaries
sessions_needing_summary = [s for s in sessions if len(s) >= 3]
print(f"📊 Sessions with 3+ messages (should have summaries): {len(sessions_needing_summary)}")
print(f"📊 Actual summaries found: {len(summaries)}")

if len(summaries) == 0:
    print("\n❌ SUMMARIZATION NOT WORKING:")
    print("   - No conversation summaries found in Qdrant")
    print("   - Summaries should be created for sessions with multiple messages")
    print("   - Check if summarization is triggered in conversation flow")
elif len(summaries) < len(sessions_needing_summary):
    print(f"\n⚠️  PARTIAL SUMMARIZATION:")
    print(f"   - Expected ~{len(sessions_needing_summary)} summaries")
    print(f"   - Found {len(summaries)} summaries")
    print(f"   - Gap: {len(sessions_needing_summary) - len(summaries)} missing summaries")
else:
    print(f"\n✅ SUMMARIZATION WORKING:")
    print(f"   - Found {len(summaries)} summaries for {len(sessions_needing_summary)} sessions")

# 4. Memory narrative (long-term memories)
print("\n\n📋 TEST 4: Long-term Memory Narrative")
print("-" * 80)

narrative_result = client.scroll(
    collection_name=COLLECTION_NAME,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=USER_ID)),
            models.FieldCondition(key="memory_type", match=models.MatchValue(value="relationship"))
        ]
    ),
    limit=50,
    with_payload=True,
    with_vectors=False
)

narratives = narrative_result[0]

if narratives:
    print(f"✅ Found {len(narratives)} relationship/narrative memories")
    print("\nNarrative memory samples:")
    for i, narrative in enumerate(narratives[:3], 1):
        payload = narrative.payload if narrative.payload else {}
        content = payload.get("content", "")[:150]
        print(f"\n  Memory {i}: {content}...")
else:
    print("❌ No relationship/narrative memories found")

print("\n" + "=" * 80)
print("\n🎯 SUMMARY:")
print(f"  Conversation messages: {len(sorted_messages)}")
print(f"  Conversation sessions: {len(sessions)}")
print(f"  Sessions needing summary: {len(sessions_needing_summary)}")
print(f"  Actual summaries stored: {len(summaries)}")
print(f"  Long-term narratives: {len(narratives)}")
print()

if len(summaries) == 0:
    print("⚠️  ACTION NEEDED: Conversation summarization appears to be disabled or not triggered")
elif len(summaries) < len(sessions_needing_summary):
    print("⚠️  ACTION NEEDED: Some sessions are missing summaries")
else:
    print("✅ Conversation summarization is working correctly!")
print()
