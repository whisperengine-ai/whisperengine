"""
WhisperEngine Health Monitoring System

Provides comprehensive system health monitoring, metrics collection,
and operational visibility for the WhisperEngine platform.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import psutil
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of system components to monitor."""
    LLM_SERVICE = "llm_service"
    DATABASE = "database"
    MEMORY_SYSTEM = "memory_system"
    DISCORD_BOT = "discord_bot"
    CACHE_SYSTEM = "cache_system"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    SYSTEM_RESOURCES = "system_resources"


@dataclass
class HealthMetric:
    """Individual health metric data."""
    name: str
    value: float
    unit: str
    status: HealthStatus
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    message: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ComponentHealth:
    """Health status for a specific system component."""
    component: ComponentType
    status: HealthStatus
    metrics: List[HealthMetric]
    last_check: datetime
    error_count: int = 0
    uptime: Optional[timedelta] = None
    details: Optional[Dict[str, Any]] = None
    
    def add_metric(self, metric: HealthMetric):
        """Add a metric to this component."""
        self.metrics.append(metric)
        
        # Update component status based on metric status
        if metric.status == HealthStatus.CRITICAL:
            self.status = HealthStatus.CRITICAL
        elif metric.status == HealthStatus.WARNING and self.status != HealthStatus.CRITICAL:
            self.status = HealthStatus.WARNING


@dataclass
class SystemHealth:
    """Overall system health status."""
    overall_status: HealthStatus
    components: Dict[ComponentType, ComponentHealth]
    timestamp: datetime
    uptime: timedelta
    total_errors: int = 0
    performance_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'overall_status': self.overall_status.value,
            'timestamp': self.timestamp.isoformat(),
            'uptime': str(self.uptime),
            'total_errors': self.total_errors,
            'performance_score': self.performance_score,
            'components': {
                comp_type.value: {
                    'status': comp_health.status.value,
                    'last_check': comp_health.last_check.isoformat(),
                    'error_count': comp_health.error_count,
                    'uptime': str(comp_health.uptime) if comp_health.uptime else None,
                    'metrics': [
                        {
                            'name': metric.name,
                            'value': metric.value,
                            'unit': metric.unit,
                            'status': metric.status.value,
                            'threshold_warning': metric.threshold_warning,
                            'threshold_critical': metric.threshold_critical,
                            'message': metric.message,
                            'timestamp': metric.timestamp.isoformat()
                        }
                        for metric in comp_health.metrics
                    ],
                    'details': comp_health.details
                }
                for comp_type, comp_health in self.components.items()
            }
        }


class HealthMonitor:
    """Comprehensive system health monitoring."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.start_time = datetime.now()
        self.last_health_check = None
        self.health_history: List[SystemHealth] = []
        self.max_history = self.config.get('max_history', 100)
        
        # Monitoring intervals (seconds)
        self.check_interval = self.config.get('check_interval', 30)
        self.full_check_interval = self.config.get('full_check_interval', 300)
        
        # Component status cache
        self._component_cache: Dict[ComponentType, ComponentHealth] = {}
        self._monitoring_active = False
        
        # Initialize component checkers
        self._checkers = {
            ComponentType.SYSTEM_RESOURCES: self._check_system_resources,
            ComponentType.FILE_SYSTEM: self._check_file_system,
            ComponentType.NETWORK: self._check_network,
            ComponentType.LLM_SERVICE: self._check_llm_service,
            ComponentType.DATABASE: self._check_database,
            ComponentType.MEMORY_SYSTEM: self._check_memory_system,
            ComponentType.CACHE_SYSTEM: self._check_cache_system,
            ComponentType.DISCORD_BOT: self._check_discord_bot
        }
        
        logger.info("Health monitor initialized")
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self._monitoring_active:
            logger.warning("Health monitoring already active")
            return
            
        self._monitoring_active = True
        logger.info("Starting health monitoring")
        
        # Start monitoring task
        asyncio.create_task(self._monitoring_loop())
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        self._monitoring_active = False
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        last_full_check = 0
        
        while self._monitoring_active:
            try:
                current_time = time.time()
                
                # Determine if we should do a full check
                do_full_check = (current_time - last_full_check) >= self.full_check_interval
                
                # Perform health check
                if do_full_check:
                    await self.check_system_health(full_check=True)
                    last_full_check = current_time
                else:
                    await self.check_system_health(full_check=False)
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def check_system_health(self, full_check: bool = True) -> SystemHealth:
        """Perform comprehensive system health check."""
        start_time = time.time()
        components = {}
        total_errors = 0
        
        # Check each component
        for component_type, checker in self._checkers.items():
            try:
                # Skip some checks for quick checks
                if not full_check and component_type in [ComponentType.DATABASE, ComponentType.LLM_SERVICE]:
                    # Use cached data for expensive checks
                    if component_type in self._component_cache:
                        components[component_type] = self._component_cache[component_type]
                        continue
                
                component_health = await checker()
                components[component_type] = component_health
                self._component_cache[component_type] = component_health
                total_errors += component_health.error_count
                
            except Exception as e:
                logger.error(f"Error checking {component_type.value}: {e}")
                # Create error component health
                components[component_type] = ComponentHealth(
                    component=component_type,
                    status=HealthStatus.CRITICAL,
                    metrics=[
                        HealthMetric(
                            name="check_error",
                            value=1,
                            unit="errors",
                            status=HealthStatus.CRITICAL,
                            message=f"Health check failed: {str(e)}"
                        )
                    ],
                    last_check=datetime.now(),
                    error_count=1
                )
                total_errors += 1
        
        # Calculate overall status
        overall_status = self._calculate_overall_status(components)
        
        # Calculate performance score
        performance_score = self._calculate_performance_score(components)
        
        # Create system health
        system_health = SystemHealth(
            overall_status=overall_status,
            components=components,
            timestamp=datetime.now(),
            uptime=datetime.now() - self.start_time,
            total_errors=total_errors,
            performance_score=performance_score
        )
        
        # Store in history
        self.health_history.append(system_health)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        self.last_health_check = system_health
        
        check_duration = time.time() - start_time
        logger.debug(f"Health check completed in {check_duration:.2f}s - Status: {overall_status.value}")
        
        return system_health
    
    def _calculate_overall_status(self, components: Dict[ComponentType, ComponentHealth]) -> HealthStatus:
        """Calculate overall system status from component statuses."""
        if not components:
            return HealthStatus.UNKNOWN
        
        statuses = [comp.status for comp in components.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.WARNING
    
    def _calculate_performance_score(self, components: Dict[ComponentType, ComponentHealth]) -> float:
        """Calculate overall performance score (0-100)."""
        if not components:
            return 0.0
        
        scores = []
        for component in components.values():
            if component.status == HealthStatus.HEALTHY:
                scores.append(100.0)
            elif component.status == HealthStatus.WARNING:
                scores.append(70.0)
            elif component.status == HealthStatus.CRITICAL:
                scores.append(30.0)
            else:
                scores.append(50.0)
        
        return sum(scores) / len(scores)
    
    # Component checker methods
    async def _check_system_resources(self) -> ComponentHealth:
        """Check system resource utilization."""
        metrics = []
        status = HealthStatus.HEALTHY
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_metric = HealthMetric(
                name="cpu_usage",
                value=cpu_percent,
                unit="percent",
                status=HealthStatus.HEALTHY if cpu_percent < 80 else 
                       HealthStatus.WARNING if cpu_percent < 95 else HealthStatus.CRITICAL,
                threshold_warning=80.0,
                threshold_critical=95.0
            )
            metrics.append(cpu_metric)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_metric = HealthMetric(
                name="memory_usage",
                value=memory.percent,
                unit="percent",
                status=HealthStatus.HEALTHY if memory.percent < 85 else 
                       HealthStatus.WARNING if memory.percent < 95 else HealthStatus.CRITICAL,
                threshold_warning=85.0,
                threshold_critical=95.0
            )
            metrics.append(memory_metric)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_metric = HealthMetric(
                name="disk_usage",
                value=disk_percent,
                unit="percent",
                status=HealthStatus.HEALTHY if disk_percent < 85 else 
                       HealthStatus.WARNING if disk_percent < 95 else HealthStatus.CRITICAL,
                threshold_warning=85.0,
                threshold_critical=95.0
            )
            metrics.append(disk_metric)
            
            # Update overall status
            critical_metrics = [m for m in metrics if m.status == HealthStatus.CRITICAL]
            warning_metrics = [m for m in metrics if m.status == HealthStatus.WARNING]
            
            if critical_metrics:
                status = HealthStatus.CRITICAL
            elif warning_metrics:
                status = HealthStatus.WARNING
                
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            status = HealthStatus.CRITICAL
            metrics.append(
                HealthMetric(
                    name="system_check_error",
                    value=1,
                    unit="errors",
                    status=HealthStatus.CRITICAL,
                    message=str(e)
                )
            )
        
        return ComponentHealth(
            component=ComponentType.SYSTEM_RESOURCES,
            status=status,
            metrics=metrics,
            last_check=datetime.now(),
            uptime=datetime.now() - self.start_time
        )
    
    async def _check_file_system(self) -> ComponentHealth:
        """Check file system accessibility."""
        metrics = []
        status = HealthStatus.HEALTHY
        
        try:
            # Check critical directories
            critical_paths = [
                Path('src'),
                Path('logs'),
                Path('data'),
                Path('.env.example')
            ]
            
            accessible_count = 0
            for path in critical_paths:
                try:
                    if path.exists():
                        accessible_count += 1
                except Exception:
                    pass
            
            accessibility_percent = (accessible_count / len(critical_paths)) * 100
            metrics.append(
                HealthMetric(
                    name="file_system_accessibility",
                    value=accessibility_percent,
                    unit="percent",
                    status=HealthStatus.HEALTHY if accessibility_percent == 100 else 
                           HealthStatus.WARNING if accessibility_percent >= 75 else HealthStatus.CRITICAL,
                    threshold_warning=75.0,
                    threshold_critical=50.0
                )
            )
            
            if accessibility_percent < 100:
                status = HealthStatus.WARNING if accessibility_percent >= 75 else HealthStatus.CRITICAL
                
        except Exception as e:
            logger.error(f"Error checking file system: {e}")
            status = HealthStatus.CRITICAL
            metrics.append(
                HealthMetric(
                    name="filesystem_check_error",
                    value=1,
                    unit="errors",
                    status=HealthStatus.CRITICAL,
                    message=str(e)
                )
            )
        
        return ComponentHealth(
            component=ComponentType.FILE_SYSTEM,
            status=status,
            metrics=metrics,
            last_check=datetime.now()
        )
    
    async def _check_network(self) -> ComponentHealth:
        """Check network connectivity."""
        metrics = []
        status = HealthStatus.HEALTHY
        
        try:
            # Basic network interface check
            network_stats = psutil.net_io_counters()
            if network_stats:
                metrics.append(
                    HealthMetric(
                        name="network_bytes_sent",
                        value=network_stats.bytes_sent,
                        unit="bytes",
                        status=HealthStatus.HEALTHY
                    )
                )
                metrics.append(
                    HealthMetric(
                        name="network_bytes_recv",
                        value=network_stats.bytes_recv,
                        unit="bytes",
                        status=HealthStatus.HEALTHY
                    )
                )
            else:
                status = HealthStatus.WARNING
                metrics.append(
                    HealthMetric(
                        name="network_unavailable",
                        value=1,
                        unit="status",
                        status=HealthStatus.WARNING,
                        message="Network statistics unavailable"
                    )
                )
                
        except Exception as e:
            logger.error(f"Error checking network: {e}")
            status = HealthStatus.CRITICAL
            metrics.append(
                HealthMetric(
                    name="network_check_error",
                    value=1,
                    unit="errors",
                    status=HealthStatus.CRITICAL,
                    message=str(e)
                )
            )
        
        return ComponentHealth(
            component=ComponentType.NETWORK,
            status=status,
            metrics=metrics,
            last_check=datetime.now()
        )
    
    async def _check_llm_service(self) -> ComponentHealth:
        """Check LLM service connectivity and response."""
        metrics = []
        status = HealthStatus.HEALTHY
        
        try:
            # This would integrate with the existing LLM client
            # For now, we'll check if the service is configured
            import os
            llm_url = os.getenv('LLM_CHAT_API_URL')
            llm_model = os.getenv('LLM_CHAT_MODEL')
            
            if llm_url and llm_model:
                metrics.append(
                    HealthMetric(
                        name="llm_configured",
                        value=1,
                        unit="status",
                        status=HealthStatus.HEALTHY,
                        message="LLM service configured"
                    )
                )
            else:
                status = HealthStatus.WARNING
                metrics.append(
                    HealthMetric(
                        name="llm_configured",
                        value=0,
                        unit="status",
                        status=HealthStatus.WARNING,
                        message="LLM service not fully configured"
                    )
                )
                
        except Exception as e:
            logger.error(f"Error checking LLM service: {e}")
            status = HealthStatus.CRITICAL
            metrics.append(
                HealthMetric(
                    name="llm_check_error",
                    value=1,
                    unit="errors",
                    status=HealthStatus.CRITICAL,
                    message=str(e)
                )
            )
        
        return ComponentHealth(
            component=ComponentType.LLM_SERVICE,
            status=status,
            metrics=metrics,
            last_check=datetime.now()
        )
    
    async def _check_database(self) -> ComponentHealth:
        """Check database connectivity and performance."""
        # Placeholder - would integrate with actual database checks
        return ComponentHealth(
            component=ComponentType.DATABASE,
            status=HealthStatus.HEALTHY,
            metrics=[
                HealthMetric(
                    name="database_responsive",
                    value=1,
                    unit="status",
                    status=HealthStatus.HEALTHY,
                    message="Database health check placeholder"
                )
            ],
            last_check=datetime.now()
        )
    
    async def _check_memory_system(self) -> ComponentHealth:
        """Check memory system health."""
        # Placeholder - would integrate with actual memory system checks
        return ComponentHealth(
            component=ComponentType.MEMORY_SYSTEM,
            status=HealthStatus.HEALTHY,
            metrics=[
                HealthMetric(
                    name="memory_system_responsive",
                    value=1,
                    unit="status",
                    status=HealthStatus.HEALTHY,
                    message="Memory system health check placeholder"
                )
            ],
            last_check=datetime.now()
        )
    
    async def _check_cache_system(self) -> ComponentHealth:
        """Check cache system health."""
        # Placeholder - would integrate with Redis/cache checks
        return ComponentHealth(
            component=ComponentType.CACHE_SYSTEM,
            status=HealthStatus.HEALTHY,
            metrics=[
                HealthMetric(
                    name="cache_responsive",
                    value=1,
                    unit="status",
                    status=HealthStatus.HEALTHY,
                    message="Cache system health check placeholder"
                )
            ],
            last_check=datetime.now()
        )
    
    async def _check_discord_bot(self) -> ComponentHealth:
        """Check Discord bot status."""
        # Placeholder - would integrate with Discord bot status
        return ComponentHealth(
            component=ComponentType.DISCORD_BOT,
            status=HealthStatus.HEALTHY,
            metrics=[
                HealthMetric(
                    name="discord_connected",
                    value=1,
                    unit="status",
                    status=HealthStatus.HEALTHY,
                    message="Discord bot health check placeholder"
                )
            ],
            last_check=datetime.now()
        )
    
    def get_current_health(self) -> Optional[SystemHealth]:
        """Get the current system health status."""
        return self.last_health_check
    
    def get_health_history(self, hours: int = 24) -> List[SystemHealth]:
        """Get health history for the specified number of hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [h for h in self.health_history if h.timestamp >= cutoff_time]
    
    def get_component_health(self, component: ComponentType) -> Optional[ComponentHealth]:
        """Get health status for a specific component."""
        if self.last_health_check:
            return self.last_health_check.components.get(component)
        return None
    
    def export_health_report(self, filepath: Optional[Path] = None) -> Dict[str, Any]:
        """Export comprehensive health report."""
        if not filepath:
            filepath = Path(f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'monitor_uptime': str(datetime.now() - self.start_time),
            'current_health': self.last_health_check.to_dict() if self.last_health_check else None,
            'health_history_count': len(self.health_history),
            'config': self.config
        }
        
        # Write to file if path provided
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Health report exported to {filepath}")
        
        return report


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor(config: Optional[Dict[str, Any]] = None) -> HealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor(config)
    return _health_monitor


async def initialize_health_monitoring(config: Optional[Dict[str, Any]] = None):
    """Initialize and start health monitoring."""
    monitor = get_health_monitor(config)
    await monitor.start_monitoring()
    return monitor