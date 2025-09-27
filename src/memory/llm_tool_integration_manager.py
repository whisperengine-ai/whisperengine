"""
LLM Tool Integration Manager for Phase 2

Integrates Character Evolution and Emotional Intelligence tools with LLM calling system.
Provides unified interface for all Phase 2 LLM tooling capabilities.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

# Import taxonomy for consistent emotion handling
try:
    from src.intelligence.emotion_taxonomy import standardize_emotion
except ImportError:
    def standardize_emotion(emotion):
        return emotion.lower() if emotion else "neutral"
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
                 phase3_memory_tool_manager, phase4_orchestration_manager, llm_client,
                 web_search_tool_manager=None):
        self.vector_memory_tools = vector_memory_tool_manager
        self.intelligent_memory_tools = intelligent_memory_manager
        self.character_evolution_tools = character_evolution_tool_manager
        self.emotional_intelligence_tools = emotional_intelligence_tool_manager
        self.phase3_memory_tools = phase3_memory_tool_manager  # Phase 3: Multi-Dimensional Memory Networks
        self.phase4_orchestration_tools = phase4_orchestration_manager  # Phase 4: Proactive Intelligence & Tool Orchestration
        self.web_search_tools = web_search_tool_manager  # Web Search: Current Events & Information
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
        
        # Add Phase 3 memory network tools (Phase 3)
        if hasattr(self.phase3_memory_tools, 'tools'):
            combined_tools.extend(self.phase3_memory_tools.tools)
        
        # Add Phase 4 orchestration tools (Phase 4)
        if hasattr(self.phase4_orchestration_tools, 'tools'):
            combined_tools.extend(self.phase4_orchestration_tools.tools)
        
        # Add web search tools (Current Events & Information)
        if self.web_search_tools and hasattr(self.web_search_tools, 'tools'):
            combined_tools.extend(self.web_search_tools.tools)
        
        logger.info("Combined %d tools from all managers", len(combined_tools))
        return combined_tools
    
    def _filter_relevant_tools(self, user_message: str, emotional_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Intelligently filter tools based on conversation context to reduce token usage"""
        
        # Always include core memory tools (Phase 1) - these are lightweight and frequently useful
        core_tools = []
        for tool in self.all_tools:
            tool_name = tool.get("function", {}).get("name", "")
            if tool_name in ["store_semantic_memory", "update_memory_context", "enhance_memory_retrieval", "create_memory_summary"]:
                core_tools.append(tool)
        
        # Check for emotional crisis indicators
        emotional_crisis_detected = self._detect_emotional_crisis(user_message, emotional_context)
        
        # Check for character evolution requests  
        character_adaptation_needed = self._detect_character_adaptation_request(user_message)
        
        # Check for complex analysis requests
        complex_analysis_needed = self._detect_complex_analysis_request(user_message)
        
        # Check for workflow/planning requests
        workflow_planning_needed = self._detect_workflow_planning_request(user_message)
        
        # Check for current events/web search requests
        web_search_needed = self._detect_web_search_request(user_message)
        
        # Log web search detection for monitoring
        if web_search_needed:
            logger.info("🔍 Web search needed detected for message: '%s'", user_message[:100] + "..." if len(user_message) > 100 else user_message)
        else:
            logger.debug("🔍 No web search needed for message: '%s'", user_message[:50] + "..." if len(user_message) > 50 else user_message)
        
        additional_tools = []
        
        # Add emotional intelligence tools if crisis detected
        if emotional_crisis_detected:
            for tool in self.all_tools:
                tool_name = tool.get("function", {}).get("name", "")
                if any(keyword in tool_name for keyword in ["emotional", "crisis", "empathy", "detect_emotional", "analyze_emotional", "calibrate_emotional"]):
                    additional_tools.append(tool)
        
        # Add character evolution tools if adaptation requested
        if character_adaptation_needed:
            for tool in self.all_tools:
                tool_name = tool.get("function", {}).get("name", "")
                if "character" in tool_name or "personality" in tool_name or "adapt" in tool_name:
                    additional_tools.append(tool)
        
        # Add Phase 3 tools for complex analysis
        if complex_analysis_needed:
            for tool in self.all_tools:
                tool_name = tool.get("function", {}).get("name", "")
                if "analyze" in tool_name or "pattern" in tool_name or "insight" in tool_name:
                    additional_tools.append(tool)
        
        # Add Phase 4 tools for workflow planning
        if workflow_planning_needed:
            for tool in self.all_tools:
                tool_name = tool.get("function", {}).get("name", "")
                if "orchestrate" in tool_name or "plan" in tool_name or "workflow" in tool_name:
                    additional_tools.append(tool)
        
        # Add web search tools for current events
        web_search_tools_added = 0
        if web_search_needed:
            for tool in self.all_tools:
                tool_name = tool.get("function", {}).get("name", "")
                if "search_current_events" in tool_name or "verify_current_information" in tool_name:
                    additional_tools.append(tool)
                    web_search_tools_added += 1
            
            if web_search_tools_added > 0:
                logger.info("🔍 Added %d web search tools to LLM context", web_search_tools_added)
            else:
                logger.warning("🔍 Web search needed but no web search tools available in system")
        
        # Combine and deduplicate
        relevant_tools = core_tools + additional_tools
        seen_names = set()
        filtered_tools = []
        for tool in relevant_tools:
            tool_name = tool.get("function", {}).get("name", "")
            if tool_name not in seen_names:
                filtered_tools.append(tool)
                seen_names.add(tool_name)
        
        logger.info("Filtered tools: %d/%d (saved %d tools from prompt)", 
                   len(filtered_tools), len(self.all_tools), len(self.all_tools) - len(filtered_tools))
        
        return filtered_tools
    
    def _detect_emotional_crisis(self, message: str, emotional_context: Optional[Dict[str, Any]] = None) -> bool:
        """Detect if message indicates emotional crisis requiring support tools"""
        crisis_keywords = [
            'depressed', 'hopeless', 'overwhelmed', 'anxious', 'panic', 'crisis',
            'can\'t cope', 'breaking down', 'falling apart', 'desperate', 'suicidal',
            'sad', 'feeling sad', 'upset', 'emotional support', 'distressed'
        ]
        message_lower = message.lower()
        
        # Check for crisis keywords
        keyword_crisis = any(keyword in message_lower for keyword in crisis_keywords)
        
        # Check emotional context if available
        context_crisis = False
        if emotional_context:
            # Check for explicit support needed flag
            if emotional_context.get('support_needed', False):
                context_crisis = True
            
            # Check for distressed mood using standardized emotions
            if emotional_context.get('mood'):
                standardized_mood = standardize_emotion(emotional_context.get('mood'))
                if standardized_mood in ['sadness', 'fear', 'anger']:  # 7-core taxonomy crisis emotions
                    context_crisis = True
            
            # Check for high intensity emotions - standardize before checking
            high_intensity_emotions = emotional_context.get('high_intensity_emotions', [])
            standardized_high_emotions = [standardize_emotion(emotion) for emotion in high_intensity_emotions]
            context_crisis = context_crisis or any(emotion in ['sadness', 'fear'] for emotion in standardized_high_emotions)
        
        return keyword_crisis or context_crisis
    
    def _detect_character_adaptation_request(self, message: str) -> bool:
        """Detect if user is requesting character adaptation"""
        adaptation_keywords = [
            'be more', 'be less', 'adapt', 'change your', 'adjust your',
            'personality', 'communication style', 'approach', 'manner',
            'tone', 'be different', 'act more', 'respond differently'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in adaptation_keywords)
    
    def _detect_complex_analysis_request(self, message: str) -> bool:
        """Detect if user is requesting complex memory analysis"""
        analysis_keywords = [
            'analyze', 'pattern', 'insight', 'understand', 'explain',
            'what do you notice', 'trends', 'connections', 'relationships',
            'history', 'development', 'evolution', 'changes over time'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in analysis_keywords)
    
    def _detect_workflow_planning_request(self, message: str) -> bool:
        """Detect if user is requesting workflow planning or complex tasks"""
        workflow_keywords = [
            'plan', 'help me', 'guide me', 'steps', 'process', 'workflow',
            'organize', 'strategy', 'approach', 'method', 'accomplish',
            'achieve', 'goal', 'project', 'task'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in workflow_keywords)
    
    def _detect_web_search_request(self, message: str) -> bool:
        """Detect if user is requesting current events or web search"""
        web_search_keywords = [
            'news', 'current', 'recent', 'latest', 'what\'s happening',
            'look up', 'search', 'find out', 'current events', 'today',
            'this week', 'this month', 'verify', 'fact check', 'check if',
            'is it true', 'what happened', 'recent developments',
            'current situation', 'up to date', 'recent information'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in web_search_keywords)
    
    async def execute_llm_with_tools(self, user_message: str, user_id: str, 
                                   character_context: str = "", 
                                   emotional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute LLM with intelligently filtered tool calling capabilities"""
        start_time = datetime.now()
        
        try:
            # Build comprehensive context for LLM
            system_prompt = self._build_system_prompt(character_context, emotional_context)
            
            # Intelligently filter tools based on conversation context
            relevant_tools = self._filter_relevant_tools(user_message, emotional_context)
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Call LLM with filtered tools to reduce token usage
            response = await self.llm_client.generate_with_tools(
                messages=messages,
                tools=relevant_tools,
                max_tool_iterations=5,  # Allow multiple tool calls
                user_id=user_id
            )
            
            # Process any tool calls made by LLM
            tool_results = []
            # Extract tool calls from proper API response structure
            tool_calls = []
            if response.get("choices") and len(response["choices"]) > 0:
                message = response["choices"][0].get("message", {})
                tool_calls = message.get("tool_calls", [])
            
            if tool_calls:
                tool_results = await self._process_tool_calls(
                    tool_calls, user_id
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Check if web search was used and add emoji prefix
            llm_response = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            web_search_used = any(
                result.get("tool_name") in ["search_current_events", "verify_current_information"]
                for result in tool_results
                if result.get("success", False)
            )
            
            # Add emoji prefix if web search was used
            if web_search_used and llm_response:
                llm_response = f"🌐 {llm_response}"
                logger.info("🌐 Added web search indicator to response (user will see network usage)")
            
            result = {
                "success": True,
                "llm_response": llm_response,
                "tool_calls_made": len(tool_calls),
                "tool_results": tool_results,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "web_search_used": web_search_used  # For debugging/logging
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

4. CURRENT EVENTS & WEB SEARCH:
   - Search for current events, news, and recent developments
   - Verify information against current sources
   - Access up-to-date information not in memory
   - Fact-check claims using web sources
   
4. MULTI-DIMENSIONAL MEMORY NETWORKS:
   - Analyze complex memory networks for deep insights
   - Detect recurring patterns and themes across memories
   - Evaluate memory importance for better prioritization
   - Discover semantic memory clusters for contextual understanding
   - Generate actionable insights from memory analysis
   - Map connections between related memories

5. PROACTIVE INTELLIGENCE & TOOL ORCHESTRATION:
   - Plan and execute complex multi-tool workflows
   - Generate proactive insights without explicit requests
   - Analyze tool effectiveness and optimize strategies
   - Create autonomous workflow plans for long-term goals
   - Orchestrate sophisticated task decomposition and execution

TOOL USAGE GUIDELINES:
- Use tools proactively to enhance conversation quality
- Prioritize emotional intelligence tools when detecting distress
- Adapt your character based on user feedback and interaction patterns
- Store important moments and insights for future reference
- Be thoughtful about when and how to offer support
- Leverage memory network analysis for deeper user understanding
- Use pattern detection to recognize recurring themes in conversations
- Apply memory insights to create more meaningful connections
- Orchestrate complex workflows for sophisticated user requests
- Generate proactive insights to enhance relationship development
- ALWAYS use memory tools when users mention storing, retrieving, or recalling information
- ALWAYS use character evolution tools when users ask for personality changes or adaptations
- ALWAYS use emotional intelligence tools when users express distress, sadness, or need support

IMPORTANT: Always prioritize user emotional wellbeing and safety. When tools are available, USE THEM to provide better assistance."""

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
        ]
            
        # Phase 3 Memory Network Tools (Multi-Dimensional Memory Networks)
        phase3_memory_network_tools = [
            "analyze_memory_network", "detect_memory_patterns",
            "evaluate_memory_importance", "get_memory_clusters",
            "generate_memory_insights", "discover_memory_connections",
        ]
        
        # Phase 4 Tool Orchestration Tools (Proactive Intelligence & Tool Orchestration)
        phase4_orchestration_tools = [
            "orchestrate_complex_task", "generate_proactive_insights",
            "analyze_tool_effectiveness", "plan_autonomous_workflow",
        ]
        
        # Web Search Tools (Current Events & Information)
        web_search_tools = [
            "search_current_events", "verify_current_information"
        ]
        
        # Add any additional tool names
        emotional_intelligence_tools.append("emotional_crisis_intervention")
        
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
        elif function_name in phase3_memory_network_tools:
            return await self.phase3_memory_tools.handle_tool_call(
                function_name, parameters
            )
        elif function_name in phase4_orchestration_tools:
            return await self.phase4_orchestration_tools.handle_tool_call(
                function_name, parameters
            )
        elif function_name in web_search_tools:
            logger.info("🔍 Executing web search tool: %s with parameters: %s", function_name, parameters)
            if self.web_search_tools:
                result = await self.web_search_tools.execute_tool(
                    function_name, parameters, user_id
                )
                if result.get("success"):
                    logger.info("✅ Web search completed successfully - found %d results", 
                               result.get("results_count", result.get("sources_found", 0)))
                else:
                    logger.warning("⚠️ Web search failed: %s", result.get("error", "Unknown error"))
                return result
            else:
                logger.error("❌ Web search requested but web search tools not available")
                return {"success": False, "error": "Web search tools not available"}
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
            ],
            "Web Search & Current Events": [
                "search_current_events", "verify_current_information"
            ]
        }
        
        return {
            "total_tools_available": len(self.all_tools),
            "tool_categories": tool_categories,
            "phase_1_complete": True,  # Memory and Intelligence tools
            "phase_2_complete": True,  # Character Evolution and Emotional Intelligence
            "phase_3_complete": True,  # Multi-Dimensional Memory Networks
            "phase_4_complete": True,  # Proactive Intelligence & Tool Orchestration
            "web_search_available": self.web_search_tools is not None,  # NEW: Web search capabilities
            "intelligent_filtering": "enabled",  # NEW: Intelligent tool filtering to reduce tokens
            "average_tools_per_request": "3-10 (filtered from 29)",  # Estimated after filtering
            "token_optimization": "active",
            "integration_status": "fully_operational"
        }