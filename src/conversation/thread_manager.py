"""
Conversation Thread Manager for WhisperEngine
Manages conversation threads and their storage in ChromaDB.
"""

import asyncio
import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Individual message within a conversation"""

    id: str
    content: str
    sender: str  # 'user' or 'assistant'
    timestamp: str
    metadata: dict[str, Any] | None = None
    files: list[dict[str, Any]] | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.files is None:
            self.files = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "content": self.content,
            "sender": self.sender,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {},
            "files": self.files or [],
        }


@dataclass
class ConversationThread:
    """A conversation thread containing multiple messages"""

    id: str
    title: str
    user_id: str
    created_at: str
    updated_at: str
    messages: list[ConversationMessage] | None = None
    metadata: dict[str, Any] | None = None
    is_archived: bool = False
    tags: list[str] | None = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []

    def add_message(self, message: ConversationMessage):
        """Add a message to this thread"""
        if self.messages is None:
            self.messages = []
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()

    def get_message_count(self) -> int:
        """Get the number of messages in this thread"""
        return len(self.messages) if self.messages else 0

    def get_last_message(self) -> ConversationMessage | None:
        """Get the most recent message"""
        return self.messages[-1] if self.messages else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [asdict(msg) for msg in (self.messages or [])],
            "metadata": self.metadata,
            "is_archived": self.is_archived,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationThread":
        """Create from dictionary"""
        messages = [ConversationMessage(**msg) for msg in data.get("messages", [])]
        return cls(
            id=data["id"],
            title=data["title"],
            user_id=data["user_id"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            messages=messages,
            metadata=data.get("metadata", {}),
            is_archived=data.get("is_archived", False),
            tags=data.get("tags", []),
        )


class ConversationThreadManager:
    """Manages conversation threads"""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or Path.home() / ".whisperengine" / "conversations"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # SQLite database for persistent storage
        self.db_path = self.data_dir / "conversations.db"
        self.threads_cache: dict[str, ConversationThread] = {}
        self.user_threads: dict[str, list[str]] = {}  # user_id -> [thread_ids]

        # Initialize database
        asyncio.create_task(self.initialize_database())

    async def initialize_database(self):
        """Initialize SQLite database for conversation storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_archived BOOLEAN DEFAULT FALSE,
                        tags TEXT DEFAULT '[]',
                        metadata TEXT DEFAULT '{}',
                        message_count INTEGER DEFAULT 0
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        sender TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}',
                        files TEXT DEFAULT '[]',
                        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    )
                """
                )

                # Create indexes for performance
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)"
                )

                conn.commit()

            logger.info(f"Conversation database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize conversation database: {e}")

    async def create_conversation(
        self, user_id: str, title: str | None = None, initial_message: str | None = None
    ) -> ConversationThread:
        """Create a new conversation thread"""
        try:
            # Generate conversation ID
            timestamp = int(datetime.now().timestamp() * 1000)
            conversation_id = f"conv_{user_id}_{timestamp}"

            # Generate title if not provided
            if not title:
                if initial_message:
                    # Use first 30 characters of message as title
                    title = (
                        initial_message[:30] + "..."
                        if len(initial_message) > 30
                        else initial_message
                    )
                else:
                    title = f"Conversation {datetime.now().strftime('%H:%M')}"

            # Create conversation thread
            thread = ConversationThread(
                id=conversation_id,
                title=title,
                user_id=user_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )

            # Add initial message if provided
            if initial_message:
                message = ConversationMessage(
                    id=f"msg_{conversation_id}_{timestamp}",
                    content=initial_message,
                    sender="user",
                    timestamp=datetime.now().isoformat(),
                )
                thread.add_message(message)

            # Store in database
            await self.save_conversation(thread)

            # Cache the thread
            self.threads_cache[conversation_id] = thread

            # Update user threads index
            if user_id not in self.user_threads:
                self.user_threads[user_id] = []
            self.user_threads[user_id].append(conversation_id)

            logger.info(f"Created conversation {conversation_id} for user {user_id}")
            return thread

        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise

    async def get_conversation(self, conversation_id: str) -> ConversationThread | None:
        """Get a conversation by ID"""
        try:
            # Check cache first
            if conversation_id in self.threads_cache:
                return self.threads_cache[conversation_id]

            # Load from database
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Get conversation metadata
                conv_row = conn.execute(
                    "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
                ).fetchone()

                if not conv_row:
                    return None

                # Get messages
                message_rows = conn.execute(
                    "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp",
                    (conversation_id,),
                ).fetchall()

                # Build conversation object
                messages = []
                for row in message_rows:
                    message = ConversationMessage(
                        id=row["id"],
                        content=row["content"],
                        sender=row["sender"],
                        timestamp=row["timestamp"],
                        metadata=json.loads(row["metadata"]),
                        files=json.loads(row["files"]),
                    )
                    messages.append(message)

                thread = ConversationThread(
                    id=conv_row["id"],
                    title=conv_row["title"],
                    user_id=conv_row["user_id"],
                    created_at=conv_row["created_at"],
                    updated_at=conv_row["updated_at"],
                    messages=messages,
                    metadata=json.loads(conv_row["metadata"]),
                    is_archived=bool(conv_row["is_archived"]),
                    tags=json.loads(conv_row["tags"]),
                )

                # Cache the thread
                self.threads_cache[conversation_id] = thread
                return thread

        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            return None

    async def get_user_conversations(
        self, user_id: str, include_archived: bool = False
    ) -> list[ConversationThread]:
        """Get all conversations for a user"""
        try:
            conversations = []

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = "SELECT * FROM conversations WHERE user_id = ?"
                params = [user_id]

                if not include_archived:
                    query += " AND is_archived = FALSE"

                query += " ORDER BY updated_at DESC"

                rows = conn.execute(query, params).fetchall()

                for row in rows:
                    # Load full conversation (including messages)
                    thread = await self.get_conversation(row["id"])
                    if thread:
                        conversations.append(thread)

            return conversations

        except Exception as e:
            logger.error(f"Failed to get conversations for user {user_id}: {e}")
            return []

    async def add_message_to_conversation(
        self, conversation_id: str, message: ConversationMessage
    ) -> bool:
        """Add a message to an existing conversation"""
        try:
            # Get the conversation
            thread = await self.get_conversation(conversation_id)
            if not thread:
                logger.error(f"Conversation {conversation_id} not found")
                return False

            # Add message to thread
            thread.add_message(message)

            # Save to database
            await self.save_message(conversation_id, message)
            await self.update_conversation_timestamp(conversation_id)

            # Update cache
            self.threads_cache[conversation_id] = thread

            return True

        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            return False

    async def save_conversation(self, thread: ConversationThread):
        """Save conversation to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Insert or update conversation
                conn.execute(
                    """
                    INSERT OR REPLACE INTO conversations
                    (id, user_id, title, created_at, updated_at, is_archived, tags, metadata, message_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        thread.id,
                        thread.user_id,
                        thread.title,
                        thread.created_at,
                        thread.updated_at,
                        thread.is_archived,
                        json.dumps(thread.tags),
                        json.dumps(thread.metadata),
                        len(thread.messages or []),
                    ),
                )

                # Save all messages
                for message in thread.messages or []:
                    await self.save_message(thread.id, message, conn)

                conn.commit()

        except Exception as e:
            logger.error(f"Failed to save conversation {thread.id}: {e}")
            raise

    async def save_message(self, conversation_id: str, message: ConversationMessage, conn=None):
        """Save a single message to database"""
        try:
            if conn is None:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO messages
                        (id, conversation_id, content, sender, timestamp, metadata, files)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            message.id,
                            conversation_id,
                            message.content,
                            message.sender,
                            message.timestamp,
                            json.dumps(message.metadata),
                            json.dumps(message.files),
                        ),
                    )
                    conn.commit()
            else:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO messages
                    (id, conversation_id, content, sender, timestamp, metadata, files)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        message.id,
                        conversation_id,
                        message.content,
                        message.sender,
                        message.timestamp,
                        json.dumps(message.metadata),
                        json.dumps(message.files),
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to save message {message.id}: {e}")
            raise

    async def update_conversation_timestamp(self, conversation_id: str):
        """Update the last updated timestamp for a conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), conversation_id),
                )
                conn.commit()

            # Update cache if present
            if conversation_id in self.threads_cache:
                self.threads_cache[conversation_id].updated_at = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Failed to update timestamp for conversation {conversation_id}: {e}")

    async def rename_conversation(self, conversation_id: str, new_title: str) -> bool:
        """Rename a conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                    (new_title, datetime.now().isoformat(), conversation_id),
                )
                conn.commit()

            # Update cache if present
            if conversation_id in self.threads_cache:
                self.threads_cache[conversation_id].title = new_title
                self.threads_cache[conversation_id].updated_at = datetime.now().isoformat()

            logger.info(f"Renamed conversation {conversation_id} to '{new_title}'")
            return True

        except Exception as e:
            logger.error(f"Failed to rename conversation {conversation_id}: {e}")
            return False

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete messages first (foreign key constraint)
                conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                # Delete conversation
                conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                conn.commit()

            # Remove from cache
            if conversation_id in self.threads_cache:
                del self.threads_cache[conversation_id]

            # Remove from user threads index
            for _user_id, thread_ids in self.user_threads.items():
                if conversation_id in thread_ids:
                    thread_ids.remove(conversation_id)
                    break

            logger.info(f"Deleted conversation {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False

    async def archive_conversation(self, conversation_id: str) -> bool:
        """Archive a conversation (soft delete)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE conversations SET is_archived = TRUE, updated_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), conversation_id),
                )
                conn.commit()

            # Update cache if present
            if conversation_id in self.threads_cache:
                self.threads_cache[conversation_id].is_archived = True
                self.threads_cache[conversation_id].updated_at = datetime.now().isoformat()

            logger.info(f"Archived conversation {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to archive conversation {conversation_id}: {e}")
            return False

    async def search_conversations(
        self, user_id: str, query: str, limit: int = 20
    ) -> list[ConversationThread]:
        """Search conversations by content"""
        try:
            conversations = []

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Search in conversation titles and message content
                rows = conn.execute(
                    """
                    SELECT DISTINCT c.id
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    WHERE c.user_id = ? AND c.is_archived = FALSE
                    AND (c.title LIKE ? OR m.content LIKE ?)
                    ORDER BY c.updated_at DESC
                    LIMIT ?
                """,
                    (user_id, f"%{query}%", f"%{query}%", limit),
                ).fetchall()

                for row in rows:
                    thread = await self.get_conversation(row["id"])
                    if thread:
                        conversations.append(thread)

            return conversations

        except Exception as e:
            logger.error(f"Failed to search conversations for user {user_id}: {e}")
            return []

    async def get_conversation_stats(self, user_id: str) -> dict[str, Any]:
        """Get conversation statistics for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                stats = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_conversations,
                        COUNT(CASE WHEN is_archived = FALSE THEN 1 END) as active_conversations,
                        COUNT(CASE WHEN is_archived = TRUE THEN 1 END) as archived_conversations,
                        SUM(message_count) as total_messages
                    FROM conversations
                    WHERE user_id = ?
                """,
                    (user_id,),
                ).fetchone()

                return {
                    "total_conversations": stats["total_conversations"] or 0,
                    "active_conversations": stats["active_conversations"] or 0,
                    "archived_conversations": stats["archived_conversations"] or 0,
                    "total_messages": stats["total_messages"] or 0,
                }

        except Exception as e:
            logger.error(f"Failed to get conversation stats for user {user_id}: {e}")
            return {
                "total_conversations": 0,
                "active_conversations": 0,
                "archived_conversations": 0,
                "total_messages": 0,
            }

    async def export_conversation(
        self, conversation_id: str, format: str = "json"
    ) -> dict[str, Any] | None:
        """Export a conversation in the specified format"""
        try:
            thread = await self.get_conversation(conversation_id)
            if not thread:
                return None

            if format.lower() == "json":
                return thread.to_dict()
            elif format.lower() == "markdown":
                return self._export_as_markdown(thread)
            elif format.lower() == "txt":
                return self._export_as_text(thread)
            else:
                return thread.to_dict()

        except Exception as e:
            logger.error(f"Failed to export conversation {conversation_id}: {e}")
            return None

    def _export_as_markdown(self, thread: ConversationThread) -> dict[str, Any]:
        """Export conversation as markdown format"""
        markdown_content = f"# {thread.title}\n\n"
        markdown_content += f"**Created:** {thread.created_at}  \n"
        markdown_content += f"**Last Updated:** {thread.updated_at}  \n"
        markdown_content += f"**Messages:** {len(thread.messages or [])}  \n\n"

        if thread.tags:
            markdown_content += f"**Tags:** {', '.join(thread.tags)}  \n\n"

        markdown_content += "---\n\n"

        for message in thread.messages or []:
            sender_label = "🧑 **User**" if message.sender == "user" else "🤖 **Assistant**"
            markdown_content += f"### {sender_label}\n"
            markdown_content += f"*{message.timestamp}*\n\n"
            markdown_content += f"{message.content}\n\n"

            if message.files:
                markdown_content += "**Attachments:**\n"
                for file_info in message.files:
                    file_name = file_info.get("name", "unknown")
                    file_type = file_info.get("type", "unknown")
                    markdown_content += f"- {file_name} ({file_type})\n"
                markdown_content += "\n"

        return {
            "format": "markdown",
            "content": markdown_content,
            "filename": f"{thread.title.replace(' ', '_')}.md",
        }

    def _export_as_text(self, thread: ConversationThread) -> dict[str, Any]:
        """Export conversation as plain text format"""
        text_content = f"Conversation: {thread.title}\n"
        text_content += f"Created: {thread.created_at}\n"
        text_content += f"Last Updated: {thread.updated_at}\n"
        text_content += f"Messages: {len(thread.messages or [])}\n"

        if thread.tags:
            text_content += f"Tags: {', '.join(thread.tags)}\n"

        text_content += "\n" + "=" * 50 + "\n\n"

        for message in thread.messages or []:
            sender_label = "USER" if message.sender == "user" else "ASSISTANT"
            text_content += f"[{sender_label}] {message.timestamp}\n"
            text_content += f"{message.content}\n"

            if message.files:
                text_content += "Attachments:\n"
                for file_info in message.files:
                    file_name = file_info.get("name", "unknown")
                    file_type = file_info.get("type", "unknown")
                    text_content += f"  - {file_name} ({file_type})\n"

            text_content += "\n" + "-" * 30 + "\n\n"

        return {
            "format": "text",
            "content": text_content,
            "filename": f"{thread.title.replace(' ', '_')}.txt",
        }

    async def add_tag_to_conversation(self, conversation_id: str, tag: str) -> bool:
        """Add a tag to a conversation"""
        try:
            thread = await self.get_conversation(conversation_id)
            if not thread:
                return False

            # Normalize tag
            tag = tag.strip().lower()
            if not tag:
                return False

            # Add tag if not already present
            if thread.tags is None:
                thread.tags = []

            if tag not in thread.tags:
                thread.tags.append(tag)

                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "UPDATE conversations SET tags = ?, updated_at = ? WHERE id = ?",
                        (json.dumps(thread.tags), datetime.now().isoformat(), conversation_id),
                    )
                    conn.commit()

                # Update cache
                self.threads_cache[conversation_id] = thread

                logger.info(f"Added tag '{tag}' to conversation {conversation_id}")
                return True

            return True  # Tag already exists

        except Exception as e:
            logger.error(f"Failed to add tag to conversation {conversation_id}: {e}")
            return False

    async def remove_tag_from_conversation(self, conversation_id: str, tag: str) -> bool:
        """Remove a tag from a conversation"""
        try:
            thread = await self.get_conversation(conversation_id)
            if not thread:
                return False

            # Normalize tag
            tag = tag.strip().lower()

            # Remove tag if present
            if thread.tags is None:
                thread.tags = []

            if tag in thread.tags:
                thread.tags.remove(tag)

                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "UPDATE conversations SET tags = ?, updated_at = ? WHERE id = ?",
                        (json.dumps(thread.tags), datetime.now().isoformat(), conversation_id),
                    )
                    conn.commit()

                # Update cache
                self.threads_cache[conversation_id] = thread

                logger.info(f"Removed tag '{tag}' from conversation {conversation_id}")
                return True

            return True  # Tag wasn't there anyway

        except Exception as e:
            logger.error(f"Failed to remove tag from conversation {conversation_id}: {e}")
            return False

    async def get_conversations_by_tag(self, user_id: str, tag: str) -> list[ConversationThread]:
        """Get all conversations with a specific tag"""
        try:
            conversations = []
            tag = tag.strip().lower()

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                rows = conn.execute(
                    """
                    SELECT * FROM conversations
                    WHERE user_id = ? AND is_archived = FALSE
                    AND tags LIKE ?
                    ORDER BY updated_at DESC
                """,
                    (user_id, f'%"{tag}"%'),
                ).fetchall()

                for row in rows:
                    # Load full conversation and verify tag match
                    thread = await self.get_conversation(row["id"])
                    if thread and thread.tags and tag in thread.tags:
                        conversations.append(thread)

            return conversations

        except Exception as e:
            logger.error(f"Failed to get conversations by tag '{tag}' for user {user_id}: {e}")
            return []

    async def get_all_tags(self, user_id: str) -> list[str]:
        """Get all unique tags used by a user"""
        try:
            all_tags = set()

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                rows = conn.execute(
                    "SELECT tags FROM conversations WHERE user_id = ? AND is_archived = FALSE",
                    (user_id,),
                ).fetchall()

                for row in rows:
                    try:
                        tags = json.loads(row["tags"])
                        all_tags.update(tags)
                    except (json.JSONDecodeError, TypeError):
                        continue

            return sorted(all_tags)

        except Exception as e:
            logger.error(f"Failed to get all tags for user {user_id}: {e}")
            return []

    async def merge_conversations(
        self, source_conversation_id: str, target_conversation_id: str
    ) -> bool:
        """Merge one conversation into another"""
        try:
            source_thread = await self.get_conversation(source_conversation_id)
            target_thread = await self.get_conversation(target_conversation_id)

            if not source_thread or not target_thread:
                logger.error("One or both conversations not found for merging")
                return False

            if source_thread.user_id != target_thread.user_id:
                logger.error("Cannot merge conversations from different users")
                return False

            # Merge messages
            if target_thread.messages is None:
                target_thread.messages = []
            target_thread.messages.extend(source_thread.messages or [])

            # Sort messages by timestamp
            target_thread.messages.sort(key=lambda msg: msg.timestamp)

            # Merge tags
            if target_thread.tags is None:
                target_thread.tags = []
            if source_thread.tags:
                target_thread.tags.extend(
                    [tag for tag in source_thread.tags if tag not in target_thread.tags]
                )

            # Update target conversation
            target_thread.updated_at = datetime.now().isoformat()

            # Save merged conversation
            await self.save_conversation(target_thread)

            # Delete source conversation
            await self.delete_conversation(source_conversation_id)

            logger.info(
                f"Merged conversation {source_conversation_id} into {target_conversation_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to merge conversations: {e}")
            return False

    def cleanup_cache(self):
        """Clean up cached conversations to free memory"""
        # Keep only the most recently accessed conversations
        max_cache_size = 50
        if len(self.threads_cache) > max_cache_size:
            # Sort by access time (or updated_at) and keep only the most recent
            sorted_threads = sorted(
                self.threads_cache.items(), key=lambda x: x[1].updated_at, reverse=True
            )

            # Keep only the most recent conversations
            self.threads_cache = dict(sorted_threads[:max_cache_size])
            logger.info(
                f"Cleaned up conversation cache, kept {max_cache_size} most recent conversations"
            )
