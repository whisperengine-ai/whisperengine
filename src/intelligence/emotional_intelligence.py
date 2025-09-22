"""
Phase 2 Predictive Emotional Intelligence System
===============================================

Integrates emotion prediction, mood detection, and proactive support
into a comprehensive emotional intelligence framework.

Phase 2: Complete Implementation
"""

import json
import logging
import os
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, cast

# Try to import spaCy-dependent components
try:
    from .emotion_predictor import EmotionalPrediction, EmotionPredictor
    EMOTION_PREDICTOR_AVAILABLE = True
except ImportError:
    EMOTION_PREDICTOR_AVAILABLE = False
    EmotionalPrediction = None
    EmotionPredictor = None

try:
    from .mood_detector import (
        EmotionalAlert,
        MoodAssessment,
        MoodCategory,
        MoodDetector,
        StressAssessment,
        StressLevel,
    )
    MOOD_DETECTOR_AVAILABLE = True
except ImportError:
    MOOD_DETECTOR_AVAILABLE = False
    EmotionalAlert = None
    MoodAssessment = None
    MoodCategory = None
    MoodDetector = None
    StressAssessment = None
    StressLevel = None
from .proactive_support import (
    ProactiveSupport,
    SupportIntervention,
    SupportOutcome,
    SupportStrategy,
)

# Database imports for persistence
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)

# Metrics (optional)
try:
    from src.metrics import metrics_collector as metrics
except (ImportError, ModuleNotFoundError):  # Metrics are optional; fail safe
    metrics = None


class PhaseStatus(Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    MONITORING = "monitoring"
    INTERVENTION = "intervention"
    CRISIS = "crisis"


@dataclass
class EmotionalIntelligenceAssessment:
    """Comprehensive emotional intelligence assessment"""

    user_id: str
    assessment_timestamp: datetime

    # Core assessments
    mood_assessment: MoodAssessment
    stress_assessment: StressAssessment
    emotional_prediction: EmotionalPrediction
    emotional_alerts: list[EmotionalAlert]

    # Support recommendations
    support_needs: dict[str, Any]
    recommended_intervention: SupportIntervention | None

    # System status
    phase_status: PhaseStatus
    confidence_score: float
    next_assessment_time: datetime


@dataclass
class EmotionalIntelligenceMetrics:
    """Performance metrics for the emotional intelligence system"""

    total_assessments: int
    prediction_accuracy: float
    intervention_success_rate: float
    crisis_prevention_count: int
    user_satisfaction_score: float
    average_response_time: float
    last_updated: datetime


class PredictiveEmotionalIntelligence:
    """
    Phase 2: Complete Predictive Emotional Intelligence System

    Combines emotion prediction, mood detection, and proactive support
    to provide comprehensive emotional intelligence capabilities.
    """

    def __init__(self, graph_personality_manager=None, conversation_cache=None):
        """Initialize the complete emotional intelligence system"""
        logger.info("Initializing Phase 2 Predictive Emotional Intelligence System")

        # Core components - initialize only if available
        if EMOTION_PREDICTOR_AVAILABLE:
            self.emotion_predictor = EmotionPredictor()
        else:
            self.emotion_predictor = None
            logger.warning("Emotion predictor not available - spaCy dependency missing")

        if MOOD_DETECTOR_AVAILABLE:
            self.mood_detector = MoodDetector()
        else:
            self.mood_detector = None
            logger.warning("Mood detector not available - spaCy dependency missing")

        self.proactive_support = ProactiveSupport()

        # External integrations
        self.graph_personality_manager = graph_personality_manager
        self.conversation_cache = conversation_cache

        # System configuration
        self.assessment_frequency = timedelta(minutes=30)  # Regular assessments
        self.emergency_threshold = 0.8  # Crisis intervention threshold
        self.prediction_horizon = timedelta(hours=24)  # How far ahead to predict

        # Memory and caching
        self.user_assessments = defaultdict(deque)  # Last 20 assessments per user
        self.user_strategies = {}  # Personalized support strategies (WILL BE PERSISTENT)
        self.active_interventions = {}  # Currently active interventions (EPHEMERAL - session only)
        self.system_metrics = EmotionalIntelligenceMetrics(
            total_assessments=0,
            prediction_accuracy=0.0,
            intervention_success_rate=0.0,
            crisis_prevention_count=0,
            user_satisfaction_score=0.0,
            average_response_time=0.0,
            last_updated=datetime.now(UTC),
        )

        # Assessment history for learning
        self.max_history_per_user = 20

        # Initialize database persistence
        self._persistence_initialized = False

        logger.info("Phase 2 Emotional Intelligence System initialized successfully")

    def _create_fallback_mood_assessment(self):
        """Create fallback mood assessment when mood detector is not available"""
        # Return a simple object with the required attributes for compatibility
        class FallbackMoodAssessment:
            def __init__(self):
                self.mood_category = type('MoodCategory', (), {'value': 'neutral'})()
                self.mood_score = 0.0
                self.confidence = 0.3
                self.contributing_factors = ['mood_detector_unavailable']
                self.linguistic_indicators = []
                self.temporal_context = 'unknown'
                self.assessment_timestamp = datetime.now(UTC)
        
        return FallbackMoodAssessment()

    def _create_fallback_stress_assessment(self):
        """Create fallback stress assessment when mood detector is not available"""
        # Return a simple object with the required attributes for compatibility
        class FallbackStressAssessment:
            def __init__(self):
                self.stress_level = type('StressLevel', (), {'value': 'low'})()
                self.stress_score = 0.0
                self.immediate_stressors = []
                self.physiological_indicators = []
                self.cognitive_load_indicators = []
                self.coping_indicators = ['system_fallback']
                self.assessment_timestamp = datetime.now(UTC)
        
        return FallbackStressAssessment()

    def _create_fallback_emotional_prediction(self):
        """Create fallback emotional prediction when emotion predictor is not available"""
        # Return a simple object with the required attributes for compatibility
        class FallbackEmotionalPrediction:
            def __init__(self):
                self.predicted_emotion = 'neutral'
                self.confidence = 0.3
                self.time_horizon = 'unknown'
                self.triggering_factors = ['emotion_predictor_unavailable']
                self.recommended_actions = ['continue_monitoring']
                self.risk_level = 'low'
        
        return FallbackEmotionalPrediction()

    def _safe_asdict(self, obj):
        """Safely convert object to dict, handling both dataclasses and fallback objects"""
        try:
            return asdict(obj)
        except TypeError:
            # For fallback objects, manually create dict
            return {
                attr: getattr(obj, attr) for attr in dir(obj) 
                if not attr.startswith('_') and not callable(getattr(obj, attr))
            }

    async def comprehensive_emotional_assessment(
        self, user_id: str, current_message: str, conversation_context: dict[str, Any]
    ) -> EmotionalIntelligenceAssessment:
        """
        Perform complete emotional intelligence assessment

        Args:
            user_id: User identifier
            current_message: Current user message
            conversation_context: Full conversation context

        Returns:
            Comprehensive emotional assessment with recommendations
        """
        start_time = datetime.now()
        perf_start = time.perf_counter()
        logger.debug("Starting comprehensive emotional assessment for user %s", user_id)

        try:
            # Step 1: Real-time mood and stress detection
            if self.mood_detector is not None:
                mood_assessment = await self.mood_detector.assess_current_mood(
                    current_message, conversation_context
                )

                stress_assessment = await self.mood_detector.assess_stress_level(
                    current_message, conversation_context
                )
            else:
                # Fallback when mood detector is not available
                logger.warning("Mood detector not available, using fallback values")
                mood_assessment = self._create_fallback_mood_assessment()
                stress_assessment = self._create_fallback_stress_assessment()

            # Step 2: Get historical patterns for prediction
            conversation_history = await self._get_conversation_history(user_id)
            emotional_patterns = None  # Initialize to avoid scope issues

            if len(conversation_history) >= 2 and self.emotion_predictor is not None:
                emotional_patterns = await self.emotion_predictor.analyze_emotional_patterns(
                    user_id, conversation_history
                )

                # Step 3: Generate emotional prediction
                prediction_context = {
                    "topic": conversation_context.get("topic", "general"),
                    "recent_messages": [current_message],
                    "communication_style": conversation_context.get(
                        "communication_style", "casual"
                    ),
                    "recent_mood_history": [self._safe_asdict(mood_assessment)],
                    "recent_stress_history": [self._safe_asdict(stress_assessment)],
                }

                emotional_prediction = await self.emotion_predictor.predict_emotional_state(
                    user_id, prediction_context, emotional_patterns
                )
            else:
                logger.debug(
                    "Building emotional profile: %d conversation turns with user %s (emotion predictor available: %s)",
                    len(conversation_history),
                    user_id,
                    self.emotion_predictor is not None,
                )
                emotional_prediction = self._create_fallback_emotional_prediction()

            # Step 4: Detect emotional alerts
            user_mood_history = self._get_recent_mood_history(user_id)
            user_stress_history = self._get_recent_stress_history(user_id)

            if self.mood_detector is not None:
                emotional_alerts = await self.mood_detector.detect_emotional_alerts(
                    user_mood_history + [mood_assessment],
                    user_stress_history + [stress_assessment],
                    conversation_context,
                )
            else:
                emotional_alerts = []  # No alerts when mood detector unavailable

            # Step 5: Analyze support needs
            emotional_context = {
                "mood_assessment": self._safe_asdict(mood_assessment),
                "stress_assessment": self._safe_asdict(stress_assessment),
                "emotional_alerts": [self._safe_asdict(alert) for alert in emotional_alerts],
                "emotional_predictions": self._safe_asdict(emotional_prediction),
                "emotional_trajectory": (
                    emotional_patterns.get("emotional_trajectory", {})
                    if emotional_patterns and len(conversation_history) >= 2
                    else {}
                ),
            }

            support_needs = await self.proactive_support.analyze_support_needs(
                user_id, emotional_context, conversation_history
            )

            # Step 6: Create intervention if needed
            recommended_intervention = None
            if support_needs.get("support_urgency", 1) >= 3:
                user_strategy = self.user_strategies.get(user_id)
                recommended_intervention = await self.proactive_support.create_support_intervention(
                    user_id, support_needs, user_strategy
                )

            # Step 7: Determine system phase status
            phase_status = self._determine_phase_status(
                mood_assessment, stress_assessment, emotional_alerts
            )

            # Step 8: Calculate confidence score
            confidence_score = self._calculate_assessment_confidence(
                mood_assessment, stress_assessment, emotional_prediction, len(conversation_history)
            )

            # Step 9: Schedule next assessment
            next_assessment_time = self._calculate_next_assessment_time(
                phase_status, emotional_alerts
            )

            assessment = EmotionalIntelligenceAssessment(
                user_id=user_id,
                assessment_timestamp=datetime.now(UTC),
                mood_assessment=mood_assessment,
                stress_assessment=stress_assessment,
                emotional_prediction=emotional_prediction,
                emotional_alerts=emotional_alerts,
                support_needs=support_needs,
                recommended_intervention=recommended_intervention,
                phase_status=phase_status,
                confidence_score=confidence_score,
                next_assessment_time=next_assessment_time,
            )

            self._store_assessment(user_id, assessment)

            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_system_metrics(assessment, processing_time)

            logger.info(
                "Comprehensive assessment completed for %s: %s status, confidence %.2f",
                user_id,
                phase_status.value,
                confidence_score,
            )
            if metrics and metrics.metrics_enabled():
                duration = time.perf_counter() - perf_start
                try:
                    metrics.record_timing(
                        "emotional_assessment_seconds",
                        duration,
                        phase=phase_status.value,
                        alerts=len(emotional_alerts),
                    )
                    metrics.incr(
                        "emotional_assessment_total",
                        status="success",
                        phase=phase_status.value,
                    )
                    if emotional_alerts:
                        metrics.incr(
                            "emotional_alerts_generated", amount=len(emotional_alerts)
                        )
                except (ValueError, RuntimeError, TypeError) as metrics_err:
                    logger.debug(
                        "Metrics recording skipped due to error: %s", metrics_err
                    )
            return assessment

        except Exception as e:  # noqa: BLE001 keep broad to ensure safe fallback
            logger.error(
                "Error in comprehensive emotional assessment for %s: %s", user_id, e
            )
            if metrics and metrics.metrics_enabled():
                duration = time.perf_counter() - perf_start
                try:
                    metrics.record_timing(
                        "emotional_assessment_seconds",
                        duration,
                        phase="error",
                        alerts=0,
                        error=True,
                    )
                    metrics.incr("emotional_assessment_total", status="error")
                except (ValueError, RuntimeError, TypeError) as metrics_err:
                    logger.debug(
                        "Metrics error path recording failed: %s", metrics_err
                    )
            return EmotionalIntelligenceAssessment(
                user_id=user_id,
                assessment_timestamp=datetime.now(UTC),
                mood_assessment=self._create_fallback_mood_assessment(),
                stress_assessment=self._create_fallback_stress_assessment(),
                emotional_prediction=self._create_fallback_emotional_prediction(),
                emotional_alerts=[],
                support_needs={},
                recommended_intervention=None,
                phase_status=PhaseStatus.MONITORING,
                confidence_score=0.0,
                next_assessment_time=datetime.now(UTC) + timedelta(minutes=5),
            )

    async def _get_conversation_history(self, user_id: str) -> list[dict]:
        """Get conversation history for pattern analysis"""

        # IMPORTANT: In Discord, each channel represents one continuous conversation
        # We need to count conversation TURNS (user-assistant exchanges), not separate conversations

        formatted_history = []

        try:
            # Try to get conversation data from stored assessments (most reliable)
            user_assessments = self.user_assessments.get(user_id, deque())

            # Each assessment represents a conversation turn with the user
            for assessment in user_assessments:
                formatted_conv = {
                    "timestamp": assessment.assessment_timestamp.isoformat(),
                    "emotion": assessment.mood_assessment.mood_category.value,
                    "stress_level": assessment.stress_assessment.stress_level.value,
                    "user_message": "",  # Historical limitation - not stored in assessments
                    "bot_response": "",
                    "topic": "general",
                    "communication_style": "casual",
                }
                formatted_history.append(formatted_conv)

            # Sort by timestamp to maintain chronological order
            formatted_history.sort(key=lambda x: x["timestamp"])

            logger.debug(
                f"Retrieved {len(formatted_history)} conversation turns from stored assessments for user {user_id}"
            )

        except Exception as e:
            logger.warning(f"Could not retrieve conversation history for {user_id}: {str(e)}")

        return formatted_history

    def _get_recent_mood_history(self, user_id: str) -> list[MoodAssessment]:
        """Get recent mood assessment history"""
        user_assessments = self.user_assessments.get(user_id, deque())
        return [assessment.mood_assessment for assessment in list(user_assessments)[-10:]]

    def _get_recent_stress_history(self, user_id: str) -> list[StressAssessment]:
        """Get recent stress assessment history"""
        user_assessments = self.user_assessments.get(user_id, deque())
        return [assessment.stress_assessment for assessment in list(user_assessments)[-10:]]

    def _determine_phase_status(
        self, mood: MoodAssessment, stress: StressAssessment, alerts: list[EmotionalAlert]
    ) -> PhaseStatus:
        """Determine current system phase status"""

        # Crisis phase
        crisis_alerts = [alert for alert in alerts if alert.severity == "critical"]
        if crisis_alerts or stress.stress_level.value == "critical":
            return PhaseStatus.CRISIS

        # Intervention phase
        high_priority_alerts = [alert for alert in alerts if alert.urgency_level >= 4]
        if (
            high_priority_alerts
            or stress.stress_level.value == "high"
            or mood.mood_category.value == "very_negative"
        ):
            return PhaseStatus.INTERVENTION

        # Monitoring phase
        if (
            alerts
            or stress.stress_level.value in ["moderate", "high"]
            or mood.mood_category.value == "negative"
        ):
            return PhaseStatus.MONITORING

        # Active phase (normal operation)
        return PhaseStatus.ACTIVE

    def _calculate_assessment_confidence(
        self,
        mood: MoodAssessment,
        _stress: StressAssessment,
        prediction: EmotionalPrediction,
        history_length: int,
    ) -> float:
        """Calculate overall assessment confidence"""

        # Weight different confidence scores
        mood_weight = 0.3
        stress_weight = 0.2
        prediction_weight = 0.3
        history_weight = 0.2

        # History confidence (more history = higher confidence)
        history_confidence = min(1.0, history_length / 20.0)

        # Combined confidence
        overall_confidence = (
            mood.confidence * mood_weight
            + 0.8 * stress_weight  # Stress assessment is generally reliable
            + prediction.confidence * prediction_weight
            + history_confidence * history_weight
        )

        return min(1.0, overall_confidence)

    def _calculate_next_assessment_time(
        self, phase_status: PhaseStatus, _alerts: list[EmotionalAlert]
    ) -> datetime:
        """Calculate when next assessment should occur"""

        base_time = datetime.now(UTC)

        if phase_status == PhaseStatus.CRISIS:
            return base_time + timedelta(minutes=5)  # Very frequent monitoring
        elif phase_status == PhaseStatus.INTERVENTION:
            return base_time + timedelta(minutes=15)  # Frequent monitoring
        elif phase_status == PhaseStatus.MONITORING:
            return base_time + timedelta(minutes=30)  # Regular monitoring
        else:  # ACTIVE
            return base_time + self.assessment_frequency

    def _store_assessment(self, user_id: str, assessment: EmotionalIntelligenceAssessment):
        """Store assessment in user history"""
        if user_id not in self.user_assessments:
            self.user_assessments[user_id] = deque(maxlen=self.max_history_per_user)

        self.user_assessments[user_id].append(assessment)

    async def _update_system_metrics(
        self, _assessment: EmotionalIntelligenceAssessment, processing_time: float
    ):
        """Update system performance metrics"""
        self.system_metrics.total_assessments += 1

        # Update average response time
        current_avg = self.system_metrics.average_response_time
        total_assessments = self.system_metrics.total_assessments

        self.system_metrics.average_response_time = (
            current_avg * (total_assessments - 1) + processing_time
        ) / total_assessments

        self.system_metrics.last_updated = datetime.now(UTC)

    async def execute_intervention(
        self, intervention: SupportIntervention, delivery_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a support intervention

        Args:
            intervention: The intervention to execute
            delivery_context: Context for delivery

        Returns:
            Execution result
        """
        logger.info("Executing intervention %s", intervention.intervention_id)

        try:
            delivery_result = await self.proactive_support.deliver_intervention(
                intervention, delivery_context
            )

            if delivery_result.get("delivered"):
                # Track active intervention session state (ephemeral)
                self.active_interventions[intervention.intervention_id] = {
                    "intervention": intervention,
                    "delivery_result": delivery_result,
                    "start_time": datetime.now(UTC),
                }
                logger.info(
                    "Intervention %s delivered successfully", intervention.intervention_id
                )
            else:
                logger.warning(
                    "Intervention %s delivery failed: %s",
                    intervention.intervention_id,
                    delivery_result.get("reason"),
                )
            return delivery_result
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Error executing intervention %s: %s", intervention.intervention_id, e
            )
            return {
                "delivered": False,
                "error": str(e),
                "intervention_id": intervention.intervention_id,
            }

    async def track_intervention_response(
        self, intervention_id: str, user_response: str, response_context: dict[str, Any]
    ) -> SupportOutcome:
        """Track user response and update intervention metrics."""
        logger.debug("Tracking response to intervention %s", intervention_id)
        try:
            outcome = await self.proactive_support.track_intervention_outcome(
                intervention_id, user_response, response_context
            )
            if intervention_id in self.active_interventions:
                self.active_interventions[intervention_id]["outcome"] = outcome
                self.active_interventions[intervention_id]["end_time"] = datetime.now(UTC)
                self._update_intervention_success_rate(
                    outcome.effectiveness_score >= 0.6
                )
            await self._learn_from_intervention_outcome(intervention_id, outcome)
            logger.debug(
                "Intervention %s outcome: %s (effectiveness: %.2f)",
                intervention_id,
                outcome.outcome_type,
                outcome.effectiveness_score,
            )
            return outcome
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Error tracking intervention response for %s: %s", intervention_id, e
            )
            # Minimal fallback SupportOutcome to maintain flow
            return SupportOutcome(
                intervention_id=intervention_id,
                outcome_type="error",
                user_response=user_response,
                effectiveness_score=0.0,
                follow_up_needed=True,
                lessons_learned=["error_processing_intervention_response"],
                timestamp=datetime.now(UTC),
            )
        # NOTE: The following block previously existed outside the method due to
        # indentation errors introduced during logging refactor. It has been
        # removed to prevent unreachable code and structural corruption.

    async def get_user_emotional_dashboard(self, user_id: str) -> dict[str, Any]:
        """
        Generate comprehensive emotional dashboard for user

        Args:
            user_id: User identifier

        Returns:
            Comprehensive emotional intelligence dashboard
        """
        logger.debug("Generating emotional dashboard for user %s", user_id)

        user_assessments = list(self.user_assessments.get(user_id, deque()))

        if not user_assessments:
            return {
                "user_id": user_id,
                "status": "no_data",
                "message": "No assessment data available for this user",
            }

        latest_assessment = user_assessments[-1]

        # Calculate trends
        mood_trend = self._calculate_mood_trend(user_assessments)
        stress_trend = self._calculate_stress_trend(user_assessments)

        # Get active interventions
        user_active_interventions = {
            k: v
            for k, v in self.active_interventions.items()
            if k.startswith(f"{user_id}_intervention_")
        }

        # Get user strategy
        user_strategy = self.user_strategies.get(user_id)

        dashboard = {
            "user_id": user_id,
            "last_updated": latest_assessment.assessment_timestamp.isoformat(),
            "current_status": {
                "phase": latest_assessment.phase_status.value,
                "mood": latest_assessment.mood_assessment.mood_category.value,
                "stress": latest_assessment.stress_assessment.stress_level.value,
                "confidence": f"{latest_assessment.confidence_score:.1%}",
                "alerts": len(latest_assessment.emotional_alerts),
            },
            "trends": {
                "mood_trend": mood_trend,
                "stress_trend": stress_trend,
                "assessment_count": len(user_assessments),
            },
            "predictions": {
                "next_emotion": latest_assessment.emotional_prediction.predicted_emotion,
                "confidence": f"{latest_assessment.emotional_prediction.confidence:.1%}",
                "risk_level": latest_assessment.emotional_prediction.risk_level,
                "time_horizon": latest_assessment.emotional_prediction.time_horizon,
            },
            "support": {
                "active_interventions": len(user_active_interventions),
                "support_urgency": latest_assessment.support_needs.get("support_urgency", 1),
                "recommended_actions": latest_assessment.emotional_prediction.recommended_actions,
            },
            "personalization": {
                "effective_approaches": user_strategy.effective_approaches if user_strategy else [],
                "communication_style": (
                    user_strategy.communication_style if user_strategy else "unknown"
                ),
                "support_history_count": len(user_strategy.support_history) if user_strategy else 0,
            },
            "next_assessment": latest_assessment.next_assessment_time.isoformat(),
        }

        return dashboard

    def _calculate_mood_trend(self, assessments: list[EmotionalIntelligenceAssessment]) -> str:
        """Calculate mood trend from recent assessments"""
        if len(assessments) < 2:
            return "insufficient_data"

        recent_moods = [assessment.mood_assessment.mood_score for assessment in assessments[-5:]]

        if len(recent_moods) >= 3:
            # Calculate linear trend
            x = list(range(len(recent_moods)))
            y = recent_moods

            # Simple linear regression slope
            n = len(x)
            slope = (n * sum(xi * yi for xi, yi in zip(x, y, strict=False)) - sum(x) * sum(y)) / (
                n * sum(xi**2 for xi in x) - sum(x) ** 2
            )

            if slope > 0.1:
                return "improving"
            elif slope < -0.1:
                return "declining"
            else:
                return "stable"

        # Fallback: compare first and last
        if recent_moods[-1] > recent_moods[0] + 0.2:
            return "improving"
        elif recent_moods[-1] < recent_moods[0] - 0.2:
            return "declining"
        else:
            return "stable"

    def _calculate_stress_trend(self, assessments: list[EmotionalIntelligenceAssessment]) -> str:
        """Calculate stress trend from recent assessments"""
        if len(assessments) < 2:
            return "insufficient_data"

        recent_stress = [
            assessment.stress_assessment.stress_score for assessment in assessments[-5:]
        ]

        if len(recent_stress) >= 3:
            # Calculate average change
            changes = [
                recent_stress[i] - recent_stress[i - 1] for i in range(1, len(recent_stress))
            ]
            avg_change = sum(changes) / len(changes)

            if avg_change > 0.1:
                return "increasing"
            elif avg_change < -0.1:
                return "decreasing"
            else:
                return "stable"

        # Fallback: compare first and last
        if recent_stress[-1] > recent_stress[0] + 0.2:
            return "increasing"
        elif recent_stress[-1] < recent_stress[0] - 0.2:
            return "decreasing"
        else:
            return "stable"

    async def get_system_health_report(self) -> dict[str, Any]:
        """Generate system health and performance report"""

        total_users = len(self.user_assessments)
        total_active_interventions = len(self.active_interventions)

        # Calculate intervention effectiveness
        completed_interventions = [
            intervention
            for intervention in self.active_interventions.values()
            if "outcome" in intervention
        ]

        if completed_interventions:
            avg_effectiveness = sum(
                intervention["outcome"].effectiveness_score
                for intervention in completed_interventions
            ) / len(completed_interventions)
        else:
            avg_effectiveness = 0.0

        # Count users by phase status
        phase_distribution = defaultdict(int)
        for user_assessments in self.user_assessments.values():
            if user_assessments:
                latest_phase = user_assessments[-1].phase_status
                phase_distribution[latest_phase.value] += 1

        report = {
            "system_status": "operational",
            "timestamp": datetime.now(UTC).isoformat(),
            "performance_metrics": asdict(self.system_metrics),
            "user_statistics": {
                "total_users": total_users,
                "users_by_phase": dict(phase_distribution),
                "active_interventions": total_active_interventions,
            },
            "intervention_analytics": {
                "total_interventions": len(self.active_interventions),
                "completed_interventions": len(completed_interventions),
                "average_effectiveness": f"{avg_effectiveness:.1%}",
                "success_rate": f"{self.system_metrics.intervention_success_rate:.1%}",
            },
            "system_performance": {
                "average_response_time": f"{self.system_metrics.average_response_time:.2f}s",
                "total_assessments": self.system_metrics.total_assessments,
                "uptime": "operational",  # Would calculate actual uptime in production
            },
        }

        return report

    def get_assessment_summary(self, assessment: EmotionalIntelligenceAssessment) -> dict[str, Any]:
        """Generate human-readable assessment summary"""
        return {
            "user_id": assessment.user_id,
            "timestamp": assessment.assessment_timestamp.isoformat(),
            "emotional_state": {
                "mood": assessment.mood_assessment.mood_category.value,
                "mood_score": f"{assessment.mood_assessment.mood_score:.2f}",
                "stress_level": assessment.stress_assessment.stress_level.value,
                "stress_score": f"{assessment.stress_assessment.stress_score:.2f}",
            },
            "predictions": {
                "predicted_emotion": assessment.emotional_prediction.predicted_emotion,
                "confidence": f"{assessment.emotional_prediction.confidence:.1%}",
                "risk_level": assessment.emotional_prediction.risk_level,
            },
            "alerts": {
                "count": len(assessment.emotional_alerts),
                "highest_priority": max(
                    [alert.urgency_level for alert in assessment.emotional_alerts], default=0
                ),
                "requires_intervention": assessment.recommended_intervention is not None,
            },
            "system_status": {
                "phase": assessment.phase_status.value,
                "confidence": f"{assessment.confidence_score:.1%}",
                "next_assessment": assessment.next_assessment_time.isoformat(),
            },
            "summary": f"Phase 2 Assessment: {assessment.phase_status.value} status, {assessment.mood_assessment.mood_category.value} mood, {assessment.stress_assessment.stress_level.value} stress",
        }

    # ===== STRATEGY MANAGEMENT HELPERS =====

    async def _ensure_user_strategy_loaded(self, user_id: str):
        """Ensure user strategy is loaded from database or create new one"""
        if user_id in self.user_strategies:
            return  # Already loaded

        # Try to load from database first
        if not self._persistence_initialized:
            await self.initialize_persistence()
            self._persistence_initialized = True

        # Load existing strategy from database
        existing_strategy = await self.load_user_strategy(user_id, f"{user_id}_strategy")
        
        if existing_strategy:
            self.user_strategies[user_id] = existing_strategy
            logger.debug("Loaded existing strategy for user %s", user_id)
        else:
            # Create new strategy
            new_strategy = SupportStrategy(
                strategy_id=f"{user_id}_strategy",
                user_preferences={},
                effective_approaches=[],
                approaches_to_avoid=[],
                optimal_timing={},
                communication_style="casual",
                support_history=[],
                last_updated=datetime.now(UTC),
            )
            self.user_strategies[user_id] = new_strategy
            # Save to database
            await self.save_user_strategy(user_id, new_strategy)
            logger.debug("Created new strategy for user %s", user_id)

    async def _save_strategy_if_updated(self, user_id: str):
        """Save user strategy to database if it has been updated"""
        if user_id in self.user_strategies:
            strategy = self.user_strategies[user_id]
            strategy.last_updated = datetime.now(UTC)
            await self.save_user_strategy(user_id, strategy)

    # ===== DATABASE PERSISTENCE METHODS =====

    def _get_db_connection(self):
        """Get database connection for emotional intelligence persistence"""
        if not POSTGRES_AVAILABLE:
            logger.warning("PostgreSQL not available - emotional intelligence data will not persist")
            return None

        try:
            connection = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "whisper_engine"),
                user=os.getenv("POSTGRES_USER", "bot_user"),
                password=os.getenv("POSTGRES_PASSWORD", "securepassword123"),
            )
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL for emotional intelligence persistence: {e}")
            return None

    def _ensure_emotional_intelligence_tables(self):
        """Ensure emotional intelligence tables exist in the database"""
        connection = self._get_db_connection()
        if not connection:
            return False

        try:
            with connection.cursor() as cursor:
                # User emotional profiles table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_emotional_profiles (
                        user_id VARCHAR(255) PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Core emotional intelligence metrics
                        total_assessments INTEGER DEFAULT 0,
                        prediction_accuracy FLOAT DEFAULT 0.0,
                        intervention_success_rate FLOAT DEFAULT 0.0,
                        crisis_prevention_count INTEGER DEFAULT 0,
                        user_satisfaction_score FLOAT DEFAULT 0.0,
                        average_response_time FLOAT DEFAULT 0.0,
                        
                        -- Emotional patterns
                        primary_emotional_patterns JSONB DEFAULT '[]'::jsonb,
                        stress_triggers JSONB DEFAULT '[]'::jsonb,
                        emotional_recovery_patterns JSONB DEFAULT '{}'::jsonb,
                        
                        -- System metrics
                        last_assessment_time TIMESTAMP,
                        next_assessment_time TIMESTAMP,
                        phase_status VARCHAR(50) DEFAULT 'monitoring'
                    )
                """
                )

                # User support strategies table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_support_strategies (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        strategy_type VARCHAR(100) NOT NULL,
                        
                        -- Strategy details
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Effectiveness metrics
                        success_rate FLOAT DEFAULT 0.0,
                        usage_count INTEGER DEFAULT 0,
                        user_feedback_score FLOAT DEFAULT 0.0,
                        
                        -- Strategy content
                        effective_approaches JSONB DEFAULT '[]'::jsonb,
                        approaches_to_avoid JSONB DEFAULT '[]'::jsonb,
                        personalized_triggers JSONB DEFAULT '[]'::jsonb,
                        recommended_responses JSONB DEFAULT '[]'::jsonb,
                        
                        -- Context
                        context_patterns JSONB DEFAULT '{}'::jsonb,
                        support_history JSONB DEFAULT '[]'::jsonb,
                        
                        -- Constraints
                        CONSTRAINT fk_user_emotional_profile
                            FOREIGN KEY (user_id)
                            REFERENCES user_emotional_profiles(user_id)
                            ON DELETE CASCADE,
                        
                        -- Unique constraint for user + strategy type
                        CONSTRAINT unique_user_strategy
                            UNIQUE (user_id, strategy_type)
                    )
                """
                )

                # Support strategy history table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS support_strategy_history (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        strategy_id INTEGER NOT NULL,
                        
                        -- Historical record
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        action_type VARCHAR(50) NOT NULL,
                        
                        -- Context of the action
                        context_data JSONB DEFAULT '{}'::jsonb,
                        effectiveness_score FLOAT,
                        user_response VARCHAR(500),
                        
                        -- What changed
                        changes_made JSONB DEFAULT '{}'::jsonb,
                        previous_values JSONB DEFAULT '{}'::jsonb,
                        
                        -- Constraints
                        CONSTRAINT fk_user_emotional_profile_history
                            FOREIGN KEY (user_id)
                            REFERENCES user_emotional_profiles(user_id)
                            ON DELETE CASCADE,
                        
                        CONSTRAINT fk_support_strategy
                            FOREIGN KEY (strategy_id)
                            REFERENCES user_support_strategies(id)
                            ON DELETE CASCADE
                    )
                """
                )

                # Emotional assessments table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS emotional_assessments (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        
                        -- Assessment details
                        assessment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        assessment_type VARCHAR(100) NOT NULL,
                        
                        -- Assessment results
                        primary_emotion VARCHAR(50),
                        emotional_intensity FLOAT,
                        stress_level FLOAT,
                        confidence_score FLOAT,
                        
                        -- Predictions and recommendations
                        predicted_emotional_state JSONB DEFAULT '{}'::jsonb,
                        recommended_intervention_type VARCHAR(100),
                        support_recommendations JSONB DEFAULT '[]'::jsonb,
                        
                        -- Context
                        conversation_context JSONB DEFAULT '{}'::jsonb,
                        environmental_factors JSONB DEFAULT '{}'::jsonb,
                        
                        -- Results tracking
                        intervention_applied BOOLEAN DEFAULT FALSE,
                        intervention_success BOOLEAN,
                        user_feedback JSONB DEFAULT '{}'::jsonb,
                        
                        -- Constraints
                        CONSTRAINT fk_user_emotional_profile_assessment
                            FOREIGN KEY (user_id)
                            REFERENCES user_emotional_profiles(user_id)
                            ON DELETE CASCADE
                    )
                """
                )

                # Indexes for performance
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_user_support_strategies_user_id 
                    ON user_support_strategies(user_id)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_user_support_strategies_type 
                    ON user_support_strategies(user_id, strategy_type)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_support_strategy_history_user_id 
                    ON support_strategy_history(user_id)
                """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_emotional_assessments_user_id 
                    ON emotional_assessments(user_id)
                """
                )

                connection.commit()
                logger.info("Emotional intelligence database tables ensured")
                return True

        except Exception as e:
            logger.error(f"Failed to create emotional intelligence tables: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()

    async def save_user_strategy(self, user_id: str, strategy: SupportStrategy):
        """Save user support strategy to database"""
        connection = self._get_db_connection()
        if not connection:
            return False

        try:
            with connection.cursor() as cursor:
                # First ensure user profile exists
                cursor.execute(
                    """
                    INSERT INTO user_emotional_profiles (user_id)
                    VALUES (%s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (user_id,)
                )

                # Insert or update strategy
                cursor.execute(
                    """
                    INSERT INTO user_support_strategies
                    (user_id, strategy_type, last_updated, effective_approaches, 
                     approaches_to_avoid, context_patterns, support_history)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, strategy_type) DO UPDATE SET
                        last_updated = EXCLUDED.last_updated,
                        effective_approaches = EXCLUDED.effective_approaches,
                        approaches_to_avoid = EXCLUDED.approaches_to_avoid,
                        context_patterns = EXCLUDED.context_patterns,
                        support_history = EXCLUDED.support_history
                """,
                    (
                        user_id,
                        strategy.strategy_id,  # Use strategy_id as strategy_type
                        strategy.last_updated,
                        json.dumps(strategy.effective_approaches),
                        json.dumps(strategy.approaches_to_avoid),
                        json.dumps(strategy.user_preferences),  # Store user_preferences as context_patterns
                        json.dumps(strategy.support_history),
                    ),
                )

                connection.commit()
                logger.debug(
                    "Saved support strategy for user %s, type %s", user_id, strategy.strategy_id
                )
                return True

        except psycopg2.Error as e:  # type: ignore[name-defined]
            logger.error(
                "Failed to save support strategy for user %s: %s", user_id, e
            )
            connection.rollback()
            return False
        finally:
            connection.close()

    async def load_user_strategy(self, user_id: str, strategy_type: str) -> SupportStrategy | None:
        """Load user support strategy from database"""
        connection = self._get_db_connection()
        if not connection:
            return None

        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM user_support_strategies
                    WHERE user_id = %s AND strategy_type = %s
                """,
                    (user_id, strategy_type),
                )
                strategy_row = cursor.fetchone()

                if not strategy_row:
                    return None

                # Reconstruct SupportStrategy object with validated types
                raw_prefs = self._safe_json_loads(strategy_row["context_patterns"], {})
                user_prefs = raw_prefs if isinstance(raw_prefs, dict) else {}
                raw_effective = self._safe_json_loads(strategy_row["effective_approaches"], [])
                effective_list = [str(x) for x in raw_effective] if isinstance(raw_effective, list) else []
                raw_avoid = self._safe_json_loads(strategy_row["approaches_to_avoid"], [])
                avoid_list = [str(x) for x in raw_avoid] if isinstance(raw_avoid, list) else []
                raw_history = self._safe_json_loads(strategy_row["support_history"], [])
                history_list = [cast(dict[str, Any], x) for x in raw_history] if isinstance(raw_history, list) else []
                strategy = SupportStrategy(
                    strategy_id=strategy_row["strategy_type"],
                    user_preferences=cast(dict[str, Any], user_prefs),
                    effective_approaches=cast(list[str], effective_list),
                    approaches_to_avoid=cast(list[str], avoid_list),
                    optimal_timing={"any": "flexible"},  # Default timing
                    communication_style="adaptive",  # Default style
                    support_history=history_list,
                    last_updated=strategy_row["last_updated"],
                )

                logger.debug(
                    "Loaded support strategy for user %s, type %s", user_id, strategy_type
                )
                return strategy

        except psycopg2.Error as e:  # type: ignore[name-defined]
            logger.error(
                "Failed to load support strategy for user %s: %s", user_id, e
            )
            return None
        finally:
            connection.close()

    async def load_all_user_strategies(self, user_id: str) -> dict[str, SupportStrategy]:
        """Load all support strategies for a user"""
        connection = self._get_db_connection()
        if not connection:
            return {}

        try:
            strategies = {}
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM user_support_strategies
                    WHERE user_id = %s
                """,
                    (user_id,),
                )
                strategy_rows = cursor.fetchall()

                for strategy_row in strategy_rows:
                    raw_prefs = self._safe_json_loads(strategy_row["context_patterns"], {})
                    user_prefs = raw_prefs if isinstance(raw_prefs, dict) else {}
                    raw_effective = self._safe_json_loads(strategy_row["effective_approaches"], [])
                    effective_list = [str(x) for x in raw_effective] if isinstance(raw_effective, list) else []
                    raw_avoid = self._safe_json_loads(strategy_row["approaches_to_avoid"], [])
                    avoid_list = [str(x) for x in raw_avoid] if isinstance(raw_avoid, list) else []
                    raw_history = self._safe_json_loads(strategy_row["support_history"], [])
                    history_list = [cast(dict[str, Any], x) for x in raw_history] if isinstance(raw_history, list) else []
                    strategy = SupportStrategy(
                        strategy_id=strategy_row["strategy_type"],
                        user_preferences=cast(dict[str, Any], user_prefs),
                        effective_approaches=cast(list[str], effective_list),
                        approaches_to_avoid=cast(list[str], avoid_list),
                        optimal_timing={"any": "flexible"},
                        communication_style="adaptive",
                        support_history=history_list,
                        last_updated=strategy_row["last_updated"],
                    )
                    strategies[strategy.strategy_id] = strategy

                logger.debug(
                    "Loaded %d support strategies for user %s", len(strategies), user_id
                )
                return strategies

        except psycopg2.Error as e:  # type: ignore[name-defined]
            logger.error(
                "Failed to load support strategies for user %s: %s", user_id, e
            )
            return {}
        finally:
            connection.close()

    def _safe_json_loads(self, value, default=None):
        """Safely load JSON data, handling various input types"""
        if value is None:
            return default if default is not None else {}

        if isinstance(value, (dict, list)):
            return value

        if isinstance(value, str):
            if not value.strip():
                return default if default is not None else {}
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError) as e:  # noqa: BLE001
                logger.warning(
                    "Failed to parse JSON: %s... Error: %s", value[:50], e
                )
                return default if default is not None else {}

        logger.warning(
            "Unexpected value type for JSON parsing: %s - %s", type(value), value
        )
        return default if default is not None else {}

    # ===== INTERVENTION LEARNING HELPERS =====

    def _update_intervention_success_rate(self, successful: bool):
        """Update rolling intervention success metric using incremental average.

        Uses total_assessments as a proxy for sample size to avoid introducing
        another counter just for this lightweight Phase 2 implementation.
        """
        try:
            samples = max(1, self.system_metrics.total_assessments)
            current = self.system_metrics.intervention_success_rate
            value = 1.0 if successful else 0.0
            self.system_metrics.intervention_success_rate = (
                (current * (samples - 1)) + value
            ) / samples
        except (RuntimeError, ValueError):
            pass

    async def _learn_from_intervention_outcome(
        self, intervention_id: str, outcome: SupportOutcome
    ):
        """Lightweight adaptive learning stub.

        Future phases can extend this to update long-term personalized memory.
        Currently performs minimal heuristic adjustment of communication style.
        """
        try:
            if "_intervention_" not in intervention_id:
                return
            user_id = intervention_id.split("_intervention_")[0]
            strategy = self.user_strategies.get(user_id)
            if not strategy:
                return
            # Simple heuristic: if ineffective multiple times, switch style
            if outcome.effectiveness_score < 0.3 and strategy.communication_style == "casual":
                strategy.communication_style = "supportive"
        except (RuntimeError, ValueError):
            pass

    async def initialize_persistence(self):
        """Initialize database persistence for emotional intelligence"""
        if self._get_db_connection():
            self._ensure_emotional_intelligence_tables()
            logger.info("Emotional intelligence persistence initialized")
            
            # Load existing strategies for all users that have them
            # This could be optimized to load on-demand instead
            logger.info("Emotional intelligence persistence ready")
        else:
            logger.warning(
                "Database not available - emotional intelligence data will not persist across restarts"
            )
