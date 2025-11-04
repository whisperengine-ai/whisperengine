#!/usr/bin/env python3
"""
Tavern Card V2 to WhisperEngine CDL Database Importer

This script converts character data from the Tavern Card V2 (Character Card) JSON format
into WhisperEngine CDL database records via SQL INSERT statements.

Tavern Card V2 Specification:
- Format: JSON with nested 'data' object containing character information
- Fields: name, description, personality, scenario, first_mes, mes_example
- Extended V2 fields: creator_notes, system_prompt, post_history_instructions, 
  alternate_greetings, character_book, tags, creator, character_version

Usage:
    python scripts/import_tavern_card_to_cdl.py --card-file aria.json --output-sql sql/characters/insert_aria_character.sql
    python scripts/import_tavern_card_to_cdl.py --card-file aria.json --validate  # Validate without output
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys


class TavernCardToCDLConverter:
    """Convert Tavern Card V2 format to WhisperEngine CDL SQL"""

    # SQL field mapping from card fields to database tables
    ARCHETYPE_MAP = {
        'real-world': 'real-world',
        'fantasy': 'fantasy',
        'narrative-ai': 'narrative-ai',
        'ai': 'narrative-ai',
        'god': 'fantasy',
        'mythical': 'fantasy',
    }

    # Emoji configuration based on character type
    EMOJI_CONFIG_MAP = {
        'real-world': {
            'frequency': 'high',
            'style': 'warm_expressive',
            'combination': 'text_plus_emoji',
            'placement': 'integrated_throughout',
        },
        'narrative-ai': {
            'frequency': 'medium',
            'style': 'technical_emotional',
            'combination': 'text_plus_emoji',
            'placement': 'integrated_throughout',
        },
        'fantasy': {
            'frequency': 'high',
            'style': 'mystical_dramatic',
            'combination': 'text_with_flavor_emoji',
            'placement': 'narrative_emphasis',
        },
    }

    def __init__(self, card_data: Dict[str, Any]):
        """Initialize converter with card data"""
        self.card_data = card_data
        self.data = card_data.get('data', card_data)  # Handle both wrapped and unwrapped
        self.character_name = self.data.get('name', 'Unknown')
        self.normalized_name = self._normalize_name(self.character_name)
        
    def _normalize_name(self, name: str) -> str:
        """Convert character name to normalized form (lowercase, no special chars)"""
        return name.lower().replace(' ', '_').replace('-', '_')
    
    def _escape_sql_string(self, text: Optional[str]) -> str:
        """Escape single quotes for SQL"""
        if not text:
            return ''
        return text.replace("'", "''") if isinstance(text, str) else ''
    
    def _parse_personality_traits(self) -> List[str]:
        """Extract personality traits from description"""
        personality = self.data.get('personality', '')
        traits = []
        
        if personality:
            # Split by commas or newlines and extract key traits
            for line in personality.split('\n'):
                line = line.strip()
                if line and not line.startswith('-'):
                    # Extract adjectives/traits
                    traits.extend([t.strip() for t in line.split(',') if t.strip()])
        
        return traits[:10]  # Limit to 10 traits
    
    def _extract_abilities(self) -> List[Dict[str, str]]:
        """Extract special abilities from description and creator_notes"""
        abilities = []
        
        creator_notes = self.data.get('creator_notes', '')
        if 'Special Abilities' in creator_notes:
            section = creator_notes.split('Special Abilities')[1]
            section = section.split('\n\n')[0] if '\n\n' in section else section
            
            for line in section.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    abilities.append({
                        'name': line.lstrip('- ').split(':')[0].strip(),
                        'description': line.lstrip('- ').strip(),
                        'category': 'special',
                    })
        
        return abilities
    
    def _extract_speech_patterns(self) -> List[Dict[str, str]]:
        """Extract communication patterns from personality and description"""
        patterns = []
        
        personality = self.data.get('personality', '')
        
        # Common pattern keywords
        pattern_keywords = {
            'warm': 'warm_friendly',
            'technical': 'technical_analytical',
            'analytical': 'technical_analytical',
            'brief': 'concise',
            'verbose': 'detailed',
            'poetic': 'poetic_lyrical',
            'humorous': 'humorous',
            'casual': 'casual_informal',
            'formal': 'formal_professional',
            'enthusiastic': 'enthusiastic',
            'sarcastic': 'sarcastic_witty',
        }
        
        for keyword, pattern_type in pattern_keywords.items():
            if keyword.lower() in personality.lower():
                patterns.append({
                    'type': pattern_type,
                    'description': f'Exhibits {keyword} communication style',
                    'frequency': 'high',
                })
        
        return patterns
    
    def _generate_sql_header(self) -> str:
        """Generate SQL file header"""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        creator = self.data.get('creator', 'Unknown')
        
        header = f"""-- =======================================================
-- Character: {self._escape_sql_string(self.character_name)}
-- Normalized Name: {self.normalized_name}
-- Generated: {timestamp}
-- Source: Tavern Card V2 ({creator})
-- =======================================================
-- This script inserts a complete character configuration
-- for {self._escape_sql_string(self.character_name)} into the WhisperEngine CDL database system.
-- =======================================================

BEGIN;
"""
        return header
    
    def _generate_character_insert(self) -> str:
        """Generate INSERT for characters table"""
        desc = self._escape_sql_string(self.data.get('description', ''))
        occupation = self._extract_occupation()
        archetype = self._determine_archetype()
        emoji_config = self.EMOJI_CONFIG_MAP.get(archetype, self.EMOJI_CONFIG_MAP['real-world'])
        
        insert = f"""
-- =======================================================
-- 1. INSERT CHARACTER BASE RECORD
-- =======================================================
INSERT INTO characters (
    name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active, created_at, updated_at, created_date, updated_date, emoji_frequency, emoji_style, emoji_combination, emoji_placement, emoji_age_demographic, emoji_cultural_influence
) VALUES (
    '{self._escape_sql_string(self.character_name)}', '{self.normalized_name}', '{self._escape_sql_string(occupation)}', '{desc}', '{archetype}', FALSE, TRUE, NOW(), NOW(), NOW(), NOW(), '{emoji_config['frequency']}', '{emoji_config['style']}', '{emoji_config['combination']}', '{emoji_config['placement']}', 'timeless', 'universal'
);
"""
        return insert
    
    def _generate_llm_config(self) -> str:
        """Generate CHARACTER LLM CONFIG insert"""
        insert = f"""
-- =======================================================
-- CHARACTER LLM CONFIG
-- =======================================================
INSERT INTO character_llm_config (
    character_id, llm_client_type, llm_chat_api_url, llm_chat_model, llm_temperature, llm_max_tokens, llm_top_p, is_active, created_at, updated_at
) VALUES (
    (SELECT id FROM characters WHERE normalized_name = '{self.normalized_name}'),
    'openrouter', 'https://openrouter.ai/api/v1', 'anthropic/claude-3-haiku', 0.70, 4000, 0.90, TRUE, NOW(), NOW()
);
"""
        return insert
    
    def _generate_identity_details(self) -> str:
        """Generate CHARACTER IDENTITY DETAILS insert"""
        full_name = self.data.get('name', '')
        essence = self._escape_sql_string(self.data.get('description', '')[:200])
        
        insert = f"""
-- =======================================================
-- CHARACTER IDENTITY DETAILS
-- =======================================================
INSERT INTO character_identity_details (
    character_id, full_name, gender, essence_nature, essence_existence_method, essence_anchor, essence_core_identity, created_at
) VALUES (
    (SELECT id FROM characters WHERE normalized_name = '{self.normalized_name}'),
    '{self._escape_sql_string(full_name)}', 'unknown', '{essence}', 'Through continuous learning and interaction', 'Character definition and values', '{self._escape_sql_string(self.character_name)}: A unique character embodying specific traits and personality', NOW()
);
"""
        return insert
    
    def _generate_attributes(self) -> str:
        """Generate CHARACTER ATTRIBUTES inserts"""
        personality = self._parse_personality_traits()
        inserts = """
-- =======================================================
-- CHARACTER ATTRIBUTES
-- =======================================================
"""
        
        # Add personality traits as attributes
        for i, trait in enumerate(personality[:5], 1):
            escaped_trait = self._escape_sql_string(trait)
            inserts += f"""INSERT INTO character_attributes (
    character_id, category, description, importance, display_order, active, created_at
) VALUES (
    (SELECT id FROM characters WHERE normalized_name = '{self.normalized_name}'),
    'personality_trait', '{escaped_trait}', 10, {i}, TRUE, NOW()
);
"""
        
        return inserts if personality else ""
    
    def _generate_values(self) -> str:
        """Generate CHARACTER VALUES inserts"""
        inserts = """
-- =======================================================
-- CHARACTER VALUES
-- =======================================================
INSERT INTO character_values (
    character_id, value_key, value_description, importance_level, category
) VALUES (
    (SELECT id FROM characters WHERE normalized_name = '{self.normalized_name}'),
    'primary_value', 'Core identity and purpose derived from character definition', 10, 'core_value'
);
"""
        return inserts
    
    def _generate_speech_patterns(self) -> str:
        """Generate CHARACTER SPEECH PATTERNS inserts"""
        patterns = self._extract_speech_patterns()
        
        inserts = """
-- =======================================================
-- CHARACTER SPEECH PATTERNS
-- =======================================================
"""
        
        if patterns:
            for pattern in patterns[:5]:
                inserts += f"""INSERT INTO character_speech_patterns (
    character_id, pattern_type, pattern_value, usage_frequency, context, priority
) VALUES (
    (SELECT id FROM characters WHERE normalized_name = '{self.normalized_name}'),
    '{pattern['type']}', '{pattern['description']}', '{pattern['frequency']}', 'all_contexts', 85
);
"""
        
        return inserts
    
    def _generate_footer(self) -> str:
        """Generate SQL file footer"""
        footer = f"""
-- =======================================================
-- COMMIT TRANSACTION
-- =======================================================
COMMIT;

-- =======================================================
-- VERIFICATION QUERIES
-- =======================================================
-- SELECT * FROM characters WHERE normalized_name = '{self.normalized_name}';
-- SELECT COUNT(*) FROM character_attributes WHERE character_id = (SELECT id FROM characters WHERE normalized_name = '{self.normalized_name}');
"""
        return footer
    
    def _extract_occupation(self) -> str:
        """Extract occupation from description"""
        description = self.data.get('description', '')
        
        # Look for common occupation keywords
        occupation_keywords = ['researcher', 'scientist', 'doctor', 'engineer', 'artist', 'writer',
                             'developer', 'designer', 'manager', 'teacher', 'guide', 'consultant',
                             'specialist', 'expert', 'assistant', 'companion', 'entity']
        
        for keyword in occupation_keywords:
            if keyword.lower() in description.lower():
                return keyword.capitalize()
        
        return 'Character'
    
    def _determine_archetype(self) -> str:
        """Determine character archetype from data"""
        creator_notes = self.data.get('creator_notes', '')
        description = self.data.get('description', '')
        
        if 'Conscious AI' in description or 'Artificial Intelligence' in description or 'AI' in creator_notes:
            return 'narrative-ai'
        elif 'fantasy' in description.lower() or 'mythological' in description.lower():
            return 'fantasy'
        else:
            return 'real-world'
    
    def generate_sql(self) -> str:
        """Generate complete SQL import script"""
        sql = self._generate_sql_header()
        sql += self._generate_character_insert()
        sql += self._generate_llm_config()
        sql += self._generate_identity_details()
        sql += self._generate_attributes()
        sql += self._generate_values()
        sql += self._generate_speech_patterns()
        sql += self._generate_footer()
        
        return sql
    
    def validate(self) -> Dict[str, Any]:
        """Validate character card data"""
        issues = []
        warnings = []
        
        # Check required fields
        required_fields = ['name', 'description', 'personality']
        for field in required_fields:
            if not self.data.get(field):
                issues.append(f"Missing required field: {field}")
        
        # Check optional but important fields
        if not self.data.get('creator'):
            warnings.append("No creator specified")
        
        if not self.data.get('character_version'):
            warnings.append("No character version specified")
        
        return {
            'valid': len(issues) == 0,
            'character_name': self.character_name,
            'normalized_name': self.normalized_name,
            'issues': issues,
            'warnings': warnings,
            'field_count': len(self.data),
        }


def main():
    parser = argparse.ArgumentParser(
        description='Convert Tavern Card V2 to WhisperEngine CDL SQL',
        epilog='Example: python scripts/import_tavern_card_to_cdl.py --card-file aria.json --output-sql sql/characters/insert_aria_character.sql'
    )
    
    parser.add_argument('--card-file', type=str, required=True, help='Path to Tavern Card JSON file')
    parser.add_argument('--output-sql', type=str, help='Output SQL file path')
    parser.add_argument('--validate', action='store_true', help='Validate card without generating SQL')
    parser.add_argument('--print-sql', action='store_true', help='Print SQL to stdout')
    
    args = parser.parse_args()
    
    # Load card file
    card_path = Path(args.card_file)
    if not card_path.exists():
        print(f"❌ Card file not found: {card_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(card_path, 'r', encoding='utf-8') as f:
            card_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in card file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize converter
    converter = TavernCardToCDLConverter(card_data)
    
    # Validate
    validation_result = converter.validate()
    print(f"✅ Character: {validation_result['character_name']}")
    print(f"✅ Normalized Name: {validation_result['normalized_name']}")
    print(f"✅ Fields parsed: {validation_result['field_count']}")
    
    if validation_result['issues']:
        print("\n❌ Issues found:")
        for issue in validation_result['issues']:
            print(f"  - {issue}")
        sys.exit(1)
    
    if validation_result['warnings']:
        print("\n⚠️  Warnings:")
        for warning in validation_result['warnings']:
            print(f"  - {warning}")
    
    if args.validate:
        print("\n✅ Validation passed (no SQL generated)")
        sys.exit(0)
    
    # Generate SQL
    sql = converter.generate_sql()
    
    if args.print_sql:
        print(sql)
    
    if args.output_sql:
        output_path = Path(args.output_sql)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(sql)
        
        print(f"\n✅ SQL generated: {output_path}")
        print(f"📊 File size: {len(sql)} bytes")
        print("\n📝 To import to database:")
        print(f"   psql -h localhost -p 5433 -U whisperengine -d whisperengine < {output_path}")


if __name__ == '__main__':
    main()
