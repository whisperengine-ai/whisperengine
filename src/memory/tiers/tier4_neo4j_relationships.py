# src/memory/tiers/tier4_neo4j_relationships.py

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
import json

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j driver not available. Install with: pip install neo4j")

class Neo4jRelationshipEngine:
    """
    Tier 4: Relationship intelligence and knowledge graph
    Maps topics, entities, and conversation patterns for enhanced context
    """
    
    def __init__(self, uri: str, user: str, password: str):
        if not NEO4J_AVAILABLE:
            raise ImportError("Neo4j driver not available")
        
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize Neo4j connection and ensure schema"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            
            # Verify connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            await self._ensure_schema()
            self.logger.info("Neo4j relationship engine initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize Neo4j: %s", e)
            raise
    
    async def _ensure_schema(self):
        """Ensure graph schema and constraints exist"""
        constraints_and_indexes = [
            # Node constraints
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "CREATE CONSTRAINT conversation_id_unique IF NOT EXISTS FOR (c:Conversation) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT topic_name_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
            
            # Performance indexes for frequently queried properties
            "CREATE INDEX conversation_timestamp IF NOT EXISTS FOR (c:Conversation) ON (c.timestamp)",
            "CREATE INDEX topic_category IF NOT EXISTS FOR (t:Topic) ON (t.category)",
            "CREATE INDEX user_name IF NOT EXISTS FOR (u:User) ON (u.name)",
            "CREATE INDEX session_start_time IF NOT EXISTS FOR (s:Session) ON (s.start_time)",
            
            # Memory-related indexes based on runtime warnings
            "CREATE INDEX memory_user_id IF NOT EXISTS FOR (m:Memory) ON (m.user_id)",
            "CREATE INDEX memory_timestamp IF NOT EXISTS FOR (m:Memory) ON (m.timestamp)",
            "CREATE INDEX memory_type IF NOT EXISTS FOR (m:Memory) ON (m.type)",
            "CREATE INDEX user_memory_lookup IF NOT EXISTS FOR (u:User) ON (u.id)",
            
            # Conversation-related indexes for performance
            "CREATE INDEX conversation_user_id IF NOT EXISTS FOR (c:Conversation) ON (c.user_id)",
            "CREATE INDEX session_user_id IF NOT EXISTS FOR (s:Session) ON (s.user_id)",
        ]
        
        try:
            with self.driver.session() as session:
                for cypher in constraints_and_indexes:
                    try:
                        session.run(cypher)
                    except Exception as constraint_error:
                        # Some constraints might already exist
                        self.logger.debug("Constraint/Index creation info: %s", constraint_error)
            
            self.logger.debug("Graph schema ensured")
            
        except Exception as e:
            self.logger.error("Failed to ensure graph schema: %s", e)
            raise
    
    async def store_conversation_relationships(
        self,
        conversation_id: str,
        user_id: str,
        topics: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store conversation and its relationships in the knowledge graph"""
        
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized")
        
        metadata = metadata or {}
        
        try:
            with self.driver.session() as session:
                # Create or update user node
                session.run("""
                    MERGE (u:User {id: $user_id})
                    ON CREATE SET u.name = $user_id, u.created_at = datetime()
                    ON MATCH SET u.last_active = datetime()
                """, user_id=user_id)
                
                # Create conversation node
                session.run("""
                    CREATE (c:Conversation {
                        id: $conversation_id,
                        timestamp: datetime($timestamp),
                        session_id: $session_id,
                        channel_id: $channel_id,
                        intent: $intent,
                        emotional_tone: $emotional_tone
                    })
                """, 
                    conversation_id=conversation_id,
                    timestamp=datetime.now().isoformat(),
                    session_id=metadata.get('session_id'),
                    channel_id=metadata.get('channel_id'),
                    intent=metadata.get('intent', 'unknown'),
                    emotional_tone=metadata.get('emotional_tone', 'neutral')
                )
                
                # Link user to conversation
                session.run("""
                    MATCH (u:User {id: $user_id})
                    MATCH (c:Conversation {id: $conversation_id})
                    CREATE (u)-[:HAD_CONVERSATION {timestamp: datetime()}]->(c)
                """, user_id=user_id, conversation_id=conversation_id)
                
                # Process topics
                for i, topic in enumerate(topics[:5]):  # Limit to 5 topics
                    await self._store_topic_relationships(
                        session, conversation_id, user_id, topic, i, metadata
                    )
                
                # Handle session relationships if session_id provided
                if metadata.get('session_id'):
                    await self._store_session_relationships(
                        session, conversation_id, user_id, metadata['session_id'], metadata
                    )
                
                self.logger.debug("Stored relationships for conversation %s", conversation_id)
                
        except Exception as e:
            self.logger.error("Failed to store conversation relationships: %s", e)
            raise
    
    async def _store_topic_relationships(
        self,
        session,
        conversation_id: str,
        user_id: str,
        topic: str,
        topic_index: int,
        metadata: Dict[str, Any]
    ):
        """Store topic relationships and connections"""
        
        topic_cleaned = topic.lower().strip()
        if not topic_cleaned:
            return
        
        # Create or update topic node
        session.run("""
            MERGE (t:Topic {name: $topic_name})
            ON CREATE SET 
                t.category = $category,
                t.first_discussed = datetime(),
                t.discussion_count = 1
            ON MATCH SET 
                t.discussion_count = t.discussion_count + 1,
                t.last_discussed = datetime()
        """, 
            topic_name=topic_cleaned,
            category=self._categorize_topic(topic_cleaned)
        )
        
        # Link conversation to topic
        session.run("""
            MATCH (c:Conversation {id: $conversation_id})
            MATCH (t:Topic {name: $topic_name})
            CREATE (c)-[:DISCUSSED {
                relevance: $relevance,
                topic_index: $topic_index,
                timestamp: datetime()
            }]->(t)
        """, 
            conversation_id=conversation_id,
            topic_name=topic_cleaned,
            relevance=1.0 - (topic_index * 0.1),  # Higher relevance for earlier topics
            topic_index=topic_index
        )
        
        # Link user interest to topic
        session.run("""
            MATCH (u:User {id: $user_id})
            MATCH (t:Topic {name: $topic_name})
            MERGE (u)-[r:INTERESTED_IN]->(t)
            ON CREATE SET 
                r.strength = 1.0,
                r.first_discussed = datetime(),
                r.discussion_count = 1
            ON MATCH SET 
                r.strength = r.strength + 0.1,
                r.discussion_count = r.discussion_count + 1,
                r.last_discussed = datetime()
        """, user_id=user_id, topic_name=topic_cleaned)
        
        # Create topic-to-topic relationships for frequently co-occurring topics
        other_topics = [t.lower().strip() for t in metadata.get('topics', []) if t.lower().strip() != topic_cleaned]
        for other_topic in other_topics[:2]:  # Limit to 2 related topics
            session.run("""
                MATCH (t1:Topic {name: $topic1})
                MATCH (t2:Topic {name: $topic2})
                MERGE (t1)-[r:RELATED_TO]-(t2)
                ON CREATE SET r.strength = 1.0, r.co_occurrences = 1
                ON MATCH SET 
                    r.strength = r.strength + 0.1,
                    r.co_occurrences = r.co_occurrences + 1
            """, topic1=topic_cleaned, topic2=other_topic)
    
    async def _store_session_relationships(
        self,
        session,
        conversation_id: str,
        user_id: str,
        session_id: str,
        metadata: Dict[str, Any]
    ):
        """Store session-based relationships"""
        
        # Create or update session node
        session.run("""
            MERGE (s:Session {id: $session_id})
            ON CREATE SET 
                s.start_time = datetime(),
                s.user_id = $user_id,
                s.conversation_count = 1
            ON MATCH SET 
                s.conversation_count = s.conversation_count + 1,
                s.last_activity = datetime()
        """, session_id=session_id, user_id=user_id)
        
        # Link conversation to session
        session.run("""
            MATCH (c:Conversation {id: $conversation_id})
            MATCH (s:Session {id: $session_id})
            CREATE (c)-[:PART_OF_SESSION]->(s)
        """, conversation_id=conversation_id, session_id=session_id)
        
        # Find conversation flow patterns within session
        session.run("""
            MATCH (s:Session {id: $session_id})<-[:PART_OF_SESSION]-(c1:Conversation)
            MATCH (s)<-[:PART_OF_SESSION]-(c2:Conversation)
            WHERE c1.timestamp < c2.timestamp
            AND duration.between(c1.timestamp, c2.timestamp).minutes <= 30
            WITH c1, c2
            ORDER BY c1.timestamp DESC, c2.timestamp ASC
            LIMIT 1
            MERGE (c1)-[r:FOLLOWED_BY]->(c2)
            ON CREATE SET r.delay_minutes = duration.between(c1.timestamp, c2.timestamp).minutes
        """, session_id=session_id)
    
    def _categorize_topic(self, topic: str) -> str:
        """Simple topic categorization"""
        tech_keywords = ['programming', 'python', 'javascript', 'coding', 'software', 'api', 'database', 'ai', 'machine', 'learning']
        personal_keywords = ['career', 'advice', 'help', 'problem', 'issue', 'feeling', 'think']
        educational_keywords = ['learn', 'study', 'understand', 'explain', 'concept', 'theory']
        
        topic_lower = topic.lower()
        
        if any(keyword in topic_lower for keyword in tech_keywords):
            return 'technology'
        elif any(keyword in topic_lower for keyword in personal_keywords):
            return 'personal'
        elif any(keyword in topic_lower for keyword in educational_keywords):
            return 'educational'
        else:
            return 'general'
    
    async def get_related_conversation_topics(
        self,
        user_id: str,
        current_topics: List[str],
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Get related topics and conversations based on user's interest graph"""
        
        if not self.driver or not current_topics:
            return []
        
        current_topics_cleaned = [topic.lower().strip() for topic in current_topics if topic.strip()]
        
        try:
            with self.driver.session() as session:
                # Find related topics through user interests and topic relationships
                result = session.run("""
                    MATCH (u:User {id: $user_id})-[ui:INTERESTED_IN]->(current_topic:Topic)
                    WHERE current_topic.name IN $current_topics
                    
                    // Find related topics (use OPTIONAL MATCH to handle missing RELATED_TO relationships)
                    OPTIONAL MATCH (current_topic)-[rel:RELATED_TO]-(related_topic:Topic)
                    WHERE related_topic IS NOT NULL
                    OPTIONAL MATCH (u)-[ui2:INTERESTED_IN]->(related_topic)
                    WHERE ui2 IS NOT NULL
                    
                    // Get recent conversations about related topics
                    OPTIONAL MATCH (related_topic)<-[disc:DISCUSSED]-(c:Conversation)<-[:HAD_CONVERSATION]-(u)
                    WHERE c.timestamp > datetime() - duration('P30D')
                    
                    WITH related_topic, ui2, rel, collect(DISTINCT c.id) as conversation_ids, count(DISTINCT c) as conv_count
                    WHERE related_topic IS NOT NULL AND ui2 IS NOT NULL
                    
                    RETURN 
                        related_topic.name as topic,
                        related_topic.category as category,
                        ui2.strength as user_interest_strength,
                        COALESCE(rel.strength, 0.5) as topic_relationship_strength,
                        conversation_ids[0..2] as recent_conversation_ids,
                        conv_count as conversation_count
                    
                    ORDER BY (ui2.strength * COALESCE(rel.strength, 0.5)) DESC
                    LIMIT $limit
                """, 
                    user_id=user_id,
                    current_topics=current_topics_cleaned,
                    limit=limit
                )
                
                related_topics = []
                for record in result:
                    topic_data = {
                        "topic": record["topic"],
                        "category": record["category"],
                        "user_interest_strength": float(record["user_interest_strength"]),
                        "topic_relationship_strength": float(record["topic_relationship_strength"]),
                        "conversation_ids": record["recent_conversation_ids"],
                        "conversation_count": record["conversation_count"],
                        "relevance_score": float(record["user_interest_strength"]) * float(record["topic_relationship_strength"])
                    }
                    related_topics.append(topic_data)
                
                self.logger.debug("Found %d related topics for user %s", len(related_topics), user_id)
                return related_topics
                
        except Exception as e:
            self.logger.error("Failed to get related topics: %s", e)
            return []
    
    async def get_user_interest_profile(
        self,
        user_id: str,
        min_strength: float = 1.0
    ) -> Dict[str, Any]:
        """Get comprehensive user interest profile from the knowledge graph"""
        
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # Get user's primary interests
                interests_result = session.run("""
                    MATCH (u:User {id: $user_id})-[r:INTERESTED_IN]->(t:Topic)
                    WHERE r.strength >= $min_strength
                    RETURN 
                        t.name as topic,
                        t.category as category,
                        r.strength as strength,
                        r.discussion_count as discussion_count,
                        r.first_discussed as first_discussed,
                        r.last_discussed as last_discussed
                    ORDER BY r.strength DESC
                    LIMIT 10
                """, user_id=user_id, min_strength=min_strength)
                
                interests = []
                for record in interests_result:
                    interest = {
                        "topic": record["topic"],
                        "category": record["category"],
                        "strength": float(record["strength"]),
                        "discussion_count": record["discussion_count"],
                        "first_discussed": record["first_discussed"].isoformat() if record["first_discussed"] else None,
                        "last_discussed": record["last_discussed"].isoformat() if record["last_discussed"] else None
                    }
                    interests.append(interest)
                
                # Get conversation patterns
                patterns_result = session.run("""
                    MATCH (u:User {id: $user_id})-[:HAD_CONVERSATION]->(c:Conversation)
                    RETURN 
                        count(c) as total_conversations,
                        count(DISTINCT c.session_id) as unique_sessions,
                        collect(DISTINCT c.intent)[0..5] as common_intents,
                        collect(DISTINCT c.emotional_tone)[0..5] as emotional_patterns
                """, user_id=user_id)
                
                patterns = {}
                if patterns_result.single():
                    record = patterns_result.single()
                    patterns = {
                        "total_conversations": record["total_conversations"],
                        "unique_sessions": record["unique_sessions"],
                        "common_intents": record["common_intents"],
                        "emotional_patterns": record["emotional_patterns"]
                    }
                
                profile = {
                    "user_id": user_id,
                    "interests": interests,
                    "conversation_patterns": patterns,
                    "generated_at": datetime.now().isoformat()
                }
                
                return profile
                
        except Exception as e:
            self.logger.error("Failed to get user interest profile: %s", e)
            return {}
    
    async def find_conversation_patterns(
        self,
        user_id: str,
        pattern_type: str = "temporal",
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Find conversation patterns for user"""
        
        if not self.driver:
            return []
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            with self.driver.session() as session:
                if pattern_type == "temporal":
                    # Find temporal conversation patterns
                    result = session.run("""
                        MATCH (u:User {id: $user_id})-[:HAD_CONVERSATION]->(c:Conversation)
                        WHERE c.timestamp > datetime($since_date)
                        
                        WITH c, c.timestamp.hour as hour
                        
                        RETURN 
                            hour,
                            count(*) as conversation_count,
                            collect(DISTINCT c.intent)[0..3] as common_intents
                        ORDER BY conversation_count DESC
                        LIMIT 10
                    """, user_id=user_id, since_date=since_date)
                    
                elif pattern_type == "topical":
                    # Find topical conversation flows
                    result = session.run("""
                        MATCH (u:User {id: $user_id})-[:HAD_CONVERSATION]->(c1:Conversation)-[:FOLLOWED_BY]->(c2:Conversation)
                        MATCH (c1)-[:DISCUSSED]->(t1:Topic)
                        MATCH (c2)-[:DISCUSSED]->(t2:Topic)
                        WHERE c1.timestamp > datetime($since_date)
                        
                        RETURN 
                            t1.name as from_topic,
                            t2.name as to_topic,
                            count(*) as transition_count,
                            avg(c1.timestamp) as avg_delay_minutes
                        ORDER BY transition_count DESC
                        LIMIT 10
                    """, user_id=user_id, since_date=since_date)
                    
                else:
                    return []
                
                patterns = []
                for record in result:
                    pattern = dict(record)
                    patterns.append(pattern)
                
                return patterns
                
        except Exception as e:
            self.logger.error("Failed to find conversation patterns: %s", e)
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and its relationships"""
        
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Conversation {id: $conversation_id})
                    DETACH DELETE c
                    RETURN count(c) as deleted_count
                """, conversation_id=conversation_id)
                
                deleted = result.single()["deleted_count"] > 0
                
                if deleted:
                    self.logger.debug("Deleted conversation %s from knowledge graph", conversation_id)
                
                return deleted
                
        except Exception as e:
            self.logger.error("Failed to delete conversation %s: %s", conversation_id, e)
            return False
    
    async def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User) WITH count(u) as users
                    MATCH (c:Conversation) WITH users, count(c) as conversations
                    MATCH (t:Topic) WITH users, conversations, count(t) as topics
                    MATCH (s:Session) WITH users, conversations, topics, count(s) as sessions
                    MATCH ()-[r]->() WITH users, conversations, topics, sessions, count(r) as relationships
                    
                    RETURN users, conversations, topics, sessions, relationships
                """)
                
                stats = {}
                if result.single():
                    record = result.single()
                    stats = {
                        "users": record["users"],
                        "conversations": record["conversations"],
                        "topics": record["topics"],
                        "sessions": record["sessions"],
                        "relationships": record["relationships"],
                        "status": "healthy"
                    }
                
                return stats
                
        except Exception as e:
            self.logger.error("Failed to get graph stats: %s", e)
            return {"status": "error", "error": str(e)}
    
    async def ping(self) -> bool:
        """Check if Neo4j connection is alive"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            return True
        except Exception as e:
            self.logger.error("Neo4j ping failed: %s", e)
            return False
    
    async def cleanup_old_relationships(self, days_to_keep: int = 365) -> int:
        """Cleanup old conversations and relationships"""
        
        if not self.driver:
            return 0
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Conversation)
                    WHERE c.timestamp < datetime($cutoff_date)
                    DETACH DELETE c
                    RETURN count(c) as deleted_count
                """, cutoff_date=cutoff_date)
                
                deleted_count = result.single()["deleted_count"]
                
                # Cleanup orphaned topics (topics with no conversations)
                session.run("""
                    MATCH (t:Topic)
                    WHERE NOT (t)<-[:DISCUSSED]-(:Conversation)
                    DETACH DELETE t
                """)
                
                self.logger.info("Cleaned up %d old conversations from knowledge graph", deleted_count)
                return deleted_count
                
        except Exception as e:
            self.logger.error("Failed to cleanup old relationships: %s", e)
            return 0
    
    async def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j driver connection closed")


# Utility functions

async def create_neo4j_engine(uri: str, user: str, password: str) -> Neo4jRelationshipEngine:
    """Create and initialize a Neo4j relationship engine"""
    engine = Neo4jRelationshipEngine(uri, user, password)
    await engine.initialize()
    return engine

async def test_neo4j_performance():
    """Test Neo4j relationship engine performance"""
    import os
    
    # Use test Neo4j instance or default
    uri = os.getenv('TEST_NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('TEST_NEO4J_USER', 'neo4j')
    password = os.getenv('TEST_NEO4J_PASSWORD', 'password')
    
    if not NEO4J_AVAILABLE:
        print("Neo4j driver not available. Install with: pip install neo4j")
        return
    
    try:
        engine = await create_neo4j_engine(uri, user, password)
        
        import time
        import uuid
        
        user_id = "test_user"
        test_conversations = []
        
        # Store test relationships
        start_time = time.time()
        for i in range(10):
            conversation_id = str(uuid.uuid4())
            test_conversations.append(conversation_id)
            
            topics = [f"topic_{i}", f"category_{i % 3}"]
            
            await engine.store_conversation_relationships(
                conversation_id=conversation_id,
                user_id=user_id,
                topics=topics,
                metadata={
                    "intent": "test",
                    "session_id": str(uuid.uuid4()) if i % 3 == 0 else None
                }
            )
        
        store_time = time.time() - start_time
        
        # Test relationship queries
        start_time = time.time()
        related_topics = await engine.get_related_conversation_topics(
            user_id=user_id,
            current_topics=["topic_1", "category_1"],
            limit=3
        )
        query_time = time.time() - start_time
        
        # Test user profile
        start_time = time.time()
        profile = await engine.get_user_interest_profile(user_id)
        profile_time = time.time() - start_time
        
        # Cleanup
        for conv_id in test_conversations:
            await engine.delete_conversation(conv_id)
        
        await engine.close()
        
        print(f"Store performance: {store_time:.4f}s for 10 relationships")
        print(f"Query performance: {query_time:.4f}s, found {len(related_topics)} related topics")
        print(f"Profile performance: {profile_time:.4f}s, {len(profile.get('interests', []))} interests")
        
    except Exception as e:
        print(f"Neo4j test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_neo4j_performance())