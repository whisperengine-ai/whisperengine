"""
Database Integration for WhisperEngine
Simple database integration using Docker environment variables.
"""

import asyncio
import os
from pathlib import Path
from typing import Any

from src.database.abstract_database import DatabaseManager, create_database_manager


class WhisperEngineDatabaseConfig:
    """Database configuration for WhisperEngine using environment variables"""

    def __init__(self):
        """Initialize with simple environment variable configuration"""
        self.deployment_info = self._get_simple_deployment_info()

    def _get_simple_deployment_info(self) -> dict[str, Any]:
        """Get basic deployment info from environment variables"""
        return {
            "deployment_mode": os.environ.get("DEPLOYMENT_MODE", "container"),
            "use_postgresql": os.environ.get("USE_POSTGRESQL", "false").lower() == "true",
            "use_redis": os.environ.get("USE_REDIS_CACHE", "false").lower() == "true",
        }

    def get_database_connection_string(self) -> str:
        """Generate database connection string based on environment variables"""

        # Check if PostgreSQL is enabled via environment variable
        if os.environ.get("USE_POSTGRESQL", "false").lower() == "true":
            # PostgreSQL configuration from environment
            host = os.environ.get("POSTGRES_HOST", "localhost")
            port = os.environ.get("POSTGRES_PORT", "5432")
            database = os.environ.get("POSTGRES_DB", "whisperengine")
            username = os.environ.get("POSTGRES_USER", "whisperengine")
            password = os.environ.get("POSTGRES_PASSWORD", "")

            if password:
                return f"postgresql://{username}:{password}@{host}:{port}/{database}"
            else:
                return f"postgresql://{username}@{host}:{port}/{database}"
        else:
            # Default to SQLite
            db_path = Path.home() / ".whisperengine" / "database.db"
            return f"sqlite:///{db_path}"

    def get_config_info(self) -> dict:
        """Get database configuration information using environment variables"""
        return {
            "deployment_mode": os.environ.get("DEPLOYMENT_MODE", "development"),
            "scale_tier": "docker",  # Simple Docker deployment
        }

    def get_backup_configuration(self) -> dict[str, Any]:
        """Get backup configuration from environment variables"""
        backup_enabled = os.environ.get("BACKUP_ENABLED", "false").lower() == "true"

        return {
            "enabled": backup_enabled,
            "directory": os.environ.get("BACKUP_DIRECTORY", "./data/backups") if backup_enabled else None,
            "max_files": int(os.environ.get("BACKUP_MAX_FILES", "5")) if backup_enabled else 0,
            "compression": os.environ.get("BACKUP_COMPRESSION", "true").lower() == "true" if backup_enabled else False,
        }

    def get_database_manager(self) -> DatabaseManager:
        """Create and return a database manager based on environment configuration"""
        connection_string = self.get_database_connection_string()
        use_postgresql = os.environ.get("USE_POSTGRESQL", "false").lower() == "true"
        
        if use_postgresql:
            return create_database_manager("postgresql", connection_string)
        else:
            return create_database_manager("in_memory", connection_string)


class WhisperEngineSchema:
    """WhisperEngine database schema definitions"""

    @staticmethod
    def get_core_schema() -> dict[str, str]:
        """Get core WhisperEngine database schema"""
        return {
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    preferences TEXT DEFAULT '{}',
                    privacy_settings TEXT DEFAULT '{}'
                )
            """,
            "conversations": """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    bot_response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    context_used TEXT,
                    response_time_ms INTEGER,
                    ai_model_used TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """,
            "memory_entries": """
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance_score REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """,
            "facts": """
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    fact_type TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.8,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified BOOLEAN DEFAULT FALSE,
                    global_fact BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """,
            "emotions": """
                CREATE TABLE IF NOT EXISTS emotions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    detected_emotion TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    context TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_adapted BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """,
            "relationships": """
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL DEFAULT 0.5,
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    interaction_count INTEGER DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """,
            "system_settings": """
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "performance_metrics": """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT DEFAULT '{}'
                )
            """,
            "banned_users": """
                CREATE TABLE IF NOT EXISTS banned_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_user_id TEXT NOT NULL UNIQUE,
                    banned_by TEXT NOT NULL,
                    ban_reason TEXT,
                    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    notes TEXT
                )
            """,
        }

    @staticmethod
    def get_postgresql_schema() -> dict[str, str]:
        """Get PostgreSQL-specific schema (with UUID support)"""
        schema = WhisperEngineSchema.get_core_schema()

        # Modify for PostgreSQL-specific features
        schema["users"] = schema["users"].replace(
            "user_id TEXT PRIMARY KEY", "id SERIAL PRIMARY KEY, user_id TEXT UNIQUE NOT NULL"
        )

        schema["conversations"] = (
            schema["conversations"]
            .replace("id INTEGER PRIMARY KEY AUTOINCREMENT", "id SERIAL PRIMARY KEY")
            .replace(
                "FOREIGN KEY (user_id) REFERENCES users (user_id)",
                "FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE",
            )
        )

        # Transform all other tables with AUTOINCREMENT to SERIAL
        for table_name in [
            "memory_entries",
            "facts",
            "emotions",
            "relationships",
            "performance_metrics",
            "banned_users",
        ]:
            if table_name in schema:
                schema[table_name] = schema[table_name].replace(
                    "id INTEGER PRIMARY KEY AUTOINCREMENT", "id SERIAL PRIMARY KEY"
                )

        # Add indexes for better performance
        schema[
            "indexes"
        ] = """
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
            CREATE INDEX IF NOT EXISTS idx_memory_entries_user_id ON memory_entries(user_id);
            CREATE INDEX IF NOT EXISTS idx_facts_user_id ON facts(user_id);
            CREATE INDEX IF NOT EXISTS idx_emotions_user_id ON emotions(user_id);
            CREATE INDEX IF NOT EXISTS idx_banned_users_discord_id ON banned_users(discord_user_id);
            CREATE INDEX IF NOT EXISTS idx_banned_users_active ON banned_users(is_active);
        """

        return schema


class DatabaseIntegrationManager:
    """Main integration manager for WhisperEngine database operations"""

    def __init__(self):
        """Initialize with simple environment variable configuration"""
        self.config_manager = None
        self.db_config = WhisperEngineDatabaseConfig()
        self.database_manager: DatabaseManager | None = None
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize the database system"""
        try:
            # Create database manager
            self.database_manager = self.db_config.get_database_manager()

            # Connect to database
            await self.database_manager.initialize()

            # Setup schema
            if self.database_manager.database_type.value == "postgresql":
                schema = WhisperEngineSchema.get_postgresql_schema()
            else:
                schema = WhisperEngineSchema.get_core_schema()

            await self.database_manager.setup_schema(schema)

            # Initialize system settings
            await self._initialize_system_settings()

            # Create backup if enabled
            backup_config = self.db_config.get_backup_configuration()
            if backup_config["enabled"] and backup_config["backup_on_startup"]:
                await self._create_startup_backup()

            self.initialized = True
            return True

        except (ImportError, ConnectionError, OSError) as e:
            print(f"Failed to initialize database: {e}")
            return False

    async def cleanup(self) -> None:
        """Cleanup database resources"""
        if self.database_manager:
            await self.database_manager.cleanup()
            self.initialized = False

    async def _initialize_system_settings(self) -> None:
        """Initialize system settings table with default values"""
        if not self.database_manager:
            return

        default_settings = {
            "schema_version": "1.0.0",
            "deployment_mode": os.environ.get("DEPLOYMENT_MODE", "development"),
            "scale_tier": "docker",
            "last_startup": "CURRENT_TIMESTAMP",
            "performance_mode": "balanced",
        }

        for key, value in default_settings.items():
            # Insert or ignore if already exists
            await self.database_manager.query(
                "INSERT OR IGNORE INTO system_settings (key, value) VALUES (:key, :value)",
                {"key": key, "value": value},
            )

    async def _create_startup_backup(self) -> None:
        """Create a backup on startup"""
        if not self.database_manager:
            return

        try:
            backup_config = self.db_config.get_backup_configuration()
            backup_dir = Path(backup_config["backup_directory"])
            backup_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"whisperengine_startup_{timestamp}.db"
            backup_path = backup_dir / backup_filename

            await self.database_manager.backup(str(backup_path))

        except (OSError, ConnectionError) as e:
            print(f"Backup failed: {e}")  # Log backup failure but don't crash initialization

    def get_database_manager(self) -> DatabaseManager:
        """Get the database manager instance"""
        if not self.database_manager:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.database_manager

    def get_detailed_info(self) -> dict:
        """Get detailed database configuration information using environment variables"""
        return {
            "database_type": "postgresql" if os.environ.get("USE_POSTGRESQL", "false").lower() == "true" else "in_memory",
            "connection_pool_size": int(os.environ.get("DB_POOL_SIZE", "10")),
            "backup_enabled": os.environ.get("BACKUP_ENABLED", "false").lower() == "true",
            "cache_type": "redis" if os.environ.get("USE_REDIS_CACHE", "false").lower() == "true" else "in_memory",
            "deployment_mode": os.environ.get("DEPLOYMENT_MODE", "development"),
            "scale_tier": "docker",  # Simple Docker deployment
        }


# Factory function for easy integration
def create_database_integration() -> DatabaseIntegrationManager:
    """Factory function to create database integration"""
    return DatabaseIntegrationManager()


# Example usage
async def main():
    """Example usage of database integration"""
    # Create integration
    db_integration = create_database_integration()

    try:
        # Initialize database
        if await db_integration.initialize():

            # Get database manager for operations
            db_manager = db_integration.get_database_manager()

            # Example operation: insert a user
            await db_manager.query(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (:user_id, :username)",
                {"user_id": "test_user_123", "username": "TestUser"},
            )

            # Query users
            await db_manager.query("SELECT * FROM users LIMIT 5")

            # Show configuration info
            print("Database configuration:", db_integration.get_detailed_info())

        else:
            pass

    finally:
        await db_integration.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
