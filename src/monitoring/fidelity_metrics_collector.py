"""
Fidelity-First Performance Metrics Collector for InfluxDB

Comprehensive time series data collection for WhisperEngine's fidelity-first architecture.
Tracks character consistency, optimization ratios, memory quality, and performance metrics.
"""

import asyncio
import logging
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
    # Fallback implementation
    import os
    def get_normalized_bot_name_from_env() -> str:
        bot_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
        if not bot_name or not isinstance(bot_name, str):
            return "unknown"
        return bot_name.strip().lower().replace(' ', '_')

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of fidelity-first metrics to track"""
    FIDELITY_SCORE = "fidelity_score"
    CHARACTER_CONSISTENCY = "character_consistency"
    OPTIMIZATION_RATIO = "optimization_ratio"
    MEMORY_QUALITY = "memory_quality"
    RESPONSE_TIME = "response_time"
    TOKEN_USAGE = "token_usage"
    SYSTEM_PERFORMANCE = "system_performance"
    USER_ENGAGEMENT = "user_engagement"


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
                 influxdb_url: str = "http://localhost:8086",
                 influxdb_token: str = "whisperengine-fidelity-first-metrics-token",
                 influxdb_org: str = "whisperengine",
                 influxdb_bucket: str = "performance_metrics"):
        
        self.influxdb_url = influxdb_url
        self.influxdb_token = influxdb_token
        self.influxdb_org = influxdb_org
        self.influxdb_bucket = influxdb_bucket
        
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
            # Memory quality score
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
            
            # Response time for memory operations
            self.record_metric(FidelityMetric(
                metric_type=MetricType.RESPONSE_TIME,
                value=retrieval_time_ms,
                bot_name=self.bot_name,
                user_id=user_id,
                operation=f"memory_{operation}",
                tags={
                    "operation_type": "memory_retrieval"
                }
            ))
            
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
            
            # System performance snapshot
            process = psutil.Process()
            self.record_metric(FidelityMetric(
                metric_type=MetricType.SYSTEM_PERFORMANCE,
                value=process.cpu_percent(),
                bot_name=self.bot_name,
                operation=operation,
                fields={
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "cpu_percent": process.cpu_percent(),
                    "operation_duration_ms": duration_ms,
                    "operation_success": 1 if success else 0
                }
            ))
            
        except Exception as e:
            logger.error(f"Error recording performance metrics: {e}")
    
    def record_user_engagement(self, user_id: str, engagement_score: float,
                             conversation_length: int, response_quality: float):
        """Record user engagement metrics"""
        try:
            self.record_metric(FidelityMetric(
                metric_type=MetricType.USER_ENGAGEMENT,
                value=engagement_score,
                bot_name=self.bot_name,
                user_id=user_id,
                fields={
                    "conversation_length": conversation_length,
                    "response_quality": response_quality
                }
            ))
        except Exception as e:
            logger.error(f"Error recording user engagement metrics: {e}")
    
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
        
        # Add custom tags
        for key, value in metric.tags.items():
            point = point.tag(key, value)
        
        # Add value as main field
        point = point.field("value", metric.value)
        
        # Add additional fields
        for key, value in metric.fields.items():
            point = point.field(key, value)
        
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