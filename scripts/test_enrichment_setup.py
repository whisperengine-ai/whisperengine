"""
Test script for enrichment worker setup validation

Validates:
1. PostgreSQL connection and schema
2. Qdrant connection and collections
3. Configuration validity
4. LLM client initialization (without making API calls)
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.enrichment.config import config
from qdrant_client import QdrantClient
import asyncpg


async def test_configuration():
    """Test configuration validation"""
    print("🔧 Testing configuration...")
    try:
        config.validate()
        print("✅ Configuration valid")
        print(f"   - Qdrant: {config.QDRANT_HOST}:{config.QDRANT_PORT}")
        print(f"   - PostgreSQL: {config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}")
        print(f"   - LLM Model: {config.LLM_MODEL}")
        print(f"   - Enrichment Interval: {config.ENRICHMENT_INTERVAL_SECONDS}s")
        return True
    except Exception as e:
        print(f"❌ Configuration invalid: {e}")
        return False


async def test_postgres_connection():
    """Test PostgreSQL connection"""
    print("\n🗄️  Testing PostgreSQL connection...")
    try:
        pool = await asyncpg.create_pool(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            database=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            min_size=1,
            max_size=2
        )
        
        async with pool.acquire() as conn:
            # Test basic query
            version = await conn.fetchval("SELECT version()")
            print(f"✅ PostgreSQL connected: {version[:50]}...")
            
            # Check if conversation_summaries table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'conversation_summaries'
                )
            """)
            
            if table_exists:
                count = await conn.fetchval("SELECT COUNT(*) FROM conversation_summaries")
                print(f"✅ conversation_summaries table exists ({count} rows)")
            else:
                print("⚠️  conversation_summaries table not found - run migration:")
                print("   alembic upgrade head")
        
        await pool.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


async def test_qdrant_connection():
    """Test Qdrant connection"""
    print("\n🔍 Testing Qdrant connection...")
    try:
        client = QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT
        )
        
        # Get collections
        collections = client.get_collections()
        print(f"✅ Qdrant connected - {len(collections.collections)} collections found")
        
        # List WhisperEngine collections
        bot_collections = [
            col.name for col in collections.collections
            if col.name.startswith('whisperengine_memory_') or 
               col.name.startswith('chat_memories_')
        ]
        
        if bot_collections:
            print(f"   Bot collections ({len(bot_collections)}):")
            for col in bot_collections[:5]:  # Show first 5
                print(f"   - {col}")
            if len(bot_collections) > 5:
                print(f"   ... and {len(bot_collections) - 5} more")
        else:
            print("⚠️  No bot collections found - start some bots first")
        
        return True
        
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        return False


async def test_llm_client():
    """Test LLM client initialization (without API call)"""
    print("\n🤖 Testing LLM client initialization...")
    try:
        from src.llm.llm_protocol import create_llm_client
        
        llm_client = create_llm_client(llm_client_type="openrouter")
        print("✅ LLM client initialized")
        print(f"   - Model: {config.LLM_MODEL}")
        print("   - Note: Not making API call (would cost $)")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM client initialization failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("WhisperEngine Enrichment Worker - Setup Validation")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(await test_configuration())
    results.append(await test_postgres_connection())
    results.append(await test_qdrant_connection())
    results.append(await test_llm_client())
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        print("\n🚀 Ready to start enrichment worker:")
        print("   docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d enrichment-worker")
        return 0
    else:
        print(f"❌ Some tests failed ({passed}/{total} passed)")
        print("\n📝 Fix the issues above before starting enrichment worker")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
