#!/usr/bin/env python3
"""
Check CDL Completeness for All Characters
Validates that all characters have complete CDL data in the database
"""

import os
import asyncio
import asyncpg
from datetime import datetime

# Database settings
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5433')
os.environ.setdefault('POSTGRES_USER', 'whisperengine')
os.environ.setdefault('POSTGRES_PASSWORD', 'whisperengine_password')
os.environ.setdefault('POSTGRES_DB', 'whisperengine')


async def check_all_characters():
    """Check CDL completeness for all active characters"""
    
    print("🔍 WhisperEngine CDL Completeness Check")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        print("✅ Connected to database\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Get all active characters
    characters = await conn.fetch("""
        SELECT id, name, normalized_name, occupation, archetype, allow_full_roleplay
        FROM characters
        WHERE is_active = true
        ORDER BY name
    """)
    
    print(f"📊 Found {len(characters)} active characters\n")
    print("=" * 80)
    
    # CDL tables to check
    cdl_tables = [
        'character_metadata',
        'personality_traits',
        'communication_styles',
        'character_memories',
        'character_relationships',
        'character_instructions',
        'character_values',
        'character_essence',
        'character_voice_traits',
        'character_background',
        'character_abilities',
        'character_expertise_domains',
        'character_speech_patterns',
        'character_emotional_triggers',
        'character_behavioral_triggers'
    ]
    
    # Critical sections (minimum required)
    critical_sections = [
        'personality_traits',
        'communication_styles',
        'character_metadata'
    ]
    
    # Important sections (highly recommended)
    important_sections = [
        'character_memories',
        'character_relationships',
        'character_instructions'
    ]
    
    all_results = []
    
    for char in characters:
        char_id = char['id']
        char_name = char['name']
        
        print(f"\n{'='*80}")
        print(f"📋 Character: {char_name} (ID: {char_id})")
        print(f"   Normalized: {char['normalized_name']}")
        print(f"   Occupation: {char['occupation']}")
        print(f"   Archetype: {char['archetype']}")
        print(f"   Full Roleplay: {char['allow_full_roleplay']}")
        print(f"{'='*80}")
        
        counts = {}
        critical_missing = []
        important_missing = []
        
        for table in cdl_tables:
            try:
                count = await conn.fetchval(
                    f"SELECT COUNT(*) FROM {table} WHERE character_id = $1",
                    char_id
                )
                counts[table] = count
                
                # Check critical sections
                if table in critical_sections and count == 0:
                    critical_missing.append(table)
                
                # Check important sections
                if table in important_sections and count == 0:
                    important_missing.append(table)
                
                # Status indicator
                if count > 0:
                    print(f"   ✅ {table}: {count} rows")
                else:
                    print(f"   ❌ {table}: 0 rows")
                    
            except Exception as e:
                print(f"   ⚠️  {table}: Error - {e}")
                counts[table] = -1
        
        # Calculate completeness
        total_tables = len(cdl_tables)
        populated_tables = sum(1 for c in counts.values() if c > 0)
        completeness_pct = (populated_tables / total_tables) * 100
        
        print(f"\n📊 Completeness: {populated_tables}/{total_tables} tables ({completeness_pct:.1f}%)")
        
        # Overall status
        if critical_missing:
            status = "❌ INCOMPLETE (Missing Critical Sections)"
            print(f"\n{status}")
            print(f"   Critical missing: {', '.join(critical_missing)}")
        elif important_missing:
            status = "⚠️  PARTIAL (Missing Important Sections)"
            print(f"\n{status}")
            print(f"   Important missing: {', '.join(important_missing)}")
        else:
            status = "✅ COMPLETE"
            print(f"\n{status}")
        
        all_results.append({
            'id': char_id,
            'name': char_name,
            'normalized_name': char['normalized_name'],
            'archetype': char['archetype'],
            'completeness_pct': completeness_pct,
            'populated_tables': populated_tables,
            'total_tables': total_tables,
            'status': status,
            'critical_missing': critical_missing,
            'important_missing': important_missing,
            'counts': counts
        })
    
    await conn.close()
    
    # Summary report
    print("\n" + "=" * 80)
    print("📊 SUMMARY REPORT")
    print("=" * 80)
    
    complete_chars = [r for r in all_results if not r['critical_missing'] and not r['important_missing']]
    partial_chars = [r for r in all_results if not r['critical_missing'] and r['important_missing']]
    incomplete_chars = [r for r in all_results if r['critical_missing']]
    
    print(f"\n✅ Complete Characters: {len(complete_chars)}")
    for r in complete_chars:
        print(f"   • {r['name']} ({r['completeness_pct']:.1f}% complete)")
    
    print(f"\n⚠️  Partial Characters: {len(partial_chars)}")
    for r in partial_chars:
        print(f"   • {r['name']} ({r['completeness_pct']:.1f}% complete)")
        print(f"     Missing: {', '.join(r['important_missing'])}")
    
    print(f"\n❌ Incomplete Characters: {len(incomplete_chars)}")
    for r in incomplete_chars:
        print(f"   • {r['name']} ({r['completeness_pct']:.1f}% complete)")
        print(f"     Missing critical: {', '.join(r['critical_missing'])}")
        if r['important_missing']:
            print(f"     Missing important: {', '.join(r['important_missing'])}")
    
    # Average completeness
    avg_completeness = sum(r['completeness_pct'] for r in all_results) / len(all_results)
    print(f"\n📈 Average Completeness: {avg_completeness:.1f}%")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    if incomplete_chars:
        print("\n🚨 Priority: Fix incomplete characters")
        for r in incomplete_chars:
            print(f"\n   {r['name']}:")
            print(f"   - Run: python import_characters_to_clean_schema.py")
            if r['name'].lower() == 'aetheris':
                print(f"   - Or: python import_aetheris_supplement.py")
    
    if partial_chars:
        print("\n⚠️  Consider: Enhance partial characters")
        for r in partial_chars:
            print(f"\n   {r['name']}:")
            print(f"   - Add: {', '.join(r['important_missing'])}")
            print(f"   - Create custom supplement script if needed")
    
    if complete_chars:
        print("\n✅ Maintenance: Keep complete characters updated")
        for r in complete_chars:
            print(f"   • {r['name']}: Regular backups recommended")
            print(f"     python export_character_simple.py {r['normalized_name']}")
    
    print("\n" + "=" * 80)
    print("🎉 Completeness Check Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(check_all_characters())
