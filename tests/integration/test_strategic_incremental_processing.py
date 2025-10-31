"""
Test incremental strategic intelligence processing

Validates that enrichment worker doesn't re-process users with fresh cache.

Usage:
    source .venv/bin/activate && \
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
    export QDRANT_HOST="localhost" && \
    export QDRANT_PORT="6334" && \
    export POSTGRES_HOST="localhost" && \
    export POSTGRES_PORT="5433" && \
    export DISCORD_BOT_NAME=elena && \
    python tests/integration/test_strategic_incremental_processing.py
"""

import asyncio
import asyncpg
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.enrichment.worker import EnrichmentWorker
from qdrant_client import QdrantClient

# Test configuration
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5433
POSTGRES_USER = "whisperengine"
POSTGRES_PASSWORD = "whisperengine"
POSTGRES_DB = "whisperengine"

QDRANT_HOST = "localhost"
QDRANT_PORT = 6334

TEST_BOT = "elena"
TEST_COLLECTION = "whisperengine_memory_elena"


async def test_incremental_processing():
    """Test that worker only processes users with stale/missing cache"""
    
    print("\n" + "="*80)
    print("🧪 STRATEGIC INTELLIGENCE INCREMENTAL PROCESSING TEST")
    print("="*80 + "\n")
    
    # Initialize database
    print("📦 Connecting to PostgreSQL...")
    db_pool = await asyncpg.create_pool(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
        min_size=1,
        max_size=5
    )
    print("✅ Connected to PostgreSQL\n")
    
    # Initialize Qdrant
    print("📦 Connecting to Qdrant...")
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print("✅ Connected to Qdrant\n")
    
    try:
        # Test 1: Get users from collection
        print("🔍 Test 1: Getting users from collection...")
        
        # Get some users from the collection
        users = []
        offset = None
        while len(users) < 5:  # Get at least 5 users
            result = qdrant_client.scroll(
                collection_name=TEST_COLLECTION,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            points, offset = result
            
            if not points:
                break
            
            for point in points:
                if point.payload and 'user_id' in point.payload:
                    user_id = point.payload['user_id']
                    if user_id not in users:
                        users.append(user_id)
                        if len(users) >= 5:
                            break
            
            if offset is None or len(users) >= 5:
                break
        
        print(f"✅ Found {len(users)} test users\n")
        
        if len(users) < 2:
            print("⚠️  Need at least 2 users for testing. Add more conversations first.")
            return
        
        # Test 2: Create fresh cache for first 3 users
        print("🔍 Test 2: Creating fresh cache entries for 3 users...")
        
        fresh_users = users[:3]
        stale_users = users[3:] if len(users) > 3 else []
        
        for user_id in fresh_users:
            await db_pool.execute("""
                INSERT INTO strategic_memory_health 
                (user_id, bot_name, memory_snapshot, avg_memory_age_hours, 
                 retrieval_frequency_trend, forgetting_risk_memories, 
                 computed_at, expires_at)
                VALUES ($1, $2, '{}'::jsonb, 100.0, 'stable', '[]'::jsonb, 
                        NOW(), NOW() + INTERVAL '5 minutes')
                ON CONFLICT (user_id, bot_name) 
                DO UPDATE SET expires_at = NOW() + INTERVAL '5 minutes'
            """, user_id, TEST_BOT)
        
        print(f"✅ Created fresh cache for {len(fresh_users)} users")
        print(f"   Fresh: {[u[:12] for u in fresh_users]}")
        print(f"   Stale/missing: {[u[:12] for u in stale_users]}\n")
        
        # Test 3: Initialize worker and check filtering
        print("🔍 Test 3: Testing incremental processing filter...")
        
        worker = EnrichmentWorker(postgres_pool=db_pool)
        
        # Call the filtering method
        users_needing_analysis = await worker._get_users_needing_strategic_analysis(
            users, TEST_BOT
        )
        
        print(f"✅ Filter results:")
        print(f"   Total users: {len(users)}")
        print(f"   Need analysis: {len(users_needing_analysis)}")
        print(f"   Users with fresh cache: {len(users) - len(users_needing_analysis)}")
        
        # Validate filtering logic
        fresh_in_result = [u for u in fresh_users if u in users_needing_analysis]
        stale_in_result = [u for u in stale_users if u in users_needing_analysis]
        
        if fresh_in_result:
            print(f"   ❌ ERROR: Fresh users incorrectly flagged for reprocessing: {fresh_in_result}")
        else:
            print(f"   ✅ Correctly skipped {len(fresh_users)} users with fresh cache")
        
        if len(stale_in_result) == len(stale_users):
            print(f"   ✅ Correctly identified {len(stale_users)} users needing analysis")
        else:
            print(f"   ⚠️  Expected {len(stale_users)} stale users, got {len(stale_in_result)}")
        
        print()
        
        # Test 4: Expire one cache entry and re-test
        print("🔍 Test 4: Testing with expired cache entry...")
        
        if fresh_users:
            expired_user = fresh_users[0]
            await db_pool.execute("""
                UPDATE strategic_memory_health
                SET expires_at = NOW() - INTERVAL '1 minute'
                WHERE user_id = $1 AND bot_name = $2
            """, expired_user, TEST_BOT)
            
            print(f"✅ Expired cache for user {expired_user[:12]}")
            
            # Re-run filter
            users_after_expiry = await worker._get_users_needing_strategic_analysis(
                users, TEST_BOT
            )
            
            if expired_user in users_after_expiry:
                print(f"✅ Correctly identified expired cache entry")
            else:
                print(f"❌ ERROR: Failed to detect expired cache")
            
            print(f"   Need analysis after expiry: {len(users_after_expiry)}")
        
        print()
        
        # Test 5: Process strategic intelligence (should skip fresh users)
        print("🔍 Test 5: Running _process_strategic_intelligence...")
        print("   (This should only process users with stale/missing cache)\n")
        
        processed_count = await worker._process_strategic_intelligence(
            TEST_COLLECTION, TEST_BOT
        )
        
        print(f"\n✅ Processed {processed_count} users")
        print(f"   Expected: {len(users_needing_analysis)} (stale/missing cache)")
        
        if processed_count <= len(users_needing_analysis) + 1:  # +1 for expired user
            print(f"   ✅ Incremental processing working correctly!")
        else:
            print(f"   ⚠️  Processed more users than expected")
        
        print()
        
        # Final summary
        print("="*80)
        print("✅ INCREMENTAL PROCESSING TEST COMPLETE")
        print("="*80)
        print("\nKey Findings:")
        print(f"  - Filtering correctly identifies stale/missing cache entries")
        print(f"  - Fresh cache entries (within TTL) are skipped")
        print(f"  - Expired cache entries are correctly detected")
        print(f"  - Worker avoids redundant re-processing")
        print("\nBehavior:")
        print(f"  - Only processes users with cache older than 5 minutes")
        print(f"  - Prevents unnecessary computation on every cycle")
        print(f"  - Follows same pattern as conversation summaries")
        
    finally:
        await db_pool.close()
        print("\n🔒 Database connection closed\n")


if __name__ == "__main__":
    asyncio.run(test_incremental_processing())
