"""
Example Integration of Monitoring System

This file demonstrates how to integrate the monitoring system 
into the main WhisperEngine application components.
"""

import asyncio
import logging
from typing import Optional

# Example integration with DiscordBotCore
class MonitoringIntegration:
    """Example of how to integrate monitoring into DiscordBotCore."""
    
    def __init__(self, bot_core):
        self.bot_core = bot_core
        self.monitoring_manager = None
        
    async def initialize_monitoring(self):
        """Initialize monitoring system."""
        from .monitoring import initialize_monitoring
        
        # Configure monitoring based on environment
        config = {
            'enable_health_monitoring': True,
            'enable_engagement_tracking': True,
            'enable_error_tracking': True,
            'enable_dashboard': True,  # Enable dashboard for admin visibility
            'dashboard': {
                'host': '127.0.0.1',
                'port': 8080,
                'debug': False
            },
            'health_monitor': {
                'check_interval': 30,      # Check every 30 seconds
                'full_check_interval': 300, # Full check every 5 minutes
                'max_history': 100
            },
            'engagement_tracker': {
                'data_dir': 'data/engagement',
                'session_timeout_minutes': 30,
                'max_history_days': 90
            },
            'error_tracker': {
                'data_dir': 'data/errors',
                'pattern_detection_threshold': 5,
                'max_history_days': 30
            }
        }
        
        self.monitoring_manager = await initialize_monitoring(config)
        logging.info("Monitoring system initialized")
        
        return self.monitoring_manager
    
    def register_monitoring_commands(self, bot):
        """Register monitoring commands with the bot. (DISABLED - commands deleted)"""
        # Monitoring commands have been deleted as they were unused bloat
        logging.info("⚠️ Monitoring commands disabled - handlers were deleted")
    
    async def track_user_interaction(self, user_id: str, interaction_type: str, 
                                   command_name: Optional[str] = None,
                                   message_length: int = 0,
                                   response_time: Optional[float] = None):
        """Track user interactions for engagement metrics."""
        if not self.monitoring_manager:
            return
        
        if interaction_type == 'message':
            self.monitoring_manager.track_message(user_id, message_length, response_time)
        elif interaction_type == 'command':
            self.monitoring_manager.track_command(user_id, command_name or 'unknown', response_time)
    
    def track_error(self, exception: Exception, user_id: Optional[str] = None,
                   command: Optional[str] = None) -> Optional[str]:
        """Track errors for monitoring."""
        if not self.monitoring_manager:
            return None
        
        if user_id:
            return self.monitoring_manager.track_user_error(exception, user_id, command)
        else:
            return self.monitoring_manager.track_error(exception)
    
    async def get_system_status(self) -> dict:
        """Get current system status for health checks."""
        if not self.monitoring_manager:
            return {'status': 'monitoring_unavailable'}
        
        return self.monitoring_manager.get_system_overview()
    
    async def shutdown_monitoring(self):
        """Shutdown monitoring system."""
        if self.monitoring_manager:
            await self.monitoring_manager.shutdown()
            logging.info("Monitoring system shutdown")


# Example Discord Bot Integration
"""
# In src/core/bot.py or similar main bot file:

class DiscordBotCore:
    def __init__(self, debug_mode=False):
        # ... existing initialization ...
        
        # Add monitoring integration
        self.monitoring = MonitoringIntegration(self)
    
    async def setup(self):
        # ... existing setup ...
        
        # Initialize monitoring
        await self.monitoring.initialize_monitoring()
        
        # Register monitoring commands
        self.monitoring.register_monitoring_commands(self.bot)
    
    async def on_message(self, message):
        try:
            # ... existing message handling ...
            
            # Track user interaction
            if not message.author.bot:
                await self.monitoring.track_user_interaction(
                    str(message.author.id), 
                    'message',
                    message_length=len(message.content)
                )
                
        except Exception as e:
            # Track error
            error_id = self.monitoring.track_error(e, str(message.author.id))
            logging.error(f"Error in message handling (tracked: {error_id}): {e}")
    
    async def on_command(self, ctx):
        try:
            start_time = time.time()
            
            # ... existing command handling ...
            
            # Track command usage
            response_time = time.time() - start_time
            await self.monitoring.track_user_interaction(
                str(ctx.author.id),
                'command', 
                command_name=ctx.command.name,
                response_time=response_time
            )
            
        except Exception as e:
            # Track error
            error_id = self.monitoring.track_error(e, str(ctx.author.id), ctx.command.name)
            logging.error(f"Error in command handling (tracked: {error_id}): {e}")
    
    async def shutdown(self):
        # ... existing shutdown ...
        
        # Shutdown monitoring
        await self.monitoring.shutdown_monitoring()
"""


# Example Health Check Endpoint
"""
# For web-based health checks or API endpoints:

async def health_check_endpoint(request):
    '''Health check endpoint for load balancers/monitoring.'''
    try:
        from .monitoring import get_monitoring_manager
        
        manager = get_monitoring_manager()
        overview = manager.get_system_overview()
        
        # Determine overall health
        health_status = overview.get('health', {}).get('overall_status', 'unknown')
        
        if health_status == 'critical':
            status_code = 503  # Service Unavailable
        elif health_status == 'warning':
            status_code = 200  # OK but with warnings
        elif health_status == 'healthy':
            status_code = 200  # OK
        else:
            status_code = 503  # Unknown state treated as unhealthy
        
        return web.json_response(overview, status=status_code)
        
    except Exception as e:
        return web.json_response(
            {'error': 'Health check failed', 'details': str(e)}, 
            status=500
        )
"""


# Example Error Handler Decorator
"""
def monitor_errors(func):
    '''Decorator to automatically track errors from functions.'''
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Track the error
            from .monitoring import track_error_simple
            error_id = track_error_simple(e)
            logging.error(f"Error in {func.__name__} (tracked: {error_id}): {e}")
            raise
    
    return wrapper

# Usage:
@monitor_errors
async def risky_function():
    # Function that might raise errors
    pass
"""


if __name__ == "__main__":
    print("This file contains integration examples for the monitoring system.")
    print("See the commented code sections for specific integration patterns.")