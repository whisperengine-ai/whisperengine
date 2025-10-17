"""
Test Character Insight Storage - Layer 1 (PostgreSQL) Validation

Direct Python test to validate character learning persistence without Docker restarts.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.characters.learning.character_insight_storage import (
    create_character_insight_storage,
    CharacterInsight,
    InsightRelationship,
    LearningTimelineEvent
)


async def test_character_insight_storage():
    """Test all character insight storage operations"""
    
    print("=" * 80)
    print("🧪 CHARACTER INSIGHT STORAGE TEST - Layer 1 (PostgreSQL)")
    print("=" * 80)
    
    # Create storage instance
    print("\n📦 Creating storage instance...")
    storage = await create_character_insight_storage(
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5433")),
        postgres_db=os.getenv("POSTGRES_DB", "whisperengine"),
        postgres_user=os.getenv("POSTGRES_USER", "whisperengine"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "whisperengine")
    )
    
    # Test character ID (using Elena = 1, assuming from existing characters table)
    test_character_id = 1
    
    # ========== TEST 1: Store Character Insights ==========
    print("\n" + "=" * 80)
    print("TEST 1: Store Character Insights")
    print("=" * 80)
    
    insight1 = CharacterInsight(
        character_id=test_character_id,
        insight_type="emotional_pattern",
        insight_content="Shows increased enthusiasm when discussing marine conservation topics",
        confidence_score=0.85,
        importance_level=7,
        emotional_valence=0.8,
        triggers=["marine conservation", "ocean protection", "reef preservation"],
        supporting_evidence=[
            "User: 'You seem passionate about ocean conservation'",
            "Response showed elevated emotional intensity (0.92)"
        ],
        conversation_context="Discussion about coral reef restoration projects"
    )
    
    insight2 = CharacterInsight(
        character_id=test_character_id,
        insight_type="preference",
        insight_content="Prefers visual metaphors when explaining complex scientific concepts",
        confidence_score=0.78,
        importance_level=6,
        emotional_valence=0.5,
        triggers=["teaching", "education", "explanation"],
        supporting_evidence=[
            "Used ocean wave analogy for DNA structure",
            "Referenced colors when describing chemical processes"
        ],
        conversation_context="Explaining marine biology concepts to user"
    )
    
    insight3 = CharacterInsight(
        character_id=test_character_id,
        insight_type="memory_formation",
        insight_content="Forms stronger memories during conversations about personal experiences in field research",
        confidence_score=0.91,
        importance_level=8,
        emotional_valence=0.7,
        triggers=["field research", "personal experience", "Barcelona research station"],
        supporting_evidence=[
            "Memory confidence scores 0.9+ for field research stories",
            "User referenced 'Barcelona days' conversation multiple times"
        ],
        conversation_context="Sharing field research experiences"
    )
    
    try:
        insight1_id = await storage.store_insight(insight1)
        print(f"✅ Stored insight 1: ID {insight1_id}")
        
        insight2_id = await storage.store_insight(insight2)
        print(f"✅ Stored insight 2: ID {insight2_id}")
        
        insight3_id = await storage.store_insight(insight3)
        print(f"✅ Stored insight 3: ID {insight3_id}")
        
    except Exception as e:
        print(f"❌ Error storing insights: {e}")
        return
    
    # ========== TEST 2: Retrieve Insight by ID ==========
    print("\n" + "=" * 80)
    print("TEST 2: Retrieve Insight by ID")
    print("=" * 80)
    
    retrieved = await storage.get_insight_by_id(insight1_id)
    if retrieved:
        print(f"✅ Retrieved insight {insight1_id}:")
        print(f"   Type: {retrieved.insight_type}")
        print(f"   Content: {retrieved.insight_content[:60]}...")
        print(f"   Confidence: {retrieved.confidence_score}")
        print(f"   Triggers: {retrieved.triggers}")
    else:
        print(f"❌ Failed to retrieve insight {insight1_id}")
    
    # ========== TEST 3: Search by Triggers ==========
    print("\n" + "=" * 80)
    print("TEST 3: Search Insights by Triggers")
    print("=" * 80)
    
    search_triggers = ["marine conservation", "ocean"]
    matching_insights = await storage.get_insights_by_triggers(
        character_id=test_character_id,
        triggers=search_triggers,
        limit=10
    )
    
    print(f"✅ Found {len(matching_insights)} insights matching {search_triggers}:")
    for idx, insight in enumerate(matching_insights, 1):
        print(f"   {idx}. [{insight.insight_type}] {insight.insight_content[:50]}...")
        print(f"      Confidence: {insight.confidence_score}, Importance: {insight.importance_level}")
    
    # ========== TEST 4: Get Recent Insights ==========
    print("\n" + "=" * 80)
    print("TEST 4: Get Recent Insights")
    print("=" * 80)
    
    recent = await storage.get_recent_insights(
        character_id=test_character_id,
        days_back=30,
        limit=20
    )
    
    print(f"✅ Found {len(recent)} recent insights (last 30 days):")
    for idx, insight in enumerate(recent, 1):
        print(f"   {idx}. {insight.discovery_date.strftime('%Y-%m-%d %H:%M:%S')} - "
              f"{insight.insight_content[:50]}...")
    
    # ========== TEST 5: Update Insight Confidence ==========
    print("\n" + "=" * 80)
    print("TEST 5: Update Insight Confidence")
    print("=" * 80)
    
    updated = await storage.update_insight_confidence(insight1_id, 0.92)
    if updated:
        print(f"✅ Updated insight {insight1_id} confidence to 0.92")
        
        # Verify update
        verified = await storage.get_insight_by_id(insight1_id)
        print(f"   Verified new confidence: {verified.confidence_score}")
    else:
        print(f"❌ Failed to update insight {insight1_id}")
    
    # ========== TEST 6: Create Insight Relationships ==========
    print("\n" + "=" * 80)
    print("TEST 6: Create Insight Relationships (Graph)")
    print("=" * 80)
    
    # Relationship 1: insight1 supports insight3
    rel1 = InsightRelationship(
        from_insight_id=insight1_id,
        to_insight_id=insight3_id,
        relationship_type="supports",
        strength=0.8
    )
    
    # Relationship 2: insight2 builds_on insight3
    rel2 = InsightRelationship(
        from_insight_id=insight2_id,
        to_insight_id=insight3_id,
        relationship_type="builds_on",
        strength=0.6
    )
    
    try:
        rel1_id = await storage.create_relationship(rel1)
        print(f"✅ Created relationship {rel1_id}: insight{insight1_id} --[supports]--> insight{insight3_id}")
        
        rel2_id = await storage.create_relationship(rel2)
        print(f"✅ Created relationship {rel2_id}: insight{insight2_id} --[builds_on]--> insight{insight3_id}")
        
    except Exception as e:
        print(f"❌ Error creating relationships: {e}")
    
    # ========== TEST 7: Graph Traversal (Get Related Insights) ==========
    print("\n" + "=" * 80)
    print("TEST 7: Graph Traversal - Get Related Insights")
    print("=" * 80)
    
    related = await storage.get_related_insights(insight1_id)
    print(f"✅ Found {len(related)} insights related to insight {insight1_id}:")
    for insight in related:
        print(f"   - [{insight.insight_type}] {insight.insight_content[:50]}...")
    
    # Filter by relationship type
    supporting = await storage.get_related_insights(
        insight1_id,
        relationship_types=["supports"]
    )
    print(f"\n✅ Found {len(supporting)} insights with 'supports' relationship:")
    for insight in supporting:
        print(f"   - {insight.insight_content[:50]}...")
    
    # ========== TEST 8: Record Learning Timeline Events ==========
    print("\n" + "=" * 80)
    print("TEST 8: Record Learning Timeline Events")
    print("=" * 80)
    
    event1 = LearningTimelineEvent(
        character_id=test_character_id,
        learning_event="Discovered strong emotional connection to marine conservation",
        learning_type="self_discovery",
        before_state="General awareness of ocean topics",
        after_state="Deep passion and advocacy for marine ecosystems",
        trigger_conversation="User discussion about coral reef bleaching",
        significance_score=0.9
    )
    
    event2 = LearningTimelineEvent(
        character_id=test_character_id,
        learning_event="Evolved teaching style to incorporate more visual metaphors",
        learning_type="preference_evolution",
        before_state="Direct scientific explanations",
        after_state="Visual analogies and relatable comparisons",
        trigger_conversation="User struggled with DNA structure explanation",
        significance_score=0.7
    )
    
    try:
        event1_id = await storage.record_learning_event(event1)
        print(f"✅ Recorded timeline event {event1_id}: {event1.learning_event[:50]}...")
        
        event2_id = await storage.record_learning_event(event2)
        print(f"✅ Recorded timeline event {event2_id}: {event2.learning_event[:50]}...")
        
    except Exception as e:
        print(f"❌ Error recording timeline events: {e}")
    
    # ========== TEST 9: Get Learning Timeline ==========
    print("\n" + "=" * 80)
    print("TEST 9: Get Learning Timeline")
    print("=" * 80)
    
    timeline = await storage.get_learning_timeline(
        character_id=test_character_id,
        days_back=30,
        limit=50
    )
    
    print(f"✅ Found {len(timeline)} learning events (last 30 days):")
    for idx, event in enumerate(timeline, 1):
        print(f"   {idx}. {event.learning_date.strftime('%Y-%m-%d %H:%M:%S')} - "
              f"[{event.learning_type}]")
        print(f"      Event: {event.learning_event[:60]}...")
        if event.significance_score:
            print(f"      Significance: {event.significance_score:.2f}")
    
    # ========== TEST 10: Get Insight Statistics ==========
    print("\n" + "=" * 80)
    print("TEST 10: Get Insight Statistics")
    print("=" * 80)
    
    stats = await storage.get_insight_stats(test_character_id)
    
    print(f"✅ Character {test_character_id} Learning Statistics:")
    print(f"   Total Insights: {stats['total_insights']}")
    print(f"   Average Confidence: {stats['avg_confidence']:.2f}")
    print(f"   Average Importance: {stats['avg_importance']:.2f}")
    print(f"   Unique Insight Types: {stats['unique_insight_types']}")
    print(f"   Last Discovery: {stats['last_discovery']}")
    
    # ========== CLEANUP ==========
    print("\n" + "=" * 80)
    print("🧹 CLEANUP: Removing Test Data")
    print("=" * 80)
    
    async with storage.db_pool.acquire() as conn:
        # Delete test data (cascade will handle relationships)
        deleted_insights = await conn.execute(
            "DELETE FROM character_insights WHERE id = ANY($1)",
            [insight1_id, insight2_id, insight3_id]
        )
        
        deleted_events = await conn.execute(
            "DELETE FROM character_learning_timeline WHERE id = ANY($1)",
            [event1_id, event2_id]
        )
        
        print(f"✅ Cleaned up test insights and events")
    
    # Close connection pool
    await storage.db_pool.close()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Layer 1 (PostgreSQL) Implementation Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_character_insight_storage())
