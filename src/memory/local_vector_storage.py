"""
Local Vector Storage for Desktop Mode
Provides ChromaDB-compatible interface using simple cosine similarity search.
Replacement for ChromaDB in desktop/local deployment scenarios.
"""

import hashlib
import logging
import pickle
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """Document stored in local vector storage"""

    id: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any]
    timestamp: float
    doc_type: str


class LocalVectorStorage:
    """
    Local vector storage that provides ChromaDB-compatible interface.

    Features:
    - In-memory vector search using numpy cosine similarity
    - File persistence for embeddings and metadata
    - Thread-safe operations
    - Document metadata support
    - Multiple collection support
    - Similarity search with filtering
    """

    def __init__(self, storage_dir: Path | None = None, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.storage_dir = storage_dir or (Path.home() / ".whisperengine" / "vectors")

        # In-memory storage
        self.collections: dict[str, dict[str, Any]] = {}
        self.documents: dict[str, dict[str, VectorDocument]] = (
            {}
        )  # collection_name -> doc_id -> document

        # Thread safety
        self._lock = threading.RLock()

        # Initialize storage
        self._initialize_storage()

        logger.info(
            f"LocalVectorStorage initialized: dim={embedding_dim}, storage={self.storage_dir}"
        )

    def _initialize_storage(self):
        """Initialize storage directory and load persistent data"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_persistent_data()

    def _get_collection_path(self, collection_name: str) -> Path:
        """Get file path for collection data"""
        return self.storage_dir / f"{collection_name}.pkl"

    def _load_persistent_data(self):
        """Load persistent vector data from disk"""
        try:
            for collection_file in self.storage_dir.glob("*.pkl"):
                collection_name = collection_file.stem

                with open(collection_file, "rb") as f:
                    collection_data = pickle.load(f)

                # Load documents
                self.documents[collection_name] = {}
                for doc_id, doc_data in collection_data.get("documents", {}).items():
                    self.documents[collection_name][doc_id] = VectorDocument(
                        id=doc_data["id"],
                        content=doc_data["content"],
                        embedding=doc_data["embedding"],
                        metadata=doc_data["metadata"],
                        timestamp=doc_data["timestamp"],
                        doc_type=doc_data["doc_type"],
                    )

                self.collections[collection_name] = {
                    "metadata": collection_data.get("metadata", {}),
                    "created_at": collection_data.get("created_at", time.time()),
                }

            logger.info(f"Loaded {len(self.collections)} collections from persistent storage")
        except Exception as e:
            logger.warning(f"Failed to load persistent vector data: {e}")

    def _save_collection(self, collection_name: str):
        """Save collection data to disk"""
        try:
            with self._lock:
                if collection_name not in self.collections:
                    return

                # Prepare documents for serialization
                documents_data = {}
                for doc_id, doc in self.documents.get(collection_name, {}).items():
                    documents_data[doc_id] = {
                        "id": doc.id,
                        "content": doc.content,
                        "embedding": doc.embedding,
                        "metadata": doc.metadata,
                        "timestamp": doc.timestamp,
                        "doc_type": doc.doc_type,
                    }

                collection_data = {
                    "documents": documents_data,
                    "metadata": self.collections[collection_name]["metadata"],
                    "created_at": self.collections[collection_name]["created_at"],
                }

                # Save collection data
                collection_path = self._get_collection_path(collection_name)
                with open(collection_path, "wb") as f:
                    pickle.dump(collection_data, f)

            logger.debug(f"Saved collection '{collection_name}' to persistent storage")
        except Exception as e:
            logger.error(f"Failed to save collection '{collection_name}': {e}")

    def _generate_doc_id(self, content: str, user_id: str | None = None) -> str:
        """Generate deterministic document ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        user_part = f"_{user_id}" if user_id else ""
        timestamp = int(time.time() * 1000) % 100000  # Last 5 digits of timestamp
        return f"doc_{content_hash}_{timestamp}{user_part}"

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            a_np = np.array(a, dtype=np.float32)
            b_np = np.array(b, dtype=np.float32)

            # Normalize vectors
            a_norm = a_np / (np.linalg.norm(a_np) + 1e-8)
            b_norm = b_np / (np.linalg.norm(b_np) + 1e-8)

            # Calculate cosine similarity
            return float(np.dot(a_norm, b_norm))
        except:
            return 0.0

    def _matches_filter(self, metadata: dict[str, Any], where: dict[str, Any]) -> bool:
        """Check if metadata matches the where filter"""
        for key, value in where.items():
            if key not in metadata:
                return False

            if isinstance(value, dict):
                # Handle operators like {"$eq": "value"}, {"$ne": "value"}, etc.
                for op, op_value in value.items():
                    if op == "$eq" and metadata[key] != op_value:
                        return False
                    elif op == "$ne" and metadata[key] == op_value:
                        return False
                    elif op == "$in" and metadata[key] not in op_value:
                        return False
                    elif op == "$nin" and metadata[key] in op_value:
                        return False
            else:
                # Direct equality
                if metadata[key] != value:
                    return False

        return True

    def create_collection(self, name: str, metadata: dict[str, Any] | None = None) -> bool:
        """Create a new collection (ChromaDB-compatible)"""
        with self._lock:
            if name in self.collections:
                return False

            self.collections[name] = {"metadata": metadata or {}, "created_at": time.time()}

            self.documents[name] = {}
            self._save_collection(name)

        logger.info(f"Created collection '{name}'")
        return True

    def get_collection(self, name: str) -> dict[str, Any] | None:
        """Get collection info (ChromaDB-compatible)"""
        with self._lock:
            if name not in self.collections:
                return None

            collection = self.collections[name]
            return {
                "name": name,
                "metadata": collection["metadata"],
                "created_at": collection["created_at"],
                "document_count": len(self.documents.get(name, {})),
            }

    def list_collections(self) -> list[str]:
        """List all collections (ChromaDB-compatible)"""
        with self._lock:
            return list(self.collections.keys())

    def delete_collection(self, name: str) -> bool:
        """Delete a collection (ChromaDB-compatible)"""
        with self._lock:
            if name not in self.collections:
                return False

            # Remove from memory
            del self.collections[name]
            if name in self.documents:
                del self.documents[name]

            # Remove persistent files
            try:
                collection_path = self._get_collection_path(name)
                if collection_path.exists():
                    collection_path.unlink()
            except Exception as e:
                logger.error(f"Failed to remove persistent files for collection '{name}': {e}")

        logger.info(f"Deleted collection '{name}'")
        return True

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]],
        ids: list[str] | None = None,
    ) -> list[str]:
        """Add documents to collection (ChromaDB-compatible)"""
        with self._lock:
            if collection_name not in self.collections:
                self.create_collection(collection_name)

            collection_docs = self.documents[collection_name]
            doc_ids = []

            for i, (doc, embedding, meta) in enumerate(
                zip(documents, embeddings, metadata, strict=False)
            ):
                # Generate or use provided ID
                doc_id = (
                    ids[i]
                    if ids and i < len(ids)
                    else self._generate_doc_id(doc, meta.get("user_id"))
                )
                doc_ids.append(doc_id)

                # Create document
                document = VectorDocument(
                    id=doc_id,
                    content=doc,
                    embedding=embedding,
                    metadata=meta,
                    timestamp=time.time(),
                    doc_type=meta.get("doc_type", "conversation"),
                )

                collection_docs[doc_id] = document

            # Save to disk
            self._save_collection(collection_name)

        logger.debug(f"Added {len(doc_ids)} documents to collection '{collection_name}'")
        return doc_ids

    def query_documents(
        self,
        collection_name: str,
        query_embeddings: list[list[float]],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, list[Any]]:
        """Query documents from collection (ChromaDB-compatible)"""
        with self._lock:
            if collection_name not in self.collections:
                return {"ids": [], "documents": [], "metadatas": [], "distances": []}

            collection_docs = self.documents[collection_name]
            results = {"ids": [], "documents": [], "metadatas": [], "distances": []}

            for query_embedding in query_embeddings:
                # Calculate similarities
                similarities = []

                for doc_id, document in collection_docs.items():
                    # Apply filtering if specified
                    if where and not self._matches_filter(document.metadata, where):
                        continue

                    similarity = self._cosine_similarity(query_embedding, document.embedding)
                    similarities.append((similarity, doc_id, document))

                # Sort by similarity (highest first)
                similarities.sort(key=lambda x: x[0], reverse=True)

                # Take top results
                top_similarities = similarities[:n_results]

                query_ids = []
                query_docs = []
                query_metas = []
                query_distances = []

                for similarity, doc_id, document in top_similarities:
                    query_ids.append(doc_id)
                    query_docs.append(document.content)
                    query_metas.append(document.metadata)
                    query_distances.append(similarity)

                results["ids"].append(query_ids)
                results["documents"].append(query_docs)
                results["metadatas"].append(query_metas)
                results["distances"].append(query_distances)

            return results

    def get_documents(
        self,
        collection_name: str,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, list[Any]]:
        """Get documents from collection (ChromaDB-compatible)"""
        with self._lock:
            if collection_name not in self.collections:
                return {"ids": [], "documents": [], "metadatas": []}

            collection_docs = self.documents[collection_name]

            # Filter documents
            filtered_docs = []

            if ids:
                # Get specific documents by ID
                for doc_id in ids:
                    if doc_id in collection_docs:
                        filtered_docs.append(collection_docs[doc_id])
            else:
                # Get all documents, optionally filtered
                for document in collection_docs.values():
                    if where is None or self._matches_filter(document.metadata, where):
                        filtered_docs.append(document)

            # Apply offset and limit
            if offset:
                filtered_docs = filtered_docs[offset:]
            if limit:
                filtered_docs = filtered_docs[:limit]

            # Format results
            return {
                "ids": [doc.id for doc in filtered_docs],
                "documents": [doc.content for doc in filtered_docs],
                "metadatas": [doc.metadata for doc in filtered_docs],
            }

    def delete_documents(self, collection_name: str, ids: list[str]) -> int:
        """Delete documents from collection (ChromaDB-compatible)"""
        with self._lock:
            if collection_name not in self.collections:
                return 0

            collection_docs = self.documents[collection_name]
            deleted_count = 0

            for doc_id in ids:
                if doc_id in collection_docs:
                    del collection_docs[doc_id]
                    deleted_count += 1

            if deleted_count > 0:
                self._save_collection(collection_name)

        logger.debug(f"Deleted {deleted_count} documents from collection '{collection_name}'")
        return deleted_count

    def count_documents(self, collection_name: str) -> int:
        """Count documents in collection"""
        with self._lock:
            if collection_name not in self.collections:
                return 0
            return len(self.documents.get(collection_name, {}))

    def get_stats(self) -> dict[str, Any]:
        """Get storage statistics"""
        with self._lock:
            total_docs = sum(len(docs) for docs in self.documents.values())
            total_size = 0

            for collection_docs in self.documents.values():
                for doc in collection_docs.values():
                    total_size += len(doc.content) + len(str(doc.embedding))

            return {
                "total_collections": len(self.collections),
                "total_documents": total_docs,
                "estimated_size_bytes": total_size,
                "embedding_dimension": self.embedding_dim,
                "storage_directory": str(self.storage_dir),
            }

    def close(self):
        """Save all collections and clean shutdown"""
        with self._lock:
            for collection_name in self.collections.keys():
                self._save_collection(collection_name)

        logger.info("LocalVectorStorage closed successfully")


class LocalVectorStorageAdapter:
    """Adapter to make LocalVectorStorage compatible with existing ChromaDB usage patterns"""

    def __init__(self, storage_dir: Path | None = None, embedding_dim: int = 384):
        self.storage = LocalVectorStorage(storage_dir, embedding_dim)

        # Default collection names (matching ChromaDB usage)
        self.conversations_collection = "conversations"
        self.user_facts_collection = "user_facts"
        self.global_facts_collection = "global_facts"

        # Ensure default collections exist
        self._ensure_default_collections()

    def _ensure_default_collections(self):
        """Ensure default collections exist"""
        for collection_name in [
            self.conversations_collection,
            self.user_facts_collection,
            self.global_facts_collection,
        ]:
            if collection_name not in self.storage.list_collections():
                self.storage.create_collection(collection_name)

    async def store_conversation(
        self,
        user_id: str,
        message: str,
        response: str,
        embeddings: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store conversation with embedding (compatible with existing interface)"""
        meta = metadata or {}
        meta.update({"user_id": user_id, "doc_type": "conversation", "timestamp": time.time()})

        content = f"User: {message}\nAssistant: {response}"

        doc_ids = self.storage.add_documents(
            collection_name=self.conversations_collection,
            documents=[content],
            embeddings=[embeddings],
            metadata=[meta],
        )

        return doc_ids[0] if doc_ids else ""

    async def search_memories(
        self,
        query_embeddings: list[float],
        user_id: str | None = None,
        limit: int = 10,
        doc_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search memories with optional filtering"""
        where_filter = {}
        if user_id:
            where_filter["user_id"] = user_id
        if doc_types:
            where_filter["doc_type"] = {"$in": doc_types}

        results = self.storage.query_documents(
            collection_name=self.conversations_collection,
            query_embeddings=[query_embeddings],
            n_results=limit,
            where=where_filter if where_filter else None,
        )

        memories = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                memories.append(
                    {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity_score": results["distances"][0][i],
                    }
                )

        return memories

    async def get_stats(self) -> dict[str, Any]:
        """Get storage statistics"""
        stats = self.storage.get_stats()
        stats.update(
            {
                "type": "LocalVectorStorage",
                "conversations_count": self.storage.count_documents(self.conversations_collection),
                "user_facts_count": self.storage.count_documents(self.user_facts_collection),
                "global_facts_count": self.storage.count_documents(self.global_facts_collection),
            }
        )
        return stats

    async def close(self):
        """Clean shutdown"""
        self.storage.close()
