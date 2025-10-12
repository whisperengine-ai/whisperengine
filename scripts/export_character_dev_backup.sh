#!/bin/bash
# ==============================================================================
# WhisperEngine Character Development Backup Export Script
# ==============================================================================
# Exports complete character data including:
# - Characters table (core definition)
# - 9 Extended Data Tables (message_triggers, cultural_expressions, etc.)
# - Semantic Knowledge Graph data (facts, entities, relationships)
#
# Usage:
#   ./scripts/export_character_dev_backup.sh <character_name>
#   ./scripts/export_character_dev_backup.sh elena
#   ./scripts/export_character_dev_backup.sh all   # Export all active characters
#
# Output: sql/characters/dev/<character_name>.sql
# ==============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_CONTAINER="postgres"
DB_USER="whisperengine"
DB_NAME="whisperengine"
OUTPUT_DIR="sql/characters/dev"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ==============================================================================
# Export Single Character Function
# ==============================================================================

export_character() {
    local CHARACTER_NAME="$1"
    local NORMALIZED_NAME="$2"
    local OUTPUT_FILE="$OUTPUT_DIR/${NORMALIZED_NAME}.sql"
    
    log_info "Exporting character: $CHARACTER_NAME (normalized: $NORMALIZED_NAME)"
    
    # Start building the SQL file
    cat > "$OUTPUT_FILE" <<EOF
-- ==============================================================================
-- WhisperEngine Character Development Backup
-- Character: $CHARACTER_NAME
-- Generated: $(date '+%Y-%m-%d %H:%M:%S')
-- ==============================================================================
-- This file contains the complete character definition including:
-- - Core character data (characters table)
-- - Extended data (9 tables: message_triggers, cultural_expressions, etc.)
-- - Semantic knowledge graph data (facts, entities, relationships)
--
-- To load this character:
--   docker exec -i postgres psql -U whisperengine -d whisperengine -f /app/sql/characters/dev/${NORMALIZED_NAME}.sql
--
-- Or use the helper script:
--   ./scripts/load_dev_character.sh ${NORMALIZED_NAME}
-- ==============================================================================

BEGIN;

-- ==============================================================================
-- 1. CORE CHARACTER DATA
-- ==============================================================================

EOF

    # Export characters table
    log_info "  Exporting core character data..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "
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
        WHERE normalized_name = '$NORMALIZED_NAME';
    " >> "$OUTPUT_FILE"

    # Add character ID variable for use in extended data
    cat >> "$OUTPUT_FILE" <<EOF

-- Get the character ID for use in extended data inserts
DO \$\$
DECLARE
    v_character_id INTEGER;
BEGIN
    SELECT id INTO v_character_id FROM characters WHERE normalized_name = '$NORMALIZED_NAME';
    
    IF v_character_id IS NULL THEN
        RAISE EXCEPTION 'Character not found: $NORMALIZED_NAME';
    END IF;
    
    -- Store in temporary table for use in subsequent inserts
    CREATE TEMP TABLE IF NOT EXISTS temp_character_id (id INTEGER);
    DELETE FROM temp_character_id;
    INSERT INTO temp_character_id VALUES (v_character_id);
END \$\$;

-- ==============================================================================
-- 2. EXTENDED DATA TABLES (9 tables)
-- ==============================================================================

-- 2.1 Message Triggers
-- Pattern-based triggers for character responses
EOF

    log_info "  Exporting message triggers..."
    TRIGGER_COUNT=$(docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "
        SELECT COUNT(*) FROM character_message_triggers cmt
        JOIN characters c ON cmt.character_id = c.id
        WHERE c.normalized_name = '$NORMALIZED_NAME';
    ")
    
    if [ "$TRIGGER_COUNT" -gt 0 ]; then
        docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "
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
            WHERE c.normalized_name = '$NORMALIZED_NAME'
            ORDER BY cmt.id;
        " >> "$OUTPUT_FILE"
        log_success "    Exported $TRIGGER_COUNT message triggers"
    else
        log_warning "No message triggers found"
    fi

    cat >> "$OUTPUT_FILE" <<EOF

-- 2.2 Cultural Expressions
-- Cultural phrases, idioms, and expressions
EOF

    log_info "  Exporting cultural expressions..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        COPY (
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
            WHERE c.normalized_name = '$NORMALIZED_NAME'
            ORDER BY cce.id
        ) TO STDOUT;
    " >> "$OUTPUT_FILE" 2>/dev/null || log_warning "No cultural expressions found"

    cat >> "$OUTPUT_FILE" <<EOF

-- 2.3 Emotional Triggers
-- Emotional responses and trigger patterns
EOF

    log_info "  Exporting emotional triggers..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        COPY (
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
            WHERE c.normalized_name = '$NORMALIZED_NAME'
            ORDER BY cet.id
        ) TO STDOUT;
    " >> "$OUTPUT_FILE" 2>/dev/null || log_warning "No emotional triggers found"

    cat >> "$OUTPUT_FILE" <<EOF

-- 2.4 Voice Traits
-- Voice characteristics and speech patterns
EOF

    log_info "  Exporting voice traits..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        COPY (
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
            WHERE c.normalized_name = '$NORMALIZED_NAME'
            ORDER BY cvt.id
        ) TO STDOUT;
    " >> "$OUTPUT_FILE" 2>/dev/null || log_warning "No voice traits found"

    cat >> "$OUTPUT_FILE" <<EOF

-- 2.5 Response Guidelines
-- Guidelines for appropriate responses in different contexts
EOF

    log_info "  Exporting response guidelines..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        COPY (
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
            WHERE c.normalized_name = '$NORMALIZED_NAME'
            ORDER BY crg.id
        ) TO STDOUT;
    " >> "$OUTPUT_FILE" 2>/dev/null || log_warning "No response guidelines found"

    cat >> "$OUTPUT_FILE" <<EOF

-- 2.6 Expertise Domains
-- Areas of expertise and specialized knowledge
EOF

    log_info "  Exporting expertise domains..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        COPY (
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
            WHERE c.normalized_name = '$NORMALIZED_NAME'
            ORDER BY ced.id
        ) TO STDOUT;
    " >> "$OUTPUT_FILE" 2>/dev/null || log_warning "No expertise domains found"

    cat >> "$OUTPUT_FILE" <<EOF

-- 2.7 AI Scenarios
-- Scenario-specific behavior patterns for AI roleplay
EOF

    log_info "  Exporting AI scenarios..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        COPY (
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
            WHERE c.normalized_name = '$NORMALIZED_NAME'
            ORDER BY cas.id
        ) TO STDOUT;
    " >> "$OUTPUT_FILE" 2>/dev/null || log_warning "No AI scenarios found"

    cat >> "$OUTPUT_FILE" <<EOF

-- 2.8 Conversation Flows
-- Dynamic conversation flow patterns and transitions
EOF

    log_info "  Exporting conversation flows..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        COPY (
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
            WHERE c.normalized_name = '$NORMALIZED_NAME'
            ORDER BY ccf.id
        ) TO STDOUT;
    " >> "$OUTPUT_FILE" 2>/dev/null || log_warning "No conversation flows found"

    cat >> "$OUTPUT_FILE" <<EOF

-- 2.9 Emoji Patterns
-- Emoji usage patterns and preferences
EOF

    log_info "  Exporting emoji patterns..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        COPY (
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
            WHERE c.normalized_name = '$NORMALIZED_NAME'
            ORDER BY cep.id
        ) TO STDOUT;
    " >> "$OUTPUT_FILE" 2>/dev/null || log_warning "No emoji patterns found"

    cat >> "$OUTPUT_FILE" <<EOF

-- ==============================================================================
-- 3. SEMANTIC KNOWLEDGE GRAPH DATA
-- ==============================================================================
-- Character-specific facts, entities, and relationships

-- 3.1 Fact Entities
EOF

    log_info "  Exporting fact entities..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        COPY (
            SELECT 
                'INSERT INTO fact_entities (entity_name, entity_type, entity_metadata, confidence, created_at, character_name) VALUES (' ||
                quote_literal(entity_name) || ', ' ||
                quote_literal(COALESCE(entity_type, 'general')) || ', ' ||
                quote_literal(COALESCE(entity_metadata::text, '{}')) || ', ' ||
                COALESCE(confidence, 1.0) || ', ' ||
                quote_literal(created_at::text) || ', ' ||
                quote_literal(character_name) ||
                ') ON CONFLICT DO NOTHING;'
            FROM fact_entities
            WHERE character_name = '$NORMALIZED_NAME'
            ORDER BY id
        ) TO STDOUT;
    " >> "$OUTPUT_FILE" 2>/dev/null || log_warning "No fact entities found"

    cat >> "$OUTPUT_FILE" <<EOF

-- 3.2 Character Fact Relationships
EOF

    log_info "  Exporting character fact relationships..."
    docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        COPY (
            SELECT 
                'INSERT INTO character_fact_relationships (character_name, entity_name, relationship_type, confidence, metadata, last_mentioned_at) VALUES (' ||
                quote_literal(character_name) || ', ' ||
                quote_literal(entity_name) || ', ' ||
                quote_literal(relationship_type) || ', ' ||
                COALESCE(confidence, 1.0) || ', ' ||
                quote_literal(COALESCE(metadata::text, '{}')) || ', ' ||
                quote_literal(COALESCE(last_mentioned_at::text, CURRENT_TIMESTAMP::text)) ||
                ') ON CONFLICT DO NOTHING;'
            FROM character_fact_relationships
            WHERE character_name = '$NORMALIZED_NAME'
            ORDER BY id
        ) TO STDOUT;
    " >> "$OUTPUT_FILE" 2>/dev/null || log_warning "No character fact relationships found"

    cat >> "$OUTPUT_FILE" <<EOF

-- Cleanup temporary table
DROP TABLE IF EXISTS temp_character_id;

COMMIT;

-- ==============================================================================
-- Export Complete
-- ==============================================================================
-- Character: $CHARACTER_NAME
-- Generated: $(date '+%Y-%m-%d %H:%M:%S')
-- 
-- Next steps:
-- 1. Review the exported data
-- 2. Test loading: ./scripts/load_dev_character.sh ${NORMALIZED_NAME}
-- 3. Commit to version control for development backup
-- ==============================================================================
EOF

    log_success "Exported character: $CHARACTER_NAME → $OUTPUT_FILE"
    
    # Show statistics
    local TOTAL_LINES=$(wc -l < "$OUTPUT_FILE")
    local INSERT_COUNT=$(grep -c "INSERT INTO" "$OUTPUT_FILE" || true)
    log_info "  Statistics: $INSERT_COUNT INSERT statements, $TOTAL_LINES total lines"
}

# ==============================================================================
# Main Script Logic
# ==============================================================================

if [ $# -eq 0 ]; then
    log_error "Usage: $0 <character_name|all>"
    log_info "Examples:"
    log_info "  $0 elena      # Export Elena character"
    log_info "  $0 all        # Export all active characters"
    exit 1
fi

CHARACTER_ARG="$1"

# Check if Docker container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    log_error "PostgreSQL container '$DB_CONTAINER' is not running"
    log_info "Start it with: docker-compose up -d postgres"
    exit 1
fi

if [ "$CHARACTER_ARG" = "all" ]; then
    log_info "Exporting ALL active characters..."
    
    # Get list of all active characters
    CHARACTERS=$(docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT name || '|||' || normalized_name 
        FROM characters 
        WHERE is_active = true 
        ORDER BY name;
    ")
    
    EXPORT_COUNT=0
    while IFS= read -r CHAR_DATA; do
        # Trim whitespace
        CHAR_DATA=$(echo "$CHAR_DATA" | xargs)
        
        if [ -z "$CHAR_DATA" ]; then
            continue
        fi
        
        CHARACTER_NAME=$(echo "$CHAR_DATA" | cut -d'|' -f1)
        NORMALIZED_NAME=$(echo "$CHAR_DATA" | cut -d'|' -f4)
        
        if [ -n "$CHARACTER_NAME" ] && [ -n "$NORMALIZED_NAME" ]; then
            export_character "$CHARACTER_NAME" "$NORMALIZED_NAME"
            EXPORT_COUNT=$((EXPORT_COUNT + 1))
        fi
    done <<< "$CHARACTERS"
    
    log_success "Exported $EXPORT_COUNT characters to $OUTPUT_DIR/"
    
else
    # Export single character
    NORMALIZED_NAME="$CHARACTER_ARG"
    
    # Get character full name
    CHARACTER_NAME=$(docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "
        SELECT name FROM characters WHERE normalized_name = '$NORMALIZED_NAME';
    " | xargs)
    
    if [ -z "$CHARACTER_NAME" ]; then
        log_error "Character not found: $NORMALIZED_NAME"
        log_info "Available characters:"
        docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
            SELECT normalized_name, name FROM characters WHERE is_active = true ORDER BY name;
        "
        exit 1
    fi
    
    export_character "$CHARACTER_NAME" "$NORMALIZED_NAME"
fi

log_success "✨ Character export complete!"
