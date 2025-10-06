"""
Monitoring Integration

Centralized monitoring system integration for WhisperEngine.
Provides unified access to health monitoring, engagement tracking, and error tracking.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import monitoring components
from .health_monitor import get_health_monitor, initialize_health_monitoring, HealthStatus
from .error_tracker import get_error_tracker, track_error, ErrorSeverity, ErrorCategory, ErrorContext

# Placeholder for InteractionType (removed with engagement_tracker)
from enum import Enum

class InteractionType(Enum):
    """Stub for interaction types - engagement tracking moved to InfluxDB"""
    MESSAGE = "message"
    COMMAND = "command"

logger = logging.getLogger(__name__)


def _create_monitoring_config_from_env() -> Dict[str, Any]:
    """Create monitoring configuration from environment variables."""
    return {
        'enable_health_monitoring': True,  # Always enabled in development
        'enable_engagement_tracking': True,  # Always enabled in development
        'enable_error_tracking': True,  # Always enabled in development
        'enable_dashboard': os.getenv('ENABLE_MONITORING_DASHBOARD', 'false').lower() == 'true',
        'dashboard': {
            'host': os.getenv('DASHBOARD_HOST', '127.0.0.1'),
            'port': int(os.getenv('DASHBOARD_PORT', '8080')),
            'debug': os.getenv('DASHBOARD_DEBUG', 'false').lower() == 'true'
        },
        'health_monitor': {
            'check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
            'full_check_interval': int(os.getenv('HEALTH_FULL_CHECK_INTERVAL', '300')),
            'max_history': int(os.getenv('HEALTH_MAX_HISTORY', '100'))
        },
        'engagement_tracker': {
            'data_dir': os.getenv('ENGAGEMENT_DATA_DIR', 'data/engagement'),
            'session_timeout_minutes': int(os.getenv('ENGAGEMENT_SESSION_TIMEOUT', '30')),
            'max_history_days': int(os.getenv('ENGAGEMENT_MAX_HISTORY_DAYS', '90'))
        },
        'error_tracker': {
            'data_dir': os.getenv('ERROR_DATA_DIR', 'data/errors'),
            'pattern_detection_threshold': int(os.getenv('ERROR_PATTERN_THRESHOLD', '5')),
            'max_history_days': int(os.getenv('ERROR_MAX_HISTORY_DAYS', '30'))
        }
    }


class MonitoringManager:
    """Centralized monitoring system manager."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Use environment-based config if none provided
        if config is None:
            config = _create_monitoring_config_from_env()
        
        self.config = config
        self.initialized = False
        
        # Component instances
        self.health_monitor = None
        self.engagement_tracker = None
        self.error_tracker = None
        self.dashboard = None
        
        # Configuration
        self.enable_health_monitoring = self.config.get('enable_health_monitoring', True)
        self.enable_engagement_tracking = self.config.get('enable_engagement_tracking', True)
        self.enable_error_tracking = self.config.get('enable_error_tracking', True)
        self.enable_dashboard = self.config.get('enable_dashboard', False)
        
        # Dashboard configuration
        self.dashboard_config = self.config.get('dashboard', {})
        
        logger.info("Monitoring manager created")
    
    async def initialize(self):
        """Initialize all monitoring components."""
        if self.initialized:
            logger.debug("Monitoring already initialized - skipping duplicate initialization")
            return
        
        try:
            # Initialize health monitoring
            if self.enable_health_monitoring:
                self.health_monitor = get_health_monitor(self.config.get('health_monitor', {}))
                await initialize_health_monitoring(self.config.get('health_monitor', {}))
                logger.info("Health monitoring initialized")
            
            # Engagement tracking disabled - replaced with InfluxDB via FidelityMetricsCollector
            self.engagement_tracker = None
            
            # Initialize error tracking
            if self.enable_error_tracking:
                self.error_tracker = get_error_tracker(self.config.get('error_tracker', {}))
                logger.info("Error tracking initialized")
            
            # Initialize dashboard if enabled
            if self.enable_dashboard:
                try:
                    from .dashboard import get_dashboard
                    self.dashboard = get_dashboard(self.dashboard_config)
                    if self.dashboard.available:
                        await self.dashboard.start()
                        logger.info("Monitoring dashboard started")
                    else:
                        logger.warning("Dashboard unavailable - web dependencies missing")
                except ImportError as e:
                    logger.warning("Dashboard unavailable: %s", e)
            
            self.initialized = True
            logger.info("Monitoring system fully initialized")
            
        except Exception as e:
            logger.error("Error initializing monitoring: %s", e)
            raise
    
    async def shutdown(self):
        """Shutdown all monitoring components."""
        if not self.initialized:
            return
        
        try:
            # Stop dashboard
            if self.dashboard:
                await self.dashboard.stop()
                logger.info("Dashboard stopped")
            
            # Stop health monitoring
            if self.health_monitor:
                self.health_monitor.stop_monitoring()
                logger.info("Health monitoring stopped")
            
            # Clean up components
            if self.engagement_tracker:
                self.engagement_tracker.cleanup_old_sessions()
                logger.info("Engagement tracking cleaned up")
            
            if self.error_tracker:
                self.error_tracker.cleanup_old_errors()
                logger.info("Error tracking cleaned up")
            
            self.initialized = False
            logger.info("Monitoring system shutdown complete")
            
        except Exception as e:
            logger.error("Error during monitoring shutdown: %s", e)
    
    # Health monitoring interface
    def get_system_health(self):
        """Get current system health status."""
        if self.health_monitor:
            return self.health_monitor.get_current_health()
        return None
    
    async def check_health(self, full_check: bool = False):
        """Perform health check."""
        if self.health_monitor:
            return await self.health_monitor.check_system_health(full_check)
        return None
    
    def get_health_history(self, hours: int = 24):
        """Get health history."""
        if self.health_monitor:
            return self.health_monitor.get_health_history(hours)
        return []
    
    # Engagement tracking interface
    def start_user_session(self, user_id: str, platform: str = 'discord') -> Optional[str]:
        """Start a user session."""
        if self.engagement_tracker:
            return self.engagement_tracker.start_session(user_id, platform)
        return None
    
    def end_user_session(self, user_id: str):
        """End a user session."""
        if self.engagement_tracker:
            self.engagement_tracker.end_session(user_id)
    
    def track_user_interaction(self, user_id: str, interaction_type: InteractionType, 
                              metadata: Optional[Dict[str, Any]] = None):
        """Track a user interaction."""
        if self.engagement_tracker:
            self.engagement_tracker.track_interaction(user_id, interaction_type, metadata)
    
    def track_message(self, user_id: str, message_length: int = 0, response_time: Optional[float] = None):
        """Convenience method to track a message interaction."""
        metadata: Dict[str, Any] = {'message_length': message_length}
        if response_time is not None:
            metadata['response_time'] = response_time
        self.track_user_interaction(user_id, InteractionType.MESSAGE, metadata)
    
    def track_command(self, user_id: str, command_name: str, response_time: Optional[float] = None):
        """Convenience method to track a command interaction."""
        metadata: Dict[str, Any] = {'command_name': command_name}
        if response_time is not None:
            metadata['response_time'] = response_time
        self.track_user_interaction(user_id, InteractionType.COMMAND, metadata)
    
    def get_engagement_summary(self):
        """Get engagement summary."""
        if self.engagement_tracker:
            return self.engagement_tracker.generate_engagement_summary()
        return None
    
    def get_active_users(self, hours: int = 24) -> List[str]:
        """Get list of active users."""
        if self.engagement_tracker:
            return self.engagement_tracker.get_active_users(hours)
        return []
    
    # Error tracking interface
    def track_error(self, exception: Exception, context: Optional[ErrorContext] = None,
                   severity: Optional[ErrorSeverity] = None,
                   category: Optional[ErrorCategory] = None) -> Optional[str]:
        """Track an error."""
        if self.error_tracker:
            return self.error_tracker.track_error(exception, context, severity, category)
        return None
    
    def track_user_error(self, exception: Exception, user_id: str, command: Optional[str] = None,
                        platform: str = 'discord') -> Optional[str]:
        """Convenience method to track a user-related error."""
        context = ErrorContext(
            user_id=user_id,
            command=command,
            platform=platform
        )
        return self.track_error(exception, context)
    
    def get_error_summary(self, hours: int = 24):
        """Get error summary."""
        if self.error_tracker:
            return self.error_tracker.get_error_summary(hours)
        return {}
    
    def get_error_patterns(self):
        """Get identified error patterns."""
        if self.error_tracker:
            return list(self.error_tracker.error_patterns.values())
        return []
    
    # Dashboard interface
    def get_dashboard_url(self) -> Optional[str]:
        """Get dashboard URL if available."""
        if self.dashboard and self.dashboard.available:
            return f"http://{self.dashboard.host}:{self.dashboard.port}"
        return None
    
    def is_dashboard_running(self) -> bool:
        """Check if dashboard is running."""
        return (self.dashboard is not None and 
                self.dashboard.available and 
                self.dashboard.runner is not None)
    
    # Combined monitoring methods
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview."""
        overview = {
            'timestamp': datetime.now().isoformat(),
            'monitoring_enabled': {
                'health': self.enable_health_monitoring,
                'engagement': self.enable_engagement_tracking,
                'errors': self.enable_error_tracking,
                'dashboard': self.enable_dashboard
            }
        }
        
        # Add health data
        if self.health_monitor:
            health = self.health_monitor.get_current_health()
            overview['health'] = health.to_dict() if health else None
        
        # Add engagement data
        if self.engagement_tracker:
            engagement = self.engagement_tracker.generate_engagement_summary()
            overview['engagement'] = engagement.to_dict()
        
        # Add error data
        if self.error_tracker:
            overview['errors'] = self.error_tracker.get_error_summary(24)
        
        # Add dashboard info
        overview['dashboard'] = {
            'available': self.is_dashboard_running(),
            'url': self.get_dashboard_url()
        }
        
        return overview
    
    def export_monitoring_report(self, days: int = 7) -> Dict[str, Any]:
        """Export comprehensive monitoring report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'report_period_days': days,
            'system_overview': self.get_system_overview()
        }
        
        # Add detailed reports from each component
        if self.health_monitor:
            report['health_report'] = self.health_monitor.export_health_report()
        
        if self.engagement_tracker:
            report['engagement_report'] = self.engagement_tracker.export_engagement_report(days)
        
        if self.error_tracker:
            report['error_report'] = self.error_tracker.export_error_report(days)
        
        return report


# Global monitoring manager instance
_monitoring_manager: Optional[MonitoringManager] = None


def get_monitoring_manager(config: Optional[Dict[str, Any]] = None) -> MonitoringManager:
    """Get the global monitoring manager instance."""
    # Using global state for singleton pattern
    # pylint: disable=global-statement
    global _monitoring_manager
    if _monitoring_manager is None:
        _monitoring_manager = MonitoringManager(config)
    return _monitoring_manager


async def initialize_monitoring(config: Optional[Dict[str, Any]] = None) -> MonitoringManager:
    """Initialize the monitoring system."""
    manager = get_monitoring_manager(config)
    await manager.initialize()
    return manager


async def shutdown_monitoring():
    """Shutdown the monitoring system."""
    global _monitoring_manager
    if _monitoring_manager:
        await _monitoring_manager.shutdown()


# Convenience functions for easy integration
def track_error_simple(exception: Exception, user_id: Optional[str] = None, 
                      command: Optional[str] = None) -> Optional[str]:
    """Simple error tracking function."""
    manager = get_monitoring_manager()
    if user_id:
        return manager.track_user_error(exception, user_id, command)
    else:
        return manager.track_error(exception)


def track_user_message(user_id: str, message_length: int = 0, response_time: Optional[float] = None):
    """Simple message tracking function."""
    manager = get_monitoring_manager()
    manager.track_message(user_id, message_length, response_time)


def track_user_command(user_id: str, command_name: str, response_time: Optional[float] = None):
    """Simple command tracking function."""
    manager = get_monitoring_manager()
    manager.track_command(user_id, command_name, response_time)


def get_system_status() -> Dict[str, Any]:
    """Get quick system status."""
    manager = get_monitoring_manager()
    return manager.get_system_overview()