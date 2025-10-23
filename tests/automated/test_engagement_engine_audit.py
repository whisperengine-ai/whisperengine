"""
Test Engagement Engine Audit - Enhancement #4

Validates that telemetry tracking works correctly for ProactiveConversationEngagementEngine
to determine actual production usage patterns.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine


class TestEngagementEngineAudit:
    """Test telemetry tracking for engagement engine usage audit."""
    
    @pytest.mark.asyncio
    async def test_engagement_engine_initialization_telemetry(self):
        """Test that engagement engine initializes with telemetry tracking."""
        # Create engagement engine
        engine = ProactiveConversationEngagementEngine(
            thread_manager=None,
            emotional_engine=None,
            personality_profiler=None,
            memory_manager=None
        )
        
        # Verify telemetry initialized
        assert hasattr(engine, '_telemetry')
        assert engine._telemetry is not None
        assert engine._telemetry['analyze_conversation_engagement_count'] == 0
        assert engine._telemetry['analyze_engagement_potential_count'] == 0
        assert engine._telemetry['interventions_generated'] == 0
        assert engine._telemetry['total_recommendations'] == 0
        assert 'initialization_time' in engine._telemetry
        
        print(f"✅ EngagementEngine telemetry initialized: {engine._telemetry}")
    
    @pytest.mark.asyncio
    async def test_analyze_engagement_potential_telemetry(self):
        """Test that analyze_engagement_potential tracks invocations."""
        # Create engagement engine
        engine = ProactiveConversationEngagementEngine(
            thread_manager=None,
            emotional_engine=None,
            personality_profiler=None,
            memory_manager=None
        )
        
        # Mock the internal analyze_conversation_engagement method
        engine.analyze_conversation_engagement = AsyncMock(return_value={
            "engagement_potential": 0.7,
            "flow_state": "engaging",
            "intervention_needed": False,
            "recommendations": []
        })
        
        # Call analyze_engagement_potential multiple times
        message = Mock()
        message.content = "This is a test message"
        
        result1 = await engine.analyze_engagement_potential(
            user_id="test_user_123",
            message=message,
            conversation_history=[]
        )
        
        result2 = await engine.analyze_engagement_potential(
            user_id="test_user_123",
            message=message,
            conversation_history=[]
        )
        
        # Verify telemetry tracking
        assert engine._telemetry['analyze_engagement_potential_count'] == 2
        assert result1 is not None
        assert result2 is not None
        
        print(f"✅ analyze_engagement_potential telemetry validated: "
              f"{engine._telemetry['analyze_engagement_potential_count']} calls")
    
    @pytest.mark.asyncio
    async def test_analyze_conversation_engagement_telemetry(self):
        """Test that analyze_conversation_engagement tracks invocations."""
        # Create engagement engine
        engine = ProactiveConversationEngagementEngine(
            thread_manager=None,
            emotional_engine=None,
            personality_profiler=None,
            memory_manager=None
        )
        
        # Mock internal methods to avoid complex dependencies
        engine._analyze_conversation_flow = AsyncMock(return_value={
            "current_state": Mock(value="engaging"),
            "trend": "stable",
            "engagement_score": 0.7,
            "flow_indicators": []
        })
        engine._detect_stagnation_signals = AsyncMock(return_value={
            "risk_level": "low"
        })
        engine._assess_intervention_need = AsyncMock(return_value=False)
        engine._update_conversation_rhythm = AsyncMock()
        engine._get_conversation_rhythm_summary = AsyncMock(return_value={})
        engine._get_recent_interventions = AsyncMock(return_value=[])
        
        # Call method
        result = await engine.analyze_conversation_engagement(
            user_id="test_user_123",
            context_id="context_123",
            recent_messages=[
                {"content": "Hello", "timestamp": datetime.now().isoformat()},
                {"content": "How are you?", "timestamp": datetime.now().isoformat()}
            ],
            current_thread_info=None
        )
        
        # Verify telemetry
        assert engine._telemetry['analyze_conversation_engagement_count'] == 1
        assert result is not None
        assert result['flow_state'] == "engaging"
        
        print(f"✅ analyze_conversation_engagement telemetry validated: "
              f"{engine._telemetry['analyze_conversation_engagement_count']} calls")
    
    @pytest.mark.asyncio
    async def test_intervention_generation_telemetry(self):
        """Test that intervention generation tracks recommendations."""
        # Create engagement engine
        engine = ProactiveConversationEngagementEngine(
            thread_manager=None,
            emotional_engine=None,
            personality_profiler=None,
            memory_manager=None
        )
        
        # Mock internal methods
        engine._analyze_conversation_flow = AsyncMock(return_value={
            "current_state": Mock(value="stagnating"),
            "trend": "declining",
            "engagement_score": 0.3,
            "flow_indicators": []
        })
        engine._detect_stagnation_signals = AsyncMock(return_value={
            "risk_level": "high"
        })
        engine._assess_intervention_need = AsyncMock(return_value=True)  # Intervention needed
        
        # Mock recommendation generation to return mock recommendations
        mock_recommendations = [
            {"type": "topic_suggestion", "strategy": Mock(value="topic_suggestion")},
            {"type": "follow_up_question", "strategy": Mock(value="follow_up_question")}
        ]
        engine._generate_proactive_recommendations = AsyncMock(return_value=mock_recommendations)
        engine._update_conversation_rhythm = AsyncMock()
        engine._get_conversation_rhythm_summary = AsyncMock(return_value={})
        engine._get_recent_interventions = AsyncMock(return_value=[])
        
        # Call method
        result = await engine.analyze_conversation_engagement(
            user_id="test_user_123",
            context_id="context_123",
            recent_messages=[
                {"content": "hi", "timestamp": datetime.now().isoformat()}
            ],
            current_thread_info=None
        )
        
        # Verify intervention telemetry
        assert engine._telemetry['interventions_generated'] == 1
        assert engine._telemetry['total_recommendations'] == 2
        assert result['intervention_needed'] is True
        assert len(result['recommendations']) == 2
        
        print(f"✅ Intervention telemetry validated: "
              f"{engine._telemetry['interventions_generated']} interventions, "
              f"{engine._telemetry['total_recommendations']} recommendations")
    
    @pytest.mark.asyncio
    async def test_telemetry_accumulation(self):
        """Test that telemetry accumulates across multiple calls."""
        # Create engagement engine
        engine = ProactiveConversationEngagementEngine(
            thread_manager=None,
            emotional_engine=None,
            personality_profiler=None,
            memory_manager=None
        )
        
        # Mock methods
        engine._analyze_conversation_flow = AsyncMock(return_value={
            "current_state": Mock(value="stagnating"),
            "trend": "declining",
            "engagement_score": 0.3,
            "flow_indicators": []
        })
        engine._detect_stagnation_signals = AsyncMock(return_value={"risk_level": "high"})
        engine._assess_intervention_need = AsyncMock(return_value=True)
        engine._generate_proactive_recommendations = AsyncMock(return_value=[
            {"type": "test", "strategy": Mock(value="test")}
        ])
        engine._update_conversation_rhythm = AsyncMock()
        engine._get_conversation_rhythm_summary = AsyncMock(return_value={})
        engine._get_recent_interventions = AsyncMock(return_value=[])
        
        # Call multiple times
        for i in range(3):
            await engine.analyze_conversation_engagement(
                user_id=f"user_{i}",
                context_id=f"context_{i}",
                recent_messages=[{"content": "test", "timestamp": datetime.now().isoformat()}],
                current_thread_info=None
            )
        
        # Verify accumulation
        assert engine._telemetry['analyze_conversation_engagement_count'] == 3
        assert engine._telemetry['interventions_generated'] == 3
        assert engine._telemetry['total_recommendations'] == 3  # 1 per intervention
        
        print(f"✅ Telemetry accumulation validated: "
              f"{engine._telemetry['analyze_conversation_engagement_count']} analyses, "
              f"{engine._telemetry['interventions_generated']} interventions, "
              f"{engine._telemetry['total_recommendations']} recommendations")


def test_audit_summary():
    """Print summary of engagement engine audit implementation."""
    print("\n" + "="*80)
    print("Engagement Engine Audit Summary (Enhancement #4)")
    print("="*80)
    print("\n✅ TELEMETRY IMPLEMENTED:")
    print("   - analyze_engagement_potential_count (adapter method invocations)")
    print("   - analyze_conversation_engagement_count (main analysis invocations)")
    print("   - interventions_generated (proactive interventions triggered)")
    print("   - total_recommendations (cumulative recommendations generated)")
    print("   - initialization_time (engine startup timestamp)")
    
    print("\n📊 MONITORING STRATEGY:")
    print("   - Logs every invocation at INFO level")
    print("   - Tracks cumulative intervention and recommendation counts")
    print("   - Non-intrusive (no behavior changes, logging only)")
    
    print("\n🎯 EVALUATION CRITERIA:")
    print("   - IF analyze_engagement_potential_count == 0:")
    print("     → Feature is UNUSED - consider disabling")
    print("   - IF analyze_engagement_potential_count > 0 AND interventions_generated == 0:")
    print("     → Feature invoked but never triggers - review thresholds")
    print("   - IF interventions_generated > 0:")
    print("     → Feature is ACTIVE - evaluate effectiveness")
    print("   - IF interventions_generated / analyze_engagement_potential_count < 0.05:")
    print("     → Rare usage (<5%) - consider optimization or removal")
    print("   - IF interventions_generated / analyze_engagement_potential_count >= 0.05:")
    print("     → Regular usage (>=5%) - keep and monitor")
    
    print("\n📝 DATA COLLECTION PLAN:")
    print("   1. Deploy to production with telemetry enabled")
    print("   2. Collect 1-2 weeks of conversation data")
    print("   3. Grep Discord logs for 'ENGAGEMENT TELEMETRY' entries")
    print("   4. Calculate usage rates and intervention frequency")
    print("   5. Decision: Keep as-is, optimize, or disable feature")
    
    print("\n💾 MEMORY IMPACT:")
    print("   - IF disabled: ~5-10MB memory savings per bot")
    print("   - Current: Lazy initialization (low overhead)")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
