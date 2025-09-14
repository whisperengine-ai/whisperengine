#!/usr/bin/env python3
"""
Simple Desktop to Docker Migration Test

This script tests the data migration path from SQLite (desktop) to PostgreSQL (Docker)
by creating test data and verifying schema compatibility.
"""

import asyncio
import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.database.database_integration import WhisperEngineSchema

def create_test_sqlite_data():
    """Create test data in SQLite database"""
    db_path = Path.home() / ".whisperengine" / "test_migration.db"
    db_path.parent.mkdir(exist_ok=True)
    
    # Clean up existing database
    if db_path.exists():
        db_path.unlink()
        print(f"🧹 Cleaned up existing test database")
    
    print(f"📝 Creating test data in {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create schema
    schema = WhisperEngineSchema.get_core_schema()
    for table_name, table_sql in schema.items():
        cursor.execute(table_sql)
    
    # Insert test data
    test_data = [
        # Users
        ("INSERT INTO users (user_id, username, display_name, preferences) VALUES (?, ?, ?, ?)",
         ["test_user_1", "testuser1", "Test User One", '{"theme": "dark"}']),
        ("INSERT INTO users (user_id, username, display_name, preferences) VALUES (?, ?, ?, ?)",
         ["test_user_2", "testuser2", "Test User Two", '{"theme": "light"}']),
        
        # Conversations
        ("INSERT INTO conversations (user_id, channel_id, message_content, bot_response, ai_model_used) VALUES (?, ?, ?, ?, ?)",
         ["test_user_1", "general", "Hello bot!", "Hello! How can I help you?", "local-model"]),
        ("INSERT INTO conversations (user_id, channel_id, message_content, bot_response, ai_model_used) VALUES (?, ?, ?, ?, ?)",
         ["test_user_2", "general", "What's the weather?", "I don't have access to weather data.", "local-model"]),
        
        # Memory entries
        ("INSERT INTO memory_entries (user_id, memory_type, content, importance_score, tags) VALUES (?, ?, ?, ?, ?)",
         ["test_user_1", "preference", "User prefers dark theme", 0.8, '["ui", "preference"]']),
        ("INSERT INTO memory_entries (user_id, memory_type, content, importance_score, tags) VALUES (?, ?, ?, ?, ?)",
         ["test_user_2", "fact", "User asked about weather", 0.6, '["weather", "question"]']),
        
        # Facts
        ("INSERT INTO facts (user_id, fact_type, subject, content, confidence_score, global_fact) VALUES (?, ?, ?, ?, ?, ?)",
         ["test_user_1", "personal", "name", "User's name is Test User One", 0.9, False]),
        ("INSERT INTO facts (fact_type, subject, content, confidence_score, global_fact) VALUES (?, ?, ?, ?, ?)",
         ["general", "ai", "WhisperEngine is an AI Discord bot", 1.0, True]),
        
        # Emotions
        ("INSERT INTO emotions (user_id, detected_emotion, confidence, context) VALUES (?, ?, ?, ?)",
         ["test_user_1", "curious", 0.7, "Asking about bot capabilities"]),
        
        # Relationships
        ("INSERT INTO relationships (user_id, relationship_type, strength, notes) VALUES (?, ?, ?, ?)",
         ["test_user_1", "friendly", 0.8, "Polite and curious user"]),
        
        # System settings
        ("INSERT INTO system_settings (key, value, description) VALUES (?, ?, ?)",
         ["last_backup", datetime.now().isoformat(), "Last database backup time"]),
        ("INSERT INTO system_settings (key, value, description) VALUES (?, ?, ?)",
         ["schema_version", "1.0", "Current database schema version"]),
        
        # Performance metrics
        ("INSERT INTO performance_metrics (metric_name, metric_value, tags) VALUES (?, ?, ?)",
         ["response_time_ms", 150.5, '{"endpoint": "chat"}']),
        ("INSERT INTO performance_metrics (metric_name, metric_value, tags) VALUES (?, ?, ?)",
         ["memory_usage_mb", 256.7, '{"component": "llm"}']),
    ]
    
    for sql, params in test_data:
        cursor.execute(sql, params)
    
    conn.commit()
    
    # Verify data
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM conversations")
    conv_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM memory_entries")
    memory_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ Created test data: {user_count} users, {conv_count} conversations, {memory_count} memories")
    return db_path

def analyze_sqlite_data(db_path):
    """Analyze SQLite data structure"""
    print(f"🔍 Analyzing SQLite data structure in {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 Tables found: {', '.join(tables)}")
    
    # Get row counts
    for table in tables:
        if table != 'sqlite_sequence':
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} rows")
    
    # Sample some data
    print(f"\\n📋 Sample data:")
    cursor.execute("SELECT user_id, username, display_name FROM users LIMIT 2")
    users = cursor.fetchall()
    for user in users:
        print(f"  User: {user[1]} ({user[0]}) - {user[2]}")
    
    cursor.execute("SELECT user_id, channel_id, message_content FROM conversations LIMIT 2")
    conversations = cursor.fetchall()
    for conv in conversations:
        print(f"  Message: {conv[2][:50]}... in {conv[1]} by {conv[0]}")
    
    conn.close()

def generate_postgresql_migration_sql(db_path):
    """Generate PostgreSQL migration SQL"""
    print(f"🔄 Generating PostgreSQL migration SQL")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    migration_sql = []
    migration_sql.append("-- WhisperEngine SQLite to PostgreSQL Migration")
    migration_sql.append("-- Generated migration script\n")
    
    # Get PostgreSQL schema
    postgres_schema = WhisperEngineSchema.get_postgresql_schema()
    
    # Add schema creation
    migration_sql.append("-- Create PostgreSQL schema")
    for table_name, table_sql in postgres_schema.items():
        if table_name != 'indexes':
            migration_sql.append(table_sql + ";")
    
    migration_sql.append("\n-- Create indexes")
    migration_sql.append(postgres_schema['indexes'])
    
    migration_sql.append("\n-- Migrate data")
    
    # Generate data migration for each table
    tables = ['users', 'conversations', 'memory_entries', 'facts', 'emotions', 'relationships', 'system_settings', 'performance_metrics']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        if count > 0:
            migration_sql.append(f"\n-- Migrate {table} ({count} rows)")
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # For PostgreSQL users table, we need to handle the id column differently
            if table == 'users':
                postgres_columns = ['user_id', 'username', 'display_name', 'created_at', 'last_seen', 'message_count', 'preferences', 'privacy_settings']
                columns = [col for col in columns if col in postgres_columns]
            
            column_list = ', '.join(columns)
            placeholder_list = ', '.join(['%s'] * len(columns))
            
            cursor.execute(f"SELECT {column_list} FROM {table}")
            rows = cursor.fetchall()
            
            for row in rows:
                # Convert Python values to PostgreSQL format
                formatted_values = []
                for val in row:
                    if val is None:
                        formatted_values.append('NULL')
                    elif isinstance(val, str):
                        escaped_val = val.replace("'", "''")
                        formatted_values.append(f"'{escaped_val}'")
                    else:
                        formatted_values.append(str(val))
                
                values_str = ', '.join(formatted_values)
                migration_sql.append(f"INSERT INTO {table} ({column_list}) VALUES ({values_str});")
    
    conn.close()
    
    # Save migration SQL
    migration_file = Path(__file__).parent / "migration_sqlite_to_postgres.sql"
    with open(migration_file, 'w') as f:
        f.write('\n'.join(migration_sql))
    
    print(f"✅ Migration SQL saved to {migration_file}")
    return migration_file

def test_schema_compatibility():
    """Test schema compatibility between SQLite and PostgreSQL"""
    print(f"🔧 Testing schema compatibility")
    
    sqlite_schema = WhisperEngineSchema.get_core_schema()
    postgres_schema = WhisperEngineSchema.get_postgresql_schema()
    
    # Check table names
    sqlite_tables = set(sqlite_schema.keys())
    postgres_tables = set(postgres_schema.keys()) - {'indexes'}  # Exclude indexes
    
    if sqlite_tables == postgres_tables:
        print(f"✅ Table names match: {', '.join(sorted(sqlite_tables))}")
    else:
        print(f"❌ Table mismatch!")
        print(f"  SQLite only: {sqlite_tables - postgres_tables}")
        print(f"  PostgreSQL only: {postgres_tables - sqlite_tables}")
    
    # Check for key transformations
    for table in sqlite_tables:
        if table in postgres_tables:
            sqlite_sql = sqlite_schema[table]
            postgres_sql = postgres_schema[table]
            
            # Check for expected transformations
            if 'INTEGER PRIMARY KEY AUTOINCREMENT' in sqlite_sql and 'SERIAL PRIMARY KEY' in postgres_sql:
                print(f"✅ {table}: AUTO_INCREMENT -> SERIAL conversion detected")
            elif 'PRIMARY KEY AUTOINCREMENT' in sqlite_sql or 'SERIAL PRIMARY KEY' in postgres_sql:
                print(f"⚠️  {table}: Check primary key conversion")

def main():
    """Main migration test function"""
    print("🚀 Starting Desktop to Docker Migration Test")
    print("=" * 60)
    
    try:
        # 1. Create test SQLite data
        db_path = create_test_sqlite_data()
        
        # 2. Analyze the data
        analyze_sqlite_data(db_path)
        
        # 3. Test schema compatibility
        test_schema_compatibility()
        
        # 4. Generate migration SQL
        migration_file = generate_postgresql_migration_sql(db_path)
        
        print(f"\n" + "=" * 60)
        print(f"🎉 Migration test completed successfully!")
        print(f"\n📋 Next steps for real migration:")
        print(f"  1. Start Docker services: docker compose up -d postgres")
        print(f"  2. Run migration: docker compose exec postgres psql -U bot_user -d whisper_engine -f /path/to/{migration_file.name}")
        print(f"  3. Verify data: docker compose exec postgres psql -U bot_user -d whisper_engine -c 'SELECT COUNT(*) FROM users;'")
        print(f"\n📁 Files created:")
        print(f"  - Test database: {db_path}")
        print(f"  - Migration SQL: {migration_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)