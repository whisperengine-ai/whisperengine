from typing import Type, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from loguru import logger

from src_v2.memory.manager import memory_manager
from src_v2.knowledge.manager import knowledge_manager
from src_v2.evolution.trust import trust_manager

class SearchSummariesInput(BaseModel):
    query: str = Field(description="The topic or concept to search for in past conversation summaries.")
    time_range: Optional[str] = Field(description="Optional time range (e.g., 'last week', 'yesterday').", default=None)

class SearchSummariesTool(BaseTool):
    name: str = "search_archived_summaries"
    description: str = "Searches high-level summaries of past conversations. Use this to recall topics, events, or emotional context from days or weeks ago."
    args_schema: Type[BaseModel] = SearchSummariesInput
    user_id: str = Field(exclude=True) # Exclude from LLM schema

    def _run(self, query: str, time_range: Optional[str] = None) -> str:
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, query: str, time_range: Optional[str] = None) -> str:
        try:
            results = await memory_manager.search_summaries(query, self.user_id)
            if not results:
                return "No relevant summaries found."
            
            formatted = "\n".join([
                f"- [Score: {r['meaningfulness']}/5] {r['content']} ({r['timestamp'][:10]})" 
                for r in results
            ])
            return f"Found Summaries:\n{formatted}"
        except Exception as e:
            return f"Error searching summaries: {e}"

class SearchEpisodesInput(BaseModel):
    query: str = Field(description="The specific detail or quote to search for.")

class SearchEpisodesTool(BaseTool):
    name: str = "search_specific_memories"
    description: str = "Searches for specific details, quotes, or moments in conversation history. Use this for specific questions like 'What was that boat name?'."
    args_schema: Type[BaseModel] = SearchEpisodesInput
    user_id: str = Field(exclude=True)

    def _run(self, query: str) -> str:
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, query: str) -> str:
        try:
            # Use standard memory search (episodes)
            results = await memory_manager.search_memories(query, self.user_id)
            if not results:
                return "No specific memories found."
            
            formatted = "\n".join([f"- {r['content']}" for r in results])
            return f"Found Episodes:\n{formatted}"
        except Exception as e:
            return f"Error searching episodes: {e}"

class LookupFactsInput(BaseModel):
    query: str = Field(description="The natural language query for user facts (e.g. 'What is my dog's name?').")

class LookupFactsTool(BaseTool):
    name: str = "lookup_user_facts"
    description: str = "Retrieves structured facts about the user from the Knowledge Graph. Use this for verifying names, relationships, preferences, or biographical info."
    args_schema: Type[BaseModel] = LookupFactsInput
    user_id: str = Field(exclude=True)

    def _run(self, query: str) -> str:
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, query: str) -> str:
        try:
            # TODO: Implement knowledge_manager.query_graph(user_id, query)
            # For now, return a placeholder or call existing method
            # facts = await knowledge_manager.get_user_knowledge(self.user_id)
            # But we want to query based on the input 'query'.
            # Let's assume get_user_knowledge returns everything for now.
            
            facts = await knowledge_manager.get_user_knowledge(self.user_id)
            return f"User Facts:\n{facts}"
        except Exception as e:
            return f"Error looking up facts: {e}"


class GetEvolutionStateInput(BaseModel):
    """No parameters needed - retrieves current state for this user."""
    pass

class CharacterEvolutionTool(BaseTool):
    name: str = "get_character_evolution"
    description: str = "Retrieves the current relationship level, trust score, and unlocked personality traits between you and the user. Use this to understand how your personality should adapt to this specific relationship."
    args_schema: Type[BaseModel] = GetEvolutionStateInput
    user_id: str = Field(exclude=True)
    character_name: str = Field(exclude=True)

    def _run(self) -> str:
        raise NotImplementedError("Use _arun instead")

    async def _arun(self) -> str:
        try:
            relationship = await trust_manager.get_relationship_level(self.user_id, self.character_name)
            
            output = f"""Current Relationship State:
- Trust Score: {relationship['trust_score']}/150
- Relationship Level: {relationship['level']}
- Unlocked Traits: {', '.join(relationship['unlocked_traits']) if relationship['unlocked_traits'] else 'None yet'}

This means you should behave as a {relationship['level'].lower()} with this user."""
            
            return output
        except Exception as e:
            return f"Error retrieving evolution state: {e}"
