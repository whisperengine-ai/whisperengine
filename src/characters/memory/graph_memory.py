"""
Character Graph Memory System

This module extends the character memory system with graph database integration
for connected memories, relationship mapping, and complex memory associations.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
import uuid

from src.characters.memory.self_memory import (
    CharacterSelfMemoryManager, 
    PersonalMemory, 
    MemoryType, 
    EmotionalWeight
)
from src.graph_database.neo4j_connector import Neo4jConnector, get_neo4j_connector
from src.graph_database.models import BaseNode

logger = logging.getLogger(__name__)


class CharacterNode(BaseNode):
    """Character node representation in graph database"""
    
    def __init__(self, character_id: str, name: str, occupation: str = "", age: int = 0):
        super().__init__()
        self.character_id = character_id
        self.name = name
        self.occupation = occupation
        self.age = age
        self.memory_count = 0
        self.development_level = "basic"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "character_id": self.character_id,
            "name": self.name,
            "occupation": self.occupation,
            "age": self.age,
            "memory_count": self.memory_count,
            "development_level": self.development_level
        })
        return data


class MemoryNode(BaseNode):
    """Character memory node in graph database"""
    
    def __init__(self, memory_id: str, character_id: str, content: str, 
                 memory_type: str, emotional_weight: float, themes: List[str]):
        super().__init__()
        self.memory_id = memory_id
        self.character_id = character_id
        self.content = content[:500]  # Truncate for graph storage
        self.memory_type = memory_type
        self.emotional_weight = emotional_weight
        self.themes = themes
        self.recall_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "memory_id": self.memory_id,
            "character_id": self.character_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "emotional_weight": self.emotional_weight,
            "themes": self.themes,
            "recall_count": self.recall_count
        })
        return data


class ThemeNode(BaseNode):
    """Memory theme/concept node"""
    
    def __init__(self, theme: str, category: str = "general"):
        super().__init__()
        self.theme = theme
        self.category = category
        self.memory_count = 0
        self.characters_connected = 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "theme": self.theme,
            "category": self.category,
            "memory_count": self.memory_count,
            "characters_connected": self.characters_connected
        })
        return data


class MemoryRelationshipType:
    """Types of relationships between memories"""
    SIMILAR_THEME = "SIMILAR_THEME"
    TEMPORAL_SEQUENCE = "TEMPORAL_SEQUENCE"
    EMOTIONAL_ASSOCIATION = "EMOTIONAL_ASSOCIATION"
    CAUSAL_RELATIONSHIP = "CAUSAL_RELATIONSHIP"
    PERSON_MENTIONED = "PERSON_MENTIONED"
    LOCATION_SHARED = "LOCATION_SHARED"
    TRIGGERED_BY = "TRIGGERED_BY"
    CONTRADICTS = "CONTRADICTS"
    REINFORCES = "REINFORCES"


class CharacterGraphMemoryManager:
    """
    Graph-enhanced character memory manager that uses Neo4j for connected memories.
    
    This extends the basic character memory system with:
    - Memory relationship mapping
    - Theme-based memory networks
    - Character memory interconnections
    - Cross-character memory associations
    """
    
    def __init__(self, character_id: str, base_memory_manager: CharacterSelfMemoryManager):
        self.character_id = character_id
        self.base_memory_manager = base_memory_manager
        self.logger = logging.getLogger(__name__)
        
        # Graph database connection
        self._neo4j_connector: Optional[Neo4jConnector] = None
        self._graph_enabled = True
        
        # Memory association settings
        self.similarity_threshold = 0.7
        self.max_associations_per_memory = 10
        self.auto_association_enabled = True
        
    async def _get_graph_connector(self) -> Optional[Neo4jConnector]:
        """Get Neo4j connector with graceful fallback"""
        if not self._graph_enabled:
            return None
        
        try:
            if self._neo4j_connector is None:
                self._neo4j_connector = await get_neo4j_connector()
            return self._neo4j_connector
        except Exception as e:
            self.logger.warning("Neo4j connection failed, using basic memory only: %s", e)
            self._graph_enabled = False
            return None
    
    async def initialize_character_in_graph(self, character_name: str, 
                                          occupation: str = "", age: int = 0) -> bool:
        """Initialize character node in graph database"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return False
            
            # Create character node
            character_node = CharacterNode(self.character_id, character_name, occupation, age)
            
            query = """
                MERGE (c:Character {character_id: $character_id})
                SET c += $properties
                RETURN c
            """
            
            await connector.execute_query(
                query, 
                {
                    "character_id": self.character_id,
                    **character_node.to_dict()
                }
            )
            
            self.logger.info("Initialized character %s in graph database", character_name)
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize character in graph: %s", e)
            return False
    
    async def store_memory_with_graph(self, memory: PersonalMemory) -> bool:
        """Store memory in both SQLite and graph database with relationships"""
        try:
            # Store in base memory system first
            stored = self.base_memory_manager.store_memory(memory)
            if not stored:
                return False
            
            # Store in graph database
            await self._store_memory_in_graph(memory)
            
            # Create memory associations if enabled
            if self.auto_association_enabled:
                await self._create_memory_associations(memory)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to store memory with graph: %s", e)
            return False
    
    async def _store_memory_in_graph(self, memory: PersonalMemory) -> bool:
        """Store memory as a node in the graph database"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return False
            
            # Create memory node
            memory_node = MemoryNode(
                memory.memory_id,
                memory.character_id,
                memory.content,
                memory.memory_type.value,
                memory.emotional_weight,
                memory.themes
            )
            
            # Store memory node
            memory_query = """
                MERGE (m:Memory {memory_id: $memory_id})
                SET m += $properties
                RETURN m
            """
            
            await connector.execute_query(
                memory_query,
                {
                    "memory_id": memory.memory_id,
                    **memory_node.to_dict()
                }
            )
            
            # Connect memory to character
            character_relation_query = """
                MATCH (c:Character {character_id: $character_id})
                MATCH (m:Memory {memory_id: $memory_id})
                MERGE (c)-[r:HAS_MEMORY]->(m)
                SET r.created_at = datetime()
                RETURN r
            """
            
            await connector.execute_query(
                character_relation_query,
                {
                    "character_id": self.character_id,
                    "memory_id": memory.memory_id
                }
            )
            
            # Create theme nodes and relationships
            await self._create_theme_relationships(memory)
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to store memory in graph: %s", e)
            return False
    
    async def _create_theme_relationships(self, memory: PersonalMemory):
        """Create theme nodes and connect them to memory"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return
            
            for theme in memory.themes:
                # Create/update theme node
                theme_query = """
                    MERGE (t:Theme {theme: $theme})
                    ON CREATE SET t.id = $theme_id, t.created_at = datetime(), 
                                 t.memory_count = 1, t.characters_connected = 1
                    ON MATCH SET t.memory_count = t.memory_count + 1
                    RETURN t
                """
                
                await connector.execute_query(
                    theme_query,
                    {
                        "theme": theme,
                        "theme_id": str(uuid.uuid4())
                    }
                )
                
                # Connect memory to theme
                memory_theme_query = """
                    MATCH (m:Memory {memory_id: $memory_id})
                    MATCH (t:Theme {theme: $theme})
                    MERGE (m)-[r:HAS_THEME]->(t)
                    SET r.created_at = datetime()
                    RETURN r
                """
                
                await connector.execute_query(
                    memory_theme_query,
                    {
                        "memory_id": memory.memory_id,
                        "theme": theme
                    }
                )
                
        except Exception as e:
            self.logger.error("Failed to create theme relationships: %s", e)
    
    async def _create_memory_associations(self, new_memory: PersonalMemory):
        """Create associations between the new memory and existing memories"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return
            
            # Find memories with similar themes
            similar_memories = await self._find_similar_memories(new_memory)
            
            for similar_memory, similarity_score in similar_memories:
                if similarity_score >= self.similarity_threshold:
                    await self._create_memory_relationship(
                        new_memory.memory_id,
                        similar_memory.memory_id,
                        MemoryRelationshipType.SIMILAR_THEME,
                        {"similarity_score": similarity_score}
                    )
            
            # Create temporal relationships (if memories are sequential)
            await self._create_temporal_relationships(new_memory)
            
            # Create emotional associations
            await self._create_emotional_associations(new_memory)
            
        except Exception as e:
            self.logger.error("Failed to create memory associations: %s", e)
    
    async def _find_similar_memories(self, memory: PersonalMemory) -> List[Tuple[PersonalMemory, float]]:
        """Find memories with similar themes and content"""
        try:
            # Get memories with overlapping themes
            overlapping_memories = []
            
            for theme in memory.themes:
                theme_memories = self.base_memory_manager.recall_memories(
                    themes=[theme],
                    limit=20,
                    boost_recall=False
                )
                overlapping_memories.extend(theme_memories)
            
            # Calculate similarity scores
            similar_memories = []
            for other_memory in overlapping_memories:
                if other_memory.memory_id != memory.memory_id:
                    similarity = self._calculate_memory_similarity(memory, other_memory)
                    if similarity > 0.3:  # Minimum threshold
                        similar_memories.append((other_memory, similarity))
            
            # Sort by similarity and return top matches
            similar_memories.sort(key=lambda x: x[1], reverse=True)
            return similar_memories[:self.max_associations_per_memory]
            
        except Exception as e:
            self.logger.error("Failed to find similar memories: %s", e)
            return []
    
    def _calculate_memory_similarity(self, memory1: PersonalMemory, memory2: PersonalMemory) -> float:
        """Calculate similarity score between two memories"""
        try:
            # Theme overlap
            theme_overlap = len(set(memory1.themes) & set(memory2.themes))
            max_themes = max(len(memory1.themes), len(memory2.themes))
            theme_similarity = theme_overlap / max_themes if max_themes > 0 else 0
            
            # Emotional weight similarity
            weight_diff = abs(memory1.emotional_weight - memory2.emotional_weight)
            weight_similarity = 1.0 - weight_diff
            
            # Memory type similarity
            type_similarity = 1.0 if memory1.memory_type == memory2.memory_type else 0.3
            
            # Time proximity (recent memories are more similar)
            time_diff = abs((memory1.created_date - memory2.created_date).total_seconds())
            time_similarity = max(0, 1.0 - (time_diff / (30 * 24 * 3600)))  # 30 days max
            
            # Location similarity
            location_similarity = 0.0
            if memory1.location and memory2.location:
                location_similarity = 1.0 if memory1.location == memory2.location else 0.5
            
            # People similarity
            people_overlap = len(set(memory1.related_people) & set(memory2.related_people))
            max_people = max(len(memory1.related_people), len(memory2.related_people))
            people_similarity = people_overlap / max_people if max_people > 0 else 0
            
            # Weighted average
            similarity = (
                theme_similarity * 0.35 +
                weight_similarity * 0.25 +
                type_similarity * 0.15 +
                time_similarity * 0.10 +
                location_similarity * 0.10 +
                people_similarity * 0.05
            )
            
            return min(1.0, similarity)
            
        except Exception as e:
            self.logger.error("Failed to calculate memory similarity: %s", e)
            return 0.0
    
    async def _create_memory_relationship(self, memory1_id: str, memory2_id: str,
                                        relationship_type: str, properties: Optional[Dict[str, Any]] = None):
        """Create a relationship between two memories in the graph"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return
            
            properties = properties or {}
            properties['created_at'] = datetime.now().isoformat()
            properties['type'] = relationship_type
            
            query = f"""
                MATCH (m1:Memory {{memory_id: $memory1_id}})
                MATCH (m2:Memory {{memory_id: $memory2_id}})
                MERGE (m1)-[r:{relationship_type}]->(m2)
                SET r += $properties
                RETURN r
            """
            
            await connector.execute_query(
                query,
                {
                    "memory1_id": memory1_id,
                    "memory2_id": memory2_id,
                    **properties
                }
            )
            
        except Exception as e:
            self.logger.error("Failed to create memory relationship: %s", e)
    
    async def _create_temporal_relationships(self, new_memory: PersonalMemory):
        """Create temporal sequence relationships between memories"""
        try:
            # Find recent memories from the same character
            recent_memories = self.base_memory_manager.get_recent_memories(days=7, limit=5)
            
            for recent_memory in recent_memories:
                if recent_memory.memory_id != new_memory.memory_id:
                    # Check if memories are temporally related
                    time_diff = abs((new_memory.created_date - recent_memory.created_date).total_seconds())
                    
                    # If memories are within 24 hours and have related themes
                    if time_diff < 24 * 3600:
                        theme_overlap = set(new_memory.themes) & set(recent_memory.themes)
                        if theme_overlap:
                            await self._create_memory_relationship(
                                recent_memory.memory_id,
                                new_memory.memory_id,
                                MemoryRelationshipType.TEMPORAL_SEQUENCE,
                                {"hours_apart": time_diff / 3600, "shared_themes": list(theme_overlap)}
                            )
            
        except Exception as e:
            self.logger.error("Failed to create temporal relationships: %s", e)
    
    async def _create_emotional_associations(self, new_memory: PersonalMemory):
        """Create emotional associations between memories"""
        try:
            # Find memories with similar emotional weight
            weight_range = 0.2  # ±0.2 emotional weight
            min_weight = max(0.0, new_memory.emotional_weight - weight_range)
            max_weight = min(1.0, new_memory.emotional_weight + weight_range)
            
            similar_emotional_memories = self.base_memory_manager.recall_memories(
                min_emotional_weight=min_weight,
                limit=10,
                boost_recall=False
            )
            
            for emotional_memory in similar_emotional_memories:
                if (emotional_memory.memory_id != new_memory.memory_id and
                    abs(emotional_memory.emotional_weight - new_memory.emotional_weight) <= weight_range):
                    
                    await self._create_memory_relationship(
                        new_memory.memory_id,
                        emotional_memory.memory_id,
                        MemoryRelationshipType.EMOTIONAL_ASSOCIATION,
                        {
                            "emotional_similarity": 1.0 - abs(new_memory.emotional_weight - emotional_memory.emotional_weight),
                            "new_weight": new_memory.emotional_weight,
                            "other_weight": emotional_memory.emotional_weight
                        }
                    )
            
        except Exception as e:
            self.logger.error("Failed to create emotional associations: %s", e)
    
    async def get_connected_memories(self, memory_id: str, 
                                   relationship_types: Optional[List[str]] = None,
                                   max_depth: int = 2,
                                   limit: int = 20) -> List[Dict[str, Any]]:
        """Get memories connected to a specific memory through graph relationships"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return []
            
            relationship_types = relationship_types or [
                MemoryRelationshipType.SIMILAR_THEME,
                MemoryRelationshipType.EMOTIONAL_ASSOCIATION,
                MemoryRelationshipType.TEMPORAL_SEQUENCE
            ]
            
            # Build relationship type filter
            rel_filter = "|".join(relationship_types)
            
            query = f"""
                MATCH (start:Memory {{memory_id: $memory_id}})
                MATCH path = (start)-[r:{rel_filter}*1..{max_depth}]-(connected:Memory)
                WHERE connected.character_id = $character_id
                RETURN connected, r, length(path) as depth
                ORDER BY depth ASC, connected.emotional_weight DESC
                LIMIT {limit}
            """
            
            result = await connector.execute_query(
                query,
                {
                    "memory_id": memory_id,
                    "character_id": self.character_id
                }
            )
            
            connected_memories = []
            for record in result:
                memory_data = record.get('connected', {})
                relationships = record.get('r', [])
                depth = record.get('depth', 0)
                
                connected_memories.append({
                    'memory': memory_data,
                    'relationships': relationships,
                    'connection_depth': depth
                })
            
            return connected_memories
            
        except Exception as e:
            self.logger.error("Failed to get connected memories: %s", e)
            return []
    
    async def get_memory_network_analysis(self) -> Dict[str, Any]:
        """Get network analysis of character's memory connections"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return {}
            
            # Get memory network statistics
            stats_query = """
                MATCH (c:Character {character_id: $character_id})-[:HAS_MEMORY]->(m:Memory)
                OPTIONAL MATCH (m)-[r]-(connected:Memory)
                WHERE connected.character_id = $character_id
                RETURN 
                    count(DISTINCT m) as total_memories,
                    count(DISTINCT r) as total_connections,
                    count(DISTINCT connected) as connected_memories,
                    avg(m.emotional_weight) as avg_emotional_weight
            """
            
            result = await connector.execute_query(
                stats_query,
                {"character_id": self.character_id}
            )
            
            if result:
                record = result[0]
                
                # Get theme network
                theme_query = """
                    MATCH (c:Character {character_id: $character_id})-[:HAS_MEMORY]->(m:Memory)-[:HAS_THEME]->(t:Theme)
                    RETURN t.theme as theme, count(m) as memory_count
                    ORDER BY memory_count DESC
                    LIMIT 10
                """
                
                theme_result = await connector.execute_query(
                    theme_query,
                    {"character_id": self.character_id}
                )
                
                themes = [{"theme": r["theme"], "count": r["memory_count"]} for r in theme_result]
                
                return {
                    "total_memories": record.get("total_memories", 0),
                    "total_connections": record.get("total_connections", 0),
                    "connected_memories": record.get("connected_memories", 0),
                    "connection_density": record.get("total_connections", 0) / max(1, record.get("total_memories", 1)),
                    "average_emotional_weight": record.get("avg_emotional_weight", 0.0),
                    "top_themes": themes,
                    "network_complexity": self._calculate_network_complexity(record)
                }
            
            return {}
            
        except Exception as e:
            self.logger.error("Failed to get memory network analysis: %s", e)
            return {}
    
    def _calculate_network_complexity(self, stats: Dict[str, Any]) -> str:
        """Calculate network complexity level based on connections"""
        total_memories = stats.get("total_memories", 0)
        total_connections = stats.get("total_connections", 0)
        
        if total_memories == 0:
            return "none"
        
        connection_ratio = total_connections / total_memories
        
        if connection_ratio >= 3.0:
            return "highly_complex"
        elif connection_ratio >= 2.0:
            return "complex"
        elif connection_ratio >= 1.0:
            return "moderate"
        elif connection_ratio >= 0.5:
            return "simple"
        else:
            return "sparse"
    
    async def find_memory_paths(self, start_memory_id: str, end_memory_id: str,
                              max_hops: int = 4) -> List[List[Dict[str, Any]]]:
        """Find paths between two memories through the graph"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return []
            
            query = f"""
                MATCH (start:Memory {{memory_id: $start_id}})
                MATCH (end:Memory {{memory_id: $end_id}})
                MATCH path = shortestPath((start)-[*1..{max_hops}]-(end))
                WHERE all(node in nodes(path) WHERE node.character_id = $character_id)
                RETURN path
                LIMIT 5
            """
            
            result = await connector.execute_query(
                query,
                {
                    "start_id": start_memory_id,
                    "end_id": end_memory_id,
                    "character_id": self.character_id
                }
            )
            
            paths = []
            for record in result:
                path_data = record.get('path', [])
                # Process path data to extract nodes and relationships
                processed_path = self._process_path_data(path_data)
                paths.append(processed_path)
            
            return paths
            
        except Exception as e:
            self.logger.error("Failed to find memory paths: %s", e)
            return []
    
    def _process_path_data(self, path_data: Any) -> List[Dict[str, Any]]:
        """Process Neo4j path data into a structured format"""
        # This would process the actual Neo4j path object
        # For now, return a placeholder structure
        return [{"type": "memory", "id": "placeholder", "content": "Path processing"}]


class CharacterMemoryNetworkIntegrator:
    """
    Integrates character graph memories with the main memory integration system.
    
    This provides enhanced memory recall using graph relationships and
    network analysis for more sophisticated character behavior.
    """
    
    def __init__(self, character_id: str, base_integrator):
        self.character_id = character_id
        self.base_integrator = base_integrator
        self.graph_memory_manager: Optional[CharacterGraphMemoryManager] = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize_graph_integration(self, character_name: str, 
                                         occupation: str = "", age: int = 0):
        """Initialize graph memory integration"""
        try:
            self.graph_memory_manager = CharacterGraphMemoryManager(
                self.character_id,
                self.base_integrator.self_memory
            )
            
            # Initialize character in graph
            await self.graph_memory_manager.initialize_character_in_graph(
                character_name, occupation, age
            )
            
            self.logger.info("Initialized graph memory integration for %s", character_name)
            
        except Exception as e:
            self.logger.error("Failed to initialize graph integration: %s", e)
    
    async def get_enhanced_memories_for_conversation(self, 
                                                   themes: List[str],
                                                   context_memory_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get memories enhanced with graph relationships"""
        try:
            if not self.graph_memory_manager:
                # Fallback to basic memory recall
                basic_memories = await self.base_integrator.get_relevant_memories_for_conversation(themes)
                return [{"memory": mem, "connections": [], "network_depth": 0} for mem in basic_memories]
            
            # Get basic relevant memories
            relevant_memories = await self.base_integrator.get_relevant_memories_for_conversation(themes)
            
            enhanced_memories = []
            for memory in relevant_memories:
                # Get connected memories for each relevant memory
                connected = await self.graph_memory_manager.get_connected_memories(
                    memory.memory_id,
                    limit=5,
                    max_depth=2
                )
                
                enhanced_memories.append({
                    "memory": memory,
                    "connections": connected,
                    "network_depth": len(connected)
                })
            
            # If we have a context memory, find paths to relevant memories
            if context_memory_id:
                for enhanced_memory in enhanced_memories:
                    paths = await self.graph_memory_manager.find_memory_paths(
                        context_memory_id,
                        enhanced_memory["memory"].memory_id
                    )
                    enhanced_memory["connection_paths"] = paths
            
            return enhanced_memories
            
        except Exception as e:
            self.logger.error("Failed to get enhanced memories: %s", e)
            return []
    
    async def create_memory_with_graph(self, 
                                     conversation_content: str,
                                     user_message: str,
                                     character_response: str,
                                     emotional_context: Optional[Dict] = None) -> Optional[PersonalMemory]:
        """Create memory with graph relationship building"""
        try:
            # Create memory using base integrator
            memory = await self.base_integrator.create_conversation_memory(
                conversation_content, user_message, character_response, emotional_context
            )
            
            if memory and self.graph_memory_manager:
                # Store in graph with relationships
                await self.graph_memory_manager.store_memory_with_graph(memory)
            
            return memory
            
        except Exception as e:
            self.logger.error("Failed to create memory with graph: %s", e)
            return None
    
    async def get_memory_network_insights(self) -> Dict[str, Any]:
        """Get insights about the character's memory network"""
        try:
            if not self.graph_memory_manager:
                return {"graph_enabled": False}
            
            network_analysis = await self.graph_memory_manager.get_memory_network_analysis()
            
            # Add interpretation of the network
            insights = {
                "graph_enabled": True,
                "network_analysis": network_analysis,
                "insights": self._interpret_network_analysis(network_analysis)
            }
            
            return insights
            
        except Exception as e:
            self.logger.error("Failed to get memory network insights: %s", e)
            return {"graph_enabled": False, "error": str(e)}
    
    def _interpret_network_analysis(self, analysis: Dict[str, Any]) -> List[str]:
        """Interpret network analysis into human-readable insights"""
        insights = []
        
        complexity = analysis.get("network_complexity", "none")
        total_memories = analysis.get("total_memories", 0)
        connection_density = analysis.get("connection_density", 0.0)
        
        if complexity == "highly_complex":
            insights.append("Character has a highly interconnected memory network with rich associations")
        elif complexity == "complex":
            insights.append("Character shows good memory integration with meaningful connections")
        elif complexity == "moderate":
            insights.append("Character is developing connected memories and associations")
        elif complexity == "simple":
            insights.append("Character has basic memory connections")
        else:
            insights.append("Character memories are mostly isolated with few connections")
        
        if total_memories > 50:
            insights.append("Character has extensive life experiences and memories")
        elif total_memories > 20:
            insights.append("Character has a good foundation of memories")
        elif total_memories > 5:
            insights.append("Character is building their memory base")
        
        top_themes = analysis.get("top_themes", [])
        if top_themes:
            dominant_theme = top_themes[0]["theme"]
            insights.append(f"Character's memories are strongly focused on '{dominant_theme}'")
        
        return insights


# Integration with existing character memory system
def enhance_character_with_graph_memory(character_integrator) -> CharacterMemoryNetworkIntegrator:
    """
    Enhance an existing character memory integrator with graph capabilities.
    
    Args:
        character_integrator: Existing CharacterMemoryIntegrator instance
        
    Returns:
        Enhanced integrator with graph memory capabilities
    """
    return CharacterMemoryNetworkIntegrator(
        character_integrator.character_id,
        character_integrator
    )