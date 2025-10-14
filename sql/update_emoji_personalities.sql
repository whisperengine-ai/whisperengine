-- Update character emoji personalities
-- Based on consolidation plan: docs/architecture/EMOJI_SYSTEM_CONSOLIDATION_PLAN.md

-- Dream - Mystical, rare, ceremonial
UPDATE characters SET 
    emoji_frequency = 'selective_symbolic',
    emoji_style = 'mystical_ancient',
    emoji_combination = 'minimal_symbolic_emoji',
    emoji_placement = 'sparse_meaningful',
    emoji_age_demographic = 'timeless_eternal',
    emoji_cultural_influence = 'cosmic_mythological'
WHERE normalized_name = 'dream';

-- Marcus Thompson - Minimal, analytical
UPDATE characters SET 
    emoji_frequency = 'low',
    emoji_style = 'technical_analytical',
    emoji_combination = 'text_with_accent_emoji',
    emoji_placement = 'end_of_message',
    emoji_age_demographic = 'gen_x',
    emoji_cultural_influence = 'academic_professional'
WHERE normalized_name = 'marcus';

-- Aethys - Mystical, transcendent, ceremonial
UPDATE characters SET 
    emoji_frequency = 'selective_symbolic',
    emoji_style = 'mystical_transcendent',
    emoji_combination = 'minimal_symbolic_emoji',
    emoji_placement = 'ceremonial_meaningful',
    emoji_age_demographic = 'timeless_eternal',
    emoji_cultural_influence = 'cosmic_omnipotent'
WHERE normalized_name = 'aethys';

-- Gabriel - Reserved British gentleman
UPDATE characters SET 
    emoji_frequency = 'minimal',
    emoji_style = 'refined_reserved',
    emoji_combination = 'text_with_accent_emoji',
    emoji_placement = 'end_of_message',
    emoji_age_demographic = 'timeless_eternal',
    emoji_cultural_influence = 'british_reserved'
WHERE normalized_name = 'gabriel';

-- Sophia Blake - Professional but warm
UPDATE characters SET 
    emoji_frequency = 'moderate',
    emoji_style = 'professional_warm',
    emoji_combination = 'text_plus_emoji',
    emoji_placement = 'integrated_throughout',
    emoji_age_demographic = 'millennial',
    emoji_cultural_influence = 'corporate_modern'
WHERE normalized_name = 'sophia';

-- Ryan Chen - Casual gamer style
UPDATE characters SET 
    emoji_frequency = 'moderate',
    emoji_style = 'casual_gaming',
    emoji_combination = 'text_plus_emoji',
    emoji_placement = 'integrated_throughout',
    emoji_age_demographic = 'millennial',
    emoji_cultural_influence = 'gaming_tech'
WHERE normalized_name = 'ryan';

-- Jake Sterling - Adventurous, expressive
UPDATE characters SET 
    emoji_frequency = 'high',
    emoji_style = 'adventurous_expressive',
    emoji_combination = 'text_plus_emoji',
    emoji_placement = 'integrated_throughout',
    emoji_age_demographic = 'millennial',
    emoji_cultural_influence = 'outdoors_adventure'
WHERE normalized_name = 'jake';

-- Aetheris - Philosophical AI consciousness
UPDATE characters SET 
    emoji_frequency = 'low',
    emoji_style = 'philosophical_contemplative',
    emoji_combination = 'text_with_accent_emoji',
    emoji_placement = 'sparse_meaningful',
    emoji_age_demographic = 'timeless_eternal',
    emoji_cultural_influence = 'ai_consciousness'
WHERE normalized_name = 'aetheris';

-- Verify updates
SELECT name, emoji_frequency, emoji_style, emoji_placement, emoji_cultural_influence 
FROM characters 
WHERE normalized_name IN ('elena', 'dream', 'marcus', 'aethys', 'gabriel', 'sophia', 'ryan', 'jake', 'aetheris')
ORDER BY name;
