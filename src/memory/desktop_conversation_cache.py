#!/usr/bin/env python3
"""
Desktop Conversation Cache
Lightweight, file-based conversation caching for desktop mode
Replaces Redis with SQLite + in-memory caching for optimal performance
"""

import sqlite3
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CachedMessage:
    """Lightweight message representation for caching"""
    content: str
    author_id: str
    author_name: str
    timestamp: str
    bot: bool = False
    message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DesktopConversationCache:
    """
    Desktop-optimized conversation cache combining:
    - SQLite for persistence (replaces Redis for desktop mode)
    - In-memory cache for performance (recent conversations)
    - Automatic cleanup and size management
    """
    
    def __init__(self, 
                 data_dir: str = "data/cache",
                 max_memory_conversations: int = 50,
                 max_messages_per_conversation: int = 100,
                 cache_ttl_hours: int = 24):
        """
        Initialize desktop conversation cache
        
        Args:
            data_dir: Directory for SQLite database
            max_memory_conversations: Max conversations in memory
            max_messages_per_conversation: Max messages per conversation
            cache_ttl_hours: TTL for cached conversations
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "conversations.db"
        self.max_memory_conversations = max_memory_conversations
        self.max_messages_per_conversation = max_messages_per_conversation
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        
        # In-memory cache for active conversations
        self.memory_cache: Dict[str, List[CachedMessage]] = {}
        self.cache_access_times: Dict[str, datetime] = {}
        self.lock = threading.RLock()
        
        # SQLite connection (thread-local)
        self._local = threading.local()
        
        self.initialized = False
    
    @property
    def db_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
        return self._local.connection
    
    async def initialize(self) -> bool:
        """Initialize the cache system"""
        try:
            # Create database tables
            await self._create_tables()
            
            # Load recent conversations into memory
            await self._load_recent_to_memory()
            
            # Start background cleanup task
            asyncio.create_task(self._background_cleanup())
            
            self.initialized = True
            logger.info(f"✅ Desktop conversation cache initialized (db: {self.db_path})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize desktop conversation cache: {e}")
            return False
    
    async def _create_tables(self):
        """Create SQLite tables for conversation storage"""
        conn = self.db_connection
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                content TEXT NOT NULL,
                author_id TEXT NOT NULL,
                author_name TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                is_bot BOOLEAN NOT NULL DEFAULT 0,
                message_id TEXT,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
            )
        """)
        
        # Create indexes for performance
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation 
            ON messages (conversation_id, timestamp DESC)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user 
            ON conversations (user_id, last_activity DESC)
        """)
        
        conn.commit()
    
    async def _load_recent_to_memory(self):
        """Load recent active conversations into memory cache"""
        try:
            conn = self.db_connection
            
            # Get recent active conversations
            cutoff_time = datetime.now() - self.cache_ttl
            cursor = conn.execute("""
                SELECT conversation_id 
                FROM conversations 
                WHERE last_activity > ? 
                ORDER BY last_activity DESC 
                LIMIT ?
            """, (cutoff_time, self.max_memory_conversations))
            
            conversation_ids = [row[0] for row in cursor.fetchall()]
            
            # Load messages for each conversation
            for conv_id in conversation_ids:
                messages = await self._load_conversation_from_db(conv_id)
                if messages:
                    with self.lock:
                        self.memory_cache[conv_id] = messages
                        self.cache_access_times[conv_id] = datetime.now()
            
            logger.debug(f"Loaded {len(conversation_ids)} conversations into memory cache")
            
        except Exception as e:
            logger.warning(f"Failed to load conversations to memory: {e}")
    
    async def _load_conversation_from_db(self, conversation_id: str) -> List[CachedMessage]:
        """Load conversation messages from SQLite"""
        try:
            conn = self.db_connection
            cursor = conn.execute("""
                SELECT content, author_id, author_name, timestamp, is_bot, message_id, metadata
                FROM messages 
                WHERE conversation_id = ? 
                ORDER BY timestamp ASC
                LIMIT ?
            """, (conversation_id, self.max_messages_per_conversation))
            
            messages = []
            for row in cursor:
                metadata = json.loads(row[6]) if row[6] else {}
                messages.append(CachedMessage(
                    content=row[0],
                    author_id=row[1],
                    author_name=row[2],
                    timestamp=row[3],
                    bot=bool(row[4]),
                    message_id=row[5],
                    metadata=metadata
                ))
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to load conversation {conversation_id} from DB: {e}")
            return []
    
    async def add_message(self, conversation_id: str, message: Any):
        """Add message to conversation cache"""
        try:
            # Convert message to CachedMessage format
            cached_msg = self._convert_to_cached_message(message)
            
            # Add to memory cache
            with self.lock:
                if conversation_id not in self.memory_cache:
                    self.memory_cache[conversation_id] = []
                
                self.memory_cache[conversation_id].append(cached_msg)
                self.cache_access_times[conversation_id] = datetime.now()
                
                # Trim if too long
                if len(self.memory_cache[conversation_id]) > self.max_messages_per_conversation:
                    self.memory_cache[conversation_id] = self.memory_cache[conversation_id][-self.max_messages_per_conversation:]
            
            # Persist to SQLite asynchronously
            await self._persist_message_to_db(conversation_id, cached_msg)
            
        except Exception as e:
            logger.error(f"Failed to add message to cache: {e}")
    
    def _convert_to_cached_message(self, message: Any) -> CachedMessage:
        """Convert various message formats to CachedMessage"""
        if hasattr(message, 'content'):
            # Discord message
            return CachedMessage(
                content=str(message.content),
                author_id=str(message.author.id),
                author_name=getattr(message.author, 'display_name', str(message.author.name)),
                timestamp=message.created_at.isoformat() if hasattr(message, 'created_at') else datetime.now().isoformat(),
                bot=getattr(message.author, 'bot', False),
                message_id=str(message.id) if hasattr(message, 'id') else None
            )
        elif isinstance(message, dict):
            # Dictionary format
            return CachedMessage(
                content=message.get('content', ''),
                author_id=message.get('author_id', ''),
                author_name=message.get('author_name', 'Unknown'),
                timestamp=message.get('timestamp', datetime.now().isoformat()),
                bot=message.get('bot', False),
                message_id=message.get('message_id'),
                metadata=message.get('metadata', {})
            )
        else:
            # String or other format
            return CachedMessage(
                content=str(message),
                author_id='unknown',
                author_name='Unknown',
                timestamp=datetime.now().isoformat(),
                bot=False
            )
    
    async def _persist_message_to_db(self, conversation_id: str, message: CachedMessage):
        """Persist message to SQLite database"""
        try:
            conn = self.db_connection
            
            # Insert or update conversation record
            conn.execute("""
                INSERT OR REPLACE INTO conversations 
                (conversation_id, user_id, last_activity, message_count) 
                VALUES (?, ?, ?, 
                    COALESCE((SELECT message_count FROM conversations WHERE conversation_id = ?), 0) + 1)
            """, (conversation_id, message.author_id, datetime.now(), conversation_id))
            
            # Insert message
            conn.execute("""
                INSERT INTO messages 
                (conversation_id, content, author_id, author_name, timestamp, is_bot, message_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation_id,
                message.content,
                message.author_id,
                message.author_name,
                message.timestamp,
                message.bot,
                message.message_id,
                json.dumps(message.metadata)
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to persist message to DB: {e}")
    
    async def get_user_conversation_context(self, 
                                           channel, 
                                           user_id: int, 
                                           limit: int = 15,
                                           exclude_message_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation context for user (compatible with existing interface)"""
        try:
            conversation_id = self._get_conversation_id(channel, user_id)
            
            # Try memory cache first
            with self.lock:
                if conversation_id in self.memory_cache:
                    self.cache_access_times[conversation_id] = datetime.now()
                    messages = self.memory_cache[conversation_id][-limit:]
                else:
                    # Load from database
                    messages = await self._load_conversation_from_db(conversation_id)
                    if messages:
                        self.memory_cache[conversation_id] = messages
                        self.cache_access_times[conversation_id] = datetime.now()
                        messages = messages[-limit:]
                    else:
                        messages = []
            
            # Convert to expected format
            result = []
            for msg in messages:
                if exclude_message_id and msg.message_id == str(exclude_message_id):
                    continue
                
                result.append({
                    'content': msg.content,
                    'author_id': msg.author_id,
                    'author_name': msg.author_name,
                    'timestamp': msg.timestamp,
                    'bot': msg.bot,
                    'from_cache': True
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return []
    
    def _get_conversation_id(self, channel, user_id: int) -> str:
        """Generate conversation ID from channel and user"""
        if hasattr(channel, 'id'):
            return f"conv_{channel.id}_{user_id}"
        else:
            return f"conv_web_{user_id}"
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            conn = self.db_connection
            
            # Memory cache stats
            memory_conversations = len(self.memory_cache)
            memory_messages = sum(len(msgs) for msgs in self.memory_cache.values())
            
            # Database stats
            cursor = conn.execute("SELECT COUNT(*) FROM conversations")
            total_conversations = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            
            return {
                "memory_conversations": memory_conversations,
                "memory_messages": memory_messages,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "cache_type": "desktop_sqlite",
                "db_path": str(self.db_path),
                "cache_ttl_hours": self.cache_ttl.total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}
    
    def clear_channel_cache(self, channel_id: str):
        """Clear cache for specific channel"""
        try:
            conversation_pattern = f"conv_{channel_id}_"
            
            with self.lock:
                # Clear from memory
                keys_to_remove = [key for key in self.memory_cache.keys() if key.startswith(conversation_pattern)]
                for key in keys_to_remove:
                    del self.memory_cache[key]
                    self.cache_access_times.pop(key, None)
            
            # Clear from database
            conn = self.db_connection
            cursor = conn.execute("SELECT conversation_id FROM conversations WHERE conversation_id LIKE ?", (f"{conversation_pattern}%",))
            conversation_ids = [row[0] for row in cursor.fetchall()]
            
            for conv_id in conversation_ids:
                conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
                conn.execute("DELETE FROM conversations WHERE conversation_id = ?", (conv_id,))
            
            conn.commit()
            logger.info(f"Cleared cache for channel {channel_id}")
            
        except Exception as e:
            logger.error(f"Failed to clear channel cache: {e}")
    
    async def _background_cleanup(self):
        """Background task to clean up old data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean memory cache
                await self._cleanup_memory_cache()
                
                # Clean database
                await self._cleanup_database()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")
    
    async def _cleanup_memory_cache(self):
        """Clean up memory cache based on LRU and TTL"""
        try:
            now = datetime.now()
            cutoff_time = now - self.cache_ttl
            
            with self.lock:
                # Remove expired conversations
                expired_keys = [
                    key for key, access_time in self.cache_access_times.items()
                    if access_time < cutoff_time
                ]
                
                for key in expired_keys:
                    self.memory_cache.pop(key, None)
                    self.cache_access_times.pop(key, None)
                
                # If still too many, remove least recently used
                if len(self.memory_cache) > self.max_memory_conversations:
                    sorted_by_access = sorted(
                        self.cache_access_times.items(),
                        key=lambda x: x[1]
                    )
                    
                    excess_count = len(self.memory_cache) - self.max_memory_conversations
                    for key, _ in sorted_by_access[:excess_count]:
                        self.memory_cache.pop(key, None)
                        self.cache_access_times.pop(key, None)
            
            logger.debug(f"Memory cache cleanup: {len(expired_keys)} expired conversations removed")
            
        except Exception as e:
            logger.error(f"Memory cache cleanup failed: {e}")
    
    async def _cleanup_database(self):
        """Clean up old database records"""
        try:
            cutoff_time = datetime.now() - timedelta(days=30)  # Keep 30 days
            
            conn = self.db_connection
            
            # Delete old messages
            cursor = conn.execute("DELETE FROM messages WHERE timestamp < ?", (cutoff_time,))
            deleted_messages = cursor.rowcount
            
            # Delete conversations with no messages
            cursor = conn.execute("""
                DELETE FROM conversations 
                WHERE conversation_id NOT IN (SELECT DISTINCT conversation_id FROM messages)
            """)
            deleted_conversations = cursor.rowcount
            
            conn.commit()
            
            # Vacuum database periodically
            if deleted_messages > 1000:
                conn.execute("VACUUM")
            
            logger.debug(f"Database cleanup: {deleted_messages} messages, {deleted_conversations} conversations removed")
            
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
    
    async def close(self):
        """Close the cache and cleanup resources"""
        try:
            # Close database connections
            if hasattr(self._local, 'connection'):
                self._local.connection.close()
            
            # Clear memory cache
            with self.lock:
                self.memory_cache.clear()
                self.cache_access_times.clear()
            
            logger.info("Desktop conversation cache closed")
            
        except Exception as e:
            logger.error(f"Error closing conversation cache: {e}")


# Factory function for easy integration
def create_desktop_conversation_cache(**kwargs) -> DesktopConversationCache:
    """Create and return a desktop conversation cache instance"""
    return DesktopConversationCache(**kwargs)