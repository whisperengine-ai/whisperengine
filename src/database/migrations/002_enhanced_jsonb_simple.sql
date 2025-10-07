-- Simplified Enhanced CDL JSONB Schema Migration
-- Creates new JSONB-based character storage without enum dependencies

-- ============================================================================
-- CREATE ENUM TYPES FIRST
-- ============================================================================

-- Character archetype classification
CREATE TYPE character_archetype_enum AS ENUM (
    'real_world',           -- Elena, Marcus, Jake, Ryan, Gabriel, Sophia
    'fantasy_mystical',     -- Dream, Aethys  
    'narrative_ai'          -- Dotty
);

-- Workflow status tracking
CREATE TYPE workflow_status_enum AS ENUM (
    'active',
    'paused', 
    'completed',
    'failed',
    'cancelled'
);

-- ============================================================================
-- NEW ENHANCED JSONB SCHEMA
-- ============================================================================

-- Characters table with JSONB approach
CREATE TABLE characters_v2 (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL UNIQUE,
    bot_name VARCHAR(100),
    
    -- Character classification
    archetype character_archetype_enum DEFAULT 'real_world',
    allow_full_roleplay BOOLEAN DEFAULT false,
    
    -- Flexible JSONB storage for all CDL data
    cdl_data JSONB NOT NULL,
    
    -- Workflow support
    workflow_data JSONB DEFAULT '{}',
    
    -- Metadata and tracking
    metadata JSONB DEFAULT '{}',
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

-- Workflow instances for state management
CREATE TABLE workflow_instances_v2 (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT REFERENCES characters_v2(id) ON DELETE CASCADE,
    workflow_name VARCHAR(200) NOT NULL,
    current_state VARCHAR(100) NOT NULL,
    status workflow_status_enum DEFAULT 'active',
    context_data JSONB DEFAULT '{}',
    state_history JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(character_id, workflow_name)
);

-- ============================================================================
-- PERFORMANCE OPTIMIZATION
-- ============================================================================

-- GIN indexes for fast JSONB queries
CREATE INDEX CONCURRENTLY idx_characters_v2_cdl_gin ON characters_v2 USING gin (cdl_data);
CREATE INDEX CONCURRENTLY idx_characters_v2_workflow_gin ON characters_v2 USING gin (workflow_data);
CREATE INDEX CONCURRENTLY idx_characters_v2_normalized_name ON characters_v2(normalized_name);
CREATE INDEX CONCURRENTLY idx_characters_v2_bot_name ON characters_v2(bot_name);

-- Workflow instance indexes
CREATE INDEX CONCURRENTLY idx_workflow_instances_v2_character ON workflow_instances_v2(character_id);
CREATE INDEX CONCURRENTLY idx_workflow_instances_v2_name ON workflow_instances_v2(workflow_name);
CREATE INDEX CONCURRENTLY idx_workflow_instances_v2_status ON workflow_instances_v2(status);

-- ============================================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ============================================================================

-- Fast character profile loading
CREATE MATERIALIZED VIEW character_profiles_v2 AS
SELECT 
    c.id,
    c.name,
    c.normalized_name,
    c.bot_name,
    c.archetype,
    c.allow_full_roleplay,
    c.cdl_data,
    c.workflow_data,
    c.metadata,
    c.created_at,
    c.updated_at,
    c.version,
    -- Aggregate active workflows
    COALESCE(
        array_agg(
            wi.workflow_name
        ) FILTER (WHERE wi.status = 'active'), 
        ARRAY[]::VARCHAR[]
    ) as active_workflows
FROM characters_v2 c
LEFT JOIN workflow_instances_v2 wi ON c.id = wi.character_id AND wi.status = 'active'
GROUP BY c.id, c.name, c.normalized_name, c.bot_name, c.archetype, 
         c.allow_full_roleplay, c.cdl_data, c.workflow_data, c.metadata,
         c.created_at, c.updated_at, c.version;

-- Create unique index on materialized view
CREATE UNIQUE INDEX idx_character_profiles_v2_id ON character_profiles_v2(id);
CREATE INDEX idx_character_profiles_v2_normalized_name ON character_profiles_v2(normalized_name);

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Upsert character function
CREATE OR REPLACE FUNCTION upsert_character_v2(
    p_name VARCHAR(200),
    p_normalized_name VARCHAR(200),
    p_bot_name VARCHAR(100),
    p_archetype character_archetype_enum,
    p_cdl_data JSONB,
    p_workflow_data JSONB DEFAULT '{}',
    p_metadata JSONB DEFAULT '{}'
) RETURNS BIGINT AS $$
DECLARE
    char_id BIGINT;
BEGIN
    -- Try to update existing character
    UPDATE characters_v2 
    SET 
        name = p_name,
        bot_name = p_bot_name,
        archetype = p_archetype,
        cdl_data = p_cdl_data,
        workflow_data = p_workflow_data,
        metadata = p_metadata,
        updated_at = NOW(),
        version = version + 1
    WHERE normalized_name = p_normalized_name
    RETURNING id INTO char_id;
    
    -- If no update occurred, insert new character
    IF char_id IS NULL THEN
        INSERT INTO characters_v2 (
            name, normalized_name, bot_name, archetype, 
            cdl_data, workflow_data, metadata
        ) VALUES (
            p_name, p_normalized_name, p_bot_name, p_archetype,
            p_cdl_data, p_workflow_data, p_metadata
        ) RETURNING id INTO char_id;
    END IF;
    
    -- Refresh materialized view
    REFRESH MATERIALIZED VIEW CONCURRENTLY character_profiles_v2;
    
    RETURN char_id;
END;
$$ LANGUAGE plpgsql;

-- Get character CDL data function
CREATE OR REPLACE FUNCTION get_character_cdl_v2(p_normalized_name VARCHAR(200))
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT cdl_data INTO result
    FROM character_profiles_v2
    WHERE normalized_name = p_normalized_name;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Update workflow state function
CREATE OR REPLACE FUNCTION update_workflow_state_v2(
    p_character_id BIGINT,
    p_workflow_name VARCHAR(200),
    p_new_state VARCHAR(100),
    p_context_data JSONB DEFAULT '{}'
) RETURNS BOOLEAN AS $$
DECLARE
    old_state VARCHAR(100);
    state_entry JSONB;
BEGIN
    -- Get current state
    SELECT current_state INTO old_state
    FROM workflow_instances_v2
    WHERE character_id = p_character_id AND workflow_name = p_workflow_name;
    
    -- Create state history entry
    state_entry := jsonb_build_object(
        'from_state', old_state,
        'to_state', p_new_state,
        'timestamp', extract(epoch from now()),
        'context', p_context_data
    );
    
    -- Update workflow instance
    UPDATE workflow_instances_v2
    SET 
        current_state = p_new_state,
        context_data = p_context_data,
        state_history = state_history || state_entry,
        updated_at = NOW()
    WHERE character_id = p_character_id AND workflow_name = p_workflow_name;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '🎭 Enhanced JSONB CDL Schema migration completed successfully!';
    RAISE NOTICE '✅ Created characters_v2 table with JSONB storage';
    RAISE NOTICE '✅ Created workflow_instances_v2 for state management';
    RAISE NOTICE '✅ Created performance indexes and materialized views';
    RAISE NOTICE '✅ Created utility functions for character management';
    RAISE NOTICE '🚀 Ready for character data import and testing!';
END $$;