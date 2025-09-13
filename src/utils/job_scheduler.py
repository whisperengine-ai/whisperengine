"""
Generic Job Scheduler for Discord Bot
=====================================

A flexible job scheduling system that can handle various background tasks:
- Follow-up messages
- Data cleanup tasks  
- Periodic health checks
- Analytics generation
- Backup operations
- etc.

Integrates with existing PostgreSQL and Redis infrastructure.
"""

import asyncio
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(Enum):
    FOLLOW_UP_MESSAGE = "follow_up_message"
    DATA_CLEANUP = "data_cleanup"
    HEALTH_CHECK = "health_check"
    ANALYTICS = "analytics"
    BACKUP = "backup"
    CUSTOM = "custom"

@dataclass
class ScheduledJob:
    """Represents a scheduled job"""
    job_id: str
    job_type: JobType
    scheduled_time: datetime
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

class JobScheduler:
    """
    Generic job scheduler that runs within the existing bot process
    Uses existing PostgreSQL for persistence and Redis for queue management
    """
    
    def __init__(self, postgres_pool, redis_client=None, memory_manager=None):
        self.postgres_pool = postgres_pool
        self.redis_client = redis_client
        self.memory_manager = memory_manager
        self.job_handlers: Dict[JobType, Callable] = {}
        self.scheduler_task: Optional[asyncio.Task] = None
        self.running = False
        self.check_interval = 30  # Check for due jobs every 30 seconds
        
    async def initialize(self):
        """Initialize job scheduler tables and setup"""
        await self._create_job_tables()
        await self._register_default_handlers()
        
    async def _create_job_tables(self):
        """Create job scheduler tables if they don't exist"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    job_id VARCHAR(255) PRIMARY KEY,
                    job_type VARCHAR(100) NOT NULL,
                    scheduled_time TIMESTAMPTZ NOT NULL,
                    payload JSONB NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    started_at TIMESTAMPTZ,
                    completed_at TIMESTAMPTZ,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3
                );
                
                CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_time_status 
                ON scheduled_jobs(scheduled_time, status);
                
                CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_type 
                ON scheduled_jobs(job_type);
            """)
            
            # Job execution history for analytics
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS job_execution_history (
                    execution_id SERIAL PRIMARY KEY,
                    job_id VARCHAR(255) NOT NULL,
                    job_type VARCHAR(100) NOT NULL,
                    execution_time TIMESTAMPTZ NOT NULL,
                    duration_ms INTEGER,
                    status VARCHAR(50) NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_job_history_time 
                ON job_execution_history(execution_time);
            """)
    
    async def _register_default_handlers(self):
        """Register default job type handlers"""
        from src.jobs.follow_up_handler import FollowUpHandler
        from src.jobs.cleanup_handler import CleanupHandler
        
        # Register job handlers with memory manager if available
        follow_up_handler = FollowUpHandler(self.postgres_pool, memory_manager=self.memory_manager)
        self.register_handler(JobType.FOLLOW_UP_MESSAGE, follow_up_handler)
        self.register_handler(JobType.DATA_CLEANUP, CleanupHandler(self.postgres_pool))
        
    def register_handler(self, job_type: JobType, handler: Any):
        """Register a handler for a specific job type"""
        self.job_handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type.value}")
    
    def set_bot_client(self, bot_client):
        """Set the bot client for handlers that need it"""
        for job_type, handler in self.job_handlers.items():
            if hasattr(handler, 'set_bot'):
                handler.set_bot(bot_client)
                logger.info(f"Set bot client for {job_type.value} handler")
        logger.info("Bot client set for all applicable job handlers")
    
    async def schedule_job(self, 
                          job_type: JobType, 
                          scheduled_time: datetime,
                          payload: Dict[str, Any],
                          job_id: Optional[str] = None,
                          max_retries: int = 3) -> str:
        """Schedule a new job"""
        if job_id is None:
            job_id = str(uuid.uuid4())
            
        job = ScheduledJob(
            job_id=job_id,
            job_type=job_type,
            scheduled_time=scheduled_time,
            payload=payload,
            max_retries=max_retries
        )
        
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO scheduled_jobs 
                (job_id, job_type, scheduled_time, payload, status, created_at, max_retries)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, job_id, job_type.value, scheduled_time, json.dumps(payload), 
                JobStatus.PENDING.value, job.created_at, max_retries)
        
        logger.info(f"Scheduled {job_type.value} job {job_id} for {scheduled_time}")
        return job_id
    
    async def schedule_follow_up_message(self, 
                                       user_id: str, 
                                       delay_hours: int = 24,
                                       message_context: Optional[Dict] = None,
                                       channel_id: Optional[str] = None) -> str:
        """Convenience method to schedule follow-up messages"""
        scheduled_time = datetime.now(timezone.utc) + timedelta(hours=delay_hours)
        
        context = message_context or {}
        
        # Extract channel_id from message_context if not provided directly
        if not channel_id and "channel" in context:
            channel_id = str(context["channel"])
        
        payload = {
            "user_id": user_id,
            "channel_id": channel_id,
            "message_context": context,
            "delay_hours": delay_hours
        }
        
        return await self.schedule_job(
            JobType.FOLLOW_UP_MESSAGE,
            scheduled_time,
            payload
        )
    
    async def start(self):
        """Start the job scheduler loop"""
        if self.running:
            logger.warning("Job scheduler already running")
            return
            
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Job scheduler started")
    
    async def stop(self):
        """Stop the job scheduler"""
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Job scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        try:
            while self.running:
                await self._process_due_jobs()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")
    
    async def _process_due_jobs(self):
        """Process all jobs that are due for execution"""
        now = datetime.now(timezone.utc)
        
        async with self.postgres_pool.acquire() as conn:
            # Get all due jobs
            rows = await conn.fetch("""
                SELECT job_id, job_type, scheduled_time, payload, retry_count, max_retries
                FROM scheduled_jobs 
                WHERE status = 'pending' 
                AND scheduled_time <= $1
                ORDER BY scheduled_time ASC
                LIMIT 50
            """, now)
            
            for row in rows:
                job = ScheduledJob(
                    job_id=row['job_id'],
                    job_type=JobType(row['job_type']),
                    scheduled_time=row['scheduled_time'],
                    payload=json.loads(row['payload']),
                    retry_count=row['retry_count'],
                    max_retries=row['max_retries']
                )
                
                # Execute job in background
                asyncio.create_task(self._execute_job(job))
    
    async def _execute_job(self, job: ScheduledJob):
        """Execute a single job"""
        start_time = datetime.now(timezone.utc)
        
        # Mark job as running
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                UPDATE scheduled_jobs 
                SET status = 'running', started_at = $1
                WHERE job_id = $2
            """, start_time, job.job_id)
        
        try:
            # Get handler for job type
            handler = self.job_handlers.get(job.job_type)
            if not handler:
                raise ValueError(f"No handler registered for job type: {job.job_type}")
            
            # Execute the job
            await handler.execute(job.payload)
            
            # Mark as completed
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE scheduled_jobs 
                    SET status = 'completed', completed_at = $1
                    WHERE job_id = $2
                """, end_time, job.job_id)
                
                # Log execution history
                await conn.execute("""
                    INSERT INTO job_execution_history 
                    (job_id, job_type, execution_time, duration_ms, status)
                    VALUES ($1, $2, $3, $4, 'completed')
                """, job.job_id, job.job_type.value, start_time, duration_ms)
            
            logger.info(f"Job {job.job_id} completed successfully in {duration_ms}ms")
            
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            
            # Handle retry logic
            if job.retry_count < job.max_retries:
                # Schedule retry
                retry_delay = min(300 * (2 ** job.retry_count), 3600)  # Exponential backoff, max 1 hour
                retry_time = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)
                
                async with self.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE scheduled_jobs 
                        SET status = 'pending', scheduled_time = $1, retry_count = $2, error_message = $3
                        WHERE job_id = $4
                    """, retry_time, job.retry_count + 1, str(e), job.job_id)
                
                logger.info(f"Job {job.job_id} scheduled for retry {job.retry_count + 1}/{job.max_retries} at {retry_time}")
            else:
                # Mark as failed permanently
                async with self.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE scheduled_jobs 
                        SET status = 'failed', completed_at = $1, error_message = $2
                        WHERE job_id = $3
                    """, datetime.now(timezone.utc), str(e), job.job_id)
                
                # Log failure
                await conn.execute("""
                    INSERT INTO job_execution_history 
                    (job_id, job_type, execution_time, status, error_message)
                    VALUES ($1, $2, $3, 'failed', $4)
                """, job.job_id, job.job_type.value, start_time, str(e))
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        async with self.postgres_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM scheduled_jobs WHERE job_id = $1
            """, job_id)
            
            if row:
                return dict(row)
        return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job"""
        async with self.postgres_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE scheduled_jobs 
                SET status = 'cancelled'
                WHERE job_id = $1 AND status = 'pending'
            """, job_id)
            
            return result != "UPDATE 0"
    
    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        async with self.postgres_pool.acquire() as conn:
            # Job counts by status
            status_counts = await conn.fetch("""
                SELECT status, COUNT(*) as count
                FROM scheduled_jobs 
                GROUP BY status
            """)
            
            # Recent execution stats
            recent_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_executions,
                    AVG(duration_ms) as avg_duration_ms,
                    COUNT(*) FILTER (WHERE status = 'completed') as successful_executions,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_executions
                FROM job_execution_history 
                WHERE execution_time >= NOW() - INTERVAL '24 hours'
            """)
            
            return {
                "running": self.running,
                "status_counts": {row['status']: row['count'] for row in status_counts},
                "recent_24h": dict(recent_stats) if recent_stats else {},
                "registered_handlers": list(self.job_handlers.keys())
            }
