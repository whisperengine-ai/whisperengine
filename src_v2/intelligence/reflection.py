from typing import List, Dict, Any, Optional
import json
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src_v2.core.database import db_manager
from src_v2.agents.llm_factory import create_llm
from src_v2.memory.manager import memory_manager

class ReflectionResult(BaseModel):
    insights: List[str] = Field(description="List of high-level insights about the user (e.g., 'Values honesty', 'Stressed about work').")
    updated_traits: List[str] = Field(description="List of personality traits the user has revealed.")

class ReflectionEngine:
    def __init__(self):
        self.llm = create_llm(temperature=0.4)
        self.parser = PydanticOutputParser(pydantic_object=ReflectionResult)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert psychologist AI.
Your goal is to analyze a series of conversation summaries and extract high-level insights about the user.

INPUT:
A list of recent conversation summaries.

OUTPUT:
1. Insights: Deep observations about the user's personality, values, struggles, or preferences.
2. Traits: Specific personality traits observed.

RULES:
- Be specific but concise.
- Focus on patterns across multiple sessions if possible.
- Ignore trivial details.

{format_instructions}
"""),
            ("human", "Recent Summaries:\n{summaries_text}")
        ])

    async def analyze_user_patterns(self, user_id: str, character_name: str) -> Optional[ReflectionResult]:
        """
        Analyzes recent summaries for a user and updates their insights profile.
        """
        if not db_manager.postgres_pool:
            return None

        try:
            # 1. Fetch recent summaries (last 5)
            # We need to query v2_summaries joined with v2_conversation_sessions
            async with db_manager.postgres_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT s.content, s.meaningfulness_score, sess.start_time
                    FROM v2_summaries s
                    JOIN v2_conversation_sessions sess ON s.session_id = sess.id
                    WHERE sess.user_id = $1 AND sess.character_name = $2
                    ORDER BY sess.start_time DESC
                    LIMIT 5
                """, user_id, character_name)
                
                if not rows:
                    logger.info("No summaries found for reflection.")
                    return None
                
                summaries_text = ""
                for row in rows:
                    summaries_text += f"- [{row['start_time']}] (Score: {row['meaningfulness_score']}): {row['content']}\n"

            # 2. Generate Reflection
            chain = self.prompt | self.llm | self.parser
            result = await chain.ainvoke({
                "summaries_text": summaries_text,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # 3. Update Database
            await self._update_user_insights(user_id, character_name, result)
            
            return result

        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            return None

    async def _update_user_insights(self, user_id: str, character_name: str, result: ReflectionResult):
        """
        Updates the v2_user_relationships table with new insights.
        """
        if not db_manager.postgres_pool:
            return

        try:
            async with db_manager.postgres_pool.acquire() as conn:
                # Fetch existing insights
                current_data = await conn.fetchval("""
                    SELECT insights 
                    FROM v2_user_relationships 
                    WHERE user_id = $1 AND character_name = $2
                """, user_id, character_name)
                
                existing_insights = []
                if current_data:
                    # If it's already a dict/list (jsonb), use it. 
                    # If it's a string, parse it.
                    if isinstance(current_data, str):
                        existing_insights = json.loads(current_data)
                    else:
                        existing_insights = current_data
                
                # Merge new insights (simple append for now, could be smarter)
                # We'll store it as a list of strings for simplicity
                if not isinstance(existing_insights, list):
                    existing_insights = []
                
                # Add new unique insights
                for insight in result.insights:
                    if insight not in existing_insights:
                        existing_insights.append(insight)
                
                # Update DB
                await conn.execute("""
                    UPDATE v2_user_relationships
                    SET insights = $1, updated_at = NOW()
                    WHERE user_id = $2 AND character_name = $3
                """, json.dumps(existing_insights), user_id, character_name)
                
                logger.info(f"Updated insights for user {user_id}: {len(result.insights)} new insights.")

        except Exception as e:
            logger.error(f"Failed to update user insights: {e}")

# Global instance
reflection_engine = ReflectionEngine()
