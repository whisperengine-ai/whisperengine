"""
Multi-Entity Relationship Manager

This module provides comprehensive management of relationships between
Users, Characters, and AI Self entities in the graph database.
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid

from src.graph_database.neo4j_connector import Neo4jConnector, get_neo4j_connector
from src.graph_database.multi_entity_models import (
    EnhancedUserNode, EnhancedCharacterNode, AISelfNode,
    EntityRelationship, InteractionEvent, EntityType, RelationshipType,
    TrustLevel, FamiliarityLevel, RELATIONSHIP_PATTERNS
)

logger = logging.getLogger(__name__)


def _serialize_for_neo4j(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize complex data types for Neo4j storage.
    Neo4j can only store primitive types (str, int, float, bool) and arrays thereof.
    Complex objects like dicts need to be serialized to JSON strings.
    """
    serialized = {}
    for key, value in data.items():
        if isinstance(value, dict):
            # Serialize dict to JSON string (even empty dicts)
            serialized[key] = json.dumps(value)
        elif isinstance(value, datetime):
            # Convert datetime to ISO string
            serialized[key] = value.isoformat() if value else None
        elif isinstance(value, list):
            # Check if list contains complex objects
            if value and isinstance(value[0], dict):
                # Serialize list of dicts to JSON string
                serialized[key] = json.dumps(value)
            else:
                # Keep simple lists as is
                serialized[key] = value
        else:
            # Keep primitive types as is
            serialized[key] = value
    return serialized


class MultiEntityRelationshipManager:
    """
    Manages relationships between Users, Characters, and AI Self entities.
    
    This system enables:
    - User-Character associations (creation, favorites, trust)
    - Character-Character relationships (knowledge, similarity)
    - AI Self management of all entities
    - Dynamic relationship evolution through interactions
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._neo4j_connector: Optional[Neo4jConnector] = None
        self._graph_enabled = True
        
        # Relationship evolution settings
        self.trust_decay_rate = 0.01  # Daily trust decay without interaction
        self.familiarity_decay_rate = 0.005  # Daily familiarity decay
        self.relationship_strength_threshold = 0.3  # Minimum for active relationships
        
    async def _get_graph_connector(self) -> Optional[Neo4jConnector]:
        """Get Neo4j connector with graceful fallback"""
        if not self._graph_enabled:
            return None
        
        try:
            if self._neo4j_connector is None:
                self._neo4j_connector = await get_neo4j_connector()
            return self._neo4j_connector
        except Exception as e:
            self.logger.warning("Neo4j connection failed, relationships disabled: %s", e)
            self._graph_enabled = False
            return None
    
    async def initialize_schema(self) -> bool:
        """Initialize multi-entity relationship schema in Neo4j"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return False
            
            # Create constraints and indexes for multi-entity system
            schema_queries = [
                # Enhanced User constraints
                "CREATE CONSTRAINT enhanced_user_id_unique IF NOT EXISTS FOR (u:EnhancedUser) REQUIRE u.id IS UNIQUE",
                "CREATE INDEX enhanced_user_discord_id IF NOT EXISTS FOR (u:EnhancedUser) ON (u.discord_id)",
                "CREATE INDEX enhanced_user_username IF NOT EXISTS FOR (u:EnhancedUser) ON (u.username)",
                
                # Enhanced Character constraints
                "CREATE CONSTRAINT enhanced_character_id_unique IF NOT EXISTS FOR (c:EnhancedCharacter) REQUIRE c.id IS UNIQUE",
                "CREATE INDEX enhanced_character_character_id IF NOT EXISTS FOR (c:EnhancedCharacter) ON (c.character_id)",
                "CREATE INDEX enhanced_character_name IF NOT EXISTS FOR (c:EnhancedCharacter) ON (c.name)",
                "CREATE INDEX enhanced_character_creator IF NOT EXISTS FOR (c:EnhancedCharacter) ON (c.creator_user_id)",
                
                # AI Self constraints
                "CREATE CONSTRAINT ai_self_id_unique IF NOT EXISTS FOR (ai:AISelf) REQUIRE ai.id IS UNIQUE",
                "CREATE INDEX ai_self_persona_name IF NOT EXISTS FOR (ai:AISelf) ON (ai.persona_name)",
                
                # Relationship indexes
                "CREATE INDEX relationship_trust_level IF NOT EXISTS FOR ()-[r:RELATIONSHIP]-() ON (r.trust_level)",
                "CREATE INDEX relationship_type IF NOT EXISTS FOR ()-[r:RELATIONSHIP]-() ON (r.relationship_type)",
                "CREATE INDEX relationship_last_interaction IF NOT EXISTS FOR ()-[r:RELATIONSHIP]-() ON (r.last_interaction)",
                
                # Interaction indexes
                "CREATE INDEX interaction_timestamp IF NOT EXISTS FOR ()-[r:INTERACTION]-() ON (r.timestamp)",
                "CREATE INDEX interaction_type IF NOT EXISTS FOR ()-[r:INTERACTION]-() ON (r.interaction_type)",
            ]
            
            for query in schema_queries:
                try:
                    await connector.execute_query(query)
                    self.logger.debug("Executed schema query: %s", query[:50])
                except Exception as e:
                    self.logger.warning("Schema query failed (may already exist): %s - %s", query[:50], e)
            
            self.logger.info("Multi-entity relationship schema initialized")
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize multi-entity schema: %s", e)
            return False
    
    async def create_user_entity(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create or update user entity in graph database"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return None
            
            user_node = EnhancedUserNode(
                discord_id=user_data.get('discord_id', ''),
                username=user_data.get('username', ''),
                display_name=user_data.get('display_name', ''),
                personality_traits=user_data.get('personality_traits', []),
                communication_style=user_data.get('communication_style', 'neutral'),
                user_preferences=user_data.get('preferences', {}),
                privacy_level=user_data.get('privacy_level', 'standard')
            )
            
            query = """
                MERGE (u:EnhancedUser {discord_id: $discord_id})
                SET u += $properties
                RETURN u.id as user_id
            """
            
            # Prepare properties dict for the $properties parameter
            user_properties = _serialize_for_neo4j(user_node.to_dict())
            
            # Debug logging
            self.logger.debug(f"Original user_node.to_dict(): {user_node.to_dict()}")
            self.logger.debug(f"Serialized user_properties: {user_properties}")
            
            result = await connector.execute_query(
                query,
                {
                    "discord_id": user_data.get('discord_id', ''),
                    "properties": user_properties
                }
            )
            
            if result:
                user_id = result[0]['user_id']
                self.logger.info("Created/updated user entity: %s", user_id)
                return user_id
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to create user entity: %s", e)
            return None
    
    async def get_user_entity_id_by_discord_id(self, discord_id: str) -> Optional[str]:
        """Get the internal user entity ID from Discord ID"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return None
            
            query = """
                MATCH (u:EnhancedUser {discord_id: $discord_id})
                RETURN u.id as user_id
            """
            
            result = await connector.execute_query(query, {"discord_id": discord_id})
            
            if result and len(result) > 0:
                return result[0]['user_id']
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to get user entity ID for discord_id %s: %s", discord_id, e)
            return None
    
    async def create_character_entity(self, character_data: Dict[str, Any], creator_user_id: Optional[str] = None) -> Optional[str]:
        """Create character entity in graph database"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return None
            
            character_node = EnhancedCharacterNode(
                character_id=character_data.get('character_id', str(uuid.uuid4())),
                name=character_data.get('name', ''),
                occupation=character_data.get('occupation', ''),
                age=character_data.get('age', 0),
                personality_traits=character_data.get('personality_traits', []),
                communication_style=character_data.get('communication_style', 'neutral'),
                background_summary=character_data.get('background_summary', ''),
                creator_user_id=creator_user_id,
                preferred_topics=character_data.get('preferred_topics', []),
                conversation_style=character_data.get('conversation_style', 'adaptive')
            )
            
            # Create character node
            query = """
                CREATE (c:EnhancedCharacter)
                SET c += $properties
                RETURN c.id as character_id
            """
            
            result = await connector.execute_query(
                query,
                {"properties": _serialize_for_neo4j(character_node.to_dict())}
            )
            
            if result:
                character_id = result[0]['character_id']
                
                # Create relationship with creator if specified
                if creator_user_id:
                    await self.create_relationship(
                        creator_user_id, character_id,
                        EntityType.USER, EntityType.CHARACTER,
                        RelationshipType.CREATED_BY,
                        relationship_context="Character creation",
                        trust_level=0.8,
                        familiarity_level=1.0
                    )
                
                # Create relationship with AI Self
                ai_self_id = await self.get_or_create_ai_self()
                if ai_self_id:
                    await self.create_relationship(
                        ai_self_id, character_id,
                        EntityType.AI_SELF, EntityType.CHARACTER,
                        RelationshipType.MANAGES,
                        relationship_context="AI system character management",
                        trust_level=1.0,
                        familiarity_level=1.0
                    )
                
                self.logger.info("Created character entity: %s", character_id)
                return character_id
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to create character entity: %s", e)
            return None
    
    async def get_or_create_ai_self(self) -> Optional[str]:
        """Get or create the AI Self entity"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return None
            
            # Check if AI Self already exists
            query = """
                MATCH (ai:AISelf)
                RETURN ai.id as ai_id
                LIMIT 1
            """
            
            result = await connector.execute_query(query)
            
            if result:
                return result[0]['ai_id']
            
            # Create AI Self entity
            ai_self_node = AISelfNode(
                persona_name="WhisperEngine",
                system_version="1.0.0",
                capabilities=[
                    "character_management",
                    "conversation_facilitation",
                    "relationship_tracking",
                    "memory_integration",
                    "emotional_intelligence"
                ],
                management_style="collaborative",
                learning_focus=[
                    "user_preferences",
                    "character_development",
                    "relationship_dynamics"
                ]
            )
            
            create_query = """
                CREATE (ai:AISelf)
                SET ai += $properties
                RETURN ai.id as ai_id
            """
            
            result = await connector.execute_query(
                create_query,
                {"properties": _serialize_for_neo4j(ai_self_node.to_dict())}
            )
            
            if result:
                ai_id = result[0]['ai_id']
                self.logger.info("Created AI Self entity: %s", ai_id)
                return ai_id
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to get/create AI Self: %s", e)
            return None
    
    async def create_relationship(self,
                                from_entity_id: str,
                                to_entity_id: str,
                                from_entity_type: EntityType,
                                to_entity_type: EntityType,
                                relationship_type: RelationshipType,
                                relationship_context: str = "",
                                trust_level: float = 0.5,
                                familiarity_level: float = 0.0) -> bool:
        """Create a relationship between two entities"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return False
            
            relationship = EntityRelationship(
                from_entity_id=from_entity_id,
                to_entity_id=to_entity_id,
                from_entity_type=from_entity_type,
                to_entity_type=to_entity_type,
                relationship_type=relationship_type,
                trust_level=trust_level,
                familiarity_level=familiarity_level,
                relationship_context=relationship_context
            )
            
            # Calculate initial relationship strength
            relationship.relationship_strength = (trust_level + familiarity_level) / 2
            
            # Get node labels based on entity types
            from_label = self._get_node_label(from_entity_type)
            to_label = self._get_node_label(to_entity_type)
            
            query = f"""
                MATCH (from:{from_label} {{id: $from_id}})
                MATCH (to:{to_label} {{id: $to_id}})
                MERGE (from)-[r:RELATIONSHIP {{relationship_type: $rel_type}}]->(to)
                SET r += $properties
                RETURN r
            """
            
            await connector.execute_query(
                query,
                {
                    "from_id": from_entity_id,
                    "to_id": to_entity_id,
                    "rel_type": relationship_type.value,
                    "properties": _serialize_for_neo4j(relationship.to_dict())
                }
            )
            
            self.logger.info("Created relationship: %s %s %s", 
                           from_entity_type.value, relationship_type.value, to_entity_type.value)
            return True
            
        except Exception as e:
            self.logger.error("Failed to create relationship: %s", e)
            return False
    
    def _get_node_label(self, entity_type: EntityType) -> str:
        """Get Neo4j node label for entity type"""
        label_map = {
            EntityType.USER: "EnhancedUser",
            EntityType.CHARACTER: "EnhancedCharacter",
            EntityType.AI_SELF: "AISelf",
            EntityType.BOT_PERSONA: "AISelf"
        }
        return label_map.get(entity_type, "BaseNode")
    
    async def record_interaction(self,
                               from_entity_id: str,
                               to_entity_id: str,
                               interaction_type: str,
                               content_summary: str,
                               emotional_tone: str = "neutral",
                               sentiment_score: float = 0.0,
                               duration_minutes: float = 0.0) -> bool:
        """Record an interaction between two entities"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return False
            
            interaction = InteractionEvent(
                from_entity_id=from_entity_id,
                to_entity_id=to_entity_id,
                interaction_type=interaction_type,
                content_summary=content_summary,
                emotional_tone=emotional_tone,
                sentiment_score=sentiment_score,
                duration_minutes=duration_minutes
            )
            
            # Create interaction relationship
            query = """
                MATCH (from {id: $from_id})
                MATCH (to {id: $to_id})
                MERGE (from)-[i:INTERACTION {interaction_id: $interaction_id}]->(to)
                SET i += $properties
                RETURN i
            """
            
            await connector.execute_query(
                query,
                {
                    "from_id": from_entity_id,
                    "to_id": to_entity_id,
                    "interaction_id": interaction.interaction_id,
                    "properties": _serialize_for_neo4j(interaction.to_dict())
                }
            )
            
            # Update relationship based on interaction
            await self._update_relationship_from_interaction(interaction)
            
            self.logger.info("Recorded interaction: %s -> %s (%s)", 
                           from_entity_id[:8], to_entity_id[:8], interaction_type)
            return True
            
        except Exception as e:
            self.logger.error("Failed to record interaction: %s", e)
            return False
    
    async def _update_relationship_from_interaction(self, interaction: InteractionEvent):
        """Update relationship metrics based on interaction"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return
            
            # Calculate changes based on interaction
            trust_change = 0.0
            familiarity_change = 0.05  # Small familiarity increase from any interaction
            
            # Adjust based on sentiment
            if interaction.sentiment_score > 0.5:
                trust_change = 0.02  # Positive interaction increases trust
            elif interaction.sentiment_score < -0.5:
                trust_change = -0.05  # Negative interaction decreases trust
            
            # Adjust based on interaction quality
            if interaction.interaction_quality > 0.7:
                trust_change += 0.01
                familiarity_change += 0.02
            
            # Update relationship
            query = """
                MATCH ()-[r:RELATIONSHIP {from_entity_id: $from_id, to_entity_id: $to_id}]-()
                SET r.trust_level = CASE 
                    WHEN r.trust_level + $trust_change > 1.0 THEN 1.0
                    WHEN r.trust_level + $trust_change < 0.0 THEN 0.0
                    ELSE r.trust_level + $trust_change
                END,
                r.familiarity_level = CASE
                    WHEN r.familiarity_level + $familiarity_change > 1.0 THEN 1.0
                    ELSE r.familiarity_level + $familiarity_change
                END,
                r.last_interaction = $timestamp,
                r.interaction_count = r.interaction_count + 1,
                r.relationship_strength = (r.trust_level + r.familiarity_level) / 2
                RETURN r
            """
            
            await connector.execute_query(
                query,
                {
                    "from_id": interaction.from_entity_id,
                    "to_id": interaction.to_entity_id,
                    "trust_change": trust_change,
                    "familiarity_change": familiarity_change,
                    "timestamp": interaction.timestamp.isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error("Failed to update relationship from interaction: %s", e)
    
    async def get_entity_relationships(self, entity_id: str, relationship_types: Optional[List[RelationshipType]] = None) -> List[Dict[str, Any]]:
        """Get all relationships for an entity"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return []
            
            # Build relationship type filter
            if relationship_types:
                rel_filter = " OR ".join([f"r.relationship_type = '{rt.value}'" for rt in relationship_types])
                where_clause = f"WHERE {rel_filter}"
            else:
                where_clause = ""
            
            query = f"""
                MATCH (entity {{id: $entity_id}})
                MATCH (entity)-[r:RELATIONSHIP]-(other)
                {where_clause}
                RETURN other, r, 
                       CASE WHEN startNode(r).id = $entity_id 
                            THEN 'outgoing' 
                            ELSE 'incoming' 
                       END as direction
                ORDER BY r.relationship_strength DESC, r.last_interaction DESC
            """
            
            result = await connector.execute_query(
                query,
                {"entity_id": entity_id}
            )
            
            relationships = []
            for record in result:
                relationships.append({
                    "related_entity": record['other'],
                    "relationship": record['r'],
                    "direction": record['direction']
                })
            
            return relationships
            
        except Exception as e:
            self.logger.error("Failed to get entity relationships: %s", e)
            return []
    
    async def get_user_characters(self, discord_id: str) -> List[Dict[str, Any]]:
        """Get all characters associated with a user by Discord ID"""
        try:
            # First get the internal user entity ID from Discord ID
            user_entity_id = await self.get_user_entity_id_by_discord_id(discord_id)
            if not user_entity_id:
                self.logger.warning("No user entity found for discord_id: %s", discord_id)
                return []
            
            relationships = await self.get_entity_relationships(
                user_entity_id, 
                [RelationshipType.CREATED_BY, RelationshipType.FAVORITE_OF, RelationshipType.TRUSTED_BY]
            )
            
            characters = []
            for rel in relationships:
                try:
                    # Extract relationship data - handle both dict and other formats
                    related_entity = None
                    relationship_data = None
                    
                    if isinstance(rel, dict):
                        # Expected dictionary format from get_entity_relationships
                        related_entity = rel.get('related_entity')
                        relationship_data = rel.get('relationship')
                    elif isinstance(rel, (tuple, list)) and len(rel) >= 2:
                        # Fallback for tuple format (other, r, direction)
                        related_entity = rel[0]
                        relationship_data = rel[1]
                    else:
                        self.logger.warning("Unexpected relationship format: %s", rel)
                        continue
                    
                    if not relationship_data:
                        continue
                        
                    # Extract to_entity_type - handle Neo4j relationship object or dict
                    to_entity_type = None
                    relationship_type = None
                    
                    # Check if relationship_data is a tuple (Neo4j relationship format)
                    if isinstance(relationship_data, tuple) and len(relationship_data) >= 3:
                        # Neo4j relationship tuple format: (properties, type, all_properties)
                        # The actual properties are in index 2
                        relationship_properties = relationship_data[2]
                        
                        if isinstance(relationship_properties, dict):
                            to_entity_type = relationship_properties.get('to_entity_type')
                            relationship_type = relationship_properties.get('relationship_type')
                    elif isinstance(relationship_data, dict):
                        # Direct dictionary format
                        to_entity_type = relationship_data.get('to_entity_type')
                        relationship_type = relationship_data.get('relationship_type')
                    elif hasattr(relationship_data, 'get'):
                        # Has get method (dict-like)
                        to_entity_type = relationship_data.get('to_entity_type')
                        relationship_type = relationship_data.get('relationship_type')
                    elif hasattr(relationship_data, '__getitem__'):
                        # Indexable but not dict-like (try key access)
                        try:
                            to_entity_type = relationship_data['to_entity_type']
                            relationship_type = relationship_data['relationship_type']
                        except (KeyError, TypeError) as e:
                            self.logger.debug("Could not access relationship properties: %s", e)
                    
                    # Check if this is a character relationship - check if related_entity has character properties
                    is_character_relationship = False
                    if related_entity and isinstance(related_entity, dict):
                        # Check for character-specific properties to identify character entities
                        has_character_props = any(prop in related_entity for prop in 
                                                ['character_id', 'personality_traits', 'conversation_style', 'background_summary'])
                        if has_character_props:
                            is_character_relationship = True
                    
                    # Also check the extracted to_entity_type if available
                    if to_entity_type == 'character':
                        is_character_relationship = True
                    
                    # Check if this is a character relationship
                    if is_character_relationship:
                        characters.append({
                            "character": related_entity,
                            "relationship": relationship_data,
                            "relationship_type": relationship_type or 'unknown'
                        })
                    
                except Exception as inner_e:
                    self.logger.error("Error processing relationship %s: %s", rel, inner_e, exc_info=True)

            self.logger.info("Found %d characters for user %s", len(characters), discord_id)
            return characters
            
        except Exception as e:
            self.logger.error("Failed to get user characters for discord_id %s: %s", discord_id, e)
            return []
    
    async def get_character_network(self, character_id: str) -> Dict[str, Any]:
        """Get the full network of relationships for a character"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return {}
            
            # Get character info
            char_query = """
                MATCH (c:EnhancedCharacter {id: $character_id})
                RETURN c
            """
            
            char_result = await connector.execute_query(
                char_query,
                {"character_id": character_id}
            )
            
            if not char_result:
                return {}
            
            character = char_result[0]['c']
            
            # Get all relationships
            relationships = await self.get_entity_relationships(character_id)
            
            # Categorize relationships
            users = []
            characters = []
            ai_entities = []
            
            for rel in relationships:
                entity = rel['related_entity']
                rel_data = rel['relationship']
                
                if rel_data.get('to_entity_type') == 'user' or rel_data.get('from_entity_type') == 'user':
                    users.append({
                        "user": entity,
                        "relationship": rel_data,
                        "trust_level": rel_data.get('trust_level', 0.5),
                        "familiarity": rel_data.get('familiarity_level', 0.0)
                    })
                elif rel_data.get('to_entity_type') == 'character' or rel_data.get('from_entity_type') == 'character':
                    characters.append({
                        "character": entity,
                        "relationship": rel_data,
                        "relationship_type": rel_data.get('relationship_type', 'unknown')
                    })
                elif rel_data.get('to_entity_type') == 'ai_self' or rel_data.get('from_entity_type') == 'ai_self':
                    ai_entities.append({
                        "ai_entity": entity,
                        "relationship": rel_data,
                        "management_type": rel_data.get('relationship_type', 'unknown')
                    })
            
            return {
                "character": character,
                "connected_users": users,
                "connected_characters": characters,
                "ai_relationships": ai_entities,
                "total_relationships": len(relationships),
                "network_strength": sum(r['relationship'].get('relationship_strength', 0) for r in relationships) / max(1, len(relationships))
            }
            
        except Exception as e:
            self.logger.error("Failed to get character network: %s", e)
            return {}
    
    async def find_character_similarities(self, character_id: str, similarity_threshold: float = 0.6) -> List[Dict[str, Any]]:
        """Find characters similar to the given character"""
        try:
            connector = await self._get_graph_connector()
            if not connector:
                return []
            
            # Get character's traits and preferences
            char_query = """
                MATCH (c:EnhancedCharacter {id: $character_id})
                RETURN c.personality_traits as traits, 
                       c.preferred_topics as topics,
                       c.communication_style as style,
                       c.occupation as occupation
            """
            
            char_result = await connector.execute_query(
                char_query,
                {"character_id": character_id}
            )
            
            if not char_result:
                return []
            
            char_data = char_result[0]
            
            # Find similar characters
            similar_query = """
                MATCH (c:EnhancedCharacter)
                WHERE c.id <> $character_id
                RETURN c,
                       size([trait IN c.personality_traits WHERE trait IN $traits]) as trait_overlap,
                       size([topic IN c.preferred_topics WHERE topic IN $topics]) as topic_overlap,
                       CASE WHEN c.communication_style = $style THEN 1 ELSE 0 END as style_match,
                       CASE WHEN c.occupation = $occupation THEN 1 ELSE 0 END as occupation_match
                ORDER BY trait_overlap DESC, topic_overlap DESC
                LIMIT 10
            """
            
            result = await connector.execute_query(
                similar_query,
                {
                    "character_id": character_id,
                    "traits": char_data['traits'] or [],
                    "topics": char_data['topics'] or [],
                    "style": char_data['style'],
                    "occupation": char_data['occupation']
                }
            )
            
            similar_characters = []
            for record in result:
                # Calculate similarity score
                trait_overlap = record['trait_overlap']
                topic_overlap = record['topic_overlap']
                style_match = record['style_match']
                occupation_match = record['occupation_match']
                
                max_traits = max(len(char_data['traits'] or []), len(record['c'].get('personality_traits', [])))
                max_topics = max(len(char_data['topics'] or []), len(record['c'].get('preferred_topics', [])))
                
                trait_similarity = trait_overlap / max_traits if max_traits > 0 else 0
                topic_similarity = topic_overlap / max_topics if max_topics > 0 else 0
                
                overall_similarity = (
                    trait_similarity * 0.4 +
                    topic_similarity * 0.3 +
                    style_match * 0.2 +
                    occupation_match * 0.1
                )
                
                if overall_similarity >= similarity_threshold:
                    similar_characters.append({
                        "character": record['c'],
                        "similarity_score": overall_similarity,
                        "trait_overlap": trait_overlap,
                        "topic_overlap": topic_overlap,
                        "style_match": bool(style_match),
                        "occupation_match": bool(occupation_match)
                    })
            
            return similar_characters
            
        except Exception as e:
            self.logger.error("Failed to find character similarities: %s", e)
            return []
    
    async def get_ai_self_overview(self) -> Dict[str, Any]:
        """Get overview of AI Self and managed entities"""
        try:
            ai_self_id = await self.get_or_create_ai_self()
            if not ai_self_id:
                return {}
            
            connector = await self._get_graph_connector()
            if not connector:
                return {}
            
            # Get AI Self data and managed entities
            overview_query = """
                MATCH (ai:AISelf {id: $ai_id})
                OPTIONAL MATCH (ai)-[r:RELATIONSHIP]->(managed)
                RETURN ai,
                       collect(DISTINCT {
                           entity: managed,
                           relationship: r,
                           entity_type: CASE 
                               WHEN managed:EnhancedUser THEN 'user'
                               WHEN managed:EnhancedCharacter THEN 'character'
                               ELSE 'unknown'
                           END
                       }) as managed_entities
            """
            
            result = await connector.execute_query(
                overview_query,
                {"ai_id": ai_self_id}
            )
            
            if not result:
                return {}
            
            ai_data = result[0]['ai']
            managed_entities = result[0]['managed_entities']
            
            # Categorize managed entities
            users = [e for e in managed_entities if e['entity_type'] == 'user']
            characters = [e for e in managed_entities if e['entity_type'] == 'character']
            
            return {
                "ai_self": ai_data,
                "managed_users": len(users),
                "managed_characters": len(characters),
                "total_managed_entities": len(managed_entities),
                "management_relationships": {
                    "users": users,
                    "characters": characters
                },
                "ai_capabilities": ai_data.get('capabilities', []),
                "management_style": ai_data.get('management_style', 'unknown'),
                "learning_focus": ai_data.get('learning_focus', [])
            }
            
        except Exception as e:
            self.logger.error("Failed to get AI Self overview: %s", e)
            return {}