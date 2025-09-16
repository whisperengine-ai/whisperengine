#!/usr/bin/env python3
"""
ChromaDB HTTP Client Manager

ChromaDB manager that connects to containerized ChromaDB service via HTTP API
instead of using embedded/local ChromaDB. This provides better scalability,
persistence, and separation of concerns.
"""

import os
import json
import logging
import hashlib
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import httpx
import chromadb
from chromadb.config import Settings
from src.utils.embedding_manager import ExternalEmbeddingManager

logger = logging.getLogger(__name__)


class ChromaDBHTTPManager:
    """ChromaDB manager using HTTP client for containerized service"""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """Initialize ChromaDB HTTP client"""
        self.host = host or os.getenv("CHROMADB_HOST", "localhost")
        self.port = port or int(os.getenv("CHROMADB_PORT", "8000"))
        self.base_url = f"http://{self.host}:{self.port}"

        # Collection names from environment
        self.user_collection_name = os.getenv("CHROMADB_COLLECTION_NAME", "user_memories")
        self.global_collection_name = os.getenv("CHROMADB_GLOBAL_COLLECTION_NAME", "global_facts")

        # Check if external embeddings are configured to avoid loading local models
        from src.utils.embedding_manager import is_external_embedding_configured

        self.use_external_embeddings = is_external_embedding_configured()

        if self.use_external_embeddings:
            logger.info(
                "External embeddings detected - ChromaDB will not load local embedding models"
            )

        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

        # Initialize external embedding manager for consistent embeddings
        self.embedding_manager = ExternalEmbeddingManager()

        # ChromaDB client for operations
        self.client = None
        self.user_collection = None
        self.global_collection = None

        # Initialize connection
        self._initialized = False

    async def initialize(self):
        """Initialize ChromaDB client and collections"""
        if self._initialized:
            return

        try:
            # Create ChromaDB HTTP client
            self.client = chromadb.HttpClient(
                host=self.host, port=self.port, settings=Settings(anonymized_telemetry=False)
            )

            # Test connection
            await self._test_connection()

            # Get or create collections
            await self._ensure_collections()

            self._initialized = True
            logger.info(f"ChromaDB HTTP client initialized: {self.base_url}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB HTTP client: {e}")
            raise

    async def _test_connection(self):
        """Test connection to ChromaDB service"""
        try:
            response = await self.http_client.get("/api/v1/heartbeat")
            if response.status_code != 200:
                raise ConnectionError(f"ChromaDB service not healthy: {response.status_code}")
            logger.info("ChromaDB service connection verified")
        except Exception as e:
            logger.error(f"ChromaDB connection test failed: {e}")
            raise

    async def _ensure_collections(self):
        """Ensure required collections exist"""
        try:
            # Get or create user collection
            try:
                self.user_collection = self.client.get_collection(name=self.user_collection_name)
                logger.info(f"Connected to existing user collection: {self.user_collection_name}")
            except Exception:
                self.user_collection = self.client.create_collection(
                    name=self.user_collection_name,
                    metadata={"description": "User conversation memories and personal facts"},
                )
                logger.info(f"Created new user collection: {self.user_collection_name}")

            # Get or create global collection
            try:
                self.global_collection = self.client.get_collection(
                    name=self.global_collection_name
                )
                logger.info(
                    f"Connected to existing global collection: {self.global_collection_name}"
                )
            except Exception:
                self.global_collection = self.client.create_collection(
                    name=self.global_collection_name,
                    metadata={"description": "Global facts and general knowledge"},
                )
                logger.info(f"Created new global collection: {self.global_collection_name}")

        except Exception as e:
            logger.error(f"Failed to ensure collections: {e}")
            raise

    async def store_conversation(
        self, user_id: str, message: str, response: str, metadata: Optional[Dict] = None
    ):
        """Store conversation in ChromaDB"""
        if not self._initialized:
            await self.initialize()

        try:
            # Create document ID
            timestamp = datetime.now().isoformat()
            content_hash = hashlib.sha256(f"{message}{response}".encode()).hexdigest()[:12]
            doc_id = f"conversation_{user_id}_{timestamp}_{content_hash}"

            # Prepare document content
            document_content = f"User: {message}\nBot: {response}"

            # Prepare metadata
            doc_metadata = {
                "doc_type": "conversation",
                "user_id": user_id,
                "timestamp": timestamp,
                "source": "discord",
                "message_content": message,
                "response_content": response,
                "content_hash": content_hash,
                **(metadata or {}),
            }

            # Generate embedding for the document content
            embeddings = await self.embedding_manager.get_embeddings([document_content])
            if not embeddings:
                raise RuntimeError("Failed to generate embeddings for conversation")

            # Store in ChromaDB
            if self.user_collection is None:
                raise RuntimeError("User collection not initialized")

            self.user_collection.add(
                documents=[document_content],
                metadatas=[doc_metadata],
                ids=[doc_id],
                embeddings=[embeddings[0]],  # Add external embeddings
            )

            logger.debug(f"Stored conversation: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            raise

    async def store_user_fact(
        self,
        user_id: str,
        fact: str,
        category: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None,
    ):
        """Store user-specific fact in ChromaDB"""
        if not self._initialized:
            await self.initialize()

        try:
            # Create document ID
            timestamp = datetime.now().isoformat()
            content_hash = hashlib.sha256(fact.encode()).hexdigest()[:12]
            doc_id = f"user_fact_{user_id}_{timestamp}_{content_hash}"

            # Prepare metadata
            doc_metadata = {
                "doc_type": "user_fact",
                "user_id": user_id,
                "timestamp": timestamp,
                "source": "extracted",
                "category": category or "general",
                "confidence": confidence,
                "content_hash": content_hash,
                **(metadata or {}),
            }

            # Generate embedding for the fact
            embeddings = await self.embedding_manager.get_embeddings([fact])
            if not embeddings:
                raise RuntimeError("Failed to generate embeddings for user fact")

            # Store in ChromaDB
            self.user_collection.add(
                documents=[fact],
                metadatas=[doc_metadata],
                ids=[doc_id],
                embeddings=[embeddings[0]],  # Add external embeddings
            )

            logger.debug(f"Stored user fact: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store user fact: {e}")
            raise

    async def store_global_fact(
        self,
        fact: str,
        category: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None,
    ):
        """Store global fact in ChromaDB"""
        if not self._initialized:
            await self.initialize()

        try:
            # Create document ID
            timestamp = datetime.now().isoformat()
            content_hash = hashlib.sha256(fact.encode()).hexdigest()[:12]
            doc_id = f"global_fact_{timestamp}_{content_hash}"

            # Prepare metadata
            doc_metadata = {
                "doc_type": "global_fact",
                "timestamp": timestamp,
                "source": "extracted",
                "category": category or "general",
                "confidence": confidence,
                "content_hash": content_hash,
                **(metadata or {}),
            }

            # Generate embedding for the fact
            embeddings = await self.embedding_manager.get_embeddings([fact])
            if not embeddings:
                raise RuntimeError("Failed to generate embeddings for global fact")

            # Store in ChromaDB
            self.global_collection.add(
                documents=[fact],
                metadatas=[doc_metadata],
                ids=[doc_id],
                embeddings=[embeddings[0]],  # Add external embeddings
            )

            logger.debug(f"Stored global fact: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store global fact: {e}")
            raise

    async def search_memories(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        limit: int = 5,
        doc_types: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Search for relevant memories using external embeddings"""
        if not self._initialized:
            await self.initialize()

        try:
            results = []

            # Generate embedding for query using external embedding manager
            query_embeddings = await self.embedding_manager.get_embeddings([query_text])
            if not query_embeddings:
                logger.error("Failed to generate query embeddings")
                return []

            # Search user collection
            if self.user_collection:
                where_filter = {}
                if user_id:
                    where_filter["user_id"] = user_id
                if doc_types:
                    where_filter["doc_type"] = {"$in": doc_types}

                user_results = self.user_collection.query(
                    query_embeddings=[query_embeddings[0]],  # Use embeddings instead of text
                    n_results=limit,
                    where=where_filter if where_filter else None,
                )

                # Process user results
                if user_results and user_results["documents"] and user_results["documents"][0]:
                    for i in range(len(user_results["documents"][0])):
                        results.append(
                            {
                                "content": user_results["documents"][0][i],
                                "metadata": user_results["metadatas"][0][i],
                                "distance": user_results["distances"][0][i],
                                "collection": "user",
                            }
                        )

            # Search global collection for general knowledge
            if self.global_collection and (not doc_types or "global_fact" in doc_types):
                global_results = self.global_collection.query(
                    query_embeddings=[query_embeddings[0]],  # Use embeddings instead of text
                    n_results=min(3, limit),  # Limit global results
                    where={"doc_type": "global_fact"} if doc_types else None,
                )

                # Process global results
                if (
                    global_results
                    and global_results["documents"]
                    and global_results["documents"][0]
                ):
                    for i in range(len(global_results["documents"][0])):
                        results.append(
                            {
                                "content": global_results["documents"][0][i],
                                "metadata": global_results["metadatas"][0][i],
                                "distance": global_results["distances"][0][i],
                                "collection": "global",
                            }
                        )

            # Sort by relevance (distance) and limit
            results.sort(key=lambda x: x["distance"])
            return results[:limit]

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations for a user"""
        if not self._initialized:
            await self.initialize()

        try:
            if not self.user_collection:
                return []

            results = self.user_collection.get(
                where={"user_id": user_id, "doc_type": "conversation"}, limit=limit
            )

            conversations = []
            for i in range(len(results["documents"])):
                conversations.append(
                    {
                        "id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                    }
                )

            # Sort by timestamp (most recent first)
            conversations.sort(key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)

            return conversations

        except Exception as e:
            logger.error(f"Failed to get user conversations: {e}")
            return []

    async def get_user_facts(
        self, user_id: str, category: Optional[str] = None, limit: int = 20
    ) -> List[Dict]:
        """Get facts about a specific user"""
        if not self._initialized:
            await self.initialize()

        try:
            if not self.user_collection:
                return []

            where_filter = {"user_id": user_id, "doc_type": "user_fact"}
            if category:
                where_filter["category"] = category

            results = self.user_collection.get(where=where_filter, limit=limit)

            facts = []
            for i in range(len(results["documents"])):
                facts.append(
                    {
                        "id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i],
                    }
                )

            return facts

        except Exception as e:
            logger.error(f"Failed to get user facts: {e}")
            return []

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about ChromaDB collections"""
        if not self._initialized:
            await self.initialize()

        try:
            stats = {}

            # User collection stats
            if self.user_collection:
                user_count = self.user_collection.count()
                stats["user_collection"] = {
                    "name": self.user_collection_name,
                    "document_count": user_count,
                }

            # Global collection stats
            if self.global_collection:
                global_count = self.global_collection.count()
                stats["global_collection"] = {
                    "name": self.global_collection_name,
                    "document_count": global_count,
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """Check ChromaDB service health"""
        try:
            response = await self.http_client.get("/api/v1/heartbeat")
            is_healthy = response.status_code == 200

            stats = await self.get_collection_stats() if is_healthy else {}

            return {
                "healthy": is_healthy,
                "service_url": self.base_url,
                "status_code": response.status_code,
                "collections": stats,
            }

        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return {"healthy": False, "service_url": self.base_url, "error": str(e)}

    async def close(self):
        """Close HTTP client connection"""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("ChromaDB HTTP client closed")


# Global instance for backward compatibility
_chromadb_manager = None


async def get_chromadb_manager() -> ChromaDBHTTPManager:
    """Get or create ChromaDB manager instance"""
    global _chromadb_manager
    if _chromadb_manager is None:
        _chromadb_manager = ChromaDBHTTPManager()
        await _chromadb_manager.initialize()
    return _chromadb_manager


# Backward compatibility functions
async def store_conversation_async(
    user_id: str, message: str, response: str, metadata: Dict = None
) -> str:
    """Store conversation (async)"""
    manager = await get_chromadb_manager()
    return await manager.store_conversation(user_id, message, response, metadata)


async def store_user_fact_async(
    user_id: str, fact: str, category: str = None, confidence: float = 1.0, metadata: Dict = None
) -> str:
    """Store user fact (async)"""
    manager = await get_chromadb_manager()
    return await manager.store_user_fact(user_id, fact, category, confidence, metadata)


async def search_memories_async(
    query_text: str, user_id: str = None, limit: int = 5, doc_types: List[str] = None
) -> List[Dict]:
    """Search memories (async)"""
    manager = await get_chromadb_manager()
    return await manager.search_memories(query_text, user_id, limit, doc_types)
