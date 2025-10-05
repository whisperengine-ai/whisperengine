-- ============================================================================
-- WhisperEngine Semantic Knowledge Graph Schema
-- ============================================================================
-- Purpose: Enhanced PostgreSQL schema for factual relationship management
-- Consolidates graph functionality into PostgreSQL for operational simplicity
-- Supports personality-first character responses with structured intelligence
--
-- Date: October 4, 2025
-- Status: Phase 1 Implementation
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For similarity matching
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- ============================================================================
-- FACT ENTITIES
-- ============================================================================
-- Core entity storage with full-text search capabilities
-- Represents things users can have relationships with (foods, hobbies, places, etc.)

CREATE TABLE IF NOT EXISTS fact_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL, -- 'food', 'hobby', 'person', 'place', 'media', 'activity', 'topic'
    entity_name TEXT NOT NULL,
    category TEXT, -- e.g., 'italian' for pizza, 'outdoor' for hiking
    subcategory TEXT, -- More specific classification
    attributes JSONB DEFAULT '{}', -- Flexible additional attributes
    
    -- Full-text search vector (auto-generated)
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', 
            COALESCE(entity_name, '') || ' ' || 
            COALESCE(category, '') || ' ' || 
            COALESCE(subcategory, '') || ' ' ||
            COALESCE(attributes->>'tags', '')
        )
    ) STORED,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(entity_type, entity_name),
    CHECK(entity_type IN ('food', 'hobby', 'person', 'place', 'media', 'activity', 'topic', 'other'))
);

-- Indexes for performance
CREATE INDEX idx_fact_entities_type ON fact_entities(entity_type);
CREATE INDEX idx_fact_entities_category ON fact_entities(entity_type, category);
CREATE INDEX idx_fact_entities_search ON fact_entities USING GIN(search_vector);
CREATE INDEX idx_fact_entities_attributes ON fact_entities USING GIN(attributes);
CREATE INDEX idx_fact_entities_name_trgm ON fact_entities USING GIN(entity_name gin_trgm_ops);

COMMENT ON TABLE fact_entities IS 'Core entity storage for facts and concepts';
COMMENT ON COLUMN fact_entities.entity_type IS 'Type of entity for categorical organization';
COMMENT ON COLUMN fact_entities.search_vector IS 'Auto-generated full-text search vector';
COMMENT ON COLUMN fact_entities.attributes IS 'Flexible JSONB storage for entity-specific attributes';

-- ============================================================================
-- USER-FACT RELATIONSHIPS
-- ============================================================================
-- The knowledge graph core - relationships between users and entities
-- This is where we store "User likes Pizza" type relationships

CREATE TABLE IF NOT EXISTS user_fact_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES universal_users(universal_id) ON DELETE CASCADE,
    entity_id UUID NOT NULL REFERENCES fact_entities(id) ON DELETE CASCADE,
    
    -- Relationship properties
    relationship_type TEXT NOT NULL, -- 'likes', 'dislikes', 'knows', 'visited', 'wants', 'owns', 'prefers'
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1) DEFAULT 0.5,
    strength FLOAT CHECK (strength >= 0 AND strength <= 1) DEFAULT 0.5,
    
    -- Context metadata
    emotional_context TEXT, -- 'happy', 'excited', 'neutral', 'sad', 'angry', 'anxious'
    context_metadata JSONB DEFAULT '{}', -- Additional flexible context
    
    -- Source tracking (critical for character-aware responses)
    source_conversation_id TEXT, -- Link to conversation where this was learned
    mentioned_by_character TEXT, -- Which character learned this fact
    source_platform TEXT DEFAULT 'discord', -- 'discord', 'web', 'api'
    
    -- Graph relationships stored as JSONB for flexible traversal
    -- Format: [{"entity_id": "uuid", "relation": "similar_to", "weight": 0.8}]
    related_entities JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, entity_id, relationship_type),
    CHECK(LENGTH(relationship_type) > 0 AND LENGTH(relationship_type) <= 50)  -- Flexible validation
);

-- Indexes for high-performance queries
CREATE INDEX idx_user_facts_lookup ON user_fact_relationships(user_id, confidence DESC, updated_at DESC);
CREATE INDEX idx_user_facts_type ON user_fact_relationships(user_id, relationship_type, confidence DESC);
CREATE INDEX idx_user_facts_entity ON user_fact_relationships(entity_id, confidence DESC);
CREATE INDEX idx_user_facts_character ON user_fact_relationships(user_id, mentioned_by_character, confidence DESC);
CREATE INDEX idx_user_facts_emotional ON user_fact_relationships(user_id, emotional_context, confidence DESC);
CREATE INDEX idx_user_facts_related ON user_fact_relationships USING GIN(related_entities);
CREATE INDEX idx_user_facts_created ON user_fact_relationships(user_id, created_at DESC);

COMMENT ON TABLE user_fact_relationships IS 'Knowledge graph relationships between users and entities';
COMMENT ON COLUMN user_fact_relationships.confidence IS 'Confidence score 0-1 based on frequency and recency';
COMMENT ON COLUMN user_fact_relationships.mentioned_by_character IS 'Character who learned this fact for character-aware responses';
COMMENT ON COLUMN user_fact_relationships.related_entities IS 'JSONB array of related entity connections';

-- ============================================================================
-- ENTITY RELATIONSHIPS
-- ============================================================================
-- Relationships between entities (like graph edges)
-- E.g., "Pizza is similar to Pasta", "Hiking is part of Outdoor Activities"

CREATE TABLE IF NOT EXISTS entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity_id UUID NOT NULL REFERENCES fact_entities(id) ON DELETE CASCADE,
    to_entity_id UUID NOT NULL REFERENCES fact_entities(id) ON DELETE CASCADE,
    
    -- Relationship properties
    relationship_type TEXT NOT NULL, -- 'similar_to', 'part_of', 'category_of', 'related_to', 'opposite_of', 'requires'
    weight FLOAT CHECK (weight >= 0 AND weight <= 1) DEFAULT 0.5,
    bidirectional BOOLEAN DEFAULT false, -- If true, relationship works both ways
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(from_entity_id, to_entity_id, relationship_type),
    CHECK(from_entity_id != to_entity_id), -- No self-relationships
    CHECK(relationship_type IN ('similar_to', 'part_of', 'category_of', 'related_to', 'opposite_of', 'requires'))
);

-- Indexes for graph traversal
CREATE INDEX idx_entity_rel_forward ON entity_relationships(from_entity_id, weight DESC);
CREATE INDEX idx_entity_rel_reverse ON entity_relationships(to_entity_id, weight DESC);
CREATE INDEX idx_entity_rel_type ON entity_relationships(relationship_type, weight DESC);
CREATE INDEX idx_entity_rel_bidirectional ON entity_relationships(bidirectional, from_entity_id, to_entity_id);

COMMENT ON TABLE entity_relationships IS 'Relationships between entities for graph traversal';
COMMENT ON COLUMN entity_relationships.bidirectional IS 'If true, relationship applies in both directions';

-- ============================================================================
-- CHARACTER INTERACTIONS
-- ============================================================================
-- Track which characters mentioned which entities in conversations
-- Critical for character-aware response generation

CREATE TABLE IF NOT EXISTS character_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES universal_users(universal_id) ON DELETE CASCADE,
    character_name TEXT NOT NULL,
    
    -- Interaction details
    interaction_type TEXT NOT NULL, -- 'conversation', 'fact_mention', 'emotional_support', 'advice', 'education'
    session_id TEXT, -- Optional session grouping
    entity_references JSONB DEFAULT '[]', -- Array of entity names mentioned
    
    -- Context
    emotional_tone TEXT, -- Emotional tone of the interaction
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CHECK(interaction_type IN ('conversation', 'fact_mention', 'emotional_support', 'advice', 'education', 'other'))
);

-- Indexes for character-aware queries
CREATE INDEX idx_char_interactions_user ON character_interactions(user_id, character_name, created_at DESC);
CREATE INDEX idx_char_interactions_type ON character_interactions(user_id, interaction_type, created_at DESC);
CREATE INDEX idx_char_interactions_entities ON character_interactions USING GIN(entity_references);

COMMENT ON TABLE character_interactions IS 'Track character-specific interactions for personality-aware responses';
COMMENT ON COLUMN character_interactions.entity_references IS 'JSONB array of entity names mentioned in this interaction';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_fact_entities_updated_at
    BEFORE UPDATE ON fact_entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_fact_relationships_updated_at
    BEFORE UPDATE ON user_fact_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to auto-discover similar entities using pg_trgm
CREATE OR REPLACE FUNCTION discover_similar_entities(
    p_entity_id UUID,
    p_similarity_threshold FLOAT DEFAULT 0.3,
    p_limit INT DEFAULT 5
)
RETURNS TABLE (
    similar_entity_id UUID,
    similar_entity_name TEXT,
    similarity_score FLOAT
) AS $$
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
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION discover_similar_entities IS 'Auto-discover similar entities using trigram similarity';

-- Function to get user facts with related entities (1-2 hop traversal)
CREATE OR REPLACE FUNCTION get_user_facts_with_relations(
    p_user_id UUID,
    p_entity_type TEXT DEFAULT NULL,
    p_min_confidence FLOAT DEFAULT 0.5,
    p_limit INT DEFAULT 20
)
RETURNS TABLE (
    entity_name TEXT,
    entity_category TEXT,
    relationship_type TEXT,
    confidence FLOAT,
    emotional_context TEXT,
    mentioned_by_character TEXT,
    related_entities_count BIGINT,
    last_updated TIMESTAMP
) AS $$
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
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_facts_with_relations IS 'Get user facts with count of related entities';

-- ============================================================================
-- SAMPLE QUERIES FOR COMMON USE CASES
-- ============================================================================

-- Query 1: Simple fact retrieval - "What foods do I like?"
/*
SELECT 
    fe.entity_name, 
    ufr.confidence, 
    ufr.emotional_context,
    ufr.mentioned_by_character,
    ufr.updated_at
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = $1 
  AND fe.entity_type = 'food'
  AND ufr.relationship_type = 'likes'
  AND ufr.confidence > 0.5
ORDER BY ufr.confidence DESC, ufr.updated_at DESC
LIMIT 10;
*/

-- Query 2: Character-aware facts - "What have I told Elena?"
/*
SELECT 
    fe.entity_name,
    ufr.confidence,
    ufr.relationship_type,
    COUNT(ci.id) as mention_count,
    MAX(ci.created_at) as last_mentioned
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
LEFT JOIN character_interactions ci ON ci.user_id = ufr.user_id 
    AND ci.character_name = $2
    AND ci.entity_references @> jsonb_build_array(fe.entity_name::text)
WHERE ufr.user_id = $1 
  AND (ufr.mentioned_by_character = $2 OR ci.id IS NOT NULL)
GROUP BY fe.entity_name, ufr.confidence, ufr.relationship_type
ORDER BY mention_count DESC, ufr.confidence DESC
LIMIT 20;
*/

-- Query 3: Relationship discovery (2-hop) - "What's similar to pizza?"
/*
WITH user_foods AS (
    SELECT fe.entity_name, fe.id, ufr.confidence
    FROM user_fact_relationships ufr
    JOIN fact_entities fe ON ufr.entity_id = fe.id
    WHERE ufr.user_id = $1 AND fe.entity_type = 'food'
),
related_foods AS (
    SELECT DISTINCT
        fe2.entity_name,
        er.weight,
        er.relationship_type,
        uf.confidence as source_confidence
    FROM user_foods uf
    JOIN entity_relationships er ON uf.id = er.from_entity_id
    JOIN fact_entities fe2 ON er.to_entity_id = fe2.id
    WHERE er.relationship_type IN ('similar_to', 'related_to')
      AND er.weight > 0.5
      AND fe2.entity_name != uf.entity_name
)
SELECT entity_name, weight, relationship_type, source_confidence
FROM related_foods
ORDER BY weight * source_confidence DESC
LIMIT 20;
*/

-- Query 4: Full-text entity search
/*
SELECT 
    entity_name, 
    category, 
    entity_type,
    ts_rank(search_vector, plainto_tsquery('english', $1)) as relevance
FROM fact_entities
WHERE search_vector @@ plainto_tsquery('english', $1)
ORDER BY relevance DESC
LIMIT 20;
*/

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO whisperengine_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO whisperengine_app;
