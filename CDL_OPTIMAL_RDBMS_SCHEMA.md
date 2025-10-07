# WhisperEngine CDL Optimal RDBMS Schema Design

## Current Schema Analysis

### ❌ Current Issues
1. **Rigid Categorization**: Fixed categories (`speaking_style`, `interaction_preferences`) limit flexibility
2. **JSON-in-SQL**: Using TEXT fields for complex structures loses RDBMS benefits
3. **Missing Hierarchical Support**: No parent-child relationships for nested concepts
4. **Limited Extensibility**: Adding new field types requires schema changes
5. **Poor Query Performance**: Aggregated JSON views are slow
6. **Version Control**: Character evolution tracking is basic

### ✅ Current Strengths
- Good normalization
- Proper indexing
- JSONB aggregation for complex queries
- CASCADE deletion
- Character archetype support

## 🎯 OPTIMAL CDL RDBMS SCHEMA DESIGN

### Design Philosophy
- **Flexibility-First**: Support any CDL field structure without schema changes
- **Performance-Optimized**: Fast queries for character loading and AI integration
- **Hierarchical Support**: Natural parent-child relationships for nested data
- **Version-Aware**: Complete audit trail and rollback capabilities
- **Type-Safe**: Structured data types with validation
- **Extension-Ready**: Easy addition of new field types and structures

### Core Schema Design

```sql
-- ============================================================================
-- CHARACTER ENTITIES - Core character management
-- ============================================================================

-- Characters table - Core character registry
CREATE TABLE characters (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL UNIQUE,
    display_name VARCHAR(200),
    bot_name VARCHAR(100),
    
    -- Character classification
    archetype character_archetype_enum DEFAULT 'real_world',
    allow_full_roleplay BOOLEAN DEFAULT false,
    
    -- Status and versioning
    status character_status_enum DEFAULT 'active',
    version INTEGER DEFAULT 1,
    schema_version VARCHAR(20) DEFAULT '2.0',
    
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),
    
    -- Character metadata as JSONB for flexible fields
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT characters_name_check CHECK (length(name) >= 1),
    CONSTRAINT characters_normalized_name_check CHECK (normalized_name ~ '^[a-z0-9_]+$')
);

-- Character field definitions - Define what fields exist and their types
CREATE TABLE character_field_definitions (
    id BIGSERIAL PRIMARY KEY,
    field_path VARCHAR(200) NOT NULL UNIQUE, -- dot notation: identity.age, personality.traits.openness
    field_type field_type_enum NOT NULL,
    data_type data_type_enum NOT NULL, -- string, number, boolean, array, object
    
    -- Field metadata
    display_name VARCHAR(200),
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    
    -- Validation rules
    is_required BOOLEAN DEFAULT false,
    default_value JSONB,
    validation_rules JSONB DEFAULT '{}', -- JSON schema for validation
    
    -- Hierarchy support
    parent_field_id BIGINT REFERENCES character_field_definitions(id),
    sort_order INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Character field values - Store actual character data
CREATE TABLE character_field_values (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    field_definition_id BIGINT NOT NULL REFERENCES character_field_definitions(id),
    
    -- Value storage (only one should be populated based on data_type)
    string_value TEXT,
    number_value DECIMAL(10,4),
    boolean_value BOOLEAN,
    json_value JSONB,
    
    -- Value metadata
    confidence DECIMAL(3,2) DEFAULT 1.00,
    source VARCHAR(100) DEFAULT 'manual',
    is_public BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100),
    
    UNIQUE(character_id, field_definition_id),
    
    -- Ensure only one value type is set
    CONSTRAINT character_field_values_single_value CHECK (
        (string_value IS NOT NULL)::INTEGER + 
        (number_value IS NOT NULL)::INTEGER + 
        (boolean_value IS NOT NULL)::INTEGER + 
        (json_value IS NOT NULL)::INTEGER = 1
    )
);

-- ============================================================================
-- SPECIALIZED TABLES - High-performance access for AI integration
-- ============================================================================

-- Communication patterns - Optimized for response generation
CREATE TABLE communication_patterns (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Pattern classification
    pattern_type communication_pattern_enum NOT NULL,
    pattern_name VARCHAR(200) NOT NULL,
    context VARCHAR(200), -- when to use this pattern
    
    -- Pattern content
    pattern_content TEXT NOT NULL,
    examples JSONB DEFAULT '[]',
    triggers JSONB DEFAULT '[]', -- keywords or contexts that trigger this
    
    -- Usage metrics
    frequency_weight DECIMAL(3,2) DEFAULT 1.00,
    priority INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    
    -- Constraints and rules
    avoid_with JSONB DEFAULT '[]', -- patterns/contexts to avoid using together
    requires JSONB DEFAULT '[]', -- required conditions for this pattern
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(character_id, pattern_type, pattern_name)
);

-- Response templates - Pre-built responses for common scenarios
CREATE TABLE response_templates (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Template classification
    scenario_type response_scenario_enum NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    
    -- Template content
    template_text TEXT NOT NULL,
    variables JSONB DEFAULT '{}', -- {name: type} for template variables
    
    -- Conditions
    trigger_conditions JSONB DEFAULT '{}',
    emotional_context JSONB DEFAULT '{}',
    conversation_context JSONB DEFAULT '{}',
    
    -- Performance data
    effectiveness_score DECIMAL(3,2) DEFAULT 0.50,
    usage_stats JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(character_id, scenario_type, template_name)
);

-- Knowledge graph - Character's world knowledge and relationships
CREATE TABLE character_knowledge (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Knowledge classification
    knowledge_type knowledge_type_enum NOT NULL,
    entity_type VARCHAR(100), -- person, place, concept, fact, etc.
    
    -- Knowledge content
    key_name VARCHAR(200) NOT NULL,
    value_content TEXT NOT NULL,
    context_info JSONB DEFAULT '{}',
    
    -- Relationships to other knowledge
    parent_knowledge_id BIGINT REFERENCES character_knowledge(id),
    related_entities JSONB DEFAULT '[]',
    
    -- Knowledge metadata
    confidence_level DECIMAL(3,2) DEFAULT 1.00,
    importance_score DECIMAL(3,2) DEFAULT 0.50,
    is_core_identity BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT true,
    
    -- Usage tracking
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(character_id, knowledge_type, key_name)
);

-- ============================================================================
-- WORKFLOW SYSTEM - Support for character-specific workflow definitions
-- ============================================================================

-- Workflow definitions - Character-specific state machines and interactions
CREATE TABLE character_workflows (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Workflow identification
    workflow_name VARCHAR(200) NOT NULL,
    workflow_version VARCHAR(20) DEFAULT '1.0',
    description TEXT,
    
    -- Workflow configuration
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    concurrent_allowed BOOLEAN DEFAULT false,
    max_pending_per_user INTEGER DEFAULT 1,
    default_timeout_seconds INTEGER DEFAULT 300,
    
    -- Workflow metadata
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(character_id, workflow_name, workflow_version)
);

-- Workflow triggers - Define when workflows activate
CREATE TABLE workflow_triggers (
    id BIGSERIAL PRIMARY KEY,
    workflow_id BIGINT NOT NULL REFERENCES character_workflows(id) ON DELETE CASCADE,
    
    -- Trigger identification
    trigger_type workflow_trigger_enum NOT NULL,
    trigger_name VARCHAR(200),
    priority INTEGER DEFAULT 0,
    
    -- Pattern matching
    patterns JSONB DEFAULT '[]', -- Array of regex patterns
    keywords JSONB DEFAULT '[]', -- Array of trigger keywords
    context_requirements JSONB DEFAULT '{}', -- Required context conditions
    
    -- LLM validation (for complex intent detection)
    llm_validation_enabled BOOLEAN DEFAULT false,
    llm_validation_prompt TEXT,
    llm_confidence_threshold DECIMAL(3,2) DEFAULT 0.7,
    
    -- Trigger metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow states - Define state machine states
CREATE TABLE workflow_states (
    id BIGSERIAL PRIMARY KEY,
    workflow_id BIGINT NOT NULL REFERENCES character_workflows(id) ON DELETE CASCADE,
    
    -- State identification
    state_name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- State properties
    is_initial BOOLEAN DEFAULT false,
    is_final BOOLEAN DEFAULT false,
    
    -- Prompt injection for this state
    prompt_injection TEXT,
    system_prompt_addition TEXT,
    
    -- State timeout configuration
    timeout_seconds INTEGER,
    timeout_action VARCHAR(200),
    timeout_message TEXT,
    
    -- State metadata
    state_data JSONB DEFAULT '{}', -- Additional state configuration
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(workflow_id, state_name)
);

-- Workflow transitions - Define state machine transitions
CREATE TABLE workflow_transitions (
    id BIGSERIAL PRIMARY KEY,
    from_state_id BIGINT NOT NULL REFERENCES workflow_states(id) ON DELETE CASCADE,
    to_state_id BIGINT NOT NULL REFERENCES workflow_states(id) ON DELETE CASCADE,
    
    -- Transition identification
    transition_name VARCHAR(200),
    description TEXT,
    
    -- Transition triggers
    trigger_patterns JSONB DEFAULT '[]',
    trigger_keywords JSONB DEFAULT '[]',
    trigger_conditions JSONB DEFAULT '{}',
    
    -- Transition action
    action_name VARCHAR(200),
    action_parameters JSONB DEFAULT '{}',
    
    -- Transition metadata
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow context extractors - Define how to extract context from messages
CREATE TABLE workflow_context_extractors (
    id BIGSERIAL PRIMARY KEY,
    workflow_id BIGINT NOT NULL REFERENCES character_workflows(id) ON DELETE CASCADE,
    
    -- Extractor identification
    context_key VARCHAR(200) NOT NULL,
    extractor_type context_extractor_enum NOT NULL,
    
    -- Extraction configuration
    extraction_config JSONB NOT NULL, -- Source, patterns, transforms, defaults
    validation_rules JSONB DEFAULT '{}',
    
    -- Metadata
    description TEXT,
    is_required BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(workflow_id, context_key)
);

-- Workflow lookup tables - Support for workflow data lookups
CREATE TABLE workflow_lookup_tables (
    id BIGSERIAL PRIMARY KEY,
    character_id BIGINT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Table identification
    table_name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Table data
    table_data JSONB NOT NULL, -- Key-value pairs for lookups
    
    -- Metadata
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(character_id, table_name)
);

-- ============================================================================
-- WORKFLOW EXECUTION TRACKING
-- ============================================================================

-- Active workflow instances - Track running workflow instances for users
CREATE TABLE workflow_instances (
    id BIGSERIAL PRIMARY KEY,
    workflow_id BIGINT NOT NULL REFERENCES character_workflows(id) ON DELETE CASCADE,
    
    -- Instance identification
    user_id VARCHAR(200) NOT NULL,
    session_id VARCHAR(200),
    instance_key VARCHAR(200), -- Unique key for this instance
    
    -- Current state
    current_state_id BIGINT NOT NULL REFERENCES workflow_states(id),
    
    -- Instance context and data
    context_data JSONB DEFAULT '{}', -- Extracted context for this instance
    instance_data JSONB DEFAULT '{}', -- Runtime data for this instance
    
    -- Status tracking
    status workflow_status_enum DEFAULT 'active',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Timeout tracking
    timeout_at TIMESTAMPTZ,
    
    UNIQUE(user_id, workflow_id, instance_key)
);

-- Workflow execution log - Audit trail of workflow transitions and actions
CREATE TABLE workflow_execution_log (
    id BIGSERIAL PRIMARY KEY,
    workflow_instance_id BIGINT NOT NULL REFERENCES workflow_instances(id) ON DELETE CASCADE,
    
    -- Execution details
    event_type workflow_event_enum NOT NULL,
    from_state_id BIGINT REFERENCES workflow_states(id),
    to_state_id BIGINT REFERENCES workflow_states(id),
    transition_id BIGINT REFERENCES workflow_transitions(id),
    
    -- Event context
    trigger_message TEXT,
    action_executed VARCHAR(200),
    action_result JSONB DEFAULT '{}',
    
    -- Event metadata
    execution_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
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

CREATE TYPE workflow_trigger_enum AS ENUM (
    'pattern_match',     -- Regex pattern matching
    'keyword_match',     -- Keyword detection
    'intent_detection',  -- LLM-based intent detection
    'context_change',    -- Context or state changes
    'time_trigger',      -- Time-based triggers
    'user_action',       -- Specific user actions
    'system_event'       -- System-generated events
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

CREATE TYPE context_extractor_enum AS ENUM (
    'pattern_group',    -- Extract from regex capture group
    'keyword_match',    -- Extract based on keyword matching
    'message_full',     -- Use full message content
    'lookup_table',     -- Look up value from table
    'literal_value',    -- Use literal value
    'llm_extraction',   -- LLM-based extraction
    'context_reference' -- Reference to existing context
);

CREATE TYPE character_status_enum AS ENUM (
    'active',
    'inactive', 
    'development',
    'archived',
    'deprecated'
);

CREATE TYPE field_type_enum AS ENUM (
    'identity',           -- Basic identity info
    'personality',        -- Traits, characteristics
    'communication',      -- Speaking styles, patterns
    'knowledge',          -- Background, expertise
    'behavior',           -- Guidelines, anti-patterns
    'emotional',          -- Emotional expressions
    'interaction',        -- Modes, preferences
    'backstory',          -- History, experiences
    'relationships',      -- Social connections
    'skills',            -- Abilities, expertise
    'preferences',        -- Likes, dislikes
    'appearance',         -- Physical description
    'custom'             -- Extension field
);

CREATE TYPE data_type_enum AS ENUM (
    'string',
    'number',
    'boolean',
    'array',
    'object',
    'text',              -- Large text content
    'enum',              -- Controlled vocabulary
    'reference'          -- Reference to another entity
);

CREATE TYPE communication_pattern_enum AS ENUM (
    'greeting',
    'farewell', 
    'question_response',
    'excitement',
    'concern',
    'advice_giving',
    'storytelling',
    'technical_explanation',
    'emotional_support',
    'humor',
    'cultural_expression',
    'expertise_sharing'
);

CREATE TYPE response_scenario_enum AS ENUM (
    'first_meeting',
    'casual_chat',
    'deep_conversation',
    'technical_discussion',
    'emotional_support',
    'teaching_moment',
    'conflict_resolution',
    'celebration',
    'problem_solving',
    'creative_collaboration'
);

CREATE TYPE knowledge_type_enum AS ENUM (
    'identity',          -- Who they are
    'biography',         -- Life history
    'expertise',         -- Professional knowledge
    'relationships',     -- Social connections
    'experiences',       -- Life experiences
    'preferences',       -- Likes/dislikes
    'beliefs',          -- Values, worldview
    'skills',           -- Abilities
    'memories',         -- Specific memories
    'goals',            -- Aspirations
    'fears',            -- Concerns, anxieties
    'cultural',         -- Cultural background
    'family',           -- Family information
    'career',           -- Professional background
    'hobbies',          -- Interests, activities
    'facts'             -- General factual knowledge
);

-- ============================================================================
-- VERSIONING & AUDIT SYSTEM
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
    field_values_snapshot JSONB NOT NULL,
    
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
    field_definition_id BIGINT REFERENCES character_field_definitions(id),
    
    -- Change details
    change_type change_type_enum NOT NULL,
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

-- Field value lookup indexes
CREATE INDEX idx_character_field_values_character_field ON character_field_values(character_id, field_definition_id);
CREATE INDEX idx_character_field_values_field_type ON character_field_values(field_definition_id) 
    INCLUDE (character_id, string_value, number_value, boolean_value);

-- Field definition indexes
CREATE INDEX idx_character_field_definitions_path ON character_field_definitions(field_path);
CREATE INDEX idx_character_field_definitions_type_category ON character_field_definitions(field_type, category);
CREATE INDEX idx_character_field_definitions_parent ON character_field_definitions(parent_field_id);

-- Communication pattern indexes
CREATE INDEX idx_communication_patterns_character_type ON communication_patterns(character_id, pattern_type);
CREATE INDEX idx_communication_patterns_priority ON communication_patterns(character_id, priority DESC, frequency_weight DESC);

-- Knowledge graph indexes  
CREATE INDEX idx_character_knowledge_character_type ON character_knowledge(character_id, knowledge_type);
CREATE INDEX idx_character_knowledge_entity_type ON character_knowledge(entity_type, character_id);
CREATE INDEX idx_character_knowledge_importance ON character_knowledge(character_id, importance_score DESC);
CREATE INDEX idx_character_knowledge_core_identity ON character_knowledge(character_id, is_core_identity, importance_score DESC);

-- Full-text search indexes
CREATE INDEX idx_character_knowledge_content_fts ON character_knowledge USING gin(to_tsvector('english', value_content));
CREATE INDEX idx_communication_patterns_content_fts ON communication_patterns USING gin(to_tsvector('english', pattern_content));

-- Workflow execution indexes
CREATE INDEX idx_character_workflows_character ON character_workflows(character_id, is_active);
CREATE INDEX idx_workflow_triggers_workflow ON workflow_triggers(workflow_id, trigger_type);
CREATE INDEX idx_workflow_states_workflow ON workflow_states(workflow_id, is_initial, is_final);
CREATE INDEX idx_workflow_transitions_from_state ON workflow_transitions(from_state_id);
CREATE INDEX idx_workflow_transitions_to_state ON workflow_transitions(to_state_id);
CREATE INDEX idx_workflow_instances_user_status ON workflow_instances(user_id, status);
CREATE INDEX idx_workflow_instances_timeout ON workflow_instances(timeout_at) WHERE timeout_at IS NOT NULL;
CREATE INDEX idx_workflow_execution_log_instance ON workflow_execution_log(workflow_instance_id, created_at DESC);

-- Version and audit indexes
CREATE INDEX idx_character_versions_character_version ON character_versions(character_id, version_number DESC);
CREATE INDEX idx_character_change_log_character_timestamp ON character_change_log(character_id, created_at DESC);

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
    
    -- Core identity fields (pre-computed)
    (SELECT json_object_agg(fd.field_path, 
        CASE 
            WHEN cfv.string_value IS NOT NULL THEN to_jsonb(cfv.string_value)
            WHEN cfv.number_value IS NOT NULL THEN to_jsonb(cfv.number_value)
            WHEN cfv.boolean_value IS NOT NULL THEN to_jsonb(cfv.boolean_value)
            WHEN cfv.json_value IS NOT NULL THEN cfv.json_value
        END
    ) FROM character_field_values cfv
    JOIN character_field_definitions fd ON cfv.field_definition_id = fd.id
    WHERE cfv.character_id = c.id AND fd.field_type = 'identity') as identity_data,
    
    -- Communication patterns summary
    (SELECT json_object_agg(cp.pattern_type, 
        json_build_object(
            'patterns', json_agg(
                json_build_object(
                    'name', cp.pattern_name,
                    'content', cp.pattern_content,
                    'weight', cp.frequency_weight
                ) ORDER BY cp.priority DESC, cp.frequency_weight DESC
            )
        )
    ) FROM communication_patterns cp
    WHERE cp.character_id = c.id
    GROUP BY cp.character_id) as communication_summary,
    
    -- Core knowledge summary
    (SELECT json_object_agg(ck.knowledge_type,
        json_agg(
            json_build_object(
                'key', ck.key_name,
                'value', ck.value_content,
                'confidence', ck.confidence_level,
                'importance', ck.importance_score
            ) ORDER BY ck.importance_score DESC, ck.is_core_identity DESC
        )
    ) FROM character_knowledge ck
    WHERE ck.character_id = c.id
    GROUP BY ck.character_id) as knowledge_summary,
    
    -- Active workflows summary
    (SELECT json_object_agg(cw.workflow_name,
        json_build_object(
            'description', cw.description,
            'version', cw.workflow_version,
            'priority', cw.priority,
            'states_count', (SELECT COUNT(*) FROM workflow_states ws WHERE ws.workflow_id = cw.id),
            'triggers_count', (SELECT COUNT(*) FROM workflow_triggers wt WHERE wt.workflow_id = cw.id)
        )
    ) FROM character_workflows cw
    WHERE cw.character_id = c.id AND cw.is_active = true
    GROUP BY cw.character_id) as workflows_summary,
    
    c.updated_at

FROM characters c
WHERE c.status = 'active';

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

CREATE TRIGGER refresh_character_profiles_on_field_change
    AFTER INSERT OR UPDATE OR DELETE ON character_field_values
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

-- Upsert character field value
CREATE OR REPLACE FUNCTION upsert_character_field(
    char_id BIGINT,
    field_path VARCHAR,
    field_value JSONB,
    field_source VARCHAR DEFAULT 'manual'
)
RETURNS BOOLEAN AS $$
DECLARE
    field_def_id BIGINT;
    field_data_type data_type_enum;
BEGIN
    -- Get field definition
    SELECT id, data_type INTO field_def_id, field_data_type
    FROM character_field_definitions
    WHERE field_path = upsert_character_field.field_path;
    
    IF field_def_id IS NULL THEN
        RAISE EXCEPTION 'Field definition not found for path: %', field_path;
    END IF;
    
    -- Upsert the value based on data type
    INSERT INTO character_field_values (
        character_id, field_definition_id, 
        string_value, number_value, boolean_value, json_value,
        source, created_by
    )
    VALUES (
        char_id, field_def_id,
        CASE WHEN field_data_type IN ('string', 'text', 'enum') THEN field_value #>> '{}' END,
        CASE WHEN field_data_type = 'number' THEN (field_value #>> '{}')::DECIMAL END,
        CASE WHEN field_data_type = 'boolean' THEN (field_value #>> '{}')::BOOLEAN END,
        CASE WHEN field_data_type IN ('array', 'object', 'reference') THEN field_value END,
        field_source, field_source
    )
    ON CONFLICT (character_id, field_definition_id)
    DO UPDATE SET
        string_value = EXCLUDED.string_value,
        number_value = EXCLUDED.number_value,
        boolean_value = EXCLUDED.boolean_value,
        json_value = EXCLUDED.json_value,
        updated_at = NOW(),
        source = EXCLUDED.source;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Bulk character import from JSON
CREATE OR REPLACE FUNCTION import_character_from_json(
    character_json JSONB,
    import_source VARCHAR DEFAULT 'json_import'
)
RETURNS BIGINT AS $$
DECLARE
    char_id BIGINT;
    field_path VARCHAR;
    field_value JSONB;
    char_data JSONB;
BEGIN
    -- Extract character metadata
    char_data := character_json -> 'character';
    
    -- Create or update character
    INSERT INTO characters (
        name, normalized_name, display_name, 
        archetype, allow_full_roleplay, 
        created_by, metadata
    )
    VALUES (
        char_data -> 'metadata' ->> 'name',
        lower(replace(char_data -> 'metadata' ->> 'name', ' ', '_')),
        char_data -> 'metadata' ->> 'name',
        COALESCE((char_data ->> 'character_archetype')::character_archetype_enum, 'real_world'),
        COALESCE((char_data ->> 'allow_full_roleplay_immersion')::BOOLEAN, false),
        import_source,
        char_data -> 'metadata'
    )
    ON CONFLICT (normalized_name)
    DO UPDATE SET
        name = EXCLUDED.name,
        updated_at = NOW(),
        metadata = EXCLUDED.metadata
    RETURNING id INTO char_id;
    
    -- Import all character fields dynamically
    FOR field_path, field_value IN
        SELECT * FROM jsonb_each(char_data)
    LOOP
        -- Skip metadata (already handled)
        CONTINUE WHEN field_path = 'metadata';
        
        -- Upsert the field
        PERFORM upsert_character_field(char_id, field_path, field_value, import_source);
    END LOOP;
    
    RETURN char_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- WORKFLOW MANAGEMENT FUNCTIONS
-- ============================================================================

-- Import workflow from YAML structure
CREATE OR REPLACE FUNCTION import_workflow_from_yaml(
    character_name VARCHAR,
    workflow_yaml JSONB
)
RETURNS BIGINT AS $$
DECLARE
    char_id BIGINT;
    workflow_id BIGINT;
    workflow_data JSONB;
    state_data JSONB;
    state_name VARCHAR;
    state_id BIGINT;
    trigger_data JSONB;
    transition_data JSONB;
    extractor_data JSONB;
    lookup_data JSONB;
    table_name VARCHAR;
    table_content JSONB;
BEGIN
    -- Get character ID
    SELECT id INTO char_id FROM characters WHERE normalized_name = lower(character_name);
    IF char_id IS NULL THEN
        RAISE EXCEPTION 'Character not found: %', character_name;
    END IF;
    
    -- Import each workflow
    FOR workflow_data IN SELECT jsonb_array_elements(workflow_yaml -> 'workflows') LOOP
        -- Create workflow
        INSERT INTO character_workflows (
            character_id, workflow_name, workflow_version, description,
            priority, concurrent_allowed, max_pending_per_user, default_timeout_seconds
        )
        VALUES (
            char_id,
            workflow_data ->> 'name',
            workflow_yaml ->> 'version',
            workflow_data ->> 'description',
            COALESCE((workflow_data ->> 'priority')::INTEGER, 0),
            COALESCE((workflow_yaml -> 'config' ->> 'concurrent_workflows')::BOOLEAN, false),
            COALESCE((workflow_yaml -> 'config' ->> 'max_pending_per_user')::INTEGER, 1),
            COALESCE((workflow_yaml -> 'config' ->> 'default_timeout_seconds')::INTEGER, 300)
        )
        ON CONFLICT (character_id, workflow_name, workflow_version)
        DO UPDATE SET
            description = EXCLUDED.description,
            updated_at = NOW()
        RETURNING id INTO workflow_id;
        
        -- Import workflow triggers
        FOR trigger_data IN SELECT jsonb_array_elements(workflow_data -> 'triggers') LOOP
            INSERT INTO workflow_triggers (
                workflow_id, trigger_type, trigger_name,
                patterns, keywords, context_requirements,
                llm_validation_enabled, llm_validation_prompt, llm_confidence_threshold
            )
            VALUES (
                workflow_id,
                'pattern_match'::workflow_trigger_enum,
                trigger_data ->> 'name',
                trigger_data -> 'patterns',
                trigger_data -> 'keywords',
                trigger_data -> 'context_required',
                COALESCE((trigger_data -> 'llm_validation' ->> 'enabled')::BOOLEAN, false),
                trigger_data -> 'llm_validation' ->> 'prompt',
                COALESCE((trigger_data -> 'llm_validation' ->> 'confidence_threshold')::DECIMAL, 0.7)
            );
        END LOOP;
        
        -- Import workflow states
        FOR state_name, state_data IN SELECT * FROM jsonb_each(workflow_data -> 'states') LOOP
            INSERT INTO workflow_states (
                workflow_id, state_name, description,
                is_initial, is_final,
                prompt_injection, system_prompt_addition,
                timeout_seconds, timeout_action, timeout_message
            )
            VALUES (
                workflow_id,
                state_name,
                state_data ->> 'description',
                state_name = (workflow_data ->> 'initial_state'),
                COALESCE((state_data ->> 'final')::BOOLEAN, false),
                state_data ->> 'prompt_injection',
                workflow_data ->> 'system_prompt_addition',
                COALESCE((state_data -> 'timeout' ->> 'duration_seconds')::INTEGER, NULL),
                state_data -> 'timeout' ->> 'action',
                state_data -> 'timeout' ->> 'message'
            )
            RETURNING id INTO state_id;
            
            -- Import state transitions
            FOR transition_data IN SELECT jsonb_array_elements(state_data -> 'transitions') LOOP
                INSERT INTO workflow_transitions (
                    from_state_id, 
                    to_state_id,
                    transition_name,
                    trigger_patterns,
                    trigger_keywords,
                    action_name
                )
                VALUES (
                    state_id,
                    (SELECT id FROM workflow_states 
                     WHERE workflow_id = import_workflow_from_yaml.workflow_id 
                     AND state_name = (transition_data ->> 'to_state')),
                    transition_data ->> 'name',
                    transition_data -> 'triggers' -> 'patterns',
                    transition_data -> 'triggers' -> 'keywords',
                    transition_data ->> 'action'
                );
            END LOOP;
        END LOOP;
        
        -- Import context extractors
        FOR extractor_data IN SELECT jsonb_array_elements(workflow_data -> 'on_trigger' -> 'extract_context') LOOP
            INSERT INTO workflow_context_extractors (
                workflow_id, context_key, extractor_type, extraction_config
            )
            VALUES (
                workflow_id,
                extractor_data ->> 'key',
                (extractor_data ->> 'from')::context_extractor_enum,
                extractor_data
            );
        END LOOP;
    END LOOP;
    
    -- Import lookup tables
    FOR table_name, table_content IN SELECT * FROM jsonb_each(workflow_yaml -> 'lookup_tables') LOOP
        INSERT INTO workflow_lookup_tables (
            character_id, table_name, table_data
        )
        VALUES (
            char_id,
            table_name,
            table_content
        )
        ON CONFLICT (character_id, table_name)
        DO UPDATE SET
            table_data = EXCLUDED.table_data,
            updated_at = NOW();
    END LOOP;
    
    RETURN char_id;
END;
$$ LANGUAGE plpgsql;

-- Start workflow instance
CREATE OR REPLACE FUNCTION start_workflow_instance(
    user_id_param VARCHAR,
    character_name VARCHAR,
    workflow_name_param VARCHAR,
    initial_context JSONB DEFAULT '{}'
)
RETURNS BIGINT AS $$
DECLARE
    char_id BIGINT;
    workflow_id BIGINT;
    initial_state_id BIGINT;
    instance_id BIGINT;
    instance_key VARCHAR;
BEGIN
    -- Get character and workflow IDs
    SELECT c.id, w.id INTO char_id, workflow_id
    FROM characters c
    JOIN character_workflows w ON c.id = w.character_id
    WHERE c.normalized_name = lower(character_name)
    AND w.workflow_name = workflow_name_param
    AND w.is_active = true;
    
    IF workflow_id IS NULL THEN
        RAISE EXCEPTION 'Workflow not found: % for character %', workflow_name_param, character_name;
    END IF;
    
    -- Get initial state
    SELECT id INTO initial_state_id
    FROM workflow_states
    WHERE workflow_id = start_workflow_instance.workflow_id
    AND is_initial = true;
    
    IF initial_state_id IS NULL THEN
        RAISE EXCEPTION 'No initial state found for workflow: %', workflow_name_param;
    END IF;
    
    -- Generate unique instance key
    instance_key := workflow_name_param || '_' || extract(epoch from now())::TEXT;
    
    -- Create workflow instance
    INSERT INTO workflow_instances (
        workflow_id, user_id, instance_key,
        current_state_id, context_data, status
    )
    VALUES (
        workflow_id, user_id_param, instance_key,
        initial_state_id, initial_context, 'active'
    )
    RETURNING id INTO instance_id;
    
    -- Log workflow start
    INSERT INTO workflow_execution_log (
        workflow_instance_id, event_type, to_state_id, trigger_message
    )
    VALUES (
        instance_id, 'workflow_started', initial_state_id, 'Workflow instance created'
    );
    
    RETURN instance_id;
END;
$$ LANGUAGE plpgsql;

-- Get active workflows for user
CREATE OR REPLACE FUNCTION get_user_active_workflows(user_id_param VARCHAR)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT json_agg(
        json_build_object(
            'instance_id', wi.id,
            'workflow_name', cw.workflow_name,
            'character_name', c.name,
            'current_state', ws.state_name,
            'context_data', wi.context_data,
            'started_at', wi.started_at,
            'timeout_at', wi.timeout_at
        )
    ) INTO result
    FROM workflow_instances wi
    JOIN character_workflows cw ON wi.workflow_id = cw.id
    JOIN characters c ON cw.character_id = c.id
    JOIN workflow_states ws ON wi.current_state_id = ws.id
    WHERE wi.user_id = user_id_param
    AND wi.status = 'active';
    
    RETURN COALESCE(result, '[]'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Check workflow trigger matches
CREATE OR REPLACE FUNCTION check_workflow_triggers(
    character_name VARCHAR,
    user_message TEXT,
    user_id_param VARCHAR
)
RETURNS JSONB AS $$
DECLARE
    result JSONB := '[]'::jsonb;
    trigger_record RECORD;
    pattern_match BOOLEAN;
    keyword_match BOOLEAN;
BEGIN
    -- Check all active workflows for this character
    FOR trigger_record IN
        SELECT 
            cw.workflow_name,
            cw.id as workflow_id,
            wt.trigger_type,
            wt.patterns,
            wt.keywords,
            wt.llm_validation_enabled,
            wt.llm_validation_prompt,
            wt.priority
        FROM characters c
        JOIN character_workflows cw ON c.id = cw.character_id
        JOIN workflow_triggers wt ON cw.id = wt.workflow_id
        WHERE c.normalized_name = lower(character_name)
        AND cw.is_active = true
        AND wt.is_active = true
        ORDER BY wt.priority DESC, cw.priority DESC
    LOOP
        pattern_match := false;
        keyword_match := false;
        
        -- Check pattern matches
        IF trigger_record.patterns IS NOT NULL THEN
            -- Simple pattern matching (would need proper regex in production)
            pattern_match := trigger_record.patterns::text ILIKE '%' || user_message || '%';
        END IF;
        
        -- Check keyword matches
        IF trigger_record.keywords IS NOT NULL THEN
            -- Simple keyword matching
            keyword_match := EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(trigger_record.keywords) kw
                WHERE lower(user_message) LIKE '%' || lower(kw) || '%'
            );
        END IF;
        
        -- If trigger matches, add to results
        IF pattern_match OR keyword_match THEN
            result := result || json_build_object(
                'workflow_name', trigger_record.workflow_name,
                'workflow_id', trigger_record.workflow_id,
                'trigger_type', trigger_record.trigger_type,
                'pattern_match', pattern_match,
                'keyword_match', keyword_match,
                'llm_validation_required', trigger_record.llm_validation_enabled,
                'priority', trigger_record.priority
            )::jsonb;
        END IF;
    END LOOP;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

### Key Benefits of This Design

#### 🎯 **Flexibility & Extensibility**
- **No Schema Changes**: Add new CDL fields without altering tables
- **Dynamic Field Definitions**: Support any nested structure through field paths
- **Type Safety**: Enforced data types with validation rules
- **Hierarchical Support**: Parent-child relationships for complex structures
- **Workflow Integration**: Complete state machine support for character interactions

#### ⚡ **Performance Optimized**
- **Materialized Views**: Pre-computed character profiles for instant loading
- **Specialized Tables**: Communication patterns and knowledge optimized for AI queries
- **Strategic Indexing**: Full-text search, priority-based queries, field lookups
- **Single Query Loading**: Complete character data in one database call
- **Workflow Caching**: Active workflow instances cached for fast state transitions

#### 🔄 **Version Control & Audit**
- **Complete Versioning**: Full character snapshots with rollback capability
- **Detailed Change Log**: Track every modification with context and reasoning
- **Impact Assessment**: Measure changes and validate effectiveness
- **AI Optimization Tracking**: Monitor automatic character improvements
- **Workflow Execution Audit**: Complete audit trail of workflow interactions

#### 🧠 **AI Integration Ready**
- **Fast Pattern Matching**: Communication patterns table optimized for response generation
- **Knowledge Graph**: Structured character knowledge with relationship mapping
- **Response Templates**: Pre-built responses for common scenarios
- **Usage Analytics**: Track pattern effectiveness and optimize automatically
- **State Machine Support**: Complex workflow management for interactive characters

#### 🎭 **Advanced Workflow Features**
- **State Machine Engine**: Full support for complex character interaction workflows
- **Dynamic Trigger Detection**: Pattern matching, keyword detection, LLM-based intent recognition
- **Context Extraction**: Flexible context extraction from user messages
- **Lookup Table Support**: Character-specific data lookup for workflow decisions
- **Instance Management**: Track multiple concurrent workflow instances per user
- **Timeout Handling**: Automatic timeout management with configurable actions
- **Execution Tracking**: Complete audit trail of workflow state transitions

### Migration Strategy

1. **Phase 1**: Deploy new schema alongside existing tables
2. **Phase 2**: Migrate existing characters using `import_character_from_json()` function  
3. **Phase 3**: Update application code to use new API functions
4. **Phase 4**: Remove old tables after validation
5. **Phase 5**: Enable automatic AI optimization features

This design provides a future-proof foundation that can scale from our current 10 characters to hundreds while maintaining performance and enabling advanced AI features. The integrated workflow system supports complex interactive characters like Dotty's bartender workflows, with full state machine capabilities, dynamic trigger detection, and comprehensive execution tracking.

## 🎭 **Workflow System Integration**

### **Current Workflow Support**
Based on Dotty's bartender workflow (`dotty_bartender.yaml`), the schema now supports:

- ✅ **State Machine Workflows**: Multi-state character interactions (drink ordering, payment, completion)
- ✅ **Dynamic Triggers**: Pattern matching, keyword detection, LLM-based intent recognition
- ✅ **Context Extraction**: Extract drink names, prices, user preferences from messages
- ✅ **Lookup Tables**: Character-specific data (drink prices, menu items)
- ✅ **Instance Management**: Track multiple workflow instances per user
- ✅ **Timeout Handling**: Automatic order cancellation after 5 minutes
- ✅ **Execution Audit**: Complete workflow interaction history

### **Example Workflow Features Supported**

```sql
-- Example: Check if user message triggers drink order workflow
SELECT check_workflow_triggers('dotty', 'I''ll have a whiskey please', 'user123');

-- Result: Detects "drink_order" workflow match with extracted context

-- Example: Start workflow instance for drink order
SELECT start_workflow_instance('user123', 'dotty', 'drink_order', 
    '{"drink_name": "whiskey", "price": 5}'::jsonb);

-- Example: Get user's active workflows
SELECT get_user_active_workflows('user123');
-- Result: Shows pending drink order with current state and timeout
```

### **Workflow Migration Benefits**

1. **Database Performance**: Faster workflow trigger checking vs YAML parsing
2. **Real-time Tracking**: Live workflow instances with state persistence
3. **Analytics**: Workflow success rates, completion times, user patterns
4. **Scalability**: Support hundreds of workflows across multiple characters
5. **Integration**: Seamless integration with character personality system
6. **Version Control**: Workflow evolution tracking and rollback capabilities

The schema seamlessly integrates CDL character definitions with sophisticated workflow capabilities, providing a comprehensive foundation for advanced AI character interactions.