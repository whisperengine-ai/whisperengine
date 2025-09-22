"""
Intelligent Memory Manager for LLM-Driven Memory Curation

Coordinates LLM tool calling to analyze conversations and proactively manage 
vector memory with semantic understanding and intelligent optimization.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class IntelligentMemoryManager:
    """AI-driven memory management using LLM tool calling for vector store optimization"""
    
    def __init__(self, vector_memory_store, llm_client, vector_tool_manager):
        self.vector_store = vector_memory_store
        self.llm_client = llm_client
        self.tool_manager = vector_tool_manager
        self.analysis_history: List[Dict[str, Any]] = []
        
        # Configuration for memory analysis
        self.analysis_temperature = 0.1  # Low temperature for consistent analysis
        self.max_memory_actions_per_analysis = 5
        self.min_confidence_for_action = 0.6
    
    async def analyze_conversation_for_memory_actions(
        self, 
        user_message: str, 
        bot_response: str, 
        user_id: str,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze conversation and determine intelligent memory actions using LLM tool calling
        
        Returns:
            List of executed memory actions with results
        """
        analysis_start = datetime.now()
        
        try:
            # Create comprehensive memory management prompt
            system_prompt = self._create_memory_analysis_system_prompt()
            conversation_prompt = self._create_conversation_analysis_prompt(
                user_message, bot_response, conversation_context or {}
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": conversation_prompt}
            ]
            
            # Call LLM with memory management tools
            logger.debug("Requesting LLM analysis for memory actions")
            response = await self.llm_client.generate_chat_completion_with_tools(
                messages=messages,
                tools=self.tool_manager.get_tools(),
                tool_choice="auto",  # Let LLM decide when to use tools
                temperature=self.analysis_temperature,
                max_tokens=2000  # Enough for analysis and tool calls
            )
            
            # Execute any tool calls made by the LLM
            executed_actions = []
            if self._has_tool_calls(response):
                tool_calls = self._extract_tool_calls(response)
                
                for tool_call in tool_calls[:self.max_memory_actions_per_analysis]:
                    action_result = await self._execute_memory_tool_call(
                        tool_call, user_id
                    )
                    executed_actions.append(action_result)
            
            # Log analysis for debugging and improvement
            analysis_record = {
                "timestamp": analysis_start.isoformat(),
                "user_id": user_id,
                "user_message": user_message[:200],  # Truncate for logging
                "bot_response": bot_response[:200],
                "actions_taken": len(executed_actions),
                "llm_response": self._extract_llm_reasoning(response),
                "success": all(action.get("result", {}).get("success", False) for action in executed_actions)
            }
            self.analysis_history.append(analysis_record)
            
            if executed_actions:
                logger.info("Executed %d memory actions for user %s", len(executed_actions), user_id)
            
            return executed_actions
            
        except Exception as e:
            logger.error("Failed to analyze conversation for memory actions: %s", str(e))
            return []
    
    def _create_memory_analysis_system_prompt(self) -> str:
        """Create the system prompt for memory analysis"""
        return """You are an intelligent memory curator for an AI companion named WhisperEngine. 

Your role is to analyze conversations and determine what memory management actions should be taken to maintain an optimal, relevant, and accurate memory system.

MEMORY MANAGEMENT PRINCIPLES:
1. Store important new information that will help future conversations
2. Update or correct existing memories when users provide clarifications
3. Organize related memories to improve retrieval and understanding
4. Archive outdated or irrelevant information to keep memory focused
5. Enhance frequently accessed memories for better retrieval

WHEN TO TAKE ACTION:
- User shares new personal information (name, preferences, relationships, goals)
- User corrects or clarifies something previously discussed
- User expresses strong preferences or opinions
- User mentions important events, experiences, or future plans
- User provides updates on ongoing situations
- Information contradicts or supersedes existing memories

WHEN NOT TO TAKE ACTION:
- Casual conversation without new information
- Temporary emotional states (unless significant)
- Generic questions or small talk
- Information that's too specific or unlikely to be relevant later

TOOL USAGE GUIDELINES:
- Use store_semantic_memory for new important information
- Use update_memory_context for corrections or clarifications
- Use organize_related_memories when multiple related topics are discussed
- Use enhance_memory_retrieval for frequently referenced topics
- Use archive_outdated_memories cautiously and only when clearly outdated

Always provide clear reasoning for each action in the function arguments."""

    def _create_conversation_analysis_prompt(
        self, 
        user_message: str, 
        bot_response: str, 
        context: Dict[str, Any]
    ) -> str:
        """Create the conversation analysis prompt"""
        context_str = json.dumps(context, indent=2) if context else "No additional context"
        
        return f"""Analyze this conversation exchange for memory management opportunities:

USER MESSAGE: {user_message}

BOT RESPONSE: {bot_response}

CONVERSATION CONTEXT: {context_str}

ANALYSIS REQUIRED:
1. Identify any new important information that should be stored
2. Detect corrections or clarifications that need memory updates
3. Recognize opportunities to organize or enhance existing memories
4. Determine if any information might be outdated or contradictory

For each memory action you decide to take, use the appropriate tool with clear reasoning. Focus on information that will improve future conversation quality and relevance.

If no significant memory actions are needed, simply respond with your analysis without using any tools."""

    def _has_tool_calls(self, llm_response: Dict[str, Any]) -> bool:
        """Check if LLM response contains tool calls"""
        choices = llm_response.get("choices", [])
        if not choices:
            return False
        
        message = choices[0].get("message", {})
        return "tool_calls" in message and message["tool_calls"]

    def _extract_tool_calls(self, llm_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response"""
        choices = llm_response.get("choices", [])
        if not choices:
            return []
        
        message = choices[0].get("message", {})
        return message.get("tool_calls", [])

    def _extract_llm_reasoning(self, llm_response: Dict[str, Any]) -> str:
        """Extract LLM's reasoning from response"""
        choices = llm_response.get("choices", [])
        if not choices:
            return "No response content"
        
        message = choices[0].get("message", {})
        content = message.get("content", "")
        
        # If there are tool calls, the content might be empty or contain reasoning
        if not content and "tool_calls" in message:
            tool_calls = message["tool_calls"]
            reasoning_parts = []
            for call in tool_calls:
                function = call.get("function", {})
                name = function.get("name", "unknown")
                reasoning_parts.append(f"Called {name}")
            content = "; ".join(reasoning_parts)
        
        return content or "No reasoning provided"

    async def _execute_memory_tool_call(
        self, 
        tool_call: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """Execute a single memory tool call"""
        function_data = tool_call.get("function", {})
        function_name = function_data.get("name", "")
        
        try:
            # Parse function arguments
            arguments_str = function_data.get("arguments", "{}")
            parameters = json.loads(arguments_str)
            
            # Execute the tool
            result = await self.tool_manager.execute_tool(
                function_name, 
                parameters, 
                user_id
            )
            
            logger.debug("Executed tool %s with result: %s", function_name, result.get("success", False))
            
            return {
                "tool_call_id": tool_call.get("id", ""),
                "function": function_name,
                "parameters": parameters,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse tool call arguments: %s", str(e))
            return {
                "tool_call_id": tool_call.get("id", ""),
                "function": function_name,
                "error": f"Invalid arguments: {str(e)}",
                "result": {"success": False, "error": "Invalid JSON arguments"}
            }
        except Exception as e:
            logger.error("Failed to execute tool call %s: %s", function_name, str(e))
            return {
                "tool_call_id": tool_call.get("id", ""),
                "function": function_name,
                "error": str(e),
                "result": {"success": False, "error": str(e)}
            }

    async def analyze_and_optimize_user_memories(
        self, 
        user_id: str, 
        optimization_scope: str = "recent"
    ) -> Dict[str, Any]:
        """
        Proactively analyze and optimize a user's memory organization
        
        Args:
            user_id: User to optimize memories for
            optimization_scope: "recent", "all", or specific timeframe
            
        Returns:
            Summary of optimization actions taken
        """
        try:
            # Get user's recent memory patterns for analysis
            recent_memories = await self._get_user_memory_sample(user_id, optimization_scope)
            search_patterns = await self._analyze_search_patterns(user_id)
            
            # Create optimization analysis prompt
            optimization_prompt = self._create_optimization_prompt(
                recent_memories, search_patterns, optimization_scope
            )
            
            messages = [
                {"role": "system", "content": self._create_optimization_system_prompt()},
                {"role": "user", "content": optimization_prompt}
            ]
            
            # Get LLM analysis with optimization tools
            response = await self.llm_client.generate_chat_completion_with_tools(
                messages=messages,
                tools=self.tool_manager.get_tools(),
                tool_choice="auto",
                temperature=0.1,  # Very consistent for optimization
                max_tokens=3000
            )
            
            # Execute optimization actions
            optimization_actions = []
            if self._has_tool_calls(response):
                tool_calls = self._extract_tool_calls(response)
                
                for tool_call in tool_calls[:10]:  # Limit optimization actions
                    action_result = await self._execute_memory_tool_call(tool_call, user_id)
                    optimization_actions.append(action_result)
            
            logger.info("Completed memory optimization for user %s with %d actions", 
                       user_id, len(optimization_actions))
            
            return {
                "success": True,
                "user_id": user_id,
                "scope": optimization_scope,
                "actions_taken": len(optimization_actions),
                "optimization_results": optimization_actions,
                "llm_analysis": self._extract_llm_reasoning(response),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to optimize user memories: %s", str(e))
            return {
                "success": False,
                "user_id": user_id,
                "error": str(e)
            }

    def _create_optimization_system_prompt(self) -> str:
        """System prompt for memory optimization"""
        return """You are a memory optimization specialist for WhisperEngine AI companion.

Your task is to analyze a user's memory patterns and proactively improve memory organization for better conversation quality.

OPTIMIZATION OBJECTIVES:
1. Identify and link related memories that should be cross-referenced
2. Find duplicate or redundant information that can be consolidated
3. Detect outdated information that should be archived
4. Enhance frequently accessed memories for better retrieval
5. Create useful summaries of complex topics with many memories

OPTIMIZATION STRATEGIES:
- organize_related_memories: Group thematically related memories
- archive_outdated_memories: Remove irrelevant or superseded information
- enhance_memory_retrieval: Boost important or frequently accessed memories
- create_memory_summary: Summarize complex topics with many related memories
- update_memory_context: Consolidate similar or overlapping information

Be conservative with archival - only archive clearly outdated information.
Focus on improvements that will enhance conversation relevance and continuity."""

    def _create_optimization_prompt(
        self, 
        memories: List[Dict[str, Any]], 
        search_patterns: Dict[str, Any], 
        scope: str
    ) -> str:
        """Create optimization analysis prompt"""
        memory_summary = self._format_memories_for_analysis(memories)
        
        return f"""Analyze this user's memory patterns for optimization opportunities:

MEMORY SCOPE: {scope}
TOTAL MEMORIES ANALYZED: {len(memories)}

RECENT SEARCH PATTERNS:
{json.dumps(search_patterns, indent=2)}

MEMORY SAMPLE (most recent/relevant):
{memory_summary}

OPTIMIZATION ANALYSIS NEEDED:
1. Identify clusters of related memories that should be linked
2. Find potential duplicates or redundant information
3. Detect memories that might be outdated or superseded
4. Recognize frequently referenced topics that need enhancement
5. Suggest memory summaries for complex topics

Use the available tools to implement specific optimizations. Focus on changes that will improve conversation quality and memory retrieval effectiveness."""

    async def _get_user_memory_sample(
        self, 
        user_id: str, 
        scope: str = "recent"
    ) -> List[Dict[str, Any]]:
        """Get a sample of user memories for analysis"""
        try:
            # This is a simplified implementation - a real system would have more sophisticated sampling
            sample_size = 50 if scope == "recent" else 100
            
            # Get recent memories using a broad search
            memories = await self.vector_store.search_memories(
                query="",  # Empty query to get general recent memories
                user_id=user_id,
                top_k=sample_size
            )
            
            return memories
        except Exception as e:
            logger.error("Failed to get user memory sample: %s", str(e))
            return []

    async def _analyze_search_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's search patterns for optimization insights"""
        # This would integrate with search analytics if available
        # For now, return basic structure
        return {
            "frequent_topics": ["work", "family", "preferences"],
            "search_frequency": "daily",
            "common_queries": ["work project", "family plans", "favorite foods"]
        }

    def _format_memories_for_analysis(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories for LLM analysis"""
        if not memories:
            return "No memories found"
        
        formatted = []
        for i, memory in enumerate(memories[:20]):  # Limit to prevent prompt overflow
            content = memory.get("content", "")[:200]  # Truncate long content
            memory_type = memory.get("metadata", {}).get("memory_type", "unknown")
            timestamp = memory.get("metadata", {}).get("created_at", "")
            
            formatted.append(f"{i+1}. [{memory_type}] {content} (Created: {timestamp[:10]})")
        
        return "\n".join(formatted)

    def get_analysis_history(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get history of memory analyses"""
        analyses = self.analysis_history
        
        if user_id:
            analyses = [analysis for analysis in analyses if analysis.get("user_id") == user_id]
        
        return sorted(analyses, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_memory_management_stats(self) -> Dict[str, Any]:
        """Get statistics about memory management activities"""
        total_analyses = len(self.analysis_history)
        successful_analyses = sum(1 for a in self.analysis_history if a.get("success", False))
        total_actions = sum(a.get("actions_taken", 0) for a in self.analysis_history)
        
        return {
            "total_analyses": total_analyses,
            "successful_analyses": successful_analyses,
            "success_rate": successful_analyses / max(total_analyses, 1),
            "total_memory_actions": total_actions,
            "average_actions_per_analysis": total_actions / max(total_analyses, 1),
            "last_analysis": self.analysis_history[-1]["timestamp"] if self.analysis_history else None
        }