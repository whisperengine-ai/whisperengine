from typing import List, Optional
from loguru import logger
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src_v2.config.settings import settings
from src_v2.core.database import db_manager
from src_v2.knowledge.extractor import FactExtractor, Fact
from src_v2.agents.llm_factory import create_llm

class KnowledgeManager:
    def __init__(self):
        self.extractor = FactExtractor()
        self.llm = create_llm(temperature=0.0)
        
        self.cypher_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Neo4j Cypher developer.
Your task is to convert a natural language question into a Cypher query to retrieve information about a user.

SCHEMA:
- Nodes: (:User {{id: $user_id}}), (:Entity {{name: "..."}})
- Relationships: [:FACT {{predicate: "..."}}] (e.g., predicate="LIKES", "OWNS", "LIVES_IN")

EXAMPLES:
1. Q: "What do I like?"
   A: MATCH (u:User {{id: $user_id}})-[r:FACT]->(o:Entity) WHERE r.predicate = 'LIKES' RETURN o.name

2. Q: "Where do I live?"
   A: MATCH (u:User {{id: $user_id}})-[r:FACT]->(o:Entity) WHERE r.predicate = 'LIVES_IN' RETURN o.name

3. Q: "Do I have any pets?"
   A: MATCH (u:User {{id: $user_id}})-[r:FACT]->(o:Entity) WHERE r.predicate = 'OWNS' OR o.name CONTAINS 'dog' OR o.name CONTAINS 'cat' RETURN r.predicate, o.name

RULES:
- ALWAYS use the parameter $user_id for the User node.
- Return the relevant properties (usually o.name or r.predicate).
- Do NOT include markdown formatting (```cypher). Just the raw query.
- Use case-insensitive matching if unsure (e.g., toLower(r.predicate) = 'likes').
"""),
            ("human", "{question}")
        ])
        self.cypher_chain = self.cypher_prompt | self.llm | StrOutputParser()

    async def initialize(self):
        """
        Initializes the Knowledge Graph schema (constraints and indexes).
        """
        if not db_manager.neo4j_driver:
            logger.warning("Neo4j driver not available. Skipping Knowledge Graph initialization.")
            return

        try:
            async with db_manager.neo4j_driver.session() as session:
                # Create constraints (which also create indexes)
                # User id must be unique
                await session.run("CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
                
                # Entity name should be indexed/unique
                await session.run("CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")
                
                # Register relationship types and properties to avoid warnings
                # Create a dummy pattern and delete it immediately
                await session.run("""
                    MERGE (u:User {id: '_schema_init_'})
                    MERGE (e:Entity {name: '_schema_init_'})
                    MERGE (u)-[r:FACT {predicate: '_init_', confidence: 0.0}]->(e)
                    DELETE r, u, e
                """)

                logger.info("Knowledge Graph schema initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Knowledge Graph schema: {e}")

    async def query_graph(self, user_id: str, question: str) -> str:
        """
        Generates and executes a Cypher query based on a natural language question.
        """
        if not db_manager.neo4j_driver:
            return "Graph database not available."

        try:
            # 1. Generate Cypher
            cypher_query = await self.cypher_chain.ainvoke({"question": question})
            cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()
            
            logger.info(f"Generated Cypher: {cypher_query}")

            # 2. Execute
            async with db_manager.neo4j_driver.session() as session:
                result = await session.run(cypher_query, user_id=user_id)
                records = await result.data()
                
                if not records:
                    return "No relevant information found in the graph."
                
                # Format results
                formatted_results = []
                for record in records:
                    # Flatten the record values
                    values = [str(v) for v in record.values()]
                    formatted_results.append(" ".join(values))
                
                return ", ".join(formatted_results)

        except Exception as e:
            logger.error(f"Graph query failed: {e}")
            return "Error querying knowledge graph."

    async def process_user_message(self, user_id: str, message: str):
        """
        Extracts facts from the message and stores them in the Knowledge Graph.
        """
        if not settings.ENABLE_RUNTIME_FACT_EXTRACTION:
            return

        if not db_manager.neo4j_driver:
            return

        # 1. Extract Facts
        facts = await self.extractor.extract_facts(message)
        if not facts:
            return

        logger.info(f"Extracted {len(facts)} facts for user {user_id}")

        # 2. Store in Neo4j
        async with db_manager.neo4j_driver.session() as session:
            for fact in facts:
                await session.execute_write(self._merge_fact, user_id, fact)

    @staticmethod
    async def _merge_fact(tx, user_id: str, fact: Fact):
        """
        Cypher query to merge the fact into the graph.
        Handles single-value predicates and antonym conflicts.
        """
        SINGLE_VALUE_PREDICATES = {"LIVES_IN", "HAS_NAME", "IS_AGED", "HAS_GENDER"}
        ANTONYM_PAIRS = {
            "LIKES": ["HATES", "DISLIKES"],
            "LOVES": ["HATES", "DISLIKES"],
            "HATES": ["LIKES", "LOVES"],
            "DISLIKES": ["LIKES", "LOVES"]
        }
        
        predicate = fact.predicate.upper()

        # 1. Handle Single Value Predicates (Global overwrite)
        if predicate in SINGLE_VALUE_PREDICATES:
            delete_query = """
            MATCH (u:User {id: $user_id})-[r:FACT {predicate: $predicate}]->()
            DELETE r
            """
            await tx.run(delete_query, user_id=user_id, predicate=predicate)

        # 2. Handle Antonyms (Specific object overwrite)
        if predicate in ANTONYM_PAIRS:
            antonyms = ANTONYM_PAIRS[predicate]
            # Delete relationships with antonym predicates to the SAME object
            delete_antonym_query = """
            MATCH (u:User {id: $user_id})-[r:FACT]->(o:Entity {name: $object_name})
            WHERE r.predicate IN $antonyms
            DELETE r
            """
            await tx.run(delete_antonym_query, 
                         user_id=user_id, 
                         object_name=fact.object, 
                         antonyms=antonyms)

        # 3. Merge New Fact
        query_safe = """
        MERGE (u:User {id: $user_id})
        MERGE (o:Entity {name: $object_name})
        MERGE (u)-[r:FACT {predicate: $predicate}]->(o)
        SET r.confidence = $confidence
        """
        
        await tx.run(query_safe, 
                     user_id=user_id, 
                     object_name=fact.object, 
                     predicate=predicate,
                     confidence=fact.confidence)

    async def get_user_knowledge(self, user_id: str, limit: int = 10) -> str:
        """
        Retrieves known facts about the user.
        """
        if not db_manager.neo4j_driver:
            return ""

        try:
            async with db_manager.neo4j_driver.session() as session:
                result = await session.execute_read(self._fetch_facts, user_id, limit)
                return "\n".join(result)
        except Exception as e:
            logger.error(f"Failed to fetch knowledge: {e}")
            return ""

    @staticmethod
    async def _fetch_facts(tx, user_id: str, limit: int) -> List[str]:
        query = """
        MATCH (u:User {id: $user_id})-[r:FACT]->(o:Entity)
        RETURN r.predicate, o.name
        ORDER BY r.confidence DESC
        LIMIT $limit
        """
        result = await tx.run(query, user_id=user_id, limit=limit)
        records = await result.data()
        
        facts = []
        for record in records:
            predicate = record['r.predicate']
            obj = record['o.name']
            # Format: "User LIKES Pizza"
            facts.append(f"User {predicate} {obj}")
            
        return facts

# Global instance
knowledge_manager = KnowledgeManager()
