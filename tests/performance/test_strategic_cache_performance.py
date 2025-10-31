#!/usr/bin/env python3
"""
Phase 3A Task 3: Strategic Cache Performance Testing

Tests cache helper functions under load to validate production readiness:
- High concurrency (100+ parallel requests)
- P95/P99 latency measurement
- Cache hit rate validation
- Connection pool saturation testing
- Realistic multi-user scenarios

Target: <5ms P95 latency, >95% cache hit rate
"""

import asyncio
import json
import os
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime
from statistics import mean, median
from typing import Dict, List, Any, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.database.postgres_pool_manager import get_postgres_pool


class PerformanceMetrics:
    """Collect and analyze performance metrics."""
    
    def __init__(self):
        self.latencies: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = 0
        self.start_time = None
        self.end_time = None
    
    def record_latency(self, latency_ms: float, cache_hit: bool, error: bool = False):
        """Record a single query result."""
        self.latencies.append(latency_ms)
        if error:
            self.errors += 1
        elif cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def get_percentile(self, percentile: int) -> float:
        """Calculate latency percentile."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * percentile / 100)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        total_queries = self.cache_hits + self.cache_misses + self.errors
        duration_seconds = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        
        return {
            'total_queries': total_queries,
            'duration_seconds': duration_seconds,
            'queries_per_second': total_queries / duration_seconds if duration_seconds > 0 else 0,
            'cache_hit_rate': self.cache_hits / total_queries if total_queries > 0 else 0,
            'error_rate': self.errors / total_queries if total_queries > 0 else 0,
            'latency_mean_ms': mean(self.latencies) if self.latencies else 0,
            'latency_median_ms': median(self.latencies) if self.latencies else 0,
            'latency_p95_ms': self.get_percentile(95),
            'latency_p99_ms': self.get_percentile(99),
            'latency_max_ms': max(self.latencies) if self.latencies else 0,
        }


async def setup_test_data(pool, num_users: int = 10, bot_name: str = 'elena') -> List[str]:
    """Create test cache data for multiple users."""
    user_ids = [f'perf_test_user_{i}_{uuid.uuid4().hex[:6]}' for i in range(num_users)]
    
    print(f"\n📝 Setting up test data for {num_users} users...")
    
    query = """
        INSERT INTO strategic_memory_health 
        (user_id, bot_name, memory_snapshot, avg_memory_age_hours, 
         retrieval_frequency_trend, forgetting_risk_memories, 
         computed_at, expires_at)
        VALUES ($1, $2, $3::jsonb, $4, $5, $6::jsonb, NOW(), NOW() + INTERVAL '5 minutes')
        ON CONFLICT (user_id, bot_name) 
        DO UPDATE SET 
            memory_snapshot = EXCLUDED.memory_snapshot,
            computed_at = EXCLUDED.computed_at,
            expires_at = EXCLUDED.expires_at
    """
    
    async with pool.acquire() as conn:
        for user_id in user_ids:
            test_data = {
                'memory_snapshot': {
                    'user_id': user_id,
                    'test': True,
                    'timestamp': datetime.utcnow().isoformat()
                },
                'avg_memory_age_hours': 12.5,
                'retrieval_frequency_trend': 'stable',
                'forgetting_risk_memories': []
            }
            
            await conn.execute(
                query, user_id, bot_name,
                json.dumps(test_data['memory_snapshot']),
                test_data['avg_memory_age_hours'],
                test_data['retrieval_frequency_trend'],
                json.dumps(test_data['forgetting_risk_memories'])
            )
    
    print(f"✅ Created cache data for {len(user_ids)} users")
    return user_ids


async def read_cache_once(pool, user_id: str, bot_name: str) -> Tuple[float, bool, bool]:
    """Read cache and return (latency_ms, cache_hit, error)."""
    query = """
        SELECT memory_snapshot, avg_memory_age_hours, retrieval_frequency_trend,
               forgetting_risk_memories, computed_at, expires_at
        FROM strategic_memory_health
        WHERE user_id = $1 AND bot_name = $2
        AND expires_at > NOW()
        ORDER BY computed_at DESC
        LIMIT 1
    """
    
    try:
        start = time.perf_counter()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, bot_name)
        end = time.perf_counter()
        
        latency_ms = (end - start) * 1000
        cache_hit = row is not None
        
        return (latency_ms, cache_hit, False)
    except Exception as e:
        print(f"❌ Cache read error: {e}")
        return (0, False, True)


async def test_concurrent_reads(pool, user_ids: List[str], bot_name: str, concurrency: int) -> PerformanceMetrics:
    """Test concurrent cache reads with specified concurrency level."""
    print(f"\n{'='*80}")
    print(f"TEST: {concurrency} Concurrent Cache Reads")
    print(f"{'='*80}")
    
    metrics = PerformanceMetrics()
    metrics.start_time = time.perf_counter()
    
    # Create tasks for concurrent reads
    tasks = []
    for i in range(concurrency):
        user_id = user_ids[i % len(user_ids)]  # Round-robin through users
        tasks.append(read_cache_once(pool, user_id, bot_name))
    
    # Execute all reads concurrently
    results = await asyncio.gather(*tasks)
    
    metrics.end_time = time.perf_counter()
    
    # Record results
    for latency_ms, cache_hit, error in results:
        metrics.record_latency(latency_ms, cache_hit, error)
    
    # Print summary
    summary = metrics.get_summary()
    print(f"✅ Completed {summary['total_queries']} queries in {summary['duration_seconds']:.2f}s")
    print(f"   Throughput: {summary['queries_per_second']:.0f} queries/sec")
    print(f"   Cache hit rate: {summary['cache_hit_rate']*100:.1f}%")
    print(f"   Error rate: {summary['error_rate']*100:.1f}%")
    print(f"   Latency mean: {summary['latency_mean_ms']:.2f}ms")
    print(f"   Latency median: {summary['latency_median_ms']:.2f}ms")
    print(f"   Latency P95: {summary['latency_p95_ms']:.2f}ms")
    print(f"   Latency P99: {summary['latency_p99_ms']:.2f}ms")
    print(f"   Latency max: {summary['latency_max_ms']:.2f}ms")
    
    # Validation
    target_p95 = 5.0  # 5ms target
    target_hit_rate = 0.95  # 95% target
    
    if summary['latency_p95_ms'] > target_p95:
        print(f"⚠️  WARNING: P95 latency {summary['latency_p95_ms']:.2f}ms exceeds {target_p95}ms target")
    else:
        print(f"✅ Performance target met: P95 {summary['latency_p95_ms']:.2f}ms < {target_p95}ms")
    
    if summary['cache_hit_rate'] < target_hit_rate:
        print(f"⚠️  WARNING: Cache hit rate {summary['cache_hit_rate']*100:.1f}% below {target_hit_rate*100:.0f}% target")
    else:
        print(f"✅ Cache hit rate met: {summary['cache_hit_rate']*100:.1f}% >= {target_hit_rate*100:.0f}%")
    
    return metrics


async def test_cache_miss_scenario(pool, bot_name: str, num_queries: int = 50) -> PerformanceMetrics:
    """Test performance with cache misses (non-existent users)."""
    print(f"\n{'='*80}")
    print(f"TEST: Cache Miss Scenario ({num_queries} queries)")
    print(f"{'='*80}")
    
    metrics = PerformanceMetrics()
    metrics.start_time = time.perf_counter()
    
    # Generate random user IDs that don't exist in cache
    tasks = []
    for i in range(num_queries):
        fake_user_id = f'nonexistent_user_{uuid.uuid4().hex[:8]}'
        tasks.append(read_cache_once(pool, fake_user_id, bot_name))
    
    results = await asyncio.gather(*tasks)
    metrics.end_time = time.perf_counter()
    
    for latency_ms, cache_hit, error in results:
        metrics.record_latency(latency_ms, cache_hit, error)
    
    summary = metrics.get_summary()
    print(f"✅ Completed {summary['total_queries']} cache miss queries")
    print(f"   Mean latency: {summary['latency_mean_ms']:.2f}ms")
    print(f"   P95 latency: {summary['latency_p95_ms']:.2f}ms")
    print(f"   Cache miss rate: {summary['cache_hit_rate']*100:.1f}% (expected 0%)")
    
    if summary['latency_p95_ms'] > 5.0:
        print(f"⚠️  Cache miss overhead: P95 {summary['latency_p95_ms']:.2f}ms")
    else:
        print(f"✅ Cache miss handled efficiently: P95 {summary['latency_p95_ms']:.2f}ms < 5ms")
    
    return metrics


async def test_sustained_load(pool, user_ids: List[str], bot_name: str, duration_seconds: int = 30) -> PerformanceMetrics:
    """Test sustained load over time period."""
    print(f"\n{'='*80}")
    print(f"TEST: Sustained Load ({duration_seconds}s continuous queries)")
    print(f"{'='*80}")
    
    metrics = PerformanceMetrics()
    metrics.start_time = time.perf_counter()
    
    query_count = 0
    end_time = time.perf_counter() + duration_seconds
    
    print("Running sustained load test...")
    
    while time.perf_counter() < end_time:
        # Random user
        user_id = user_ids[query_count % len(user_ids)]
        
        latency_ms, cache_hit, error = await read_cache_once(pool, user_id, bot_name)
        metrics.record_latency(latency_ms, cache_hit, error)
        
        query_count += 1
        
        # Brief pause to avoid overwhelming
        await asyncio.sleep(0.01)  # 10ms between queries
    
    metrics.end_time = time.perf_counter()
    
    summary = metrics.get_summary()
    print(f"✅ Sustained load test complete")
    print(f"   Total queries: {summary['total_queries']}")
    print(f"   Duration: {summary['duration_seconds']:.1f}s")
    print(f"   Throughput: {summary['queries_per_second']:.0f} queries/sec")
    print(f"   Cache hit rate: {summary['cache_hit_rate']*100:.1f}%")
    print(f"   Mean latency: {summary['latency_mean_ms']:.2f}ms")
    print(f"   P95 latency: {summary['latency_p95_ms']:.2f}ms")
    
    return metrics


async def cleanup_test_data(pool, user_ids: List[str]):
    """Remove test data from cache tables."""
    print(f"\n{'='*80}")
    print("Cleanup: Removing test data")
    print(f"{'='*80}")
    
    query = """
        DELETE FROM strategic_memory_health
        WHERE user_id = ANY($1)
        RETURNING id
    """
    
    async with pool.acquire() as conn:
        deleted = await conn.fetch(query, user_ids)
        print(f"✅ Cleaned up {len(deleted)} test cache entries")


async def main():
    """Run comprehensive performance tests."""
    print("="*80)
    print("PHASE 3A TASK 3: Strategic Cache Performance Testing")
    print("="*80)
    
    # Get PostgreSQL pool
    pool = await get_postgres_pool()
    if not pool:
        print("❌ FAILED: Could not get PostgreSQL pool")
        return False
    
    print("✅ PostgreSQL pool acquired")
    
    # Test configuration
    bot_name = 'elena'
    num_test_users = 20
    
    try:
        # Setup test data
        user_ids = await setup_test_data(pool, num_users=num_test_users, bot_name=bot_name)
        
        # Wait for data to be committed
        await asyncio.sleep(0.5)
        
        # Test 1: Low concurrency (10 queries)
        metrics_10 = await test_concurrent_reads(pool, user_ids, bot_name, concurrency=10)
        
        # Test 2: Medium concurrency (50 queries)
        metrics_50 = await test_concurrent_reads(pool, user_ids, bot_name, concurrency=50)
        
        # Test 3: High concurrency (100 queries)
        metrics_100 = await test_concurrent_reads(pool, user_ids, bot_name, concurrency=100)
        
        # Test 4: Very high concurrency (200 queries)
        metrics_200 = await test_concurrent_reads(pool, user_ids, bot_name, concurrency=200)
        
        # Test 5: Cache miss scenario
        metrics_miss = await test_cache_miss_scenario(pool, bot_name, num_queries=50)
        
        # Test 6: Sustained load
        metrics_sustained = await test_sustained_load(pool, user_ids, bot_name, duration_seconds=30)
        
        # Cleanup
        await cleanup_test_data(pool, user_ids)
        
        # Final summary
        print(f"\n{'='*80}")
        print("✅ ALL PERFORMANCE TESTS COMPLETE!")
        print(f"{'='*80}")
        
        print("\n📊 Performance Summary Across All Tests:")
        print(f"   10 concurrent:  P95={metrics_10.get_summary()['latency_p95_ms']:.2f}ms")
        print(f"   50 concurrent:  P95={metrics_50.get_summary()['latency_p95_ms']:.2f}ms")
        print(f"   100 concurrent: P95={metrics_100.get_summary()['latency_p95_ms']:.2f}ms")
        print(f"   200 concurrent: P95={metrics_200.get_summary()['latency_p95_ms']:.2f}ms")
        print(f"   Cache miss:     P95={metrics_miss.get_summary()['latency_p95_ms']:.2f}ms")
        print(f"   Sustained load: P95={metrics_sustained.get_summary()['latency_p95_ms']:.2f}ms")
        
        # Overall validation
        all_metrics = [metrics_10, metrics_50, metrics_100, metrics_200, metrics_sustained]
        max_p95 = max(m.get_summary()['latency_p95_ms'] for m in all_metrics)
        min_hit_rate = min(m.get_summary()['cache_hit_rate'] for m in all_metrics)
        
        print(f"\n🎯 Overall Performance:")
        print(f"   Maximum P95 latency: {max_p95:.2f}ms (target: <5ms)")
        print(f"   Minimum cache hit rate: {min_hit_rate*100:.1f}% (target: >95%)")
        
        if max_p95 <= 5.0 and min_hit_rate >= 0.95:
            print(f"\n✅ PERFORMANCE TARGETS MET - PRODUCTION READY!")
            return True
        else:
            print(f"\n⚠️  Some performance targets not met - review results above")
            return False
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
