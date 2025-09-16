"""
Cleanup Handler for Job Scheduler
=================================

Handler for various cleanup tasks including old conversations, failed jobs, etc.
"""

import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CleanupHandler:
    """Handler for data cleanup jobs"""

    def __init__(self, postgres_pool):
        self.postgres_pool = postgres_pool

    async def execute(self, payload: dict[str, Any]):
        """Execute a cleanup job"""
        cleanup_type = payload.get("type", "old_conversations")
        days_to_keep = payload.get("days_to_keep", 30)

        if cleanup_type == "old_conversations":
            await self._cleanup_old_conversations(days_to_keep)
        elif cleanup_type == "failed_jobs":
            await self._cleanup_failed_jobs(days_to_keep)
        elif cleanup_type == "temp_data":
            await self._cleanup_temp_data()
        else:
            logger.warning(f"Unknown cleanup type: {cleanup_type}")

    async def _cleanup_old_conversations(self, days_to_keep: int):
        """Clean up old conversation history"""
        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)

        async with self.postgres_pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM conversation_history
                WHERE timestamp < $1
            """,
                cutoff_date,
            )

            deleted_count = int(result.split()[-1]) if result != "DELETE 0" else 0
            logger.info(f"Cleaned up {deleted_count} old conversation records")

    async def _cleanup_failed_jobs(self, days_to_keep: int):
        """Clean up old failed jobs"""
        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)

        async with self.postgres_pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM scheduled_jobs
                WHERE status IN ('failed', 'completed')
                AND completed_at < $1
            """,
                cutoff_date,
            )

            deleted_count = int(result.split()[-1]) if result != "DELETE 0" else 0
            logger.info(f"Cleaned up {deleted_count} old job records")

    async def _cleanup_temp_data(self):
        """Clean up temporary data like old images"""
        # This would clean up temp files, cache data, etc.
        import glob

        # Get project root directory dynamically
        project_root = Path(__file__).parent.parent.parent

        temp_dirs = [project_root / "temp_images", project_root / "data" / "temp_images"]

        total_cleaned = 0
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                # Remove files older than 24 hours
                cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)

                for file_path in glob.glob(str(temp_dir / "*")):
                    if os.path.isfile(file_path):
                        if os.path.getmtime(file_path) < cutoff_time:
                            try:
                                os.remove(file_path)
                                total_cleaned += 1
                            except Exception as e:
                                logger.warning(f"Failed to remove temp file {file_path}: {e}")

        logger.info(f"Cleaned up {total_cleaned} temporary files")
