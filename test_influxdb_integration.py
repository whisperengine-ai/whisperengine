#!/usr/bin/env python3
"""
Quick test script for InfluxDB integration

Tests the synthetic metrics collection system with WhisperEngine's InfluxDB.
"""

import asyncio
import logging

from synthetic_influxdb_integration import SyntheticMetricsCollector, SyntheticTestMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_influxdb_integration():
    """Test InfluxDB integration with sample synthetic metrics"""
    
    logger.info("🧪 Testing InfluxDB integration...")
    
    # Initialize metrics collector
    collector = SyntheticMetricsCollector()
    
    # Check if InfluxDB is enabled
    if not collector.enabled:
        logger.warning("⚠️ InfluxDB not enabled - check environment variables")
        logger.info("Required: INFLUXDB_HOST, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET")
        return False
    
    logger.info("✅ InfluxDB collector initialized")
    
    # Create sample test metrics
    sample_metrics = SyntheticTestMetrics(
        memory_recall_accuracy=87.3,
        emotion_detection_precision=94.1,
        cdl_personality_consistency=91.7, 
        relationship_progression_score=78.4,
        cross_pollination_accuracy=85.6,
        conversation_quality_score=87.4,
        conversations_analyzed=156,
        unique_synthetic_users=8,
        test_duration_hours=12.5,
        expanded_taxonomy_usage=42.3
    )
    
    # Test recording synthetic test metrics
    logger.info("📊 Recording sample synthetic test metrics...")
    test_metrics_success = await collector.record_synthetic_test_metrics(sample_metrics, "integration_test")
    
    if test_metrics_success:
        logger.info("✅ Successfully recorded synthetic test metrics")
    else:
        logger.error("❌ Failed to record synthetic test metrics")
        return False
    
    # Test recording conversation rate
    logger.info("💬 Recording sample conversation rate...")
    bot_distribution = {"elena": 45, "marcus": 38, "ryan": 29, "gabriel": 22, "jake": 22}
    conversation_rate_success = await collector.record_synthetic_conversation_rate(
        conversations_per_hour=12.5,
        active_synthetic_users=8,
        bot_distribution=bot_distribution
    )
    
    if conversation_rate_success:
        logger.info("✅ Successfully recorded conversation rate metrics")
    else:
        logger.error("❌ Failed to record conversation rate metrics")
        return False
    
    # Test recording expanded taxonomy usage
    logger.info("😊 Recording sample emotion taxonomy usage...")
    emotion_distribution = {
        "joy": 45, "love": 23, "trust": 18, "optimism": 15, 
        "excitement": 12, "gratitude": 8, "surprise": 7,
        "sadness": 5, "fear": 3, "anger": 2
    }
    expanded_taxonomy_percentage = 42.3
    
    taxonomy_success = await collector.record_expanded_taxonomy_usage(
        emotion_distribution, expanded_taxonomy_percentage
    )
    
    if taxonomy_success:
        logger.info("✅ Successfully recorded emotion taxonomy metrics")
    else:
        logger.error("❌ Failed to record emotion taxonomy metrics")  
        return False
    
    # Close collector
    collector.close()
    
    logger.info("🎉 All InfluxDB integration tests passed!")
    logger.info("📈 Check your InfluxDB dashboard for the test metrics")
    logger.info("🔍 Metrics recorded:")
    logger.info("   - synthetic_test_quality (comprehensive test metrics)")
    logger.info("   - synthetic_conversation_rate (conversation generation stats)")
    logger.info("   - synthetic_emotion_taxonomy (expanded emotion usage)")
    
    return True


if __name__ == "__main__":
    test_success = asyncio.run(test_influxdb_integration())
    exit(0 if test_success else 1)