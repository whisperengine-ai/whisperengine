#!/usr/bin/env python3
"""
Database migration runner for WhisperEngine
Runs SQL migrations from sql/ directory using asyncpg
"""
import asyncio
import asyncpg
import os
import sys
import subprocess
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
    # Some pg_dump exports set search_path to an empty string which breaks
    # unqualified table references (e.g. INSERT INTO characters). Replace
    # that pattern with an explicit public search_path so subsequent
    # statements find the expected tables.
    if "pg_catalog.set_config('search_path', '', false)" in sql or "SET search_path = ''" in sql:
        print("🔧 Adjusting search_path in SQL dump to use 'public' schema")
        sql = sql.replace("pg_catalog.set_config('search_path', '', false)", "pg_catalog.set_config('search_path', 'public', false)")
        sql = sql.replace("SET search_path = ''", "SET search_path = 'public'")
    
    try:
        # Execute the entire SQL file
        # Note: asyncpg supports multi-statement execution; the SQL dump
        # contains CREATE FUNCTION... $$ bodies and other complex constructs.
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
        # Check if schema_migrations table exists first
        schema_migrations_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'schema_migrations'
            );
        """)
        
        # Check if database has existing tables (besides schema_migrations)
        table_count = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name != 'schema_migrations'
        """)
        
        # Check if this is an Alembic-managed database
        alembic_version_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            );
        """)
        
        if alembic_version_exists:
            print("🔍 Detected Alembic-managed database - running Alembic migrations...")
            print("ℹ️  PRODUCTION MODE: Using Alembic incremental migrations")
            
            # Run Alembic migrations
            # Set the database URL for Alembic
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            env = os.environ.copy()
            env['DATABASE_URL'] = database_url
            
            try:
                # Run Alembic upgrade to head
                result = subprocess.run([
                    'alembic', 'upgrade', 'head'
                ], cwd='/app', env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Alembic migrations completed successfully!")
                    print("🎉 All migrations complete!")
                    return 0
                else:
                    print(f"❌ Alembic migration failed!")
                    print(f"STDOUT: {result.stdout}")
                    print(f"STDERR: {result.stderr}")
                    return 1
                    
            except Exception as e:
                print(f"❌ Failed to run Alembic migrations: {e}")
                return 1
        
        # QUICKSTART MODE: Apply comprehensive 00_init.sql ONLY, skip incremental migrations
        # Single authoritative database initialization file with all 73 tables
        print("ℹ️  QUICKSTART MODE: New database detected - using comprehensive schema")
        init_schema_path = Path("/app/sql/00_init.sql")
        if init_schema_path.exists():
            migration_name = "00_init.sql"
            
            # Check if migration already applied (only if schema_migrations exists)
            migration_applied = False
            if schema_migrations_exists:
                migration_applied = await is_migration_applied(conn, migration_name)
            
            if not migration_applied:
                if table_count == 0:
                    print("🗄️  Database is empty - applying comprehensive init schema (73 tables)...")
                    if await apply_sql_file(conn, init_schema_path, migration_name):
                        # After successful init, record the migration
                        await record_migration(conn, migration_name)
                        print("✅ Comprehensive schema applied - 73 tables + AI Assistant character ready!")
                    else:
                        print("❌ Init schema failed - exiting")
                        return 1
                else:
                    print(f"ℹ️  Database has {table_count} tables - skipping init schema (already initialized)")
                    # Create migrations tracking table if it doesn't exist (for existing DBs)
                    await create_migrations_table(conn)
                    print("ℹ️  Recording init schema as applied to prevent future attempts...")
                    await record_migration(conn, migration_name)
            else:
                print("✅ Comprehensive init schema (00_init.sql) already applied, skipping...")
        
        # Apply seed data (safe to run multiple times due to ON CONFLICT DO NOTHING)
        seed_data_path = Path("/app/sql/01_seed_data.sql")
        if seed_data_path.exists():
            seed_migration_name = "01_seed_data.sql"
            
            # Check if seed data already applied (only if schema_migrations exists)
            seed_applied = False
            if schema_migrations_exists or table_count > 0:
                seed_applied = await is_migration_applied(conn, seed_migration_name)
            
            if not seed_applied:
                print("🌱 Applying seed data (default AI Assistant character)...")
                if await apply_sql_file(conn, seed_data_path, seed_migration_name):
                    await record_migration(conn, seed_migration_name)
                    print("✅ Seed data applied successfully!")
                else:
                    print("⚠️  Seed data failed - continuing anyway (non-critical)")
            else:
                print("✅ Seed data already applied, skipping...")
        
        # QUICKSTART MODE: Skip incremental migrations - we use comprehensive 00_init.sql
        print("ℹ️  QUICKSTART MODE: Schema (00_init.sql) + Seed Data (01_seed_data.sql)")
        print("ℹ️  Skipping incremental migrations (sql/migrations/) - single init file deployment")
        
        print("🎉 All migrations complete!")
        return 0
        
    finally:
        await conn.close()

if __name__ == "__main__":
    sys.exit(asyncio.run(run_migrations()))
