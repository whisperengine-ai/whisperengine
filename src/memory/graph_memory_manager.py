"""Graph-based memory manager for integrating ChromaDB with Neo4j for global facts."""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..graph_database.neo4j_connector import get_neo4j_connector, Neo4jConnector
from ..graph_database.models import (
    GlobalFactNode,
    KnowledgeDomainNode,
    FactRelationshipTypes,
    KnowledgeDomains,
)

logger = logging.getLogger(__name__)


class GraphMemoryManager:
    """Manages global facts with hybrid ChromaDB + Neo4j storage."""

    def __init__(self):
        self._neo4j_connector: Optional[Neo4jConnector] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the graph memory manager."""
        if self._initialized:
            return

        try:
            self._neo4j_connector = await get_neo4j_connector()
            await self._ensure_default_domains()
            self._initialized = True
            logger.info("GraphMemoryManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GraphMemoryManager: {e}")
            raise

    async def _ensure_default_domains(self) -> None:
        """Ensure default knowledge domains exist in the graph."""
        if not self._neo4j_connector:
            return

        default_domains = [
            # Top-level domains
            (KnowledgeDomains.SCIENCE, "Natural and physical sciences", None),
            (KnowledgeDomains.TECHNOLOGY, "Technology and computing", None),
            (KnowledgeDomains.HISTORY, "Historical events and periods", None),
            (KnowledgeDomains.PHILOSOPHY, "Philosophical concepts and ideas", None),
            (KnowledgeDomains.ARTS, "Creative arts and expression", None),
            (KnowledgeDomains.GENERAL, "General knowledge", None),
            # Science sub-domains
            (KnowledgeDomains.PHYSICS, "Physics and physical phenomena", KnowledgeDomains.SCIENCE),
            (
                KnowledgeDomains.CHEMISTRY,
                "Chemistry and chemical processes",
                KnowledgeDomains.SCIENCE,
            ),
            (KnowledgeDomains.BIOLOGY, "Biology and life sciences", KnowledgeDomains.SCIENCE),
            (
                KnowledgeDomains.MATHEMATICS,
                "Mathematics and mathematical concepts",
                KnowledgeDomains.SCIENCE,
            ),
            # Social sciences
            (
                KnowledgeDomains.PSYCHOLOGY,
                "Psychology and human behavior",
                KnowledgeDomains.SCIENCE,
            ),
            (
                KnowledgeDomains.SOCIOLOGY,
                "Sociology and social structures",
                KnowledgeDomains.SCIENCE,
            ),
            (
                KnowledgeDomains.ECONOMICS,
                "Economics and economic systems",
                KnowledgeDomains.SCIENCE,
            ),
            (KnowledgeDomains.POLITICS, "Politics and governance", KnowledgeDomains.SCIENCE),
            # Humanities
            (KnowledgeDomains.LITERATURE, "Literature and written works", KnowledgeDomains.ARTS),
            (
                KnowledgeDomains.GEOGRAPHY,
                "Geography and spatial knowledge",
                KnowledgeDomains.SCIENCE,
            ),
        ]

        for domain_name, description, parent_domain in default_domains:
            try:
                await self._neo4j_connector.create_or_update_knowledge_domain(
                    domain_name, description, parent_domain
                )
            except Exception as e:
                logger.warning(f"Failed to create domain {domain_name}: {e}")

    async def store_global_fact_hybrid(
        self,
        chromadb_id: str,
        fact_content: str,
        knowledge_domain: str = KnowledgeDomains.GENERAL,
        confidence_score: float = 0.8,
        source: str = "learned",
        fact_type: str = "declarative",
        tags: Optional[List[str]] = None,
    ) -> str:
        """Store a global fact in both ChromaDB (via existing system) and Neo4j."""
        if not self._initialized:
            await self.initialize()

        # Generate unique fact ID
        fact_id = f"fact_{uuid.uuid4().hex[:12]}"

        # Store in Neo4j graph database
        try:
            if self._neo4j_connector:
                result = await self._neo4j_connector.store_global_fact(
                    fact_id=fact_id,
                    chromadb_id=chromadb_id,
                    fact_content=fact_content,
                    knowledge_domain=knowledge_domain,
                    confidence_score=confidence_score,
                    source=source,
                    fact_type=fact_type,
                    tags=tags or [],
                )
                logger.debug(f"Stored global fact in Neo4j: {fact_id}")
            else:
                logger.warning("Neo4j connector not available for global fact storage")
        except Exception as e:
            logger.error(f"Failed to store global fact in Neo4j: {e}")
            # Continue without Neo4j storage - ChromaDB should still work

        return fact_id

    async def create_fact_relationship(
        self,
        fact_id_1: str,
        fact_id_2: str,
        relationship_type: str = FactRelationshipTypes.RELATES_TO,
        strength: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a relationship between two global facts using ChromaDB IDs or Graph IDs."""
        if not self._initialized:
            await self.initialize()

        if not self._neo4j_connector:
            logger.warning("Neo4j connector not available for relationship creation")
            return False

        try:
            # First try to find facts by ChromaDB ID, then by Graph ID
            fact_1 = await self._neo4j_connector.get_fact_by_chromadb_id(fact_id_1)
            if not fact_1:
                # Try as graph fact ID
                query = "MATCH (gf:GlobalFact {id: $fact_id}) RETURN gf"
                result = await self._neo4j_connector.execute_query(query, {"fact_id": fact_id_1})
                fact_1 = result[0]["gf"] if result else None

            fact_2 = await self._neo4j_connector.get_fact_by_chromadb_id(fact_id_2)
            if not fact_2:
                # Try as graph fact ID
                query = "MATCH (gf:GlobalFact {id: $fact_id}) RETURN gf"
                result = await self._neo4j_connector.execute_query(query, {"fact_id": fact_id_2})
                fact_2 = result[0]["gf"] if result else None

            if not fact_1 or not fact_2:
                logger.warning(f"Could not find facts for relationship: {fact_id_1}, {fact_id_2}")
                return False

            # Get the graph IDs
            graph_fact_id_1 = fact_1["id"]
            graph_fact_id_2 = fact_2["id"]

            success = await self._neo4j_connector.create_fact_relationship(
                from_fact_id=graph_fact_id_1,
                to_fact_id=graph_fact_id_2,
                relationship_type=relationship_type,
                strength=strength,
                properties=properties or {},
            )

            if success:
                logger.debug(
                    f"Created {relationship_type} relationship between {fact_id_1} and {fact_id_2}"
                )

            return success
        except Exception as e:
            logger.error(f"Failed to create fact relationship: {e}")
            return False

    async def get_related_facts(
        self, chromadb_id: str, relationship_types: Optional[List[str]] = None, max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """Get facts related to a given fact through graph relationships."""
        if not self._initialized:
            await self.initialize()

        if not self._neo4j_connector:
            return []

        try:
            # First find the fact by ChromaDB ID
            fact = await self._neo4j_connector.get_fact_by_chromadb_id(chromadb_id)
            if not fact:
                logger.debug(f"No fact found for ChromaDB ID: {chromadb_id}")
                return []

            fact_id = fact["id"]

            # Get related facts
            related_facts = await self._neo4j_connector.get_related_facts(
                fact_id=fact_id, relationship_types=relationship_types, max_depth=max_depth
            )

            return related_facts
        except Exception as e:
            logger.error(f"Failed to get related facts: {e}")
            return []

    async def search_facts_by_domain(
        self, knowledge_domain: str, include_subdomain: bool = True, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for facts within a knowledge domain."""
        if not self._initialized:
            await self.initialize()

        if not self._neo4j_connector:
            return []

        try:
            facts = await self._neo4j_connector.search_facts_by_domain(
                knowledge_domain=knowledge_domain, include_subdomain=include_subdomain, limit=limit
            )

            return facts
        except Exception as e:
            logger.error(f"Failed to search facts by domain: {e}")
            return []

    async def update_fact_verification(
        self, chromadb_id: str, verification_status: str, confidence_score: Optional[float] = None
    ) -> bool:
        """Update the verification status and confidence of a fact."""
        if not self._initialized:
            await self.initialize()

        if not self._neo4j_connector:
            return False

        try:
            # Find fact by ChromaDB ID
            fact = await self._neo4j_connector.get_fact_by_chromadb_id(chromadb_id)
            if not fact:
                return False

            fact_id = fact["id"]

            success = await self._neo4j_connector.update_fact_verification(
                fact_id=fact_id,
                verification_status=verification_status,
                confidence_score=confidence_score,
            )

            return success
        except Exception as e:
            logger.error(f"Failed to update fact verification: {e}")
            return False

    async def analyze_fact_contradictions(self, chromadb_id: str) -> List[Dict[str, Any]]:
        """Analyze if a fact contradicts any existing facts."""
        contradicting_facts = await self.get_related_facts(
            chromadb_id=chromadb_id,
            relationship_types=[FactRelationshipTypes.CONTRADICTS],
            max_depth=1,
        )

        return contradicting_facts

    async def find_supporting_facts(
        self, chromadb_id: str, max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """Find facts that support a given fact."""
        supporting_facts = await self.get_related_facts(
            chromadb_id=chromadb_id,
            relationship_types=[FactRelationshipTypes.SUPPORTS, FactRelationshipTypes.ELABORATES],
            max_depth=max_depth,
        )

        return supporting_facts

    async def get_knowledge_domain_hierarchy(self, domain_name: str) -> Dict[str, Any]:
        """Get the hierarchy structure of a knowledge domain."""
        if not self._initialized:
            await self.initialize()

        if not self._neo4j_connector:
            return {}

        try:
            query = """
            MATCH (domain:KnowledgeDomain {name: $domain_name})
            OPTIONAL MATCH (domain)<-[:BELONGS_TO]-(child:KnowledgeDomain)
            OPTIONAL MATCH (domain)-[:BELONGS_TO]->(parent:KnowledgeDomain)
            
            RETURN {
                domain: domain,
                parent: parent,
                children: collect(DISTINCT child),
                total_facts: domain.fact_count
            } as hierarchy
            """

            result = await self._neo4j_connector.execute_query(query, {"domain_name": domain_name})
            return result[0]["hierarchy"] if result else {}
        except Exception as e:
            logger.error(f"Failed to get domain hierarchy: {e}")
            return {}

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the global facts graph."""
        if not self._initialized:
            await self.initialize()

        if not self._neo4j_connector:
            return {}

        try:
            query = """
            MATCH (gf:GlobalFact)
            OPTIONAL MATCH (gf)-[r]-(other:GlobalFact)
            WITH count(DISTINCT gf) as total_facts,
                 count(DISTINCT r) as total_relationships,
                 avg(gf.confidence_score) as avg_confidence
            
            MATCH (kd:KnowledgeDomain)
            WITH total_facts, total_relationships, avg_confidence,
                 count(kd) as total_domains
            
            RETURN {
                total_facts: total_facts,
                total_relationships: total_relationships,
                total_domains: total_domains,
                avg_confidence: avg_confidence
            } as stats
            """

            result = await self._neo4j_connector.execute_query(query)
            return result[0]["stats"] if result else {}
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {}


# Global instance
_graph_memory_manager: Optional[GraphMemoryManager] = None


async def get_graph_memory_manager() -> GraphMemoryManager:
    """Get or create the global GraphMemoryManager instance."""
    global _graph_memory_manager

    if _graph_memory_manager is None:
        _graph_memory_manager = GraphMemoryManager()
        await _graph_memory_manager.initialize()

    return _graph_memory_manager
