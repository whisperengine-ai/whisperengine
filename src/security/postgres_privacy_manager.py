"""
PostgreSQL-backed privacy and context boundaries manager
Replaces JSON file storage with proper database backend for better security and performance
"""

import asyncio
import asyncpg
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from contextlib import asynccontextmanager

from src.security.context_boundaries_security import PrivacyLevel, ConsentStatus, PrivacyPreferences

logger = logging.getLogger(__name__)


class PostgreSQLPrivacyManager:
    """PostgreSQL-backed privacy and context boundaries manager"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "whisper_engine",
        user: str = "bot_user",
        password: str = "bot_password_change_me",
        min_size: int = 3,
        max_size: int = 10,
    ):
        """Initialize PostgreSQL privacy manager"""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        self._lock = asyncio.Lock()

        logger.info(f"PostgreSQL PrivacyManager configured for {host}:{port}/{database}")

    async def initialize(self):
        """Initialize the database connection pool and schema"""
        async with self._lock:
            if self._initialized:
                return

            try:
                # Create connection pool
                self.pool = await asyncpg.create_pool(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    command_timeout=30,
                )

                # Initialize schema
                await self._initialize_schema()

                self._initialized = True
                logger.info("PostgreSQL privacy manager initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL privacy manager: {e}")
                raise

    async def _initialize_schema(self):
        """Initialize the privacy database schema"""
        schema_sql = """
        -- User Privacy Preferences Table
        CREATE TABLE IF NOT EXISTS user_privacy_preferences (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL UNIQUE,
            privacy_level TEXT NOT NULL DEFAULT 'moderate' CHECK (privacy_level IN ('strict', 'moderate', 'permissive')),
            allow_cross_server BOOLEAN DEFAULT FALSE,
            allow_dm_to_server BOOLEAN DEFAULT FALSE,
            allow_server_to_dm BOOLEAN DEFAULT FALSE,
            allow_private_to_public BOOLEAN DEFAULT FALSE,
            custom_rules JSONB DEFAULT '{}',
            consent_status TEXT NOT NULL DEFAULT 'not_asked' CHECK (consent_status IN ('not_asked', 'granted', 'denied', 'expired')),
            consent_timestamp TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Context Boundary Audit Log Table
        CREATE TABLE IF NOT EXISTS context_boundary_audit (
            id SERIAL PRIMARY KEY,
            user_id TEXT NOT NULL,
            request_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            source_context TEXT NOT NULL,
            target_context TEXT NOT NULL,
            decision TEXT NOT NULL CHECK (decision IN ('allowed', 'blocked', 'consent_requested', 'allowed_once', 'denied_once', 'allowed_always', 'denied_always')),
            reason TEXT,
            privacy_level TEXT
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_privacy_preferences_user_id ON user_privacy_preferences(user_id);
        CREATE INDEX IF NOT EXISTS idx_privacy_preferences_privacy_level ON user_privacy_preferences(privacy_level);
        CREATE INDEX IF NOT EXISTS idx_privacy_preferences_updated_at ON user_privacy_preferences(updated_at);
        
        CREATE INDEX IF NOT EXISTS idx_audit_user_id ON context_boundary_audit(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON context_boundary_audit(request_timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_decision ON context_boundary_audit(decision);
        CREATE INDEX IF NOT EXISTS idx_audit_source_target ON context_boundary_audit(source_context, target_context);
        
        -- Auto-update timestamp function and trigger
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_privacy_preferences_updated_at ON user_privacy_preferences;
        CREATE TRIGGER update_privacy_preferences_updated_at
            BEFORE UPDATE ON user_privacy_preferences
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """

        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
            logger.info("Privacy database schema initialized")

    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL privacy manager connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """Context manager for database connections"""
        if not self._initialized:
            await self.initialize()

        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        async with self.pool.acquire() as conn:
            yield conn

    async def get_user_preferences(self, user_id: str) -> Optional[PrivacyPreferences]:
        """Get user privacy preferences"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, privacy_level, allow_cross_server, allow_dm_to_server,
                       allow_server_to_dm, allow_private_to_public, custom_rules,
                       consent_status, consent_timestamp, updated_at
                FROM user_privacy_preferences 
                WHERE user_id = $1
            """,
                user_id,
            )

            if row:
                return PrivacyPreferences(
                    user_id=row["user_id"],
                    privacy_level=PrivacyLevel(row["privacy_level"]),
                    allow_cross_server=row["allow_cross_server"],
                    allow_dm_to_server=row["allow_dm_to_server"],
                    allow_server_to_dm=row["allow_server_to_dm"],
                    allow_private_to_public=row["allow_private_to_public"],
                    custom_rules=dict(row["custom_rules"]),
                    consent_status=ConsentStatus(row["consent_status"]),
                    consent_timestamp=row["consent_timestamp"],
                    updated_timestamp=row["updated_at"],
                )
            return None

    async def update_user_preferences(self, preferences: PrivacyPreferences):
        """Update user privacy preferences"""
        async with self.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO user_privacy_preferences 
                (user_id, privacy_level, allow_cross_server, allow_dm_to_server,
                 allow_server_to_dm, allow_private_to_public, custom_rules,
                 consent_status, consent_timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (user_id) DO UPDATE SET
                    privacy_level = EXCLUDED.privacy_level,
                    allow_cross_server = EXCLUDED.allow_cross_server,
                    allow_dm_to_server = EXCLUDED.allow_dm_to_server,
                    allow_server_to_dm = EXCLUDED.allow_server_to_dm,
                    allow_private_to_public = EXCLUDED.allow_private_to_public,
                    custom_rules = EXCLUDED.custom_rules,
                    consent_status = EXCLUDED.consent_status,
                    consent_timestamp = EXCLUDED.consent_timestamp,
                    updated_at = CURRENT_TIMESTAMP
            """,
                preferences.user_id,
                preferences.privacy_level.value,
                preferences.allow_cross_server,
                preferences.allow_dm_to_server,
                preferences.allow_server_to_dm,
                preferences.allow_private_to_public,
                json.dumps(preferences.custom_rules),
                preferences.consent_status.value,
                preferences.consent_timestamp,
            )

            logger.info(f"Updated privacy preferences for user {preferences.user_id}")

    async def log_decision(
        self,
        user_id: str,
        source_context: str,
        target_context: str,
        decision: str,
        reason: str,
        privacy_level: str,
    ):
        """Log a privacy decision to the audit trail"""
        async with self.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO context_boundary_audit 
                (user_id, source_context, target_context, decision, reason, privacy_level)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                user_id,
                source_context,
                target_context,
                decision,
                reason,
                privacy_level,
            )

    async def get_audit_history(
        self, user_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit history, optionally filtered by user"""
        async with self.get_connection() as conn:
            if user_id:
                rows = await conn.fetch(
                    """
                    SELECT user_id, request_timestamp, source_context, target_context,
                           decision, reason, privacy_level
                    FROM context_boundary_audit 
                    WHERE user_id = $1
                    ORDER BY request_timestamp DESC 
                    LIMIT $2
                """,
                    user_id,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT user_id, request_timestamp, source_context, target_context,
                           decision, reason, privacy_level
                    FROM context_boundary_audit 
                    ORDER BY request_timestamp DESC 
                    LIMIT $1
                """,
                    limit,
                )

            return [dict(row) for row in rows]

    async def get_all_user_preferences(self) -> Dict[str, PrivacyPreferences]:
        """Get all user privacy preferences"""
        async with self.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, privacy_level, allow_cross_server, allow_dm_to_server,
                       allow_server_to_dm, allow_private_to_public, custom_rules,
                       consent_status, consent_timestamp, updated_at
                FROM user_privacy_preferences
            """
            )

            preferences = {}
            for row in rows:
                preferences[row["user_id"]] = PrivacyPreferences(
                    user_id=row["user_id"],
                    privacy_level=PrivacyLevel(row["privacy_level"]),
                    allow_cross_server=row["allow_cross_server"],
                    allow_dm_to_server=row["allow_dm_to_server"],
                    allow_server_to_dm=row["allow_server_to_dm"],
                    allow_private_to_public=row["allow_private_to_public"],
                    custom_rules=dict(row["custom_rules"]),
                    consent_status=ConsentStatus(row["consent_status"]),
                    consent_timestamp=row["consent_timestamp"],
                    updated_timestamp=row["updated_at"],
                )

            return preferences

    async def cleanup_old_audit_entries(self, days_to_keep: int = 90):
        """Clean up old audit entries for privacy compliance"""
        async with self.get_connection() as conn:
            result = await conn.execute(
                """
                DELETE FROM context_boundary_audit 
                WHERE request_timestamp < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """
                % days_to_keep
            )

            count = int(result.split()[-1])
            logger.info(f"Cleaned up {count} old audit entries older than {days_to_keep} days")
            return count


def create_privacy_manager_from_env() -> PostgreSQLPrivacyManager:
    """Create privacy manager from environment variables"""
    return PostgreSQLPrivacyManager(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "whisper_engine"),
        user=os.getenv("POSTGRES_USER", "bot_user"),
        password=os.getenv("POSTGRES_PASSWORD", "bot_password_change_me"),
        min_size=int(os.getenv("POSTGRES_PRIVACY_MIN_CONNECTIONS", "3")),
        max_size=int(os.getenv("POSTGRES_PRIVACY_MAX_CONNECTIONS", "10")),
    )
