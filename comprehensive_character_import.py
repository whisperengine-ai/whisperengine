#!/usr/bin/env python3
"""
Comprehensive Character Import Script
WhisperEngine CDL System - Rich Data Import
Version: 2.0 - October 2025

Imports rich character data from JSON files into comprehensive RDBMS schema.
Populates appearance, background, abilities, memories, communication patterns, etc.
"""

import os
import json
import asyncio
import asyncpg
from pathlib import Path
from typing import Dict, Any, List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveCharacterImporter:
    """Import rich character data from JSON files to comprehensive RDBMS schema"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.json_dir = Path("characters/examples_legacy_backup")
        
    async def import_all_characters(self):
        """Import all character JSON files to rich schema"""
        json_files = list(self.json_dir.glob("*.json"))
        
        # Group files by base character name to avoid duplicates
        character_files = {}
        for json_file in json_files:
            filename = json_file.stem
            
            # Extract base character name (elena from elena.backup_20251006_223336)
            base_name = filename.split('.')[0].lower()
            
            # Skip non-character files
            if any(skip_pattern in filename.lower() for skip_pattern in ['template', 'example', 'test']):
                logger.info(f"Skipping non-character file: {filename}")
                continue
                
            if base_name not in character_files:
                character_files[base_name] = []
            character_files[base_name].append(json_file)
        
        logger.info(f"Found {len(character_files)} unique characters with {sum(len(files) for files in character_files.values())} total files")
        
        for base_name, files in character_files.items():
            if len(files) > 1:
                logger.info(f"Character '{base_name}' has {len(files)} files - will merge data")
            
            # Import all files for this character (they'll merge into the same character record)
            for json_file in files:
                file_stem = json_file.stem
                logger.info(f"Importing rich data from {file_stem} for character '{base_name}'...")
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        character_data = json.load(f)
                    
                    # Use the base character name for database lookup, not the filename
                    await self.import_character_rich_data(base_name, character_data)
                    logger.info(f"✅ Successfully imported rich data from {file_stem}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to import {file_stem}: {e}")
    
    async def import_character_rich_data(self, character_name: str, json_data: Dict[str, Any]):
        """Import rich character data from JSON structure"""
        async with self.pool.acquire() as conn:
            # Get character ID
            char_row = await conn.fetchrow("SELECT id FROM characters WHERE LOWER(name) = LOWER($1)", character_name)
            if not char_row:
                logger.warning(f"Character '{character_name}' not found in database - skipping")
                return
            
            character_id = char_row['id']
            
            # Handle different JSON structures (Elena vs Marcus format)
            if 'character' in json_data:
                # Marcus format
                char_data = json_data['character']
            else:
                # Elena format
                char_data = json_data
            
            # Import different data types
            await self._import_appearance_data(conn, character_id, char_data)
            await self._import_background_data(conn, character_id, char_data)
            await self._import_abilities_data(conn, character_id, char_data)
            await self._import_communication_patterns(conn, character_id, char_data)
            await self._import_essence_data(conn, character_id, char_data)
            await self._import_instruction_data(conn, character_id, char_data)
            await self._import_metadata(conn, character_id, json_data, character_name)
    
    async def _import_appearance_data(self, conn: asyncpg.Connection, character_id: int, char_data: Dict[str, Any]):
        """Import physical and digital appearance data (merge with existing)"""
        try:
            # Physical appearance
            if 'physical_appearance' in char_data:
                physical = char_data['physical_appearance']
                for key, value in physical.items():
                    if value:  # Only import non-empty values
                        await conn.execute("""
                            INSERT INTO character_appearance (character_id, category, attribute, value)
                            VALUES ($1, 'physical', $2, $3)
                            ON CONFLICT (character_id, category, attribute) 
                            DO UPDATE SET value = CASE 
                                WHEN LENGTH($3) > LENGTH(character_appearance.value) 
                                THEN $3 
                                ELSE character_appearance.value 
                            END
                        """, character_id, key, str(value))
            
            # Digital communication style as appearance
            if 'digital_communication' in char_data:
                digital = char_data['digital_communication']
                for key, value in digital.items():
                    if value:
                        await conn.execute("""
                            INSERT INTO character_appearance (character_id, category, attribute, value)
                            VALUES ($1, 'digital', $2, $3)
                            ON CONFLICT (character_id, category, attribute) 
                            DO UPDATE SET value = CASE 
                                WHEN LENGTH($3) > LENGTH(character_appearance.value) 
                                THEN $3 
                                ELSE character_appearance.value 
                            END
                        """, character_id, key, str(value))
        
        except Exception as e:
            logger.error(f"Error importing appearance data: {e}")
    
    async def _import_background_data(self, conn: asyncpg.Connection, character_id: int, char_data: Dict[str, Any]):
        """Import background and history data"""
        try:
            if 'background' in char_data:
                background = char_data['background']
                
                # Education
                if 'education' in background:
                    education = background['education']
                    if isinstance(education, list):
                        for i, edu in enumerate(education):
                            await conn.execute("""
                                INSERT INTO character_background 
                                (character_id, category, title, description, importance_level)
                                VALUES ($1, 'education', $2, $3, $4)
                            """, character_id, f"Education {i+1}", str(edu), 8)
                    elif isinstance(education, str):
                        await conn.execute("""
                            INSERT INTO character_background 
                            (character_id, category, title, description, importance_level)
                            VALUES ($1, 'education', 'Education', $2, 8)
                        """, character_id, education)
                
                # Career history
                if 'career_history' in background:
                    career = background['career_history']
                    if isinstance(career, list):
                        for i, job in enumerate(career):
                            await conn.execute("""
                                INSERT INTO character_background 
                                (character_id, category, title, description, importance_level)
                                VALUES ($1, 'career', $2, $3, $4)
                            """, character_id, f"Career {i+1}", str(job), 7)
                    elif isinstance(career, str):
                        await conn.execute("""
                            INSERT INTO character_background 
                            (character_id, category, title, description, importance_level)
                            VALUES ($1, 'career', 'Career History', $2, 7)
                        """, character_id, career)
                
                # Personal history
                if 'personal_history' in background:
                    personal = background['personal_history']
                    await conn.execute("""
                        INSERT INTO character_background 
                        (character_id, category, title, description, importance_level)
                        VALUES ($1, 'personal', 'Personal History', $2, 6)
                    """, character_id, str(personal))
                
                # Cultural background
                if 'cultural_background' in background:
                    cultural = background['cultural_background']
                    await conn.execute("""
                        INSERT INTO character_background 
                        (character_id, category, title, description, importance_level)
                        VALUES ($1, 'cultural', 'Cultural Background', $2, 5)
                    """, character_id, str(cultural))
        
        except Exception as e:
            logger.error(f"Error importing background data: {e}")
    
    async def _import_abilities_data(self, conn: asyncpg.Connection, character_id: int, char_data: Dict[str, Any]):
        """Import abilities and skills data"""
        try:
            # Mystical abilities
            if 'mystical_abilities' in char_data:
                abilities = char_data['mystical_abilities']
                if isinstance(abilities, list):
                    for ability in abilities:
                        await conn.execute("""
                            INSERT INTO character_abilities 
                            (character_id, category, ability_name, proficiency_level, description)
                            VALUES ($1, 'mystical', $2, $3, $4)
                            ON CONFLICT (character_id, category, ability_name) 
                            DO UPDATE SET proficiency_level = $3, description = $4
                        """, character_id, str(ability)[:100], 9, str(ability))
                elif isinstance(abilities, dict):
                    for name, desc in abilities.items():
                        await conn.execute("""
                            INSERT INTO character_abilities 
                            (character_id, category, ability_name, proficiency_level, description)
                            VALUES ($1, 'mystical', $2, $3, $4)
                            ON CONFLICT (character_id, category, ability_name) 
                            DO UPDATE SET proficiency_level = $3, description = $4
                        """, character_id, name[:100], 9, str(desc))
            
            # Professional skills (inferred from occupation)
            if 'identity' in char_data and 'occupation' in char_data['identity']:
                occupation = char_data['identity']['occupation']
                if occupation:
                    await conn.execute("""
                        INSERT INTO character_abilities 
                        (character_id, category, ability_name, proficiency_level, description)
                        VALUES ($1, 'professional', $2, $3, $4)
                        ON CONFLICT (character_id, category, ability_name) 
                        DO UPDATE SET proficiency_level = $3, description = $4
                    """, character_id, occupation[:100], 10, f"Expert-level skills in {occupation}")
        
        except Exception as e:
            logger.error(f"Error importing abilities data: {e}")
    
    async def _import_communication_patterns(self, conn: asyncpg.Connection, character_id: int, char_data: Dict[str, Any]):
        """Import communication patterns and preferences"""
        try:
            # Digital communication patterns
            if 'digital_communication' in char_data:
                digital = char_data['digital_communication']
                for pattern_name, pattern_value in digital.items():
                    if pattern_value:
                        await conn.execute("""
                            INSERT INTO character_communication_patterns 
                            (character_id, pattern_type, pattern_name, pattern_value, frequency)
                            VALUES ($1, 'digital', $2, $3, 'regular')
                            ON CONFLICT (character_id, pattern_type, pattern_name) 
                            DO UPDATE SET pattern_value = $3
                        """, character_id, pattern_name, str(pattern_value))
            
            # Communication style as patterns
            if 'communication' in char_data or 'communication_style' in char_data:
                comm_data = char_data.get('communication', char_data.get('communication_style', {}))
                for style_name, style_data in comm_data.items():
                    if isinstance(style_data, dict) and 'value' in style_data:
                        await conn.execute("""
                            INSERT INTO character_communication_patterns 
                            (character_id, pattern_type, pattern_name, pattern_value, description)
                            VALUES ($1, 'style', $2, $3, $4)
                            ON CONFLICT (character_id, pattern_type, pattern_name) 
                            DO UPDATE SET pattern_value = $3, description = $4
                        """, character_id, style_name, str(style_data['value']), 
                             style_data.get('description', ''))
        
        except Exception as e:
            logger.error(f"Error importing communication patterns: {e}")
    
    async def _import_essence_data(self, conn: asyncpg.Connection, character_id: int, char_data: Dict[str, Any]):
        """Import essence and core identity data (for mystical characters)"""
        try:
            if 'essence' in char_data:
                essence = char_data['essence']
                for essence_type, essence_data in essence.items():
                    if isinstance(essence_data, str):
                        await conn.execute("""
                            INSERT INTO character_essence 
                            (character_id, essence_type, essence_name, description)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (character_id, essence_type, essence_name) 
                            DO UPDATE SET description = $4
                        """, character_id, essence_type, essence_type, essence_data)
                    elif isinstance(essence_data, dict):
                        for name, desc in essence_data.items():
                            await conn.execute("""
                                INSERT INTO character_essence 
                                (character_id, essence_type, essence_name, description)
                                VALUES ($1, $2, $3, $4)
                                ON CONFLICT (character_id, essence_type, essence_name) 
                                DO UPDATE SET description = $4
                            """, character_id, essence_type, name, str(desc))
        
        except Exception as e:
            logger.error(f"Error importing essence data: {e}")
    
    async def _import_instruction_data(self, conn: asyncpg.Connection, character_id: int, char_data: Dict[str, Any]):
        """Import custom instructions and overrides"""
        try:
            # Custom introduction
            if 'custom_introduction' in char_data:
                intro = char_data['custom_introduction']
                await conn.execute("""
                    INSERT INTO character_instructions 
                    (character_id, instruction_type, instruction_text, priority)
                    VALUES ($1, 'introduction', $2, 9)
                """, character_id, str(intro))
            
            # Character override instructions
            if 'character_override_instructions' in char_data:
                override = char_data['character_override_instructions']
                await conn.execute("""
                    INSERT INTO character_instructions 
                    (character_id, instruction_type, instruction_text, priority)
                    VALUES ($1, 'override', $2, 10)
                """, character_id, str(override))
        
        except Exception as e:
            logger.error(f"Error importing instruction data: {e}")
    
    async def _import_metadata(self, conn: asyncpg.Connection, character_id: int, json_data: Dict[str, Any], character_name: str):
        """Import character metadata"""
        try:
            # Extract metadata from JSON
            metadata = json_data.get('metadata', {})
            character_id_meta = metadata.get('character_id', character_name)
            version = metadata.get('version', 1)
            tags = metadata.get('tags', ['json_import'])
            
            # Update metadata if it exists, insert if it doesn't
            await conn.execute("""
                INSERT INTO character_metadata 
                (character_id, version, character_tags, author, notes)
                VALUES ($1, $2, $3, 'JSON Import', $4)
                ON CONFLICT (character_id, version) 
                DO UPDATE SET character_tags = $3, notes = $4, updated_date = CURRENT_TIMESTAMP
            """, character_id, version, tags, f"Imported from {character_name}.json with rich data")
        
        except Exception as e:
            logger.error(f"Error importing metadata: {e}")

async def main():
    """Main import process"""
    # Database connection
    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'whisperengine')}:{os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'whisperengine')}"
    
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        importer = ComprehensiveCharacterImporter(pool)
        
        print("🚀 Starting comprehensive character import...")
        await importer.import_all_characters()
        print("✅ Comprehensive character import complete!")
        
        # Test the enhanced manager
        print("\n🧪 Testing enhanced CDL manager...")
        from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
        
        manager = create_enhanced_cdl_manager(pool)
        elena_data = await manager.get_character_by_name('elena')
        
        if elena_data:
            print("✅ Enhanced manager test successful!")
            print(f"   Core CDL keys: {list(elena_data.keys())}")
            
            # Show rich data preview
            if 'appearance' in elena_data:
                print(f"   🎭 Appearance categories: {list(elena_data['appearance'].keys())}")
            if 'background' in elena_data:
                print(f"   📚 Background categories: {list(elena_data['background'].keys())}")
            if 'abilities' in elena_data:
                print(f"   💪 Abilities categories: {list(elena_data['abilities'].keys())}")
            if 'communication_patterns' in elena_data:
                print(f"   💬 Communication patterns: {list(elena_data['communication_patterns'].keys())}")
            if 'custom_instructions' in elena_data:
                print(f"   📋 Custom instructions: {list(elena_data['custom_instructions'].keys())}")
        else:
            print("❌ Enhanced manager test failed")
        
        await pool.close()
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())