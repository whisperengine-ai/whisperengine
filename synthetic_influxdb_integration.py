#!/usr/bin/env python3
"""
InfluxDB Synthetic Metrics Integration

Pushes synthetic conversation validation metrics directly into WhisperEngine's existing InfluxDB 
for unified monitoring and dashboarding. No separate dashboard needed.

This integrates with WhisperEngine's temporal intelligence infrastructure to provide:
- Long-term synthetic test quality metrics
- ML system performance trends over time  
- Validation against real user conversation patterns
- Integrated dashboard viewing in existing InfluxDB UI

Author: WhisperEngine AI Team
Created: October 8, 2025
Purpose: Unified synthetic test metrics in InfluxDB
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    from influxdb_client.client.influxdb_client import InfluxDBClient
    from influxdb_client.client.write.point import Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    logging.warning("InfluxDB client not available - synthetic metrics will not be stored")

logger = logging.getLogger(__name__)


@dataclass
class SyntheticTestMetrics:
    """Synthetic test metrics for InfluxDB storage"""
    memory_recall_accuracy: float
    emotion_detection_precision: float
    cdl_personality_consistency: float
    relationship_progression_score: float
    cross_pollination_accuracy: float
    conversation_quality_score: float
    conversations_analyzed: int
    unique_synthetic_users: int
    test_duration_hours: float
    expanded_taxonomy_usage: float  # Percentage of new emotions used


class SyntheticMetricsCollector:
    """Collects and stores synthetic test metrics in InfluxDB"""
    
    def __init__(self):
        self.enabled = INFLUXDB_AVAILABLE and self._validate_config()
        self.client = None
        self.write_api = None
        
        if self.enabled:
            self._initialize_client()
        else:
            logger.warning("SyntheticMetricsCollector disabled - InfluxDB not available or not configured")
    
    def _validate_config(self) -> bool:
        """Validate InfluxDB configuration"""
        required_vars = ['INFLUXDB_URL', 'INFLUXDB_TOKEN', 'INFLUXDB_ORG', 'INFLUXDB_BUCKET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning("InfluxDB config missing: %s", missing_vars)
            return False
        return True
    
    def _initialize_client(self):
        """Initialize InfluxDB client"""
        try:
            self.client = InfluxDBClient(
                url=os.getenv('INFLUXDB_URL'),
                token=os.getenv('INFLUXDB_TOKEN'),
                org=os.getenv('INFLUXDB_ORG')
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            logger.info("InfluxDB synthetic metrics client initialized")
        except Exception as e:
            logger.error("Failed to initialize InfluxDB client: %s", e)
            self.enabled = False
    
    async def record_synthetic_test_metrics(
        self,
        metrics: SyntheticTestMetrics,
        test_type: str = "comprehensive",
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record synthetic test metrics to InfluxDB
        
        Args:
            metrics: Synthetic test metrics
            test_type: Type of synthetic test run
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.warning("InfluxDB not enabled, skipping synthetic metrics recording")
            return False
        
        try:
            point = Point("synthetic_test_quality") \
                .tag("test_type", test_type) \
                .tag("source", "synthetic_generator") \
                .field("memory_recall_accuracy", metrics.memory_recall_accuracy) \
                .field("emotion_detection_precision", metrics.emotion_detection_precision) \
                .field("cdl_personality_consistency", metrics.cdl_personality_consistency) \
                .field("relationship_progression_score", metrics.relationship_progression_score) \
                .field("cross_pollination_accuracy", metrics.cross_pollination_accuracy) \
                .field("conversation_quality_score", metrics.conversation_quality_score) \
                .field("conversations_analyzed", metrics.conversations_analyzed) \
                .field("unique_synthetic_users", metrics.unique_synthetic_users) \
                .field("test_duration_hours", metrics.test_duration_hours) \
                .field("expanded_taxonomy_usage", metrics.expanded_taxonomy_usage)
            
            if timestamp:
                point = point.time(timestamp)
            
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.info("Recorded synthetic test metrics to InfluxDB: quality_score=%.2f", 
                       metrics.conversation_quality_score)
            return True
            
        except Exception as e:
            logger.error("Failed to record synthetic test metrics: %s", e)
            return False
    
    async def record_synthetic_conversation_rate(
        self,
        conversations_per_hour: float,
        active_synthetic_users: int,
        bot_distribution: Dict[str, int],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record synthetic conversation rate metrics
        
        Args:
            conversations_per_hour: Rate of synthetic conversations
            active_synthetic_users: Number of active synthetic users
            bot_distribution: Distribution of conversations per bot
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False
        
        try:
            point = Point("synthetic_conversation_rate") \
                .tag("source", "synthetic_generator") \
                .field("conversations_per_hour", conversations_per_hour) \
                .field("active_synthetic_users", active_synthetic_users) \
                .field("total_bot_conversations", sum(bot_distribution.values()))
            
            # Add bot-specific conversation counts
            for bot_name, count in bot_distribution.items():
                point = point.field(f"conversations_{bot_name}", count)
            
            if timestamp:
                point = point.time(timestamp)
            
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.info("Recorded synthetic conversation rate: %.1f conv/hr, %d users", 
                       conversations_per_hour, active_synthetic_users)
            return True
            
        except Exception as e:
            logger.error("Failed to record synthetic conversation rate: %s", e)
            return False
    
    async def record_expanded_taxonomy_usage(
        self,
        emotion_distribution: Dict[str, int],
        expanded_emotion_percentage: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record expanded emotion taxonomy usage metrics
        
        Args:
            emotion_distribution: Count of each emotion detected
            expanded_emotion_percentage: Percentage using new emotions (love, trust, etc.)
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False
        
        try:
            point = Point("synthetic_emotion_taxonomy") \
                .tag("source", "synthetic_generator") \
                .field("expanded_emotion_percentage", expanded_emotion_percentage) \
                .field("total_emotions_detected", sum(emotion_distribution.values()))
            
            # Add specific emotion counts
            core_emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust']
            expanded_emotions = ['love', 'trust', 'optimism', 'pessimism', 'anticipation']
            
            core_count = sum(emotion_distribution.get(emotion, 0) for emotion in core_emotions)
            expanded_count = sum(emotion_distribution.get(emotion, 0) for emotion in expanded_emotions)
            
            point = point.field("core_emotion_count", core_count) \
                        .field("expanded_emotion_count", expanded_count)
            
            # Add top emotions
            sorted_emotions = sorted(emotion_distribution.items(), key=lambda x: x[1], reverse=True)
            for i, (emotion, count) in enumerate(sorted_emotions[:10]):  # Top 10
                point = point.field(f"emotion_{i+1}_{emotion}", count)
            
            if timestamp:
                point = point.time(timestamp)
            
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.info("Recorded expanded taxonomy usage: %.1f%% expanded emotions", 
                       expanded_emotion_percentage * 100)
            return True
            
        except Exception as e:
            logger.error("Failed to record expanded taxonomy usage: %s", e)
            return False
    
    async def record_synthetic_user_persona_metrics(
        self,
        persona_distribution: Dict[str, int],
        persona_quality_scores: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record synthetic user persona performance metrics
        
        Args:
            persona_distribution: Count of conversations per persona type
            persona_quality_scores: Quality scores per persona
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False
        
        try:
            point = Point("synthetic_user_personas") \
                .tag("source", "synthetic_generator") \
                .field("total_personas", len(persona_distribution)) \
                .field("total_conversations", sum(persona_distribution.values()))
            
            # Add persona-specific metrics
            for persona, count in persona_distribution.items():
                point = point.field(f"conversations_{persona}", count)
                if persona in persona_quality_scores:
                    point = point.field(f"quality_{persona}", persona_quality_scores[persona])
            
            if timestamp:
                point = point.time(timestamp)
            
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.info("Recorded synthetic user persona metrics: %d persona types", 
                       len(persona_distribution))
            return True
            
        except Exception as e:
            logger.error("Failed to record synthetic user persona metrics: %s", e)
            return False
    
    def close(self):
        """Close InfluxDB client"""
        if self.client:
            self.client.close()


def create_synthetic_metrics_collector() -> SyntheticMetricsCollector:
    """Factory function to create synthetic metrics collector"""
    return SyntheticMetricsCollector()


# Example usage and testing
async def main():
    """Test function for synthetic metrics collection"""
    collector = create_synthetic_metrics_collector()
    
    if not collector.enabled:
        logger.error("InfluxDB not configured - cannot test synthetic metrics")
        return
    
    # Test synthetic test metrics
    test_metrics = SyntheticTestMetrics(
        memory_recall_accuracy=0.85,
        emotion_detection_precision=0.92,
        cdl_personality_consistency=0.88,
        relationship_progression_score=0.76,
        cross_pollination_accuracy=0.82,
        conversation_quality_score=0.79,
        conversations_analyzed=150,
        unique_synthetic_users=8,
        test_duration_hours=24.5,
        expanded_taxonomy_usage=0.34
    )
    
    success = await collector.record_synthetic_test_metrics(test_metrics, "test_run")
    if success:
        logger.info("✅ Synthetic test metrics recorded successfully")
    else:
        logger.error("❌ Failed to record synthetic test metrics")
    
    # Test conversation rate metrics
    success = await collector.record_synthetic_conversation_rate(
        conversations_per_hour=6.2,
        active_synthetic_users=8,
        bot_distribution={
            "elena": 15, "marcus": 12, "ryan": 8, "dream": 10, "gabriel": 11, 
            "sophia": 9, "jake": 7, "dotty": 6, "aetheris": 8, "aethys": 14
        }
    )
    if success:
        logger.info("✅ Conversation rate metrics recorded successfully")
    
    collector.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())