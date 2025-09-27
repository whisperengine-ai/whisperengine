#!/usr/bin/env python3
"""
Unknown Records Investigator

Examines records with bot_name="unknown" to see if we can identify
which bot they should belong to based on content patterns, user IDs, etc.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List
from collections import Counter, defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qdrant_client import QdrantClient, models
from dotenv import load_dotenv

load_dotenv()

async def investigate_unknown_records():
    """Investigate records with bot_name='unknown'"""
    
    print("🔍 INVESTIGATING UNKNOWN RECORDS")
    print("=" * 60)
    
    try:
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6334"))
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "whisperengine_memory")
        
        print(f"🔌 Connecting to Qdrant: {host}:{port}")
        client = QdrantClient(host=host, port=port)
        
        # Get all records with bot_name="unknown"
        print("📊 Fetching unknown records...")
        
        unknown_records = []
        offset = None
        
        while True:
            result = client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="bot_name",
                            match=models.MatchValue(value="unknown")
                        )
                    ]
                ),
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            points, next_offset = result
            
            if not points:
                break
                
            for point in points:
                payload = point.payload or {}
                unknown_records.append({
                    "id": str(point.id),
                    "content": payload.get("content", ""),
                    "user_id": payload.get("user_id", ""),
                    "memory_type": payload.get("memory_type", ""),
                    "timestamp": payload.get("timestamp", ""),
                    "metadata": payload.get("metadata", {}),
                })
            
            offset = next_offset
            if not next_offset:
                break
        
        print(f"📋 Found {len(unknown_records)} unknown records")
        
        if not unknown_records:
            print("✅ No unknown records found!")
            return
        
        # Analyze patterns
        print("\n" + "=" * 60)
        print("📊 PATTERN ANALYSIS")
        print("=" * 60)
        
        # User ID distribution
        user_counts = Counter(r["user_id"] for r in unknown_records)
        print(f"\n👥 User ID Distribution:")
        for user_id, count in user_counts.most_common(10):
            print(f"  {user_id}: {count} records")
        
        # Memory type distribution
        memory_types = Counter(r["memory_type"] for r in unknown_records)
        print(f"\n💭 Memory Type Distribution:")
        for mem_type, count in memory_types.items():
            print(f"  {mem_type}: {count} records")
        
        # Content patterns
        print(f"\n📝 Content Samples (first 10):")
        for i, record in enumerate(unknown_records[:10]):
            content = record["content"][:100]
            role = record.get("metadata", {}).get("role", "unknown")
            print(f"  {i+1}. [{role}] '{content}{'...' if len(record['content']) > 100 else ''}'")
        
        # Look for character name mentions in content
        print(f"\n🔍 Character Name Analysis:")
        character_mentions = defaultdict(int)
        known_bots = ["elena", "marcus", "gabriel", "dream", "jake", "sophia", "ryan"]
        
        for record in unknown_records:
            content = record["content"].lower()
            for bot in known_bots:
                if bot in content:
                    character_mentions[bot] += 1
        
        if character_mentions:
            print("  Character mentions in unknown records:")
            for char, count in sorted(character_mentions.items(), key=lambda x: x[1], reverse=True):
                print(f"    {char}: {count} mentions")
        else:
            print("  No obvious character name mentions found")
        
        # Check timestamps to see when these were created
        timestamps = []
        for record in unknown_records:
            ts = record.get("timestamp")
            if ts:
                timestamps.append(ts)
        
        if timestamps:
            timestamps.sort()
            print(f"\n⏰ Timestamp Range:")
            print(f"  Earliest: {timestamps[0]}")
            print(f"  Latest: {timestamps[-1]}")
        
        # Recommendations
        print("\n" + "=" * 60)  
        print("💡 RECOMMENDATIONS")
        print("=" * 60)
        
        if len(set(r["user_id"] for r in unknown_records)) == 1:
            single_user = list(set(r["user_id"] for r in unknown_records))[0]
            print(f"\n🎯 All unknown records belong to single user: {single_user}")
            print("   Recommendation: Check which bot this user primarily interacts with")
        
        if character_mentions:
            top_mention = max(character_mentions.items(), key=lambda x: x[1])
            print(f"\n🎯 Most mentioned character: {top_mention[0]} ({top_mention[1]} mentions)")
            print(f"   Recommendation: Consider reassigning unknown records to '{top_mention[0]}'")
        
        print(f"\n📋 Summary:")
        print(f"  - {len(unknown_records)} records need bot_name assignment")
        print(f"  - {len(user_counts)} unique users")
        print(f"  - Most records: {memory_types.most_common(1)[0] if memory_types else 'N/A'}")
        
        return unknown_records
        
    except Exception as e:
        print(f"❌ Error investigating unknown records: {e}")
        return []

async def investigate_marcus_chen_records():
    """Investigate marcus_chen records for renaming to ryan_chen"""
    
    print("\n" + "=" * 60)
    print("🔍 INVESTIGATING MARCUS_CHEN RECORDS")
    print("=" * 60)
    
    try:
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6334"))
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "whisperengine_memory")
        
        client = QdrantClient(host=host, port=port)
        
        # Get all records with bot_name="marcus_chen"
        print("📊 Fetching marcus_chen records...")
        
        marcus_chen_records = []
        offset = None
        
        while True:
            result = client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="bot_name",
                            match=models.MatchValue(value="marcus_chen")
                        )
                    ]
                ),
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            points, next_offset = result
            
            if not points:
                break
                
            for point in points:
                payload = point.payload or {}
                marcus_chen_records.append({
                    "id": str(point.id),
                    "content": payload.get("content", "")[:100],
                    "user_id": payload.get("user_id", ""),
                    "memory_type": payload.get("memory_type", ""),
                    "timestamp": payload.get("timestamp", ""),
                })
            
            offset = next_offset
            if not next_offset:
                break
        
        print(f"📋 Found {len(marcus_chen_records)} marcus_chen records")
        
        if marcus_chen_records:
            # Analyze these records
            user_counts = Counter(r["user_id"] for r in marcus_chen_records)
            memory_types = Counter(r["memory_type"] for r in marcus_chen_records)
            
            print(f"\n👥 User Distribution:")
            for user_id, count in user_counts.most_common(5):
                print(f"  {user_id}: {count} records")
            
            print(f"\n💭 Memory Types:")
            for mem_type, count in memory_types.items():
                print(f"  {mem_type}: {count} records")
            
            print(f"\n📝 Sample Content:")
            for i, record in enumerate(marcus_chen_records[:5]):
                print(f"  {i+1}. '{record['content']}{'...' if len(record['content']) >= 100 else ''}'")
            
            print(f"\n💡 RECOMMENDATION:")
            print(f"  ✅ Update all {len(marcus_chen_records)} records from 'marcus_chen' to 'ryan_chen'")
            print(f"  ✅ This will consolidate with existing 136 ryan_chen records")
        else:
            print("✅ No marcus_chen records found!")
        
        return marcus_chen_records
        
    except Exception as e:
        print(f"❌ Error investigating marcus_chen records: {e}")
        return []

async def main():
    """Main investigation function"""
    unknown_records = await investigate_unknown_records()
    marcus_chen_records = await investigate_marcus_chen_records()
    
    if unknown_records or marcus_chen_records:
        print(f"\n🔧 Ready to create migration script for:")
        if unknown_records:
            print(f"  - {len(unknown_records)} unknown records (need analysis)")
        if marcus_chen_records:
            print(f"  - {len(marcus_chen_records)} marcus_chen → ryan_chen records")

if __name__ == "__main__":
    asyncio.run(main())