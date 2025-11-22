from typing import Optional
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

from src_v2.agents.llm_factory import create_llm
from src_v2.core.character import character_manager
from src_v2.memory.manager import memory_manager
from src_v2.knowledge.manager import knowledge_manager
from src_v2.evolution.trust import trust_manager
from src_v2.config.settings import settings

class ProactiveAgent:
    """
    Generates context-aware opening messages to initiate conversation with the user.
    """
    def __init__(self):
        self.llm = create_llm(temperature=0.8) # Higher temp for creativity

    async def generate_opener(self, user_id: str, character_name: str) -> Optional[str]:
        """
        Generates a proactive opening message based on recent memories and knowledge.
        """
        try:
            # 1. Load Character
            character = character_manager.get_character(character_name)
            if not character:
                logger.error(f"Character {character_name} not found.")
                return None

            # 2. Gather Context
            # We want recent memories to know what we last talked about
            recent_history = await memory_manager.get_recent_history(user_id, character_name, limit=5)
            
            # We want knowledge facts to ask about specific things (e.g., "How is your cat?")
            knowledge_facts = await knowledge_manager.get_user_knowledge(user_id)
            
            # We want relationship status to know the tone
            relationship = await trust_manager.get_relationship_level(user_id, character_name)

            # 3. Construct Prompt
            system_prompt = f"""You are {character.name}.
{character.system_prompt}

TASK:
You are initiating a conversation with the user after a period of silence.
Your goal is to send a friendly, relevant opening message.
Do NOT say "Hello" or "Hi" generically.
Reference a specific topic from the past or a fact you know about them.
Keep it short (1-2 sentences).
Be natural, like a friend texting another friend.

[RELATIONSHIP STATUS]
Level: {relationship.get('level', 'Stranger')}
Trust: {relationship.get('trust_score', 0)}

[KNOWN FACTS]
{knowledge_facts}

[RECENT CONVERSATION TOPICS]
"""
            # Add summary of recent history if available
            if recent_history:
                # We just dump the raw messages for context
                for msg in recent_history:
                    role = "User" if isinstance(msg, HumanMessage) else character.name
                    system_prompt += f"{role}: {msg.content}\n"
            else:
                system_prompt += "(No recent history available)\n"

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "Generate a proactive opening message now.")
            ])

            # 4. Generate
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            
            content = response.content
            if isinstance(content, str):
                opener = content.strip()
            else:
                # Handle list content (rare for text-only models but possible in LangChain)
                opener = str(content).strip()

            logger.info(f"Generated proactive opener for {user_id}: {opener}")
            return opener

        except Exception as e:
            logger.error(f"Failed to generate proactive opener: {e}")
            return None

proactive_agent = ProactiveAgent()
