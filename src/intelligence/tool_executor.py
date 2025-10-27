"""
Tool Executor - Executes LLM tool calls for the Hybrid Query Router.

This module implements the ToolExecutor class that handles execution of the 5 core tools:
1. query_user_facts - Query PostgreSQL user_fact_relationships
2. recall_conversation_context - Query Qdrant conversation history
3. query_character_backstory - Query PostgreSQL CDL database
4. query_temporal_trends - Query InfluxDB metrics
5. summarize_user_relationship - Multi-source aggregation

Architecture:
- Each tool is implemented as an async method
- Tools access existing infrastructure (PostgreSQL, Qdrant, InfluxDB)
- Results are formatted for LLM consumption
- Comprehensive error handling and logging

Design Document: docs/architecture/hybrid-routing-initiative/HYBRID_QUERY_ROUTING_DESIGN.md
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Executes LLM tool calls for the Hybrid Query Router.
    
    This class handles execution of all 5 core tools, accessing existing
    infrastructure (PostgreSQL, Qdrant, InfluxDB) and formatting results
    for LLM consumption.
    
    Tool Execution Flow:
    1. LLM determines which tool(s) to use
    2. ToolExecutor.execute_tool_call() routes to appropriate method
    3. Tool accesses data (PostgreSQL/Qdrant/InfluxDB)
    4. Results formatted as JSON for LLM
    5. LLM generates response using tool results
    
    Example:
        executor = ToolExecutor(
            postgres_pool=postgres_pool,
            vector_memory=vector_memory,
            influxdb_client=influxdb_client
        )
        
        result = await executor.execute_tool_call(
            tool_name="query_user_facts",
            tool_arguments={"user_id": "user123", "fact_type": "pet"}
        )
    """
    
    def __init__(
        self,
        postgres_pool=None,  # asyncpg connection pool
        vector_memory=None,  # VectorMemorySystem instance
        influxdb_client=None,  # InfluxDB client instance
        character_name: Optional[str] = None
    ):
        """
        Initialize the ToolExecutor.
        
        Args:
            postgres_pool: asyncpg connection pool for PostgreSQL queries
            vector_memory: VectorMemorySystem instance for Qdrant queries
            influxdb_client: InfluxDB client for metrics queries
            character_name: Current character name (for logging)
        """
        self.postgres_pool = postgres_pool
        self.vector_memory = vector_memory
        self.influxdb_client = influxdb_client
        self.character_name = character_name or "unknown"
        
        logger.info(
            "ToolExecutor initialized for character: %s | "
            "PostgreSQL: %s | Qdrant: %s | InfluxDB: %s",
            self.character_name,
            "connected" if postgres_pool else "not connected",
            "connected" if vector_memory else "not connected",
            "connected" if influxdb_client else "not connected"
        )
    
    async def execute_tool_call(
        self,
        tool_name: str,
        tool_arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool call and return results.
        
        Routes to the appropriate tool execution method based on tool_name.
        Handles errors and formats results for LLM consumption.
        
        Args:
            tool_name: Name of the tool to execute
            tool_arguments: Dictionary of tool arguments
        
        Returns:
            Dict with tool results:
                {
                    "success": bool,
                    "tool_name": str,
                    "data": Any,  # Tool-specific results
                    "error": Optional[str],
                    "execution_time_ms": float
                }
        """
        start_time = datetime.now()
        
        try:
            logger.info(
                "Executing tool: %s | Character: %s | Arguments: %s",
                tool_name,
                self.character_name,
                json.dumps(tool_arguments)
            )
            
            # Route to appropriate tool method
            if tool_name == "query_user_facts":
                data = await self._query_user_facts(**tool_arguments)
            elif tool_name == "recall_conversation_context":
                data = await self._recall_conversation_context(**tool_arguments)
            elif tool_name == "query_character_backstory":
                data = await self._query_character_backstory(**tool_arguments)
            elif tool_name == "summarize_user_relationship":
                data = await self._summarize_user_relationship(**tool_arguments)
            elif tool_name == "query_temporal_trends":
                data = await self._query_temporal_trends(**tool_arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(
                "Tool execution successful: %s | Time: %.2fms | Results: %d items",
                tool_name,
                execution_time,
                len(data) if isinstance(data, list) else 1
            )
            
            return {
                "success": True,
                "tool_name": tool_name,
                "data": data,
                "error": None,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            logger.error(
                "Tool execution failed: %s | Error: %s | Time: %.2fms",
                tool_name,
                error_msg,
                execution_time,
                exc_info=True
            )
            
            return {
                "success": False,
                "tool_name": tool_name,
                "data": None,
                "error": error_msg,
                "execution_time_ms": execution_time
            }
    
    async def _query_user_facts(
        self,
        user_id: str,
        fact_type: str = "all",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Tool 1: Query PostgreSQL for user facts and preferences.
        
        Queries the user_fact_relationships and fact_entities tables to retrieve
        structured information about a user (pets, hobbies, family, preferences, etc.).
        
        Args:
            user_id: User's unique identifier
            fact_type: Type of facts to query (pet|hobby|family|preference|location|all)
            limit: Maximum number of facts to return
        
        Returns:
            List of user facts with structure:
                [
                    {
                        "entity_type": str,  # e.g., "pet", "hobby"
                        "entity_name": str,  # e.g., "Max the dog"
                        "relationship_type": str,  # e.g., "owns", "interested_in"
                        "confidence": float,  # 0.0 to 1.0
                        "mentioned_by_character": str,  # Character who extracted fact
                        "created_at": str,  # ISO timestamp
                        "category": Optional[str]  # Entity category
                    },
                    ...
                ]
        """
        if not self.postgres_pool:
            raise RuntimeError("PostgreSQL connection pool not available")
        
        # Build query based on fact_type filter
        if fact_type == "all":
            type_filter = "AND fe.entity_type != '_processing_marker'"  # Exclude enrichment markers
        else:
            type_filter = f"AND fe.entity_type = '{fact_type}'"
        
        query = f"""
            SELECT 
                ufr.relationship_type,
                fe.entity_type,
                fe.entity_name,
                fe.category,
                ufr.confidence,
                ufr.mentioned_by_character,
                ufr.created_at
            FROM user_fact_relationships ufr
            JOIN fact_entities fe ON ufr.entity_id = fe.id
            WHERE ufr.user_id = $1
                {type_filter}
                AND ufr.relationship_type NOT LIKE '_enrichment%'  -- Exclude enrichment markers
            ORDER BY ufr.created_at DESC
            LIMIT $2
        """
        
        async with self.postgres_pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit)
        
        # Format results
        facts = [
            {
                "relationship_type": row["relationship_type"],
                "entity_type": row["entity_type"],
                "entity_name": row["entity_name"],
                "category": row["category"],
                "confidence": float(row["confidence"]) if row["confidence"] else 1.0,
                "mentioned_by_character": row["mentioned_by_character"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
            for row in rows
        ]
        
        logger.debug(
            "query_user_facts | User: %s | Type: %s | Found: %d facts",
            user_id,
            fact_type,
            len(facts)
        )
        
        return facts
    
    async def _recall_conversation_context(
        self,
        user_id: str,
        query: str,
        time_window: str = "all",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Tool 2: Query Qdrant for relevant conversation history using semantic search.
        
        Uses existing VectorMemorySystem infrastructure to retrieve contextually
        relevant past messages with emotion analysis and timestamps.
        
        Args:
            user_id: User's unique identifier
            query: Semantic search query
            time_window: Time window filter (24h|7d|30d|all)
            limit: Maximum number of memories to return
        
        Returns:
            List of conversation memories with structure:
                [
                    {
                        "user_message": str,
                        "bot_response": str,
                        "timestamp": str,  # ISO timestamp
                        "emotion": str,  # Primary emotion
                        "emotion_confidence": float,
                        "relevance_score": float  # Semantic similarity score
                    },
                    ...
                ]
        """
        if not self.vector_memory:
            raise RuntimeError("Vector memory system not available")
        
        # Calculate time filter if needed
        time_filter = None
        if time_window != "all":
            window_hours = {
                "24h": 24,
                "7d": 24 * 7,
                "30d": 24 * 30
            }
            hours = window_hours.get(time_window, 24 * 365)  # Default to 1 year
            time_filter = datetime.now() - timedelta(hours=hours)
        
        # Use existing VectorMemorySystem.retrieve_relevant_memories()
        memories = await self.vector_memory.retrieve_relevant_memories(
            user_id=user_id,
            query=query,
            limit=limit,
            time_filter=time_filter
        )
        
        # Format results for LLM consumption
        formatted_memories = [
            {
                "user_message": mem.get("user_message", ""),
                "bot_response": mem.get("bot_response", ""),
                "timestamp": mem.get("timestamp", ""),
                "emotion": mem.get("emotion", ""),
                "emotion_confidence": mem.get("emotion_confidence", 0.0),
                "relevance_score": mem.get("score", 0.0)
            }
            for mem in memories
        ]
        
        logger.debug(
            "recall_conversation_context | User: %s | Query: '%s' | "
            "Window: %s | Found: %d memories",
            user_id,
            query[:50],
            time_window,
            len(formatted_memories)
        )
        
        return formatted_memories
    
    async def _query_character_backstory(
        self,
        character_name: str,
        query: str,
        source: str = "both"
    ) -> Dict[str, Any]:
        """
        Tool 3: Query PostgreSQL CDL database for character backstory and personality.
        
        Queries character_* tables (background, identity_details, interests, etc.)
        for designer-defined facts and bot self-reflections.
        
        Args:
            character_name: Character's name (e.g., 'elena', 'marcus')
            query: What to query about the character
            source: Data source (cdl_database|self_memory|both)
        
        Returns:
            Dict with character information:
                {
                    "character_name": str,
                    "query": str,
                    "background": Dict[str, Any],  # From character_background
                    "identity": Dict[str, Any],  # From character_identity_details
                    "interests": List[str],  # From character_interests
                    "source": str  # Which source(s) were queried
                }
        """
        if not self.postgres_pool:
            raise RuntimeError("PostgreSQL connection pool not available")
        
        # TODO: Implement CDL database queries
        # This will query character_background, character_identity_details,
        # character_interests, and other character_* tables based on the query
        
        # For now, return placeholder
        logger.warning(
            "query_character_backstory NOT FULLY IMPLEMENTED | "
            "Character: %s | Query: '%s' | Source: %s",
            character_name,
            query[:50],
            source
        )
        
        return {
            "character_name": character_name,
            "query": query,
            "background": {},
            "identity": {},
            "interests": [],
            "source": source,
            "note": "Full implementation pending - requires CDL table schema analysis"
        }
    
    async def _summarize_user_relationship(
        self,
        user_id: str,
        include_facts: bool = True,
        include_conversations: bool = True,
        time_window: str = "all"
    ) -> Dict[str, Any]:
        """
        Tool 4: Generate comprehensive user relationship summary (multi-source aggregation).
        
        Aggregates user facts from PostgreSQL and conversation history from Qdrant
        to create a holistic relationship summary.
        
        Args:
            user_id: User's unique identifier
            include_facts: Include user facts from PostgreSQL
            include_conversations: Include conversation history from Qdrant
            time_window: Time window for conversations (24h|7d|30d|all)
        
        Returns:
            Dict with relationship summary:
                {
                    "user_id": str,
                    "facts": List[Dict],  # User facts if include_facts=True
                    "conversation_summary": Dict,  # Conversation stats if include_conversations=True
                    "relationship_duration": str,  # How long character has known user
                    "total_interactions": int,
                    "most_discussed_topics": List[str]
                }
        """
        summary = {
            "user_id": user_id,
            "facts": [],
            "conversation_summary": {},
            "relationship_duration": None,
            "total_interactions": 0,
            "most_discussed_topics": []
        }
        
        # Get user facts if requested
        if include_facts and self.postgres_pool:
            summary["facts"] = await self._query_user_facts(
                user_id=user_id,
                fact_type="all",
                limit=20  # More facts for comprehensive summary
            )
        
        # Get conversation summary if requested
        if include_conversations and self.vector_memory:
            # Use semantic search to find representative conversations
            memories = await self._recall_conversation_context(
                user_id=user_id,
                query="general conversation",  # Broad query for summary
                time_window=time_window,
                limit=10  # Sample of recent conversations
            )
            
            if memories:
                summary["conversation_summary"] = {
                    "recent_conversations": len(memories),
                    "time_window": time_window,
                    "sample_interactions": memories[:3]  # First 3 for context
                }
                summary["total_interactions"] = len(memories)
        
        logger.debug(
            "summarize_user_relationship | User: %s | Facts: %d | "
            "Conversations: %d | Window: %s",
            user_id,
            len(summary["facts"]),
            summary["total_interactions"],
            time_window
        )
        
        return summary
    
    async def _query_temporal_trends(
        self,
        user_id: str,
        metric: str = "all",
        time_window: str = "7d"
    ) -> Dict[str, Any]:
        """
        Tool 5: Query InfluxDB for conversation quality metrics over time.
        
        Retrieves temporal trend data for engagement scores, satisfaction scores,
        coherence scores, and other conversation quality metrics.
        
        Args:
            user_id: User's unique identifier
            metric: Metric to query (engagement_score|satisfaction_score|coherence_score|all)
            time_window: Time window for trends (24h|7d|30d)
        
        Returns:
            Dict with temporal trend data:
                {
                    "user_id": str,
                    "metric": str,
                    "time_window": str,
                    "data_points": List[Dict],  # Time series data
                    "summary": Dict  # Aggregate statistics
                }
        """
        if not self.influxdb_client:
            logger.warning(
                "query_temporal_trends | InfluxDB not available | "
                "User: %s | Metric: %s",
                user_id,
                metric
            )
            return {
                "user_id": user_id,
                "metric": metric,
                "time_window": time_window,
                "data_points": [],
                "summary": {},
                "note": "InfluxDB client not available"
            }
        
        # TODO: Implement InfluxDB queries
        # This will query conversation_quality measurement for metrics over time
        
        logger.warning(
            "query_temporal_trends NOT FULLY IMPLEMENTED | "
            "User: %s | Metric: %s | Window: %s",
            user_id,
            metric,
            time_window
        )
        
        return {
            "user_id": user_id,
            "metric": metric,
            "time_window": time_window,
            "data_points": [],
            "summary": {},
            "note": "Full implementation pending - requires InfluxDB schema analysis"
        }
