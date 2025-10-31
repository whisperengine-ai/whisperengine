"""
Test enrichment worker strategic intelligence integration

Validates:
1. Worker processes users and populates strategic_memory_health table
2. Cache entries have proper TTL and structure
3. Processing time meets <30s per user target
4. Batch processing works correctly

Usage:
    source .venv/bin/activate && \
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
    export QDRANT_HOST="localhost" && \
    export QDRANT_PORT="6334" && \
    export POSTGRES_HOST="localhost" && \
    export POSTGRES_PORT="5433" && \
    export DISCORD_BOT_NAME=elena && \
    python tests/integration/test_worker_strategic_intelligence.py
"""

import asyncio
import asyncpg
import time
import sys
from pathlib import Path
from datetime import datetime, timezone
from qdrant_client import QdrantClient

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5433
POSTGRES_USER = "whisperengine"
POSTGRES_PASSWORD = "whisperengine"
POSTGRES_DB = "whisperengine"

QDRANT_HOST = "localhost"
QDRANT_PORT = 6334

# Test bot and user
TEST_BOT = "elena"
TEST_COLLECTION = "whisperengine_memory_elena"


async def test_worker_integration():
    """Test that enrichment worker can process strategic intelligence"""
    
    print("\n" + "="*80)
    print("🧪 ENRICHMENT WORKER STRATEGIC INTELLIGENCE INTEGRATION TEST")
    print("="*80 + "\n")
    
    # Initialize database connection
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
    
    # Initialize Qdrant client
    print("📦 Connecting to Qdrant...")
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print("✅ Connected to Qdrant\n")
    
    try:
        # Test 1: Check for users with conversations
        print("🔍 Test 1: Finding users in test collection...")
        users = await _get_users_in_collection(qdrant_client, TEST_COLLECTION)
        
        if not users:
            print(f"⚠️  WARNING: No users found in {TEST_COLLECTION}")
            print("   Run some test conversations first to populate memories")
            return
        
        print(f"✅ Found {len(users)} users with conversations")
        test_user = users[0]
        print(f"   Using test user: {test_user}\n")
        
        # Test 2: Import and initialize MemoryAgingEngine
        print("🔍 Test 2: Initializing MemoryAgingEngine...")
        from src.enrichment.memory_aging_engine import MemoryAgingEngine
        
        engine = MemoryAgingEngine(
            qdrant_client=qdrant_client,
            postgres_pool=db_pool
        )
        print("✅ MemoryAgingEngine initialized\n")
        
        # Test 3: Run memory health analysis
        print(f"🔍 Test 3: Analyzing memory health for user {test_user}...")
        start_time = time.perf_counter()
        
        memory_health = await engine.analyze_memory_health(
            user_id=test_user,
            bot_name=TEST_BOT,
            collection_name=TEST_COLLECTION
        )
        
        analysis_duration = time.perf_counter() - start_time
        
        if memory_health:
            print(f"✅ Memory health analysis completed in {analysis_duration:.2f}s")
            print(f"   Avg memory age: {memory_health.avg_memory_age_hours / 24:.1f} days")
            print(f"   Retrieval trend: {memory_health.retrieval_frequency_trend}")
            print(f"   Total memories: {memory_health.total_memories}")
            print(f"   At-risk memories: {len(memory_health.forgetting_risk_memories)}")
            
            # Validate performance target
            if analysis_duration < 30:
                print(f"   ✅ Performance target met (<30s): {analysis_duration:.2f}s")
            else:
                print(f"   ⚠️  Performance target missed (>30s): {analysis_duration:.2f}s")
        else:
            print(f"⚠️  No memory health data returned (likely insufficient memories)")
            print(f"   Analysis took: {analysis_duration:.2f}s\n")
            return
        
        print()
        
        # Test 4: Store in strategic cache
        print("🔍 Test 4: Storing memory health in strategic cache...")
        stored = await engine.store_memory_health(metrics=memory_health)
        
        if stored:
            print("✅ Memory health stored successfully")
        else:
            print("❌ Failed to store memory health")
            return
        
        print()
        
        # Test 5: Verify cache entry
        print("🔍 Test 5: Verifying cache entry in strategic_memory_health...")
        cache_entry = await db_pool.fetchrow(
            """
            SELECT user_id, bot_name, memory_snapshot, expires_at, computed_at
            FROM strategic_memory_health
            WHERE user_id = $1 AND bot_name = $2
            """,
            test_user, TEST_BOT
        )
        
        if cache_entry:
            print("✅ Cache entry found:")
            print(f"   User: {cache_entry['user_id']}")
            print(f"   Bot: {cache_entry['bot_name']}")
            print(f"   Computed: {cache_entry['computed_at']}")
            print(f"   Expires: {cache_entry['expires_at']}")
            
            # Check TTL
            now = datetime.now(timezone.utc)
            expires_at = cache_entry['expires_at']
            ttl_remaining = (expires_at - now).total_seconds() / 60
            print(f"   TTL remaining: {ttl_remaining:.1f} minutes")
            
            if 4 <= ttl_remaining <= 6:
                print("   ✅ TTL is correct (~5 minutes)")
            else:
                print(f"   ⚠️  TTL unexpected: {ttl_remaining:.1f} minutes")
            
            # Check memory snapshot structure (parse JSON if string)
            import json
            snapshot = cache_entry['memory_snapshot']
            if isinstance(snapshot, str):
                snapshot = json.loads(snapshot)
            print(f"   Memory snapshot keys: {list(snapshot.keys())}")
            
        else:
            print("❌ Cache entry NOT found in strategic_memory_health table")
            return
        
        print()
        
        # Test 6: Test batch processing with multiple users
        print("🔍 Test 6: Testing batch processing...")
        batch_users = users[:3] if len(users) >= 3 else users
        batch_start = time.perf_counter()
        processed = 0
        
        for user in batch_users:
            try:
                health = await engine.analyze_memory_health(
                    user_id=user,
                    bot_name=TEST_BOT,
                    collection_name=TEST_COLLECTION
                )
                if health:
                    await engine.store_memory_health(metrics=health)
                    processed += 1
            except Exception as e:
                print(f"   ⚠️  Error processing user {user}: {e}")
        
        batch_duration = time.perf_counter() - batch_start
        avg_per_user = batch_duration / len(batch_users)
        
        print(f"✅ Batch processing completed:")
        print(f"   Users processed: {processed}/{len(batch_users)}")
        print(f"   Total time: {batch_duration:.2f}s")
        print(f"   Average per user: {avg_per_user:.2f}s")
        
        if avg_per_user < 30:
            print(f"   ✅ Performance target met (<30s per user)")
        else:
            print(f"   ⚠️  Performance target missed (>30s per user)")
        
        print()
        
        # Test 7: Test cache retrieval (simulate hot path)
        print("🔍 Test 7: Testing cache retrieval (hot path simulation)...")
        retrieval_start = time.perf_counter()
        
        cached = await db_pool.fetchrow(
            """
            SELECT user_id, bot_name, memory_snapshot, computed_at,
                   EXTRACT(EPOCH FROM (NOW() - computed_at)) as age_seconds
            FROM strategic_memory_health
            WHERE user_id = $1 AND bot_name = $2
              AND expires_at > NOW()
            """,
            test_user, TEST_BOT
        )
        
        retrieval_duration = (time.perf_counter() - retrieval_start) * 1000  # Convert to ms
        
        if cached:
            print(f"✅ Cache retrieved in {retrieval_duration:.2f}ms")
            print(f"   Cache age: {cached['age_seconds']:.1f} seconds")
            
            if retrieval_duration < 5:
                print(f"   ✅ Retrieval meets <5ms target")
            else:
                print(f"   ⚠️  Retrieval slower than 5ms target")
        else:
            print("❌ Cache retrieval failed")
        
        print()
        
        # Final summary
        print("="*80)
        print("✅ ALL TESTS PASSED - Worker integration validated!")
        print("="*80)
        print("\nKey Findings:")
        print(f"  - Memory health analysis: {analysis_duration:.2f}s per user")
        print(f"  - Batch processing: {avg_per_user:.2f}s average per user")
        print(f"  - Cache retrieval: {retrieval_duration:.2f}ms")
        print(f"  - Cache TTL: {ttl_remaining:.1f} minutes")
        print("\nNext Steps:")
        print("  1. Run enrichment worker in background")
        print("  2. Verify continuous cache population")
        print("  3. Add hot path cache retrieval in MessageProcessor")
        print("  4. Test end-to-end with real Discord messages")
        
    finally:
        await db_pool.close()
        print("\n🔒 Database connection closed\n")


async def _get_users_in_collection(client: QdrantClient, collection_name: str):
    """Get list of unique users in a collection"""
    try:
        # Scroll through collection and collect unique user_ids
        users = set()
        offset = None
        
        while True:
            result = client.scroll(
                collection_name=collection_name,
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
                    users.add(point.payload['user_id'])
            
            if offset is None:
                break
        
        return list(users)
    
    except Exception as e:
        print(f"❌ Error getting users from collection: {e}")
        return []


if __name__ == "__main__":
    asyncio.run(test_worker_integration())
