#!/usr/bin/env python3
"""
Quick script to add a Discord user to the ban database.
Usage: python add_ban.py
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def add_ban_to_database():
    """Add a Discord user ID to the ban database."""
    
    # Discord ID to ban
    discord_id = "ID"
    banned_by = "admin_manual"
    reason = "Manual ban via script"
    
    # Database connection details
    # OVERRIDE: Use localhost:5433 when running locally (outside Docker)
    # The .env file has "postgres:5432" which only works inside Docker containers
    db_host = 'localhost'  # Override .env value which uses Docker container name
    db_port = 5433  # Override .env value which uses internal Docker port
    db_name = os.getenv('POSTGRES_DB', 'whisperengine')
    db_user = os.getenv('POSTGRES_USER', 'whisperengine')
    db_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
    
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        print(f"✅ Connected to PostgreSQL database at {db_host}:{db_port}")
        
        # Check if user is already banned
        existing_ban = await conn.fetchrow(
            """
            SELECT discord_user_id, is_active, ban_reason 
            FROM banned_users 
            WHERE discord_user_id = $1 AND is_active = TRUE
            """,
            discord_id
        )
        
        if existing_ban:
            print(f"⚠️  User {discord_id} is already banned!")
            print(f"   Reason: {existing_ban['ban_reason']}")
            await conn.close()
            return
        
        # Insert ban record
        await conn.execute(
            """
            INSERT INTO banned_users 
            (discord_user_id, banned_by, ban_reason, banned_at, is_active, notes)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP, TRUE, 'Banned via manual script')
            """,
            discord_id,
            banned_by,
            reason
        )
        
        print(f"✅ Successfully banned Discord user: {discord_id}")
        print(f"   Banned by: {banned_by}")
        print(f"   Reason: {reason}")
        
        # Verify the ban was added
        verify = await conn.fetchrow(
            """
            SELECT discord_user_id, banned_by, ban_reason, banned_at, is_active
            FROM banned_users 
            WHERE discord_user_id = $1
            """,
            discord_id
        )
        
        if verify:
            print(f"\n✅ Verification: Ban record created successfully")
            print(f"   Active: {verify['is_active']}")
            print(f"   Banned at: {verify['banned_at']}")
        
        await conn.close()
        print("\n✅ Database connection closed")
        
    except asyncpg.exceptions.UndefinedTableError:
        print("❌ Error: 'banned_users' table does not exist!")
        print("   You may need to run database migrations first.")
    except Exception as e:
        print(f"❌ Error adding ban to database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(add_ban_to_database())
