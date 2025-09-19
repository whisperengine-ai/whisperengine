// Neo4j Schema for Hierarchical Memory Architecture
// Initialize constraints and indexes for Tier 4: Relationship Graph

// Create constraints for unique nodes
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT topic_name_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT conversation_id_unique IF NOT EXISTS FOR (c:Conversation) REQUIRE c.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX user_last_active IF NOT EXISTS FOR (u:User) ON (u.last_active);
CREATE INDEX topic_category IF NOT EXISTS FOR (t:Topic) ON (t.category);
CREATE INDEX conversation_timestamp IF NOT EXISTS FOR (c:Conversation) ON (c.timestamp);

// Example data structure creation
// This will be populated dynamically by the hierarchical memory system

RETURN "Hierarchical Memory Neo4j schema initialized successfully!" as status;