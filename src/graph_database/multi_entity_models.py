"""
Multi-Entity Graph Database Models

This module extends the graph database with comprehensive models for
character-user-AI self associations, enabling rich relationship networks.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Dict
from enum import Enum

from src.graph_database.models import BaseNode


class EntityType(Enum):
    """Types of entities in the system"""
    USER = "user"
    CHARACTER = "character" 
    AI_SELF = "ai_self"
    BOT_PERSONA = "bot_persona"


class RelationshipType(Enum):
    """Types of relationships between entities"""
    # User-Character relationships
    CREATED_BY = "CREATED_BY"           # Character created by User
    FAVORITE_OF = "FAVORITE_OF"         # Character is favorite of User
    TRUSTED_BY = "TRUSTED_BY"           # Character trusted by User
    DISTRUSTS = "DISTRUSTS"             # Character distrusted by User
    FAMILIAR_WITH = "FAMILIAR_WITH"     # Character familiar with User
    INTERACTS_WITH = "INTERACTS_WITH"   # General interaction relationship
    
    # Character-Character relationships
    KNOWS_ABOUT = "KNOWS_ABOUT"         # Character knows about other Character
    RELATED_TO = "RELATED_TO"           # Characters are related (family, colleagues)
    SIMILAR_TO = "SIMILAR_TO"           # Characters have similar traits
    CONTRASTS_WITH = "CONTRASTS_WITH"   # Characters have opposing traits
    INSPIRED_BY = "INSPIRED_BY"         # Character inspired by another
    
    # AI Self relationships
    MANAGES = "MANAGES"                 # AI Self manages Character/User
    OBSERVES = "OBSERVES"               # AI Self observes interactions
    FACILITATES = "FACILITATES"         # AI Self facilitates relationship
    LEARNS_FROM = "LEARNS_FROM"         # AI Self learns from entity
    ADAPTS_TO = "ADAPTS_TO"             # AI Self adapts behavior for entity


class TrustLevel(Enum):
    """Trust levels between entities"""
    UNKNOWN = 0.0
    DISTRUSTFUL = 0.2
    CAUTIOUS = 0.4
    NEUTRAL = 0.5
    TRUSTING = 0.7
    HIGHLY_TRUSTED = 0.9
    ABSOLUTE_TRUST = 1.0


class FamiliarityLevel(Enum):
    """Familiarity levels between entities"""
    STRANGER = 0.0
    ACQUAINTANCE = 0.3
    FAMILIAR = 0.6
    WELL_KNOWN = 0.8
    INTIMATE = 1.0


@dataclass
class EnhancedUserNode(BaseNode):
    """Enhanced user node with relationship capabilities"""
    
    discord_id: str = ""
    username: str = ""
    display_name: str = ""
    personality_traits: List[str] = field(default_factory=list)
    communication_style: str = "neutral"
    preferred_characters: List[str] = field(default_factory=list)
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    privacy_level: str = "standard"  # minimal, standard, open
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "discord_id": self.discord_id,
            "username": self.username,
            "display_name": self.display_name,
            "personality_traits": self.personality_traits,
            "communication_style": self.communication_style,
            "preferred_characters": self.preferred_characters,
            "interaction_count": self.interaction_count,
            "last_interaction": self.last_interaction,
            "user_preferences": self.user_preferences,
            "privacy_level": self.privacy_level
        })
        return data


@dataclass
class EnhancedCharacterNode(BaseNode):
    """Enhanced character node with full relationship support"""
    
    character_id: str = ""
    name: str = ""
    occupation: str = ""
    age: int = 0
    personality_traits: List[str] = field(default_factory=list)
    communication_style: str = "neutral"
    background_summary: str = ""
    creator_user_id: Optional[str] = None
    
    # Character development metrics
    memory_count: int = 0
    interaction_count: int = 0
    development_level: str = "basic"  # basic, developing, mature, complex
    last_conversation: Optional[datetime] = None
    
    # Character capabilities
    emotional_intelligence: float = 0.5
    creativity_level: float = 0.5
    knowledge_breadth: float = 0.5
    social_awareness: float = 0.5
    
    # Character preferences
    preferred_topics: List[str] = field(default_factory=list)
    conversation_style: str = "adaptive"
    humor_level: float = 0.5
    formality_level: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "character_id": self.character_id,
            "name": self.name,
            "occupation": self.occupation,
            "age": self.age,
            "personality_traits": self.personality_traits,
            "communication_style": self.communication_style,
            "background_summary": self.background_summary,
            "creator_user_id": self.creator_user_id,
            "memory_count": self.memory_count,
            "interaction_count": self.interaction_count,
            "development_level": self.development_level,
            "last_conversation": self.last_conversation,
            "emotional_intelligence": self.emotional_intelligence,
            "creativity_level": self.creativity_level,
            "knowledge_breadth": self.knowledge_breadth,
            "social_awareness": self.social_awareness,
            "preferred_topics": self.preferred_topics,
            "conversation_style": self.conversation_style,
            "humor_level": self.humor_level,
            "formality_level": self.formality_level
        })
        return data


@dataclass
class AISelfNode(BaseNode):
    """AI 'Self' node - the meta-entity that manages characters and users"""
    
    persona_name: str = "WhisperEngine"
    system_version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    active_characters: List[str] = field(default_factory=list)
    managed_users: List[str] = field(default_factory=list)
    
    # AI Self metrics
    total_interactions: int = 0
    characters_created: int = 0
    learning_rate: float = 0.1
    adaptation_level: float = 0.5
    
    # AI Self awareness
    self_awareness_level: float = 0.7
    meta_cognitive_ability: float = 0.6
    context_retention: float = 0.8
    cross_character_awareness: float = 0.5
    
    # AI Self preferences and style
    management_style: str = "collaborative"  # directive, collaborative, hands-off
    intervention_threshold: float = 0.3
    learning_focus: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "persona_name": self.persona_name,
            "system_version": self.system_version,
            "capabilities": self.capabilities,
            "active_characters": self.active_characters,
            "managed_users": self.managed_users,
            "total_interactions": self.total_interactions,
            "characters_created": self.characters_created,
            "learning_rate": self.learning_rate,
            "adaptation_level": self.adaptation_level,
            "self_awareness_level": self.self_awareness_level,
            "meta_cognitive_ability": self.meta_cognitive_ability,
            "context_retention": self.context_retention,
            "cross_character_awareness": self.cross_character_awareness,
            "management_style": self.management_style,
            "intervention_threshold": self.intervention_threshold,
            "learning_focus": self.learning_focus
        })
        return data


@dataclass
class EntityRelationship:
    """Relationship between any two entities"""
    
    from_entity_id: str
    to_entity_id: str
    from_entity_type: EntityType
    to_entity_type: EntityType
    relationship_type: RelationshipType
    
    # Relationship strength and quality
    trust_level: float = 0.5  # 0.0 - 1.0
    familiarity_level: float = 0.0  # 0.0 - 1.0
    emotional_bond: float = 0.0  # -1.0 to 1.0 (negative = conflict)
    interaction_frequency: float = 0.0  # interactions per day
    
    # Relationship metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    relationship_strength: float = 0.0  # computed metric
    
    # Relationship context
    relationship_context: str = ""  # how they met, relationship origin
    shared_experiences: List[str] = field(default_factory=list)
    shared_interests: List[str] = field(default_factory=list)
    communication_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Dynamic relationship evolution
    trust_trend: str = "stable"  # increasing, decreasing, stable, volatile
    relationship_stage: str = "initial"  # initial, developing, established, complex, declining
    conflict_history: List[Dict[str, Any]] = field(default_factory=list)
    positive_memories: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_entity_id": self.from_entity_id,
            "to_entity_id": self.to_entity_id,
            "from_entity_type": self.from_entity_type.value,
            "to_entity_type": self.to_entity_type.value,
            "relationship_type": self.relationship_type.value,
            "trust_level": self.trust_level,
            "familiarity_level": self.familiarity_level,
            "emotional_bond": self.emotional_bond,
            "interaction_frequency": self.interaction_frequency,
            "created_at": self.created_at,
            "last_interaction": self.last_interaction,
            "interaction_count": self.interaction_count,
            "relationship_strength": self.relationship_strength,
            "relationship_context": self.relationship_context,
            "shared_experiences": self.shared_experiences,
            "shared_interests": self.shared_interests,
            "communication_patterns": self.communication_patterns,
            "trust_trend": self.trust_trend,
            "relationship_stage": self.relationship_stage,
            "conflict_history": self.conflict_history,
            "positive_memories": self.positive_memories
        }


@dataclass
class InteractionEvent:
    """Individual interaction between entities"""
    
    interaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_entity_id: str = ""
    to_entity_id: str = ""
    interaction_type: str = "conversation"  # conversation, creation, management, observation
    
    # Interaction content
    content_summary: str = ""
    topics_discussed: List[str] = field(default_factory=list)
    emotional_tone: str = "neutral"
    sentiment_score: float = 0.0  # -1.0 to 1.0
    
    # Interaction metadata
    timestamp: datetime = field(default_factory=datetime.now)
    duration_minutes: float = 0.0
    interaction_quality: float = 0.5  # 0.0 - 1.0
    context_type: str = "direct"  # direct, mediated, observed
    
    # Interaction outcomes
    trust_change: float = 0.0
    familiarity_change: float = 0.0
    relationship_impact: str = "neutral"  # positive, neutral, negative
    learning_occurred: bool = False
    conflict_occurred: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "from_entity_id": self.from_entity_id,
            "to_entity_id": self.to_entity_id,
            "interaction_type": self.interaction_type,
            "content_summary": self.content_summary,
            "topics_discussed": self.topics_discussed,
            "emotional_tone": self.emotional_tone,
            "sentiment_score": self.sentiment_score,
            "timestamp": self.timestamp,
            "duration_minutes": self.duration_minutes,
            "interaction_quality": self.interaction_quality,
            "context_type": self.context_type,
            "trust_change": self.trust_change,
            "familiarity_change": self.familiarity_change,
            "relationship_impact": self.relationship_impact,
            "learning_occurred": self.learning_occurred,
            "conflict_occurred": self.conflict_occurred
        }


# Example relationship patterns
RELATIONSHIP_PATTERNS = {
    "user_creates_character": {
        "type": RelationshipType.CREATED_BY,
        "trust_level": 0.8,
        "familiarity_level": 1.0,
        "relationship_context": "Character creation by user"
    },
    "character_trusts_user": {
        "type": RelationshipType.TRUSTED_BY,
        "trust_level": 0.7,
        "familiarity_level": 0.6,
        "relationship_context": "Character developed trust through interactions"
    },
    "ai_self_manages_character": {
        "type": RelationshipType.MANAGES,
        "trust_level": 1.0,
        "familiarity_level": 1.0,
        "relationship_context": "AI system management of character entity"
    },
    "character_knows_character": {
        "type": RelationshipType.KNOWS_ABOUT,
        "trust_level": 0.5,
        "familiarity_level": 0.3,
        "relationship_context": "Characters aware of each other"
    }
}