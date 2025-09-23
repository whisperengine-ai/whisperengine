"""
LLM Tool Integration Manager for Phase 2

Integrates Character Evolution and Emotional Intelligence tools with LLM calling system.
Provides unified interface for all Phase 2 LLM tooling capabilities.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LLMToolResult:
    """Result from LLM tool execution"""
    tool_name: str
    success: bool
    result: Dict[str, Any]
    execution_time: float
    user_id: str
    timestamp: datetime
    error: Optional[str] = None


class LLMToolIntegrationManager:
    """Unified manager for all LLM tool calling capabilities"""
    
    def __init__(self, vector_memory_tool_manager, intelligent_memory_manager, 
                 character_evolution_tool_manager, emotional_intelligence_tool_manager,
                 llm_client):
        self.vector_memory_tools = vector_memory_tool_manager
        self.intelligent_memory_tools = intelligent_memory_manager
        self.character_evolution_tools = character_evolution_tool_manager
        self.emotional_intelligence_tools = emotional_intelligence_tool_manager
        self.llm_client = llm_client
        
        # Combine all tools
        self.all_tools = self._combine_all_tools()
        self.execution_history: List[LLMToolResult] = []
    
    def _combine_all_tools(self) -> List[Dict[str, Any]]:
        """Combine tools from all managers into unified list"""
        combined_tools = []
        
        # Add vector memory tools (Phase 1)
        if hasattr(self.vector_memory_tools, 'tools'):
            combined_tools.extend(self.vector_memory_tools.tools)
        
        # Add intelligent memory tools (Phase 1)
        if hasattr(self.intelligent_memory_tools, 'tools'):
            combined_tools.extend(self.intelligent_memory_tools.tools)
        
        # Add character evolution tools (Phase 2)
        if hasattr(self.character_evolution_tools, 'tools'):
            combined_tools.extend(self.character_evolution_tools.tools)
        
        # Add emotional intelligence tools (Phase 2)
        if hasattr(self.emotional_intelligence_tools, 'tools'):
            combined_tools.extend(self.emotional_intelligence_tools.tools)
        
        logger.info("Combined %d tools from all managers", len(combined_tools))
        return combined_tools
    
    async def execute_llm_with_tools(self, user_message: str, user_id: str, 
                                   character_context: str = "", 
                                   emotional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute LLM with full tool calling capabilities"""
        start_time = datetime.now()
        
        try:
            # Build comprehensive context for LLM
            system_prompt = self._build_system_prompt(character_context, emotional_context)
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Call LLM with all available tools
            response = await self.llm_client.generate_with_tools(
                messages=messages,
                tools=self.all_tools,
                max_tool_iterations=5,  # Allow multiple tool calls
                user_id=user_id
            )
            
            # Process any tool calls made by LLM
            tool_results = []
            if response.get("tool_calls"):
                tool_results = await self._process_tool_calls(
                    response["tool_calls"], user_id
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "llm_response": response.get("content", ""),
                "tool_calls_made": len(response.get("tool_calls", [])),
                "tool_results": tool_results,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error("Failed to execute LLM with tools: %s", e)
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_system_prompt(self, character_context: str = "", 
                           emotional_context: Dict[str, Any] = None) -> str:
        """Build comprehensive system prompt for LLM tool calling"""
        
        base_prompt = """You are an advanced AI companion with sophisticated emotional intelligence and character adaptation capabilities.

You have access to powerful tools for:

1. MEMORY MANAGEMENT:
   - Store and retrieve conversation memories
   - Search for relevant past interactions
   - Optimize memory for better recall
   - Manage conversation context intelligently

2. CHARACTER EVOLUTION:
   - Adapt personality traits based on user interactions
   - Update character backstory through shared experiences
   - Modify communication style to match user preferences
   - Calibrate emotional expression for optimal connection
   - Develop meaningful relationships over time

3. EMOTIONAL INTELLIGENCE:
   - Detect emotional crisis situations requiring support
   - Calibrate empathetic responses to user's emotional state
   - Provide proactive emotional support when needed
   - Analyze emotional patterns for better understanding
   - Implement crisis intervention when necessary

TOOL USAGE GUIDELINES:
- Use tools proactively to enhance conversation quality
- Prioritize emotional intelligence tools when detecting distress
- Adapt your character based on user feedback and interaction patterns
- Store important moments and insights for future reference
- Be thoughtful about when and how to offer support

IMPORTANT: Always prioritize user emotional wellbeing and safety."""

        if character_context:
            base_prompt += f"\n\nCHARACTER CONTEXT:\n{character_context}"
        
        if emotional_context:
            base_prompt += f"\n\nEMOTIONAL CONTEXT:\n"
            for key, value in emotional_context.items():
                base_prompt += f"- {key}: {value}\n"
        
        return base_prompt
    
    async def _process_tool_calls(self, tool_calls: List[Dict[str, Any]], 
                                user_id: str) -> List[Dict[str, Any]]:
        """Process tool calls made by LLM"""
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.get("function", {}).get("name")
            parameters = tool_call.get("function", {}).get("arguments", {})
            
            start_time = datetime.now()
            
            try:
                # Route to appropriate tool manager
                result = await self._route_tool_call(function_name, parameters, user_id)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                tool_result = LLMToolResult(
                    tool_name=function_name,
                    success=result.get("success", False),
                    result=result,
                    execution_time=execution_time,
                    user_id=user_id,
                    timestamp=datetime.now()
                )
                
                self.execution_history.append(tool_result)
                results.append(result)
                
            except Exception as e:
                logger.error("Error processing tool call %s: %s", function_name, e)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                error_result = LLMToolResult(
                    tool_name=function_name,
                    success=False,
                    result={"success": False, "error": str(e)},
                    execution_time=execution_time,
                    user_id=user_id,
                    timestamp=datetime.now(),
                    error=str(e)
                )
                
                self.execution_history.append(error_result)
                results.append({"success": False, "error": str(e)})
        
        return results
    
    async def _route_tool_call(self, function_name: str, parameters: Dict[str, Any], 
                             user_id: str) -> Dict[str, Any]:
        """Route tool call to appropriate manager"""
        
        # Vector Memory Tools (Phase 1)
        vector_memory_tools = [
            "store_conversation_memory", "retrieve_relevant_memories", 
            "search_memories_with_context", "get_conversation_summary",
            "manage_memory_capacity", "optimize_memory_storage"
        ]
        
        # Intelligent Memory Tools (Phase 1)
        intelligent_memory_tools = [
            "analyze_conversation_patterns", "detect_context_switches",
            "generate_memory_insights", "optimize_memory_recall"
        ]
        
        # Character Evolution Tools (Phase 2)
        character_evolution_tools = [
            "adapt_personality_trait", "update_character_backstory",
            "modify_communication_style", "calibrate_emotional_expression",
            "create_character_relationship"
        ]
        
        # Emotional Intelligence Tools (Phase 2)
        emotional_intelligence_tools = [
            "detect_emotional_crisis", "calibrate_empathy_response",
            "provide_proactive_support", "analyze_emotional_patterns",
            "emotional_crisis_intervention"
        ]
        
        # Route to appropriate manager
        if function_name in vector_memory_tools:
            return await self.vector_memory_tools.execute_tool(
                function_name, parameters, user_id
            )
        elif function_name in intelligent_memory_tools:
            return await self.intelligent_memory_tools.execute_tool(
                function_name, parameters, user_id
            )
        elif function_name in character_evolution_tools:
            return await self.character_evolution_tools.execute_tool(
                function_name, parameters, user_id
            )
        elif function_name in emotional_intelligence_tools:
            return await self.emotional_intelligence_tools.execute_tool(
                function_name, parameters, user_id
            )
        else:
            logger.warning("Unknown tool function: %s", function_name)
            return {"success": False, "error": f"Unknown tool: {function_name}"}
    
    async def get_tool_analytics(self, user_id: str = None) -> Dict[str, Any]:
        """Get analytics on tool usage and effectiveness"""
        history = self.execution_history
        if user_id:
            history = [r for r in history if r.user_id == user_id]
        
        if not history:
            return {"message": "No tool execution history available"}
        
        # Calculate analytics
        total_executions = len(history)
        successful_executions = len([r for r in history if r.success])
        success_rate = successful_executions / total_executions if total_executions > 0 else 0
        
        # Tool usage breakdown
        tool_usage = {}
        for result in history:
            tool_usage[result.tool_name] = tool_usage.get(result.tool_name, 0) + 1
        
        # Average execution times
        avg_execution_time = sum(r.execution_time for r in history) / len(history)
        
        # Recent activity (last 24 hours)
        recent_cutoff = datetime.now().timestamp() - (24 * 60 * 60)
        recent_activity = [
            r for r in history 
            if r.timestamp.timestamp() > recent_cutoff
        ]
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": success_rate,
            "tool_usage_breakdown": tool_usage,
            "average_execution_time": avg_execution_time,
            "recent_activity_24h": len(recent_activity),
            "most_used_tool": max(tool_usage.items(), key=lambda x: x[1])[0] if tool_usage else None
        }
    
    def get_available_tools_summary(self) -> Dict[str, Any]:
        """Get summary of all available tools"""
        tool_categories = {
            "Memory Management": [
                "store_conversation_memory", "retrieve_relevant_memories",
                "search_memories_with_context", "get_conversation_summary",
                "manage_memory_capacity", "optimize_memory_storage"
            ],
            "Intelligent Analysis": [
                "analyze_conversation_patterns", "detect_context_switches",
                "generate_memory_insights", "optimize_memory_recall"
            ],
            "Character Evolution": [
                "adapt_personality_trait", "update_character_backstory",
                "modify_communication_style", "calibrate_emotional_expression",
                "create_character_relationship"
            ],
            "Emotional Intelligence": [
                "detect_emotional_crisis", "calibrate_empathy_response",
                "provide_proactive_support", "analyze_emotional_patterns",
                "emotional_crisis_intervention"
            ]
        }
        
        return {
            "total_tools_available": len(self.all_tools),
            "tool_categories": tool_categories,
            "phase_1_complete": True,  # Memory and Intelligence tools
            "phase_2_complete": True,  # Character Evolution and Emotional Intelligence
            "integration_status": "fully_operational"
        }