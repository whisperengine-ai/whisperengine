from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from loguru import logger
from src_v2.agents.llm_factory import create_llm

class Fact(BaseModel):
    subject: str = Field(description="The subject of the fact (e.g., 'User', 'Luna')")
    predicate: str = Field(description="The relationship or action (e.g., 'OWNS', 'LIKES', 'IS_LOCATED_IN')")
    object: str = Field(description="The object of the fact (e.g., 'Cat', 'Blue', 'New York')")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")

class FactExtractionResult(BaseModel):
    facts: List[Fact] = Field(default_factory=list)

class FactExtractor:
    def __init__(self):
        self.llm = create_llm(temperature=0.0) # Low temp for extraction
        self.parser = PydanticOutputParser(pydantic_object=FactExtractionResult)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Knowledge Graph Engineer. 
Your task is to extract structured facts from user messages to build a knowledge graph about the user.

Extract facts in the format: (Subject)-[PREDICATE]->(Object).
- Subject should usually be 'User' if the user is talking about themselves.
- Predicates should be UPPERCASE verbs (e.g., LIKES, OWNS, LIVES_IN, HAS_JOB).
- Objects should be specific entities.

Only extract facts that are explicitly stated and have long-term value (e.g., names, pets, location, preferences).
Ignore transient states (e.g., "I am hungry", "I am walking").

{format_instructions}
"""),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    async def extract_facts(self, text: str) -> List[Fact]:
        try:
            result = await self.chain.ainvoke({
                "input": text,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result.facts
        except Exception as e:
            logger.error(f"Fact extraction failed: {e}")
            return []
