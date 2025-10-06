"""
InfluxDB Temporal Intelligence Client for WhisperEngine

This module provides time-series data recording and analysis for:
- Confidence evolution tracking
- Relationship progression analysis  
- Conversation quality metrics
- Character authenticity measurements
- User interaction patterns

Author: WhisperEngine AI Team
Created: October 4, 2025
Phase: 5 - Temporal Intelligence Integration
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

try:
    from influxdb_client.client.influxdb_client import InfluxDBClient
    from influxdb_client.client.write.point import Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    logging.warning("InfluxDB client not available - temporal intelligence disabled")

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of temporal metrics we track"""
    CONFIDENCE_EVOLUTION = "confidence_evolution"
    RELATIONSHIP_PROGRESSION = "relationship_progression" 
    CONVERSATION_QUALITY = "conversation_quality"
    # CHARACTER_AUTHENTICITY = "character_authenticity"  # REMOVED: No implementation
    # USER_ENGAGEMENT = "user_engagement"  # REMOVED: Use conversation_quality.engagement_score instead
    # EMOTIONAL_INTELLIGENCE = "emotional_intelligence"  # REMOVED: Use bot_emotion/user_emotion instead


@dataclass
class ConfidenceMetrics:
    """Confidence metrics for temporal tracking"""
    user_fact_confidence: float  # 0.0-1.0
    relationship_confidence: float  # 0.0-1.0
    context_confidence: float  # 0.0-1.0
    emotional_confidence: float  # 0.0-1.0
    overall_confidence: float  # 0.0-1.0


@dataclass
class RelationshipMetrics:
    """Relationship progression metrics"""
    trust_level: float  # 0.0-1.0
    affection_level: float  # 0.0-1.0  
    attunement_level: float  # 0.0-1.0
    interaction_quality: float  # 0.0-1.0
    communication_comfort: float  # 0.0-1.0


@dataclass
class ConversationQualityMetrics:
    """Conversation quality assessment"""
    engagement_score: float  # 0.0-1.0
    satisfaction_score: float  # 0.0-1.0
    natural_flow_score: float  # 0.0-1.0
    emotional_resonance: float  # 0.0-1.0
    topic_relevance: float  # 0.0-1.0


class TemporalIntelligenceClient:
    """
    InfluxDB client for temporal intelligence data recording and analysis
    """

    def __init__(self):
        self.enabled = INFLUXDB_AVAILABLE and self._validate_config()
        self.client = None
        self.write_api = None
        self.query_api = None
        
        if self.enabled:
            self._initialize_client()
        else:
            logger.warning("TemporalIntelligenceClient disabled - InfluxDB not available or not configured")

    def _validate_config(self) -> bool:
        """Validate InfluxDB configuration"""
        required_vars = ['INFLUXDB_URL', 'INFLUXDB_TOKEN', 'INFLUXDB_ORG', 'INFLUXDB_BUCKET']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning("InfluxDB config missing: %s", missing_vars)
            return False
        return True

    def _initialize_client(self):
        """Initialize InfluxDB client with configuration"""
        try:
            self.client = InfluxDBClient(
                url=os.getenv('INFLUXDB_URL', 'http://localhost:8086'),
                token=os.getenv('INFLUXDB_TOKEN'),
                org=os.getenv('INFLUXDB_ORG')
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info("InfluxDB temporal intelligence client initialized")
        except (ImportError, ValueError, ConnectionError) as e:
            logger.error("Failed to initialize InfluxDB client: %s", e)
            self.enabled = False

    async def record_confidence_evolution(
        self,
        bot_name: str,
        user_id: str,
        confidence_metrics: ConfidenceMetrics,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record confidence evolution metrics to InfluxDB
        
        Args:
            bot_name: Name of the bot (elena, marcus, etc.)
            user_id: User identifier
            confidence_metrics: Confidence measurements
            session_id: Optional session identifier
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("confidence_evolution") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id)
            
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("user_fact_confidence", confidence_metrics.user_fact_confidence) \
                .field("relationship_confidence", confidence_metrics.relationship_confidence) \
                .field("context_confidence", confidence_metrics.context_confidence) \
                .field("emotional_confidence", confidence_metrics.emotional_confidence) \
                .field("overall_confidence", confidence_metrics.overall_confidence)
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded confidence evolution for %s/%s", bot_name, user_id)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record confidence evolution: %s", e)
            return False

    async def record_relationship_progression(
        self,
        bot_name: str,
        user_id: str,
        relationship_metrics: RelationshipMetrics,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record relationship progression metrics to InfluxDB
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier  
            relationship_metrics: Relationship measurements
            session_id: Optional session identifier
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("relationship_progression") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id)
            
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("trust_level", relationship_metrics.trust_level) \
                .field("affection_level", relationship_metrics.affection_level) \
                .field("attunement_level", relationship_metrics.attunement_level) \
                .field("interaction_quality", relationship_metrics.interaction_quality) \
                .field("communication_comfort", relationship_metrics.communication_comfort)
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded relationship progression for %s/%s", bot_name, user_id)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record relationship progression: %s", e)
            return False

    async def record_conversation_quality(
        self,
        bot_name: str,
        user_id: str,
        quality_metrics: ConversationQualityMetrics,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record conversation quality metrics to InfluxDB
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            quality_metrics: Quality measurements  
            session_id: Optional session identifier
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("conversation_quality") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id)
            
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("engagement_score", quality_metrics.engagement_score) \
                .field("satisfaction_score", quality_metrics.satisfaction_score) \
                .field("natural_flow_score", quality_metrics.natural_flow_score) \
                .field("emotional_resonance", quality_metrics.emotional_resonance) \
                .field("topic_relevance", quality_metrics.topic_relevance)
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded conversation quality for %s/%s", bot_name, user_id)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record conversation quality: %s", e)
            return False

    async def record_bot_emotion(
        self,
        bot_name: str,
        user_id: str,
        primary_emotion: str,
        intensity: float,
        confidence: float,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record bot emotion metrics to InfluxDB (Phase 7.5)
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            primary_emotion: Bot's primary emotion (joy, sadness, curiosity, etc.)
            intensity: Emotion intensity (0.0-1.0)
            confidence: Emotion detection confidence (0.0-1.0)
            session_id: Optional session identifier
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("bot_emotion") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id) \
                .tag("emotion", primary_emotion)
            
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("intensity", intensity) \
                .field("confidence", confidence)
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded bot emotion '%s' for %s/%s (intensity: %.2f)", 
                        primary_emotion, bot_name, user_id, intensity)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record bot emotion: %s", e)
            return False

    async def record_user_emotion(
        self,
        bot_name: str,
        user_id: str,
        primary_emotion: str,
        intensity: float,
        confidence: float,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record user emotion metrics to InfluxDB (Phase 7.5)
        
        Captures user's emotional state during conversation for temporal analysis.
        Critical for understanding user emotional patterns and character tuning.
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            primary_emotion: User's primary detected emotion (joy, sadness, anger, etc.)
            intensity: Emotion intensity (0.0-1.0)
            confidence: Emotion detection confidence (0.0-1.0)
            session_id: Optional session identifier for grouping
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("user_emotion") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id) \
                .tag("emotion", primary_emotion)
            
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("intensity", intensity) \
                .field("confidence", confidence)
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded user emotion '%s' for %s/%s (intensity: %.2f)", 
                        primary_emotion, bot_name, user_id, intensity)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record user emotion: %s", e)
            return False

    async def get_confidence_trend(
        self,
        bot_name: str,
        user_id: str,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get confidence evolution trend for user
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            hours_back: How many hours of history to retrieve
            
        Returns:
            List of confidence measurements over time
        """
        if not self.enabled:
            return []

        try:
            query = f'''
                from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
                |> range(start: -{hours_back}h)
                |> filter(fn: (r) => r._measurement == "confidence_evolution")
                |> filter(fn: (r) => r.bot == "{bot_name}")
                |> filter(fn: (r) => r.user_id == "{user_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(query)
            
            trends = []
            for table in result:
                for record in table.records:
                    trends.append({
                        'timestamp': record.get_time(),
                        'user_fact_confidence': record.get_value('user_fact_confidence'),
                        'relationship_confidence': record.get_value('relationship_confidence'),
                        'context_confidence': record.get_value('context_confidence'),
                        'emotional_confidence': record.get_value('emotional_confidence'),
                        'overall_confidence': record.get_value('overall_confidence')
                    })
            
            return sorted(trends, key=lambda x: x['timestamp'])
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to get confidence trend: %s", e)
            return []

    async def get_relationship_evolution(
        self,
        bot_name: str,
        user_id: str,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get relationship progression over time
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            days_back: How many days of history to retrieve
            
        Returns:
            List of relationship measurements over time
        """
        if not self.enabled:
            return []

        try:
            query = f'''
                from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
                |> range(start: -{days_back}d)
                |> filter(fn: (r) => r._measurement == "relationship_progression")
                |> filter(fn: (r) => r.bot == "{bot_name}")
                |> filter(fn: (r) => r.user_id == "{user_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(query)
            
            evolution = []
            for table in result:
                for record in table.records:
                    evolution.append({
                        'timestamp': record.get_time(),
                        'trust_level': record.get_value('trust_level'),
                        'affection_level': record.get_value('affection_level'),
                        'attunement_level': record.get_value('attunement_level'),
                        'interaction_quality': record.get_value('interaction_quality'),
                        'communication_comfort': record.get_value('communication_comfort')
                    })
            
            return sorted(evolution, key=lambda x: x['timestamp'])
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to get relationship evolution: %s", e)
            return []

    def close(self):
        """Close InfluxDB client connection"""
        if self.client:
            self.client.close()


# Factory function for easy integration
def create_temporal_intelligence_client() -> TemporalIntelligenceClient:
    """Create and return temporal intelligence client instance"""
    return TemporalIntelligenceClient()


# Module-level client instance (will be initialized when needed)
_temporal_client = None


def get_temporal_client() -> TemporalIntelligenceClient:
    """Get or create module-level temporal intelligence client"""
    # Use module-level variable to avoid global statement
    if '_temporal_client' not in globals() or globals()['_temporal_client'] is None:
        globals()['_temporal_client'] = create_temporal_intelligence_client()
    return globals()['_temporal_client']