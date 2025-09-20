# src/memory/tiers/tier3_chromadb_summaries.py

import chromadb
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChromaDBSemanticSummaries:
    """
    Tier 3: Semantic search on conversation summaries
    Stores ~150 character summaries for efficient vector search
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000, embedding_function=None):
        self.host = host
        self.port = port
        self.embedding_function = embedding_function
        self.client = None
        self.summaries_collection = None
        self.topics_collection = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize ChromaDB client and collections"""
        try:
            # Create ChromaDB client
            self.client = chromadb.HttpClient(host=self.host, port=self.port)
            
            # Create or get summaries collection
            self.summaries_collection = self.client.get_or_create_collection(
                name="conversation_summaries_v2",
                metadata={
                    "description": "Semantic summaries of conversations for efficient search",
                    "version": "2.0",
                    "created": datetime.now().isoformat()
                },
                embedding_function=self.embedding_function
            )
            
            # Create or get topics collection for enhanced topical search
            self.topics_collection = self.client.get_or_create_collection(
                name="conversation_topics_v2",
                metadata={
                    "description": "Topic-based conversation indexing",
                    "version": "2.0",
                    "created": datetime.now().isoformat()
                },
                embedding_function=self.embedding_function
            )
            
            self.logger.info("ChromaDB semantic summaries tier initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize ChromaDB summaries: %s", e)
            raise
        
    async def store_summary(
        self,
        conversation_id: str,
        user_id: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store conversation summary for semantic search"""
        
        if not self.summaries_collection:
            raise RuntimeError("ChromaDB summaries collection not initialized")
        
        doc_id = f"summary_{conversation_id}"
        
        # Prepare metadata
        doc_metadata = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "type": "conversation_summary",
            "summary_length": len(summary),
            "summary_hash": self._hash_content(summary)
        }
        
        # Add provided metadata
        if metadata:
            # Extract key fields for searchability
            if "topics" in metadata:
                doc_metadata["topics"] = metadata["topics"][:5]  # Limit topics
            
            if "intent" in metadata:
                doc_metadata["intent"] = metadata["intent"]
            
            if "emotion_data" in metadata:
                emotion_data = metadata["emotion_data"]
                if isinstance(emotion_data, dict):
                    # Extract primary emotion if available
                    primary_emotion = emotion_data.get("primary_emotion", "neutral")
                    doc_metadata["primary_emotion"] = primary_emotion
                    
                    # Extract emotional intensity
                    intensity = emotion_data.get("intensity", 0.5)
                    doc_metadata["emotional_intensity"] = float(intensity)
            
            if "session_id" in metadata:
                doc_metadata["session_id"] = metadata["session_id"]
            
            if "channel_id" in metadata:
                doc_metadata["channel_id"] = metadata["channel_id"]
        
        try:
            # Store in summaries collection
            self.summaries_collection.add(
                documents=[summary],
                metadatas=[doc_metadata],
                ids=[doc_id]
            )
            
            # Also store topics if available for topical search
            if metadata and "topics" in metadata:
                await self._store_topic_mapping(conversation_id, user_id, metadata["topics"])
            
            self.logger.debug("Stored summary for conversation %s", conversation_id)
            
        except Exception as e:
            self.logger.error("Failed to store summary for conversation %s: %s", conversation_id, e)
            raise
    
    async def _store_topic_mapping(self, conversation_id: str, user_id: str, topics: List[str]):
        """Store topic mappings for enhanced topical search"""
        
        if not self.topics_collection or not topics:
            return
        
        try:
            for i, topic in enumerate(topics[:3]):  # Limit to top 3 topics
                topic_doc_id = f"topic_{conversation_id}_{i}"
                
                topic_metadata = {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "topic": topic.lower(),
                    "topic_index": i,
                    "timestamp": datetime.now().isoformat(),
                    "type": "topic_mapping"
                }
                
                # Use topic as document content for semantic similarity
                self.topics_collection.add(
                    documents=[f"Discussion about {topic}"],
                    metadatas=[topic_metadata],
                    ids=[topic_doc_id]
                )
            
        except Exception as e:
            self.logger.warning("Failed to store topic mapping: %s", e)
    
    async def search_summaries(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        time_decay: bool = True,
        include_emotions: bool = False,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search conversation summaries semantically"""
        
        if not self.summaries_collection:
            return []
        
        try:
            # Build query filters - temporarily use only user_id to test ChromaDB
            where_filter = {"user_id": user_id}
            
            # TODO: Add back type filtering once ChromaDB query syntax is resolved
            # if session_id:
            #     where_filter["session_id"] = session_id
            
            # Search summaries
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
                    
                    # Calculate relevance score
                    relevance_score = 1 - distance
                    
                    # Apply time decay if requested
                    if time_decay:
                        relevance_score = self._apply_time_decay(
                            relevance_score, 
                            metadata.get("timestamp")
                        )
                    
                    # Apply emotion filtering if requested
                    if include_emotions and "primary_emotion" in metadata:
                        emotion_boost = self._calculate_emotion_boost(metadata)
                        relevance_score *= emotion_boost
                    
                    summary_result = {
                        "conversation_id": metadata.get("conversation_id"),
                        "summary": doc,
                        "relevance_score": relevance_score,
                        "timestamp": metadata.get("timestamp"),
                        "topics": metadata.get("topics", []),
                        "intent": metadata.get("intent", "unknown"),
                        "metadata": metadata
                    }
                    
                    summaries.append(summary_result)
            
            # Sort by relevance score
            summaries.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            self.logger.debug("Found %d relevant summaries for user %s", len(summaries), user_id)
            return summaries
            
        except Exception as e:
            self.logger.error("Failed to search summaries: %s", e)
            return []
    
    async def search_by_topics(
        self,
        user_id: str,
        topics: List[str],
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Search conversations by specific topics"""
        
        if not self.topics_collection or not topics:
            return []
        
        try:
            # Search for topic mappings
            topic_query = " ".join([f"Discussion about {topic}" for topic in topics])
            
            results = self.topics_collection.query(
                query_texts=[topic_query],
                where={"user_id": user_id, "type": "topic_mapping"},
                n_results=limit * 2,  # Get more results to filter
                include=["documents", "metadatas", "distances"]
            )
            
            topic_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    
                    topic_result = {
                        "conversation_id": metadata.get("conversation_id"),
                        "topic": metadata.get("topic"),
                        "relevance_score": 1 - distance,
                        "timestamp": metadata.get("timestamp")
                    }
                    
                    topic_results.append(topic_result)
            
            # Group by conversation and take top results
            conversation_scores = {}
            for result in topic_results:
                conv_id = result["conversation_id"]
                if conv_id not in conversation_scores:
                    conversation_scores[conv_id] = result
                else:
                    # Keep the highest scoring topic for each conversation
                    if result["relevance_score"] > conversation_scores[conv_id]["relevance_score"]:
                        conversation_scores[conv_id] = result
            
            # Sort and limit
            final_results = list(conversation_scores.values())
            final_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            self.logger.debug("Found %d topic-based results for user %s", len(final_results), user_id)
            return final_results[:limit]
            
        except Exception as e:
            self.logger.error("Failed to search by topics: %s", e)
            return []
    
    async def get_user_conversation_themes(
        self,
        user_id: str,
        days: int = 30,
        min_occurrences: int = 2
    ) -> List[Dict[str, Any]]:
        """Get recurring conversation themes for user"""
        
        if not self.topics_collection:
            return []
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            # Get all topics for user in time range
            results = self.topics_collection.get(
                where={
                    "user_id": user_id,
                    "type": "topic_mapping",
                    "timestamp": {"$gte": since_date}
                },
                include=["metadatas"]
            )
            
            # Count topic occurrences
            topic_counts = {}
            topic_conversations = {}
            
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    topic = metadata.get("topic", "").lower()
                    conv_id = metadata.get("conversation_id")
                    
                    if topic and conv_id:
                        if topic not in topic_counts:
                            topic_counts[topic] = 0
                            topic_conversations[topic] = set()
                        
                        topic_counts[topic] += 1
                        topic_conversations[topic].add(conv_id)
            
            # Filter and format themes
            themes = []
            for topic, count in topic_counts.items():
                if count >= min_occurrences:
                    theme = {
                        "topic": topic,
                        "occurrence_count": count,
                        "unique_conversations": len(topic_conversations[topic]),
                        "conversation_ids": list(topic_conversations[topic])
                    }
                    themes.append(theme)
            
            # Sort by occurrence count
            themes.sort(key=lambda x: x["occurrence_count"], reverse=True)
            
            self.logger.debug("Found %d recurring themes for user %s", len(themes), user_id)
            return themes
            
        except Exception as e:
            self.logger.error("Failed to get conversation themes: %s", e)
            return []
    
    def _apply_time_decay(self, base_score: float, timestamp_str: Optional[str]) -> float:
        """Apply time decay to favor recent conversations"""
        if not timestamp_str:
            return base_score
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            days_ago = (datetime.now() - timestamp).days
            
            # Decay factor: 1.0 for today, 0.9 for 1 week ago, 0.8 for 1 month ago
            decay_factor = max(0.5, 1.0 - (days_ago * 0.01))
            return base_score * decay_factor
            
        except (ValueError, TypeError):
            return base_score
    
    def _calculate_emotion_boost(self, metadata: Dict[str, Any]) -> float:
        """Calculate emotional relevance boost"""
        try:
            primary_emotion = metadata.get("primary_emotion", "neutral")
            intensity = metadata.get("emotional_intensity", 0.5)
            
            # Boost scores for high-emotion conversations
            emotion_weights = {
                "joy": 1.2,
                "excitement": 1.2,
                "anger": 1.1,
                "sadness": 1.1,
                "fear": 1.1,
                "surprise": 1.1,
                "neutral": 1.0
            }
            
            base_boost = emotion_weights.get(primary_emotion, 1.0)
            intensity_boost = 1.0 + (intensity * 0.2)  # Up to 20% boost for high intensity
            
            return base_boost * intensity_boost
            
        except (TypeError, ValueError):
            return 1.0
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def delete_summary(self, conversation_id: str) -> bool:
        """Delete a conversation summary"""
        
        if not self.summaries_collection:
            return False
        
        doc_id = f"summary_{conversation_id}"
        
        try:
            # Delete from summaries collection
            self.summaries_collection.delete(ids=[doc_id])
            
            # Delete related topic mappings
            if self.topics_collection:
                # Get topic mappings for this conversation
                results = self.topics_collection.get(
                    where={"conversation_id": conversation_id},
                    include=["ids"]
                )
                
                if results["ids"]:
                    self.topics_collection.delete(ids=results["ids"])
            
            self.logger.debug("Deleted summary for conversation %s", conversation_id)
            return True
            
        except Exception as e:
            self.logger.error("Failed to delete summary for conversation %s: %s", conversation_id, e)
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        
        stats = {
            "summaries_collection": {},
            "topics_collection": {},
            "status": "healthy"
        }
        
        try:
            if self.summaries_collection:
                summary_count = self.summaries_collection.count()
                stats["summaries_collection"] = {
                    "document_count": summary_count,
                    "collection_name": "conversation_summaries_v2"
                }
            
            if self.topics_collection:
                topic_count = self.topics_collection.count()
                stats["topics_collection"] = {
                    "document_count": topic_count,
                    "collection_name": "conversation_topics_v2"
                }
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get collection stats: %s", e)
            stats["status"] = "error"
            stats["error"] = str(e)
            return stats
    
    async def ping(self) -> bool:
        """Check if ChromaDB connection is alive"""
        try:
            if self.client:
                # Simple heartbeat check
                self.client.heartbeat()
                return True
            return False
        except Exception as e:
            self.logger.error("ChromaDB ping failed: %s", e)
            return False
    
    async def cleanup_old_summaries(self, days_to_keep: int = 365) -> int:
        """Cleanup summaries older than specified days"""
        
        if not self.summaries_collection:
            return 0
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        try:
            # Get old summaries
            results = self.summaries_collection.get(
                where={"timestamp": {"$lt": cutoff_date}},
                include=["ids"]
            )
            
            deleted_count = 0
            if results["ids"]:
                # Delete old summaries
                self.summaries_collection.delete(ids=results["ids"])
                deleted_count = len(results["ids"])
                
                # Also cleanup related topic mappings
                if self.topics_collection:
                    topic_results = self.topics_collection.get(
                        where={"timestamp": {"$lt": cutoff_date}},
                        include=["ids"]
                    )
                    
                    if topic_results["ids"]:
                        self.topics_collection.delete(ids=topic_results["ids"])
            
            self.logger.info("Cleaned up %d old summaries", deleted_count)
            return deleted_count
            
        except Exception as e:
            self.logger.error("Failed to cleanup old summaries: %s", e)
            return 0


# Utility functions

async def create_chromadb_summaries(host: str = "localhost", port: int = 8000, embedding_function=None) -> ChromaDBSemanticSummaries:
    """Create and initialize a ChromaDB summaries instance"""
    summaries = ChromaDBSemanticSummaries(host, port, embedding_function)
    await summaries.initialize()
    return summaries

async def test_chromadb_summaries_performance():
    """Test ChromaDB summaries performance"""
    summaries = await create_chromadb_summaries()
    
    import time
    import uuid
    
    user_id = "test_user"
    test_conversations = []
    
    # Generate test summaries
    test_data = [
        ("Asked about machine learning concepts", ["machine_learning", "ai", "concepts"]),
        ("Discussed programming best practices", ["programming", "coding", "best_practices"]),
        ("Requested help with Python debugging", ["python", "debugging", "help"]),
        ("Talked about career advice", ["career", "advice", "professional"]),
        ("Asked about data science tools", ["data_science", "tools", "analytics"])
    ]
    
    # Store test summaries
    start_time = time.time()
    for summary, topics in test_data:
        conversation_id = str(uuid.uuid4())
        test_conversations.append(conversation_id)
        
        await summaries.store_summary(
            conversation_id=conversation_id,
            user_id=user_id,
            summary=summary,
            metadata={
                "topics": topics,
                "intent": "question",
                "session_id": str(uuid.uuid4())
            }
        )
    
    store_time = time.time() - start_time
    
    # Test semantic search
    start_time = time.time()
    search_results = await summaries.search_summaries(
        user_id=user_id,
        query="machine learning and programming",
        limit=3
    )
    search_time = time.time() - start_time
    
    # Test topic search
    start_time = time.time()
    topic_results = await summaries.search_by_topics(
        user_id=user_id,
        topics=["programming", "python"],
        limit=2
    )
    topic_search_time = time.time() - start_time
    
    # Cleanup
    for conv_id in test_conversations:
        await summaries.delete_summary(conv_id)
    
    print(f"Store performance: {store_time:.4f}s for {len(test_data)} summaries")
    print(f"Search performance: {search_time:.4f}s, found {len(search_results)} results")
    print(f"Topic search performance: {topic_search_time:.4f}s, found {len(topic_results)} results")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chromadb_summaries_performance())