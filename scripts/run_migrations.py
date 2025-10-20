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
    """Apply a SQL migration file in a transaction for atomicity"""
    try:
        sql_content = file_path.read_text()
        
        # 00_init.sql sets search_path to empty string which breaks our schema access
        # Force search_path to public for all migrations
        if 'SET search_path = TO' in sql_content or "SET search_path = ''" in sql_content:
            print(f"🔧 Adjusting search_path in SQL dump to use 'public' schema")
            sql_content = sql_content.replace("SET search_path = TO 'public';", "SET search_path = public;")
            sql_content = sql_content.replace("SET search_path = '';", "SET search_path = public;")
        
        # Execute in transaction for atomicity
        # If migration fails partway, entire transaction rolls back
        print(f"📝 Applying migration: {migration_name} (in transaction)")
        async with conn.transaction():
            await conn.execute(sql_content)
            print(f"✅ Migration {migration_name} applied successfully!")
        return True
    except Exception as e:
        print(f"❌ Error applying migration {migration_name}: {e}")
        print("🔄 Transaction rolled back - database is unchanged")
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
        
        # Check if this is a database with existing schema but no Alembic tracking
        # This could be:
        # 1. TRUE legacy v1.0.6 database (minimal tables, old schema)
        # 2. Database from 00_init.sql dump (many tables but potentially outdated)
        if table_count > 0 and not alembic_version_exists:
            print("🔍 Detected database with existing schema but no Alembic tracking...")
            
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            env = os.environ.copy()
            env['DATABASE_URL'] = database_url
            
            # Check if this database has emoji columns (added in recent migrations)
            emoji_columns_exist = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'characters' 
                AND column_name LIKE 'emoji%'
            """)
            
            if table_count < 30:
                print(f"ℹ️  Small database ({table_count} tables) - likely true legacy v1.0.6")
                print("🏷️  Stamping with baseline revision to apply incremental updates...")
                # v1.0.6 had ~20-25 tables, should stamp as baseline and run migrations
                stamp_revision = "20251011_baseline_v106"
            elif emoji_columns_exist > 0:
                print(f"ℹ️  Large database ({table_count} tables) with recent changes (emoji columns found)")
                print("🏷️  Stamping as fully up-to-date...")
                stamp_revision = "head"
            else:
                print(f"ℹ️  Large database ({table_count} tables) but missing recent changes (no emoji columns)")
                print("ℹ️  This appears to be from an older 00_init.sql dump")
                print("🏷️  Stamping with baseline revision and will apply incremental updates...")
                # This matches the revision that 00_init.sql was generated from
                stamp_revision = "20251011_baseline_v106"
            
            try:
                # Stamp the database with appropriate revision
                result = subprocess.run([
                    'alembic', 'stamp', stamp_revision
                ], cwd='/app', env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Database stamped with Alembic revision: {stamp_revision}")
                    
                    # Now run any migrations that need to be applied
                    print("🔄 Running any pending migrations...")
                    upgrade_result = subprocess.run([
                        'alembic', 'upgrade', 'head'
                    ], cwd='/app', env=env, capture_output=True, text=True)
                    
                    if upgrade_result.returncode == 0:
                        print("✅ All Alembic migrations completed successfully!")
                        print("🎉 Database is now fully up-to-date!")
                        return 0
                    else:
                        print(f"❌ Migration upgrade failed: {upgrade_result.stderr}")
                        print(f"STDOUT: {upgrade_result.stdout}")
                        return 1
                else:
                    print(f"⚠️  Failed to stamp database: {result.stderr}")
                    print(f"⚠️  You may need to manually run: docker exec <container> alembic stamp {stamp_revision}")
                    print("⚠️  Continuing anyway to allow container startup...")
                    return 0  # Don't fail - allow container to start
                    
            except Exception as e:
                print(f"⚠️  Exception while processing database: {e}")
                print("⚠️  Continuing anyway to allow container startup...")
                return 0  # Don't fail - allow container to start
        
        if alembic_version_exists:
            print("🔍 Detected Alembic-managed database - running Alembic migrations...")
            
            # Check migration mode - DEV allows graceful handling of missing migrations
            migration_mode = os.getenv('MIGRATION_MODE', 'production').lower()
            is_dev_mode = migration_mode == 'dev'
            
            if is_dev_mode:
                print("ℹ️  DEV MODE: Graceful migration handling enabled")
                print("   (Docker image may not have latest migration files yet)")
            else:
                print("ℹ️  PRODUCTION MODE: Using Alembic incremental migrations")
            
            # Run Alembic migrations
            # Set the database URL for Alembic
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            env = os.environ.copy()
            env['DATABASE_URL'] = database_url
            
            try:
                # Show current migration status BEFORE upgrade
                print("\n" + "=" * 80)
                print("📊 CURRENT MIGRATION STATUS (BEFORE):")
                print("=" * 80)
                status_before = subprocess.run([
                    'alembic', 'current', '--verbose'
                ], cwd='/app', env=env, capture_output=True, text=True)
                print(status_before.stdout if status_before.returncode == 0 else status_before.stderr)
                
                # Show what migrations are available
                print("\n" + "=" * 80)
                print("📋 AVAILABLE MIGRATIONS:")
                print("=" * 80)
                history_result = subprocess.run([
                    'alembic', 'history', '--verbose'
                ], cwd='/app', env=env, capture_output=True, text=True)
                print(history_result.stdout if history_result.returncode == 0 else history_result.stderr)
                
                # Show heads
                print("\n" + "=" * 80)
                print("🎯 MIGRATION HEADS:")
                print("=" * 80)
                heads_result = subprocess.run([
                    'alembic', 'heads'
                ], cwd='/app', env=env, capture_output=True, text=True)
                print(heads_result.stdout if heads_result.returncode == 0 else heads_result.stderr)
                
                # Run Alembic upgrade to head (no --verbose flag for upgrade command)
                print("\n" + "=" * 80)
                print("⚡ RUNNING ALEMBIC UPGRADE TO HEAD:")
                print("=" * 80)
                result = subprocess.run([
                    'alembic', 'upgrade', 'head'
                ], cwd='/app', env=env, capture_output=True, text=True)
                
                print("STDOUT:")
                print(result.stdout)
                if result.stderr:
                    print("\nSTDERR:")
                    print(result.stderr)
                
                if result.returncode == 0:
                    # Show final migration status AFTER upgrade
                    print("\n" + "=" * 80)
                    print("📊 FINAL MIGRATION STATUS (AFTER):")
                    print("=" * 80)
                    status_after = subprocess.run([
                        'alembic', 'current', '--verbose'
                    ], cwd='/app', env=env, capture_output=True, text=True)
                    print(status_after.stdout if status_after.returncode == 0 else status_after.stderr)
                    
                    print("\n" + "=" * 80)
                    print("✅ ALEMBIC MIGRATIONS COMPLETED SUCCESSFULLY!")
                    print("=" * 80)
                    print("🎉 All migrations complete!")
                    return 0
                else:
                    print("\n" + "=" * 80)
                    print(f"❌ ALEMBIC MIGRATION FAILED! (Exit code: {result.returncode})")
                    print("=" * 80)
                    
                    # In DEV mode, allow graceful failure if migration files are missing
                    if is_dev_mode and "Can't locate revision" in result.stderr:
                        print("⚠️  DEV MODE: Migration file not found in Docker image")
                        print("   This is expected when developing new migrations")
                        print("   The database schema is ahead of the Docker image")
                        print("   ✅ Allowing container to start - bots will still work")
                        return 0  # Don't fail - allow container to start
                    
                    return 1
                    
            except Exception as e:
                print(f"❌ Failed to run Alembic migrations: {e}")
                
                # In DEV mode, be more forgiving of errors
                if is_dev_mode:
                    print("⚠️  DEV MODE: Exception during migration")
                    print("   ✅ Allowing container to start anyway")
                    return 0
                
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
                        
                        # Stamp database with Alembic revision matching the init SQL dump
                        # This allows future Alembic migrations to run incrementally
                        print("🏷️  Stamping database with Alembic revision...")
                        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
                        env = os.environ.copy()
                        env['DATABASE_URL'] = database_url
                        
                        # 00_init.sql was generated on Oct 11, 2025 from baseline schema
                        # It corresponds to the 20251011_baseline_v106 revision
                        INIT_SQL_ALEMBIC_REVISION = "20251011_baseline_v106"
                        
                        try:
                            result = subprocess.run([
                                'alembic', 'stamp', INIT_SQL_ALEMBIC_REVISION
                            ], cwd='/app', env=env, capture_output=True, text=True)
                            
                            if result.returncode == 0:
                                print(f"✅ Database stamped with Alembic revision: {INIT_SQL_ALEMBIC_REVISION}")
                                print("ℹ️  Future Alembic migrations will now apply incrementally from this point")
                                
                                # CRITICAL: Run Alembic migrations NOW (not on second restart!)
                                # This applies all migrations AFTER baseline (e.g., c64001afbd46 personality backfill)
                                print("\n🔄 Running Alembic migrations from baseline to head...")
                                upgrade_result = subprocess.run([
                                    'alembic', 'upgrade', 'head'
                                ], cwd='/app', env=env, capture_output=True, text=True)
                                
                                if upgrade_result.returncode == 0:
                                    print("✅ All Alembic migrations completed successfully!")
                                    if upgrade_result.stdout:
                                        print(f"📋 Migration output:\n{upgrade_result.stdout}")
                                else:
                                    print(f"⚠️  Alembic migrations failed: {upgrade_result.stderr}")
                                    print(f"⚠️  STDOUT: {upgrade_result.stdout}")
                                    print("⚠️  Fresh install may be missing recent schema updates")
                            else:
                                print(f"⚠️  Failed to stamp Alembic revision: {result.stderr}")
                                print("⚠️  Continuing anyway - you may need to manually run: alembic stamp 20251011_baseline_v106")
                        except Exception as e:
                            print(f"⚠️  Exception while stamping Alembic: {e}")
                            print("⚠️  Continuing anyway - you may need to manually run: alembic stamp 20251011_baseline_v106")
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
