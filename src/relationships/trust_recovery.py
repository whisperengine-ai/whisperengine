"""
Trust Recovery System - Relationship Intelligence Framework

Intelligent trust repair and relationship recovery using trend analysis.
Automatically detects trust decline and provides sophisticated recovery strategies
that maintain character authenticity while rebuilding user confidence.

Key Features:
- Detect trust decline using TrendWise trend analysis
- Activate recovery mode when trust drops below thresholds
- Track recovery progress over time
- Integration with relationship evolution for trust repair

MVP Approach:
- Simple threshold-based detection (trust_slope < -0.1)
- Binary recovery mode (active/inactive)
- Use existing InfluxDB trend_analyzer for pattern detection
- No complex multi-stage recovery yet (can enhance later)
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RecoveryStage(Enum):
    """Trust recovery stages"""
    NOT_NEEDED = "not_needed"        # Trust is healthy
    MONITORING = "monitoring"        # Slight decline detected, watching
    ACTIVE = "active"                # Active recovery needed
    RECOVERING = "recovering"        # Recovery in progress
    RECOVERED = "recovered"          # Trust restored


class TrustDeclineReason(Enum):
    """Reasons for trust decline"""
    CONVERSATION_QUALITY = "conversation_quality"  # Poor conversations
    CONSISTENCY = "consistency"                    # Inconsistent behavior
    MISUNDERSTANDING = "misunderstanding"          # Communication breakdown
    EMOTIONAL_MISMATCH = "emotional_mismatch"      # Emotion handling issues
    UNKNOWN = "unknown"                            # Can't determine cause


@dataclass
class TrustDeclineDetection:
    """Result of trust decline detection"""
    user_id: str
    bot_name: str
    current_trust: float
    trust_trend_slope: float      # From InfluxDB trend analysis
    decline_severity: str         # "minor", "moderate", "severe"
    decline_reason: TrustDeclineReason
    needs_recovery: bool
    suggested_actions: List[str]
    detection_timestamp: datetime


@dataclass
class RecoveryProgress:
    """Track trust recovery progress"""
    user_id: str
    bot_name: str
    recovery_stage: RecoveryStage
    initial_trust: float          # Trust when recovery started
    current_trust: float
    target_trust: float           # Goal to reach
    progress_percentage: float    # 0-100
    recovery_actions_taken: List[str]
    started_at: datetime
    last_updated: datetime
    estimated_completion: Optional[datetime] = None


class TrustRecoverySystem:
    """
    Trust recovery system that detects decline and manages recovery.
    
    Uses TrendWise trend analysis to detect when trust is declining,
    then activates recovery strategies to repair the relationship.
    """
    
    def __init__(
        self,
        postgres_pool=None,
        temporal_client=None,
        trend_analyzer=None
    ):
        """
        Initialize trust recovery system.
        
        Args:
            postgres_pool: PostgreSQL connection pool
            temporal_client: InfluxDB temporal client
            trend_analyzer: TrendWise analyzer for trend detection
        """
        self.postgres_pool = postgres_pool
        self.temporal_client = temporal_client
        self.trend_analyzer = trend_analyzer
        self.logger = logger
        
        # Detection thresholds
        self.thresholds = {
            'minor_decline': -0.05,      # Trust slope < -0.05 = minor issue
            'moderate_decline': -0.10,   # Trust slope < -0.10 = moderate issue
            'severe_decline': -0.20,     # Trust slope < -0.20 = severe issue
            'critical_trust': 0.30,      # Trust < 0.30 = critical situation
            'low_trust': 0.40            # Trust < 0.40 = concerning
        }
        
        # Recovery targets
        self.recovery_targets = {
            'minor': 0.10,    # Aim to recover 0.10 trust for minor declines
            'moderate': 0.15, # Aim to recover 0.15 trust for moderate declines
            'severe': 0.20    # Aim to recover 0.20 trust for severe declines
        }
    
    async def detect_trust_decline(
        self,
        user_id: str,
        bot_name: str,
        time_window_days: int = 7
    ) -> Optional[TrustDeclineDetection]:
        """
        Detect if trust is declining for a user-bot relationship.
        
        Uses TrendWise trend analysis to identify declining patterns.
        
        Args:
            user_id: User identifier
            bot_name: Bot name
            time_window_days: Days of history to analyze (default 7)
            
        Returns:
            TrustDeclineDetection if decline detected, None if trust is healthy
        """
        try:
            # Get current relationship scores
            current_trust = await self._get_current_trust(user_id, bot_name)
            
            # Get trust trend from InfluxDB (TrendWise)
            if self.trend_analyzer:
                relationship_trend = await self.trend_analyzer.get_relationship_trends(
                    user_id=user_id,
                    bot_name=bot_name,
                    time_window_days=time_window_days
                )
                
                if relationship_trend:
                    trust_trend = relationship_trend.trust_trend
                    trust_slope = trust_trend.slope
                else:
                    # No trend data available
                    return None
            else:
                # No trend analyzer - can't detect decline
                self.logger.warning("No trend analyzer available for trust decline detection")
                return None
            
            # Determine decline severity
            severity = self._determine_decline_severity(trust_slope, current_trust)
            
            if severity == "none":
                # No decline detected
                return None
            
            # Determine decline reason
            reason = await self._determine_decline_reason(
                user_id, 
                bot_name, 
                trust_slope,
                time_window_days
            )
            
            # Generate suggested recovery actions
            suggested_actions = self._generate_recovery_suggestions(
                severity,
                reason,
                current_trust
            )
            
            detection = TrustDeclineDetection(
                user_id=user_id,
                bot_name=bot_name,
                current_trust=current_trust,
                trust_trend_slope=trust_slope,
                decline_severity=severity,
                decline_reason=reason,
                needs_recovery=True,
                suggested_actions=suggested_actions,
                detection_timestamp=datetime.now()
            )
            
            self.logger.info(
                "⚠️ Trust decline detected for %s/%s: trust=%.2f, slope=%.3f, severity=%s",
                bot_name, user_id, current_trust, trust_slope, severity
            )
            
            return detection
            
        except Exception as e:
            self.logger.error("Error detecting trust decline: %s", e)
            return None
    
    async def activate_recovery_mode(
        self,
        detection: TrustDeclineDetection
    ) -> RecoveryProgress:
        """
        Activate trust recovery mode for a declining relationship.
        
        Args:
            detection: Trust decline detection result
            
        Returns:
            RecoveryProgress tracking object
        """
        try:
            user_id = detection.user_id
            bot_name = detection.bot_name
            
            # Determine recovery target based on severity
            if detection.decline_severity == "severe":
                target_increase = self.recovery_targets['severe']
            elif detection.decline_severity == "moderate":
                target_increase = self.recovery_targets['moderate']
            else:
                target_increase = self.recovery_targets['minor']
            
            target_trust = min(1.0, detection.current_trust + target_increase)
            
            # Create recovery progress tracker
            recovery = RecoveryProgress(
                user_id=user_id,
                bot_name=bot_name,
                recovery_stage=RecoveryStage.ACTIVE,
                initial_trust=detection.current_trust,
                current_trust=detection.current_trust,
                target_trust=target_trust,
                progress_percentage=0.0,
                recovery_actions_taken=detection.suggested_actions.copy(),
                started_at=datetime.now(),
                last_updated=datetime.now(),
                estimated_completion=None
            )
            
            # Store recovery state in PostgreSQL
            await self._store_recovery_state(recovery)
            
            # Record recovery activation to InfluxDB
            await self._record_recovery_event(
                user_id,
                bot_name,
                "recovery_activated",
                detection.decline_severity,
                detection.current_trust
            )
            
            self.logger.info(
                "🔧 Recovery mode activated for %s/%s: target_trust=%.2f (current=%.2f)",
                bot_name, user_id, target_trust, detection.current_trust
            )
            
            return recovery
            
        except Exception as e:
            self.logger.error("Error activating recovery mode: %s", e)
            raise
    
    async def track_recovery_progress(
        self,
        user_id: str,
        bot_name: str
    ) -> Optional[RecoveryProgress]:
        """
        Track progress of active trust recovery.
        
        Args:
            user_id: User identifier
            bot_name: Bot name
            
        Returns:
            RecoveryProgress if recovery is active, None otherwise
        """
        try:
            # Get recovery state from PostgreSQL
            recovery = await self._get_recovery_state(user_id, bot_name)
            
            if not recovery or recovery.recovery_stage not in [
                RecoveryStage.ACTIVE, 
                RecoveryStage.RECOVERING
            ]:
                return None
            
            # Get current trust level
            current_trust = await self._get_current_trust(user_id, bot_name)
            
            # Calculate progress
            trust_gained = current_trust - recovery.initial_trust
            trust_needed = recovery.target_trust - recovery.initial_trust
            
            if trust_needed > 0:
                progress_pct = min(100.0, (trust_gained / trust_needed) * 100)
            else:
                progress_pct = 100.0
            
            # Update recovery state
            recovery.current_trust = current_trust
            recovery.progress_percentage = progress_pct
            recovery.last_updated = datetime.now()
            
            # Update recovery stage based on progress
            if progress_pct >= 100.0:
                recovery.recovery_stage = RecoveryStage.RECOVERED
                self.logger.info(
                    "✅ Trust recovery complete for %s/%s: %.2f -> %.2f",
                    bot_name, user_id, recovery.initial_trust, current_trust
                )
            elif progress_pct >= 30.0:
                recovery.recovery_stage = RecoveryStage.RECOVERING
            
            # Store updated state
            await self._store_recovery_state(recovery)
            
            # Record progress event
            await self._record_recovery_event(
                user_id,
                bot_name,
                "recovery_progress",
                recovery.recovery_stage.value,
                current_trust,
                progress_pct
            )
            
            return recovery
            
        except Exception as e:
            self.logger.error("Error tracking recovery progress: %s", e)
            return None
    
    def _determine_decline_severity(
        self,
        trust_slope: float,
        current_trust: float
    ) -> str:
        """
        Determine severity of trust decline.
        
        Returns: "none", "minor", "moderate", or "severe"
        """
        # Check if trust is critically low
        if current_trust < self.thresholds['critical_trust']:
            return "severe"
        
        # Check slope severity
        if trust_slope <= self.thresholds['severe_decline']:
            return "severe"
        elif trust_slope <= self.thresholds['moderate_decline']:
            return "moderate"
        elif trust_slope <= self.thresholds['minor_decline']:
            return "minor"
        else:
            return "none"
    
    async def _determine_decline_reason(
        self,
        user_id: str,
        bot_name: str,
        trust_slope: float,
        time_window_days: int
    ) -> TrustDeclineReason:
        """
        Determine most likely reason for trust decline.
        
        For MVP, uses simple heuristics. Future enhancement:
        could use ML or more sophisticated pattern analysis.
        """
        # For MVP, return CONVERSATION_QUALITY as default
        # Future enhancement: analyze conversation outcomes, emotion patterns, etc.
        return TrustDeclineReason.CONVERSATION_QUALITY
    
    def _generate_recovery_suggestions(
        self,
        severity: str,
        reason: TrustDeclineReason,
        current_trust: float
    ) -> List[str]:
        """
        Generate suggested recovery actions based on decline analysis.
        """
        suggestions = []
        
        # Base suggestions for all cases
        suggestions.append("increase_response_quality")
        suggestions.append("show_empathy")
        
        # Severity-specific suggestions
        if severity == "severe":
            suggestions.extend([
                "acknowledge_past_issues",
                "proactive_check_in",
                "extra_validation"
            ])
        elif severity == "moderate":
            suggestions.extend([
                "improve_understanding",
                "validate_emotions"
            ])
        
        # Reason-specific suggestions
        if reason == TrustDeclineReason.CONVERSATION_QUALITY:
            suggestions.append("enhance_conversation_engagement")
        elif reason == TrustDeclineReason.EMOTIONAL_MISMATCH:
            suggestions.append("adjust_emotional_tone")
        elif reason == TrustDeclineReason.MISUNDERSTANDING:
            suggestions.append("clarify_communications")
        
        return suggestions
    
    async def _get_current_trust(self, user_id: str, bot_name: str) -> float:
        """Get current trust score from PostgreSQL."""
        if not self.postgres_pool:
            return 0.5  # Default
        
        try:
            async with self.postgres_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT trust
                    FROM relationship_scores
                    WHERE user_id = $1 AND bot_name = $2
                """, user_id, bot_name)
                
                return float(row['trust']) if row else 0.5
                
        except Exception as e:
            self.logger.error("Error fetching trust score: %s", e)
            return 0.5
    
    async def _get_recovery_state(
        self,
        user_id: str,
        bot_name: str
    ) -> Optional[RecoveryProgress]:
        """Get recovery state from PostgreSQL."""
        if not self.postgres_pool:
            return None
        
        try:
            async with self.postgres_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT recovery_stage, initial_trust, current_trust, target_trust,
                           progress_percentage, recovery_actions_taken, started_at,
                           last_updated, estimated_completion
                    FROM trust_recovery_state
                    WHERE user_id = $1 AND bot_name = $2
                    AND recovery_stage IN ('active', 'recovering')
                    ORDER BY started_at DESC
                    LIMIT 1
                """, user_id, bot_name)
                
                if row:
                    return RecoveryProgress(
                        user_id=user_id,
                        bot_name=bot_name,
                        recovery_stage=RecoveryStage(row['recovery_stage']),
                        initial_trust=float(row['initial_trust']),
                        current_trust=float(row['current_trust']),
                        target_trust=float(row['target_trust']),
                        progress_percentage=float(row['progress_percentage']),
                        recovery_actions_taken=row['recovery_actions_taken'] or [],
                        started_at=row['started_at'],
                        last_updated=row['last_updated'],
                        estimated_completion=row['estimated_completion']
                    )
                
                return None
                
        except Exception as e:
            self.logger.error("Error fetching recovery state: %s", e)
            return None
    
    async def _store_recovery_state(self, recovery: RecoveryProgress) -> None:
        """Store recovery state in PostgreSQL."""
        if not self.postgres_pool:
            self.logger.warning("No PostgreSQL pool - recovery state not persisted")
            return
        
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO trust_recovery_state
                        (user_id, bot_name, recovery_stage, initial_trust,
                         current_trust, target_trust, progress_percentage,
                         recovery_actions_taken, started_at, last_updated,
                         estimated_completion)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (user_id, bot_name, started_at)
                    DO UPDATE SET
                        recovery_stage = EXCLUDED.recovery_stage,
                        current_trust = EXCLUDED.current_trust,
                        progress_percentage = EXCLUDED.progress_percentage,
                        last_updated = EXCLUDED.last_updated
                """,
                recovery.user_id, recovery.bot_name, recovery.recovery_stage.value,
                recovery.initial_trust, recovery.current_trust, recovery.target_trust,
                recovery.progress_percentage, recovery.recovery_actions_taken,
                recovery.started_at, recovery.last_updated, recovery.estimated_completion
                )
                
        except Exception as e:
            self.logger.error("Error storing recovery state: %s", e)
            raise
    
    async def _record_recovery_event(
        self,
        user_id: str,
        bot_name: str,
        event_type: str,
        severity_or_stage: str,
        trust_value: float,
        progress: Optional[float] = None
    ) -> None:
        """Record recovery event to InfluxDB."""
        if not self.temporal_client:
            return
        
        try:
            await self.temporal_client.store_trust_recovery_event(
                user_id=user_id,
                bot_name=bot_name,
                event_type=event_type,
                severity_or_stage=severity_or_stage,
                trust_value=trust_value,
                progress=progress,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error("Error recording recovery event: %s", e)
            # Non-fatal


# Factory function
def create_trust_recovery_system(
    postgres_pool=None,
    temporal_client=None,
    trend_analyzer=None
) -> TrustRecoverySystem:
    """
    Factory function to create TrustRecoverySystem instance.
    
    Args:
        postgres_pool: PostgreSQL connection pool
        temporal_client: InfluxDB temporal client
        trend_analyzer: TrendWise trend analyzer
        
    Returns:
        Configured TrustRecoverySystem instance
    """
    return TrustRecoverySystem(
        postgres_pool=postgres_pool,
        temporal_client=temporal_client,
        trend_analyzer=trend_analyzer
    )
