#!/usr/bin/env python3
"""
Database Schema Version Manager
Tracks schema changes and enables migrations across all datastores
"""

import asyncio
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class SchemaVersionManager:
    """Manages database schema versions and migrations"""

    def __init__(
        self,
        postgres_host: str = "localhost",
        postgres_port: int = 5432,
        postgres_db: str = "discord_bot",
        postgres_user: str = "bot_user",
        postgres_password: str = "bot_password_change_me",
    ):
        """Initialize schema version manager"""
        self.postgres_config = {
            "host": postgres_host,
            "port": postgres_port,
            "database": postgres_db,
            "user": postgres_user,
            "password": postgres_password,
        }
        self.pool: asyncpg.Pool | None = None

        # Schema version definitions
        self.schema_versions = {
            "postgresql": {
                "current_version": 3,
                "versions": {
                    1: {
                        "description": "Initial users, emotion_history, interactions tables",
                        "file": "scripts/migrations/v1_initial_schema.sql",
                        "date": "2025-09-12",
                    },
                    2: {
                        "description": "Added privacy tables and context boundaries",
                        "file": "scripts/migrations/v2_privacy_schema.sql",
                        "date": "2025-09-12",
                    },
                    3: {
                        "description": "Added job scheduler and follow-up system tables",
                        "file": "scripts/migrations/v3_scheduler_schema.sql",
                        "date": "2025-09-12",
                    },
                },
            },
            "chromadb": {
                "current_version": 1,
                "versions": {
                    1: {
                        "description": "Initial user_memories and global_facts collections",
                        "script": "scripts/init_chromadb.py",
                        "date": "2025-09-12",
                    }
                },
            },
            "redis": {
                "current_version": 1,
                "versions": {
                    1: {
                        "description": "Redis cache structure for conversations",
                        "description_detail": "Key patterns: discord_cache:messages:*, discord_cache:meta:*",
                        "date": "2025-09-12",
                    }
                },
            },
            "neo4j": {
                "current_version": 1,
                "versions": {
                    1: {
                        "description": "Initial graph schema with User, Topic, Memory, EmotionContext nodes",
                        "script": "scripts/setup_neo4j.sh",
                        "date": "2025-09-12",
                    }
                },
            },
        }

    async def initialize(self) -> bool:
        """Initialize schema version tracking"""
        try:
            logger.info("🔄 Initializing schema version manager...")

            # Connect to PostgreSQL
            if not await self._connect_postgres():
                return False

            # Create schema version table
            if not await self._create_version_table():
                return False

            logger.info("✅ Schema version manager initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize schema version manager: {e}")
            return False

    async def _connect_postgres(self) -> bool:
        """Connect to PostgreSQL for version tracking"""
        try:
            self.pool = await asyncpg.create_pool(**self.postgres_config)

            # Test connection
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")

            logger.info("Connected to PostgreSQL for schema versioning")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False

    async def _create_version_table(self) -> bool:
        """Create the schema_versions table"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_versions (
                        component TEXT PRIMARY KEY,  -- postgresql, chromadb, redis, neo4j
                        current_version INTEGER NOT NULL,
                        last_migration_date TIMESTAMP WITH TIME ZONE,
                        migration_history JSONB DEFAULT '[]'::jsonb,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create update trigger
                await conn.execute(
                    """
                    CREATE OR REPLACE FUNCTION update_schema_versions_updated_at()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql';

                    DROP TRIGGER IF EXISTS update_schema_versions_updated_at ON schema_versions;
                    CREATE TRIGGER update_schema_versions_updated_at
                        BEFORE UPDATE ON schema_versions
                        FOR EACH ROW
                        EXECUTE FUNCTION update_schema_versions_updated_at();
                """
                )

            logger.info("Schema versions table created/verified")
            return True

        except Exception as e:
            logger.error(f"Failed to create schema versions table: {e}")
            return False

    async def get_current_version(self, component: str) -> int | None:
        """Get current schema version for a component"""
        try:
            if not self.pool:
                logger.error("PostgreSQL pool not initialized")
                return None

            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT current_version FROM schema_versions WHERE component = $1", component
                )
                return result
        except Exception as e:
            logger.error(f"Failed to get version for {component}: {e}")
            return None

    async def set_version(
        self, component: str, version: int, migration_info: dict | None = None
    ) -> bool:
        """Set schema version for a component"""
        try:
            if not self.pool:
                logger.error("PostgreSQL pool not initialized")
                return False

            async with self.pool.acquire() as conn:
                # Get existing migration history
                existing = await conn.fetchrow(
                    "SELECT migration_history FROM schema_versions WHERE component = $1", component
                )

                migration_history = existing["migration_history"] if existing else []

                # Add new migration entry
                if migration_info:
                    migration_entry = {
                        "version": version,
                        "timestamp": datetime.now(UTC).isoformat(),
                        **migration_info,
                    }
                    migration_history.append(migration_entry)

                # Upsert version record
                await conn.execute(
                    """
                    INSERT INTO schema_versions (component, current_version, last_migration_date, migration_history)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (component) DO UPDATE SET
                        current_version = EXCLUDED.current_version,
                        last_migration_date = EXCLUDED.last_migration_date,
                        migration_history = EXCLUDED.migration_history,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    component,
                    version,
                    datetime.now(UTC),
                    json.dumps(migration_history),
                )

            logger.info(f"Set {component} schema version to {version}")
            return True

        except Exception as e:
            logger.error(f"Failed to set version for {component}: {e}")
            return False

    async def check_migrations_needed(self) -> dict[str, list[int]]:
        """Check which components need migrations"""
        migrations_needed = {}

        for component, schema_info in self.schema_versions.items():
            current_db_version = await self.get_current_version(component)
            target_version = schema_info["current_version"]

            if current_db_version is None:
                # Component not tracked yet, needs all migrations
                migrations_needed[component] = list(range(1, target_version + 1))
            elif current_db_version < target_version:
                # Needs migrations from current+1 to target
                migrations_needed[component] = list(
                    range(current_db_version + 1, target_version + 1)
                )

        return migrations_needed

    async def get_status_report(self) -> dict[str, Any]:
        """Get comprehensive status report of all schema versions"""
        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "components": {},
            "migrations_needed": await self.check_migrations_needed(),
        }

        for component, schema_info in self.schema_versions.items():
            current_version = await self.get_current_version(component)
            target_version = schema_info["current_version"]

            # Get migration history
            try:
                if not self.pool:
                    history = []
                else:
                    async with self.pool.acquire() as conn:
                        result = await conn.fetchrow(
                            "SELECT * FROM schema_versions WHERE component = $1", component
                        )
                        history = result["migration_history"] if result else []
            except Exception:
                history = []

            report["components"][component] = {
                "current_version": current_version,
                "target_version": target_version,
                "up_to_date": current_version == target_version if current_version else False,
                "migration_history": history,
                "available_versions": schema_info["versions"],
            }

        return report

    async def initialize_component_versions(self) -> bool:
        """Initialize version tracking for all components"""
        try:
            logger.info("🔄 Initializing component version tracking...")

            for component, _schema_info in self.schema_versions.items():
                current_version = await self.get_current_version(component)

                if current_version is None:
                    # Set to version 0 initially (will be updated after migrations)
                    await self.set_version(
                        component,
                        0,
                        {
                            "description": f"Initial version tracking for {component}",
                            "auto_initialized": True,
                        },
                    )
                    logger.info(f"Initialized version tracking for {component}")

            logger.info("✅ Component version tracking initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize component versions: {e}")
            return False

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()


def get_postgres_config() -> dict[str, Any]:
    """Get PostgreSQL configuration from environment"""
    return {
        "postgres_host": os.getenv("POSTGRES_HOST", "localhost"),
        "postgres_port": int(os.getenv("POSTGRES_PORT", "5432")),
        "postgres_db": os.getenv("POSTGRES_DB", "discord_bot"),
        "postgres_user": os.getenv("POSTGRES_USER", "bot_user"),
        "postgres_password": os.getenv("POSTGRES_PASSWORD", "bot_password_change_me"),
    }


async def main():
    """Main function for command-line usage"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


    # Get configuration
    config = get_postgres_config()

    # Initialize version manager
    manager = SchemaVersionManager(**config)

    try:
        # Initialize
        if not await manager.initialize():
            return

        # Initialize component version tracking
        await manager.initialize_component_versions()

        # Get status report
        report = await manager.get_status_report()

        for _component, info in report["components"].items():
            "✅" if info["up_to_date"] else "⚠️"
            info["current_version"] or "untracked"
            info["target_version"]

        # Show needed migrations
        if report["migrations_needed"]:
            for _component, _versions in report["migrations_needed"].items():
                pass
        else:
            pass

    except Exception:
        pass
    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
