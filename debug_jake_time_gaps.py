#!/usr/bin/env python3
"""
Debug script to analyze time gaps in Jake's conversation with user 672814231002939413.
Shows actual temporal distribution to understand conversation patterns.
"""
import os
import sys
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client import models

# Jake's configuration
BOT_NAME = "jake"
COLLECTION_NAME = "whisperengine_memory_jake_7d"
USER_ID = "672814231002939413"

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6334)

print(f"🔍 Analyzing conversation time gaps for user {USER_ID}\n")

# Query Jake's conversation messages
scroll_result = client.scroll(
    collection_name=COLLECTION_NAME,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=USER_ID)),
            models.FieldCondition(key="memory_type", match=models.MatchValue(value="conversation"))
        ]
    ),
    limit=50,
    with_payload=True,
    with_vectors=False
)

points = scroll_result[0]

if not points:
    print(f"❌ No conversation messages found")
    sys.exit(1)

# Sort by timestamp_unix
sorted_points = sorted(points, key=lambda p: p.payload.get("timestamp_unix", 0) if p.payload else 0)

print(f"✅ Found {len(sorted_points)} conversation messages")
print("=" * 100)
print()

# Analyze consecutive messages
prev_ts = None
prev_role = None
prev_content = None

for i, point in enumerate(sorted_points, 1):
    payload = point.payload if point.payload else {}
    
    ts_unix = payload.get("timestamp_unix", 0)
    ts_iso = payload.get("timestamp", "unknown")
    role = payload.get("role", "unknown")
    content = payload.get("content", "")[:60]
    
    # Calculate time gap from previous message
    time_gap_str = "N/A"
    if prev_ts and ts_unix:
        gap_seconds = ts_unix - prev_ts
        gap_minutes = gap_seconds / 60
        gap_hours = gap_minutes / 60
        
        if gap_hours >= 1:
            time_gap_str = f"{gap_hours:.1f} hours"
        elif gap_minutes >= 1:
            time_gap_str = f"{gap_minutes:.1f} min"
        else:
            time_gap_str = f"{gap_seconds:.1f} sec"
    
    print(f"Message {i:2d}:")
    print(f"  Time: {ts_iso}")
    print(f"  Gap from previous: {time_gap_str}")
    print(f"  Role: [{role}]")
    print(f"  Content: {content}...")
    print()
    
    prev_ts = ts_unix
    prev_role = role
    prev_content = content

print("=" * 100)
print("\n🎯 CONTINUITY ANALYSIS:")

# Find pairs with good continuity (< 15 min gap)
continuity_pairs = 0
total_pairs = len(sorted_points) - 1

sorted_points_list = list(sorted_points)
for i in range(len(sorted_points_list) - 1):
    curr = sorted_points_list[i]
    next_msg = sorted_points_list[i + 1]
    
    if not (curr.payload and next_msg.payload):
        continue
    
    curr_ts = curr.payload.get("timestamp_unix", 0)
    next_ts = next_msg.payload.get("timestamp_unix", 0)
    
    if curr_ts and next_ts:
        gap_minutes = (next_ts - curr_ts) / 60
        if gap_minutes <= 15:
            continuity_pairs += 1

continuity_rate = (continuity_pairs / total_pairs * 100) if total_pairs > 0 else 0

print(f"  Total message pairs: {total_pairs}")
print(f"  Pairs within 15min: {continuity_pairs}")
print(f"  Temporal continuity rate: {continuity_rate:.1f}%")
print()
