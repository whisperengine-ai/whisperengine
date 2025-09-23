#!/usr/bin/env python3
"""
Test Universal Identity Adapter

Tests the automatic ID conversion and legacy fallback behavior.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Set environment variables
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['POSTGRES_DB'] = 'whisperengine'
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine_password'

async def test_universal_adapter():
    """Test Universal Identity Adapter functionality"""
    try:
        from src.identity.universal_identity_adapter import UniversalIdentityAdapter
        from src.memory.memory_protocol import create_memory_manager
        from src.utils.postgresql_user_db import PostgreSQLUserDB
        
        print("🚀 Testing Universal Identity Adapter...")
        
        # Initialize database
        postgres_db = PostgreSQLUserDB()
        await postgres_db.initialize()
        
        # Create memory manager and wrap with adapter
        base_memory_manager = create_memory_manager('vector')
        adapter = UniversalIdentityAdapter(base_memory_manager, postgres_db.pool)
        
        print("\n1️⃣ Testing ID conversion for existing Discord user...")
        discord_id = '672814231002939413'  # From .env.dream
        universal_id = await adapter._get_universal_id(discord_id)
        print(f"   Discord {discord_id} → Universal {universal_id}")
        
        print("\n2️⃣ Testing Universal ID passthrough...")
        test_universal = await adapter._get_universal_id('weu_ef5c25db3beb41a8')
        print(f"   Universal ID passthrough: weu_ef5c25db3beb41a8 → {test_universal}")
        
        print("\n3️⃣ Testing new Discord user auto-creation...")
        new_discord_id = '999888777666555444'  # Fake Discord ID
        new_universal_id = await adapter._get_universal_id(new_discord_id)
        print(f"   New Discord {new_discord_id} → Universal {new_universal_id}")
        
        print("\n4️⃣ Testing non-Discord ID passthrough...")
        web_id = 'web_testuser_123456'
        passthrough_id = await adapter._get_universal_id(web_id)
        print(f"   Web ID passthrough: {web_id} → {passthrough_id}")
        
        print("\n✅ All tests completed!")
        
        await postgres_db.pool.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_universal_adapter())