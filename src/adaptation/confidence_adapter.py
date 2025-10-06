"""
Confidence Adapter - Sprint 1: TrendWise

Adapts bot response style based on confidence trend analysis.
When confidence is declining or below thresholds, adjusts:
- Response detail level
- Uncertainty acknowledgment
- Explanation depth
- Validation seeking behavior

This is the first adaptive component that demonstrates how InfluxDB
analytics can drive real-time behavior modifications.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ResponseStyle(Enum):
    """Response style adaptation modes"""
    STANDARD = "standard"
    MORE_DETAILED = "more_detailed"
    MORE_CAREFUL = "more_careful"
    CONFIDENCE_BUILDING = "confidence_building"
    UNCERTAINTY_ACKNOWLEDGMENT = "uncertainty_acknowledgment"


class ExplanationLevel(Enum):
    """Explanation depth levels"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class AdaptationParameters:
    """Parameters for response adaptation"""
    response_style: ResponseStyle
    explanation_level: ExplanationLevel
    uncertainty_acknowledgment: bool
    validation_seeking: bool
    clarification_frequency: str  # 'low', 'medium', 'high'
    detail_enhancement: float  # Multiplier for response detail (0.5-2.0)
    confidence_threshold: float  # Threshold for triggering adaptations
    adaptation_reason: str  # Human-readable reason for adaptation


@dataclass 
class AdaptationGuidance:
    """Guidance for message processor integration"""
    system_prompt_additions: List[str]
    response_modifiers: Dict[str, Any]
    behavior_adjustments: Dict[str, Any]
    monitoring_flags: Dict[str, bool]


class ConfidenceAdapter:
    """
    Adapts bot response style based on confidence trend analysis.
    
    Provides adaptive guidance that can be integrated into the message
    processing pipeline to modify responses in real-time.
    """
    
    def __init__(self, trend_analyzer=None):
        """
        Initialize confidence adapter.
        
        Args:
            trend_analyzer: InfluxDBTrendAnalyzer instance
        """
        self.trend_analyzer = trend_analyzer
        self.logger = logger
        
        # Adaptation thresholds
        self.critical_confidence_threshold = 0.6
        self.declining_trend_threshold = -0.05  # Negative slope threshold
        self.volatility_threshold = 0.15
        
        # Cache for adaptation parameters to avoid repeated calculations
        self._adaptation_cache = {}
        self._cache_duration_minutes = 10
    
    async def adjust_response_style(
        self, 
        user_id: str, 
        bot_name: str
    ) -> Optional[AdaptationParameters]:
        """
        Generate response style adjustments based on confidence trends.
        
        Args:
            user_id: User identifier
            bot_name: Bot name
            
        Returns:
            AdaptationParameters object with adjustment recommendations
        """
        try:
            # Check cache first
            cache_key = f"{bot_name}:{user_id}"
            if cache_key in self._adaptation_cache:
                cached_params, timestamp = self._adaptation_cache[cache_key]
                if self._is_cache_valid(timestamp):
                    self.logger.debug("Using cached adaptation parameters for %s", cache_key)
                    return cached_params
            
            # Get confidence trends
            if not self.trend_analyzer:
                self.logger.warning("No trend analyzer available for confidence adaptation")
                return None
                
            confidence_trend = await self.trend_analyzer.get_confidence_trends(
                bot_name=bot_name,
                user_id=user_id,
                days_back=30
            )
            
            if not confidence_trend:
                self.logger.debug("No confidence trend data available for %s/%s", bot_name, user_id)
                return None
            
            # Calculate adaptation parameters
            adaptation_params = self._calculate_adaptation_parameters(confidence_trend)
            
            # Cache the results
            self._adaptation_cache[cache_key] = (adaptation_params, datetime.now())
            
            self.logger.info(
                "Generated adaptation parameters for %s/%s: %s (reason: %s)",
                bot_name, user_id, adaptation_params.response_style.value, 
                adaptation_params.adaptation_reason
            )
            
            return adaptation_params
            
        except Exception as e:
            self.logger.error("Failed to adjust response style for %s/%s: %s", bot_name, user_id, e)
            return None
    
    def _calculate_adaptation_parameters(
        self, 
        confidence_trend
    ) -> AdaptationParameters:
        """
        Calculate specific adaptation parameters based on confidence trend.
        
        Args:
            confidence_trend: ConfidenceTrend object
            
        Returns:
            AdaptationParameters with specific adjustments
        """
        trend_analysis = confidence_trend.trend_analysis
        recent_confidence = confidence_trend.recent_confidence
        
        # Determine primary adaptation strategy
        if recent_confidence < self.critical_confidence_threshold:
            # Critical: Low confidence requires detailed, careful responses
            return AdaptationParameters(
                response_style=ResponseStyle.MORE_DETAILED,
                explanation_level=ExplanationLevel.COMPREHENSIVE,
                uncertainty_acknowledgment=True,
                validation_seeking=True,
                clarification_frequency='high',
                detail_enhancement=1.5,
                confidence_threshold=recent_confidence,
                adaptation_reason=f"Low confidence ({recent_confidence:.2f} < {self.critical_confidence_threshold})"
            )
            
        elif trend_analysis.direction.value == 'declining':
            # Declining: Becoming more careful and seeking validation
            return AdaptationParameters(
                response_style=ResponseStyle.MORE_CAREFUL,
                explanation_level=ExplanationLevel.DETAILED,
                uncertainty_acknowledgment=True,
                validation_seeking=True,
                clarification_frequency='medium',
                detail_enhancement=1.3,
                confidence_threshold=recent_confidence,
                adaptation_reason=f"Declining confidence trend (slope: {trend_analysis.slope:.3f})"
            )
            
        elif trend_analysis.direction.value == 'volatile':
            # Volatile: Inconsistent performance requires stability measures
            return AdaptationParameters(
                response_style=ResponseStyle.CONFIDENCE_BUILDING,
                explanation_level=ExplanationLevel.DETAILED,
                uncertainty_acknowledgment=False,
                validation_seeking=False,
                clarification_frequency='low',
                detail_enhancement=1.2,
                confidence_threshold=recent_confidence,
                adaptation_reason=f"Volatile confidence (volatility: {trend_analysis.volatility:.3f})"
            )
            
        elif recent_confidence > 0.8 and trend_analysis.direction.value == 'improving':
            # High confidence: Can be more concise and confident
            return AdaptationParameters(
                response_style=ResponseStyle.STANDARD,
                explanation_level=ExplanationLevel.STANDARD,
                uncertainty_acknowledgment=False,
                validation_seeking=False,
                clarification_frequency='low',
                detail_enhancement=0.9,
                confidence_threshold=recent_confidence,
                adaptation_reason=f"High stable confidence ({recent_confidence:.2f})"
            )
            
        else:
            # Default: Standard approach
            return AdaptationParameters(
                response_style=ResponseStyle.STANDARD,
                explanation_level=ExplanationLevel.STANDARD,
                uncertainty_acknowledgment=False,
                validation_seeking=False,
                clarification_frequency='medium',
                detail_enhancement=1.0,
                confidence_threshold=recent_confidence,
                adaptation_reason="Standard confidence level"
            )
    
    def generate_adaptation_guidance(
        self, 
        adaptation_params: AdaptationParameters
    ) -> AdaptationGuidance:
        """
        Generate specific guidance for message processor integration.
        
        Args:
            adaptation_params: AdaptationParameters object
            
        Returns:
            AdaptationGuidance with specific integration instructions
        """
        system_prompt_additions = []
        response_modifiers = {}
        behavior_adjustments = {}
        monitoring_flags = {}
        
        # System prompt modifications based on response style
        if adaptation_params.response_style == ResponseStyle.MORE_DETAILED:
            system_prompt_additions.append(
                "Provide more comprehensive explanations with additional context and examples. "
                "Break down complex topics into clear, manageable steps."
            )
            response_modifiers['target_length_multiplier'] = adaptation_params.detail_enhancement
            
        elif adaptation_params.response_style == ResponseStyle.MORE_CAREFUL:
            system_prompt_additions.append(
                "Be more cautious and measured in responses. Acknowledge when you're uncertain "
                "and provide qualified statements rather than absolute claims."
            )
            behavior_adjustments['uncertainty_phrases'] = True
            
        elif adaptation_params.response_style == ResponseStyle.CONFIDENCE_BUILDING:
            system_prompt_additions.append(
                "Focus on providing clear, consistent responses that build user confidence. "
                "Avoid contradictory statements and maintain a steady, reliable tone."
            )
            behavior_adjustments['consistency_check'] = True
        
        # Explanation level adjustments
        if adaptation_params.explanation_level == ExplanationLevel.COMPREHENSIVE:
            system_prompt_additions.append(
                "Include detailed explanations of reasoning and provide background context "
                "to help the user understand your responses."
            )
            response_modifiers['explanation_depth'] = 'comprehensive'
            
        elif adaptation_params.explanation_level == ExplanationLevel.DETAILED:
            system_prompt_additions.append(
                "Provide clear explanations for your responses and reasoning."
            )
            response_modifiers['explanation_depth'] = 'detailed'
        
        # Uncertainty acknowledgment
        if adaptation_params.uncertainty_acknowledgment:
            system_prompt_additions.append(
                "When uncertain about information, explicitly acknowledge this uncertainty "
                "and suggest ways to verify or get more reliable information."
            )
            behavior_adjustments['acknowledge_uncertainty'] = True
        
        # Validation seeking
        if adaptation_params.validation_seeking:
            system_prompt_additions.append(
                "Periodically ask for feedback on whether your responses are helpful "
                "and encourage the user to correct any misunderstandings."
            )
            behavior_adjustments['seek_validation'] = True
        
        # Clarification frequency
        if adaptation_params.clarification_frequency == 'high':
            system_prompt_additions.append(
                "Frequently ask clarifying questions to ensure you understand the user's needs correctly."
            )
            behavior_adjustments['clarification_rate'] = 'high'
        
        # Monitoring flags
        monitoring_flags['track_adaptation_effectiveness'] = True
        monitoring_flags['confidence_threshold'] = adaptation_params.confidence_threshold
        monitoring_flags['adaptation_reason'] = adaptation_params.adaptation_reason
        
        return AdaptationGuidance(
            system_prompt_additions=system_prompt_additions,
            response_modifiers=response_modifiers,
            behavior_adjustments=behavior_adjustments,
            monitoring_flags=monitoring_flags
        )
    
    def _is_cache_valid(self, timestamp) -> bool:
        """Check if cached adaptation parameters are still valid."""
        return datetime.now() - timestamp < timedelta(minutes=self._cache_duration_minutes)
    
    async def record_adaptation_effectiveness(
        self, 
        user_id: str, 
        bot_name: str, 
        adaptation_params: AdaptationParameters,
        conversation_quality_score: float
    ):
        """
        Record the effectiveness of adaptation for learning purposes.
        
        Args:
            user_id: User identifier
            bot_name: Bot name  
            adaptation_params: Applied adaptation parameters
            conversation_quality_score: Resulting conversation quality (0-1)
        """
        try:
            # Record adaptation effectiveness metrics
            # This could be stored back to InfluxDB for future analysis
            self.logger.info(
                "Adaptation effectiveness - User: %s, Bot: %s, Style: %s, Quality: %.3f",
                user_id, bot_name, adaptation_params.response_style.value, conversation_quality_score
            )
            
            # TODO: Store adaptation effectiveness metrics in InfluxDB
            # This would create a feedback loop for improving adaptations
            
        except Exception as e:
            self.logger.error("Failed to record adaptation effectiveness: %s", e)


# Factory function for easy integration
def create_confidence_adapter(trend_analyzer=None) -> ConfidenceAdapter:
    """Create and return confidence adapter instance.""" 
    return ConfidenceAdapter(trend_analyzer=trend_analyzer)