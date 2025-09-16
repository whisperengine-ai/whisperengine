"""
Graph Database Memory Enhancement

This module provides Neo4j integration for relationship-aware memory management,
enhancing the existing ChromaDB/PostgreSQL system with graph-based connections.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

try:
    from neo4j import AsyncGraphDatabase, GraphDatabase

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None
    AsyncGraphDatabase = None

logger = logging.getLogger(__name__)


@dataclass
class GraphMemoryConfig:
    """Configuration for graph database connection"""

    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "password"
    database: str = "whisper_engine"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50


class GraphMemoryManager:
    """Enhanced memory manager using Neo4j for relationship modeling"""

    def __init__(self, config: GraphMemoryConfig, memory_manager=None):
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available. Graph features disabled.")
            self.enabled = False
            return

        self.config = config
        self.memory_manager = memory_manager  # Reference to existing ChromaDB manager
        self.driver = None
        self.enabled = True

    async def initialize(self):
        """Initialize Neo4j connection and create constraints/indexes"""
        if not self.enabled:
            return

        try:
            self.driver = AsyncGraphDatabase.driver(
                self.config.uri, auth=(self.config.username, self.config.password)
            )

            # Test connection
            await self.driver.verify_connectivity()

            # Create schema
            await self._create_schema()

            logger.info("Graph database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize graph database: {e}")
            self.enabled = False

    async def _create_schema(self):
        """Create necessary constraints and indexes"""
        schema_queries = [
            # Constraints
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "CREATE CONSTRAINT topic_name_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT emotion_id_unique IF NOT EXISTS FOR (e:EmotionContext) REQUIRE e.id IS UNIQUE",
            # Indexes for performance
            "CREATE INDEX user_discord_id IF NOT EXISTS FOR (u:User) ON (u.discord_id)",
            "CREATE INDEX topic_category IF NOT EXISTS FOR (t:Topic) ON (t.category)",
            "CREATE INDEX memory_timestamp IF NOT EXISTS FOR (m:Memory) ON (m.timestamp)",
            "CREATE INDEX emotion_timestamp IF NOT EXISTS FOR (e:EmotionContext) ON (e.timestamp)",
        ]

        async with self.driver.session(database=self.config.database) as session:
            for query in schema_queries:
                try:
                    await session.run(query)
                    logger.debug(f"Schema query executed: {query}")
                except Exception as e:
                    logger.warning(f"Schema query failed: {query}, Error: {e}")

    async def create_or_update_user(
        self,
        user_id: str,
        discord_id: str,
        name: str | None = None,
        personality_traits: list[str] | None = None,
        communication_style: str | None = None,
    ) -> bool:
        """Create or update user node"""
        if not self.enabled:
            return False

        query = """
        MERGE (u:User {id: $user_id})
        SET u.discord_id = $discord_id,
            u.name = $name,
            u.personality_traits = $personality_traits,
            u.communication_style = $communication_style,
            u.updated_at = datetime()
        ON CREATE SET u.created_at = datetime()
        RETURN u
        """

        try:
            async with self.driver.session(database=self.config.database) as session:
                result = await session.run(
                    query,
                    user_id=user_id,
                    discord_id=discord_id,
                    name=name,
                    personality_traits=personality_traits or [],
                    communication_style=communication_style,
                )
                await result.consume()
                return True

        except Exception as e:
            logger.error(f"Failed to create/update user {user_id}: {e}")
            return False

    async def create_memory_with_relationships(
        self,
        user_id: str,
        chromadb_id: str,
        summary: str,
        topics: list[str],
        emotion_data: dict | None = None,
        importance: float = 0.5,
    ) -> bool:
        """Create memory node and establish relationships"""
        if not self.enabled:
            return False

        memory_id = f"{user_id}_{chromadb_id}_{int(datetime.now().timestamp())}"

        # Create memory node
        memory_query = """
        MATCH (u:User {id: $user_id})
        CREATE (m:Memory {
            id: $memory_id,
            chromadb_id: $chromadb_id,
            summary: $summary,
            importance: $importance,
            timestamp: datetime(),
            context_type: 'conversation'
        })
        CREATE (u)-[:REMEMBERS {
            access_count: 1,
            importance: $importance,
            created_at: datetime()
        }]->(m)
        RETURN m
        """

        try:
            async with self.driver.session(database=self.config.database) as session:
                # Create memory
                await session.run(
                    memory_query,
                    user_id=user_id,
                    memory_id=memory_id,
                    chromadb_id=chromadb_id,
                    summary=summary,
                    importance=importance,
                )

                # Create topic relationships
                for topic in topics:
                    await self._create_topic_relationship(session, memory_id, topic, user_id)

                # Create emotion context if provided
                if emotion_data:
                    await self._create_emotion_relationship(
                        session, memory_id, emotion_data, user_id
                    )

                return True

        except Exception as e:
            logger.error(f"Failed to create memory relationships: {e}")
            return False

    async def _create_topic_relationship(self, session, memory_id: str, topic: str, user_id: str):
        """Create or update topic relationships"""
        topic_query = """
        MERGE (t:Topic {name: $topic})
        ON CREATE SET t.category = 'general',
                     t.importance_score = 0.5,
                     t.first_mentioned = datetime(),
                     t.created_at = datetime()
        SET t.last_mentioned = datetime()

        WITH t
        MATCH (m:Memory {id: $memory_id})
        MERGE (m)-[r:ABOUT]->(t)
        SET r.relevance = 0.8

        WITH t
        MATCH (u:User {id: $user_id})
        MERGE (u)-[i:INTERESTED_IN]->(t)
        ON CREATE SET i.strength = 0.3, i.since = datetime()
        SET i.strength = i.strength + 0.1
        """

        await session.run(topic_query, topic=topic, memory_id=memory_id, user_id=user_id)

    async def _create_emotion_relationship(
        self, session, memory_id: str, emotion_data: dict, user_id: str
    ):
        """Create emotion context and relationships"""
        emotion_id = f"emotion_{memory_id}_{emotion_data.get('detected_emotion', 'neutral')}"

        emotion_query = """
        CREATE (e:EmotionContext {
            id: $emotion_id,
            emotion: $emotion,
            intensity: $intensity,
            trigger_event: $trigger_event,
            timestamp: datetime(),
            resolved: false
        })

        WITH e
        MATCH (m:Memory {id: $memory_id})
        CREATE (m)-[:EVOKED_EMOTION {strength: $intensity}]->(e)

        WITH e
        MATCH (u:User {id: $user_id})
        CREATE (u)-[:EXPERIENCED {
            context: 'conversation',
            intensity: $intensity,
            timestamp: datetime()
        }]->(e)
        """

        await session.run(
            emotion_query,
            emotion_id=emotion_id,
            emotion=emotion_data.get("detected_emotion", "neutral"),
            intensity=emotion_data.get("intensity", 0.5),
            trigger_event=emotion_data.get("trigger_event", "conversation"),
            memory_id=memory_id,
            user_id=user_id,
        )

    async def get_relationship_context(self, user_id: str) -> dict:
        """Get comprehensive relationship context for personalized responses"""
        if not self.enabled:
            return {}

        context_query = """
        MATCH (u:User {id: $user_id})
        OPTIONAL MATCH (u)-[r:REMEMBERS]->(m:Memory)
        OPTIONAL MATCH (u)-[i:INTERESTED_IN]->(t:Topic)
        OPTIONAL MATCH (u)-[e:EXPERIENCED]->(ec:EmotionContext)

        WITH u,
             count(DISTINCT m) as memory_count,
             count(DISTINCT t) as topic_count,
             collect(DISTINCT t.name) as topics,
             collect(DISTINCT {emotion: ec.emotion, intensity: e.intensity}) as emotions

        RETURN {
            name: u.name,
            memory_count: memory_count,
            topic_count: topic_count,
            interests: topics[0..5],
            recent_emotions: emotions[-5..],
            communication_style: u.communication_style,
            personality_traits: u.personality_traits,
            intimacy_level: CASE
                WHEN memory_count > 50 THEN 0.9
                WHEN memory_count > 20 THEN 0.7
                WHEN memory_count > 10 THEN 0.5
                ELSE 0.3
            END
        } as context
        """

        try:
            async with self.driver.session(database=self.config.database) as session:
                result = await session.run(context_query, user_id=user_id)
                record = await result.single()
                return record["context"] if record else {}

        except Exception as e:
            logger.error(f"Failed to get relationship context for {user_id}: {e}")
            return {}

    async def get_emotional_patterns(self, user_id: str) -> dict:
        """Analyze emotional patterns and triggers"""
        if not self.enabled:
            return {}

        pattern_query = """
        MATCH (u:User {id: $user_id})-[:EXPERIENCED]->(e:EmotionContext)
        WITH u, e.emotion as emotion, count(e) as frequency, avg(e.intensity) as avg_intensity
        ORDER BY frequency DESC, avg_intensity DESC

        WITH u, collect({
            emotion: emotion,
            frequency: frequency,
            avg_intensity: avg_intensity
        }) as emotion_patterns

        MATCH (u)-[:INTERESTED_IN]->(t:Topic)-[:TRIGGERS]->(trigger_e:EmotionContext)
        WITH u, emotion_patterns,
             collect({
                topic: t.name,
                triggered_emotion: trigger_e.emotion,
                frequency: count(trigger_e)
             }) as triggers

        RETURN {
            patterns: emotion_patterns,
            triggers: triggers,
            dominant_emotions: emotion_patterns[0..3]
        } as emotional_analysis
        """

        try:
            async with self.driver.session(database=self.config.database) as session:
                result = await session.run(pattern_query, user_id=user_id)
                record = await result.single()
                return record["emotional_analysis"] if record else {}

        except Exception as e:
            logger.error(f"Failed to get emotional patterns for {user_id}: {e}")
            return {}

    async def find_related_memories(
        self, user_id: str, current_topics: list[str], limit: int = 5
    ) -> list[dict]:
        """Find memories related to current topics with emotional context"""
        if not self.enabled:
            return []

        related_query = """
        MATCH (u:User {id: $user_id})-[:REMEMBERS]->(m:Memory)-[:ABOUT]->(t:Topic)
        WHERE t.name IN $topics
        OPTIONAL MATCH (m)-[:EVOKED_EMOTION]->(e:EmotionContext)

        WITH m, t, e,
             m.importance +
             CASE WHEN e IS NOT NULL THEN e.intensity * 0.3 ELSE 0 END as relevance_score

        ORDER BY relevance_score DESC, m.timestamp DESC
        LIMIT $limit

        RETURN {
            memory_id: m.id,
            chromadb_id: m.chromadb_id,
            summary: m.summary,
            topic: t.name,
            emotion: e.emotion,
            emotional_intensity: e.intensity,
            importance: m.importance,
            relevance_score: relevance_score
        } as related_memory
        """

        try:
            async with self.driver.session(database=self.config.database) as session:
                result = await session.run(
                    related_query, user_id=user_id, topics=current_topics, limit=limit
                )

                memories = []
                async for record in result:
                    memories.append(record["related_memory"])

                return memories

        except Exception as e:
            logger.error(f"Failed to find related memories: {e}")
            return []

    async def update_relationship_milestone(
        self, user_id: str, milestone_type: str, context: str | None = None
    ):
        """Track relationship progression milestones"""
        if not self.enabled:
            return

        milestone_query = """
        MATCH (u:User {id: $user_id})
        MERGE (bot:User {id: 'bot', name: 'Assistant'})
        CREATE (u)-[:RELATIONSHIP_MILESTONE {
            level: $milestone_type,
            achieved_at: datetime(),
            context: $context
        }]->(bot)
        """

        try:
            async with self.driver.session(database=self.config.database) as session:
                await session.run(
                    milestone_query,
                    user_id=user_id,
                    milestone_type=milestone_type,
                    context=context or "",
                )

        except Exception as e:
            logger.error(f"Failed to update relationship milestone: {e}")

    async def close(self):
        """Close database connection"""
        if self.driver:
            await self.driver.close()
