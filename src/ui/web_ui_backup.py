"""
Web-Based UI Server for WhisperEngine
Provides browser-accessible interface with system tray integration for desktop users.
"""

import asyncio
import json
import os
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

try:
    from fastapi import FastAPI, WebSocket, Request, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse, JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    import pystray
    from PIL import Image
    SYSTEM_TRAY_AVAILABLE = True
except ImportError:
    SYSTEM_TRAY_AVAILABLE = False

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import DatabaseIntegrationManager


class TokenUsageTracker:
    """Track and analyze token usage patterns"""
    
    def __init__(self, db_manager: DatabaseIntegrationManager):
        self.db_manager = db_manager
    
    async def log_token_usage(self, 
                            user_id: str,
                            model_name: str,
                            input_tokens: int,
                            output_tokens: int,
                            cost_usd: float,
                            endpoint: str = "chat") -> None:
        """Log token usage to database"""
        try:
            await self.db_manager.get_database_manager().query("""
                INSERT INTO token_usage_log (
                    user_id, model_name, endpoint, input_tokens, output_tokens, 
                    total_tokens, cost_usd, timestamp
                ) VALUES (
                    :user_id, :model_name, :endpoint, :input_tokens, :output_tokens,
                    :total_tokens, :cost_usd, :timestamp
                )
            """, {
                "user_id": user_id,
                "model_name": model_name,
                "endpoint": endpoint,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": cost_usd,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logging.error(f"Failed to log token usage: {e}")
    
    async def get_usage_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get token usage summary for the last N days"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            result = await self.db_manager.get_database_manager().query("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_usd) as total_cost,
                    AVG(input_tokens) as avg_input_tokens,
                    AVG(output_tokens) as avg_output_tokens,
                    model_name,
                    endpoint
                FROM token_usage_log 
                WHERE timestamp >= :since_date
                GROUP BY model_name, endpoint
                ORDER BY total_cost DESC
            """, {"since_date": since_date.isoformat()})
            
            return {
                "period_days": days,
                "since_date": since_date.isoformat(),
                "usage_by_model": result.rows,
                "summary": self._calculate_summary(result.rows)
            }
        except Exception as e:
            logging.error(f"Failed to get usage summary: {e}")
            return {"error": str(e)}
    
    def _calculate_summary(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall summary statistics"""
        if not usage_data:
            return {"total_requests": 0, "total_cost": 0, "total_tokens": 0}
        
        total_requests = sum(row.get('total_requests', 0) for row in usage_data)
        total_cost = sum(row.get('total_cost', 0) for row in usage_data)
        total_tokens = sum(row.get('total_tokens', 0) for row in usage_data)
        
        return {
            "total_requests": total_requests,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "avg_cost_per_request": round(total_cost / max(total_requests, 1), 4),
            "avg_tokens_per_request": round(total_tokens / max(total_requests, 1), 1)
        }


class WhisperEngineWebUI:
    """Web-based UI for WhisperEngine with token monitoring"""
    
    def __init__(self, config_manager: AdaptiveConfigManager, port: int = 8080):
        self.config_manager = config_manager
        self.port = port
        self.db_manager = DatabaseIntegrationManager(config_manager)
        self.token_tracker = TokenUsageTracker(self.db_manager)
        self.app = None
        self.server = None
        self.tray_icon = None
        
        # Setup paths
        self.ui_dir = Path(__file__).parent / "ui"
        self.static_dir = self.ui_dir / "static"
        self.templates_dir = self.ui_dir / "templates"
        
        if FASTAPI_AVAILABLE:
            self.setup_fastapi()
    
    def setup_fastapi(self):
        """Setup FastAPI application"""
        self.app = FastAPI(title="WhisperEngine Dashboard", version="1.0.0")
        
        # Mount static files
        if self.static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
        
        # Setup templates
        if self.templates_dir.exists():
            self.templates = Jinja2Templates(directory=str(self.templates_dir))
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard page"""
            deployment_info = self.config_manager.get_deployment_info()
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "deployment_info": deployment_info,
                "title": "WhisperEngine Dashboard"
            })
        
        @self.app.get("/api/status")
        async def get_status():
            """Get system status"""
            return JSONResponse({
                "status": "running",
                "deployment_mode": self.config_manager.config.deployment_mode,
                "scale_tier": self.config_manager.config.scale_tier,
                "database_connected": self.db_manager.initialized,
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.get("/api/token-usage")
        async def get_token_usage(days: int = 7):
            """Get token usage statistics"""
            return JSONResponse(await self.token_tracker.get_usage_summary(days))
        
        @self.app.get("/api/system-info")
        async def get_system_info():
            """Get system information"""
            return JSONResponse(self.config_manager.get_deployment_info())
        
        @self.app.get("/api/performance-metrics")
        async def get_performance_metrics():
            """Get performance metrics"""
            try:
                result = await self.db_manager.get_database_manager().query("""
                    SELECT metric_name, metric_value, timestamp 
                    FROM performance_metrics 
                    WHERE timestamp >= :since
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, {"since": (datetime.now() - timedelta(hours=24)).isoformat()})
                
                return JSONResponse({
                    "metrics": result.rows,
                    "count": len(result.rows)
                })
            except Exception as e:
                return JSONResponse({"error": str(e)})
        
        @self.app.post("/api/log-token-usage")
        async def log_token_usage(request: Request):
            """Log token usage from bot"""
            try:
                data = await request.json()
                await self.token_tracker.log_token_usage(
                    user_id=data.get("user_id", "unknown"),
                    model_name=data.get("model_name", "unknown"),
                    input_tokens=data.get("input_tokens", 0),
                    output_tokens=data.get("output_tokens", 0),
                    cost_usd=data.get("cost_usd", 0.0),
                    endpoint=data.get("endpoint", "chat")
                )
                return JSONResponse({"status": "logged"})
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=400)
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates"""
            await websocket.accept()
            try:
                while True:
                    # Send periodic status updates
                    status = {
                        "type": "status_update",
                        "timestamp": datetime.now().isoformat(),
                        "data": await self.get_real_time_status()
                    }
                    await websocket.send_text(json.dumps(status))
                    await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
    
    async def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time status data"""
        try:
            # Get recent token usage
            recent_usage = await self.token_tracker.get_usage_summary(days=1)
            
            # Get system resources (if available)
            system_info = self.config_manager.get_deployment_info()
            
            return {
                "system_info": system_info,
                "token_usage": recent_usage,
                "active_connections": 1,  # Could track actual connections
                "uptime": "running"  # Could calculate actual uptime
            }
        except Exception as e:
            return {"error": str(e)}
    
    def create_system_tray(self):
        """Create system tray icon and menu"""
        if not SYSTEM_TRAY_AVAILABLE:
            return None
        
        try:
            # Create a simple icon (you'd want a proper icon file)
            icon_image = Image.new('RGB', (64, 64), color='blue')
            
            menu = pystray.Menu(
                pystray.MenuItem("Open Dashboard", self.open_dashboard),
                pystray.MenuItem("Token Usage", self.show_token_usage),
                pystray.MenuItem("Settings", self.show_settings),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self.quit_application)
            )
            
            self.tray_icon = pystray.Icon(
                "WhisperEngine",
                icon_image,
                "WhisperEngine Dashboard",
                menu
            )
            
            return self.tray_icon
        except Exception as e:
            logging.error(f"Failed to create system tray: {e}")
            return None
    
    def open_dashboard(self, icon=None, item=None):
        """Open dashboard in browser"""
        webbrowser.open(f"http://localhost:{self.port}")
    
    def show_token_usage(self, icon=None, item=None):
        """Show token usage page"""
        webbrowser.open(f"http://localhost:{self.port}/token-usage")
    
    def show_settings(self, icon=None, item=None):
        """Show settings page"""
        webbrowser.open(f"http://localhost:{self.port}/settings")
    
    def quit_application(self, icon=None, item=None):
        """Quit the application"""
        if self.tray_icon:
            self.tray_icon.stop()
        if self.server:
            self.server.should_exit = True
    
    async def start_server(self):
        """Start the web server"""
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI is required for web UI")
        
        # Initialize database
        await self.db_manager.initialize()
        
        # Add token usage table to schema if not exists
        await self._ensure_token_usage_table()
        
        # Configure and start server
        config = uvicorn.Config(
            app=self.app,
            host="127.0.0.1",
            port=self.port,
            log_level="info"
        )
        
        self.server = uvicorn.Server(config)
        
        # Start server in background
        server_task = asyncio.create_task(self.server.serve())
        
        # Open browser automatically
        await asyncio.sleep(1)  # Give server time to start
        self.open_dashboard()
        
        return server_task
    
    async def _ensure_token_usage_table(self):
        """Ensure token usage table exists"""
        try:
            await self.db_manager.get_database_manager().query("""
                CREATE TABLE IF NOT EXISTS token_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            await self.db_manager.get_database_manager().query("""
                CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp 
                ON token_usage_log(timestamp)
            """)
            
            await self.db_manager.get_database_manager().query("""
                CREATE INDEX IF NOT EXISTS idx_token_usage_user_model 
                ON token_usage_log(user_id, model_name)
            """)
        except Exception as e:
            logging.error(f"Failed to create token usage table: {e}")
    
    def run_desktop_mode(self):
        """Run in desktop mode with system tray"""
        async def desktop_main():
            # Start web server
            server_task = await self.start_server()
            
            # Setup system tray if available
            if SYSTEM_TRAY_AVAILABLE:
                tray_icon = self.create_system_tray()
                if tray_icon:
                    # Run tray in thread
                    import threading
                    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
                    tray_thread.start()
            
            print(f"WhisperEngine Dashboard running at http://localhost:{self.port}")
            print("Press Ctrl+C to stop")
            
            try:
                await server_task
            except KeyboardInterrupt:
                print("\nShutting down...")
            finally:
                await self.db_manager.cleanup()
        
        asyncio.run(desktop_main())
    
    def run_server_mode(self):
        """Run in server mode (no system tray)"""
        async def server_main():
            server_task = await self.start_server()
            print(f"WhisperEngine Dashboard running at http://localhost:{self.port}")
            
            try:
                await server_task
            except KeyboardInterrupt:
                print("\nShutting down...")
            finally:
                await self.db_manager.cleanup()
        
        asyncio.run(server_main())


def create_ui_files():
    """Create basic HTML templates and static files"""
    ui_dir = Path(__file__).parent / "ui"
    templates_dir = ui_dir / "templates"
    static_dir = ui_dir / "static"
    
    # Create directories
    templates_dir.mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dashboard template
    dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .metric { text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007acc; }
        .metric-label { color: #666; margin-top: 5px; }
        .status-good { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-error { color: #dc3545; }
        h1, h2 { color: #333; }
        .update-time { float: right; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>WhisperEngine Dashboard <span class="update-time" id="updateTime"></span></h1>
        
        <div class="card">
            <h2>System Status</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value status-good">{{ deployment_info.deployment_mode.title() }}</div>
                    <div class="metric-label">Deployment Mode</div>
                </div>
                <div class="metric">
                    <div class="metric-value">Tier {{ deployment_info.scale_tier }}</div>
                    <div class="metric-label">Scale Tier</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ deployment_info.cpu_cores }}</div>
                    <div class="metric-label">CPU Cores</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ "%.1f"|format(deployment_info.memory_gb) }} GB</div>
                    <div class="metric-label">Memory</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Token Usage (Last 7 Days)</h2>
            <div id="tokenUsage">Loading...</div>
            <canvas id="tokenChart" width="400" height="200"></canvas>
        </div>
        
        <div class="card">
            <h2>Recent Activity</h2>
            <div id="recentActivity">Loading...</div>
        </div>
    </div>
    
    <script>
        // Update timestamp
        function updateTime() {
            document.getElementById('updateTime').textContent = new Date().toLocaleTimeString();
        }
        updateTime();
        setInterval(updateTime, 1000);
        
        // Load token usage data
        async function loadTokenUsage() {
            try {
                const response = await fetch('/api/token-usage');
                const data = await response.json();
                
                const usageDiv = document.getElementById('tokenUsage');
                if (data.summary) {
                    usageDiv.innerHTML = `
                        <div class="metrics">
                            <div class="metric">
                                <div class="metric-value">$${data.summary.total_cost}</div>
                                <div class="metric-label">Total Cost</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.summary.total_requests}</div>
                                <div class="metric-label">Requests</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">${data.summary.total_tokens.toLocaleString()}</div>
                                <div class="metric-label">Total Tokens</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">$${data.summary.avg_cost_per_request}</div>
                                <div class="metric-label">Avg Cost/Request</div>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Failed to load token usage:', error);
                document.getElementById('tokenUsage').innerHTML = '<p>Failed to load token usage data</p>';
            }
        }
        
        // WebSocket for real-time updates
        const ws = new WebSocket(`ws://localhost:${window.location.port}/ws`);
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'status_update') {
                updateTime();
                // Update any real-time metrics here
            }
        };
        
        // Load initial data
        loadTokenUsage();
        setInterval(loadTokenUsage, 30000); // Refresh every 30 seconds
    </script>
</body>
</html>"""
    
    with open(templates_dir / "dashboard.html", "w") as f:
        f.write(dashboard_html)
    
    print(f"Created UI files in {ui_dir}")


# Factory function
def create_web_ui(config_manager: Optional[AdaptiveConfigManager] = None, port: int = 8080) -> WhisperEngineWebUI:
    """Factory function to create web UI"""
    if config_manager is None:
        config_manager = AdaptiveConfigManager()
    
    return WhisperEngineWebUI(config_manager, port)


# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='WhisperEngine Web UI')
    parser.add_argument('--port', type=int, default=8080, help='Port to run on')
    parser.add_argument('--desktop', action='store_true', help='Run in desktop mode with system tray')
    parser.add_argument('--create-ui-files', action='store_true', help='Create UI template files')
    
    args = parser.parse_args()
    
    if args.create_ui_files:
        create_ui_files()
        return
    
    if not FASTAPI_AVAILABLE:
        print("FastAPI is required for web UI. Install with: pip install fastapi uvicorn jinja2")
        return
    
    # Create web UI
    ui = create_web_ui(port=args.port)
    
    if args.desktop and SYSTEM_TRAY_AVAILABLE:
        ui.run_desktop_mode()
    else:
        ui.run_server_mode()


if __name__ == "__main__":
    main()