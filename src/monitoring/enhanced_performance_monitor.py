"""
Enhanced Performance Monitor with InfluxDB Integration

Extends the existing performance monitoring with time series data collection,
specifically designed for fidelity-first architecture monitoring.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
import psutil

# Import existing performance monitoring
from src.utils.performance_monitor import PerformanceMonitor, PerformanceMetric
from src.monitoring.fidelity_metrics_collector import (
    get_fidelity_metrics_collector, 
    FidelityOptimizationMetric,
    record_performance_metric,
    record_memory_quality
)

logger = logging.getLogger(__name__)


class FidelityFirstPerformanceMonitor(PerformanceMonitor):
    """
    Enhanced performance monitor with fidelity-first metrics collection.
    
    Extends the base PerformanceMonitor with:
    - Time series data storage in InfluxDB
    - Fidelity-specific metrics tracking
    - Character consistency monitoring
    - Optimization ratio analysis
    """
    
    def __init__(self, max_metrics_per_operation: int = 1000, enable_influxdb: bool = True):
        super().__init__(max_metrics_per_operation)
        
        self.enable_influxdb = enable_influxdb
        self.metrics_collector = get_fidelity_metrics_collector() if enable_influxdb else None
        
        # Fidelity-specific thresholds
        self.fidelity_thresholds = {
            'min_character_consistency': 0.85,
            'min_optimization_ratio': 0.70,
            'max_response_time_fidelity_ms': 5000,
            'min_memory_relevance': 0.75
        }
        
        logger.info("🎯 FidelityFirstPerformanceMonitor initialized with InfluxDB integration")
    
    def record_metric(self, operation: str, duration_ms: float, success: bool = True, 
                     metadata: Optional[Dict] = None, user_id: Optional[str] = None):
        """Enhanced metric recording with InfluxDB integration"""
        
        # Call parent implementation for in-memory metrics
        super().record_metric(operation, duration_ms, success, metadata, user_id)
        
        # Send to InfluxDB for time series analysis
        if self.enable_influxdb and self.metrics_collector:
            try:
                record_performance_metric(
                    operation=operation,
                    duration_ms=duration_ms,
                    success=success,
                    user_id=user_id,
                    metadata=metadata
                )
            except Exception as e:
                logger.warning("Failed to record metric to InfluxDB: %s", str(e))
    
    def record_fidelity_optimization(self, 
                                   operation: str,
                                   original_word_count: int,
                                   optimized_word_count: int,
                                   character_preservation_score: float,
                                   context_quality_score: float,
                                   full_fidelity_used: bool = True,
                                   intelligent_trimming_applied: bool = False):
        """Record fidelity-first optimization metrics"""
        
        try:
            # Calculate optimization ratio
            if original_word_count > 0:
                optimization_ratio = optimized_word_count / original_word_count
            else:
                optimization_ratio = 1.0
            
            # Create optimization metric
            optimization_metric = FidelityOptimizationMetric(
                operation=operation,
                original_word_count=original_word_count,
                optimized_word_count=optimized_word_count,
                optimization_ratio=optimization_ratio,
                character_preservation_score=character_preservation_score,
                context_quality_score=context_quality_score,
                full_fidelity_used=full_fidelity_used,
                intelligent_trimming_applied=intelligent_trimming_applied
            )
            
            # Send to metrics collector
            if self.enable_influxdb and self.metrics_collector:
                self.metrics_collector.record_fidelity_optimization(optimization_metric)
            
            # Check fidelity quality
            self._check_fidelity_quality(optimization_metric)
            
        except Exception as e:
            logger.error("Error recording fidelity optimization metrics: %s", str(e))
    
    def record_memory_operation(self, 
                              user_id: str,
                              operation: str,
                              retrieval_time_ms: float,
                              memory_count: int,
                              relevance_score: float,
                              vector_similarity: float):
        """Record memory system operation metrics"""
        
        try:
            # Record general performance metric
            self.record_metric(
                operation=f"memory_{operation}",
                duration_ms=retrieval_time_ms,
                success=True,
                user_id=user_id,
                metadata={
                    "memory_count": memory_count,
                    "relevance_score": relevance_score,
                    "vector_similarity": vector_similarity
                }
            )
            
            # Record memory quality metrics
            if self.enable_influxdb and self.metrics_collector:
                record_memory_quality(
                    user_id=user_id,
                    operation=operation,
                    relevance_score=relevance_score,
                    retrieval_time_ms=retrieval_time_ms,
                    memory_count=memory_count,
                    vector_similarity=vector_similarity
                )
            
            # Check memory quality
            self._check_memory_quality(relevance_score, retrieval_time_ms)
            
        except Exception as e:
            logger.error("Error recording memory operation metrics: %s", str(e))
    
    def _check_fidelity_quality(self, optimization_metric: FidelityOptimizationMetric):
        """Check fidelity quality against thresholds"""
        
        issues = []
        
        # Check character consistency
        if optimization_metric.character_preservation_score < self.fidelity_thresholds['min_character_consistency']:
            issues.append(f"Low character consistency: {optimization_metric.character_preservation_score:.2f}")
        
        # Check optimization ratio
        if optimization_metric.optimization_ratio < self.fidelity_thresholds['min_optimization_ratio']:
            issues.append(f"Heavy optimization applied: {optimization_metric.optimization_ratio:.2f}")
        
        # Log warnings if quality issues detected
        if issues:
            logger.warning("Fidelity quality issues in %s: %s", 
                         optimization_metric.operation, "; ".join(issues))
    
    def _check_memory_quality(self, relevance_score: float, retrieval_time_ms: float):
        """Check memory quality against thresholds"""
        
        issues = []
        
        # Check relevance score
        if relevance_score < self.fidelity_thresholds['min_memory_relevance']:
            issues.append(f"Low memory relevance: {relevance_score:.2f}")
        
        # Check retrieval time
        if retrieval_time_ms > self.fidelity_thresholds['max_response_time_fidelity_ms']:
            issues.append(f"Slow memory retrieval: {retrieval_time_ms:.0f}ms")
        
        # Log warnings if quality issues detected
        if issues:
            logger.warning("Memory quality issues: %s", "; ".join(issues))
    
    async def get_fidelity_dashboard_data(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive fidelity dashboard data"""
        
        try:
            dashboard_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "period_hours": hours,
                "in_memory_stats": {},
                "time_series_data": {},
                "system_health": self.get_system_health(),
                "bottlenecks": self.get_bottlenecks()
            }
            
            # Get in-memory performance stats
            all_stats = self.get_all_stats()
            dashboard_data["in_memory_stats"] = {
                operation: {
                    "avg_duration_ms": stats.avg_duration_ms,
                    "success_rate": stats.success_rate,
                    "total_calls": stats.total_calls,
                    "p95_duration_ms": stats.p95_duration_ms
                }
                for operation, stats in all_stats.items()
            }
            
            # Get time series data from InfluxDB
            if self.enable_influxdb and self.metrics_collector:
                try:
                    fidelity_trends = await self.metrics_collector.get_fidelity_trends(hours)
                    dashboard_data["time_series_data"] = fidelity_trends
                except Exception as e:
                    dashboard_data["time_series_data"] = {"error": str(e)}
            
            return dashboard_data
            
        except Exception as e:
            logger.error("Error generating fidelity dashboard data: %s", str(e))
            return {"error": str(e)}
    
    async def flush_metrics(self):
        """Flush buffered metrics to time series database"""
        if self.enable_influxdb and self.metrics_collector:
            await self.metrics_collector.flush_buffer()


# Global enhanced performance monitor instance
_fidelity_performance_monitor: Optional[FidelityFirstPerformanceMonitor] = None


def get_fidelity_performance_monitor() -> FidelityFirstPerformanceMonitor:
    """Get global fidelity performance monitor instance"""
    global _fidelity_performance_monitor
    
    if _fidelity_performance_monitor is None:
        _fidelity_performance_monitor = FidelityFirstPerformanceMonitor()
    
    return _fidelity_performance_monitor


def monitor_fidelity_performance(operation: str, include_optimization: bool = False):
    """
    Decorator for monitoring fidelity-first performance.
    
    Usage:
    @monitor_fidelity_performance("prompt_building", include_optimization=True)
    async def build_optimized_prompt(...):
        # Function implementation
        return result
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            monitor = get_fidelity_performance_monitor()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract user_id if available
                user_id = kwargs.get('user_id')
                if not user_id and args:
                    for arg in args:
                        if hasattr(arg, 'author') and hasattr(arg.author, 'id'):
                            user_id = str(arg.author.id)
                            break
                
                # Record basic performance
                monitor.record_metric(operation, duration_ms, True, user_id=user_id)
                
                # Record optimization metrics if enabled and result contains them
                if include_optimization and isinstance(result, dict):
                    if all(key in result for key in ['original_words', 'optimized_words', 'character_score']):
                        monitor.record_fidelity_optimization(
                            operation=operation,
                            original_word_count=result['original_words'],
                            optimized_word_count=result['optimized_words'], 
                            character_preservation_score=result.get('character_score', 1.0),
                            context_quality_score=result.get('context_score', 1.0),
                            full_fidelity_used=result.get('full_fidelity', True),
                            intelligent_trimming_applied=result.get('trimming_applied', False)
                        )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                monitor.record_metric(operation, duration_ms, False)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            monitor = get_fidelity_performance_monitor()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract user_id if available
                user_id = kwargs.get('user_id')
                
                # Record performance
                monitor.record_metric(operation, duration_ms, True, user_id=user_id)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                monitor.record_metric(operation, duration_ms, False)
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator