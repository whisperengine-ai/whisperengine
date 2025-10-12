#!/usr/bin/env python3
"""
Export Character CDL Data to YAML (Simple Version)
Exports character data from database focusing on core CDL sections
"""

import os
import asyncio
import asyncpg
import yaml
import json
from pathlib import Path
from datetime import datetime

# Database settings
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5433')
os.environ.setdefault('POSTGRES_USER', 'whisperengine')
os.environ.setdefault('POSTGRES_PASSWORD', 'whisperengine_password')
os.environ.setdefault('POSTGRES_DB', 'whisperengine')


async def export_character(character_name: str, output_dir: str = "exports"):
    """Export character to YAML with defensive error handling"""
    
    print(f"🚀 Exporting Character: {character_name}")
    print("=" * 70)
    
    try:
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    try:
        # Get main character record
        char_row = await conn.fetchrow("""
            SELECT * FROM characters
            WHERE LOWER(normalized_name) = LOWER($1) OR LOWER(name) = LOWER($1)
        """, character_name)
        
        if not char_row:
            print(f"❌ Character '{character_name}' not found")
            await conn.close()
            return False
        
        char_id = char_row['id']
        char_name = char_row['name']
        print(f"✅ Found: {char_name} (ID: {char_id})\n")
        
        # Build export structure
        export = {
            'cdl_version': '1.0',
            'format': 'yaml',
            'export_date': datetime.now().isoformat(),
            'description': f'CDL Export - {char_name}',
            'character': {
                'metadata': {},
                'identity': {},
                'personality': {},
                'background': {},
                'relationships': {},
                'communication': {},
                'instructions': {}
            }
        }
        
        char = export['character']
        sections_exported = 0
        
        # 1. Main character identity
        print("👤 Exporting identity...")
        char['identity'] = {
            'name': char_row['name'],
            'normalized_name': char_row['normalized_name'],
            'occupation': char_row['occupation'],
            'description': char_row['description'],
            'archetype': char_row['archetype'],
            'allow_full_roleplay': char_row['allow_full_roleplay']
        }
        print(f"   ✅ Identity exported")
        sections_exported += 1
        
        # 2. Metadata
        print("\n📦 Exporting metadata...")
        try:
            meta_rows = await conn.fetch(
                "SELECT * FROM character_metadata WHERE character_id = $1", char_id)
            if meta_rows:
                meta = meta_rows[0]
                char['metadata'] = {
                    'version': f"{meta['version']}.0.0" if meta.get('version') else "1.0.0",
                    'character_tags': list(meta['character_tags']) if meta.get('character_tags') else [],
                    'author': meta.get('author'),
                    'created_date': str(meta['created_date']) if meta.get('created_date') else None
                }
                # Add notes if it's JSON
                if meta.get('notes'):
                    try:
                        notes_data = json.loads(meta['notes'])
                        char['metadata'].update(notes_data)
                    except:
                        char['metadata']['notes'] = meta['notes']
                print(f"   ✅ Metadata exported")
                sections_exported += 1
        except Exception as e:
            print(f"   ⚠️  Metadata: {e}")
        
        # 3. Personality traits
        print("\n🎭 Exporting personality...")
        try:
            trait_rows = await conn.fetch(
                "SELECT * FROM personality_traits WHERE character_id = $1", char_id)
            if trait_rows:
                big_five_names = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
                big_five = {}
                custom = {}
                for t in trait_rows:
                    if t['trait_name'].lower() in big_five_names:
                        big_five[t['trait_name']] = float(t['trait_value'])
                    else:
                        custom[t['trait_name']] = float(t['trait_value'])
                char['personality'] = {
                    'big_five': big_five,
                    'custom_traits': custom
                }
                print(f"   ✅ {len(big_five)} Big Five + {len(custom)} custom traits")
                sections_exported += 1
        except Exception as e:
            print(f"   ⚠️  Personality: {e}")
        
        # 4. Character values
        print("\n💎 Exporting values...")
        try:
            value_rows = await conn.fetch(
                "SELECT * FROM character_values WHERE character_id = $1", char_id)
            if value_rows:
                values = [v['value_description'] for v in value_rows if v.get('value_description')]
                if values:
                    if 'personality' not in char:
                        char['personality'] = {}
                    char['personality']['values'] = values
                    print(f"   ✅ {len(values)} values exported")
                    sections_exported += 1
        except Exception as e:
            print(f"   ⚠️  Values: {e}")
        
        # 5. Communication style
        print("\n💬 Exporting communication...")
        try:
            comm_rows = await conn.fetch(
                "SELECT * FROM communication_styles WHERE character_id = $1", char_id)
            if comm_rows:
                comm = comm_rows[0]
                char['communication'] = {}
                for key in ['engagement_level', 'formality', 'emotional_expression', 'response_length']:
                    if comm.get(key):
                        char['communication'][key] = comm[key]
                
                # Parse JSON fields
                for field in ['conversation_flow_guidance', 'ai_identity_handling']:
                    if comm.get(field):
                        try:
                            data = json.loads(comm[field]) if isinstance(comm[field], str) else comm[field]
                            char['communication'][field] = data
                        except:
                            char['communication'][field] = comm[field]
                
                print(f"   ✅ Communication exported")
                sections_exported += 1
        except Exception as e:
            print(f"   ⚠️  Communication: {e}")
        
        # 6. Memories
        print("\n🧠 Exporting memories...")
        try:
            mem_rows = await conn.fetch(
                "SELECT * FROM character_memories WHERE character_id = $1 ORDER BY importance_level DESC", char_id)
            if mem_rows:
                memories = []
                for m in mem_rows:
                    memories.append({
                        'event': m['title'],
                        'description': m['description'],
                        'emotional_impact': m.get('emotional_impact'),
                        'time_period': m.get('time_period'),
                        'importance': m.get('importance_level')
                    })
                char['background']['key_memories'] = memories
                print(f"   ✅ {len(memories)} memories exported")
                sections_exported += 1
        except Exception as e:
            print(f"   ⚠️  Memories: {e}")
        
        # 7. Relationships
        print("\n💝 Exporting relationships...")
        try:
            rel_rows = await conn.fetch(
                "SELECT * FROM character_relationships WHERE character_id = $1", char_id)
            if rel_rows:
                relationships = {}
                for r in rel_rows:
                    key = r['related_entity'].lower().replace(' ', '_').replace('(', '').replace(')', '')
                    relationships[key] = {
                        'type': r['relationship_type'],
                        'entity': r['related_entity'],
                        'strength': r.get('relationship_strength'),
                        'status': r.get('status')
                    }
                    # Parse description if JSON
                    if r.get('description'):
                        try:
                            desc_data = json.loads(r['description'])
                            relationships[key].update(desc_data)
                        except:
                            relationships[key]['description'] = r['description']
                
                char['relationships'] = relationships
                print(f"   ✅ {len(relationships)} relationships exported")
                sections_exported += 1
        except Exception as e:
            print(f"   ⚠️  Relationships: {e}")
        
        # 8. Instructions/Core Directives
        print("\n📋 Exporting instructions...")
        try:
            inst_rows = await conn.fetch(
                "SELECT * FROM character_instructions WHERE character_id = $1 ORDER BY priority DESC", char_id)
            if inst_rows:
                directives = {}
                for i in inst_rows:
                    key = i.get('context') or f"directive_{i['instruction_type']}"
                    directives[key] = i['instruction_text']
                char['core_directives'] = directives
                print(f"   ✅ {len(directives)} instructions exported")
                sections_exported += 1
        except Exception as e:
            print(f"   ⚠️  Instructions: {e}")
        
        await conn.close()
        
        # Write YAML file
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{char_row['normalized_name']}_export_{timestamp}.yaml"
        filepath = output_path / filename
        
        print(f"\n💾 Writing: {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(export, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
        
        print("\n" + "=" * 70)
        print("🎉 Export Complete!")
        print("=" * 70)
        print(f"📄 File: {filepath}")
        print(f"📦 Character: {char_name}")
        print(f"🎭 Archetype: {char_row['archetype']}")
        print(f"📊 Sections exported: {sections_exported}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        await conn.close()
        return False


async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("🎭 WhisperEngine CDL Character Export to YAML")
        print("=" * 70)
        print("\nUsage: python export_character_simple.py <character_name> [output_dir]")
        print("\nExample: python export_character_simple.py aetheris")
        return
    
    character_name = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "exports"
    
    success = await export_character(character_name, output_dir)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
