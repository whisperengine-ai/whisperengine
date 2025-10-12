#!/usr/bin/env python3
"""
WhisperEngine Character Development Backup Export Script (Python Version)
Exports complete character data including extended data tables and semantic knowledge graph.
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
DB_CONTAINER = "postgres"
DB_USER = "whisperengine"
DB_NAME = "whisperengine"
OUTPUT_DIR = Path("sql/characters/dev")

# Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def log_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")

def log_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")

def log_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")

def log_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")

def execute_psql(query, tuples_only=True):
    """Execute a PostgreSQL query and return the results."""
    cmd = [
        "docker", "exec", "-i", DB_CONTAINER,
        "psql", "-U", DB_USER, "-d", DB_NAME
    ]
    
    if tuples_only:
        cmd.extend(["-t", "-A"])  # Tuples only, no alignment
    
    cmd.extend(["-c", query])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log_error(f"Query failed: {e}")
        log_error(f"stderr: {e.stderr}")
        return None

def export_table_data(character_name, table_name, columns_query, output_file):
    """Export data from a table for a specific character."""
    # Count records first
    count_query = f"""
        SELECT COUNT(*) FROM {table_name} t
        JOIN characters c ON t.character_id = c.id
        WHERE c.normalized_name = '{character_name}';
    """
    
    count = execute_psql(count_query)
    
    if not count or int(count) == 0:
        return 0
    
    # Export INSERT statements
    result = execute_psql(columns_query)
    
    if result:
        with open(output_file, 'a') as f:
            f.write(result + '\n')
        
        return int(count)
    
    return 0

def export_character(character_name, normalized_name):
    """Export a single character with all extended data."""
    output_file = OUTPUT_DIR / f"{normalized_name}.sql"
    
    log_info(f"Exporting character: {character_name} (normalized: {normalized_name})")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Start building the SQL file
    header = f"""-- ==============================================================================
-- WhisperEngine Character Development Backup
-- Character: {character_name}
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ==============================================================================
-- This file contains the complete character definition including:
-- - Core character data (characters table)
-- - Extended data (9 tables: message_triggers, cultural_expressions, etc.)
-- - Semantic knowledge graph data (facts, entities, relationships)
--
-- To load this character:
--   docker exec -i postgres psql -U whisperengine -d whisperengine -f /app/sql/characters/dev/{normalized_name}.sql
--
-- Or use the helper script:
--   ./scripts/load_dev_character.sh {normalized_name}
-- ==============================================================================

BEGIN;

-- ==============================================================================
-- 1. CORE CHARACTER DATA
-- ==============================================================================

"""
    
    with open(output_file, 'w') as f:
        f.write(header)
    
    # Export core character data
    log_info("  Exporting core character data...")
    core_query = f"""
        SELECT 
            'INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active) VALUES (' ||
            quote_literal(name) || ', ' ||
            quote_literal(normalized_name) || ', ' ||
            quote_literal(occupation) || ', ' ||
            quote_literal(description) || ', ' ||
            quote_literal(archetype) || ', ' ||
            allow_full_roleplay || ', ' ||
            is_active ||
            ') ON CONFLICT (normalized_name) DO UPDATE SET ' ||
            'name = EXCLUDED.name, ' ||
            'occupation = EXCLUDED.occupation, ' ||
            'description = EXCLUDED.description, ' ||
            'archetype = EXCLUDED.archetype, ' ||
            'allow_full_roleplay = EXCLUDED.allow_full_roleplay, ' ||
            'is_active = EXCLUDED.is_active, ' ||
            'updated_at = CURRENT_TIMESTAMP;'
        FROM characters 
        WHERE normalized_name = '{normalized_name}';
    """
    
    core_data = execute_psql(core_query)
    if core_data:
        with open(output_file, 'a') as f:
            f.write(core_data + '\n')
    
    # Add temp table for character ID
    with open(output_file, 'a') as f:
        f.write(f"""
-- Get the character ID for use in extended data inserts
DO $$
DECLARE
    v_character_id INTEGER;
BEGIN
    SELECT id INTO v_character_id FROM characters WHERE normalized_name = '{normalized_name}';
    
    IF v_character_id IS NULL THEN
        RAISE EXCEPTION 'Character not found: {normalized_name}';
    END IF;
    
    -- Store in temporary table for use in subsequent inserts
    CREATE TEMP TABLE IF NOT EXISTS temp_character_id (id INTEGER);
    DELETE FROM temp_character_id;
    INSERT INTO temp_character_id VALUES (v_character_id);
END $$;

-- ==============================================================================
-- 2. EXTENDED DATA TABLES (9 tables)
-- ==============================================================================

""")
    
    # Define extended data tables with their queries
    extended_tables = [
        {
            'name': 'character_message_triggers',
            'label': '2.1 Message Triggers',
            'description': 'Pattern-based triggers for character responses',
            'query': f"""
                SELECT 
                    'INSERT INTO character_message_triggers (character_id, trigger_category, trigger_type, trigger_value, response_style, priority_level) VALUES (' ||
                    '(SELECT id FROM temp_character_id), ' ||
                    quote_literal(COALESCE(trigger_category, '')) || ', ' ||
                    quote_literal(COALESCE(trigger_type, '')) || ', ' ||
                    quote_literal(trigger_value) || ', ' ||
                    quote_literal(COALESCE(response_style, '')) || ', ' ||
                    COALESCE(priority_level, 5) ||
                    ');'
                FROM character_message_triggers cmt
                JOIN characters c ON cmt.character_id = c.id
                WHERE c.normalized_name = '{normalized_name}'
                ORDER BY cmt.id;
            """
        },
        {
            'name': 'character_cultural_expressions',
            'label': '2.2 Cultural Expressions',
            'description': 'Cultural phrases, idioms, and expressions',
            'query': f"""
                SELECT 
                    'INSERT INTO character_cultural_expressions (character_id, expression_category, expression_type, expression_value, context_usage, frequency) VALUES (' ||
                    '(SELECT id FROM temp_character_id), ' ||
                    quote_literal(COALESCE(expression_category, '')) || ', ' ||
                    quote_literal(COALESCE(expression_type, '')) || ', ' ||
                    quote_literal(expression_value) || ', ' ||
                    quote_literal(COALESCE(context_usage, '')) || ', ' ||
                    quote_literal(COALESCE(frequency, 'regular')) ||
                    ');'
                FROM character_cultural_expressions cce
                JOIN characters c ON cce.character_id = c.id
                WHERE c.normalized_name = '{normalized_name}'
                ORDER BY cce.id;
            """
        },
        {
            'name': 'character_emotional_triggers',
            'label': '2.3 Emotional Triggers',
            'description': 'Emotional responses and trigger patterns',
            'query': f"""
                SELECT 
                    'INSERT INTO character_emotional_triggers (character_id, trigger_category, trigger_name, emotional_response, intensity_level, response_behavior) VALUES (' ||
                    '(SELECT id FROM temp_character_id), ' ||
                    quote_literal(COALESCE(trigger_category, '')) || ', ' ||
                    quote_literal(trigger_name) || ', ' ||
                    quote_literal(COALESCE(emotional_response, '')) || ', ' ||
                    COALESCE(intensity_level, 5) || ', ' ||
                    quote_literal(COALESCE(response_behavior, '')) ||
                    ');'
                FROM character_emotional_triggers cet
                JOIN characters c ON cet.character_id = c.id
                WHERE c.normalized_name = '{normalized_name}'
                ORDER BY cet.id;
            """
        },
        {
            'name': 'character_voice_traits',
            'label': '2.4 Voice Traits',
            'description': 'Voice characteristics and speech patterns',
            'query': f"""
                SELECT 
                    'INSERT INTO character_voice_traits (character_id, trait_category, trait_type, trait_value, description, usage_frequency) VALUES (' ||
                    '(SELECT id FROM temp_character_id), ' ||
                    quote_literal(COALESCE(trait_category, '')) || ', ' ||
                    quote_literal(COALESCE(trait_type, '')) || ', ' ||
                    quote_literal(trait_value) || ', ' ||
                    quote_literal(COALESCE(description, '')) || ', ' ||
                    quote_literal(COALESCE(usage_frequency, 'regular')) ||
                    ');'
                FROM character_voice_traits cvt
                JOIN characters c ON cvt.character_id = c.id
                WHERE c.normalized_name = '{normalized_name}'
                ORDER BY cvt.id;
            """
        },
        {
            'name': 'character_response_guidelines',
            'label': '2.5 Response Guidelines',
            'description': 'Guidelines for appropriate responses in different contexts',
            'query': f"""
                SELECT 
                    'INSERT INTO character_response_guidelines (character_id, context_category, guideline_type, guideline_text, priority_level, example_scenario) VALUES (' ||
                    '(SELECT id FROM temp_character_id), ' ||
                    quote_literal(COALESCE(context_category, '')) || ', ' ||
                    quote_literal(COALESCE(guideline_type, '')) || ', ' ||
                    quote_literal(guideline_text) || ', ' ||
                    COALESCE(priority_level, 5) || ', ' ||
                    quote_literal(COALESCE(example_scenario, '')) ||
                    ');'
                FROM character_response_guidelines crg
                JOIN characters c ON crg.character_id = c.id
                WHERE c.normalized_name = '{normalized_name}'
                ORDER BY crg.id;
            """
        },
        {
            'name': 'character_expertise_domains',
            'label': '2.6 Expertise Domains',
            'description': 'Areas of expertise and specialized knowledge',
            'query': f"""
                SELECT 
                    'INSERT INTO character_expertise_domains (character_id, domain_category, domain_name, proficiency_level, specialization, teaching_style) VALUES (' ||
                    '(SELECT id FROM temp_character_id), ' ||
                    quote_literal(COALESCE(domain_category, '')) || ', ' ||
                    quote_literal(domain_name) || ', ' ||
                    COALESCE(proficiency_level, 5) || ', ' ||
                    quote_literal(COALESCE(specialization, '')) || ', ' ||
                    quote_literal(COALESCE(teaching_style, '')) ||
                    ');'
                FROM character_expertise_domains ced
                JOIN characters c ON ced.character_id = c.id
                WHERE c.normalized_name = '{normalized_name}'
                ORDER BY ced.id;
            """
        },
        {
            'name': 'character_ai_scenarios',
            'label': '2.7 AI Scenarios',
            'description': 'Scenario-specific behavior patterns for AI roleplay',
            'query': f"""
                SELECT 
                    'INSERT INTO character_ai_scenarios (character_id, scenario_category, scenario_name, response_approach, example_response, handling_priority) VALUES (' ||
                    '(SELECT id FROM temp_character_id), ' ||
                    quote_literal(COALESCE(scenario_category, '')) || ', ' ||
                    quote_literal(scenario_name) || ', ' ||
                    quote_literal(COALESCE(response_approach, '')) || ', ' ||
                    quote_literal(COALESCE(example_response, '')) || ', ' ||
                    COALESCE(handling_priority, 5) ||
                    ');'
                FROM character_ai_scenarios cas
                JOIN characters c ON cas.character_id = c.id
                WHERE c.normalized_name = '{normalized_name}'
                ORDER BY cas.id;
            """
        },
        {
            'name': 'character_conversation_flows',
            'label': '2.8 Conversation Flows',
            'description': 'Dynamic conversation flow patterns and transitions',
            'query': f"""
                SELECT 
                    'INSERT INTO character_conversation_flows (character_id, flow_type, flow_category, energy_level, conversational_approach, topic_transition, context_adaptation) VALUES (' ||
                    '(SELECT id FROM temp_character_id), ' ||
                    quote_literal(flow_type) || ', ' ||
                    quote_literal(COALESCE(flow_category, '')) || ', ' ||
                    quote_literal(COALESCE(energy_level, '')) || ', ' ||
                    quote_literal(COALESCE(conversational_approach, '')) || ', ' ||
                    quote_literal(COALESCE(topic_transition, '')) || ', ' ||
                    quote_literal(COALESCE(context_adaptation, '')) ||
                    ');'
                FROM character_conversation_flows ccf
                JOIN characters c ON ccf.character_id = c.id
                WHERE c.normalized_name = '{normalized_name}'
                ORDER BY ccf.id;
            """
        },
        {
            'name': 'character_emoji_patterns',
            'label': '2.9 Emoji Patterns',
            'description': 'Emoji usage patterns and preferences',
            'query': f"""
                SELECT 
                    'INSERT INTO character_emoji_patterns (character_id, pattern_category, emoji_value, usage_context, emotional_association, frequency) VALUES (' ||
                    '(SELECT id FROM temp_character_id), ' ||
                    quote_literal(COALESCE(pattern_category, '')) || ', ' ||
                    quote_literal(emoji_value) || ', ' ||
                    quote_literal(COALESCE(usage_context, '')) || ', ' ||
                    quote_literal(COALESCE(emotional_association, '')) || ', ' ||
                    quote_literal(COALESCE(frequency, 'regular')) ||
                    ');'
                FROM character_emoji_patterns cep
                JOIN characters c ON cep.character_id = c.id
                WHERE c.normalized_name = '{normalized_name}'
                ORDER BY cep.id;
            """
        }
    ]
    
    total_records = 0
    
    # Export each extended table
    for table_info in extended_tables:
        with open(output_file, 'a') as f:
            f.write(f"\n-- {table_info['label']}\n")
            f.write(f"-- {table_info['description']}\n\n")
        
        log_info(f"  Exporting {table_info['name']}...")
        count = export_table_data(normalized_name, table_info['name'], table_info['query'], output_file)
        
        if count > 0:
            log_success(f"    Exported {count} records from {table_info['name']}")
            total_records += count
        else:
            log_warning(f"    No records found in {table_info['name']}")
    
    # Add semantic knowledge graph data section
    with open(output_file, 'a') as f:
        f.write("""
-- ==============================================================================
-- 3. SEMANTIC KNOWLEDGE GRAPH DATA
-- ==============================================================================
-- Character-specific facts, entities, and relationships

-- 3.1 Fact Entities

""")
    
    # Export fact entities (if any)
    log_info("  Exporting fact entities...")
    facts_query = f"""
        SELECT 
            'INSERT INTO fact_entities (entity_name, entity_type, entity_metadata, confidence, created_at, character_name) VALUES (' ||
            quote_literal(entity_name) || ', ' ||
            quote_literal(COALESCE(entity_type, 'general')) || ', ' ||
            quote_literal(COALESCE(entity_metadata::text, '{{}}')) || ', ' ||
            COALESCE(confidence, 1.0) || ', ' ||
            quote_literal(created_at::text) || ', ' ||
            quote_literal(character_name) ||
            ') ON CONFLICT DO NOTHING;'
        FROM fact_entities
        WHERE character_name = '{normalized_name}'
        ORDER BY id;
    """
    
    facts_data = execute_psql(facts_query)
    if facts_data:
        with open(output_file, 'a') as f:
            f.write(facts_data + '\n')
        log_success("    Exported fact entities")
    
    with open(output_file, 'a') as f:
        f.write("\n-- 3.2 Character Fact Relationships\n\n")
    
    # Export character fact relationships
    log_info("  Exporting character fact relationships...")
    relationships_query = f"""
        SELECT 
            'INSERT INTO character_fact_relationships (character_name, entity_name, relationship_type, confidence, metadata, last_mentioned_at) VALUES (' ||
            quote_literal(character_name) || ', ' ||
            quote_literal(entity_name) || ', ' ||
            quote_literal(relationship_type) || ', ' ||
            COALESCE(confidence, 1.0) || ', ' ||
            quote_literal(COALESCE(metadata::text, '{{}}')) || ', ' ||
            quote_literal(COALESCE(last_mentioned_at::text, CURRENT_TIMESTAMP::text)) ||
            ') ON CONFLICT DO NOTHING;'
        FROM character_fact_relationships
        WHERE character_name = '{normalized_name}'
        ORDER BY id;
    """
    
    relationships_data = execute_psql(relationships_query)
    if relationships_data:
        with open(output_file, 'a') as f:
            f.write(relationships_data + '\n')
        log_success("    Exported character fact relationships")
    
    # Add footer
    with open(output_file, 'a') as f:
        f.write(f"""
-- Cleanup temporary table
DROP TABLE IF EXISTS temp_character_id;

COMMIT;

-- ==============================================================================
-- Export Complete
-- ==============================================================================
-- Character: {character_name}
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Total extended data records: {total_records}
-- 
-- Next steps:
-- 1. Review the exported data
-- 2. Test loading: ./scripts/load_dev_character.sh {normalized_name}
-- 3. Commit to version control for development backup
-- ==============================================================================
""")
    
    log_success(f"Exported character: {character_name} → {output_file}")
    log_info(f"  Total extended data records: {total_records}")
    
    return total_records

def main():
    if len(sys.argv) < 2:
        log_error("Usage: export_character_dev_backup.py <character_name|all>")
        log_info("Examples:")
        log_info("  export_character_dev_backup.py elena")
        log_info("  export_character_dev_backup.py all")
        sys.exit(1)
    
    character_arg = sys.argv[1]
    
    # Check if PostgreSQL container is running
    try:
        subprocess.run(["docker", "ps"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        log_error("Docker is not running")
        sys.exit(1)
    
    if character_arg == "all":
        log_info("Exporting ALL active characters...")
        
        # Get list of all active characters
        query = """
            SELECT name, normalized_name 
            FROM characters 
            WHERE is_active = true 
            ORDER BY name;
        """
        
        result = execute_psql(query)
        
        if not result:
            log_error("No active characters found")
            sys.exit(1)
        
        characters = []
        for line in result.split('\n'):
            if line.strip():
                parts = line.split('|')
                if len(parts) == 2:
                    characters.append((parts[0].strip(), parts[1].strip()))
        
        total_chars = 0
        total_records = 0
        
        for char_name, norm_name in characters:
            records = export_character(char_name, norm_name)
            total_chars += 1
            total_records += records
        
        log_success(f"Exported {total_chars} characters with {total_records} total extended data records!")
    
    else:
        normalized_name = character_arg
        
        # Get character full name
        query = f"SELECT name FROM characters WHERE normalized_name = '{normalized_name}';"
        character_name = execute_psql(query)
        
        if not character_name:
            log_error(f"Character not found: {normalized_name}")
            log_info("Available characters:")
            subprocess.run([
                "docker", "exec", "-i", DB_CONTAINER,
                "psql", "-U", DB_USER, "-d", DB_NAME,
                "-c", "SELECT normalized_name, name FROM characters WHERE is_active = true ORDER BY name;"
            ])
            sys.exit(1)
        
        export_character(character_name, normalized_name)
    
    log_success("✨ Character export complete!")

if __name__ == "__main__":
    main()
