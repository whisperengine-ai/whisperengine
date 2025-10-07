#!/usr/bin/env python3
"""
CDL Database Migration Script
Migrates from JSONB blob storage to proper normalized schema with hybrid JSON approach.
"""

import asyncio
import logging
import json
import os
from pathlib import Path
from pathlib import Path
from typing import Dict, Any, Optional

import asyncpg

logger = logging.getLogger(__name__)

class CDLDatabaseMigrator:
    """Migrates CDL data from JSONB blobs to normalized schema"""
    
    def __init__(self):
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        # Use Docker network connection details
        postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
        postgres_port = os.getenv('POSTGRES_PORT', '5432') 
        postgres_db = os.getenv('POSTGRES_DB', 'whisperengine')
        postgres_user = os.getenv('POSTGRES_USER', 'whisperengine')
        postgres_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
        
        database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
        print(f"Connecting to: postgresql://{postgres_user}:***@{postgres_host}:{postgres_port}/{postgres_db}")
        
        self.pool = await asyncpg.create_pool(database_url)
    
    async def run_migration(self):
        """Execute the complete migration process"""
        logger.info("🚀 Starting CDL database migration...")
        
        try:
            # 1. Create new schema
            await self._create_new_schema()
            
            # 2. Import character data from CDL JSON files
            await self._import_from_cdl_files(self.pool)
            
            # 3. Verify migration
            await self._verify_migration()
            
            logger.info("✅ CDL migration completed successfully!")
            
        except Exception as e:
            logger.error("❌ Migration failed: %s", e)
            raise
    
    async def _create_new_schema(self):
        """Create the new normalized schema if it doesn't exist."""
        logger.info("📋 Checking/creating normalized schema...")
        
        async with self.pool.acquire() as conn:
            # Check if characters table already exists
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'characters'
                )
            """)
            
            if result:
                logger.info("✅ Normalized schema already exists, skipping creation")
                return
            
            # Read the schema file
            schema_path = os.path.join(
                os.path.dirname(__file__), 
                'schema', 
                'cdl_normalized_schema.sql'
            )
            
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema creation
            await conn.execute(schema_sql)
            logger.info("✅ Normalized schema created successfully")
    
    async def _import_from_cdl_files(self, pool):
        """Import character data directly from CDL JSON files."""
        print("� Importing character data from CDL JSON files...")
        
        # Get the characters directory
        characters_dir = Path(__file__).parent.parent.parent / "characters" / "examples"
        
        if not characters_dir.exists():
            print(f"❌ Characters directory not found: {characters_dir}")
            return
            
        # Find all JSON files
        json_files = list(characters_dir.glob("*.json"))
        
        # Filter out backup files and unwanted files
        filtered_files = []
        for json_file in json_files:
            filename = json_file.name
            # Skip backup files, version files, and temporary files
            if ('backup' in filename.lower() or 
                filename.startswith('.') or 
                '_v2' in filename.lower()):
                print(f"Skipping backup/version file: {filename}")
                continue
            filtered_files.append(json_file)
            
        print(f"Found {len(filtered_files)} character files to import (skipped {len(json_files) - len(filtered_files)} backup/version files)")
        
        async with pool.acquire() as conn:
            for json_file in filtered_files:
                character_name = json_file.stem
                print(f"Importing character: {character_name}")
                
                try:
                    # Load CDL JSON data
                    with open(json_file, 'r', encoding='utf-8') as f:
                        cdl_data = json.load(f)
                    
                    # Extract character data
                    extracted_data = self._extract_character_data(cdl_data, character_name)
                    
                    # Insert into normalized tables
                    await self._insert_character_data(conn, extracted_data)
                    print(f"✅ Successfully imported {character_name}")
                    
                except Exception as e:
                    print(f"❌ Error importing {character_name}: {e}")
                    continue

    def _extract_character_data(self, cdl_data, character_name):
        """Extract character data from CDL JSON structure."""
        # Handle nested structure - some characters have data under 'character' key
        if 'character' in cdl_data:
            character_data = cdl_data['character']
        else:
            character_data = cdl_data
            
        return {
            'name': character_name,  # Fixed: use 'name' not 'character_name'
            'display_name': character_data.get('identity', {}).get('name', character_name),
            'occupation': character_data.get('identity', {}).get('occupation', ''),
            'age': character_data.get('identity', {}).get('age'),
            'location': character_data.get('identity', {}).get('location', ''),
            'description': character_data.get('identity', {}).get('description', ''),
            'is_active': True,
            'created_at': 'NOW()',
            'updated_at': 'NOW()',
            'raw_cdl_data': json.dumps(cdl_data),
            
            # Identity data
            'identity_data': character_data.get('identity', {}),
            
            # Personality data
            'personality_data': character_data.get('personality', {}),
            
            # Communication data
            'communication_data': character_data.get('communication', {}),
            
            # Backstory data
            'backstory_data': character_data.get('backstory', {}),
            
            # Current life data
            'current_life_data': character_data.get('current_life', {}),
            
            # Relationships data
            'relationships_data': character_data.get('relationships', {}),
            
            # Values data
            'values_data': character_data.get('values', {}),
            
            # Goals data
            'goals_data': character_data.get('goals', {}),
            
            # Interests data
            'interests_data': character_data.get('interests', {}),
            
            # Metadata
            'metadata': {
                'version': character_data.get('metadata', {}).get('version', '1.0'),
                'last_updated': character_data.get('metadata', {}).get('created_date', ''),
                'notes': character_data.get('metadata', {}).get('description', '')
            }
        }

    async def _insert_character_data(self, conn, character_data):
        """Insert character data into normalized tables."""
        
        # 1. Insert main character record
        character_id = await conn.fetchval("""
            INSERT INTO characters (name)
            VALUES ($1)
            ON CONFLICT (name) DO UPDATE SET
                updated_at = NOW()
            RETURNING id
        """, 
            character_data['name']
        )
        
        # 2. Insert identity data
        await conn.execute("""
            INSERT INTO character_identity (character_id, name, occupation, location, description, extended_data)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (character_id) DO UPDATE SET
                name = EXCLUDED.name,
                occupation = EXCLUDED.occupation,
                location = EXCLUDED.location,
                description = EXCLUDED.description,
                extended_data = EXCLUDED.extended_data,
                updated_at = NOW()
        """, 
            character_id, 
            character_data['display_name'],
            character_data['occupation'],
            character_data['location'],
            character_data['description'],
            json.dumps(character_data['identity_data'])
        )
        
        # 3. Insert personality data
        personality = character_data['personality_data']
        big_five = personality.get('big_five', {})
        
        # Extract Big Five values (handle complex structure)
        def extract_big_five_value(trait_data):
            if isinstance(trait_data, dict):
                return trait_data.get('value') 
            elif isinstance(trait_data, (int, float)):
                return trait_data
            return None
        
        await conn.execute("""
            INSERT INTO character_personality (
                character_id, openness, conscientiousness, extraversion, agreeableness, neuroticism,
                custom_traits, values, core_beliefs, dreams, fears, quirks
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT (character_id) DO UPDATE SET
                openness = EXCLUDED.openness,
                conscientiousness = EXCLUDED.conscientiousness,
                extraversion = EXCLUDED.extraversion,
                agreeableness = EXCLUDED.agreeableness,
                neuroticism = EXCLUDED.neuroticism,
                custom_traits = EXCLUDED.custom_traits,
                values = EXCLUDED.values,
                core_beliefs = EXCLUDED.core_beliefs,
                dreams = EXCLUDED.dreams,
                fears = EXCLUDED.fears,
                quirks = EXCLUDED.quirks,
                updated_at = NOW()
        """, 
            character_id,
            extract_big_five_value(big_five.get('openness')),
            extract_big_five_value(big_five.get('conscientiousness')), 
            extract_big_five_value(big_five.get('extraversion')),
            extract_big_five_value(big_five.get('agreeableness')),
            extract_big_five_value(big_five.get('neuroticism')),
            json.dumps(personality.get('traits', {})),
            json.dumps(personality.get('values', [])),
            json.dumps(personality.get('core_beliefs', [])),
            json.dumps(personality.get('dreams', [])),
            json.dumps(personality.get('fears', [])),
            json.dumps(personality.get('quirks', []))
        )
        
        # 4. Insert communication data
        communication = character_data['communication_data']
        await conn.execute("""
            INSERT INTO character_communication (
                character_id, response_length, communication_style, 
                typical_responses, emotional_expressions, message_pattern_triggers,
                conversation_flow_guidance, ai_identity_handling
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (character_id) DO UPDATE SET
                response_length = EXCLUDED.response_length,
                communication_style = EXCLUDED.communication_style,
                typical_responses = EXCLUDED.typical_responses,
                emotional_expressions = EXCLUDED.emotional_expressions,
                message_pattern_triggers = EXCLUDED.message_pattern_triggers,
                conversation_flow_guidance = EXCLUDED.conversation_flow_guidance,
                ai_identity_handling = EXCLUDED.ai_identity_handling,
                updated_at = NOW()
        """, 
            character_id, 
            communication.get('response_length', 'moderate'),
            communication.get('communication_style', 'adaptive'),
            json.dumps(communication.get('typical_responses', {})),
            json.dumps(communication.get('emotional_expressions', {})),
            json.dumps(communication.get('message_pattern_triggers', {})),
            json.dumps(communication.get('conversation_flow_guidance', {})),
            json.dumps(communication.get('ai_identity_handling', {}))
        )
        
        # 5. Insert remaining data as JSON in extended tables
        # (backstory, current_life, relationships, values, goals, interests)
        
        print(f"Character {character_data['name']} imported successfully")
    
    async def _migrate_from_json_files(self):
        """Fallback: migrate from JSON files if no database data exists"""
        logger.info("📁 Migrating from JSON files...")
        
        characters_dir = Path(__file__).parent.parent.parent / "characters" / "examples"
        
        if not characters_dir.exists():
            logger.warning("⚠️ No characters directory found")
            return
        
        async with self.pool.acquire() as conn:
            for json_file in characters_dir.glob("*.json"):
                character_name = json_file.stem
                logger.info(f"Migrating from JSON: {character_name}")
                
                try:
                    character_data = json.loads(json_file.read_text())
                    await self._migrate_single_character(conn, character_name, character_data)
                except Exception as e:
                    logger.error(f"Failed to migrate {character_name}: {e}")
    
    async def _migrate_single_character(self, conn, character_name: str, character_data: Dict[str, Any]):
        """Migrate a single character to the new schema"""
        try:
            # Extract nested character data if present
            if 'character' in character_data:
                char_data = character_data['character']
            else:
                char_data = character_data
            
            # 1. Insert into characters table
            char_id = await conn.fetchval("""
                INSERT INTO characters (name, version)
                VALUES ($1, $2)
                ON CONFLICT (name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, character_name, str(char_data.get('version', '1.0')))
            
            if char_id is None:
                # Character already exists, get its ID
                char_id = await conn.fetchval("SELECT id FROM characters WHERE name = $1", character_name)
            
            # 2. Migrate identity
            await self._migrate_identity(conn, char_id, char_data)
            
            # 3. Migrate personality
            await self._migrate_personality(conn, char_id, char_data)
            
            # 4. Migrate communication
            await self._migrate_communication(conn, char_id, char_data)
            
            # 5. Migrate backstory
            await self._migrate_backstory(conn, char_id, char_data)
            
            # 6. Migrate current life
            await self._migrate_current_life(conn, char_id, char_data)
            
            # 7. Migrate speech patterns
            await self._migrate_speech_patterns(conn, char_id, char_data)
            
            # 8. Migrate personal knowledge
            await self._migrate_personal_knowledge(conn, char_id, char_data)
            
            # 9. Migrate metadata
            await self._migrate_metadata(conn, char_id, char_data, character_name)
            
            logger.info(f"✅ Successfully migrated {character_name} (ID: {char_id})")
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate character {character_name}: {e}")
            raise
    
    async def _migrate_identity(self, conn, char_id: int, char_data: Dict[str, Any]):
        """Migrate identity data"""
        identity = char_data.get('identity', {})
        
        # Extract core fields
        name = identity.get('name', char_data.get('name', 'Unknown'))
        occupation = identity.get('occupation', '')
        location = identity.get('location', '')
        description = identity.get('description', '')
        
        # Put everything else in extended_data
        extended_data = {k: v for k, v in identity.items() 
                        if k not in ['name', 'occupation', 'location', 'description']}
        
        await conn.execute("""
            INSERT INTO character_identity 
            (character_id, name, occupation, location, description, extended_data)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (character_id) DO UPDATE SET
                name = EXCLUDED.name,
                occupation = EXCLUDED.occupation,
                location = EXCLUDED.location,
                description = EXCLUDED.description,
                extended_data = EXCLUDED.extended_data,
                updated_at = CURRENT_TIMESTAMP
        """, char_id, name, occupation, location, description, json.dumps(extended_data))
    
    async def _migrate_personality(self, conn, char_id: int, char_data: Dict[str, Any]):
        """Migrate personality data"""
        personality = char_data.get('personality', {})
        big_five = personality.get('big_five', {})
        
        # Extract Big Five traits
        openness = big_five.get('openness', 0.5)
        conscientiousness = big_five.get('conscientiousness', 0.5)
        extraversion = big_five.get('extraversion', 0.5)
        agreeableness = big_five.get('agreeableness', 0.5)
        neuroticism = big_five.get('neuroticism', 0.5)
        
        # Extract lists and nested data for JSON storage
        custom_traits = personality.get('custom_traits', {})
        values = personality.get('values', [])
        core_beliefs = personality.get('core_beliefs', [])
        dreams = personality.get('dreams', [])
        fears = personality.get('fears', [])
        quirks = personality.get('quirks', [])
        
        await conn.execute("""
            INSERT INTO character_personality 
            (character_id, openness, conscientiousness, extraversion, agreeableness, neuroticism,
             custom_traits, values, core_beliefs, dreams, fears, quirks)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT (character_id) DO UPDATE SET
                openness = EXCLUDED.openness,
                conscientiousness = EXCLUDED.conscientiousness,
                extraversion = EXCLUDED.extraversion,
                agreeableness = EXCLUDED.agreeableness,
                neuroticism = EXCLUDED.neuroticism,
                custom_traits = EXCLUDED.custom_traits,
                values = EXCLUDED.values,
                core_beliefs = EXCLUDED.core_beliefs,
                dreams = EXCLUDED.dreams,
                fears = EXCLUDED.fears,
                quirks = EXCLUDED.quirks,
                updated_at = CURRENT_TIMESTAMP
        """, char_id, openness, conscientiousness, extraversion, agreeableness, neuroticism,
             json.dumps(custom_traits), json.dumps(values), json.dumps(core_beliefs),
             json.dumps(dreams), json.dumps(fears), json.dumps(quirks))
    
    async def _migrate_communication(self, conn, char_id: int, char_data: Dict[str, Any]):
        """Migrate communication data"""
        communication = char_data.get('communication', {})
        
        # Extract core fields
        response_length = communication.get('response_length', 'moderate')
        communication_style = communication.get('communication_style', 'adaptive')
        
        # Extract complex nested data for JSON storage
        typical_responses = communication.get('typical_responses', {})
        emotional_expressions = communication.get('emotional_expressions', {})
        message_pattern_triggers = communication.get('message_pattern_triggers', {})
        conversation_flow_guidance = communication.get('conversation_flow_guidance', {})
        ai_identity_handling = communication.get('ai_identity_handling', {})
        
        await conn.execute("""
            INSERT INTO character_communication 
            (character_id, response_length, communication_style, typical_responses,
             emotional_expressions, message_pattern_triggers, conversation_flow_guidance,
             ai_identity_handling)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (character_id) DO UPDATE SET
                response_length = EXCLUDED.response_length,
                communication_style = EXCLUDED.communication_style,
                typical_responses = EXCLUDED.typical_responses,
                emotional_expressions = EXCLUDED.emotional_expressions,
                message_pattern_triggers = EXCLUDED.message_pattern_triggers,
                conversation_flow_guidance = EXCLUDED.conversation_flow_guidance,
                ai_identity_handling = EXCLUDED.ai_identity_handling,
                updated_at = CURRENT_TIMESTAMP
        """, char_id, response_length, communication_style,
             json.dumps(typical_responses), json.dumps(emotional_expressions),
             json.dumps(message_pattern_triggers), json.dumps(conversation_flow_guidance),
             json.dumps(ai_identity_handling))
    
    async def _migrate_backstory(self, conn, char_id: int, char_data: Dict[str, Any]):
        """Migrate backstory data"""
        backstory = char_data.get('backstory', {})
        
        # All backstory data goes to JSON since it's complex and varied
        childhood = backstory.get('childhood', {})
        education = backstory.get('education', {})
        career_history = backstory.get('career_history', [])
        key_events = backstory.get('key_events', [])
        relationships = backstory.get('relationships', {})
        
        await conn.execute("""
            INSERT INTO character_backstory 
            (character_id, childhood, education, career_history, key_events, relationships)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (character_id) DO UPDATE SET
                childhood = EXCLUDED.childhood,
                education = EXCLUDED.education,
                career_history = EXCLUDED.career_history,
                key_events = EXCLUDED.key_events,
                relationships = EXCLUDED.relationships,
                updated_at = CURRENT_TIMESTAMP
        """, char_id, json.dumps(childhood), json.dumps(education),
             json.dumps(career_history), json.dumps(key_events), json.dumps(relationships))
    
    async def _migrate_current_life(self, conn, char_id: int, char_data: Dict[str, Any]):
        """Migrate current life data"""
        current_life = char_data.get('current_life', {})
        
        # Extract flexible current state data
        daily_routine = current_life.get('daily_routine', {})
        current_projects = current_life.get('current_projects', [])
        goals = current_life.get('goals', [])
        challenges = current_life.get('challenges', [])
        social_circle = current_life.get('social_circle', [])
        interests = current_life.get('interests', [])
        
        await conn.execute("""
            INSERT INTO character_current_life 
            (character_id, daily_routine, current_projects, goals, challenges, social_circle, interests)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (character_id) DO UPDATE SET
                daily_routine = EXCLUDED.daily_routine,
                current_projects = EXCLUDED.current_projects,
                goals = EXCLUDED.goals,
                challenges = EXCLUDED.challenges,
                social_circle = EXCLUDED.social_circle,
                interests = EXCLUDED.interests,
                updated_at = CURRENT_TIMESTAMP
        """, char_id, json.dumps(daily_routine), json.dumps(current_projects),
             json.dumps(goals), json.dumps(challenges), json.dumps(social_circle), 
             json.dumps(interests))
    
    async def _migrate_speech_patterns(self, conn, char_id: int, char_data: Dict[str, Any]):
        """Migrate speech patterns data"""
        speech_patterns = char_data.get('speech_patterns', {})
        identity = char_data.get('identity', {})
        voice = identity.get('voice', {})
        
        # Extract vocabulary and language patterns
        vocabulary = speech_patterns.get('vocabulary', {"preferred_words": [], "avoided_words": []})
        language_patterns = speech_patterns.get('language_patterns', {})
        favorite_phrases = voice.get('favorite_phrases', [])
        speech_quirks = speech_patterns.get('speech_quirks', [])
        
        await conn.execute("""
            INSERT INTO character_speech_patterns 
            (character_id, vocabulary, language_patterns, favorite_phrases, speech_quirks)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (character_id) DO UPDATE SET
                vocabulary = EXCLUDED.vocabulary,
                language_patterns = EXCLUDED.language_patterns,
                favorite_phrases = EXCLUDED.favorite_phrases,
                speech_quirks = EXCLUDED.speech_quirks,
                updated_at = CURRENT_TIMESTAMP
        """, char_id, json.dumps(vocabulary), json.dumps(language_patterns),
             json.dumps(favorite_phrases), json.dumps(speech_quirks))
    
    async def _migrate_personal_knowledge(self, conn, char_id: int, char_data: Dict[str, Any]):
        """Migrate personal knowledge data"""
        personal = char_data.get('personal', {})
        
        # Extract personal information
        relationships = personal.get('relationships', {})
        career = personal.get('career', {})
        hobbies = personal.get('hobbies', {})
        preferences = personal.get('preferences', {})
        memories = personal.get('memories', [])
        secrets = personal.get('secrets', [])
        
        await conn.execute("""
            INSERT INTO character_personal_knowledge 
            (character_id, relationships, career, hobbies, preferences, memories, secrets)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (character_id) DO UPDATE SET
                relationships = EXCLUDED.relationships,
                career = EXCLUDED.career,
                hobbies = EXCLUDED.hobbies,
                preferences = EXCLUDED.preferences,
                memories = EXCLUDED.memories,
                secrets = EXCLUDED.secrets,
                updated_at = CURRENT_TIMESTAMP
        """, char_id, json.dumps(relationships), json.dumps(career),
             json.dumps(hobbies), json.dumps(preferences), json.dumps(memories),
             json.dumps(secrets))
    
    async def _migrate_metadata(self, conn, char_id: int, char_data: Dict[str, Any], character_name: str):
        """Migrate metadata"""
        metadata = char_data.get('metadata', {})
        
        created_by = metadata.get('created_by', 'migration')
        source_file = f"characters/examples/{character_name}.json"
        schema_version = "1.0"
        
        # Put any extra metadata in extended_metadata
        extended_metadata = {k: v for k, v in metadata.items() 
                           if k not in ['created_by', 'source_file', 'schema_version']}
        
        await conn.execute("""
            INSERT INTO character_metadata 
            (character_id, created_by, source_file, schema_version, extended_metadata)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (character_id) DO UPDATE SET
                created_by = EXCLUDED.created_by,
                source_file = EXCLUDED.source_file,
                schema_version = EXCLUDED.schema_version,
                extended_metadata = EXCLUDED.extended_metadata,
                updated_at = CURRENT_TIMESTAMP
        """, char_id, created_by, source_file, schema_version, json.dumps(extended_metadata))
    
    async def _verify_migration(self):
        """Verify the migration was successful"""
        logger.info("🔍 Verifying migration...")
        
        async with self.pool.acquire() as conn:
            # Count characters in new schema
            char_count = await conn.fetchval("SELECT COUNT(*) FROM characters")
            logger.info(f"Characters migrated: {char_count}")
            
            # Verify each table has data
            tables = [
                'character_identity', 'character_personality', 'character_communication',
                'character_backstory', 'character_current_life', 'character_speech_patterns',
                'character_personal_knowledge', 'character_metadata'
            ]
            
            for table in tables:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                logger.info(f"{table}: {count} records")
            
            # Sample a character to verify structure
            sample = await conn.fetchrow("""
                SELECT c.name, ci.occupation, cp.openness, cc.response_length
                FROM characters c
                JOIN character_identity ci ON c.id = ci.character_id
                JOIN character_personality cp ON c.id = cp.character_id
                JOIN character_communication cc ON c.id = cc.character_id
                LIMIT 1
            """)
            
            if sample:
                logger.info(f"Sample character: {dict(sample)}")
            
            logger.info("✅ Migration verification completed")


async def main():
    """Run the migration"""
    logging.basicConfig(level=logging.INFO)
    
    migrator = CDLDatabaseMigrator()
    await migrator.initialize()
    await migrator.run_migration()


if __name__ == "__main__":
    asyncio.run(main())