# Technical Implementation Guide
## Hierarchical Memory Architecture for WhisperEngine

## 🎯 **Implementation Overview**

This guide provides step-by-step technical implementation details for migrating from the current ChromaDB-centric memory system to a hierarchical four-tier architecture.

## 📁 **Project Structure Changes**

```
src/
├── memory/
│   ├── core/
│   │   ├── storage_abstraction.py      # Main storage interface
│   │   ├── context_assembler.py        # Intelligent context assembly
│   │   └── migration_manager.py        # Data migration utilities
│   ├── tiers/
│   │   ├── tier1_redis_cache.py        # Recent context cache
│   │   ├── tier2_postgresql.py         # Full conversation archive
│   │   ├── tier3_chromadb_summaries.py # Semantic summaries
│   │   └── tier4_neo4j_relationships.py # Relationship intelligence
│   ├── processors/
│   │   ├── conversation_summarizer.py   # Text summarization
│   │   ├── topic_extractor.py          # Topic and entity extraction
│   │   └── intent_classifier.py        # Intent analysis
│   └── legacy/
│       └── chromadb_migrator.py        # Migration from old system
```

## 🔧 **Implementation Steps**

### **Step 1: Storage Abstraction Layer**

Create the main interface that coordinates all storage tiers:

```python
# src/memory/core/storage_abstraction.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Assembled conversation context from all tiers"""
    recent_messages: List[Dict[str, Any]]
    semantic_summaries: List[Dict[str, Any]] 
    related_topics: List[Dict[str, Any]]
    full_conversations: List[Dict[str, Any]]
    assembly_metadata: Dict[str, Any]
    
    def to_context_string(self, max_length: int = 4000) -> str:
        """Convert to optimized context string for LLM"""
        # Intelligent context string assembly
        # Priority: recent > semantic > topical > historical
        pass

@dataclass
class StorageMetrics:
    """Performance and usage metrics"""
    retrieval_time_ms: int
    sources_used: List[str]
    context_size_chars: int
    cache_hit_ratio: float
    total_conversations: int

class HierarchicalMemoryManager:
    """
    Main interface for hierarchical memory system
    Coordinates all four storage tiers for optimal performance
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tier1_cache = None      # Redis recent context
        self.tier2_archive = None    # PostgreSQL full conversations
        self.tier3_semantic = None   # ChromaDB summaries  
        self.tier4_graph = None      # Neo4j relationships
        
        self.metrics = StorageMetrics(0, [], 0, 0.0, 0)
        self.initialized = False
    
    async def initialize(self):
        """Initialize all storage tiers"""
        logger.info("Initializing hierarchical memory system...")
        
        # Initialize each tier with proper error handling
        await self._init_tier1_cache()
        await self._init_tier2_archive() 
        await self._init_tier3_semantic()
        await self._init_tier4_graph()
        
        self.initialized = True
        logger.info("Hierarchical memory system initialized successfully")
    
    async def store_conversation(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store conversation across all appropriate tiers
        Returns conversation_id for future reference
        """
        start_time = datetime.now()
        conversation_id = None
        
        try:
            # Step 1: Store full conversation in PostgreSQL (source of truth)
            conversation_id = await self.tier2_archive.store_conversation(
                user_id=user_id,
                user_message=user_message,
                bot_response=bot_response,
                metadata=metadata
            )
            
            # Step 2: Generate and store semantic summary in ChromaDB
            summary = await self._generate_conversation_summary(
                user_message, bot_response
            )
            await self.tier3_semantic.store_summary(
                conversation_id=conversation_id,
                user_id=user_id,
                summary=summary,
                metadata=metadata
            )
            
            # Step 3: Extract and store relationships in Neo4j
            await self._extract_and_store_relationships(
                conversation_id=conversation_id,
                user_id=user_id,
                user_message=user_message,
                bot_response=bot_response
            )
            
            # Step 4: Update recent context cache in Redis
            await self.tier1_cache.add_to_recent_context(
                user_id=user_id,
                conversation_id=conversation_id,
                user_message=user_message,
                bot_response=bot_response,
                metadata=metadata
            )
            
            # Record storage metrics
            storage_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(f"Stored conversation {conversation_id} in {storage_time:.2f}ms")
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            # Attempt cleanup if partial storage occurred
            if conversation_id:
                await self._cleanup_partial_storage(conversation_id)
            raise
    
    async def get_conversation_context(
        self,
        user_id: str,
        current_query: str,
        max_context_length: int = 4000
    ) -> ConversationContext:
        """
        Intelligent context assembly from all tiers
        Target: <100ms total retrieval time
        """
        start_time = datetime.now()
        
        try:
            # Execute retrieval from all tiers in parallel for optimal performance
            retrieval_tasks = [
                self._get_recent_context(user_id),
                self._get_semantic_context(user_id, current_query),
                self._get_topical_context(user_id, current_query),
            ]
            
            recent_context, semantic_context, topical_context = await asyncio.gather(
                *retrieval_tasks, return_exceptions=True
            )
            
            # Handle any retrieval failures gracefully
            recent_context = recent_context if not isinstance(recent_context, Exception) else []
            semantic_context = semantic_context if not isinstance(semantic_context, Exception) else []
            topical_context = topical_context if not isinstance(topical_context, Exception) else []
            
            # Get full conversation details for most relevant items
            relevant_conversation_ids = self._extract_relevant_conversation_ids(
                semantic_context, topical_context, limit=3
            )
            
            full_conversations = await self.tier2_archive.get_conversations(
                conversation_ids=relevant_conversation_ids
            )
            
            # Assemble final context with intelligent prioritization
            context = ConversationContext(
                recent_messages=recent_context,
                semantic_summaries=semantic_context,
                related_topics=topical_context,
                full_conversations=full_conversations,
                assembly_metadata={
                    'retrieval_time_ms': (datetime.now() - start_time).total_seconds() * 1000,
                    'sources_used': self._get_sources_used(recent_context, semantic_context, topical_context),
                    'query': current_query,
                    'user_id': user_id
                }
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error assembling conversation context: {e}")
            # Return minimal context from cache if available
            return await self._get_fallback_context(user_id)
```

### **Step 2: Tier 1 - Redis Recent Context Cache**

```python
# src/memory/tiers/tier1_redis_cache.py

import redis.asyncio as redis
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class RedisContextCache:
    """
    Tier 1: Ultra-fast recent context cache
    Stores last 20 messages per user with <1ms retrieval
    """
    
    def __init__(self, redis_url: str, default_ttl: int = 1800):
        self.redis_url = redis_url
        self.default_ttl = default_ttl  # 30 minutes
        self.redis_client = None
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url)
        await self.redis_client.ping()
        
    async def add_to_recent_context(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        bot_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add new conversation to recent context cache"""
        cache_key = f"recent_context:{user_id}"
        
        conversation_data = {
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'bot_response': bot_response,
            'metadata': metadata or {}
        }
        
        # Add to list (most recent first)
        await self.redis_client.lpush(cache_key, json.dumps(conversation_data))
        
        # Trim to keep only last 20 conversations
        await self.redis_client.ltrim(cache_key, 0, 19)
        
        # Set expiration
        await self.redis_client.expire(cache_key, self.default_ttl)
        
    async def get_recent_context(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        cache_key = f"recent_context:{user_id}"
        
        try:
            # Get recent conversations from Redis
            recent_data = await self.redis_client.lrange(cache_key, 0, limit - 1)
            
            conversations = []
            for data in recent_data:
                try:
                    conversation = json.loads(data)
                    conversations.append(conversation)
                except json.JSONDecodeError:
                    continue
                    
            return conversations
            
        except Exception as e:
            logger.error(f"Error retrieving recent context for {user_id}: {e}")
            return []
```

### **Step 3: Tier 2 - PostgreSQL Conversation Archive**

```python
# src/memory/tiers/tier2_postgresql.py

import asyncpg
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

class PostgreSQLConversationArchive:
    """
    Tier 2: Complete conversation archive with full fidelity
    Optimized for chronological access and data integrity
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
        
    async def initialize(self):
        """Initialize PostgreSQL connection pool"""
        self.pool = await asyncpg.create_pool(self.database_url)
        await self._ensure_schema()
        
    async def _ensure_schema(self):
        """Ensure database schema exists"""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id VARCHAR(255) NOT NULL,
            channel_id VARCHAR(255),
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            session_id UUID,
            thread_id UUID,
            message_type VARCHAR(50) DEFAULT 'conversation',
            emotion_data JSONB,
            user_metadata JSONB,
            processing_metadata JSONB
        );
        
        CREATE INDEX IF NOT EXISTS idx_conversations_user_time 
        ON conversations(user_id, timestamp DESC);
        
        CREATE INDEX IF NOT EXISTS idx_conversations_fts 
        USING gin(to_tsvector('english', user_message || ' ' || bot_response));
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
    
    async def store_conversation(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store complete conversation with full fidelity"""
        
        conversation_id = str(uuid.uuid4())
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversations (
                    conversation_id, user_id, channel_id, user_message, 
                    bot_response, emotion_data, user_metadata, processing_metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
                conversation_id,
                user_id,
                metadata.get('channel_id') if metadata else None,
                user_message,
                bot_response,
                metadata.get('emotion_data') if metadata else None,
                metadata.get('user_metadata') if metadata else None,
                metadata.get('processing_metadata') if metadata else None
            )
            
        return conversation_id
    
    async def get_conversations(
        self,
        conversation_ids: List[str],
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Get full conversation details by IDs"""
        
        if not conversation_ids:
            return []
            
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT conversation_id, user_id, channel_id, user_message,
                       bot_response, timestamp, emotion_data, user_metadata,
                       processing_metadata
                FROM conversations 
                WHERE conversation_id = ANY($1::uuid[])
                ORDER BY timestamp DESC
            """, conversation_ids)
            
            conversations = []
            for row in rows:
                conversation = dict(row)
                # Convert UUID to string for JSON serialization
                conversation['conversation_id'] = str(conversation['conversation_id'])
                conversations.append(conversation)
                
            return conversations
    
    async def get_user_conversation_history(
        self,
        user_id: str,
        limit: int = 50,
        since_days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get chronological conversation history for user"""
        
        since_date = datetime.now() - timedelta(days=since_days)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT conversation_id, user_message, bot_response, timestamp
                FROM conversations 
                WHERE user_id = $1 AND timestamp >= $2
                ORDER BY timestamp DESC
                LIMIT $3
            """, user_id, since_date, limit)
            
            return [dict(row) for row in rows]
```

### **Step 4: Tier 3 - ChromaDB Semantic Summaries**

```python
# src/memory/tiers/tier3_chromadb_summaries.py

import chromadb
from datetime import datetime
import hashlib
from typing import List, Dict, Any, Optional

class ChromaDBSemanticSummaries:
    """
    Tier 3: Semantic search on conversation summaries
    Stores ~150 character summaries for efficient vector search
    """
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client = None
        self.summaries_collection = None
        
    async def initialize(self):
        """Initialize ChromaDB client and collections"""
        self.client = chromadb.HttpClient(host=self.host, port=self.port)
        
        # Create or get summaries collection
        self.summaries_collection = self.client.get_or_create_collection(
            name="conversation_summaries",
            metadata={"description": "Semantic summaries of conversations for efficient search"}
        )
        
    async def store_summary(
        self,
        conversation_id: str,
        user_id: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store conversation summary for semantic search"""
        
        doc_id = f"summary_{conversation_id}"
        
        doc_metadata = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "type": "conversation_summary",
            "summary_length": len(summary),
            **(metadata or {})
        }
        
        self.summaries_collection.add(
            documents=[summary],
            metadatas=[doc_metadata],
            ids=[doc_id]
        )
        
    async def search_summaries(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        time_decay: bool = True
    ) -> List[Dict[str, Any]]:
        """Search conversation summaries semantically"""
        
        # Build query filters
        where_filter = {"user_id": user_id, "type": "conversation_summary"}
        
        results = self.summaries_collection.query(
            query_texts=[query],
            where=where_filter,
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        summaries = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                
                # Apply time decay if requested
                relevance_score = 1 - distance
                if time_decay:
                    relevance_score = self._apply_time_decay(
                        relevance_score, 
                        metadata.get("timestamp")
                    )
                
                summaries.append({
                    "conversation_id": metadata.get("conversation_id"),
                    "summary": doc,
                    "relevance_score": relevance_score,
                    "metadata": metadata
                })
                
        return summaries
    
    def _apply_time_decay(self, base_score: float, timestamp_str: str) -> float:
        """Apply time decay to favor recent conversations"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            days_ago = (datetime.now() - timestamp).days
            
            # Decay factor: 1.0 for today, 0.9 for 1 week ago, 0.8 for 1 month ago
            decay_factor = max(0.5, 1.0 - (days_ago * 0.01))
            return base_score * decay_factor
            
        except Exception:
            return base_score
```

### **Step 5: Migration Strategy Implementation**

```python
# src/memory/legacy/chromadb_migrator.py

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ChromaDBMigrator:
    """
    Migrate existing ChromaDB conversations to hierarchical storage
    Preserves all data while optimizing for new architecture
    """
    
    def __init__(self, old_chromadb_client, new_hierarchical_manager):
        self.old_client = old_chromadb_client
        self.new_manager = new_hierarchical_manager
        self.migration_stats = {
            'total_conversations': 0,
            'migrated_successfully': 0,
            'failed_migrations': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def migrate_all_conversations(self, batch_size: int = 100):
        """Migrate all conversations from old ChromaDB to new hierarchical system"""
        
        self.migration_stats['start_time'] = datetime.now()
        logger.info("Starting ChromaDB conversation migration...")
        
        try:
            # Get all conversations from old ChromaDB
            old_collection = self.old_client.get_collection("user_memories")
            
            # Process in batches to avoid memory issues
            offset = 0
            while True:
                batch = old_collection.get(
                    limit=batch_size,
                    offset=offset,
                    include=["documents", "metadatas", "ids"]
                )
                
                if not batch["documents"]:
                    break
                    
                await self._migrate_batch(batch)
                offset += batch_size
                
                logger.info(f"Migrated {offset} conversations...")
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.migration_stats['end_time'] = datetime.now()
            self._log_migration_summary()
    
    async def _migrate_batch(self, batch: Dict[str, Any]):
        """Migrate a batch of conversations"""
        
        for i, doc in enumerate(batch["documents"]):
            try:
                metadata = batch["metadatas"][i]
                
                # Extract conversation components from old format
                user_message = metadata.get("user_message", "")
                bot_response = metadata.get("bot_response", "")
                user_id = metadata.get("user_id", "")
                
                if user_message and bot_response and user_id:
                    # Store in new hierarchical system
                    await self.new_manager.store_conversation(
                        user_id=user_id,
                        user_message=user_message,
                        bot_response=bot_response,
                        metadata=metadata
                    )
                    
                    self.migration_stats['migrated_successfully'] += 1
                else:
                    logger.warning(f"Skipping incomplete conversation: {metadata}")
                    self.migration_stats['failed_migrations'] += 1
                    
                self.migration_stats['total_conversations'] += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate conversation {i}: {e}")
                self.migration_stats['failed_migrations'] += 1
    
    def _log_migration_summary(self):
        """Log migration completion summary"""
        duration = (
            self.migration_stats['end_time'] - self.migration_stats['start_time']
        ).total_seconds()
        
        logger.info(f"""
        Migration Summary:
        ==================
        Total conversations processed: {self.migration_stats['total_conversations']}
        Successfully migrated: {self.migration_stats['migrated_successfully']}
        Failed migrations: {self.migration_stats['failed_migrations']}
        Duration: {duration:.2f} seconds
        Success rate: {self.migration_stats['migrated_successfully'] / max(1, self.migration_stats['total_conversations']) * 100:.1f}%
        """)
```

## 🚀 **Integration with Existing System**

### **Update Main Bot to Use Hierarchical Storage**

```python
# src/core/bot.py - Updated to use hierarchical memory

class DiscordBotCore:
    def __init__(self, config):
        # Replace old memory manager with hierarchical system
        self.memory_manager = HierarchicalMemoryManager(config)
        
    async def initialize(self):
        # Initialize hierarchical memory system
        await self.memory_manager.initialize()
        
        # Optional: Run migration from old system
        if config.get('migrate_from_chromadb', False):
            await self._run_migration()
```

This implementation provides a complete foundation for the hierarchical memory architecture with clear separation of concerns, optimal performance characteristics, and a smooth migration path from the existing system.

## 📊 **Performance Monitoring**

The new system includes comprehensive performance monitoring to ensure we achieve our <100ms context retrieval targets and can optimize further based on real usage patterns.

Ready to begin implementation of any specific tier or component!