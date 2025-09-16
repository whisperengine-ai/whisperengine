"""
Database Abstraction Layer for WhisperEngine
Provides unified interface for SQLite (desktop) and PostgreSQL (cloud) deployments.
"""

import asyncio
import os
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import asyncpg

    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

try:
    import aiosqlite

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


class DatabaseType(Enum):
    """Database types supported by the abstraction layer"""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    POSTGRESQL_CLUSTER = "postgresql_cluster"


@dataclass
class DatabaseConfig:
    """Database configuration"""

    db_type: DatabaseType
    connection_string: str
    pool_size: int = 5
    timeout: int = 30
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    encryption_enabled: bool = False
    migration_enabled: bool = True


@dataclass
class QueryResult:
    """Standardized query result"""

    rows: list[dict[str, Any]]
    row_count: int
    execution_time_ms: float
    success: bool
    error: str | None = None


class DatabaseConnectionError(Exception):
    """Database connection errors"""

    pass


class DatabaseQueryError(Exception):
    """Database query errors"""

    pass


class AbstractDatabaseAdapter(ABC):
    """Abstract base class for database adapters"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_pool = None
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish database connection"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    async def execute_query(self, query: str, params: dict[str, Any] | None = None) -> QueryResult:
        """Execute a query and return results"""
        pass

    @abstractmethod
    async def execute_transaction(self, queries: list[tuple[str, dict[str, Any] | None]]) -> bool:
        """Execute multiple queries in a transaction"""
        pass

    @abstractmethod
    async def create_tables(self, schema: dict[str, str]) -> bool:
        """Create database tables from schema"""
        pass

    @abstractmethod
    async def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        pass

    @abstractmethod
    async def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        pass

    @abstractmethod
    async def migrate_schema(self, migration_scripts: list[str]) -> bool:
        """Apply schema migrations"""
        pass

    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._connected


class SQLiteAdapter(AbstractDatabaseAdapter):
    """SQLite database adapter for desktop deployments"""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.db_path = self._extract_db_path(config.connection_string)
        self.connection = None

    def _extract_db_path(self, connection_string: str) -> str:
        """Extract database path from connection string"""
        if connection_string.startswith("sqlite:///"):
            return connection_string[10:]  # Remove 'sqlite:///'
        elif connection_string.startswith("sqlite://"):
            return connection_string[9:]  # Remove 'sqlite://'
        else:
            return connection_string

    async def connect(self) -> bool:
        """Establish SQLite connection"""
        try:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

            if AIOSQLITE_AVAILABLE:
                self.connection = await aiosqlite.connect(self.db_path)
                # Enable WAL mode for better performance
                await self.connection.execute("PRAGMA journal_mode=WAL")
                await self.connection.execute("PRAGMA synchronous=NORMAL")
                await self.connection.execute("PRAGMA cache_size=10000")
                await self.connection.commit()
            else:
                # Fallback to synchronous sqlite3
                self.connection = sqlite3.connect(self.db_path)
                self.connection.execute("PRAGMA journal_mode=WAL")
                self.connection.execute("PRAGMA synchronous=NORMAL")
                self.connection.execute("PRAGMA cache_size=10000")
                self.connection.commit()

            self._connected = True
            return True

        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to SQLite: {e}")

    async def disconnect(self) -> None:
        """Close SQLite connection"""
        if self.connection:
            if AIOSQLITE_AVAILABLE:
                await self.connection.close()
            else:
                self.connection.close()
            self._connected = False

    async def execute_query(self, query: str, params: dict[str, Any] | None = None) -> QueryResult:
        """Execute SQLite query"""
        import time

        start_time = time.time()

        try:
            if AIOSQLITE_AVAILABLE:
                cursor = await self.connection.execute(query, params or {})
                rows = await cursor.fetchall()
                await self.connection.commit()

                # Convert rows to dict format
                columns = (
                    [description[0] for description in cursor.description]
                    if cursor.description
                    else []
                )
                result_rows = [dict(zip(columns, row, strict=False)) for row in rows]
            else:
                # Synchronous fallback
                cursor = self.connection.execute(query, params or {})
                rows = cursor.fetchall()
                self.connection.commit()

                # Convert rows to dict format
                columns = (
                    [description[0] for description in cursor.description]
                    if cursor.description
                    else []
                )
                result_rows = [dict(zip(columns, row, strict=False)) for row in rows]

            execution_time = (time.time() - start_time) * 1000

            return QueryResult(
                rows=result_rows,
                row_count=len(result_rows),
                execution_time_ms=execution_time,
                success=True,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return QueryResult(
                rows=[], row_count=0, execution_time_ms=execution_time, success=False, error=str(e)
            )

    async def execute_transaction(self, queries: list[tuple[str, dict[str, Any] | None]]) -> bool:
        """Execute multiple queries in a transaction"""
        try:
            if AIOSQLITE_AVAILABLE:
                async with self.connection:
                    for query, params in queries:
                        await self.connection.execute(query, params or {})
            else:
                # Synchronous transaction
                self.connection.execute("BEGIN TRANSACTION")
                try:
                    for query, params in queries:
                        self.connection.execute(query, params or {})
                    self.connection.commit()
                except Exception:
                    self.connection.rollback()
                    raise

            return True

        except Exception as e:
            raise DatabaseQueryError(f"Transaction failed: {e}")

    async def create_tables(self, schema: dict[str, str]) -> bool:
        """Create SQLite tables from schema"""
        try:
            for _table_name, table_sql in schema.items():
                await self.execute_query(table_sql)
            return True
        except Exception as e:
            raise DatabaseQueryError(f"Failed to create tables: {e}")

    async def backup_database(self, backup_path: str) -> bool:
        """Create SQLite database backup"""
        try:
            backup_dir = Path(backup_path).parent
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Simple file copy for SQLite
            import shutil

            shutil.copy2(self.db_path, backup_path)

            # Also backup WAL and SHM files if they exist
            wal_path = f"{self.db_path}-wal"
            shm_path = f"{self.db_path}-shm"

            if os.path.exists(wal_path):
                shutil.copy2(wal_path, f"{backup_path}-wal")
            if os.path.exists(shm_path):
                shutil.copy2(shm_path, f"{backup_path}-shm")

            return True

        except Exception as e:
            raise DatabaseQueryError(f"Backup failed: {e}")

    async def restore_database(self, backup_path: str) -> bool:
        """Restore SQLite database from backup"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            # Close current connection
            await self.disconnect()

            # Restore database file
            import shutil

            shutil.copy2(backup_path, self.db_path)

            # Restore WAL and SHM files if they exist
            wal_backup = f"{backup_path}-wal"
            shm_backup = f"{backup_path}-shm"

            if os.path.exists(wal_backup):
                shutil.copy2(wal_backup, f"{self.db_path}-wal")
            if os.path.exists(shm_backup):
                shutil.copy2(shm_backup, f"{self.db_path}-shm")

            # Reconnect
            await self.connect()
            return True

        except Exception as e:
            raise DatabaseQueryError(f"Restore failed: {e}")

    async def migrate_schema(self, migration_scripts: list[str]) -> bool:
        """Apply SQLite schema migrations"""
        try:
            # Create migrations table if it doesn't exist
            await self.execute_query(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_name TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Apply each migration
            for script in migration_scripts:
                # Check if migration already applied
                result = await self.execute_query(
                    "SELECT COUNT(*) as count FROM schema_migrations WHERE script_name = ?",
                    {"script_name": script},
                )

                if result.rows[0]["count"] == 0:
                    # Apply migration (script should contain the SQL)
                    await self.execute_query(script)

                    # Record migration
                    await self.execute_query(
                        "INSERT INTO schema_migrations (script_name) VALUES (?)",
                        {"script_name": script},
                    )

            return True

        except Exception as e:
            raise DatabaseQueryError(f"Migration failed: {e}")


class PostgreSQLAdapter(AbstractDatabaseAdapter):
    """PostgreSQL database adapter for cloud deployments"""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.pool = None

    async def connect(self) -> bool:
        """Establish PostgreSQL connection pool"""
        if not ASYNCPG_AVAILABLE:
            raise DatabaseConnectionError("asyncpg is required for PostgreSQL support")

        try:
            self.pool = await asyncpg.create_pool(
                self.config.connection_string,
                min_size=1,
                max_size=self.config.pool_size,
                command_timeout=self.config.timeout,
            )
            self._connected = True
            return True

        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to PostgreSQL: {e}")

    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool"""
        if self.pool:
            await self.pool.close()
            self._connected = False

    async def execute_query(self, query: str, params: dict[str, Any] | None = None) -> QueryResult:
        """Execute PostgreSQL query"""
        import time

        start_time = time.time()

        try:
            async with self.pool.acquire() as connection:
                # Convert named parameters to positional for asyncpg
                if params:
                    # Simple parameter substitution (could be enhanced)
                    for key, _value in params.items():
                        query = query.replace(f":{key}", f"${list(params.keys()).index(key) + 1}")
                    rows = await connection.fetch(query, *params.values())
                else:
                    rows = await connection.fetch(query)

                # Convert asyncpg Records to dict
                result_rows = [dict(row) for row in rows]

            execution_time = (time.time() - start_time) * 1000

            return QueryResult(
                rows=result_rows,
                row_count=len(result_rows),
                execution_time_ms=execution_time,
                success=True,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return QueryResult(
                rows=[], row_count=0, execution_time_ms=execution_time, success=False, error=str(e)
            )

    async def execute_transaction(self, queries: list[tuple[str, dict[str, Any] | None]]) -> bool:
        """Execute multiple queries in a PostgreSQL transaction"""
        try:
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    for query, params in queries:
                        if params:
                            # Convert named to positional parameters
                            for key, _value in params.items():
                                query = query.replace(
                                    f":{key}", f"${list(params.keys()).index(key) + 1}"
                                )
                            await connection.execute(query, *params.values())
                        else:
                            await connection.execute(query)

            return True

        except Exception as e:
            raise DatabaseQueryError(f"Transaction failed: {e}")

    async def create_tables(self, schema: dict[str, str]) -> bool:
        """Create PostgreSQL tables from schema"""
        try:
            for _table_name, table_sql in schema.items():
                await self.execute_query(table_sql)
            return True
        except Exception as e:
            raise DatabaseQueryError(f"Failed to create tables: {e}")

    async def backup_database(self, backup_path: str) -> bool:
        """Create PostgreSQL database backup using pg_dump"""
        try:
            import subprocess
            from urllib.parse import urlparse

            # Parse connection string
            parsed = urlparse(self.config.connection_string)

            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h",
                parsed.hostname or "localhost",
                "-p",
                str(parsed.port or 5432),
                "-U",
                parsed.username or "postgres",
                "-d",
                parsed.path.lstrip("/") if parsed.path else "postgres",
                "-f",
                backup_path,
                "--verbose",
            ]

            # Set password via environment
            env = os.environ.copy()
            if parsed.password:
                env["PGPASSWORD"] = parsed.password

            # Execute backup
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                raise DatabaseQueryError(f"pg_dump failed: {result.stderr}")

        except Exception as e:
            raise DatabaseQueryError(f"Backup failed: {e}")

    async def restore_database(self, backup_path: str) -> bool:
        """Restore PostgreSQL database from backup using psql"""
        try:
            import subprocess
            from urllib.parse import urlparse

            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            # Parse connection string
            parsed = urlparse(self.config.connection_string)

            # Build psql command
            cmd = [
                "psql",
                "-h",
                parsed.hostname or "localhost",
                "-p",
                str(parsed.port or 5432),
                "-U",
                parsed.username or "postgres",
                "-d",
                parsed.path.lstrip("/") if parsed.path else "postgres",
                "-f",
                backup_path,
            ]

            # Set password via environment
            env = os.environ.copy()
            if parsed.password:
                env["PGPASSWORD"] = parsed.password

            # Execute restore
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            else:
                raise DatabaseQueryError(f"psql failed: {result.stderr}")

        except Exception as e:
            raise DatabaseQueryError(f"Restore failed: {e}")

    async def migrate_schema(self, migration_scripts: list[str]) -> bool:
        """Apply PostgreSQL schema migrations"""
        try:
            # Create migrations table if it doesn't exist
            await self.execute_query(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    script_name VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Apply each migration
            for script in migration_scripts:
                # Check if migration already applied
                result = await self.execute_query(
                    "SELECT COUNT(*) as count FROM schema_migrations WHERE script_name = :script_name",
                    {"script_name": script},
                )

                if result.rows[0]["count"] == 0:
                    # Apply migration
                    await self.execute_query(script)

                    # Record migration
                    await self.execute_query(
                        "INSERT INTO schema_migrations (script_name) VALUES (:script_name)",
                        {"script_name": script},
                    )

            return True

        except Exception as e:
            raise DatabaseQueryError(f"Migration failed: {e}")


class DatabaseManager:
    """Unified database manager that provides abstraction over different database types"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.adapter = self._create_adapter()

    def _create_adapter(self) -> AbstractDatabaseAdapter:
        """Create appropriate database adapter based on configuration"""
        if self.config.db_type == DatabaseType.SQLITE:
            return SQLiteAdapter(self.config)
        elif self.config.db_type in [DatabaseType.POSTGRESQL, DatabaseType.POSTGRESQL_CLUSTER]:
            return PostgreSQLAdapter(self.config)
        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")

    async def initialize(self) -> bool:
        """Initialize database connection"""
        return await self.adapter.connect()

    async def cleanup(self) -> None:
        """Cleanup database resources"""
        await self.adapter.disconnect()

    async def query(self, query: str, params: dict[str, Any] | None = None) -> QueryResult:
        """Execute a database query"""
        return await self.adapter.execute_query(query, params)

    async def transaction(self, queries: list[tuple[str, dict[str, Any] | None]]) -> bool:
        """Execute queries in a transaction"""
        return await self.adapter.execute_transaction(queries)

    async def setup_schema(self, schema: dict[str, str]) -> bool:
        """Create database schema"""
        return await self.adapter.create_tables(schema)

    async def backup(self, backup_path: str) -> bool:
        """Create database backup"""
        return await self.adapter.backup_database(backup_path)

    async def restore(self, backup_path: str) -> bool:
        """Restore database from backup"""
        return await self.adapter.restore_database(backup_path)

    async def migrate(self, migration_scripts: list[str]) -> bool:
        """Apply schema migrations"""
        return await self.adapter.migrate_schema(migration_scripts)

    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.adapter.is_connected

    @property
    def database_type(self) -> DatabaseType:
        """Get database type"""
        return self.config.db_type


# Factory function for easy database manager creation
def create_database_manager(
    database_type: str, connection_string: str, pool_size: int = 5, **kwargs
) -> DatabaseManager:
    """Factory function to create database manager"""

    # Map string to enum
    db_type_mapping = {
        "sqlite": DatabaseType.SQLITE,
        "postgresql": DatabaseType.POSTGRESQL,
        "postgresql_cluster": DatabaseType.POSTGRESQL_CLUSTER,
    }

    db_type = db_type_mapping.get(database_type.lower())
    if not db_type:
        raise ValueError(f"Unsupported database type: {database_type}")

    config = DatabaseConfig(
        db_type=db_type, connection_string=connection_string, pool_size=pool_size, **kwargs
    )

    return DatabaseManager(config)


# Example usage and testing
async def main():
    """Example usage of the database abstraction layer"""

    # Example SQLite configuration for desktop
    sqlite_manager = create_database_manager(
        database_type="sqlite",
        connection_string="sqlite:///~/.whisperengine/database.db",
        pool_size=2,
    )

    try:
        # Initialize connection
        await sqlite_manager.initialize()

        # Example schema
        schema = {
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "messages": """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """,
        }

        # Setup schema
        await sqlite_manager.setup_schema(schema)

        # Example query
        await sqlite_manager.query(
            "INSERT INTO users (user_id, username) VALUES (:user_id, :username)",
            {"user_id": "123456", "username": "TestUser"},
        )

        # Query data
        await sqlite_manager.query("SELECT * FROM users")

    finally:
        await sqlite_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
