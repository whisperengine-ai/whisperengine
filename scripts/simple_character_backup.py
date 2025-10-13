#!/usr/bin/env python3
"""
Simple Character Database Backup to YAML Script

Exports basic character data from PostgreSQL database to clean YAML files.
This provides a reliable backup of current dev characters.

Usage:
    python scripts/simple_character_backup.py

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

class SimpleCharacterYAMLExporter:
    """Export basic CDL character data from PostgreSQL database to clean YAML format"""
    
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
    
    async def get_basic_characters(self, conn: asyncpg.Connection) -> List[Dict[str, Any]]:
        """Get basic character data that we know exists"""
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
    
    async def get_character_values(self, conn: asyncpg.Connection, char_id: int) -> List[str]:
        """Get character values safely"""
        try:
            values = await conn.fetch(
                "SELECT value_key, value_description FROM character_values WHERE character_id = $1", 
                char_id
            )
            return [f"{v['value_key']}: {v['value_description']}" if v['value_description'] 
                   else v['value_key'] for v in values]
        except (ValueError, KeyError, AttributeError):
            return []
    
    async def get_character_interests(self, conn: asyncpg.Connection, char_id: int) -> List[str]:
        """Get character interests safely"""
        try:
            interests = await conn.fetch(
                "SELECT topic_keyword FROM character_interest_topics WHERE character_id = $1", 
                char_id
            )
            return [i['topic_keyword'] for i in interests]
        except (ValueError, KeyError, AttributeError):
            return []
    
    def convert_to_yaml_structure(self, character_data: Dict[str, Any], values: List[str], interests: List[str]) -> Dict[str, Any]:
        """Convert database structure to clean YAML CDL format"""
        
        yaml_structure = {
            'name': character_data['name'],
            'identity': {
                'name': character_data['name'],
                'occupation': character_data.get('occupation'),
                'description': character_data.get('description'),
                'archetype': character_data.get('archetype', 'real-world'),
                'allow_full_roleplay_immersion': character_data.get('allow_full_roleplay', False)
            },
            'metadata': {
                'database_id': character_data['id'],
                'normalized_name': character_data.get('normalized_name'),
                'export_date': datetime.now().isoformat(),
                'created_at': character_data['created_at'].isoformat() if character_data['created_at'] else None,
                'updated_at': character_data['updated_at'].isoformat() if character_data['updated_at'] else None,
                'is_active': character_data.get('is_active', True),
                'schema_version': '1.0',
                'source': 'whisperengine_postgresql_backup'
            }
        }
        
        # Add values if available
        if values:
            yaml_structure['values'] = values
            
        # Add interests if available
        if interests:
            yaml_structure['interests'] = interests
            
        # Remove None values from identity
        yaml_structure['identity'] = {k: v for k, v in yaml_structure['identity'].items() if v is not None}
        
        return yaml_structure
    
    def normalize_filename(self, name: str) -> str:
        """Convert character name to safe filename"""
        return name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace("'", "")
    
    async def export_character_to_yaml(self, conn: asyncpg.Connection, character_data: Dict[str, Any]) -> str:
        """Export single character to YAML file"""
        
        # Get additional data
        values = await self.get_character_values(conn, character_data['id'])
        interests = await self.get_character_interests(conn, character_data['id'])
        
        yaml_data = self.convert_to_yaml_structure(character_data, values, interests)
        
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
            characters = await self.get_basic_characters(conn)
            
            if not characters:
                print("⚠️ No active characters found in database")
                return []
            
            exported_files = []
            for character in characters:
                try:
                    filepath = await self.export_character_to_yaml(conn, character)
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
        exporter = SimpleCharacterYAMLExporter()
        exported_files = await exporter.backup_all_characters()
        
        print("\n📋 Character Backups Created:")
        for filepath in exported_files:
            print(f"  • {Path(filepath).name}")
            
    except (ConnectionError, ValueError, RuntimeError) as e:
        print(f"❌ Backup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())