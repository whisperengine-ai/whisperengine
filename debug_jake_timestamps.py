#!/usr/bin/env python3
"""
Debug script to check actual timestamp data in Jake's Qdrant collection.
Checks both 'timestamp' and 'timestamp_unix' fields.
"""
import os
import sys
from qdrant_client import QdrantClient
from qdrant_client import models

# Jake's configuration
BOT_NAME = "jake"
COLLECTION_NAME = "whisperengine_memory_jake_7d"
USER_ID = "672814231002939413"  # User with conversation history

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6334)

print(f"🔍 Checking timestamps in {COLLECTION_NAME} for user {USER_ID}\n")

# Query Jake's conversation messages
scroll_result = client.scroll(
    collection_name=COLLECTION_NAME,
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=USER_ID)),
            models.FieldCondition(key="memory_type", match=models.MatchValue(value="conversation"))
        ]
    ),
    limit=20,
    with_payload=True,
    with_vectors=False
)

points = scroll_result[0]

if not points:
    print(f"❌ No conversation messages found for user {USER_ID}")
    sys.exit(1)

print(f"✅ Found {len(points)} conversation messages\n")
print("=" * 80)

for i, point in enumerate(points[:10], 1):  # Check first 10
    payload = point.payload
    
    # Extract timestamp fields
    timestamp_iso = payload.get("timestamp", "MISSING")
    timestamp_unix = payload.get("timestamp_unix", "MISSING")
    content = payload.get("content", "")[:50]
    role = payload.get("role", "unknown")
    
    print(f"\nMessage {i}:")
    print(f"  Role: {role}")
    print(f"  Content: {content}...")
    print(f"  timestamp (ISO): {timestamp_iso}")
    print(f"  timestamp_unix: {timestamp_unix}")
    print(f"  Type of timestamp: {type(timestamp_iso)}")
    print(f"  Type of timestamp_unix: {type(timestamp_unix)}")

print("\n" + "=" * 80)
print(f"\n🎯 ANALYSIS:")

# Check for missing timestamps
missing_iso = sum(1 for p in points if not p.payload.get("timestamp"))
missing_unix = sum(1 for p in points if not p.payload.get("timestamp_unix"))

print(f"  Messages missing 'timestamp' (ISO): {missing_iso}/{len(points)}")
print(f"  Messages missing 'timestamp_unix': {missing_unix}/{len(points)}")

# Check for zero/invalid timestamps
if points:
    sample_unix = points[0].payload.get("timestamp_unix", 0)
    if isinstance(sample_unix, (int, float)) and sample_unix == 0:
        print(f"  ⚠️  timestamp_unix values are ZERO (not being set)")
    elif isinstance(sample_unix, (int, float)) and sample_unix > 0:
        print(f"  ✅ timestamp_unix values look valid (non-zero)")
    else:
        print(f"  ❓ timestamp_unix type unexpected: {type(sample_unix)}")

print("\n")
