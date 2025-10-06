"""
Unit Tests for Confidence Adapter - Sprint 1: TrendWise

Tests the response style adaptation functionality including:
- Adaptation parameter calculation
- Response style guidance generation
- Confidence-based adjustments
- Integration with trend analysis
"""

import unittest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import asyncio

# Import the components we're testing
from src.adaptation.confidence_adapter import (
    ConfidenceAdapter,
    AdaptationParameters,
    ResponseStyle,
    ExplanationLevel,
    create_confidence_adapter
)
from src.analytics.trend_analyzer import (
    ConfidenceTrend,
    TrendAnalysis,
    TrendDirection
)


class TestConfidenceAdapter(unittest.IsolatedAsyncioTestCase):
    """Test cases for Confidence Adapter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_trend_analyzer = Mock()
        self.adapter = ConfidenceAdapter(self.mock_trend_analyzer)
        
        # Sample trend data for testing
        self.improving_trend = ConfidenceTrend(
            user_id="user123",
            bot_name="elena",
            trend_analysis=TrendAnalysis(
                direction=TrendDirection.IMPROVING,
                slope=0.05,
                confidence=0.8,
                current_value=0.7,
                average_value=0.6,
                volatility=0.1,
                data_points=15,
                time_span_days=30
            ),
            recent_confidence=0.7,
            historical_average=0.6,
            needs_adaptation=False
        )
        
        self.declining_trend = ConfidenceTrend(
            user_id="user123",
            bot_name="elena",
            trend_analysis=TrendAnalysis(
                direction=TrendDirection.DECLINING,
                slope=-0.08,
                confidence=0.9,
                current_value=0.4,
                average_value=0.7,
                volatility=0.15,
                data_points=20,
                time_span_days=30
            ),
            recent_confidence=0.4,
            historical_average=0.7,
            needs_adaptation=True
        )
    
    async def test_adjust_response_style_improving(self):
        """Test response style adjustment for improving confidence trend"""
        # Mock trend analyzer
        self.mock_trend_analyzer.get_confidence_trends = AsyncMock(
            return_value=self.improving_trend
        )
        
        # Test the method
        result = await self.adapter.adjust_response_style("user123", "elena")
        
        # Assertions
        self.assertIsNotNone(result)
        if result:
            self.assertIsInstance(result, AdaptationParameters)
            self.assertIsInstance(result.response_style, ResponseStyle)
            self.assertIsInstance(result.explanation_level, ExplanationLevel)
    
    async def test_adjust_response_style_declining(self):
        """Test response style adjustment for declining confidence trend"""
        # Mock trend analyzer
        self.mock_trend_analyzer.get_confidence_trends = AsyncMock(
            return_value=self.declining_trend
        )
        
        # Test the method
        result = await self.adapter.adjust_response_style("user123", "elena")
        
        # Assertions
        self.assertIsNotNone(result)
        if result:
            self.assertIsInstance(result, AdaptationParameters)
            # Should indicate adaptation is needed for declining trends
            self.assertTrue(result.uncertainty_acknowledgment or 
                          result.validation_seeking or 
                          result.detail_enhancement > 1.0)
    
    async def test_get_adaptation_guidance_low_confidence(self):
        """Test adaptation guidance generation for low confidence"""
        # Mock trend analyzer
        self.mock_trend_analyzer.get_confidence_trends = AsyncMock(
            return_value=self.declining_trend
        )
        
        # Test the method using adjust_response_style which is the main public interface
        result = await self.adapter.adjust_response_style("user123", "elena")
        
        # Assertions
        self.assertIsNotNone(result)
        if result:
            self.assertIsInstance(result, AdaptationParameters)
            self.assertTrue(result.needs_adaptation)
    
    async def test_get_adaptation_guidance_high_confidence(self):
        """Test adaptation guidance generation for high confidence"""
        high_confidence_trend = ConfidenceTrend(
            user_id="user123",
            bot_name="elena",
            trend_analysis=TrendAnalysis(
                direction=TrendDirection.IMPROVING,
                slope=0.02,
                confidence=0.7,
                current_value=0.9,
                average_value=0.8,
                volatility=0.05,
                data_points=25,
                time_span_days=30
            ),
            recent_confidence=0.9,
            historical_average=0.8,
            needs_adaptation=False
        )
        
        self.mock_trend_analyzer.get_confidence_trends = AsyncMock(
            return_value=high_confidence_trend
        )
        
        # Test the method
        result = await self.adapter.adjust_response_style("user123", "elena")
        
        # Assertions
        self.assertIsNotNone(result)
        if result:
            # High confidence typically doesn't need major adaptations
            self.assertIsInstance(result, AdaptationParameters)
    
    async def test_integration_with_cache(self):
        """Test that caching mechanism works"""
        # Mock trend analyzer
        self.mock_trend_analyzer.get_confidence_trends = AsyncMock(
            return_value=self.improving_trend
        )
        
        # First call should hit the trend analyzer
        result1 = await self.adapter.adjust_response_style("user123", "elena")
        self.assertIsNotNone(result1)
        
        # Second call should use cache (analyzer won't be called again)
        result2 = await self.adapter.adjust_response_style("user123", "elena")
        self.assertIsNotNone(result2)
        
        # Should have called trend analyzer only once due to caching
        self.mock_trend_analyzer.get_confidence_trends.assert_called_once()
    
    async def test_no_trend_data_available(self):
        """Test behavior when no trend data is available"""
        # Mock no trend data
        self.mock_trend_analyzer.get_confidence_trends = AsyncMock(
            return_value=None
        )
        
        # Test adaptation parameters
        result = await self.adapter.adjust_response_style("user123", "elena")
        self.assertIsNone(result)
    
    async def test_no_trend_analyzer(self):
        """Test behavior when no trend analyzer is available"""
        adapter_no_analyzer = ConfidenceAdapter(None)
        
        # Test adaptation parameters
        result = await adapter_no_analyzer.adjust_response_style("user123", "elena")
        self.assertIsNone(result)
    
    def test_factory_function(self):
        """Test factory function"""
        adapter = create_confidence_adapter(self.mock_trend_analyzer)
        self.assertIsInstance(adapter, ConfidenceAdapter)
        self.assertEqual(adapter.trend_analyzer, self.mock_trend_analyzer)


class TestAdaptationParametersDataClass(unittest.TestCase):
    """Test the AdaptationParameters data class"""
    
    def test_adaptation_parameters_creation(self):
        """Test AdaptationParameters data class"""
        
        params = AdaptationParameters(
            response_style=ResponseStyle.CONFIDENCE_BUILDING,
            explanation_level=ExplanationLevel.DETAILED,
            uncertainty_acknowledgment=True,
            validation_seeking=True,
            clarification_frequency="high",
            detail_enhancement=1.5,
            confidence_threshold=0.6,
            adaptation_reason="Declining confidence trend detected"
        )
        
        self.assertEqual(params.response_style, ResponseStyle.CONFIDENCE_BUILDING)
        self.assertEqual(params.explanation_level, ExplanationLevel.DETAILED)
        self.assertTrue(params.uncertainty_acknowledgment)
        self.assertTrue(params.validation_seeking)
        self.assertEqual(params.clarification_frequency, "high")
        self.assertEqual(params.detail_enhancement, 1.5)
        self.assertEqual(params.adaptation_reason, "Declining confidence trend detected")


if __name__ == '__main__':
    unittest.main()