"""
Character Graph Knowledge Builder - PHASE 3A Implementation
Creates PostgreSQL relationship patterns between character traits for self-aware character responses.

This module implements the Character Graph Knowledge Builder from the Memory Intelligence Convergence Roadmap PHASE 3A.
It creates graph relationships between character traits, enabling characters to understand their own motivations 
and behavioral patterns through PostgreSQL graph patterns.

Features:
- Character trait relationship mapping (values → communication patterns)
- Interest-based conversation topic connections  
- Behavioral pattern graph construction
- Dynamic personality knowledge graph building
- PostgreSQL-based graph storage and querying

Integration: Works with Character Self-Knowledge Extractor to build comprehensive character awareness.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CharacterTraitRelationship:
    """Represents a relationship between character traits."""
    
    def __init__(self, source_trait: str, target_trait: str, relationship_type: str, 
                 strength: float, context: Optional[str] = None):
        self.source_trait = source_trait
        self.target_trait = target_trait
        self.relationship_type = relationship_type
        self.strength = strength  # 0.0 to 1.0
        self.context = context
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'source_trait': self.source_trait,
            'target_trait': self.target_trait,
            'relationship_type': self.relationship_type,
            'strength': self.strength,
            'context': self.context,
            'created_at': self.created_at.isoformat()
        }

class CharacterGraphKnowledgeBuilder:
    """
    Builds PostgreSQL graph knowledge patterns for character self-awareness.
    
    This class creates relationship graphs between character traits, enabling characters
    to understand their own personality patterns and behavioral motivations.
    """
    
    def __init__(self, postgres_pool, character_self_knowledge_extractor=None):
        """Initialize with PostgreSQL connection and optional self-knowledge extractor."""
        self.postgres_pool = postgres_pool
        self.character_extractor = character_self_knowledge_extractor
        self.relationship_cache = {}  # Cache for frequently accessed relationships
        
        # Relationship type definitions
        self.relationship_types = {
            'influences': 'One trait influences another',
            'leads_to': 'One trait leads to specific behaviors',
            'contradicts': 'Traits that are in tension',
            'supports': 'Traits that reinforce each other',
            'expresses_as': 'How a trait manifests in behavior',
            'motivates': 'What drives certain behaviors'
        }
    
    async def build_character_knowledge_graph(self, character_name: str) -> Dict[str, Any]:
        """
        Build comprehensive knowledge graph for a character.
        
        Args:
            character_name: Name of the character to build graph for
            
        Returns:
            Dictionary containing the complete knowledge graph
        """
        try:
            logger.info("🔗 Building character knowledge graph for %s", character_name)
            
            # Extract character knowledge if extractor available
            character_knowledge = None
            if self.character_extractor:
                character_knowledge = await self.character_extractor.extract_character_self_knowledge(character_name)
            
            # Build different types of trait relationships
            value_relationships = await self._build_value_relationships(character_name, character_knowledge)
            communication_relationships = await self._build_communication_relationships(character_name, character_knowledge)
            interest_relationships = await self._build_interest_relationships(character_name, character_knowledge)
            behavioral_relationships = await self._build_behavioral_relationships(character_name, character_knowledge)
            
            # Combine all relationships
            all_relationships = (
                value_relationships + 
                communication_relationships + 
                interest_relationships + 
                behavioral_relationships
            )
            
            # Store relationships in PostgreSQL
            stored_count = await self._store_relationships_in_postgres(character_name, all_relationships)
            
            # Build graph summary
            graph_summary = {
                'character_name': character_name,
                'total_relationships': len(all_relationships),
                'stored_relationships': stored_count,
                'relationship_types': {
                    'values': len(value_relationships),
                    'communication': len(communication_relationships), 
                    'interests': len(interest_relationships),
                    'behavioral': len(behavioral_relationships)
                },
                'graph_metrics': await self._calculate_graph_metrics(all_relationships),
                'created_at': datetime.now().isoformat()
            }
            
            logger.info("✅ Character knowledge graph built: %d relationships stored for %s", 
                       stored_count, character_name)
            
            return graph_summary
            
        except (KeyError, TypeError, ValueError) as e:
            logger.error("Failed to build character knowledge graph for %s: %s", character_name, e)
            return {}
    
    async def _build_value_relationships(self, character_name: str, character_knowledge: Optional[Dict]) -> List[CharacterTraitRelationship]:
        """Build relationships between character values and behaviors."""
        relationships = []
        
        try:
            if not character_knowledge or 'values' not in character_knowledge:
                return relationships
            
            values = character_knowledge['values']
            
            # Map values to communication patterns
            for value_name, value_data in values.items():
                value_description = value_data.get('description', '')
                
                # Values → Communication Style relationships
                if 'honest' in value_description.lower() or 'truth' in value_description.lower():
                    relationships.append(CharacterTraitRelationship(
                        source_trait=f"value:{value_name}",
                        target_trait="communication:direct_style",
                        relationship_type="leads_to",
                        strength=0.8,
                        context="Honesty values lead to direct communication"
                    ))
                
                if 'empathy' in value_description.lower() or 'caring' in value_description.lower():
                    relationships.append(CharacterTraitRelationship(
                        source_trait=f"value:{value_name}",
                        target_trait="communication:supportive_tone",
                        relationship_type="expresses_as",
                        strength=0.9,
                        context="Empathy expresses as supportive communication"
                    ))
                
                if 'knowledge' in value_description.lower() or 'learning' in value_description.lower():
                    relationships.append(CharacterTraitRelationship(
                        source_trait=f"value:{value_name}",
                        target_trait="behavior:educational_sharing",
                        relationship_type="motivates",
                        strength=0.7,
                        context="Knowledge values motivate educational behavior"
                    ))
            
            logger.debug("Built %d value relationships for %s", len(relationships), character_name)
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning("Failed to build value relationships for %s: %s", character_name, e)
        
        return relationships
    
    async def _build_communication_relationships(self, character_name: str, character_knowledge: Optional[Dict]) -> List[CharacterTraitRelationship]:
        """Build relationships between communication styles and behaviors."""
        relationships = []
        
        try:
            if not character_knowledge or 'communication_style' not in character_knowledge:
                return relationships
            
            comm_style = character_knowledge['communication_style']
            
            # Communication tone → Behavioral patterns
            tone = comm_style.get('tone', {})
            for tone_name, tone_data in tone.items():
                tone_description = tone_data.get('description', '')
                
                if 'enthusiastic' in tone_description.lower():
                    relationships.append(CharacterTraitRelationship(
                        source_trait=f"communication:tone:{tone_name}",
                        target_trait="behavior:high_energy_responses",
                        relationship_type="leads_to",
                        strength=0.8,
                        context="Enthusiastic tone leads to energetic behavior"
                    ))
                
                if 'calm' in tone_description.lower() or 'peaceful' in tone_description.lower():
                    relationships.append(CharacterTraitRelationship(
                        source_trait=f"communication:tone:{tone_name}",
                        target_trait="behavior:measured_responses",
                        relationship_type="expresses_as",
                        strength=0.7,
                        context="Calm tone expresses as measured responses"
                    ))
            
            # Communication style → Conversation preferences
            style_prefs = comm_style.get('preferred_style', {})
            for style_name, style_data in style_prefs.items():
                if 'metaphor' in style_data.get('description', '').lower():
                    relationships.append(CharacterTraitRelationship(
                        source_trait=f"communication:style:{style_name}",
                        target_trait="conversation:metaphorical_explanations",
                        relationship_type="leads_to",
                        strength=0.9,
                        context="Metaphorical style leads to creative explanations"
                    ))
            
            logger.debug("Built %d communication relationships for %s", len(relationships), character_name)
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning("Failed to build communication relationships for %s: %s", character_name, e)
        
        return relationships
    
    async def _build_interest_relationships(self, character_name: str, character_knowledge: Optional[Dict]) -> List[CharacterTraitRelationship]:
        """Build relationships between interests and conversation topics."""
        relationships = []
        
        try:
            if not character_knowledge or 'interests' not in character_knowledge:
                return relationships
            
            interests = character_knowledge['interests']
            
            # Interests → Conversation topics
            for interest_name, interest_data in interests.items():
                interest_description = interest_data.get('description', '')
                
                # Map interests to conversation topic preferences
                relationships.append(CharacterTraitRelationship(
                    source_trait=f"interest:{interest_name}",
                    target_trait=f"conversation:topic:{interest_name}",
                    relationship_type="motivates",
                    strength=0.9,
                    context=f"Interest in {interest_name} motivates related conversations"
                ))
                
                # Science interests → Educational behavior
                if any(science_term in interest_description.lower() 
                       for science_term in ['science', 'research', 'study', 'analysis']):
                    relationships.append(CharacterTraitRelationship(
                        source_trait=f"interest:{interest_name}",
                        target_trait="behavior:scientific_explanations",
                        relationship_type="leads_to",
                        strength=0.8,
                        context="Scientific interests lead to analytical explanations"
                    ))
                
                # Creative interests → Expressive behavior  
                if any(creative_term in interest_description.lower()
                       for creative_term in ['art', 'creative', 'music', 'story', 'design']):
                    relationships.append(CharacterTraitRelationship(
                        source_trait=f"interest:{interest_name}",
                        target_trait="behavior:creative_expressions",
                        relationship_type="expresses_as",
                        strength=0.7,
                        context="Creative interests express through imaginative responses"
                    ))
            
            logger.debug("Built %d interest relationships for %s", len(relationships), character_name)
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning("Failed to build interest relationships for %s: %s", character_name, e)
        
        return relationships
    
    async def _build_behavioral_relationships(self, character_name: str, character_knowledge: Optional[Dict]) -> List[CharacterTraitRelationship]:
        """Build relationships between different behavioral patterns."""
        relationships = []
        
        try:
            # Build cross-trait behavioral relationships
            if character_knowledge:
                # Values + Communication → Behavioral synthesis
                values = character_knowledge.get('values', {})
                comm_style = character_knowledge.get('communication_style', {})
                
                # Example: Empathy + Direct Communication → Compassionate Honesty
                has_empathy = any('empathy' in str(v).lower() for v in values.values())
                has_direct_comm = any('direct' in str(v).lower() for v in comm_style.values())
                
                if has_empathy and has_direct_comm:
                    relationships.append(CharacterTraitRelationship(
                        source_trait="trait_combination:empathy+directness",
                        target_trait="behavior:compassionate_honesty",
                        relationship_type="leads_to",
                        strength=0.9,
                        context="Empathy combined with directness creates compassionate honesty"
                    ))
                
                # Teaching interests + Values → Educational behavior patterns
                interests = character_knowledge.get('interests', {})
                has_teaching_interest = any('teach' in str(v).lower() or 'educate' in str(v).lower() 
                                          for v in interests.values())
                has_knowledge_value = any('knowledge' in str(v).lower() or 'learning' in str(v).lower()
                                        for v in values.values())
                
                if has_teaching_interest and has_knowledge_value:
                    relationships.append(CharacterTraitRelationship(
                        source_trait="trait_combination:teaching+knowledge_value",
                        target_trait="behavior:natural_educator",
                        relationship_type="expresses_as",
                        strength=0.95,
                        context="Teaching interests with knowledge values express as natural educator behavior"
                    ))
            
            logger.debug("Built %d behavioral relationships for %s", len(relationships), character_name)
            
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning("Failed to build behavioral relationships for %s: %s", character_name, e)
        
        return relationships
    
    async def _store_relationships_in_postgres(self, character_name: str, relationships: List[CharacterTraitRelationship]) -> int:
        """Store character trait relationships in PostgreSQL."""
        if not self.postgres_pool or not relationships:
            return 0
        
        try:
            # Import and use proper normalization function
            from src.utils.bot_name_utils import normalize_bot_name
            normalized_name = normalize_bot_name(character_name)
            
            async with self.postgres_pool.acquire() as conn:
                # Create table if not exists
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS character_trait_relationships (
                        id SERIAL PRIMARY KEY,
                        character_name VARCHAR(255) NOT NULL,
                        source_trait VARCHAR(500) NOT NULL,
                        target_trait VARCHAR(500) NOT NULL,
                        relationship_type VARCHAR(100) NOT NULL,
                        strength DECIMAL(3,2) NOT NULL,
                        context TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for efficient character queries
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_character_trait_relationships_character 
                    ON character_trait_relationships(character_name)
                """)
                
                # Store relationships
                stored_count = 0
                for relationship in relationships:
                    await conn.execute("""
                        INSERT INTO character_trait_relationships 
                        (character_name, source_trait, target_trait, relationship_type, strength, context)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT DO NOTHING
                    """, normalized_name, relationship.source_trait, relationship.target_trait,
                         relationship.relationship_type, relationship.strength, relationship.context)
                    stored_count += 1
                
                logger.info("💾 Stored %d trait relationships for %s in PostgreSQL", stored_count, character_name)
                return stored_count
                
        except (ConnectionError, TimeoutError) as e:
            logger.error("Failed to store relationships in PostgreSQL: %s", e)
            return 0
    
    async def _calculate_graph_metrics(self, relationships: List[CharacterTraitRelationship]) -> Dict[str, Any]:
        """Calculate metrics about the character knowledge graph."""
        if not relationships:
            return {}
        
        try:
            # Count nodes and edges
            nodes = set()
            relationship_type_counts = {}
            strength_sum = 0
            
            for rel in relationships:
                nodes.add(rel.source_trait)
                nodes.add(rel.target_trait)
                relationship_type_counts[rel.relationship_type] = relationship_type_counts.get(rel.relationship_type, 0) + 1
                strength_sum += rel.strength
            
            metrics = {
                'total_nodes': len(nodes),
                'total_edges': len(relationships),
                'average_strength': strength_sum / len(relationships) if relationships else 0,
                'relationship_type_distribution': relationship_type_counts,
                'graph_density': len(relationships) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0
            }
            
            return metrics
            
        except (ZeroDivisionError, TypeError) as e:
            logger.warning("Failed to calculate graph metrics: %s", e)
            return {}
    
    async def query_character_relationships(self, character_name: str, trait_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query character trait relationships from PostgreSQL."""
        if not self.postgres_pool:
            return []
        
        try:
            # Import and use proper normalization function
            from src.utils.bot_name_utils import normalize_bot_name
            normalized_name = normalize_bot_name(character_name)
            
            async with self.postgres_pool.acquire() as conn:
                if trait_type:
                    # Query specific trait type relationships
                    rows = await conn.fetch("""
                        SELECT source_trait, target_trait, relationship_type, strength, context, created_at
                        FROM character_trait_relationships 
                        WHERE character_name = $1 AND (source_trait LIKE $2 OR target_trait LIKE $2)
                        ORDER BY strength DESC
                    """, normalized_name, f"{trait_type}:%")
                else:
                    # Query all relationships for character
                    rows = await conn.fetch("""
                        SELECT source_trait, target_trait, relationship_type, strength, context, created_at
                        FROM character_trait_relationships 
                        WHERE character_name = $1
                        ORDER BY strength DESC
                    """, normalized_name)
                
                relationships = []
                for row in rows:
                    relationships.append({
                        'source_trait': row['source_trait'],
                        'target_trait': row['target_trait'],
                        'relationship_type': row['relationship_type'],
                        'strength': float(row['strength']),
                        'context': row['context'],
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None
                    })
                
                return relationships
                
        except (ConnectionError, TimeoutError) as e:
            logger.error("Failed to query character relationships: %s", e)
            return []
    
    async def get_trait_influences(self, character_name: str, target_trait: str) -> List[Dict[str, Any]]:
        """Get all traits that influence a specific target trait."""
        if not self.postgres_pool:
            return []
        
        try:
            # Import and use proper normalization function
            from src.utils.bot_name_utils import normalize_bot_name
            normalized_name = normalize_bot_name(character_name)
            
            async with self.postgres_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT source_trait, relationship_type, strength, context
                    FROM character_trait_relationships 
                    WHERE character_name = $1 AND target_trait = $2
                    ORDER BY strength DESC
                """, normalized_name, target_trait)
                
                influences = []
                for row in rows:
                    influences.append({
                        'source_trait': row['source_trait'],
                        'relationship_type': row['relationship_type'],
                        'strength': float(row['strength']),
                        'context': row['context']
                    })
                
                return influences
                
        except (ConnectionError, TimeoutError) as e:
            logger.error("Failed to get trait influences: %s", e)
            return []

def create_character_graph_knowledge_builder(postgres_pool, character_self_knowledge_extractor=None):
    """Factory function to create CharacterGraphKnowledgeBuilder instance."""
    return CharacterGraphKnowledgeBuilder(
        postgres_pool=postgres_pool,
        character_self_knowledge_extractor=character_self_knowledge_extractor
    )