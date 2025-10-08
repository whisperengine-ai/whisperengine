-- WhisperEngine CDL Schema - Data Migration from JSON TEXT to Relational Tables
-- Date: October 7, 2025
-- Purpose: Extract data from existing JSON TEXT fields and populate new relational tables
-- WARNING: Run this AFTER 001_expand_cdl_schema_full_fidelity.sql

-- =============================================================================
-- STEP 1: Break out communication_styles.conversation_flow_guidance JSON
-- =============================================================================

-- This requires Python/application-side processing since PostgreSQL
-- would need complex JSON parsing of TEXT fields
-- See: migrate_conversation_flow_guidance.py

-- =============================================================================
-- STEP 2: Break out communication_styles.ai_identity_handling JSON  
-- =============================================================================

-- This requires Python/application-side processing
-- See: migrate_ai_identity_handling.py

-- =============================================================================
-- STEP 3: After data migration, optionally drop old JSON TEXT columns
-- =============================================================================

-- CAREFUL: Only run these after verifying data migration is complete!

-- Backup first!
-- CREATE TABLE communication_styles_backup_20251007 AS SELECT * FROM communication_styles;

-- Drop JSON TEXT columns (OPTIONAL - only after successful migration)
-- ALTER TABLE communication_styles DROP COLUMN IF EXISTS conversation_flow_guidance;
-- ALTER TABLE communication_styles DROP COLUMN IF EXISTS ai_identity_handling;

-- =============================================================================
-- STEP 4: Verification queries
-- =============================================================================

-- Check core principles migration
SELECT 
    c.name,
    COUNT(cp.id) as principle_count
FROM characters c
LEFT JOIN character_core_principles cp ON cp.character_id = c.id
WHERE c.is_active = TRUE
GROUP BY c.id, c.name
ORDER BY c.name;

-- Check conversation flow patterns
SELECT 
    c.name,
    COUNT(cfp.id) as flow_pattern_count
FROM characters c
LEFT JOIN character_conversation_flow_patterns cfp ON cfp.character_id = c.id
WHERE c.is_active = TRUE
GROUP BY c.id, c.name
ORDER BY c.name;

-- Check AI identity config
SELECT 
    c.name,
    aic.allow_full_roleplay_immersion,
    aic.philosophy
FROM characters c
LEFT JOIN character_ai_identity_config aic ON aic.character_id = c.id
WHERE c.is_active = TRUE
ORDER BY c.name;

-- Check fears/dreams/quirks (Elena-style data)
SELECT 
    c.name,
    COUNT(f.id) as fear_count,
    COUNT(d.id) as dream_count,
    COUNT(q.id) as quirk_count
FROM characters c
LEFT JOIN character_fears f ON f.character_id = c.id
LEFT JOIN character_dreams d ON d.character_id = c.id
LEFT JOIN character_quirks q ON q.character_id = c.id
WHERE c.is_active = TRUE
GROUP BY c.id, c.name
ORDER BY c.name;

-- =============================================================================
-- NOTES
-- =============================================================================

/*
The actual data migration from JSON TEXT fields to relational tables requires
Python scripts because:

1. PostgreSQL TEXT columns don't support JSON operators (they're plain strings)
2. Complex nested JSON structures need proper parsing
3. Character-specific variations in JSON structure need conditional logic

Migration workflow:
1. Run 001_expand_cdl_schema_full_fidelity.sql (creates new tables)
2. Run Python migration scripts:
   - migrate_conversation_flow_guidance.py
   - migrate_ai_identity_handling.py
   - import_full_character_data.py (for backup JSON imports)
3. Verify data with queries above
4. Optionally drop old JSON TEXT columns
5. Update application code to query new relational tables

See: scripts/migrations/ directory for Python migration scripts
*/
