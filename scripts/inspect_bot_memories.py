#!/usr/bin/env python3
"""
Inspect bot-bridge memories to see what's actually stored
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from qdrant_client import QdrantClient

# Connect to Qdrant
qdrant_host = os.getenv("QDRANT_HOST", "localhost")
qdrant_port = int(os.getenv("QDRANT_PORT", "6334"))

client = QdrantClient(host=qdrant_host, port=qdrant_port)

# Check Dotty's memories
print("=" * 80)
print("Checking Dotty's collection for memories with user_id='nottaylor'")
print("=" * 80)

try:
    result = client.scroll(
        collection_name="whisperengine_memory_dotty",
        scroll_filter=None,
        limit=10,
        with_payload=True,
        with_vectors=False
    )
    
    print(f"\nTotal points in collection: (showing first 10)")
    for point in result[0]:
        user_id = point.payload.get("user_id", "N/A")
        platform = point.payload.get("metadata", {}).get("platform", "N/A")
        content = point.payload.get("content", "")[:100]
        print(f"\nPoint ID: {point.id}")
        print(f"  user_id: {user_id}")
        print(f"  platform: {platform}")
        print(f"  content: {content}...")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("Checking NotTaylor's collection for memories with user_id='dotty'")
print("=" * 80)

try:
    result = client.scroll(
        collection_name="whisperengine_memory_nottaylor",
        scroll_filter=None,
        limit=10,
        with_payload=True,
        with_vectors=False
    )
    
    print(f"\nTotal points in collection: (showing first 10)")
    for point in result[0]:
        user_id = point.payload.get("user_id", "N/A")
        platform = point.payload.get("metadata", {}).get("platform", "N/A")
        content = point.payload.get("content", "")[:100]
        print(f"\nPoint ID: {point.id}")
        print(f"  user_id: {user_id}")
        print(f"  platform: {platform}")
        print(f"  content: {content}...")
        
except Exception as e:
    print(f"Error: {e}")
