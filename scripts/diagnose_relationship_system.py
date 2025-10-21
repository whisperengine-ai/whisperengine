#!/usr/bin/env python3
"""
Diagnose CDL Relationship System
=================================
Tests why character relationships aren't appearing in system prompts.
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def main():
    """Diagnose relationship system for nottaylor character"""
    
    # Database connection
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5433')
    db_name = os.getenv('POSTGRES_DB', 'whisperengine')
    db_user = os.getenv('POSTGRES_USER', 'whisperengine')
    db_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
    
    print("=" * 80)
    print("WhisperEngine Relationship System Diagnosis")
    print("=" * 80)
    print(f"Database: {db_host}:{db_port}/{db_name}")
    print()
    
    # Test character
    character_name = 'nottaylor'
    
    # Connect to database
    pool = await asyncpg.create_pool(
        host=db_host,
        port=int(db_port),
        database=db_name,
        user=db_user,
        password=db_password,
        min_size=1,
        max_size=5
    )
    
    try:
        async with pool.acquire() as conn:
            # 1. Check if character exists
            print(f"1️⃣ Checking if character '{character_name}' exists...")
            char_result = await conn.fetchrow(
                "SELECT id, name, normalized_name FROM characters WHERE normalized_name = $1",
                character_name
            )
            
            if not char_result:
                print(f"❌ Character '{character_name}' not found!")
                return
            
            character_id = char_result['id']
            print(f"✅ Found character: {char_result['name']} (ID: {character_id})")
            print()
            
            # 2. Check relationships in database
            print(f"2️⃣ Checking relationships in database...")
            relationships = await conn.fetch("""
                SELECT 
                    related_entity, 
                    relationship_type, 
                    relationship_strength, 
                    description, 
                    status
                FROM character_relationships 
                WHERE character_id = $1
                ORDER BY relationship_strength DESC
            """, character_id)
            
            if not relationships:
                print("❌ No relationships found in database!")
                return
            
            print(f"✅ Found {len(relationships)} relationships:")
            for rel in relationships:
                print(f"   - {rel['related_entity']}: strength={rel['relationship_strength']}, type={rel['relationship_type']}")
            print()
            
            # 3. Test EnhancedCDLManager.get_relationships()
            print(f"3️⃣ Testing EnhancedCDLManager.get_relationships()...")
            try:
                from src.characters.cdl.enhanced_cdl_manager import get_enhanced_cdl_manager
                
                enhanced_manager = get_enhanced_cdl_manager()
                await enhanced_manager.initialize()
                
                manager_relationships = await enhanced_manager.get_relationships(character_name)
                
                if not manager_relationships:
                    print("❌ EnhancedCDLManager returned NO relationships!")
                else:
                    print(f"✅ EnhancedCDLManager returned {len(manager_relationships)} relationships:")
                    for rel in manager_relationships:
                        print(f"   - {rel.related_entity}: strength={rel.relationship_strength}")
                print()
                
            except Exception as e:
                print(f"❌ Error testing EnhancedCDLManager: {e}")
                import traceback
                traceback.print_exc()
                print()
            
            # 4. Test CDLAIPromptIntegration with relationships
            print(f"4️⃣ Testing CDLAIPromptIntegration.create_character_aware_prompt()...")
            try:
                from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
                
                # Create integration instance
                cdl_integration = CDLAIPromptIntegration(
                    enhanced_manager=enhanced_manager
                )
                
                # Set environment variable for bot name
                os.environ['DISCORD_BOT_NAME'] = character_name
                
                # Create a test prompt
                test_prompt = await cdl_integration.create_character_aware_prompt(
                    character_name=character_name,
                    user_id='test_user_12345',
                    message_content='Hello Silas!'
                )
                
                # Check if relationship section exists
                has_relationship_section = '💕 RELATIONSHIP CONTEXT' in test_prompt
                has_silas = 'Silas' in test_prompt
                has_sitva = 'Sitva' in test_prompt
                
                print(f"   Has '💕 RELATIONSHIP CONTEXT' section: {has_relationship_section}")
                print(f"   Has 'Silas' in prompt: {has_silas}")
                print(f"   Has 'Sitva' in prompt: {has_sitva}")
                print()
                
                if has_relationship_section:
                    # Extract relationship section
                    import re
                    match = re.search(r'💕 RELATIONSHIP CONTEXT:.*?(?=\n\n[^-\s]|\Z)', test_prompt, re.DOTALL)
                    if match:
                        print("   Relationship section content:")
                        print("   " + "-" * 70)
                        for line in match.group(0).split('\n')[:15]:  # First 15 lines
                            print(f"   {line}")
                        print("   " + "-" * 70)
                else:
                    print("   ❌ RELATIONSHIP CONTEXT section NOT FOUND in prompt!")
                    
                    # Try to find where Silas appears
                    if has_silas:
                        print()
                        print("   But 'Silas' DOES appear somewhere. Searching...")
                        for match in re.finditer(r'.{0,100}Silas.{0,100}', test_prompt):
                            snippet = match.group(0).replace('\n', ' ')
                            print(f"   Found: ...{snippet}...")
                
                print()
                
            except Exception as e:
                print(f"❌ Error testing CDLAIPromptIntegration: {e}")
                import traceback
                traceback.print_exc()
                print()
            
            # 5. Check for filtering thresholds
            print(f"5️⃣ Analyzing relationship strength thresholds...")
            print("   Current code filters:")
            print("   - strength >= 8: High-priority (bold)")
            print("   - strength >= 5: Medium-priority (regular)")
            print()
            print("   Nottaylor relationships vs thresholds:")
            for rel in relationships:
                strength = rel['relationship_strength']
                entity = rel['related_entity']
                if strength >= 8:
                    print(f"   ✅ {entity} (strength={strength}) -> Should appear as HIGH-PRIORITY")
                elif strength >= 5:
                    print(f"   ✅ {entity} (strength={strength}) -> Should appear as MEDIUM-PRIORITY")
                else:
                    print(f"   ❌ {entity} (strength={strength}) -> FILTERED OUT (below threshold)")
            print()
            
    finally:
        await pool.close()
    
    print("=" * 80)
    print("Diagnosis complete!")
    print("=" * 80)


if __name__ == '__main__':
    asyncio.run(main())
