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
                url=os.getenv('INFLUXDB_URL', 'http://localhost:8087'),
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

    async def record_memory_aging_metrics(
        self,
        bot_name: str,
        user_id: str,
        health_status: str,
        total_memories: int,
        memories_flagged: int,
        flagged_ratio: float,
        processing_time: float,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record memory aging intelligence metrics to InfluxDB
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            health_status: Memory health status
            total_memories: Total number of memories analyzed
            memories_flagged: Number of memories flagged for aging
            flagged_ratio: Ratio of flagged memories (0.0-1.0)
            processing_time: Processing time in seconds
            session_id: Optional session identifier
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("memory_aging_metrics") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id) \
                .tag("health_status", health_status)
            
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("total_memories", total_memories) \
                .field("memories_flagged", memories_flagged) \
                .field("flagged_ratio", flagged_ratio) \
                .field("processing_time_ms", processing_time * 1000)
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded memory aging metrics for %s/%s: %d/%d flagged (%.2f%%)", 
                        bot_name, user_id, memories_flagged, total_memories, flagged_ratio * 100)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record memory aging metrics: %s", e)
            return False

    async def record_character_graph_performance(
        self,
        bot_name: str,
        user_id: str,
        operation: str,
        query_time_ms: float,
        knowledge_matches: int,
        cache_hit: bool,
        character_name: Optional[str] = None,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record CharacterGraphManager performance metrics to InfluxDB
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            operation: Type of graph operation (knowledge_query, skill_lookup, etc.)
            query_time_ms: Database query time in milliseconds
            knowledge_matches: Number of knowledge items found
            cache_hit: Whether query hit cache
            character_name: Character being queried
            session_id: Optional session identifier
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("character_graph_performance") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id) \
                .tag("operation", operation) \
                .tag("cache_hit", str(cache_hit).lower())
            
            if character_name:
                point = point.tag("character_name", character_name)
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("query_time_ms", query_time_ms) \
                .field("knowledge_matches", knowledge_matches) \
                .field("cache_hit_value", 1 if cache_hit else 0)
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded character graph performance for %s/%s: %s in %.1fms (%d matches)", 
                        bot_name, user_id, operation, query_time_ms, knowledge_matches)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record character graph performance: %s", e)
            return False

    async def record_intelligence_coordination_metrics(
        self,
        bot_name: str,
        user_id: str,
        systems_used: List[str],
        coordination_time_ms: float,
        authenticity_score: float,
        confidence_score: float,
        context_type: str,
        coordination_strategy: str,
        character_name: Optional[str] = None,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record UnifiedCharacterIntelligenceCoordinator performance metrics to InfluxDB
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            systems_used: List of intelligence systems used
            coordination_time_ms: Total coordination time in milliseconds
            authenticity_score: Character authenticity score (0.0-1.0)
            confidence_score: Coordination confidence score (0.0-1.0)
            context_type: Type of context detected
            coordination_strategy: Strategy used for coordination
            character_name: Character being coordinated
            session_id: Optional session identifier
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("intelligence_coordination_metrics") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id) \
                .tag("context_type", context_type) \
                .tag("coordination_strategy", coordination_strategy)
            
            if character_name:
                point = point.tag("character_name", character_name)
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("coordination_time_ms", coordination_time_ms) \
                .field("authenticity_score", authenticity_score) \
                .field("confidence_score", confidence_score) \
                .field("systems_count", len(systems_used)) \
                .field("systems_used", ",".join(systems_used))
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded intelligence coordination for %s/%s: %.1fms, %d systems, authenticity=%.2f", 
                        bot_name, user_id, coordination_time_ms, len(systems_used), authenticity_score)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record intelligence coordination metrics: %s", e)
            return False

    async def record_emotion_analysis_performance(
        self,
        bot_name: str,
        user_id: str,
        analysis_time_ms: float,
        confidence_score: float,
        emotion_count: int,
        primary_emotion: str,
        vector_dimension: int = 24,
        roberta_inference_time_ms: Optional[float] = None,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record Enhanced Vector Emotion Analyzer performance metrics to InfluxDB
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            analysis_time_ms: Total emotion analysis time in milliseconds
            confidence_score: RoBERTa confidence score (0.0-1.0)
            emotion_count: Number of emotions detected
            primary_emotion: Primary emotion detected
            vector_dimension: Emotion vector dimension
            roberta_inference_time_ms: RoBERTa transformer inference time
            session_id: Optional session identifier
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("emotion_analysis_performance") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id) \
                .tag("primary_emotion", primary_emotion)
            
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("analysis_time_ms", analysis_time_ms) \
                .field("confidence_score", confidence_score) \
                .field("emotion_count", emotion_count) \
                .field("vector_dimension", vector_dimension)
            
            if roberta_inference_time_ms is not None:
                point = point.field("roberta_inference_time_ms", roberta_inference_time_ms)
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded emotion analysis performance for %s/%s: %.1fms, %s (%.2f confidence)", 
                        bot_name, user_id, analysis_time_ms, primary_emotion, confidence_score)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record emotion analysis performance: %s", e)
            return False

    async def record_vector_memory_performance(
        self,
        bot_name: str,
        user_id: str,
        operation: str,
        search_time_ms: float,
        memories_found: int,
        avg_relevance_score: float,
        collection_name: str,
        vector_type: str = "content",
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record Vector Memory System performance metrics to InfluxDB
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            operation: Memory operation (search, store, retrieve)
            search_time_ms: Qdrant search time in milliseconds
            memories_found: Number of memories found
            avg_relevance_score: Average relevance score (0.0-1.0)
            collection_name: Qdrant collection name
            vector_type: Type of vector search (content, emotion, semantic)
            session_id: Optional session identifier
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("vector_memory_performance") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id) \
                .tag("operation", operation) \
                .tag("collection_name", collection_name) \
                .tag("vector_type", vector_type)
            
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("search_time_ms", search_time_ms) \
                .field("memories_found", memories_found) \
                .field("avg_relevance_score", avg_relevance_score)
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded vector memory performance for %s/%s: %s in %.1fms (%d memories, %.2f relevance)", 
                        bot_name, user_id, operation, search_time_ms, memories_found, avg_relevance_score)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record vector memory performance: %s", e)
            return False

    async def record_cdl_integration_performance(
        self,
        bot_name: str,
        user_id: str,
        operation: str,
        generation_time_ms: float,
        character_consistency_score: float,
        prompt_length: int,
        character_name: Optional[str] = None,
        mode_type: Optional[str] = None,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Record CDL AI Integration performance metrics to InfluxDB
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            operation: CDL operation (prompt_generation, mode_switching, knowledge_extraction)
            generation_time_ms: Prompt generation time in milliseconds
            character_consistency_score: Character consistency score (0.0-1.0)
            prompt_length: Length of generated prompt
            character_name: Character being integrated
            mode_type: Mode type (technical, creative, etc.)
            session_id: Optional session identifier
            timestamp: Optional timestamp
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            point = Point("cdl_integration_performance") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id) \
                .tag("operation", operation)
            
            if character_name:
                point = point.tag("character_name", character_name)
            if mode_type:
                point = point.tag("mode_type", mode_type)
            if session_id:
                point = point.tag("session_id", session_id)
                
            point = point \
                .field("generation_time_ms", generation_time_ms) \
                .field("character_consistency_score", character_consistency_score) \
                .field("prompt_length", prompt_length)
            
            if timestamp:
                point = point.time(timestamp)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded CDL integration performance for %s/%s: %s in %.1fms (consistency=%.2f)", 
                        bot_name, user_id, operation, generation_time_ms, character_consistency_score)
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record CDL integration performance: %s", e)
            return False

    async def record_point(
        self,
        point: Any,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Record a custom InfluxDB point (for advanced use cases)
        
        Args:
            point: InfluxDB Point object
            session_id: Optional session identifier
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False

        try:
            if session_id and hasattr(point, 'tag'):
                point = point.tag("session_id", session_id)
                
            self.write_api.write(bucket=os.getenv('INFLUXDB_BUCKET'), record=point)
            logger.debug("Recorded custom point to InfluxDB")
            return True
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to record custom point: %s", e)
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
                    # Use record.values dictionary for pivoted data
                    trends.append({
                        'timestamp': record.get_time(),
                        'user_fact_confidence': record.values.get('user_fact_confidence', 0.0),
                        'relationship_confidence': record.values.get('relationship_confidence', 0.0),
                        'context_confidence': record.values.get('context_confidence', 0.0),
                        'emotional_confidence': record.values.get('emotional_confidence', 0.0),
                        'overall_confidence': record.values.get('overall_confidence', 0.0)
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
                    # Use record.values dictionary for pivoted data
                    evolution.append({
                        'timestamp': record.get_time(),
                        'trust_level': record.values.get('trust_level', 0.0),
                        'affection_level': record.values.get('affection_level', 0.0),
                        'attunement_level': record.values.get('attunement_level', 0.0),
                        'interaction_quality': record.values.get('interaction_quality', 0.0),
                        'communication_comfort': record.values.get('communication_comfort', 0.0)
                    })
            
            return sorted(evolution, key=lambda x: x['timestamp'])
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to get relationship evolution: %s", e)
            return []

    async def get_bot_emotion_trend(
        self,
        bot_name: str,
        user_id: str,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get bot emotion trend for specific user over time.
        
        Retrieves chronological bot emotion data from InfluxDB for Phase 6.5
        bot emotional trajectory analysis.
        
        Args:
            bot_name: Name of the bot (elena, marcus, etc.)
            user_id: User identifier
            hours_back: How many hours of history to retrieve (default: 24)
            
        Returns:
            List of bot emotion measurements sorted chronologically:
            [
                {
                    'timestamp': datetime,
                    'primary_emotion': str,
                    'intensity': float,
                    'confidence': float
                },
                ...
            ]
            
        Example:
            >>> emotions = await client.get_bot_emotion_trend("elena", "123456", hours_back=48)
            >>> print(emotions[0])
            {'timestamp': '2025-10-15T10:30:00Z', 'primary_emotion': 'joy', 'intensity': 0.87}
        """
        if not self.enabled:
            return []

        try:
            query = f'''
                from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
                |> range(start: -{hours_back}h)
                |> filter(fn: (r) => r._measurement == "bot_emotion")
                |> filter(fn: (r) => r.bot == "{bot_name}")
                |> filter(fn: (r) => r.user_id == "{user_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: false)
            '''
            
            result = self.query_api.query(query)
            
            emotions = []
            for table in result:
                for record in table.records:
                    emotions.append({
                        'timestamp': record.get_time(),
                        'primary_emotion': record.values.get('emotion', 'neutral'),  # From tag
                        'intensity': record.values.get('intensity', 0.0),
                        'confidence': record.values.get('confidence', 0.0)
                    })
            
            return sorted(emotions, key=lambda x: x['timestamp'])
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to get bot emotion trend: %s", e)
            return []

    async def get_bot_emotion_overall_trend(
        self,
        bot_name: str,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get bot emotion trend across ALL users (character-level analysis).
        
        Retrieves bot's emotional patterns aggregated across all conversations.
        Useful for character behavior analysis and emotional consistency monitoring.
        
        Args:
            bot_name: Name of the bot (elena, marcus, etc.)
            hours_back: How many hours of history to retrieve (default: 24)
            
        Returns:
            List of bot emotion measurements across all users:
            [
                {
                    'timestamp': datetime,
                    'primary_emotion': str,
                    'intensity': float,
                    'confidence': float,
                    'user_id': str  # Which user triggered this emotion
                },
                ...
            ]
            
        Example:
            >>> emotions = await client.get_bot_emotion_overall_trend("elena", hours_back=168)
            >>> joy_count = sum(1 for e in emotions if e['primary_emotion'] == 'joy')
        """
        if not self.enabled:
            return []

        try:
            query = f'''
                from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
                |> range(start: -{hours_back}h)
                |> filter(fn: (r) => r._measurement == "bot_emotion")
                |> filter(fn: (r) => r.bot == "{bot_name}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: false)
            '''
            
            result = self.query_api.query(query)
            
            emotions = []
            for table in result:
                for record in table.records:
                    emotions.append({
                        'timestamp': record.get_time(),
                        'primary_emotion': record.values.get('emotion', 'neutral'),  # From tag
                        'intensity': record.values.get('intensity', 0.0),
                        'confidence': record.values.get('confidence', 0.0),
                        'user_id': record.values.get('user_id', 'unknown')  # From tag
                    })
            
            return sorted(emotions, key=lambda x: x['timestamp'])
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to get bot emotion overall trend: %s", e)
            return []

    async def get_confidence_overall_trend(
        self,
        bot_name: str,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get confidence evolution trend across ALL users.
        
        Character-level confidence analysis for behavior monitoring.
        
        Args:
            bot_name: Name of the bot (elena, marcus, etc.)
            hours_back: How many hours of history to retrieve (default: 24)
            
        Returns:
            List of confidence measurements across all users:
            [
                {
                    'timestamp': datetime,
                    'user_fact_confidence': float,
                    'relationship_confidence': float,
                    'context_confidence': float,
                    'emotional_confidence': float,
                    'overall_confidence': float,
                    'user_id': str  # Which user this confidence applies to
                },
                ...
            ]
        """
        if not self.enabled:
            return []

        try:
            query = f'''
                from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
                |> range(start: -{hours_back}h)
                |> filter(fn: (r) => r._measurement == "confidence_evolution")
                |> filter(fn: (r) => r.bot == "{bot_name}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: false)
            '''
            
            result = self.query_api.query(query)
            
            trends = []
            for table in result:
                for record in table.records:
                    trends.append({
                        'timestamp': record.get_time(),
                        'user_fact_confidence': record.values.get('user_fact_confidence', 0.0),
                        'relationship_confidence': record.values.get('relationship_confidence', 0.0),
                        'context_confidence': record.values.get('context_confidence', 0.0),
                        'emotional_confidence': record.values.get('emotional_confidence', 0.0),
                        'overall_confidence': record.values.get('overall_confidence', 0.0),
                        'user_id': record.values.get('user_id', 'unknown')  # From tag
                    })
            
            return sorted(trends, key=lambda x: x['timestamp'])
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to get confidence overall trend: %s", e)
            return []

    async def get_conversation_quality_trend(
        self,
        bot_name: str,
        user_id: str,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get conversation quality trend for specific user over time.
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            hours_back: How many hours of history to retrieve (default: 24)
            
        Returns:
            List of quality measurements sorted chronologically:
            [
                {
                    'timestamp': datetime,
                    'engagement_score': float,
                    'satisfaction_score': float,
                    'natural_flow_score': float,
                    'emotional_resonance': float,
                    'topic_relevance': float
                },
                ...
            ]
        """
        if not self.enabled:
            return []

        try:
            query = f'''
                from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
                |> range(start: -{hours_back}h)
                |> filter(fn: (r) => r._measurement == "conversation_quality")
                |> filter(fn: (r) => r.bot == "{bot_name}")
                |> filter(fn: (r) => r.user_id == "{user_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: false)
            '''
            
            result = self.query_api.query(query)
            
            quality_data = []
            for table in result:
                for record in table.records:
                    quality_data.append({
                        'timestamp': record.get_time(),
                        'engagement_score': record.values.get('engagement_score', 0.0),
                        'satisfaction_score': record.values.get('satisfaction_score', 0.0),
                        'natural_flow_score': record.values.get('natural_flow_score', 0.0),
                        'emotional_resonance': record.values.get('emotional_resonance', 0.0),
                        'topic_relevance': record.values.get('topic_relevance', 0.0)
                    })
            
            return sorted(quality_data, key=lambda x: x['timestamp'])
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to get conversation quality trend: %s", e)
            return []

    async def get_conversation_quality_overall_trend(
        self,
        bot_name: str,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get conversation quality trend across ALL users.
        
        Character-level quality analysis for behavior monitoring.
        
        Args:
            bot_name: Name of the bot
            hours_back: How many hours of history to retrieve (default: 24)
            
        Returns:
            List of quality measurements across all users with user_id included
        """
        if not self.enabled:
            return []

        try:
            query = f'''
                from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
                |> range(start: -{hours_back}h)
                |> filter(fn: (r) => r._measurement == "conversation_quality")
                |> filter(fn: (r) => r.bot == "{bot_name}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: false)
            '''
            
            result = self.query_api.query(query)
            
            quality_data = []
            for table in result:
                for record in table.records:
                    quality_data.append({
                        'timestamp': record.get_time(),
                        'engagement_score': record.values.get('engagement_score', 0.0),
                        'satisfaction_score': record.values.get('satisfaction_score', 0.0),
                        'natural_flow_score': record.values.get('natural_flow_score', 0.0),
                        'emotional_resonance': record.values.get('emotional_resonance', 0.0),
                        'topic_relevance': record.values.get('topic_relevance', 0.0),
                        'user_id': record.values.get('user_id', 'unknown')  # From tag
                    })
            
            return sorted(quality_data, key=lambda x: x['timestamp'])
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to get conversation quality overall trend: %s", e)
            return []

    async def query_data(
        self,
        flux_query: str
    ) -> List[Dict[str, Any]]:
        """
        Execute generic Flux query and return results.
        
        Low-level query method for custom InfluxDB queries.
        Use specific methods (get_bot_emotion_trend, etc.) when possible.
        
        Args:
            flux_query: Complete Flux query string
            
        Returns:
            List of query results as dictionaries:
            [
                {
                    'timestamp': datetime,
                    'field_name': value,
                    ...
                },
                ...
            ]
            
        Example:
            >>> query = '''
            ... from(bucket: "whisperengine")
            ... |> range(start: -1h)
            ... |> filter(fn: (r) => r._measurement == "bot_emotion")
            ... '''
            >>> results = await client.query_data(query)
        """
        if not self.enabled:
            return []

        try:
            result = self.query_api.query(flux_query)
            
            data = []
            for table in result:
                for record in table.records:
                    # Extract all values from record
                    row = {
                        'timestamp': record.get_time(),
                        '_measurement': record.get_measurement(),
                        '_field': record.get_field()
                    }
                    
                    # Add all other fields from values
                    row.update(record.values)
                    
                    data.append(row)
            
            return data
            
        except (ValueError, ConnectionError, KeyError) as e:
            logger.error("Failed to execute query: %s", e)
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