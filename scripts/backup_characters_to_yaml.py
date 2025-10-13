#!/usr/bin/env python3
"""
Character Database Backup to YAML Script

Exports all active characters from the PostgreSQL CDL database to individual YAML files.
This provides clean, human-readable backups that are easier to manage than JSON.

Usage:
    python scripts/backup_characters_to_yaml.py

Output:
    backups/characters_yaml/YYYY-MM-DD/character_name.yaml
"""

import os
import sys
import yaml
import asyncio
import asyncpg
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CharacterYAMLExporter:
    """Export CDL characters from PostgreSQL database to clean YAML format"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5433')),
            'database': os.getenv('POSTGRES_DB', 'whisperengine'),
            'user': os.getenv('POSTGRES_USER', 'whisperengine'),
            'password': os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
        }
        self.backup_dir = Path("backups/characters_yaml") / datetime.now().strftime("%Y-%m-%d")
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
        """Get all active characters with full CDL data"""
        # First get basic character data
        basic_query = """
        SELECT 
            id, name, normalized_name, occupation, description, archetype, 
            allow_full_roleplay, is_active, created_at, updated_at
        FROM characters 
        WHERE is_active = true
        ORDER BY name
        """
        
        characters = await conn.fetch(basic_query)
        print(f"✅ Found {len(characters)} active characters")
        
        # For each character, gather additional CDL data from related tables
        enriched_characters = []
        for char in characters:
            char_data = dict(char)
            char_id = char['id']
            
            # Get additional character data from various tables
            try:
                # Character identity details
                identity_data = await conn.fetchrow(
                    "SELECT * FROM character_identity_details WHERE character_id = $1", char_id
                )
                if identity_data:
                    char_data['identity_details'] = dict(identity_data)
                
                # Character values
                values = await conn.fetch(
                    "SELECT value_text FROM character_values WHERE character_id = $1", char_id
                )
                if values:
                    char_data['values'] = [v['value_text'] for v in values]
                
                # Character interests
                interests = await conn.fetch(
                    "SELECT topic FROM character_interest_topics WHERE character_id = $1", char_id
                )
                if interests:
                    char_data['interests'] = [i['topic'] for i in interests]
                
                # Character communication patterns
                comm_patterns = await conn.fetchrow(
                    "SELECT * FROM character_communication_patterns WHERE character_id = $1", char_id
                )
                if comm_patterns:
                    char_data['communication_patterns'] = dict(comm_patterns)
                
                # Character speech patterns
                speech_patterns = await conn.fetchrow(
                    "SELECT * FROM character_speech_patterns WHERE character_id = $1", char_id
                )
                if speech_patterns:
                    char_data['speech_patterns'] = dict(speech_patterns)
                
                # Character background
                background = await conn.fetchrow(
                    "SELECT * FROM character_background WHERE character_id = $1", char_id
                )
                if background:
                    char_data['background'] = dict(background)
                
                # Character roleplay config
                roleplay_config = await conn.fetchrow(
                    "SELECT * FROM character_roleplay_config WHERE character_id = $1", char_id
                )
                if roleplay_config:
                    char_data['roleplay_config'] = dict(roleplay_config)
                
            except (ValueError, KeyError, AttributeError) as e:
                print(f"⚠️ Warning: Could not fetch extended data for {char['name']}: {e}")
            
            enriched_characters.append(char_data)
        
        return enriched_characters
    
    def convert_to_yaml_structure(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database structure to clean YAML CDL format"""
        
        yaml_structure = {
            'name': character_data['name'],
            'normalized_name': character_data.get('normalized_name'),
            'created_at': character_data['created_at'].isoformat() if character_data['created_at'] else None,
            'updated_at': character_data['updated_at'].isoformat() if character_data['updated_at'] else None,
            'is_active': character_data.get('is_active', True)
        }
        
        # Identity section
        identity = {
            'name': character_data['name'],
        }
        
        if character_data.get('occupation'):
            identity['occupation'] = character_data['occupation']
        if character_data.get('description'):
            identity['description'] = character_data['description']
        if character_data.get('archetype'):
            identity['archetype'] = character_data['archetype']
        if character_data.get('allow_full_roleplay') is not None:
            identity['allow_full_roleplay_immersion'] = character_data['allow_full_roleplay']
            
        # Add identity details if available
        if character_data.get('identity_details'):
            identity.update(character_data['identity_details'])
            
        yaml_structure['identity'] = identity
            
        # Values section
        if character_data.get('values'):
            yaml_structure['values'] = character_data['values']
            
        # Interests section
        if character_data.get('interests'):
            yaml_structure['interests'] = character_data['interests']
            
        # Communication section
        communication = {}
        if character_data.get('communication_patterns'):
            comm_patterns = character_data['communication_patterns']
            # Remove character_id and other meta fields
            communication = {k: v for k, v in comm_patterns.items() 
                           if k not in ['character_id', 'id', 'created_at', 'updated_at'] and v is not None}
                           
        if communication:
            yaml_structure['communication'] = communication
            
        # Speech patterns section
        if character_data.get('speech_patterns'):
            speech_patterns = character_data['speech_patterns']
            # Clean speech patterns data
            cleaned_speech = {k: v for k, v in speech_patterns.items() 
                            if k not in ['character_id', 'id', 'created_at', 'updated_at'] and v is not None}
            if cleaned_speech:
                yaml_structure['speech_patterns'] = cleaned_speech
            
        # Background section
        if character_data.get('background'):
            background = character_data['background']
            # Clean background data
            cleaned_background = {k: v for k, v in background.items() 
                                if k not in ['character_id', 'id', 'created_at', 'updated_at'] and v is not None}
            if cleaned_background:
                yaml_structure['background'] = cleaned_background
            
        # Roleplay configuration section
        if character_data.get('roleplay_config'):
            roleplay_config = character_data['roleplay_config']
            # Clean roleplay config data
            cleaned_roleplay = {k: v for k, v in roleplay_config.items() 
                              if k not in ['character_id', 'id', 'created_at', 'updated_at'] and v is not None}
            if cleaned_roleplay:
                yaml_structure['roleplay_config'] = cleaned_roleplay
            
        # Metadata section
        metadata = {
            'database_id': character_data['id'],
            'export_date': datetime.now().isoformat(),
            'schema_version': '1.0'
        }
        yaml_structure['metadata'] = metadata
            
        # Remove None values from top level
        return {k: v for k, v in yaml_structure.items() if v is not None}
    
    def normalize_filename(self, name: str) -> str:
        """Convert character name to safe filename"""
        return name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
    
    async def export_character_to_yaml(self, character_data: Dict[str, Any]) -> str:
        """Export single character to YAML file"""
        yaml_data = self.convert_to_yaml_structure(character_data)
        
        # Create filename
        filename = f"{self.normalize_filename(character_data['name'])}.yaml"
        filepath = self.backup_dir / filename
        
        # Write YAML file with clean formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, 
                     default_flow_style=False,
                     allow_unicode=True,
                     sort_keys=False,
                     indent=2,
                     width=120)
        
        print(f"✅ Exported {character_data['name']} → {filepath}")
        return str(filepath)
    
    async def backup_all_characters(self) -> List[str]:
        """Export all characters to YAML backups"""
        print(f"🚀 Starting character backup to {self.backup_dir}")
        
        conn = await self.connect_db()
        try:
            characters = await self.get_all_characters(conn)
            
            if not characters:
                print("⚠️ No active characters found in database")
                return []
            
            exported_files = []
            for character in characters:
                try:
                    filepath = await self.export_character_to_yaml(character)
                    exported_files.append(filepath)
                except (ValueError, KeyError, AttributeError, IOError) as e:
                    print(f"❌ Failed to export {character.get('name', 'Unknown')}: {e}")
            
            print("\n🎉 Backup complete!")
            print(f"📁 Location: {self.backup_dir}")
            print(f"📄 Files exported: {len(exported_files)}")
            
            return exported_files
            
        finally:
            await conn.close()

async def main():
    """Main backup function"""
    try:
        exporter = CharacterYAMLExporter()
        exported_files = await exporter.backup_all_characters()
        
        print("\n📋 Summary:")
        for filepath in exported_files:
            print(f"  • {Path(filepath).name}")
            
    except (ConnectionError, ValueError, RuntimeError) as e:
        print(f"❌ Backup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())