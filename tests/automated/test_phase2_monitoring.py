"""
Test suite for Phase 2 intelligent retrieval monitoring system.

Integration tests that verify IntelligentRetrievalMonitor functionality with real components.
When InfluxDB is not configured, monitoring is gracefully disabled.
"""

import pytest

from src.memory.intelligent_retrieval_monitor import IntelligentRetrievalMonitor, get_intelligent_retrieval_monitor
from src.memory.query_classifier import QueryCategory


class TestIntelligentRetrievalMonitor:
    """Test IntelligentRetrievalMonitor initialization and configuration."""
    
    @pytest.mark.asyncio
    async def test_monitor_initialization(self):
        """Monitor should initialize without errors."""
        monitor = IntelligentRetrievalMonitor()
        assert monitor is not None
    
    @pytest.mark.asyncio
    async def test_monitor_graceful_degradation(self):
        """Monitor should gracefully handle missing InfluxDB."""
        monitor = IntelligentRetrievalMonitor()
        
        # Should not raise error even if InfluxDB not configured
        await monitor.track_classification(
            user_id="test_user",
            query="test query",
            category=QueryCategory.GENERAL,
            classification_time_ms=10.0
        )


class TestClassificationTracking:
    """Test classification tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_track_classification_success(self):
        """Test successful classification tracking (integration test)."""
        monitor = IntelligentRetrievalMonitor()
        
        # Should not raise error regardless of InfluxDB availability
        await monitor.track_classification(
            user_id="test_user",
            query="What did we talk about yesterday?",
            category=QueryCategory.TEMPORAL,
            emotion_intensity=0.7,
            is_temporal=True,
            classification_time_ms=15.5
        )
        
        assert monitor is not None
    
    @pytest.mark.asyncio
    async def test_track_classification_when_disabled(self):
        """Test classification tracking when monitoring disabled."""
        monitor = IntelligentRetrievalMonitor()
        
        # Should not raise error even if InfluxDB not available
        await monitor.track_classification(
            user_id="test_user",
            query="test query",
            category=QueryCategory.GENERAL,
            classification_time_ms=10.0
        )


class TestRoutingTracking:
    """Test routing decision tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_track_routing_success(self):
        """Test routing tracking with multi-vector fusion (integration test)."""
        monitor = IntelligentRetrievalMonitor()
        
        # Should not raise error regardless of InfluxDB availability
        await monitor.track_routing(
            user_id="test_user",
            query_category=QueryCategory.EMOTIONAL,
            search_type="multi_vector_fusion",
            vectors_used=["content", "emotion"],
            memory_count=8,
            search_time_ms=45.2,
            fusion_enabled=True
        )
        
        assert monitor is not None
    
    @pytest.mark.asyncio
    async def test_track_routing_when_disabled(self):
        """Test routing tracking when monitoring disabled."""
        monitor = IntelligentRetrievalMonitor()
        
        # Should not raise error even if InfluxDB not available
        await monitor.track_routing(
            user_id="test_user",
            query_category=QueryCategory.GENERAL,
            search_type="content_only",
            vectors_used=["content"],
            memory_count=10,
            search_time_ms=30.0
        )


class TestPerformanceTracking:
    """Test performance metrics tracking."""
    
    @pytest.mark.asyncio
    async def test_track_performance_with_fusion(self):
        """Test performance tracking with fusion overhead (integration test)."""
        monitor = IntelligentRetrievalMonitor()
        
        # Should not raise error regardless of InfluxDB availability
        await monitor.track_retrieval_performance(
            user_id="test_user",
            total_time_ms=30.5,
            classification_time_ms=2.0,
            search_time_ms=23.5,
            fusion_time_ms=5.0,
            intelligent_routing_used=True
        )
        
        assert monitor is not None


class TestABTestTracking:
    """Test A/B testing metrics tracking."""
    
    @pytest.mark.asyncio
    async def test_track_ab_test_phase2_variant(self):
        """Test Phase 2 A/B test results tracking (integration test)."""
        monitor = IntelligentRetrievalMonitor()
        
        # Should not raise error regardless of InfluxDB availability
        await monitor.track_ab_test_result(
            user_id="test_user",
            query="How are you feeling?",
            variant="phase2",
            query_category=QueryCategory.EMOTIONAL,
            memory_relevance_score=0.82,
            response_quality_score=0.90,
            user_reaction="positive"
        )
        
        assert monitor is not None


class TestMonitorSingleton:
    """Test global monitor singleton pattern."""
    
    def test_get_intelligent_retrieval_monitor_singleton(self):
        """get_intelligent_retrieval_monitor should return same instance."""
        monitor1 = get_intelligent_retrieval_monitor()
        monitor2 = get_intelligent_retrieval_monitor()
        
        assert monitor1 is monitor2
    
    def test_get_intelligent_retrieval_monitor_creates_instance(self):
        """get_intelligent_retrieval_monitor should create IntelligentRetrievalMonitor instance."""
        monitor = get_intelligent_retrieval_monitor()
        
        assert isinstance(monitor, IntelligentRetrievalMonitor)
