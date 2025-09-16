"""Data models for graph database entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid


@dataclass
class BaseNode:
    """Base class for all graph nodes."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j storage."""
        return {"id": self.id, "created_at": self.created_at, "updated_at": self.updated_at}


@dataclass
class UserNode(BaseNode):
    """User node representation."""

    discord_id: str = ""
    name: str = ""
    personality_traits: List[str] = field(default_factory=list)
    communication_style: str = "neutral"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "discord_id": self.discord_id,
                "name": self.name,
                "personality_traits": self.personality_traits,
                "communication_style": self.communication_style,
            }
        )
        return data


@dataclass
class TopicNode(BaseNode):
    """Topic/concept node representation."""

    name: str = ""
    category: str = "general"
    importance_score: float = 0.5
    first_mentioned: Optional[datetime] = None
    last_mentioned: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "name": self.name,
                "category": self.category,
                "importance_score": self.importance_score,
                "first_mentioned": self.first_mentioned,
                "last_mentioned": self.last_mentioned,
            }
        )
        return data


@dataclass
class MemoryNode(BaseNode):
    """Memory fragment node representation."""

    chromadb_id: str = ""
    summary: str = ""
    importance: float = 0.5
    timestamp: Optional[datetime] = None
    context_type: str = "conversation"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "chromadb_id": self.chromadb_id,
                "summary": self.summary,
                "importance": self.importance,
                "timestamp": self.timestamp,
                "context_type": self.context_type,
            }
        )
        return data


@dataclass
class EmotionContextNode(BaseNode):
    """Emotion context node representation."""

    emotion: str = "neutral"
    intensity: float = 0.5
    trigger_event: str = ""
    timestamp: Optional[datetime] = None
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "emotion": self.emotion,
                "intensity": self.intensity,
                "trigger_event": self.trigger_event,
                "timestamp": self.timestamp,
                "resolved": self.resolved,
            }
        )
        return data


@dataclass
class ExperienceNode(BaseNode):
    """Experience/event node representation."""

    title: str = ""
    description: str = ""
    emotional_impact: float = 0.5
    timestamp: Optional[datetime] = None
    outcome: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "title": self.title,
                "description": self.description,
                "emotional_impact": self.emotional_impact,
                "timestamp": self.timestamp,
                "outcome": self.outcome,
            }
        )
        return data


@dataclass
class KnowledgeDomainNode(BaseNode):
    """Knowledge domain node for categorizing global facts."""

    name: str = ""
    description: str = ""
    parent_domain: Optional[str] = None  # For hierarchical domains
    depth: int = 0  # Domain hierarchy depth
    fact_count: int = 0  # Number of facts in this domain

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "name": self.name,
                "description": self.description,
                "parent_domain": self.parent_domain,
                "depth": self.depth,
                "fact_count": self.fact_count,
            }
        )
        return data


@dataclass
class GlobalFactNode(BaseNode):
    """Global fact node for storing knowledge in graph database."""

    chromadb_id: str = ""  # Link to ChromaDB storage
    fact_content: str = ""
    knowledge_domain: str = "general"
    confidence_score: float = 0.8
    source: str = "learned"  # learned, user_provided, external_api, etc.
    fact_type: str = "declarative"  # declarative, procedural, episodic
    verification_status: str = "unverified"  # verified, unverified, disputed
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "chromadb_id": self.chromadb_id,
                "fact_content": self.fact_content,
                "knowledge_domain": self.knowledge_domain,
                "confidence_score": self.confidence_score,
                "source": self.source,
                "fact_type": self.fact_type,
                "verification_status": self.verification_status,
                "tags": self.tags,
            }
        )
        return data


@dataclass
class RelationshipData:
    """Relationship data container."""

    from_node: str
    to_node: str
    relationship_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    strength: float = 1.0
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_node": self.from_node,
            "to_node": self.to_node,
            "relationship_type": self.relationship_type,
            "properties": self.properties,
            "strength": self.strength,
            "created_at": self.created_at,
        }


# Global Fact Relationship Types
class FactRelationshipTypes:
    """Constants for fact relationship types."""

    RELATES_TO = "RELATES_TO"
    CONTRADICTS = "CONTRADICTS"
    SUPPORTS = "SUPPORTS"
    ELABORATES = "ELABORATES"
    GENERALIZES = "GENERALIZES"
    SPECIALIZES = "SPECIALIZES"
    CAUSES = "CAUSES"
    ENABLES = "ENABLES"
    REQUIRES = "REQUIRES"


# Knowledge Domain Categories
class KnowledgeDomains:
    """Constants for predefined knowledge domains."""

    SCIENCE = "science"
    HISTORY = "history"
    TECHNOLOGY = "technology"
    PHILOSOPHY = "philosophy"
    MATHEMATICS = "mathematics"
    LITERATURE = "literature"
    ARTS = "arts"
    GEOGRAPHY = "geography"
    BIOLOGY = "biology"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    PSYCHOLOGY = "psychology"
    SOCIOLOGY = "sociology"
    ECONOMICS = "economics"
    POLITICS = "politics"
    GENERAL = "general"
