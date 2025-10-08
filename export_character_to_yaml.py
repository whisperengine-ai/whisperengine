#!/usr/bin/env python3
"""
Export Character CDL Data to YAML
Exports complete character data from structured RDBMS schema to YAML format
"""

import os
import sys
import asyncio
import asyncpg
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Database connection settings
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5433')
os.environ.setdefault('POSTGRES_USER', 'whisperengine')
os.environ.setdefault('POSTGRES_PASSWORD', 'whisperengine_password')
os.environ.setdefault('POSTGRES_DB', 'whisperengine')


async def get_database_connection():
    """Get database connection"""
    return await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )


async def export_character_to_yaml(character_name: str, output_dir: str = "exports") -> bool:
    """Export complete character CDL data to YAML format"""
    
    print(f"🚀 Exporting Character: {character_name}")
    print("=" * 70)
    
    # Connect to database
    try:
        conn = await get_database_connection()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    try:
        # 1. Get main character record
        character = await conn.fetchrow("""
            SELECT id, name, normalized_name, occupation, description,
                   archetype, allow_full_roleplay, is_active,
                   created_at, updated_at
            FROM characters
            WHERE LOWER(normalized_name) = LOWER($1) OR LOWER(name) = LOWER($1)
        """, character_name)
        
        if not character:
            print(f"❌ Character '{character_name}' not found in database")
            await conn.close()
            return False
        
        char_id = character['id']
        char_name = character['name']
        print(f"✅ Found character: {char_name} (ID: {char_id})")
        
        # Initialize export data structure
        export_data = {
            'cdl_version': '1.0',
            'format': 'yaml',
            'export_date': datetime.now().isoformat(),
            'description': f'Character Definition Language Export - {char_name}',
            'character': {
                'metadata': {},
                'identity': {},
                'personality': {},
                'background': {},
                'capabilities': {},
                'behavioral_patterns': {},
                'speech_patterns': {},
                'emotional_profile': {},
                'communication': {},
                'relationships': {},
                'instructions': {}
            }
        }
        
        char = export_data['character']
        
        # 2. Export character_metadata
        print("\n📦 Exporting metadata...")
        metadata_rows = await conn.fetch("""
            SELECT version, character_tags, created_date, updated_date, author, notes
            FROM character_metadata WHERE character_id = $1
        """, char_id)
        
        if metadata_rows:
            metadata = metadata_rows[0]
            char['metadata'] = {
                'character_id': f"{character['normalized_name']}-001",
                'name': char_name,
                'version': f"{metadata['version']}.0.0" if metadata['version'] else "1.0.0",
                'created_by': metadata['author'] or 'WhisperEngine AI',
                'created_date': metadata['created_date'].isoformat() if metadata['created_date'] else None,
                'updated_date': metadata['updated_date'].isoformat() if metadata['updated_date'] else None,
                'license': 'open',
                'tags': list(metadata['character_tags']) if metadata['character_tags'] else []
            }
            # Add notes data if present
            if metadata['notes']:
                import json
                try:
                    notes_data = json.loads(metadata['notes'])
                    char['metadata'].update(notes_data)
                except:
                    char['metadata']['notes'] = metadata['notes']
            print(f"   ✅ Exported metadata (version {char['metadata']['version']})")
        
        # 3. Export identity (main character record)
        print("\n👤 Exporting identity...")
        char['identity'] = {
            'name': char_name,
            'normalized_name': character['normalized_name'],
            'occupation': character['occupation'],
            'description': character['description'],
            'archetype': character['archetype'],
            'allow_full_roleplay': character['allow_full_roleplay']
        }
        print(f"   ✅ Exported identity (archetype: {character['archetype']})")
        
        # 4. Export character_essence
        print("\n✨ Exporting essence...")
        essence_rows = await conn.fetch("""
            SELECT essence_type, essence_name, description, manifestation, power_level
            FROM character_essence WHERE character_id = $1
        """, char_id)
        
        if essence_rows:
            essence_data = {}
            for row in essence_rows:
                essence_data[row['essence_name']] = {
                    'type': row['essence_type'],
                    'description': row['description'],
                    'manifestation': row['manifestation'],
                    'power_level': row['power_level']
                }
            char['identity']['essence'] = essence_data
            print(f"   ✅ Exported {len(essence_rows)} essence entries")
        
        # 5. Export character_voice_traits
        print("\n🗣️  Exporting voice traits...")
        voice_rows = await conn.fetch("""
            SELECT trait_type, trait_value, situational_context, examples
            FROM character_voice_traits WHERE character_id = $1
        """, char_id)
        
        if voice_rows:
            voice_data = {}
            for row in voice_rows:
                voice_data[row['trait_type']] = {
                    'value': row['trait_value'],
                    'context': row['situational_context'],
                    'examples': row['examples']
                }
            char['identity']['voice'] = voice_data
            print(f"   ✅ Exported {len(voice_rows)} voice traits")
        
        # 6. Export personality_traits
        print("\n🎭 Exporting personality traits...")
        trait_rows = await conn.fetch("""
            SELECT trait_name, trait_value, intensity, description
            FROM personality_traits WHERE character_id = $1
        """, char_id)
        
        if trait_rows:
            # Try to categorize traits by name patterns
            big_five_names = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            big_five = {}
            custom_traits = {}
            
            for row in trait_rows:
                trait_name = row['trait_name']
                if trait_name.lower() in big_five_names:
                    big_five[trait_name] = row['trait_value']
                else:
                    custom_traits[trait_name] = row['trait_value']
            
            char['personality'] = {
                'big_five': big_five if big_five else {},
                'custom_traits': custom_traits if custom_traits else {}
            }
            print(f"   ✅ Exported {len(big_five)} Big Five + {len(custom_traits)} custom traits")
        
        # 7. Export character_values
        print("\n💎 Exporting character values...")
        value_rows = await conn.fetch("""
            SELECT value_key, value_description, importance_level, category
            FROM character_values WHERE character_id = $1
        """, char_id)
        
        if value_rows:
            values = [row['value_description'] for row in value_rows]
            char['personality']['values'] = values
            print(f"   ✅ Exported {len(values)} character values")
        
        # 8. Export communication_styles
        print("\n💬 Exporting communication style...")
        comm_rows = await conn.fetch("""
            SELECT engagement_level, formality, emotional_expression,
                   response_length, conversation_flow_guidance, ai_identity_handling
            FROM communication_styles WHERE character_id = $1
        """, char_id)
        
        if comm_rows:
            comm = comm_rows[0]
            char['communication'] = {
                'engagement_level': comm['engagement_level'],
                'formality': comm['formality'],
                'emotional_expression': comm['emotional_expression'],
                'response_length': comm['response_length']
            }
            
            # Parse JSON fields
            import json
            if comm['conversation_flow_guidance']:
                try:
                    flow_data = json.loads(comm['conversation_flow_guidance']) if isinstance(comm['conversation_flow_guidance'], str) else comm['conversation_flow_guidance']
                    char['communication']['conversation_flow_guidance'] = flow_data
                except:
                    char['communication']['conversation_flow_guidance'] = comm['conversation_flow_guidance']
            
            if comm['ai_identity_handling']:
                try:
                    ai_data = json.loads(comm['ai_identity_handling']) if isinstance(comm['ai_identity_handling'], str) else comm['ai_identity_handling']
                    char['communication']['ai_identity_handling'] = ai_data
                except:
                    char['communication']['ai_identity_handling'] = comm['ai_identity_handling']
            
            print(f"   ✅ Exported communication style")
        
        # 9. Export character_background
        print("\n📜 Exporting background...")
        background_rows = await conn.fetch("""
            SELECT category, period, title, description, date_range, importance_level
            FROM character_background WHERE character_id = $1
            ORDER BY importance_level DESC
        """, char_id)
        
        if background_rows:
            background_entries = []
            for row in background_rows:
                background_entries.append({
                    'category': row['category'],
                    'period': row['period'],
                    'title': row['title'],
                    'description': row['description'],
                    'date_range': row['date_range'],
                    'importance': row['importance_level']
                })
            char['background']['entries'] = background_entries
            print(f"   ✅ Exported {len(background_entries)} background entries")
        
        # 10. Export character_memories
        print("\n🧠 Exporting memories...")
        memory_rows = await conn.fetch("""
            SELECT memory_type, title, description, emotional_impact,
                   time_period, importance_level, triggers
            FROM character_memories WHERE character_id = $1
            ORDER BY importance_level DESC, emotional_impact DESC
        """, char_id)
        
        if memory_rows:
            key_memories = []
            for row in memory_rows:
                key_memories.append({
                    'event': row['title'],
                    'description': row['description'],
                    'emotional_impact': row['emotional_impact'],
                    'time_period': row['time_period'],
                    'importance_level': row['importance_level'],
                    'triggers': list(row['triggers']) if row['triggers'] else []
                })
            char['background']['key_memories'] = key_memories
            print(f"   ✅ Exported {len(key_memories)} memories")
        
        # 11. Export character_relationships
        print("\n💝 Exporting relationships...")
        rel_rows = await conn.fetch("""
            SELECT relationship_type, related_entity, relationship_strength,
                   description, status
            FROM character_relationships WHERE character_id = $1
        """, char_id)
        
        if rel_rows:
            relationships = {}
            for row in rel_rows:
                rel_key = row['related_entity'].lower().replace(' ', '_')
                relationships[rel_key] = {
                    'relationship_type': row['relationship_type'],
                    'related_entity': row['related_entity'],
                    'relationship_strength': row['relationship_strength'],
                    'status': row['status']
                }
                
                # Parse description if it's JSON
                import json
                if row['description']:
                    try:
                        desc_data = json.loads(row['description']) if isinstance(row['description'], str) else row['description']
                        relationships[rel_key].update(desc_data)
                    except:
                        relationships[rel_key]['description'] = row['description']
            
            char['relationships'] = relationships
            print(f"   ✅ Exported {len(relationships)} relationships")
        
        # 12. Export character_abilities
        print("\n⚡ Exporting abilities...")
        try:
            ability_rows = await conn.fetch("""
                SELECT category, ability_name, description, proficiency_level,
                       development_method, usage_frequency
                FROM character_abilities WHERE character_id = $1
            """, char_id)
            
            if ability_rows:
                abilities = []
                for row in ability_rows:
                    abilities.append({
                        'category': row['category'],
                        'name': row['ability_name'],
                        'description': row['description'],
                        'proficiency': row['proficiency_level'],
                        'development': row['development_method'],
                        'frequency': row['usage_frequency']
                    })
                char['capabilities']['abilities'] = abilities
                print(f"   ✅ Exported {len(abilities)} abilities")
        except Exception as e:
            print(f"   ⚠️  Could not export abilities: {e}")
        
        # 13. Export character_expertise_domains
        print("\n🎓 Exporting expertise domains...")
        expertise_rows = await conn.fetch("""
            SELECT domain_name, expertise_level, description
            FROM character_expertise_domains WHERE character_id = $1
        """, char_id)
        
        if expertise_rows:
            knowledge_domains = [row['domain_name'] for row in expertise_rows]
            char['capabilities']['knowledge_domains'] = knowledge_domains
            print(f"   ✅ Exported {len(knowledge_domains)} expertise domains")
        
        # 14. Export character_speech_patterns
        print("\n🗨️  Exporting speech patterns...")
        speech_rows = await conn.fetch("""
            SELECT vocabulary_style, sentence_structure, punctuation_style,
                   response_length_guidance, pattern_data
            FROM character_speech_patterns WHERE character_id = $1
        """, char_id)
        
        if speech_rows:
            speech = speech_rows[0]
            speech_patterns = {}
            
            # Parse JSON fields
            import json
            if speech['vocabulary_style']:
                try:
                    vocab = json.loads(speech['vocabulary_style']) if isinstance(speech['vocabulary_style'], str) else speech['vocabulary_style']
                    speech_patterns['vocabulary'] = {'preferred_words': vocab}
                except:
                    speech_patterns['vocabulary_style'] = speech['vocabulary_style']
            
            if speech['sentence_structure']:
                speech_patterns['sentence_structure'] = speech['sentence_structure']
            
            if speech['punctuation_style']:
                speech_patterns['punctuation_style'] = speech['punctuation_style']
            
            if speech['response_length_guidance']:
                speech_patterns['response_length'] = speech['response_length_guidance']
            
            if speech['pattern_data']:
                try:
                    pattern = json.loads(speech['pattern_data']) if isinstance(speech['pattern_data'], str) else speech['pattern_data']
                    speech_patterns.update(pattern)
                except:
                    pass
            
            char['speech_patterns'] = speech_patterns
            print(f"   ✅ Exported speech patterns")
        
        # 15. Export character_emotional_triggers
        print("\n😊 Exporting emotional triggers...")
        trigger_rows = await conn.fetch("""
            SELECT trigger_type, trigger_description, emotional_response
            FROM character_emotional_triggers WHERE character_id = $1
        """, char_id)
        
        if trigger_rows:
            triggers = {'positive': [], 'negative': []}
            for row in trigger_rows:
                trigger_type = row['trigger_type']
                if trigger_type in triggers:
                    triggers[trigger_type].append(row['trigger_description'])
            
            char['emotional_profile'] = {'triggers': triggers}
            print(f"   ✅ Exported {len(trigger_rows)} emotional triggers")
        
        # 16. Export character_behavioral_triggers
        print("\n🎯 Exporting behavioral patterns...")
        behavior_rows = await conn.fetch("""
            SELECT trigger_pattern, response_behavior, priority_level
            FROM character_behavioral_triggers WHERE character_id = $1
        """, char_id)
        
        if behavior_rows:
            recognition_responses = [row['response_behavior'] for row in behavior_rows]
            char['behavioral_patterns'] = {
                'recognition_responses': recognition_responses
            }
            print(f"   ✅ Exported {len(recognition_responses)} behavioral patterns")
        
        # 17. Export character_instructions
        print("\n📋 Exporting instructions...")
        instruction_rows = await conn.fetch("""
            SELECT instruction_type, instruction_text, priority, context
            FROM character_instructions WHERE character_id = $1
            ORDER BY priority DESC
        """, char_id)
        
        if instruction_rows:
            core_directives = {}
            for row in instruction_rows:
                key = row['context'] or f"directive_{row['instruction_type']}"
                core_directives[key] = row['instruction_text']
            
            char['core_directives'] = core_directives
            print(f"   ✅ Exported {len(core_directives)} instructions/directives")
        
        await conn.close()
        
        # Write to YAML file
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{character['normalized_name']}_export_{timestamp}.yaml"
        filepath = output_path / filename
        
        print(f"\n💾 Writing to file: {filepath}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
        
        print("\n" + "=" * 70)
        print("🎉 Export Complete!")
        print("=" * 70)
        print(f"\n📄 File: {filepath}")
        print(f"📦 Character: {char_name}")
        print(f"🎭 Archetype: {character['archetype']}")
        print(f"📊 Total sections exported: {sum(1 for k, v in char.items() if v)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        await conn.close()
        return False


async def list_characters():
    """List all available characters in the database"""
    try:
        conn = await get_database_connection()
        characters = await conn.fetch("""
            SELECT id, name, normalized_name, occupation, archetype, is_active
            FROM characters
            WHERE is_active = true
            ORDER BY name
        """)
        await conn.close()
        return characters
    except Exception as e:
        print(f"❌ Failed to list characters: {e}")
        return []


async def main():
    """Main export function"""
    
    if len(sys.argv) < 2:
        print("🎭 WhisperEngine CDL Character Export to YAML")
        print("=" * 70)
        print("\nUsage:")
        print("  python export_character_to_yaml.py <character_name> [output_dir]")
        print("\nExamples:")
        print("  python export_character_to_yaml.py aetheris")
        print("  python export_character_to_yaml.py elena exports/backups")
        print("\nAvailable characters:")
        
        characters = await list_characters()
        if characters:
            print()
            for char in characters:
                print(f"  • {char['name']} ({char['normalized_name']}) - {char['occupation']}")
        else:
            print("  (No characters found in database)")
        
        return
    
    character_name = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "exports"
    
    success = await export_character_to_yaml(character_name, output_dir)
    
    if success:
        print("\n✅ Export completed successfully!")
        print(f"   Character '{character_name}' exported to YAML format")
    else:
        print("\n❌ Export failed - see errors above")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
