#!/usr/bin/env python3
"""
Local Graph Database - NetworkX + SQLite Hybrid
Replaces Neo4j for local native installations with full graph capabilities.

This implementation provides:
- NetworkX for in-memory graph operations and algorithms
- SQLite for persistent storage
- Neo4j-compatible API interface
- Advanced graph analytics for AI memory systems
"""

import asyncio
import gzip
import json
import logging
import pickle
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Node in the local graph database"""

    id: str
    label: str
    properties: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class GraphEdge:
    """Edge in the local graph database"""

    source_id: str
    target_id: str
    relationship_type: str
    properties: dict[str, Any]
    weight: float = 1.0
    created_at: datetime | None = None


class LocalGraphStorage:
    """
    Local graph database using NetworkX + SQLite for WhisperEngine.

    Provides Neo4j-compatible interface while running entirely locally.

    Features:
    - In-memory NetworkX graph for fast operations
    - SQLite persistence with automatic snapshots
    - Advanced graph algorithms (shortest path, centrality, clustering)
    - User memory relationship tracking
    - Topic and fact relationship networks
    - Emotional pattern analysis
    - Multi-threaded safety
    """

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or (Path.home() / ".whisperengine" / "graph.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # NetworkX graph for in-memory operations
        self.graph = nx.MultiDiGraph()  # Supports multiple edges between nodes

        # Thread safety
        self._lock = threading.RLock()

        # Performance tracking
        self.query_count = 0
        self.last_snapshot = datetime.now()
        self.snapshot_interval = timedelta(minutes=5)  # Auto-snapshot every 5 min

        # Index for fast lookups
        self.node_index = {}  # label -> set of node_ids
        self.edge_index = {}  # relationship_type -> set of (source, target)

        # Initialize
        self._initialize_database()
        self._load_graph_from_db()

        logger.info(f"LocalGraphStorage initialized: {self.db_path}")
        logger.info(
            f"Loaded graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges"
        )

    def _initialize_database(self):
        """Initialize SQLite database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS edges (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source_id) REFERENCES nodes (id),
                    FOREIGN KEY (target_id) REFERENCES nodes (id)
                )
            """
            )

            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_label ON nodes (label)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_type ON edges (relationship_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges (source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges (target_id)")

            # Graph snapshots table (compressed NetworkX data)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS graph_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_data BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    node_count INTEGER,
                    edge_count INTEGER
                )
            """
            )

            conn.commit()

    def _load_graph_from_db(self):
        """Load graph from SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Load nodes
                nodes = conn.execute("SELECT * FROM nodes").fetchall()
                for node in nodes:
                    properties = json.loads(node["properties"])
                    self.graph.add_node(
                        node["id"],
                        label=node["label"],
                        properties=properties,
                        created_at=node["created_at"],
                        updated_at=node["updated_at"],
                    )

                    # Update index
                    if node["label"] not in self.node_index:
                        self.node_index[node["label"]] = set()
                    self.node_index[node["label"]].add(node["id"])

                # Load edges
                edges = conn.execute("SELECT * FROM edges").fetchall()
                for edge in edges:
                    properties = json.loads(edge["properties"])
                    self.graph.add_edge(
                        edge["source_id"],
                        edge["target_id"],
                        key=edge["id"],
                        relationship_type=edge["relationship_type"],
                        properties=properties,
                        weight=edge["weight"],
                        created_at=edge["created_at"],
                    )

                    # Update index
                    if edge["relationship_type"] not in self.edge_index:
                        self.edge_index[edge["relationship_type"]] = set()
                    self.edge_index[edge["relationship_type"]].add(
                        (edge["source_id"], edge["target_id"])
                    )

        except Exception as e:
            logger.warning(f"Failed to load graph from database: {e}")

    async def connect(self) -> None:
        """Establish connection (compatibility with Neo4j interface)"""
        # Already connected via SQLite - just verify
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT 1").fetchone()
            logger.info("Local graph database connected")
        except Exception as e:
            logger.error(f"Failed to connect to local graph database: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect and save snapshot"""
        await self._save_snapshot()
        logger.info("Local graph database disconnected")

    # ========== Node Operations ==========

    async def create_or_update_user(
        self,
        user_id: str,
        discord_id: str,
        username: str = "",
        display_name: str = "",
        avatar_url: str = "",
        **kwargs,
    ) -> dict[str, Any]:
        """Create or update a user node"""
        with self._lock:
            properties = {
                "discord_id": discord_id,
                "username": username,
                "display_name": display_name,
                "avatar_url": avatar_url,
                **kwargs,
            }

            now = datetime.now().isoformat()

            # Update graph
            if self.graph.has_node(user_id):
                # Update existing
                self.graph.nodes[user_id]["properties"].update(properties)
                self.graph.nodes[user_id]["updated_at"] = now
            else:
                # Create new
                self.graph.add_node(
                    user_id, label="User", properties=properties, created_at=now, updated_at=now
                )

                # Update index
                if "User" not in self.node_index:
                    self.node_index["User"] = set()
                self.node_index["User"].add(user_id)

            # Persist to SQLite
            await self._persist_node(user_id, "User", properties, now)

            return {"user_id": user_id, "created": True}

    async def create_or_update_topic(
        self, topic_id: str, name: str, description: str = "", category: str = "", **kwargs
    ) -> dict[str, Any]:
        """Create or update a topic node"""
        with self._lock:
            properties = {"name": name, "description": description, "category": category, **kwargs}

            now = datetime.now().isoformat()

            if self.graph.has_node(topic_id):
                self.graph.nodes[topic_id]["properties"].update(properties)
                self.graph.nodes[topic_id]["updated_at"] = now
            else:
                self.graph.add_node(
                    topic_id, label="Topic", properties=properties, created_at=now, updated_at=now
                )

                if "Topic" not in self.node_index:
                    self.node_index["Topic"] = set()
                self.node_index["Topic"].add(topic_id)

            await self._persist_node(topic_id, "Topic", properties, now)

            return {"topic_id": topic_id, "created": True}

    # ========== Memory and Relationship Operations ==========

    async def create_memory_with_relationships(
        self,
        memory_id: str,
        user_id: str,
        content: str,
        importance: float = 0.5,
        emotional_context: str = "",
        topics: list[str] | None = None,
        related_memories: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create memory node with relationships"""
        with self._lock:
            # Create memory node
            properties = {
                "content": content,
                "importance": importance,
                "emotional_context": emotional_context,
                **kwargs,
            }

            now = datetime.now().isoformat()

            self.graph.add_node(
                memory_id, label="Memory", properties=properties, created_at=now, updated_at=now
            )

            if "Memory" not in self.node_index:
                self.node_index["Memory"] = set()
            self.node_index["Memory"].add(memory_id)

            # Create relationship to user
            await self._create_relationship(
                user_id, memory_id, "HAS_MEMORY", {"importance": importance, "created_at": now}
            )

            # Create topic relationships
            for topic_id in topics or []:
                await self._create_relationship(
                    memory_id, topic_id, "RELATES_TO", {"relevance": 1.0, "created_at": now}
                )

            # Create memory-to-memory relationships
            for related_memory_id in related_memories or []:
                if self.graph.has_node(related_memory_id):
                    await self._create_relationship(
                        memory_id,
                        related_memory_id,
                        "RELATED_TO",
                        {"strength": 0.8, "created_at": now},
                    )

            await self._persist_node(memory_id, "Memory", properties, now)

            return {
                "memory_id": memory_id,
                "relationships_created": len(topics or []) + len(related_memories or []) + 1,
            }

    async def _create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: dict[str, Any],
        weight: float = 1.0,
    ) -> str:
        """Create relationship between nodes"""
        edge_id = f"{source_id}_{relationship_type}_{target_id}_{hash(json.dumps(properties, sort_keys=True)) % 10000}"

        # Add to graph
        self.graph.add_edge(
            source_id,
            target_id,
            key=edge_id,
            relationship_type=relationship_type,
            properties=properties,
            weight=weight,
            created_at=datetime.now().isoformat(),
        )

        # Update index
        if relationship_type not in self.edge_index:
            self.edge_index[relationship_type] = set()
        self.edge_index[relationship_type].add((source_id, target_id))

        # Persist to SQLite
        await self._persist_edge(
            edge_id, source_id, target_id, relationship_type, properties, weight
        )

        return edge_id

    # ========== Advanced Graph Analytics ==========

    async def get_user_relationship_context(self, user_id: str) -> dict[str, Any]:
        """Get comprehensive relationship context for user"""
        with self._lock:
            if not self.graph.has_node(user_id):
                return {}

            # Get all connected nodes
            connected_nodes = list(self.graph.neighbors(user_id))

            # Analyze memory patterns
            memories = [
                node
                for node in connected_nodes
                if self.graph.nodes.get(node, {}).get("label") == "Memory"
            ]

            # Topic analysis
            topics = set()
            for memory in memories:
                topic_neighbors = [
                    n
                    for n in self.graph.neighbors(memory)
                    if self.graph.nodes.get(n, {}).get("label") == "Topic"
                ]
                topics.update(topic_neighbors)

            # Calculate relationship strengths using PageRank
            try:
                centrality = nx.pagerank(self.graph)
                user_centrality = centrality.get(user_id, 0)
            except:
                user_centrality = 0

            # Recent activity
            recent_memories = []
            for memory in memories:
                created_at = self.graph.nodes[memory].get("created_at", "")
                try:
                    created_time = datetime.fromisoformat(created_at)
                    if datetime.now() - created_time < timedelta(days=30):
                        recent_memories.append(memory)
                except:
                    pass

            return {
                "user_id": user_id,
                "total_memories": len(memories),
                "recent_memories": len(recent_memories),
                "connected_topics": len(topics),
                "centrality_score": user_centrality,
                "relationship_strength": len(connected_nodes),
                "memory_ids": memories[:10],  # Limit for performance
                "topic_ids": list(topics)[:10],
            }

    async def get_contextual_memories(
        self, user_id: str, topic: str, max_depth: int = 2, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get memories related to user and topic using graph traversal"""
        with self._lock:
            if not self.graph.has_node(user_id):
                return []

            # Find topic nodes matching the query
            topic_nodes = []
            for node_id in self.node_index.get("Topic", set()):
                topic_name = self.graph.nodes[node_id]["properties"].get("name", "").lower()
                if topic.lower() in topic_name:
                    topic_nodes.append(node_id)

            # Find memories connected to both user and topics
            contextual_memories = []

            for topic_node in topic_nodes:
                try:
                    # Find shortest paths from user to topic through memories
                    paths = nx.all_simple_paths(self.graph, user_id, topic_node, cutoff=max_depth)

                    for path in paths:
                        # Extract memory nodes from path
                        for node in path:
                            if self.graph.nodes.get(node, {}).get(
                                "label"
                            ) == "Memory" and node not in [
                                m["memory_id"] for m in contextual_memories
                            ]:

                                memory_data = {
                                    "memory_id": node,
                                    "content": self.graph.nodes[node]["properties"].get(
                                        "content", ""
                                    ),
                                    "importance": self.graph.nodes[node]["properties"].get(
                                        "importance", 0.5
                                    ),
                                    "path_length": len(path) - 1,
                                    "topic_relevance": 1.0 / len(path),  # Closer = more relevant
                                }
                                contextual_memories.append(memory_data)

                                if len(contextual_memories) >= limit:
                                    break

                        if len(contextual_memories) >= limit:
                            break
                except nx.NetworkXNoPath:
                    continue

            # Sort by relevance
            contextual_memories.sort(key=lambda x: x["topic_relevance"], reverse=True)

            return contextual_memories[:limit]

    async def get_emotional_patterns(self, user_id: str) -> dict[str, Any]:
        """Analyze emotional patterns using graph connections"""
        with self._lock:
            if not self.graph.has_node(user_id):
                return {}

            # Get all user memories
            user_memories = []
            for neighbor in self.graph.neighbors(user_id):
                if self.graph.nodes.get(neighbor, {}).get("label") == "Memory":
                    user_memories.append(neighbor)

            # Analyze emotional contexts
            emotional_data = {}
            emotion_counts = {}

            for memory in user_memories:
                emotional_context = self.graph.nodes[memory]["properties"].get(
                    "emotional_context", ""
                )
                importance = self.graph.nodes[memory]["properties"].get("importance", 0.5)

                if emotional_context:
                    emotion_counts[emotional_context] = emotion_counts.get(emotional_context, 0) + 1

                    if emotional_context not in emotional_data:
                        emotional_data[emotional_context] = {
                            "count": 0,
                            "total_importance": 0,
                            "memories": [],
                        }

                    emotional_data[emotional_context]["count"] += 1
                    emotional_data[emotional_context]["total_importance"] += importance
                    emotional_data[emotional_context]["memories"].append(memory)

            # Calculate patterns
            patterns = {}
            total_memories = len(user_memories)

            for emotion, data in emotional_data.items():
                patterns[emotion] = {
                    "frequency": data["count"] / total_memories if total_memories > 0 else 0,
                    "average_importance": data["total_importance"] / data["count"],
                    "memory_count": data["count"],
                }

            return {
                "user_id": user_id,
                "total_memories_analyzed": total_memories,
                "emotional_patterns": patterns,
                "dominant_emotion": (
                    max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None
                ),
            }

    # ========== Persistence Methods ==========

    async def _persist_node(
        self, node_id: str, label: str, properties: dict[str, Any], timestamp: str
    ):
        """Persist node to SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO nodes (id, label, properties, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (node_id, label, json.dumps(properties), timestamp, timestamp),
            )
            conn.commit()

    async def _persist_edge(
        self,
        edge_id: str,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: dict[str, Any],
        weight: float,
    ):
        """Persist edge to SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO edges (id, source_id, target_id, relationship_type, properties, weight, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    edge_id,
                    source_id,
                    target_id,
                    relationship_type,
                    json.dumps(properties),
                    weight,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()

    async def _save_snapshot(self):
        """Save compressed NetworkX graph snapshot"""
        try:
            # Serialize graph
            graph_data = nx.node_link_data(self.graph)
            serialized = pickle.dumps(graph_data)
            compressed = gzip.compress(serialized)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO graph_snapshots (snapshot_data, created_at, node_count, edge_count)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        compressed,
                        datetime.now().isoformat(),
                        self.graph.number_of_nodes(),
                        self.graph.number_of_edges(),
                    ),
                )

                # Keep only last 10 snapshots
                conn.execute(
                    """
                    DELETE FROM graph_snapshots
                    WHERE id NOT IN (
                        SELECT id FROM graph_snapshots
                        ORDER BY created_at DESC
                        LIMIT 10
                    )
                """
                )
                conn.commit()

            self.last_snapshot = datetime.now()
            logger.debug("Graph snapshot saved")

        except Exception as e:
            logger.warning(f"Failed to save graph snapshot: {e}")

    # ========== Health and Statistics ==========

    async def health_check(self) -> dict[str, Any]:
        """Get database health and statistics"""
        with self._lock:
            # Graph statistics
            node_count = self.graph.number_of_nodes()
            edge_count = self.graph.number_of_edges()

            # Node type breakdown
            node_types = {}
            for node_id in self.graph.nodes():
                label = self.graph.nodes[node_id].get("label", "Unknown")
                node_types[label] = node_types.get(label, 0) + 1

            # Edge type breakdown
            edge_types = {}
            for _, _, data in self.graph.edges(data=True):
                rel_type = data.get("relationship_type", "Unknown")
                edge_types[rel_type] = edge_types.get(rel_type, 0) + 1

            # Database file size
            db_size_mb = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0

            return {
                "status": "healthy",
                "database_type": "local_graph_networkx",
                "database_path": str(self.db_path),
                "database_size_mb": round(db_size_mb, 2),
                "graph_statistics": {
                    "nodes": node_count,
                    "edges": edge_count,
                    "node_types": node_types,
                    "edge_types": edge_types,
                },
                "performance": {
                    "query_count": self.query_count,
                    "last_snapshot": self.last_snapshot.isoformat(),
                    "index_sizes": {k: len(v) for k, v in self.node_index.items()},
                },
            }

    # ========== Neo4j Compatibility Methods ==========

    async def execute_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a Cypher-like query (limited compatibility)"""
        # This is a simplified compatibility layer
        # For complex queries, use the specific methods above
        self.query_count += 1

        # Basic query parsing for common patterns
        query = query.strip().upper()

        if query.startswith("MATCH") and "RETURN" in query:
            # Simple node matching
            if "(u:User)" in query:
                users = []
                for node_id in self.node_index.get("User", set()):
                    node_data = self.graph.nodes[node_id]
                    users.append(
                        {
                            "u": {
                                "id": node_id,
                                "label": node_data["label"],
                                "properties": node_data["properties"],
                            }
                        }
                    )
                return users

        logger.warning(f"Query not implemented in compatibility layer: {query}")
        return []

    async def execute_write_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a write query (limited compatibility)"""
        return await self.execute_query(query, parameters)


# ========== Factory Function ==========


def create_local_graph_storage(db_path: Path | None = None) -> LocalGraphStorage:
    """Factory function to create local graph storage"""
    return LocalGraphStorage(db_path)


# ========== Example Usage ==========


async def example_usage():
    """Example of how to use LocalGraphStorage"""

    # Initialize
    graph_db = LocalGraphStorage()
    await graph_db.connect()

    # Create user
    await graph_db.create_or_update_user(
        user_id="user_123",
        discord_id="123456789",
        username="alice",
        display_name="Alice Wonderland",
    )

    # Create topics
    await graph_db.create_or_update_topic(
        topic_id="topic_ai",
        name="Artificial Intelligence",
        description="AI and machine learning discussions",
    )

    # Create memory with relationships
    await graph_db.create_memory_with_relationships(
        memory_id="memory_001",
        user_id="user_123",
        content="Discussed neural networks and their applications",
        importance=0.8,
        emotional_context="curious",
        topics=["topic_ai"],
    )

    # Get user context
    await graph_db.get_user_relationship_context("user_123")

    # Get contextual memories
    await graph_db.get_contextual_memories("user_123", "AI")

    # Health check
    await graph_db.health_check()

    await graph_db.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())
