from typing import List, Dict, Any
import uuid
import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from loguru import logger
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
from src_v2.core.database import db_manager
from src_v2.config.settings import settings
from src_v2.memory.embeddings import EmbeddingService

class MemoryManager:
    def __init__(self):
        self.collection_name = f"whisperengine_memory_{settings.DISCORD_BOT_NAME}" if settings.DISCORD_BOT_NAME else "whisperengine_memory_default"
        self.embedding_service = EmbeddingService()

    async def initialize(self):
        """
        Creates the necessary tables and collections if they don't exist.
        """
        await self._initialize_postgres()
        await self._initialize_qdrant()

    async def _initialize_postgres(self):
        if not db_manager.postgres_pool:
            logger.warning("Postgres pool not available, memory persistence disabled.")
            return
            
        # We now use Alembic for schema management.
        # This method just verifies connectivity.
        try:
            async with db_manager.postgres_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            logger.info("Postgres connection verified.")
        except Exception as e:
            logger.error(f"Postgres connection failed: {e}")

    async def _initialize_qdrant(self):
        if not db_manager.qdrant_client:
            logger.warning("Qdrant client not available, vector memory disabled.")
            return
            
        try:
            # Check if collection exists
            collections_response = await db_manager.qdrant_client.get_collections()
            collections = collections_response.collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                
                # Define named vectors configuration (matching WE1)
                vectors_config = {
                    "content": VectorParams(size=384, distance=Distance.COSINE),
                    "emotion": VectorParams(size=384, distance=Distance.COSINE),
                    "semantic": VectorParams(size=384, distance=Distance.COSINE)
                }
                
                await db_manager.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=vectors_config
                )
                logger.info("Qdrant collection initialized with named vectors.")
            else:
                logger.info(f"Qdrant collection {self.collection_name} already exists.")
                
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")

    async def add_message(self, user_id: str, character_name: str, role: str, content: str):
        """
        Adds a message to the history.
        role: 'human' or 'ai'
        """
        if not db_manager.postgres_pool:
            return

        try:
            async with db_manager.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO v2_chat_history (user_id, character_name, role, content)
                    VALUES ($1, $2, $3, $4)
                """, str(user_id), character_name, role, content)
            
            # Also save to vector memory
            await self._save_vector_memory(user_id, role, content)
            
        except Exception as e:
            logger.error(f"Failed to save message: {e}")

    async def _save_vector_memory(self, user_id: str, role: str, content: str):
        """
        Embeds and saves the message to Qdrant using named vectors.
        """
        if not db_manager.qdrant_client:
            return

        try:
            # Generate embeddings for each named vector asynchronously
            # TODO: Implement proper emotion and semantic extraction logic from WE1
            content_embedding = await self.embedding_service.embed_query_async(content)
            emotion_embedding = await self.embedding_service.embed_query_async(f"emotion: {content}")
            semantic_embedding = await self.embedding_service.embed_query_async(f"concept: {content}")
            
            # Create payload
            payload = {
                "user_id": str(user_id),
                "role": role,
                "content": content,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Upsert to Qdrant
            point_id = str(uuid.uuid4())
            await db_manager.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector={
                            "content": content_embedding,
                            "emotion": emotion_embedding,
                            "semantic": semantic_embedding
                        },
                        payload=payload
                    )
                ]
            )
            logger.debug(f"Saved vector memory for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to save vector memory: {e}")

    async def search_memories(self, query: str, user_id: str, limit: int = 5, vector_name: str = "content") -> List[Dict[str, Any]]:
        """
        Searches for relevant memories in Qdrant.
        """
        if not db_manager.qdrant_client:
            return []

        try:
            embedding = await self.embedding_service.embed_query_async(query)
            
            # Search with filter for user_id
            
            search_result = await db_manager.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=(vector_name, embedding), # Tuple for named vector search
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=str(user_id))
                        )
                    ]
                ),
                limit=limit
            )
            
            return [
                {
                    "content": hit.payload.get("content"),
                    "role": hit.payload.get("role"),
                    "score": hit.score,
                    "timestamp": hit.payload.get("timestamp")
                }
                for hit in search_result
            ]
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def clear_memory(self, user_id: str, character_name: str):
        """
        Clears all memory for a specific user and character from both Postgres and Qdrant.
        """
        # 1. Clear Postgres
        if db_manager.postgres_pool:
            try:
                async with db_manager.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        DELETE FROM v2_chat_history 
                        WHERE user_id = $1 AND character_name = $2
                    """, str(user_id), character_name)
                logger.info(f"Cleared Postgres history for user {user_id} and character {character_name}")
            except Exception as e:
                logger.error(f"Failed to clear Postgres history: {e}")

        # 2. Clear Qdrant
        if db_manager.qdrant_client:
            try:
                await db_manager.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector=Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=str(user_id))
                            )
                        ]
                    )
                )
                logger.info(f"Cleared Qdrant memory for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to clear Qdrant memory: {e}")

    async def get_recent_history(self, user_id: str, character_name: str, limit: int = 10) -> List[BaseMessage]:
        """
        Retrieves the recent chat history for a user and character.
        """
        if not db_manager.postgres_pool:
            return []

        messages = []
        try:
            async with db_manager.postgres_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT role, content 
                    FROM v2_chat_history 
                    WHERE user_id = $1 AND character_name = $2
                    ORDER BY timestamp DESC
                    LIMIT $3
                """, str(user_id), character_name, limit)
                
                # Reverse to get chronological order
                for row in reversed(rows):
                    if row['role'] == 'human':
                        messages.append(HumanMessage(content=row['content']))
                    elif row['role'] == 'ai':
                        messages.append(AIMessage(content=row['content']))
                        
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            
        return messages

# Global instance
memory_manager = MemoryManager()
