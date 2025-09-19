# src/memory/tiers/tier2_postgresql.py

import asyncpg
import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PostgreSQLConversationArchive:
    """
    Tier 2: Complete conversation archive with full fidelity
    Optimized for chronological access and data integrity
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            await self._ensure_schema()
            self.logger.info("PostgreSQL conversation archive initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize PostgreSQL archive: %s", e)
            raise
        
    async def _ensure_schema(self):
        """Ensure database schema exists"""
        schema_sql = """
        -- Main conversations table
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
            processing_metadata JSONB,
            
            -- Performance indexes
            CONSTRAINT conversations_user_id_check CHECK (char_length(user_id) > 0),
            CONSTRAINT conversations_user_message_check CHECK (char_length(user_message) > 0),
            CONSTRAINT conversations_bot_response_check CHECK (char_length(bot_response) > 0)
        );
        
        -- Indexes for optimal performance
        CREATE INDEX IF NOT EXISTS idx_conversations_user_time 
        ON conversations(user_id, timestamp DESC);
        
        CREATE INDEX IF NOT EXISTS idx_conversations_channel_time 
        ON conversations(channel_id, timestamp DESC) WHERE channel_id IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_conversations_session 
        ON conversations(session_id, timestamp) WHERE session_id IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_conversations_thread 
        ON conversations(thread_id, timestamp) WHERE thread_id IS NOT NULL;
        
        -- Full-text search capability
        CREATE INDEX IF NOT EXISTS idx_conversations_fts 
        ON conversations USING gin(to_tsvector('english', user_message || ' ' || bot_response));
        
        -- Conversation sessions for grouping related interactions
        CREATE TABLE IF NOT EXISTS conversation_sessions (
            session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id VARCHAR(255) NOT NULL,
            start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            end_time TIMESTAMP WITH TIME ZONE,
            session_type VARCHAR(50),
            topic_summary TEXT,
            message_count INTEGER DEFAULT 0,
            last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            CONSTRAINT sessions_user_id_check CHECK (char_length(user_id) > 0)
        );
        
        CREATE INDEX IF NOT EXISTS idx_sessions_user_time 
        ON conversation_sessions(user_id, start_time DESC);
        
        CREATE INDEX IF NOT EXISTS idx_sessions_active 
        ON conversation_sessions(user_id, last_activity DESC) 
        WHERE end_time IS NULL;
        
        -- Performance monitoring table
        CREATE TABLE IF NOT EXISTS conversation_metrics (
            metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            conversation_id UUID REFERENCES conversations(conversation_id),
            retrieval_time_ms INTEGER,
            context_size_chars INTEGER,
            sources_used TEXT[], -- ['redis', 'postgresql', 'chromadb', 'neo4j']
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            CONSTRAINT metrics_retrieval_time_check CHECK (retrieval_time_ms >= 0),
            CONSTRAINT metrics_context_size_check CHECK (context_size_chars >= 0)
        );
        
        CREATE INDEX IF NOT EXISTS idx_metrics_conversation 
        ON conversation_metrics(conversation_id, timestamp DESC);
        
        CREATE INDEX IF NOT EXISTS idx_metrics_performance 
        ON conversation_metrics(timestamp DESC, retrieval_time_ms);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
            self.logger.debug("Database schema ensured")
    
    async def store_conversation(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store complete conversation with full fidelity"""
        
        if not self.pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        
        conversation_id = str(uuid.uuid4())
        metadata = metadata or {}
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO conversations (
                        conversation_id, user_id, channel_id, user_message, 
                        bot_response, session_id, thread_id, message_type,
                        emotion_data, user_metadata, processing_metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, 
                    conversation_id,
                    user_id,
                    metadata.get('channel_id'),
                    user_message,
                    bot_response,
                    metadata.get('session_id'),
                    metadata.get('thread_id'),
                    metadata.get('message_type', 'conversation'),
                    json.dumps(metadata.get('emotion_data')) if metadata.get('emotion_data') else None,
                    json.dumps(metadata.get('user_metadata')) if metadata.get('user_metadata') else None,
                    json.dumps(metadata.get('processing_metadata')) if metadata.get('processing_metadata') else None
                )
                
                # Update session if provided
                if metadata.get('session_id'):
                    await self._update_session_activity(conn, metadata['session_id'], user_id)
                
                self.logger.debug("Stored conversation %s for user %s", conversation_id, user_id)
                return conversation_id
                
        except Exception as e:
            self.logger.error("Failed to store conversation: %s", e)
            raise
    
    async def _update_session_activity(self, conn, session_id: str, user_id: str):
        """Update session activity and message count"""
        try:
            await conn.execute("""
                INSERT INTO conversation_sessions (session_id, user_id, message_count, last_activity)
                VALUES ($1, $2, 1, NOW())
                ON CONFLICT (session_id) 
                DO UPDATE SET 
                    message_count = conversation_sessions.message_count + 1,
                    last_activity = NOW()
            """, session_id, user_id)
        except Exception as e:
            self.logger.warning("Failed to update session activity: %s", e)
    
    async def get_conversations(
        self,
        conversation_ids: List[str],
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Get full conversation details by IDs"""
        
        if not conversation_ids or not self.pool:
            return []
        
        try:
            async with self.pool.acquire() as conn:
                if include_metadata:
                    query = """
                        SELECT conversation_id, user_id, channel_id, user_message,
                               bot_response, timestamp, session_id, thread_id, 
                               message_type, emotion_data, user_metadata, processing_metadata
                        FROM conversations 
                        WHERE conversation_id = ANY($1::uuid[])
                        ORDER BY timestamp DESC
                    """
                else:
                    query = """
                        SELECT conversation_id, user_id, user_message, bot_response, timestamp
                        FROM conversations 
                        WHERE conversation_id = ANY($1::uuid[])
                        ORDER BY timestamp DESC
                    """
                
                rows = await conn.fetch(query, conversation_ids)
                
                conversations = []
                for row in rows:
                    conversation = dict(row)
                    # Convert UUID to string for JSON serialization
                    conversation['conversation_id'] = str(conversation['conversation_id'])
                    
                    # Parse JSON fields if they exist
                    if include_metadata:
                        for field in ['emotion_data', 'user_metadata', 'processing_metadata']:
                            if conversation.get(field):
                                try:
                                    conversation[field] = json.loads(conversation[field])
                                except (json.JSONDecodeError, TypeError):
                                    conversation[field] = None
                    
                    conversations.append(conversation)
                    
                self.logger.debug("Retrieved %d conversations", len(conversations))
                return conversations
                
        except Exception as e:
            self.logger.error("Failed to retrieve conversations: %s", e)
            return []
    
    async def get_user_conversation_history(
        self,
        user_id: str,
        limit: int = 50,
        since_days: int = 30,
        session_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get chronological conversation history for user"""
        
        if not self.pool:
            return []
        
        since_date = datetime.now() - timedelta(days=since_days)
        
        try:
            async with self.pool.acquire() as conn:
                # Build query based on filters
                where_conditions = ["user_id = $1", "timestamp >= $2"]
                params = [user_id, since_date]
                
                if session_id:
                    where_conditions.append(f"session_id = ${len(params) + 1}")
                    params.append(session_id)
                
                if thread_id:
                    where_conditions.append(f"thread_id = ${len(params) + 1}")
                    params.append(thread_id)
                
                query = f"""
                    SELECT conversation_id, user_message, bot_response, timestamp,
                           session_id, thread_id, message_type
                    FROM conversations 
                    WHERE {' AND '.join(where_conditions)}
                    ORDER BY timestamp DESC
                    LIMIT ${len(params) + 1}
                """
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                
                conversations = []
                for row in rows:
                    conversation = dict(row)
                    conversation['conversation_id'] = str(conversation['conversation_id'])
                    conversations.append(conversation)
                
                self.logger.debug("Retrieved %d conversations for user %s", len(conversations), user_id)
                return conversations
                
        except Exception as e:
            self.logger.error("Failed to retrieve user history: %s", e)
            return []
    
    async def search_conversations(
        self,
        user_id: str,
        search_query: str,
        limit: int = 20,
        since_days: int = 90
    ) -> List[Dict[str, Any]]:
        """Full-text search conversations for user"""
        
        if not self.pool:
            return []
        
        since_date = datetime.now() - timedelta(days=since_days)
        
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT conversation_id, user_message, bot_response, timestamp,
                           ts_rank(to_tsvector('english', user_message || ' ' || bot_response), 
                                  plainto_tsquery('english', $3)) as rank
                    FROM conversations 
                    WHERE user_id = $1 
                      AND timestamp >= $2
                      AND to_tsvector('english', user_message || ' ' || bot_response) 
                          @@ plainto_tsquery('english', $3)
                    ORDER BY rank DESC, timestamp DESC
                    LIMIT $4
                """
                
                rows = await conn.fetch(query, user_id, since_date, search_query, limit)
                
                conversations = []
                for row in rows:
                    conversation = dict(row)
                    conversation['conversation_id'] = str(conversation['conversation_id'])
                    conversations.append(conversation)
                
                self.logger.debug("Found %d conversations matching search for user %s", 
                               len(conversations), user_id)
                return conversations
                
        except Exception as e:
            self.logger.error("Failed to search conversations: %s", e)
            return []
    
    async def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """Get conversation statistics for user"""
        
        if not self.pool:
            return {}
        
        try:
            async with self.pool.acquire() as conn:
                stats_query = """
                    SELECT 
                        COUNT(*) as total_conversations,
                        COUNT(DISTINCT DATE(timestamp)) as days_active,
                        MIN(timestamp) as first_conversation,
                        MAX(timestamp) as last_conversation,
                        COUNT(DISTINCT session_id) as unique_sessions,
                        AVG(char_length(user_message)) as avg_user_message_length,
                        AVG(char_length(bot_response)) as avg_bot_response_length
                    FROM conversations 
                    WHERE user_id = $1
                """
                
                row = await conn.fetchrow(stats_query, user_id)
                
                if row:
                    stats = dict(row)
                    # Convert datetime objects to strings
                    for field in ['first_conversation', 'last_conversation']:
                        if stats[field]:
                            stats[field] = stats[field].isoformat()
                    
                    # Calculate additional metrics
                    if stats['total_conversations'] > 0:
                        days_span = (datetime.now() - datetime.fromisoformat(stats['first_conversation'].replace('+00:00', ''))).days
                        stats['conversations_per_day'] = stats['total_conversations'] / max(days_span, 1)
                    else:
                        stats['conversations_per_day'] = 0
                    
                    return stats
                
                return {}
                
        except Exception as e:
            self.logger.error("Failed to get conversation stats: %s", e)
            return {}
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID"""
        
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM conversations WHERE conversation_id = $1",
                    conversation_id
                )
                
                deleted = result.split()[-1] == '1'  # Check if 1 row was deleted
                
                if deleted:
                    self.logger.debug("Deleted conversation %s", conversation_id)
                
                return deleted
                
        except Exception as e:
            self.logger.error("Failed to delete conversation %s: %s", conversation_id, e)
            return False
    
    async def create_session(
        self,
        user_id: str,
        session_type: str = "general",
        topic_summary: Optional[str] = None
    ) -> str:
        """Create a new conversation session"""
        
        if not self.pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        
        session_id = str(uuid.uuid4())
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO conversation_sessions (session_id, user_id, session_type, topic_summary)
                    VALUES ($1, $2, $3, $4)
                """, session_id, user_id, session_type, topic_summary)
                
                self.logger.debug("Created session %s for user %s", session_id, user_id)
                return session_id
                
        except Exception as e:
            self.logger.error("Failed to create session: %s", e)
            raise
    
    async def close_session(self, session_id: str) -> bool:
        """Close an active session"""
        
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE conversation_sessions 
                    SET end_time = NOW() 
                    WHERE session_id = $1 AND end_time IS NULL
                """, session_id)
                
                closed = result.split()[-1] == '1'
                
                if closed:
                    self.logger.debug("Closed session %s", session_id)
                
                return closed
                
        except Exception as e:
            self.logger.error("Failed to close session %s: %s", session_id, e)
            return False
    
    async def store_performance_metric(
        self,
        conversation_id: str,
        retrieval_time_ms: int,
        context_size_chars: int,
        sources_used: List[str]
    ):
        """Store performance metrics for monitoring"""
        
        if not self.pool:
            return
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO conversation_metrics 
                    (conversation_id, retrieval_time_ms, context_size_chars, sources_used)
                    VALUES ($1, $2, $3, $4)
                """, conversation_id, retrieval_time_ms, context_size_chars, sources_used)
                
        except Exception as e:
            self.logger.warning("Failed to store performance metric: %s", e)
    
    async def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get performance metrics for the last N days"""
        
        if not self.pool:
            return {}
        
        since_date = datetime.now() - timedelta(days=days)
        
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        COUNT(*) as total_queries,
                        AVG(retrieval_time_ms) as avg_retrieval_time_ms,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY retrieval_time_ms) as p95_retrieval_time_ms,
                        AVG(context_size_chars) as avg_context_size_chars,
                        MAX(context_size_chars) as max_context_size_chars,
                        COUNT(DISTINCT unnest(sources_used)) as unique_sources
                    FROM conversation_metrics
                    WHERE timestamp >= $1
                """
                
                row = await conn.fetchrow(query, since_date)
                
                if row:
                    return dict(row)
                
                return {}
                
        except Exception as e:
            self.logger.error("Failed to get performance metrics: %s", e)
            return {}
    
    async def ping(self) -> bool:
        """Check if PostgreSQL connection is alive"""
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            self.logger.error("PostgreSQL ping failed: %s", e)
            return False
    
    async def cleanup_old_conversations(self, days_to_keep: int = 365) -> int:
        """Cleanup conversations older than specified days"""
        
        if not self.pool:
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM conversations WHERE timestamp < $1",
                    cutoff_date
                )
                
                deleted_count = int(result.split()[-1])
                self.logger.info("Cleaned up %d old conversations", deleted_count)
                return deleted_count
                
        except Exception as e:
            self.logger.error("Failed to cleanup old conversations: %s", e)
            return 0
    
    async def close(self):
        """Close the database connection pool"""
        if self.pool:
            await self.pool.close()
            self.logger.info("PostgreSQL connection pool closed")


# Utility functions

async def create_postgresql_archive(database_url: str) -> PostgreSQLConversationArchive:
    """Create and initialize a PostgreSQL archive instance"""
    archive = PostgreSQLConversationArchive(database_url)
    await archive.initialize()
    return archive

async def test_postgresql_performance():
    """Test PostgreSQL archive performance"""
    import os
    
    # Use test database URL or default
    db_url = os.getenv('TEST_DATABASE_URL', 'postgresql://localhost/whisperengine_test')
    
    archive = await create_postgresql_archive(db_url)
    
    import time
    
    # Test data
    user_id = "test_user"
    test_conversations = []
    
    # Store test conversations
    start_time = time.time()
    for i in range(100):
        conversation_id = await archive.store_conversation(
            user_id=user_id,
            user_message=f"Test message {i}",
            bot_response=f"Test response {i}",
            metadata={"test": True, "index": i}
        )
        test_conversations.append(conversation_id)
    
    store_time = time.time() - start_time
    
    # Test retrieval
    start_time = time.time()
    retrieved = await archive.get_conversations(test_conversations[:10])
    retrieve_time = time.time() - start_time
    
    # Test search
    start_time = time.time()
    search_results = await archive.search_conversations(user_id, "test message")
    search_time = time.time() - start_time
    
    # Cleanup
    for conv_id in test_conversations:
        await archive.delete_conversation(conv_id)
    
    await archive.close()
    
    print(f"Store performance: {store_time:.4f}s for 100 conversations")
    print(f"Retrieve performance: {retrieve_time:.4f}s for 10 conversations")
    print(f"Search performance: {search_time:.4f}s, found {len(search_results)} results")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_postgresql_performance())