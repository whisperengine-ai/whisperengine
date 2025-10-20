"""
Character Graph Self-Knowledge Extractor
WhisperEngine Memory Intelligence Convergence - PHASE 3A
Version: 1.0 - October 2025

Enables characters to extract and understand their own personality knowledge
from the CDL database, creating self-aware character trait understanding
without hardcoded logic.

Core Capabilities:
- Extract character personality data from CDL database
- Analyze trait relationships and patterns
- Build character self-knowledge graphs
- Enable dynamic personality understanding
"""

import logging
from typing import Dict, Any, List, Optional
import asyncpg
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class CharacterTraitNode:
    """Represents a single character trait with metadata"""
    trait_type: str  # 'personality', 'value', 'interest', 'communication', 'behavior'
    trait_name: str
    trait_value: Any
    intensity: float = 0.0
    importance: int = 5
    context: Optional[str] = None
    related_traits: Optional[List[str]] = None

    def __post_init__(self):
        if self.related_traits is None:
            self.related_traits = []

@dataclass
class CharacterKnowledgeProfile:
    """Complete character self-knowledge profile"""
    character_name: str
    personality_traits: List[CharacterTraitNode]
    values_beliefs: List[CharacterTraitNode]
    interests_expertise: List[CharacterTraitNode]
    communication_patterns: List[CharacterTraitNode]
    behavioral_triggers: List[CharacterTraitNode]
    knowledge_graph: Dict[str, List[str]]  # trait -> related traits mapping
    extraction_timestamp: datetime
    confidence_score: float = 0.0

class CharacterSelfKnowledgeExtractor:
    """
    Extracts character personality knowledge from CDL database
    and builds self-awareness understanding for characters.
    """
    
    def __init__(self, postgres_pool: asyncpg.Pool):
        self.postgres_pool = postgres_pool
        
    async def extract_character_self_knowledge(self, character_name: str) -> Optional[CharacterKnowledgeProfile]:
        """
        Extract complete self-knowledge profile for a character.
        
        Args:
            character_name: Name of the character to analyze
            
        Returns:
            CharacterKnowledgeProfile with comprehensive self-knowledge data
        """
        try:
            logger.info("🧠 SELF-KNOWLEDGE: Extracting character knowledge for '%s'", character_name)
            
            async with self.postgres_pool.acquire() as conn:
                # Get character ID
                character_id = await self._get_character_id(conn, character_name)
                if not character_id:
                    logger.warning("🧠 SELF-KNOWLEDGE: Character '%s' not found", character_name)
                    return None
                
                # Extract all trait types
                personality_traits = await self._extract_personality_traits(conn, character_id)
                values_beliefs = await self._extract_values_beliefs(conn, character_id)
                interests_expertise = await self._extract_interests_expertise(conn, character_id)
                communication_patterns = await self._extract_communication_patterns(conn, character_id)
                behavioral_triggers = await self._extract_behavioral_triggers(conn, character_id)
                
                # Build knowledge graph relationships
                knowledge_graph = self._build_trait_relationships(
                    personality_traits, values_beliefs, interests_expertise, 
                    communication_patterns, behavioral_triggers
                )
                
                # Calculate confidence score based on data completeness
                confidence_score = self._calculate_knowledge_confidence(
                    personality_traits, values_beliefs, interests_expertise,
                    communication_patterns, behavioral_triggers
                )
                
                profile = CharacterKnowledgeProfile(
                    character_name=character_name,
                    personality_traits=personality_traits,
                    values_beliefs=values_beliefs,
                    interests_expertise=interests_expertise,
                    communication_patterns=communication_patterns,
                    behavioral_triggers=behavioral_triggers,
                    knowledge_graph=knowledge_graph,
                    extraction_timestamp=datetime.now(),
                    confidence_score=confidence_score
                )
                
                logger.info("🧠 SELF-KNOWLEDGE: Extracted knowledge profile for '%s' - %.1f%% confidence, %d total traits",
                           character_name, confidence_score * 100, 
                           len(personality_traits) + len(values_beliefs) + len(interests_expertise))
                
                return profile
                
        except (asyncpg.PostgresError, ValueError, KeyError) as e:
            logger.error("🧠 SELF-KNOWLEDGE: Failed to extract knowledge for '%s': %s", character_name, str(e))
            return None
    
    async def _get_character_id(self, conn: asyncpg.Connection, character_name: str) -> Optional[int]:
        """Get character ID from database"""
        # Import and use proper normalization function
        from src.utils.bot_name_utils import normalize_bot_name
        normalized_name = normalize_bot_name(character_name)
        
        row = await conn.fetchrow(
            "SELECT id FROM characters WHERE normalized_name = $1",
            normalized_name
        )
        return row['id'] if row else None
    
    async def _extract_personality_traits(self, conn: asyncpg.Connection, character_id: int) -> List[CharacterTraitNode]:
        """Extract Big Five personality traits"""
        traits = []
        
        query = """
            SELECT trait_name, trait_value, intensity, trait_description
            FROM personality_traits
            WHERE character_id = $1
        """
        
        rows = await conn.fetch(query, character_id)
        for row in rows:
            trait = CharacterTraitNode(
                trait_type='personality',
                trait_name=row['trait_name'],
                trait_value=float(row['trait_value']) if row['trait_value'] else 0.0,
                intensity=float(row['trait_value']) if row['trait_value'] else 0.0,
                importance=8,  # Personality traits are high importance
                context=row['trait_description']
            )
            traits.append(trait)
        
        logger.debug("🧠 SELF-KNOWLEDGE: Extracted %d personality traits", len(traits))
        return traits
    
    async def _extract_values_beliefs(self, conn: asyncpg.Connection, character_id: int) -> List[CharacterTraitNode]:
        """Extract character values and beliefs"""
        traits = []
        
        query = """
            SELECT category, value_key, value_description, importance_level
            FROM character_values
            WHERE character_id = $1
        """
        
        rows = await conn.fetch(query, character_id)
        for row in rows:
            trait = CharacterTraitNode(
                trait_type='value',
                trait_name=f"{row['category']}.{row['value_key']}",
                trait_value=row['value_description'],
                importance=row['importance_level'] or 5,
                context=f"Category: {row['category']}"
            )
            traits.append(trait)
        
        logger.debug("🧠 SELF-KNOWLEDGE: Extracted %d values/beliefs", len(traits))
        return traits
    
    async def _extract_interests_expertise(self, conn: asyncpg.Connection, character_id: int) -> List[CharacterTraitNode]:
        """Extract character interests and areas of expertise"""
        traits = []
        
        # Extract from character abilities
        abilities_query = """
            SELECT category, ability_name, proficiency_level, description, usage_frequency
            FROM character_abilities
            WHERE character_id = $1
        """
        
        rows = await conn.fetch(abilities_query, character_id)
        for row in rows:
            trait = CharacterTraitNode(
                trait_type='expertise',
                trait_name=f"{row['category']}.{row['ability_name']}",
                trait_value=row['proficiency_level'] or 5,
                intensity=float(row['proficiency_level']) / 10.0 if row['proficiency_level'] else 0.5,
                importance=7,
                context=f"Usage: {row['usage_frequency']}, Description: {row['description']}"
            )
            traits.append(trait)
        
        # Extract from character interests (if available in schema)
        # Note: This would need to be expanded based on actual database schema
        
        logger.debug("🧠 SELF-KNOWLEDGE: Extracted %d interests/expertise", len(traits))
        return traits
    
    async def _extract_communication_patterns(self, conn: asyncpg.Connection, character_id: int) -> List[CharacterTraitNode]:
        """Extract communication style patterns"""
        traits = []
        
        query = """
            SELECT engagement_level, formality, emotional_expression, response_length,
                   ai_identity_handling
            FROM communication_styles
            WHERE character_id = $1
        """
        
        row = await conn.fetchrow(query, character_id)
        if row:
            # Convert communication style fields to trait nodes
            if row['engagement_level'] is not None:
                trait = CharacterTraitNode(
                    trait_type='communication',
                    trait_name='engagement_level',
                    trait_value=float(row['engagement_level']),
                    intensity=float(row['engagement_level']) / 10.0,
                    importance=6,
                    context="How actively character engages in conversations"
                )
                traits.append(trait)
            
            if row['formality']:
                trait = CharacterTraitNode(
                    trait_type='communication',
                    trait_name='formality',
                    trait_value=row['formality'],
                    importance=6,
                    context="Character's preferred communication formality level"
                )
                traits.append(trait)
            
            if row['emotional_expression'] is not None:
                trait = CharacterTraitNode(
                    trait_type='communication',
                    trait_name='emotional_expression',
                    trait_value=float(row['emotional_expression']),
                    intensity=float(row['emotional_expression']) / 10.0,
                    importance=7,
                    context="How emotionally expressive character is"
                )
                traits.append(trait)
            
            if row['response_length']:
                trait = CharacterTraitNode(
                    trait_type='communication',
                    trait_name='response_length',
                    trait_value=row['response_length'],
                    importance=5,
                    context="Character's preferred response length style"
                )
                traits.append(trait)
        
        logger.debug("🧠 SELF-KNOWLEDGE: Extracted %d communication patterns", len(traits))
        return traits
    
    async def _extract_behavioral_triggers(self, conn: asyncpg.Connection, character_id: int) -> List[CharacterTraitNode]:
        """Extract behavioral triggers and response patterns"""
        traits = []
        
        query = """
            SELECT trigger_type, trigger_value, response_type, response_description, intensity_level
            FROM behavioral_triggers
            WHERE character_id = $1
        """
        
        rows = await conn.fetch(query, character_id)
        for row in rows:
            trait = CharacterTraitNode(
                trait_type='behavior',
                trait_name=f"{row['trigger_type']}.{row['trigger_value']}",
                trait_value=row['response_type'],
                intensity=float(row['intensity_level']) / 10.0 if row['intensity_level'] else 0.5,
                importance=6,
                context=row['response_description']
            )
            traits.append(trait)
        
        logger.debug("🧠 SELF-KNOWLEDGE: Extracted %d behavioral triggers", len(traits))
        return traits
    
    def _build_trait_relationships(self, *trait_lists) -> Dict[str, List[str]]:
        """
        Build relationships between character traits based on logical connections.
        This creates the 'knowledge graph' of how traits relate to each other.
        """
        knowledge_graph = {}
        all_traits = []
        
        # Flatten all trait lists
        for trait_list in trait_lists:
            all_traits.extend(trait_list)
        
        # Build relationships based on trait analysis
        for trait in all_traits:
            trait_key = f"{trait.trait_type}.{trait.trait_name}"
            knowledge_graph[trait_key] = []
            
            # Find related traits based on type and content similarity
            for other_trait in all_traits:
                if other_trait == trait:
                    continue
                
                other_key = f"{other_trait.trait_type}.{other_trait.trait_name}"
                
                # Build relationships based on logical connections
                if self._are_traits_related(trait, other_trait):
                    knowledge_graph[trait_key].append(other_key)
        
        logger.debug("🧠 SELF-KNOWLEDGE: Built knowledge graph with %d trait relationships", len(knowledge_graph))
        return knowledge_graph
    
    def _are_traits_related(self, trait1: CharacterTraitNode, trait2: CharacterTraitNode) -> bool:
        """Determine if two traits are logically related"""
        
        # Same type traits are often related
        if trait1.trait_type == trait2.trait_type:
            return True
        
        # High importance traits relate to communication patterns
        if trait1.importance >= 7 and trait2.trait_type == 'communication':
            return True
        
        # Values relate to behaviors
        if trait1.trait_type == 'value' and trait2.trait_type == 'behavior':
            return True
        
        # Personality traits relate to communication
        if trait1.trait_type == 'personality' and trait2.trait_type == 'communication':
            return True
        
        # Expertise relates to behavioral triggers
        if trait1.trait_type == 'expertise' and trait2.trait_type == 'behavior':
            return True
        
        return False
    
    def _calculate_knowledge_confidence(self, *trait_lists) -> float:
        """Calculate confidence score based on data completeness"""
        total_traits = sum(len(trait_list) for trait_list in trait_lists)
        
        if total_traits == 0:
            return 0.0
        
        # Base confidence on trait count and variety
        trait_types = set()
        high_importance_count = 0
        
        for trait_list in trait_lists:
            for trait in trait_list:
                trait_types.add(trait.trait_type)
                if trait.importance >= 7:
                    high_importance_count += 1
        
        # Calculate confidence based on:
        # - Total number of traits
        # - Variety of trait types
        # - Number of high-importance traits
        base_confidence = min(total_traits / 20.0, 1.0)  # 20+ traits = full base confidence
        variety_bonus = len(trait_types) / 5.0 * 0.2  # 5 types = 20% bonus
        importance_bonus = min(high_importance_count / 10.0, 1.0) * 0.1  # 10+ high importance = 10% bonus
        
        confidence = min(base_confidence + variety_bonus + importance_bonus, 1.0)
        return confidence

def create_character_self_knowledge_extractor(postgres_pool: asyncpg.Pool) -> CharacterSelfKnowledgeExtractor:
    """Factory function to create CharacterSelfKnowledgeExtractor"""
    return CharacterSelfKnowledgeExtractor(postgres_pool)