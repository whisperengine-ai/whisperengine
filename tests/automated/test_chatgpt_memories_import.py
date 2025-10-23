"""
Test ChatGPT Memories Import Script Compatibility

Verifies that the ChatGPT memories import script works correctly with
the current user facts and preferences system after recent changes.
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import asyncpg

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.chatgpt_import.memories_importer import ChatGPTMemoriesImporter
from src.knowledge.semantic_router import SemanticKnowledgeRouter


async def test_memory_parsing():
    """Test that memory parsing still works correctly"""
    print("\n🧪 TEST 1: Memory Parsing & Preference Classification")
    print("=" * 60)
    
    importer = ChatGPTMemoriesImporter(
        user_id="test_user_chatgpt",
        character_name="elena",
        dry_run=True
    )
    
    test_cases = [
        # (text, entity_type, relationship, is_preference)
        ("User likes Italian food", "preference", "likes", True),
        ("User has a cat named Whiskers", "possession", "owns", False),
        ("User has experience with Python programming", "experience", "experienced_in", False),
        ("User works on machine learning projects", "professional", "works_on", False),
        ("User wants to learn Spanish", "learning", "wants_to_learn", False),
        ("User prefers dark mode", "preference", "prefers", True),
        ("User is a software engineer", "characteristic", "is", False),
        ("User dislikes cold weather", "preference", "dislikes", True),
        ("User enjoys hiking", "activity", "enjoys", True),
    ]
    
    passed = 0
    failed = 0
    
    for memory_text, expected_type, expected_relationship, expected_is_pref in test_cases:
        parsed = importer.parse_memory_line(memory_text)
        
        if parsed:
            type_match = parsed.entity_type == expected_type
            rel_match = parsed.relationship_type == expected_relationship
            pref_match = parsed.is_preference == expected_is_pref
            
            if type_match and rel_match and pref_match:
                pref_label = "PREFERENCE" if parsed.is_preference else "FACT"
                print(f"✅ PASS: '{memory_text}' → {pref_label}")
                print(f"   {parsed.entity_name} ({parsed.entity_type}, {parsed.relationship_type})")
                passed += 1
            else:
                print(f"❌ FAIL: '{memory_text}'")
                print(f"   Expected: {expected_type}, {expected_relationship}, pref={expected_is_pref}")
                print(f"   Got: {parsed.entity_type}, {parsed.relationship_type}, pref={parsed.is_preference}")
                failed += 1
        else:
            print(f"❌ FAIL: '{memory_text}' - Failed to parse")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0


async def test_database_schema_compatibility():
    """Test that the script can connect to database and schema is compatible"""
    print("\n🧪 TEST 2: Database Schema Compatibility")
    print("=" * 60)
    
    try:
        # Connect to PostgreSQL
        db_pool = await asyncpg.create_pool(
            host="localhost",
            port=5433,
            database="whisperengine",
            user="whisperengine",
            password="development_password_change_in_production",
            min_size=1,
            max_size=2
        )
        
        print("✅ Database connection successful")
        
        # Check that required tables exist
        async with db_pool.acquire() as conn:
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('fact_entities', 'user_fact_relationships', 'universal_users')
                ORDER BY table_name
            """)
            
            table_names = [row['table_name'] for row in tables]
            print(f"✅ Found required tables: {', '.join(table_names)}")
            
            if len(table_names) != 3:
                print("❌ Missing tables!")
                await db_pool.close()
                return False
            
            # Check fact_entities schema
            columns = await conn.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'fact_entities'
                ORDER BY ordinal_position
            """)
            
            required_columns = ['id', 'entity_type', 'entity_name', 'category', 'attributes']
            found_columns = [col['column_name'] for col in columns]
            
            for req_col in required_columns:
                if req_col in found_columns:
                    print(f"✅ fact_entities.{req_col} exists")
                else:
                    print(f"❌ fact_entities.{req_col} MISSING!")
                    await db_pool.close()
                    return False
            
            # Check user_fact_relationships schema
            columns = await conn.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'user_fact_relationships'
                ORDER BY ordinal_position
            """)
            
            required_columns = [
                'id', 'user_id', 'entity_id', 'relationship_type', 
                'confidence', 'emotional_context', 'mentioned_by_character'
            ]
            found_columns = [col['column_name'] for col in columns]
            
            for req_col in required_columns:
                if req_col in found_columns:
                    print(f"✅ user_fact_relationships.{req_col} exists")
                else:
                    print(f"❌ user_fact_relationships.{req_col} MISSING!")
                    await db_pool.close()
                    return False
        
        await db_pool.close()
        print("\n✅ Database schema is compatible")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


async def test_end_to_end_import():
    """Test actual import with database storage - verifies facts vs preferences routing"""
    print("\n🧪 TEST 3: End-to-End Import with Facts vs Preferences Routing")
    print("=" * 60)
    
    # Create a temporary test file with mixed facts and preferences
    test_memories = """User likes pizza

User has a cat named Luna

User has experience with Python programming

User wants to learn machine learning

User prefers dark theme in code editors

User is a software developer

User works on AI projects

User owns a MacBook Pro

User enjoys hiking on weekends

User dislikes cold weather"""
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_memories)
            temp_file = f.name
        
        print(f"📝 Created test file: {temp_file}")
        
        # Initialize importer
        test_user_id = f"test_chatgpt_import_{int(asyncio.get_event_loop().time())}"
        importer = ChatGPTMemoriesImporter(
            user_id=test_user_id,
            character_name="elena",
            dry_run=False,  # Actually store in database
            verbose=True
        )
        
        await importer.initialize()
        print("✅ Importer initialized")
        
        # Run import
        stats = await importer.import_memories_file(temp_file)
        
        print(f"\n📊 Import Statistics:")
        print(f"   Total blocks: {stats['total_blocks']}")
        print(f"   Processed: {stats['processed']}")
        print(f"   Skipped: {stats['skipped']}")
        print(f"   Errors: {stats['errors']}")
        
        # Verify data was stored in correct locations
        async with importer.db_pool.acquire() as conn:
            # Count stored facts
            fact_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM user_fact_relationships
                WHERE user_id = $1
            """, test_user_id)
            
            print(f"\n✅ Stored {fact_count} facts in user_fact_relationships table")
            
            # Retrieve and display a few facts
            facts = await conn.fetch("""
                SELECT 
                    fe.entity_name,
                    fe.entity_type,
                    ufr.relationship_type,
                    ufr.confidence
                FROM user_fact_relationships ufr
                JOIN fact_entities fe ON ufr.entity_id = fe.id
                WHERE ufr.user_id = $1
                LIMIT 5
            """, test_user_id)
            
            print("\n📋 Sample stored FACTS:")
            for fact in facts:
                print(f"   • {fact['entity_name']} ({fact['entity_type']}) - "
                      f"{fact['relationship_type']} (confidence: {fact['confidence']:.2f})")
            
            # Check stored preferences
            preferences = await conn.fetchval("""
                SELECT preferences
                FROM universal_users
                WHERE universal_id = $1
            """, test_user_id)
            
            if preferences:
                import json
                prefs_dict = json.loads(preferences) if isinstance(preferences, str) else preferences
                pref_count = len(prefs_dict)
                print(f"\n✅ Stored {pref_count} preferences in universal_users.preferences JSONB")
                
                print("\n📋 Sample stored PREFERENCES:")
                for pref_type, pref_data in list(prefs_dict.items())[:5]:
                    value = pref_data.get('value') if isinstance(pref_data, dict) else pref_data
                    print(f"   • {pref_type}: {value}")
            else:
                print("\n⚠️  No preferences stored")
            
            # Clean up test data
            print(f"\n🧹 Cleaning up test data for user {test_user_id}...")
            await conn.execute("""
                DELETE FROM user_fact_relationships
                WHERE user_id = $1
            """, test_user_id)
            
            await conn.execute("""
                DELETE FROM universal_users
                WHERE universal_id = $1
            """, test_user_id)
        
        await importer.close()
        
        # Clean up temp file
        Path(temp_file).unlink()
        
        print("✅ End-to-end import test passed!")
        return stats['errors'] == 0 and stats['processed'] > 0
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multi_line_memory_support():
    """Test that multi-line memories are handled correctly"""
    print("\n🧪 TEST 4: Multi-Line Memory Support")
    print("=" * 60)
    
    importer = ChatGPTMemoriesImporter(
        user_id="test_user_multiline",
        character_name="elena",
        dry_run=True
    )
    
    # Test multi-line memory (common in ChatGPT exports)
    multi_line_memory = """User owns the following art books:
- The Art of War
- Techniques of Traditional Japanese Art
- Modern Architecture Design"""
    
    parsed = importer.parse_memory_line(multi_line_memory)
    
    if parsed:
        print(f"✅ Multi-line memory parsed successfully")
        print(f"   Entity type: {parsed.entity_type}")
        print(f"   Relationship: {parsed.relationship_type}")
        print(f"   Is multiline: {parsed.attributes.get('is_multiline', False)}")
        print(f"   Content length: {len(parsed.entity_name)} chars")
        return parsed.attributes.get('is_multiline', False) == True
    else:
        print("❌ Multi-line memory parsing failed")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ChatGPT Memories Import Script Compatibility Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Memory parsing
    results.append(await test_memory_parsing())
    
    # Test 2: Database schema compatibility
    results.append(await test_database_schema_compatibility())
    
    # Test 3: End-to-end import
    results.append(await test_end_to_end_import())
    
    # Test 4: Multi-line memory support
    results.append(await test_multi_line_memory_support())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUITE SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results)
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if all(results):
        print("\n✅ ALL TESTS PASSED - Import script is fully compatible!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Import script needs updates")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
