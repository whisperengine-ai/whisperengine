#!/usr/bin/env python3
"""
ChromaDB Local Database Integration Manager
Provides consistent ChromaDB experience across desktop and server deployments.

This manager uses ChromaDB PersistentClient for local desktop installations,
ensuring perfect API consistency with server deployments while maintaining
local data control and privacy.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import (
    WhisperEngineDatabaseConfig,
    DatabaseIntegrationManager,
)
from src.memory.chromadb_manager_simple import ChromaDBManagerSimple
from src.graph_database.local_graph_storage import LocalGraphStorage
from src.memory.desktop_conversation_cache import DesktopConversationCache

logger = logging.getLogger(__name__)


class ChromaDBLocalDatabaseManager(DatabaseIntegrationManager):
    """
    Database integration manager using ChromaDB PersistentClient for local installations.

    Provides perfect consistency with server deployments:
    - ChromaDB PersistentClient for vector storage
    - Same API surface as HTTP ChromaDB deployments
    - Seamless migration between desktop ↔ server
    - Local graph storage for relationships (Neo4j replacement)
    - Local cache for session data (Redis replacement)
    """

    def __init__(self, config_manager: AdaptiveConfigManager):
        super().__init__(config_manager)

        # ChromaDB local storage
        self.chromadb_manager: Optional[ChromaDBManagerSimple] = None
        self.graph_storage: Optional[LocalGraphStorage] = None
        self.local_cache: Optional[DesktopConversationCache] = None

        # Storage paths
        self.data_dir = Path.home() / ".whisperengine"
        self.chromadb_path = self.data_dir / "chromadb"
        self.graph_db_path = self.data_dir / "graph.db"
        self.cache_dir = self.data_dir / "cache"

        # Ensure directories exist
        for directory in [self.data_dir, self.chromadb_path, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        logger.info("ChromaDBLocalDatabaseManager initialized")

    async def initialize(self) -> bool:
        """Initialize all database components with ChromaDB consistency"""
        try:
            # Initialize base SQL database
            base_init_success = await super().initialize()
            if not base_init_success:
                logger.error("Failed to initialize base database")
                return False

            # Initialize ChromaDB PersistentClient (same API as server deployments)
            logger.info("🔍 Initializing ChromaDB PersistentClient for local storage...")
            self.chromadb_manager = ChromaDBManagerSimple(persist_directory=str(self.chromadb_path))

            # Initialize graph storage (Neo4j replacement)
            logger.info("🕸️ Initializing local graph storage...")
            self.graph_storage = LocalGraphStorage(db_path=self.graph_db_path)
            await self.graph_storage.connect()

            # Initialize local cache (Redis replacement)
            logger.info("💾 Initializing local conversation cache...")
            self.local_cache = DesktopConversationCache()

            # Create default collections if they don't exist
            await self._ensure_default_collections()

            logger.info("✅ All ChromaDB local database components initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB local database components: {e}")
            return False

    async def _ensure_default_collections(self):
        """Ensure default ChromaDB collections exist"""
        try:
            if not self.chromadb_manager:
                logger.error("ChromaDB manager not initialized")
                return

            # Create default collections if they don't exist
            collection_names = ["user_memories", "global_facts"]

            for collection_name in collection_names:
                try:
                    # Try to get the collection first
                    collection = self.chromadb_manager.client.get_collection(name=collection_name)
                    logger.info(f"✅ Collection '{collection_name}' already exists")
                except Exception:
                    # Collection doesn't exist, create it
                    try:
                        collection = self.chromadb_manager.client.create_collection(
                            name=collection_name
                        )
                        logger.info(f"✅ Created collection '{collection_name}'")

                        # Update manager references
                        if collection_name == "user_memories":
                            self.chromadb_manager.user_collection = collection
                        elif collection_name == "global_facts":
                            self.chromadb_manager.global_collection = collection

                    except Exception as e:
                        logger.error(f"Failed to create collection '{collection_name}': {e}")

            # Test connection after collection setup
            self.chromadb_manager.client.heartbeat()
            logger.info("✅ ChromaDB collections ready")

        except Exception as e:
            logger.warning(f"Failed to setup ChromaDB collections: {e}")

    # ========== ChromaDB Interface ==========

    def get_chromadb_manager(self) -> ChromaDBManagerSimple:
        """Get the ChromaDB manager instance"""
        if not self.chromadb_manager:
            raise RuntimeError("ChromaDB manager not initialized")
        return self.chromadb_manager

    async def store_conversation(
        self, user_id: str, message: str, response: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store conversation using ChromaDB (same API as server deployments)"""
        try:
            if not self.chromadb_manager:
                raise RuntimeError("ChromaDB manager not initialized")

            # Use ChromaDB manager's store method (maintains consistency with server)
            # Note: ChromaDBManagerSimple needs async wrapper or we need to modify this
            # For now, using sync call (consistent with existing ChromaDB usage)

            # Create document content (standard format)
            document_content = f"User: {message}\nAssistant: {response}"

            # Prepare metadata (standard format)
            doc_metadata = {
                "doc_type": "conversation",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "source": "desktop",
                "message_content": message,
                "response_content": response,
                **(metadata or {}),
            }

            # Generate unique ID
            import hashlib

            content_hash = hashlib.sha256(f"{message}{response}".encode()).hexdigest()[:12]
            doc_id = f"conversation_{user_id}_{content_hash}"

            # Store in ChromaDB using standard collection
            if self.chromadb_manager.user_collection:
                self.chromadb_manager.user_collection.add(
                    documents=[document_content], metadatas=[doc_metadata], ids=[doc_id]
                )
            else:
                logger.error("User collection not available in ChromaDB manager")
                raise RuntimeError("ChromaDB user collection not initialized")

            logger.debug(f"Stored conversation in ChromaDB: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store conversation in ChromaDB: {e}")
            raise

    async def search_conversations(
        self, user_id: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search conversations using ChromaDB semantic search"""
        try:
            if not self.chromadb_manager or not self.chromadb_manager.user_collection:
                raise RuntimeError("ChromaDB not initialized")

            # Query ChromaDB (this would need embedding generation)
            # For now, implementing basic search - would need embedding manager integration
            results = self.chromadb_manager.user_collection.query(
                query_texts=[query], n_results=limit, where={"user_id": user_id}
            )

            # Format results (same structure as server deployments)
            conversations = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = (
                        results["metadatas"][0][i]
                        if results["metadatas"] and results["metadatas"][0]
                        else {}
                    )
                    conversations.append(
                        {
                            "id": results["ids"][0][i],
                            "content": doc,
                            "metadata": metadata,
                            "distance": (
                                results["distances"][0][i] if results.get("distances") else 0.0
                            ),
                        }
                    )

            return conversations

        except Exception as e:
            logger.error(f"Failed to search conversations in ChromaDB: {e}")
            return []

    # ========== Graph Storage Interface (Neo4j replacement) ==========

    def get_graph_storage(self) -> LocalGraphStorage:
        """Get the local graph storage instance"""
        if not self.graph_storage:
            raise RuntimeError("Graph storage not initialized")
        return self.graph_storage

    # ========== Cache Interface (Redis replacement) ==========

    def get_cache(self) -> DesktopConversationCache:
        """Get the local cache instance"""
        if not self.local_cache:
            raise RuntimeError("Local cache not initialized")
        return self.local_cache

    # ========== Health and Statistics ==========

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all local database components"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "overall_healthy": True,
            "components": {},
        }

        try:
            # Check ChromaDB
            if self.chromadb_manager:
                try:
                    self.chromadb_manager.client.heartbeat()
                    status["components"]["chromadb"] = {
                        "healthy": True,
                        "storage_path": str(self.chromadb_path),
                        "collections": {
                            "user_collection": self.chromadb_manager.user_collection is not None,
                            "global_collection": self.chromadb_manager.global_collection
                            is not None,
                        },
                    }
                except Exception as e:
                    status["components"]["chromadb"] = {"healthy": False, "error": str(e)}
                    status["overall_healthy"] = False
            else:
                status["components"]["chromadb"] = {"healthy": False, "error": "Not initialized"}
                status["overall_healthy"] = False

            # Check graph storage
            if self.graph_storage:
                graph_stats = await self.graph_storage.get_stats()
                status["components"]["graph"] = {"healthy": True, "stats": graph_stats}
            else:
                status["components"]["graph"] = {"healthy": False, "error": "Not initialized"}
                status["overall_healthy"] = False

            # Check cache
            if self.local_cache:
                cache_stats = await self.local_cache.get_stats()
                status["components"]["cache"] = {"healthy": True, "stats": cache_stats}
            else:
                status["components"]["cache"] = {"healthy": False, "error": "Not initialized"}
                status["overall_healthy"] = False

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            status["overall_healthy"] = False
            status["error"] = str(e)

        return status

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get detailed storage statistics"""
        stats = {"timestamp": datetime.now().isoformat(), "chromadb": {}, "graph": {}, "cache": {}}

        try:
            # ChromaDB stats
            if self.chromadb_manager:
                # Get collection counts (if collections exist)
                try:
                    user_count = 0
                    global_count = 0

                    if self.chromadb_manager.user_collection:
                        user_result = self.chromadb_manager.user_collection.count()
                        user_count = user_result if isinstance(user_result, int) else 0

                    if self.chromadb_manager.global_collection:
                        global_result = self.chromadb_manager.global_collection.count()
                        global_count = global_result if isinstance(global_result, int) else 0

                    stats["chromadb"] = {
                        "user_memories": user_count,
                        "global_facts": global_count,
                        "storage_path": str(self.chromadb_path),
                    }
                except Exception as e:
                    stats["chromadb"] = {"error": f"Failed to get collection counts: {e}"}

            # Graph stats
            if self.graph_storage:
                stats["graph"] = await self.graph_storage.get_stats()

            # Cache stats
            if self.local_cache:
                stats["cache"] = await self.local_cache.get_stats()

        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            stats["error"] = str(e)

        return stats

    async def close(self):
        """Clean shutdown of all database components"""
        try:
            logger.info("Shutting down ChromaDB local database components...")

            # Close graph storage
            if self.graph_storage:
                await self.graph_storage.close()
                logger.info("✅ Graph storage closed")

            # Close cache
            if self.local_cache:
                await self.local_cache.close()
                logger.info("✅ Local cache closed")

            # ChromaDB doesn't need explicit closing for PersistentClient
            # but we can clear references
            self.chromadb_manager = None
            logger.info("✅ ChromaDB references cleared")

            # Close base database
            await super().close()

            logger.info("✅ All ChromaDB local database components closed")

        except Exception as e:
            logger.error(f"Error during ChromaDB local database shutdown: {e}")
