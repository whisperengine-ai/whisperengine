"""
Unified Datastore Factory for WhisperEngine
Automatically selects and configures appropriate datastore implementations based on deployment mode.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DeploymentMode(Enum):
    """Deployment mode enumeration"""

    CONTAINER = "container"
    DOCKER = "docker"
    CLOUD = "cloud"


@dataclass
class DeploymentInfo:
    """Deployment information"""

    mode: DeploymentMode
    scale_tier: str = "small"
    data_dir: Path = Path("data")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for compatibility"""
        return {
            "mode": self.mode.value,
            "scale_tier": self.scale_tier,
            "data_dir": str(self.data_dir),
        }


# Import availability checks
# Adaptive config is no longer used - simplified to Docker environment variables
ADAPTIVE_CONFIG_AVAILABLE = False
AdaptiveConfigManager = None

try:
    from src.database.database_integration import DatabaseIntegrationManager

    DATABASE_INTEGRATION_AVAILABLE = True
except ImportError:
    DATABASE_INTEGRATION_AVAILABLE = False
    DatabaseIntegrationManager = None

try:
    from src.memory.local_memory_cache import LocalMemoryCacheAdapter

    LOCAL_MEMORY_AVAILABLE = True
except ImportError:
    LOCAL_MEMORY_AVAILABLE = False
    LocalMemoryCacheAdapter = None

try:
    from src.memory.local_vector_storage import LocalVectorStorageAdapter

    LOCAL_VECTOR_AVAILABLE = True
except ImportError:
    LOCAL_VECTOR_AVAILABLE = False
    LocalVectorStorageAdapter = None

# Try to import cloud/production datastores with fallbacks
try:
    # Redis conversation cache disabled for vector-native approach
    # from src.memory.redis_conversation_cache import RedisConversationCache

    REDIS_AVAILABLE = False  # Explicitly disabled
    RedisConversationCache = None  # Explicitly set to None
except ImportError:
    REDIS_AVAILABLE = False
    RedisConversationCache = None

try:
    from src.memory.chromadb_manager_simple import ChromaDBManagerSimple

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    ChromaDBManagerSimple = None

try:
    from src.memory.optimized_adapter import OptimizedMemoryAdapter

    OPTIMIZED_MEMORY_AVAILABLE = True
except ImportError:
    OPTIMIZED_MEMORY_AVAILABLE = False
    OptimizedMemoryAdapter = None

try:
    from src.memory.hybrid_conversation_cache import HybridConversationCache

    HYBRID_CACHE_AVAILABLE = True
except ImportError:
    HYBRID_CACHE_AVAILABLE = False
    HybridConversationCache = None


class DatastoreFactory:
    """
    Factory for creating appropriate datastore implementations based on deployment configuration.

    Automatically selects:
    - SQLite vs PostgreSQL for primary database
    - Local memory cache vs Redis for conversation cache
    - Local vector storage vs ChromaDB for vector operations
    - Local graph storage vs Neo4j for graph operations (optional)
    """

    def __init__(self, deployment_info: DeploymentInfo | None = None):
        """Initialize datastore factory with deployment configuration"""
        if deployment_info is None:
            deployment_info = self._detect_deployment_mode()

        self.deployment_info = deployment_info
        self.deployment_mode = deployment_info.mode
        self.data_dir = deployment_info.data_dir

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize config manager if available
        if ADAPTIVE_CONFIG_AVAILABLE:
            try:
                self.config = AdaptiveConfigManager()
            except Exception:
                self.config = None
        else:
            self.config = None

        logger.info(f"DatastoreFactory initialized for {self.deployment_mode.value} mode")

    def _detect_deployment_mode(self) -> DeploymentInfo:
        """Auto-detect deployment mode from environment"""
        # Check for Docker environment
        if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
            return DeploymentInfo(
                mode=DeploymentMode.DOCKER, scale_tier="medium", data_dir=Path("/app/data")
            )

        # Check for cloud deployment markers
        if os.environ.get("CLOUD_PROVIDER") or os.environ.get("KUBERNETES_SERVICE_HOST"):
            return DeploymentInfo(
                mode=DeploymentMode.CLOUD, scale_tier="large", data_dir=Path("/data")
            )

        # Default to desktop mode
        return DeploymentInfo(
            mode=DeploymentMode.CONTAINER, scale_tier="small", data_dir=Path("data")
        )

    def create_database_manager(self) -> Any:
        """Create and configure database manager based on deployment mode"""
        try:
            if DATABASE_INTEGRATION_AVAILABLE and self.config:
                return DatabaseIntegrationManager(self.config)
            else:
                logger.warning("DatabaseIntegrationManager not available, using fallback")
                return self._create_fallback_database()
        except Exception as e:
            logger.error(f"Failed to create database manager: {e}")
            return self._create_fallback_database()

    def _create_fallback_database(self) -> Any:
        """Create a fallback database implementation"""

        class FallbackDatabase:
            def __init__(self):
                self.connected = False

            async def initialize(self):
                self.connected = True
                return True

            async def close(self):
                self.connected = False

            def get_connection(self):
                return None

        return FallbackDatabase()

    def create_conversation_cache(self) -> Any:
        """Create conversation cache implementation"""
        try:
            # Use fallback memory cache for all deployment modes
            from src.memory.local_memory_cache import LocalMemoryCache

            cache = LocalMemoryCache()
            logger.info("✅ Created fallback conversation cache")
            return cache
        except ImportError:
            # Final fallback to simple in-memory cache
            logger.warning("Using simple fallback conversation cache")
            return None

            # Ultimate fallback - simple in-memory cache
            class BasicMemoryCache:
                def __init__(self):
                    self.conversations = {}

                async def initialize(self):
                    return True

                async def add_message(self, conversation_id: str, message):
                    if conversation_id not in self.conversations:
                        self.conversations[conversation_id] = []
                    self.conversations[conversation_id].append(message)

                async def get_user_conversation_context(
                    self, channel, user_id: int, limit: int = 15, exclude_message_id=None
                ):
                    conv_id = f"conv_{getattr(channel, 'id', 'web')}_{user_id}"
                    messages = self.conversations.get(conv_id, [])
                    return [
                        {"content": str(msg), "author_id": str(user_id), "bot": False}
                        for msg in messages[-limit:]
                    ]

                def clear_channel_cache(self, channel_id: str):
                    keys_to_remove = [k for k in self.conversations.keys() if channel_id in k]
                    for key in keys_to_remove:
                        del self.conversations[key]

                async def get_cache_stats(self):
                    return {"type": "basic_memory", "conversations": len(self.conversations)}

            return BasicMemoryCache()

    def create_vector_storage(self, **kwargs) -> LocalVectorStorageAdapter | Any:
        """Create vector storage based on deployment mode and preferences"""
        vector_type = self.db_config.vector_type

        # Check for explicit ChromaDB preference
        prefer_chromadb = kwargs.get("prefer_chromadb_consistency", False)

        if vector_type == "local_chromadb" and CHROMADB_AVAILABLE and prefer_chromadb:
            # Use ChromaDB PersistentClient for perfect server consistency
            logger.info("Using ChromaDB PersistentClient for consistent API experience")
            chromadb_path = kwargs.get("chromadb_path") or (
                Path.home() / ".whisperengine" / "chromadb"
            )
            return self._create_chromadb_manager(
                "local_chromadb", chromadb_path=chromadb_path, **kwargs
            )

        elif vector_type == "local_chromadb" or not CHROMADB_AVAILABLE:
            # Use local vector storage for desktop mode
            logger.info("Using LocalVectorStorage for local vector operations")
            storage_dir = kwargs.get("storage_dir") or (Path.home() / ".whisperengine" / "vectors")
            return LocalVectorStorageAdapter(
                storage_dir=storage_dir, embedding_dim=kwargs.get("embedding_dim", 384)
            )

        elif vector_type in ["http_chromadb", "distributed_chromadb"] and CHROMADB_AVAILABLE:
            # Use ChromaDB HTTP/distributed for production/cloud mode
            logger.info(f"Using ChromaDB ({vector_type}) for vector operations")
            return self._create_chromadb_manager(vector_type, **kwargs)

        else:
            logger.warning(
                f"Unknown vector type '{vector_type}', falling back to local vector storage"
            )
            storage_dir = kwargs.get("storage_dir") or (Path.home() / ".whisperengine" / "vectors")
            return LocalVectorStorageAdapter(
                storage_dir=storage_dir, embedding_dim=kwargs.get("embedding_dim", 384)
            )

    def _create_chromadb_manager(self, vector_type: str, **kwargs):
        """Create ChromaDB manager based on vector type"""
        if not CHROMADB_AVAILABLE:
            raise RuntimeError(
                "ChromaDB not available but required for vector_type: " + vector_type
            )

        if vector_type == "local_chromadb":
            # Use ChromaDB PersistentClient for local desktop mode
            logger.info("Creating ChromaDB PersistentClient for local storage")
            chromadb_path = kwargs.get("chromadb_path", "./chromadb_data")
            if ChromaDBManagerSimple:
                return ChromaDBManagerSimple(persist_directory=str(chromadb_path))
            else:
                raise RuntimeError("ChromaDBManagerSimple not available for local ChromaDB")

        elif vector_type in ["http_chromadb", "distributed_chromadb"]:
            # Use ChromaDB HTTP client for server/distributed modes
            if OPTIMIZED_MEMORY_AVAILABLE and OptimizedMemoryAdapter and ChromaDBManagerSimple:
                logger.info("Using OptimizedMemoryAdapter for ChromaDB operations")
                return OptimizedMemoryAdapter(chromadb_manager=ChromaDBManagerSimple(), **kwargs)
            elif ChromaDBManagerSimple:
                logger.info("Using ChromaDBManagerSimple for vector operations")
                return ChromaDBManagerSimple()
            else:
                raise RuntimeError("ChromaDB components not available")
        else:
            raise RuntimeError(f"Unknown ChromaDB vector type: {vector_type}")

    def create_memory_manager(self, **kwargs):
        """Create unified memory manager that coordinates all memory systems"""
        try:
            # Create core components
            database_manager = self.create_database_manager()
            conversation_cache = self.create_conversation_cache(**kwargs)
            vector_storage = self.create_vector_storage(**kwargs)

            # Create unified memory manager
            memory_manager = UnifiedMemoryManager(
                database_manager=database_manager,
                conversation_cache=conversation_cache,
                vector_storage=vector_storage,
                config=self.config,
            )

            logger.info("Created unified memory manager with all datastore components")
            return memory_manager

        except Exception as e:
            logger.error(f"Failed to create memory manager: {e}")
            raise

    def get_datastore_info(self) -> dict[str, Any]:
        """Get information about configured datastores"""
        return {
            "deployment_mode": self.deployment_info.mode,
            "scale_tier": self.deployment_info.scale_tier,
            "database_type": self.db_config.primary_type,
            "cache_type": self.db_config.cache_type,
            "vector_type": self.db_config.vector_type,
            "redis_available": REDIS_AVAILABLE,
            "chromadb_available": CHROMADB_AVAILABLE,
            "optimized_memory_available": OPTIMIZED_MEMORY_AVAILABLE,
        }


class UnifiedMemoryManager:
    """
    Unified memory manager that coordinates all memory systems.
    Provides a single interface for memory operations across different backends.
    """

    def __init__(self, database_manager, conversation_cache, vector_storage, config):
        self.database_manager = database_manager
        self.conversation_cache = conversation_cache
        self.vector_storage = vector_storage
        self.config = config

        self._initialized = False

        logger.info("UnifiedMemoryManager created")

    async def initialize(self):
        """Initialize all memory systems"""
        try:
            # Initialize database
            await self.database_manager.initialize()
            logger.info("Database manager initialized")

            # Initialize conversation cache (if async)
            if hasattr(self.conversation_cache, "initialize") and callable(
                self.conversation_cache.initialize
            ):
                await self.conversation_cache.initialize()
                logger.info("Conversation cache initialized")

            # Initialize vector storage (if async)
            if hasattr(self.vector_storage, "initialize") and callable(
                self.vector_storage.initialize
            ):
                await self.vector_storage.initialize()
                logger.info("Vector storage initialized")

            self._initialized = True
            logger.info("UnifiedMemoryManager fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize UnifiedMemoryManager: {e}")
            raise

    async def store_conversation(
        self, user_id: str, message: str, response: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Store conversation in both cache and vector storage"""
        try:
            # Store in conversation cache
            if hasattr(self.conversation_cache, "store_conversation"):
                await self.conversation_cache.store_conversation(
                    user_id, message, response, metadata
                )

            # Store in vector storage (if embeddings are available)
            if hasattr(self.vector_storage, "store_conversation"):
                # This would need embeddings - placeholder for now
                # embeddings = await self._get_embeddings(f"{message} {response}")
                # await self.vector_storage.store_conversation(user_id, message, response, embeddings, metadata)
                pass

            return True

        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            return False

    async def retrieve_conversation_context(self, channel, limit: int = 5, exclude_message_id=None):
        """Retrieve conversation context from cache"""
        try:
            if hasattr(self.conversation_cache, "get_conversation_context"):
                return await self.conversation_cache.get_conversation_context(
                    channel, limit, exclude_message_id
                )
            else:
                logger.warning("Conversation cache does not support get_conversation_context")
                return []
        except Exception as e:
            logger.error(f"Failed to retrieve conversation context: {e}")
            return []

    async def search_memories(
        self, query: str, user_id: str | None = None, limit: int = 10
    ) -> list:
        """Search memories using vector storage"""
        try:
            if hasattr(self.vector_storage, "search_memories"):
                # This would need query embeddings - placeholder for now
                # query_embeddings = await self._get_embeddings(query)
                # return await self.vector_storage.search_memories(query_embeddings, user_id, limit)
                return []
            else:
                logger.warning("Vector storage does not support search_memories")
                return []
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def get_stats(self) -> dict[str, Any]:
        """Get statistics from all memory systems"""
        stats = {}

        try:
            # Database stats
            if hasattr(self.database_manager, "get_stats"):
                stats["database"] = await self.database_manager.get_stats()

            # Cache stats
            if hasattr(self.conversation_cache, "get_stats"):
                cache_stats = await self.conversation_cache.get_stats()
                stats["conversation_cache"] = cache_stats

            # Vector storage stats
            if hasattr(self.vector_storage, "get_stats"):
                vector_stats = await self.vector_storage.get_stats()
                stats["vector_storage"] = vector_stats

            stats["initialized"] = self._initialized

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            stats["error"] = str(e)

        return stats

    async def close(self):
        """Clean shutdown of all memory systems"""
        try:
            if hasattr(self.conversation_cache, "close"):
                await self.conversation_cache.close()

            if hasattr(self.vector_storage, "close"):
                await self.vector_storage.close()

            if hasattr(self.database_manager, "close"):
                await self.database_manager.close()

            logger.info("UnifiedMemoryManager closed successfully")

        except Exception as e:
            logger.error(f"Error during UnifiedMemoryManager shutdown: {e}")


def create_datastore_factory(
    adaptive_config: AdaptiveConfigManager | None = None,
) -> DatastoreFactory:
    """Convenience function to create a datastore factory"""
    return DatastoreFactory(adaptive_config)


def create_memory_manager(adaptive_config: AdaptiveConfigManager | None = None, **kwargs):
    """Convenience function to create a unified memory manager"""
    factory = DatastoreFactory(adaptive_config)
    return factory.create_memory_manager(**kwargs)
