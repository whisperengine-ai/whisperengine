"""Neo4j connector for Docker containerized Neo4j database."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


@dataclass
class Neo4jConfig:
    """Configuration for Neo4j connection."""

    host: str = "neo4j"  # Docker service name
    port: int = 7687
    username: str = "neo4j"
    password: str = "neo4j_password_change_me"
    database: str = "neo4j"

    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        """Create config from environment variables."""
        return cls(
            host=os.getenv("NEO4J_HOST", "neo4j"),
            port=int(os.getenv("NEO4J_PORT", "7687")),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "neo4j_password_change_me"),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
        )

    @property
    def uri(self) -> str:
        """Get Neo4j connection URI."""
        return f"bolt://{self.host}:{self.port}"


class Neo4jConnector:
    """Async Neo4j database connector for Docker containerized setup."""

    def __init__(self, config: Neo4jConfig | None = None):
        self.config = config or Neo4jConfig.from_env()
        self._driver: Driver | None = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self._driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                max_connection_lifetime=3600,  # 1 hour
                max_connection_pool_size=50,
                connection_timeout=30,
                encrypted=False,  # Docker internal communication
            )

            # Test connection
            await self._verify_connectivity()
            self._connected = True
            logger.info(f"Connected to Neo4j at {self.config.uri}")

            # Initialize schema
            await self._initialize_schema()

        except ServiceUnavailable as e:
            error_msg = f"Neo4j server is not available at {self.config.uri}"
            logger.error(error_msg)
            logger.info(
                "To fix: Start Neo4j with 'docker compose up neo4j' or disable graph database"
            )
            raise ConnectionError(error_msg) from e
        except Exception as e:
            if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                error_msg = f"Neo4j authentication failed for user '{self.config.username}'"
                logger.error(error_msg)
                logger.info("To fix: Check NEO4J_USERNAME and NEO4J_PASSWORD environment variables")
                raise ConnectionError(error_msg) from e
            elif "connection" in str(e).lower() or "refused" in str(e).lower():
                error_msg = f"Cannot connect to Neo4j server at {self.config.uri}"
                logger.error(error_msg)
                logger.info("To fix: Ensure Neo4j server is running and accessible")
                raise ConnectionError(error_msg) from e
            else:
                error_msg = f"Unexpected Neo4j connection error: {e}"
                logger.error(error_msg)
                raise ConnectionError(error_msg) from e

    async def disconnect(self) -> None:
        """Close Neo4j connection."""
        if self._driver:
            await asyncio.get_event_loop().run_in_executor(None, self._driver.close)
            self._connected = False
            logger.info("Disconnected from Neo4j")

    async def _verify_connectivity(self) -> None:
        """Verify database connectivity."""

        def verify_connection(driver: Driver):
            with driver.session(database=self.config.database) as session:
                session.run("RETURN 1")

        await asyncio.get_event_loop().run_in_executor(None, verify_connection, self._driver)

    async def _initialize_schema(self) -> None:
        """Initialize database schema with constraints and indexes."""
        constraints_and_indexes = [
            # User constraints
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            # Topic constraints
            "CREATE CONSTRAINT topic_id_unique IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE",
            # Memory constraints
            "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
            # Experience constraints
            "CREATE CONSTRAINT experience_id_unique IF NOT EXISTS FOR (e:Experience) REQUIRE e.id IS UNIQUE",
            # EmotionContext constraints
            "CREATE CONSTRAINT emotion_id_unique IF NOT EXISTS FOR (ec:EmotionContext) REQUIRE ec.id IS UNIQUE",
            # GlobalFact constraints
            "CREATE CONSTRAINT global_fact_id_unique IF NOT EXISTS FOR (gf:GlobalFact) REQUIRE gf.id IS UNIQUE",
            "CREATE CONSTRAINT global_fact_chromadb_id_unique IF NOT EXISTS FOR (gf:GlobalFact) REQUIRE gf.chromadb_id IS UNIQUE",
            # KnowledgeDomain constraints
            "CREATE CONSTRAINT knowledge_domain_id_unique IF NOT EXISTS FOR (kd:KnowledgeDomain) REQUIRE kd.id IS UNIQUE",
            "CREATE CONSTRAINT knowledge_domain_name_unique IF NOT EXISTS FOR (kd:KnowledgeDomain) REQUIRE kd.name IS UNIQUE",
            # Indexes for better performance
            "CREATE INDEX user_discord_id IF NOT EXISTS FOR (u:User) ON (u.discord_id)",
            "CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name)",
            "CREATE INDEX memory_timestamp IF NOT EXISTS FOR (m:Memory) ON (m.timestamp)",
            "CREATE INDEX emotion_timestamp IF NOT EXISTS FOR (ec:EmotionContext) ON (ec.timestamp)",
            "CREATE INDEX experience_timestamp IF NOT EXISTS FOR (e:Experience) ON (e.timestamp)",
            # Global fact indexes
            "CREATE INDEX global_fact_domain IF NOT EXISTS FOR (gf:GlobalFact) ON (gf.knowledge_domain)",
            "CREATE INDEX global_fact_source IF NOT EXISTS FOR (gf:GlobalFact) ON (gf.source)",
            "CREATE INDEX global_fact_type IF NOT EXISTS FOR (gf:GlobalFact) ON (gf.fact_type)",
            "CREATE INDEX global_fact_confidence IF NOT EXISTS FOR (gf:GlobalFact) ON (gf.confidence_score)",
            "CREATE TEXT INDEX global_fact_content IF NOT EXISTS FOR (gf:GlobalFact) ON (gf.fact_content)",
            "CREATE TEXT INDEX global_fact_tags IF NOT EXISTS FOR (gf:GlobalFact) ON (gf.tags)",
            # Knowledge domain indexes
            "CREATE INDEX knowledge_domain_parent IF NOT EXISTS FOR (kd:KnowledgeDomain) ON (kd.parent_domain)",
            "CREATE INDEX knowledge_domain_depth IF NOT EXISTS FOR (kd:KnowledgeDomain) ON (kd.depth)",
        ]

        for query in constraints_and_indexes:
            try:
                await self.execute_query(query)
                logger.debug(f"Executed schema query: {query}")
            except Exception as e:
                logger.warning(f"Schema query failed (may already exist): {query} - {e}")

    @asynccontextmanager
    async def session(self):
        """Async context manager for Neo4j sessions."""
        if not self._connected or not self._driver:
            await self.connect()

        def get_session():
            return self._driver.session(database=self.config.database)

        session = await asyncio.get_event_loop().run_in_executor(None, get_session)
        try:
            yield session
        finally:
            await asyncio.get_event_loop().run_in_executor(None, session.close)

    async def execute_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return results."""
        if not self._connected:
            await self.connect()

        parameters = parameters or {}

        def run_query(session):
            result = session.run(query, parameters)
            return [record.data() for record in result]

        async with self.session() as session:
            return await asyncio.get_event_loop().run_in_executor(None, run_query, session)

    async def execute_write_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a write query in a transaction."""
        if not self._connected:
            await self.connect()

        parameters = parameters or {}

        def run_write_query(session):
            with session.begin_transaction() as tx:
                result = tx.run(query, parameters)
                records = [record.data() for record in result]
                tx.commit()
                return records

        async with self.session() as session:
            return await asyncio.get_event_loop().run_in_executor(None, run_write_query, session)

    # User Management
    async def create_or_update_user(
        self, user_id: str, discord_id: str, name: str, **properties
    ) -> dict[str, Any]:
        """Create or update a user node."""
        query = """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.created_at = datetime()
        SET u.discord_id = $discord_id,
            u.name = $name,
            u.updated_at = datetime(),
            u += $properties
        RETURN u
        """

        result = await self.execute_write_query(
            query,
            {"user_id": user_id, "discord_id": discord_id, "name": name, "properties": properties},
        )

        return result[0]["u"] if result else {}

    # Topic Management
    async def create_or_update_topic(
        self, topic_id: str, name: str, category: str = "general", **properties
    ) -> dict[str, Any]:
        """Create or update a topic node."""
        query = """
        MERGE (t:Topic {id: $topic_id})
        ON CREATE SET t.created_at = datetime(),
                     t.first_mentioned = datetime()
        ON MATCH SET t.last_mentioned = datetime()
        SET t.name = $name,
            t.category = $category,
            t.updated_at = datetime(),
            t += $properties
        RETURN t
        """

        result = await self.execute_write_query(
            query,
            {"topic_id": topic_id, "name": name, "category": category, "properties": properties},
        )

        return result[0]["t"] if result else {}

    # Memory Management
    async def create_memory_with_relationships(
        self,
        memory_id: str,
        user_id: str,
        chromadb_id: str,
        summary: str,
        topics: list[str],
        emotion_data: dict | None = None,
        importance: float = 0.5,
    ) -> dict[str, Any]:
        """Create a memory node with topic and emotion relationships."""

        # Create memory node
        memory_query = """
        MERGE (m:Memory {id: $memory_id})
        ON CREATE SET m.created_at = datetime()
        SET m.chromadb_id = $chromadb_id,
            m.summary = $summary,
            m.importance = $importance,
            m.timestamp = datetime(),
            m.updated_at = datetime()
        RETURN m
        """

        memory_result = await self.execute_write_query(
            memory_query,
            {
                "memory_id": memory_id,
                "chromadb_id": chromadb_id,
                "summary": summary,
                "importance": importance,
            },
        )

        # Link to user
        user_link_query = """
        MATCH (u:User {id: $user_id}), (m:Memory {id: $memory_id})
        MERGE (u)-[r:REMEMBERS]->(m)
        ON CREATE SET r.created_at = datetime()
        SET r.access_count = COALESCE(r.access_count, 0) + 1,
            r.importance = $importance,
            r.last_accessed = datetime()
        """

        await self.execute_write_query(
            user_link_query, {"user_id": user_id, "memory_id": memory_id, "importance": importance}
        )

        # Link to topics
        for topic in topics:
            topic_link_query = """
            MERGE (t:Topic {name: $topic})
            ON CREATE SET t.id = randomUUID(),
                         t.category = 'auto_detected',
                         t.created_at = datetime(),
                         t.first_mentioned = datetime()
            ON MATCH SET t.last_mentioned = datetime()

            WITH t
            MATCH (m:Memory {id: $memory_id})
            MERGE (m)-[r:ABOUT]->(t)
            SET r.relevance = $relevance,
                r.created_at = COALESCE(r.created_at, datetime())
            """

            await self.execute_write_query(
                topic_link_query,
                {
                    "topic": topic,
                    "memory_id": memory_id,
                    "relevance": 0.8,  # Default relevance score
                },
            )

        # Create emotion context if provided
        if emotion_data:
            emotion_id = f"{memory_id}_emotion_{int(datetime.now().timestamp())}"
            emotion_query = """
            CREATE (ec:EmotionContext {
                id: $emotion_id,
                emotion: $emotion,
                intensity: $intensity,
                trigger_event: $trigger_event,
                timestamp: datetime(),
                resolved: false
            })

            WITH ec
            MATCH (m:Memory {id: $memory_id})
            CREATE (m)-[:EVOKED_EMOTION {strength: $intensity}]->(ec)

            WITH ec
            MATCH (u:User {id: $user_id})
            CREATE (u)-[:EXPERIENCED {
                context: $context,
                intensity: $intensity,
                timestamp: datetime()
            }]->(ec)

            RETURN ec
            """

            await self.execute_write_query(
                emotion_query,
                {
                    "emotion_id": emotion_id,
                    "emotion": emotion_data.get("emotion", "neutral"),
                    "intensity": emotion_data.get("intensity", 0.5),
                    "trigger_event": emotion_data.get("trigger", "conversation"),
                    "context": emotion_data.get("context", "chat"),
                    "memory_id": memory_id,
                    "user_id": user_id,
                },
            )

        return memory_result[0]["m"] if memory_result else {}

    # Relationship Analysis
    async def get_user_relationship_context(self, user_id: str) -> dict[str, Any]:
        """Get comprehensive relationship context for a user."""
        query = """
        MATCH (u:User {id: $user_id})

        // Get interaction history
        OPTIONAL MATCH (u)-[r:REMEMBERS]->(m:Memory)
        WITH u, count(m) as memory_count, avg(m.importance) as avg_importance

        // Get emotional patterns
        OPTIONAL MATCH (u)-[:EXPERIENCED]->(ec:EmotionContext)
        WITH u, memory_count, avg_importance,
             collect(DISTINCT ec.emotion) as experienced_emotions,
             avg(ec.intensity) as avg_emotional_intensity

        // Get topic interests
        OPTIONAL MATCH (u)-[:REMEMBERS]->(m:Memory)-[:ABOUT]->(t:Topic)
        WITH u, memory_count, avg_importance, experienced_emotions, avg_emotional_intensity,
             collect(DISTINCT {name: t.name, category: t.category}) as topics

        // Get relationship milestones
        OPTIONAL MATCH (u)-[rm:RELATIONSHIP_MILESTONE]->(bot:User {id: 'bot'})
        WITH u, memory_count, avg_importance, experienced_emotions, avg_emotional_intensity, topics,
             collect(DISTINCT {level: rm.level, achieved_at: rm.achieved_at}) as milestones

        RETURN {
            user_id: u.id,
            name: u.name,
            memory_count: memory_count,
            avg_importance: avg_importance,
            experienced_emotions: experienced_emotions,
            avg_emotional_intensity: avg_emotional_intensity,
            topics: topics,
            milestones: milestones,
            intimacy_level: CASE
                WHEN memory_count > 100 AND avg_emotional_intensity > 0.7 THEN 0.9
                WHEN memory_count > 50 AND avg_emotional_intensity > 0.5 THEN 0.7
                WHEN memory_count > 20 THEN 0.5
                ELSE 0.3
            END
        } as relationship_context
        """

        result = await self.execute_query(query, {"user_id": user_id})
        return result[0]["relationship_context"] if result else {}

    async def get_emotional_patterns(self, user_id: str) -> dict[str, Any]:
        """Get emotional response patterns for a user."""
        query = """
        MATCH (u:User {id: $user_id})-[:EXPERIENCED]->(ec:EmotionContext)
        <-[:TRIGGERS]-(t:Topic)

        WITH t.name as topic, ec.emotion as emotion,
             avg(ec.intensity) as avg_intensity,
             count(ec) as frequency

        RETURN {
            triggers: collect({
                topic: topic,
                emotion: emotion,
                avg_intensity: avg_intensity,
                frequency: frequency
            })
        } as emotional_patterns
        """

        result = await self.execute_query(query, {"user_id": user_id})
        return result[0]["emotional_patterns"] if result else {"triggers": []}

    async def get_contextual_memories(
        self, user_id: str, topic: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get memories related to a specific topic with emotional context."""
        query = """
        MATCH (u:User {id: $user_id})-[:REMEMBERS]->(m:Memory)-[:ABOUT]->(t:Topic)
        WHERE t.name CONTAINS $topic OR t.category = $topic

        OPTIONAL MATCH (m)-[:EVOKED_EMOTION]->(ec:EmotionContext)

        RETURN {
            memory_id: m.id,
            chromadb_id: m.chromadb_id,
            summary: m.summary,
            importance: m.importance,
            timestamp: m.timestamp,
            topic: t.name,
            topic_category: t.category,
            emotion: ec.emotion,
            emotion_intensity: ec.intensity
        } as memory_context

        ORDER BY m.importance DESC, m.timestamp DESC
        LIMIT $limit
        """

        result = await self.execute_query(
            query, {"user_id": user_id, "topic": topic, "limit": limit}
        )

        return [record["memory_context"] for record in result]

    # Global Facts Management
    async def create_or_update_knowledge_domain(
        self, domain_name: str, description: str = "", parent_domain: str | None = None
    ) -> dict[str, Any]:
        """Create or update a knowledge domain node."""
        # Calculate depth based on parent
        depth = 0
        if parent_domain:
            parent_query = """
            MATCH (parent:KnowledgeDomain {name: $parent_domain})
            RETURN parent.depth as parent_depth
            """
            parent_result = await self.execute_query(parent_query, {"parent_domain": parent_domain})
            if parent_result:
                depth = parent_result[0]["parent_depth"] + 1

        query = """
        MERGE (kd:KnowledgeDomain {name: $domain_name})
        ON CREATE SET kd.id = randomUUID(),
                     kd.created_at = datetime(),
                     kd.fact_count = 0
        SET kd.description = $description,
            kd.parent_domain = $parent_domain,
            kd.depth = $depth,
            kd.updated_at = datetime()
        RETURN kd
        """

        result = await self.execute_write_query(
            query,
            {
                "domain_name": domain_name,
                "description": description,
                "parent_domain": parent_domain,
                "depth": depth,
            },
        )

        # Create parent relationship if specified
        if parent_domain:
            parent_link_query = """
            MATCH (child:KnowledgeDomain {name: $domain_name}),
                  (parent:KnowledgeDomain {name: $parent_domain})
            MERGE (child)-[:BELONGS_TO]->(parent)
            """
            await self.execute_write_query(
                parent_link_query, {"domain_name": domain_name, "parent_domain": parent_domain}
            )

        return result[0]["kd"] if result else {}

    async def store_global_fact(
        self,
        fact_id: str,
        chromadb_id: str,
        fact_content: str,
        knowledge_domain: str = "general",
        confidence_score: float = 0.8,
        source: str = "learned",
        fact_type: str = "declarative",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Store a global fact in the graph database."""
        tags = tags or []

        # Ensure knowledge domain exists
        await self.create_or_update_knowledge_domain(knowledge_domain)

        query = """
        MERGE (gf:GlobalFact {id: $fact_id})
        ON CREATE SET gf.created_at = datetime()
        SET gf.chromadb_id = $chromadb_id,
            gf.fact_content = $fact_content,
            gf.knowledge_domain = $knowledge_domain,
            gf.confidence_score = $confidence_score,
            gf.source = $source,
            gf.fact_type = $fact_type,
            gf.verification_status = 'unverified',
            gf.tags = $tags,
            gf.updated_at = datetime()

        WITH gf
        MATCH (kd:KnowledgeDomain {name: $knowledge_domain})
        MERGE (gf)-[:BELONGS_TO_DOMAIN]->(kd)
        SET kd.fact_count = kd.fact_count + 1

        RETURN gf
        """

        result = await self.execute_write_query(
            query,
            {
                "fact_id": fact_id,
                "chromadb_id": chromadb_id,
                "fact_content": fact_content,
                "knowledge_domain": knowledge_domain,
                "confidence_score": confidence_score,
                "source": source,
                "fact_type": fact_type,
                "tags": tags,
            },
        )

        return result[0]["gf"] if result else {}

    async def create_fact_relationship(
        self,
        from_fact_id: str,
        to_fact_id: str,
        relationship_type: str,
        strength: float = 1.0,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create a relationship between two global facts."""
        properties = properties or {}

        # Build the SET clause for properties
        set_clauses = [
            "r.strength = $strength",
            "r.created_at = COALESCE(r.created_at, datetime())",
            "r.updated_at = datetime()",
        ]

        # Add properties to parameters, but exclude them from SET clause if empty
        params = {"from_fact_id": from_fact_id, "to_fact_id": to_fact_id, "strength": strength}

        # Only add individual properties if they exist
        for key, value in properties.items():
            if value is not None:
                set_clauses.append(f"r.{key} = ${key}")
                params[key] = value

        set_clause = ", ".join(set_clauses)

        query = f"""
        MATCH (from_fact:GlobalFact {{id: $from_fact_id}}),
              (to_fact:GlobalFact {{id: $to_fact_id}})
        MERGE (from_fact)-[r:{relationship_type}]->(to_fact)
        SET {set_clause}
        RETURN r
        """

        result = await self.execute_write_query(query, params)

        return len(result) > 0

    async def get_related_facts(
        self, fact_id: str, relationship_types: list[str] | None = None, max_depth: int = 2
    ) -> list[dict[str, Any]]:
        """Get facts related to a given fact through graph relationships."""
        relationship_filter = ""
        if relationship_types:
            rel_types = "|".join(relationship_types)
            relationship_filter = f":{rel_types}"

        query = f"""
        MATCH (source:GlobalFact {{id: $fact_id}})
        CALL apoc.path.subgraphNodes(source, {{
            relationshipFilter: '{relationship_filter}',
            maxLevel: $max_depth,
            filterStartNode: false
        }})
        YIELD node
        WHERE node <> source AND labels(node)[0] = 'GlobalFact'

        MATCH path = (source)-[r{relationship_filter}*1..{max_depth}]-(node)
        WITH node, relationships(path) as rels, length(path) as distance

        RETURN {{
            fact: node,
            distance: distance,
            relationship_chain: [rel in rels | type(rel)],
            relevance_score: reduce(score = 1.0, rel in rels | score * rel.strength)
        }} as related_fact
        ORDER BY distance ASC, related_fact.relevance_score DESC
        """

        try:
            result = await self.execute_query(query, {"fact_id": fact_id, "max_depth": max_depth})
            return [record["related_fact"] for record in result]
        except Exception as e:
            # Fallback query without APOC procedures
            logger.warning(f"APOC procedures not available, using simple query: {e}")
            simple_query = f"""
            MATCH (source:GlobalFact {{id: $fact_id}})-[r{relationship_filter}]-(related:GlobalFact)
            RETURN {{
                fact: related,
                distance: 1,
                relationship_chain: [type(r)],
                relevance_score: r.strength
            }} as related_fact
            ORDER BY r.strength DESC
            """
            result = await self.execute_query(simple_query, {"fact_id": fact_id})
            return [record["related_fact"] for record in result]

    async def search_facts_by_domain(
        self, knowledge_domain: str, include_subdomain: bool = True, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Search for facts within a knowledge domain."""
        if include_subdomain:
            query = """
            MATCH (kd:KnowledgeDomain)
            WHERE kd.name = $knowledge_domain OR kd.parent_domain = $knowledge_domain
            WITH collect(kd.name) as domain_names

            MATCH (gf:GlobalFact)
            WHERE gf.knowledge_domain IN domain_names
            RETURN gf
            ORDER BY gf.confidence_score DESC, gf.updated_at DESC
            LIMIT $limit
            """
        else:
            query = """
            MATCH (gf:GlobalFact {knowledge_domain: $knowledge_domain})
            RETURN gf
            ORDER BY gf.confidence_score DESC, gf.updated_at DESC
            LIMIT $limit
            """

        result = await self.execute_query(
            query, {"knowledge_domain": knowledge_domain, "limit": limit}
        )

        return [record["gf"] for record in result]

    async def get_fact_by_chromadb_id(self, chromadb_id: str) -> dict[str, Any] | None:
        """Get a global fact by its ChromaDB ID."""
        query = """
        MATCH (gf:GlobalFact {chromadb_id: $chromadb_id})
        RETURN gf
        """

        result = await self.execute_query(query, {"chromadb_id": chromadb_id})
        return result[0]["gf"] if result else None

    async def update_fact_verification(
        self, fact_id: str, verification_status: str, confidence_score: float | None = None
    ) -> bool:
        """Update the verification status and confidence of a fact."""
        set_clause = "gf.verification_status = $verification_status, gf.updated_at = datetime()"
        params: dict[str, Any] = {"fact_id": fact_id, "verification_status": verification_status}

        if confidence_score is not None:
            set_clause += ", gf.confidence_score = $confidence_score"
            params["confidence_score"] = confidence_score

        query = f"""
        MATCH (gf:GlobalFact {{id: $fact_id}})
        SET {set_clause}
        RETURN gf
        """

        result = await self.execute_write_query(query, params)
        return len(result) > 0

    # Health Check
    async def health_check(self) -> dict[str, Any]:
        """Check database health and connection status."""
        try:
            result = await self.execute_query("RETURN 'healthy' as status, datetime() as timestamp")
            node_count = await self.execute_query("MATCH (n) RETURN count(n) as total_nodes")
            relationship_count = await self.execute_query(
                "MATCH ()-[r]->() RETURN count(r) as total_relationships"
            )

            return {
                "status": "healthy",
                "connected": self._connected,
                "timestamp": result[0]["timestamp"] if result else None,
                "total_nodes": node_count[0]["total_nodes"] if node_count else 0,
                "total_relationships": (
                    relationship_count[0]["total_relationships"] if relationship_count else 0
                ),
                "config": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "database": self.config.database,
                },
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "config": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "database": self.config.database,
                },
            }


# Global instance
_neo4j_connector: Neo4jConnector | None = None


async def get_neo4j_connector() -> Neo4jConnector:
    """Get or create the global Neo4j connector instance."""
    global _neo4j_connector

    if _neo4j_connector is None:
        _neo4j_connector = Neo4jConnector()
        await _neo4j_connector.connect()

    return _neo4j_connector


async def close_neo4j_connector():
    """Close the global Neo4j connector."""
    global _neo4j_connector

    if _neo4j_connector:
        await _neo4j_connector.disconnect()
        _neo4j_connector = None
