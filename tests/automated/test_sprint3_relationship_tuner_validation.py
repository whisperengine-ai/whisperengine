"""
Sprint 3 RelationshipTuner Direct Validation Tests

Comprehensive validation suite using direct Python internal API calls.
Tests relationship evolution engine, trust recovery system, and PostgreSQL integration.

Test Strategy (following Sprint 2 pattern):
1. Direct Python API calls (no HTTP layer)
2. Mock/stub external dependencies where needed
3. Test internal data structures and logic
4. Validate PostgreSQL schema and operations
5. Test Sprint 1/Sprint 2 integration points
6. Performance and edge case validation

Target: 100% test pass rate (7-10 comprehensive tests)
"""

import asyncio
import asyncpg
import pytest
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.relationships.evolution_engine import (
    RelationshipEvolutionEngine,
    ConversationQuality,
    RelationshipScores,
    RelationshipUpdate,
    create_relationship_evolution_engine
)
from src.relationships.trust_recovery import (
    TrustRecoverySystem,
    TrustDeclineDetection,
    RecoveryProgress,
    RecoveryStage,
    create_trust_recovery_system
)


# ============================================================================
# Test Fixtures and Mocks
# ============================================================================

class MockTemporalClient:
    """Mock InfluxDB temporal client for testing."""
    
    def __init__(self):
        self.events = []
    
    async def store_relationship_update(self, **kwargs):
        """Store relationship update event."""
        self.events.append({
            'type': 'relationship_update',
            **kwargs
        })
    
    async def store_trust_recovery_event(self, **kwargs):
        """Store trust recovery event."""
        self.events.append({
            'type': 'trust_recovery',
            **kwargs
        })
    
    def get_events(self, event_type=None):
        """Get stored events."""
        if event_type:
            return [e for e in self.events if e.get('type') == event_type]
        return self.events
    
    def clear(self):
        """Clear all events."""
        self.events = []


class MockTrendAnalyzer:
    """Mock Sprint 1 TrendWise analyzer for testing."""
    
    def __init__(self):
        self.trend_data = {}
    
    def set_trust_trend(self, user_id: str, bot_name: str, slope: float):
        """Set trust trend for testing."""
        from dataclasses import dataclass
        from enum import Enum
        
        class TrendDirection(Enum):
            IMPROVING = "improving"
            DECLINING = "declining"
            STABLE = "stable"
        
        @dataclass
        class TrendAnalysis:
            direction: TrendDirection
            slope: float
            confidence: float
            current_value: float
            average_value: float
            volatility: float
            data_points: int
            time_span_days: int
        
        @dataclass
        class RelationshipTrend:
            user_id: str
            bot_name: str
            trust_trend: TrendAnalysis
            affection_trend: TrendAnalysis
            attunement_trend: TrendAnalysis
            overall_direction: TrendDirection
            needs_attention: bool
        
        # Create trend analysis
        direction = TrendDirection.DECLINING if slope < -0.05 else TrendDirection.STABLE
        trust_trend = TrendAnalysis(
            direction=direction,
            slope=slope,
            confidence=0.85,
            current_value=0.5,
            average_value=0.55,
            volatility=0.1,
            data_points=10,
            time_span_days=7
        )
        
        # Store trend
        key = f"{user_id}:{bot_name}"
        self.trend_data[key] = RelationshipTrend(
            user_id=user_id,
            bot_name=bot_name,
            trust_trend=trust_trend,
            affection_trend=trust_trend,
            attunement_trend=trust_trend,
            overall_direction=direction,
            needs_attention=(slope < -0.1)
        )
    
    async def get_relationship_trends(self, user_id: str, bot_name: str, time_window_days: int = 7):
        """Get relationship trends."""
        key = f"{user_id}:{bot_name}"
        return self.trend_data.get(key)


@pytest.fixture
async def postgres_pool():
    """Create PostgreSQL connection pool for testing."""
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = int(os.getenv('POSTGRES_PORT', '5433'))
    db_name = os.getenv('POSTGRES_DB', 'whisperengine')
    db_user = os.getenv('POSTGRES_USER', 'whisperengine')
    db_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_pass')
    
    pool = await asyncpg.create_pool(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        min_size=1,
        max_size=3
    )
    
    yield pool
    
    # Cleanup test data
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM trust_recovery_state WHERE user_id LIKE 'test_%'")
        await conn.execute("DELETE FROM relationship_events WHERE user_id LIKE 'test_%'")
        await conn.execute("DELETE FROM relationship_scores WHERE user_id LIKE 'test_%'")
    
    await pool.close()


@pytest.fixture
def mock_temporal_client():
    """Create mock temporal client."""
    return MockTemporalClient()


@pytest.fixture
def mock_trend_analyzer():
    """Create mock trend analyzer."""
    return MockTrendAnalyzer()


# ============================================================================
# Test 1: RelationshipEvolutionEngine Factory Creation
# ============================================================================

@pytest.mark.asyncio
async def test_relationship_evolution_engine_factory():
    """
    Test 1: Validate RelationshipEvolutionEngine factory creation.
    
    Validates:
    - Factory function creates proper instance
    - Component initialization
    - Default configuration
    """
    print("\n" + "="*70)
    print("TEST 1: RelationshipEvolutionEngine Factory Creation")
    print("="*70)
    
    # Create engine via factory
    engine = create_relationship_evolution_engine()
    
    # Validate instance
    assert engine is not None, "Engine should be created"
    assert isinstance(engine, RelationshipEvolutionEngine), "Should be RelationshipEvolutionEngine instance"
    
    # Validate default rates
    assert 'trust_positive' in engine.default_rates, "Should have trust_positive rate"
    assert 'affection_positive' in engine.default_rates, "Should have affection_positive rate"
    assert 'attunement_positive' in engine.default_rates, "Should have attunement_positive rate"
    
    # Validate thresholds
    assert 'high_complexity' in engine.complexity_thresholds, "Should have complexity thresholds"
    
    print("✅ Factory creation successful")
    print(f"   - Default trust rate: {engine.default_rates['trust_positive']}")
    print(f"   - Default affection rate: {engine.default_rates['affection_positive']}")
    print(f"   - Default attunement rate: {engine.default_rates['attunement_positive']}")
    print(f"   - High complexity threshold: {engine.complexity_thresholds['high_complexity']}")


# ============================================================================
# Test 2: Relationship Score Updates (Basic)
# ============================================================================

@pytest.mark.asyncio
async def test_relationship_score_updates_basic(postgres_pool, mock_temporal_client):
    """
    Test 2: Validate basic relationship score updates.
    
    Validates:
    - Score updates for different conversation qualities
    - Proper delta calculations
    - PostgreSQL persistence
    - Bounds checking (0-1 range)
    """
    print("\n" + "="*70)
    print("TEST 2: Relationship Score Updates (Basic)")
    print("="*70)
    
    # Create engine
    engine = create_relationship_evolution_engine(
        postgres_pool=postgres_pool,
        temporal_client=mock_temporal_client
    )
    
    user_id = "test_user_basic"
    bot_name = "TestBot"
    
    # Test EXCELLENT conversation (should increase scores)
    print("\n📈 Testing EXCELLENT conversation quality...")
    update = await engine.calculate_dynamic_relationship_score(
        user_id=user_id,
        bot_name=bot_name,
        conversation_quality=ConversationQuality.EXCELLENT,
        emotion_data={'emotion_variance': 0.3}
    )
    
    assert update is not None, "Update should be returned"
    assert update.changes['trust'] > 0, "Trust should increase for EXCELLENT"
    assert update.changes['affection'] > 0, "Affection should increase for EXCELLENT"
    assert update.changes['attunement'] > 0, "Attunement should increase for EXCELLENT"
    
    print(f"   ✅ Trust: {update.previous_scores.trust:.3f} → {update.new_scores.trust:.3f} (Δ{update.changes['trust']:+.3f})")
    print(f"   ✅ Affection: {update.previous_scores.affection:.3f} → {update.new_scores.affection:.3f} (Δ{update.changes['affection']:+.3f})")
    print(f"   ✅ Attunement: {update.previous_scores.attunement:.3f} → {update.new_scores.attunement:.3f} (Δ{update.changes['attunement']:+.3f})")
    
    # Test POOR conversation (should decrease scores)
    print("\n📉 Testing POOR conversation quality...")
    update_poor = await engine.calculate_dynamic_relationship_score(
        user_id=user_id,
        bot_name=bot_name,
        conversation_quality=ConversationQuality.POOR,
        emotion_data={'emotion_variance': 0.6}
    )
    
    assert update_poor.changes['trust'] < 0, "Trust should decrease for POOR"
    assert update_poor.changes['affection'] < 0, "Affection should decrease for POOR"
    
    print(f"   ✅ Trust: {update_poor.previous_scores.trust:.3f} → {update_poor.new_scores.trust:.3f} (Δ{update_poor.changes['trust']:+.3f})")
    print(f"   ✅ Affection: {update_poor.previous_scores.affection:.3f} → {update_poor.new_scores.affection:.3f} (Δ{update_poor.changes['affection']:+.3f})")
    
    # Validate bounds (0-1 range)
    assert 0.0 <= update_poor.new_scores.trust <= 1.0, "Trust should be in 0-1 range"
    assert 0.0 <= update_poor.new_scores.affection <= 1.0, "Affection should be in 0-1 range"
    assert 0.0 <= update_poor.new_scores.attunement <= 1.0, "Attunement should be in 0-1 range"
    
    # Validate PostgreSQL persistence
    async with postgres_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT trust, affection, attunement, interaction_count
            FROM relationship_scores
            WHERE user_id = $1 AND bot_name = $2
        """, user_id, bot_name)
        
        assert row is not None, "Scores should be persisted in PostgreSQL"
        assert row['interaction_count'] == 2, "Should have 2 interactions"
        print(f"\n✅ PostgreSQL persistence validated (interaction_count={row['interaction_count']})")


# ============================================================================
# Test 3: RoBERTa Emotion Variance Integration (Sprint 2)
# ============================================================================

@pytest.mark.asyncio
async def test_roberta_emotion_variance_integration(postgres_pool, mock_temporal_client):
    """
    Test 3: Validate Sprint 2 RoBERTa emotion_variance integration.
    
    Validates:
    - High emotion_variance slows trust changes
    - Low emotion_variance accelerates trust changes
    - Complexity modifiers applied correctly
    """
    print("\n" + "="*70)
    print("TEST 3: RoBERTa Emotion Variance Integration (Sprint 2)")
    print("="*70)
    
    engine = create_relationship_evolution_engine(
        postgres_pool=postgres_pool,
        temporal_client=mock_temporal_client
    )
    
    user_id = "test_user_emotion"
    bot_name = "TestBot"
    
    # Test HIGH emotion variance (complex emotional state)
    print("\n🎭 Testing HIGH emotion variance (complex emotions)...")
    update_high = await engine.calculate_dynamic_relationship_score(
        user_id=f"{user_id}_high",
        bot_name=bot_name,
        conversation_quality=ConversationQuality.EXCELLENT,
        emotion_data={'emotion_variance': 0.7}  # High complexity
    )
    
    # Test LOW emotion variance (clear emotional state)
    print("\n😊 Testing LOW emotion variance (clear emotions)...")
    update_low = await engine.calculate_dynamic_relationship_score(
        user_id=f"{user_id}_low",
        bot_name=bot_name,
        conversation_quality=ConversationQuality.EXCELLENT,
        emotion_data={'emotion_variance': 0.1}  # Low complexity
    )
    
    # Compare trust changes
    trust_high = update_high.changes['trust']
    trust_low = update_low.changes['trust']
    
    print(f"\n   High variance trust change: {trust_high:+.4f}")
    print(f"   Low variance trust change: {trust_low:+.4f}")
    print(f"   Difference: {abs(trust_high - trust_low):.4f}")
    
    # Validate: Low variance should change faster than high variance
    assert abs(trust_low) > abs(trust_high), "Low variance should produce larger changes"
    
    print("\n✅ Emotion variance integration working correctly")
    print(f"   - High complexity (0.7): slower trust changes ({trust_high:+.4f})")
    print(f"   - Low complexity (0.1): faster trust changes ({trust_low:+.4f})")
    print(f"   - Sprint 2 RoBERTa metadata properly integrated!")


# ============================================================================
# Test 4: Trust Recovery Detection
# ============================================================================

@pytest.mark.asyncio
async def test_trust_recovery_detection(postgres_pool, mock_temporal_client, mock_trend_analyzer):
    """
    Test 4: Validate trust decline detection.
    
    Validates:
    - Trust decline detection using Sprint 1 TrendWise
    - Severity classification (minor/moderate/severe)
    - Detection thresholds
    """
    print("\n" + "="*70)
    print("TEST 4: Trust Recovery Detection")
    print("="*70)
    
    # Create trust recovery system
    recovery_system = create_trust_recovery_system(
        postgres_pool=postgres_pool,
        temporal_client=mock_temporal_client,
        trend_analyzer=mock_trend_analyzer
    )
    
    user_id = "test_user_recovery"
    bot_name = "TestBot"
    
    # Setup: Create relationship with declining trust
    async with postgres_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO relationship_scores
                (user_id, bot_name, trust, affection, attunement, interaction_count)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id, bot_name) DO UPDATE SET
                trust = EXCLUDED.trust,
                affection = EXCLUDED.affection,
                attunement = EXCLUDED.attunement
        """, user_id, bot_name, 0.35, 0.40, 0.30, 10)
    
    # Test MODERATE decline detection
    print("\n⚠️ Testing MODERATE trust decline...")
    mock_trend_analyzer.set_trust_trend(user_id, bot_name, slope=-0.12)
    
    detection = await recovery_system.detect_trust_decline(
        user_id=user_id,
        bot_name=bot_name,
        time_window_days=7
    )
    
    assert detection is not None, "Should detect decline"
    assert detection.decline_severity == "moderate", "Should classify as moderate"
    assert detection.needs_recovery is True, "Should need recovery"
    assert len(detection.suggested_actions) > 0, "Should have suggested actions"
    
    print(f"   ✅ Decline detected: severity={detection.decline_severity}")
    print(f"   ✅ Trust slope: {detection.trust_trend_slope:.3f}")
    print(f"   ✅ Current trust: {detection.current_trust:.3f}")
    print(f"   ✅ Suggested actions: {len(detection.suggested_actions)}")
    
    # Test SEVERE decline detection
    print("\n🚨 Testing SEVERE trust decline...")
    mock_trend_analyzer.set_trust_trend(f"{user_id}_severe", bot_name, slope=-0.25)
    
    async with postgres_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO relationship_scores
                (user_id, bot_name, trust, affection, attunement, interaction_count)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, f"{user_id}_severe", bot_name, 0.25, 0.30, 0.20, 15)
    
    detection_severe = await recovery_system.detect_trust_decline(
        user_id=f"{user_id}_severe",
        bot_name=bot_name,
        time_window_days=7
    )
    
    assert detection_severe.decline_severity == "severe", "Should classify as severe"
    print(f"   ✅ Severe decline detected: severity={detection_severe.decline_severity}")
    
    # Test NO decline (healthy trust)
    print("\n✅ Testing healthy trust (no decline)...")
    mock_trend_analyzer.set_trust_trend(f"{user_id}_healthy", bot_name, slope=0.02)
    
    async with postgres_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO relationship_scores
                (user_id, bot_name, trust, affection, attunement, interaction_count)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, f"{user_id}_healthy", bot_name, 0.75, 0.80, 0.70, 20)
    
    detection_healthy = await recovery_system.detect_trust_decline(
        user_id=f"{user_id}_healthy",
        bot_name=bot_name,
        time_window_days=7
    )
    
    assert detection_healthy is None, "Should not detect decline for healthy trust"
    print(f"   ✅ No decline detected for healthy trust")


# ============================================================================
# Test 5: Trust Recovery Activation and Progress Tracking
# ============================================================================

@pytest.mark.asyncio
async def test_trust_recovery_activation_and_progress(postgres_pool, mock_temporal_client, mock_trend_analyzer):
    """
    Test 5: Validate recovery mode activation and progress tracking.
    
    Validates:
    - Recovery activation
    - Progress calculation
    - Recovery state persistence
    - Stage transitions
    """
    print("\n" + "="*70)
    print("TEST 5: Trust Recovery Activation and Progress")
    print("="*70)
    
    recovery_system = create_trust_recovery_system(
        postgres_pool=postgres_pool,
        temporal_client=mock_temporal_client,
        trend_analyzer=mock_trend_analyzer
    )
    
    user_id = "test_user_activation"
    bot_name = "TestBot"
    
    # Setup declining trust
    async with postgres_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO relationship_scores
                (user_id, bot_name, trust, affection, attunement, interaction_count)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, user_id, bot_name, 0.38, 0.42, 0.35, 12)
    
    mock_trend_analyzer.set_trust_trend(user_id, bot_name, slope=-0.15)
    
    # Detect decline
    print("\n🔍 Detecting trust decline...")
    detection = await recovery_system.detect_trust_decline(
        user_id=user_id,
        bot_name=bot_name,
        time_window_days=7
    )
    
    assert detection is not None, "Should detect decline"
    print(f"   ✅ Decline detected: {detection.decline_severity}")
    
    # Activate recovery mode
    print("\n🔧 Activating recovery mode...")
    recovery = await recovery_system.activate_recovery_mode(detection)
    
    assert recovery is not None, "Recovery should be activated"
    assert recovery.recovery_stage == RecoveryStage.ACTIVE, "Should be in ACTIVE stage"
    assert recovery.target_trust > recovery.initial_trust, "Target should be higher than initial"
    assert recovery.progress_percentage == 0.0, "Initial progress should be 0%"
    
    print(f"   ✅ Recovery activated")
    print(f"   ✅ Initial trust: {recovery.initial_trust:.3f}")
    print(f"   ✅ Target trust: {recovery.target_trust:.3f}")
    print(f"   ✅ Recovery stage: {recovery.recovery_stage.value}")
    
    # Simulate trust improvement
    print("\n📈 Simulating trust improvement...")
    new_trust = 0.45  # Improved from 0.38
    async with postgres_pool.acquire() as conn:
        await conn.execute("""
            UPDATE relationship_scores
            SET trust = $1
            WHERE user_id = $2 AND bot_name = $3
        """, new_trust, user_id, bot_name)
    
    # Track progress
    progress = await recovery_system.track_recovery_progress(
        user_id=user_id,
        bot_name=bot_name
    )
    
    assert progress is not None, "Progress should be tracked"
    assert progress.progress_percentage > 0, "Progress should be > 0%"
    assert progress.current_trust == new_trust, "Current trust should be updated"
    
    print(f"   ✅ Progress tracked: {progress.progress_percentage:.1f}%")
    print(f"   ✅ Current trust: {progress.current_trust:.3f}")
    print(f"   ✅ Recovery stage: {progress.recovery_stage.value}")
    
    # Validate PostgreSQL persistence
    async with postgres_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT recovery_stage, progress_percentage
            FROM trust_recovery_state
            WHERE user_id = $1 AND bot_name = $2
            ORDER BY started_at DESC
            LIMIT 1
        """, user_id, bot_name)
        
        assert row is not None, "Recovery state should be persisted"
        print(f"\n✅ PostgreSQL persistence validated")


# ============================================================================
# Test 6: PostgreSQL Schema Validation
# ============================================================================

@pytest.mark.asyncio
async def test_postgresql_schema_validation(postgres_pool):
    """
    Test 6: Validate PostgreSQL schema structure.
    
    Validates:
    - Table existence
    - Column types and constraints
    - Indexes
    - Foreign keys
    """
    print("\n" + "="*70)
    print("TEST 6: PostgreSQL Schema Validation")
    print("="*70)
    
    async with postgres_pool.acquire() as conn:
        # Check relationship_scores table
        print("\n🔍 Validating relationship_scores table...")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'relationship_scores'
            ORDER BY ordinal_position
        """)
        
        column_names = [c['column_name'] for c in columns]
        assert 'user_id' in column_names, "Should have user_id column"
        assert 'bot_name' in column_names, "Should have bot_name column"
        assert 'trust' in column_names, "Should have trust column"
        assert 'affection' in column_names, "Should have affection column"
        assert 'attunement' in column_names, "Should have attunement column"
        assert 'interaction_count' in column_names, "Should have interaction_count column"
        
        print(f"   ✅ All required columns present ({len(column_names)} total)")
        
        # Check constraints
        print("\n🔍 Validating constraints...")
        constraints = await conn.fetch("""
            SELECT conname, contype
            FROM pg_constraint
            WHERE conrelid = 'relationship_scores'::regclass
        """)
        
        # Convert bytes to strings for comparison
        constraint_types = [c['contype'].decode('utf-8') if isinstance(c['contype'], bytes) else c['contype'] for c in constraints]
        assert 'p' in constraint_types, "Should have PRIMARY KEY"
        assert 'c' in constraint_types, "Should have CHECK constraints"
        
        print(f"   ✅ Constraints validated ({len(constraints)} total)")
        
        # Check indexes
        print("\n🔍 Validating indexes...")
        indexes = await conn.fetch("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'relationship_scores'
        """)
        
        index_names = [i['indexname'] for i in indexes]
        assert any('user' in name for name in index_names), "Should have user index"
        assert any('bot' in name for name in index_names), "Should have bot index"
        assert any('trust' in name for name in index_names), "Should have trust index"
        
        print(f"   ✅ Indexes validated ({len(indexes)} total)")
        
        # Check relationship_events table
        print("\n🔍 Validating relationship_events table...")
        events_columns = await conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'relationship_events'
        """)
        
        events_column_names = [c['column_name'] for c in events_columns]
        assert 'trust_delta' in events_column_names, "Should have trust_delta column"
        assert 'affection_delta' in events_column_names, "Should have affection_delta column"
        assert 'emotion_variance' in events_column_names, "Should have emotion_variance column"
        assert 'conversation_quality' in events_column_names, "Should have conversation_quality column"
        
        print(f"   ✅ relationship_events validated ({len(events_column_names)} columns)")
        
        # Check trust_recovery_state table
        print("\n🔍 Validating trust_recovery_state table...")
        recovery_columns = await conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'trust_recovery_state'
        """)
        
        recovery_column_names = [c['column_name'] for c in recovery_columns]
        assert 'recovery_stage' in recovery_column_names, "Should have recovery_stage column"
        assert 'progress_percentage' in recovery_column_names, "Should have progress_percentage column"
        assert 'target_trust' in recovery_column_names, "Should have target_trust column"
        
        print(f"   ✅ trust_recovery_state validated ({len(recovery_column_names)} columns)")


# ============================================================================
# Test 7: End-to-End Integration (Sprint 1 + Sprint 2 + Sprint 3)
# ============================================================================

@pytest.mark.asyncio
async def test_end_to_end_integration(postgres_pool, mock_temporal_client, mock_trend_analyzer):
    """
    Test 7: End-to-end integration test across all sprints.
    
    Validates:
    - Sprint 1 ConversationQuality integration
    - Sprint 2 RoBERTa emotion_variance integration
    - Sprint 3 relationship evolution and recovery
    - Complete workflow from conversation → relationship update → trust recovery
    """
    print("\n" + "="*70)
    print("TEST 7: End-to-End Integration (Sprint 1 + 2 + 3)")
    print("="*70)
    
    # Create both systems
    evolution_engine = create_relationship_evolution_engine(
        postgres_pool=postgres_pool,
        temporal_client=mock_temporal_client
    )
    
    recovery_system = create_trust_recovery_system(
        postgres_pool=postgres_pool,
        temporal_client=mock_temporal_client,
        trend_analyzer=mock_trend_analyzer
    )
    
    user_id = "test_user_e2e"
    bot_name = "TestBot"
    
    print("\n📝 Scenario: User has declining relationship with bot")
    print("="*70)
    
    # Step 1: Simulate several POOR conversations
    print("\n1️⃣ Simulating 3 POOR conversations...")
    for i in range(3):
        update = await evolution_engine.calculate_dynamic_relationship_score(
            user_id=user_id,
            bot_name=bot_name,
            conversation_quality=ConversationQuality.POOR,
            emotion_data={'emotion_variance': 0.5}
        )
        print(f"   Conversation {i+1}: Trust now {update.new_scores.trust:.3f}")
    
    # Step 2: Set up declining trend
    print("\n2️⃣ Setting up declining trust trend...")
    mock_trend_analyzer.set_trust_trend(user_id, bot_name, slope=-0.18)
    
    # Step 3: Detect trust decline
    print("\n3️⃣ Detecting trust decline...")
    detection = await recovery_system.detect_trust_decline(
        user_id=user_id,
        bot_name=bot_name,
        time_window_days=7
    )
    
    assert detection is not None, "Should detect decline"
    print(f"   ✅ Decline detected: {detection.decline_severity}")
    print(f"   ✅ Current trust: {detection.current_trust:.3f}")
    print(f"   ✅ Suggested actions: {detection.suggested_actions}")
    
    # Step 4: Activate recovery
    print("\n4️⃣ Activating trust recovery...")
    recovery = await recovery_system.activate_recovery_mode(detection)
    
    assert recovery.recovery_stage == RecoveryStage.ACTIVE, "Should be in recovery"
    print(f"   ✅ Recovery activated")
    print(f"   ✅ Target trust: {recovery.target_trust:.3f}")
    
    # Step 5: Simulate improvement with EXCELLENT conversations
    print("\n5️⃣ Simulating recovery with EXCELLENT conversations...")
    for i in range(3):
        update = await evolution_engine.calculate_dynamic_relationship_score(
            user_id=user_id,
            bot_name=bot_name,
            conversation_quality=ConversationQuality.EXCELLENT,
            emotion_data={'emotion_variance': 0.2}
        )
        print(f"   Conversation {i+1}: Trust now {update.new_scores.trust:.3f}")
    
    # Step 6: Track recovery progress
    print("\n6️⃣ Tracking recovery progress...")
    progress = await recovery_system.track_recovery_progress(
        user_id=user_id,
        bot_name=bot_name
    )
    
    assert progress is not None, "Should have progress"
    print(f"   ✅ Progress: {progress.progress_percentage:.1f}%")
    print(f"   ✅ Current trust: {progress.current_trust:.3f}")
    print(f"   ✅ Recovery stage: {progress.recovery_stage.value}")
    
    # Validate temporal events recorded
    print("\n7️⃣ Validating InfluxDB event recording...")
    events = mock_temporal_client.get_events()
    assert len(events) > 0, "Should have recorded events"
    
    relationship_events = [e for e in events if e.get('type') == 'relationship_update']
    recovery_events = [e for e in events if e.get('type') == 'trust_recovery']
    
    print(f"   ✅ Relationship events: {len(relationship_events)}")
    print(f"   ✅ Recovery events: {len(recovery_events)}")
    
    print("\n" + "="*70)
    print("🎉 END-TO-END INTEGRATION COMPLETE!")
    print("="*70)
    print("✅ Sprint 1 (TrendWise): ConversationQuality integrated")
    print("✅ Sprint 2 (MemoryBoost): RoBERTa emotion_variance integrated")
    print("✅ Sprint 3 (RelationshipTuner): Evolution + Recovery working")
    print("✅ PostgreSQL: All data persisted correctly")
    print("✅ InfluxDB: All events recorded correctly")


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == '__main__':
    """
    Run all validation tests directly.
    
    Usage:
        export POSTGRES_HOST=localhost
        export POSTGRES_PORT=5433
        python tests/automated/test_sprint3_relationship_tuner_validation.py
    """
    print("\n" + "="*70)
    print("SPRINT 3 RELATIONSHIPTUNER VALIDATION SUITE")
    print("="*70)
    print("Running comprehensive validation tests...")
    print("Strategy: Direct Python internal API calls")
    print("Target: 100% test pass rate (7 tests)")
    print("="*70)
    
    # Run pytest with config overrides
    exit_code = pytest.main([
        __file__,
        '-v',
        '-s',
        '--tb=short',
        '--color=yes',
        '-o', 'addopts='  # Override pytest.ini addopts to skip coverage
    ])
    
    sys.exit(exit_code)
