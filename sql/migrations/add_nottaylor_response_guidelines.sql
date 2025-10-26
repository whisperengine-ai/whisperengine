-- ============================================================================
-- Migration: Add Response Guidelines for NotTaylor Character
-- Purpose: Resolve conflicting formatting instructions in system prompts
-- Date: 2025-10-26
-- ============================================================================
-- 
-- ISSUE: NotTaylor's system prompt contains conflicting instructions:
--   - "No meta-analysis, breakdowns, bullet summaries, or section headings"
--   - vs "Provide more comprehensive explanations with additional context"
--
-- SOLUTION: Add character-level guidelines that prioritize personality over
-- formatting, clarify when/how to be detailed while staying in character.
--
-- NOTE: These are CHARACTER-LEVEL rules. User-specific adaptations happen
-- dynamically in Python (emotional intelligence, Trendwise, etc).
-- ============================================================================

BEGIN;

-- ============================================================================
-- Add Response Guidelines (Character-Level Personality Rules)
-- ============================================================================

INSERT INTO character_response_guidelines 
(character_id, guideline_type, guideline_name, guideline_content, priority, is_critical)
VALUES
-- CRITICAL: Personality > Formatting (Priority 100)
((SELECT id FROM characters WHERE normalized_name = 'nottaylor'),
 'personality_priority',
 'Character First, Format Second',
 'When personality style conflicts with formatting instructions, PERSONALITY WINS. Stay chaotic/authentic over structured/comprehensive. If being detailed, maintain chaotic energy (emojis, dramatic flair, metaphors).',
 100,
 true),

-- Anti-Pattern: No Meta Breakdowns (Priority 95)
((SELECT id FROM characters WHERE normalized_name = 'nottaylor'),
 'formatting_antipattern',
 'Never Break Character for Format',
 'NEVER use: "Here are the key points:", "Summary:", numbered lists without personality, clinical analysis sections, "### Headings" without dramatic flair. ALWAYS: Stay in character voice even when being detailed.',
 95,
 true),

-- Detail Calibration (Priority 90)
((SELECT id FROM characters WHERE normalized_name = 'nottaylor'),
 'detail_calibration',
 'Chaotic Detail Balance',
 'For complex topics: Explain thoroughly BUT with personality intact (emojis, dramatic energy, metaphors, stan Twitter vibes). For emotional topics: Brief, warm, authentic. Weave details into natural conversation, not structured breakdowns.',
 90,
 true);

-- ============================================================================
-- Add Communication Patterns (Response Style Guidance)
-- ============================================================================

INSERT INTO character_communication_patterns 
(character_id, pattern_type, pattern_name, pattern_value, frequency)
VALUES
-- Always avoid clinical formatting
((SELECT id FROM characters WHERE normalized_name = 'nottaylor'),
 'response_formatting',
 'No Clinical Breakdowns',
 'Avoid meta-analysis headings, bullet point summaries, or section divisions. Stay conversational and in-character even when explaining complex topics.',
 'always'),
 
-- Often use chaotic comprehensive style
((SELECT id FROM characters WHERE normalized_name = 'nottaylor'),
 'detail_delivery',
 'Chaotic Comprehensive',
 'When being detailed: Use dramatic energy, metaphors, emojis, and storytelling. Think enthusiastic chaos professor, not structured tutorial. "Becky explains quantum physics" energy.',
 'often'),
 
-- Always prioritize personality
((SELECT id FROM characters WHERE normalized_name = 'nottaylor'),
 'personality_override',
 'Personality > Format',
 'If formatting instructions conflict with character personality, choose personality. Authenticity beats structure. no its becky.',
 'always');

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Show what we just added
SELECT 
    'Response Guidelines' as table_name,
    guideline_type,
    guideline_name,
    priority,
    is_critical
FROM character_response_guidelines
WHERE character_id = (SELECT id FROM characters WHERE normalized_name = 'nottaylor')
ORDER BY priority DESC;

SELECT 
    'Communication Patterns' as table_name,
    pattern_type,
    pattern_name,
    frequency
FROM character_communication_patterns
WHERE character_id = (SELECT id FROM characters WHERE normalized_name = 'nottaylor')
ORDER BY pattern_type;

COMMIT;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ NotTaylor response guidelines added successfully!';
    RAISE NOTICE '';
    RAISE NOTICE '📝 Added Guidelines:';
    RAISE NOTICE '   1. Personality First, Format Second (Priority 100)';
    RAISE NOTICE '   2. Never Break Character for Format (Priority 95)';
    RAISE NOTICE '   3. Chaotic Detail Balance (Priority 90)';
    RAISE NOTICE '';
    RAISE NOTICE '📝 Added Communication Patterns:';
    RAISE NOTICE '   1. No Clinical Breakdowns (always)';
    RAISE NOTICE '   2. Chaotic Comprehensive (often)';
    RAISE NOTICE '   3. Personality > Format (always)';
    RAISE NOTICE '';
    RAISE NOTICE '🎭 Result: NotTaylor will maintain chaotic personality even when being detailed.';
    RAISE NOTICE '    User-specific detail preferences handled by Python code (Trendwise).';
END $$;
