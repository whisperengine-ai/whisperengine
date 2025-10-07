-- ============================================================================
-- WhisperEngine CDL Enhanced JSONB Schema
-- Simplified, flexible approach using PostgreSQL JSONB for character data
-- ============================================================================

-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS cdl_personal_knowledge CASCADE;
DROP TABLE IF EXISTS cdl_anti_patterns CASCADE;
DROP TABLE IF EXISTS cdl_values CASCADE;
DROP TABLE IF EXISTS cdl_communication_styles CASCADE;
DROP TABLE IF EXISTS cdl_personality_traits CASCADE;
DROP TABLE IF EXISTS cdl_evolution_history CASCADE;
DROP TABLE IF EXISTS cdl_interaction_modes CASCADE;
DROP TABLE IF EXISTS cdl_characters CASCADE;

-- Drop existing views
DROP VIEW IF EXISTS cdl_character_profiles CASCADE;

-- ============================================================================
-- CORE TABLES - Simplified JSONB approach
-- ============================================================================

-- Characters table - Core character registry with flexible JSONB data
CREATE TABLE characters (
    id BIGSERIAL PRIMARY KEY,
    
    -- Basic identification
    name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL UNIQUE,
    display_name VARCHAR(200),
    bot_name VARCHAR(100),
    
    -- Character classification
    archetype character_archetype_enum DEFAULT 'real_world',
    allow_full_roleplay BOOLEAN DEFAULT false,
    
    -- All CDL data as flexible JSONB (personality, communication, values, etc.)
    cdl_data JSONB NOT NULL DEFAULT '{}',
    
    -- Workflow definitions as JSONB (state machines, triggers, etc.)
    workflow_data JSONB DEFAULT '{}',
    
    -- Character metadata
    metadata JSONB DEFAULT '{}',
    
    -- Status and versioning
    status character_status_enum DEFAULT 'active',
    version INTEGER DEFAULT 1,
    schema_version VARCHAR(20) DEFAULT '2.0',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),
    
    -- Constraints
    CONSTRAINT characters_name_check CHECK (length(name) >= 1),
    CONSTRAINT characters_normalized_name_check CHECK (normalized_name ~ '^[a-z0-9_]+$'),
    CONSTRAINT characters_cdl_data_check CHECK (jsonb_typeof(cdl_data) = 'object'),
    CONSTRAINT characters_workflow_data_check CHECK (jsonb_typeof(workflow_data) = 'object')
);

-- ============================================================================
-- WORKFLOW EXECUTION TRACKING - Relational for ACID guarantees
-- ============================================================================

-- Active workflow instances - Track running workflow instances for users
CREATE TABLE workflow_instances (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Instance identification
    user_id VARCHAR(200) NOT NULL,
    session_id VARCHAR(200),
    workflow_name VARCHAR(200) NOT NULL,
    instance_key VARCHAR(200), -- Unique key for this instance
    
    -- Current state (stored as JSONB for flexibility)
    current_state JSONB NOT NULL DEFAULT '{}',
    
    -- Instance context and data
    context_data JSONB DEFAULT '{}',
    instance_data JSONB DEFAULT '{}',
    
    -- Status tracking
    status workflow_status_enum DEFAULT 'active',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Timeout tracking
    timeout_at TIMESTAMPTZ,
    
    UNIQUE(user_id, character_id, workflow_name, instance_key)
);

-- Workflow execution log - Audit trail of workflow transitions and actions
CREATE TABLE workflow_execution_log (
    id BIGSERIAL PRIMARY KEY,
    workflow_instance_id BIGINT NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    
    -- Execution details
    event_type workflow_event_enum NOT NULL,
    event_data JSONB DEFAULT '{}',
    
    -- Event context
    trigger_message TEXT,
    action_executed VARCHAR(200),
    action_result JSONB DEFAULT '{}',
    
    -- Performance data
    execution_time_ms INTEGER,
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- CHARACTER CHANGE TRACKING - Simple audit system
-- ============================================================================

-- Character versions - Complete versioning system
CREATE TABLE character_versions (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    
    -- Version metadata
    version_name VARCHAR(200),
    description TEXT,
    change_summary JSONB DEFAULT '{}',
    
    -- Complete character snapshot
    character_snapshot JSONB NOT NULL,
    
    -- Version relationships
    parent_version_id BIGINT REFERENCES character_versions(id),
    is_active BOOLEAN DEFAULT false,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),
    
    UNIQUE(character_id, version_number)
);

-- Change log - Detailed audit trail
CREATE TABLE character_change_log (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Change details
    change_type change_type_enum NOT NULL,
    field_path VARCHAR(500), -- JSON path that was changed (e.g., 'personality.traits.openness')
    old_value JSONB,
    new_value JSONB,
    
    -- Change context
    change_reason TEXT,
    change_source VARCHAR(100), -- manual, ai_optimization, usage_analytics
    confidence DECIMAL(3,2) DEFAULT 1.00,
    
    -- Impact assessment
    impact_score DECIMAL(3,2),
    validation_status validation_status_enum DEFAULT 'pending',
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- ============================================================================
-- ENUMS - Type safety and validation
-- ============================================================================

CREATE TYPE character_archetype_enum AS ENUM (
    'real_world',     -- Elena, Marcus, Jake, etc.
    'fantasy',        -- Dream, Aethys
    'narrative_ai',   -- Dotty
    'historical',     -- Future historical characters
    'fictional'       -- Future fictional adaptations
);

CREATE TYPE character_status_enum AS ENUM (
    'active',
    'inactive', 
    'development',
    'archived',
    'deprecated'
);

CREATE TYPE workflow_status_enum AS ENUM (
    'active',           -- Currently running
    'pending',          -- Waiting for user input
    'completed',        -- Successfully completed
    'cancelled',        -- Cancelled by user
    'timeout',          -- Timed out
    'error',           -- Error occurred
    'paused'           -- Temporarily paused
);

CREATE TYPE workflow_event_enum AS ENUM (
    'workflow_started',
    'state_entered',
    'state_exited',
    'transition_triggered',
    'action_executed',
    'workflow_completed',
    'workflow_cancelled',
    'workflow_timeout',
    'error_occurred'
);

CREATE TYPE change_type_enum AS ENUM (
    'field_added',
    'field_updated', 
    'field_removed',
    'character_created',
    'character_updated',
    'version_created',
    'bulk_import',
    'ai_optimization',
    'performance_tuning'
);

CREATE TYPE validation_status_enum AS ENUM (
    'pending',
    'validated',
    'rejected',
    'needs_review'
);

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Character lookup indexes
CREATE INDEX idx_characters_normalized_name ON characters(normalized_name);
CREATE INDEX idx_characters_bot_name ON characters(bot_name);
CREATE INDEX idx_characters_archetype_status ON characters(archetype, status);

-- JSONB indexes for fast nested queries
CREATE INDEX idx_characters_cdl_data_gin ON characters USING gin(cdl_data);
CREATE INDEX idx_characters_workflow_data_gin ON characters USING gin(workflow_data);

-- Specific JSONB field indexes for common queries
CREATE INDEX idx_characters_occupation ON characters USING gin((cdl_data->'identity'->'occupation'));
CREATE INDEX idx_characters_personality_traits ON characters USING gin((cdl_data->'personality'->'traits'));
CREATE INDEX idx_characters_communication ON characters USING gin((cdl_data->'communication'));

-- Workflow execution indexes
CREATE INDEX idx_workflow_instances_user_status ON workflow_instances(user_id, status);
CREATE INDEX idx_workflow_instances_character ON workflow_instances(character_id, status);
CREATE INDEX idx_workflow_instances_timeout ON workflow_instances(timeout_at) WHERE timeout_at IS NOT NULL;
CREATE INDEX idx_workflow_execution_log_instance ON workflow_execution_log(workflow_instance_id, created_at DESC);

-- Version and audit indexes
CREATE INDEX idx_character_versions_character_version ON character_versions(character_id, version_number DESC);
CREATE INDEX idx_character_change_log_character_timestamp ON character_change_log(character_id, created_at DESC);

-- Full-text search on CDL content
CREATE INDEX idx_characters_cdl_fts ON characters USING gin(to_tsvector('english', cdl_data::text));

-- ============================================================================
-- MATERIALIZED VIEWS - Performance optimization
-- ============================================================================

-- Fast character profile assembly
CREATE MATERIALIZED VIEW character_profiles_fast AS
SELECT 
    c.id,
    c.name,
    c.normalized_name,
    c.bot_name,
    c.archetype,
    c.allow_full_roleplay,
    c.status,
    c.version,
    c.cdl_data,
    c.workflow_data,
    c.metadata,
    
    -- Extract key CDL fields for fast access
    c.cdl_data->'identity'->>'occupation' as occupation,
    c.cdl_data->'identity'->>'location' as location,
    c.cdl_data->'personality'->'traits'->>'openness' as openness,
    c.cdl_data->'personality'->'traits'->>'extraversion' as extraversion,
    
    -- Count active workflows
    (SELECT COUNT(*) FROM workflow_instances wi 
     WHERE wi.character_id = c.id AND wi.status = 'active') as active_workflows_count,
    
    c.updated_at

FROM characters c
WHERE c.status = 'active';

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX idx_character_profiles_fast_id ON character_profiles_fast(id);

-- Refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_character_profiles()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY character_profiles_fast;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Auto-refresh triggers
CREATE TRIGGER refresh_character_profiles_on_character_change
    AFTER INSERT OR UPDATE OR DELETE ON characters
    FOR EACH STATEMENT EXECUTE FUNCTION refresh_character_profiles();

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Get complete character data (main API function)
CREATE OR REPLACE FUNCTION get_character_complete(char_normalized_name VARCHAR)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT to_jsonb(cp.*) INTO result
    FROM character_profiles_fast cp
    WHERE cp.normalized_name = char_normalized_name;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Upsert character CDL field using JSON path
CREATE OR REPLACE FUNCTION upsert_character_cdl_field(
    char_normalized_name VARCHAR,
    field_path TEXT, -- JSON path like 'personality.traits.openness'
    field_value JSONB,
    change_reason TEXT DEFAULT 'manual_update'
)
RETURNS BOOLEAN AS $$
DECLARE
    char_id BIGINT;
    old_value JSONB;
    path_array TEXT[];
BEGIN
    -- Get character ID
    SELECT id INTO char_id FROM characters WHERE normalized_name = char_normalized_name;
    IF char_id IS NULL THEN
        RAISE EXCEPTION 'Character not found: %', char_normalized_name;
    END IF;
    
    -- Convert dot notation to PostgreSQL JSON path
    path_array := string_to_array(field_path, '.');
    
    -- Get old value for audit
    SELECT cdl_data #> path_array INTO old_value FROM characters WHERE id = char_id;
    
    -- Update the field using jsonb_set
    UPDATE characters 
    SET cdl_data = jsonb_set(cdl_data, path_array, field_value, true),
        updated_at = NOW()
    WHERE id = char_id;
    
    -- Log the change
    INSERT INTO character_change_log (
        character_id, change_type, field_path, old_value, new_value, change_reason
    )
    VALUES (
        char_id, 'field_updated', field_path, old_value, field_value, change_reason
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Import character from JSON (simplified)
CREATE OR REPLACE FUNCTION import_character_from_json(
    character_json JSONB,
    import_source VARCHAR DEFAULT 'json_import'
)
RETURNS BIGINT AS $$
DECLARE
    char_id BIGINT;
    char_metadata JSONB;
    char_name VARCHAR(200);
    normalized_name VARCHAR(200);
BEGIN
    -- Extract metadata
    char_metadata := character_json -> 'character' -> 'metadata';
    char_name := char_metadata ->> 'name';
    normalized_name := lower(replace(char_name, ' ', '_'));
    
    -- Create or update character
    INSERT INTO characters (
        name, normalized_name, display_name,
        archetype, allow_full_roleplay,
        cdl_data, metadata, created_by
    )
    VALUES (
        char_name,
        normalized_name,
        char_name,
        COALESCE((character_json -> 'character' ->> 'character_archetype')::character_archetype_enum, 'real_world'),
        COALESCE((character_json -> 'character' ->> 'allow_full_roleplay_immersion')::BOOLEAN, false),
        character_json -> 'character',
        char_metadata,
        import_source
    )
    ON CONFLICT (normalized_name)
    DO UPDATE SET
        name = EXCLUDED.name,
        cdl_data = EXCLUDED.cdl_data,
        metadata = EXCLUDED.metadata,
        updated_at = NOW()
    RETURNING id INTO char_id;
    
    -- Create version snapshot
    INSERT INTO character_versions (
        character_id, version_number, version_name, character_snapshot, created_by
    )
    VALUES (
        char_id, 
        (SELECT COALESCE(MAX(version_number), 0) + 1 FROM character_versions WHERE character_id = char_id),
        'Import from JSON',
        character_json,
        import_source
    );
    
    RETURN char_id;
END;
$$ LANGUAGE plpgsql;

-- Import workflow from YAML structure (simplified)
CREATE OR REPLACE FUNCTION import_workflow_from_yaml(
    char_normalized_name VARCHAR,
    workflow_yaml JSONB
)
RETURNS BOOLEAN AS $$
DECLARE
    char_id BIGINT;
BEGIN
    -- Get character ID
    SELECT id INTO char_id FROM characters WHERE normalized_name = char_normalized_name;
    IF char_id IS NULL THEN
        RAISE EXCEPTION 'Character not found: %', char_normalized_name;
    END IF;
    
    -- Store workflow data as JSONB
    UPDATE characters 
    SET workflow_data = workflow_yaml,
        updated_at = NOW()
    WHERE id = char_id;
    
    -- Log the change
    INSERT INTO character_change_log (
        character_id, change_type, change_reason, new_value
    )
    VALUES (
        char_id, 'field_updated', 'Workflow import from YAML', workflow_yaml
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Start workflow instance (simplified)
CREATE OR REPLACE FUNCTION start_workflow_instance(
    user_id_param VARCHAR,
    char_normalized_name VARCHAR,
    workflow_name_param VARCHAR,
    initial_context JSONB DEFAULT '{}'
)
RETURNS BIGINT AS $$
DECLARE
    char_id BIGINT;
    instance_id BIGINT;
    instance_key VARCHAR;
    workflow_config JSONB;
    initial_state JSONB;
BEGIN
    -- Get character ID and workflow config
    SELECT id, workflow_data -> 'workflows' -> workflow_name_param 
    INTO char_id, workflow_config
    FROM characters 
    WHERE normalized_name = char_normalized_name;
    
    IF char_id IS NULL OR workflow_config IS NULL THEN
        RAISE EXCEPTION 'Character or workflow not found: % / %', char_normalized_name, workflow_name_param;
    END IF;
    
    -- Generate unique instance key
    instance_key := workflow_name_param || '_' || extract(epoch from now())::TEXT;
    
    -- Get initial state from workflow config
    initial_state := workflow_config -> 'initial_state';
    
    -- Create workflow instance
    INSERT INTO workflow_instances (
        character_id, user_id, workflow_name, instance_key,
        current_state, context_data, status
    )
    VALUES (
        char_id, user_id_param, workflow_name_param, instance_key,
        initial_state, initial_context, 'active'
    )
    RETURNING id INTO instance_id;
    
    -- Log workflow start
    INSERT INTO workflow_execution_log (
        workflow_instance_id, event_type, trigger_message
    )
    VALUES (
        instance_id, 'workflow_started', 'Workflow instance created'
    );
    
    RETURN instance_id;
END;
$$ LANGUAGE plpgsql;

-- Get user's active workflows
CREATE OR REPLACE FUNCTION get_user_active_workflows(user_id_param VARCHAR)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT COALESCE(json_agg(
        json_build_object(
            'instance_id', wi.id,
            'workflow_name', wi.workflow_name,
            'character_name', c.name,
            'current_state', wi.current_state,
            'context_data', wi.context_data,
            'started_at', wi.started_at,
            'timeout_at', wi.timeout_at
        )
    ), '[]'::json)::jsonb INTO result
    FROM workflow_instances wi
    JOIN characters c ON wi.character_id = c.id
    WHERE wi.user_id = user_id_param
    AND wi.status = 'active';
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Update trigger for characters table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_characters_updated_at 
    BEFORE UPDATE ON characters 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_instances_updated_at 
    BEFORE UPDATE ON workflow_instances 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE characters IS 'Core character definitions with flexible JSONB storage for CDL data';
COMMENT ON COLUMN characters.cdl_data IS 'Complete CDL character data (personality, communication, values, etc.) stored as JSONB';
COMMENT ON COLUMN characters.workflow_data IS 'Workflow definitions and state machine configurations stored as JSONB';

COMMENT ON TABLE workflow_instances IS 'Active workflow instances tracking user interactions with character workflows';
COMMENT ON TABLE workflow_execution_log IS 'Audit trail of workflow state transitions and actions';
COMMENT ON TABLE character_versions IS 'Complete character version history with snapshots';
COMMENT ON TABLE character_change_log IS 'Detailed audit trail of character modifications';

COMMENT ON MATERIALIZED VIEW character_profiles_fast IS 'Pre-computed character profiles for fast loading';

-- ============================================================================
-- SAMPLE DATA INSERTION
-- ============================================================================

-- This would be populated by the migration script
-- INSERT INTO characters (name, normalized_name, cdl_data) VALUES (...);