"""
Batched Memory Manager Adapter

This adapter wraps the existing memory managers to use ChromaDB batch operations,
reducing HTTP calls from 6+ per message to 1-2 batch operations.

Key improvements:
- Batch document storage (multiple memories stored in single HTTP call)
- Batch memory retrieval (multiple queries in single HTTP call)
- Automatic batching with intelligent flush timing
- Connection pooling for better HTTP performance
- Performance metrics and monitoring
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from src.memory.chromadb_batch_optimizer import get_batch_optimizer
from typing import Any

logger = logging.getLogger(__name__)


class BatchedMemoryManager:
    """
    Memory manager adapter that uses ChromaDB batch operations for performance
    """

    def __init__(self, base_memory_manager: Any):
        self.base_manager = base_memory_manager
        self.batch_optimizer = None
        self._pending_stores = []
        self._pending_queries = []
        self._store_batch_timer = None
        self._query_batch_timer = None
        
        # Performance tracking
        self.performance_metrics = {
            'stores_batched': 0,
            'queries_batched': 0,
            'http_calls_saved': 0,
            'total_operations': 0,
            'avg_batch_size': 0.0,
            'last_batch_time': 0.0
        }
        
        logger.info("Batched Memory Manager initialized")

    async def initialize(self):
        """Initialize batch optimizer"""
        try:
            self.batch_optimizer = await get_batch_optimizer()
            logger.info("✅ ChromaDB batch optimizer connected")
        except (ConnectionError, ImportError, ValueError) as e:
            logger.warning("Failed to initialize batch optimizer, falling back to direct operations: %s", e)
            self.batch_optimizer = None

    async def store_conversation_batched(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        channel_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store conversation using batch operations"""
        if not self.batch_optimizer:
            # Fallback to direct operation
            return self.base_manager.store_conversation(
                user_id, user_message, bot_response, channel_id, {}, metadata or {}
            )

        try:
            # Prepare document for batch storage
            from datetime import datetime
            import hashlib
            
            timestamp = datetime.now().isoformat()
            content_hash = hashlib.md5(f"{user_message}{bot_response}".encode()).hexdigest()
            doc_id = f"{user_id}_{timestamp}_{content_hash[:8]}"
            
            document_content = f"User: {user_message}\nBot: {bot_response}"
            
            doc_metadata = {
                "user_id": user_id,
                "timestamp": timestamp,
                "type": "conversation",
                "user_message": user_message,
                "bot_response": bot_response,
                "channel_id": channel_id or "",
                **(metadata or {}),
            }
            
            # Use batch add instead of individual add
            await self.batch_optimizer.add_single_document(
                collection_name="user_memories",
                document=document_content,
                metadata=doc_metadata,
                doc_id=doc_id
            )
            
            self.performance_metrics['stores_batched'] += 1
            self.performance_metrics['total_operations'] += 1
            
            logger.debug("Stored conversation in batch: %s", doc_id)
            return doc_id
            
        except (ConnectionError, ValueError, KeyError) as e:
            logger.error("Batch store failed, falling back to direct: %s", e)
            # Fallback to direct operation
            result = self.base_manager.store_conversation(
                user_id, user_message, bot_response, channel_id, {}, metadata or {}
            )
            return str(result) if result else ""

    async def retrieve_relevant_memories_batched(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
        include_global: bool = True
    ) -> List[Dict[str, Any]]:
        """Retrieve memories using batch operations"""
        if not self.batch_optimizer:
            # Fallback to direct operation
            return self.base_manager.retrieve_relevant_memories(user_id, query, limit)

        try:
            # Prepare batch query
            where_clause = {"user_id": user_id}
            
            # Use batch query instead of individual query
            results = await self.batch_optimizer.query_single(
                collection_name="user_memories",
                query_text=query,
                n_results=limit,
                where=where_clause
            )
            
            # Convert to expected format
            memories = []
            if results.get("documents"):
                for i, doc in enumerate(results["documents"]):
                    memory = {
                        "content": doc,
                        "metadata": results["metadatas"][i] if results.get("metadatas") and i < len(results["metadatas"]) else {},
                        "id": results["ids"][i] if results.get("ids") and i < len(results["ids"]) else None,
                        "distance": results["distances"][i] if results.get("distances") and i < len(results["distances"]) else 0.0,
                        "source": "user_memory",
                    }
                    memories.append(memory)
            
            # Include global facts if requested and using batching
            if include_global:
                try:
                    global_results = await self.batch_optimizer.query_single(
                        collection_name="global_facts",
                        query_text=query,
                        n_results=min(limit, 5),  # Limit global results
                        where={"type": "global_fact"}
                    )
                    
                    if global_results.get("documents"):
                        for i, doc in enumerate(global_results["documents"]):
                            memory = {
                                "content": doc,
                                "metadata": global_results["metadatas"][i] if global_results.get("metadatas") and i < len(global_results["metadatas"]) else {},
                                "id": global_results["ids"][i] if global_results.get("ids") and i < len(global_results["ids"]) else None,
                                "distance": global_results["distances"][i] if global_results.get("distances") and i < len(global_results["distances"]) else 0.0,
                                "source": "global_fact",
                            }
                            memories.append(memory)
                except (ConnectionError, ValueError) as e:
                    logger.warning("Failed to retrieve global facts in batch: %s", e)
            
            # Sort by relevance
            memories.sort(key=lambda x: x.get("distance", 0.0))
            
            self.performance_metrics['queries_batched'] += 1
            self.performance_metrics['total_operations'] += 1
            
            logger.debug("Retrieved %d memories in batch for query: %s...", len(memories), query[:50])
            return memories[:limit]
            
        except (ConnectionError, ValueError, KeyError) as e:
            logger.error("Batch query failed, falling back to direct: %s", e)
            # Fallback to direct operation
            return self.base_manager.retrieve_relevant_memories(user_id, query, limit)

    async def store_multiple_conversations_batch(
        self,
        conversations: List[Dict[str, Any]]
    ) -> List[str]:
        """Store multiple conversations in a single batch operation"""
        if not self.batch_optimizer:
            # Fallback to individual operations
            results = []
            for conv in conversations:
                result = self.base_manager.store_conversation(
                    conv["user_id"],
                    conv["user_message"],
                    conv["bot_response"],
                    conv.get("channel_id"),
                    {},
                    conv.get("metadata", {})
                )
                results.append(str(result) if result else "")
            return results

        try:
            documents = []
            metadatas = []
            ids = []
            
            from datetime import datetime
            import hashlib
            
            for conv in conversations:
                timestamp = datetime.now().isoformat()
                content_hash = hashlib.md5(f"{conv['user_message']}{conv['bot_response']}".encode()).hexdigest()
                doc_id = f"{conv['user_id']}_{timestamp}_{content_hash[:8]}"
                
                document_content = f"User: {conv['user_message']}\nBot: {conv['bot_response']}"
                
                doc_metadata = {
                    "user_id": conv["user_id"],
                    "timestamp": timestamp,
                    "type": "conversation",
                    "user_message": conv["user_message"],
                    "bot_response": conv["bot_response"],
                    "channel_id": conv.get("channel_id", ""),
                    **conv.get("metadata", {}),
                }
                
                documents.append(document_content)
                metadatas.append(doc_metadata)
                ids.append(doc_id)
            
            # Single batch operation for all conversations
            await self.batch_optimizer.batch_add_documents(
                collection_name="user_memories",
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            batch_size = len(conversations)
            self.performance_metrics['stores_batched'] += batch_size
            self.performance_metrics['http_calls_saved'] += batch_size - 1  # Saved N-1 HTTP calls
            self.performance_metrics['total_operations'] += batch_size
            
            logger.info(f"✅ Stored {batch_size} conversations in single batch operation")
            return ids
            
        except Exception as e:
            logger.error(f"Multi-conversation batch failed: {e}")
            # Fallback to individual operations
            results = []
            for conv in conversations:
                result = self.base_manager.store_conversation(
                    conv["user_id"],
                    conv["user_message"],
                    conv["bot_response"],
                    conv.get("channel_id"),
                    {},
                    conv.get("metadata", {})
                )
                results.append(str(result) if result else "")
            return results

    async def retrieve_multiple_queries_batch(
        self,
        queries: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Retrieve memories for multiple queries in a single batch operation"""
        if not self.batch_optimizer:
            # Fallback to individual operations
            results = []
            for query_data in queries:
                result = self.base_manager.retrieve_relevant_memories(
                    query_data["user_id"],
                    query_data["query"],
                    query_data.get("limit", 10)
                )
                results.append(result)
            return results

        try:
            # Group queries by similar parameters for efficient batching
            query_texts = []
            user_ids = []
            limits = []
            
            for query_data in queries:
                query_texts.append(query_data["query"])
                user_ids.append(query_data["user_id"])
                limits.append(query_data.get("limit", 10))
            
            # Batch query operation
            batch_results = await self.batch_optimizer.batch_query_documents(
                collection_name="user_memories",
                query_texts=query_texts,
                n_results=max(limits),  # Use max limit for all queries
                where=None  # We'll filter by user_id post-query
            )
            
            # Process and filter results for each individual query
            individual_results = []
            for i, query_data in enumerate(queries):
                user_id = query_data["user_id"]
                limit = query_data.get("limit", 10)
                
                # Extract results for this specific query
                if (batch_results.get("documents") and 
                    i < len(batch_results["documents"]) and
                    batch_results["documents"][i]):
                    
                    query_memories = []
                    for j, doc in enumerate(batch_results["documents"][i]):
                        # Check if this document belongs to the right user
                        metadata = (batch_results["metadatas"][i][j] 
                                   if batch_results.get("metadatas") and 
                                      i < len(batch_results["metadatas"]) and
                                      j < len(batch_results["metadatas"][i])
                                   else {})
                        
                        if metadata.get("user_id") == user_id:
                            memory = {
                                "content": doc,
                                "metadata": metadata,
                                "id": (batch_results["ids"][i][j] 
                                      if batch_results.get("ids") and 
                                         i < len(batch_results["ids"]) and
                                         j < len(batch_results["ids"][i])
                                      else None),
                                "distance": (batch_results["distances"][i][j] 
                                           if batch_results.get("distances") and 
                                              i < len(batch_results["distances"]) and
                                              j < len(batch_results["distances"][i])
                                           else 0.0),
                                "source": "user_memory",
                            }
                            query_memories.append(memory)
                    
                    # Sort and limit
                    query_memories.sort(key=lambda x: x.get("distance", 0.0))
                    individual_results.append(query_memories[:limit])
                else:
                    individual_results.append([])
            
            batch_size = len(queries)
            self.performance_metrics['queries_batched'] += batch_size
            self.performance_metrics['http_calls_saved'] += batch_size - 1
            self.performance_metrics['total_operations'] += batch_size
            
            logger.info(f"✅ Retrieved memories for {batch_size} queries in single batch operation")
            return individual_results
            
        except Exception as e:
            logger.error(f"Multi-query batch failed: {e}")
            # Fallback to individual operations
            results = []
            for query_data in queries:
                result = self.base_manager.retrieve_relevant_memories(
                    query_data["user_id"],
                    query_data["query"],
                    query_data.get("limit", 10)
                )
                results.append(result)
            return results

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics including batch optimizer metrics"""
        metrics = self.performance_metrics.copy()
        
        if self.batch_optimizer:
            batch_metrics = self.batch_optimizer.get_performance_metrics()
            metrics.update({
                f"batch_optimizer_{k}": v for k, v in batch_metrics.items()
            })
        
        # Calculate efficiency
        if metrics['total_operations'] > 0:
            metrics['batching_efficiency'] = (metrics['http_calls_saved'] / metrics['total_operations']) * 100
        else:
            metrics['batching_efficiency'] = 0.0
        
        return metrics

    # Proxy methods for compatibility with existing code
    def __getattr__(self, name):
        """Proxy all missing attributes to the base memory manager"""
        if hasattr(self.base_manager, name):
            return getattr(self.base_manager, name)
        raise AttributeError(f"{self.__class__.__name__} object has no attribute '{name}'")

    # Explicit proxy methods for core functionality
    def store_conversation(self, *args, **kwargs):
        """Route to batched version"""
        return asyncio.create_task(self.store_conversation_batched(*args, **kwargs))

    def retrieve_relevant_memories(self, *args, **kwargs):
        """Route to batched version"""
        return asyncio.create_task(self.retrieve_relevant_memories_batched(*args, **kwargs))

    async def cleanup(self):
        """Cleanup batch optimizer"""
        if self.batch_optimizer:
            await self.batch_optimizer.stop()
        logger.info("Batched Memory Manager cleaned up")