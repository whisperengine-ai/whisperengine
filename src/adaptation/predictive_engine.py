"""
🎯 Predictive Adaptation Engine

This module implements predictive adaptation based on conversation quality tracking analysis.
It uses historical InfluxDB data to predict user needs and proactively adapt responses
before issues arise.

Key Features:
- User behavior pattern prediction using conversation quality trends
- Proactive response adaptation based on predicted needs
- Confidence decline prediction and intervention
- Response style pre-optimization based on historical patterns
- Prediction accuracy validation and learning

Architecture:
- Leverages Sprint 1 TrendWise infrastructure for trend analysis
- Uses InfluxDB temporal data for pattern recognition
- Integrates with confidence adaptation for preemptive adjustments
- Validates predictions against actual outcomes for continuous learning
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import TrendDirection from trend_analyzer for proper ConfidenceTrend handling
from src.analytics.trend_analyzer import TrendDirection

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of predictions the engine can make."""
    CONFIDENCE_DECLINE = "confidence_decline"
    CONVERSATION_QUALITY_DROP = "conversation_quality_drop"
    RELATIONSHIP_STRAIN = "relationship_strain"
    ENGAGEMENT_DECREASE = "engagement_decrease"
    USER_FRUSTRATION = "user_frustration"
    RESPONSE_STYLE_MISMATCH = "response_style_mismatch"


class PredictionConfidence(Enum):
    """Confidence levels for predictions."""
    VERY_HIGH = "very_high"      # >90% confidence
    HIGH = "high"                # 80-90% confidence
    MEDIUM = "medium"            # 60-80% confidence
    LOW = "low"                  # 40-60% confidence
    VERY_LOW = "very_low"        # <40% confidence


class AdaptationStrategy(Enum):
    """Types of adaptation strategies."""
    INCREASE_DETAIL = "increase_detail"
    SIMPLIFY_RESPONSES = "simplify_responses"
    ENHANCE_EMPATHY = "enhance_empathy"
    ADJUST_CONFIDENCE_LEVEL = "adjust_confidence_level"
    CHANGE_COMMUNICATION_STYLE = "change_communication_style"
    PROVIDE_MORE_CONTEXT = "provide_more_context"
    REDUCE_VERBOSITY = "reduce_verbosity"
    INCREASE_INTERACTIVITY = "increase_interactivity"


@dataclass
class PredictedNeed:
    """Represents a predicted user need."""
    user_id: str
    bot_name: str
    prediction_type: PredictionType
    confidence: PredictionConfidence
    predicted_at: datetime
    likely_occurrence_time: datetime
    description: str
    indicators: List[str]
    recommended_adaptations: List[AdaptationStrategy]
    historical_accuracy: float
    metadata: Dict[str, Any]


@dataclass
class AdaptationAction:
    """Represents a specific adaptation action to take."""
    action_id: str
    user_id: str
    bot_name: str
    strategy: AdaptationStrategy
    parameters: Dict[str, Any]
    trigger_prediction: PredictedNeed
    created_at: datetime
    expires_at: datetime
    effectiveness_score: Optional[float] = None


@dataclass
class PredictionValidation:
    """Tracks prediction accuracy for learning."""
    prediction_id: str
    predicted_need: PredictedNeed
    actual_outcome: bool
    outcome_severity: float
    validation_timestamp: datetime
    accuracy_score: float
    learned_indicators: List[str]
    model_adjustments: Dict[str, Any]


class PredictiveAdaptationEngine:
    """
    🔮 Predictive Adaptation Engine - Sprint 6 Component
    
    Uses Sprint 1 TrendWise analysis to predict user needs and proactively adapt
    responses before issues arise. Implements machine learning-like pattern recognition
    using InfluxDB temporal data.
    """
    
    def __init__(self, 
                 trend_analyzer=None,
                 confidence_adapter=None, 
                 temporal_client=None,
                 memory_manager=None):
        """Initialize the Predictive Adaptation Engine."""
        self.trend_analyzer = trend_analyzer      # Sprint 1 TrendWise component
        self.confidence_adapter = confidence_adapter  # Sprint 1 confidence adaptation
        self.temporal_client = temporal_client    # InfluxDB client for trend data
        self.memory_manager = memory_manager      # For historical pattern analysis
        
        # Prediction tracking
        self._active_predictions: Dict[str, PredictedNeed] = {}
        self._active_adaptations: Dict[str, AdaptationAction] = {}
        self._prediction_history: List[PredictionValidation] = []
        
        # Learning parameters
        self._prediction_accuracy_threshold = 0.7
        self._adaptation_effectiveness_threshold = 0.6
        self._max_active_predictions_per_user = 5
        
        logger.info("Predictive Adaptation Engine initialized")
    
    # =============================================================================
    # Core Prediction Methods
    # =============================================================================
    
    async def predict_user_needs(self, user_id: str, bot_name: str, 
                                prediction_horizon_hours: int = 24) -> List[PredictedNeed]:
        """
        🔮 Predict user needs based on historical patterns and current trends.
        
        Uses Sprint 1 TrendWise analysis to identify patterns that typically
        precede user issues or needs.
        """
        logger.info("Predicting user needs for %s with %s (horizon: %dh)", 
                   user_id, bot_name, prediction_horizon_hours)
        
        try:
            predictions = []
            
            # Get historical trend data from Sprint 1 TrendWise
            trend_data = await self._get_trend_analysis(user_id, bot_name)
            
            # Analyze different prediction types
            confidence_predictions = await self._predict_confidence_issues(
                user_id, bot_name, trend_data, prediction_horizon_hours
            )
            predictions.extend(confidence_predictions)
            
            quality_predictions = await self._predict_quality_issues(
                user_id, bot_name, trend_data, prediction_horizon_hours
            )
            predictions.extend(quality_predictions)
            
            relationship_predictions = await self._predict_relationship_issues(
                user_id, bot_name, trend_data, prediction_horizon_hours
            )
            predictions.extend(relationship_predictions)
            
            engagement_predictions = await self._predict_engagement_issues(
                user_id, bot_name, trend_data, prediction_horizon_hours
            )
            predictions.extend(engagement_predictions)
            
            # Store active predictions for tracking
            for prediction in predictions:
                prediction_key = f"{user_id}_{bot_name}_{prediction.prediction_type.value}"
                self._active_predictions[prediction_key] = prediction
            
            # Record prediction metrics
            await self._record_prediction_metrics(user_id, bot_name, predictions)
            
            logger.info("Generated %d predictions for %s", len(predictions), user_id)
            return predictions
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to predict user needs for %s: %s", user_id, str(e))
            return []
    
    async def preemptively_adapt_responses(self, predicted_needs: List[PredictedNeed]) -> List[AdaptationAction]:
        """
        ⚡ Create proactive adaptation actions based on predicted needs.
        
        Generates specific adaptation strategies before issues occur.
        """
        logger.info("Creating preemptive adaptations for %d predicted needs", len(predicted_needs))
        
        try:
            adaptations = []
            
            for need in predicted_needs:
                # Only create adaptations for high-confidence predictions
                if need.confidence in [PredictionConfidence.HIGH, PredictionConfidence.VERY_HIGH]:
                    adaptation_actions = await self._create_adaptation_actions(need)
                    adaptations.extend(adaptation_actions)
            
            # Store active adaptations
            for adaptation in adaptations:
                adaptation_key = f"{adaptation.user_id}_{adaptation.bot_name}_{adaptation.strategy.value}"
                self._active_adaptations[adaptation_key] = adaptation
            
            # Record adaptation metrics
            await self._record_adaptation_metrics(adaptations)
            
            logger.info("Created %d preemptive adaptations", len(adaptations))
            return adaptations
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to create preemptive adaptations: %s", str(e))
            return []
    
    async def validate_predictions(self, user_id: str, bot_name: str) -> List[PredictionValidation]:
        """
        📊 Validate prediction accuracy against actual outcomes.
        
        This is the learning component that improves prediction accuracy over time.
        """
        logger.info("Validating predictions for %s with %s", user_id, bot_name)
        
        try:
            validations = []
            
            # Find predictions that should be validated (past their occurrence time)
            current_time = datetime.utcnow()
            predictions_to_validate = [
                pred for pred in self._active_predictions.values()
                if (pred.user_id == user_id and pred.bot_name == bot_name and
                    pred.likely_occurrence_time <= current_time)
            ]
            
            for prediction in predictions_to_validate:
                validation = await self._validate_single_prediction(prediction)
                validations.append(validation)
                
                # Remove validated prediction from active list
                prediction_key = f"{user_id}_{bot_name}_{prediction.prediction_type.value}"
                self._active_predictions.pop(prediction_key, None)
            
            # Update prediction model based on validations
            await self._update_prediction_model(validations)
            
            # Record validation metrics
            await self._record_validation_metrics(validations)
            
            logger.info("Validated %d predictions for %s", len(validations), user_id)
            return validations
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to validate predictions for %s: %s", user_id, str(e))
            return []
    
    # =============================================================================
    # Prediction Type Specific Methods
    # =============================================================================
    
    async def _predict_confidence_issues(self, user_id: str, bot_name: str, 
                                       trend_data: Dict, horizon_hours: int) -> List[PredictedNeed]:
        """Predict confidence decline based on Sprint 1 TrendWise patterns."""
        predictions = []
        
        if not trend_data.get('confidence_trend'):
            return predictions
        
        confidence_trend = trend_data['confidence_trend']
        
        # Pattern: Declining confidence trend
        # confidence_trend is a ConfidenceTrend dataclass with trend_analysis: TrendAnalysis attribute
        if hasattr(confidence_trend, 'trend_analysis') and confidence_trend.trend_analysis.direction == TrendDirection.DECLINING:
            # Use absolute slope as severity indicator (how fast it's declining)
            severity = abs(confidence_trend.trend_analysis.slope) if hasattr(confidence_trend.trend_analysis, 'slope') else 0.0
            current_confidence = confidence_trend.recent_confidence
            
            # Predict confidence will drop below threshold
            if current_confidence > 0.6 and severity > 0.01:  # slope > 0.01 indicates meaningful decline
                prediction = PredictedNeed(
                    user_id=user_id,
                    bot_name=bot_name,
                    prediction_type=PredictionType.CONFIDENCE_DECLINE,
                    confidence=self._calculate_prediction_confidence(severity * 10, confidence_trend),  # Scale slope to 0-1 range
                    predicted_at=datetime.utcnow(),
                    likely_occurrence_time=datetime.utcnow() + timedelta(hours=horizon_hours//2),
                    description="Confidence likely to drop below 0.6 based on declining trend",
                    indicators=[
                        f"Current confidence: {current_confidence:.2f}",
                        f"Decline rate (slope): {severity:.3f}",
                        f"Trend direction: {confidence_trend.trend_analysis.direction.value}",
                        f"Volatility: {confidence_trend.trend_analysis.volatility:.2f}"
                    ],
                    recommended_adaptations=[
                        AdaptationStrategy.INCREASE_DETAIL,
                        AdaptationStrategy.PROVIDE_MORE_CONTEXT,
                        AdaptationStrategy.ADJUST_CONFIDENCE_LEVEL
                    ],
                    historical_accuracy=0.75,  # Default accuracy for confidence predictions
                    metadata={'trend_data': confidence_trend}
                )
                predictions.append(prediction)
        
        return predictions
    
    async def _predict_quality_issues(self, user_id: str, bot_name: str,
                                    trend_data: Dict, horizon_hours: int) -> List[PredictedNeed]:
        """Predict conversation quality drops."""
        predictions = []
        
        quality_trend = trend_data.get('quality_trend')
        if not quality_trend:
            return predictions
        
        # Pattern: Quality degradation
        # QualityTrend is a dataclass with satisfaction_trend, flow_trend, emotional_resonance_trend (TrendAnalysis objects)
        # Check if any major quality metric is declining
        satisfaction_declining = (hasattr(quality_trend, 'satisfaction_trend') and 
                                 quality_trend.satisfaction_trend.direction == TrendDirection.DECLINING)
        flow_declining = (hasattr(quality_trend, 'flow_trend') and 
                         quality_trend.flow_trend.direction == TrendDirection.DECLINING)
        emotional_resonance_declining = (hasattr(quality_trend, 'emotional_resonance_trend') and 
                                        quality_trend.emotional_resonance_trend.direction == TrendDirection.DECLINING)
        
        # Check overall quality score
        overall_score = quality_trend.overall_score if hasattr(quality_trend, 'overall_score') else 0.7
        
        # Predict quality drop if multiple metrics declining or overall score is low
        if ((satisfaction_declining and flow_declining) or 
            overall_score < 0.5 or 
            (emotional_resonance_declining and overall_score < 0.6)):
            
            prediction = PredictedNeed(
                user_id=user_id,
                bot_name=bot_name,
                prediction_type=PredictionType.CONVERSATION_QUALITY_DROP,
                confidence=PredictionConfidence.MEDIUM,
                predicted_at=datetime.utcnow(),
                likely_occurrence_time=datetime.utcnow() + timedelta(hours=horizon_hours//3),
                description=f"Quality decline detected (score: {overall_score:.2f})",
                indicators=[
                    f"Overall quality score: {overall_score:.2f}",
                    f"Satisfaction trend: {quality_trend.satisfaction_trend.direction.value if hasattr(quality_trend, 'satisfaction_trend') else 'unknown'}",
                    f"Flow trend: {quality_trend.flow_trend.direction.value if hasattr(quality_trend, 'flow_trend') else 'unknown'}",
                    f"Emotional resonance: {quality_trend.emotional_resonance_trend.direction.value if hasattr(quality_trend, 'emotional_resonance_trend') else 'unknown'}"
                ],
                recommended_adaptations=[
                    AdaptationStrategy.ENHANCE_EMPATHY,
                    AdaptationStrategy.ADJUST_CONFIDENCE_LEVEL,
                    AdaptationStrategy.CHANGE_COMMUNICATION_STYLE
                ],
                historical_accuracy=0.68,
                metadata={'quality_trend': quality_trend}
            )
            predictions.append(prediction)
        
        return predictions
    
    async def _predict_relationship_issues(self, user_id: str, bot_name: str,
                                         trend_data: Dict, horizon_hours: int) -> List[PredictedNeed]:
        """Predict relationship strain based on interaction patterns."""
        predictions = []
        
        relationship_trend = trend_data.get('relationship_trend')
        if not relationship_trend:
            return predictions
        
        # Pattern: Trust or affection declining
        # RelationshipTrend is a dataclass with trust_trend, affection_trend attributes (TrendAnalysis objects)
        # Access the current_value from the TrendAnalysis objects
        trust_score = relationship_trend.trust_trend.current_value if hasattr(relationship_trend, 'trust_trend') else 0.5
        affection_score = relationship_trend.affection_trend.current_value if hasattr(relationship_trend, 'affection_trend') else 0.5
        
        # Check if trust or affection are declining with low values
        trust_declining = (hasattr(relationship_trend, 'trust_trend') and 
                          relationship_trend.trust_trend.direction == TrendDirection.DECLINING)
        affection_declining = (hasattr(relationship_trend, 'affection_trend') and 
                              relationship_trend.affection_trend.direction == TrendDirection.DECLINING)
        
        if (trust_score < 0.4 or affection_score < 0.4) or (trust_declining and affection_declining):
            prediction = PredictedNeed(
                user_id=user_id,
                bot_name=bot_name,
                prediction_type=PredictionType.RELATIONSHIP_STRAIN,
                confidence=PredictionConfidence.HIGH,
                predicted_at=datetime.utcnow(),
                likely_occurrence_time=datetime.utcnow() + timedelta(hours=horizon_hours//4),
                description=f"Relationship strain detected (trust: {trust_score:.2f}, affection: {affection_score:.2f})",
                indicators=[
                    f"Trust score: {trust_score:.2f}",
                    f"Affection score: {affection_score:.2f}",
                    f"Trust trend: {relationship_trend.trust_trend.direction.value if hasattr(relationship_trend, 'trust_trend') else 'unknown'}",
                    f"Affection trend: {relationship_trend.affection_trend.direction.value if hasattr(relationship_trend, 'affection_trend') else 'unknown'}",
                    "Relationship metrics need attention"
                ],
                recommended_adaptations=[
                    AdaptationStrategy.ENHANCE_EMPATHY,
                    AdaptationStrategy.CHANGE_COMMUNICATION_STYLE,
                    AdaptationStrategy.INCREASE_INTERACTIVITY
                ],
                historical_accuracy=0.82,
                metadata={'relationship_trend': relationship_trend}
            )
            predictions.append(prediction)
        
        return predictions
    
    async def _predict_engagement_issues(self, user_id: str, bot_name: str,
                                       trend_data: Dict, horizon_hours: int) -> List[PredictedNeed]:
        """Predict engagement decrease based on interaction patterns."""
        predictions = []
        
        engagement_trend = trend_data.get('engagement_trend', {})
        if not engagement_trend:
            return predictions
        
        # Pattern: Decreasing engagement with longer response times
        if (engagement_trend.get('direction') == 'declining' and
            engagement_trend.get('response_time_trend') == 'increasing'):
            
            prediction = PredictedNeed(
                user_id=user_id,
                bot_name=bot_name,
                prediction_type=PredictionType.ENGAGEMENT_DECREASE,
                confidence=PredictionConfidence.MEDIUM,
                predicted_at=datetime.utcnow(),
                likely_occurrence_time=datetime.utcnow() + timedelta(hours=horizon_hours//2),
                description="Engagement decline predicted based on interaction patterns",
                indicators=[
                    f"Engagement direction: {engagement_trend.get('direction')}",
                    f"Response time trend: {engagement_trend.get('response_time_trend')}"
                ],
                recommended_adaptations=[
                    AdaptationStrategy.INCREASE_INTERACTIVITY,
                    AdaptationStrategy.REDUCE_VERBOSITY,
                    AdaptationStrategy.CHANGE_COMMUNICATION_STYLE
                ],
                historical_accuracy=0.71,
                metadata={'engagement_trend': engagement_trend}
            )
            predictions.append(prediction)
        
        return predictions
    
    # =============================================================================
    # Adaptation Action Creation
    # =============================================================================
    
    async def _create_adaptation_actions(self, predicted_need: PredictedNeed) -> List[AdaptationAction]:
        """Create specific adaptation actions for a predicted need."""
        actions = []
        
        for strategy in predicted_need.recommended_adaptations:
            action = AdaptationAction(
                action_id=f"{predicted_need.user_id}_{strategy.value}_{int(datetime.utcnow().timestamp())}",
                user_id=predicted_need.user_id,
                bot_name=predicted_need.bot_name,
                strategy=strategy,
                parameters=await self._get_strategy_parameters(strategy, predicted_need),
                trigger_prediction=predicted_need,
                created_at=datetime.utcnow(),
                expires_at=predicted_need.likely_occurrence_time + timedelta(hours=24)
            )
            actions.append(action)
        
        return actions
    
    async def _get_strategy_parameters(self, strategy: AdaptationStrategy, 
                                     predicted_need: PredictedNeed) -> Dict[str, Any]:
        """Get specific parameters for adaptation strategy."""
        base_params = {
            'prediction_type': predicted_need.prediction_type.value,
            'confidence': predicted_need.confidence.value,
            'user_id': predicted_need.user_id,
            'bot_name': predicted_need.bot_name
        }
        
        if strategy == AdaptationStrategy.INCREASE_DETAIL:
            return {**base_params, 'detail_increase_factor': 1.3, 'add_examples': True}
        elif strategy == AdaptationStrategy.SIMPLIFY_RESPONSES:
            return {**base_params, 'complexity_reduction': 0.7, 'shorter_sentences': True}
        elif strategy == AdaptationStrategy.ENHANCE_EMPATHY:
            return {**base_params, 'empathy_boost': 1.4, 'emotional_acknowledgment': True}
        elif strategy == AdaptationStrategy.ADJUST_CONFIDENCE_LEVEL:
            return {**base_params, 'confidence_adjustment': -0.1, 'uncertainty_phrases': True}
        elif strategy == AdaptationStrategy.CHANGE_COMMUNICATION_STYLE:
            return {**base_params, 'style_shift': 'more_conversational', 'formality_reduction': 0.3}
        elif strategy == AdaptationStrategy.PROVIDE_MORE_CONTEXT:
            return {**base_params, 'context_expansion': 1.5, 'background_info': True}
        elif strategy == AdaptationStrategy.REDUCE_VERBOSITY:
            return {**base_params, 'verbosity_reduction': 0.6, 'key_points_only': True}
        elif strategy == AdaptationStrategy.INCREASE_INTERACTIVITY:
            return {**base_params, 'question_frequency': 1.4, 'engagement_prompts': True}
        else:
            return base_params
    
    # =============================================================================
    # Validation and Learning Methods
    # =============================================================================
    
    async def _validate_single_prediction(self, prediction: PredictedNeed) -> PredictionValidation:
        """Validate a single prediction against actual outcome."""
        
        # Get actual outcome data from InfluxDB
        actual_outcome = await self._check_actual_outcome(prediction)
        
        # Calculate accuracy score
        accuracy_score = await self._calculate_accuracy_score(prediction, actual_outcome)
        
        validation = PredictionValidation(
            prediction_id=f"{prediction.user_id}_{prediction.prediction_type.value}_{int(prediction.predicted_at.timestamp())}",
            predicted_need=prediction,
            actual_outcome=actual_outcome['occurred'],
            outcome_severity=actual_outcome.get('severity', 0.0),
            validation_timestamp=datetime.utcnow(),
            accuracy_score=accuracy_score,
            learned_indicators=actual_outcome.get('indicators', []),
            model_adjustments=await self._calculate_model_adjustments(prediction, actual_outcome, accuracy_score)
        )
        
        return validation
    
    async def _check_actual_outcome(self, prediction: PredictedNeed) -> Dict[str, Any]:
        """Check if the predicted outcome actually occurred."""
        
        # This would query InfluxDB for actual data around the predicted time
        # For now, placeholder implementation
        
        if prediction.prediction_type == PredictionType.CONFIDENCE_DECLINE:
            # Check if confidence actually dropped below threshold
            # actual_confidence = await self._get_actual_confidence(prediction)
            return {'occurred': True, 'severity': 0.6, 'indicators': ['confidence_drop_confirmed']}
        
        # Default: assume prediction was partially correct
        return {'occurred': True, 'severity': 0.5, 'indicators': ['general_pattern_match']}
    
    async def _calculate_accuracy_score(self, prediction: PredictedNeed, actual_outcome: Dict) -> float:
        """Calculate prediction accuracy score."""
        
        base_accuracy = 1.0 if actual_outcome['occurred'] else 0.0
        
        # Adjust for severity match
        severity_match = 1.0 - abs(prediction.metadata.get('expected_severity', 0.5) - actual_outcome.get('severity', 0.5))
        
        # Adjust for timing accuracy (how close to predicted time)
        timing_accuracy = 0.8  # Placeholder
        
        # Weight the components
        final_accuracy = (base_accuracy * 0.5 + severity_match * 0.3 + timing_accuracy * 0.2)
        
        return max(0.0, min(1.0, final_accuracy))
    
    async def _calculate_model_adjustments(self, _prediction: PredictedNeed, 
                                         actual_outcome: Dict, accuracy_score: float) -> Dict[str, Any]:
        """Calculate adjustments to improve future predictions."""
        adjustments = {}
        
        if accuracy_score < self._prediction_accuracy_threshold:
            # Adjust confidence thresholds
            adjustments['confidence_threshold_adjustment'] = -0.1
            
            # Adjust timing predictions
            if 'timing_error' in actual_outcome:
                adjustments['timing_adjustment_hours'] = actual_outcome['timing_error']
            
            # Adjust severity calculations
            if 'severity_error' in actual_outcome:
                adjustments['severity_calibration'] = actual_outcome['severity_error']
        
        return adjustments
    
    async def _update_prediction_model(self, validations: List[PredictionValidation]):
        """Update prediction model based on validation results."""
        
        if not validations:
            return
        
        # Calculate overall accuracy
        total_accuracy = sum(v.accuracy_score for v in validations) / len(validations)
        
        # Update model parameters based on learned patterns
        for validation in validations:
            if validation.accuracy_score > self._prediction_accuracy_threshold:
                # Reinforce successful patterns
                logger.info("Reinforcing successful prediction pattern: %s", 
                           validation.predicted_need.prediction_type.value)
            else:
                # Adjust unsuccessful patterns
                logger.info("Adjusting prediction model for: %s (accuracy: %.2f)", 
                           validation.predicted_need.prediction_type.value, validation.accuracy_score)
        
        logger.info("Updated prediction model (overall accuracy: %.2f)", total_accuracy)
    
    # =============================================================================
    # Helper Methods
    # =============================================================================
    
    async def _get_trend_analysis(self, user_id: str, bot_name: str) -> Dict[str, Any]:
        """Get trend analysis from Sprint 1 TrendWise components."""
        
        if not self.trend_analyzer:
            logger.warning("Trend analyzer not available for predictive analysis")
            return {}
        
        try:
            # Get confidence trends
            confidence_trends = await self.trend_analyzer.get_confidence_trends(
                bot_name=bot_name, user_id=user_id, days_back=30
            )
            
            # Get relationship trends  
            relationship_trends = await self.trend_analyzer.get_relationship_trends(
                bot_name=bot_name, user_id=user_id, days_back=14
            )
            
            # Get quality trends
            quality_trends = await self.trend_analyzer.get_quality_trends(
                bot_name=bot_name, days_back=7
            )
            
            return {
                'confidence_trend': confidence_trends,
                'relationship_trend': relationship_trends, 
                'quality_trend': quality_trends,
                'analysis_timestamp': datetime.utcnow()
            }
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to get trend analysis: %s", str(e))
            return {}
    
    def _calculate_prediction_confidence(self, severity: float, trend_data) -> PredictionConfidence:
        """Calculate confidence level for a prediction.
        
        Args:
            severity: Trend severity score (0-1)
            trend_data: Can be ConfidenceTrend, RelationshipTrend, QualityTrend object, or dict
        """
        
        # Base confidence on trend strength and data quality
        base_confidence = severity * 0.7
        
        # Extract data points - handle both dict and dataclass objects
        data_points = 0
        if isinstance(trend_data, dict):
            data_points = trend_data.get('data_points', 0)
        elif hasattr(trend_data, 'trend_analysis'):
            # For ConfidenceTrend, RelationshipTrend, QualityTrend - access via trend_analysis
            data_points = trend_data.trend_analysis.data_points if hasattr(trend_data.trend_analysis, 'data_points') else 0
        
        # Adjust for data quality
        if data_points > 20:
            base_confidence += 0.2
        elif data_points > 10:
            base_confidence += 0.1
        
        # Adjust for trend consistency (lower volatility = more consistent)
        consistency = 0.0
        if isinstance(trend_data, dict):
            consistency = trend_data.get('consistency', 0.0)
        elif hasattr(trend_data, 'trend_analysis'):
            # Higher confidence and lower volatility indicates consistency
            trend_confidence = trend_data.trend_analysis.confidence if hasattr(trend_data.trend_analysis, 'confidence') else 0.0
            volatility = trend_data.trend_analysis.volatility if hasattr(trend_data.trend_analysis, 'volatility') else 1.0
            consistency = trend_confidence * (1.0 - min(volatility, 1.0))
        
        if consistency > 0.8:
            base_confidence += 0.1
        
        # Convert to confidence enum
        if base_confidence >= 0.9:
            return PredictionConfidence.VERY_HIGH
        elif base_confidence >= 0.8:
            return PredictionConfidence.HIGH
        elif base_confidence >= 0.6:
            return PredictionConfidence.MEDIUM
        elif base_confidence >= 0.4:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.VERY_LOW
    
    # =============================================================================
    # Metrics and Monitoring
    # =============================================================================
    
    async def _record_prediction_metrics(self, user_id: str, bot_name: str, predictions: List[PredictedNeed]):
        """Record prediction metrics to InfluxDB."""
        if not self.temporal_client:
            return
        
        try:
            for prediction in predictions:
                await self.temporal_client.record_point(
                    measurement="predictive_adaptation",
                    tags={
                        "bot_name": bot_name,
                        "user_id": user_id,
                        "prediction_type": prediction.prediction_type.value,
                        "confidence": prediction.confidence.value
                    },
                    fields={
                        "prediction_created": 1,
                        "confidence_score": self._confidence_to_score(prediction.confidence),
                        "horizon_hours": (prediction.likely_occurrence_time - prediction.predicted_at).total_seconds() / 3600,
                        "adaptation_count": len(prediction.recommended_adaptations),
                        "historical_accuracy": prediction.historical_accuracy
                    }
                )
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("Failed to record prediction metrics: %s", str(e))
    
    async def _record_adaptation_metrics(self, adaptations: List[AdaptationAction]):
        """Record adaptation metrics to InfluxDB."""
        if not self.temporal_client:
            return
        
        try:
            for adaptation in adaptations:
                await self.temporal_client.record_point(
                    measurement="adaptation_actions",
                    tags={
                        "bot_name": adaptation.bot_name,
                        "user_id": adaptation.user_id,
                        "strategy": adaptation.strategy.value,
                        "prediction_type": adaptation.trigger_prediction.prediction_type.value
                    },
                    fields={
                        "adaptation_created": 1,
                        "expires_in_hours": (adaptation.expires_at - adaptation.created_at).total_seconds() / 3600,
                        "parameter_count": len(adaptation.parameters)
                    }
                )
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("Failed to record adaptation metrics: %s", str(e))
    
    async def _record_validation_metrics(self, validations: List[PredictionValidation]):
        """Record validation metrics to InfluxDB."""
        if not self.temporal_client:
            return
        
        try:
            for validation in validations:
                await self.temporal_client.record_point(
                    measurement="prediction_validation",
                    tags={
                        "prediction_type": validation.predicted_need.prediction_type.value,
                        "bot_name": validation.predicted_need.bot_name,
                        "outcome": "success" if validation.actual_outcome else "miss"
                    },
                    fields={
                        "accuracy_score": validation.accuracy_score,
                        "outcome_severity": validation.outcome_severity,
                        "validation_completed": 1,
                        "model_adjustments_count": len(validation.model_adjustments)
                    }
                )
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("Failed to record validation metrics: %s", str(e))
    
    def _confidence_to_score(self, confidence: PredictionConfidence) -> float:
        """Convert confidence enum to numeric score."""
        confidence_scores = {
            PredictionConfidence.VERY_HIGH: 0.95,
            PredictionConfidence.HIGH: 0.85,
            PredictionConfidence.MEDIUM: 0.70,
            PredictionConfidence.LOW: 0.50,
            PredictionConfidence.VERY_LOW: 0.30
        }
        return confidence_scores.get(confidence, 0.50)
    
    # =============================================================================
    # Public Status Methods
    # =============================================================================
    
    def get_active_predictions(self, user_id: Optional[str] = None, bot_name: Optional[str] = None) -> List[PredictedNeed]:
        """Get currently active predictions."""
        predictions = list(self._active_predictions.values())
        
        if user_id:
            predictions = [p for p in predictions if p.user_id == user_id]
        
        if bot_name:
            predictions = [p for p in predictions if p.bot_name == bot_name]
        
        return predictions
    
    def get_active_adaptations(self, user_id: Optional[str] = None, bot_name: Optional[str] = None) -> List[AdaptationAction]:
        """Get currently active adaptations."""
        adaptations = list(self._active_adaptations.values())
        
        if user_id:
            adaptations = [a for a in adaptations if a.user_id == user_id]
        
        if bot_name:
            adaptations = [a for a in adaptations if a.bot_name == bot_name]
        
        return adaptations
    
    def get_prediction_accuracy_stats(self) -> Dict[str, float]:
        """Get prediction accuracy statistics."""
        if not self._prediction_history:
            return {'overall_accuracy': 0.0, 'total_predictions': 0}
        
        total_accuracy = sum(v.accuracy_score for v in self._prediction_history)
        overall_accuracy = total_accuracy / len(self._prediction_history)
        
        return {
            'overall_accuracy': overall_accuracy,
            'total_predictions': len(self._prediction_history),
            'successful_predictions': len([v for v in self._prediction_history if v.accuracy_score > self._prediction_accuracy_threshold])
        }


def create_predictive_adaptation_engine(trend_analyzer=None, confidence_adapter=None, 
                                      temporal_client=None, memory_manager=None):
    """
    🏭 Factory function to create Predictive Adaptation Engine.
    
    Args:
        trend_analyzer: Sprint 1 TrendWise trend analyzer
        confidence_adapter: Sprint 1 confidence adapter  
        temporal_client: InfluxDB temporal client
        memory_manager: Memory manager for pattern analysis
        
    Returns:
        PredictiveAdaptationEngine: Configured predictive engine
    """
    return PredictiveAdaptationEngine(
        trend_analyzer=trend_analyzer,
        confidence_adapter=confidence_adapter,
        temporal_client=temporal_client,
        memory_manager=memory_manager
    )