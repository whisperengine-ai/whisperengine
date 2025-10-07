#!/usr/bin/env python3
"""
Analyze current vector storage state before migration
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append('/Users/markcastillo/git/whisperengine')

from qdrant_client import QdrantClient

async def analyze_collections():
    """Analyze current collections and bot_name usage"""
    client = QdrantClient(
        host=os.getenv('QDRANT_HOST', 'localhost'),
        port=int(os.getenv('QDRANT_PORT', '6334'))
    )
    
    collections = [
        'whisperengine_memory_aetheris',
        'whisperengine_memory_aethys', 
        'whisperengine_memory_dotty',
        'whisperengine_memory_dream_7d',
        'whisperengine_memory_elena_7d',
        'whisperengine_memory_gabriel_7d', 
        'whisperengine_memory_jake_7d',
        'whisperengine_memory_marcus_7d',
        'whisperengine_memory_ryan_7d',
        'whisperengine_memory_sophia_7d'
    ]
    
    print("🔍 Current Vector Storage Analysis:")
    print("=" * 50)
    
    total_points = 0
    total_with_bot_name = 0
    
    for collection_name in collections:
        try:
            # Get collection info
            collection_info = client.get_collection(collection_name)
            points_count = collection_info.points_count or 0
            total_points += points_count
            
            # Sample points to check bot_name usage
            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=100,
                with_payload=True,
                with_vectors=False
            )
            
            bot_names = set()
            points_with_bot_name = 0
            
            for point in scroll_result[0]:
                if point.payload and 'bot_name' in point.payload:
                    bot_names.add(point.payload['bot_name'])
                    points_with_bot_name += 1
            
            total_with_bot_name += points_with_bot_name
            
            print(f"📊 {collection_name}:")
            print(f"    Points: {points_count}")
            print(f"    Sample with bot_name: {points_with_bot_name}/{len(scroll_result[0])}")
            print(f"    Bot names found: {bot_names}")
            print()
            
        except Exception as e:
            print(f"❌ {collection_name}: {e}")
    
    print("📈 SUMMARY:")
    print(f"    Total points across all collections: {total_points}")
    print(f"    Estimated points with bot_name field: {total_with_bot_name}")
    print("    Migration impact: Remove bot_name field from vector payloads")
    print("    Benefit: Simplified queries, reduced payload size, cleaner architecture")

if __name__ == "__main__":
    asyncio.run(analyze_collections())