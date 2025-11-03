"""
Fidelity-First Performance Metrics Collector for InfluxDB

Comprehensive time series data collection for WhisperEngine's fidelity-first architecture.
Tracks character consistency, optimization ratios, memory quality, and performance metrics.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

# InfluxDB client for time series data
try:
    from influxdb_client import InfluxDBClient, Point, WriteOptions
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    InfluxDBClient = None
    Point = None
    WriteOptions = None
    SYNCHRONOUS = None
    logger = logging.getLogger(__name__)
    logger.warning("InfluxDB client not available. Install with: pip install influxdb-client")

# Performance monitoring
import psutil

# Bot name utility - use existing implementation
try:
    from src.memory.vector_memory_system import get_normalized_bot_name_from_env
except ImportError:
    # Fallback implementation - use proper bot name normalization
    try:
        from src.utils.bot_name_utils import get_normalized_bot_name_from_env
    except ImportError:
        # Last resort fallback
        import os
        import re
        def get_normalized_bot_name_from_env() -> str:
            raw_bot_name = os.getenv('DISCORD_BOT_NAME') or os.getenv('BOT_NAME') or 'unknown'
            if not raw_bot_name or not isinstance(raw_bot_name, str):
                return "unknown"
            normalized = raw_bot_name.strip().lower()
            normalized = re.sub(r'\s+', '_', normalized)
            normalized = re.sub(r'[^a-z0-9_-]', '', normalized)
            normalized = re.sub(r'[_-]+', '_', normalized).strip('_-')
            return normalized if normalized else "unknown"

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of fidelity-first metrics to track"""
    # v2: Fixed integer field type preservation for all measurements
    FIDELITY_SCORE = "fidelity_score_v2"
    CHARACTER_CONSISTENCY = "character_consistency_v2"
    OPTIMIZATION_RATIO = "optimization_ratio_v2"
    MEMORY_QUALITY = "memory_quality_v2"
    RESPONSE_TIME = "response_time_v2"
    # TOKEN_USAGE = "token_usage"  # REMOVED: Never used
    # SYSTEM_PERFORMANCE = "system_performance"  # REMOVED: Already tracked by ConcurrentConversationManager
    # USER_ENGAGEMENT = "user_engagement"  # REMOVED: Redundant with temporal intelligence


@dataclass
class FidelityMetric:
    """Individual fidelity-first metric measurement"""
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    bot_name: Optional[str] = None
    user_id: Optional[str] = None
    operation: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    fields: Dict[str, Union[float, int, str]] = field(default_factory=dict)


@dataclass
class FidelityOptimizationMetric:
    """Metrics specific to fidelity-first optimization"""
    operation: str
    original_word_count: int
    optimized_word_count: int
    optimization_ratio: float  # 0.0 = full optimization, 1.0 = no optimization
    character_preservation_score: float  # 0.0-1.0 how much character nuance preserved
    context_quality_score: float  # 0.0-1.0 relevance of context preserved
    full_fidelity_used: bool
    intelligent_trimming_applied: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FidelityMetricsCollector:
    """
    Time series metrics collector for fidelity-first performance monitoring.
    
    Key Features:
    - Real-time fidelity score tracking
    - Character consistency monitoring
    - Optimization ratio analysis
    - Performance vs. quality trade-offs
    - Multi-bot comparison metrics
    """
    
    def __init__(self, 
                 influxdb_url: Optional[str] = None,
                 influxdb_token: Optional[str] = None,
                 influxdb_org: Optional[str] = None,
                 influxdb_bucket: Optional[str] = None):
        
        # Use environment variables with fallback defaults
        self.influxdb_url = influxdb_url or os.getenv('INFLUXDB_URL', 'http://localhost:8087')
        self.influxdb_token = influxdb_token or os.getenv('INFLUXDB_TOKEN', 'whisperengine-fidelity-first-metrics-token')
        self.influxdb_org = influxdb_org or os.getenv('INFLUXDB_ORG', 'whisperengine')
        self.influxdb_bucket = influxdb_bucket or os.getenv('INFLUXDB_BUCKET', 'performance_metrics')
        
        # InfluxDB client (lazy initialization)
        self._client: Optional[Any] = None
        self._write_api = None
        self._query_api = None
        
        # In-memory buffer for offline operation
        self._metric_buffer: List[FidelityMetric] = []
        self._max_buffer_size = 1000
        
        # Bot identification
        self.bot_name = get_normalized_bot_name_from_env()
        
        logger.info(f"�📊 FidelityMetricsCollector initialized for bot: {self.bot_name}")
    
    @property
    def client(self) -> Optional[Any]:
        """Lazy initialization of InfluxDB client"""
        if not INFLUXDB_AVAILABLE:
            return None
            
        if self._client is None:
            try:
                if not INFLUXDB_AVAILABLE or InfluxDBClient is None:
                    logger.warning("InfluxDB client not available")
                    return None
                    
                self._client = InfluxDBClient(
                    url=self.influxdb_url,
                    token=self.influxdb_token,
                    org=self.influxdb_org
                )
                self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
                self._query_api = self._client.query_api()
                logger.info("✅ Connected to InfluxDB for metrics collection")
            except Exception as e:
                logger.warning(f"Failed to connect to InfluxDB: {e}")
                return None
        
        return self._client
    
    def record_fidelity_optimization(self, optimization_metric: FidelityOptimizationMetric):
        """Record fidelity-first optimization metrics"""
        try:
            # Primary optimization ratio metric
            self.record_metric(FidelityMetric(
                metric_type=MetricType.OPTIMIZATION_RATIO,
                value=optimization_metric.optimization_ratio,
                bot_name=self.bot_name,
                operation=optimization_metric.operation,
                tags={
                    "full_fidelity_used": str(optimization_metric.full_fidelity_used),
                    "intelligent_trimming": str(optimization_metric.intelligent_trimming_applied)
                },
                fields={
                    "original_words": optimization_metric.original_word_count,
                    "optimized_words": optimization_metric.optimized_word_count,
                    "character_preservation": optimization_metric.character_preservation_score,
                    "context_quality": optimization_metric.context_quality_score
                }
            ))
            
            # Character consistency metric
            self.record_metric(FidelityMetric(
                metric_type=MetricType.CHARACTER_CONSISTENCY,
                value=optimization_metric.character_preservation_score,
                bot_name=self.bot_name,
                operation=optimization_metric.operation,
                tags={
                    "optimization_level": "full" if optimization_metric.optimization_ratio > 0.8 else "partial"
                }
            ))
            
            # Fidelity score (composite metric)
            fidelity_score = (optimization_metric.character_preservation_score + 
                            optimization_metric.context_quality_score) / 2
            self.record_metric(FidelityMetric(
                metric_type=MetricType.FIDELITY_SCORE,
                value=fidelity_score,
                bot_name=self.bot_name,
                operation=optimization_metric.operation
            ))
            
        except Exception as e:
            logger.error(f"Error recording fidelity optimization metrics: {e}")
    
    def record_memory_quality(self, user_id: str, operation: str, 
                            relevance_score: float, retrieval_time_ms: float,
                            memory_count: int, vector_similarity: float):
        """Record memory system quality metrics"""
        try:
            # Memory quality score (ONLY record this - timing handled by main performance tracking)
            self.record_metric(FidelityMetric(
                metric_type=MetricType.MEMORY_QUALITY,
                value=relevance_score,
                bot_name=self.bot_name,
                user_id=user_id,
                operation=operation,
                fields={
                    "retrieval_time_ms": retrieval_time_ms,
                    "memory_count": memory_count,
                    "vector_similarity": vector_similarity
                }
            ))
            
            # REMOVED: Redundant response time tracking - already tracked by record_performance_metric
            
        except Exception as e:
            logger.error(f"Error recording memory quality metrics: {e}")
    
    def record_performance_metric(self, operation: str, duration_ms: float, 
                                success: bool = True, user_id: Optional[str] = None,
                                metadata: Optional[Dict] = None):
        """Record general performance metrics"""
        try:
            # Response time metric
            self.record_metric(FidelityMetric(
                metric_type=MetricType.RESPONSE_TIME,
                value=duration_ms,
                bot_name=self.bot_name,
                user_id=user_id,
                operation=operation,
                tags={
                    "success": str(success),
                    "operation_type": "general"
                },
                fields=metadata or {}
            ))
            
            # REMOVED: Redundant system performance snapshot per operation
            # System performance is already tracked every 5s by ConcurrentConversationManager
            
        except Exception as e:
            logger.error(f"Error recording performance metrics: {e}")
    
    # REMOVED: record_user_engagement method - redundant with temporal intelligence
    
    def record_emotion_and_stance(self, user_id: str, operation: str,
                                 user_emotion: Optional[str] = None,
                                 user_emotion_confidence: float = 0.0,
                                 bot_emotion: Optional[str] = None,
                                 bot_emotion_confidence: float = 0.0,
                                 user_stance: Optional[str] = None,
                                 user_self_focus: float = 0.0,
                                 bot_stance: Optional[str] = None,
                                 bot_self_focus: float = 0.0,
                                 stance_confidence: float = 0.0):
        """
        Record emotion and stance analysis metrics for both user and bot.
        
        Enables tracking of:
        - User's actual emotional state (with self-focus ratio)
        - Bot's genuine emotional response (not empathetic echoing)
        - Emotional attribution accuracy (direct vs attributed emotions)
        - Conversation emotion flow and dynamics
        
        Args:
            user_id: Platform user ID (Discord ID, etc.)
            operation: Operation name (e.g., "message_processing")
            user_emotion: Primary emotion detected in user message
            user_emotion_confidence: Confidence of user emotion (0.0-1.0)
            bot_emotion: Primary emotion in bot response
            bot_emotion_confidence: Confidence of bot emotion (0.0-1.0)
            user_stance: Emotional stance type ("direct", "attributed", "mixed", "none")
            user_self_focus: Ratio of self-focused emotions in user message (0.0-1.0)
            bot_stance: Bot's emotional stance type
            bot_self_focus: Ratio of self-focused emotions in bot response (0.0-1.0)
            stance_confidence: Overall stance detection confidence (0.0-1.0)
        """
        try:
            # User emotion and stance metrics
            if user_emotion:
                self.record_metric(FidelityMetric(
                    metric_type=MetricType.FIDELITY_SCORE,  # Reuse for emotional fidelity
                    value=user_emotion_confidence,
                    bot_name=self.bot_name,
                    user_id=user_id,
                    operation=f"{operation}_user_emotion",
                    tags={
                        "emotion_source": "user",
                        "emotion_type": user_emotion,
                        "stance_type": user_stance or "unknown"
                    },
                    fields={
                        "user_self_focus": user_self_focus,
                        "confidence": user_emotion_confidence
                    }
                ))
            
            # Bot emotion and stance metrics
            if bot_emotion:
                self.record_metric(FidelityMetric(
                    metric_type=MetricType.FIDELITY_SCORE,  # Reuse for emotional fidelity
                    value=bot_emotion_confidence,
                    bot_name=self.bot_name,
                    user_id=user_id,
                    operation=f"{operation}_bot_emotion",
                    tags={
                        "emotion_source": "bot",
                        "emotion_type": bot_emotion,
                        "stance_type": bot_stance or "unknown"
                    },
                    fields={
                        "bot_self_focus": bot_self_focus,
                        "confidence": bot_emotion_confidence
                    }
                ))
            
            # Stance analysis summary (meta-metric for emotional attribution accuracy)
            self.record_metric(FidelityMetric(
                metric_type=MetricType.CHARACTER_CONSISTENCY,  # Reuse for stance consistency
                value=stance_confidence,
                bot_name=self.bot_name,
                user_id=user_id,
                operation=f"{operation}_stance_analysis",
                tags={
                    "user_stance": user_stance or "none",
                    "bot_stance": bot_stance or "none"
                },
                fields={
                    "user_self_focus": user_self_focus,
                    "bot_self_focus": bot_self_focus,
                    "stance_confidence": stance_confidence
                }
            ))
            
            logger.debug(
                f"📊 EMOTION/STANCE METRICS: user_emotion={user_emotion} (stance={user_stance}, "
                f"self_focus={user_self_focus:.2f}), bot_emotion={bot_emotion} (stance={bot_stance}, "
                f"self_focus={bot_self_focus:.2f})"
            )
            
        except Exception as e:
            logger.error(f"Error recording emotion and stance metrics: {e}")
    
    def record_metric(self, metric: FidelityMetric):
        """Record a generic metric to InfluxDB or buffer"""
        try:
            if self.client and self._write_api:
                # Write to InfluxDB
                point = self._create_influx_point(metric)
                self._write_api.write(bucket=self.influxdb_bucket, record=point)
            else:
                # Buffer for offline operation
                self._metric_buffer.append(metric)
                if len(self._metric_buffer) > self._max_buffer_size:
                    self._metric_buffer.pop(0)  # Remove oldest
                    
        except Exception as e:
            logger.error(f"Error recording metric {metric.metric_type}: {e}")
            # Fallback to buffer
            self._metric_buffer.append(metric)
    
    def _create_influx_point(self, metric: FidelityMetric) -> Optional[Any]:
        """Create InfluxDB Point from FidelityMetric"""
        if not INFLUXDB_AVAILABLE or Point is None:
            return None
            
        point = Point(metric.metric_type.value).time(metric.timestamp)
        
        # Add tags
        point = point.tag("bot_name", metric.bot_name or "unknown")
        if metric.user_id:
            point = point.tag("user_id", metric.user_id)
        if metric.operation:
            point = point.tag("operation", metric.operation)
        
        # Add custom tags (validate string values)
        for key, value in metric.tags.items():
            if value is not None:
                point = point.tag(key, str(value))
        
        # Add value as main field (validate numeric)
        if isinstance(metric.value, (int, float)) and not (isinstance(metric.value, float) and (metric.value != metric.value)):  # Check for NaN
            point = point.field("value", float(metric.value))
        else:
            logger.warning("Invalid metric value for %s: %s", metric.metric_type, metric.value)
            return None
        
        # Add additional fields (validate types and preserve int/float distinction)
        for key, value in metric.fields.items():
            if value is not None:
                if isinstance(value, bool):
                    # Boolean must be checked before int (bool is subclass of int in Python)
                    point = point.field(key, value)
                elif isinstance(value, int):
                    # Preserve integers as integers (important for InfluxDB schema)
                    point = point.field(key, int(value))
                elif isinstance(value, float):
                    # Check for NaN
                    if value == value:  # NaN != NaN, so this filters out NaN
                        point = point.field(key, float(value))
                    else:
                        logger.debug("Skipping NaN value for field %s", key)
                elif isinstance(value, str):
                    point = point.field(key, value)
                else:
                    logger.debug("Skipping unsupported field type for %s: %s", key, type(value))
        
        return point
    
    async def flush_buffer(self):
        """Flush buffered metrics to InfluxDB"""
        if not self._metric_buffer or not self.client or not INFLUXDB_AVAILABLE:
            return
            
        try:
            points = [self._create_influx_point(metric) for metric in self._metric_buffer if self._create_influx_point(metric) is not None]
            if points and hasattr(self, '_write_api') and self._write_api:
                self._write_api.write(bucket=self.influxdb_bucket, record=points)
                logger.info(f"✅ Flushed {len(self._metric_buffer)} buffered metrics to InfluxDB")
                self._metric_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing metrics buffer: {e}")
    
    async def get_fidelity_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Query fidelity trends from InfluxDB"""
        if not self.client or not self._query_api:
            return {"error": "InfluxDB not available"}
        
        try:
            query = f'''
            from(bucket: "{self.influxdb_bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r["_measurement"] == "fidelity_score")
                |> filter(fn: (r) => r["bot_name"] == "{self.bot_name}")
                |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
                |> yield(name: "mean")
            '''
            
            result = self._query_api.query(query)
            
            trends = []
            for table in result:
                for record in table.records:
                    trends.append({
                        "time": record.get_time(),
                        "value": record.get_value(),
                        "bot_name": record.values.get("bot_name")
                    })
            
            return {"trends": trends, "period_hours": hours}
            
        except Exception as e:
            logger.error(f"Error querying fidelity trends: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Close InfluxDB connection"""
        if self._client:
            self._client.close()
            logger.info("📊 InfluxDB connection closed")


# Global instance for easy access
_fidelity_metrics_collector: Optional[FidelityMetricsCollector] = None


def get_fidelity_metrics_collector() -> FidelityMetricsCollector:
    """Get global fidelity metrics collector instance"""
    global _fidelity_metrics_collector
    
    if _fidelity_metrics_collector is None:
        _fidelity_metrics_collector = FidelityMetricsCollector()
    
    return _fidelity_metrics_collector


def record_fidelity_optimization(optimization_metric: FidelityOptimizationMetric):
    """Convenience function to record fidelity optimization metrics"""
    collector = get_fidelity_metrics_collector()
    collector.record_fidelity_optimization(optimization_metric)


def record_memory_quality(user_id: str, operation: str, 
                         relevance_score: float, retrieval_time_ms: float,
                         memory_count: int, vector_similarity: float):
    """Convenience function to record memory quality metrics"""
    collector = get_fidelity_metrics_collector()
    collector.record_memory_quality(user_id, operation, relevance_score, 
                                   retrieval_time_ms, memory_count, vector_similarity)


def record_performance_metric(operation: str, duration_ms: float, 
                            success: bool = True, user_id: Optional[str] = None,
                            metadata: Optional[Dict] = None):
    """Convenience function to record performance metrics"""
    collector = get_fidelity_metrics_collector()
    collector.record_performance_metric(operation, duration_ms, success, user_id, metadata)


def record_emotion_and_stance(user_id: str, operation: str,
                             user_emotion: Optional[str] = None,
                             user_emotion_confidence: float = 0.0,
                             bot_emotion: Optional[str] = None,
                             bot_emotion_confidence: float = 0.0,
                             user_stance: Optional[str] = None,
                             user_self_focus: float = 0.0,
                             bot_stance: Optional[str] = None,
                             bot_self_focus: float = 0.0,
                             stance_confidence: float = 0.0):
    """
    Convenience function to record emotion and stance analysis metrics.
    
    This integrates stance analysis data into WhisperEngine's metrics collection,
    enabling tracking of emotional attribution accuracy and character consistency.
    """
    collector = get_fidelity_metrics_collector()
    collector.record_emotion_and_stance(
        user_id=user_id,
        operation=operation,
        user_emotion=user_emotion,
        user_emotion_confidence=user_emotion_confidence,
        bot_emotion=bot_emotion,
        bot_emotion_confidence=bot_emotion_confidence,
        user_stance=user_stance,
        user_self_focus=user_self_focus,
        bot_stance=bot_stance,
        bot_self_focus=bot_self_focus,
        stance_confidence=stance_confidence
    )