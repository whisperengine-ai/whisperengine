-- Migration: Create default assistant character for quickstart
-- This provides a ready-to-use assistant character for new deployments

INSERT INTO cdl_characters (
    name, 
    normalized_name,
    bot_name,
    occupation, 
    description, 
    character_archetype,
    allow_full_roleplay_immersion,
    is_active,
    version,
    created_at,
    updated_at
) VALUES (
    'AI Assistant',
    'assistant',
    'assistant',
    'AI Assistant',
    'A helpful, knowledgeable AI assistant ready to help with questions, tasks, and conversations. Friendly, professional, and adaptable to different conversation styles.',
    'real-world',
    false,
    true,
    1,
    NOW(),
    NOW()
) ON CONFLICT (normalized_name) DO NOTHING;
