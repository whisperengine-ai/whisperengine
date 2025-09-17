"""
Advanced Emotional State Data Model for WhisperEngine

Supports 12+ core emotions, nuanced states, multi-modal detection, temporal and cultural context.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class AdvancedEmotionalState:
    # Core emotions (expanded from 8 to 12)
    primary_emotion: str  # joy, sadness, anger, fear, surprise, disgust, trust, anticipation, contempt, pride, shame, guilt
    secondary_emotions: List[str] = field(default_factory=list)  # Nuanced emotional states
    emotional_intensity: float = 0.0  # 0.0-1.0

    # Multi-modal detection
    text_indicators: List[str] = field(default_factory=list)
    emoji_analysis: Dict[str, float] = field(default_factory=dict)
    punctuation_patterns: Dict[str, int] = field(default_factory=dict)

    # Temporal context
    emotional_trajectory: List[float] = field(default_factory=list)  # Last 5 measurements
    pattern_type: Optional[str] = None  # stable, escalating, oscillating, declining

    # Cultural adaptation
    cultural_context: Optional[str] = None
    expression_style: Optional[str] = None  # direct, indirect, expressive, reserved

    # Timestamp for state
    timestamp: datetime = field(default_factory=datetime.utcnow)
