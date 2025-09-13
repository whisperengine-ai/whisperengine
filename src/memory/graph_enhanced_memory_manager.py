"""Graph-enhanced memory manager that integrates with existing ChromaDB system."""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import asyncio

from src.memory.memory_manager import UserMemoryManager
from src.graph_database.neo4j_connector import get_neo4j_connector, Neo4jConnector
from src.graph_database.models import (
    UserNode, MemoryNode, TopicNode, EmotionContextNode, RelationshipData
)

logger = logging.getLogger(__name__)


class GraphEnhancedMemoryManager(UserMemoryManager):
    """Memory manager enhanced with graph database for relationship tracking."""
    
    def __init__(self, *args, **kwargs):
        """Initialize with graph database support."""
        super().__init__(*args, **kwargs)
        self._neo4j_connector: Optional[Neo4jConnector] = None
        self._graph_enabled = True
        
    async def _get_graph_connector(self) -> Optional[Neo4jConnector]:
        """Get Neo4j connector, handling connection failures gracefully."""
        if not self._graph_enabled:
            return None
            
        try:
            if self._neo4j_connector is None:
                self._neo4j_connector = await get_neo4j_connector()
            return self._neo4j_connector
        except Exception as e:
            logger.warning(f"Neo4j connection failed, falling back to ChromaDB only: {e}")
            self._graph_enabled = False
            return None
    
    async def store_conversation_enhanced(self, user_id: str, message: str, 
                                        response: str, emotion_data: Optional[Dict] = None,
                                        topics: Optional[List[str]] = None) -> str:
        """Store conversation with graph relationship building."""
        
        # Store in ChromaDB using existing functionality
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.store_conversation, user_id, message, response
            )
        except Exception as e:
            logger.error(f"Failed to store conversation in ChromaDB: {e}")
            raise
        
        # Generate memory ID for graph linking
        memory_id = str(uuid.uuid4())
        chromadb_id = f"{user_id}_{int(datetime.now().timestamp())}"
        
        # Extract topics if not provided
        if topics is None:
            topics = await self._extract_topics_from_message(message)
        
        # Build graph relationships
        graph_connector = await self._get_graph_connector()
        if graph_connector:
            try:
                await self._create_graph_memory(
                    memory_id=memory_id,
                    user_id=user_id,
                    chromadb_id=chromadb_id,
                    message=message,
                    response=response,
                    topics=topics,
                    emotion_data=emotion_data
                )
                logger.debug(f"Created graph relationships for memory {memory_id}")
            except Exception as e:
                logger.warning(f"Failed to create graph relationships: {e}")
        
        return memory_id
    
    async def _extract_topics_from_message(self, message: str) -> List[str]:
        """Extract topics from message using simple keyword extraction."""
        # Simple topic extraction - in production, you might use NLP
        topics = []
        
        # Common topic indicators
        topic_keywords = {
            "work": ["work", "job", "career", "office", "meeting", "project"],
            "family": ["family", "mom", "dad", "parent", "child", "sibling"],
            "hobby": ["hobby", "interest", "play", "game", "sport", "music"],
            "health": ["health", "doctor", "medical", "sick", "exercise"],
            "food": ["food", "eat", "restaurant", "cook", "meal", "hungry"],
            "travel": ["travel", "trip", "vacation", "visit", "journey"],
            "technology": ["computer", "phone", "app", "software", "tech"],
            "personal": ["feel", "think", "believe", "personal", "private"]
        }
        
        message_lower = message.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)
        
        # If no topics found, use generic
        if not topics:
            topics = ["general"]
        
        return topics
    
    async def _create_graph_memory(self, memory_id: str, user_id: str, 
                                 chromadb_id: str, message: str, response: str,
                                 topics: List[str], emotion_data: Optional[Dict] = None):
        """Create memory node and relationships in graph database."""
        
        graph_connector = await self._get_graph_connector()
        if not graph_connector:
            return
        
        # Ensure user exists in graph
        await graph_connector.create_or_update_user(
            user_id=user_id,
            discord_id=user_id,  # Assuming user_id is discord_id
            name=f"User_{user_id[-4:]}"  # Simple name from ID
        )
        
        # Create memory with relationships
        summary = f"{message[:100]}..." if len(message) > 100 else message
        importance = await self._calculate_importance(message, emotion_data)
        
        await graph_connector.create_memory_with_relationships(
            memory_id=memory_id,
            user_id=user_id,
            chromadb_id=chromadb_id,
            summary=summary,
            topics=topics,
            emotion_data=emotion_data,
            importance=importance
        )
    
    async def _calculate_importance(self, message: str, emotion_data: Optional[Dict] = None) -> float:
        """Calculate memory importance based on content and emotion."""
        importance = 0.5  # Base importance
        
        # Increase importance for emotional content
        if emotion_data:
            emotion_intensity = emotion_data.get("intensity", 0.5)
            importance += emotion_intensity * 0.3
        
        # Increase importance for longer messages
        if len(message) > 200:
            importance += 0.1
        
        # Increase importance for questions or requests
        if any(word in message.lower() for word in ["help", "how", "what", "why", "?", "please"]):
            importance += 0.2
        
        # Cap at 1.0
        return min(importance, 1.0)
    
    async def get_personalized_context(self, user_id: str, current_message: str, 
                                     limit: int = 10) -> Dict[str, Any]:
        """Get context that considers emotional associations and relationship depth."""
        
        # Get standard ChromaDB context
        try:
            chromadb_context = await asyncio.get_event_loop().run_in_executor(
                None, self.retrieve_relevant_memories, user_id, current_message, limit
            )
        except Exception as e:
            logger.error(f"Failed to retrieve ChromaDB memories: {e}")
            chromadb_context = []
        
        # Enhance with graph context
        graph_context = {}
        graph_connector = await self._get_graph_connector()
        if graph_connector:
            try:
                # Extract topics from current message
                topics = await self._extract_topics_from_message(current_message)
                
                # Get graph-enhanced memories
                graph_memories = []
                for topic in topics:
                    topic_memories = await graph_connector.get_contextual_memories(
                        user_id, topic, limit=5
                    )
                    graph_memories.extend(topic_memories)
                
                # Get relationship context
                relationship_context = await graph_connector.get_user_relationship_context(user_id)
                emotional_patterns = await graph_connector.get_emotional_patterns(user_id)
                
                graph_context = {
                    "graph_memories": graph_memories,
                    "relationship_context": relationship_context,
                    "emotional_patterns": emotional_patterns,
                    "topics": topics
                }
                
            except Exception as e:
                logger.warning(f"Failed to retrieve graph context: {e}")
        
        return {
            "chromadb_memories": chromadb_context,
            "graph_context": graph_context,
            "total_memories": len(chromadb_context) + len(graph_context.get("graph_memories", []))
        }
    
    async def generate_personalized_system_prompt(self, user_id: str, 
                                                current_message: str) -> str:
        """Generate system prompt based on graph relationship analysis."""
        
        graph_connector = await self._get_graph_connector()
        if not graph_connector:
            return ""  # Fallback to existing system prompt
        
        try:
            # Get relationship context
            relationship_context = await graph_connector.get_user_relationship_context(user_id)
            emotional_patterns = await graph_connector.get_emotional_patterns(user_id)
            
            prompt_elements = []
            
            # Relationship-specific tone
            intimacy_level = relationship_context.get("intimacy_level", 0.3)
            memory_count = relationship_context.get("memory_count", 0)
            
            if intimacy_level >= 0.8:
                prompt_elements.append(
                    f"You have a close relationship with this user. You've shared "
                    f"{memory_count} conversations together. Be warm, personal, and "
                    f"reference shared experiences when appropriate."
                )
            elif intimacy_level >= 0.5:
                prompt_elements.append(
                    f"You have a developing relationship with this user. You've had "
                    f"{memory_count} conversations. Be friendly and show you remember "
                    f"previous discussions."
                )
            else:
                prompt_elements.append(
                    "This user is relatively new to you. Be helpful and friendly "
                    "while building rapport."
                )
            
            # Emotional sensitivity
            triggers = emotional_patterns.get("triggers", [])
            if triggers:
                sensitive_topics = [
                    t["topic"] for t in triggers 
                    if t.get("avg_intensity", 0) > 0.7
                ]
                if sensitive_topics:
                    prompt_elements.append(
                        f"Be particularly sensitive when discussing: {', '.join(sensitive_topics[:3])}. "
                        f"These topics have previously caused strong emotional reactions."
                    )
            
            # Interest areas
            topics = relationship_context.get("topics", [])
            if topics:
                interest_topics = [t["name"] for t in topics[:5]]
                prompt_elements.append(
                    f"The user has shown interest in: {', '.join(interest_topics)}. "
                    f"Feel free to relate conversations to these areas."
                )
            
            return "\n\n".join(prompt_elements)
            
        except Exception as e:
            logger.warning(f"Failed to generate personalized prompt: {e}")
            return ""
    
    async def update_relationship_milestone(self, user_id: str, milestone_level: str, 
                                          context: str = ""):
        """Update relationship progression milestone."""
        
        graph_connector = await self._get_graph_connector()
        if not graph_connector:
            return
        
        try:
            query = """
            MATCH (u:User {id: $user_id})
            MERGE (bot:User {id: 'bot'})
            MERGE (u)-[r:RELATIONSHIP_MILESTONE {level: $level}]->(bot)
            SET r.achieved_at = datetime(),
                r.context = $context
            ON CREATE SET r.created_at = datetime()
            """
            
            await graph_connector.execute_write_query(query, {
                "user_id": user_id,
                "level": milestone_level,
                "context": context
            })
            
            logger.info(f"Updated relationship milestone for {user_id}: {milestone_level}")
            
        except Exception as e:
            logger.warning(f"Failed to update relationship milestone: {e}")
    
    async def analyze_conversation_for_milestones(self, user_id: str, message: str, 
                                                response: str) -> Optional[str]:
        """Analyze conversation to detect relationship milestones."""
        
        message_lower = message.lower()
        response_lower = response.lower()
        
        # First name sharing
        if any(phrase in message_lower for phrase in ["my name is", "i'm ", "call me"]):
            await self.update_relationship_milestone(user_id, "first_name", "User shared their name")
            return "first_name"
        
        # Personal information sharing
        personal_indicators = ["my family", "my job", "my work", "i work", "i feel", "personal"]
        if any(indicator in message_lower for indicator in personal_indicators):
            await self.update_relationship_milestone(user_id, "shared_personal", "User shared personal information")
            return "shared_personal"
        
        # Trust indicators
        trust_indicators = ["secret", "don't tell", "between us", "confidential", "private"]
        if any(indicator in message_lower for indicator in trust_indicators):
            await self.update_relationship_milestone(user_id, "trusted_with_secret", "User shared confidential information")
            return "trusted_with_secret"
        
        return None
    
    async def get_graph_health_status(self) -> Dict[str, Any]:
        """Get health status of graph database connection."""
        
        graph_connector = await self._get_graph_connector()
        if not graph_connector:
            return {
                "status": "disabled",
                "message": "Graph database is disabled or unavailable"
            }
        
        try:
            health = await graph_connector.health_check()
            return health
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {e}"
            }
    
    # Override existing methods to include graph functionality
    async def store_conversation_async(self, user_id: str, message: str, response: str):
        """Async wrapper for conversation storage with graph enhancement."""
        
        # Detect emotion if emotion manager is available
        emotion_data = None
        if hasattr(self, 'emotion_manager') and self.emotion_manager:
            try:
                emotion_data = await asyncio.get_event_loop().run_in_executor(
                    None, self.emotion_manager.analyze_emotion, message
                )
            except Exception as e:
                logger.warning(f"Emotion analysis failed: {e}")
        
        # Store with graph enhancement
        memory_id = await self.store_conversation_enhanced(
            user_id, message, response, emotion_data
        )
        
        # Analyze for relationship milestones
        milestone = await self.analyze_conversation_for_milestones(user_id, message, response)
        if milestone:
            logger.info(f"Relationship milestone achieved for {user_id}: {milestone}")
        
        return memory_id
