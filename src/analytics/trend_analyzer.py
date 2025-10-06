"""
InfluxDB Trend Analyzer - Sprint 1: TrendWise

Analyzes historical trends from InfluxDB to identify patterns in:
- Confidence evolution over time
- Relationship progression trends  
- Conversation quality patterns
- Performance metrics across bots

This is the foundation component that other sprints will leverage for
intelligence-driven adaptation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from statistics import mean, stdev

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction classification"""
    IMPROVING = "improving"
    DECLINING = "declining" 
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class TrendAnalysis:
    """Result of trend analysis"""
    direction: TrendDirection
    slope: float  # Rate of change
    confidence: float  # Confidence in trend detection (0-1)
    current_value: float
    average_value: float
    volatility: float  # Standard deviation
    data_points: int
    time_span_days: int
    

@dataclass
class ConfidenceTrend:
    """Confidence evolution trend data"""
    user_id: str
    bot_name: str
    trend_analysis: TrendAnalysis
    recent_confidence: float
    historical_average: float
    critical_threshold: float = 0.6
    needs_adaptation: bool = False


@dataclass
class RelationshipTrend:
    """Relationship progression trend data"""
    user_id: str
    bot_name: str
    trust_trend: TrendAnalysis
    affection_trend: TrendAnalysis
    attunement_trend: TrendAnalysis
    overall_direction: TrendDirection
    needs_attention: bool = False


@dataclass
class QualityTrend:
    """Conversation quality trend data"""
    bot_name: str
    satisfaction_trend: TrendAnalysis
    flow_trend: TrendAnalysis
    emotional_resonance_trend: TrendAnalysis
    overall_score: float
    needs_optimization: bool = False


class InfluxDBTrendAnalyzer:
    """
    Core trend analysis engine for InfluxDB historical data.
    
    Analyzes patterns in confidence, relationships, and quality metrics
    to provide insights for adaptive behavior systems.
    """
    
    def __init__(self, temporal_client=None):
        """
        Initialize trend analyzer.
        
        Args:
            temporal_client: TemporalIntelligenceClient instance
        """
        self.temporal_client = temporal_client
        self.logger = logger
        
        # Trend detection parameters
        self.min_data_points = 5  # Minimum points needed for trend analysis
        self.volatility_threshold = 0.15  # Threshold for volatile classification
        self.trend_confidence_threshold = 0.7  # Minimum confidence for trend detection
        
    async def get_confidence_trends(
        self, 
        bot_name: str, 
        user_id: str, 
        days_back: int = 30
    ) -> Optional[ConfidenceTrend]:
        """
        Analyze confidence evolution trends for a specific user-bot pair.
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier  
            days_back: Number of days to analyze
            
        Returns:
            ConfidenceTrend object with analysis results
        """
        if not self.temporal_client:
            self.logger.warning("No temporal client available for confidence trend analysis")
            return None
            
        try:
            # Get confidence data from InfluxDB
            confidence_data = await self.temporal_client.get_confidence_trends(
                bot_name=bot_name,
                user_id=user_id, 
                days_back=days_back
            )
            
            if not confidence_data or len(confidence_data) < self.min_data_points:
                self.logger.debug(f"Insufficient confidence data for {bot_name}/{user_id}")
                return None
                
            # Extract confidence values and timestamps
            values = [point.get('confidence', 0.0) for point in confidence_data]
            timestamps = [point.get('timestamp') for point in confidence_data]
            
            # Perform trend analysis
            trend_analysis = self._analyze_trend(values, timestamps, days_back)
            
            # Calculate recent vs historical averages
            recent_window = min(7, len(values) // 3)  # Last week or 1/3 of data
            recent_confidence = mean(values[-recent_window:]) if recent_window > 0 else values[-1]
            historical_average = mean(values)
            
            # Determine if adaptation is needed
            needs_adaptation = (
                recent_confidence < 0.6 or  # Below critical threshold
                trend_analysis.direction == TrendDirection.DECLINING or
                trend_analysis.volatility > self.volatility_threshold
            )
            
            return ConfidenceTrend(
                user_id=user_id,
                bot_name=bot_name,
                trend_analysis=trend_analysis,
                recent_confidence=recent_confidence,
                historical_average=historical_average,
                needs_adaptation=needs_adaptation
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze confidence trends: {e}")
            return None
    
    async def get_relationship_trends(
        self,
        bot_name: str,
        user_id: str,
        days_back: int = 14
    ) -> Optional[RelationshipTrend]:
        """
        Analyze relationship progression trends for a user-bot pair.
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            days_back: Number of days to analyze
            
        Returns:
            RelationshipTrend object with analysis results
        """
        if not self.temporal_client:
            self.logger.warning("No temporal client available for relationship trend analysis")
            return None
            
        try:
            # Get relationship data from InfluxDB
            relationship_data = await self.temporal_client.get_relationship_evolution(
                bot_name=bot_name,
                user_id=user_id,
                days_back=days_back
            )
            
            if not relationship_data or len(relationship_data) < self.min_data_points:
                self.logger.debug(f"Insufficient relationship data for {bot_name}/{user_id}")
                return None
                
            # Extract trend data for each relationship metric
            timestamps = [point.get('timestamp') for point in relationship_data]
            
            trust_values = [point.get('trust_level', 0.0) for point in relationship_data]
            affection_values = [point.get('affection_level', 0.0) for point in relationship_data]  
            attunement_values = [point.get('attunement_level', 0.0) for point in relationship_data]
            
            # Analyze trends for each metric
            trust_trend = self._analyze_trend(trust_values, timestamps, days_back)
            affection_trend = self._analyze_trend(affection_values, timestamps, days_back)
            attunement_trend = self._analyze_trend(attunement_values, timestamps, days_back)
            
            # Determine overall relationship direction
            declining_count = sum(1 for trend in [trust_trend, affection_trend, attunement_trend] 
                                if trend.direction == TrendDirection.DECLINING)
            improving_count = sum(1 for trend in [trust_trend, affection_trend, attunement_trend]
                                if trend.direction == TrendDirection.IMPROVING)
            
            if declining_count >= 2:
                overall_direction = TrendDirection.DECLINING
            elif improving_count >= 2:  
                overall_direction = TrendDirection.IMPROVING
            else:
                overall_direction = TrendDirection.STABLE
                
            # Check if relationship needs attention
            needs_attention = (
                overall_direction == TrendDirection.DECLINING or
                any(trend.current_value < 40 for trend in [trust_trend, affection_trend, attunement_trend])
            )
            
            return RelationshipTrend(
                user_id=user_id,
                bot_name=bot_name,
                trust_trend=trust_trend,
                affection_trend=affection_trend,
                attunement_trend=attunement_trend,
                overall_direction=overall_direction,
                needs_attention=needs_attention
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze relationship trends: {e}")
            return None
    
    async def get_quality_trends(
        self,
        bot_name: str, 
        days_back: int = 7
    ) -> Optional[QualityTrend]:
        """
        Analyze conversation quality trends across all users for a bot.
        
        Args:
            bot_name: Name of the bot
            days_back: Number of days to analyze
            
        Returns:
            QualityTrend object with analysis results
        """
        if not self.temporal_client:
            self.logger.warning("No temporal client available for quality trend analysis")
            return None
            
        try:
            # Get quality data from InfluxDB (would need to implement this method)
            # For now, we'll simulate the interface
            quality_data = await self._get_quality_data(bot_name, days_back)
            
            if not quality_data or len(quality_data) < self.min_data_points:
                self.logger.debug(f"Insufficient quality data for {bot_name}")
                return None
                
            # Extract quality metrics
            timestamps = [point.get('timestamp') for point in quality_data]
            satisfaction_values = [point.get('satisfaction_score', 0.0) for point in quality_data]
            flow_values = [point.get('natural_flow_score', 0.0) for point in quality_data]
            resonance_values = [point.get('emotional_resonance', 0.0) for point in quality_data]
            
            # Analyze trends for each quality metric
            satisfaction_trend = self._analyze_trend(satisfaction_values, timestamps, days_back)
            flow_trend = self._analyze_trend(flow_values, timestamps, days_back)
            resonance_trend = self._analyze_trend(resonance_values, timestamps, days_back)
            
            # Calculate overall quality score
            overall_score = mean([
                satisfaction_trend.current_value,
                flow_trend.current_value,
                resonance_trend.current_value
            ])
            
            # Check if optimization is needed
            needs_optimization = (
                overall_score < 0.7 or
                any(trend.direction == TrendDirection.DECLINING 
                    for trend in [satisfaction_trend, flow_trend, resonance_trend])
            )
            
            return QualityTrend(
                bot_name=bot_name,
                satisfaction_trend=satisfaction_trend,
                flow_trend=flow_trend,
                emotional_resonance_trend=resonance_trend,
                overall_score=overall_score,
                needs_optimization=needs_optimization
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze quality trends: {e}")
            return None
    
    def _analyze_trend(
        self, 
        values: List[float], 
        timestamps: List[datetime], 
        time_span_days: int
    ) -> TrendAnalysis:
        """
        Analyze trend in a series of values.
        
        Args:
            values: List of numeric values
            timestamps: Corresponding timestamps
            time_span_days: Time span of the data
            
        Returns:
            TrendAnalysis object
        """
        if len(values) < 2:
            return TrendAnalysis(
                direction=TrendDirection.STABLE,
                slope=0.0,
                confidence=0.0,
                current_value=values[0] if values else 0.0,
                average_value=values[0] if values else 0.0,
                volatility=0.0,
                data_points=len(values),
                time_span_days=time_span_days
            )
        
        # Calculate basic statistics
        current_value = values[-1]
        average_value = mean(values)
        volatility = stdev(values) if len(values) > 1 else 0.0
        
        # Calculate trend slope using linear regression
        x = list(range(len(values)))
        slope = self._calculate_slope(x, values)
        
        # Determine trend direction based on slope significance first
        # Only classify as volatile if slope is insignificant AND volatility is high
        if abs(slope) < 0.001:  # Very small slope
            direction = TrendDirection.STABLE
        elif abs(slope) < 0.01 and volatility > self.volatility_threshold:
            # Only volatile if both slope is weak AND volatility is high
            direction = TrendDirection.VOLATILE
        elif slope > 0:
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.DECLINING
            
        # Calculate confidence in trend detection
        confidence = self._calculate_trend_confidence(values, slope, volatility)
        
        return TrendAnalysis(
            direction=direction,
            slope=slope,
            confidence=confidence,
            current_value=current_value,
            average_value=average_value,
            volatility=volatility,
            data_points=len(values),
            time_span_days=time_span_days
        )
    
    def _calculate_slope(self, x: List[int], y: List[float]) -> float:
        """Calculate linear regression slope."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
            
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x_squared = sum(x_val ** 2 for x_val in x)
        
        denominator = n * sum_x_squared - sum_x ** 2
        if denominator == 0:
            return 0.0
            
        return (n * sum_xy - sum_x * sum_y) / denominator
    
    def _calculate_trend_confidence(
        self, 
        values: List[float], 
        slope: float, 
        volatility: float
    ) -> float:
        """
        Calculate confidence in trend detection.
        
        Higher confidence for:
        - More data points
        - Lower volatility  
        - Stronger slope
        """
        if len(values) < self.min_data_points:
            return 0.0
            
        # Base confidence from data point count
        data_confidence = min(1.0, len(values) / 20.0)  # Full confidence at 20+ points
        
        # Volatility penalty
        volatility_confidence = max(0.0, 1.0 - (volatility / 0.3))  # Penalty for high volatility
        
        # Slope strength bonus
        slope_confidence = min(1.0, abs(slope) * 10)  # Bonus for strong trends
        
        # Combined confidence
        confidence = (data_confidence + volatility_confidence + slope_confidence) / 3
        return max(0.0, min(1.0, confidence))
    
    async def _get_quality_data(self, bot_name: str, days_back: int) -> List[Dict[str, Any]]:
        """
        Get conversation quality data from InfluxDB.
        
        NOTE: This is a placeholder - needs to be implemented based on
        actual InfluxDB schema for conversation_quality measurements.
        """
        # TODO: Implement actual InfluxDB query for conversation quality
        # This would query the conversation_quality measurement table
        
        # For now, return empty list - this will be implemented when
        # the temporal client has the get_quality_data method
        self.logger.debug(f"Quality data retrieval not yet implemented for {bot_name}")
        return []
    
    async def calculate_trend_direction(self, data_points: List[float]) -> str:
        """
        Public method to calculate trend direction from data points.
        
        Args:
            data_points: List of numeric values
            
        Returns:
            Trend direction string: 'improving', 'declining', 'stable', 'volatile'
        """
        if len(data_points) < 2:
            return TrendDirection.STABLE.value
            
        trend_analysis = self._analyze_trend(
            values=data_points,
            timestamps=[datetime.now() - timedelta(days=i) for i in range(len(data_points))],
            time_span_days=len(data_points)
        )
        
        return trend_analysis.direction.value


# Factory function for easy integration
def create_trend_analyzer(temporal_client=None) -> InfluxDBTrendAnalyzer:
    """Create and return trend analyzer instance."""
    return InfluxDBTrendAnalyzer(temporal_client=temporal_client)