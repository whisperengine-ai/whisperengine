#!/usr/bin/env python3
"""
CDL JSON to Database Migration Script
WhisperEngine Character Definition Language Migration Tool

Migrates existing JSON CDL character files to PostgreSQL database.
Preserves all character data and provides validation and rollback capabilities.
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.cdl_database import CDLDatabaseManager
from src.characters.cdl.parser import CDLParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CDLMigrationTool:
    """Migration tool for CDL JSON files to PostgreSQL database"""
    
    def __init__(self, characters_dir: str = "characters/examples"):
        self.characters_dir = Path(characters_dir)
        self.db_manager = CDLDatabaseManager()
        self.cdl_parser = CDLParser()
        self.migration_log = []
        
    async def initialize(self):
        """Initialize database connection and check schema"""
        await self.db_manager.initialize_pool()
        
        # Check if schema exists
        schema_exists = await self.db_manager.check_schema_exists()
        if not schema_exists:
            logger.error("CDL database schema not found. Please run migration first:")
            logger.error("psql -h localhost -p 5433 -U whisperengine -d whisperengine -f src/database/migrations/001_create_cdl_schema.sql")
            raise RuntimeError("Database schema not initialized")
            
        logger.info("CDL database schema verified")
    
    async def cleanup(self):
        """Clean up database connections"""
        await self.db_manager.close_pool()
    
    def find_character_files(self) -> List[Path]:
        """Find all JSON CDL character files"""
        if not self.characters_dir.exists():
            logger.error("Characters directory not found: %s", self.characters_dir)
            return []
        
        json_files = list(self.characters_dir.glob("*.json"))
        logger.info("Found %d JSON character files", len(json_files))
        return json_files
    
    def load_character_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and validate character JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Handle nested CDL structure - extract character data from 'character' key
            if 'character' in raw_data:
                character_data = raw_data['character']
                # Add metadata from top level
                character_data['cdl_version'] = raw_data.get('cdl_version')
                character_data['format'] = raw_data.get('format')
                character_data['source_file'] = file_path.name
            else:
                # Legacy format - character data at root level
                character_data = raw_data
                character_data['source_file'] = file_path.name
            
            # Basic validation using nested structure
            metadata = character_data.get('metadata', {})
            identity = character_data.get('identity', {})
            
            character_name = (metadata.get('name') or 
                            identity.get('name') or 
                            character_data.get('name'))
            
            if not character_name:
                logger.error("Character file %s missing name field in metadata/identity", file_path.name)
                return None
                
            if not identity:
                logger.error("Character file %s missing 'identity' section", file_path.name)
                return None
            
            # Add computed name for easier access
            character_data['computed_name'] = character_name
            
            logger.info("Loaded character: %s", character_name)
            return character_data
            
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load %s: %s", file_path.name, e)
            return None
    
    def extract_character_basic_info(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic character information for cdl_characters table"""
        metadata = character_data.get('metadata', {})
        identity = character_data.get('identity', {})
        
        # Get name from computed field or fallback chain
        character_name = character_data.get('computed_name')
        
        # Extract AI identity handling settings
        communication = character_data.get('communication', {})
        ai_identity = communication.get('ai_identity_handling', {})
        
        return {
            'name': character_name,
            'normalized_name': character_name.lower().replace(' ', '_') if character_name else None,
            'bot_name': character_data.get('bot_name'),
            'occupation': identity.get('occupation'),
            'location': identity.get('location'), 
            'age_range': str(identity.get('age')) if identity.get('age') else identity.get('age_range'),
            'background': identity.get('cultural_background') or identity.get('background'),
            'description': identity.get('description'),
            'character_archetype': character_data.get('character_archetype', 'real-world'),
            'allow_full_roleplay_immersion': ai_identity.get('allow_full_roleplay_immersion', False),
            'created_by': metadata.get('created_by', 'migration_script'),
            'notes': f"Migrated from {character_data.get('source_file', 'unknown')} - CDL v{character_data.get('cdl_version', '1.0')}"
        }
    
    def extract_personality_traits(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract personality traits from character data"""
        traits = []
        
        # Big Five personality traits
        personality = character_data.get('personality', {})
        big_five = personality.get('big_five', {})
        
        for trait_name, trait_value in big_five.items():
            if isinstance(trait_value, dict):
                traits.append({
                    'category': 'big_five',
                    'name': trait_name,
                    'value': trait_value.get('score'),
                    'description': trait_value.get('description'),
                    'intensity': self._score_to_intensity(trait_value.get('score', 0.5))
                })
            elif isinstance(trait_value, (int, float)):
                traits.append({
                    'category': 'big_five',
                    'name': trait_name,
                    'value': trait_value,
                    'description': f"{trait_name.replace('_', ' ').title()} trait",
                    'intensity': self._score_to_intensity(trait_value)
                })
        
        # Custom traits
        custom_traits = personality.get('custom_traits', {})
        for trait_name, trait_value in custom_traits.items():
            if isinstance(trait_value, dict):
                traits.append({
                    'category': 'custom',
                    'name': trait_name,
                    'value': trait_value.get('score'),
                    'description': trait_value.get('description'),
                    'intensity': trait_value.get('intensity', 'medium')
                })
            elif isinstance(trait_value, (int, float)):
                traits.append({
                    'category': 'custom',
                    'name': trait_name,
                    'value': trait_value,
                    'description': f"Custom trait: {trait_name}",
                    'intensity': self._score_to_intensity(trait_value)
                })
            else:
                traits.append({
                    'category': 'custom',
                    'name': trait_name,
                    'value': None,
                    'description': str(trait_value),
                    'intensity': 'medium'
                })
        
        return traits
    
    def extract_communication_styles(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract communication styles from character data"""
        styles = []
        
        # Identity voice characteristics
        identity = character_data.get('identity', {})
        voice = identity.get('voice', {})
        for voice_key, voice_value in voice.items():
            if voice_key == 'speech_patterns' and isinstance(voice_value, list):
                for i, pattern in enumerate(voice_value):
                    styles.append({
                        'category': 'voice_patterns',
                        'name': f'speech_pattern_{i+1}',
                        'value': str(pattern),
                        'description': f"Speech pattern: {pattern}",
                        'priority': i
                    })
            elif voice_key == 'favorite_phrases' and isinstance(voice_value, list):
                for i, phrase in enumerate(voice_value):
                    styles.append({
                        'category': 'favorite_phrases',
                        'name': f'phrase_{i+1}',
                        'value': str(phrase),
                        'description': f"Favorite phrase: {phrase}",
                        'priority': i
                    })
            else:
                styles.append({
                    'category': 'voice',
                    'name': voice_key,
                    'value': json.dumps(voice_value) if isinstance(voice_value, (dict, list)) else str(voice_value),
                    'description': f"Voice characteristic: {voice_key}",
                    'priority': 0
                })
        
        # Digital communication patterns
        digital_comm = identity.get('digital_communication', {})
        emoji_personality = digital_comm.get('emoji_personality', {})
        for emoji_key, emoji_value in emoji_personality.items():
            styles.append({
                'category': 'emoji_personality',
                'name': emoji_key,
                'value': json.dumps(emoji_value) if isinstance(emoji_value, (dict, list)) else str(emoji_value),
                'description': f"Emoji personality: {emoji_key}",
                'priority': 0
            })
        
        emoji_patterns = digital_comm.get('emoji_usage_patterns', {})
        for pattern_category, pattern_data in emoji_patterns.items():
            styles.append({
                'category': 'emoji_patterns',
                'name': pattern_category,
                'value': json.dumps(pattern_data),
                'description': f"Emoji usage pattern: {pattern_category}",
                'priority': 0
            })
        
        # Personality communication style
        personality = character_data.get('personality', {})
        comm_style = personality.get('communication_style', {})
        for style_key, style_value in comm_style.items():
            if style_key == 'language_patterns':
                for lang_key, lang_value in style_value.items():
                    styles.append({
                        'category': 'language_patterns',
                        'name': lang_key,
                        'value': json.dumps(lang_value) if isinstance(lang_value, (dict, list)) else str(lang_value),
                        'description': f"Language pattern: {lang_key}",
                        'priority': 0
                    })
            elif style_key == 'interaction_preferences':
                for pref_key, pref_value in style_value.items():
                    styles.append({
                        'category': 'interaction_preferences',
                        'name': pref_key,
                        'value': json.dumps(pref_value) if isinstance(pref_value, (dict, list)) else str(pref_value),
                        'description': f"Interaction preference: {pref_key}",
                        'priority': 0
                    })
            elif style_key == 'emotional_expression':
                for emotion_key, emotion_value in style_value.items():
                    styles.append({
                        'category': 'emotional_expression',
                        'name': emotion_key,
                        'value': json.dumps(emotion_value) if isinstance(emotion_value, (dict, list)) else str(emotion_value),
                        'description': f"Emotional expression: {emotion_key}",
                        'priority': 0
                    })
            else:
                styles.append({
                    'category': 'communication_style',
                    'name': style_key,
                    'value': json.dumps(style_value) if isinstance(style_value, (dict, list)) else str(style_value),
                    'description': f"Communication style: {style_key}",
                    'priority': 0
                })
        
        # Speech patterns
        speech_patterns = character_data.get('speech_patterns', {})
        for speech_key, speech_value in speech_patterns.items():
            if speech_key == 'vocabulary':
                vocab = speech_value
                for vocab_key, vocab_value in vocab.items():
                    styles.append({
                        'category': 'vocabulary',
                        'name': vocab_key,
                        'value': json.dumps(vocab_value) if isinstance(vocab_value, list) else str(vocab_value),
                        'description': f"Vocabulary: {vocab_key}",
                        'priority': 0
                    })
            else:
                styles.append({
                    'category': 'speech_patterns',
                    'name': speech_key,
                    'value': json.dumps(speech_value) if isinstance(speech_value, (dict, list)) else str(speech_value),
                    'description': f"Speech pattern: {speech_key}",
                    'priority': 0
                })
        
        # Communication section (top-level responses and patterns)
        communication = character_data.get('communication', {})
        for comm_key, comm_value in communication.items():
            if comm_key == 'ai_identity_handling':
                # Handle AI identity separately
                continue
            elif comm_key == 'typical_responses':
                for response_type, responses in comm_value.items():
                    styles.append({
                        'category': 'typical_responses',
                        'name': response_type,
                        'value': json.dumps(responses),
                        'description': f"Typical response for: {response_type}",
                        'priority': 0
                    })
            else:
                styles.append({
                    'category': 'communication',
                    'name': comm_key,
                    'value': json.dumps(comm_value) if isinstance(comm_value, (dict, list)) else str(comm_value),
                    'description': f"Communication: {comm_key}",
                    'priority': 0
                })
        
        return styles
    
    def extract_values_and_beliefs(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract values and beliefs from character data"""
        values = []
        
        # Core personality values
        personality = character_data.get('personality', {})
        
        # Values array
        values_list = personality.get('values', [])
        for i, value in enumerate(values_list):
            values.append({
                'category': 'core_values',
                'name': f'value_{i+1}',
                'description': str(value),
                'importance_level': 'high'
            })
        
        # Core beliefs array
        core_beliefs = personality.get('core_beliefs', [])
        for i, belief in enumerate(core_beliefs):
            values.append({
                'category': 'core_beliefs',
                'name': f'belief_{i+1}',
                'description': str(belief),
                'importance_level': 'high'
            })
        
        # Dreams
        dreams = personality.get('dreams', [])
        for i, dream in enumerate(dreams):
            values.append({
                'category': 'dreams',
                'name': f'dream_{i+1}',
                'description': str(dream),
                'importance_level': 'medium'
            })
        
        # Fears
        fears = personality.get('fears', [])
        for i, fear in enumerate(fears):
            values.append({
                'category': 'fears',
                'name': f'fear_{i+1}',
                'description': str(fear),
                'importance_level': 'medium'
            })
        
        # Quirks
        quirks = personality.get('quirks', [])
        for i, quirk in enumerate(quirks):
            values.append({
                'category': 'quirks',
                'name': f'quirk_{i+1}',
                'description': str(quirk),
                'importance_level': 'low'
            })
        
        # Moral alignment
        moral_alignment = personality.get('moral_alignment')
        if moral_alignment:
            values.append({
                'category': 'moral_alignment',
                'name': 'alignment',
                'description': str(moral_alignment),
                'importance_level': 'high'
            })
        
        return values
    
    def extract_anti_patterns(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract anti-patterns and behavioral guidelines"""
        anti_patterns = []
        
        # Speech patterns - avoided words
        speech_patterns = character_data.get('speech_patterns', {})
        vocabulary = speech_patterns.get('vocabulary', {})
        avoided_words = vocabulary.get('avoided_words', [])
        
        for i, word in enumerate(avoided_words):
            anti_patterns.append({
                'category': 'avoid_words',
                'name': f'avoid_word_{i+1}',
                'description': f"Avoid using the word: {word}",
                'severity': 'medium'
            })
        
        # Communication anti-patterns from AI identity handling
        communication = character_data.get('communication', {})
        ai_identity = communication.get('ai_identity_handling', {})
        
        # Add general anti-pattern for characters that don't allow full roleplay
        if not ai_identity.get('allow_full_roleplay_immersion', False):
            anti_patterns.append({
                'category': 'ai_behavior',
                'name': 'honest_ai_disclosure',
                'description': 'Must be honest about AI nature when directly asked, while maintaining character personality',
                'severity': 'high'
            })
        
        return anti_patterns
    
    def extract_personal_knowledge(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract personal knowledge and background information"""
        knowledge = []
        
        # Identity information
        identity = character_data.get('identity', {})
        
        # Basic identity facts
        identity_fields = ['full_name', 'nickname', 'age', 'gender', 'ethnicity', 'occupation', 'location']
        for field in identity_fields:
            value = identity.get(field)
            if value:
                knowledge.append({
                    'category': 'identity',
                    'type': 'fact',
                    'key': field,
                    'value': str(value),
                    'context': 'Core identity information',
                    'confidence_level': 1.0,
                    'is_public': True
                })
        
        # Physical appearance
        physical = identity.get('physical_appearance', {})
        for key, value in physical.items():
            if isinstance(value, list):
                for i, item in enumerate(value):
                    knowledge.append({
                        'category': 'physical_appearance',
                        'type': 'fact',
                        'key': f'{key}_{i+1}',
                        'value': str(item),
                        'context': f'Physical appearance: {key}',
                        'confidence_level': 1.0,
                        'is_public': True
                    })
            else:
                knowledge.append({
                    'category': 'physical_appearance',
                    'type': 'fact',
                    'key': key,
                    'value': str(value),
                    'context': f'Physical appearance: {key}',
                    'confidence_level': 1.0,
                    'is_public': True
                })
        
        # Character essence and background
        essence = identity.get('essence', {})
        for key, value in essence.items():
            knowledge.append({
                'category': 'essence',
                'type': 'fact',
                'key': key,
                'value': str(value),
                'context': 'Character essence and core identity',
                'confidence_level': 1.0,
                'is_public': True
            })
        
        # Cultural background
        cultural_bg = identity.get('cultural_background')
        if cultural_bg:
            knowledge.append({
                'category': 'background',
                'type': 'fact',
                'key': 'cultural_background',
                'value': str(cultural_bg),
                'context': 'Cultural heritage and upbringing',
                'confidence_level': 1.0,
                'is_public': True
            })
        
        # Life phases from background section
        background = character_data.get('background', {})
        life_phases = background.get('life_phases', [])
        for i, phase in enumerate(life_phases):
            phase_key = f"life_phase_{i+1}"
            knowledge.append({
                'category': 'life_history',
                'type': 'experience',
                'key': phase_key,
                'value': json.dumps(phase),
                'context': f"Life phase: {phase.get('title', 'Unknown')}",
                'confidence_level': 1.0,
                'is_public': True
            })
        
        # Personal knowledge section
        personal = character_data.get('personal', {})
        
        # Relationships
        relationships = personal.get('relationships', {})
        for rel_type, rel_data in relationships.items():
            knowledge.append({
                'category': 'relationships',
                'type': 'relationship',
                'key': rel_type,
                'value': json.dumps(rel_data) if isinstance(rel_data, (dict, list)) else str(rel_data),
                'context': f'Relationship: {rel_type}',
                'confidence_level': 1.0,
                'is_public': True
            })
        
        # Career information
        career = personal.get('career', {})
        for career_key, career_value in career.items():
            knowledge.append({
                'category': 'career',
                'type': 'fact',
                'key': career_key,
                'value': json.dumps(career_value) if isinstance(career_value, (dict, list)) else str(career_value),
                'context': f'Career information: {career_key}',
                'confidence_level': 1.0,
                'is_public': True
            })
        
        # Current focus and interests
        current_focus = personal.get('current_focus', [])
        for i, focus in enumerate(current_focus):
            knowledge.append({
                'category': 'interests',
                'type': 'preference',
                'key': f'current_focus_{i+1}',
                'value': str(focus),
                'context': 'Current areas of focus and interest',
                'confidence_level': 1.0,
                'is_public': True
            })
        
        # Social circle
        social_circle = personal.get('social_circle', [])
        for i, connection in enumerate(social_circle):
            knowledge.append({
                'category': 'social',
                'type': 'relationship',
                'key': f'social_connection_{i+1}',
                'value': str(connection),
                'context': 'Social connections and community',
                'confidence_level': 1.0,
                'is_public': True
            })
        
        return knowledge
        for family_key, family_value in family.items():
            knowledge_items.append({
                'category': 'family',
                'type': 'relationship',
                'key': family_key,
                'value': str(family_value),
                'context': 'Family relationship',
                'confidence_level': 1.0,
                'is_public': True
            })
        
        # Extract career information
        career = personal_info.get('career', {})
        for career_key, career_value in career.items():
            knowledge_items.append({
                'category': 'career',
                'type': 'fact',
                'key': career_key,
                'value': str(career_value),
                'context': 'Career background',
                'confidence_level': 1.0,
                'is_public': True
            })
        
        # Extract preferences
        preferences = personal_info.get('preferences', {})
        for pref_key, pref_value in preferences.items():
            knowledge_items.append({
                'category': 'preferences',
                'type': 'preference',
                'key': pref_key,
                'value': str(pref_value),
                'context': 'Personal preference',
                'confidence_level': 1.0,
                'is_public': True
            })
        
        return knowledge_items
    
    def _score_to_intensity(self, score: float) -> str:
        """Convert numeric score to intensity level"""
        if score < 0.3:
            return 'low'
        elif score < 0.6:
            return 'medium'
        elif score < 0.8:
            return 'high'
        else:
            return 'very_high'
    
    async def migrate_character(self, character_data: Dict[str, Any]) -> bool:
        """Migrate a single character to database"""
        try:
            # Check if character already exists
            character_name = character_data.get('computed_name')
            if not character_name:
                logger.error("Character missing computed name, cannot migrate")
                return False
                
            existing = await self.db_manager.get_character_by_name(character_name)
            if existing:
                logger.warning("Character %s already exists in database, skipping", character_name)
                return False
            
            # Create character record
            basic_info = self.extract_character_basic_info(character_data)
            character_id = await self.db_manager.create_character(basic_info)
            
            # Migrate personality traits
            traits = self.extract_personality_traits(character_data)
            for trait in traits:
                await self.db_manager.add_personality_trait(character_id, trait)
            
            # Migrate communication styles
            styles = self.extract_communication_styles(character_data)
            for style in styles:
                await self.db_manager.add_communication_style(character_id, style)
            
            # Migrate values and beliefs
            values = self.extract_values_and_beliefs(character_data)
            for value in values:
                await self.db_manager.add_value(character_id, value)
            
            # Migrate anti-patterns
            anti_patterns = self.extract_anti_patterns(character_data)
            for pattern in anti_patterns:
                await self.db_manager.add_anti_pattern(character_id, pattern)
            
            # Migrate personal knowledge
            knowledge = self.extract_personal_knowledge(character_data)
            for knowledge_item in knowledge:
                await self.db_manager.add_personal_knowledge(character_id, knowledge_item)
            
            # Log migration
            migration_entry = {
                'character_name': character_name,
                'character_id': character_id,
                'traits_count': len(traits),
                'styles_count': len(styles),
                'values_count': len(values),
                'anti_patterns_count': len(anti_patterns),
                'knowledge_count': len(knowledge),
                'migration_timestamp': datetime.now().isoformat(),
                'status': 'completed'
            }
            self.migration_log.append(migration_entry)
            
            logger.info("Successfully migrated character %s (ID: %d) - %d traits, %d styles, %d values, %d patterns, %d knowledge items", 
                       character_name, character_id, len(traits), len(styles), len(values), len(anti_patterns), len(knowledge))
            return True
            
        except (RuntimeError, OSError, json.JSONDecodeError) as e:
            logger.error("Failed to migrate character %s: %s", character_name, e)
            
            # Log failure
            migration_entry = {
                'character_name': character_name,
                'character_id': None,
                'error': str(e),
                'migration_timestamp': datetime.now().isoformat(),
                'status': 'failed'
            }
            self.migration_log.append(migration_entry)
            return False
    
    async def run_migration(self, dry_run: bool = False) -> bool:
        """Run the complete migration process"""
        try:
            await self.initialize()
            
            character_files = self.find_character_files()
            if not character_files:
                logger.error("No character files found to migrate")
                return False
            
            logger.info("Starting migration of %d characters (dry_run=%s)", len(character_files), dry_run)
            
            success_count = 0
            for file_path in character_files:
                character_data = self.load_character_json(file_path)
                if not character_data:
                    continue
                
                character_data['source_file'] = file_path.name
                
                if dry_run:
                    character_name = character_data.get('computed_name', 'Unknown')
                    logger.info("DRY RUN: Would migrate character %s", character_name)
                    # Validate structure without actually migrating
                    traits = self.extract_personality_traits(character_data)
                    styles = self.extract_communication_styles(character_data)
                    values = self.extract_values_and_beliefs(character_data)
                    anti_patterns = self.extract_anti_patterns(character_data)
                    knowledge = self.extract_personal_knowledge(character_data)
                    logger.info("  - %d traits, %d styles, %d values, %d patterns, %d knowledge items", 
                               len(traits), len(styles), len(values), len(anti_patterns), len(knowledge))
                    success_count += 1
                else:
                    if await self.migrate_character(character_data):
                        success_count += 1
            
            logger.info("Migration completed: %d/%d characters processed successfully", 
                       success_count, len(character_files))
            
            # Save migration log
            log_file = f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.migration_log, f, indent=2)
            logger.info("Migration log saved to %s", log_file)
            
            return success_count == len(character_files)
            
        except (RuntimeError, OSError) as e:
            logger.error("Migration failed: %s", e)
            return False
        finally:
            await self.cleanup()

async def main():
    """Main migration script entry point"""
    parser = argparse.ArgumentParser(description="Migrate CDL JSON files to PostgreSQL database")
    parser.add_argument("--characters-dir", default="characters/examples", 
                       help="Directory containing character JSON files")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Validate files without actually migrating")
    parser.add_argument("--verbose", action="store_true", 
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    migration_tool = CDLMigrationTool(args.characters_dir)
    success = await migration_tool.run_migration(dry_run=args.dry_run)
    
    if success:
        logger.info("Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("Migration failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())