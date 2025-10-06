"""
Monitoring Dashboard

Web-based dashboard for system health, engagement metrics, and error tracking.
Provides real-time operational visibility for WhisperEngine.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import weakref

from .health_monitor import get_health_monitor, HealthStatus, ComponentType
from .error_tracker import get_error_tracker, ErrorSeverity, ErrorCategory

# Initialize logger BEFORE any code that might use it
logger = logging.getLogger(__name__)

# Engagement tracker disabled - replaced with InfluxDB metrics
try:
    from .engagement_tracker import get_engagement_tracker, InteractionType
    ENGAGEMENT_TRACKER_AVAILABLE = True
except ImportError:
    logger.debug("Engagement tracker not available - using InfluxDB metrics instead")
    ENGAGEMENT_TRACKER_AVAILABLE = False
    get_engagement_tracker = None
    InteractionType = None

# Optional web dependencies
try:
    import aiohttp
    from aiohttp import web, WSMsgType
    WEB_AVAILABLE = True
except ImportError:
    logger.warning("aiohttp not available - web dashboard disabled")
    WEB_AVAILABLE = False
    aiohttp = None
    web = None
    WSMsgType = None

try:
    import aiohttp_cors
    CORS_AVAILABLE = True
except ImportError:
    logger.debug("aiohttp_cors not available - CORS support disabled")
    CORS_AVAILABLE = False
    aiohttp_cors = None


class MonitoringDashboard:
    """Web-based monitoring dashboard for system visibility."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.host = self.config.get('host', '127.0.0.1')
        self.port = self.config.get('port', 8080)
        self.debug = self.config.get('debug', False)
        
        # Check if web framework is available
        if not WEB_AVAILABLE:
            logger.warning("Web dashboard unavailable - aiohttp not installed")
            self.available = False
            return
        
        self.available = True
        
        # Component managers
        self.health_monitor = get_health_monitor()
        self.engagement_tracker = get_engagement_tracker() if ENGAGEMENT_TRACKER_AVAILABLE else None
        self.error_tracker = get_error_tracker()
        
        # Web application
        self.app = None
        self.runner = None
        self.site = None
        
        # WebSocket connections for real-time updates
        self.websockets: weakref.WeakSet = weakref.WeakSet()
        
        # Dashboard state
        self.last_update = None
        self.update_interval = self.config.get('update_interval', 30)  # seconds
        
        logger.info("Monitoring dashboard initialized")
    
    async def start(self):
        """Start the monitoring dashboard web server."""
        if not self.available:
            logger.error("Cannot start dashboard - web dependencies not available")
            return
            
        if self.runner:
            logger.warning("Dashboard already running")
            return
        
        # Create web application
        self.app = web.Application()
        
        # Setup CORS if available
        if CORS_AVAILABLE and aiohttp_cors:
            cors = aiohttp_cors.setup(self.app, defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*"
                )
            })
            
            # Setup routes
            self._setup_routes()
            
            # Add CORS to all routes
            for route in list(self.app.router.routes()):
                cors.add(route)
        else:
            # Setup routes without CORS
            self._setup_routes()
        
        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info("Dashboard started at http://%s:%s", self.host, self.port)
        
        # Start background tasks
        asyncio.create_task(self._update_loop())
        if WEB_AVAILABLE:
            asyncio.create_task(self._websocket_broadcast_loop())
    
    async def stop(self):
        """Stop the monitoring dashboard."""
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
            self.site = None
            logger.info("Dashboard stopped")
    
    def _setup_routes(self):
        """Setup web application routes."""
        if not self.app:
            return
            
        # Static files (dashboard UI)
        dashboard_static = Path(__file__).parent / 'dashboard_static'
        if dashboard_static.exists():
            self.app.router.add_static('/', str(dashboard_static), name='static')
        
        # API endpoints
        self.app.router.add_get('/api/health', self._handle_health)
        self.app.router.add_get('/api/health/history', self._handle_health_history)
        self.app.router.add_get('/api/engagement', self._handle_engagement)
        self.app.router.add_get('/api/engagement/summary', self._handle_engagement_summary)
        self.app.router.add_get('/api/errors', self._handle_errors)
        self.app.router.add_get('/api/errors/patterns', self._handle_error_patterns)
        self.app.router.add_get('/api/errors/trends', self._handle_error_trends)
        self.app.router.add_get('/api/overview', self._handle_overview)
        
        # WebSocket endpoint for real-time updates
        self.app.router.add_get('/ws', self._handle_websocket)
        
        # Dashboard HTML (if no static files)
        self.app.router.add_get('/', self._handle_dashboard_html)
    
    async def _handle_health(self, request):
        """Handle health status API request."""
        try:
            health = await self.health_monitor.check_system_health()
            return web.json_response(health.to_dict())
        except Exception as e:
            logger.error("Error getting health status: %s", e)
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_health_history(self, request):
        """Handle health history API request."""
        try:
            hours = int(request.query.get('hours', 24))
            history = self.health_monitor.get_health_history(hours)
            return web.json_response([h.to_dict() for h in history])
        except Exception as e:
            logger.error("Error getting health history: %s", e)
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_engagement(self, request):
        """Handle engagement metrics API request."""
        try:
            days = int(request.query.get('days', 7))
            if self.engagement_tracker:
                report = self.engagement_tracker.export_engagement_report(days)
            else:
                report = {'message': 'Engagement tracking disabled - using InfluxDB metrics', 'days': days}
            return web.json_response(report)
        except Exception as e:
            logger.error("Error getting engagement data: %s", e)
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_engagement_summary(self, request):
        """Handle engagement summary API request."""
        try:
            if self.engagement_tracker:
                summary = self.engagement_tracker.generate_engagement_summary()
                return web.json_response(summary.to_dict())
            else:
                summary = {'message': 'Engagement tracking disabled - using InfluxDB metrics'}
                return web.json_response(summary)
        except Exception as e:
            logger.error("Error getting engagement summary: %s", e)
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_errors(self, request):
        """Handle error summary API request."""
        try:
            hours = int(request.query.get('hours', 24))
            summary = self.error_tracker.get_error_summary(hours)
            return web.json_response(summary)
        except Exception as e:
            logger.error("Error getting error summary: %s", e)
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_error_patterns(self, request):
        """Handle error patterns API request."""
        try:
            patterns = [pattern.to_dict() for pattern in self.error_tracker.error_patterns.values()]
            return web.json_response(patterns)
        except Exception as e:
            logger.error("Error getting error patterns: %s", e)
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_error_trends(self, request):
        """Handle error trends API request."""
        try:
            days = int(request.query.get('days', 7))
            trends = self.error_tracker.get_error_trends(days)
            return web.json_response(trends)
        except Exception as e:
            logger.error("Error getting error trends: %s", e)
            return web.json_response({'error': str(e)}, status=500)
    
    async def _handle_overview(self, request):
        """Handle overview dashboard API request."""
        try:
            # Get current health
            health = self.health_monitor.get_current_health()
            health_data = health.to_dict() if health else None
            
            # Get engagement summary
            engagement_summary = self.engagement_tracker.generate_engagement_summary()
            
            # Get error summary
            error_summary = self.error_tracker.get_error_summary(24)
            
            # Calculate system score
            system_score = self._calculate_system_score(health, engagement_summary, error_summary)
            
            overview = {
                'timestamp': datetime.now().isoformat(),
                'system_score': system_score,
                'health': health_data,
                'engagement': engagement_summary.to_dict(),
                'errors': error_summary,
                'status': {
                    'health_status': health.overall_status.value if health else 'unknown',
                    'active_users_24h': engagement_summary.total_active_users,
                    'error_rate_24h': error_summary['error_rate_per_hour'],
                    'critical_errors': error_summary['unresolved_critical_errors']
                }
            }
            
            return web.json_response(overview)
            
        except Exception as e:
            logger.error("Error getting overview: %s", e)
            return web.json_response({'error': str(e)}, status=500)
    
    def _calculate_system_score(self, health, engagement_summary, error_summary) -> float:
        """Calculate overall system health score (0-100)."""
        score = 100.0
        
        # Health component (40% weight)
        if health:
            if health.overall_status == HealthStatus.CRITICAL:
                score -= 40
            elif health.overall_status == HealthStatus.WARNING:
                score -= 20
        else:
            score -= 30
        
        # Error rate component (30% weight)
        error_rate = error_summary.get('error_rate_per_hour', 0)
        if error_rate > 10:
            score -= 30
        elif error_rate > 5:
            score -= 20
        elif error_rate > 1:
            score -= 10
        
        # Engagement component (20% weight)
        if engagement_summary.total_active_users == 0:
            score -= 20
        elif engagement_summary.total_active_users < 5:
            score -= 10
        
        # Critical errors component (10% weight)
        critical_errors = error_summary.get('unresolved_critical_errors', 0)
        if critical_errors > 0:
            score -= min(critical_errors * 5, 10)
        
        return max(0.0, score)
    
    async def _handle_websocket(self, request):
        """Handle WebSocket connections for real-time updates."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Add to active connections
        self.websockets.add(ws)
        logger.debug("WebSocket connection established")
        
        try:
            # Send initial data
            overview = await self._get_overview_data()
            await ws.send_str(json.dumps({
                'type': 'initial',
                'data': overview
            }))
            
            # Handle incoming messages
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_websocket_message(ws, data)
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON from WebSocket client")
                elif msg.type == WSMsgType.ERROR:
                    logger.error("WebSocket error: %s", ws.exception())
                    break
                    
        except Exception as e:
            logger.error("WebSocket connection error: %s", e)
        finally:
            logger.debug("WebSocket connection closed")
        
        return ws
    
    async def _handle_websocket_message(self, ws, data):
        """Handle incoming WebSocket messages."""
        message_type = data.get('type')
        
        if message_type == 'subscribe':
            # Client wants to subscribe to specific updates
            pass
        elif message_type == 'request_update':
            # Client requesting immediate update
            overview = await self._get_overview_data()
            await ws.send_str(json.dumps({
                'type': 'update',
                'data': overview
            }))
    
    async def _get_overview_data(self):
        """Get overview data for WebSocket updates."""
        try:
            # Get current health
            health = self.health_monitor.get_current_health()
            health_data = health.to_dict() if health else None
            
            # Get engagement summary
            engagement_summary = self.engagement_tracker.generate_engagement_summary()
            
            # Get error summary
            error_summary = self.error_tracker.get_error_summary(1)  # Last hour for real-time
            
            return {
                'timestamp': datetime.now().isoformat(),
                'health': health_data,
                'engagement': engagement_summary.to_dict(),
                'errors': error_summary
            }
        except Exception as e:
            logger.error("Error getting overview data: %s", e)
            return {'error': str(e)}
    
    async def _update_loop(self):
        """Background loop for periodic updates."""
        while True:
            try:
                # Trigger component updates
                await self.health_monitor.check_system_health(full_check=False)
                # Engagement tracker disabled - using InfluxDB metrics instead
                if self.engagement_tracker:
                    self.engagement_tracker.cleanup_old_sessions()
                self.error_tracker.cleanup_old_errors()
                
                self.last_update = datetime.now()
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error("Error in update loop: %s", e)
                await asyncio.sleep(self.update_interval)
    
    async def _websocket_broadcast_loop(self):
        """Background loop for broadcasting updates to WebSocket clients."""
        while True:
            try:
                if self.websockets:
                    overview = await self._get_overview_data()
                    message = json.dumps({
                        'type': 'update',
                        'data': overview
                    })
                    
                    # Send to all connected clients
                    disconnected = []
                    for ws in self.websockets:
                        try:
                            await ws.send_str(message)
                        except Exception:
                            disconnected.append(ws)
                    
                    # Remove disconnected clients
                    for ws in disconnected:
                        try:
                            self.websockets.remove(ws)
                        except KeyError:
                            pass
                
                await asyncio.sleep(10)  # Broadcast every 10 seconds
                
            except Exception as e:
                logger.error("Error in WebSocket broadcast loop: %s", e)
                await asyncio.sleep(10)
    
    async def _handle_dashboard_html(self, request):
        """Serve basic dashboard HTML if no static files."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>WhisperEngine Monitoring Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status { display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }
        .status.healthy { background: #4caf50; }
        .status.warning { background: #ff9800; }
        .status.critical { background: #f44336; }
        .status.unknown { background: #9e9e9e; }
        .metric { margin: 10px 0; }
        .metric-value { font-size: 1.5em; font-weight: bold; color: #333; }
        .metric-label { font-size: 0.9em; color: #666; }
        h1, h2 { color: #333; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .error { color: #f44336; }
        #status { font-size: 0.9em; color: #666; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 WhisperEngine Monitoring Dashboard</h1>
        <div id="status">Loading...</div>
        
        <div class="grid">
            <div class="card">
                <h2>System Health</h2>
                <div id="health-content">Loading...</div>
            </div>
            
            <div class="card">
                <h2>User Engagement</h2>
                <div id="engagement-content">Loading...</div>
            </div>
            
            <div class="card">
                <h2>Error Summary</h2>
                <div id="errors-content">Loading...</div>
            </div>
        </div>
        
        <div class="card">
            <h2>Quick Actions</h2>
            <p>
                <a href="/api/health" target="_blank">Health API</a> | 
                <a href="/api/engagement" target="_blank">Engagement API</a> | 
                <a href="/api/errors" target="_blank">Errors API</a> | 
                <a href="/api/overview" target="_blank">Overview API</a>
            </p>
        </div>
    </div>

    <script>
        let ws = null;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                if (message.type === 'initial' || message.type === 'update') {
                    updateDashboard(message.data);
                }
            };
            
            ws.onclose = function() {
                setTimeout(connectWebSocket, 5000); // Reconnect after 5 seconds
            };
        }
        
        function updateDashboard(data) {
            document.getElementById('status').textContent = `Last updated: ${new Date(data.timestamp).toLocaleString()}`;
            
            // Update health
            if (data.health) {
                const healthHtml = `
                    <div class="metric">
                        <div class="status ${data.health.overall_status}">${data.health.overall_status.toUpperCase()}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${data.health.uptime}</div>
                        <div class="metric-label">System Uptime</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${Object.keys(data.health.components).length}</div>
                        <div class="metric-label">Components Monitored</div>
                    </div>
                `;
                document.getElementById('health-content').innerHTML = healthHtml;
            }
            
            // Update engagement
            if (data.engagement) {
                const engagementHtml = `
                    <div class="metric">
                        <div class="metric-value">${data.engagement.total_active_users}</div>
                        <div class="metric-label">Active Users (24h)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${data.engagement.new_users}</div>
                        <div class="metric-label">New Users</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${data.engagement.total_conversations}</div>
                        <div class="metric-label">Conversations (24h)</div>
                    </div>
                `;
                document.getElementById('engagement-content').innerHTML = engagementHtml;
            }
            
            // Update errors
            if (data.errors) {
                const errorsHtml = `
                    <div class="metric">
                        <div class="metric-value ${data.errors.unresolved_critical_errors > 0 ? 'error' : ''}">${data.errors.total_errors}</div>
                        <div class="metric-label">Total Errors (24h)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value ${data.errors.unresolved_critical_errors > 0 ? 'error' : ''}">${data.errors.unresolved_critical_errors}</div>
                        <div class="metric-label">Critical Errors</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${data.errors.error_rate_per_hour.toFixed(2)}</div>
                        <div class="metric-label">Error Rate/Hour</div>
                    </div>
                `;
                document.getElementById('errors-content').innerHTML = errorsHtml;
            }
        }
        
        // Initial load
        fetch('/api/overview')
            .then(response => response.json())
            .then(data => updateDashboard(data))
            .catch(error => console.error('Error loading initial data:', error));
        
        // Connect WebSocket for real-time updates
        connectWebSocket();
    </script>
</body>
</html>
        """
        return web.Response(text=html, content_type='text/html')


# Global dashboard instance
_dashboard: Optional[MonitoringDashboard] = None


def get_dashboard(config: Optional[Dict[str, Any]] = None) -> MonitoringDashboard:
    """Get the global dashboard instance."""
    # Using global state for singleton pattern
    # pylint: disable=global-statement
    global _dashboard
    if _dashboard is None:
        _dashboard = MonitoringDashboard(config)
    return _dashboard


async def start_dashboard(config: Optional[Dict[str, Any]] = None) -> MonitoringDashboard:
    """Start the monitoring dashboard."""
    dashboard = get_dashboard(config)
    await dashboard.start()
    return dashboard