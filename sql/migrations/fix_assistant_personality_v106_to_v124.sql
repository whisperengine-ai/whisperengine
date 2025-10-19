-- ============================================================================
-- Migration Fix: Restore Assistant Personality for v1.0.6 → v1.0.24 Upgrades
-- ============================================================================
-- 
-- PROBLEM: Users upgrading from v1.0.6 to v1.0.24 lost their assistant's
--          personality because new CDL tables (character_personalities,
--          character_voices, character_modes) were added but not populated
--          for existing characters.
--
-- SOLUTION: This script populates the missing CDL data for the "assistant"
--           character that exists but has no personality traits.
--
-- SAFE TO RUN: Uses INSERT...ON CONFLICT to update existing or create new
--              Won't duplicate data or break existing installations
--
-- USAGE:
--   psql -h localhost -p 5433 -U whisperengine -d whisperengine \
--        -f sql/migrations/fix_assistant_personality_v106_to_v124.sql
--
-- OR via Docker:
--   docker exec -i whisperengine-postgres psql -U whisperengine -d whisperengine \
--        < sql/migrations/fix_assistant_personality_v106_to_v124.sql
--
-- ============================================================================

SET search_path = public;

\echo ''
\echo '============================================================================'
\echo 'WhisperEngine Assistant Personality Restoration'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- Step 1: Verify Assistant Character Exists
-- ============================================================================

\echo 'Step 1: Checking for assistant character...'

DO $$
DECLARE
    char_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO char_count 
    FROM characters 
    WHERE normalized_name = 'assistant';
    
    IF char_count = 0 THEN
        RAISE EXCEPTION 'ERROR: No "assistant" character found in database. Please run sql/01_seed_data.sql first.';
    ELSE
        RAISE NOTICE '✅ Found assistant character (ID: %)', (SELECT id FROM characters WHERE normalized_name = 'assistant');
    END IF;
END $$;

-- ============================================================================
-- Step 2: Add/Update Character Personality (Big Five Traits)
-- ============================================================================

\echo ''
\echo 'Step 2: Adding personality traits...'

INSERT INTO character_personalities (
    character_id,
    openness,
    conscientiousness,
    extraversion,
    agreeableness,
    neuroticism,
    created_at
)
SELECT 
    id,
    0.80,  -- Openness: Intellectually curious and open to new ideas
    0.90,  -- Conscientiousness: Organized, reliable, thorough
    0.70,  -- Extraversion: Socially engaged but balanced
    0.90,  -- Agreeableness: Cooperative, empathetic, helpful
    0.20,  -- Neuroticism: Emotionally stable and calm
    NOW()
FROM characters 
WHERE normalized_name = 'assistant'
ON CONFLICT (character_id) 
DO UPDATE SET
    openness = EXCLUDED.openness,
    conscientiousness = EXCLUDED.conscientiousness,
    extraversion = EXCLUDED.extraversion,
    agreeableness = EXCLUDED.agreeableness,
    neuroticism = EXCLUDED.neuroticism,
    updated_at = NOW();

\echo '✅ Personality traits configured'

-- ============================================================================
-- Step 3: Add/Update Character Voice (Speaking Style)
-- ============================================================================

\echo ''
\echo 'Step 3: Adding voice characteristics...'

INSERT INTO character_voices (
    character_id,
    tone,
    pace,
    volume,
    accent,
    vocabulary_level,
    formality_level,
    humor_style,
    created_at
)
SELECT 
    id,
    'warm and professional',
    'moderate',
    'normal',
    'neutral',
    'accessible',
    'professional',
    'subtle and situational',
    NOW()
FROM characters 
WHERE normalized_name = 'assistant'
ON CONFLICT (character_id) 
DO UPDATE SET
    tone = EXCLUDED.tone,
    pace = EXCLUDED.pace,
    volume = EXCLUDED.volume,
    accent = EXCLUDED.accent,
    vocabulary_level = EXCLUDED.vocabulary_level,
    formality_level = EXCLUDED.formality_level,
    humor_style = EXCLUDED.humor_style,
    updated_at = NOW();

\echo '✅ Voice characteristics configured'

-- ============================================================================
-- Step 4: Add/Update Character Mode (Conversation Style)
-- ============================================================================

\echo ''
\echo 'Step 4: Adding conversation mode...'

INSERT INTO character_modes (
    character_id,
    mode_name,
    description,
    is_default,
    activation_keywords,
    created_at
)
SELECT 
    id,
    'helpful_assistant',
    'Balanced, supportive assistance adapting to user needs',
    true,
    ARRAY['help', 'assist', 'question', 'support'],
    NOW()
FROM characters 
WHERE normalized_name = 'assistant'
ON CONFLICT (character_id, mode_name) 
DO UPDATE SET
    description = EXCLUDED.description,
    is_default = EXCLUDED.is_default,
    activation_keywords = EXCLUDED.activation_keywords,
    updated_at = NOW();

\echo '✅ Conversation mode configured'

-- ============================================================================
-- Step 5: Add/Update Communication Style Preferences
-- ============================================================================

\echo ''
\echo 'Step 5: Adding communication style...'

INSERT INTO communication_styles (
    character_id,
    response_length_preference,
    emoji_usage,
    punctuation_style,
    paragraph_style,
    created_at
)
SELECT 
    id,
    'medium',
    'moderate',
    'standard',
    'structured',
    NOW()
FROM characters 
WHERE normalized_name = 'assistant'
ON CONFLICT (character_id) 
DO UPDATE SET
    response_length_preference = EXCLUDED.response_length_preference,
    emoji_usage = EXCLUDED.emoji_usage,
    punctuation_style = EXCLUDED.punctuation_style,
    paragraph_style = EXCLUDED.paragraph_style,
    updated_at = NOW();

\echo '✅ Communication style configured'

-- ============================================================================
-- Step 6: Verification - Check All CDL Components
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'Verification: Assistant Character CDL Completeness'
\echo '============================================================================'
\echo ''

SELECT 
    c.name AS "Character Name",
    c.normalized_name AS "Normalized Name",
    CASE WHEN cp.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END AS "Has Personality",
    CASE WHEN cv.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END AS "Has Voice",
    CASE WHEN cm.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END AS "Has Mode",
    CASE WHEN cs.id IS NOT NULL THEN '✅ YES' ELSE '❌ MISSING' END AS "Has Communication Style"
FROM characters c
LEFT JOIN character_personalities cp ON c.id = cp.character_id
LEFT JOIN character_voices cv ON c.id = cv.character_id
LEFT JOIN character_modes cm ON c.id = cm.character_id AND cm.is_default = true
LEFT JOIN communication_styles cs ON c.id = cs.character_id
WHERE c.normalized_name = 'assistant';

\echo ''
\echo '============================================================================'
\echo 'Migration Complete!'
\echo '============================================================================'
\echo ''
\echo 'Next Steps:'
\echo '  1. Restart your WhisperEngine bot'
\echo '  2. Test a conversation - personality should be restored'
\echo '  3. Check logs for warnings about missing character data'
\echo ''
\echo 'If you still see personality issues, check:'
\echo '  - DISCORD_BOT_NAME environment variable is set to "assistant"'
\echo '  - Database connection is working (check bot startup logs)'
\echo '  - No errors in the output above'
\echo ''
