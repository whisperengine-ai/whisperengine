-- Migration: Create default assistant character for quickstart
-- This provides a ready-to-use assistant character for new deployments
-- Updated to work with existing 'characters' table schema

INSERT INTO characters (
    name, 
    normalized_name,
    occupation, 
    description, 
    archetype,
    allow_full_roleplay,
    is_active,
    created_at,
    updated_at
) VALUES (
    'AI Assistant',
    'assistant',
    'AI Assistant',
    'A helpful, knowledgeable AI assistant ready to help with questions, tasks, and conversations. Friendly, professional, and adaptable to different conversation styles.',
    'real-world',
    false,
    true,
    NOW(),
    NOW()
) ON CONFLICT (normalized_name) DO NOTHING;
