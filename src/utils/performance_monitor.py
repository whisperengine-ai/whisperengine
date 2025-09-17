#!/usr/bin/env python3
"""
Performance Monitor and Optimization System
Real-time performance tracking, bottleneck identification, and automatic optimization for WhisperEngine
"""

import time
import asyncio
import logging
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
from datetime import datetime, timedelta
import functools
import psutil
import threading
import weakref

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance measurement"""
    operation: str
    duration_ms: float
    timestamp: datetime
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None


@dataclass
class PerformanceStats:
    """Aggregated performance statistics"""
    operation: str
    total_calls: int
    success_rate: float
    avg_duration_ms: float
    median_duration_ms: float
    p95_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    last_updated: datetime
    
    def is_degraded(self, baseline_ms: float = 1000) -> bool:
        """Check if performance is degraded compared to baseline"""
        return self.p95_duration_ms > baseline_ms * 2 or self.success_rate < 0.95


class PerformanceMonitor:
    """
    Real-time performance monitoring with automatic bottleneck detection
    """
    
    def __init__(self, max_metrics_per_operation: int = 1000):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_metrics_per_operation))
        self.stats_cache: Dict[str, PerformanceStats] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=5)
        
        # Performance baselines (in milliseconds)
        self.baselines = {
            'llm_request': 3000,
            'memory_retrieval': 200,
            'database_query': 100,
            'discord_api': 500,
            'image_processing': 2000,
            'emotion_analysis': 1000,
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'slow_operation_ms': 5000,
            'low_success_rate': 0.90,
            'high_memory_mb': 500,
            'high_cpu_percent': 80
        }
        
        # Background monitoring
        self._monitoring_task = None
        self._running = False
        
    def start_monitoring(self):
        """Start background performance monitoring"""
        if not self._running:
            self._running = True
            self._monitoring_task = asyncio.create_task(self._background_monitor())
            logger.info("📊 Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background performance monitoring"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            logger.info("📊 Performance monitoring stopped")
    
    def record_metric(self, operation: str, duration_ms: float, success: bool = True, 
                     metadata: Optional[Dict] = None, user_id: Optional[str] = None):
        """Record a performance metric"""
        
        # Get system stats
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        metric = PerformanceMetric(
            operation=operation,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            success=success,
            metadata=metadata or {},
            user_id=user_id,
            memory_usage_mb=memory_mb,
            cpu_percent=cpu_percent
        )
        
        self.metrics[operation].append(metric)
        
        # Invalidate cache for this operation
        if operation in self.cache_expiry:
            del self.cache_expiry[operation]
            del self.stats_cache[operation]
        
        # Check for immediate alerts
        self._check_alerts(metric)
    
    def get_stats(self, operation: str) -> Optional[PerformanceStats]:
        """Get performance statistics for an operation"""
        
        # Check cache
        if operation in self.cache_expiry:
            if datetime.now() < self.cache_expiry[operation]:
                return self.stats_cache[operation]
        
        # Calculate fresh stats
        if operation not in self.metrics or not self.metrics[operation]:
            return None
        
        metrics = list(self.metrics[operation])
        if not metrics:
            return None
        
        durations = [m.duration_ms for m in metrics]
        successes = [1 if m.success else 0 for m in metrics]  # Convert booleans to integers
        
        stats = PerformanceStats(
            operation=operation,
            total_calls=len(metrics),
            success_rate=sum(successes) / len(successes) if successes else 0,
            avg_duration_ms=statistics.mean(durations),
            median_duration_ms=statistics.median(durations),
            p95_duration_ms=self._percentile(durations, 95),
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            last_updated=datetime.now()
        )
        
        # Cache results
        self.stats_cache[operation] = stats
        self.cache_expiry[operation] = datetime.now() + self.cache_duration
        
        return stats
    
    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """Get performance statistics for all operations"""
        all_stats = {}
        for operation in self.metrics.keys():
            stats = self.get_stats(operation)
            if stats:
                all_stats[operation] = stats
        return all_stats
    
    def get_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify current performance bottlenecks"""
        bottlenecks = []
        
        for operation, stats in self.get_all_stats().items():
            baseline = self.baselines.get(operation, 1000)
            
            issues = []
            
            # Check response time
            if stats.p95_duration_ms > baseline * 2:
                issues.append(f"P95 response time ({stats.p95_duration_ms:.0f}ms) is {stats.p95_duration_ms/baseline:.1f}x baseline")
            
            # Check success rate
            if stats.success_rate < 0.95:
                issues.append(f"Success rate ({stats.success_rate:.1%}) is below 95%")
            
            # Check for high variance
            if stats.max_duration_ms > stats.avg_duration_ms * 5:
                issues.append(f"High variance: max ({stats.max_duration_ms:.0f}ms) vs avg ({stats.avg_duration_ms:.0f}ms)")
            
            if issues:
                bottlenecks.append({
                    'operation': operation,
                    'severity': 'high' if stats.p95_duration_ms > baseline * 5 else 'medium',
                    'issues': issues,
                    'stats': stats,
                    'recommendations': self._get_optimization_recommendations(operation, stats)
                })
        
        # Sort by severity
        bottlenecks.sort(key=lambda x: (x['severity'] == 'high', x['stats'].p95_duration_ms), reverse=True)
        return bottlenecks
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        process = psutil.Process()
        
        # Calculate overall metrics
        all_stats = self.get_all_stats()
        if all_stats:
            avg_success_rate = statistics.mean([s.success_rate for s in all_stats.values()])
            avg_response_time = statistics.mean([s.avg_duration_ms for s in all_stats.values()])
        else:
            avg_success_rate = 1.0
            avg_response_time = 0.0
        
        # Get recent memory usage
        recent_memory = []
        for metrics in self.metrics.values():
            for metric in list(metrics)[-10:]:  # Last 10 metrics
                if metric.memory_usage_mb:
                    recent_memory.append(metric.memory_usage_mb)
        
        return {
            'overall_health': 'good' if avg_success_rate > 0.95 and avg_response_time < 2000 else 'degraded',
            'avg_success_rate': avg_success_rate,
            'avg_response_time_ms': avg_response_time,
            'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
            'memory_trend': 'stable' if not recent_memory else ('increasing' if len(recent_memory) > 5 and recent_memory[-1] > recent_memory[0] * 1.2 else 'stable'),
            'active_operations': len(all_stats),
            'total_metrics': sum(len(metrics) for metrics in self.metrics.values()),
            'bottlenecks_count': len(self.get_bottlenecks())
        }
    
    async def _background_monitor(self):
        """Background monitoring loop"""
        while self._running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Clean old metrics
                cutoff_time = datetime.now() - timedelta(hours=1)
                for operation, metrics in self.metrics.items():
                    # Remove old metrics
                    while metrics and metrics[0].timestamp < cutoff_time:
                        metrics.popleft()
                
                # Check for system-wide issues
                health = self.get_system_health()
                if health['overall_health'] == 'degraded':
                    logger.warning("⚠️ System performance degraded: %.1f%% success rate, %.0fms avg response time", 
                                 health['avg_success_rate'] * 100, health['avg_response_time_ms'])
                
                # Report bottlenecks
                bottlenecks = self.get_bottlenecks()
                if bottlenecks:
                    logger.info("📊 Performance bottlenecks detected: %d operations", len(bottlenecks))
                    for bottleneck in bottlenecks[:3]:  # Top 3
                        logger.info("   • %s: %s", bottleneck['operation'], bottleneck['issues'][0])
                
            except Exception as e:
                logger.error("Background monitoring error: %s", e)
    
    def _check_alerts(self, metric: PerformanceMetric):
        """Check if metric triggers any alerts"""
        
        # Slow operation alert
        if metric.duration_ms > self.alert_thresholds['slow_operation_ms']:
            logger.warning("🐌 Slow operation detected: %s took %.0fms", 
                         metric.operation, metric.duration_ms)
        
        # High memory usage alert
        if metric.memory_usage_mb and metric.memory_usage_mb > self.alert_thresholds['high_memory_mb']:
            logger.warning("🧠 High memory usage: %.0fMB during %s", 
                         metric.memory_usage_mb, metric.operation)
        
        # High CPU usage alert
        if metric.cpu_percent and metric.cpu_percent > self.alert_thresholds['high_cpu_percent']:
            logger.warning("⚡ High CPU usage: %.1f%% during %s", 
                         metric.cpu_percent, metric.operation)
    
    def _get_optimization_recommendations(self, operation: str, stats: PerformanceStats) -> List[str]:
        """Get optimization recommendations for an operation"""
        recommendations = []
        
        # Operation-specific recommendations
        if 'llm' in operation.lower():
            if stats.avg_duration_ms > 5000:
                recommendations.append("Consider using a smaller/faster model")
                recommendations.append("Implement response streaming")
                recommendations.append("Add request timeout handling")
        
        elif 'memory' in operation.lower():
            if stats.avg_duration_ms > 500:
                recommendations.append("Add memory result caching")
                recommendations.append("Optimize database query patterns")
                recommendations.append("Consider memory system indexing")
        
        elif 'database' in operation.lower():
            if stats.avg_duration_ms > 200:
                recommendations.append("Add database connection pooling")
                recommendations.append("Optimize queries with proper indexes")
                recommendations.append("Consider caching frequent queries")
        
        elif 'discord' in operation.lower():
            if stats.success_rate < 0.95:
                recommendations.append("Implement exponential backoff for retries")
                recommendations.append("Add rate limit handling")
                recommendations.append("Check Discord API status")
        
        # General recommendations
        if stats.success_rate < 0.90:
            recommendations.append("Add better error handling and recovery")
            
        if stats.max_duration_ms > stats.avg_duration_ms * 10:
            recommendations.append("Investigate timeout edge cases")
            
        return recommendations
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(
    operation: str,
    include_metadata: bool = True,
    timeout_ms: Optional[float] = None
):
    """
    Decorator for automatic performance monitoring
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            metadata = {}
            
            try:
                # Add timeout if specified
                if timeout_ms:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs), 
                        timeout=timeout_ms / 1000
                    )
                else:
                    result = await func(*args, **kwargs)
                
                # Extract metadata if requested
                if include_metadata:
                    if hasattr(result, '__dict__'):
                        metadata['result_type'] = type(result).__name__
                    if isinstance(result, str):
                        metadata['response_length'] = len(result)
                
                return result
                
            except asyncio.TimeoutError:
                success = False
                metadata['error'] = 'timeout'
                raise
            except Exception as e:
                success = False
                metadata['error'] = type(e).__name__
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract user_id from common parameter patterns
                user_id = None
                if 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                elif args and hasattr(args[0], 'author') and hasattr(args[0].author, 'id'):
                    user_id = str(args[0].author.id)  # Discord context
                
                performance_monitor.record_metric(
                    operation=operation,
                    duration_ms=duration_ms,
                    success=success,
                    metadata=metadata,
                    user_id=user_id
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            metadata = {}
            
            try:
                result = func(*args, **kwargs)
                
                # Extract metadata if requested
                if include_metadata:
                    if hasattr(result, '__dict__'):
                        metadata['result_type'] = type(result).__name__
                    if isinstance(result, str):
                        metadata['response_length'] = len(result)
                
                return result
                
            except Exception as e:
                success = False
                metadata['error'] = type(e).__name__
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract user_id from common parameter patterns
                user_id = None
                if 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                elif args and hasattr(args[0], 'author') and hasattr(args[0].author, 'id'):
                    user_id = str(args[0].author.id)  # Discord context
                
                performance_monitor.record_metric(
                    operation=operation,
                    duration_ms=duration_ms,
                    success=success,
                    metadata=metadata,
                    user_id=user_id
                )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class PerformanceOptimizer:
    """
    Automatic performance optimization based on monitoring data
    """
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.optimizations_applied = {}
        
    def suggest_optimizations(self) -> List[Dict[str, Any]]:
        """Suggest performance optimizations based on current data"""
        suggestions = []
        
        bottlenecks = self.monitor.get_bottlenecks()
        health = self.monitor.get_system_health()
        
        # Memory optimization suggestions
        if health['memory_usage_mb'] > 300:
            suggestions.append({
                'type': 'memory',
                'priority': 'high' if health['memory_usage_mb'] > 500 else 'medium',
                'description': f"High memory usage: {health['memory_usage_mb']:.0f}MB",
                'actions': [
                    'Clear conversation cache periodically',
                    'Optimize memory manager retention',
                    'Review large object storage'
                ]
            })
        
        # Response time optimization suggestions
        for bottleneck in bottlenecks:
            if bottleneck['severity'] == 'high':
                suggestions.append({
                    'type': 'performance',
                    'priority': 'high',
                    'description': f"Slow operation: {bottleneck['operation']}",
                    'actions': bottleneck['recommendations']
                })
        
        # System-wide suggestions
        if health['avg_success_rate'] < 0.95:
            suggestions.append({
                'type': 'reliability',
                'priority': 'high',
                'description': f"Low success rate: {health['avg_success_rate']:.1%}",
                'actions': [
                    'Improve error handling',
                    'Add retry mechanisms',
                    'Monitor external service health'
                ]
            })
        
        return suggestions
    
    def get_optimization_report(self) -> str:
        """Generate a comprehensive optimization report"""
        health = self.monitor.get_system_health()
        bottlenecks = self.monitor.get_bottlenecks()
        suggestions = self.suggest_optimizations()
        
        report = "📊 **Performance Optimization Report**\\n\\n"
        
        # System health summary
        report += f"🏥 **System Health**: {health['overall_health'].title()}\\n"
        report += f"   • Success Rate: {health['avg_success_rate']:.1%}\\n"
        report += f"   • Avg Response Time: {health['avg_response_time_ms']:.0f}ms\\n"
        report += f"   • Memory Usage: {health['memory_usage_mb']:.0f}MB\\n"
        report += f"   • Active Operations: {health['active_operations']}\\n\\n"
        
        # Bottlenecks
        if bottlenecks:
            report += f"🔍 **Performance Bottlenecks** ({len(bottlenecks)} found):\\n"
            for i, bottleneck in enumerate(bottlenecks[:5], 1):
                report += f"{i}. **{bottleneck['operation']}** ({bottleneck['severity']} priority)\\n"
                report += f"   • {bottleneck['issues'][0]}\\n"
                if bottleneck['recommendations']:
                    report += f"   • Recommendation: {bottleneck['recommendations'][0]}\\n"
            report += "\\n"
        
        # Optimization suggestions
        if suggestions:
            report += f"💡 **Optimization Suggestions** ({len(suggestions)} items):\\n"
            high_priority = [s for s in suggestions if s['priority'] == 'high']
            medium_priority = [s for s in suggestions if s['priority'] == 'medium']
            
            if high_priority:
                report += "**High Priority:**\\n"
                for suggestion in high_priority:
                    report += f"• {suggestion['description']}\\n"
                    report += f"  Action: {suggestion['actions'][0]}\\n"
            
            if medium_priority:
                report += "**Medium Priority:**\\n"
                for suggestion in medium_priority:
                    report += f"• {suggestion['description']}\\n"
        else:
            report += "✅ **No immediate optimizations needed**\\n"
        
        return report


# Global optimizer instance
performance_optimizer = PerformanceOptimizer(performance_monitor)