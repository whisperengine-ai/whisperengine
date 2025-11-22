from typing import List
from loguru import logger
from src_v2.config.settings import settings
from src_v2.core.database import db_manager
from src_v2.knowledge.extractor import FactExtractor, Fact

class KnowledgeManager:
    def __init__(self):
        self.extractor = FactExtractor()

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
        """
        query = """
        MERGE (u:User {id: $user_id})
        MERGE (o:Entity {name: $object_name})
        WITH u, o
        CALL apoc.create.relationship(u, $predicate, {}, o) YIELD rel
        RETURN rel
        """
        # Note: Dynamic relationship types in pure Cypher are tricky. 
        # APOC is best, but if not available, we might need string injection (carefully).
        # For safety/simplicity without APOC, we can use a generic relationship with a type property,
        # OR sanitize the predicate and inject it.
        
        # Let's try a safer approach without APOC for now to avoid dependency hell:
        # (User)-[FACT {type: "LIKES"}]->(Entity)
        
        query_safe = """
        MERGE (u:User {id: $user_id})
        MERGE (o:Entity {name: $object_name})
        MERGE (u)-[r:FACT {predicate: $predicate}]->(o)
        SET r.confidence = $confidence
        """
        
        await tx.run(query_safe, 
                     user_id=user_id, 
                     object_name=fact.object, 
                     predicate=fact.predicate.upper(),
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
