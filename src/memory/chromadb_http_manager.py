#!/usr/bin/env python3
"""
ChromaDB HTTP Client Manager

ChromaDB manager that connects to containerized ChromaDB service via HTTP API
instead of using embedded/local ChromaDB. This provides better scalability,
persistence, and separation of concerns.

DEPRECATED: External embedding functionality was removed in v2.4.0 (September 2025).
All embedding now uses ChromaDB built-in local models only.
"""

import hashlib
import logging
import os
from datetime import datetime
from typing import Any

import chromadb
import httpx
from chromadb.config import Settings

# Historical: ExternalEmbeddingManager and is_external_embedding_configured removed Sept 2025

logger = logging.getLogger(__name__)


class ChromaDBHTTPManager:
    """ChromaDB manager using HTTP client for containerized service"""

    def __init__(self, host: str | None = None, port: int | None = None):
        """Initialize ChromaDB HTTP client"""
        self.host = host or os.getenv("CHROMADB_HOST", "localhost")
        self.port = port or int(os.getenv("CHROMADB_PORT", "8000"))
        self.base_url = f"http://{self.host}:{self.port}"

        # Collection names from environment
        self.user_collection_name = os.getenv("CHROMADB_COLLECTION_NAME", "user_memories")
        self.global_collection_name = os.getenv("CHROMADB_GLOBAL_COLLECTION_NAME", "global_facts")

        # Historical: All embedding is now local. External embedding logic removed Sept 2025.
        self.use_external_embeddings = False
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
        )

        # Will be set when ChromaDB client is initialized
        self.client = None
        self.user_collection = None
        self.global_collection = None

    async def health_check(self) -> bool:
        """Check if ChromaDB HTTP service is available"""
        try:
            response = await self.http_client.get("/api/v1/heartbeat")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False

    async def initialize(self):
        """Initialize ChromaDB HTTP client and create collections"""
        try:
            # Create HTTP client
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(anonymized_telemetry=False)
            )

            # Create or get user collection - always use local embeddings
            try:
                self.user_collection = self.client.get_collection(name=self.user_collection_name)
                logger.debug(f"Using existing user collection: {self.user_collection_name}")
            except Exception:
                self.user_collection = self.client.create_collection(
                    name=self.user_collection_name
                )
                logger.info(f"Created user collection: {self.user_collection_name}")

            # Create or get global collection - always use local embeddings
            try:
                self.global_collection = self.client.get_collection(
                    name=self.global_collection_name
                )
                logger.debug(f"Using existing global collection: {self.global_collection_name}")
            except Exception:
                self.global_collection = self.client.create_collection(
                    name=self.global_collection_name
                )
                logger.info(f"Created global collection: {self.global_collection_name}")

            logger.info("ChromaDB HTTP manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB HTTP manager: {e}")
            raise

    async def store_conversation(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        metadata: dict | None = None,
    ) -> str:
        """Store a conversation in ChromaDB with local embeddings only"""
        try:
            if not self.user_collection:
                raise RuntimeError("User collection not initialized")

            # Create unique document ID
            timestamp = datetime.now().isoformat()
            content_hash = hashlib.md5(f"{user_message}{bot_response}".encode()).hexdigest()
            doc_id = f"{user_id}_{timestamp}_{content_hash[:8]}"

            # Combine user message and bot response
            document_content = f"User: {user_message}\nBot: {bot_response}"

            # Prepare metadata
            doc_metadata = {
                "user_id": user_id,
                "timestamp": timestamp,
                "type": "conversation",
                "user_message": user_message,
                "bot_response": bot_response,
                **(metadata or {}),
            }

            # Historical: External embedding functionality removed Sept 2025. 
            # ChromaDB now uses built-in local embeddings only.

            # Store in ChromaDB using built-in local embeddings
            self.user_collection.add(
                documents=[document_content],
                metadatas=[doc_metadata],
                ids=[doc_id],
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
        category: str | None = None,
        confidence: float = 1.0,
        metadata: dict | None = None,
    ) -> str:
        """Store a user-specific fact in ChromaDB with local embeddings only"""
        try:
            if not self.user_collection:
                raise RuntimeError("User collection not initialized")

            # Create unique document ID
            timestamp = datetime.now().isoformat()
            fact_hash = hashlib.md5(fact.encode()).hexdigest()
            doc_id = f"{user_id}_fact_{timestamp}_{fact_hash[:8]}"

            # Prepare metadata
            storage_metadata = {
                "user_id": user_id,
                "timestamp": timestamp,
                "type": "user_fact",
                "category": category or "general",
                "confidence": confidence,
                **(metadata or {}),
            }

            # Historical: External embedding functionality removed Sept 2025.
            # Use ChromaDB built-in local embeddings only.
            self.user_collection.add(
                documents=[fact],
                metadatas=[storage_metadata],
                ids=[doc_id],
            )

            logger.debug(f"Stored user fact: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store user fact: {e}")
            raise

    async def store_global_fact(
        self,
        fact: str,
        category: str | None = None,
        confidence: float = 1.0,
        metadata: dict | None = None,
    ) -> str:
        """Store a global fact in ChromaDB with local embeddings only"""
        try:
            if not self.global_collection:
                raise RuntimeError("Global collection not initialized")

            # Create unique document ID
            timestamp = datetime.now().isoformat()
            fact_hash = hashlib.md5(fact.encode()).hexdigest()
            doc_id = f"global_fact_{timestamp}_{fact_hash[:8]}"

            # Prepare metadata
            storage_metadata = {
                "timestamp": timestamp,
                "type": "global_fact",
                "category": category or "general",
                "confidence": confidence,
                **(metadata or {}),
            }

            # Historical: External embedding functionality removed Sept 2025.
            # Use ChromaDB built-in local embeddings only.
            self.global_collection.add(
                documents=[fact],
                metadatas=[storage_metadata],
                ids=[doc_id],
            )

            logger.debug(f"Stored global fact: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to store global fact: {e}")
            raise

    async def search_memories(
        self,
        query_text: str,
        user_id: str | None = None,
        limit: int = 10,
        include_global: bool = True,
    ) -> list[dict[str, Any]]:
        """Search for relevant memories using local embeddings only"""
        try:
            results = []

            # Historical: External embedding functionality removed Sept 2025.
            # Use ChromaDB built-in local embeddings for query.
            
            # Search user-specific memories
            if user_id and self.user_collection:
                user_results = self.user_collection.query(
                    query_texts=[query_text],
                    n_results=limit,
                    where={"user_id": user_id}
                )

                if user_results["documents"] and user_results["documents"][0]:
                    for i, doc in enumerate(user_results["documents"][0]):
                        results.append({
                            "content": doc,
                            "metadata": user_results["metadatas"][0][i] if user_results["metadatas"] else {},
                            "distance": user_results["distances"][0][i] if user_results["distances"] else 0.0,
                            "source": "user_memory",
                        })

            # Search global facts if requested
            if include_global and self.global_collection:
                global_results = self.global_collection.query(
                    query_texts=[query_text],
                    n_results=min(limit, 5),  # Limit global results
                    where={"type": "global_fact"}
                )

                if global_results["documents"] and global_results["documents"][0]:
                    for i, doc in enumerate(global_results["documents"][0]):
                        results.append({
                            "content": doc,
                            "metadata": global_results["metadatas"][0][i] if global_results["metadatas"] else {},
                            "distance": global_results["distances"][0][i] if global_results["distances"] else 0.0,
                            "source": "global_fact",
                        })

            # Sort by relevance (distance)
            results.sort(key=lambda x: x["distance"])
            return results[:limit]

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def get_user_facts(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get user-specific facts using local embeddings only"""
        try:
            if not self.user_collection:
                return []

            results = self.user_collection.get(
                where={"user_id": user_id, "type": "user_fact"},
                limit=limit
            )

            facts = []
            if results["documents"]:
                for i in range(len(results["documents"])):
                    facts.append({
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i] if results["metadatas"] else {},
                        "id": results["ids"][i] if results["ids"] else None,
                    })

            return facts

        except Exception as e:
            logger.error(f"Failed to get user facts: {e}")
            return []

    async def get_conversation_history(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get conversation history for a user"""
        try:
            if not self.user_collection:
                return []

            results = self.user_collection.get(
                where={"user_id": user_id, "type": "conversation"},
                limit=limit
            )

            conversations = []
            if results["documents"]:
                for i in range(len(results["documents"])):
                    conversations.append({
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i] if results["metadatas"] else {},
                        "id": results["ids"][i] if results["ids"] else None,
                    })

            return conversations

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    async def health_check_detailed(self) -> dict[str, Any]:
        """Detailed health check of ChromaDB HTTP service"""
        try:
            response = await self.http_client.get("/api/v1/heartbeat")
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "host": self.host,
                "port": self.port,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "host": self.host,
                "port": self.port,
            }

    async def close(self):
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.aclose()


# Compatibility functions for legacy code
async def store_conversation_http(
    user_id: str, message: str, response: str, metadata: dict | None = None
) -> str:
    """DEPRECATED: Legacy function for storing conversations. Use ChromaDBHTTPManager directly."""
    logger.warning("store_conversation_http is deprecated - use ChromaDBHTTPManager directly")
    return ""


async def store_global_fact_http(
    user_id: str, fact: str, category: str | None = None, confidence: float = 1.0, metadata: dict | None = None
) -> str:
    """DEPRECATED: Legacy function for storing global facts. Use ChromaDBHTTPManager directly."""
    logger.warning("store_global_fact_http is deprecated - use ChromaDBHTTPManager directly")
    return ""
