#!/usr/bin/env python3
"""
Enhanced Local Vector Storage with FAISS Integration
High-performance ChromaDB replacement for native local installations.

Features:
- FAISS for fast vector similarity search
- SQLite for metadata and persistence
- ChromaDB-compatible API
- Automatic embedding generation
- Advanced filtering and search
- Multi-collection support
"""

import json
import sqlite3
import numpy as np
import logging
import threading
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
import pickle
import hashlib
import os

# Try to import FAISS, fall back to simple cosine similarity
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available, falling back to numpy cosine similarity")

logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """Document stored in vector database"""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    timestamp: float
    collection: str
    doc_type: str = "text"

@dataclass
class SearchResult:
    """Search result with similarity score"""
    document: VectorDocument
    score: float
    distance: float


class EnhancedLocalVectorStorage:
    """
    Enhanced local vector storage with FAISS integration.
    
    Provides ChromaDB-compatible interface with high performance:
    - FAISS for vector similarity search (when available)
    - SQLite for metadata persistence
    - Automatic embedding generation
    - Multiple collection support
    - Advanced filtering capabilities
    - Thread-safe operations
    """
    
    def __init__(self, storage_dir: Optional[Path] = None, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.storage_dir = storage_dir or (Path.home() / '.whisperengine' / 'vectors')
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Database for metadata
        self.db_path = self.storage_dir / 'vector_metadata.db'
        
        # Collections storage
        self.collections: Dict[str, Dict[str, Any]] = {}
        self.indexes: Dict[str, Any] = {}  # FAISS indexes or numpy arrays
        self.documents: Dict[str, Dict[str, VectorDocument]] = {}  # collection -> doc_id -> document
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Performance tracking
        self.search_count = 0
        self.index_count = 0
        
        # Initialize
        self._initialize_database()
        self._load_collections()
        
        logger.info(f"EnhancedLocalVectorStorage initialized")
        logger.info(f"FAISS available: {FAISS_AVAILABLE}")
        logger.info(f"Storage: {self.storage_dir}")
        logger.info(f"Loaded collections: {list(self.collections.keys())}")
    
    def _initialize_database(self):
        """Initialize SQLite database for metadata"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    name TEXT PRIMARY KEY,
                    metadata TEXT NOT NULL,
                    embedding_dim INTEGER NOT NULL,
                    document_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    collection_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    metadata TEXT NOT NULL,
                    doc_type TEXT DEFAULT 'text',
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (collection_name) REFERENCES collections (name)
                )
            """)
            
            # Indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_collection ON documents (collection_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_type ON documents (doc_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_timestamp ON documents (timestamp)")
            
            conn.commit()
    
    def _load_collections(self):
        """Load collections and their indexes from storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Load collections
                collections = conn.execute("SELECT * FROM collections").fetchall()
                for collection in collections:
                    collection_name = collection['name']
                    self.collections[collection_name] = {
                        'metadata': json.loads(collection['metadata']),
                        'embedding_dim': collection['embedding_dim'],
                        'document_count': collection['document_count'],
                        'created_at': collection['created_at'],
                        'updated_at': collection['updated_at']
                    }
                    
                    # Load documents for this collection
                    self.documents[collection_name] = {}
                    docs = conn.execute(
                        "SELECT * FROM documents WHERE collection_name = ?", 
                        (collection_name,)
                    ).fetchall()
                    
                    embeddings = []
                    for doc in docs:
                        # Deserialize embedding
                        embedding = pickle.loads(doc['embedding'])
                        
                        doc_obj = VectorDocument(
                            id=doc['id'],
                            content=doc['content'],
                            embedding=embedding,
                            metadata=json.loads(doc['metadata']),
                            timestamp=doc['timestamp'],
                            collection=collection_name,
                            doc_type=doc['doc_type']
                        )
                        self.documents[collection_name][doc['id']] = doc_obj
                        embeddings.append(embedding)
                    
                    # Build search index
                    if embeddings:
                        self._build_index(collection_name, embeddings)
                        
        except Exception as e:
            logger.warning(f"Failed to load collections: {e}")
    
    def _build_index(self, collection_name: str, embeddings: List[List[float]]):
        """Build FAISS or numpy index for fast search"""
        try:
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            if FAISS_AVAILABLE and len(embeddings) > 10:  # Use FAISS for larger collections
                # Create FAISS index
                assert faiss is not None, "FAISS should be available"
                index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product (cosine similarity)
                
                # Normalize vectors for cosine similarity
                faiss.normalize_L2(embeddings_array)
                index.add(embeddings_array)
                
                self.indexes[collection_name] = {
                    'type': 'faiss',
                    'index': index,
                    'embeddings': embeddings_array
                }
                logger.debug(f"Built FAISS index for {collection_name}: {len(embeddings)} vectors")
                
            else:
                # Use numpy for smaller collections or when FAISS unavailable
                # Normalize for cosine similarity
                norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
                normalized_embeddings = embeddings_array / np.maximum(norms, 1e-8)
                
                self.indexes[collection_name] = {
                    'type': 'numpy',
                    'embeddings': normalized_embeddings
                }
                logger.debug(f"Built numpy index for {collection_name}: {len(embeddings)} vectors")
                
        except Exception as e:
            logger.error(f"Failed to build index for {collection_name}: {e}")
    
    def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new collection"""
        with self._lock:
            if name in self.collections:
                logger.warning(f"Collection {name} already exists")
                return {'name': name, 'created': False}
            
            metadata = metadata or {}
            now = datetime.now().isoformat()
            
            # Add to memory
            self.collections[name] = {
                'metadata': metadata,
                'embedding_dim': self.embedding_dim,
                'document_count': 0,
                'created_at': now,
                'updated_at': now
            }
            self.documents[name] = {}
            
            # Persist to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO collections (name, metadata, embedding_dim, document_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, json.dumps(metadata), self.embedding_dim, 0, now, now))
                conn.commit()
            
            logger.info(f"Created collection: {name}")
            return {'name': name, 'created': True}
    
    def get_collection(self, name: str) -> Optional[Dict[str, Any]]:
        """Get collection info"""
        return self.collections.get(name)
    
    def list_collections(self) -> List[str]:
        """List all collection names"""
        return list(self.collections.keys())
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection and all its documents"""
        with self._lock:
            if name not in self.collections:
                return False
            
            # Remove from memory
            del self.collections[name]
            del self.documents[name]
            if name in self.indexes:
                del self.indexes[name]
            
            # Remove from database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM documents WHERE collection_name = ?", (name,))
                conn.execute("DELETE FROM collections WHERE name = ?", (name,))
                conn.commit()
            
            logger.info(f"Deleted collection: {name}")
            return True
    
    def add_documents(self, collection_name: str, documents: List[Dict[str, Any]], 
                     embeddings: Optional[List[List[float]]] = None) -> Dict[str, Any]:
        """Add documents to collection"""
        with self._lock:
            if collection_name not in self.collections:
                self.create_collection(collection_name)
            
            if embeddings and len(embeddings) != len(documents):
                raise ValueError("Number of embeddings must match number of documents")
            
            added_ids = []
            
            # Process each document
            for i, doc in enumerate(documents):
                doc_id = doc.get('id', f"doc_{hash(doc.get('content', ''))}")
                content = doc.get('content', '')
                metadata = doc.get('metadata', {})
                doc_type = doc.get('type', 'text')
                
                # Use provided embedding or generate placeholder
                if embeddings:
                    embedding = embeddings[i]
                else:
                    # Generate a simple hash-based embedding for testing
                    # In production, this would call an embedding model
                    embedding = self._generate_placeholder_embedding(content)
                
                # Create document object
                doc_obj = VectorDocument(
                    id=doc_id,
                    content=content,
                    embedding=embedding,
                    metadata=metadata,
                    timestamp=datetime.now().timestamp(),
                    collection=collection_name,
                    doc_type=doc_type
                )
                
                # Add to memory
                self.documents[collection_name][doc_id] = doc_obj
                added_ids.append(doc_id)
                
                # Persist to database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO documents 
                        (id, collection_name, content, embedding, metadata, doc_type, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doc_id, collection_name, content, 
                        pickle.dumps(embedding), json.dumps(metadata),
                        doc_type, doc_obj.timestamp
                    ))
                    conn.commit()
            
            # Update collection document count
            self.collections[collection_name]['document_count'] = len(self.documents[collection_name])
            self.collections[collection_name]['updated_at'] = datetime.now().isoformat()
            
            # Rebuild index
            if self.documents[collection_name]:
                embeddings_list = [doc.embedding for doc in self.documents[collection_name].values()]
                self._build_index(collection_name, embeddings_list)
            
            # Update collection in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE collections 
                    SET document_count = ?, updated_at = ?
                    WHERE name = ?
                """, (self.collections[collection_name]['document_count'], 
                         self.collections[collection_name]['updated_at'], collection_name))
                conn.commit()
            
            logger.info(f"Added {len(added_ids)} documents to {collection_name}")
            return {'added_count': len(added_ids), 'added_ids': added_ids}
    
    def _generate_placeholder_embedding(self, content: str) -> List[float]:
        """Generate a simple hash-based embedding for testing"""
        # This is a placeholder - in production you'd use a real embedding model
        hash_value = hashlib.md5(content.encode()).hexdigest()
        
        # Convert hex to numbers and normalize
        numbers = [int(hash_value[i:i+2], 16) for i in range(0, min(len(hash_value), self.embedding_dim * 2), 2)]
        
        # Pad or truncate to embedding_dim
        if len(numbers) < self.embedding_dim:
            numbers.extend([0] * (self.embedding_dim - len(numbers)))
        else:
            numbers = numbers[:self.embedding_dim]
        
        # Normalize to [-1, 1]
        normalized = [(n - 127.5) / 127.5 for n in numbers]
        
        return normalized
    
    def query(self, collection_name: str, query_embedding: List[float], 
             n_results: int = 10, where: Optional[Dict[str, Any]] = None,
             include: Optional[List[str]] = None) -> Dict[str, Any]:
        """Query collection for similar documents"""
        with self._lock:
            self.search_count += 1
            
            if collection_name not in self.collections:
                return {'documents': [], 'distances': [], 'metadatas': []}
            
            if not self.documents[collection_name]:
                return {'documents': [], 'distances': [], 'metadatas': []}
            
            # Get documents and filter
            docs = list(self.documents[collection_name].values())
            if where:
                docs = self._filter_documents(docs, where)
            
            if not docs:
                return {'documents': [], 'distances': [], 'metadatas': []}
            
            # Perform similarity search
            results = self._similarity_search(collection_name, query_embedding, docs, n_results)
            
            # Format results
            documents = []
            distances = []
            metadatas = []
            ids = []
            
            include = include or ['documents', 'metadatas', 'distances']
            
            for result in results:
                if 'documents' in include:
                    documents.append(result.document.content)
                if 'metadatas' in include:
                    metadatas.append(result.document.metadata)
                if 'distances' in include:
                    distances.append(result.distance)
                ids.append(result.document.id)
            
            response = {'ids': [ids]}
            if 'documents' in include:
                response['documents'] = [documents]
            if 'metadatas' in include:
                response['metadatas'] = [metadatas]
            if 'distances' in include:
                response['distances'] = [distances]
            
            return response
    
    def _filter_documents(self, docs: List[VectorDocument], where: Dict[str, Any]) -> List[VectorDocument]:
        """Filter documents based on metadata conditions"""
        filtered = []
        for doc in docs:
            match = True
            for key, value in where.items():
                if key not in doc.metadata or doc.metadata[key] != value:
                    match = False
                    break
            if match:
                filtered.append(doc)
        return filtered
    
    def _similarity_search(self, collection_name: str, query_embedding: List[float], 
                          docs: List[VectorDocument], n_results: int) -> List[SearchResult]:
        """Perform similarity search using available index"""
        query_array = np.array([query_embedding], dtype=np.float32)
        
        if collection_name in self.indexes:
            index_info = self.indexes[collection_name]
            
            if index_info['type'] == 'faiss' and FAISS_AVAILABLE:
                # FAISS search
                assert faiss is not None, "FAISS should be available"
                faiss.normalize_L2(query_array)
                scores, indices = index_info['index'].search(query_array, min(n_results, len(docs)))
                
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < len(docs):
                        results.append(SearchResult(
                            document=docs[idx],
                            score=float(score),
                            distance=1.0 - float(score)  # Convert similarity to distance
                        ))
                
                return results
            
            elif index_info['type'] == 'numpy':
                # Numpy cosine similarity
                query_norm = query_array / np.maximum(np.linalg.norm(query_array), 1e-8)
                similarities = np.dot(index_info['embeddings'], query_norm.T).flatten()
                
                # Get top results
                top_indices = np.argsort(similarities)[::-1][:n_results]
                
                results = []
                for idx in top_indices:
                    if idx < len(docs):
                        similarity = similarities[idx]
                        results.append(SearchResult(
                            document=docs[idx],
                            score=float(similarity),
                            distance=1.0 - float(similarity)
                        ))
                
                return results
        
        # Fallback: simple cosine similarity
        query_norm = np.linalg.norm(query_embedding)
        if query_norm == 0:
            return []
        
        similarities = []
        for doc in docs:
            doc_embedding = np.array(doc.embedding)
            doc_norm = np.linalg.norm(doc_embedding)
            if doc_norm > 0:
                similarity = np.dot(query_embedding, doc_embedding) / (query_norm * doc_norm)
                similarities.append((similarity, doc))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for similarity, doc in similarities[:n_results]:
            results.append(SearchResult(
                document=doc,
                score=float(similarity),
                distance=1.0 - float(similarity)
            ))
        
        return results
    
    def get_document(self, collection_name: str, document_id: str) -> Optional[VectorDocument]:
        """Get a specific document by ID"""
        if collection_name in self.documents:
            return self.documents[collection_name].get(document_id)
        return None
    
    def delete_documents(self, collection_name: str, document_ids: List[str]) -> Dict[str, Any]:
        """Delete specific documents"""
        with self._lock:
            if collection_name not in self.collections:
                return {'deleted_count': 0}
            
            deleted_count = 0
            for doc_id in document_ids:
                if doc_id in self.documents[collection_name]:
                    del self.documents[collection_name][doc_id]
                    deleted_count += 1
                    
                    # Remove from database
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                        conn.commit()
            
            # Update collection count
            self.collections[collection_name]['document_count'] = len(self.documents[collection_name])
            
            # Rebuild index if documents remain
            if self.documents[collection_name]:
                embeddings_list = [doc.embedding for doc in self.documents[collection_name].values()]
                self._build_index(collection_name, embeddings_list)
            elif collection_name in self.indexes:
                del self.indexes[collection_name]
            
            logger.info(f"Deleted {deleted_count} documents from {collection_name}")
            return {'deleted_count': deleted_count}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_docs = sum(len(docs) for docs in self.documents.values())
        
        # Database file size
        db_size_mb = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        
        return {
            'storage_type': 'enhanced_local_vector',
            'faiss_available': FAISS_AVAILABLE,
            'total_collections': len(self.collections),
            'total_documents': total_docs,
            'embedding_dimension': self.embedding_dim,
            'search_count': self.search_count,
            'database_size_mb': round(db_size_mb, 2),
            'collections': {
                name: {
                    'document_count': info['document_count'],
                    'has_index': name in self.indexes,
                    'index_type': self.indexes[name]['type'] if name in self.indexes else None
                }
                for name, info in self.collections.items()
            }
        }


# ========== ChromaDB Compatibility Layer ==========

class ChromaDBCompatibilityLayer:
    """ChromaDB-compatible interface for EnhancedLocalVectorStorage"""
    
    def __init__(self, storage: EnhancedLocalVectorStorage):
        self.storage = storage
    
    def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """ChromaDB-compatible collection creation"""
        if name not in self.storage.collections:
            self.storage.create_collection(name, metadata)
        return ChromaDBCollection(self.storage, name)


class ChromaDBCollection:
    """ChromaDB-compatible collection interface"""
    
    def __init__(self, storage: EnhancedLocalVectorStorage, name: str):
        self.storage = storage
        self.name = name
    
    def add(self, documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None,
            ids: Optional[List[str]] = None, embeddings: Optional[List[List[float]]] = None):
        """Add documents ChromaDB-style"""
        docs = []
        for i, content in enumerate(documents):
            doc = {
                'content': content,
                'metadata': metadatas[i] if metadatas else {},
                'id': ids[i] if ids else f"doc_{i}_{hash(content)}"
            }
            docs.append(doc)
        
        return self.storage.add_documents(self.name, docs, embeddings)
    
    def query(self, query_embeddings: List[List[float]], n_results: int = 10,
             where: Optional[Dict[str, Any]] = None, include: Optional[List[str]] = None):
        """Query documents ChromaDB-style"""
        if len(query_embeddings) == 1:
            return self.storage.query(self.name, query_embeddings[0], n_results, where, include)
        
        # Handle multiple queries
        results = []
        for query_embedding in query_embeddings:
            result = self.storage.query(self.name, query_embedding, n_results, where, include)
            results.append(result)
        
        return results
    
    def get(self, ids: Optional[List[str]] = None, where: Optional[Dict[str, Any]] = None):
        """Get documents ChromaDB-style"""
        if ids:
            docs = []
            for doc_id in ids:
                doc = self.storage.get_document(self.name, doc_id)
                if doc:
                    docs.append(doc)
            return {'documents': [doc.content for doc in docs],
                   'metadatas': [doc.metadata for doc in docs],
                   'ids': [doc.id for doc in docs]}
        
        # Return all documents (with optional filtering)
        all_docs = list(self.storage.documents[self.name].values())
        if where:
            all_docs = self.storage._filter_documents(all_docs, where)
        
        return {
            'documents': [doc.content for doc in all_docs],
            'metadatas': [doc.metadata for doc in all_docs],
            'ids': [doc.id for doc in all_docs]
        }
    
    def delete(self, ids: List[str]):
        """Delete documents ChromaDB-style"""
        return self.storage.delete_documents(self.name, ids)


# ========== Factory Functions ==========

def create_enhanced_vector_storage(storage_dir: Optional[Path] = None, 
                                  embedding_dim: int = 384) -> EnhancedLocalVectorStorage:
    """Factory function to create enhanced vector storage"""
    return EnhancedLocalVectorStorage(storage_dir, embedding_dim)

def create_chromadb_compatible_client(storage_dir: Optional[Path] = None) -> ChromaDBCompatibilityLayer:
    """Create ChromaDB-compatible client"""
    storage = create_enhanced_vector_storage(storage_dir)
    return ChromaDBCompatibilityLayer(storage)


# ========== Example Usage ==========

async def example_usage():
    """Example usage of enhanced vector storage"""
    
    # Create storage
    storage = create_enhanced_vector_storage()
    
    # Create collection
    storage.create_collection("test_memories", {"description": "Test memory collection"})
    
    # Add documents
    docs = [
        {"content": "I love pizza", "metadata": {"user": "alice", "emotion": "happy"}},
        {"content": "The weather is nice", "metadata": {"user": "bob", "emotion": "neutral"}},
        {"content": "I feel sad today", "metadata": {"user": "alice", "emotion": "sad"}}
    ]
    
    result = storage.add_documents("test_memories", docs)
    print(f"Added documents: {result}")
    
    # Query for similar content
    query_embedding = storage._generate_placeholder_embedding("I enjoy food")
    results = storage.query("test_memories", query_embedding, n_results=2)
    
    print(f"Query results: {results}")
    
    # Get stats
    stats = storage.get_stats()
    print(f"Storage stats: {stats}")
    
    # ChromaDB compatibility
    client = create_chromadb_compatible_client()
    collection = client.get_or_create_collection("chroma_test")
    
    collection.add(
        documents=["Hello world", "Goodbye world"],
        metadatas=[{"type": "greeting"}, {"type": "farewell"}],
        ids=["hello", "goodbye"]
    )
    
    chroma_results = collection.query(
        query_embeddings=[storage._generate_placeholder_embedding("Hello")],
        n_results=1
    )
    print(f"ChromaDB compatible results: {chroma_results}")


if __name__ == "__main__":
    asyncio.run(example_usage())