"""
Phase 2 Predictive Emotional Intelligence System
===============================================

Integrates emotion prediction, mood detection, and proactive support
into a comprehensive emotional intelligence framework.

Phase 2: Complete Implementation
"""

import logging
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from .emotion_predictor import EmotionalPrediction, EmotionPredictor
from .mood_detector import (
    EmotionalAlert,
    MoodAssessment,
    MoodCategory,
    MoodDetector,
    StressAssessment,
    StressLevel,
)
from .proactive_support import (
    ProactiveSupport,
    SupportIntervention,
    SupportOutcome,
    SupportStrategy,
)

logger = logging.getLogger(__name__)


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

        # Core components
        self.emotion_predictor = EmotionPredictor()
        self.mood_detector = MoodDetector()
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
        self.user_strategies = {}  # Personalized support strategies
        self.active_interventions = {}  # Currently active interventions
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

        logger.info("Phase 2 Emotional Intelligence System initialized successfully")

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
        logger.debug(f"Starting comprehensive emotional assessment for user {user_id}")

        try:
            # Step 1: Real-time mood and stress detection
            mood_assessment = await self.mood_detector.assess_current_mood(
                current_message, conversation_context
            )

            stress_assessment = await self.mood_detector.assess_stress_level(
                current_message, conversation_context
            )

            # Step 2: Get historical patterns for prediction
            conversation_history = await self._get_conversation_history(user_id)

            if (
                len(conversation_history) >= 2
            ):  # Changed from 5 to 2 - we need at least 2 conversation turns for meaningful patterns
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
                    "recent_mood_history": [asdict(mood_assessment)],
                    "recent_stress_history": [asdict(stress_assessment)],
                }

                emotional_prediction = await self.emotion_predictor.predict_emotional_state(
                    user_id, prediction_context, emotional_patterns
                )
            else:
                # For new users or insufficient interaction history, use debug level
                logger.debug(
                    f"Building emotional profile: {len(conversation_history)} conversation turns with user {user_id}"
                )
                emotional_prediction = EmotionalPrediction(
                    predicted_emotion="neutral",
                    confidence=0.3,
                    time_horizon="unknown",
                    triggering_factors=["new_user_interaction"],
                    recommended_actions=["continue_monitoring"],
                    risk_level="low",
                )

            # Step 4: Detect emotional alerts
            user_mood_history = self._get_recent_mood_history(user_id)
            user_stress_history = self._get_recent_stress_history(user_id)

            emotional_alerts = await self.mood_detector.detect_emotional_alerts(
                user_mood_history + [mood_assessment],
                user_stress_history + [stress_assessment],
                conversation_context,
            )

            # Step 5: Analyze support needs
            emotional_context = {
                "mood_assessment": asdict(mood_assessment),
                "stress_assessment": asdict(stress_assessment),
                "emotional_alerts": [asdict(alert) for alert in emotional_alerts],
                "emotional_predictions": asdict(emotional_prediction),
                "emotional_trajectory": (
                    emotional_patterns.get("emotional_trajectory", {})
                    if len(conversation_history) >= 2
                    else {}
                ),  # Changed from 5 to 2
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

            # Create comprehensive assessment
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

            # Store assessment in memory
            self._store_assessment(user_id, assessment)

            # Update system metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_system_metrics(assessment, processing_time)

            logger.info(
                f"Comprehensive assessment completed for {user_id}: {phase_status.value} status, confidence {confidence_score:.2f}"
            )
            return assessment

        except Exception as e:
            logger.error(f"Error in comprehensive emotional assessment for {user_id}: {str(e)}")
            # Return minimal assessment in case of error
            return EmotionalIntelligenceAssessment(
                user_id=user_id,
                assessment_timestamp=datetime.now(UTC),
                mood_assessment=MoodAssessment(
                    mood_category=MoodCategory.NEUTRAL,
                    mood_score=0.0,
                    confidence=0.0,
                    contributing_factors=["error_in_assessment"],
                    linguistic_indicators=[],
                    temporal_context="unknown",
                    assessment_timestamp=datetime.now(UTC),
                ),
                stress_assessment=StressAssessment(
                    stress_level=StressLevel.MINIMAL,
                    stress_score=0.0,
                    immediate_stressors=[],
                    physiological_indicators=[],
                    cognitive_load_indicators=[],
                    coping_indicators=[],
                    assessment_timestamp=datetime.now(UTC),
                ),
                emotional_prediction=EmotionalPrediction(
                    predicted_emotion="neutral",
                    confidence=0.0,
                    time_horizon="unknown",
                    triggering_factors=["assessment_error"],
                    recommended_actions=["retry_assessment"],
                    risk_level="unknown",
                ),
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
        stress: StressAssessment,
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
        self, phase_status: PhaseStatus, alerts: list[EmotionalAlert]
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
        self, assessment: EmotionalIntelligenceAssessment, processing_time: float
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
        logger.info(f"Executing intervention {intervention.intervention_id}")

        try:
            # Deliver the intervention
            delivery_result = await self.proactive_support.deliver_intervention(
                intervention, delivery_context
            )

            if delivery_result["delivered"]:
                # Track active intervention
                self.active_interventions[intervention.intervention_id] = {
                    "intervention": intervention,
                    "delivery_result": delivery_result,
                    "start_time": datetime.now(UTC),
                }

                logger.info(f"Intervention {intervention.intervention_id} delivered successfully")
            else:
                logger.warning(
                    f"Intervention {intervention.intervention_id} delivery failed: {delivery_result.get('reason')}"
                )

            return delivery_result

        except Exception as e:
            logger.error(f"Error executing intervention {intervention.intervention_id}: {str(e)}")
            return {
                "delivered": False,
                "error": str(e),
                "intervention_id": intervention.intervention_id,
            }

    async def track_intervention_response(
        self, intervention_id: str, user_response: str, response_context: dict[str, Any]
    ) -> SupportOutcome:
        """
        Track user response to intervention

        Args:
            intervention_id: ID of the intervention
            user_response: User's response
            response_context: Additional context

        Returns:
            Outcome tracking information
        """
        logger.debug(f"Tracking response to intervention {intervention_id}")

        try:
            # Track the outcome
            outcome = await self.proactive_support.track_intervention_outcome(
                intervention_id, user_response, response_context
            )

            # Update intervention tracking
            if intervention_id in self.active_interventions:
                self.active_interventions[intervention_id]["outcome"] = outcome
                self.active_interventions[intervention_id]["end_time"] = datetime.now(UTC)

                # Update success rate metrics
                if outcome.effectiveness_score >= 0.6:
                    self._update_intervention_success_rate(True)
                else:
                    self._update_intervention_success_rate(False)

            # Learn from outcome for future interventions
            await self._learn_from_intervention_outcome(intervention_id, outcome)

            logger.debug(
                f"Intervention {intervention_id} outcome: {outcome.outcome_type} (effectiveness: {outcome.effectiveness_score:.2f})"
            )
            return outcome

        except Exception as e:
            logger.error(f"Error tracking intervention response for {intervention_id}: {str(e)}")
            # Return default outcome
            return SupportOutcome(
                intervention_id=intervention_id,
                outcome_type="error",
                user_response=user_response,
                effectiveness_score=0.0,
                follow_up_needed=True,
                lessons_learned=[f"Error in outcome tracking: {str(e)}"],
                timestamp=datetime.now(UTC),
            )

    def _update_intervention_success_rate(self, success: bool):
        """Update intervention success rate metrics"""
        current_rate = self.system_metrics.intervention_success_rate
        total_interventions = sum(
            1 for intervention in self.active_interventions.values() if "outcome" in intervention
        )

        if total_interventions == 1:
            self.system_metrics.intervention_success_rate = 1.0 if success else 0.0
        else:
            # Running average
            new_rate = (
                (current_rate * (total_interventions - 1)) + (1.0 if success else 0.0)
            ) / total_interventions
            self.system_metrics.intervention_success_rate = new_rate

    async def _learn_from_intervention_outcome(self, intervention_id: str, outcome: SupportOutcome):
        """Learn from intervention outcomes to improve future interventions"""
        if intervention_id not in self.active_interventions:
            return

        intervention_data = self.active_interventions[intervention_id]
        intervention = intervention_data["intervention"]

        # Extract user_id from intervention_id (format: user_id_intervention_number)
        user_id = intervention_id.split("_intervention_")[0]

        # Update or create user strategy
        if user_id not in self.user_strategies:
            self.user_strategies[user_id] = SupportStrategy(
                strategy_id=f"{user_id}_strategy",
                user_preferences={},
                effective_approaches=[],
                approaches_to_avoid=[],
                optimal_timing={},
                communication_style="casual",
                support_history=[],
                last_updated=datetime.now(UTC),
            )

        user_strategy = self.user_strategies[user_id]

        # Update strategy based on outcome
        if outcome.effectiveness_score >= 0.7:
            # This approach was effective
            approach = intervention.intervention_style.value
            if approach not in user_strategy.effective_approaches:
                user_strategy.effective_approaches.append(approach)
        elif outcome.effectiveness_score <= 0.3:
            # This approach was ineffective
            approach = intervention.intervention_style.value
            if approach not in user_strategy.approaches_to_avoid:
                user_strategy.approaches_to_avoid.append(approach)

        # Add to support history
        user_strategy.support_history.append(
            {
                "intervention_id": intervention_id,
                "intervention_style": intervention.intervention_style.value,
                "effectiveness_score": outcome.effectiveness_score,
                "outcome_type": outcome.outcome_type,
                "timestamp": outcome.timestamp.isoformat(),
            }
        )

        # Keep only recent history (last 10 interventions)
        user_strategy.support_history = user_strategy.support_history[-10:]

        user_strategy.last_updated = datetime.now(UTC)

    async def get_user_emotional_dashboard(self, user_id: str) -> dict[str, Any]:
        """
        Generate comprehensive emotional dashboard for user

        Args:
            user_id: User identifier

        Returns:
            Comprehensive emotional intelligence dashboard
        """
        logger.debug(f"Generating emotional dashboard for user {user_id}")

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
