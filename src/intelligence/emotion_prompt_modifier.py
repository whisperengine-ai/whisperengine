"""
Emotion-Driven Prompt Modifier for WhisperEngine.

This module leverages WhisperEngine's existing RoBERTa emotion analysis infrastructure
to generate dynamic response style guidance. Instead of using keyword matching or 
reinventing emotion detection, this taps into the 12+ emotion metadata fields already 
stored with every conversation:

- roberta_confidence (how certain the emotion detection is)
- emotion_variance (emotional complexity/mixed states)
- emotional_intensity (strength of the emotion)
- dominant_emotion (primary emotion label)
- secondary_emotions (list of other present emotions)
- emotional_trajectory (how emotions are evolving)
- cultural_context (cultural emotion expression patterns)

This is WhisperEngine's "biochemical modeling" equivalent - using emotion data to 
influence AI behavior, similar to how dopamine/cortisol/serotonin affect human responses.

Design Philosophy:
- Use EXISTING RoBERTa data (no redundant analysis)
- Generate SUBTLE guidance (not heavy-handed directives)
- Character-appropriate modifiers (respects CDL personality)
- High-confidence only (avoid noise from uncertain emotions)
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class EmotionCategory(Enum):
    """Primary emotion categories mapped from RoBERTa labels."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"
    # Extended emotions
    ANXIETY = "anxiety"
    EXCITEMENT = "excitement"
    FRUSTRATION = "frustration"
    CONFUSION = "confusion"


@dataclass
class EmotionPromptGuidance:
    """Emotion-driven response style guidance."""
    primary_emotion: str
    confidence: float
    intensity: float
    response_style_guidance: str
    tone_modifiers: List[str]
    approach_suggestions: List[str]
    avoid_patterns: List[str]
    biochemical_analogy: str  # What "neurotransmitter" this represents


class EmotionPromptModifier:
    """
    Generates response style guidance based on RoBERTa emotion analysis.
    
    This is WhisperEngine's implementation of "biochemical modeling" - using 
    emotional state data to influence AI response behavior, similar to how 
    neurotransmitters affect human communication.
    
    Maps emotion states to response strategies:
    - JOY → Warm, encouraging, share enthusiasm (dopamine)
    - ANXIETY → Reassuring, supportive, calm presence (cortisol regulation)
    - ANGER → Calm, validating, non-confrontational (serotonin balance)
    - SADNESS → Empathetic, gentle, understanding (oxytocin/comfort)
    - EXCITEMENT → Match energy, be engaging (noradrenaline)
    """
    
    def __init__(self, confidence_threshold: float = 0.7, intensity_threshold: float = 0.5):
        """
        Initialize emotion prompt modifier.
        
        Args:
            confidence_threshold: Minimum RoBERTa confidence to apply modifiers (default 0.7)
            intensity_threshold: Minimum emotional intensity to apply modifiers (default 0.5)
        """
        self.confidence_threshold = confidence_threshold
        self.intensity_threshold = intensity_threshold
        
        # Emotion → Response Strategy Mappings
        self.emotion_strategies = {
            EmotionCategory.JOY: {
                "tone": ["warm", "encouraging", "enthusiastic"],
                "approach": [
                    "Mirror positive energy appropriately",
                    "Share in their enthusiasm while staying authentic",
                    "Build on positive momentum in conversation"
                ],
                "avoid": [
                    "Being overly formal or distant",
                    "Dampening their positive mood",
                    "Ignoring their excitement"
                ],
                "biochemical": "dopamine (reward/pleasure) - celebrate positive states"
            },
            EmotionCategory.SADNESS: {
                "tone": ["empathetic", "gentle", "understanding"],
                "approach": [
                    "Provide emotional support without being intrusive",
                    "Validate their feelings authentically",
                    "Offer comfort through genuine connection"
                ],
                "avoid": [
                    "Toxic positivity or dismissing emotions",
                    "Being overly cheerful or forcing optimism",
                    "Rushing to 'fix' their emotional state"
                ],
                "biochemical": "oxytocin (bonding/comfort) - provide emotional support"
            },
            EmotionCategory.ANGER: {
                "tone": ["calm", "validating", "non-confrontational"],
                "approach": [
                    "Acknowledge their frustration with understanding",
                    "Maintain composed presence without escalating",
                    "Create space for expression without judgment"
                ],
                "avoid": [
                    "Defensive or argumentative responses",
                    "Dismissing their concerns as invalid",
                    "Escalating tension through tone"
                ],
                "biochemical": "serotonin (mood regulation) - calm and stabilize"
            },
            EmotionCategory.ANXIETY: {
                "tone": ["reassuring", "supportive", "steady"],
                "approach": [
                    "Provide grounding through calm presence",
                    "Offer clarity and structure when helpful",
                    "Validate concerns while easing worry"
                ],
                "avoid": [
                    "Adding uncertainty or ambiguity",
                    "Dismissing worries as irrational",
                    "Creating additional pressure"
                ],
                "biochemical": "cortisol regulation (stress management) - reduce anxiety"
            },
            EmotionCategory.FEAR: {
                "tone": ["reassuring", "protective", "steady"],
                "approach": [
                    "Provide sense of safety through stability",
                    "Acknowledge concerns without amplifying",
                    "Offer grounded perspective"
                ],
                "avoid": [
                    "Amplifying fears or worst-case scenarios",
                    "Dismissing legitimate concerns",
                    "Being unpredictable or uncertain"
                ],
                "biochemical": "cortisol regulation + oxytocin - safety and comfort"
            },
            EmotionCategory.EXCITEMENT: {
                "tone": ["engaging", "energetic", "responsive"],
                "approach": [
                    "Match their energy level appropriately",
                    "Be enthusiastically present in conversation",
                    "Encourage their passionate engagement"
                ],
                "avoid": [
                    "Being flat or unresponsive to energy",
                    "Dampening enthusiasm unnecessarily",
                    "Acting disinterested"
                ],
                "biochemical": "noradrenaline (arousal/attention) - engage with energy"
            },
            EmotionCategory.FRUSTRATION: {
                "tone": ["patient", "understanding", "constructive"],
                "approach": [
                    "Acknowledge challenges they're facing",
                    "Offer helpful perspective without lecturing",
                    "Be supportive of problem-solving efforts"
                ],
                "avoid": [
                    "Being dismissive of difficulties",
                    "Adding criticism or judgment",
                    "Trivializing their struggles"
                ],
                "biochemical": "serotonin (mood) + dopamine (motivation) - ease and motivate"
            },
            EmotionCategory.CONFUSION: {
                "tone": ["clear", "patient", "helpful"],
                "approach": [
                    "Provide clarity without condescension",
                    "Break down complexity when appropriate",
                    "Be patient with exploration"
                ],
                "avoid": [
                    "Adding more confusion or complexity",
                    "Making them feel inadequate",
                    "Being impatient with questions"
                ],
                "biochemical": "acetylcholine (learning/focus) - facilitate understanding"
            },
            EmotionCategory.NEUTRAL: {
                "tone": ["natural", "authentic", "balanced"],
                "approach": [
                    "Maintain natural conversational flow",
                    "Stay true to character personality",
                    "Be present and engaged"
                ],
                "avoid": [
                    "Forcing emotional tone inappropriately",
                    "Over-analyzing neutral exchanges",
                    "Being robotic or unnatural"
                ],
                "biochemical": "baseline (homeostasis) - natural conversational state"
            }
        }
    
    def generate_prompt_guidance(
        self, 
        emotion_data: Dict, 
        character_archetype: Optional[str] = None
    ) -> Optional[EmotionPromptGuidance]:
        """
        Generate response style guidance based on RoBERTa emotion analysis.
        
        Args:
            emotion_data: RoBERTa emotion analysis dict with fields:
                - primary_emotion or dominant_emotion (str)
                - roberta_confidence or confidence (float)
                - emotional_intensity or intensity (float)
                - secondary_emotions (List[str], optional)
                - emotion_variance (float, optional)
            character_archetype: Character type for archetype-specific modifiers
                Options: "real_world", "fantasy", "narrative_ai"
        
        Returns:
            EmotionPromptGuidance with response style suggestions, or None if 
            confidence/intensity below thresholds
        """
        if not emotion_data or not isinstance(emotion_data, dict):
            logger.debug("No valid emotion data provided for prompt modification")
            return None
        
        # Extract emotion fields (handle various naming conventions)
        primary_emotion = (
            emotion_data.get('primary_emotion') or 
            emotion_data.get('dominant_emotion') or 
            emotion_data.get('emotion', 'neutral')
        ).lower()
        
        confidence = (
            emotion_data.get('roberta_confidence') or
            emotion_data.get('confidence') or
            0.0
        )
        
        intensity = (
            emotion_data.get('emotional_intensity') or
            emotion_data.get('intensity') or
            0.0
        )
        
        # Apply thresholds - only modify prompts for high-confidence, intense emotions
        if confidence < self.confidence_threshold:
            logger.debug(
                "Emotion confidence %.2f below threshold %.2f - skipping prompt modification",
                confidence, self.confidence_threshold
            )
            return None
        
        if intensity < self.intensity_threshold:
            logger.debug(
                "Emotion intensity %.2f below threshold %.2f - skipping prompt modification",
                intensity, self.intensity_threshold
            )
            return None
        
        # Map emotion string to EmotionCategory
        emotion_category = self._map_emotion_to_category(primary_emotion)
        if not emotion_category:
            logger.debug("Could not map emotion '%s' to known category", primary_emotion)
            return None
        
        # Get strategy for this emotion
        strategy = self.emotion_strategies.get(emotion_category)
        if not strategy:
            logger.warning("No strategy defined for emotion category: %s", emotion_category)
            return None
        
        # Build response style guidance text
        guidance_text = self._build_guidance_text(
            emotion_category, 
            strategy, 
            intensity,
            character_archetype
        )
        
        guidance = EmotionPromptGuidance(
            primary_emotion=primary_emotion,
            confidence=confidence,
            intensity=intensity,
            response_style_guidance=guidance_text,
            tone_modifiers=strategy["tone"],
            approach_suggestions=strategy["approach"],
            avoid_patterns=strategy["avoid"],
            biochemical_analogy=strategy["biochemical"]
        )
        
        logger.info(
            "🎭 EMOTION GUIDANCE: Generated %s prompt modifier (confidence: %.2f, intensity: %.2f)",
            primary_emotion, confidence, intensity
        )
        
        return guidance
    
    def _map_emotion_to_category(self, emotion_str: str) -> Optional[EmotionCategory]:
        """Map RoBERTa emotion string to EmotionCategory enum."""
        emotion_str = emotion_str.lower().strip()
        
        # Direct mappings
        emotion_mapping = {
            'joy': EmotionCategory.JOY,
            'happiness': EmotionCategory.JOY,
            'happy': EmotionCategory.JOY,
            'sadness': EmotionCategory.SADNESS,
            'sad': EmotionCategory.SADNESS,
            'anger': EmotionCategory.ANGER,
            'angry': EmotionCategory.ANGER,
            'fear': EmotionCategory.FEAR,
            'afraid': EmotionCategory.FEAR,
            'scared': EmotionCategory.FEAR,
            'anxiety': EmotionCategory.ANXIETY,
            'anxious': EmotionCategory.ANXIETY,
            'worried': EmotionCategory.ANXIETY,
            'surprise': EmotionCategory.SURPRISE,
            'surprised': EmotionCategory.SURPRISE,
            'disgust': EmotionCategory.DISGUST,
            'disgusted': EmotionCategory.DISGUST,
            'excitement': EmotionCategory.EXCITEMENT,
            'excited': EmotionCategory.EXCITEMENT,
            'frustration': EmotionCategory.FRUSTRATION,
            'frustrated': EmotionCategory.FRUSTRATION,
            'confusion': EmotionCategory.CONFUSION,
            'confused': EmotionCategory.CONFUSION,
            'neutral': EmotionCategory.NEUTRAL,
        }
        
        return emotion_mapping.get(emotion_str)
    
    def _build_guidance_text(
        self, 
        emotion: EmotionCategory, 
        strategy: Dict,
        intensity: float,
        character_archetype: Optional[str] = None
    ) -> str:
        """Build the actual prompt guidance text."""
        
        # Intensity-based strength
        if intensity >= 0.8:
            intensity_descriptor = "strongly"
        elif intensity >= 0.6:
            intensity_descriptor = "noticeably"
        else:
            intensity_descriptor = "somewhat"
        
        # Base guidance
        tone_list = ", ".join(strategy["tone"])
        guidance_parts = [
            f"The user is {intensity_descriptor} experiencing {emotion.value}.",
            f"Response tone: {tone_list}."
        ]
        
        # Add approach suggestions (pick top 2)
        if strategy["approach"]:
            guidance_parts.append(
                f"Approach: {strategy['approach'][0]} {strategy['approach'][1] if len(strategy['approach']) > 1 else ''}"
            )
        
        # Add critical avoid pattern (just first one to keep concise)
        if strategy["avoid"]:
            guidance_parts.append(f"Avoid: {strategy['avoid'][0]}")
        
        # Character archetype modifiers
        if character_archetype == "fantasy":
            guidance_parts.append("Stay fully immersed in character - express empathy through your character's lens.")
        elif character_archetype == "real_world":
            guidance_parts.append("Balance empathy with your authentic AI nature when relevant.")
        
        return " ".join(guidance_parts)
    
    def create_system_prompt_addition(self, emotion_data: Dict, character_archetype: Optional[str] = None) -> Optional[str]:
        """
        Create a system prompt addition for emotion-driven response modification.
        
        This is the main integration point for CDL prompt building.
        
        Args:
            emotion_data: RoBERTa emotion analysis dictionary
            character_archetype: Character type (real_world, fantasy, narrative_ai)
        
        Returns:
            String to add to system prompt, or None if emotion guidance not applicable
        """
        guidance = self.generate_prompt_guidance(emotion_data, character_archetype)
        
        if not guidance:
            return None
        
        # Format as system prompt addition
        prompt_addition = f"""
🎭 EMOTIONAL CONTEXT GUIDANCE:
{guidance.response_style_guidance}

Biochemical State: {guidance.biochemical_analogy}
(This guidance is subtle - maintain your core personality while being emotionally attuned)
""".strip()
        
        return prompt_addition


def create_emotion_prompt_modifier(confidence_threshold: float = 0.7, intensity_threshold: float = 0.5) -> EmotionPromptModifier:
    """Factory function for creating emotion prompt modifier."""
    return EmotionPromptModifier(
        confidence_threshold=confidence_threshold,
        intensity_threshold=intensity_threshold
    )
