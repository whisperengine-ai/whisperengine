-- CDL Graph Intelligence Performance Indexes
-- STEP 8: Database Performance Optimization
-- Optimizes graph query performance to sub-millisecond response times

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- ================================================================
-- CORE CDL CHARACTER TABLE INDEXES
-- ================================================================

-- Character lookup performance (primary operations)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_characters_name_lookup 
ON characters(name);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_characters_active_lookup 
ON characters(id) WHERE is_active = true;

-- ================================================================
-- CHARACTER BACKGROUND PERFORMANCE INDEXES
-- ================================================================

-- GIN index for trigger-based memory queries (array overlap)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_background_triggers_gin 
ON character_background USING GIN(triggers);

-- Trigram index for text similarity search (natural language matching)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_background_description_trgm 
ON character_background USING GIN(description gin_trgm_ops);

-- Importance level sorting (highest priority background first)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_background_importance 
ON character_background(character_id, importance_level DESC);

-- Category-filtered queries with importance sorting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_background_category_importance 
ON character_background(character_id, category, importance_level DESC);

-- Combined trigger + importance index for cross-pollination queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_background_triggers_importance 
ON character_background USING GIN(character_id, triggers, importance_level);

-- ================================================================
-- CHARACTER MEMORIES PERFORMANCE INDEXES
-- ================================================================

-- GIN index for memory trigger array overlap queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_memories_triggers_gin 
ON character_memories USING GIN(triggers);

-- Memory importance sorting (most impactful memories first)  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_memories_importance 
ON character_memories(character_id, importance_level DESC);

-- Emotional impact sorting for empathy matching
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_memories_emotional_impact 
ON character_memories(character_id, emotional_impact DESC);

-- Combined memory query index (triggers + importance)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_memories_trigger_importance 
ON character_memories USING GIN(character_id, triggers, importance_level);

-- ================================================================
-- CHARACTER RELATIONSHIPS PERFORMANCE INDEXES  
-- ================================================================

-- Relationship strength sorting (strongest relationships first)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_relationships_strength 
ON character_relationships(character_id, relationship_strength DESC);

-- Relationship type filtering with strength
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_relationships_type_strength 
ON character_relationships(character_id, relationship_type, relationship_strength DESC);

-- ================================================================
-- CHARACTER ABILITIES PERFORMANCE INDEXES
-- ================================================================

-- Proficiency level sorting (highest skills first)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_abilities_proficiency 
ON character_abilities(character_id, proficiency_level DESC);

-- Ability type filtering with proficiency  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_abilities_type_proficiency 
ON character_abilities(character_id, ability_type, proficiency_level DESC);

-- ================================================================
-- FACT ENTITIES AND USER RELATIONSHIPS (Semantic Router Integration)
-- ================================================================

-- Entity lookup performance for cross-pollination
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fact_entities_name_lookup 
ON fact_entities(entity_name);

-- User fact relationships for confidence-aware conversations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_fact_relationships_user_confidence 
ON user_fact_relationships(user_id, confidence_score DESC);

-- Combined user + entity lookup for fact retrieval
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_fact_relationships_user_entity 
ON user_fact_relationships(user_id, entity_id, confidence_score DESC);

-- Entity type filtering for categorized fact queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fact_entities_type_lookup 
ON fact_entities(entity_type, entity_name);

-- ================================================================
-- COMPOSITE INDEXES FOR COMPLEX GRAPH QUERIES
-- ================================================================

-- Character graph intelligence composite index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_character_graph_intelligence_composite 
ON character_background(character_id, importance_level DESC, category) 
INCLUDE (description, triggers);

-- Cross-pollination optimization index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cross_pollination_composite 
ON character_background USING GIN(triggers) 
INCLUDE (character_id, importance_level, description);

-- Memory trigger optimization index  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memory_trigger_composite 
ON character_memories USING GIN(triggers) 
INCLUDE (character_id, importance_level, emotional_impact, memory_content);

-- ================================================================
-- PERFORMANCE ANALYSIS VIEWS
-- ================================================================

-- Create performance monitoring view
CREATE OR REPLACE VIEW character_graph_performance AS
SELECT 
    'character_background' as table_name,
    count(*) as total_rows,
    avg(length(description)) as avg_description_length,
    count(DISTINCT character_id) as unique_characters,
    min(importance_level) as min_importance,
    max(importance_level) as max_importance
FROM character_background
UNION ALL
SELECT 
    'character_memories' as table_name,
    count(*) as total_rows,
    avg(length(memory_content)) as avg_content_length,
    count(DISTINCT character_id) as unique_characters,
    min(importance_level) as min_importance,
    max(importance_level) as max_importance
FROM character_memories
UNION ALL
SELECT 
    'character_relationships' as table_name,
    count(*) as total_rows,
    null as avg_content_length,
    count(DISTINCT character_id) as unique_characters,
    min(relationship_strength) as min_importance,
    max(relationship_strength) as max_importance
FROM character_relationships
UNION ALL
SELECT 
    'character_abilities' as table_name,
    count(*) as total_rows,
    null as avg_content_length,
    count(DISTINCT character_id) as unique_characters,
    min(proficiency_level) as min_importance,
    max(proficiency_level) as max_importance
FROM character_abilities;

-- ================================================================
-- INDEX USAGE STATISTICS
-- ================================================================

-- Create function to analyze index performance
CREATE OR REPLACE FUNCTION analyze_cdl_graph_index_performance()
RETURNS TABLE(
    index_name text,
    table_name text,
    index_size text,
    index_scans bigint,
    tuples_read bigint,
    tuples_fetched bigint
) AS $$
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
$$ LANGUAGE plpgsql;

-- ================================================================
-- QUERY PERFORMANCE TARGETS
-- ================================================================

/*
Performance Goals with New Indexes:

1. Character Background Queries: <10ms
   - SELECT * FROM character_background WHERE character_id = ? ORDER BY importance_level DESC
   - Uses: idx_character_background_importance

2. Memory Trigger Queries: <15ms 
   - SELECT * FROM character_memories WHERE triggers && ARRAY['diving'] AND character_id = ?
   - Uses: idx_character_memories_triggers_gin

3. Cross-Pollination Queries: <20ms
   - SELECT * FROM character_background WHERE triggers && (SELECT array_agg(entity_name) FROM fact_entities...)
   - Uses: idx_character_background_triggers_gin + idx_fact_entities_name_lookup

4. Confidence-Aware Queries: <10ms
   - SELECT * FROM user_fact_relationships WHERE user_id = ? ORDER BY confidence_score DESC
   - Uses: idx_user_fact_relationships_user_confidence

5. Relationship Queries: <10ms
   - SELECT * FROM character_relationships WHERE character_id = ? ORDER BY relationship_strength DESC
   - Uses: idx_character_relationships_strength

6. Ability Queries: <10ms  
   - SELECT * FROM character_abilities WHERE character_id = ? ORDER BY proficiency_level DESC
   - Uses: idx_character_abilities_proficiency

Total Graph Query Target: <50ms end-to-end
*/

-- ================================================================
-- MAINTENANCE AND MONITORING
-- ================================================================

-- Create maintenance function for index health
CREATE OR REPLACE FUNCTION maintain_cdl_graph_indexes()
RETURNS void AS $$
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
$$ LANGUAGE plpgsql;

-- Schedule maintenance (example - adjust for your environment)
-- SELECT cron.schedule('maintain-cdl-indexes', '0 2 * * *', 'SELECT maintain_cdl_graph_indexes();');

COMMIT;