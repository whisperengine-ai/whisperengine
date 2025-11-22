from typing import List, Dict, Any, Optional
import uuid
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src_v2.core.database import db_manager
from src_v2.agents.llm_factory import create_llm
from src_v2.memory.manager import MemoryManager

class SummaryResult(BaseModel):
    summary: str = Field(description="The concise summary of the conversation. Include key topics and facts.")
    meaningfulness_score: int = Field(description="A score from 1-5 indicating how meaningful/deep the conversation was. 1=Trivial, 5=Profound.")
    emotions: List[str] = Field(description="List of prevailing emotions detected in the conversation.")

class SummaryManager:
    def __init__(self):
        self.llm = create_llm(temperature=0.3)
        self.memory_manager = MemoryManager()
        self.parser = PydanticOutputParser(pydantic_object=SummaryResult)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert conversation summarizer for an AI companion.
Your goal is to compress the conversation into a concise summary that preserves context for future recall.

RULES:
1. Focus on FACTS, TOPICS, and USER OPINIONS.
2. Ignore generic greetings ("Hi", "Hello") unless they are the only content.
3. Rate "Meaningfulness" (1-5):
   - 1: Small talk, greetings, short jokes.
   - 3: Hobbies, daily events, opinions.
   - 5: Deep emotional sharing, philosophy, life goals, trauma.
4. Detect Emotions: List 2-3 dominant emotions.

{format_instructions}
"""),
            ("human", "Conversation to summarize:\n{conversation_text}")
        ])

    async def generate_summary(self, messages: List[Dict[str, Any]]) -> Optional[SummaryResult]:
        """
        Generates a summary from a list of message dictionaries.
        Messages should have 'role' and 'content'.
        """
        if not messages:
            return None

        # Format conversation text
        conversation_text = ""
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            conversation_text += f"{role}: {content}\n"

        try:
            chain = self.prompt | self.llm | self.parser
            result = await chain.ainvoke({
                "conversation_text": conversation_text,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None

    async def save_summary(self, session_id: str, result: SummaryResult):
        """
        Saves the summary to Postgres and Qdrant.
        """
        if not db_manager.postgres_pool:
            return

        try:
            # 1. Save to Postgres
            summary_id = uuid.uuid4()
            async with db_manager.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO v2_summaries (id, session_id, content, meaningfulness_score)
                    VALUES ($1, $2, $3, $4)
                """, summary_id, session_id, result.summary, result.meaningfulness_score)
            
            # 2. Embed and Save to Qdrant (Collection: summaries)
            # We need to ensure the 'summaries' collection exists or use the main one with a tag.
            # For now, let's use the main collection but with type='summary' payload.
            
            # Construct payload
            payload = {
                "type": "summary",
                "session_id": str(session_id),
                "meaningfulness_score": result.meaningfulness_score,
                "emotions": result.emotions,
                "content": result.summary
            }
            
            # Use MemoryManager to save (we might need to expose a raw save method)
            # For now, let's assume we can use the embedding service directly if we had it exposed,
            # but MemoryManager encapsulates it.
            # Let's add a method to MemoryManager to save structured data.
            
            # For now, I'll just log it as a TODO until I update MemoryManager
            logger.info(f"Summary saved to Postgres: {summary_id}")
            
            # Call MemoryManager to save vector
            embedding_id = await self.memory_manager.save_summary_vector(
                session_id=session_id,
                content=result.summary,
                meaningfulness_score=result.meaningfulness_score,
                emotions=result.emotions
            )
            
            if embedding_id:
                # Update Postgres with embedding_id
                async with db_manager.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE v2_summaries 
                        SET embedding_id = $1 
                        WHERE id = $2
                    """, uuid.UUID(embedding_id), summary_id)
            
        except Exception as e:
            logger.error(f"Failed to save summary to DB: {e}")
