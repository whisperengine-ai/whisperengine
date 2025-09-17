#!/usr/bin/env python3
"""
Visual Emotion Analysis Data Models for WhisperEngine Sprint 6

This module defines data structures for visual emotion analysis, supporting
both cloud-based and local processing while maintaining privacy compliance.

Key Features:
- Visual emotion detection from images
- Facial emotion analysis
- Privacy-compliant storage (no raw images)
- Multi-modal emotion fusion
- Discord integration support
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
import uuid


class VisualEmotionCategory(Enum):
    """Comprehensive visual emotion categories for image analysis"""
    
    # Core emotions detected in visual content
    JOY = "joy"                    # Smiles, celebrations, positive scenes
    SADNESS = "sadness"            # Tears, melancholy expressions, somber scenes
    ANGER = "anger"                # Frowns, aggressive gestures, tense scenes
    FEAR = "fear"                  # Wide eyes, defensive postures, scary content
    SURPRISE = "surprise"          # Open mouth, raised eyebrows, unexpected scenes
    DISGUST = "disgust"            # Wrinkled nose, negative reactions
    CONTEMPT = "contempt"          # Eye rolls, dismissive expressions
    TRUST = "trust"                # Warm expressions, intimate moments
    ANTICIPATION = "anticipation"  # Excited expressions, expectant scenes
    
    # Visual-specific emotions
    NOSTALGIA = "nostalgia"        # Old photos, vintage content, memories
    AWE = "awe"                    # Breathtaking landscapes, impressive scenes
    EMBARRASSMENT = "embarrassment" # Blushing, hiding faces, awkward moments
    PRIDE = "pride"                # Achievement poses, accomplishment displays
    SHAME = "shame"                # Hidden faces, withdrawn postures
    GUILT = "guilt"                # Averted gazes, defensive body language


class VisualContextType(Enum):
    """Categories of visual content for context-aware processing"""
    
    SELFIE = "selfie"              # Personal photos, self-portraits
    GROUP_PHOTO = "group_photo"    # Multiple people, social gatherings
    LANDSCAPE = "landscape"        # Nature, scenery, places
    MEME = "meme"                  # Humor, internet culture, reaction images
    ARTWORK = "artwork"            # Creative content, illustrations, designs
    PET = "pet"                    # Animals, pets, cute creatures
    FOOD = "food"                  # Meals, cooking, dining experiences
    EVENT = "event"                # Celebrations, parties, special occasions
    SCREENSHOT = "screenshot"      # Digital content, conversations, apps
    DOCUMENT = "document"          # Text-heavy images, forms, papers
    NATURE = "nature"              # Wildlife, plants, natural scenes
    ARCHITECTURE = "architecture"  # Buildings, structures, urban scenes
    VEHICLE = "vehicle"            # Cars, transportation, travel
    UNKNOWN = "unknown"            # Unclassified content


class ProcessingMode(Enum):
    """Visual processing deployment modes"""
    
    LOCAL = "local"                # Local multimodal models (LLaVA, CLIP)
    CLOUD = "cloud"                # Cloud vision APIs (GPT-4V, Claude 3)
    HYBRID = "hybrid"              # Local with cloud fallback


class PrivacyLevel(Enum):
    """Privacy classification for visual content"""
    
    PUBLIC = "public"              # Safe for general processing
    PRIVATE = "private"            # Contains personal information
    SENSITIVE = "sensitive"        # Contains faces or intimate content
    RESTRICTED = "restricted"      # Should not be processed


@dataclass
class DetectedEmotion:
    """Individual emotion detection result with spatial information"""
    
    emotion: VisualEmotionCategory
    confidence: float              # 0.0-1.0
    intensity: float              # 0.0-1.0
    region_coords: Optional[Tuple[int, int, int, int]] = None  # Bounding box (x, y, w, h)
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate emotion detection data"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(f"Intensity must be between 0.0 and 1.0, got {self.intensity}")


@dataclass
class FacialEmotionData:
    """Facial emotion analysis for individual detected faces"""
    
    face_id: str
    bounding_box: Tuple[int, int, int, int]  # (x, y, width, height)
    emotions: List[DetectedEmotion]
    dominant_emotion: VisualEmotionCategory
    overall_confidence: float
    
    # Optional demographic estimates (privacy-sensitive)
    age_estimate: Optional[int] = None
    gender_estimate: Optional[str] = None
    expression_description: str = ""
    
    # Facial features analysis
    eye_contact: Optional[bool] = None
    smile_intensity: Optional[float] = None
    eyebrow_position: Optional[str] = None  # "raised", "normal", "furrowed"
    
    def __post_init__(self):
        """Validate facial emotion data"""
        if not self.emotions:
            raise ValueError("At least one emotion must be detected for a face")
        
        # Ensure dominant emotion is in the emotions list
        if self.dominant_emotion not in [e.emotion for e in self.emotions]:
            raise ValueError("Dominant emotion must be present in emotions list")


@dataclass
class VisualEmotionAnalysis:
    """Complete visual emotion analysis results for an image"""
    
    # Unique identifiers
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    image_id: str = ""
    user_id: str = ""
    channel_id: str = ""
    message_id: Optional[str] = None
    
    # Temporal information
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Core emotional analysis
    primary_emotions: List[DetectedEmotion] = field(default_factory=list)
    dominant_emotion: Optional[VisualEmotionCategory] = None
    emotion_confidence: float = 0.0
    emotional_intensity: float = 0.0
    
    # Visual context analysis
    image_type: VisualContextType = VisualContextType.UNKNOWN
    scene_description: str = ""
    detected_objects: List[str] = field(default_factory=list)
    color_palette: List[str] = field(default_factory=list)
    composition_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Face and people analysis
    people_count: int = 0
    facial_emotions: List[FacialEmotionData] = field(default_factory=list)
    contains_faces: bool = False
    
    # Technical processing information
    processing_mode: ProcessingMode = ProcessingMode.LOCAL
    model_used: str = ""
    processing_time_ms: int = 0
    image_dimensions: Optional[Tuple[int, int]] = None
    
    # Context and integration
    text_context: Optional[str] = None  # Associated message text
    conversation_context: Optional[str] = None
    emotional_resonance_score: float = 0.0
    
    # Privacy and compliance
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    contains_text: bool = False
    nsfw_detected: bool = False
    
    def get_emotion_summary(self) -> str:
        """Generate human-readable emotion summary"""
        if not self.primary_emotions:
            return "No emotions detected"
        
        if len(self.primary_emotions) == 1:
            emotion = self.primary_emotions[0]
            return f"{emotion.emotion.value} ({emotion.confidence:.2f} confidence)"
        
        emotions_str = ", ".join([f"{e.emotion.value}" for e in self.primary_emotions[:3]])
        return f"Mixed emotions: {emotions_str}"
    
    def get_privacy_implications(self) -> List[str]:
        """Get list of privacy considerations for this analysis"""
        implications = []
        
        if self.contains_faces:
            implications.append("Contains facial data")
        if self.people_count > 1:
            implications.append("Multiple people detected")
        if self.privacy_level in [PrivacyLevel.SENSITIVE, PrivacyLevel.RESTRICTED]:
            implications.append("Sensitive content detected")
        if self.processing_mode == ProcessingMode.CLOUD:
            implications.append("Processed using cloud services")
        
        return implications


@dataclass
class VisualEmotionMemory:
    """Privacy-compliant memory entry for visual emotions (no raw image data)"""
    
    # Memory metadata
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Emotional summary (derived from analysis)
    emotional_summary: str = ""
    dominant_emotion: VisualEmotionCategory = VisualEmotionCategory.JOY
    emotional_intensity: float = 0.0
    emotion_categories: List[VisualEmotionCategory] = field(default_factory=list)
    
    # Visual description (no identifying information)
    scene_description: str = ""
    image_type: VisualContextType = VisualContextType.UNKNOWN
    color_mood: str = ""  # "warm", "cool", "vibrant", "muted"
    general_composition: str = ""  # "close-up", "wide-shot", "portrait"
    
    # Context information
    associated_text: Optional[str] = None
    conversation_topic: Optional[str] = None
    emotional_context: Optional[str] = None
    
    # Significance and impact
    emotional_impact_score: float = 0.0
    memorable_elements: List[str] = field(default_factory=list)
    user_reaction: Optional[str] = None
    ai_response_generated: bool = False
    
    # Privacy and retention
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    retention_policy: str = "standard"  # "standard", "extended", "minimal"
    contains_faces: bool = False
    processing_mode: ProcessingMode = ProcessingMode.LOCAL
    
    # Integration metadata
    memory_cluster_id: Optional[str] = None
    related_memories: List[str] = field(default_factory=list)
    conversation_importance: float = 0.0
    
    def should_retain(self, retention_days: int) -> bool:
        """Determine if memory should be retained based on age and significance"""
        age_days = (datetime.utcnow() - self.created_at).days
        
        if age_days <= retention_days:
            return True
        
        # Retain high-impact memories longer
        if self.emotional_impact_score > 0.8:
            return age_days <= (retention_days * 2)
        
        # Retain memories with strong emotional significance
        if self.emotional_intensity > 0.9:
            return age_days <= (retention_days * 1.5)
        
        return False
    
    def anonymize(self) -> 'VisualEmotionMemory':
        """Create anonymized version for research or analytics"""
        anonymized = VisualEmotionMemory(
            emotional_summary=self.emotional_summary,
            dominant_emotion=self.dominant_emotion,
            emotional_intensity=self.emotional_intensity,
            scene_description=self._anonymize_description(self.scene_description),
            image_type=self.image_type,
            color_mood=self.color_mood,
            emotional_impact_score=self.emotional_impact_score,
            privacy_level=PrivacyLevel.PUBLIC,
            contains_faces=False,  # Remove face indication
            processing_mode=self.processing_mode
        )
        return anonymized
    
    def _anonymize_description(self, description: str) -> str:
        """Remove potentially identifying information from description"""
        # Basic anonymization - in practice, would use more sophisticated methods
        anonymized = description.replace("person", "individual")
        anonymized = anonymized.replace("man", "person").replace("woman", "person")
        return anonymized


@dataclass
class VisualEmotionConfig:
    """Configuration for visual emotion analysis system"""
    
    # Processing configuration
    enabled: bool = True
    processing_mode: ProcessingMode = ProcessingMode.LOCAL
    confidence_threshold: float = 0.6
    max_image_size_mb: int = 10
    
    # Model configuration
    vision_model_provider: str = "local"  # "local", "openai", "anthropic"
    vision_model_name: str = "llava-1.5-7b"
    fallback_model: Optional[str] = None
    
    # Privacy configuration
    privacy_mode: str = "enhanced"  # "basic", "enhanced", "strict"
    store_facial_data: bool = False
    retention_days: int = 30
    anonymize_descriptions: bool = True
    
    # Discord integration
    discord_enabled: bool = True
    generate_responses: bool = True
    add_emoji_reactions: bool = True
    response_probability: float = 0.7  # Probability of generating a response
    
    # Performance configuration
    max_concurrent_analyses: int = 3
    analysis_timeout_seconds: int = 30
    cache_results: bool = True
    
    def validate(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []
        
        if not 0.0 <= self.confidence_threshold <= 1.0:
            issues.append("confidence_threshold must be between 0.0 and 1.0")
        
        if self.max_image_size_mb <= 0:
            issues.append("max_image_size_mb must be positive")
        
        if not 0.0 <= self.response_probability <= 1.0:
            issues.append("response_probability must be between 0.0 and 1.0")
        
        if self.retention_days < 1:
            issues.append("retention_days must be at least 1")
        
        return issues


@dataclass
class FusedEmotion:
    """Emotion result from combining visual and textual analysis"""
    
    emotion: VisualEmotionCategory
    intensity: float
    confidence: float
    sources: List[str]  # ["visual", "text", "audio", etc.]
    
    # Source-specific data
    visual_intensity: Optional[float] = None
    text_intensity: Optional[float] = None
    fusion_method: str = "weighted_average"
    
    def get_primary_source(self) -> str:
        """Get the primary source of this emotion"""
        if len(self.sources) == 1:
            return self.sources[0]
        
        # Logic to determine primary source based on intensity
        if self.visual_intensity and self.text_intensity:
            return "visual" if self.visual_intensity > self.text_intensity else "text"
        
        return "multimodal"


@dataclass
class EnhancedEmotionalState:
    """Enhanced emotional state combining multiple modalities"""
    
    emotions: List[FusedEmotion]
    dominant_emotion: VisualEmotionCategory
    multimodal_confidence: float
    
    # Context information
    visual_context: Optional[str] = None
    text_context: Optional[str] = None
    conversation_context: Optional[str] = None
    
    # Temporal information
    timestamp: datetime = field(default_factory=datetime.utcnow)
    previous_state: Optional['EnhancedEmotionalState'] = None
    
    # Analysis metadata
    fusion_method: str = "adaptive_weighting"
    processing_components: List[str] = field(default_factory=list)
    
    def get_emotion_vector(self) -> Dict[str, float]:
        """Get emotion intensities as a vector for ML processing"""
        vector = {}
        for emotion in self.emotions:
            vector[emotion.emotion.value] = emotion.intensity
        return vector
    
    def compare_to_previous(self) -> Optional[Dict[str, float]]:
        """Compare current state to previous state and return changes"""
        if not self.previous_state:
            return None
        
        current_vector = self.get_emotion_vector()
        previous_vector = self.previous_state.get_emotion_vector()
        
        changes = {}
        for emotion in set(list(current_vector.keys()) + list(previous_vector.keys())):
            current_val = current_vector.get(emotion, 0.0)
            previous_val = previous_vector.get(emotion, 0.0)
            changes[emotion] = current_val - previous_val
        
        return changes


# Type aliases for convenience
VisualEmotionResult = VisualEmotionAnalysis
EmotionDetectionList = List[DetectedEmotion]
FacialAnalysisList = List[FacialEmotionData]
VisualMemoryList = List[VisualEmotionMemory]