"""
Test Suite: Trust Recovery System Monitoring
Purpose: Validate telemetry tracking for trust recovery evaluation

Enhancement #6: Trust Recovery Monitoring
- Track detect_trust_decline invocations
- Track actual decline detections
- Track activate_recovery_mode invocations
- Track successful recovery activations
- Monitor system usage for production evaluation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.relationships.trust_recovery import (
    TrustRecoverySystem,
    TrustDeclineDetection,
    TrustDeclineReason,
    RecoveryProgress,
    RecoveryStage
)


@pytest.fixture
async def trust_recovery_system():
    """Create TrustRecoverySystem with mocked dependencies"""
    
    # Mock PostgreSQL pool with proper async context manager
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.fetch = AsyncMock(return_value=[])
    
    # Setup acquire() to return an async context manager
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire
    
    # Mock InfluxDB temporal client
    mock_temporal_client = AsyncMock()
    mock_temporal_client.write_data_point = AsyncMock()
    mock_temporal_client.query_time_series = AsyncMock(return_value=[])
    
    # Create system
    system = TrustRecoverySystem(
        postgres_pool=mock_pool,
        temporal_client=mock_temporal_client,
        trend_analyzer=None  # Optional dependency
    )
    
    return system


class TestTrustRecoveryInitializationTelemetry:
    """Test telemetry initialization in TrustRecoverySystem"""
    
    @pytest.mark.asyncio
    async def test_initialization_telemetry(self, trust_recovery_system):
        """Verify telemetry counters initialized on system creation"""
        
        # Verify telemetry dictionary exists
        assert hasattr(trust_recovery_system, '_telemetry')
        assert isinstance(trust_recovery_system._telemetry, dict)
        
        # Verify all counters initialized
        assert 'detect_trust_decline_count' in trust_recovery_system._telemetry
        assert 'activate_recovery_count' in trust_recovery_system._telemetry
        assert 'assess_recovery_progress_count' in trust_recovery_system._telemetry
        assert 'declines_detected' in trust_recovery_system._telemetry
        assert 'recoveries_activated' in trust_recovery_system._telemetry
        assert 'initialization_time' in trust_recovery_system._telemetry
        
        # Verify initial values
        assert trust_recovery_system._telemetry['detect_trust_decline_count'] == 0
        assert trust_recovery_system._telemetry['activate_recovery_count'] == 0
        assert trust_recovery_system._telemetry['assess_recovery_progress_count'] == 0
        assert trust_recovery_system._telemetry['declines_detected'] == 0
        assert trust_recovery_system._telemetry['recoveries_activated'] == 0
        assert isinstance(trust_recovery_system._telemetry['initialization_time'], datetime)


class TestDetectTrustDeclineTelemetry:
    """Test telemetry tracking for trust decline detection"""
    
    @pytest.mark.asyncio
    async def test_detect_trust_decline_invocation_tracking(self, trust_recovery_system):
        """Verify detect_trust_decline_count increments on method call"""
        
        user_id = "test_user_123"
        bot_name = "elena"
        
        # Mock temporal_client to return empty trust history (no decline)
        trust_recovery_system.temporal_client.query_time_series = AsyncMock(return_value=[])
        
        # Call detect_trust_decline
        result = await trust_recovery_system.detect_trust_decline(user_id, bot_name)
        
        # Verify invocation counter incremented
        assert trust_recovery_system._telemetry['detect_trust_decline_count'] == 1
        
        # Call again to verify accumulation
        result = await trust_recovery_system.detect_trust_decline(user_id, bot_name)
        assert trust_recovery_system._telemetry['detect_trust_decline_count'] == 2
        
        # Verify declines_detected remains 0 (no actual declines)
        assert trust_recovery_system._telemetry['declines_detected'] == 0
    
    @pytest.mark.asyncio
    async def test_decline_detection_counter(self, trust_recovery_system):
        """Verify declines_detected increments when decline found"""
        
        user_id = "test_user_456"
        bot_name = "marcus"
        
        # Mock trust history showing decline (high trust → low trust)
        now = datetime.utcnow()
        mock_trust_history = [
            {'time': now - timedelta(days=7), 'trust_score': 85.0},
            {'time': now - timedelta(days=6), 'trust_score': 82.0},
            {'time': now - timedelta(days=5), 'trust_score': 78.0},
            {'time': now - timedelta(days=4), 'trust_score': 72.0},
            {'time': now - timedelta(days=3), 'trust_score': 65.0},
            {'time': now - timedelta(days=2), 'trust_score': 58.0},
            {'time': now - timedelta(days=1), 'trust_score': 50.0},
            {'time': now, 'trust_score': 45.0},  # Below threshold (50)
        ]
        trust_recovery_system.temporal_client.query_time_series = AsyncMock(return_value=mock_trust_history)
        
        # Call detect_trust_decline
        result = await trust_recovery_system.detect_trust_decline(user_id, bot_name)
        
        # Verify decline detected
        assert result is not None
        assert isinstance(result, TrustDeclineDetection)
        
        # Verify both counters incremented
        assert trust_recovery_system._telemetry['detect_trust_decline_count'] == 1
        assert trust_recovery_system._telemetry['declines_detected'] == 1


class TestActivateRecoveryModeTelemetry:
    """Test telemetry tracking for recovery mode activation"""
    
    @pytest.mark.asyncio
    async def test_activate_recovery_invocation_tracking(self, trust_recovery_system):
        """Verify activate_recovery_count increments on method call"""
        
        user_id = "test_user_789"
        bot_name = "jake"
        
        # Create mock decline detection (matching actual schema)
        detection = TrustDeclineDetection(
            user_id=user_id,
            bot_name=bot_name,
            current_trust=45.0,
            trust_trend_slope=-4.3,  # Changed from decline_rate
            decline_severity="severe",
            decline_reason=TrustDeclineReason.CONVERSATION_QUALITY,  # Changed from primary_reason
            needs_recovery=True,
            suggested_actions=["increase_empathy", "improve_context"],
            detection_timestamp=datetime.utcnow()
        )
        
        # Mock database operations
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)  # No existing recovery
        mock_conn.fetchval = AsyncMock(return_value=1)  # Insert success
        trust_recovery_system.postgres_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        
        # Mock _record_recovery_event
        trust_recovery_system._record_recovery_event = AsyncMock()
        
        # Call activate_recovery_mode
        result = await trust_recovery_system.activate_recovery_mode(detection)
        
        # Verify invocation counter incremented
        assert trust_recovery_system._telemetry['activate_recovery_count'] == 1
        
        # Verify recovery activated counter incremented
        assert trust_recovery_system._telemetry['recoveries_activated'] == 1
        
        # Verify result
        assert isinstance(result, RecoveryProgress)
    
    @pytest.mark.asyncio
    async def test_recoveries_activated_accumulation(self, trust_recovery_system):
        """Verify recoveries_activated increments for each successful activation"""
        
        # Create multiple mock decline detections (matching actual schema)
        detections = [
            TrustDeclineDetection(
                user_id=f"user_{i}",
                bot_name="elena",
                current_trust=40.0 + i,
                trust_trend_slope=-3.5,
                decline_severity="moderate",
                decline_reason=TrustDeclineReason.CONVERSATION_QUALITY,
                needs_recovery=True,
                suggested_actions=["improve_responses"],
                detection_timestamp=datetime.utcnow()
            )
            for i in range(3)
        ]
        
        # Mock database operations
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_conn.fetchval = AsyncMock(return_value=1)
        trust_recovery_system.postgres_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        trust_recovery_system._record_recovery_event = AsyncMock()
        
        # Activate recovery for each detection
        for detection in detections:
            await trust_recovery_system.activate_recovery_mode(detection)
        
        # Verify counters accumulated
        assert trust_recovery_system._telemetry['activate_recovery_count'] == 3
        assert trust_recovery_system._telemetry['recoveries_activated'] == 3


class TestTelemetryAccumulation:
    """Test telemetry accumulation across multiple operations"""
    
    @pytest.mark.asyncio
    async def test_combined_telemetry_accumulation(self, trust_recovery_system):
        """Verify telemetry accumulates correctly across decline detection and recovery activation"""
        
        user_id = "test_user_combined"
        bot_name = "dream"
        
        # Setup: Mock trust history showing decline
        now = datetime.utcnow()
        mock_trust_history = [
            {'time': now - timedelta(days=7), 'trust_score': 80.0},
            {'time': now, 'trust_score': 40.0},
        ]
        trust_recovery_system.temporal_client.query_time_series = AsyncMock(return_value=mock_trust_history)
        
        # Mock database operations for recovery activation
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_conn.fetchval = AsyncMock(return_value=1)
        trust_recovery_system.postgres_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        trust_recovery_system._record_recovery_event = AsyncMock()
        
        # Step 1: Detect decline
        detection = await trust_recovery_system.detect_trust_decline(user_id, bot_name)
        
        # Verify detection telemetry
        assert trust_recovery_system._telemetry['detect_trust_decline_count'] == 1
        assert trust_recovery_system._telemetry['declines_detected'] == 1
        assert trust_recovery_system._telemetry['recoveries_activated'] == 0
        
        # Step 2: Activate recovery
        recovery = await trust_recovery_system.activate_recovery_mode(detection)
        
        # Verify combined telemetry
        assert trust_recovery_system._telemetry['detect_trust_decline_count'] == 1
        assert trust_recovery_system._telemetry['declines_detected'] == 1
        assert trust_recovery_system._telemetry['activate_recovery_count'] == 1
        assert trust_recovery_system._telemetry['recoveries_activated'] == 1
        
        # Step 3: Detect another decline (no actual decline this time)
        trust_recovery_system.temporal_client.query_time_series = AsyncMock(return_value=[])
        result = await trust_recovery_system.detect_trust_decline(user_id, bot_name)
        
        # Verify telemetry: invocation incremented, but not detection
        assert trust_recovery_system._telemetry['detect_trust_decline_count'] == 2
        assert trust_recovery_system._telemetry['declines_detected'] == 1  # Still 1


class TestMonitoringSummary:
    """Test monitoring summary for trust recovery evaluation"""
    
    @pytest.mark.asyncio
    async def test_monitoring_summary(self, trust_recovery_system):
        """Verify telemetry provides complete summary for system evaluation"""
        
        # Simulate realistic usage scenario
        
        # 1. Multiple decline detection checks (5 checks, 2 actual declines)
        for i in range(5):
            if i in [1, 3]:  # Simulate declines on checks 1 and 3
                now = datetime.utcnow()
                mock_trust_history = [
                    {'time': now - timedelta(days=7), 'trust_score': 80.0},
                    {'time': now, 'trust_score': 40.0},
                ]
                trust_recovery_system.temporal_client.query_time_series = AsyncMock(return_value=mock_trust_history)
            else:
                trust_recovery_system.temporal_client.query_time_series = AsyncMock(return_value=[])
            
            await trust_recovery_system.detect_trust_decline(f"user_{i}", "elena")
        
        # 2. Activate recovery for the detected declines (1 successful, 1 skipped)
        detection = TrustDeclineDetection(
            user_id="user_1",
            bot_name="elena",
            current_trust=40.0,
            trust_trend_slope=-5.7,
            decline_severity="severe",
            decline_reason=TrustDeclineReason.EMOTIONAL_MISMATCH,
            needs_recovery=True,
            suggested_actions=["enhance_empathy", "improve_context"],
            detection_timestamp=datetime.utcnow()
        )
        
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_conn.fetchval = AsyncMock(return_value=1)
        trust_recovery_system.postgres_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        trust_recovery_system._record_recovery_event = AsyncMock()
        
        await trust_recovery_system.activate_recovery_mode(detection)
        
        # Verify comprehensive telemetry summary
        telemetry = trust_recovery_system._telemetry
        
        # Detection metrics
        assert telemetry['detect_trust_decline_count'] == 5  # Total checks
        assert telemetry['declines_detected'] == 2  # Actual declines found
        
        # Recovery metrics
        assert telemetry['activate_recovery_count'] == 1  # Recovery attempts
        assert telemetry['recoveries_activated'] == 1  # Successful activations
        
        # Metadata
        assert isinstance(telemetry['initialization_time'], datetime)
        
        # Calculate decline detection rate (for evaluation)
        detection_rate = telemetry['declines_detected'] / telemetry['detect_trust_decline_count']
        assert detection_rate == 0.4  # 40% of checks found declines
        
        # Calculate recovery activation rate
        activation_rate = telemetry['recoveries_activated'] / telemetry['declines_detected']
        assert activation_rate == 0.5  # 50% of declines triggered recovery
        
        print("\n✅ Trust Recovery Monitoring Summary:")
        print(f"   - Trust decline checks: {telemetry['detect_trust_decline_count']}")
        print(f"   - Declines detected: {telemetry['declines_detected']} ({detection_rate:.1%})")
        print(f"   - Recovery activations: {telemetry['activate_recovery_count']}")
        print(f"   - Successful recoveries: {telemetry['recoveries_activated']} ({activation_rate:.1%})")
        print(f"   - System uptime: {datetime.utcnow() - telemetry['initialization_time']}")
