#!/usr/bin/env python3
"""
Comprehensive CDL Character Backup - FULL FIDELITY

Exports ALL character data from PostgreSQL database to YAML files.
Captures every table and every field for complete restoration capability.

Usage:
    python scripts/comprehensive_character_backup.py

Output:
    backups/characters_yaml_full/YYYY-MM-DD/character_name.yaml
"""

import os
import sys
import yaml
import asyncio
import asyncpg
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ComprehensiveCDLBackup:
    """Export COMPLETE character data from PostgreSQL database"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5433')),
            'database': os.getenv('POSTGRES_DB', 'whisperengine'),
            'user': os.getenv('POSTGRES_USER', 'whisperengine'),
            'password': os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
        }
        self.backup_dir = Path("backups/characters_yaml_full") / datetime.now().strftime("%Y-%m-%d")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    async def connect_db(self) -> asyncpg.Connection:
        """Connect to PostgreSQL database"""
        try:
            conn = await asyncpg.connect(**self.db_config)
            print(f"✅ Connected to PostgreSQL at {self.db_config['host']}:{self.db_config['port']}")
            return conn
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            raise
    
    async def get_all_characters(self, conn: asyncpg.Connection) -> List[Dict[str, Any]]:
        """Get all active characters"""
        query = """
        SELECT 
            id, name, normalized_name, occupation, description, archetype, 
            allow_full_roleplay, is_active, created_at, updated_at
        FROM characters 
        WHERE is_active = true
        ORDER BY name
        """
        rows = await conn.fetch(query)
        print(f"✅ Found {len(rows)} active characters")
        return [dict(row) for row in rows]
    
    async def export_character_full(self, conn: asyncpg.Connection, char_id: int, char_name: str) -> Dict[str, Any]:
        """Export ALL data for a single character"""
        
        character_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'schema_version': '1.0',
                'source': 'whisperengine_comprehensive_backup'
            }
        }
        
        # Define all character-related tables
        tables_to_export = {
            'character_values': 'VALUES',
            'character_interest_topics': 'INTERESTS',
            'character_identity_details': 'IDENTITY_DETAILS',
            'character_appearance': 'APPEARANCE',
            'character_voice_profile': 'VOICE_PROFILE',
            'character_voice_traits': 'VOICE_TRAITS',
            'character_attributes': 'ATTRIBUTES',
            'character_background': 'BACKGROUND',
            'character_relationships': 'RELATIONSHIPS',
            'character_communication_patterns': 'COMMUNICATION_PATTERNS',
            'character_behavioral_triggers': 'BEHAVIORAL_TRIGGERS',
            'character_speech_patterns': 'SPEECH_PATTERNS',
            'character_emotion_profile': 'EMOTION_PROFILE',
            'character_emotion_range': 'EMOTION_RANGE',
            'character_emotional_triggers': 'EMOTIONAL_TRIGGERS',
            'character_emotional_triggers_v2': 'EMOTIONAL_TRIGGERS_V2',
            'character_response_patterns': 'RESPONSE_PATTERNS',
            'character_response_style': 'RESPONSE_STYLE',
            'character_response_style_items': 'RESPONSE_STYLE_ITEMS',
            'character_response_modes': 'RESPONSE_MODES',
            'character_response_guidelines': 'RESPONSE_GUIDELINES',
            'character_conversation_flows': 'CONVERSATION_FLOWS',
            'character_conversation_flows_json_backup': 'CONVERSATION_FLOWS_JSON',
            'character_conversation_modes': 'CONVERSATION_MODES',
            'character_conversation_contexts': 'CONVERSATION_CONTEXTS',
            'character_conversation_directives': 'CONVERSATION_DIRECTIVES',
            'character_general_conversation': 'GENERAL_CONVERSATION',
            'character_mode_guidance': 'MODE_GUIDANCE',
            'character_mode_examples': 'MODE_EXAMPLES',
            'character_context_guidance': 'CONTEXT_GUIDANCE',
            'character_directives': 'DIRECTIVES',
            'character_instructions': 'INSTRUCTIONS',
            'character_message_triggers': 'MESSAGE_TRIGGERS',
            'character_ai_scenarios': 'AI_SCENARIOS',
            'character_roleplay_config': 'ROLEPLAY_CONFIG',
            'character_roleplay_scenarios_v2': 'ROLEPLAY_SCENARIOS_V2',
            'character_scenario_triggers_v2': 'SCENARIO_TRIGGERS_V2',
            'character_abilities': 'ABILITIES',
            'character_expertise_domains': 'EXPERTISE_DOMAINS',
            'character_interests': 'INTERESTS_EXTENDED',
            'character_cultural_expressions': 'CULTURAL_EXPRESSIONS',
            'character_vocabulary': 'VOCABULARY',
            'character_emoji_patterns': 'EMOJI_PATTERNS',
            'character_memories': 'MEMORIES',
            'character_current_context': 'CURRENT_CONTEXT',
            'character_current_goals': 'CURRENT_GOALS',
            'character_question_templates': 'QUESTION_TEMPLATES',
            'character_essence': 'ESSENCE',
            'character_entity_categories': 'ENTITY_CATEGORIES',
            'character_metadata': 'METADATA_EXTENDED'
        }
        
        print(f"  📦 Exporting {len(tables_to_export)} tables for {char_name}...")
        
        for table_name, data_key in tables_to_export.items():
            try:
                # Query all rows for this character
                rows = await conn.fetch(
                    f"SELECT * FROM {table_name} WHERE character_id = $1",
                    char_id
                )
                
                if rows:
                    # Convert rows to dictionaries
                    data_list = []
                    for row in rows:
                        row_dict = dict(row)
                        # Remove character_id (it's redundant in export)
                        row_dict.pop('character_id', None)
                        # Convert datetime objects to ISO strings
                        for key, value in row_dict.items():
                            if hasattr(value, 'isoformat'):
                                row_dict[key] = value.isoformat()
                        data_list.append(row_dict)
                    
                    character_data[data_key] = data_list
                    print(f"    ✓ {table_name}: {len(data_list)} rows")
                    
            except Exception as e:
                # Table might not exist or have different schema
                print(f"    ⚠️  {table_name}: {str(e)[:50]}")
        
        return character_data
    
    async def export_all_characters(self) -> List[str]:
        """Export all characters with full data"""
        print(f"🚀 Starting COMPREHENSIVE character backup")
        print(f"📁 Output directory: {self.backup_dir}")
        print()
        
        conn = await self.connect_db()
        
        try:
            characters = await self.get_all_characters(conn)
            
            if not characters:
                print("⚠️ No active characters found")
                return []
            
            exported_files = []
            
            for char in characters:
                char_id = char['id']
                char_name = char['name']
                
                print(f"\n{'='*60}")
                print(f"Exporting: {char_name}")
                print(f"{'='*60}")
                
                # Get basic character data
                basic_data = {
                    'name': char_name,
                    'normalized_name': char['normalized_name'],
                    'database_id': char_id,
                    'occupation': char['occupation'],
                    'description': char['description'],
                    'archetype': char['archetype'],
                    'allow_full_roleplay': char['allow_full_roleplay'],
                    'is_active': char['is_active'],
                    'created_at': char['created_at'].isoformat() if char['created_at'] else None,
                    'updated_at': char['updated_at'].isoformat() if char['updated_at'] else None
                }
                
                # Get comprehensive data
                comprehensive_data = await self.export_character_full(conn, char_id, char_name)
                
                # Combine
                full_export = {
                    'character': basic_data,
                    'data': comprehensive_data
                }
                
                # Write to YAML
                filename = self._normalize_filename(char_name) + ".yaml"
                filepath = self.backup_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(
                        full_export,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                        width=120,
                        indent=2
                    )
                
                print(f"\n✅ Exported to: {filepath}")
                exported_files.append(str(filepath))
            
            print(f"\n{'='*60}")
            print(f"🎉 COMPREHENSIVE BACKUP COMPLETE!")
            print(f"{'='*60}")
            print(f"📁 Location: {self.backup_dir}")
            print(f"📄 Files: {len(exported_files)}")
            
            # Calculate total size
            total_size = sum(Path(f).stat().st_size for f in exported_files)
            print(f"💾 Total size: {total_size / 1024:.2f} KB")
            
            return exported_files
            
        finally:
            await conn.close()
    
    def _normalize_filename(self, name: str) -> str:
        """Convert character name to safe filename"""
        return name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace("'", "")


async def main():
    """Main backup function"""
    try:
        exporter = ComprehensiveCDLBackup()
        exported_files = await exporter.export_all_characters()
        
        print("\n📋 Backup Files:")
        for filepath in exported_files:
            size = Path(filepath).stat().st_size
            print(f"  • {Path(filepath).name} ({size / 1024:.2f} KB)")
        
        print(f"\n✅ All character data backed up successfully!")
        print(f"📁 Location: {exporter.backup_dir}")
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
