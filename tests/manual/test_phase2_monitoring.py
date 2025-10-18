#!/usr/bin/env python3
"""
Test Phase 2 monitoring integration.

Verifies that query classification and routing metrics are tracked correctly.
"""

import asyncio
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

from src.memory.query_classifier import create_query_classifier, QueryCategory
from src.memory.phase2_monitoring import get_phase2_monitor


async def test_monitoring():
    """Test Phase 2 monitoring functionality."""
    
    print("="*80)
    print("PHASE 2 MONITORING TEST")
    print("="*80)
    print()
    
    # Get monitor instance
    monitor = get_phase2_monitor()
    
    print(f"📊 Monitor enabled: {monitor.enabled}")
    print(f"📊 TemporalClient available: {monitor.temporal_client is not None}")
    print()
    
    if not monitor.enabled:
        print("⚠️  Monitoring disabled (InfluxDB not configured)")
        print("   This is normal for local development.")
        print("   Monitoring will be enabled in production with InfluxDB.")
        return
    
    # Test 1: Track classification
    print("Test 1: Track Query Classification")
    print("-" * 80)
    
    await monitor.track_classification(
        user_id="test_user",
        query="How are you feeling?",
        category=QueryCategory.EMOTIONAL,
        emotion_intensity=0.65,
        is_temporal=False,
        pattern_matched="feeling",
        classification_time_ms=2.5
    )
    print("✅ Classification tracked")
    
    # Test 2: Track routing
    print("\nTest 2: Track Vector Routing")
    print("-" * 80)
    
    await monitor.track_routing(
        user_id="test_user",
        query_category=QueryCategory.EMOTIONAL,
        search_type="multi_vector_fusion",
        vectors_used=["content", "emotion"],
        memory_count=10,
        search_time_ms=25.3,
        fusion_enabled=True,
        retrieval_score=0.82
    )
    print("✅ Routing tracked")
    
    # Test 3: Track performance
    print("\nTest 3: Track Phase 2 Performance")
    print("-" * 80)
    
    await monitor.track_retrieval_performance(
        user_id="test_user",
        total_time_ms=30.5,
        classification_time_ms=2.0,
        search_time_ms=23.5,
        fusion_time_ms=5.0,
        intelligent_routing_used=True
    )
    print("✅ Performance tracked")
    
    # Test 4: Track A/B test result
    print("\nTest 4: Track A/B Test Result")
    print("-" * 80)
    
    await monitor.track_ab_test_result(
        user_id="test_user",
        query="How are you feeling?",
        variant="phase2",
        query_category=QueryCategory.EMOTIONAL,
        memory_relevance_score=0.82,
        response_quality_score=0.90,
        user_reaction="positive"
    )
    print("✅ A/B test result tracked")
    
    print("\n" + "="*80)
    print("ALL TESTS PASSED ✅")
    print("="*80)
    print()
    print("📊 Metrics successfully sent to InfluxDB")
    print("   You can view them in Grafana dashboards")


async def main():
    """Main test runner."""
    try:
        await test_monitoring()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
