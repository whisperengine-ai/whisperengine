"""
Character data models

This module defines the core data structures for character definitions
following the Character Definition Language (CDL) specification.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class LicenseType(Enum):
    """License types for character definitions"""
    OPEN = "open"
    RESTRICTED = "restricted"
    COMMERCIAL = "commercial"
    PERSONAL = "personal"


class GenderIdentity(Enum):
    """Gender identity options"""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


@dataclass
class BigFivePersonality:
    """Big Five personality traits (0.0 to 1.0 scale)"""
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    def __post_init__(self):
        """Validate trait values are in valid range"""
        for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            value = getattr(self, trait)
            if not 0.0 <= value <= 1.0:
                setattr(self, trait, max(0.0, min(1.0, value)))


@dataclass
class Appearance:
    """Character physical appearance"""
    height: str = ""
    build: str = ""
    hair_color: str = ""
    hair_style: str = ""
    eye_color: str = ""
    skin_tone: str = ""
    distinctive_features: List[str] = field(default_factory=list)
    clothing_style: str = ""
    accessories: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Voice:
    """Character voice characteristics"""
    tone: str = "neutral"
    pace: str = "moderate"
    volume: str = "normal"
    accent: str = ""
    speech_patterns: List[str] = field(default_factory=list)
    vocabulary_style: str = "casual"
    catchphrases: List[str] = field(default_factory=list)


@dataclass
class CharacterPersonality:
    """Character personality traits and attributes"""
    big_five: BigFivePersonality = field(default_factory=BigFivePersonality)
    custom_traits: Dict[str, float] = field(default_factory=dict)
    values: List[str] = field(default_factory=list)
    fears: List[str] = field(default_factory=list)
    dreams: List[str] = field(default_factory=list)
    quirks: List[str] = field(default_factory=list)
    moral_alignment: str = "neutral"
    core_beliefs: List[str] = field(default_factory=list)
    communication_style: str = "adaptive"
    humor_style: str = "situational"
    conflict_resolution: str = "collaborative"


@dataclass
class LifePhase:
    """A phase in character's life history"""
    name: str = ""
    age_range: str = ""
    description: str = ""
    major_events: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    emotional_impact: str = ""


@dataclass
class CharacterBackstory:
    """Character background and history"""
    origin_story: str = ""
    family_background: str = ""
    education: str = ""
    formative_experiences: List[str] = field(default_factory=list)
    life_phases: List[LifePhase] = field(default_factory=list)
    traumas: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    regrets: List[str] = field(default_factory=list)


@dataclass
class CurrentProject:
    """A current project or goal"""
    name: str = ""
    description: str = ""
    status: str = "active"
    priority: str = "medium"
    deadline: Optional[datetime] = None
    progress: float = 0.0  # Changed from str to float to match parser expectations
    importance: str = ""  # Added field that parser expects
    daily_time_allocation: str = ""  # Added field that parser expects
    challenges: List[str] = field(default_factory=list)


@dataclass
class DailyRoutine:
    """Character's daily routine"""
    morning_routine: str = ""
    work_schedule: str = ""
    evening_routine: str = ""
    weekend_activities: List[str] = field(default_factory=list)
    sleep_schedule: str = ""
    habits: List[str] = field(default_factory=list)


@dataclass
class CharacterCurrentLife:
    """Character's current life situation"""
    living_situation: str = ""
    relationships: List[str] = field(default_factory=list)
    occupation_details: str = ""
    financial_status: str = ""
    health_status: str = ""
    projects: List[CurrentProject] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    daily_routine: Optional[DailyRoutine] = None
    social_circle: List[str] = field(default_factory=list)


@dataclass
class CharacterMetadata:
    """Character metadata and versioning information"""
    character_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    version: str = "1.0"
    created_by: str = ""
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    license: LicenseType = LicenseType.PERSONAL
    tags: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class CharacterIdentity:
    """Character identity and basic information"""
    name: str = ""
    age: int = 25
    gender: GenderIdentity = GenderIdentity.PREFER_NOT_TO_SAY
    occupation: str = ""
    location: str = ""
    timezone: str = "America/Los_Angeles"  # Default to Pacific Time (server timezone)
    nickname: str = ""
    full_name: str = ""
    description: str = ""
    appearance: Optional[Appearance] = None
    voice: Optional[Voice] = None

    def __post_init__(self):
        """Initialize appearance and voice if not provided"""
        if self.appearance is None:
            self.appearance = Appearance()
        if self.voice is None:
            self.voice = Voice()


@dataclass
class AIIdentityHandling:
    """AI identity handling configuration for character responses"""
    philosophy: str = ""
    approach: str = ""
    direct_ai_questions: Dict[str, Any] = field(default_factory=dict)
    character_background_questions: Dict[str, Any] = field(default_factory=dict)

@dataclass  
class CommunicationStyle:
    """Communication style configuration"""
    tone: str = "adaptive"
    formality: str = "moderate" 
    humor: str = "situational"
    empathy_level: str = "high"
    directness: str = "balanced"
    ai_identity_handling: AIIdentityHandling = field(default_factory=AIIdentityHandling)

@dataclass
class CharacterCommunication:
    """Character communication patterns and typical responses"""
    typical_responses: Dict[str, List[str]] = field(default_factory=dict)
    emotional_expressions: Dict[str, str] = field(default_factory=dict)
    response_length: str = "moderate"
    communication_style: CommunicationStyle = field(default_factory=CommunicationStyle)
    
    def __post_init__(self):
        """Initialize default typical responses if empty"""
        if not self.typical_responses:
            self.typical_responses = {
                "greeting": [],
                "compliment_received": [],
                "advice_giving": [],
                "romantic_interest": [],
                "farewell": [],
                "confusion": [],
                "excitement": [],
                "concern": []
            }
        
        if not self.emotional_expressions:
            self.emotional_expressions = {
                "happiness": "Warm and genuine expression",
                "sadness": "Thoughtful and empathetic",
                "anger": "Controlled but firm",
                "surprise": "Open and curious",
                "fear": "Cautious but brave",
                "disgust": "Politely dismissive"
            }


@dataclass
class Character:
    """Complete character definition following CDL specification"""
    metadata: CharacterMetadata = field(default_factory=CharacterMetadata)
    identity: CharacterIdentity = field(default_factory=CharacterIdentity)
    personality: CharacterPersonality = field(default_factory=CharacterPersonality)
    backstory: CharacterBackstory = field(default_factory=CharacterBackstory)
    current_life: CharacterCurrentLife = field(default_factory=CharacterCurrentLife)
    communication: CharacterCommunication = field(default_factory=CharacterCommunication)
    
    # Runtime state (not serialized)
    _runtime_state: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        """Initialize character after creation"""
        # Sync metadata name with identity name if metadata name is empty
        if not self.metadata.name and self.identity.name:
            self.metadata.name = self.identity.name
        
        # Update last modified timestamp
        self.metadata.last_modified = datetime.now()

    def get_display_name(self) -> str:
        """Get the character's display name"""
        return self.identity.nickname or self.identity.name or "Unnamed Character"

    def get_age_description(self) -> str:
        """Get a human-readable age description"""
        age = self.identity.age
        if age < 13:
            return "child"
        elif age < 20:
            return "teenager"
        elif age < 30:
            return "young adult"
        elif age < 50:
            return "adult"
        elif age < 65:
            return "middle-aged"
        else:
            return "elder"

    def is_valid(self) -> Tuple[bool, List[str]]:
        """
        Validate the character definition
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Basic validation
        if not self.identity.name or len(self.identity.name.strip()) < 2:
            errors.append("Character must have a valid name (at least 2 characters)")
        
        if self.identity.age < 0:
            errors.append("Character age cannot be negative")
        elif self.identity.age > 150:
            errors.append("Character age is unrealistically high (>150)")
        
        if not self.identity.occupation or len(self.identity.occupation.strip()) < 3:
            errors.append("Character must have a valid occupation")
        
        # Personality validation
        traits = self.personality.big_five
        for trait_name in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            value = getattr(traits, trait_name)
            if not 0.0 <= value <= 1.0:
                errors.append(f"Big Five trait '{trait_name}' must be between 0.0 and 1.0")
        
        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary representation"""
        from dataclasses import asdict
        result = asdict(self)
        
        # Remove runtime state
        result.pop('_runtime_state', None)
        
        # Convert enums to their values
        result['metadata']['license'] = self.metadata.license.value
        result['identity']['gender'] = self.identity.gender.value
        
        # Convert datetime objects to ISO strings
        result['metadata']['created_date'] = self.metadata.created_date.isoformat()
        result['metadata']['last_modified'] = self.metadata.last_modified.isoformat()
        
        # Handle project deadlines
        for project in result['current_life']['projects']:
            if project.get('deadline'):
                project['deadline'] = project['deadline'].isoformat()
        
        return result

    def update_last_modified(self):
        """Update the last modified timestamp"""
        self.metadata.last_modified = datetime.now()

    def add_tag(self, tag: str):
        """Add a tag to the character metadata"""
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            self.update_last_modified()

    def remove_tag(self, tag: str):
        """Remove a tag from the character metadata"""
        if tag in self.metadata.tags:
            self.metadata.tags.remove(tag)
            self.update_last_modified()

    def add_life_phase(self, phase: LifePhase):
        """Add a life phase to the character's backstory"""
        self.backstory.life_phases.append(phase)
        self.update_last_modified()

    def add_current_project(self, project: CurrentProject):
        """Add a current project to the character"""
        self.current_life.projects.append(project)
        self.update_last_modified()

    def get_personality_summary(self) -> str:
        """Get a text summary of the character's personality"""
        big_five = self.personality.big_five
        traits = []
        
        if big_five.openness > 0.7:
            traits.append("very open to new experiences")
        elif big_five.openness < 0.3:
            traits.append("prefers familiar experiences")
        
        if big_five.conscientiousness > 0.7:
            traits.append("highly organized and disciplined")
        elif big_five.conscientiousness < 0.3:
            traits.append("more spontaneous and flexible")
        
        if big_five.extraversion > 0.7:
            traits.append("very outgoing and social")
        elif big_five.extraversion < 0.3:
            traits.append("more introverted and reserved")
        
        if big_five.agreeableness > 0.7:
            traits.append("very cooperative and trusting")
        elif big_five.agreeableness < 0.3:
            traits.append("more competitive and skeptical")
        
        if big_five.neuroticism > 0.7:
            traits.append("tends to experience strong emotions")
        elif big_five.neuroticism < 0.3:
            traits.append("emotionally stable and calm")
        
        if not traits:
            return "has a balanced personality"
        
        return ", ".join(traits)

    def __str__(self) -> str:
        """String representation of the character"""
        return f"Character({self.get_display_name()}, {self.identity.age}, {self.identity.occupation})"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"Character(name='{self.identity.name}', age={self.identity.age}, "
                f"occupation='{self.identity.occupation}', id='{self.metadata.character_id}')")