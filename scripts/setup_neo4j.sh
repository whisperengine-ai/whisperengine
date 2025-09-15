#!/bin/bash

# Neo4j Graph Database Setup Script for Docker
# This script initializes the Neo4j container with the required APOC plugin and basic schema

set -e

echo "🚀 Starting Neo4j Graph Database Setup..."

# Check if Neo4j container is running
if ! docker ps | grep -q "whisperengine-neo4j"; then
    echo "❌ Neo4j container is not running. Please start with: docker-compose up -d neo4j"
    exit 1
fi

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker exec whisperengine-neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-neo4j}" "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - waiting for Neo4j..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Neo4j failed to start within expected time"
    exit 1
fi

# Initialize schema and constraints
echo "📝 Initializing Neo4j schema..."

docker exec whisperengine-neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-neo4j}" << 'EOF'
// Create constraints for unique IDs
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT topic_id_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT experience_id_unique IF NOT EXISTS FOR (e:Experience) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT emotion_id_unique IF NOT EXISTS FOR (ec:EmotionContext) REQUIRE ec.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX user_discord_id IF NOT EXISTS FOR (u:User) ON (u.discord_id);
CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name);
CREATE INDEX memory_timestamp IF NOT EXISTS FOR (m:Memory) ON (m.timestamp);
CREATE INDEX emotion_timestamp IF NOT EXISTS FOR (ec:EmotionContext) ON (ec.timestamp);
CREATE INDEX experience_timestamp IF NOT EXISTS FOR (e:Experience) ON (e.timestamp);

// Create the bot user node
MERGE (bot:User {id: 'bot'})
SET bot.name = 'Assistant',
    bot.discord_id = 'bot',
    bot.created_at = datetime(),
    bot.communication_style = 'helpful_companion';

RETURN "Schema initialized successfully" as status;
EOF

echo "✅ Neo4j schema initialized!"

# Verify APOC plugin is available
echo "🔌 Verifying APOC plugin..."
if docker exec whisperengine-neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-neo4j}" "RETURN apoc.version()" > /dev/null 2>&1; then
    echo "✅ APOC plugin is available!"
else
    echo "⚠️  APOC plugin not available - some advanced features may not work"
fi

# Create sample data for testing (optional)
if [ "${INIT_SAMPLE_DATA:-false}" = "true" ]; then
    echo "📊 Creating sample data..."
    
    docker exec whisperengine-neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-neo4j}" << 'EOF'
// Create sample user
MERGE (u:User {id: 'sample_user_123'})
SET u.discord_id = '123456789',
    u.name = 'Sample User',
    u.created_at = datetime(),
    u.communication_style = 'casual';

// Create sample topics
MERGE (t1:Topic {id: 'topic_work'})
SET t1.name = 'work',
    t1.category = 'professional',
    t1.created_at = datetime();

MERGE (t2:Topic {id: 'topic_hobbies'})
SET t2.name = 'hobbies',
    t2.category = 'personal',
    t2.created_at = datetime();

// Create sample memory
MERGE (m:Memory {id: 'memory_sample_1'})
SET m.chromadb_id = 'sample_chromadb_id_1',
    m.summary = 'User discussed their work project',
    m.importance = 0.7,
    m.timestamp = datetime(),
    m.context_type = 'conversation';

// Create relationships
MERGE (u)-[:REMEMBERS {importance: 0.7, access_count: 1, created_at: datetime()}]->(m)
MERGE (m)-[:ABOUT {relevance: 0.8, created_at: datetime()}]->(t1)
MERGE (u)-[:INTERESTED_IN {strength: 0.6, since: datetime()}]->(t1)

RETURN "Sample data created" as status;
EOF
    
    echo "✅ Sample data created!"
fi

echo "🎉 Neo4j Graph Database setup complete!"
echo ""
echo "📋 Connection Details:"
echo "  • HTTP UI: http://localhost:7474"
echo "  • Bolt Protocol: bolt://localhost:7687"
echo "  • Username: neo4j"
echo "  • Password: ${NEO4J_PASSWORD:-neo4j}"
echo ""
echo "🔗 Access the Neo4j Browser at http://localhost:7474 to explore your graph!"
