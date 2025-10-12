-- ============================================================================
-- WhisperEngine Database Schema - AUTHORITATIVE INITIALIZATION SCRIPT
-- ============================================================================
-- 
-- This is the SINGLE SOURCE OF TRUTH for WhisperEngine database schema.
-- Generated from production database on: October 12, 2025
-- 
-- PURPOSE:
--   - Fresh database initialization for development and quickstart setups
--   - Complete schema including all 73 production tables
--   - All extensions, functions, types, indexes, and constraints
-- 
-- INCLUDES:
--   - Core tables: characters, universal_users, user_profiles, conversations
--   - 40+ CDL character tables (identity, personality, voice, expertise, etc.)
--   - Semantic knowledge graph: fact_entities, entity_relationships
--   - Memory systems: memory_entries, conversations, relationship_scores
--   - Dynamic personality: personality_evolution_timeline, optimization tables
--   - Roleplay systems: roleplay_transactions, role_transactions
--   - Platform integrations: platform_identities, banned_users
-- 
-- USAGE:
--   psql -U whisperengine -d whisperengine -f sql/00_init.sql
-- 
-- NOTE: This replaces all migration-based initialization. For schema changes,
--       update this file directly or regenerate from production database.
-- 
-- ============================================================================

--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 16.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: btree_gin; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS btree_gin WITH SCHEMA public;


--
-- Name: EXTENSION btree_gin; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION btree_gin IS 'support for indexing common datatypes in GIN';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: character_archetype_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.character_archetype_enum AS ENUM (
    'real_world',
    'fantasy_mystical',
    'narrative_ai'
);


--
-- Name: workflow_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.workflow_status_enum AS ENUM (
    'active',
    'paused',
    'completed',
    'failed',
    'cancelled'
);


--
-- Name: analyze_cdl_graph_index_performance(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.analyze_cdl_graph_index_performance() RETURNS TABLE(index_name text, table_name text, index_size text, index_scans bigint, tuples_read bigint, tuples_fetched bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.indexrelname::text as index_name,
        t.relname::text as table_name,
        pg_size_pretty(pg_relation_size(i.indexrelid)) as index_size,
        s.idx_scan as index_scans,
        s.idx_tup_read as tuples_read,
        s.idx_tup_fetch as tuples_fetched
    FROM pg_class i
    JOIN pg_index idx ON i.oid = idx.indexrelid
    JOIN pg_class t ON idx.indrelid = t.oid
    JOIN pg_stat_user_indexes s ON i.oid = s.indexrelid
    WHERE i.indexrelname LIKE 'idx_character_%' 
       OR i.indexrelname LIKE 'idx_fact_%'
       OR i.indexrelname LIKE 'idx_user_fact_%'
    ORDER BY s.idx_scan DESC;
END;
$$;


--
-- Name: discover_similar_entities(uuid, double precision, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.discover_similar_entities(p_entity_id uuid, p_similarity_threshold double precision DEFAULT 0.3, p_limit integer DEFAULT 5) RETURNS TABLE(similar_entity_id uuid, similar_entity_name text, similarity_score double precision)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fe2.id,
        fe2.entity_name,
        similarity(fe1.entity_name, fe2.entity_name) as sim_score
    FROM fact_entities fe1
    CROSS JOIN fact_entities fe2
    WHERE fe1.id = p_entity_id
      AND fe2.id != p_entity_id
      AND fe1.entity_type = fe2.entity_type
      AND similarity(fe1.entity_name, fe2.entity_name) > p_similarity_threshold
    ORDER BY sim_score DESC
    LIMIT p_limit;
END;
$$;


--
-- Name: FUNCTION discover_similar_entities(p_entity_id uuid, p_similarity_threshold double precision, p_limit integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.discover_similar_entities(p_entity_id uuid, p_similarity_threshold double precision, p_limit integer) IS 'Auto-discover similar entities using trigram similarity';


--
-- Name: get_character_cdl_v2(character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_character_cdl_v2(p_normalized_name character varying) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT cdl_data INTO result
    FROM character_profiles_v2
    WHERE normalized_name = p_normalized_name;
    
    RETURN result;
END;
$$;


--
-- Name: get_character_v2(character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_character_v2(char_normalized_name character varying) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT to_jsonb(cp.*) INTO result
    FROM character_profiles_v2 cp
    WHERE cp.normalized_name = char_normalized_name;
    
    RETURN COALESCE(result, '{}'::jsonb);
END;
$$;


--
-- Name: get_user_facts_with_relations(uuid, text, double precision, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_user_facts_with_relations(p_user_id uuid, p_entity_type text DEFAULT NULL::text, p_min_confidence double precision DEFAULT 0.5, p_limit integer DEFAULT 20) RETURNS TABLE(entity_name text, entity_category text, relationship_type text, confidence double precision, emotional_context text, mentioned_by_character text, related_entities_count bigint, last_updated timestamp without time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    WITH user_entities AS (
        SELECT 
            fe.entity_name,
            fe.category,
            ufr.relationship_type,
            ufr.confidence,
            ufr.emotional_context,
            ufr.mentioned_by_character,
            ufr.updated_at,
            ufr.entity_id
        FROM user_fact_relationships ufr
        JOIN fact_entities fe ON ufr.entity_id = fe.id
        WHERE ufr.user_id = p_user_id
          AND (p_entity_type IS NULL OR fe.entity_type = p_entity_type)
          AND ufr.confidence >= p_min_confidence
    )
    SELECT 
        ue.entity_name,
        ue.category,
        ue.relationship_type,
        ue.confidence,
        ue.emotional_context,
        ue.mentioned_by_character,
        COUNT(er.id) as related_count,
        ue.updated_at
    FROM user_entities ue
    LEFT JOIN entity_relationships er ON ue.entity_id = er.from_entity_id
    GROUP BY 
        ue.entity_name, ue.category, ue.relationship_type, 
        ue.confidence, ue.emotional_context, ue.mentioned_by_character, ue.updated_at
    ORDER BY ue.confidence DESC, ue.updated_at DESC
    LIMIT p_limit;
END;
$$;


--
-- Name: FUNCTION get_user_facts_with_relations(p_user_id uuid, p_entity_type text, p_min_confidence double precision, p_limit integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_user_facts_with_relations(p_user_id uuid, p_entity_type text, p_min_confidence double precision, p_limit integer) IS 'Get user facts with count of related entities';


--
-- Name: get_user_workflows_v2(character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_user_workflows_v2(user_id_param character varying) RETURNS jsonb
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: maintain_cdl_graph_indexes(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.maintain_cdl_graph_indexes() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Analyze tables for optimal query planning
    ANALYZE characters;
    ANALYZE character_background;
    ANALYZE character_memories; 
    ANALYZE character_relationships;
    ANALYZE character_abilities;
    ANALYZE fact_entities;
    ANALYZE user_fact_relationships;
    
    -- Log maintenance completion
    RAISE NOTICE 'CDL Graph Intelligence indexes analyzed and optimized';
END;
$$;


--
-- Name: migrate_to_jsonb_schema(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.migrate_to_jsonb_schema() RETURNS integer
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: refresh_character_profiles_v2(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.refresh_character_profiles_v2() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY character_profiles_v2;
    RETURN NULL;
END;
$$;


--
-- Name: start_workflow_v2(character varying, character varying, character varying, jsonb, jsonb); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.start_workflow_v2(user_id_param character varying, char_normalized_name character varying, workflow_name_param character varying, initial_context jsonb DEFAULT '{}'::jsonb, workflow_config_param jsonb DEFAULT '{}'::jsonb) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: track_personality_parameter_changes(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.track_personality_parameter_changes() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Only track changes to personality-related fields
    IF OLD.personality_traits IS DISTINCT FROM NEW.personality_traits THEN
        INSERT INTO personality_evolution_timeline (
            character_name, parameter_path, old_value, new_value, 
            change_timestamp, change_reason
        ) VALUES (
            NEW.normalized_name, 'personality_traits', 
            OLD.personality_traits::text, NEW.personality_traits::text,
            NOW(), 'CDL personality_traits update'
        );
    END IF;
    
    IF OLD.communication_styles IS DISTINCT FROM NEW.communication_styles THEN
        INSERT INTO personality_evolution_timeline (
            character_name, parameter_path, old_value, new_value,
            change_timestamp, change_reason
        ) VALUES (
            NEW.normalized_name, 'communication_styles',
            OLD.communication_styles::text, NEW.communication_styles::text,
            NOW(), 'CDL communication_styles update'
        );
    END IF;
    
    IF OLD.empathy IS DISTINCT FROM NEW.empathy THEN
        INSERT INTO personality_evolution_timeline (
            character_name, parameter_path, old_value, new_value,
            change_timestamp, change_reason
        ) VALUES (
            NEW.normalized_name, 'emotional_intelligence.empathy',
            OLD.empathy::text, NEW.empathy::text,
            NOW(), 'CDL empathy update'
        );
    END IF;
    
    RETURN NEW;
END;
$$;


--
-- Name: FUNCTION track_personality_parameter_changes(); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.track_personality_parameter_changes() IS 'Sprint 4: Auto-tracks personality changes in CDL character updates';


--
-- Name: update_character_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_character_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE characters SET updated_date = CURRENT_TIMESTAMP WHERE id = NEW.character_id;
    RETURN NEW;
END;
$$;


--
-- Name: update_roleplay_transaction_timestamp(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_roleplay_transaction_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- Name: update_updated_at_v2(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_v2() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


--
-- Name: update_workflow_state_v2(bigint, character varying, character varying, jsonb); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_workflow_state_v2(p_character_id bigint, p_workflow_name character varying, p_new_state character varying, p_context_data jsonb DEFAULT '{}'::jsonb) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: upsert_character_v2(character varying, character varying, character varying, public.character_archetype_enum, jsonb, jsonb, jsonb); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.upsert_character_v2(p_name character varying, p_normalized_name character varying, p_bot_name character varying, p_archetype public.character_archetype_enum, p_cdl_data jsonb, p_workflow_data jsonb DEFAULT '{}'::jsonb, p_metadata jsonb DEFAULT '{}'::jsonb) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
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
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: banned_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.banned_users (
    id integer NOT NULL,
    discord_user_id text NOT NULL,
    banned_by text NOT NULL,
    ban_reason text,
    banned_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp without time zone,
    is_active boolean DEFAULT true,
    notes text
);


--
-- Name: banned_users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.banned_users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: banned_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.banned_users_id_seq OWNED BY public.banned_users.id;


--
-- Name: character_abilities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_abilities (
    id integer NOT NULL,
    character_id integer,
    category character varying(50) NOT NULL,
    ability_name character varying(100) NOT NULL,
    proficiency_level integer DEFAULT 5,
    description text,
    development_method text,
    usage_frequency character varying(20) DEFAULT 'regular'::character varying
);


--
-- Name: character_abilities_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_abilities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_abilities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_abilities_id_seq OWNED BY public.character_abilities.id;


--
-- Name: character_ai_scenarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_ai_scenarios (
    id integer NOT NULL,
    character_id integer,
    scenario_type character varying(100) NOT NULL,
    scenario_name character varying(200),
    trigger_phrases text,
    response_pattern character varying(100),
    tier_1_response text,
    tier_2_response text,
    tier_3_response text,
    example_usage text
);


--
-- Name: TABLE character_ai_scenarios; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_ai_scenarios IS 'AI identity handling scenarios and tier-based responses';


--
-- Name: character_ai_scenarios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_ai_scenarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_ai_scenarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_ai_scenarios_id_seq OWNED BY public.character_ai_scenarios.id;


--
-- Name: character_appearance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_appearance (
    id integer NOT NULL,
    character_id integer,
    category character varying(50) NOT NULL,
    attribute character varying(100) NOT NULL,
    value text NOT NULL,
    description text
);


--
-- Name: character_appearance_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_appearance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_appearance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_appearance_id_seq OWNED BY public.character_appearance.id;


--
-- Name: character_attributes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_attributes (
    id integer NOT NULL,
    character_id integer NOT NULL,
    category character varying(200) NOT NULL,
    description text NOT NULL,
    importance character varying(100),
    display_order integer,
    active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE character_attributes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_attributes IS 'Universal character attributes - replaces separate fears/dreams/quirks/values/beliefs tables';


--
-- Name: COLUMN character_attributes.category; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.character_attributes.category IS 'Type of attribute: fear, dream, quirk, value, belief, goal, strength, weakness, etc.';


--
-- Name: character_attributes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_attributes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_attributes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_attributes_id_seq OWNED BY public.character_attributes.id;


--
-- Name: character_background; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_background (
    id integer NOT NULL,
    character_id integer,
    category character varying(50) NOT NULL,
    period character varying(100),
    title text,
    description text NOT NULL,
    date_range text,
    importance_level integer DEFAULT 5,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: character_background_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_background_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_background_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_background_id_seq OWNED BY public.character_background.id;


--
-- Name: character_behavioral_triggers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_behavioral_triggers (
    id integer NOT NULL,
    character_id integer,
    trigger_type character varying(50) NOT NULL,
    trigger_value character varying(200) NOT NULL,
    response_type character varying(50) NOT NULL,
    response_description text NOT NULL,
    intensity_level integer DEFAULT 5,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: character_behavioral_triggers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_behavioral_triggers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_behavioral_triggers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_behavioral_triggers_id_seq OWNED BY public.character_behavioral_triggers.id;


--
-- Name: character_communication_patterns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_communication_patterns (
    id integer NOT NULL,
    character_id integer,
    pattern_type character varying(50) NOT NULL,
    pattern_name character varying(100) NOT NULL,
    pattern_value text NOT NULL,
    context character varying(100),
    frequency character varying(20) DEFAULT 'regular'::character varying,
    description text
);


--
-- Name: character_communication_patterns_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_communication_patterns_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_communication_patterns_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_communication_patterns_id_seq OWNED BY public.character_communication_patterns.id;


--
-- Name: character_context_guidance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_context_guidance (
    id integer NOT NULL,
    context_id integer NOT NULL,
    guidance_type character varying(200) NOT NULL,
    guidance_text text NOT NULL,
    display_order integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE character_context_guidance; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_context_guidance IS 'Avoid/encourage/example items for conversation contexts';


--
-- Name: character_context_guidance_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_context_guidance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_context_guidance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_context_guidance_id_seq OWNED BY public.character_context_guidance.id;


--
-- Name: character_conversation_contexts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_conversation_contexts (
    id integer NOT NULL,
    character_id integer NOT NULL,
    context_name character varying(500) NOT NULL,
    energy_description text,
    approach_strategy text,
    transition_style text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE character_conversation_contexts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_conversation_contexts IS 'Context-specific conversation patterns - replaces complex nested JSON structures';


--
-- Name: character_conversation_contexts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_conversation_contexts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_conversation_contexts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_conversation_contexts_id_seq OWNED BY public.character_conversation_contexts.id;


--
-- Name: character_conversation_directives; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_conversation_directives (
    id integer NOT NULL,
    conversation_flow_id integer,
    directive_type character varying(50) NOT NULL,
    directive_content text NOT NULL,
    order_sequence integer
);


--
-- Name: TABLE character_conversation_directives; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_conversation_directives IS 'Specific things to avoid/encourage in each conversation flow';


--
-- Name: character_conversation_directives_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_conversation_directives_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_conversation_directives_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_conversation_directives_id_seq OWNED BY public.character_conversation_directives.id;


--
-- Name: character_conversation_flows; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_conversation_flows (
    id integer NOT NULL,
    character_id integer,
    flow_type character varying(200) NOT NULL,
    flow_name character varying(200),
    energy_level character varying(200),
    approach_description text,
    transition_style text,
    priority integer DEFAULT 50,
    context text
);


--
-- Name: TABLE character_conversation_flows; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_conversation_flows IS 'Conversation flow guidance for different interaction types';


--
-- Name: character_conversation_flows_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_conversation_flows_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_conversation_flows_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_conversation_flows_id_seq OWNED BY public.character_conversation_flows.id;


--
-- Name: character_cultural_expressions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_cultural_expressions (
    id integer NOT NULL,
    character_id integer,
    expression_type character varying(100) NOT NULL,
    expression_value text NOT NULL,
    meaning text,
    usage_context text,
    emotional_context character varying(50),
    frequency character varying(50)
);


--
-- Name: TABLE character_cultural_expressions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_cultural_expressions IS 'Cultural expressions and language-specific terms';


--
-- Name: character_cultural_expressions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_cultural_expressions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_cultural_expressions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_cultural_expressions_id_seq OWNED BY public.character_cultural_expressions.id;


--
-- Name: character_current_context; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_current_context (
    id integer NOT NULL,
    character_id integer NOT NULL,
    living_situation text,
    daily_routine text,
    recent_events text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE character_current_context; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_current_context IS 'Current life situation and context';


--
-- Name: character_current_context_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_current_context_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_current_context_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_current_context_id_seq OWNED BY public.character_current_context.id;


--
-- Name: character_current_goals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_current_goals (
    id integer NOT NULL,
    character_id integer NOT NULL,
    goal_text text NOT NULL,
    priority character varying(100),
    timeframe character varying(200),
    status character varying(100),
    display_order integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: character_current_goals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_current_goals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_current_goals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_current_goals_id_seq OWNED BY public.character_current_goals.id;


--
-- Name: character_directives; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_directives (
    id integer NOT NULL,
    character_id integer NOT NULL,
    directive_type character varying(200) NOT NULL,
    directive_text text NOT NULL,
    priority integer,
    display_order integer,
    context character varying(500),
    active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT character_directives_priority_check CHECK (((priority >= 1) AND (priority <= 10)))
);


--
-- Name: TABLE character_directives; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_directives IS 'Universal character directives - replaces core_principles/formatting_rules/adaptations tables';


--
-- Name: COLUMN character_directives.directive_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.character_directives.directive_type IS 'Type: core_principle, formatting_rule, adaptation, guideline, constraint, instruction';


--
-- Name: character_directives_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_directives_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_directives_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_directives_id_seq OWNED BY public.character_directives.id;


--
-- Name: character_emoji_patterns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_emoji_patterns (
    id integer NOT NULL,
    character_id integer,
    pattern_category character varying(100) NOT NULL,
    pattern_name character varying(100) NOT NULL,
    emoji_sequence text,
    usage_context text,
    frequency character varying(50),
    example_usage text
);


--
-- Name: TABLE character_emoji_patterns; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_emoji_patterns IS 'Emoji usage patterns for digital communication';


--
-- Name: character_emoji_patterns_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_emoji_patterns_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_emoji_patterns_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_emoji_patterns_id_seq OWNED BY public.character_emoji_patterns.id;


--
-- Name: character_emotion_profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_emotion_profile (
    id integer NOT NULL,
    character_id integer NOT NULL,
    default_mood text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: character_emotion_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_emotion_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_emotion_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_emotion_profile_id_seq OWNED BY public.character_emotion_profile.id;


--
-- Name: character_emotion_range; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_emotion_range (
    id integer NOT NULL,
    character_id integer NOT NULL,
    emotion_name character varying(200) NOT NULL,
    base_intensity numeric(3,2),
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT character_emotion_range_base_intensity_check CHECK (((base_intensity >= (0)::numeric) AND (base_intensity <= (1)::numeric)))
);


--
-- Name: TABLE character_emotion_range; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_emotion_range IS 'Base emotional range - how intensely character experiences each emotion';


--
-- Name: character_emotion_range_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_emotion_range_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_emotion_range_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_emotion_range_id_seq OWNED BY public.character_emotion_range.id;


--
-- Name: character_emotional_triggers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_emotional_triggers (
    id integer NOT NULL,
    character_id integer,
    trigger_type character varying(100) NOT NULL,
    trigger_category character varying(100),
    trigger_content text NOT NULL,
    emotional_response text,
    response_intensity character varying(50),
    response_examples text
);


--
-- Name: TABLE character_emotional_triggers; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_emotional_triggers IS 'Emotional triggers and corresponding responses';


--
-- Name: character_emotional_triggers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_emotional_triggers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_emotional_triggers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_emotional_triggers_id_seq OWNED BY public.character_emotional_triggers.id;


--
-- Name: character_emotional_triggers_v2; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_emotional_triggers_v2 (
    id integer NOT NULL,
    character_id integer NOT NULL,
    trigger_text text NOT NULL,
    valence character varying(100) NOT NULL,
    emotion_evoked character varying(200),
    intensity integer,
    response_guidance text,
    display_order integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT character_emotional_triggers_v2_intensity_check CHECK (((intensity >= 1) AND (intensity <= 10)))
);


--
-- Name: TABLE character_emotional_triggers_v2; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_emotional_triggers_v2 IS 'Universal emotional triggers - single table for positive/negative/neutral';


--
-- Name: character_emotional_triggers_v2_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_emotional_triggers_v2_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_emotional_triggers_v2_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_emotional_triggers_v2_id_seq OWNED BY public.character_emotional_triggers_v2.id;


--
-- Name: character_essence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_essence (
    id integer NOT NULL,
    character_id integer,
    essence_type character varying(50) NOT NULL,
    essence_name character varying(100) NOT NULL,
    description text NOT NULL,
    manifestation text,
    power_level integer
);


--
-- Name: character_essence_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_essence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_essence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_essence_id_seq OWNED BY public.character_essence.id;


--
-- Name: character_expertise_domains; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_expertise_domains (
    id integer NOT NULL,
    character_id integer,
    domain_name character varying(200) NOT NULL,
    expertise_level character varying(50),
    domain_description text,
    key_concepts text,
    teaching_approach text,
    passion_level integer,
    examples text
);


--
-- Name: TABLE character_expertise_domains; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_expertise_domains IS 'Professional expertise domains and knowledge areas';


--
-- Name: character_expertise_domains_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_expertise_domains_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_expertise_domains_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_expertise_domains_id_seq OWNED BY public.character_expertise_domains.id;


--
-- Name: character_identity_details; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_identity_details (
    id integer NOT NULL,
    character_id integer NOT NULL,
    full_name character varying(500),
    nickname character varying(500),
    gender character varying(200),
    location text,
    essence_nature text,
    essence_existence_method text,
    essence_anchor text,
    essence_core_identity text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE character_identity_details; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_identity_details IS 'Extended identity information';


--
-- Name: character_identity_details_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_identity_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_identity_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_identity_details_id_seq OWNED BY public.character_identity_details.id;


--
-- Name: character_instructions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_instructions (
    id integer NOT NULL,
    character_id integer,
    instruction_type character varying(50) NOT NULL,
    priority integer DEFAULT 5,
    instruction_text text NOT NULL,
    context text,
    active boolean DEFAULT true,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: character_instructions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_instructions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_instructions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_instructions_id_seq OWNED BY public.character_instructions.id;


--
-- Name: character_interests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_interests (
    id integer NOT NULL,
    character_id integer NOT NULL,
    category character varying(200) NOT NULL,
    interest_text text NOT NULL,
    proficiency_level integer,
    importance character varying(100),
    frequency character varying(100),
    display_order integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT character_interests_proficiency_level_check CHECK (((proficiency_level >= 1) AND (proficiency_level <= 10)))
);


--
-- Name: TABLE character_interests; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_interests IS 'Universal interests - replaces hobbies/conversation_topics/expertise tables';


--
-- Name: character_interests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_interests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_interests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_interests_id_seq OWNED BY public.character_interests.id;


--
-- Name: character_memories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_memories (
    id integer NOT NULL,
    character_id integer,
    memory_type character varying(50) NOT NULL,
    title character varying(200) NOT NULL,
    description text NOT NULL,
    emotional_impact integer DEFAULT 5,
    time_period text,
    importance_level integer DEFAULT 5,
    triggers text[],
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: character_memories_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_memories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_memories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_memories_id_seq OWNED BY public.character_memories.id;


--
-- Name: character_message_triggers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_message_triggers (
    id integer NOT NULL,
    character_id integer,
    trigger_category character varying(100) NOT NULL,
    trigger_type character varying(50) NOT NULL,
    trigger_value text NOT NULL,
    response_mode character varying(100),
    priority integer DEFAULT 50,
    is_active boolean DEFAULT true
);


--
-- Name: TABLE character_message_triggers; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_message_triggers IS 'Keywords and phrases that trigger specific response modes';


--
-- Name: character_message_triggers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_message_triggers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_message_triggers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_message_triggers_id_seq OWNED BY public.character_message_triggers.id;


--
-- Name: character_metadata; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_metadata (
    id integer NOT NULL,
    character_id integer,
    version integer DEFAULT 1,
    character_tags text[],
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    author text,
    notes text
);


--
-- Name: character_metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_metadata_id_seq OWNED BY public.character_metadata.id;


--
-- Name: character_relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_relationships (
    id integer NOT NULL,
    character_id integer,
    related_entity character varying(200) NOT NULL,
    relationship_type character varying(50) NOT NULL,
    relationship_strength integer DEFAULT 5,
    description text,
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    communication_style text,
    memory_sharing text,
    name_usage text,
    connection_nature text,
    recognition_pattern text
);


--
-- Name: COLUMN character_relationships.communication_style; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.character_relationships.communication_style IS 'How character communicates with this entity';


--
-- Name: COLUMN character_relationships.memory_sharing; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.character_relationships.memory_sharing IS 'How memories are shared in this relationship';


--
-- Name: COLUMN character_relationships.name_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.character_relationships.name_usage IS 'Name/nickname used in this relationship';


--
-- Name: character_relationships_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_relationships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_relationships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_relationships_id_seq OWNED BY public.character_relationships.id;


--
-- Name: character_response_guidelines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_response_guidelines (
    id integer NOT NULL,
    character_id integer,
    guideline_type character varying(100) NOT NULL,
    guideline_name character varying(200),
    guideline_content text NOT NULL,
    priority integer DEFAULT 50,
    context character varying(100),
    is_critical boolean DEFAULT false,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE character_response_guidelines; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_response_guidelines IS 'Response length, formatting rules, and critical directives for character behavior';


--
-- Name: character_response_guidelines_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_response_guidelines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_response_guidelines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_response_guidelines_id_seq OWNED BY public.character_response_guidelines.id;


--
-- Name: character_response_modes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_response_modes (
    id integer NOT NULL,
    character_id integer,
    mode_name character varying(100) NOT NULL,
    mode_description text,
    response_style text,
    length_guideline text,
    tone_adjustment text,
    conflict_resolution_priority integer,
    examples text
);


--
-- Name: TABLE character_response_modes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_response_modes IS 'Different response modes (technical, creative, brief) and their guidelines';


--
-- Name: character_response_modes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_response_modes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_response_modes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_response_modes_id_seq OWNED BY public.character_response_modes.id;


--
-- Name: character_roleplay_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_roleplay_config (
    id integer NOT NULL,
    character_id integer NOT NULL,
    allow_full_roleplay_immersion boolean DEFAULT false,
    philosophy text,
    strategy text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE character_roleplay_config; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_roleplay_config IS 'AI identity configuration - scalar values only';


--
-- Name: character_roleplay_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_roleplay_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_roleplay_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_roleplay_config_id_seq OWNED BY public.character_roleplay_config.id;


--
-- Name: character_roleplay_scenarios_v2; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_roleplay_scenarios_v2 (
    id integer NOT NULL,
    character_id integer NOT NULL,
    scenario_name character varying(500) NOT NULL,
    response_pattern character varying(500),
    tier_1_response text,
    tier_2_response text,
    tier_3_response text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE character_roleplay_scenarios_v2; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_roleplay_scenarios_v2 IS 'Roleplay scenario responses - replaces complex nested JSON';


--
-- Name: character_roleplay_scenarios_v2_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_roleplay_scenarios_v2_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_roleplay_scenarios_v2_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_roleplay_scenarios_v2_id_seq OWNED BY public.character_roleplay_scenarios_v2.id;


--
-- Name: character_scenario_triggers_v2; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_scenario_triggers_v2 (
    id integer NOT NULL,
    scenario_id integer NOT NULL,
    trigger_phrase text NOT NULL,
    display_order integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: character_scenario_triggers_v2_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_scenario_triggers_v2_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_scenario_triggers_v2_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_scenario_triggers_v2_id_seq OWNED BY public.character_scenario_triggers_v2.id;


--
-- Name: character_speech_patterns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_speech_patterns (
    id integer NOT NULL,
    character_id integer,
    pattern_type character varying(100) NOT NULL,
    pattern_value text NOT NULL,
    usage_frequency character varying(50),
    context character varying(100),
    priority integer DEFAULT 50
);


--
-- Name: TABLE character_speech_patterns; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_speech_patterns IS 'Speech patterns, vocabulary preferences, and language style';


--
-- Name: character_speech_patterns_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_speech_patterns_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_speech_patterns_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_speech_patterns_id_seq OWNED BY public.character_speech_patterns.id;


--
-- Name: character_values; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_values (
    id integer NOT NULL,
    character_id integer,
    value_key character varying(300) NOT NULL,
    value_description text NOT NULL,
    importance_level character varying(100) DEFAULT 'medium'::character varying,
    category character varying(200)
);


--
-- Name: TABLE character_values; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_values IS 'Core values, beliefs, and fears that drive character behavior';


--
-- Name: character_values_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_values_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_values_id_seq OWNED BY public.character_values.id;


--
-- Name: character_vocabulary; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_vocabulary (
    id integer NOT NULL,
    character_id integer NOT NULL,
    word_or_phrase text NOT NULL,
    preference character varying(100) NOT NULL,
    usage_context text,
    frequency character varying(100),
    reason text,
    display_order integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE character_vocabulary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_vocabulary IS 'Universal vocabulary preferences - replaces preferred_words/avoided_words tables';


--
-- Name: COLUMN character_vocabulary.preference; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.character_vocabulary.preference IS 'preferred, avoided, signature, forbidden';


--
-- Name: character_vocabulary_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_vocabulary_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_vocabulary_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_vocabulary_id_seq OWNED BY public.character_vocabulary.id;


--
-- Name: character_voice_profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_voice_profile (
    id integer NOT NULL,
    character_id integer NOT NULL,
    tone text,
    pace text,
    volume text,
    accent text,
    sentence_structure text,
    punctuation_style text,
    response_length_guidance text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE character_voice_profile; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_voice_profile IS 'Voice and speech characteristics';


--
-- Name: character_voice_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_voice_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_voice_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_voice_profile_id_seq OWNED BY public.character_voice_profile.id;


--
-- Name: character_voice_traits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.character_voice_traits (
    id integer NOT NULL,
    character_id integer,
    trait_type character varying(100) NOT NULL,
    trait_value text NOT NULL,
    situational_context text,
    examples text
);


--
-- Name: TABLE character_voice_traits; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.character_voice_traits IS 'Voice characteristics and speaking patterns';


--
-- Name: character_voice_traits_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.character_voice_traits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: character_voice_traits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.character_voice_traits_id_seq OWNED BY public.character_voice_traits.id;


--
-- Name: characters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.characters (
    id integer NOT NULL,
    name character varying(500) NOT NULL,
    normalized_name character varying(200) NOT NULL,
    occupation character varying(500),
    description text,
    archetype character varying(100) DEFAULT 'real-world'::character varying,
    allow_full_roleplay boolean DEFAULT false,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE characters; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.characters IS 'Core character information - minimal fields needed by CDL AI integration';


--
-- Name: characters_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.characters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: characters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.characters_id_seq OWNED BY public.characters.id;


--
-- Name: communication_styles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.communication_styles (
    id integer NOT NULL,
    character_id integer,
    engagement_level numeric(3,2),
    formality character varying(500),
    emotional_expression numeric(3,2),
    response_length text,
    conversation_flow_guidance text,
    ai_identity_handling text,
    response_length_preference character varying(200)
);


--
-- Name: TABLE communication_styles; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.communication_styles IS 'Communication preferences and style guidelines';


--
-- Name: COLUMN communication_styles.response_length_preference; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.communication_styles.response_length_preference IS 'Preferred response length: concise, medium, detailed, variable';


--
-- Name: communication_styles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.communication_styles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: communication_styles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.communication_styles_id_seq OWNED BY public.communication_styles.id;


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    id integer NOT NULL,
    user_id text NOT NULL,
    channel_id text NOT NULL,
    message_content text NOT NULL,
    bot_response text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    context_used text,
    response_time_ms integer,
    ai_model_used text
);


--
-- Name: conversations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.conversations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: conversations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.conversations_id_seq OWNED BY public.conversations.id;


--
-- Name: dynamic_conversation_analyses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dynamic_conversation_analyses (
    id integer NOT NULL,
    user_id character varying(255),
    context_id character varying(255),
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    message_length integer,
    formality_score double precision,
    emotional_openness double precision,
    conversation_depth double precision,
    topics_discussed jsonb DEFAULT '[]'::jsonb,
    emotional_tone character varying(50),
    humor_detected boolean DEFAULT false,
    support_seeking boolean DEFAULT false
);


--
-- Name: dynamic_conversation_analyses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dynamic_conversation_analyses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dynamic_conversation_analyses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dynamic_conversation_analyses_id_seq OWNED BY public.dynamic_conversation_analyses.id;


--
-- Name: dynamic_personality_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dynamic_personality_profiles (
    user_id character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    total_conversations integer DEFAULT 0,
    relationship_depth double precision DEFAULT 0.0,
    trust_level double precision DEFAULT 0.0,
    preferred_response_style jsonb DEFAULT '{}'::jsonb
);


--
-- Name: dynamic_personality_traits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dynamic_personality_traits (
    id integer NOT NULL,
    user_id character varying(255),
    dimension character varying(100),
    value double precision,
    confidence double precision,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    evidence_count integer DEFAULT 0,
    evidence_sources jsonb DEFAULT '[]'::jsonb
);


--
-- Name: dynamic_personality_traits_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dynamic_personality_traits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dynamic_personality_traits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dynamic_personality_traits_id_seq OWNED BY public.dynamic_personality_traits.id;


--
-- Name: emotions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.emotions (
    id integer NOT NULL,
    user_id text NOT NULL,
    detected_emotion text NOT NULL,
    confidence real NOT NULL,
    context text,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    response_adapted boolean DEFAULT false
);


--
-- Name: emotions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.emotions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: emotions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.emotions_id_seq OWNED BY public.emotions.id;


--
-- Name: entity_relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_relationships (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    from_entity_id uuid NOT NULL,
    to_entity_id uuid NOT NULL,
    relationship_type text NOT NULL,
    weight double precision DEFAULT 0.5,
    bidirectional boolean DEFAULT false,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT entity_relationships_check CHECK ((from_entity_id <> to_entity_id)),
    CONSTRAINT entity_relationships_relationship_type_check CHECK ((relationship_type = ANY (ARRAY['similar_to'::text, 'part_of'::text, 'category_of'::text, 'related_to'::text, 'opposite_of'::text, 'requires'::text]))),
    CONSTRAINT entity_relationships_weight_check CHECK (((weight >= (0)::double precision) AND (weight <= (1)::double precision)))
);


--
-- Name: TABLE entity_relationships; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.entity_relationships IS 'Relationships between entities for graph traversal';


--
-- Name: COLUMN entity_relationships.bidirectional; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.entity_relationships.bidirectional IS 'If true, relationship applies in both directions';


--
-- Name: fact_entities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_entities (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_type text NOT NULL,
    entity_name text NOT NULL,
    category text,
    subcategory text,
    attributes jsonb DEFAULT '{}'::jsonb,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, ((((((COALESCE(entity_name, ''::text) || ' '::text) || COALESCE(category, ''::text)) || ' '::text) || COALESCE(subcategory, ''::text)) || ' '::text) || COALESCE((attributes ->> 'tags'::text), ''::text)))) STORED,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: TABLE fact_entities; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.fact_entities IS 'Core entity storage for facts and concepts';


--
-- Name: COLUMN fact_entities.entity_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fact_entities.entity_type IS 'Type of entity for categorical organization';


--
-- Name: COLUMN fact_entities.attributes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fact_entities.attributes IS 'Flexible JSONB storage for entity-specific attributes';


--
-- Name: COLUMN fact_entities.search_vector; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.fact_entities.search_vector IS 'Auto-generated full-text search vector';


--
-- Name: facts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.facts (
    id integer NOT NULL,
    user_id text,
    fact_type text NOT NULL,
    subject text NOT NULL,
    content text NOT NULL,
    confidence_score real DEFAULT 0.8,
    source text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    verified boolean DEFAULT false,
    global_fact boolean DEFAULT false
);


--
-- Name: facts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.facts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: facts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.facts_id_seq OWNED BY public.facts.id;


--
-- Name: memory_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.memory_entries (
    id integer NOT NULL,
    user_id text NOT NULL,
    memory_type text NOT NULL,
    content text NOT NULL,
    importance_score real DEFAULT 0.5,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_accessed timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    access_count integer DEFAULT 0,
    tags text DEFAULT '[]'::text,
    metadata text DEFAULT '{}'::text
);


--
-- Name: memory_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.memory_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: memory_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.memory_entries_id_seq OWNED BY public.memory_entries.id;


--
-- Name: performance_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.performance_metrics (
    id integer NOT NULL,
    metric_name text NOT NULL,
    metric_value real NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    tags text DEFAULT '{}'::text
);


--
-- Name: performance_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.performance_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: performance_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.performance_metrics_id_seq OWNED BY public.performance_metrics.id;


--
-- Name: personality_evolution_timeline; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.personality_evolution_timeline (
    id integer NOT NULL,
    character_name character varying(50) NOT NULL,
    parameter_path character varying(200) NOT NULL,
    old_value text,
    new_value text NOT NULL,
    change_magnitude numeric(5,3),
    optimization_id character varying(100),
    change_timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    change_reason text
);


--
-- Name: TABLE personality_evolution_timeline; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.personality_evolution_timeline IS 'Sprint 4: Timeline of all personality parameter changes for analytics';


--
-- Name: personality_evolution_timeline_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.personality_evolution_timeline_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: personality_evolution_timeline_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.personality_evolution_timeline_id_seq OWNED BY public.personality_evolution_timeline.id;


--
-- Name: personality_optimization_attempts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.personality_optimization_attempts (
    id integer NOT NULL,
    optimization_id character varying(100) NOT NULL,
    character_name character varying(50) NOT NULL,
    optimization_approach character varying(20) NOT NULL,
    expected_improvement numeric(5,3) NOT NULL,
    implementation_complexity character varying(10) NOT NULL,
    parameter_count integer DEFAULT 0 NOT NULL,
    attempt_timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT personality_optimization_attemp_implementation_complexity_check CHECK (((implementation_complexity)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying])::text[]))),
    CONSTRAINT personality_optimization_attempts_expected_improvement_check CHECK (((expected_improvement >= (0)::numeric) AND (expected_improvement <= (1)::numeric))),
    CONSTRAINT personality_optimization_attempts_optimization_approach_check CHECK (((optimization_approach)::text = ANY ((ARRAY['conservative'::character varying, 'moderate'::character varying, 'aggressive'::character varying])::text[])))
);


--
-- Name: TABLE personality_optimization_attempts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.personality_optimization_attempts IS 'Sprint 4: Records all character optimization attempts with approach and expected improvements';


--
-- Name: personality_optimization_attempts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.personality_optimization_attempts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: personality_optimization_attempts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.personality_optimization_attempts_id_seq OWNED BY public.personality_optimization_attempts.id;


--
-- Name: personality_optimization_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.personality_optimization_results (
    id integer NOT NULL,
    optimization_id character varying(100) NOT NULL,
    character_name character varying(50) NOT NULL,
    success boolean DEFAULT false NOT NULL,
    performance_before numeric(5,3),
    performance_after numeric(5,3),
    actual_improvement numeric(6,3),
    rollback_applied boolean DEFAULT false NOT NULL,
    issues_encountered jsonb DEFAULT '[]'::jsonb,
    completion_timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE personality_optimization_results; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.personality_optimization_results IS 'Sprint 4: Records outcomes of optimization attempts with performance metrics';


--
-- Name: personality_optimization_results_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.personality_optimization_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: personality_optimization_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.personality_optimization_results_id_seq OWNED BY public.personality_optimization_results.id;


--
-- Name: personality_optimization_summary; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.personality_optimization_summary AS
 SELECT poa.character_name,
    count(*) AS total_attempts,
    count(
        CASE
            WHEN (por.success = true) THEN 1
            ELSE NULL::integer
        END) AS successful_attempts,
    round((((count(
        CASE
            WHEN (por.success = true) THEN 1
            ELSE NULL::integer
        END))::numeric / (count(*))::numeric) * (100)::numeric), 1) AS success_rate_percent,
    avg(
        CASE
            WHEN (por.success = true) THEN por.actual_improvement
            ELSE NULL::numeric
        END) AS avg_successful_improvement,
    max(por.actual_improvement) AS best_improvement,
    min(por.actual_improvement) AS worst_result,
    count(
        CASE
            WHEN (por.rollback_applied = true) THEN 1
            ELSE NULL::integer
        END) AS rollback_count,
    max(por.completion_timestamp) AS last_optimization
   FROM (public.personality_optimization_attempts poa
     LEFT JOIN public.personality_optimization_results por ON (((poa.optimization_id)::text = (por.optimization_id)::text)))
  GROUP BY poa.character_name
  ORDER BY (round((((count(
        CASE
            WHEN (por.success = true) THEN 1
            ELSE NULL::integer
        END))::numeric / (count(*))::numeric) * (100)::numeric), 1)) DESC, (count(*)) DESC;


--
-- Name: VIEW personality_optimization_summary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.personality_optimization_summary IS 'Sprint 4: Character optimization success rates and performance overview';


--
-- Name: personality_parameter_adjustments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.personality_parameter_adjustments (
    id integer NOT NULL,
    optimization_id character varying(100) NOT NULL,
    adjustment_order integer NOT NULL,
    parameter_path character varying(200) NOT NULL,
    current_value text NOT NULL,
    target_value text NOT NULL,
    adjustment_reason text NOT NULL,
    expected_improvement numeric(5,3) NOT NULL,
    risk_level character varying(10) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT personality_parameter_adjustments_expected_improvement_check CHECK (((expected_improvement >= (0)::numeric) AND (expected_improvement <= (1)::numeric))),
    CONSTRAINT personality_parameter_adjustments_risk_level_check CHECK (((risk_level)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying])::text[])))
);


--
-- Name: TABLE personality_parameter_adjustments; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.personality_parameter_adjustments IS 'Sprint 4: Tracks specific parameter changes for each optimization attempt';


--
-- Name: personality_parameter_adjustments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.personality_parameter_adjustments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: personality_parameter_adjustments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.personality_parameter_adjustments_id_seq OWNED BY public.personality_parameter_adjustments.id;


--
-- Name: personality_parameter_change_history; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.personality_parameter_change_history AS
 SELECT pet.character_name,
    pet.parameter_path,
    pet.old_value,
    pet.new_value,
    pet.change_magnitude,
    pet.change_timestamp,
    pet.change_reason,
    poa.optimization_approach,
    por.success AS optimization_success,
    por.actual_improvement
   FROM ((public.personality_evolution_timeline pet
     LEFT JOIN public.personality_optimization_attempts poa ON (((pet.optimization_id)::text = (poa.optimization_id)::text)))
     LEFT JOIN public.personality_optimization_results por ON (((pet.optimization_id)::text = (por.optimization_id)::text)))
  ORDER BY pet.character_name, pet.parameter_path, pet.change_timestamp;


--
-- Name: VIEW personality_parameter_change_history; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.personality_parameter_change_history IS 'Sprint 4: Complete parameter evolution history with optimization context';


--
-- Name: personality_traits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.personality_traits (
    id integer NOT NULL,
    character_id integer,
    trait_name character varying(200) NOT NULL,
    trait_value numeric(3,2),
    intensity character varying(100),
    description text
);


--
-- Name: TABLE personality_traits; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.personality_traits IS 'Big Five personality traits used for character responses';


--
-- Name: personality_traits_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.personality_traits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: personality_traits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.personality_traits_id_seq OWNED BY public.personality_traits.id;


--
-- Name: platform_identities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.platform_identities (
    id integer NOT NULL,
    universal_id character varying(255) NOT NULL,
    platform character varying(50) NOT NULL,
    platform_user_id character varying(255) NOT NULL,
    username character varying(255) NOT NULL,
    display_name character varying(255),
    email character varying(255),
    verified_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: platform_identities_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.platform_identities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: platform_identities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.platform_identities_id_seq OWNED BY public.platform_identities.id;


--
-- Name: recent_personality_changes; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.recent_personality_changes AS
 SELECT pet.character_name,
    pet.parameter_path,
    pet.old_value,
    pet.new_value,
    pet.change_magnitude,
    pet.change_timestamp,
        CASE
            WHEN (pet.optimization_id IS NOT NULL) THEN 'Automated Optimization'::text
            ELSE 'Manual Change'::text
        END AS change_type,
    por.success AS optimization_success,
    poa.optimization_approach
   FROM ((public.personality_evolution_timeline pet
     LEFT JOIN public.personality_optimization_attempts poa ON (((pet.optimization_id)::text = (poa.optimization_id)::text)))
     LEFT JOIN public.personality_optimization_results por ON (((pet.optimization_id)::text = (por.optimization_id)::text)))
  WHERE (pet.change_timestamp >= (now() - '30 days'::interval))
  ORDER BY pet.change_timestamp DESC;


--
-- Name: VIEW recent_personality_changes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON VIEW public.recent_personality_changes IS 'Sprint 4: Recent personality changes for monitoring and dashboard';


--
-- Name: relationship_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.relationship_events (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    bot_name character varying(100) NOT NULL,
    event_type character varying(50) NOT NULL,
    trust_delta numeric(5,4),
    affection_delta numeric(5,4),
    attunement_delta numeric(5,4),
    trust_value numeric(5,4),
    affection_value numeric(5,4),
    attunement_value numeric(5,4),
    conversation_quality character varying(20),
    emotion_variance numeric(5,4),
    update_reason text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: relationship_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.relationship_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: relationship_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.relationship_events_id_seq OWNED BY public.relationship_events.id;


--
-- Name: relationship_scores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.relationship_scores (
    user_id character varying(255) NOT NULL,
    bot_name character varying(100) NOT NULL,
    trust numeric(5,4) DEFAULT 0.5000 NOT NULL,
    affection numeric(5,4) DEFAULT 0.4000 NOT NULL,
    attunement numeric(5,4) DEFAULT 0.3000 NOT NULL,
    interaction_count integer DEFAULT 0 NOT NULL,
    last_updated timestamp without time zone DEFAULT now() NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT relationship_scores_affection_check CHECK (((affection >= 0.0) AND (affection <= 1.0))),
    CONSTRAINT relationship_scores_attunement_check CHECK (((attunement >= 0.0) AND (attunement <= 1.0))),
    CONSTRAINT relationship_scores_interaction_count_check CHECK ((interaction_count >= 0)),
    CONSTRAINT relationship_scores_trust_check CHECK (((trust >= 0.0) AND (trust <= 1.0)))
);


--
-- Name: relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.relationships (
    id integer NOT NULL,
    user_id text NOT NULL,
    relationship_type text NOT NULL,
    strength real DEFAULT 0.5,
    last_interaction timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    interaction_count integer DEFAULT 0,
    notes text
);


--
-- Name: relationships_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.relationships_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: relationships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.relationships_id_seq OWNED BY public.relationships.id;


--
-- Name: role_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_transactions (
    id integer NOT NULL,
    transaction_id text NOT NULL,
    user_id text NOT NULL,
    bot_name text NOT NULL,
    transaction_type text NOT NULL,
    state text DEFAULT 'pending'::text,
    context jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: role_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.role_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: role_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.role_transactions_id_seq OWNED BY public.role_transactions.id;


--
-- Name: roleplay_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roleplay_transactions (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    bot_name character varying(50) NOT NULL,
    transaction_type character varying(50) NOT NULL,
    state character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    context jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    completed_at timestamp without time zone
);


--
-- Name: roleplay_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roleplay_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roleplay_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roleplay_transactions_id_seq OWNED BY public.roleplay_transactions.id;


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    migration_name character varying(255) NOT NULL,
    applied_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: schema_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_versions (
    id integer NOT NULL,
    version character varying(50) NOT NULL,
    description text,
    applied_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: schema_versions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.schema_versions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: schema_versions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.schema_versions_id_seq OWNED BY public.schema_versions.id;


--
-- Name: system_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_settings (
    key text NOT NULL,
    value text NOT NULL,
    description text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: trust_recovery_state; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trust_recovery_state (
    user_id character varying(255) NOT NULL,
    bot_name character varying(100) NOT NULL,
    recovery_stage character varying(20) NOT NULL,
    initial_trust numeric(5,4) NOT NULL,
    current_trust numeric(5,4) NOT NULL,
    target_trust numeric(5,4) NOT NULL,
    progress_percentage numeric(5,2) DEFAULT 0.00 NOT NULL,
    recovery_actions_taken text[],
    started_at timestamp without time zone NOT NULL,
    last_updated timestamp without time zone DEFAULT now() NOT NULL,
    estimated_completion timestamp without time zone,
    CONSTRAINT trust_recovery_state_current_trust_check CHECK (((current_trust >= 0.0) AND (current_trust <= 1.0))),
    CONSTRAINT trust_recovery_state_initial_trust_check CHECK (((initial_trust >= 0.0) AND (initial_trust <= 1.0))),
    CONSTRAINT trust_recovery_state_progress_percentage_check CHECK (((progress_percentage >= 0.0) AND (progress_percentage <= 100.0))),
    CONSTRAINT trust_recovery_state_target_trust_check CHECK (((target_trust >= 0.0) AND (target_trust <= 1.0)))
);


--
-- Name: universal_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.universal_users (
    universal_id character varying(255) NOT NULL,
    primary_username character varying(255) NOT NULL,
    display_name character varying(255),
    email character varying(255),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_active timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    preferences text DEFAULT '{}'::text,
    privacy_settings text DEFAULT '{}'::text
);


--
-- Name: user_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_events (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    bot_name character varying(100) NOT NULL,
    event_type character varying(100) NOT NULL,
    event_data jsonb NOT NULL,
    location_context character varying(255),
    timestamp_utc timestamp without time zone DEFAULT now(),
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: user_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_events_id_seq OWNED BY public.user_events.id;


--
-- Name: user_fact_relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_fact_relationships (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id character varying(255) NOT NULL,
    entity_id uuid NOT NULL,
    relationship_type text NOT NULL,
    confidence double precision DEFAULT 0.5,
    strength double precision DEFAULT 0.5,
    emotional_context text,
    context_metadata jsonb DEFAULT '{}'::jsonb,
    source_conversation_id text,
    mentioned_by_character text,
    source_platform text DEFAULT 'discord'::text,
    related_entities jsonb DEFAULT '[]'::jsonb,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT user_fact_relationships_confidence_check CHECK (((confidence >= (0)::double precision) AND (confidence <= (1)::double precision))),
    CONSTRAINT user_fact_relationships_relationship_type_check CHECK (((length(relationship_type) > 0) AND (length(relationship_type) <= 50))),
    CONSTRAINT user_fact_relationships_strength_check CHECK (((strength >= (0)::double precision) AND (strength <= (1)::double precision)))
);


--
-- Name: TABLE user_fact_relationships; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.user_fact_relationships IS 'Knowledge graph relationships between users and entities';


--
-- Name: COLUMN user_fact_relationships.relationship_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fact_relationships.relationship_type IS 'Flexible relationship type field (e.g., likes, dislikes, enjoys, knows, visited, wants, owns, prefers, interested_in, loves, etc.)';


--
-- Name: COLUMN user_fact_relationships.confidence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fact_relationships.confidence IS 'Confidence score 0-1 based on frequency and recency';


--
-- Name: COLUMN user_fact_relationships.mentioned_by_character; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fact_relationships.mentioned_by_character IS 'Character who learned this fact for character-aware responses';


--
-- Name: COLUMN user_fact_relationships.related_entities; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fact_relationships.related_entities IS 'JSONB array of related entity connections';


--
-- Name: user_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_preferences (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    bot_name character varying(100) NOT NULL,
    preference_type character varying(100) NOT NULL,
    preference_value character varying(500) NOT NULL,
    confidence double precision DEFAULT 1.0,
    context jsonb,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: user_preferences_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_preferences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_preferences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_preferences_id_seq OWNED BY public.user_preferences.id;


--
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_profiles (
    user_id character varying(255) NOT NULL,
    name character varying(255),
    relationship_level integer DEFAULT 1,
    current_emotion character varying(50) DEFAULT 'neutral'::character varying,
    interaction_count integer DEFAULT 0,
    first_interaction timestamp without time zone,
    last_interaction timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    emotion_history jsonb DEFAULT '[]'::jsonb,
    escalation_count integer DEFAULT 0,
    trust_indicators jsonb DEFAULT '[]'::jsonb,
    preferences jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    user_id text NOT NULL,
    username text NOT NULL,
    display_name text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_seen timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    message_count integer DEFAULT 0,
    preferences text DEFAULT '{}'::text,
    privacy_settings text DEFAULT '{}'::text
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: banned_users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.banned_users ALTER COLUMN id SET DEFAULT nextval('public.banned_users_id_seq'::regclass);


--
-- Name: character_abilities id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_abilities ALTER COLUMN id SET DEFAULT nextval('public.character_abilities_id_seq'::regclass);


--
-- Name: character_ai_scenarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_ai_scenarios ALTER COLUMN id SET DEFAULT nextval('public.character_ai_scenarios_id_seq'::regclass);


--
-- Name: character_appearance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_appearance ALTER COLUMN id SET DEFAULT nextval('public.character_appearance_id_seq'::regclass);


--
-- Name: character_attributes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_attributes ALTER COLUMN id SET DEFAULT nextval('public.character_attributes_id_seq'::regclass);


--
-- Name: character_background id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_background ALTER COLUMN id SET DEFAULT nextval('public.character_background_id_seq'::regclass);


--
-- Name: character_behavioral_triggers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_behavioral_triggers ALTER COLUMN id SET DEFAULT nextval('public.character_behavioral_triggers_id_seq'::regclass);


--
-- Name: character_communication_patterns id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_communication_patterns ALTER COLUMN id SET DEFAULT nextval('public.character_communication_patterns_id_seq'::regclass);


--
-- Name: character_context_guidance id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_context_guidance ALTER COLUMN id SET DEFAULT nextval('public.character_context_guidance_id_seq'::regclass);


--
-- Name: character_conversation_contexts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_conversation_contexts ALTER COLUMN id SET DEFAULT nextval('public.character_conversation_contexts_id_seq'::regclass);


--
-- Name: character_conversation_directives id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_conversation_directives ALTER COLUMN id SET DEFAULT nextval('public.character_conversation_directives_id_seq'::regclass);


--
-- Name: character_conversation_flows id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_conversation_flows ALTER COLUMN id SET DEFAULT nextval('public.character_conversation_flows_id_seq'::regclass);


--
-- Name: character_cultural_expressions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_cultural_expressions ALTER COLUMN id SET DEFAULT nextval('public.character_cultural_expressions_id_seq'::regclass);


--
-- Name: character_current_context id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_current_context ALTER COLUMN id SET DEFAULT nextval('public.character_current_context_id_seq'::regclass);


--
-- Name: character_current_goals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_current_goals ALTER COLUMN id SET DEFAULT nextval('public.character_current_goals_id_seq'::regclass);


--
-- Name: character_directives id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_directives ALTER COLUMN id SET DEFAULT nextval('public.character_directives_id_seq'::regclass);


--
-- Name: character_emoji_patterns id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emoji_patterns ALTER COLUMN id SET DEFAULT nextval('public.character_emoji_patterns_id_seq'::regclass);


--
-- Name: character_emotion_profile id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotion_profile ALTER COLUMN id SET DEFAULT nextval('public.character_emotion_profile_id_seq'::regclass);


--
-- Name: character_emotion_range id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotion_range ALTER COLUMN id SET DEFAULT nextval('public.character_emotion_range_id_seq'::regclass);


--
-- Name: character_emotional_triggers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotional_triggers ALTER COLUMN id SET DEFAULT nextval('public.character_emotional_triggers_id_seq'::regclass);


--
-- Name: character_emotional_triggers_v2 id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotional_triggers_v2 ALTER COLUMN id SET DEFAULT nextval('public.character_emotional_triggers_v2_id_seq'::regclass);


--
-- Name: character_essence id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_essence ALTER COLUMN id SET DEFAULT nextval('public.character_essence_id_seq'::regclass);


--
-- Name: character_expertise_domains id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_expertise_domains ALTER COLUMN id SET DEFAULT nextval('public.character_expertise_domains_id_seq'::regclass);


--
-- Name: character_identity_details id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_identity_details ALTER COLUMN id SET DEFAULT nextval('public.character_identity_details_id_seq'::regclass);


--
-- Name: character_instructions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_instructions ALTER COLUMN id SET DEFAULT nextval('public.character_instructions_id_seq'::regclass);


--
-- Name: character_interests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_interests ALTER COLUMN id SET DEFAULT nextval('public.character_interests_id_seq'::regclass);


--
-- Name: character_memories id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_memories ALTER COLUMN id SET DEFAULT nextval('public.character_memories_id_seq'::regclass);


--
-- Name: character_message_triggers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_message_triggers ALTER COLUMN id SET DEFAULT nextval('public.character_message_triggers_id_seq'::regclass);


--
-- Name: character_metadata id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_metadata ALTER COLUMN id SET DEFAULT nextval('public.character_metadata_id_seq'::regclass);


--
-- Name: character_relationships id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_relationships ALTER COLUMN id SET DEFAULT nextval('public.character_relationships_id_seq'::regclass);


--
-- Name: character_response_guidelines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_response_guidelines ALTER COLUMN id SET DEFAULT nextval('public.character_response_guidelines_id_seq'::regclass);


--
-- Name: character_response_modes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_response_modes ALTER COLUMN id SET DEFAULT nextval('public.character_response_modes_id_seq'::regclass);


--
-- Name: character_roleplay_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_roleplay_config ALTER COLUMN id SET DEFAULT nextval('public.character_roleplay_config_id_seq'::regclass);


--
-- Name: character_roleplay_scenarios_v2 id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_roleplay_scenarios_v2 ALTER COLUMN id SET DEFAULT nextval('public.character_roleplay_scenarios_v2_id_seq'::regclass);


--
-- Name: character_scenario_triggers_v2 id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_scenario_triggers_v2 ALTER COLUMN id SET DEFAULT nextval('public.character_scenario_triggers_v2_id_seq'::regclass);


--
-- Name: character_speech_patterns id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_speech_patterns ALTER COLUMN id SET DEFAULT nextval('public.character_speech_patterns_id_seq'::regclass);


--
-- Name: character_values id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_values ALTER COLUMN id SET DEFAULT nextval('public.character_values_id_seq'::regclass);


--
-- Name: character_vocabulary id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_vocabulary ALTER COLUMN id SET DEFAULT nextval('public.character_vocabulary_id_seq'::regclass);


--
-- Name: character_voice_profile id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_voice_profile ALTER COLUMN id SET DEFAULT nextval('public.character_voice_profile_id_seq'::regclass);


--
-- Name: character_voice_traits id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_voice_traits ALTER COLUMN id SET DEFAULT nextval('public.character_voice_traits_id_seq'::regclass);


--
-- Name: characters id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.characters ALTER COLUMN id SET DEFAULT nextval('public.characters_id_seq'::regclass);


--
-- Name: communication_styles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communication_styles ALTER COLUMN id SET DEFAULT nextval('public.communication_styles_id_seq'::regclass);


--
-- Name: conversations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations ALTER COLUMN id SET DEFAULT nextval('public.conversations_id_seq'::regclass);


--
-- Name: dynamic_conversation_analyses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dynamic_conversation_analyses ALTER COLUMN id SET DEFAULT nextval('public.dynamic_conversation_analyses_id_seq'::regclass);


--
-- Name: dynamic_personality_traits id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dynamic_personality_traits ALTER COLUMN id SET DEFAULT nextval('public.dynamic_personality_traits_id_seq'::regclass);


--
-- Name: emotions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emotions ALTER COLUMN id SET DEFAULT nextval('public.emotions_id_seq'::regclass);


--
-- Name: facts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facts ALTER COLUMN id SET DEFAULT nextval('public.facts_id_seq'::regclass);


--
-- Name: memory_entries id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.memory_entries ALTER COLUMN id SET DEFAULT nextval('public.memory_entries_id_seq'::regclass);


--
-- Name: performance_metrics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_metrics ALTER COLUMN id SET DEFAULT nextval('public.performance_metrics_id_seq'::regclass);


--
-- Name: personality_evolution_timeline id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_evolution_timeline ALTER COLUMN id SET DEFAULT nextval('public.personality_evolution_timeline_id_seq'::regclass);


--
-- Name: personality_optimization_attempts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_optimization_attempts ALTER COLUMN id SET DEFAULT nextval('public.personality_optimization_attempts_id_seq'::regclass);


--
-- Name: personality_optimization_results id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_optimization_results ALTER COLUMN id SET DEFAULT nextval('public.personality_optimization_results_id_seq'::regclass);


--
-- Name: personality_parameter_adjustments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_parameter_adjustments ALTER COLUMN id SET DEFAULT nextval('public.personality_parameter_adjustments_id_seq'::regclass);


--
-- Name: personality_traits id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_traits ALTER COLUMN id SET DEFAULT nextval('public.personality_traits_id_seq'::regclass);


--
-- Name: platform_identities id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_identities ALTER COLUMN id SET DEFAULT nextval('public.platform_identities_id_seq'::regclass);


--
-- Name: relationship_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationship_events ALTER COLUMN id SET DEFAULT nextval('public.relationship_events_id_seq'::regclass);


--
-- Name: relationships id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationships ALTER COLUMN id SET DEFAULT nextval('public.relationships_id_seq'::regclass);


--
-- Name: role_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_transactions ALTER COLUMN id SET DEFAULT nextval('public.role_transactions_id_seq'::regclass);


--
-- Name: roleplay_transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roleplay_transactions ALTER COLUMN id SET DEFAULT nextval('public.roleplay_transactions_id_seq'::regclass);


--
-- Name: schema_versions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_versions ALTER COLUMN id SET DEFAULT nextval('public.schema_versions_id_seq'::regclass);


--
-- Name: user_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_events ALTER COLUMN id SET DEFAULT nextval('public.user_events_id_seq'::regclass);


--
-- Name: user_preferences id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences ALTER COLUMN id SET DEFAULT nextval('public.user_preferences_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: banned_users banned_users_discord_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.banned_users
    ADD CONSTRAINT banned_users_discord_user_id_key UNIQUE (discord_user_id);


--
-- Name: banned_users banned_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.banned_users
    ADD CONSTRAINT banned_users_pkey PRIMARY KEY (id);


--
-- Name: character_abilities character_abilities_character_id_category_ability_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_abilities
    ADD CONSTRAINT character_abilities_character_id_category_ability_name_key UNIQUE (character_id, category, ability_name);


--
-- Name: character_abilities character_abilities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_abilities
    ADD CONSTRAINT character_abilities_pkey PRIMARY KEY (id);


--
-- Name: character_ai_scenarios character_ai_scenarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_ai_scenarios
    ADD CONSTRAINT character_ai_scenarios_pkey PRIMARY KEY (id);


--
-- Name: character_appearance character_appearance_character_id_category_attribute_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_appearance
    ADD CONSTRAINT character_appearance_character_id_category_attribute_key UNIQUE (character_id, category, attribute);


--
-- Name: character_appearance character_appearance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_appearance
    ADD CONSTRAINT character_appearance_pkey PRIMARY KEY (id);


--
-- Name: character_attributes character_attributes_character_id_category_display_order_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_attributes
    ADD CONSTRAINT character_attributes_character_id_category_display_order_key UNIQUE (character_id, category, display_order);


--
-- Name: character_attributes character_attributes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_attributes
    ADD CONSTRAINT character_attributes_pkey PRIMARY KEY (id);


--
-- Name: character_background character_background_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_background
    ADD CONSTRAINT character_background_pkey PRIMARY KEY (id);


--
-- Name: character_behavioral_triggers character_behavioral_triggers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_behavioral_triggers
    ADD CONSTRAINT character_behavioral_triggers_pkey PRIMARY KEY (id);


--
-- Name: character_communication_patterns character_communication_patte_character_id_pattern_type_pat_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_communication_patterns
    ADD CONSTRAINT character_communication_patte_character_id_pattern_type_pat_key UNIQUE (character_id, pattern_type, pattern_name);


--
-- Name: character_communication_patterns character_communication_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_communication_patterns
    ADD CONSTRAINT character_communication_patterns_pkey PRIMARY KEY (id);


--
-- Name: character_context_guidance character_context_guidance_context_id_guidance_type_display_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_context_guidance
    ADD CONSTRAINT character_context_guidance_context_id_guidance_type_display_key UNIQUE (context_id, guidance_type, display_order);


--
-- Name: character_context_guidance character_context_guidance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_context_guidance
    ADD CONSTRAINT character_context_guidance_pkey PRIMARY KEY (id);


--
-- Name: character_conversation_contexts character_conversation_contexts_character_id_context_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_conversation_contexts
    ADD CONSTRAINT character_conversation_contexts_character_id_context_name_key UNIQUE (character_id, context_name);


--
-- Name: character_conversation_contexts character_conversation_contexts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_conversation_contexts
    ADD CONSTRAINT character_conversation_contexts_pkey PRIMARY KEY (id);


--
-- Name: character_conversation_directives character_conversation_directives_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_conversation_directives
    ADD CONSTRAINT character_conversation_directives_pkey PRIMARY KEY (id);


--
-- Name: character_conversation_flows character_conversation_flows_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_conversation_flows
    ADD CONSTRAINT character_conversation_flows_pkey PRIMARY KEY (id);


--
-- Name: character_cultural_expressions character_cultural_expressions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_cultural_expressions
    ADD CONSTRAINT character_cultural_expressions_pkey PRIMARY KEY (id);


--
-- Name: character_current_context character_current_context_character_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_current_context
    ADD CONSTRAINT character_current_context_character_id_key UNIQUE (character_id);


--
-- Name: character_current_context character_current_context_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_current_context
    ADD CONSTRAINT character_current_context_pkey PRIMARY KEY (id);


--
-- Name: character_current_goals character_current_goals_character_id_display_order_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_current_goals
    ADD CONSTRAINT character_current_goals_character_id_display_order_key UNIQUE (character_id, display_order);


--
-- Name: character_current_goals character_current_goals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_current_goals
    ADD CONSTRAINT character_current_goals_pkey PRIMARY KEY (id);


--
-- Name: character_directives character_directives_character_id_directive_type_display_or_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_directives
    ADD CONSTRAINT character_directives_character_id_directive_type_display_or_key UNIQUE (character_id, directive_type, display_order);


--
-- Name: character_directives character_directives_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_directives
    ADD CONSTRAINT character_directives_pkey PRIMARY KEY (id);


--
-- Name: character_emoji_patterns character_emoji_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emoji_patterns
    ADD CONSTRAINT character_emoji_patterns_pkey PRIMARY KEY (id);


--
-- Name: character_emotion_profile character_emotion_profile_character_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotion_profile
    ADD CONSTRAINT character_emotion_profile_character_id_key UNIQUE (character_id);


--
-- Name: character_emotion_profile character_emotion_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotion_profile
    ADD CONSTRAINT character_emotion_profile_pkey PRIMARY KEY (id);


--
-- Name: character_emotion_range character_emotion_range_character_id_emotion_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotion_range
    ADD CONSTRAINT character_emotion_range_character_id_emotion_name_key UNIQUE (character_id, emotion_name);


--
-- Name: character_emotion_range character_emotion_range_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotion_range
    ADD CONSTRAINT character_emotion_range_pkey PRIMARY KEY (id);


--
-- Name: character_emotional_triggers_v2 character_emotional_triggers__character_id_trigger_text_val_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotional_triggers_v2
    ADD CONSTRAINT character_emotional_triggers__character_id_trigger_text_val_key UNIQUE (character_id, trigger_text, valence);


--
-- Name: character_emotional_triggers character_emotional_triggers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotional_triggers
    ADD CONSTRAINT character_emotional_triggers_pkey PRIMARY KEY (id);


--
-- Name: character_emotional_triggers_v2 character_emotional_triggers_v2_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotional_triggers_v2
    ADD CONSTRAINT character_emotional_triggers_v2_pkey PRIMARY KEY (id);


--
-- Name: character_essence character_essence_character_id_essence_type_essence_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_essence
    ADD CONSTRAINT character_essence_character_id_essence_type_essence_name_key UNIQUE (character_id, essence_type, essence_name);


--
-- Name: character_essence character_essence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_essence
    ADD CONSTRAINT character_essence_pkey PRIMARY KEY (id);


--
-- Name: character_expertise_domains character_expertise_domains_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_expertise_domains
    ADD CONSTRAINT character_expertise_domains_pkey PRIMARY KEY (id);


--
-- Name: character_identity_details character_identity_details_character_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_identity_details
    ADD CONSTRAINT character_identity_details_character_id_key UNIQUE (character_id);


--
-- Name: character_identity_details character_identity_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_identity_details
    ADD CONSTRAINT character_identity_details_pkey PRIMARY KEY (id);


--
-- Name: character_instructions character_instructions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_instructions
    ADD CONSTRAINT character_instructions_pkey PRIMARY KEY (id);


--
-- Name: character_interests character_interests_character_id_category_display_order_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_interests
    ADD CONSTRAINT character_interests_character_id_category_display_order_key UNIQUE (character_id, category, display_order);


--
-- Name: character_interests character_interests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_interests
    ADD CONSTRAINT character_interests_pkey PRIMARY KEY (id);


--
-- Name: character_memories character_memories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_memories
    ADD CONSTRAINT character_memories_pkey PRIMARY KEY (id);


--
-- Name: character_message_triggers character_message_triggers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_message_triggers
    ADD CONSTRAINT character_message_triggers_pkey PRIMARY KEY (id);


--
-- Name: character_metadata character_metadata_character_id_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_metadata
    ADD CONSTRAINT character_metadata_character_id_version_key UNIQUE (character_id, version);


--
-- Name: character_metadata character_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_metadata
    ADD CONSTRAINT character_metadata_pkey PRIMARY KEY (id);


--
-- Name: character_relationships character_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_relationships
    ADD CONSTRAINT character_relationships_pkey PRIMARY KEY (id);


--
-- Name: character_response_guidelines character_response_guidelines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_response_guidelines
    ADD CONSTRAINT character_response_guidelines_pkey PRIMARY KEY (id);


--
-- Name: character_response_modes character_response_modes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_response_modes
    ADD CONSTRAINT character_response_modes_pkey PRIMARY KEY (id);


--
-- Name: character_roleplay_config character_roleplay_config_character_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_roleplay_config
    ADD CONSTRAINT character_roleplay_config_character_id_key UNIQUE (character_id);


--
-- Name: character_roleplay_config character_roleplay_config_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_roleplay_config
    ADD CONSTRAINT character_roleplay_config_pkey PRIMARY KEY (id);


--
-- Name: character_roleplay_scenarios_v2 character_roleplay_scenarios_v2_character_id_scenario_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_roleplay_scenarios_v2
    ADD CONSTRAINT character_roleplay_scenarios_v2_character_id_scenario_name_key UNIQUE (character_id, scenario_name);


--
-- Name: character_roleplay_scenarios_v2 character_roleplay_scenarios_v2_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_roleplay_scenarios_v2
    ADD CONSTRAINT character_roleplay_scenarios_v2_pkey PRIMARY KEY (id);


--
-- Name: character_scenario_triggers_v2 character_scenario_triggers_v2_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_scenario_triggers_v2
    ADD CONSTRAINT character_scenario_triggers_v2_pkey PRIMARY KEY (id);


--
-- Name: character_scenario_triggers_v2 character_scenario_triggers_v2_scenario_id_trigger_phrase_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_scenario_triggers_v2
    ADD CONSTRAINT character_scenario_triggers_v2_scenario_id_trigger_phrase_key UNIQUE (scenario_id, trigger_phrase);


--
-- Name: character_speech_patterns character_speech_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_speech_patterns
    ADD CONSTRAINT character_speech_patterns_pkey PRIMARY KEY (id);


--
-- Name: character_values character_values_character_id_value_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_values
    ADD CONSTRAINT character_values_character_id_value_key_key UNIQUE (character_id, value_key);


--
-- Name: character_values character_values_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_values
    ADD CONSTRAINT character_values_pkey PRIMARY KEY (id);


--
-- Name: character_vocabulary character_vocabulary_character_id_word_or_phrase_preference_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_vocabulary
    ADD CONSTRAINT character_vocabulary_character_id_word_or_phrase_preference_key UNIQUE (character_id, word_or_phrase, preference);


--
-- Name: character_vocabulary character_vocabulary_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_vocabulary
    ADD CONSTRAINT character_vocabulary_pkey PRIMARY KEY (id);


--
-- Name: character_voice_profile character_voice_profile_character_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_voice_profile
    ADD CONSTRAINT character_voice_profile_character_id_key UNIQUE (character_id);


--
-- Name: character_voice_profile character_voice_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_voice_profile
    ADD CONSTRAINT character_voice_profile_pkey PRIMARY KEY (id);


--
-- Name: character_voice_traits character_voice_traits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_voice_traits
    ADD CONSTRAINT character_voice_traits_pkey PRIMARY KEY (id);


--
-- Name: characters characters_normalized_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.characters
    ADD CONSTRAINT characters_normalized_name_key UNIQUE (normalized_name);


--
-- Name: characters characters_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.characters
    ADD CONSTRAINT characters_pkey PRIMARY KEY (id);


--
-- Name: communication_styles communication_styles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communication_styles
    ADD CONSTRAINT communication_styles_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: dynamic_conversation_analyses dynamic_conversation_analyses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dynamic_conversation_analyses
    ADD CONSTRAINT dynamic_conversation_analyses_pkey PRIMARY KEY (id);


--
-- Name: dynamic_personality_profiles dynamic_personality_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dynamic_personality_profiles
    ADD CONSTRAINT dynamic_personality_profiles_pkey PRIMARY KEY (user_id);


--
-- Name: dynamic_personality_traits dynamic_personality_traits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dynamic_personality_traits
    ADD CONSTRAINT dynamic_personality_traits_pkey PRIMARY KEY (id);


--
-- Name: emotions emotions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emotions
    ADD CONSTRAINT emotions_pkey PRIMARY KEY (id);


--
-- Name: entity_relationships entity_relationships_from_entity_id_to_entity_id_relationsh_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_from_entity_id_to_entity_id_relationsh_key UNIQUE (from_entity_id, to_entity_id, relationship_type);


--
-- Name: entity_relationships entity_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_pkey PRIMARY KEY (id);


--
-- Name: fact_entities fact_entities_entity_type_entity_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_entities
    ADD CONSTRAINT fact_entities_entity_type_entity_name_key UNIQUE (entity_type, entity_name);


--
-- Name: fact_entities fact_entities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_entities
    ADD CONSTRAINT fact_entities_pkey PRIMARY KEY (id);


--
-- Name: facts facts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facts
    ADD CONSTRAINT facts_pkey PRIMARY KEY (id);


--
-- Name: memory_entries memory_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.memory_entries
    ADD CONSTRAINT memory_entries_pkey PRIMARY KEY (id);


--
-- Name: performance_metrics performance_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.performance_metrics
    ADD CONSTRAINT performance_metrics_pkey PRIMARY KEY (id);


--
-- Name: personality_evolution_timeline personality_evolution_timeline_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_evolution_timeline
    ADD CONSTRAINT personality_evolution_timeline_pkey PRIMARY KEY (id);


--
-- Name: personality_optimization_attempts personality_optimization_attempts_optimization_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_optimization_attempts
    ADD CONSTRAINT personality_optimization_attempts_optimization_id_key UNIQUE (optimization_id);


--
-- Name: personality_optimization_attempts personality_optimization_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_optimization_attempts
    ADD CONSTRAINT personality_optimization_attempts_pkey PRIMARY KEY (id);


--
-- Name: personality_optimization_results personality_optimization_results_optimization_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_optimization_results
    ADD CONSTRAINT personality_optimization_results_optimization_id_key UNIQUE (optimization_id);


--
-- Name: personality_optimization_results personality_optimization_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_optimization_results
    ADD CONSTRAINT personality_optimization_results_pkey PRIMARY KEY (id);


--
-- Name: personality_parameter_adjustments personality_parameter_adjustments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_parameter_adjustments
    ADD CONSTRAINT personality_parameter_adjustments_pkey PRIMARY KEY (id);


--
-- Name: personality_traits personality_traits_character_id_trait_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_traits
    ADD CONSTRAINT personality_traits_character_id_trait_name_key UNIQUE (character_id, trait_name);


--
-- Name: personality_traits personality_traits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_traits
    ADD CONSTRAINT personality_traits_pkey PRIMARY KEY (id);


--
-- Name: platform_identities platform_identities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_identities
    ADD CONSTRAINT platform_identities_pkey PRIMARY KEY (id);


--
-- Name: platform_identities platform_identities_platform_platform_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_identities
    ADD CONSTRAINT platform_identities_platform_platform_user_id_key UNIQUE (platform, platform_user_id);


--
-- Name: relationship_events relationship_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationship_events
    ADD CONSTRAINT relationship_events_pkey PRIMARY KEY (id);


--
-- Name: relationship_scores relationship_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationship_scores
    ADD CONSTRAINT relationship_scores_pkey PRIMARY KEY (user_id, bot_name);


--
-- Name: relationships relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationships
    ADD CONSTRAINT relationships_pkey PRIMARY KEY (id);


--
-- Name: role_transactions role_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_transactions
    ADD CONSTRAINT role_transactions_pkey PRIMARY KEY (id);


--
-- Name: role_transactions role_transactions_transaction_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_transactions
    ADD CONSTRAINT role_transactions_transaction_id_key UNIQUE (transaction_id);


--
-- Name: roleplay_transactions roleplay_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roleplay_transactions
    ADD CONSTRAINT roleplay_transactions_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (migration_name);


--
-- Name: schema_versions schema_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_versions
    ADD CONSTRAINT schema_versions_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (key);


--
-- Name: trust_recovery_state trust_recovery_state_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trust_recovery_state
    ADD CONSTRAINT trust_recovery_state_pkey PRIMARY KEY (user_id, bot_name, started_at);


--
-- Name: universal_users universal_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.universal_users
    ADD CONSTRAINT universal_users_pkey PRIMARY KEY (universal_id);


--
-- Name: user_events user_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_events
    ADD CONSTRAINT user_events_pkey PRIMARY KEY (id);


--
-- Name: user_fact_relationships user_fact_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_fact_relationships
    ADD CONSTRAINT user_fact_relationships_pkey PRIMARY KEY (id);


--
-- Name: user_fact_relationships user_fact_relationships_user_id_entity_id_relationship_type_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_fact_relationships
    ADD CONSTRAINT user_fact_relationships_user_id_entity_id_relationship_type_key UNIQUE (user_id, entity_id, relationship_type);


--
-- Name: user_preferences user_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_pkey PRIMARY KEY (id);


--
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_user_id_key UNIQUE (user_id);


--
-- Name: idx_ai_scenarios_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_scenarios_character ON public.character_ai_scenarios USING btree (character_id, scenario_type);


--
-- Name: idx_attributes_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attributes_active ON public.character_attributes USING btree (character_id, category) WHERE (active = true);


--
-- Name: idx_attributes_char_cat; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_attributes_char_cat ON public.character_attributes USING btree (character_id, category);


--
-- Name: idx_character_abilities_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_abilities_category ON public.character_abilities USING btree (character_id, category);


--
-- Name: idx_character_abilities_proficiency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_abilities_proficiency ON public.character_abilities USING btree (character_id, proficiency_level DESC);


--
-- Name: idx_character_appearance_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_appearance_category ON public.character_appearance USING btree (character_id, category);


--
-- Name: idx_character_background_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_background_category ON public.character_background USING btree (character_id, category);


--
-- Name: idx_character_background_category_importance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_background_category_importance ON public.character_background USING btree (character_id, category, importance_level DESC);


--
-- Name: idx_character_background_description_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_background_description_trgm ON public.character_background USING gin (description public.gin_trgm_ops);


--
-- Name: idx_character_background_importance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_background_importance ON public.character_background USING btree (character_id, importance_level DESC);


--
-- Name: idx_character_essence_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_essence_type ON public.character_essence USING btree (character_id, essence_type);


--
-- Name: idx_character_instructions_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_instructions_type ON public.character_instructions USING btree (character_id, instruction_type);


--
-- Name: idx_character_memories_emotional_impact; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_memories_emotional_impact ON public.character_memories USING btree (character_id, emotional_impact DESC);


--
-- Name: idx_character_memories_importance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_memories_importance ON public.character_memories USING btree (character_id, importance_level DESC);


--
-- Name: idx_character_memories_trigger_importance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_memories_trigger_importance ON public.character_memories USING gin (character_id, triggers, importance_level);


--
-- Name: idx_character_memories_triggers_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_memories_triggers_gin ON public.character_memories USING gin (triggers);


--
-- Name: idx_character_memories_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_memories_type ON public.character_memories USING btree (character_id, memory_type);


--
-- Name: idx_character_patterns_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_patterns_type ON public.character_communication_patterns USING btree (character_id, pattern_type);


--
-- Name: idx_character_relationships_strength; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_relationships_strength ON public.character_relationships USING btree (character_id, relationship_strength DESC);


--
-- Name: idx_character_relationships_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_relationships_type ON public.character_relationships USING btree (character_id, relationship_type);


--
-- Name: idx_character_relationships_type_strength; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_relationships_type_strength ON public.character_relationships USING btree (character_id, relationship_type, relationship_strength DESC);


--
-- Name: idx_character_triggers_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_triggers_type ON public.character_behavioral_triggers USING btree (character_id, trigger_type);


--
-- Name: idx_character_values_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_character_values_character ON public.character_values USING btree (character_id);


--
-- Name: idx_characters_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_characters_active ON public.characters USING btree (is_active);


--
-- Name: idx_characters_active_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_characters_active_lookup ON public.characters USING btree (id) WHERE (is_active = true);


--
-- Name: idx_characters_name_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_characters_name_lookup ON public.characters USING btree (name);


--
-- Name: idx_characters_normalized_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_characters_normalized_name ON public.characters USING btree (normalized_name);


--
-- Name: idx_communication_styles_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_communication_styles_character ON public.communication_styles USING btree (character_id);


--
-- Name: idx_context_guidance_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_context_guidance_type ON public.character_context_guidance USING btree (context_id, guidance_type);


--
-- Name: idx_conv_contexts_char; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_contexts_char ON public.character_conversation_contexts USING btree (character_id);


--
-- Name: idx_conversation_flows_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversation_flows_character ON public.character_conversation_flows USING btree (character_id, flow_type);


--
-- Name: idx_cultural_expressions_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cultural_expressions_character ON public.character_cultural_expressions USING btree (character_id, expression_type);


--
-- Name: idx_current_goals_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_current_goals_active ON public.character_current_goals USING btree (character_id, status) WHERE ((status)::text = 'active'::text);


--
-- Name: idx_current_goals_char; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_current_goals_char ON public.character_current_goals USING btree (character_id);


--
-- Name: idx_directives_char_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_directives_char_type ON public.character_directives USING btree (character_id, directive_type);


--
-- Name: idx_directives_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_directives_priority ON public.character_directives USING btree (character_id, priority DESC) WHERE (active = true);


--
-- Name: idx_dynamic_conversation_analyses_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dynamic_conversation_analyses_timestamp ON public.dynamic_conversation_analyses USING btree ("timestamp");


--
-- Name: idx_dynamic_conversation_analyses_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dynamic_conversation_analyses_user_id ON public.dynamic_conversation_analyses USING btree (user_id);


--
-- Name: idx_dynamic_personality_traits_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dynamic_personality_traits_user_id ON public.dynamic_personality_traits USING btree (user_id);


--
-- Name: idx_emoji_patterns_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emoji_patterns_character ON public.character_emoji_patterns USING btree (character_id, pattern_category);


--
-- Name: idx_emotion_range_char; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emotion_range_char ON public.character_emotion_range USING btree (character_id);


--
-- Name: idx_emotional_triggers_char_val; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emotional_triggers_char_val ON public.character_emotional_triggers_v2 USING btree (character_id, valence);


--
-- Name: idx_emotional_triggers_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_emotional_triggers_character ON public.character_emotional_triggers USING btree (character_id, trigger_type);


--
-- Name: idx_entity_rel_bidirectional; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_rel_bidirectional ON public.entity_relationships USING btree (bidirectional, from_entity_id, to_entity_id);


--
-- Name: idx_entity_rel_forward; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_rel_forward ON public.entity_relationships USING btree (from_entity_id, weight DESC);


--
-- Name: idx_entity_rel_reverse; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_rel_reverse ON public.entity_relationships USING btree (to_entity_id, weight DESC);


--
-- Name: idx_entity_rel_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_rel_type ON public.entity_relationships USING btree (relationship_type, weight DESC);


--
-- Name: idx_expertise_domains_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_expertise_domains_character ON public.character_expertise_domains USING btree (character_id, domain_name);


--
-- Name: idx_fact_entities_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_entities_attributes ON public.fact_entities USING gin (attributes);


--
-- Name: idx_fact_entities_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_entities_category ON public.fact_entities USING btree (entity_type, category);


--
-- Name: idx_fact_entities_name_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_entities_name_lookup ON public.fact_entities USING btree (entity_name);


--
-- Name: idx_fact_entities_name_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_entities_name_trgm ON public.fact_entities USING gin (entity_name public.gin_trgm_ops);


--
-- Name: idx_fact_entities_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_entities_search ON public.fact_entities USING gin (search_vector);


--
-- Name: idx_fact_entities_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_entities_type ON public.fact_entities USING btree (entity_type);


--
-- Name: idx_fact_entities_type_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fact_entities_type_lookup ON public.fact_entities USING btree (entity_type, entity_name);


--
-- Name: idx_interests_char_cat; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_interests_char_cat ON public.character_interests USING btree (character_id, category);


--
-- Name: idx_message_triggers_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_message_triggers_character ON public.character_message_triggers USING btree (character_id, trigger_category);


--
-- Name: idx_personality_evolution_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_evolution_character ON public.personality_evolution_timeline USING btree (character_name);


--
-- Name: idx_personality_evolution_magnitude; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_evolution_magnitude ON public.personality_evolution_timeline USING btree (change_magnitude);


--
-- Name: idx_personality_evolution_parameter; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_evolution_parameter ON public.personality_evolution_timeline USING btree (parameter_path);


--
-- Name: idx_personality_evolution_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_evolution_timestamp ON public.personality_evolution_timeline USING btree (change_timestamp);


--
-- Name: idx_personality_opt_attempts_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_opt_attempts_character ON public.personality_optimization_attempts USING btree (character_name);


--
-- Name: idx_personality_opt_attempts_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_opt_attempts_id ON public.personality_optimization_attempts USING btree (optimization_id);


--
-- Name: idx_personality_opt_attempts_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_opt_attempts_timestamp ON public.personality_optimization_attempts USING btree (attempt_timestamp);


--
-- Name: idx_personality_opt_results_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_opt_results_character ON public.personality_optimization_results USING btree (character_name);


--
-- Name: idx_personality_opt_results_improvement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_opt_results_improvement ON public.personality_optimization_results USING btree (actual_improvement);


--
-- Name: idx_personality_opt_results_success; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_opt_results_success ON public.personality_optimization_results USING btree (success);


--
-- Name: idx_personality_opt_results_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_opt_results_timestamp ON public.personality_optimization_results USING btree (completion_timestamp);


--
-- Name: idx_personality_param_adj_opt_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_param_adj_opt_id ON public.personality_parameter_adjustments USING btree (optimization_id);


--
-- Name: idx_personality_param_adj_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_param_adj_order ON public.personality_parameter_adjustments USING btree (optimization_id, adjustment_order);


--
-- Name: idx_personality_param_adj_path; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_param_adj_path ON public.personality_parameter_adjustments USING btree (parameter_path);


--
-- Name: idx_personality_traits_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_personality_traits_character ON public.personality_traits USING btree (character_id);


--
-- Name: idx_platform_identities_platform_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_platform_identities_platform_user ON public.platform_identities USING btree (platform, platform_user_id);


--
-- Name: idx_platform_identities_universal_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_platform_identities_universal_id ON public.platform_identities USING btree (universal_id);


--
-- Name: idx_relationship_events_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_relationship_events_timestamp ON public.relationship_events USING btree (created_at DESC);


--
-- Name: idx_relationship_events_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_relationship_events_type ON public.relationship_events USING btree (event_type);


--
-- Name: idx_relationship_events_user_bot; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_relationship_events_user_bot ON public.relationship_events USING btree (user_id, bot_name);


--
-- Name: idx_relationship_scores_bot; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_relationship_scores_bot ON public.relationship_scores USING btree (bot_name);


--
-- Name: idx_relationship_scores_trust; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_relationship_scores_trust ON public.relationship_scores USING btree (trust) WHERE (trust < 0.4);


--
-- Name: idx_relationship_scores_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_relationship_scores_user ON public.relationship_scores USING btree (user_id);


--
-- Name: idx_response_guidelines_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_response_guidelines_character ON public.character_response_guidelines USING btree (character_id, guideline_type);


--
-- Name: idx_response_modes_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_response_modes_character ON public.character_response_modes USING btree (character_id, mode_name);


--
-- Name: idx_role_transactions_state; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_transactions_state ON public.role_transactions USING btree (state);


--
-- Name: idx_role_transactions_user_bot; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_transactions_user_bot ON public.role_transactions USING btree (user_id, bot_name);


--
-- Name: idx_roleplay_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roleplay_created ON public.roleplay_transactions USING btree (created_at DESC);


--
-- Name: idx_roleplay_scenarios_char; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roleplay_scenarios_char ON public.character_roleplay_scenarios_v2 USING btree (character_id);


--
-- Name: idx_roleplay_state; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roleplay_state ON public.roleplay_transactions USING btree (state) WHERE (completed_at IS NULL);


--
-- Name: idx_roleplay_user_bot; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_roleplay_user_bot ON public.roleplay_transactions USING btree (user_id, bot_name);


--
-- Name: idx_scenario_triggers_scenario; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scenario_triggers_scenario ON public.character_scenario_triggers_v2 USING btree (scenario_id);


--
-- Name: idx_speech_patterns_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_speech_patterns_character ON public.character_speech_patterns USING btree (character_id, pattern_type);


--
-- Name: idx_trust_recovery_stage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trust_recovery_stage ON public.trust_recovery_state USING btree (recovery_stage) WHERE ((recovery_stage)::text = ANY ((ARRAY['active'::character varying, 'recovering'::character varying])::text[]));


--
-- Name: idx_trust_recovery_user_bot; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trust_recovery_user_bot ON public.trust_recovery_state USING btree (user_id, bot_name);


--
-- Name: idx_universal_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_universal_users_email ON public.universal_users USING btree (email);


--
-- Name: idx_universal_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_universal_users_username ON public.universal_users USING btree (primary_username);


--
-- Name: idx_user_events_temporal; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_events_temporal ON public.user_events USING btree (user_id, bot_name, event_type, timestamp_utc DESC);


--
-- Name: idx_user_facts_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_facts_character ON public.user_fact_relationships USING btree (user_id, mentioned_by_character, confidence DESC);


--
-- Name: idx_user_facts_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_facts_created ON public.user_fact_relationships USING btree (user_id, created_at DESC);


--
-- Name: idx_user_facts_emotional; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_facts_emotional ON public.user_fact_relationships USING btree (user_id, emotional_context, confidence DESC);


--
-- Name: idx_user_facts_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_facts_entity ON public.user_fact_relationships USING btree (entity_id, confidence DESC);


--
-- Name: idx_user_facts_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_facts_lookup ON public.user_fact_relationships USING btree (user_id, confidence DESC, updated_at DESC);


--
-- Name: idx_user_facts_related; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_facts_related ON public.user_fact_relationships USING gin (related_entities);


--
-- Name: idx_user_facts_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_facts_type ON public.user_fact_relationships USING btree (user_id, relationship_type, confidence DESC);


--
-- Name: idx_user_preferences_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_preferences_lookup ON public.user_preferences USING btree (user_id, bot_name, preference_type);


--
-- Name: idx_user_profiles_last_interaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_profiles_last_interaction ON public.user_profiles USING btree (last_interaction);


--
-- Name: idx_user_profiles_preferences_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_profiles_preferences_gin ON public.user_profiles USING gin (preferences);


--
-- Name: idx_user_profiles_relationship_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_profiles_relationship_level ON public.user_profiles USING btree (relationship_level);


--
-- Name: idx_vocabulary_char_pref; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vocabulary_char_pref ON public.character_vocabulary USING btree (character_id, preference);


--
-- Name: idx_voice_traits_character; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_voice_traits_character ON public.character_voice_traits USING btree (character_id, trait_type);


--
-- Name: character_abilities trigger_update_character_timestamp_abilities; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_character_timestamp_abilities AFTER INSERT OR DELETE OR UPDATE ON public.character_abilities FOR EACH ROW EXECUTE FUNCTION public.update_character_timestamp();


--
-- Name: character_appearance trigger_update_character_timestamp_appearance; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_character_timestamp_appearance AFTER INSERT OR DELETE OR UPDATE ON public.character_appearance FOR EACH ROW EXECUTE FUNCTION public.update_character_timestamp();


--
-- Name: character_background trigger_update_character_timestamp_background; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_character_timestamp_background AFTER INSERT OR DELETE OR UPDATE ON public.character_background FOR EACH ROW EXECUTE FUNCTION public.update_character_timestamp();


--
-- Name: character_essence trigger_update_character_timestamp_essence; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_character_timestamp_essence AFTER INSERT OR DELETE OR UPDATE ON public.character_essence FOR EACH ROW EXECUTE FUNCTION public.update_character_timestamp();


--
-- Name: character_instructions trigger_update_character_timestamp_instructions; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_character_timestamp_instructions AFTER INSERT OR DELETE OR UPDATE ON public.character_instructions FOR EACH ROW EXECUTE FUNCTION public.update_character_timestamp();


--
-- Name: character_memories trigger_update_character_timestamp_memories; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_character_timestamp_memories AFTER INSERT OR DELETE OR UPDATE ON public.character_memories FOR EACH ROW EXECUTE FUNCTION public.update_character_timestamp();


--
-- Name: character_metadata trigger_update_character_timestamp_metadata; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_character_timestamp_metadata AFTER INSERT OR DELETE OR UPDATE ON public.character_metadata FOR EACH ROW EXECUTE FUNCTION public.update_character_timestamp();


--
-- Name: character_communication_patterns trigger_update_character_timestamp_patterns; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_character_timestamp_patterns AFTER INSERT OR DELETE OR UPDATE ON public.character_communication_patterns FOR EACH ROW EXECUTE FUNCTION public.update_character_timestamp();


--
-- Name: character_relationships trigger_update_character_timestamp_relationships; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_character_timestamp_relationships AFTER INSERT OR DELETE OR UPDATE ON public.character_relationships FOR EACH ROW EXECUTE FUNCTION public.update_character_timestamp();


--
-- Name: character_behavioral_triggers trigger_update_character_timestamp_triggers; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_character_timestamp_triggers AFTER INSERT OR DELETE OR UPDATE ON public.character_behavioral_triggers FOR EACH ROW EXECUTE FUNCTION public.update_character_timestamp();


--
-- Name: roleplay_transactions trigger_update_roleplay_transaction_timestamp; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_roleplay_transaction_timestamp BEFORE UPDATE ON public.roleplay_transactions FOR EACH ROW EXECUTE FUNCTION public.update_roleplay_transaction_timestamp();


--
-- Name: fact_entities update_fact_entities_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_fact_entities_updated_at BEFORE UPDATE ON public.fact_entities FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user_fact_relationships update_user_fact_relationships_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_user_fact_relationships_updated_at BEFORE UPDATE ON public.user_fact_relationships FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: character_abilities character_abilities_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_abilities
    ADD CONSTRAINT character_abilities_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_ai_scenarios character_ai_scenarios_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_ai_scenarios
    ADD CONSTRAINT character_ai_scenarios_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_appearance character_appearance_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_appearance
    ADD CONSTRAINT character_appearance_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_attributes character_attributes_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_attributes
    ADD CONSTRAINT character_attributes_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_background character_background_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_background
    ADD CONSTRAINT character_background_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_behavioral_triggers character_behavioral_triggers_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_behavioral_triggers
    ADD CONSTRAINT character_behavioral_triggers_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_communication_patterns character_communication_patterns_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_communication_patterns
    ADD CONSTRAINT character_communication_patterns_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_context_guidance character_context_guidance_context_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_context_guidance
    ADD CONSTRAINT character_context_guidance_context_id_fkey FOREIGN KEY (context_id) REFERENCES public.character_conversation_contexts(id) ON DELETE CASCADE;


--
-- Name: character_conversation_contexts character_conversation_contexts_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_conversation_contexts
    ADD CONSTRAINT character_conversation_contexts_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_conversation_directives character_conversation_directives_conversation_flow_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_conversation_directives
    ADD CONSTRAINT character_conversation_directives_conversation_flow_id_fkey FOREIGN KEY (conversation_flow_id) REFERENCES public.character_conversation_flows(id) ON DELETE CASCADE;


--
-- Name: character_conversation_flows character_conversation_flows_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_conversation_flows
    ADD CONSTRAINT character_conversation_flows_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_cultural_expressions character_cultural_expressions_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_cultural_expressions
    ADD CONSTRAINT character_cultural_expressions_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_current_context character_current_context_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_current_context
    ADD CONSTRAINT character_current_context_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_current_goals character_current_goals_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_current_goals
    ADD CONSTRAINT character_current_goals_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_directives character_directives_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_directives
    ADD CONSTRAINT character_directives_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_emoji_patterns character_emoji_patterns_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emoji_patterns
    ADD CONSTRAINT character_emoji_patterns_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_emotion_profile character_emotion_profile_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotion_profile
    ADD CONSTRAINT character_emotion_profile_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_emotion_range character_emotion_range_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotion_range
    ADD CONSTRAINT character_emotion_range_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_emotional_triggers character_emotional_triggers_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotional_triggers
    ADD CONSTRAINT character_emotional_triggers_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_emotional_triggers_v2 character_emotional_triggers_v2_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_emotional_triggers_v2
    ADD CONSTRAINT character_emotional_triggers_v2_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_essence character_essence_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_essence
    ADD CONSTRAINT character_essence_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_expertise_domains character_expertise_domains_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_expertise_domains
    ADD CONSTRAINT character_expertise_domains_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_identity_details character_identity_details_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_identity_details
    ADD CONSTRAINT character_identity_details_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_instructions character_instructions_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_instructions
    ADD CONSTRAINT character_instructions_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_interests character_interests_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_interests
    ADD CONSTRAINT character_interests_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_memories character_memories_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_memories
    ADD CONSTRAINT character_memories_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_message_triggers character_message_triggers_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_message_triggers
    ADD CONSTRAINT character_message_triggers_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_metadata character_metadata_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_metadata
    ADD CONSTRAINT character_metadata_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_relationships character_relationships_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_relationships
    ADD CONSTRAINT character_relationships_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_response_guidelines character_response_guidelines_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_response_guidelines
    ADD CONSTRAINT character_response_guidelines_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_response_modes character_response_modes_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_response_modes
    ADD CONSTRAINT character_response_modes_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_roleplay_config character_roleplay_config_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_roleplay_config
    ADD CONSTRAINT character_roleplay_config_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_roleplay_scenarios_v2 character_roleplay_scenarios_v2_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_roleplay_scenarios_v2
    ADD CONSTRAINT character_roleplay_scenarios_v2_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_scenario_triggers_v2 character_scenario_triggers_v2_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_scenario_triggers_v2
    ADD CONSTRAINT character_scenario_triggers_v2_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.character_roleplay_scenarios_v2(id) ON DELETE CASCADE;


--
-- Name: character_speech_patterns character_speech_patterns_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_speech_patterns
    ADD CONSTRAINT character_speech_patterns_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_values character_values_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_values
    ADD CONSTRAINT character_values_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_vocabulary character_vocabulary_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_vocabulary
    ADD CONSTRAINT character_vocabulary_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_voice_profile character_voice_profile_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_voice_profile
    ADD CONSTRAINT character_voice_profile_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: character_voice_traits character_voice_traits_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.character_voice_traits
    ADD CONSTRAINT character_voice_traits_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: communication_styles communication_styles_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.communication_styles
    ADD CONSTRAINT communication_styles_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: emotions emotions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emotions
    ADD CONSTRAINT emotions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: entity_relationships entity_relationships_from_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_from_entity_id_fkey FOREIGN KEY (from_entity_id) REFERENCES public.fact_entities(id) ON DELETE CASCADE;


--
-- Name: entity_relationships entity_relationships_to_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_to_entity_id_fkey FOREIGN KEY (to_entity_id) REFERENCES public.fact_entities(id) ON DELETE CASCADE;


--
-- Name: facts facts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facts
    ADD CONSTRAINT facts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: dynamic_personality_traits fk_user_profile; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dynamic_personality_traits
    ADD CONSTRAINT fk_user_profile FOREIGN KEY (user_id) REFERENCES public.dynamic_personality_profiles(user_id) ON DELETE CASCADE;


--
-- Name: dynamic_conversation_analyses fk_user_profile_analysis; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dynamic_conversation_analyses
    ADD CONSTRAINT fk_user_profile_analysis FOREIGN KEY (user_id) REFERENCES public.dynamic_personality_profiles(user_id) ON DELETE CASCADE;


--
-- Name: memory_entries memory_entries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.memory_entries
    ADD CONSTRAINT memory_entries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: personality_evolution_timeline personality_evolution_timeline_optimization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_evolution_timeline
    ADD CONSTRAINT personality_evolution_timeline_optimization_id_fkey FOREIGN KEY (optimization_id) REFERENCES public.personality_optimization_attempts(optimization_id) ON DELETE SET NULL;


--
-- Name: personality_optimization_results personality_optimization_results_optimization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_optimization_results
    ADD CONSTRAINT personality_optimization_results_optimization_id_fkey FOREIGN KEY (optimization_id) REFERENCES public.personality_optimization_attempts(optimization_id) ON DELETE CASCADE;


--
-- Name: personality_parameter_adjustments personality_parameter_adjustments_optimization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_parameter_adjustments
    ADD CONSTRAINT personality_parameter_adjustments_optimization_id_fkey FOREIGN KEY (optimization_id) REFERENCES public.personality_optimization_attempts(optimization_id) ON DELETE CASCADE;


--
-- Name: personality_traits personality_traits_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.personality_traits
    ADD CONSTRAINT personality_traits_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(id) ON DELETE CASCADE;


--
-- Name: platform_identities platform_identities_universal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_identities
    ADD CONSTRAINT platform_identities_universal_id_fkey FOREIGN KEY (universal_id) REFERENCES public.universal_users(universal_id) ON DELETE CASCADE;


--
-- Name: relationship_events relationship_events_user_id_bot_name_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationship_events
    ADD CONSTRAINT relationship_events_user_id_bot_name_fkey FOREIGN KEY (user_id, bot_name) REFERENCES public.relationship_scores(user_id, bot_name) ON DELETE CASCADE;


--
-- Name: relationships relationships_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationships
    ADD CONSTRAINT relationships_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: trust_recovery_state trust_recovery_state_user_id_bot_name_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trust_recovery_state
    ADD CONSTRAINT trust_recovery_state_user_id_bot_name_fkey FOREIGN KEY (user_id, bot_name) REFERENCES public.relationship_scores(user_id, bot_name) ON DELETE CASCADE;


--
-- Name: user_fact_relationships user_fact_relationships_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_fact_relationships
    ADD CONSTRAINT user_fact_relationships_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.fact_entities(id) ON DELETE CASCADE;


--
-- Name: user_fact_relationships user_fact_relationships_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_fact_relationships
    ADD CONSTRAINT user_fact_relationships_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.universal_users(universal_id) ON DELETE CASCADE;


-- ============================================================================
-- SEED DATA: Default AI Assistant Character for Quickstart
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
-- End of seed data
-- ============================================================================


--
-- PostgreSQL database dump complete
--

