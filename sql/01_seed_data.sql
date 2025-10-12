-- ============================================================================
-- WhisperEngine Seed Data
-- ============================================================================
-- Initial data for new deployments
-- Safe to run multiple times (uses ON CONFLICT DO NOTHING)
-- ============================================================================

-- Set search_path to public schema to ensure tables are found
-- This is critical because 00_init.sql sets search_path to empty string
SET search_path = public;

-- ============================================================================
-- Default AI Assistant Character for Quickstart
-- ============================================================================
--
-- This creates a ready-to-use AI Assistant character for new deployments.
-- Users can start chatting immediately without needing to import characters.
--

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
    'real_world',
    false,
    true,
    NOW(),
    NOW()
) ON CONFLICT (normalized_name) DO NOTHING;

-- ============================================================================
-- Add additional seed data below as needed
-- ============================================================================

