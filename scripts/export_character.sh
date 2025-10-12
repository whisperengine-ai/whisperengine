#!/bin/bash
# Export a character and all their CDL rich data to a SQL file
# Usage: ./scripts/export_character.sh CHARACTER_NAME [output_file.sql]

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 CHARACTER_NAME [output_file.sql]"
    echo "Example: $0 elena sql/characters/dev/elena_rodriguez.sql"
    exit 1
fi

CHARACTER_NAME="$1"
OUTPUT_FILE="${2:-sql/characters/dev/${CHARACTER_NAME}.sql}"

echo "📤 Exporting character: $CHARACTER_NAME"
echo "📁 Output: $OUTPUT_FILE"

# Ensure directory exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Create SQL file header
cat > "$OUTPUT_FILE" << 'HEADER'
-- Character Export: ${CHARACTER_NAME}
-- Generated: $(date)
-- This file contains the character definition and all associated CDL rich data
-- 
-- To load this character:
--   docker exec postgres psql -U whisperengine -d whisperengine -f /app/${OUTPUT_FILE#*/}
--
-- Or use the helper script:
--   ./scripts/load_dev_character.sh ${CHARACTER_NAME}

BEGIN;

HEADER

# Export the base character record
echo "  → Exporting base character record..."
docker exec postgres psql -U whisperengine -d whisperengine -t -c "
SELECT 
    'INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active) VALUES (' ||
    quote_literal(name) || ', ' ||
    quote_literal(normalized_name) || ', ' ||
    COALESCE(quote_literal(occupation), 'NULL') || ', ' ||
    COALESCE(quote_literal(description), 'NULL') || ', ' ||
    COALESCE(quote_literal(archetype), 'NULL') || ', ' ||
    COALESCE(allow_full_roleplay::text, 'false') || ', ' ||
    'true);'
FROM characters 
WHERE normalized_name = '$CHARACTER_NAME' AND is_active = true
LIMIT 1;
" >> "$OUTPUT_FILE"

# Get character ID for foreign key references
CHARACTER_ID=$(docker exec postgres psql -U whisperengine -d whisperengine -t -c "
SELECT id FROM characters WHERE normalized_name = '$CHARACTER_NAME' AND is_active = true LIMIT 1;
" | xargs)

if [ -z "$CHARACTER_ID" ]; then
    echo "❌ Character not found: $CHARACTER_NAME"
    rm "$OUTPUT_FILE"
    exit 1
fi

echo "  → Character ID: $CHARACTER_ID"

# Export character_relationships
echo "  → Exporting relationships..."
docker exec postgres psql -U whisperengine -d whisperengine -c "
COPY (
    SELECT 
        'INSERT INTO character_relationships (character_id, related_entity, relationship_type, relationship_strength, description, communication_style, connection_nature, recognition_pattern, status) VALUES (' ||
        '(SELECT id FROM characters WHERE normalized_name = ''$CHARACTER_NAME'' LIMIT 1), ' ||
        quote_literal(related_entity) || ', ' ||
        quote_literal(relationship_type) || ', ' ||
        relationship_strength || ', ' ||
        COALESCE(quote_literal(description), 'NULL') || ', ' ||
        COALESCE(quote_literal(communication_style), 'NULL') || ', ' ||
        COALESCE(quote_literal(connection_nature), 'NULL') || ', ' ||
        COALESCE(quote_literal(recognition_pattern), 'NULL') || ', ' ||
        COALESCE(quote_literal(status), '''active''') || ');'
    FROM character_relationships
    WHERE character_id = $CHARACTER_ID
) TO STDOUT;
" >> "$OUTPUT_FILE" 2>/dev/null || echo "-- No relationships found"

# Export character_behavioral_triggers
echo "  → Exporting behavioral triggers..."
docker exec postgres psql -U whisperengine -d whisperengine -c "
COPY (
    SELECT 
        'INSERT INTO character_behavioral_triggers (character_id, trigger_category, trigger_value, response_type, response_description, intensity_level, priority) VALUES (' ||
        '(SELECT id FROM characters WHERE normalized_name = ''$CHARACTER_NAME'' LIMIT 1), ' ||
        quote_literal(trigger_category) || ', ' ||
        quote_literal(trigger_value) || ', ' ||
        quote_literal(response_type) || ', ' ||
        COALESCE(quote_literal(response_description), 'NULL') || ', ' ||
        COALESCE(intensity_level, 5) || ', ' ||
        COALESCE(priority, 50) || ');'
    FROM character_behavioral_triggers
    WHERE character_id = $CHARACTER_ID
) TO STDOUT;
" >> "$OUTPUT_FILE" 2>/dev/null || echo "-- No behavioral triggers found"

# Export character_speech_patterns
echo "  → Exporting speech patterns..."
docker exec postgres psql -U whisperengine -d whisperengine -c "
COPY (
    SELECT 
        'INSERT INTO character_speech_patterns (character_id, pattern_category, pattern_value, usage_context, frequency, priority) VALUES (' ||
        '(SELECT id FROM characters WHERE normalized_name = ''$CHARACTER_NAME'' LIMIT 1), ' ||
        quote_literal(pattern_category) || ', ' ||
        quote_literal(pattern_value) || ', ' ||
        COALESCE(quote_literal(usage_context), 'NULL') || ', ' ||
        COALESCE(quote_literal(frequency), '''medium''') || ', ' ||
        COALESCE(priority, 50) || ');'
    FROM character_speech_patterns
    WHERE character_id = $CHARACTER_ID
) TO STDOUT;
" >> "$OUTPUT_FILE" 2>/dev/null || echo "-- No speech patterns found"

# Export character_conversation_flows
echo "  → Exporting conversation flows..."
docker exec postgres psql -U whisperengine -d whisperengine -c "
COPY (
    SELECT 
        'INSERT INTO character_conversation_flows (character_id, flow_name, flow_type, energy_level, approach_description, transition_style, priority) VALUES (' ||
        '(SELECT id FROM characters WHERE normalized_name = ''$CHARACTER_NAME'' LIMIT 1), ' ||
        quote_literal(flow_name) || ', ' ||
        quote_literal(flow_type) || ', ' ||
        quote_literal(energy_level) || ', ' ||
        COALESCE(quote_literal(approach_description), 'NULL') || ', ' ||
        COALESCE(quote_literal(transition_style), 'NULL') || ', ' ||
        COALESCE(priority, 50) || ');'
    FROM character_conversation_flows
    WHERE character_id = $CHARACTER_ID
) TO STDOUT;
" >> "$OUTPUT_FILE" 2>/dev/null || echo "-- No conversation flows found"

# Add commit
echo -e "\nCOMMIT;" >> "$OUTPUT_FILE"

echo "✅ Character exported successfully!"
echo "📄 File: $OUTPUT_FILE"
echo ""
echo "To load this character:"
echo "  docker exec postgres psql -U whisperengine -d whisperengine -f /app/${OUTPUT_FILE#*/}"
echo "  or: ./scripts/load_dev_character.sh $CHARACTER_NAME"
