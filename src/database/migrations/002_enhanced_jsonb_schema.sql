-- Enhanced CDL JSONB Schema Migration
-- Migrates from normalized CDL tables to simplified JSONB approach
-- Provides document-store flexibility with RDBMS reliability

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
    cdl_data JSONB NOT NULL DEFAULT '{}',
    workflow_data JSONB DEFAULT '{}',
    
    -- Status and versioning
    status character_status_enum DEFAULT 'active',
    version INTEGER DEFAULT 1,
    schema_version VARCHAR(20) DEFAULT '2.0',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT characters_v2_name_check CHECK (length(name) >= 1),
    CONSTRAINT characters_v2_normalized_name_check CHECK (normalized_name ~ '^[a-z0-9_]+$')
);

-- Workflow instances for state management (relational for ACID)
CREATE TABLE workflow_instances_v2 (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters_v2(id) ON DELETE CASCADE,
    
    -- Instance identification
    user_id VARCHAR(200) NOT NULL,
    session_id VARCHAR(200),
    workflow_name VARCHAR(200) NOT NULL,
    instance_key VARCHAR(200),
    
    -- Current state (JSONB for flexibility)
    current_state JSONB NOT NULL DEFAULT '{}',
    context_data JSONB DEFAULT '{}',
    workflow_config JSONB DEFAULT '{}',
    
    -- Status tracking
    status workflow_status_enum DEFAULT 'active',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    timeout_at TIMESTAMPTZ,
    
    -- Performance tracking
    execution_metrics JSONB DEFAULT '{}',
    
    UNIQUE(user_id, character_id, workflow_name, instance_key)
);

-- Execution log for workflow audit trail
CREATE TABLE workflow_execution_log_v2 (
    id BIGSERIAL PRIMARY KEY,
    workflow_instance_id BIGINT NOT NULL REFERENCES workflow_instances_v2(id) ON DELETE CASCADE,
    
    -- Event details (JSONB for flexibility)
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    
    -- Context
    trigger_message TEXT,
    previous_state JSONB,
    new_state JSONB,
    
    -- Performance
    execution_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Character evolution history
CREATE TABLE character_versions_v2 (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters_v2(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    
    -- Complete character snapshot (JSONB)
    character_snapshot JSONB NOT NULL,
    
    -- Version metadata
    version_name VARCHAR(200),
    description TEXT,
    change_summary JSONB DEFAULT '{}',
    
    -- Version tracking
    parent_version_id BIGINT REFERENCES character_versions_v2(id),
    is_active BOOLEAN DEFAULT false,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),
    
    UNIQUE(character_id, version_number)
);

-- ============================================================================
-- ENUMS (reuse existing ones)
-- ============================================================================

-- Note: Reusing existing enums from current schema
-- character_archetype_enum, character_status_enum, workflow_status_enum

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Character lookup indexes
CREATE INDEX idx_characters_v2_normalized_name ON characters_v2(normalized_name);
CREATE INDEX idx_characters_v2_bot_name ON characters_v2(bot_name);
CREATE INDEX idx_characters_v2_archetype_status ON characters_v2(archetype, status);

-- JSONB GIN indexes for fast nested queries
CREATE INDEX idx_characters_v2_cdl_data_gin ON characters_v2 USING gin(cdl_data);
CREATE INDEX idx_characters_v2_workflow_data_gin ON characters_v2 USING gin(workflow_data);

-- Specific field indexes for common queries
CREATE INDEX idx_characters_v2_occupation ON characters_v2 USING gin((cdl_data->'identity'->'occupation'));
CREATE INDEX idx_characters_v2_personality ON characters_v2 USING gin((cdl_data->'personality'));
CREATE INDEX idx_characters_v2_communication ON characters_v2 USING gin((cdl_data->'communication'));

-- Workflow instance indexes
CREATE INDEX idx_workflow_instances_v2_user_status ON workflow_instances_v2(user_id, status);
CREATE INDEX idx_workflow_instances_v2_character_workflow ON workflow_instances_v2(character_id, workflow_name);
CREATE INDEX idx_workflow_instances_v2_timeout ON workflow_instances_v2(timeout_at) WHERE timeout_at IS NOT NULL;

-- Execution log indexes
CREATE INDEX idx_workflow_execution_log_v2_instance ON workflow_execution_log_v2(workflow_instance_id, created_at DESC);
CREATE INDEX idx_workflow_execution_log_v2_event_type ON workflow_execution_log_v2(event_type, created_at DESC);

-- Version indexes
CREATE INDEX idx_character_versions_v2_character_version ON character_versions_v2(character_id, version_number DESC);

-- ============================================================================
-- MATERIALIZED VIEW FOR FAST CHARACTER LOADING
-- ============================================================================

CREATE MATERIALIZED VIEW character_profiles_v2 AS
SELECT 
    c.id,
    c.name,
    c.normalized_name,
    c.bot_name,
    c.archetype,
    c.allow_full_roleplay,
    c.status,
    c.version,
    c.schema_version,
    
    -- Pre-computed CDL sections for fast access
    c.cdl_data,
    c.workflow_data,
    
    -- Active workflow summary
    (SELECT json_agg(
        json_build_object(
            'workflow_name', wi.workflow_name,
            'status', wi.status,
            'started_at', wi.started_at,
            'current_state', wi.current_state
        )
    ) FROM workflow_instances_v2 wi 
    WHERE wi.character_id = c.id AND wi.status = 'active') as active_workflows,
    
    -- Metadata
    c.metadata,
    c.created_at,
    c.updated_at

FROM characters_v2 c
WHERE c.status = 'active';

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX idx_character_profiles_v2_id ON character_profiles_v2(id);

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Get complete character data (main API function)
CREATE OR REPLACE FUNCTION get_character_v2(char_normalized_name VARCHAR)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT to_jsonb(cp.*) INTO result
    FROM character_profiles_v2 cp
    WHERE cp.normalized_name = char_normalized_name;
    
    RETURN COALESCE(result, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Upsert character data from JSON
CREATE OR REPLACE FUNCTION upsert_character_v2(
    char_name VARCHAR,
    char_normalized_name VARCHAR,
    char_bot_name VARCHAR,
    char_archetype character_archetype_enum,
    char_cdl_data JSONB,
    char_workflow_data JSONB DEFAULT '{}',
    char_metadata JSONB DEFAULT '{}'
)
RETURNS BIGINT AS $$
DECLARE
    char_id BIGINT;
BEGIN
    INSERT INTO characters_v2 (
        name, normalized_name, bot_name, archetype,
        cdl_data, workflow_data, metadata, created_by
    )
    VALUES (
        char_name, char_normalized_name, char_bot_name, char_archetype,
        char_cdl_data, char_workflow_data, char_metadata, 'upsert_function'
    )
    ON CONFLICT (normalized_name)
    DO UPDATE SET
        name = EXCLUDED.name,
        bot_name = EXCLUDED.bot_name,
        archetype = EXCLUDED.archetype,
        cdl_data = EXCLUDED.cdl_data,
        workflow_data = EXCLUDED.workflow_data,
        metadata = EXCLUDED.metadata,
        updated_at = NOW(),
        version = characters_v2.version + 1
    RETURNING id INTO char_id;
    
    RETURN char_id;
END;
$$ LANGUAGE plpgsql;

-- Bulk import from JSON file
CREATE OR REPLACE FUNCTION import_character_json_v2(
    character_json JSONB,
    import_source VARCHAR DEFAULT 'json_import'
)
RETURNS BIGINT AS $$
DECLARE
    char_id BIGINT;
    char_data JSONB;
    char_metadata JSONB;
    char_name VARCHAR;
    char_normalized_name VARCHAR;
    char_archetype character_archetype_enum;
BEGIN
    -- Extract character data
    char_data := character_json -> 'character';
    char_metadata := char_data -> 'metadata';
    char_name := char_metadata ->> 'name';
    char_normalized_name := lower(replace(char_name, ' ', '_'));
    
    -- Determine archetype
    char_archetype := COALESCE(
        (char_data ->> 'character_archetype')::character_archetype_enum, 
        'real_world'
    );
    
    -- Create character
    SELECT upsert_character_v2(
        char_name,
        char_normalized_name,
        char_metadata ->> 'bot_name',
        char_archetype,
        char_data, -- Store entire character data as JSONB
        '{}', -- Workflow data (empty initially)
        char_metadata
    ) INTO char_id;
    
    RETURN char_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- WORKFLOW MANAGEMENT FUNCTIONS
-- ============================================================================

-- Start workflow instance
CREATE OR REPLACE FUNCTION start_workflow_v2(
    user_id_param VARCHAR,
    char_normalized_name VARCHAR,
    workflow_name_param VARCHAR,
    initial_context JSONB DEFAULT '{}',
    workflow_config_param JSONB DEFAULT '{}'
)
RETURNS BIGINT AS $$
DECLARE
    char_id BIGINT;
    instance_id BIGINT;
    instance_key VARCHAR;
BEGIN
    -- Get character ID
    SELECT id INTO char_id FROM characters_v2 WHERE normalized_name = char_normalized_name;
    IF char_id IS NULL THEN
        RAISE EXCEPTION 'Character not found: %', char_normalized_name;
    END IF;
    
    -- Generate instance key
    instance_key := workflow_name_param || '_' || extract(epoch from now())::TEXT;
    
    -- Create workflow instance
    INSERT INTO workflow_instances_v2 (
        character_id, user_id, workflow_name, instance_key,
        current_state, context_data, workflow_config
    )
    VALUES (
        char_id, user_id_param, workflow_name_param, instance_key,
        '{"state": "initial"}'::jsonb, initial_context, workflow_config_param
    )
    RETURNING id INTO instance_id;
    
    -- Log workflow start
    INSERT INTO workflow_execution_log_v2 (
        workflow_instance_id, event_type, event_data, trigger_message
    )
    VALUES (
        instance_id, 'workflow_started', 
        json_build_object('workflow_name', workflow_name_param)::jsonb,
        'Workflow instance created'
    );
    
    RETURN instance_id;
END;
$$ LANGUAGE plpgsql;

-- Get user's active workflows
CREATE OR REPLACE FUNCTION get_user_workflows_v2(user_id_param VARCHAR)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT json_agg(
        json_build_object(
            'instance_id', wi.id,
            'workflow_name', wi.workflow_name,
            'character_name', c.name,
            'current_state', wi.current_state,
            'context_data', wi.context_data,
            'started_at', wi.started_at,
            'status', wi.status
        )
    ) INTO result
    FROM workflow_instances_v2 wi
    JOIN characters_v2 c ON wi.character_id = c.id
    WHERE wi.user_id = user_id_param
    AND wi.status IN ('active', 'pending');
    
    RETURN COALESCE(result, '[]'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Updated timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_v2()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger
CREATE TRIGGER update_characters_v2_updated_at 
    BEFORE UPDATE ON characters_v2 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_v2();

CREATE TRIGGER update_workflow_instances_v2_updated_at 
    BEFORE UPDATE ON workflow_instances_v2 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_v2();

-- Refresh materialized view on character changes
CREATE OR REPLACE FUNCTION refresh_character_profiles_v2()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY character_profiles_v2;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER refresh_character_profiles_v2_on_change
    AFTER INSERT OR UPDATE OR DELETE ON characters_v2
    FOR EACH STATEMENT EXECUTE FUNCTION refresh_character_profiles_v2();

-- ============================================================================
-- MIGRATION FROM EXISTING SCHEMA
-- ============================================================================

-- Migrate existing characters to new schema
CREATE OR REPLACE FUNCTION migrate_to_jsonb_schema()
RETURNS INTEGER AS $$
DECLARE
    old_char RECORD;
    cdl_data_json JSONB;
    workflow_data_json JSONB;
    migrated_count INTEGER := 0;
BEGIN
    -- Migrate each character from old normalized schema
    FOR old_char IN 
        SELECT * FROM cdl_characters WHERE is_active = true
    LOOP
        -- Build CDL data JSON from normalized tables
        SELECT json_build_object(
            'metadata', json_build_object(
                'name', old_char.name,
                'created_by', old_char.created_by,
                'version', old_char.version
            ),
            'identity', json_build_object(
                'occupation', old_char.occupation,
                'location', old_char.location,
                'age_range', old_char.age_range,
                'background', old_char.background,
                'description', old_char.description
            ),
            'personality', (
                SELECT json_object_agg(trait_name, 
                    json_build_object(
                        'value', trait_value,
                        'description', trait_description,
                        'intensity', intensity
                    )
                )
                FROM cdl_personality_traits 
                WHERE character_id = old_char.id
            ),
            'communication', (
                SELECT json_object_agg(style_name,
                    json_build_object(
                        'value', style_value,
                        'description', description,
                        'category', style_category
                    )
                )
                FROM cdl_communication_styles
                WHERE character_id = old_char.id
            ),
            'values', (
                SELECT json_object_agg(value_name,
                    json_build_object(
                        'description', value_description,
                        'importance', importance_level,
                        'category', value_category
                    )
                )
                FROM cdl_values
                WHERE character_id = old_char.id
            ),
            'knowledge', (
                SELECT json_object_agg(knowledge_key,
                    json_build_object(
                        'value', knowledge_value,
                        'context', knowledge_context,
                        'confidence', confidence_level,
                        'category', knowledge_category,
                        'type', knowledge_type
                    )
                )
                FROM cdl_personal_knowledge
                WHERE character_id = old_char.id
            )
        ) INTO cdl_data_json;
        
        -- Build workflow data (empty for now)
        workflow_data_json := '{}'::jsonb;
        
        -- Insert into new schema
        PERFORM upsert_character_v2(
            old_char.name,
            old_char.normalized_name,
            old_char.bot_name,
            old_char.character_archetype::character_archetype_enum,
            cdl_data_json,
            workflow_data_json,
            json_build_object(
                'migrated_from', 'normalized_schema',
                'migration_date', now()
            )::jsonb
        );
        
        migrated_count := migrated_count + 1;
    END LOOP;
    
    RETURN migrated_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE characters_v2 IS 'Enhanced JSONB-based character storage combining flexibility with performance';
COMMENT ON TABLE workflow_instances_v2 IS 'Workflow state management with ACID transaction support';
COMMENT ON TABLE workflow_execution_log_v2 IS 'Complete audit trail of workflow interactions';
COMMENT ON TABLE character_versions_v2 IS 'Character evolution tracking with full snapshots';

COMMENT ON COLUMN characters_v2.cdl_data IS 'Complete CDL character definition as flexible JSONB';
COMMENT ON COLUMN characters_v2.workflow_data IS 'Character-specific workflow definitions and configuration';
COMMENT ON COLUMN workflow_instances_v2.current_state IS 'Current workflow state with flexible JSONB structure';
COMMENT ON COLUMN workflow_instances_v2.context_data IS 'Workflow context and extracted user data';

-- Performance note
COMMENT ON INDEX idx_characters_v2_cdl_data_gin IS 'GIN index for fast JSONB queries on character data';
COMMENT ON MATERIALIZED VIEW character_profiles_v2 IS 'Pre-computed character profiles for instant loading';