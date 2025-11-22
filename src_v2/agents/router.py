from typing import List, Dict, Any, Optional
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool

from src_v2.agents.llm_factory import create_llm
from src_v2.tools.memory_tools import SearchSummariesTool, SearchEpisodesTool, LookupFactsTool

class CognitiveRouter:
    """
    The 'Brain' of the agent. Decides which memory tools to use based on the user's input.
    Implements 'Reasoning Transparency' by logging why a tool was chosen.
    """
    def __init__(self):
        self.llm = create_llm(temperature=0.0) # Low temp for deterministic routing

    async def route_and_retrieve(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Analyzes the query, selects tools, executes them, and returns the context.
        
        Returns:
            Dict with keys:
            - context: str (The gathered information)
            - reasoning: str (Why the tools were chosen)
            - tool_calls: List[str] (Names of tools called)
        """
        
        # 1. Instantiate tools with the current user_id
        tools = [
            SearchSummariesTool(user_id=user_id),
            SearchEpisodesTool(user_id=user_id),
            LookupFactsTool(user_id=user_id)
        ]
        
        # 2. Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(tools)
        
        # 3. Create System Prompt
        system_prompt = """You are the Cognitive Router for an advanced AI companion.
Your goal is to determine if the user's message requires retrieving external memory or facts.

AVAILABLE TOOLS:
- search_archived_summaries: For broad topics, past events, or "what did we talk about last week?".
- search_specific_memories: For specific details, quotes, or "what was the name of that movie?".
- lookup_user_facts: For biographical info about the user (name, pets, location, preferences).

RULES:
1. If the user is just saying "hi" or small talk, DO NOT call any tools.
2. If the user asks a question that requires memory, CALL the appropriate tool.
3. You can call multiple tools if needed.

Analyze the user's input and decide."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        # 4. Invoke LLM
        try:
            response = await llm_with_tools.ainvoke(messages)
        except Exception as e:
            logger.error(f"Router LLM invocation failed: {e}")
            return {"context": "", "reasoning": "Error in router", "tool_calls": []}

        tool_calls = response.tool_calls
        context_parts = []
        executed_tool_names = []
        
        # 5. Execute Tools
        if tool_calls:
            logger.info(f"Router decided to call {len(tool_calls)} tools: {[tc['name'] for tc in tool_calls]}")
            
            for tc in tool_calls:
                tool_name = tc['name']
                tool_args = tc['args']
                executed_tool_names.append(tool_name)
                
                # Find the matching tool instance
                tool_instance = next((t for t in tools if t.name == tool_name), None)
                
                if tool_instance:
                    try:
                        logger.debug(f"Executing {tool_name} with args: {tool_args}")
                        # We use ainvoke directly. The user_id is already in the tool instance.
                        result = await tool_instance.ainvoke(tool_args)
                        context_parts.append(f"--- Result from {tool_name} ---\n{result}")
                    except Exception as e:
                        logger.error(f"Tool execution failed for {tool_name}: {e}")
                        context_parts.append(f"Error executing {tool_name}: {e}")
                else:
                    logger.warning(f"LLM called unknown tool: {tool_name}")

            reasoning = f"Decided to call: {', '.join(executed_tool_names)}"
        else:
            logger.info("Router decided NO tools were needed.")
            reasoning = "No memory retrieval needed (Small talk / Immediate context)."

        return {
            "context": "\n\n".join(context_parts),
            "reasoning": reasoning,
            "tool_calls": executed_tool_names
        }
