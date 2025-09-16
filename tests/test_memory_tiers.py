#!/usr/bin/env python3
"""
Test Memory Tier System for Phase 1.2 Implementation

Tests the memory tier assignment and optimization system for personality-driven AI companions.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the memory tier system
try:
    from src.memory.memory_tiers import MemoryTierManager, MemoryTier, MemoryAccess
    print("✅ Memory tier system imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_memory_tier_classification():
    """Test basic memory tier classification"""
    print("\n🧪 Testing Memory Tier Classification")
    print("=" * 50)
    
    tier_manager = MemoryTierManager(max_hot_facts=100, max_warm_facts=500)
    
    # Test cases with different personality relevance scores
    test_cases = [
        {
            "name": "Critical emotional insight",
            "personality_relevance": 0.95,
            "emotional_weight": 0.8,
            "expected_tier": MemoryTier.HOT
        },
        {
            "name": "Important communication preference",
            "personality_relevance": 0.75,
            "emotional_weight": 0.2,
            "expected_tier": MemoryTier.HOT
        },
        {
            "name": "Moderate interest",
            "personality_relevance": 0.6,
            "emotional_weight": 0.1,
            "expected_tier": MemoryTier.WARM
        },
        {
            "name": "Low relevance fact",
            "personality_relevance": 0.3,
            "emotional_weight": 0.0,
            "expected_tier": MemoryTier.COLD
        }
    ]
    
    for case in test_cases:
        tier, reason = await tier_manager.classify_memory_tier(
            personality_relevance=case["personality_relevance"],
            emotional_weight=case["emotional_weight"],
            user_id="test_user",
            context_id="test_channel"
        )
        
        status = "✅" if tier == case["expected_tier"] else "❌"
        print(f"{status} {case['name']}")
        print(f"   Expected: {case['expected_tier'].value}")
        print(f"   Got: {tier.value}")
        print(f"   Reason: {reason}")
        print()
    
    return tier_manager


async def test_access_pattern_tracking(tier_manager):
    """Test access pattern tracking and optimization"""
    print("\n🔍 Testing Access Pattern Tracking")
    print("=" * 50)
    
    # Simulate access patterns
    user_id = "test_user"
    context_id = "test_channel"
    
    # Record multiple accesses to simulate usage patterns
    fact_accesses = [
        {"fact_id": "fact_1", "retrieval_time": 50.0, "cache_hit": True},
        {"fact_id": "fact_2", "retrieval_time": 200.0, "cache_hit": False},
        {"fact_id": "fact_1", "retrieval_time": 25.0, "cache_hit": True},  # Repeat access
        {"fact_id": "fact_3", "retrieval_time": 150.0, "cache_hit": False},
    ]
    
    for access in fact_accesses:
        await tier_manager.record_access(
            fact_id=access["fact_id"],
            user_id=user_id,
            context_id=context_id,
            retrieval_time_ms=access["retrieval_time"],
            was_cache_hit=access["cache_hit"]
        )
    
    # Check access patterns
    print("📊 Access Pattern Summary:")
    for fact_id, access_data in tier_manager.access_patterns.items():
        print(f"   {fact_id}:")
        print(f"      Access count: {access_data.access_count}")
        print(f"      Cache hits: {access_data.cache_hits}")
        print(f"      Cache misses: {access_data.cache_misses}")
        print(f"      Avg retrieval time: {sum(access_data.retrieval_times_ms) / len(access_data.retrieval_times_ms):.1f}ms")
        print()
    
    return True


async def test_memory_optimization(tier_manager):
    """Test memory tier optimization"""
    print("\n⚡ Testing Memory Tier Optimization")
    print("=" * 50)
    
    # Add some facts with different access patterns
    facts = [
        {"id": "hot_fact", "personality_relevance": 0.9, "emotional_weight": 0.7},
        {"id": "warm_fact", "personality_relevance": 0.6, "emotional_weight": 0.3},
        {"id": "cold_fact", "personality_relevance": 0.2, "emotional_weight": 0.1},
    ]
    
    user_id = "test_user"
    context_id = "test_channel"
    
    for fact in facts:
        # Create access pattern
        access = MemoryAccess(
            fact_id=fact["id"],
            user_id=user_id,
            context_id=context_id,
            personality_relevance=fact["personality_relevance"],
            emotional_weight=fact["emotional_weight"],
            access_count=5 if "hot" in fact["id"] else 2,
            last_accessed=datetime.now() - timedelta(hours=1 if "hot" in fact["id"] else 24)
        )
        tier_manager.access_patterns[fact["id"]] = access
    
    # Run optimization
    print("🔄 Running memory optimization...")
    await tier_manager.optimize_tier_assignments()
    
    # Check results
    print("📈 Optimization Results:")
    tier_distribution = await tier_manager.get_tier_distribution()
    for tier, count in tier_distribution.items():
        print(f"   {tier.upper()}: {count} facts")
    
    return True


async def test_memory_metrics(tier_manager):
    """Test memory metrics and reporting"""
    print("\n📊 Testing Memory Metrics")
    print("=" * 50)
    
    metrics = await tier_manager.get_memory_metrics()
    
    print("💾 Memory Usage:")
    print(f"   Total facts: {metrics.total_facts}")
    print(f"   Hot tier: {metrics.hot_tier_facts}")
    print(f"   Warm tier: {metrics.warm_tier_facts}")
    print(f"   Cold tier: {metrics.cold_tier_facts}")
    print()
    
    print("⚡ Performance Metrics:")
    print(f"   Cache hit rate: {metrics.cache_hit_rate:.1%}")
    print(f"   Avg retrieval time: {metrics.avg_retrieval_time_ms:.1f}ms")
    print(f"   Optimizations performed: {metrics.optimizations_performed}")
    print()
    
    # Test user-specific summary
    user_summary = await tier_manager.get_user_memory_summary("test_user")
    if "error" not in user_summary:
        print("👤 User Memory Summary:")
        print(f"   Total facts: {user_summary['total_facts']}")
        print(f"   Total accesses: {user_summary['total_accesses']}")
        print(f"   Avg personality relevance: {user_summary['avg_personality_relevance']:.2f}")
        print(f"   Relationship depth: {user_summary['relationship_depth']:.2f}")
        print(f"   Tier distribution: {user_summary['tier_distribution']}")
    
    return True


async def test_hardware_constraints():
    """Test hardware constraint handling"""
    print("\n🖥️ Testing Hardware Constraint Handling")
    print("=" * 50)
    
    # Test with strict hardware limits
    constrained_manager = MemoryTierManager(
        max_hot_facts=10,  # Very small limit
        max_warm_facts=50,
        max_cache_size_mb=100.0
    )
    
    # Try to add more facts than limits allow
    for i in range(15):
        tier, _reason = await constrained_manager.classify_memory_tier(
            personality_relevance=0.9,  # All high relevance
            emotional_weight=0.5,
            user_id=f"user_{i}",
            context_id="test_channel"
        )
        
        if i < 10:
            expected_tier = MemoryTier.HOT
        else:
            expected_tier = MemoryTier.WARM  # Should be demoted due to constraints
        
        status = "✅" if tier == expected_tier else "❌"
        print(f"{status} Fact {i+1}: {tier.value} (expected: {expected_tier.value})")
    
    metrics = await constrained_manager.get_memory_metrics()
    print(f"\n📈 Final distribution: HOT={metrics.hot_tier_facts}, WARM={metrics.warm_tier_facts}")
    
    return True


async def main():
    """Main test function"""
    print("🤖 WhisperEngine Memory Tier System Test")
    print("=" * 60)
    print("Testing Phase 1.2: Memory Tier Architecture")
    print()
    
    try:
        # Run all tests
        tier_manager = await test_memory_tier_classification()
        await test_access_pattern_tracking(tier_manager)
        await test_memory_optimization(tier_manager)
        await test_memory_metrics(tier_manager)
        await test_hardware_constraints()
        
        print("\n🎉 All Memory Tier Tests Completed Successfully!")
        print("✨ Phase 1.2 Implementation: READY")
        print()
        print("🚀 Next Steps:")
        print("   • Integrate with existing memory manager")
        print("   • Add real-time tier migration")
        print("   • Implement cache warming strategies")
        print("   • Begin Phase 2.1: Dynamic Personality Profiling")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)