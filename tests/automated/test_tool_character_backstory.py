#!/usr/bin/env python3
"""
Test Tool 3: query_character_backstory implementation.

This script validates:
1. PostgreSQL connection pool usage
2. Character ID lookup
3. CDL table queries (character_identity, character_attributes, character_communication)
4. Proper data structure formatting

Usage:
    source .venv/bin/activate && \
    export POSTGRES_HOST="localhost" && \
    export POSTGRES_PORT="5433" && \
    export DISCORD_BOT_NAME=elena && \
    python tests/automated/test_tool_character_backstory.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_query_character_backstory():
    """Test Tool 3: query_character_backstory with PostgreSQL pool."""
    print("\n" + "="*80)
    print("TEST: query_character_backstory (Tool 3)")
    print("="*80)
    
    from src.knowledge.semantic_router import create_semantic_knowledge_router
    import asyncpg
    
    # Connect to PostgreSQL with credentials
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_PORT", "5433")
    postgres_db = os.getenv("POSTGRES_DB", "whisperengine")
    postgres_user = os.getenv("POSTGRES_USER", "whisperengine")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "whisperengine_password")
    
    postgres_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    print(f"\nConnecting to PostgreSQL: postgresql://{postgres_user}:***@{postgres_host}:{postgres_port}/{postgres_db}")
    
    try:
        pool = await asyncpg.create_pool(postgres_url, min_size=1, max_size=2)
        print("✅ PostgreSQL connected")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    
    # Create SemanticKnowledgeRouter
    knowledge_router = create_semantic_knowledge_router(
        postgres_pool=pool,
        qdrant_client=None,
        influx_client=None
    )
    
    # Test 1: Query Elena's backstory (uses DISCORD_BOT_NAME from environment)
    print("\n" + "-"*80)
    print("Test 1: Query character backstory (uses DISCORD_BOT_NAME=elena)")
    print("-"*80)
    
    try:
        result = await knowledge_router._tool_query_character_backstory(
            query="Tell me about your background and personality",
            source="cdl_database"
        )
        
        print(f"✅ Query executed successfully")
        print(f"Character found: {result['found']}")
        
        if result['found']:
            print(f"\nIdentity:")
            print(f"  Full name: {result['identity'].get('full_name', 'N/A')}")
            print(f"  Nickname: {result['identity'].get('nickname', 'N/A')}")
            print(f"  Location: {result['identity'].get('location', 'N/A')}")
            
            print(f"\nAttributes: {len(result['attributes'])} total")
            for attr in result['attributes'][:3]:
                print(f"  - {attr['category']}: {attr['description'][:60]}...")
            
            print(f"\nCommunication patterns: {len(result['communication'])} total")
            for pattern in result['communication'][:3]:
                print(f"  - {pattern['pattern_type']}/{pattern['pattern_name']}: {pattern['pattern_value'][:50] if pattern['pattern_value'] else 'N/A'}...")
        
        test1_passed = result['found']
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        test1_passed = False
    
    # Test 2: Set invalid DISCORD_BOT_NAME to test not-found handling
    print("\n" + "-"*80)
    print("Test 2: Query with invalid bot_name (should handle gracefully)")
    print("-"*80)
    
    # Temporarily set invalid DISCORD_BOT_NAME
    original_bot_name = os.getenv("DISCORD_BOT_NAME")
    os.environ["DISCORD_BOT_NAME"] = "nonexistent_character"
    
    try:
        result = await knowledge_router._tool_query_character_backstory(
            query="Tell me about yourself",
            source="cdl_database"
        )
        
        print(f"✅ Query executed successfully")
        print(f"Character found: {result['found']}")
        
        test2_passed = not result['found']  # Should be False
        print(f"{'✅' if test2_passed else '❌'} Correctly returned not found")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        test2_passed = False
    finally:
        # Restore original DISCORD_BOT_NAME
        if original_bot_name:
            os.environ["DISCORD_BOT_NAME"] = original_bot_name
    
    await pool.close()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Test 1 (Query Elena backstory): {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Test 2 (Non-existent character): {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print("="*80)
    
    return test1_passed and test2_passed


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("TOOL 3: query_character_backstory VALIDATION")
    print("="*80)
    
    try:
        success = await test_query_character_backstory()
        print(f"\n{'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
        return success
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
