#!/usr/bin/env python3
"""
CDL YAML Manager - Export and Import Character Definitions

Provides unified interface for exporting CDL characters from PostgreSQL to YAML
and importing YAML files back into the database.

Usage:
    # Export single character
    python scripts/cdl_yaml_manager.py export elena
    
    # Export all characters
    python scripts/cdl_yaml_manager.py export --all
    
    # Import single character from YAML
    python scripts/cdl_yaml_manager.py import backups/characters_yaml/2025-10-12/elena_rodriguez.yaml
    
    # Import all YAML files from directory
    python scripts/cdl_yaml_manager.py import backups/characters_yaml/2025-10-12/ --all

Output:
    backups/characters_yaml/YYYY-MM-DD/character_name.yaml
"""

import os
import sys
import yaml
import asyncio
import asyncpg
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CDLYAMLManager:
    """Unified manager for CDL YAML export and import operations"""
    
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
    
    # ============================================================================
    # EXPORT FUNCTIONS
    # ============================================================================
    
    async def export_character(self, character_name: str, output_path: Optional[Path] = None) -> Path:
        """
        Export a single character to YAML file
        
        Args:
            character_name: Character normalized name (e.g., 'elena', 'marcus')
            output_path: Optional custom output path
            
        Returns:
            Path to created YAML file
        """
        conn = await self.connect_db()
        
        try:
            # Get character data
            character_data = await self._get_character_full_data(conn, character_name)
            
            if not character_data:
                print(f"❌ Character '{character_name}' not found in database")
                return None
            
            # Convert to YAML structure
            yaml_data = self._convert_to_yaml_structure(character_data)
            
            # Determine output path
            if output_path is None:
                filename = f"{self._normalize_filename(character_data['name'])}.yaml"
                output_path = self.backup_dir / filename
            
            # Write YAML file
            self._write_yaml_file(yaml_data, output_path)
            
            print(f"✅ Exported '{character_data['name']}' to {output_path}")
            return output_path
            
        finally:
            await conn.close()
    
    async def export_all_characters(self) -> List[Path]:
        """
        Export all active characters to YAML files
        
        Returns:
            List of paths to created YAML files
        """
        conn = await self.connect_db()
        exported_files = []
        
        try:
            # Get all active characters
            characters = await conn.fetch(
                "SELECT normalized_name FROM characters WHERE is_active = true ORDER BY name"
            )
            
            print(f"📦 Found {len(characters)} active characters to export")
            
            for char in characters:
                try:
                    file_path = await self.export_character(char['normalized_name'])
                    if file_path:
                        exported_files.append(file_path)
                except Exception as e:
                    print(f"⚠️  Failed to export {char['normalized_name']}: {e}")
            
            print(f"\n✅ Successfully exported {len(exported_files)} characters to {self.backup_dir}")
            return exported_files
            
        finally:
            await conn.close()
    
    async def _get_character_full_data(self, conn: asyncpg.Connection, character_name: str) -> Optional[Dict[str, Any]]:
        """Get complete character data from database"""
        
        # Get basic character data
        char_row = await conn.fetchrow("""
            SELECT id, name, normalized_name, occupation, description, archetype,
                   allow_full_roleplay, is_active, created_at, updated_at
            FROM characters
            WHERE LOWER(normalized_name) = LOWER($1) AND is_active = true
        """, character_name)
        
        if not char_row:
            return None
        
        char_data = dict(char_row)
        char_id = char_data['id']
        
        # Get additional data from related tables
        char_data['values'] = await self._get_character_values(conn, char_id)
        char_data['interests'] = await self._get_character_interests(conn, char_id)
        char_data['identity_details'] = await self._get_identity_details(conn, char_id)
        char_data['personality_traits'] = await self._get_personality_traits(conn, char_id)
        char_data['communication_patterns'] = await self._get_communication_patterns(conn, char_id)
        char_data['background'] = await self._get_background(conn, char_id)
        char_data['relationships'] = await self._get_relationships(conn, char_id)
        char_data['behavioral_patterns'] = await self._get_behavioral_patterns(conn, char_id)
        char_data['speech_patterns'] = await self._get_speech_patterns(conn, char_id)
        char_data['emotional_profile'] = await self._get_emotional_profile(conn, char_id)
        
        return char_data
    
    async def _get_character_values(self, conn: asyncpg.Connection, char_id: int) -> List[Dict[str, str]]:
        """Get character values"""
        rows = await conn.fetch("""
            SELECT value_key, value_description
            FROM character_values
            WHERE character_id = $1
            ORDER BY value_key
        """, char_id)
        return [{'key': r['value_key'], 'description': r['value_description']} for r in rows]
    
    async def _get_character_interests(self, conn: asyncpg.Connection, char_id: int) -> List[str]:
        """Get character interests"""
        rows = await conn.fetch("""
            SELECT topic_keyword
            FROM character_interest_topics
            WHERE character_id = $1
            ORDER BY topic_keyword
        """, char_id)
        return [r['topic_keyword'] for r in rows]
    
    async def _get_identity_details(self, conn: asyncpg.Connection, char_id: int) -> Optional[Dict[str, Any]]:
        """Get character identity details"""
        row = await conn.fetchrow("""
            SELECT age, gender, location, timezone, nickname, full_name,
                   height, build, hair_color, eye_color, style,
                   distinctive_features, appearance_description
            FROM character_identity_details
            WHERE character_id = $1
        """, char_id)
        return dict(row) if row else None
    
    async def _get_personality_traits(self, conn: asyncpg.Connection, char_id: int) -> Dict[str, Any]:
        """Get personality traits including Big Five"""
        traits = {}
        
        # Get Big Five scores
        big_five = await conn.fetchrow("""
            SELECT openness, conscientiousness, extraversion, agreeableness, neuroticism
            FROM character_big_five_personality
            WHERE character_id = $1
        """, char_id)
        
        if big_five:
            traits['big_five'] = dict(big_five)
        
        # Get general traits
        trait_rows = await conn.fetch("""
            SELECT trait_name, trait_value
            FROM character_personality_traits
            WHERE character_id = $1
        """, char_id)
        
        if trait_rows:
            traits['traits'] = {r['trait_name']: r['trait_value'] for r in trait_rows}
        
        return traits
    
    async def _get_communication_patterns(self, conn: asyncpg.Connection, char_id: int) -> Dict[str, Any]:
        """Get communication patterns"""
        patterns = {}
        
        # Get typical responses
        responses = await conn.fetch("""
            SELECT scenario_type, response_text
            FROM character_typical_responses
            WHERE character_id = $1
        """, char_id)
        
        if responses:
            patterns['typical_responses'] = {}
            for r in responses:
                scenario = r['scenario_type']
                if scenario not in patterns['typical_responses']:
                    patterns['typical_responses'][scenario] = []
                patterns['typical_responses'][scenario].append(r['response_text'])
        
        # Get emotional expressions
        expressions = await conn.fetch("""
            SELECT emotion_type, expression_text
            FROM character_emotional_expressions
            WHERE character_id = $1
        """, char_id)
        
        if expressions:
            patterns['emotional_expressions'] = {
                r['emotion_type']: r['expression_text'] for r in expressions
            }
        
        return patterns
    
    async def _get_background(self, conn: asyncpg.Connection, char_id: int) -> Dict[str, Any]:
        """Get character background/backstory"""
        background = {}
        
        # Get life phases
        phases = await conn.fetch("""
            SELECT phase_name, age_range, key_events, emotional_impact
            FROM character_life_phases
            WHERE character_id = $1
            ORDER BY age_range
        """, char_id)
        
        if phases:
            background['life_phases'] = [dict(p) for p in phases]
        
        return background
    
    async def _get_relationships(self, conn: asyncpg.Connection, char_id: int) -> List[Dict[str, Any]]:
        """Get character relationships"""
        rows = await conn.fetch("""
            SELECT person_name, relationship_type, description, emotional_significance
            FROM character_relationships
            WHERE character_id = $1
        """, char_id)
        return [dict(r) for r in rows]
    
    async def _get_behavioral_patterns(self, conn: asyncpg.Connection, char_id: int) -> Dict[str, Any]:
        """Get behavioral patterns"""
        patterns = {}
        
        rows = await conn.fetch("""
            SELECT pattern_type, pattern_description
            FROM character_behavioral_patterns
            WHERE character_id = $1
        """, char_id)
        
        for r in rows:
            pattern_type = r['pattern_type']
            if pattern_type not in patterns:
                patterns[pattern_type] = []
            patterns[pattern_type].append(r['pattern_description'])
        
        return patterns
    
    async def _get_speech_patterns(self, conn: asyncpg.Connection, char_id: int) -> Dict[str, Any]:
        """Get speech patterns"""
        speech = {}
        
        # Get voice characteristics
        voice = await conn.fetchrow("""
            SELECT tone, pace, volume, accent, vocabulary_level
            FROM character_voice_characteristics
            WHERE character_id = $1
        """, char_id)
        
        if voice:
            speech['voice'] = dict(voice)
        
        # Get common phrases
        phrases = await conn.fetch("""
            SELECT phrase_text, usage_context
            FROM character_common_phrases
            WHERE character_id = $1
        """, char_id)
        
        if phrases:
            speech['common_phrases'] = [
                {'phrase': r['phrase_text'], 'context': r['usage_context']} 
                for r in phrases
            ]
        
        return speech
    
    async def _get_emotional_profile(self, conn: asyncpg.Connection, char_id: int) -> Dict[str, Any]:
        """Get emotional profile"""
        profile = {}
        
        rows = await conn.fetch("""
            SELECT emotion_type, intensity, triggers, typical_response
            FROM character_emotional_patterns
            WHERE character_id = $1
        """, char_id)
        
        if rows:
            profile['emotional_patterns'] = [dict(r) for r in rows]
        
        return profile
    
    def _convert_to_yaml_structure(self, char_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database structure to clean CDL YAML format"""
        
        yaml_structure = {
            'cdl_version': '1.0',
            'character': {
                'metadata': {
                    'name': char_data['name'],
                    'database_id': char_data['id'],
                    'normalized_name': char_data['normalized_name'],
                    'export_date': datetime.now().isoformat(),
                    'created_at': char_data['created_at'].isoformat() if char_data.get('created_at') else None,
                    'updated_at': char_data['updated_at'].isoformat() if char_data.get('updated_at') else None,
                    'is_active': char_data.get('is_active', True),
                    'schema_version': '1.0',
                    'source': 'whisperengine_postgresql'
                },
                'identity': {
                    'name': char_data['name'],
                    'occupation': char_data.get('occupation'),
                    'description': char_data.get('description'),
                    'archetype': char_data.get('archetype', 'real_world'),
                    'allow_full_roleplay_immersion': char_data.get('allow_full_roleplay', False)
                }
            }
        }
        
        # Add identity details if available
        if char_data.get('identity_details'):
            identity_details = char_data['identity_details']
            if identity_details:
                yaml_structure['character']['identity'].update({
                    k: v for k, v in identity_details.items() 
                    if v is not None and k not in ['character_id']
                })
        
        # Add values
        if char_data.get('values'):
            yaml_structure['character']['values'] = char_data['values']
        
        # Add interests
        if char_data.get('interests'):
            yaml_structure['character']['interests'] = char_data['interests']
        
        # Add personality traits
        if char_data.get('personality_traits'):
            yaml_structure['character']['personality'] = char_data['personality_traits']
        
        # Add communication patterns
        if char_data.get('communication_patterns'):
            yaml_structure['character']['communication'] = char_data['communication_patterns']
        
        # Add background
        if char_data.get('background'):
            yaml_structure['character']['background'] = char_data['background']
        
        # Add relationships
        if char_data.get('relationships'):
            yaml_structure['character']['relationships'] = char_data['relationships']
        
        # Add behavioral patterns
        if char_data.get('behavioral_patterns'):
            yaml_structure['character']['behavioral_patterns'] = char_data['behavioral_patterns']
        
        # Add speech patterns
        if char_data.get('speech_patterns'):
            yaml_structure['character']['speech_patterns'] = char_data['speech_patterns']
        
        # Add emotional profile
        if char_data.get('emotional_profile'):
            yaml_structure['character']['emotional_profile'] = char_data['emotional_profile']
        
        return yaml_structure
    
    def _normalize_filename(self, name: str) -> str:
        """Convert character name to safe filename"""
        return name.lower().replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace("'", "")
    
    def _write_yaml_file(self, data: Dict[str, Any], filepath: Path) -> None:
        """Write data to YAML file with clean formatting"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(
                data, 
                f, 
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                width=120
            )
    
    # ============================================================================
    # IMPORT FUNCTIONS
    # ============================================================================
    
    async def import_character(self, yaml_path: Path, overwrite: bool = False) -> bool:
        """
        Import a character from YAML file into database
        
        Args:
            yaml_path: Path to YAML file
            overwrite: If True, overwrite existing character data
            
        Returns:
            True if successful, False otherwise
        """
        if not yaml_path.exists():
            print(f"❌ File not found: {yaml_path}")
            return False
        
        conn = await self.connect_db()
        
        try:
            # Load YAML file
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            # Validate structure
            if 'character' not in yaml_data:
                print(f"❌ Invalid YAML structure: missing 'character' section")
                return False
            
            character_data = yaml_data['character']
            
            # Extract basic info
            metadata = character_data.get('metadata', {})
            identity = character_data.get('identity', {})
            
            character_name = identity.get('name') or metadata.get('name')
            normalized_name = self._normalize_filename(character_name)
            
            # Check if character exists
            existing = await conn.fetchrow(
                "SELECT id FROM characters WHERE LOWER(normalized_name) = LOWER($1)",
                normalized_name
            )
            
            if existing and not overwrite:
                print(f"⚠️  Character '{character_name}' already exists. Use --overwrite to replace.")
                return False
            
            # Import character data
            char_id = await self._import_character_data(conn, character_data, normalized_name, existing)
            
            print(f"✅ Successfully imported '{character_name}' (ID: {char_id})")
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
            overwrite: If True, overwrite existing character data
            
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
    
    async def _import_character_data(
        self, 
        conn: asyncpg.Connection, 
        character_data: Dict[str, Any], 
        normalized_name: str,
        existing: Optional[asyncpg.Record]
    ) -> int:
        """Import character data into database"""
        
        identity = character_data.get('identity', {})
        metadata = character_data.get('metadata', {})
        
        character_name = identity.get('name') or metadata.get('name')
        
        if existing:
            # Update existing character
            char_id = existing['id']
            
            await conn.execute("""
                UPDATE characters
                SET name = $1, occupation = $2, description = $3, archetype = $4,
                    allow_full_roleplay = $5, updated_at = NOW()
                WHERE id = $6
            """,
                character_name,
                identity.get('occupation'),
                identity.get('description'),
                identity.get('archetype', 'real_world'),
                identity.get('allow_full_roleplay_immersion', False),
                char_id
            )
            
            # Clear existing related data
            await self._clear_character_data(conn, char_id)
        else:
            # Insert new character
            char_id = await conn.fetchval("""
                INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, true)
                RETURNING id
            """,
                character_name,
                normalized_name,
                identity.get('occupation'),
                identity.get('description'),
                identity.get('archetype', 'real_world'),
                identity.get('allow_full_roleplay_immersion', False)
            )
        
        # Import all sections
        await self._import_values(conn, char_id, character_data.get('values', []))
        await self._import_interests(conn, char_id, character_data.get('interests', []))
        await self._import_identity_details(conn, char_id, identity)
        await self._import_personality(conn, char_id, character_data.get('personality', {}))
        await self._import_communication(conn, char_id, character_data.get('communication', {}))
        await self._import_background(conn, char_id, character_data.get('background', {}))
        await self._import_relationships(conn, char_id, character_data.get('relationships', []))
        await self._import_behavioral_patterns(conn, char_id, character_data.get('behavioral_patterns', {}))
        await self._import_speech_patterns(conn, char_id, character_data.get('speech_patterns', {}))
        await self._import_emotional_profile(conn, char_id, character_data.get('emotional_profile', {}))
        
        return char_id
    
    async def _clear_character_data(self, conn: asyncpg.Connection, char_id: int) -> None:
        """Clear existing character data before re-import"""
        tables = [
            'character_values',
            'character_interest_topics',
            'character_identity_details',
            'character_big_five_personality',
            'character_personality_traits',
            'character_typical_responses',
            'character_emotional_expressions',
            'character_life_phases',
            'character_relationships',
            'character_behavioral_patterns',
            'character_voice_characteristics',
            'character_common_phrases',
            'character_emotional_patterns'
        ]
        
        for table in tables:
            await conn.execute(f"DELETE FROM {table} WHERE character_id = $1", char_id)
    
    async def _import_values(self, conn: asyncpg.Connection, char_id: int, values: List[Dict[str, str]]) -> None:
        """Import character values"""
        for value in values:
            if isinstance(value, dict):
                await conn.execute("""
                    INSERT INTO character_values (character_id, value_key, value_description)
                    VALUES ($1, $2, $3)
                """, char_id, value.get('key', ''), value.get('description', ''))
            elif isinstance(value, str):
                # Handle string format "key: description"
                if ':' in value:
                    key, desc = value.split(':', 1)
                    await conn.execute("""
                        INSERT INTO character_values (character_id, value_key, value_description)
                        VALUES ($1, $2, $3)
                    """, char_id, key.strip(), desc.strip())
    
    async def _import_interests(self, conn: asyncpg.Connection, char_id: int, interests: List[str]) -> None:
        """Import character interests"""
        for interest in interests:
            await conn.execute("""
                INSERT INTO character_interest_topics (character_id, topic_keyword)
                VALUES ($1, $2)
            """, char_id, interest)
    
    async def _import_identity_details(self, conn: asyncpg.Connection, char_id: int, identity: Dict[str, Any]) -> None:
        """Import identity details"""
        # Check if record exists
        existing = await conn.fetchrow(
            "SELECT character_id FROM character_identity_details WHERE character_id = $1",
            char_id
        )
        
        if existing:
            # Update existing
            await conn.execute("""
                UPDATE character_identity_details
                SET age = $2, gender = $3, location = $4, timezone = $5, nickname = $6, full_name = $7,
                    height = $8, build = $9, hair_color = $10, eye_color = $11, style = $12,
                    distinctive_features = $13, appearance_description = $14
                WHERE character_id = $1
            """,
                char_id,
                identity.get('age'),
                identity.get('gender'),
                identity.get('location'),
                identity.get('timezone'),
                identity.get('nickname'),
                identity.get('full_name'),
                identity.get('height'),
                identity.get('build'),
                identity.get('hair_color'),
                identity.get('eye_color'),
                identity.get('style'),
                identity.get('distinctive_features'),
                identity.get('appearance_description')
            )
        else:
            # Insert new
            await conn.execute("""
                INSERT INTO character_identity_details
                (character_id, age, gender, location, timezone, nickname, full_name,
                 height, build, hair_color, eye_color, style, distinctive_features, appearance_description)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """,
                char_id,
                identity.get('age'),
                identity.get('gender'),
                identity.get('location'),
                identity.get('timezone'),
                identity.get('nickname'),
                identity.get('full_name'),
                identity.get('height'),
                identity.get('build'),
                identity.get('hair_color'),
                identity.get('eye_color'),
                identity.get('style'),
                identity.get('distinctive_features'),
                identity.get('appearance_description')
            )
    
    async def _import_personality(self, conn: asyncpg.Connection, char_id: int, personality: Dict[str, Any]) -> None:
        """Import personality traits"""
        # Import Big Five if present
        if 'big_five' in personality:
            big_five = personality['big_five']
            
            existing = await conn.fetchrow(
                "SELECT character_id FROM character_big_five_personality WHERE character_id = $1",
                char_id
            )
            
            if existing:
                await conn.execute("""
                    UPDATE character_big_five_personality
                    SET openness = $2, conscientiousness = $3, extraversion = $4, agreeableness = $5, neuroticism = $6
                    WHERE character_id = $1
                """,
                    char_id,
                    big_five.get('openness'),
                    big_five.get('conscientiousness'),
                    big_five.get('extraversion'),
                    big_five.get('agreeableness'),
                    big_five.get('neuroticism')
                )
            else:
                await conn.execute("""
                    INSERT INTO character_big_five_personality
                    (character_id, openness, conscientiousness, extraversion, agreeableness, neuroticism)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    char_id,
                    big_five.get('openness'),
                    big_five.get('conscientiousness'),
                    big_five.get('extraversion'),
                    big_five.get('agreeableness'),
                    big_five.get('neuroticism')
                )
        
        # Import general traits
        if 'traits' in personality:
            for trait_name, trait_value in personality['traits'].items():
                await conn.execute("""
                    INSERT INTO character_personality_traits (character_id, trait_name, trait_value)
                    VALUES ($1, $2, $3)
                """, char_id, trait_name, trait_value)
    
    async def _import_communication(self, conn: asyncpg.Connection, char_id: int, communication: Dict[str, Any]) -> None:
        """Import communication patterns"""
        # Import typical responses
        if 'typical_responses' in communication:
            for scenario, responses in communication['typical_responses'].items():
                if isinstance(responses, list):
                    for response in responses:
                        await conn.execute("""
                            INSERT INTO character_typical_responses (character_id, scenario_type, response_text)
                            VALUES ($1, $2, $3)
                        """, char_id, scenario, response)
        
        # Import emotional expressions
        if 'emotional_expressions' in communication:
            for emotion, expression in communication['emotional_expressions'].items():
                await conn.execute("""
                    INSERT INTO character_emotional_expressions (character_id, emotion_type, expression_text)
                    VALUES ($1, $2, $3)
                """, char_id, emotion, expression)
    
    async def _import_background(self, conn: asyncpg.Connection, char_id: int, background: Dict[str, Any]) -> None:
        """Import background/backstory"""
        if 'life_phases' in background:
            for phase in background['life_phases']:
                await conn.execute("""
                    INSERT INTO character_life_phases (character_id, phase_name, age_range, key_events, emotional_impact)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    char_id,
                    phase.get('phase_name'),
                    phase.get('age_range'),
                    phase.get('key_events'),
                    phase.get('emotional_impact')
                )
    
    async def _import_relationships(self, conn: asyncpg.Connection, char_id: int, relationships: List[Dict[str, Any]]) -> None:
        """Import relationships"""
        for rel in relationships:
            await conn.execute("""
                INSERT INTO character_relationships (character_id, person_name, relationship_type, description, emotional_significance)
                VALUES ($1, $2, $3, $4, $5)
            """,
                char_id,
                rel.get('person_name'),
                rel.get('relationship_type'),
                rel.get('description'),
                rel.get('emotional_significance')
            )
    
    async def _import_behavioral_patterns(self, conn: asyncpg.Connection, char_id: int, patterns: Dict[str, Any]) -> None:
        """Import behavioral patterns"""
        for pattern_type, pattern_list in patterns.items():
            if isinstance(pattern_list, list):
                for pattern in pattern_list:
                    await conn.execute("""
                        INSERT INTO character_behavioral_patterns (character_id, pattern_type, pattern_description)
                        VALUES ($1, $2, $3)
                    """, char_id, pattern_type, pattern)
    
    async def _import_speech_patterns(self, conn: asyncpg.Connection, char_id: int, speech: Dict[str, Any]) -> None:
        """Import speech patterns"""
        # Import voice characteristics
        if 'voice' in speech:
            voice = speech['voice']
            
            existing = await conn.fetchrow(
                "SELECT character_id FROM character_voice_characteristics WHERE character_id = $1",
                char_id
            )
            
            if existing:
                await conn.execute("""
                    UPDATE character_voice_characteristics
                    SET tone = $2, pace = $3, volume = $4, accent = $5, vocabulary_level = $6
                    WHERE character_id = $1
                """,
                    char_id,
                    voice.get('tone'),
                    voice.get('pace'),
                    voice.get('volume'),
                    voice.get('accent'),
                    voice.get('vocabulary_level')
                )
            else:
                await conn.execute("""
                    INSERT INTO character_voice_characteristics
                    (character_id, tone, pace, volume, accent, vocabulary_level)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    char_id,
                    voice.get('tone'),
                    voice.get('pace'),
                    voice.get('volume'),
                    voice.get('accent'),
                    voice.get('vocabulary_level')
                )
        
        # Import common phrases
        if 'common_phrases' in speech:
            for phrase_data in speech['common_phrases']:
                if isinstance(phrase_data, dict):
                    await conn.execute("""
                        INSERT INTO character_common_phrases (character_id, phrase_text, usage_context)
                        VALUES ($1, $2, $3)
                    """, char_id, phrase_data.get('phrase'), phrase_data.get('context'))
    
    async def _import_emotional_profile(self, conn: asyncpg.Connection, char_id: int, profile: Dict[str, Any]) -> None:
        """Import emotional profile"""
        if 'emotional_patterns' in profile:
            for pattern in profile['emotional_patterns']:
                await conn.execute("""
                    INSERT INTO character_emotional_patterns (character_id, emotion_type, intensity, triggers, typical_response)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    char_id,
                    pattern.get('emotion_type'),
                    pattern.get('intensity'),
                    pattern.get('triggers'),
                    pattern.get('typical_response')
                )


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='CDL YAML Manager - Export and Import Character Definitions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export single character
  python scripts/cdl_yaml_manager.py export elena
  
  # Export all characters
  python scripts/cdl_yaml_manager.py export --all
  
  # Import single character
  python scripts/cdl_yaml_manager.py import backups/characters_yaml/2025-10-12/elena.yaml
  
  # Import all from directory
  python scripts/cdl_yaml_manager.py import backups/characters_yaml/2025-10-12/ --all
  
  # Overwrite existing character
  python scripts/cdl_yaml_manager.py import elena.yaml --overwrite
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export character(s) to YAML')
    export_parser.add_argument('character', nargs='?', help='Character normalized name (e.g., elena, marcus)')
    export_parser.add_argument('--all', action='store_true', help='Export all active characters')
    export_parser.add_argument('--output', type=Path, help='Custom output path')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import character(s) from YAML')
    import_parser.add_argument('path', type=Path, help='Path to YAML file or directory')
    import_parser.add_argument('--all', action='store_true', help='Import all YAML files from directory')
    import_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing character data')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = CDLYAMLManager()
    
    if args.command == 'export':
        if args.all:
            asyncio.run(manager.export_all_characters())
        elif args.character:
            asyncio.run(manager.export_character(args.character, args.output))
        else:
            print("❌ Please specify a character name or use --all")
            export_parser.print_help()
    
    elif args.command == 'import':
        if args.all:
            if not args.path.is_dir():
                print("❌ Path must be a directory when using --all")
                return
            asyncio.run(manager.import_all_from_directory(args.path, args.overwrite))
        else:
            if not args.path.is_file():
                print("❌ Path must be a YAML file")
                return
            asyncio.run(manager.import_character(args.path, args.overwrite))


if __name__ == '__main__':
    main()
