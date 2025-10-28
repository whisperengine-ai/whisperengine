"""
Test script for Bot Self-Reflection Tools

Tests all 5 self-reflection tools in SemanticKnowledgeRouter:
1. reflect_on_interaction - Query past similar reflections
2. analyze_self_performance - Aggregate performance metrics
3. query_self_insights - Search for specific insights
4. adapt_personality_trait - Record trait adjustments
5. record_manual_insight - Store real-time observations
"""

import asyncio
import asyncpg
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.knowledge.semantic_router import create_semantic_knowledge_router


async def test_self_reflection_tools():
    """Test all 5 self-reflection tools"""
    
    # Connect to PostgreSQL
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        database='whisperengine',
        user='whisperengine',
        password='whisperengine_password'
    )
    
    # Create router (we don't need Qdrant/InfluxDB for these tests)
    router = create_semantic_knowledge_router(
        postgres_pool=pool,
        qdrant_client=None,
        influx_client=None
    )
    
    print("=" * 80)
    print("BOT SELF-REFLECTION TOOLS TEST")
    print("=" * 80)
    
    # Test 1: reflect_on_interaction
    print("\n" + "=" * 80)
    print("TEST 1: reflect_on_interaction")
    print("=" * 80)
    print("Query: Get past reflections for Jake with test user")
    
    reflections = await router.reflect_on_interaction(
        bot_name='jake',
        user_id='test_newest_1761640312',
        current_conversation_context='user asking repetitive questions about photography',
        limit=3
    )
    
    print(f"\nFound {len(reflections)} relevant past reflections:")
    for i, ref in enumerate(reflections, 1):
        print(f"\n  Reflection {i}:")
        print(f"    User ID: {ref['user_id']}")
        print(f"    Scores: E={ref['effectiveness_score']:.2f}, A={ref['authenticity_score']:.2f}, ER={ref['emotional_resonance']:.2f}")
        print(f"    Category: {ref['reflection_category']}")
        print(f"    Trigger: {ref['trigger_type']}")
        print(f"    Created: {ref['created_at']}")
        print(f"    Insight: {ref['learning_insight'][:150]}...")
    
    # Test 2: analyze_self_performance
    print("\n" + "=" * 80)
    print("TEST 2: analyze_self_performance")
    print("=" * 80)
    print("Query: Analyze Jake's overall performance (last 30 days)")
    
    performance = await router.analyze_self_performance(
        bot_name='jake',
        metric='overall',
        time_window_days=30
    )
    
    print(f"\nPerformance Analysis:")
    print(f"  Status: {performance.get('status')}")
    if performance.get('status') == 'success':
        print(f"  Total Reflections: {performance['total_reflections']}")
        print(f"  Metrics:")
        for metric, value in performance['metrics'].items():
            print(f"    {metric}: {value}")
        print(f"  Trend: {performance['trend']}")
        print(f"  Common Categories: {', '.join(performance['common_categories'][:3])}")
        print(f"  Common Triggers: {', '.join(performance['common_triggers'][:3])}")
    else:
        print(f"  Message: {performance.get('message')}")
    
    # Test 3: query_self_insights
    print("\n" + "=" * 80)
    print("TEST 3: query_self_insights")
    print("=" * 80)
    print("Query: Search for insights about 'pattern' and 'repetition'")
    
    insights = await router.query_self_insights(
        bot_name='jake',
        query_keywords=['pattern', 'repetition', 'loop'],
        category_filter=None,
        limit=3
    )
    
    print(f"\nFound {len(insights)} relevant insights:")
    for i, insight in enumerate(insights, 1):
        print(f"\n  Insight {i}:")
        print(f"    Relevance Score: {insight.get('relevance', 0):.4f}")
        print(f"    Category: {insight['reflection_category']}")
        print(f"    Learning: {insight['learning_insight'][:200]}...")
        if insight['improvement_suggestion']:
            print(f"    Suggestion: {insight['improvement_suggestion'][:200]}...")
    
    # Test 4: adapt_personality_trait
    print("\n" + "=" * 80)
    print("TEST 4: adapt_personality_trait")
    print("=" * 80)
    print("Action: Record need to adjust 'patience' trait")
    
    adaptation = await router.adapt_personality_trait(
        bot_name='jake',
        trait_name='patience',
        adjustment_reason='Need to handle repetitive user questions with more patience and less assumption of technical issues',
        metadata={'confidence': 0.85, 'based_on': 'conversation_stagnation patterns'}
    )
    
    print(f"\nPersonality Trait Adaptation:")
    print(f"  Status: {adaptation.get('status')}")
    print(f"  Bot: {adaptation.get('bot_name')}")
    print(f"  Trait: {adaptation.get('trait')}")
    print(f"  Reason: {adaptation.get('reason')}")
    print(f"  Reflection ID: {adaptation.get('reflection_id')}")
    print(f"  Recorded At: {adaptation.get('recorded_at')}")
    
    # Test 5: record_manual_insight
    print("\n" + "=" * 80)
    print("TEST 5: record_manual_insight")
    print("=" * 80)
    print("Action: Record manual observation")
    
    manual_insight = await router.record_manual_insight(
        bot_name='jake',
        insight='Noticed that users who ask about camera settings tend to be beginners, while lens questions come from intermediate photographers',
        insight_type='pattern_noticed',
        user_id=None,  # General observation
        context='Multiple conversations over past week'
    )
    
    print(f"\nManual Insight Recording:")
    print(f"  Status: {manual_insight.get('status')}")
    print(f"  Bot: {manual_insight.get('bot_name')}")
    print(f"  Type: {manual_insight.get('insight_type')}")
    print(f"  Insight: {manual_insight.get('insight')[:150]}...")
    print(f"  Reflection ID: {manual_insight.get('reflection_id')}")
    print(f"  Recorded At: {manual_insight.get('recorded_at')}")
    
    # Verify the new records were created
    print("\n" + "=" * 80)
    print("VERIFICATION: Check new records in database")
    print("=" * 80)
    
    async with pool.acquire() as conn:
        # Check personality adaptation record
        adaptation_record = await conn.fetchrow("""
            SELECT * FROM bot_self_reflections 
            WHERE id = $1
        """, adaptation['reflection_id'])
        
        print(f"\nPersonality Adaptation Record:")
        print(f"  Category: {adaptation_record['reflection_category']}")
        print(f"  Trigger: {adaptation_record['trigger_type']}")
        print(f"  Insight: {adaptation_record['learning_insight']}")
        
        # Check manual insight record
        manual_record = await conn.fetchrow("""
            SELECT * FROM bot_self_reflections 
            WHERE id = $1
        """, manual_insight['reflection_id'])
        
        print(f"\nManual Insight Record:")
        print(f"  Category: {manual_record['reflection_category']}")
        print(f"  Trigger: {manual_record['trigger_type']}")
        print(f"  Insight: {manual_record['learning_insight'][:100]}...")
    
    print("\n" + "=" * 80)
    print("✅ ALL 5 SELF-REFLECTION TOOLS TESTED SUCCESSFULLY!")
    print("=" * 80)
    
    await pool.close()


if __name__ == '__main__':
    asyncio.run(test_self_reflection_tools())
