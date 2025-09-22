"""
Vector Memory Tool Manager for LLM Tool Calling

Provides intelligent vector memory management tools that enable LLMs to 
proactively store, organize, and optimize memory based on conversation context.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from .vector_memory_system import MemoryType

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
    """Advanced LLM tools for intelligent vector store management"""
    
    def __init__(self, vector_memory_store, llm_client=None):
        self.vector_store = vector_memory_store
        self.llm_client = llm_client
        self.tools = self._initialize_vector_tools()
        self.action_history: List[VectorMemoryAction] = []
    
    def _initialize_vector_tools(self) -> List[Dict[str, Any]]:
        """Initialize vector-specific memory tools for LLM tool calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "store_semantic_memory",
                    "description": "Store important information with semantic understanding and proper categorization for better retrieval",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The important information to remember (will be semantically optimized)"
                            },
                            "memory_type": {
                                "type": "string",
                                "enum": ["personal_fact", "preference", "relationship", "experience", "learning", "goal", "context"],
                                "description": "Type of memory for optimal storage and retrieval strategy"
                            },
                            "importance": {
                                "type": "number",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Importance level (1-10) for retention priority and retrieval ranking"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Semantic tags for enhanced retrieval (e.g., ['work', 'project', 'deadline', 'urgent'])"
                            },
                            "related_to": {
                                "type": "string",
                                "description": "What this memory relates to or expands upon (for cross-referencing)"
                            },
                            "temporal_context": {
                                "type": "string",
                                "enum": ["past", "present", "future", "ongoing", "completed"],
                                "description": "Temporal nature of the information for better organization"
                            }
                        },
                        "required": ["content", "memory_type"],
                        "additionalProperties": False
                    }
                }
            },
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
                                "description": "The correct or updated information to store"
                            },
                            "update_reason": {
                                "type": "string",
                                "description": "Why this update is being made (correction, clarification, additional context)"
                            },
                            "merge_strategy": {
                                "type": "string",
                                "enum": ["replace", "append", "merge_semantic", "create_new"],
                                "description": "How to handle the update - replace completely, add to existing, or merge intelligently"
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0.1,
                                "maximum": 1.0,
                                "description": "Confidence in this update (higher values will override lower confidence memories)"
                            }
                        },
                        "required": ["search_query", "correction_content", "update_reason"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "organize_related_memories",
                    "description": "Group and cross-reference related memories to improve retrieval and create knowledge clusters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "The topic, theme, or subject to organize memories around"
                            },
                            "relationship_type": {
                                "type": "string",
                                "enum": ["sequential", "causal", "thematic", "temporal", "contradictory", "supporting", "related"],
                                "description": "How the memories relate to each other for optimal organization"
                            },
                            "consolidation_strategy": {
                                "type": "string",
                                "enum": ["link_only", "create_summary", "merge_similar", "create_hierarchy"],
                                "description": "How to organize the related memories for better retrieval"
                            },
                            "scope": {
                                "type": "string",
                                "enum": ["recent", "all_time", "specific_period"],
                                "description": "Time scope for memory organization (recent = last 30 days)"
                            }
                        },
                        "required": ["topic"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "archive_outdated_memories",
                    "description": "Identify and archive memories that are no longer relevant, accurate, or useful",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "criteria": {
                                "type": "string", 
                                "enum": ["temporal", "superseded", "contradicted", "irrelevant", "low_importance"],
                                "description": "Criteria for identifying memories to archive"
                            },
                            "topic_filter": {
                                "type": "string",
                                "description": "Focus archival on specific topic or subject (optional)"
                            },
                            "archive_reason": {
                                "type": "string",
                                "description": "Clear explanation for why these memories should be archived"
                            },
                            "retention_period": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 365,
                                "description": "Days to keep in archive before permanent deletion (0 = permanent archive)"
                            },
                            "confidence_threshold": {
                                "type": "number",
                                "minimum": 0.1,
                                "maximum": 1.0,
                                "description": "Only archive memories below this confidence level"
                            }
                        },
                        "required": ["criteria", "archive_reason"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "enhance_memory_retrieval",
                    "description": "Add semantic enhancements and cross-references to improve future memory retrieval",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_query": {
                                "type": "string",
                                "description": "Query to find memories that need enhancement"
                            },
                            "enhancement_type": {
                                "type": "string",
                                "enum": ["add_synonyms", "extract_entities", "add_context", "create_summary", "boost_relevance"],
                                "description": "Type of enhancement to apply for better retrieval"
                            },
                            "enhancement_data": {
                                "type": "object",
                                "description": "Enhancement-specific data (synonyms list, entities, context, etc.)"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Why this enhancement is needed (e.g., 'frequently searched', 'important context')"
                            }
                        },
                        "required": ["search_query", "enhancement_type", "reason"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_memory_summary",
                    "description": "Create semantic summaries of related memories for efficient retrieval and understanding",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Topic or theme to summarize memories about"
                            },
                            "summary_type": {
                                "type": "string",
                                "enum": ["chronological", "thematic", "relationship_based", "preference_summary"],
                                "description": "Type of summary to create based on memory organization"
                            },
                            "include_timeline": {
                                "type": "boolean",
                                "description": "Whether to include temporal progression in the summary"
                            },
                            "max_memories": {
                                "type": "integer",
                                "minimum": 5,
                                "maximum": 50,
                                "description": "Maximum number of memories to include in summary"
                            }
                        },
                        "required": ["topic", "summary_type"],
                        "additionalProperties": False
                    }
                }
            }
        ]
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of available tools for LLM tool calling"""
        return self.tools
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Execute a vector memory tool based on LLM tool call"""
        action_start = datetime.now()
        
        try:
            if tool_name == "store_semantic_memory":
                result = await self._store_semantic_memory(parameters, user_id)
            elif tool_name == "update_memory_context":
                result = await self._update_memory_context(parameters, user_id)
            elif tool_name == "organize_related_memories":
                result = await self._organize_related_memories(parameters, user_id)
            elif tool_name == "archive_outdated_memories":
                result = await self._archive_outdated_memories(parameters, user_id)
            elif tool_name == "enhance_memory_retrieval":
                result = await self._enhance_memory_retrieval(parameters, user_id)
            elif tool_name == "create_memory_summary":
                result = await self._create_memory_summary(parameters, user_id)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            # Log the action
            action = VectorMemoryAction(
                action_type=tool_name,
                memory_id=result.get("memory_id"),
                content=str(parameters),
                metadata={"parameters": parameters, "user_id": user_id},
                timestamp=action_start,
                reason=parameters.get("reason", parameters.get("update_reason", parameters.get("archive_reason", "LLM-driven action"))),
                success=result.get("success", False),
                result=result
            )
            self.action_history.append(action)
            
            return result
                
        except Exception as e:
            logger.error(f"Error executing vector memory tool {tool_name}: {e}")
            error_result = {"error": f"Tool execution failed: {str(e)}", "success": False}
            
            # Log failed action
            action = VectorMemoryAction(
                action_type=tool_name,
                memory_id=None,
                content=str(parameters),
                metadata={"parameters": parameters, "user_id": user_id, "error": str(e)},
                timestamp=action_start,
                reason="Tool execution failed",
                success=False,
                result=error_result
            )
            self.action_history.append(action)
            
            return error_result
    
    async def _store_semantic_memory(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Store memory with semantic optimization and enhanced metadata"""
        content = params["content"]
        memory_type = params["memory_type"]
        importance = params.get("importance", 5)
        tags = params.get("tags", [])
        related_to = params.get("related_to")
        temporal_context = params.get("temporal_context", "present")
        
        # Create enhanced metadata for vector storage
        enhanced_metadata = {
            "memory_type": memory_type,
            "importance": importance,
            "tags": tags,
            "temporal_context": temporal_context,
            "llm_managed": True,
            "created_by": "vector_tool_manager",
            "creation_timestamp": datetime.now().isoformat(),
        }
        
        if related_to:
            enhanced_metadata["related_to"] = related_to
        
        # Convert memory_type to MemoryType enum
        memory_type_mapping = {
            "personal_fact": MemoryType.FACT,
            "preference": MemoryType.PREFERENCE,
            "relationship": MemoryType.RELATIONSHIP,
            "experience": MemoryType.CONTEXT,  # Map experience to context
            "learning": MemoryType.CONTEXT,    # Map learning to context
            "goal": MemoryType.CONTEXT,        # Map goal to context
            "context": MemoryType.CONTEXT
        }
        
        vector_memory_type = memory_type_mapping.get(memory_type, MemoryType.CONTEXT)
        
        try:
            # Store the memory with enhanced metadata
            memory_id = await self.vector_store.store_memory(
                user_id=user_id,
                content=content,
                memory_type=vector_memory_type,
                metadata=enhanced_metadata
            )
            
            logger.info(f"Stored semantic memory for user {user_id}: {memory_type} - {content[:100]}...")
            
            return {
                "success": True,
                "memory_id": memory_id,
                "message": f"Stored {memory_type} memory with importance {importance}",
                "content_preview": content[:100] + ("..." if len(content) > 100 else ""),
                "metadata": enhanced_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to store semantic memory: {e}")
            return {
                "success": False,
                "error": f"Failed to store memory: {str(e)}"
            }
    
    async def _update_memory_context(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update existing memories with new context or corrections"""
        search_query = params["search_query"]
        correction_content = params["correction_content"]
        update_reason = params["update_reason"]
        merge_strategy = params.get("merge_strategy", "merge_semantic")
        confidence = params.get("confidence", 0.8)
        
        try:
            # Search for existing memories to update
            existing_memories = await self.vector_store.search_memories(
                query=search_query,
                user_id=user_id,
                top_k=5
            )
            
            if not existing_memories:
                # No existing memory found, create new one
                memory_id = await self.vector_store.store_memory(
                    user_id=user_id,
                    content=correction_content,
                    memory_type=MemoryType.CONTEXT,
                    metadata={
                        "update_reason": update_reason,
                        "confidence": confidence,
                        "llm_managed": True,
                        "original_search": search_query
                    }
                )
                
                return {
                    "success": True,
                    "memory_id": memory_id,
                    "message": f"Created new memory (no existing found): {correction_content[:100]}...",
                    "action_taken": "create_new"
                }
            
            # Update the most relevant memory
            target_memory = existing_memories[0]
            updated_content = correction_content
            
            if merge_strategy == "append":
                updated_content = f"{target_memory.get('content', '')} {correction_content}"
            elif merge_strategy == "merge_semantic":
                # For now, replace - future could use LLM to merge semantically
                updated_content = correction_content
            # else: replace (default)
            
            # Update the memory
            await self.vector_store.update_memory(
                memory_id=target_memory.get("memory_id", target_memory.get("id")),
                content=updated_content,
                metadata={
                    **target_memory.get("metadata", {}),
                    "last_updated": datetime.now().isoformat(),
                    "update_reason": update_reason,
                    "confidence": confidence,
                    "merge_strategy": merge_strategy
                }
            )
            
            logger.info(f"Updated memory for user {user_id}: {update_reason}")
            
            return {
                "success": True,
                "memory_id": target_memory.get("memory_id", target_memory.get("id")),
                "message": f"Updated memory using {merge_strategy} strategy",
                "action_taken": merge_strategy,
                "updated_content": updated_content[:100] + ("..." if len(updated_content) > 100 else "")
            }
            
        except Exception as e:
            logger.error(f"Failed to update memory context: {e}")
            return {
                "success": False,
                "error": f"Failed to update memory: {str(e)}"
            }
    
    async def _organize_related_memories(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Organize and cross-reference related memories"""
        topic = params["topic"]
        relationship_type = params.get("relationship_type", "related")
        consolidation_strategy = params.get("consolidation_strategy", "link_only")
        scope = params.get("scope", "recent")
        
        try:
            # Determine search timeframe based on scope
            search_limit = 20 if scope == "recent" else 50
            
            # Find related memories
            related_memories = await self.vector_store.search_memories(
                query=topic,
                user_id=user_id,
                top_k=search_limit
            )
            
            if len(related_memories) < 2:
                return {
                    "success": False,
                    "message": f"Not enough related memories found for topic '{topic}' to organize",
                    "found_count": len(related_memories)
                }
            
            organized_count = 0
            
            if consolidation_strategy == "create_summary":
                # Create a summary memory of related memories
                summary_content = f"Summary of {topic}: "
                memory_contents = [mem.get("content", "") for mem in related_memories[:10]]
                summary_content += " | ".join(memory_contents[:5])  # Simplified summary
                
                summary_id = await self.vector_store.store_memory(
                    user_id=user_id,
                    content=summary_content,
                    memory_type=MemoryType.CONTEXT,
                    metadata={
                        "is_summary": True,
                        "topic": topic,
                        "relationship_type": relationship_type,
                        "source_memories": [mem.get("memory_id", mem.get("id")) for mem in related_memories[:10]],
                        "llm_managed": True
                    }
                )
                organized_count += 1
            
            elif consolidation_strategy == "link_only":
                # Add cross-reference metadata to related memories
                memory_ids = [mem.get("memory_id", mem.get("id")) for mem in related_memories]
                
                for memory in related_memories[:10]:  # Limit to top 10 to avoid overwhelming
                    memory_id = memory.get("memory_id", memory.get("id"))
                    related_ids = [mid for mid in memory_ids if mid != memory_id]
                    
                    await self.vector_store.update_memory(
                        memory_id=memory_id,
                        metadata={
                            **memory.get("metadata", {}),
                            "related_memories": related_ids[:5],  # Limit related links
                            "organization_topic": topic,
                            "relationship_type": relationship_type,
                            "organized_at": datetime.now().isoformat()
                        }
                    )
                    organized_count += 1
            
            logger.info(f"Organized {organized_count} memories for topic '{topic}' using {consolidation_strategy}")
            
            return {
                "success": True,
                "message": f"Organized {organized_count} memories about '{topic}' using {consolidation_strategy}",
                "topic": topic,
                "strategy": consolidation_strategy,
                "organized_count": organized_count,
                "total_found": len(related_memories)
            }
            
        except Exception as e:
            logger.error(f"Failed to organize related memories: {e}")
            return {
                "success": False,
                "error": f"Failed to organize memories: {str(e)}"
            }
    
    async def _archive_outdated_memories(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Archive memories that are no longer relevant"""
        criteria = params["criteria"]
        archive_reason = params["archive_reason"]
        topic_filter = params.get("topic_filter")
        retention_period = params.get("retention_period", 90)
        confidence_threshold = params.get("confidence_threshold", 0.3)
        
        try:
            # Find candidate memories for archival based on criteria
            if topic_filter:
                candidate_memories = await self.vector_store.search_memories(
                    query=topic_filter,
                    user_id=user_id,
                    top_k=50
                )
            else:
                # Get recent memories for analysis - this would need a method to get all user memories
                # For now, use a broad search
                candidate_memories = await self.vector_store.search_memories(
                    query="",  # Empty query to get general memories
                    user_id=user_id,
                    top_k=100
                )
            
            archived_count = 0
            archive_cutoff = datetime.now() - timedelta(days=30)  # 30 days ago
            
            for memory in candidate_memories:
                should_archive = False
                
                if criteria == "temporal":
                    # Archive old memories
                    memory_date = memory.get("metadata", {}).get("created_at")
                    if memory_date:
                        mem_datetime = datetime.fromisoformat(memory_date.replace('Z', '+00:00'))
                        if mem_datetime < archive_cutoff:
                            should_archive = True
                
                elif criteria == "low_importance":
                    # Archive low importance memories
                    importance = memory.get("metadata", {}).get("importance", 5)
                    if importance < 3:
                        should_archive = True
                
                elif criteria == "irrelevant":
                    # Archive memories with low confidence
                    confidence = memory.get("metadata", {}).get("confidence", 0.5)
                    if confidence < confidence_threshold:
                        should_archive = True
                
                if should_archive:
                    memory_id = memory.get("memory_id", memory.get("id"))
                    
                    # Archive by updating metadata (actual archival system would be more sophisticated)
                    await self.vector_store.update_memory(
                        memory_id=memory_id,
                        metadata={
                            **memory.get("metadata", {}),
                            "archived": True,
                            "archive_reason": archive_reason,
                            "archive_date": datetime.now().isoformat(),
                            "retention_period_days": retention_period,
                            "archived_by": "llm_tool_manager"
                        }
                    )
                    archived_count += 1
            
            logger.info(f"Archived {archived_count} memories for user {user_id} using criteria '{criteria}'")
            
            return {
                "success": True,
                "message": f"Archived {archived_count} memories based on {criteria} criteria",
                "criteria": criteria,
                "archived_count": archived_count,
                "retention_period": retention_period,
                "reason": archive_reason
            }
            
        except Exception as e:
            logger.error(f"Failed to archive outdated memories: {e}")
            return {
                "success": False,
                "error": f"Failed to archive memories: {str(e)}"
            }
    
    async def _enhance_memory_retrieval(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Enhance memories for better retrieval"""
        search_query = params["search_query"]
        enhancement_type = params["enhancement_type"]
        enhancement_data = params.get("enhancement_data", {})
        reason = params["reason"]
        
        try:
            # Find memories to enhance
            memories_to_enhance = await self.vector_store.search_memories(
                query=search_query,
                user_id=user_id,
                top_k=10
            )
            
            if not memories_to_enhance:
                return {
                    "success": False,
                    "message": f"No memories found to enhance for query: {search_query}"
                }
            
            enhanced_count = 0
            
            for memory in memories_to_enhance[:5]:  # Limit to top 5
                memory_id = memory.get("memory_id", memory.get("id"))
                current_metadata = memory.get("metadata", {})
                
                if enhancement_type == "boost_relevance":
                    # Increase importance/relevance
                    current_importance = current_metadata.get("importance", 5)
                    new_importance = min(10, current_importance + 2)
                    
                    await self.vector_store.update_memory(
                        memory_id=memory_id,
                        metadata={
                            **current_metadata,
                            "importance": new_importance,
                            "relevance_boosted": True,
                            "boost_reason": reason,
                            "boosted_at": datetime.now().isoformat()
                        }
                    )
                    enhanced_count += 1
                
                elif enhancement_type == "add_synonyms":
                    # Add synonym metadata for better matching
                    synonyms = enhancement_data.get("synonyms", [])
                    await self.vector_store.update_memory(
                        memory_id=memory_id,
                        metadata={
                            **current_metadata,
                            "synonyms": synonyms,
                            "enhanced_for_retrieval": True,
                            "enhancement_reason": reason
                        }
                    )
                    enhanced_count += 1
                
                elif enhancement_type == "add_context":
                    # Add contextual information
                    context = enhancement_data.get("context", "")
                    await self.vector_store.update_memory(
                        memory_id=memory_id,
                        metadata={
                            **current_metadata,
                            "additional_context": context,
                            "context_enhanced": True,
                            "enhancement_reason": reason
                        }
                    )
                    enhanced_count += 1
            
            logger.info(f"Enhanced {enhanced_count} memories for better retrieval")
            
            return {
                "success": True,
                "message": f"Enhanced {enhanced_count} memories using {enhancement_type}",
                "enhancement_type": enhancement_type,
                "enhanced_count": enhanced_count,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Failed to enhance memory retrieval: {e}")
            return {
                "success": False,
                "error": f"Failed to enhance memories: {str(e)}"
            }
    
    async def _create_memory_summary(self, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create semantic summaries of related memories"""
        topic = params["topic"]
        summary_type = params["summary_type"]
        include_timeline = params.get("include_timeline", False)
        max_memories = params.get("max_memories", 20)
        
        try:
            # Find memories about the topic
            topic_memories = await self.vector_store.search_memories(
                query=topic,
                user_id=user_id,
                top_k=max_memories
            )
            
            if not topic_memories:
                return {
                    "success": False,
                    "message": f"No memories found to summarize for topic: {topic}"
                }
            
            # Create summary based on type
            if summary_type == "chronological" and include_timeline:
                # Sort by timestamp and create chronological summary
                sorted_memories = sorted(
                    topic_memories,
                    key=lambda x: x.get("metadata", {}).get("created_at", ""),
                    reverse=False
                )
                summary_content = f"Chronological summary of {topic}: "
                for i, memory in enumerate(sorted_memories[:10]):
                    timestamp = memory.get("metadata", {}).get("created_at", "")
                    content = memory.get("content", "")[:100]
                    summary_content += f"[{timestamp[:10]}] {content}. "
            
            elif summary_type == "thematic":
                # Group by themes and create thematic summary
                summary_content = f"Thematic summary of {topic}: "
                content_snippets = [mem.get("content", "")[:100] for mem in topic_memories[:10]]
                summary_content += " | ".join(content_snippets)
            
            elif summary_type == "preference_summary":
                # Focus on preferences and opinions
                summary_content = f"Preferences and opinions about {topic}: "
                preference_memories = [
                    mem for mem in topic_memories 
                    if mem.get("metadata", {}).get("memory_type") == "preference"
                ]
                if preference_memories:
                    pref_content = [mem.get("content", "")[:100] for mem in preference_memories[:5]]
                    summary_content += " | ".join(pref_content)
                else:
                    summary_content += "No specific preferences recorded."
            
            else:
                # Default summary
                summary_content = f"Summary of {topic}: "
                content_snippets = [mem.get("content", "")[:100] for mem in topic_memories[:10]]
                summary_content += " ".join(content_snippets)
            
            # Store the summary as a new memory
            summary_id = await self.vector_store.store_memory(
                user_id=user_id,
                content=summary_content,
                memory_type=MemoryType.CONTEXT,
                metadata={
                    "is_summary": True,
                    "summary_type": summary_type,
                    "topic": topic,
                    "source_count": len(topic_memories),
                    "include_timeline": include_timeline,
                    "llm_managed": True,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Created {summary_type} summary for topic '{topic}' with {len(topic_memories)} source memories")
            
            return {
                "success": True,
                "summary_id": summary_id,
                "message": f"Created {summary_type} summary of {topic} from {len(topic_memories)} memories",
                "summary_preview": summary_content[:200] + ("..." if len(summary_content) > 200 else ""),
                "source_count": len(topic_memories),
                "summary_type": summary_type
            }
            
        except Exception as e:
            logger.error(f"Failed to create memory summary: {e}")
            return {
                "success": False,
                "error": f"Failed to create summary: {str(e)}"
            }
    
    def get_action_history(self, user_id: Optional[str] = None, limit: int = 50) -> List[VectorMemoryAction]:
        """Get history of memory actions taken by the LLM"""
        actions = self.action_history
        
        if user_id:
            actions = [action for action in actions if action.metadata.get("user_id") == user_id]
        
        return sorted(actions, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_tools_for_model(self) -> str:
        """Get tools formatted for model context (for debugging/logging)"""
        return json.dumps(self.tools, indent=2)