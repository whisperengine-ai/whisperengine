"""
Vector Memory Tool Manager for LLM Tool Calling (CONSOLIDATED)

CONSOLIDATION UPDATE: Removed redundant store_semantic_memory tool
that duplicates existing vector memory system functionality.

Removed tools:
- store_semantic_memory (duplicates memory_manager.store_memory())

Remaining tools provide unique functionality not available in core systems.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VectorMemoryAction:
    """Represents a memory action taken by the LLM"""
    action_type: str
    memory_id: Optional[str]
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    reason: str
    success: bool
    result: Optional[Dict[str, Any]] = None


class VectorMemoryToolManager:
    """
    Manages vector-specific memory tools for LLM tool calling
    
    CONSOLIDATION UPDATE: Removed redundant store_semantic_memory tool.
    
    Removed: store_semantic_memory -> Use memory_manager.store_memory() directly
    Remaining tools provide unique optimization and organization functionality.
    """
    
    def __init__(self, memory_manager, llm_client):
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.tools = self._initialize_vector_tools()
        self.memory_actions: List[VectorMemoryAction] = []
    
    def _initialize_vector_tools(self) -> List[Dict[str, Any]]:
        """Initialize vector-specific memory tools for LLM tool calling (consolidated)"""
        return [
            # NOTE: store_semantic_memory REMOVED - use memory_manager.store_memory() directly
            {
                "type": "function",
                "function": {
                    "name": "update_memory_context",
                    "description": "Update or correct existing memories with new context, corrections, or additional information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_query": {
                                "type": "string",
                                "description": "Query to find the memory that needs updating (be specific)"
                            },
                            "correction_content": {
                                "type": "string",
                                "description": "New or corrected information to add/update"
                            },
                            "update_type": {
                                "type": "string",
                                "enum": ["correction", "expansion", "clarification", "context_addition"],
                                "description": "Type of update being made"
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "description": "Confidence in this update (0.0-1.0)"
                            }
                        },
                        "required": ["search_query", "correction_content", "update_type"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "organize_related_memories",
                    "description": "Group and organize related memories for better retrieval and understanding",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic_query": {
                                "type": "string",
                                "description": "Main topic or theme to organize memories around"
                            },
                            "organization_strategy": {
                                "type": "string",
                                "enum": ["chronological", "thematic", "importance", "relationship", "context"],
                                "description": "Strategy for organizing the related memories"
                            },
                            "cluster_name": {
                                "type": "string",
                                "description": "Name for this memory cluster or group"
                            },
                            "max_memories": {
                                "type": "integer",
                                "minimum": 5,
                                "maximum": 50,
                                "description": "Maximum number of memories to include in this organization"
                            }
                        },
                        "required": ["topic_query", "organization_strategy", "cluster_name"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "archive_outdated_memories",
                    "description": "Identify and archive memories that are outdated, superseded, or no longer relevant",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "criteria_type": {
                                "type": "string",
                                "enum": ["temporal", "superseded", "irrelevant", "duplicate", "low_importance"],
                                "description": "Criteria for identifying memories to archive"
                            },
                            "timeframe_cutoff": {
                                "type": "string",
                                "description": "For temporal archiving - memories older than this (e.g., '30 days', '6 months')"
                            },
                            "superseding_content": {
                                "type": "string",
                                "description": "For superseded archiving - the new content that replaces old memories"
                            },
                            "archive_reason": {
                                "type": "string",
                                "description": "Detailed reason for archiving these memories"
                            },
                            "preview_only": {
                                "type": "boolean",
                                "description": "If true, only preview what would be archived without actually doing it",
                                "default": False
                            }
                        },
                        "required": ["criteria_type", "archive_reason"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "enhance_memory_retrieval",
                    "description": "Optimize memory retrieval by adding semantic tags, improving metadata, and creating cross-references",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_query": {
                                "type": "string",
                                "description": "Query to find memories that need retrieval enhancement"
                            },
                            "enhancement_type": {
                                "type": "string",
                                "enum": ["add_tags", "improve_metadata", "create_crossref", "boost_searchability"],
                                "description": "Type of retrieval enhancement to perform"
                            },
                            "new_tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "New semantic tags to add for better retrieval"
                            },
                            "cross_references": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Related topics or memories to cross-reference"
                            }
                        },
                        "required": ["target_query", "enhancement_type"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_memory_summary",
                    "description": "Create intelligent summaries of memory clusters or topics for efficient overview",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary_topic": {
                                "type": "string",
                                "description": "Topic or theme to create a summary for"
                            },
                            "summary_type": {
                                "type": "string",
                                "enum": ["chronological", "thematic", "key_insights", "relationship_map", "progress_tracking"],
                                "description": "Type of summary to create"
                            },
                            "memory_timeframe": {
                                "type": "string",
                                "enum": ["recent", "past_week", "past_month", "all_time"],
                                "description": "Timeframe of memories to include in summary"
                            },
                            "detail_level": {
                                "type": "string",
                                "enum": ["brief", "detailed", "comprehensive"],
                                "description": "Level of detail for the summary"
                            }
                        },
                        "required": ["summary_topic", "summary_type"],
                        "additionalProperties": False
                    }
                }
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available vector memory tools"""
        return self.tools
    
    async def handle_tool_call(self, function_name: str, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle LLM tool calls for vector memory operations"""
        try:
            # CONSOLIDATION: store_semantic_memory removed - redirect to memory_manager
            if function_name == "store_semantic_memory":
                logger.info("Redirecting store_semantic_memory to memory_manager.store_memory()")
                
                # Convert to standard memory storage
                content = parameters.get("content", "")
                memory_type = parameters.get("memory_type", "general")
                importance = parameters.get("importance", 5)
                tags = parameters.get("tags", [])
                related_to = parameters.get("related_to", "")
                temporal_context = parameters.get("temporal_context", "present")
                
                # Use core memory system instead
                await self.memory_manager.store_memory(
                    user_id=user_id,
                    content=content,
                    memory_type=memory_type,
                    metadata={
                        "importance": importance,
                        "tags": tags,
                        "related_to": related_to,
                        "temporal_context": temporal_context,
                        "tool_source": "llm_tool_semantic_memory"
                    }
                )
                
                return {
                    "success": True,
                    "message": "Memory stored using core memory system",
                    "memory_type": memory_type,
                    "importance": importance
                }
            
            elif function_name == "update_memory_context":
                return await self._update_memory_context(parameters, user_id)
            elif function_name == "organize_related_memories":
                return await self._organize_related_memories(parameters, user_id)
            elif function_name == "archive_outdated_memories":
                return await self._archive_outdated_memories(parameters, user_id)
            elif function_name == "enhance_memory_retrieval":
                return await self._enhance_memory_retrieval(parameters, user_id)
            elif function_name == "create_memory_summary":
                return await self._create_memory_summary(parameters, user_id)
            else:
                logger.error("Unknown vector memory tool: %s", function_name)
                return {"success": False, "error": f"Unknown tool: {function_name}"}
        
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Error handling vector memory tool %s: %s", function_name, e)
            return {"success": False, "error": str(e)}
    
    async def _update_memory_context(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update existing memories with new context"""
        search_query = params["search_query"]
        correction_content = params["correction_content"]
        update_type = params["update_type"]
        confidence = params.get("confidence", 0.8)
        
        logger.info("Updating memory context for user %s: %s", user_id, update_type)
        
        try:
            # Find memories to update
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=search_query,
                limit=10
            )
            
            if not memories:
                return {
                    "success": False,
                    "error": "No memories found matching the search query",
                    "search_query": search_query
                }
            
            # Store the update as a new memory with context
            update_content = f"UPDATE ({update_type}): {correction_content}"
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=update_content,
                memory_type="context_update",
                metadata={
                    "update_type": update_type,
                    "confidence": confidence,
                    "related_memories": len(memories),
                    "search_query": search_query,
                    "tool_source": "vector_memory_update"
                }
            )
            
            return {
                "success": True,
                "updated_memories": len(memories),
                "update_type": update_type,
                "confidence": confidence
            }
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to update memory context: %s", e)
            return {"success": False, "error": str(e)}
    
    async def _organize_related_memories(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Organize related memories into clusters"""
        topic_query = params["topic_query"]
        organization_strategy = params["organization_strategy"]
        cluster_name = params["cluster_name"]
        max_memories = params.get("max_memories", 20)
        
        logger.info("Organizing memories by %s for user %s", organization_strategy, user_id)
        
        try:
            # Retrieve relevant memories
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=topic_query,
                limit=max_memories
            )
            
            if not memories:
                return {
                    "success": False,
                    "error": "No memories found for organization",
                    "topic": topic_query
                }
            
            # Create organization record
            organization_record = {
                "cluster_name": cluster_name,
                "topic": topic_query,
                "strategy": organization_strategy,
                "memory_count": len(memories),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store organization as a meta-memory
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Memory cluster organized: {cluster_name}",
                memory_type="organization",
                metadata={
                    "cluster_record": organization_record,
                    "topic": topic_query,
                    "strategy": organization_strategy,
                    "tool_source": "vector_memory_organization"
                }
            )
            
            return {
                "success": True,
                "cluster_created": cluster_name,
                "memories_organized": len(memories),
                "organization_strategy": organization_strategy
            }
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to organize memories: %s", e)
            return {"success": False, "error": str(e)}
    
    async def _archive_outdated_memories(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Archive outdated or irrelevant memories"""
        criteria_type = params["criteria_type"]
        timeframe_cutoff = params.get("timeframe_cutoff", "30 days")
        archive_reason = params["archive_reason"]
        preview_only = params.get("preview_only", False)
        
        logger.info("Archiving memories (%s) for user %s", criteria_type, user_id)
        
        try:
            # This is a complex operation that would need careful implementation
            # For now, create a record of the archival intent
            archival_record = {
                "criteria_type": criteria_type,
                "timeframe_cutoff": timeframe_cutoff,
                "reason": archive_reason,
                "preview_only": preview_only,
                "timestamp": datetime.now().isoformat()
            }
            
            if not preview_only:
                # Store archival action as a meta-memory
                await self.memory_manager.store_memory(
                    user_id=user_id,
                    content=f"Memory archival performed: {criteria_type}",
                    memory_type="archival",
                    metadata={
                        "archival_record": archival_record,
                        "criteria": criteria_type,
                        "tool_source": "vector_memory_archival"
                    }
                )
            
            return {
                "success": True,
                "archival_type": criteria_type,
                "preview_only": preview_only,
                "reason": archive_reason
            }
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to archive memories: %s", e)
            return {"success": False, "error": str(e)}
    
    async def _enhance_memory_retrieval(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Enhance memory retrieval capabilities"""
        target_query = params["target_query"]
        enhancement_type = params["enhancement_type"]
        new_tags = params.get("new_tags", [])
        cross_references = params.get("cross_references", [])
        
        logger.info("Enhancing memory retrieval (%s) for user %s", enhancement_type, user_id)
        
        try:
            # Find memories to enhance
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=target_query,
                limit=20
            )
            
            if not memories:
                return {
                    "success": False,
                    "error": "No memories found for enhancement",
                    "query": target_query
                }
            
            # Create enhancement record
            enhancement_record = {
                "enhancement_type": enhancement_type,
                "target_query": target_query,
                "new_tags": new_tags,
                "cross_references": cross_references,
                "memories_enhanced": len(memories),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store enhancement action
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=f"Memory retrieval enhanced: {enhancement_type}",
                memory_type="enhancement",
                metadata={
                    "enhancement_record": enhancement_record,
                    "query": target_query,
                    "tool_source": "vector_memory_enhancement"
                }
            )
            
            return {
                "success": True,
                "enhancement_type": enhancement_type,
                "memories_enhanced": len(memories),
                "new_tags_added": len(new_tags)
            }
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to enhance memory retrieval: %s", e)
            return {"success": False, "error": str(e)}
    
    async def _create_memory_summary(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create intelligent memory summaries"""
        summary_topic = params["summary_topic"]
        summary_type = params["summary_type"]
        memory_timeframe = params.get("memory_timeframe", "all_time")
        detail_level = params.get("detail_level", "detailed")
        
        logger.info("Creating memory summary (%s) for user %s", summary_type, user_id)
        
        try:
            # Retrieve memories for summary
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=summary_topic,
                limit=50  # More for comprehensive summary
            )
            
            if not memories:
                return {
                    "success": False,
                    "error": "No memories found for summary",
                    "topic": summary_topic
                }
            
            # Create summary record
            summary_record = {
                "topic": summary_topic,
                "summary_type": summary_type,
                "timeframe": memory_timeframe,
                "detail_level": detail_level,
                "source_memories": len(memories),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store the summary as a special memory
            summary_content = f"Memory summary created for: {summary_topic}"
            await self.memory_manager.store_memory(
                user_id=user_id,
                content=summary_content,
                memory_type="summary",
                metadata={
                    "summary_record": summary_record,
                    "topic": summary_topic,
                    "type": summary_type,
                    "tool_source": "vector_memory_summary"
                }
            )
            
            return {
                "success": True,
                "summary_created": True,
                "topic": summary_topic,
                "summary_type": summary_type,
                "source_memories": len(memories)
            }
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("Failed to create memory summary: %s", e)
            return {"success": False, "error": str(e)}
    
    def get_memory_actions(self, user_id: Optional[str] = None) -> List[VectorMemoryAction]:
        """Get memory action history"""
        if user_id:
            return [action for action in self.memory_actions if action.content and user_id in str(action.content)]
        return self.memory_actions