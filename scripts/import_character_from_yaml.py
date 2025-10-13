#!/usr/bin/env python3
"""
CDL YAML Import Script

Imports character definitions from YAML files back into PostgreSQL database.
Works with YAML files exported by simple_character_backup.py

Usage:
    # Import single character
    python scripts/import_character_from_yaml.py elena_rodriguez.yaml
    
    # Import with overwrite
    python scripts/import_character_from_yaml.py elena_rodriguez.yaml --overwrite
    
    # Import all from directory
    python scripts/import_character_from_yaml.py backups/characters_yaml/2025-10-13/ --all

Features:
    - Safe import with overwrite protection
    - Validates YAML structure before import
    - Updates or creates characters as needed
    - Preserves character ID relationships
"""

import os
import sys
import yaml
import asyncio
import asyncpg
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CDLYAMLImporter:
    """Import CDL character definitions from YAML files"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5433')),
            'database': os.getenv('POSTGRES_DB', 'whisperengine'),
            'user': os.getenv('POSTGRES_USER', 'whisperengine'),
            'password': os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
        }
        
    async def connect_db(self) -> asyncpg.Connection:
        """Connect to PostgreSQL database"""
        try:
            conn = await asyncpg.connect(**self.db_config)
            print(f"✅ Connected to PostgreSQL at {self.db_config['host']}:{self.db_config['port']}")
            return conn
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            raise
    
    async def import_character(self, yaml_path: Path, overwrite: bool = False) -> bool:
        """
        Import a character from YAML file
        
        Args:
            yaml_path: Path to YAML file
            overwrite: If True, update existing character
            
        Returns:
            True if successful, False otherwise
        """
        if not yaml_path.exists():
            print(f"❌ File not found: {yaml_path}")
            return False
        
        # Load YAML file
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Failed to load YAML file: {e}")
            return False
        
        # Validate structure
        if 'identity' not in yaml_data or 'name' not in yaml_data.get('identity', {}):
            print("❌ Invalid YAML structure: missing identity/name")
            return False
        
        conn = await self.connect_db()
        
        try:
            identity = yaml_data.get('identity', {})
            metadata = yaml_data.get('metadata', {})
            
            character_name = identity.get('name')
            normalized_name = metadata.get('normalized_name') or self._normalize_name(character_name)
            
            # Check if character exists
            existing = await conn.fetchrow(
                "SELECT id FROM characters WHERE LOWER(normalized_name) = LOWER($1)",
                normalized_name
            )
            
            if existing and not overwrite:
                print(f"⚠️  Character '{character_name}' already exists. Use --overwrite to replace.")
                return False
            
            # Import character data
            if existing:
                char_id = existing['id']
                await self._update_character(conn, char_id, yaml_data)
                print(f"✅ Updated character '{character_name}' (ID: {char_id})")
            else:
                char_id = await self._create_character(conn, normalized_name, yaml_data)
                print(f"✅ Created character '{character_name}' (ID: {char_id})")
            
            # Import related data
            await self._import_values(conn, char_id, yaml_data.get('values', []))
            await self._import_interests(conn, char_id, yaml_data.get('interests', []))
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to import character: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await conn.close()
    
    async def import_all_from_directory(self, directory: Path, overwrite: bool = False) -> Dict[str, bool]:
        """
        Import all YAML files from a directory
        
        Args:
            directory: Path to directory containing YAML files
            overwrite: If True, update existing characters
            
        Returns:
            Dictionary mapping filenames to success status
        """
        if not directory.exists():
            print(f"❌ Directory not found: {directory}")
            return {}
        
        yaml_files = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))
        
        if not yaml_files:
            print(f"❌ No YAML files found in {directory}")
            return {}
        
        print(f"📦 Found {len(yaml_files)} YAML files to import")
        
        results = {}
        for yaml_file in yaml_files:
            print(f"\n{'='*60}")
            print(f"Importing: {yaml_file.name}")
            print(f"{'='*60}")
            
            success = await self.import_character(yaml_file, overwrite)
            results[yaml_file.name] = success
        
        # Print summary
        successful = sum(1 for s in results.values() if s)
        print(f"\n{'='*60}")
        print(f"Import Summary: {successful}/{len(results)} successful")
        print(f"{'='*60}")
        
        return results
    
    async def _create_character(self, conn: asyncpg.Connection, normalized_name: str, yaml_data: Dict[str, Any]) -> int:
        """Create new character in database"""
        identity = yaml_data.get('identity', {})
        
        char_id = await conn.fetchval("""
            INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, true)
            RETURNING id
        """,
            identity.get('name'),
            normalized_name,
            identity.get('occupation'),
            identity.get('description'),
            identity.get('archetype', 'real-world'),
            identity.get('allow_full_roleplay_immersion', False)
        )
        
        return char_id
    
    async def _update_character(self, conn: asyncpg.Connection, char_id: int, yaml_data: Dict[str, Any]) -> None:
        """Update existing character in database"""
        identity = yaml_data.get('identity', {})
        
        await conn.execute("""
            UPDATE characters
            SET name = $1, occupation = $2, description = $3, archetype = $4,
                allow_full_roleplay = $5, updated_at = NOW()
            WHERE id = $6
        """,
            identity.get('name'),
            identity.get('occupation'),
            identity.get('description'),
            identity.get('archetype', 'real-world'),
            identity.get('allow_full_roleplay_immersion', False),
            char_id
        )
        
        # Clear existing related data
        await conn.execute("DELETE FROM character_values WHERE character_id = $1", char_id)
        await conn.execute("DELETE FROM character_interest_topics WHERE character_id = $1", char_id)
    
    async def _import_values(self, conn: asyncpg.Connection, char_id: int, values: List[str]) -> None:
        """Import character values"""
        for value in values:
            if ':' in str(value):
                # Format: "key: description"
                key, desc = str(value).split(':', 1)
                await conn.execute("""
                    INSERT INTO character_values (character_id, value_key, value_description)
                    VALUES ($1, $2, $3)
                """, char_id, key.strip(), desc.strip())
            else:
                # Just a key
                await conn.execute("""
                    INSERT INTO character_values (character_id, value_key)
                    VALUES ($1, $2)
                """, char_id, str(value).strip())
    
    async def _import_interests(self, conn: asyncpg.Connection, char_id: int, interests: List[str]) -> None:
        """Import character interests"""
        for interest in interests:
            await conn.execute("""
                INSERT INTO character_interest_topics (character_id, topic_keyword)
                VALUES ($1, $2)
            """, char_id, str(interest).strip())
    
    def _normalize_name(self, name: str) -> str:
        """Convert character name to normalized form"""
        return name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace("'", "")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='CDL YAML Import - Import Character Definitions from YAML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import single character
  python scripts/import_character_from_yaml.py elena_rodriguez.yaml
  
  # Import with overwrite
  python scripts/import_character_from_yaml.py elena_rodriguez.yaml --overwrite
  
  # Import all from directory
  python scripts/import_character_from_yaml.py backups/characters_yaml/2025-10-13/ --all
        """
    )
    
    parser.add_argument('path', type=Path, help='Path to YAML file or directory')
    parser.add_argument('--all', action='store_true', help='Import all YAML files from directory')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing character data')
    
    args = parser.parse_args()
    
    importer = CDLYAMLImporter()
    
    if args.all:
        if not args.path.is_dir():
            print("❌ Path must be a directory when using --all")
            sys.exit(1)
        asyncio.run(importer.import_all_from_directory(args.path, args.overwrite))
    else:
        if not args.path.is_file():
            print("❌ Path must be a YAML file")
            sys.exit(1)
        success = asyncio.run(importer.import_character(args.path, args.overwrite))
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
