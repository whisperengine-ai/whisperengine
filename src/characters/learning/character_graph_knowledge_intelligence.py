"""
Character Graph Knowledge Intelligence
WhisperEngine Memory Intelligence Convergence - PHASE 3
Version: 1.0 - October 2025

Implements PostgreSQL semantic knowledge graph for facts, relationships, and 
structured data extraction using pure integration approach with existing 
infrastructure.

Core Capabilities:
- Extract facts and relationships from PostgreSQL user data
- Structured knowledge representation for character intelligence
- Integration with existing fact_entities and user_fact_relationships tables
- Graph-based knowledge discovery for character responses
- Pure integration approach - no new storage systems required
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncpg
import json

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeNode:
    """Represents a knowledge node in the graph."""
    entity_id: str
    entity_type: str
    properties: Dict[str, Any]
    relationships: List[Dict[str, Any]]
    confidence: float
    source: str
    timestamp: datetime

@dataclass
class KnowledgeRelationship:
    """Represents a relationship between knowledge nodes."""
    source_entity: str
    target_entity: str
    relationship_type: str
    properties: Dict[str, Any]
    confidence: float
    timestamp: datetime

@dataclass
class GraphKnowledgeResult:
    """Results from graph knowledge extraction."""
    nodes: List[KnowledgeNode]
    relationships: List[KnowledgeRelationship]
    structured_facts: Dict[str, Any]
    knowledge_summary: str
    confidence_score: float
    extraction_metadata: Dict[str, Any]

class CharacterGraphKnowledgeIntelligence:
    """
    Extracts structured knowledge and relationships from PostgreSQL infrastructure.
    
    Uses existing fact_entities and user_fact_relationships tables to build
    semantic knowledge graphs for character intelligence enhancement.
    """
    
    def __init__(self, postgres_pool=None):
        """Initialize with PostgreSQL connection pool."""
        self.postgres_pool = postgres_pool
        self.logger = logging.getLogger(__name__)
        
        # Knowledge extraction patterns
        self.fact_patterns = {
            'personal_info': ['name', 'age', 'location', 'occupation', 'interests'],
            'relationships': ['friend', 'family', 'colleague', 'partner'],
            'preferences': ['likes', 'dislikes', 'favorites', 'hobbies'],
            'experiences': ['events', 'achievements', 'travels', 'memories'],
            'goals': ['aspirations', 'plans', 'objectives', 'dreams']
        }
        
        # Relationship strength indicators
        self.relationship_weights = {
            'strong': 1.0,
            'moderate': 0.7,
            'weak': 0.4,
            'uncertain': 0.2
        }
    
    async def extract_knowledge_graph(
        self, 
        user_id: str, 
        character_name: str,
        context: Optional[str] = None
    ) -> GraphKnowledgeResult:
        """
        Extract structured knowledge graph for user-character interaction.
        
        Args:
            user_id: User identifier
            character_name: Character name for context
            context: Optional context for focused extraction
            
        Returns:
            GraphKnowledgeResult with nodes, relationships, and structured facts
        """
        try:
            if not self.postgres_pool:
                self.logger.warning("No PostgreSQL pool available - returning empty knowledge graph")
                return self._empty_knowledge_result()
            
            # Extract facts and entities from PostgreSQL
            facts = await self._extract_user_facts(user_id)
            entities = await self._extract_fact_entities(user_id)
            relationships = await self._extract_fact_relationships(user_id)
            
            # Build knowledge nodes
            knowledge_nodes = await self._build_knowledge_nodes(facts, entities)
            
            # Build knowledge relationships
            knowledge_relationships = await self._build_knowledge_relationships(relationships)
            
            # Extract structured facts by category
            structured_facts = await self._categorize_structured_facts(facts, context)
            
            # Generate knowledge summary
            knowledge_summary = await self._generate_knowledge_summary(
                knowledge_nodes, knowledge_relationships, structured_facts
            )
            
            # Calculate overall confidence
            confidence_score = await self._calculate_confidence_score(knowledge_nodes, knowledge_relationships)
            
            # Prepare metadata
            extraction_metadata = {
                'extraction_time': datetime.now().isoformat(),
                'user_id': user_id,
                'character_name': character_name,
                'context': context,
                'nodes_count': len(knowledge_nodes),
                'relationships_count': len(knowledge_relationships),
                'fact_categories': list(structured_facts.keys())
            }
            
            return GraphKnowledgeResult(
                nodes=knowledge_nodes,
                relationships=knowledge_relationships,
                structured_facts=structured_facts,
                knowledge_summary=knowledge_summary,
                confidence_score=confidence_score,
                extraction_metadata=extraction_metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting knowledge graph: {e}")
            return self._empty_knowledge_result()
    
    async def _extract_user_facts(self, user_id: str) -> List[Dict[str, Any]]:
        """Extract user facts from PostgreSQL."""
        if not self.postgres_pool:
            return []
            
        try:
            async with self.postgres_pool.acquire() as conn:
                # Query user facts from existing tables
                query = """
                    SELECT 
                        uf.id,
                        uf.fact_type,
                        uf.fact_value,
                        uf.confidence,
                        uf.source,
                        uf.created_at,
                        uf.metadata
                    FROM user_facts uf
                    WHERE uf.user_id = $1
                    ORDER BY uf.confidence DESC, uf.created_at DESC
                    LIMIT 100
                """
                
                rows = await conn.fetch(query, user_id)
                
                facts = []
                for row in rows:
                    facts.append({
                        'id': str(row['id']),
                        'fact_type': row['fact_type'],
                        'fact_value': row['fact_value'],
                        'confidence': float(row['confidence']) if row['confidence'] else 0.5,
                        'source': row['source'],
                        'created_at': row['created_at'],
                        'metadata': row['metadata'] if row['metadata'] else {}
                    })
                
                return facts
                
        except Exception as e:
            self.logger.error(f"Error extracting user facts: {e}")
            return []
    
    async def _extract_fact_entities(self, user_id: str) -> List[Dict[str, Any]]:
        """Extract fact entities from PostgreSQL."""
        if not self.postgres_pool:
            return []
            
        try:
            async with self.postgres_pool.acquire() as conn:
                # Query fact entities
                query = """
                    SELECT 
                        fe.id,
                        fe.entity_type,
                        fe.entity_value,
                        fe.properties,
                        fe.confidence,
                        fe.created_at
                    FROM fact_entities fe
                    JOIN user_facts uf ON fe.id = uf.entity_id
                    WHERE uf.user_id = $1
                    ORDER BY fe.confidence DESC
                    LIMIT 50
                """
                
                rows = await conn.fetch(query, user_id)
                
                entities = []
                for row in rows:
                    entities.append({
                        'id': str(row['id']),
                        'entity_type': row['entity_type'],
                        'entity_value': row['entity_value'],
                        'properties': row['properties'] if row['properties'] else {},
                        'confidence': float(row['confidence']) if row['confidence'] else 0.5,
                        'created_at': row['created_at']
                    })
                
                return entities
                
        except Exception as e:
            self.logger.error(f"Error extracting fact entities: {e}")
            return []
    
    async def _extract_fact_relationships(self, user_id: str) -> List[Dict[str, Any]]:
        """Extract fact relationships from PostgreSQL."""
        if not self.postgres_pool:
            return []
            
        try:
            async with self.postgres_pool.acquire() as conn:
                # Query user fact relationships
                query = """
                    SELECT 
                        ufr.id,
                        ufr.source_entity_id,
                        ufr.target_entity_id,
                        ufr.relationship_type,
                        ufr.properties,
                        ufr.confidence,
                        ufr.created_at
                    FROM user_fact_relationships ufr
                    JOIN user_facts uf ON ufr.source_entity_id = uf.entity_id
                    WHERE uf.user_id = $1
                    ORDER BY ufr.confidence DESC
                    LIMIT 50
                """
                
                rows = await conn.fetch(query, user_id)
                
                relationships = []
                for row in rows:
                    relationships.append({
                        'id': str(row['id']),
                        'source_entity_id': str(row['source_entity_id']),
                        'target_entity_id': str(row['target_entity_id']),
                        'relationship_type': row['relationship_type'],
                        'properties': row['properties'] if row['properties'] else {},
                        'confidence': float(row['confidence']) if row['confidence'] else 0.5,
                        'created_at': row['created_at']
                    })
                
                return relationships
                
        except Exception as e:
            self.logger.error(f"Error extracting fact relationships: {e}")
            return []
    
    async def _build_knowledge_nodes(
        self, 
        facts: List[Dict[str, Any]], 
        entities: List[Dict[str, Any]]
    ) -> List[KnowledgeNode]:
        """Build knowledge nodes from facts and entities."""
        nodes = []
        
        # Convert entities to knowledge nodes
        for entity in entities:
            node = KnowledgeNode(
                entity_id=entity['id'],
                entity_type=entity['entity_type'],
                properties=entity['properties'],
                relationships=[],  # Will be populated later
                confidence=entity['confidence'],
                source='fact_entities',
                timestamp=entity['created_at']
            )
            nodes.append(node)
        
        # Convert high-confidence facts to knowledge nodes
        for fact in facts:
            if fact['confidence'] >= 0.6:  # Only include confident facts
                node = KnowledgeNode(
                    entity_id=fact['id'],
                    entity_type=fact['fact_type'],
                    properties={
                        'fact_value': fact['fact_value'],
                        'metadata': fact['metadata']
                    },
                    relationships=[],
                    confidence=fact['confidence'],
                    source=fact['source'],
                    timestamp=fact['created_at']
                )
                nodes.append(node)
        
        return nodes
    
    async def _build_knowledge_relationships(
        self, 
        relationships: List[Dict[str, Any]]
    ) -> List[KnowledgeRelationship]:
        """Build knowledge relationships from relationship data."""
        knowledge_relationships = []
        
        for rel in relationships:
            knowledge_rel = KnowledgeRelationship(
                source_entity=rel['source_entity_id'],
                target_entity=rel['target_entity_id'],
                relationship_type=rel['relationship_type'],
                properties=rel['properties'],
                confidence=rel['confidence'],
                timestamp=rel['created_at']
            )
            knowledge_relationships.append(knowledge_rel)
        
        return knowledge_relationships
    
    async def _categorize_structured_facts(
        self, 
        facts: List[Dict[str, Any]], 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Categorize facts into structured knowledge categories."""
        structured_facts = {
            'personal_info': {},
            'relationships': {},
            'preferences': {},
            'experiences': {},
            'goals': {}
        }
        
        for fact in facts:
            fact_type = fact['fact_type']
            fact_value = fact['fact_value']
            confidence = fact['confidence']
            
            # Categorize based on fact type
            category = self._determine_fact_category(fact_type)
            if category and confidence >= 0.5:
                if category not in structured_facts[category]:
                    structured_facts[category][fact_type] = []
                
                structured_facts[category][fact_type].append({
                    'value': fact_value,
                    'confidence': confidence,
                    'source': fact['source'],
                    'metadata': fact['metadata']
                })
        
        # Filter empty categories
        structured_facts = {k: v for k, v in structured_facts.items() if v}
        
        return structured_facts
    
    def _determine_fact_category(self, fact_type: str) -> str:
        """Determine which category a fact type belongs to."""
        fact_type_lower = fact_type.lower()
        
        for category, patterns in self.fact_patterns.items():
            for pattern in patterns:
                if pattern in fact_type_lower:
                    return category
        
        # Default category for unmatched fact types
        return 'personal_info'
    
    async def _generate_knowledge_summary(
        self,
        nodes: List[KnowledgeNode],
        relationships: List[KnowledgeRelationship],
        structured_facts: Dict[str, Any]
    ) -> str:
        """Generate a natural language summary of the knowledge graph."""
        if not nodes and not relationships:
            return "No significant knowledge graph data available."
        
        summary_parts = []
        
        # Summarize nodes by type
        node_types = {}
        for node in nodes:
            if node.entity_type not in node_types:
                node_types[node.entity_type] = 0
            node_types[node.entity_type] += 1
        
        if node_types:
            type_summary = ", ".join([f"{count} {type_name}" for type_name, count in node_types.items()])
            summary_parts.append(f"Knowledge entities: {type_summary}")
        
        # Summarize structured facts
        if structured_facts:
            fact_categories = list(structured_facts.keys())
            summary_parts.append(f"Fact categories: {', '.join(fact_categories)}")
        
        # Summarize relationships
        if relationships:
            rel_types = {}
            for rel in relationships:
                if rel.relationship_type not in rel_types:
                    rel_types[rel.relationship_type] = 0
                rel_types[rel.relationship_type] += 1
            
            if rel_types:
                rel_summary = ", ".join([f"{count} {rel_type}" for rel_type, count in rel_types.items()])
                summary_parts.append(f"Relationships: {rel_summary}")
        
        return "; ".join(summary_parts) if summary_parts else "Knowledge graph extracted successfully."
    
    async def _calculate_confidence_score(
        self,
        nodes: List[KnowledgeNode],
        relationships: List[KnowledgeRelationship]
    ) -> float:
        """Calculate overall confidence score for the knowledge graph."""
        if not nodes and not relationships:
            return 0.0
        
        total_confidence = 0.0
        total_items = 0
        
        # Include node confidences
        for node in nodes:
            total_confidence += node.confidence
            total_items += 1
        
        # Include relationship confidences
        for rel in relationships:
            total_confidence += rel.confidence
            total_items += 1
        
        return total_confidence / total_items if total_items > 0 else 0.0
    
    def _empty_knowledge_result(self) -> GraphKnowledgeResult:
        """Return empty knowledge result for fallback."""
        return GraphKnowledgeResult(
            nodes=[],
            relationships=[],
            structured_facts={},
            knowledge_summary="No knowledge graph data available",
            confidence_score=0.0,
            extraction_metadata={
                'extraction_time': datetime.now().isoformat(),
                'status': 'empty_fallback'
            }
        )

# Factory function for easy integration
def create_character_graph_knowledge_intelligence(postgres_pool=None):
    """Create a CharacterGraphKnowledgeIntelligence instance."""
    return CharacterGraphKnowledgeIntelligence(postgres_pool=postgres_pool)