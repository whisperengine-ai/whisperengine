"""
Health check web server for container orchestration and monitoring.
Provides HTTP endpoints for health checks, metrics, and status information.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from aiohttp import web, ClientSession
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

# Configure aiohttp access logs to use DEBUG level to reduce log spam
# Health checks can be very frequent (every few seconds from load balancers)
access_logger = logging.getLogger("aiohttp.access")
access_logger.setLevel(logging.WARNING)  # Only log access errors/warnings


class HealthCheckServer:
    """Simple HTTP server for health checks and monitoring"""

    def __init__(self, bot: commands.Bot, port: int = 9090, host: str = "0.0.0.0"):
        self.bot = bot
        self.port = port
        self.host = host
        # Disable aiohttp access logging to prevent health check spam
        self.app = web.Application(logger=logger)
        self.runner = None
        self.site = None
        self.setup_routes()

    def setup_routes(self):
        """Configure HTTP routes"""
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_get("/ready", self.readiness_check)
        self.app.router.add_get("/metrics", self.metrics)
        self.app.router.add_get("/status", self.detailed_status)

    async def health_check(self, request):
        """Basic health check - is the service running?"""
        # Log only first health check or failures for debugging
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
            # Check if bot is connected to Discord
            is_ready = (
                self.bot.is_ready() and self.bot.user is not None and not self.bot.is_closed()
            )

            if is_ready:
                # Log readiness checks only at DEBUG level unless there's an issue
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
                "bot_latency_ms": (
                    round(self.bot.latency * 1000, 2) if self.bot.is_ready() else None
                ),
                "guilds_count": len(self.bot.guilds) if self.bot.is_ready() else 0,
                "users_count": len(self.bot.users) if self.bot.is_ready() else 0,
                "commands_count": len(self.bot.all_commands),
                "is_ready": self.bot.is_ready(),
                "is_closed": self.bot.is_closed(),
            }

            return web.json_response(metrics_data)

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return web.json_response(
                {"error": str(e), "timestamp": datetime.utcnow().isoformat()}, status=500
            )

    async def detailed_status(self, request):
        """Detailed status information"""
        try:
            status_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "service": "WhisperEngine Discord Bot",
                "version": "1.0.0",  # You might want to make this dynamic
                "bot": {
                    "is_ready": self.bot.is_ready(),
                    "is_closed": self.bot.is_closed(),
                    "user": str(self.bot.user) if self.bot.user else None,
                    "latency_ms": (
                        round(self.bot.latency * 1000, 2) if self.bot.is_ready() else None
                    ),
                    "guilds_count": len(self.bot.guilds) if self.bot.is_ready() else 0,
                    "users_count": len(self.bot.users) if self.bot.is_ready() else 0,
                },
                "system": {
                    "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
                    "discord_py_version": discord.__version__,
                },
            }

            return web.json_response(status_data)

        except Exception as e:
            logger.error(f"Error getting detailed status: {e}")
            return web.json_response(
                {"error": str(e), "timestamp": datetime.utcnow().isoformat()}, status=500
            )

    async def start(self):
        """Start the health check server"""
        try:
            # Configure runner to suppress access logs for health checks
            self.runner = web.AppRunner(self.app, access_log=None)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            logger.info(f"✅ Health check server started on {self.host}:{self.port}")
            logger.info(f"Health endpoints available:")
            logger.info(f"  - http://{self.host}:{self.port}/health")
            logger.info(f"  - http://{self.host}:{self.port}/ready")
            logger.info(f"  - http://{self.host}:{self.port}/metrics")
            logger.info(f"  - http://{self.host}:{self.port}/status")
            logger.debug(f"Access logging disabled to prevent health check spam")

        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
            raise

    async def stop(self):
        """Stop the health check server"""
        try:
            if self.site:
                await self.site.stop()
                logger.info("Health check server stopped")

            if self.runner:
                await self.runner.cleanup()
                logger.info("Health check server cleaned up")

        except Exception as e:
            logger.error(f"Error stopping health check server: {e}")


# Factory function for easy integration
def create_health_server(
    bot: commands.Bot, port: int = 9090, host: str = "0.0.0.0"
) -> HealthCheckServer:
    """Create and return a health check server instance"""
    return HealthCheckServer(bot, port, host)
