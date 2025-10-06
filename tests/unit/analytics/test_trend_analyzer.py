"""
Unit Tests for InfluxDB Trend Analyzer - Sprint 1: TrendWise

Tests the core trend analysis functionality including:
- Confidence trend analysis
- Relationship trend analysis  
- Quality trend analysis
- Trend direction calculation
- Statistical analysis methods
"""

import unittest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import asyncio

# Import the components we're testing
from src.analytics.trend_analyzer import (
    InfluxDBTrendAnalyzer,
    TrendDirection,
    TrendAnalysis,
    ConfidenceTrend,
    RelationshipTrend,
    create_trend_analyzer
)


class TestInfluxDBTrendAnalyzer(unittest.IsolatedAsyncioTestCase):
    """Test cases for InfluxDB Trend Analyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_temporal_client = Mock()
        self.analyzer = InfluxDBTrendAnalyzer(self.mock_temporal_client)
        
        # Sample test data
        self.sample_confidence_data = [
            {'confidence': 0.8, 'timestamp': datetime.now() - timedelta(days=i)}
            for i in range(20, 0, -1)
        ]
        
        self.sample_relationship_data = [
            {
                'trust_level': 70.0 + i,
                'affection_level': 65.0 + i,
                'attunement_level': 75.0 + i,
                'timestamp': datetime.now() - timedelta(days=i)
            }
            for i in range(10, 0, -1)
        ]
    
    async def test_get_confidence_trends_success(self):
        """Test successful confidence trend analysis"""
        # Mock temporal client response
        self.mock_temporal_client.get_confidence_trends = AsyncMock(
            return_value=self.sample_confidence_data
        )
        
        # Test the method
        result = await self.analyzer.get_confidence_trends("elena", "user123", 30)
        
        # Assertions
        self.assertIsNotNone(result)
        if result:  # Type guard for mypy
            self.assertIsInstance(result, ConfidenceTrend)
            self.assertEqual(result.user_id, "user123")
            self.assertEqual(result.bot_name, "elena")
            self.assertIsInstance(result.trend_analysis, TrendAnalysis)
            self.assertGreater(result.recent_confidence, 0)
            self.assertGreater(result.historical_average, 0)
    
    async def test_get_confidence_trends_insufficient_data(self):
        """Test handling of insufficient data"""
        # Mock insufficient data
        self.mock_temporal_client.get_confidence_trends = AsyncMock(
            return_value=[{'confidence': 0.5, 'timestamp': datetime.now()}]
        )
        
        result = await self.analyzer.get_confidence_trends("elena", "user123", 30)
        
        # Should return None for insufficient data
        self.assertIsNone(result)
    
    async def test_get_relationship_trends_success(self):
        """Test successful relationship trend analysis"""
        self.mock_temporal_client.get_relationship_evolution = AsyncMock(
            return_value=self.sample_relationship_data
        )
        
        result = await self.analyzer.get_relationship_trends("elena", "user123", 14)
        
        self.assertIsNotNone(result)
        if result:  # Type guard for mypy
            self.assertIsInstance(result, RelationshipTrend)
            self.assertEqual(result.user_id, "user123")
            self.assertEqual(result.bot_name, "elena")
            self.assertIsInstance(result.trust_trend, TrendAnalysis)
            self.assertIsInstance(result.affection_trend, TrendAnalysis)
            self.assertIsInstance(result.attunement_trend, TrendAnalysis)
    
    def test_calculate_trend_direction(self):
        """Test trend direction calculation using public interface"""
        # Test improving trend
        improving_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        result = asyncio.run(self.analyzer.calculate_trend_direction(improving_data))
        self.assertEqual(result, "improving")
        
        # Test declining trend
        declining_data = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
        result = asyncio.run(self.analyzer.calculate_trend_direction(declining_data))
        self.assertEqual(result, "declining")
        
        # Test stable trend
        stable_data = [0.5, 0.51, 0.49, 0.5, 0.52, 0.48, 0.5, 0.51]
        result = asyncio.run(self.analyzer.calculate_trend_direction(stable_data))
        self.assertEqual(result, "stable")
    
    async def test_integration_with_mock_data(self):
        """Test full integration with properly mocked data"""
        # Create realistic confidence data with improving trend
        confidence_data = [
            {'confidence': 0.5 + (i * 0.02), 'timestamp': datetime.now() - timedelta(days=20-i)}
            for i in range(20)
        ]
        
        self.mock_temporal_client.get_confidence_trends = AsyncMock(
            return_value=confidence_data
        )
        
        result = await self.analyzer.get_confidence_trends("elena", "user123", 30)
        
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(result.user_id, "user123")
            self.assertEqual(result.bot_name, "elena")
            self.assertIsInstance(result.trend_analysis, TrendAnalysis)
            # Should detect improving trend
            self.assertEqual(result.trend_analysis.direction, TrendDirection.IMPROVING)
    
    def test_no_temporal_client(self):
        """Test behavior when no temporal client is available"""
        analyzer_no_client = InfluxDBTrendAnalyzer(None)
        
        result = asyncio.run(analyzer_no_client.get_confidence_trends("elena", "user123", 30))
        self.assertIsNone(result)
    
    def test_factory_function(self):
        """Test factory function"""
        analyzer = create_trend_analyzer(self.mock_temporal_client)
        self.assertIsInstance(analyzer, InfluxDBTrendAnalyzer)
        self.assertEqual(analyzer.temporal_client, self.mock_temporal_client)


class TestTrendAnalysisDataClasses(unittest.TestCase):
    """Test the data classes used for trend analysis"""
    
    def test_trend_analysis_creation(self):
        """Test TrendAnalysis data class"""
        analysis = TrendAnalysis(
            direction=TrendDirection.IMPROVING,
            slope=0.1,
            confidence=0.8,
            current_value=0.7,
            average_value=0.6,
            volatility=0.05,
            data_points=20,
            time_span_days=30
        )
        
        self.assertEqual(analysis.direction, TrendDirection.IMPROVING)
        self.assertEqual(analysis.slope, 0.1)
        self.assertEqual(analysis.confidence, 0.8)
    
    def test_confidence_trend_creation(self):
        """Test ConfidenceTrend data class"""
        trend_analysis = TrendAnalysis(
            direction=TrendDirection.DECLINING,
            slope=-0.05,
            confidence=0.9,
            current_value=0.5,
            average_value=0.7,
            volatility=0.1,
            data_points=15,
            time_span_days=30
        )
        
        confidence_trend = ConfidenceTrend(
            user_id="user123",
            bot_name="elena",
            trend_analysis=trend_analysis,
            recent_confidence=0.5,
            historical_average=0.7,
            needs_adaptation=True
        )
        
        self.assertEqual(confidence_trend.user_id, "user123")
        self.assertEqual(confidence_trend.bot_name, "elena")
        self.assertTrue(confidence_trend.needs_adaptation)


if __name__ == '__main__':
    unittest.main()