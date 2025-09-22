#!/usr/bin/env python3
"""
Automatic Database Migration System for WhisperEngine
Runs migrations automatically when container starts up
"""

import os
import sys
import time
import logging
import asyncio
import asyncpg
from pathlib import Path
from typing import List, Dict, Any

# Add the app directory to Python path
sys.path.insert(0, '/app')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[MIGRATION] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        # Database connection parameters from environment
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'whisper_engine'),
            'user': os.getenv('POSTGRES_USER', 'bot_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'securepassword123')
        }
        
        # Migration files directory
        self.migrations_dir = Path('/app/sql/migrations')
        self.init_schema_file = Path('/app/sql/init_schema.sql')
        
    async def wait_for_database(self, max_retries: int = 30, retry_delay: int = 2) -> bool:
        """Wait for PostgreSQL to be available"""
        logger.info(f"🔍 Waiting for PostgreSQL at {self.db_config['host']}:{self.db_config['port']}")
        
        for attempt in range(max_retries):
            try:
                conn = await asyncpg.connect(**self.db_config)
                await conn.close()
                logger.info("✅ PostgreSQL is ready!")
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Attempt {attempt + 1}/{max_retries} failed, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"❌ Failed to connect to PostgreSQL after {max_retries} attempts: {e}")
                    return False
        
        return False
    
    async def database_exists(self) -> bool:
        """Check if the main tables exist"""
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Check if user_profiles table exists
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_profiles'
                );
            """)
            
            await conn.close()
            return bool(result)
            
        except Exception as e:
            logger.error(f"❌ Error checking database existence: {e}")
            return False
    
    async def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        try:
            conn = await asyncpg.connect(**self.db_config)
            
            # Create migrations table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_name VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Get applied migrations
            results = await conn.fetch("SELECT migration_name FROM schema_migrations ORDER BY applied_at;")
            applied = [row['migration_name'] for row in results]
            
            await conn.close()
            return applied
            
        except Exception as e:
            logger.error(f"❌ Error getting applied migrations: {e}")
            return []
    
    async def apply_migration(self, migration_file: Path) -> bool:
        """Apply a single migration file"""
        try:
            logger.info(f"📄 Applying migration: {migration_file.name}")
            
            # Read migration content
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            conn = await asyncpg.connect(**self.db_config)
            
            # Execute migration
            await conn.execute(migration_sql)
            
            # Record migration as applied
            await conn.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES ($1);",
                migration_file.name
            )
            
            await conn.close()
            logger.info(f"✅ Successfully applied: {migration_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply migration {migration_file.name}: {e}")
            return False
    
    async def run_initial_schema(self) -> bool:
        """Run the initial schema if database is empty"""
        if not self.init_schema_file.exists():
            logger.warning("⚠️ No init_schema.sql found, skipping initial schema")
            return True
            
        try:
            logger.info("🏗️ Applying initial database schema...")
            
            with open(self.init_schema_file, 'r') as f:
                schema_sql = f.read()
            
            conn = await asyncpg.connect(**self.db_config)
            await conn.execute(schema_sql)
            await conn.close()
            
            # Mark init schema as applied
            await self.apply_migration_record('00_init_schema.sql')
            
            logger.info("✅ Initial schema applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply initial schema: {e}")
            return False
    
    async def apply_migration_record(self, migration_name: str):
        """Record a migration as applied without executing it"""
        try:
            conn = await asyncpg.connect(**self.db_config)
            await conn.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES ($1) ON CONFLICT DO NOTHING;",
                migration_name
            )
            await conn.close()
        except Exception as e:
            logger.error(f"❌ Failed to record migration {migration_name}: {e}")
    
    async def run_migrations(self) -> bool:
        """Run all pending migrations"""
        try:
            # Wait for database to be available
            if not await self.wait_for_database():
                return False
            
            # Check if database needs initial schema
            if not await self.database_exists():
                logger.info("🔧 Database is empty, applying initial schema...")
                if not await self.run_initial_schema():
                    return False
            else:
                logger.info("📊 Database exists, checking for migrations...")
            
            # Get applied migrations
            applied_migrations = await self.get_applied_migrations()
            logger.info(f"📋 Applied migrations: {applied_migrations}")
            
            # Get all migration files
            migration_files = []
            if self.migrations_dir.exists():
                migration_files = sorted([
                    f for f in self.migrations_dir.glob('*.sql')
                    if f.is_file()
                ])
            
            # Apply pending migrations
            pending_count = 0
            for migration_file in migration_files:
                if migration_file.name not in applied_migrations:
                    if await self.apply_migration(migration_file):
                        pending_count += 1
                    else:
                        return False
            
            if pending_count > 0:
                logger.info(f"✅ Applied {pending_count} new migrations")
            else:
                logger.info("✅ No pending migrations, database is up to date")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration process failed: {e}")
            return False

async def main():
    """Main migration entry point"""
    logger.info("🚀 Starting WhisperEngine database migration system...")
    
    migrator = DatabaseMigrator()
    success = await migrator.run_migrations()
    
    if success:
        logger.info("🎉 Database migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Database migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())