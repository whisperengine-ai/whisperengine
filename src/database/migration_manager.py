"""
Database Migration System for WhisperEngine

This module provides version-aware database migration capabilities for
schema evolution, data preservation, and rollback functionality.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class MigrationScript:
    """Individual database migration script"""
    
    version: str
    name: str
    description: str
    created_at: datetime
    script_type: str  # "schema", "data", "index", "cleanup"
    up_sql: str  # SQL to apply migration
    down_sql: str  # SQL to rollback migration
    dependencies: List[str]  # List of migration versions this depends on
    checksum: str  # Hash of the migration content for integrity
    
    def calculate_checksum(self) -> str:
        """Calculate checksum of migration content"""
        content = f"{self.up_sql}|{self.down_sql}|{self.description}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class MigrationRecord:
    """Record of applied migration"""
    
    version: str
    name: str
    applied_at: datetime
    checksum: str
    execution_time_ms: int
    rollback_available: bool


class DatabaseMigrationManager:
    """Manages database schema migrations and versioning"""
    
    def __init__(self, db_path: str, migrations_dir: str = "migrations"):
        self.db_path = db_path
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(exist_ok=True)
        
        # Ensure migration tracking table exists
        self._init_migration_table()
        
        # Load available migrations
        self.available_migrations = self._load_migrations()
        
    def _init_migration_table(self):
        """Initialize migration tracking table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT NOT NULL,
                    execution_time_ms INTEGER DEFAULT 0,
                    rollback_available BOOLEAN DEFAULT TRUE,
                    migration_data TEXT DEFAULT '{}'
                )
            """)
            
            # Also create a version info table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS database_version (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    current_version TEXT NOT NULL,
                    last_migration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    migration_count INTEGER DEFAULT 0,
                    database_type TEXT DEFAULT 'sqlite',
                    schema_hash TEXT DEFAULT ''
                )
            """)
            
            # Insert initial version if not exists - PostgreSQL compatible
            conn.execute("""
                INSERT INTO database_version (id, current_version, migration_count)
                VALUES (1, '0.0.0', 0)
                ON CONFLICT (id) DO NOTHING
            """)
            
            conn.commit()
    
    def _load_migrations(self) -> Dict[str, MigrationScript]:
        """Load all available migration scripts"""
        migrations = {}
        
        # Load from migration files
        for migration_file in self.migrations_dir.glob("*.json"):
            try:
                with open(migration_file, 'r') as f:
                    migration_data = json.load(f)
                
                migration = MigrationScript(
                    version=migration_data['version'],
                    name=migration_data['name'],
                    description=migration_data['description'],
                    created_at=datetime.fromisoformat(migration_data['created_at']),
                    script_type=migration_data['script_type'],
                    up_sql=migration_data['up_sql'],
                    down_sql=migration_data['down_sql'],
                    dependencies=migration_data.get('dependencies', []),
                    checksum=migration_data['checksum']
                )
                
                # Verify checksum
                if migration.calculate_checksum() != migration.checksum:
                    logger.warning(f"Migration {migration.version} checksum mismatch")
                
                migrations[migration.version] = migration
                
            except Exception as e:
                logger.error(f"Failed to load migration {migration_file}: {e}")
        
        return migrations
    
    def create_migration(self, 
                        version: str,
                        name: str,
                        description: str,
                        up_sql: str,
                        down_sql: str,
                        script_type: str = "schema",
                        dependencies: List[str] = None) -> MigrationScript:
        """Create a new migration script"""
        
        migration = MigrationScript(
            version=version,
            name=name,
            description=description,
            created_at=datetime.now(),
            script_type=script_type,
            up_sql=up_sql,
            down_sql=down_sql,
            dependencies=dependencies or [],
            checksum=""
        )
        
        # Calculate checksum
        migration.checksum = migration.calculate_checksum()
        
        # Save to file
        migration_file = self.migrations_dir / f"{version}_{name.replace(' ', '_')}.json"
        with open(migration_file, 'w') as f:
            migration_dict = asdict(migration)
            migration_dict['created_at'] = migration.created_at.isoformat()
            json.dump(migration_dict, f, indent=2)
        
        # Add to available migrations
        self.available_migrations[version] = migration
        
        logger.info(f"Created migration {version}: {name}")
        return migration
    
    def get_current_version(self) -> str:
        """Get current database schema version"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT current_version FROM database_version WHERE id = 1")
            result = cursor.fetchone()
            return result[0] if result else "0.0.0"
    
    def get_applied_migrations(self) -> List[MigrationRecord]:
        """Get list of applied migrations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT version, name, applied_at, checksum, execution_time_ms, rollback_available
                FROM schema_migrations
                ORDER BY applied_at
            """)
            
            migrations = []
            for row in cursor.fetchall():
                migrations.append(MigrationRecord(
                    version=row[0],
                    name=row[1],
                    applied_at=datetime.fromisoformat(row[2]),
                    checksum=row[3],
                    execution_time_ms=row[4],
                    rollback_available=bool(row[5])
                ))
            
            return migrations
    
    def get_pending_migrations(self) -> List[MigrationScript]:
        """Get list of migrations that haven't been applied"""
        applied_versions = {m.version for m in self.get_applied_migrations()}
        
        pending = []
        for version, migration in self.available_migrations.items():
            if version not in applied_versions:
                pending.append(migration)
        
        # Sort by version
        pending.sort(key=lambda m: m.version)
        return pending
    
    def _check_dependencies(self, migration: MigrationScript, applied_versions: set) -> bool:
        """Check if migration dependencies are satisfied"""
        for dep_version in migration.dependencies:
            if dep_version not in applied_versions:
                logger.error(f"Migration {migration.version} depends on {dep_version} which is not applied")
                return False
        return True
    
    def apply_migration(self, migration: MigrationScript) -> bool:
        """Apply a single migration"""
        applied_versions = {m.version for m in self.get_applied_migrations()}
        
        # Check if already applied
        if migration.version in applied_versions:
            logger.info(f"Migration {migration.version} already applied")
            return True
        
        # Check dependencies
        if not self._check_dependencies(migration, applied_versions):
            return False
        
        logger.info(f"Applying migration {migration.version}: {migration.name}")
        
        start_time = datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Begin transaction
                conn.execute("BEGIN TRANSACTION")
                
                try:
                    # Execute migration SQL
                    for statement in migration.up_sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            conn.execute(statement)
                    
                    # Record migration
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    conn.execute("""
                        INSERT INTO schema_migrations 
                        (version, name, checksum, execution_time_ms, rollback_available)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        migration.version,
                        migration.name,
                        migration.checksum,
                        execution_time,
                        bool(migration.down_sql.strip())
                    ))
                    
                    # Update database version
                    conn.execute("""
                        UPDATE database_version 
                        SET current_version = ?, 
                            last_migration_date = CURRENT_TIMESTAMP,
                            migration_count = migration_count + 1
                        WHERE id = 1
                    """, (migration.version,))
                    
                    # Commit transaction
                    conn.execute("COMMIT")
                    
                    logger.info(f"Successfully applied migration {migration.version} in {execution_time}ms")
                    return True
                    
                except Exception as e:
                    # Rollback transaction
                    conn.execute("ROLLBACK")
                    logger.error(f"Failed to apply migration {migration.version}: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Database connection error during migration {migration.version}: {e}")
            return False
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration"""
        migration = self.available_migrations.get(version)
        if not migration:
            logger.error(f"Migration {version} not found")
            return False
        
        if not migration.down_sql.strip():
            logger.error(f"Migration {version} has no rollback SQL")
            return False
        
        logger.info(f"Rolling back migration {version}: {migration.name}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Begin transaction
                conn.execute("BEGIN TRANSACTION")
                
                try:
                    # Execute rollback SQL
                    for statement in migration.down_sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            conn.execute(statement)
                    
                    # Remove migration record
                    conn.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
                    
                    # Update database version (find previous version)
                    remaining_migrations = conn.execute("""
                        SELECT version FROM schema_migrations 
                        ORDER BY applied_at DESC LIMIT 1
                    """).fetchone()
                    
                    new_version = remaining_migrations[0] if remaining_migrations else "0.0.0"
                    
                    conn.execute("""
                        UPDATE database_version 
                        SET current_version = ?,
                            last_migration_date = CURRENT_TIMESTAMP,
                            migration_count = migration_count - 1
                        WHERE id = 1
                    """, (new_version,))
                    
                    # Commit transaction
                    conn.execute("COMMIT")
                    
                    logger.info(f"Successfully rolled back migration {version}")
                    return True
                    
                except Exception as e:
                    # Rollback transaction
                    conn.execute("ROLLBACK")
                    logger.error(f"Failed to rollback migration {version}: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Database connection error during rollback of {version}: {e}")
            return False
    
    def migrate_to_version(self, target_version: str) -> bool:
        """Migrate database to specific version"""
        current_version = self.get_current_version()
        
        if current_version == target_version:
            logger.info(f"Database already at version {target_version}")
            return True
        
        pending_migrations = self.get_pending_migrations()
        
        # Find migrations up to target version
        migrations_to_apply = []
        for migration in pending_migrations:
            migrations_to_apply.append(migration)
            if migration.version == target_version:
                break
        
        if not migrations_to_apply or migrations_to_apply[-1].version != target_version:
            logger.error(f"Cannot reach target version {target_version}")
            return False
        
        # Apply migrations in order
        for migration in migrations_to_apply:
            if not self.apply_migration(migration):
                logger.error(f"Migration chain failed at {migration.version}")
                return False
        
        logger.info(f"Successfully migrated to version {target_version}")
        return True
    
    def migrate_latest(self) -> bool:
        """Migrate database to latest available version"""
        pending_migrations = self.get_pending_migrations()
        
        if not pending_migrations:
            logger.info("Database is already at latest version")
            return True
        
        # Apply all pending migrations
        for migration in pending_migrations:
            if not self.apply_migration(migration):
                logger.error(f"Migration chain failed at {migration.version}")
                return False
        
        latest_version = pending_migrations[-1].version
        logger.info(f"Successfully migrated to latest version {latest_version}")
        return True
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get comprehensive migration status"""
        current_version = self.get_current_version()
        applied_migrations = self.get_applied_migrations()
        pending_migrations = self.get_pending_migrations()
        
        return {
            "current_version": current_version,
            "applied_count": len(applied_migrations),
            "pending_count": len(pending_migrations),
            "latest_available": max(self.available_migrations.keys()) if self.available_migrations else "0.0.0",
            "applied_migrations": [m.version for m in applied_migrations],
            "pending_migrations": [m.version for m in pending_migrations],
            "migration_history": [
                {
                    "version": m.version,
                    "name": m.name,
                    "applied_at": m.applied_at.isoformat(),
                    "execution_time_ms": m.execution_time_ms
                }
                for m in applied_migrations
            ]
        }


# Pre-built migration templates
class MigrationTemplates:
    """Common migration templates"""
    
    @staticmethod
    def add_column(table_name: str, column_name: str, column_type: str, default_value: str = None) -> tuple:
        """Template for adding a column"""
        up_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_value:
            up_sql += f" DEFAULT {default_value}"
        
        # Note: SQLite doesn't support DROP COLUMN in older versions
        down_sql = f"-- Cannot automatically drop column {column_name} from {table_name} in SQLite"
        
        return up_sql, down_sql
    
    @staticmethod
    def create_table(table_name: str, columns: Dict[str, str]) -> tuple:
        """Template for creating a table"""
        column_defs = [f"{name} {type_def}" for name, type_def in columns.items()]
        up_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
        down_sql = f"DROP TABLE IF EXISTS {table_name}"
        
        return up_sql, down_sql
    
    @staticmethod
    def create_index(index_name: str, table_name: str, columns: List[str], unique: bool = False) -> tuple:
        """Template for creating an index"""
        unique_keyword = "UNIQUE " if unique else ""
        up_sql = f"CREATE {unique_keyword}INDEX {index_name} ON {table_name} ({', '.join(columns)})"
        down_sql = f"DROP INDEX IF EXISTS {index_name}"
        
        return up_sql, down_sql
    
    @staticmethod
    def insert_data(table_name: str, data: List[Dict[str, Any]]) -> tuple:
        """Template for inserting data"""
        if not data:
            return "", ""
        
        columns = list(data[0].keys())
        placeholders = ", ".join(["?" for _ in columns])
        
        up_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # For rollback, we need to identify the specific rows
        down_sql = f"-- Manual cleanup required for data insertion into {table_name}"
        
        return up_sql, down_sql