"""
Health Monitor for Enhanced Concurrent Discord Bot
Provides health checks and monitoring for all components
"""

import logging
import time
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitor health of bot components"""

    def __init__(
        self,
        memory_manager,
        llm_client,
        conversation_cache,
        emotion_manager=None,
        backup_manager=None,
    ):
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.conversation_cache = conversation_cache
        self.emotion_manager = emotion_manager
        self.backup_manager = backup_manager

        # Health tracking
        self.last_check = None
        self.component_status = {}
        self.error_counts = {}
        self.start_time = time.time()

    async def perform_health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check"""
        self.last_check = datetime.now()
        health_status = {
            "timestamp": self.last_check.isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "overall_status": "healthy",
            "components": {},
        }

        # Check LLM client
        try:
            llm_connected = await self.llm_client.check_connection_async()
            health_status["components"]["llm"] = {
                "status": "healthy" if llm_connected else "unhealthy",
                "connected": llm_connected,
                "has_vision": self.llm_client.has_vision_support(),
            }
        except Exception as e:
            health_status["components"]["llm"] = {"status": "error", "error": str(e)}
            health_status["overall_status"] = "degraded"

        # Check memory manager
        try:
            # Test memory operations
            await self.memory_manager.retrieve_memories_safe("health_check", "test", limit=1)
            health_status["components"]["memory"] = {
                "status": "healthy",
                "thread_safe": True,
                "active_operations": len(getattr(self.memory_manager, "_active_operations", [])),
            }
        except Exception as e:
            health_status["components"]["memory"] = {"status": "error", "error": str(e)}
            health_status["overall_status"] = "degraded"

        # Check conversation cache
        if self.conversation_cache:
            try:
                cache_stats = self.conversation_cache.get_cache_stats()
                health_status["components"]["cache"] = {"status": "healthy", "stats": cache_stats}
            except Exception as e:
                health_status["components"]["cache"] = {"status": "error", "error": str(e)}
        else:
            health_status["components"]["cache"] = {"status": "disabled"}

        # Check emotion manager
        if self.emotion_manager:
            try:
                profile_count = len(getattr(self.emotion_manager, "user_profiles", {}))
                health_status["components"]["emotions"] = {
                    "status": "healthy",
                    "user_profiles": profile_count,
                    "auto_save_enabled": hasattr(self.emotion_manager, "_auto_save_timer"),
                }
            except Exception as e:
                health_status["components"]["emotions"] = {"status": "error", "error": str(e)}
        else:
            health_status["components"]["emotions"] = {"status": "disabled"}

        # Check backup manager
        if self.backup_manager:
            try:
                health_status["components"]["backup"] = {
                    "status": "healthy",
                    "auto_backup_enabled": getattr(
                        self.backup_manager, "auto_backup_enabled", False
                    ),
                }
            except Exception as e:
                health_status["components"]["backup"] = {"status": "error", "error": str(e)}
        else:
            health_status["components"]["backup"] = {"status": "disabled"}

        # Overall status determination
        error_components = [
            name
            for name, status in health_status["components"].items()
            if status.get("status") == "error"
        ]
        if error_components:
            health_status["overall_status"] = "unhealthy"
            health_status["error_components"] = error_components

        logger.debug(f"Health check completed: {health_status['overall_status']}")
        return health_status

    def get_uptime(self) -> str:
        """Get formatted uptime"""
        uptime_seconds = time.time() - self.start_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def increment_error_count(self, component: str):
        """Increment error count for a component"""
        self.error_counts[component] = self.error_counts.get(component, 0) + 1

    def get_error_summary(self) -> dict[str, int]:
        """Get error count summary"""
        return self.error_counts.copy()
