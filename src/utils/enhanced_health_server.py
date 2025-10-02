"""
Enhanced Health Server
Basic health monitoring for Discord bots.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import discord
from aiohttp import web
from discord.ext import commands

logger = logging.getLogger(__name__)

# Configure aiohttp access logs to use DEBUG level to reduce log spam
access_logger = logging.getLogger("aiohttp.access")
access_logger.setLevel(logging.WARNING)


class EnhancedHealthServer:
    """HTTP server with health checks for Discord bots"""

    def __init__(self, bot: commands.Bot, port: int = 9090, host: str = "0.0.0.0", bot_manager=None):
        self.bot = bot
        self.bot_manager = bot_manager
        self.port = port
        self.host = host
        # Disable aiohttp access logging to prevent health check spam
        self.app = web.Application(logger=logger)
        self.runner = None
        self.site = None
        
        self.setup_routes()

    def setup_routes(self):
        """Configure HTTP routes"""
        # Health check routes
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_get("/ready", self.readiness_check)
        self.app.router.add_get("/metrics", self.metrics)
        self.app.router.add_get("/status", self.detailed_status)
        self.app.router.add_get("/api/bot-info", self.get_bot_info)
        
        # CORS middleware setup
        self.app.middlewares.append(self.cors_middleware)
        
        # CORS middleware setup
        self.app.middlewares.append(self.cors_middleware)

    @web.middleware
    async def cors_middleware(self, request, handler):
        """Handle CORS for web UI requests"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    async def handle_cors_preflight(self, request):
        """Handle CORS preflight requests"""
        return web.Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
        )

    async def get_bot_info(self, request):
        """Get information about this bot instance"""
        try:
            bot_info = {
                "bot_name": self.bot.user.name if self.bot.user else "Unknown",
                "bot_id": str(self.bot.user.id) if self.bot.user else "unknown",
                "status": "online" if self.bot.is_ready() else "offline",
                "platform": "discord",
                "api_version": "1.0",
                "capabilities": [
                    "text_chat",
                    "conversation_memory",
                    "character_personality"
                ],
                "character_info": self._get_character_info(),
                "timestamp": datetime.now().isoformat()
            }
            
            return web.json_response(bot_info)
            
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return web.json_response(
                {"error": f"Failed to get bot info: {str(e)}"}, 
                status=500
            )

    def _get_character_info(self) -> Dict[str, Any]:
        """Get character information for this bot instance"""
        try:
            # Try to get character info from environment or bot configuration
            import os
            character_file = os.getenv("CDL_DEFAULT_CHARACTER")
            
            if character_file:
                # Extract character name from file path
                character_name = character_file.split('/')[-1].replace('.json', '').replace('-', ' ').title()
                return {
                    "character_file": character_file,
                    "character_name": character_name,
                    "has_personality": True
                }
            else:
                return {
                    "character_file": None,
                    "character_name": "Default Assistant", 
                    "has_personality": False
                }
                
        except Exception as e:
            logger.warning(f"Could not get character info: {e}")
            return {
                "character_file": None,
                "character_name": "Assistant",
                "has_personality": False
            }

    # Existing health check methods (unchanged)
    async def health_check(self, request):
        """Basic health check - is the service running?"""
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Health check from {request.remote}")

        return web.json_response(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "WhisperEngine Discord Bot",
            }
        )

    async def readiness_check(self, request):
        """Readiness check - is the service ready to handle requests?"""
        try:
            is_ready = (
                self.bot.is_ready() and self.bot.user is not None and not self.bot.is_closed()
            )

            if is_ready:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Readiness check from {request.remote} - bot ready")

                return web.json_response(
                    {
                        "status": "ready",
                        "timestamp": datetime.utcnow().isoformat(),
                        "bot_user": str(self.bot.user),
                        "guilds_count": len(self.bot.guilds),
                        "latency_ms": round(self.bot.latency * 1000, 2),
                    }
                )
            else:
                logger.warning(
                    f"Readiness check failed - bot not ready: ready={self.bot.is_ready()}, closed={self.bot.is_closed()}"
                )
                return web.json_response(
                    {
                        "status": "not_ready",
                        "timestamp": datetime.utcnow().isoformat(),
                        "reason": "Bot not connected to Discord",
                    },
                    status=503,
                )

        except Exception as e:
            logger.error(f"Error in readiness check: {e}")
            return web.json_response(
                {"status": "error", "timestamp": datetime.utcnow().isoformat(), "error": str(e)},
                status=500,
            )

    async def metrics(self, request):
        """Basic metrics endpoint"""
        try:
            metrics_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "bot_status": "ready" if self.bot.is_ready() else "not_ready",
                "guild_count": len(self.bot.guilds) if self.bot.is_ready() else 0,
                "latency_ms": round(self.bot.latency * 1000, 2) if self.bot.is_ready() else -1,
                "memory_usage_mb": self._get_memory_usage(),
            }

            return web.json_response(metrics_data)

        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return web.json_response(
                {"error": f"Failed to generate metrics: {str(e)}"}, 
                status=500
            )

    async def detailed_status(self, request):
        """Detailed status information"""
        try:
            status_data = {
                "service": "WhisperEngine Discord Bot",
                "timestamp": datetime.utcnow().isoformat(),
                "bot": {
                    "ready": self.bot.is_ready(),
                    "closed": self.bot.is_closed(),
                    "user": str(self.bot.user) if self.bot.user else None,
                    "latency_ms": round(self.bot.latency * 1000, 2) if self.bot.is_ready() else -1,
                },
                "api": {
                    "endpoints": ["/api/bot-info"]
                },
                "character": self._get_character_info()
            }

            return web.json_response(status_data)

        except Exception as e:
            logger.error(f"Error generating detailed status: {e}")
            return web.json_response(
                {"error": f"Failed to generate status: {str(e)}"}, 
                status=500
            )

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            return round(memory_mb, 2)
        except ImportError:
            return -1  # psutil not available
        except Exception:
            return -1  # Error getting memory info

    async def start(self):
        """Start the enhanced health server"""
        try:
            # Configure runner to suppress access logs for health checks
            self.runner = web.AppRunner(self.app, access_log=None)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            logger.info(f"✅ Enhanced health server started on {self.host}:{self.port}")
            logger.info("Available endpoints:")
            logger.info(f"  - http://{self.host}:{self.port}/health")
            logger.info(f"  - http://{self.host}:{self.port}/ready")
            logger.info(f"  - http://{self.host}:{self.port}/metrics")
            logger.info(f"  - http://{self.host}:{self.port}/status")
            logger.info(f"  - http://{self.host}:{self.port}/api/bot-info (GET)")

        except Exception as e:
            logger.error(f"Failed to start enhanced server: {e}")
            raise

    async def stop(self):
        """Stop the enhanced server"""
        try:
            if self.site:
                await self.site.stop()
                logger.info("Enhanced server stopped")

            if self.runner:
                await self.runner.cleanup()
                logger.info("Enhanced server cleaned up")

        except Exception as e:
            logger.error(f"Error stopping enhanced server: {e}")


# Factory function for easy integration
def create_enhanced_health_server(
    bot: commands.Bot, port: int = 9090, host: str = "0.0.0.0", bot_manager=None
) -> EnhancedHealthServer:
    """Create and return an enhanced health server instance with chat API"""
    return EnhancedHealthServer(bot, port, host, bot_manager)