#!/usr/bin/env python3
"""
Database migration runner for WhisperEngine
Runs SQL migrations from sql/ directory using asyncpg
"""
import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from datetime import datetime

async def wait_for_database(host, port, user, password, database, max_attempts=60):
    """Wait for PostgreSQL to be ready"""
    print("⏳ Waiting for PostgreSQL...")
    
    for attempt in range(max_attempts):
        try:
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                timeout=2
            )
            await conn.close()
            print("✅ PostgreSQL is ready!")
            return True
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"PostgreSQL is unavailable (attempt {attempt + 1}/{max_attempts}) - sleeping")
                await asyncio.sleep(2)
            else:
                print(f"❌ Failed to connect to PostgreSQL after {max_attempts} attempts: {e}")
                return False
    
    return False

async def create_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist"""
    print("📋 Creating migrations tracking table...")
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_name VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

async def is_migration_applied(conn, migration_name):
    """Check if a migration has already been applied"""
    result = await conn.fetchval(
        "SELECT COUNT(*) FROM schema_migrations WHERE migration_name = $1",
        migration_name
    )
    return result > 0

async def record_migration(conn, migration_name):
    """Record that a migration has been applied"""
    await conn.execute(
        "INSERT INTO schema_migrations (migration_name) VALUES ($1)",
        migration_name
    )

async def apply_sql_file(conn, file_path, migration_name):
    """Apply a SQL file"""
    print(f"📝 Applying migration: {migration_name}")
    
    with open(file_path, 'r') as f:
        sql = f.read()
    
    try:
        # Execute the entire SQL file
        await conn.execute(sql)
        print(f"✅ Migration {migration_name} applied successfully!")
        return True
    except Exception as e:
        print(f"❌ Error applying migration {migration_name}: {e}")
        return False

async def run_migrations():
    """Main migration runner"""
    print("🔧 Starting database migration...")
    
    # Get database connection parameters from environment
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = int(os.getenv('POSTGRES_PORT', '5432'))
    user = os.getenv('POSTGRES_USER', 'whisperengine')
    password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
    database = os.getenv('POSTGRES_DB', 'whisperengine')
    
    # Wait for database to be ready
    if not await wait_for_database(host, port, user, password, database):
        print("❌ Database not available - exiting")
        return 1
    
    # Connect to database
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return 1
    
    try:
        # Create migrations tracking table
        await create_migrations_table(conn)
        
        # Check if database has existing tables (besides schema_migrations)
        table_count = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name != 'schema_migrations'
        """)
        
        # ALPHA MODE: Apply init schema ONLY, skip incremental migrations
        # Since we have no production users, we can just use the base schema
        init_schema_path = Path("/app/sql/init_schema.sql")
        if init_schema_path.exists():
            migration_name = "00_init_schema.sql"
            
            if not await is_migration_applied(conn, migration_name):
                if table_count == 0:
                    print(f"🗄️  Database is empty - applying init schema...")
                    if await apply_sql_file(conn, init_schema_path, migration_name):
                        await record_migration(conn, migration_name)
                    else:
                        print("❌ Init schema failed - exiting")
                        return 1
                else:
                    print(f"ℹ️  Database has {table_count} tables - skipping init schema (already initialized)")
                    print(f"ℹ️  Recording init schema as applied to prevent future attempts...")
                    await record_migration(conn, migration_name)
            else:
                print(f"✅ Init schema already applied, skipping...")
        
        # ALPHA MODE: Skip incremental migrations - we only use init schema
        print("ℹ️  ALPHA MODE: Skipping incremental migrations (sql/migrations/)")
        print("ℹ️  Using base init_schema.sql only - no production users to migrate")
        
        print("🎉 All migrations complete!")
        return 0
        
    finally:
        await conn.close()

if __name__ == "__main__":
    sys.exit(asyncio.run(run_migrations()))
