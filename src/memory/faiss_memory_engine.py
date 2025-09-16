"""
WhisperEngine Faiss Memory Engine
High-performance memory system using Faiss for ultra-fast vector search and parallel processing
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
import threading
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np
import pandas as pd

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

logger = logging.getLogger(__name__)

@dataclass
class MemoryDocument:
    """Optimized memory document structure"""
    id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    user_id: str
    timestamp: float
    importance: float = 0.5
    doc_type: str = "conversation"

class FaissMemoryIndex:
    """High-performance Faiss index with parallel search capabilities"""
    
    def __init__(self, dimension: int = 384, index_type: str = "IVF", 
                 nlist: int = 100, use_gpu: bool = False):
        """
        Initialize Faiss index with optimized configuration
        
        Args:
            dimension: Vector dimension (384 for sentence-transformers)
            index_type: Index type (IVF, HNSW, Flat)
            nlist: Number of clusters for IVF index
            use_gpu: Whether to use GPU acceleration (if available)
        """
        if not FAISS_AVAILABLE:
            raise ImportError("Faiss not available. Install with: pip install faiss-cpu")
        
        self.dimension = dimension
        self.index_type = index_type
        self.nlist = nlist
        self.use_gpu = use_gpu
        
        # Create optimized index
        self.index = self._create_index()
        self.is_trained = False
        
        # Document storage (Faiss only stores vectors)
        self.documents: Dict[int, MemoryDocument] = {}
        self.next_id = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Performance metrics
        self.search_times = []
        self.batch_sizes = []
        
        logger.info(f"🚀 Initialized Faiss index: {index_type}, dim={dimension}, GPU={use_gpu}")
    
    def _create_index(self):
        """Create optimized Faiss index based on configuration"""
        
        if not FAISS_AVAILABLE or faiss is None:
            raise ImportError("Faiss not available")
        
        if self.index_type == "Flat":
            # Exact search - best for small datasets
            index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
            
        elif self.index_type == "IVF":
            # Approximate search with clustering - best for medium datasets
            quantizer = faiss.IndexFlatIP(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist)
            
        elif self.index_type == "HNSW":
            # Hierarchical Navigable Small World - best for large datasets
            index = faiss.IndexHNSWFlat(self.dimension, 32)  # 32 connections
            index.hnsw.efConstruction = 64  # Construction parameter
            index.hnsw.efSearch = 32  # Search parameter
            
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        
        # GPU acceleration if requested and available
        if self.use_gpu and hasattr(faiss, 'StandardGpuResources'):
            try:
                res = faiss.StandardGpuResources()
                index = faiss.index_cpu_to_gpu(res, 0, index)
                logger.info("✅ GPU acceleration enabled")
            except Exception as e:
                logger.warning(f"GPU acceleration failed, using CPU: {e}")
        
        return index
    
    def add_documents(self, documents: List[MemoryDocument]) -> List[int]:
        """Add documents to index with batch optimization"""
        
        if not FAISS_AVAILABLE or faiss is None:
            raise ImportError("Faiss not available")
        
        with self._lock:
            # Prepare vectors and metadata
            vectors = np.array([doc.embedding for doc in documents], dtype=np.float32)
            
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(vectors)
            
            # Train index if needed
            if not self.is_trained and self.index_type == "IVF":
                if len(vectors) >= self.nlist:
                    self.index.train(vectors)
                    self.is_trained = True
                    logger.info(f"✅ Trained IVF index with {len(vectors)} vectors")
            
            # Add vectors to index
            start_id = self.next_id
            ids = list(range(start_id, start_id + len(documents)))
            
            self.index.add(vectors)
            
            # Store documents
            for i, doc in enumerate(documents):
                self.documents[start_id + i] = doc
            
            self.next_id += len(documents)
            
            logger.debug(f"📥 Added {len(documents)} documents to Faiss index")
            return ids
    
    def search(self, query_vector: np.ndarray, k: int = 10, 
               user_filter: Optional[str] = None,
               doc_type_filter: Optional[List[str]] = None,
               min_importance: float = 0.0) -> List[Tuple[MemoryDocument, float]]:
        """Ultra-fast search with optional filtering"""
        
        if not FAISS_AVAILABLE or faiss is None:
            return []
        
        start_time = time.time()
        
        with self._lock:
            # Normalize query vector
            query_vector = query_vector.astype(np.float32).reshape(1, -1)
            faiss.normalize_L2(query_vector)
            
            # Perform search (this is where the speed magic happens)
            # Search more than k to account for filtering
            search_k = min(k * 3, self.index.ntotal) if (user_filter or doc_type_filter or min_importance > 0.0) else k
            
            if search_k == 0:
                return []
            
            scores, indices = self.index.search(query_vector, int(search_k))
            
            # Filter and format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # Faiss returns -1 for empty slots
                    continue
                
                doc = self.documents.get(idx)
                if not doc:
                    continue
                
                # Apply filters
                if user_filter and doc.user_id != user_filter:
                    continue
                if doc_type_filter and doc.doc_type not in doc_type_filter:
                    continue
                if doc.importance < min_importance:
                    continue
                
                results.append((doc, float(score)))
                
                if len(results) >= k:
                    break
            
            # Record performance
            search_time = time.time() - start_time
            self.search_times.append(search_time)
            if len(self.search_times) > 1000:  # Keep last 1000 searches
                self.search_times = self.search_times[-1000:]
            
            logger.debug(f"🔍 Faiss search: {len(results)} results in {search_time*1000:.2f}ms")
            
            return results
    
    def batch_search(self, query_vectors: np.ndarray, k: int = 10,
                     user_filters: Optional[List[str]] = None) -> List[List[Tuple[MemoryDocument, float]]]:
        """Parallel batch search for multiple queries"""
        
        if not FAISS_AVAILABLE or faiss is None:
            return []
        
        start_time = time.time()
        
        with self._lock:
            # Normalize all query vectors
            query_vectors = query_vectors.astype(np.float32)
            faiss.normalize_L2(query_vectors)
            
            # Batch search (highly optimized in Faiss)
            scores, indices = self.index.search(query_vectors, k)
            
            # Process results for each query
            batch_results = []
            for i in range(len(query_vectors)):
                query_results = []
                user_filter = user_filters[i] if user_filters else None
                
                for score, idx in zip(scores[i], indices[i]):
                    if idx == -1:
                        continue
                    
                    doc = self.documents.get(idx)
                    if not doc:
                        continue
                    
                    if user_filter and doc.user_id != user_filter:
                        continue
                    
                    query_results.append((doc, float(score)))
                
                batch_results.append(query_results)
            
            # Record performance
            search_time = time.time() - start_time
            self.batch_sizes.append(len(query_vectors))
            
            logger.debug(f"🔍 Faiss batch search: {len(query_vectors)} queries in {search_time*1000:.2f}ms")
            
            return batch_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "index_type": self.index_type,
            "total_documents": len(self.documents),
            "index_size": getattr(self.index, 'ntotal', 0),
            "is_trained": self.is_trained,
            "avg_search_time_ms": np.mean(self.search_times) * 1000 if self.search_times else 0,
            "avg_batch_size": np.mean(self.batch_sizes) if self.batch_sizes else 0,
            "use_gpu": self.use_gpu
        }


class FaissMemoryEngine:
    """Production-ready memory engine using Faiss for ultra-fast retrieval"""
    
    def __init__(self, embedding_dimension: int = 384, max_workers: int = 4,
                 enable_batch_processing: bool = True):
        """
        Initialize Faiss memory engine with production optimizations
        
        Args:
            embedding_dimension: Dimension of embedding vectors
            max_workers: Number of worker threads for parallel processing
            enable_batch_processing: Enable batch processing for memory operations
        """
        if not FAISS_AVAILABLE:
            raise ImportError("Faiss not available. Install with: pip install faiss-cpu")
        
        self.embedding_dimension = embedding_dimension
        self.max_workers = max_workers
        self.enable_batch_processing = enable_batch_processing
        
        # Initialize indexes for different memory types
        self.conversation_index = FaissMemoryIndex(embedding_dimension, "IVF")
        self.fact_index = FaissMemoryIndex(embedding_dimension, "HNSW")
        
        # Thread pools for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)
        
        # Batch processing queues
        self.add_queue: Optional[asyncio.Queue] = None
        self.batch_task = None
        
        # Performance tracking
        self.total_searches = 0
        self.total_adds = 0
        self.cache_hits = 0
        
        # LRU cache for frequent searches
        self.search_cache = {}
        self.cache_max_size = 1000
        
        logger.info(f"🚀 Initialized FaissMemoryEngine with {max_workers} workers")
    
    async def initialize(self):
        """Initialize async components"""
        if self.enable_batch_processing and not self.batch_task:
            self.add_queue = asyncio.Queue(maxsize=1000)
            self.batch_task = asyncio.create_task(self._batch_processor())
            logger.info("✅ Started batch processing task")
    
    async def add_memory(self, user_id: str, content: str, embedding: np.ndarray,
                        metadata: Optional[Dict[str, Any]] = None,
                        importance: float = 0.5, doc_type: str = "conversation") -> str:
        """Add single memory with async optimization"""
        
        doc = MemoryDocument(
            id=f"{user_id}_{int(time.time() * 1000)}_{self.total_adds}",
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            user_id=user_id,
            timestamp=time.time(),
            importance=importance,
            doc_type=doc_type
        )
        
        if self.enable_batch_processing and self.add_queue:
            # Add to batch queue for processing
            await self.add_queue.put(doc)
        else:
            # Add immediately
            index = self.conversation_index if doc_type == "conversation" else self.fact_index
            index.add_documents([doc])
        
        self.total_adds += 1
        return doc.id
    
    async def search_memories(self, query_embedding: np.ndarray, user_id: Optional[str] = None,
                             k: int = 10, doc_types: Optional[List[str]] = None,
                             min_importance: float = 0.0) -> List[Dict[str, Any]]:
        """Ultra-fast memory search with parallel processing"""
        
        # Check cache first
        cache_key = f"{hash(query_embedding.tobytes())}_{user_id}_{k}_{doc_types}_{min_importance}"
        if cache_key in self.search_cache:
            self.cache_hits += 1
            return self.search_cache[cache_key]
        
        # Determine which indexes to search
        search_tasks = []
        
        if not doc_types or "conversation" in doc_types:
            search_tasks.append(
                asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    self.conversation_index.search,
                    query_embedding, k, user_id, doc_types, min_importance
                )
            )
        
        if not doc_types or any(dt != "conversation" for dt in doc_types):
            search_tasks.append(
                asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    self.fact_index.search,
                    query_embedding, k, user_id, doc_types, min_importance
                )
            )
        
        # Parallel search across indexes
        search_results = await asyncio.gather(*search_tasks)
        
        # Combine and rank results
        all_results = []
        for results in search_results:
            all_results.extend(results)
        
        # Sort by score and take top k
        all_results.sort(key=lambda x: x[1], reverse=True)
        top_results = all_results[:k]
        
        # Format results
        formatted_results = []
        for doc, score in top_results:
            formatted_results.append({
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata,
                "user_id": doc.user_id,
                "doc_type": doc.doc_type,
                "importance": doc.importance,
                "similarity_score": score,
                "timestamp": doc.timestamp
            })
        
        # Cache results
        if len(self.search_cache) >= self.cache_max_size:
            # Remove oldest entries
            keys_to_remove = list(self.search_cache.keys())[:100]
            for key in keys_to_remove:
                del self.search_cache[key]
        
        self.search_cache[cache_key] = formatted_results
        self.total_searches += 1
        
        return formatted_results
    
    async def _batch_processor(self):
        """Background task for batch processing memory additions"""
        
        if not self.add_queue:
            return
        
        batch = []
        last_process_time = time.time()
        
        while True:
            try:
                # Wait for items or timeout
                try:
                    doc = await asyncio.wait_for(self.add_queue.get(), timeout=1.0)
                    batch.append(doc)
                except asyncio.TimeoutError:
                    pass
                
                # Process batch if ready
                current_time = time.time()
                should_process = (
                    len(batch) >= 10 or  # Batch size threshold
                    (batch and current_time - last_process_time > 2.0)  # Time threshold
                )
                
                if should_process and batch:
                    # Separate by type
                    conversation_docs = [d for d in batch if d.doc_type == "conversation"]
                    fact_docs = [d for d in batch if d.doc_type != "conversation"]
                    
                    # Add to appropriate indexes
                    if conversation_docs:
                        await asyncio.get_event_loop().run_in_executor(
                            self.thread_pool,
                            self.conversation_index.add_documents,
                            conversation_docs
                        )
                    
                    if fact_docs:
                        await asyncio.get_event_loop().run_in_executor(
                            self.thread_pool,
                            self.fact_index.add_documents,
                            fact_docs
                        )
                    
                    logger.debug(f"📥 Batch processed: {len(batch)} memories")
                    batch.clear()
                    last_process_time = current_time
                
            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(1.0)
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        
        conversation_stats = self.conversation_index.get_statistics()
        fact_stats = self.fact_index.get_statistics()
        
        return {
            "total_searches": self.total_searches,
            "total_adds": self.total_adds,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / max(self.total_searches, 1),
            "conversation_index": conversation_stats,
            "fact_index": fact_stats,
            "worker_threads": self.max_workers,
            "batch_processing": self.enable_batch_processing,
            "queue_size": self.add_queue.qsize() if self.add_queue else 0
        }
    
    async def shutdown(self):
        """Graceful shutdown"""
        if self.batch_task:
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
        
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        
        logger.info("✅ FaissMemoryEngine shutdown complete")


# ChromaDB adapter for drop-in replacement
class FaissChromaDBAdapter:
    """Adapter to make FaissMemoryEngine compatible with existing ChromaDB code"""
    
    def __init__(self, embedding_dimension: int = 384):
        self.engine = FaissMemoryEngine(embedding_dimension)
        self.initialized = False
    
    async def initialize(self):
        """Initialize the Faiss engine"""
        if not self.initialized:
            await self.engine.initialize()
            self.initialized = True
    
    async def search_memories_with_embedding(self, query_embedding: np.ndarray,
                                           user_id: Optional[str] = None,
                                           limit: int = 5,
                                           doc_types: Optional[List[str]] = None) -> List[Dict]:
        """ChromaDB-compatible search with pre-computed embedding"""
        
        if not self.initialized:
            await self.initialize()
        
        results = await self.engine.search_memories(
            query_embedding=query_embedding,
            user_id=user_id,
            k=limit,
            doc_types=doc_types
        )
        
        # Convert to ChromaDB format
        chromadb_results = []
        for result in results:
            chromadb_results.append({
                "content": result["content"],
                "metadata": result["metadata"],
                "distance": 1.0 - result["similarity_score"],  # Convert similarity to distance
                "collection": "user" if result["doc_type"] == "conversation" else "global"
            })
        
        return chromadb_results