"""
Database Integration for WhisperEngine
Connects the database abstraction layer to the adaptive configuration system.
"""

import os
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.abstract_database import create_database_manager, DatabaseManager


class WhisperEngineDatabaseConfig:
    """Database configuration for WhisperEngine based on adaptive configuration"""

    def __init__(self, adaptive_config_manager: AdaptiveConfigManager):
        self.config_manager = adaptive_config_manager
        self.deployment_info = adaptive_config_manager.get_deployment_info()
        self.db_config = adaptive_config_manager.config.database

    def get_database_connection_string(self) -> str:
        """Generate database connection string based on deployment mode"""

        # Check for environment override
        db_type_override = os.environ.get("WHISPERENGINE_DATABASE_TYPE")
        if db_type_override == "sqlite":
            db_path = Path.home() / ".whisperengine" / "database.db"
            return f"sqlite:///{db_path}"

        if self.db_config.primary_type == "sqlite":
            # Desktop SQLite configuration
            db_path = Path.home() / ".whisperengine" / "database.db"
            return f"sqlite:///{db_path}"

        elif self.db_config.primary_type == "postgresql":
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
            raise ValueError(f"Unsupported database type: {self.db_config.primary_type}")

    def get_database_manager(self) -> DatabaseManager:
        """Create and configure database manager"""
        connection_string = self.get_database_connection_string()

        # Check for database type override
        db_type_override = os.environ.get(
            "WHISPERENGINE_DATABASE_TYPE", self.db_config.primary_type
        )

        return create_database_manager(
            database_type=db_type_override,
            connection_string=connection_string,
            pool_size=self.db_config.connection_pool_size,
            timeout=30,
            backup_enabled=self.db_config.backup_enabled,
        )

    def get_backup_configuration(self) -> Dict[str, Any]:
        """Get backup configuration for the database"""
        base_backup_dir = Path.home() / ".whisperengine" / "backups"

        return {
            "enabled": self.db_config.backup_enabled,
            "backup_directory": str(base_backup_dir),
            "automatic_backups": True,
            "backup_interval_hours": 24,
            "max_backups_to_keep": 7,
            "backup_on_startup": True,
            "compress_backups": True,
        }


class WhisperEngineSchema:
    """WhisperEngine database schema definitions"""

    @staticmethod
    def get_core_schema() -> Dict[str, str]:
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
        }

    @staticmethod
    def get_postgresql_schema() -> Dict[str, str]:
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
        """

        return schema


class DatabaseIntegrationManager:
    """Main integration manager for WhisperEngine database operations"""

    def __init__(self, adaptive_config_manager: Optional[AdaptiveConfigManager] = None):
        if adaptive_config_manager is None:
            adaptive_config_manager = AdaptiveConfigManager()

        self.config_manager = adaptive_config_manager
        self.db_config = WhisperEngineDatabaseConfig(adaptive_config_manager)
        self.database_manager: Optional[DatabaseManager] = None
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

        except Exception as e:
            print(f"Database initialization failed: {e}")
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
            "deployment_mode": self.config_manager.config.deployment_mode,
            "scale_tier": str(self.config_manager.config.scale_tier),
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
            print(f"Startup backup created: {backup_path}")

        except Exception as e:
            print(f"Startup backup failed: {e}")

    def get_database_manager(self) -> DatabaseManager:
        """Get the database manager instance"""
        if not self.database_manager:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.database_manager

    def get_deployment_info(self) -> Dict[str, Any]:
        """Get database deployment information"""
        return {
            "database_type": self.db_config.db_config.primary_type,
            "connection_pool_size": self.db_config.db_config.connection_pool_size,
            "backup_enabled": self.db_config.db_config.backup_enabled,
            "cache_type": self.db_config.db_config.cache_type,
            "deployment_mode": self.config_manager.config.deployment_mode,
            "scale_tier": self.config_manager.config.scale_tier,
            "initialized": self.initialized,
        }


# Factory function for easy integration
def create_database_integration(
    adaptive_config_manager: Optional[AdaptiveConfigManager] = None,
) -> DatabaseIntegrationManager:
    """Factory function to create database integration"""
    return DatabaseIntegrationManager(adaptive_config_manager)


# Example usage
async def main():
    """Example usage of database integration"""
    # Create integration
    db_integration = create_database_integration()

    try:
        # Initialize database
        if await db_integration.initialize():
            print("Database initialized successfully")

            # Get database manager for operations
            db_manager = db_integration.get_database_manager()

            # Example operation: insert a user
            result = await db_manager.query(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (:user_id, :username)",
                {"user_id": "test_user_123", "username": "TestUser"},
            )
            print(f"User insert result: {result.success}")

            # Query users
            result = await db_manager.query("SELECT * FROM users LIMIT 5")
            print(f"Users in database: {len(result.rows)}")

            # Show deployment info
            deployment_info = db_integration.get_deployment_info()
            print(f"Database deployment: {deployment_info}")

        else:
            print("Database initialization failed")

    finally:
        await db_integration.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
