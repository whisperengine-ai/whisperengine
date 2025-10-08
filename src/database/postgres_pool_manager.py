"""
Centralized PostgreSQL Connection Pool Manager for WhisperEngine

This module provides a singleton PostgreSQL connection pool that all components
can use to avoid connection pool duplication and concurrency issues.
"""

import asyncio
import logging
import os
from typing import Optional
import asyncpg

logger = logging.getLogger(__name__)


class PostgreSQLPoolManager:
    """Singleton PostgreSQL connection pool manager"""
    
    _instance = None
    _pool = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_pool(self) -> Optional[asyncpg.Pool]:
        """Get or create the PostgreSQL connection pool"""
        if self._pool is None:
            async with self._lock:
                if self._pool is None:  # Double-check locking
                    await self._create_pool()
        return self._pool
    
    async def _create_pool(self) -> None:
        """Create the PostgreSQL connection pool"""
        try:
            logger.info("🐘 Creating centralized PostgreSQL connection pool...")
            
            # Get PostgreSQL configuration from environment
            db_host = os.getenv("POSTGRES_HOST", "whisperengine-multi-postgres")
            db_port = int(os.getenv("POSTGRES_PORT", "5432"))
            db_name = os.getenv("POSTGRES_DB", "whisperengine")
            db_user = os.getenv("POSTGRES_USER", "whisperengine")
            db_password = os.getenv("POSTGRES_PASSWORD", "whisperengine")
            
            # Create connection pool with optimal settings
            self._pool = await asyncpg.create_pool(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password,
                min_size=3,  # Increased from 2 to handle concurrent operations
                max_size=15, # Increased from 10 to handle multiple components
                command_timeout=30,
                server_settings={
                    'application_name': 'whisperengine',
                    'timezone': 'UTC'
                }
            )
            
            logger.info("✅ Centralized PostgreSQL pool created: %s:%s/%s (min_size=3, max_size=15)", 
                       db_host, db_port, db_name)
            
        except Exception as e:
            logger.error("❌ Failed to create PostgreSQL pool: %s", str(e))
            self._pool = None
            raise
    
    async def close(self) -> None:
        """Close the PostgreSQL connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("🐘 PostgreSQL connection pool closed")
    
    def is_available(self) -> bool:
        """Check if pool is available"""
        return self._pool is not None


# Module-level pool manager instance
_pool_manager = None


async def get_postgres_pool() -> Optional[asyncpg.Pool]:
    """
    Get the centralized PostgreSQL connection pool.
    
    This is the ONLY way application components should get database connections.
    
    Returns:
        asyncpg.Pool: The centralized connection pool
    """
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = PostgreSQLPoolManager()
    
    return await _pool_manager.get_pool()


async def close_postgres_pool() -> None:
    """Close the centralized PostgreSQL connection pool"""
    if _pool_manager:
        await _pool_manager.close()


def is_postgres_pool_available() -> bool:
    """Check if PostgreSQL pool is available"""
    return _pool_manager is not None and _pool_manager.is_available()


async def execute_with_pool(query: str, *args) -> list:
    """
    Execute a query using the centralized pool.
    
    Args:
        query: SQL query
        *args: Query parameters
        
    Returns:
        Query results
    """
    pool = await get_postgres_pool()
    if not pool:
        raise RuntimeError("PostgreSQL pool not available")
    
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def execute_transaction_with_pool(queries_and_params: list) -> None:
    """
    Execute multiple queries in a transaction using the centralized pool.
    
    Args:
        queries_and_params: List of (query, params) tuples
    """
    pool = await get_postgres_pool()
    if not pool:
        raise RuntimeError("PostgreSQL pool not available")
    
    async with pool.acquire() as conn:
        async with conn.transaction():
            for query, params in queries_and_params:
                await conn.execute(query, *params)