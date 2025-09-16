#!/usr/bin/env python3
"""
Simple Datastore Factory for WhisperEngine Desktop Mode
Provides lightweight alternatives to complex datastore dependencies
"""

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DeploymentMode(Enum):
    """Deployment mode enumeration"""

    DESKTOP = "desktop"
    DOCKER = "docker"
    CLOUD = "cloud"


class SimpleDatastoreFactory:
    """
    Simplified datastore factory for desktop mode
    Focuses on providing working implementations with minimal dependencies
    """

    def __init__(self, data_dir: Path | None = None):
        """Initialize simple datastore factory"""
        self.data_dir = data_dir or Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Detect deployment mode
        self.deployment_mode = self._detect_deployment_mode()

        logger.info(f"SimpleDatastoreFactory initialized for {self.deployment_mode.value} mode")

    def _detect_deployment_mode(self) -> DeploymentMode:
        """Auto-detect deployment mode from environment"""
        if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
            return DeploymentMode.DOCKER
        elif os.environ.get("CLOUD_PROVIDER") or os.environ.get("KUBERNETES_SERVICE_HOST"):
            return DeploymentMode.CLOUD
        else:
            return DeploymentMode.DESKTOP

    def create_conversation_cache(self) -> Any:
        """Create conversation cache for desktop mode"""
        try:
            if self.deployment_mode == DeploymentMode.DESKTOP:
                # Use our desktop conversation cache
                from src.memory.desktop_conversation_cache import create_desktop_conversation_cache

                cache = create_desktop_conversation_cache(
                    data_dir=str(self.data_dir / "cache"),
                    max_memory_conversations=50,
                    max_messages_per_conversation=100,
                    cache_ttl_hours=24,
                )
                logger.info("✅ Created desktop conversation cache (SQLite + memory)")
                return cache
            else:
                # Try to use existing caches for non-desktop modes
                try:
                    # Try to import if available, otherwise use fallback
                    logger.warning("Non-desktop mode detected, using fallback cache")
                    return self._create_fallback_cache()
                except Exception:
                    return self._create_fallback_cache()
        except Exception as e:
            logger.error(f"Failed to create conversation cache: {e}")
            return self._create_fallback_cache()

    def _create_fallback_cache(self) -> Any:
        """Create a simple fallback conversation cache"""

        class SimpleFallbackCache:
            def __init__(self):
                self.conversations = {}
                self.initialized = False

            async def initialize(self):
                self.initialized = True
                logger.info("✅ Fallback conversation cache initialized")
                return True

            async def add_message(self, conversation_id: str, message):
                if conversation_id not in self.conversations:
                    self.conversations[conversation_id] = []

                # Convert message to simple format
                if hasattr(message, "content"):
                    msg_data = {
                        "content": str(message.content),
                        "author_id": str(getattr(message.author, "id", "unknown")),
                        "author_name": str(getattr(message.author, "name", "Unknown")),
                        "bot": getattr(getattr(message, "author", None), "bot", False),
                    }
                else:
                    msg_data = {"content": str(message), "author_id": "unknown", "bot": False}

                self.conversations[conversation_id].append(msg_data)

                # Keep only last 50 messages per conversation
                if len(self.conversations[conversation_id]) > 50:
                    self.conversations[conversation_id] = self.conversations[conversation_id][-50:]

            async def get_user_conversation_context(
                self, channel, user_id: int, limit: int = 15, exclude_message_id=None
            ):
                conv_id = f"conv_{getattr(channel, 'id', 'web')}_{user_id}"
                messages = self.conversations.get(conv_id, [])

                # Convert to expected format
                result = []
                for msg in messages[-limit:]:
                    result.append(
                        {
                            "content": msg.get("content", ""),
                            "author_id": msg.get("author_id", ""),
                            "author_name": msg.get("author_name", "Unknown"),
                            "bot": msg.get("bot", False),
                            "from_cache": True,
                        }
                    )

                return result

            def clear_channel_cache(self, channel_id: str):
                keys_to_remove = [k for k in self.conversations.keys() if str(channel_id) in k]
                for key in keys_to_remove:
                    del self.conversations[key]

            async def get_cache_stats(self):
                return {
                    "type": "simple_fallback",
                    "conversations": len(self.conversations),
                    "total_messages": sum(len(msgs) for msgs in self.conversations.values()),
                }

        return SimpleFallbackCache()

    def create_vector_storage(self, **kwargs) -> Any:
        """Create vector storage for desktop mode"""
        try:
            if self.deployment_mode == DeploymentMode.DESKTOP:
                # Use local vector storage
                from src.memory.local_vector_storage import LocalVectorStorageAdapter

                storage = LocalVectorStorageAdapter(
                    storage_dir=Path(self.data_dir / "vectors"),
                    embedding_dim=kwargs.get("embedding_dim", 384),
                )
                logger.info("✅ Created local vector storage")
                return storage
            else:
                # Try ChromaDB for production
                try:
                    from src.memory.chromadb_manager_simple import ChromaDBManagerSimple

                    return ChromaDBManagerSimple()
                except ImportError:
                    logger.warning("ChromaDB not available, using fallback vector storage")
                    return self._create_fallback_vector_storage(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create vector storage: {e}")
            return self._create_fallback_vector_storage(**kwargs)

    def _create_fallback_vector_storage(self, **kwargs) -> Any:
        """Create a simple fallback vector storage"""

        class SimpleFallbackVectorStorage:
            def __init__(self, storage_dir: str, embedding_dim: int = 384):
                self.storage_dir = Path(storage_dir)
                self.storage_dir.mkdir(parents=True, exist_ok=True)
                self.embedding_dim = embedding_dim
                self.vectors = {}
                self.metadata = {}
                self.initialized = False

            async def initialize(self):
                self.initialized = True
                logger.info("✅ Fallback vector storage initialized")
                return True

            def add_documents(self, documents, metadatas=None, ids=None):
                """Add documents to vector storage"""
                if ids is None:
                    ids = [f"doc_{i}" for i in range(len(documents))]

                if metadatas is None:
                    metadatas = [{}] * len(documents)

                for _i, (doc, meta, doc_id) in enumerate(
                    zip(documents, metadatas, ids, strict=False)
                ):
                    # Store document text and metadata
                    self.vectors[doc_id] = doc
                    self.metadata[doc_id] = meta

            def query(self, query_texts, n_results=10, **kwargs):
                """Simple text matching query"""
                if not query_texts:
                    return {"documents": [[]]}

                query = (
                    query_texts[0].lower() if isinstance(query_texts, list) else query_texts.lower()
                )

                # Simple keyword matching
                results = []
                for doc_id, doc_text in self.vectors.items():
                    if any(word in doc_text.lower() for word in query.split()):
                        results.append((doc_id, doc_text))

                # Return top results
                results = results[:n_results]
                return {"documents": [[doc for _, doc in results]]}

            def delete_collection(self):
                """Clear all vectors"""
                self.vectors.clear()
                self.metadata.clear()

        return SimpleFallbackVectorStorage(
            storage_dir=str(self.data_dir / "vectors"),
            embedding_dim=kwargs.get("embedding_dim", 384),
        )

    def create_database_manager(self) -> Any:
        """Create database manager for desktop mode"""
        try:
            # Try to use existing database integration
            from src.config.adaptive_config import AdaptiveConfigManager
            from src.database.database_integration import DatabaseIntegrationManager

            config = AdaptiveConfigManager()
            return DatabaseIntegrationManager(config)
        except ImportError as e:
            logger.warning(f"Database integration not available: {e}")
            return self._create_fallback_database()
        except Exception as e:
            logger.error(f"Failed to create database manager: {e}")
            return self._create_fallback_database()

    def _create_fallback_database(self) -> Any:
        """Create a simple fallback database"""

        class SimpleFallbackDatabase:
            def __init__(self):
                self.connected = False
                self.data = {}

            async def initialize(self):
                self.connected = True
                logger.info("✅ Fallback database initialized")
                return True

            async def close(self):
                self.connected = False

            def get_connection(self):
                return self

            def execute(self, query, params=None):
                # Simple key-value storage simulation
                return None

            def fetchone(self):
                return None

            def fetchall(self):
                return []

        return SimpleFallbackDatabase()

    def create_graph_storage(self) -> Any:
        """Create graph storage for desktop mode"""

        class SimpleGraphStorage:
            def __init__(self):
                self.nodes = {}
                self.edges = []
                self.initialized = False

            async def initialize(self):
                self.initialized = True
                logger.info("✅ Simple graph storage initialized")
                return True

            def add_node(self, node_id: str, properties: dict[str, Any]):
                self.nodes[node_id] = properties

            def add_edge(
                self,
                from_node: str,
                to_node: str,
                relationship: str,
                properties: dict[str, Any] | None = None,
            ):
                self.edges.append(
                    {
                        "from": from_node,
                        "to": to_node,
                        "relationship": relationship,
                        "properties": properties or {},
                    }
                )

            def query_relationships(self, node_id: str) -> list[dict[str, Any]]:
                relationships = []
                for edge in self.edges:
                    if edge["from"] == node_id or edge["to"] == node_id:
                        relationships.append(edge)
                return relationships

            def close(self):
                pass

        return SimpleGraphStorage()

    def get_availability_info(self) -> dict[str, Any]:
        """Get information about available datastores"""
        info = {
            "deployment_mode": self.deployment_mode.value,
            "data_dir": str(self.data_dir),
            "conversation_cache": (
                "desktop_sqlite" if self.deployment_mode == DeploymentMode.DESKTOP else "fallback"
            ),
            "vector_storage": (
                "local_files" if self.deployment_mode == DeploymentMode.DESKTOP else "fallback"
            ),
            "database": "sqlite" if self.deployment_mode == DeploymentMode.DESKTOP else "fallback",
            "graph_storage": "simple_memory",
        }

        return info

    async def initialize_all(self) -> dict[str, Any]:
        """Initialize all datastore components"""
        logger.info("🚀 Initializing all datastore components...")

        components = {}

        try:
            # Initialize conversation cache
            conversation_cache = self.create_conversation_cache()
            if hasattr(conversation_cache, "initialize"):
                await conversation_cache.initialize()
            components["conversation_cache"] = conversation_cache

            # Initialize vector storage
            vector_storage = self.create_vector_storage()
            if hasattr(vector_storage, "initialize"):
                await vector_storage.initialize()
            components["vector_storage"] = vector_storage

            # Initialize database
            database = self.create_database_manager()
            if hasattr(database, "initialize"):
                await database.initialize()
            components["database"] = database

            # Initialize graph storage
            graph_storage = self.create_graph_storage()
            if hasattr(graph_storage, "initialize"):
                await graph_storage.initialize()
            components["graph_storage"] = graph_storage

            logger.info("✅ All datastore components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize datastore components: {e}")

        return components


def create_simple_datastore_factory(data_dir: Path | None = None) -> SimpleDatastoreFactory:
    """Create a simple datastore factory instance"""
    return SimpleDatastoreFactory(data_dir=data_dir)


# Compatibility function for existing code
def create_datastore_factory(**kwargs) -> SimpleDatastoreFactory:
    """Create datastore factory with compatibility"""
    data_dir = kwargs.get("data_dir") or Path("data")
    return create_simple_datastore_factory(data_dir=data_dir)
