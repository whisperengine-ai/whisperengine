from typing import Dict, Any, Optional
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from src_v2.agents.llm_factory import create_llm

class StyleAnalysisResult(BaseModel):
    consistency_score: int = Field(description="Score 1-10 on how well the response matches the character definition")
    tone_score: int = Field(description="Score 1-10 on how well the tone matches")
    formatting_score: int = Field(description="Score 1-10 on correct formatting (emojis, length)")
    critique: str = Field(description="Specific feedback on what was wrong")
    suggestion: str = Field(description="How to improve the response")

class StyleAnalyzer:
    def __init__(self):
        self.llm = create_llm(temperature=0.0)
        self.parser = JsonOutputParser(pydantic_object=StyleAnalysisResult)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Creative Writing Editor and Character Acting Coach.
Your task is to evaluate a roleplay response against a character definition.

CHARACTER DEFINITION:
{character_def}

CONTEXT AVAILABLE TO BOT:
{context_used}

BOT RESPONSE:
{response}

Evaluate the response based on:
1. Voice/Persona: Does it sound like the character? (e.g., Sarcastic, Formal, Shy)
2. Tone: Is the emotional tone appropriate?
3. Formatting: Are emojis used correctly? Is the length appropriate?
4. Knowledge Usage: Did the bot use the CONTEXT AVAILABLE naturally? (If context is provided, the bot SHOULD use it).

Return a JSON object with scores (1-10) and constructive critique.
{format_instructions}
"""),
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    async def analyze_style(self, response: str, character_def: str, context_used: str = "") -> StyleAnalysisResult:
        """
        Analyzes the style of a response against the character definition.
        """
        try:
            result = await self.chain.ainvoke({
                "character_def": character_def,
                "context_used": context_used,
                "response": response,
                "format_instructions": self.parser.get_format_instructions()
            })
            # Convert dict to Pydantic model if needed, though JsonOutputParser usually returns dict
            return StyleAnalysisResult(**result)
        except Exception as e:
            logger.error(f"Style analysis failed: {e}")
            # Return a neutral result on failure
            return StyleAnalysisResult(
                consistency_score=5,
                tone_score=5,
                formatting_score=5,
                critique="Analysis failed.",
                suggestion="None"
            )

# Global instance
style_analyzer = StyleAnalyzer()
