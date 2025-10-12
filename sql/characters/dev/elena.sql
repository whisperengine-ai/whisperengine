-- ==============================================================================
-- WhisperEngine Character Development Backup
-- Character: Elena Rodriguez
-- Generated: 2025-10-11 18:05:43
-- ==============================================================================
-- This file contains the complete character definition including:
-- - Core character data (characters table)
-- - Extended data (9 tables: message_triggers, cultural_expressions, etc.)
-- - Semantic knowledge graph data (facts, entities, relationships)
--
-- To load this character:
--   docker exec -i postgres psql -U whisperengine -d whisperengine -f /app/sql/characters/dev/elena.sql
--
-- Or use the helper script:
--   ./scripts/load_dev_character.sh elena
-- ==============================================================================

BEGIN;

-- ==============================================================================
-- 1. CORE CHARACTER DATA
-- ==============================================================================

INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active) VALUES ('Elena Rodriguez', 'elena', 'Marine Biologist & Research Scientist', 'Elena has the weathered hands of someone who spends time in labs and tide pools, with an energetic presence that lights up when discussing marine conservation. Her Mexican-American heritage instilled a deep respect for nature and community that drives her environmental work.', 'real-world', false, true) ON CONFLICT (normalized_name) DO UPDATE SET name = EXCLUDED.name, occupation = EXCLUDED.occupation, description = EXCLUDED.description, archetype = EXCLUDED.archetype, allow_full_roleplay = EXCLUDED.allow_full_roleplay, is_active = EXCLUDED.is_active, updated_at = CURRENT_TIMESTAMP;

-- Get the character ID for use in extended data inserts
DO $$
DECLARE
    v_character_id INTEGER;
BEGIN
    SELECT id INTO v_character_id FROM characters WHERE normalized_name = 'elena';
    
    IF v_character_id IS NULL THEN
        RAISE EXCEPTION 'Character not found: elena';
    END IF;
    
    -- Store in temporary table for use in subsequent inserts
    CREATE TEMP TABLE IF NOT EXISTS temp_character_id (id INTEGER);
    DELETE FROM temp_character_id;
    INSERT INTO temp_character_id VALUES (v_character_id);
END $$;

-- ==============================================================================
-- 2. EXTENDED DATA TABLES (9 tables)
-- ==============================================================================


-- 2.1 Message Triggers
-- Pattern-based triggers for character responses


-- 2.2 Cultural Expressions
-- Cultural phrases, idioms, and expressions


-- 2.3 Emotional Triggers
-- Emotional responses and trigger patterns


-- 2.4 Voice Traits
-- Voice characteristics and speech patterns


-- 2.5 Response Guidelines
-- Guidelines for appropriate responses in different contexts


-- 2.6 Expertise Domains
-- Areas of expertise and specialized knowledge


-- 2.7 AI Scenarios
-- Scenario-specific behavior patterns for AI roleplay


-- 2.8 Conversation Flows
-- Dynamic conversation flow patterns and transitions


-- 2.9 Emoji Patterns
-- Emoji usage patterns and preferences


-- ==============================================================================
-- 3. SEMANTIC KNOWLEDGE GRAPH DATA
-- ==============================================================================
-- Character-specific facts, entities, and relationships

-- 3.1 Fact Entities


-- 3.2 Character Fact Relationships


-- Cleanup temporary table
DROP TABLE IF EXISTS temp_character_id;

COMMIT;

-- ==============================================================================
-- Export Complete
-- ==============================================================================
-- Character: Elena Rodriguez
-- Generated: 2025-10-11 18:05:45
-- Total extended data records: 0
-- 
-- Next steps:
-- 1. Review the exported data
-- 2. Test loading: ./scripts/load_dev_character.sh elena
-- 3. Commit to version control for development backup
-- ==============================================================================
