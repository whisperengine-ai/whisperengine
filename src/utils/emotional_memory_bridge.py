"""
Emotional-Memory Integration Bridge

This module connects Sprint 1 emotional intelligence persistence with 
Sprint 2 memory importance patterns to create enhanced memory scoring
based on emotional context and learned emotional triggers.

Sprint 3 Task 3.2: Emotional-Memory Integration
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone as tz
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EmotionalMemoryContext:
    """Enhanced memory context with emotional intelligence data"""
    
    # Original memory data
    memory_id: str
    user_id: str
    content: str
    base_importance_score: float
    
    # Emotional context from Sprint 1
    mood_category: str
    stress_level: str
    emotional_prediction: dict[str, Any]
    emotional_alerts: list[dict[str, Any]]
    
    # Enhanced scoring results
    emotional_importance_boost: float
    emotional_trigger_match: bool
    emotional_pattern_confidence: float
    final_importance_score: float
    
    # Metadata
    assessment_timestamp: datetime
    enhancement_applied: bool


class EmotionalMemoryBridge:
    """
    Bridge between emotional intelligence and memory importance systems
    
    Provides enhanced memory scoring based on emotional context,
    learns emotional trigger patterns, and applies emotional boosts
    to memory importance calculations.
    """
    
    def __init__(self, emotional_intelligence, memory_importance_engine):
        """
        Initialize the emotional-memory bridge
        
        Args:
            emotional_intelligence: PredictiveEmotionalIntelligence instance
            memory_importance_engine: MemoryImportanceEngine instance
        """
        self.emotional_intelligence = emotional_intelligence
        self.memory_importance_engine = memory_importance_engine
        
        # Emotional boost multipliers
        self.emotional_boost_config = {
            "high_stress_boost": 1.4,      # Memories during high stress are more important
            "crisis_boost": 1.8,           # Crisis memories are extremely important
            "positive_milestone_boost": 1.3, # Positive emotional milestones
            "emotional_pattern_boost": 1.2, # Memories matching learned emotional patterns
            "emotional_resolution_boost": 1.5, # Memories that show emotional resolution
        }
        
        # Pattern confidence thresholds
        self.pattern_confidence_thresholds = {
            "high_confidence": 0.8,
            "medium_confidence": 0.6,
            "low_confidence": 0.4,
        }
        
        logger.info("Emotional-Memory Bridge initialized for Sprint 3 Task 3.2")

    async def enhance_memory_with_emotional_context(
        self,
        user_id: str,
        memory_id: str,
        memory_data: dict[str, Any],
        current_message: str,
        base_importance_score: float
    ) -> EmotionalMemoryContext:
        """
        Enhance memory importance scoring with emotional intelligence context
        
        Args:
            user_id: User identifier
            memory_id: Memory identifier
            memory_data: Original memory data
            current_message: Current user message for emotional context
            base_importance_score: Base importance score from Sprint 2
            
        Returns:
            Enhanced memory context with emotional intelligence integration
        """
        try:
            # Step 1: Get comprehensive emotional assessment
            emotional_assessment = await self.emotional_intelligence.comprehensive_emotional_assessment(
                user_id=user_id,
                current_message=current_message,
                conversation_context={"memory_retrieval": True, "memory_id": memory_id}
            )
            
            # Step 2: Calculate emotional importance boost
            emotional_boost = await self._calculate_emotional_boost(
                memory_data=memory_data,
                emotional_assessment=emotional_assessment,
                user_id=user_id
            )
            
            # Step 3: Check for emotional trigger pattern matches
            trigger_match, pattern_confidence = await self._check_emotional_trigger_patterns(
                memory_data=memory_data,
                emotional_assessment=emotional_assessment,
                user_id=user_id
            )
            
            # Step 4: Calculate final enhanced importance score
            final_score = min(1.0, base_importance_score * (1.0 + emotional_boost))
            
            # Step 5: Learn from this emotional-memory interaction
            await self._learn_emotional_memory_patterns(
                user_id=user_id,
                memory_data=memory_data,
                emotional_assessment=emotional_assessment,
                final_importance_score=final_score
            )
            
            # Create enhanced memory context
            enhanced_context = EmotionalMemoryContext(
                memory_id=memory_id,
                user_id=user_id,
                content=memory_data.get("content", ""),
                base_importance_score=base_importance_score,
                mood_category=emotional_assessment.mood_assessment.category.value,
                stress_level=emotional_assessment.stress_assessment.level.value,
                emotional_prediction={
                    "emotion": emotional_assessment.emotional_prediction.predicted_emotion,
                    "confidence": emotional_assessment.emotional_prediction.confidence,
                    "factors": emotional_assessment.emotional_prediction.triggering_factors,
                },
                emotional_alerts=[
                    {
                        "type": alert.alert_type.value,
                        "priority": alert.priority.value,
                        "message": alert.message,
                    }
                    for alert in emotional_assessment.emotional_alerts
                ],
                emotional_importance_boost=emotional_boost,
                emotional_trigger_match=trigger_match,
                emotional_pattern_confidence=pattern_confidence,
                final_importance_score=final_score,
                assessment_timestamp=datetime.now(tz.utc),
                enhancement_applied=True,
            )
            
            logger.debug(
                "Enhanced memory %s for user %s: base=%.3f → final=%.3f (boost=%.3f)",
                memory_id, user_id, base_importance_score, final_score, emotional_boost
            )
            
            return enhanced_context
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.warning("Failed to enhance memory %s with emotional context: %s", memory_id, e)
            
            # Return basic context without enhancement
            return EmotionalMemoryContext(
                memory_id=memory_id,
                user_id=user_id,
                content=memory_data.get("content", ""),
                base_importance_score=base_importance_score,
                mood_category="unknown",
                stress_level="unknown",
                emotional_prediction={"emotion": "neutral", "confidence": 0.0, "factors": []},
                emotional_alerts=[],
                emotional_importance_boost=0.0,
                emotional_trigger_match=False,
                emotional_pattern_confidence=0.0,
                final_importance_score=base_importance_score,
                assessment_timestamp=datetime.now(tz.utc),
                enhancement_applied=False,
            )

    async def _calculate_emotional_boost(
        self,
        memory_data: dict[str, Any],
        emotional_assessment: Any,  # EmotionalIntelligenceAssessment
        user_id: str
    ) -> float:
        """Calculate emotional importance boost based on emotional context"""
        boost = 0.0
        
        try:
            # High stress memories are more important (survival significance)
            if emotional_assessment.stress_assessment.level.value in ["high", "extreme"]:
                boost += self.emotional_boost_config["high_stress_boost"] - 1.0
                logger.debug("Applied high stress boost for user %s", user_id)
            
            # Crisis situations create extremely important memories
            if emotional_assessment.emotional_alerts:
                for alert in emotional_assessment.emotional_alerts:
                    if alert.priority.value in ["high", "urgent"]:
                        boost += self.emotional_boost_config["crisis_boost"] - 1.0
                        logger.debug("Applied crisis boost for user %s", user_id)
                        break
            
            # Positive emotional milestones are important for growth
            if (emotional_assessment.mood_assessment.category.value in ["happy", "excited", "grateful"] and
                emotional_assessment.emotional_prediction.confidence > 0.7):
                boost += self.emotional_boost_config["positive_milestone_boost"] - 1.0
                logger.debug("Applied positive milestone boost for user %s", user_id)
            
            # Check for emotional resolution (important for healing)
            if await self._detect_emotional_resolution(memory_data, emotional_assessment):
                boost += self.emotional_boost_config["emotional_resolution_boost"] - 1.0
                logger.debug("Applied emotional resolution boost for user %s", user_id)
            
            return min(boost, 1.0)  # Cap total boost at 100%
            
        except (ValueError, KeyError, AttributeError) as e:
            logger.warning("Error calculating emotional boost: %s", e)
            return 0.0

    async def _check_emotional_trigger_patterns(
        self,
        memory_data: dict[str, Any],
        emotional_assessment: Any,
        user_id: str
    ) -> tuple[bool, float]:
        """Check if memory matches learned emotional trigger patterns"""
        try:
            # Get user's emotional trigger patterns from persistence
            emotional_patterns = await self.memory_importance_engine.load_user_importance_patterns(user_id)
            
            memory_content = memory_data.get("content", "").lower()
            current_emotion = emotional_assessment.emotional_prediction.predicted_emotion
            
            # Check patterns for matches
            trigger_match = False
            max_confidence = 0.0
            
            for pattern in emotional_patterns:
                if pattern.get("pattern_type") == "emotional_trigger":
                    # Check emotional associations
                    pattern_emotions = pattern.get("emotional_associations", [])
                    if current_emotion in pattern_emotions:
                        # Check keyword matches
                        pattern_keywords = pattern.get("pattern_keywords", [])
                        keyword_matches = sum(1 for keyword in pattern_keywords if keyword in memory_content)
                        
                        if keyword_matches > 0:
                            trigger_match = True
                            pattern_confidence = pattern.get("confidence_score", 0.0)
                            max_confidence = max(max_confidence, pattern_confidence)
                            logger.debug("Emotional trigger pattern match for user %s: %s", 
                                       user_id, pattern.get("pattern_name"))
            
            return trigger_match, max_confidence
            
        except (ValueError, KeyError) as e:
            logger.warning("Error checking emotional trigger patterns: %s", e)
            return False, 0.0

    async def _detect_emotional_resolution(
        self,
        memory_data: dict[str, Any],
        emotional_assessment: Any
    ) -> bool:
        """Detect if memory represents emotional resolution or breakthrough"""
        try:
            content = memory_data.get("content", "").lower()
            
            # Keywords that suggest emotional resolution
            resolution_keywords = [
                "feel better", "resolved", "breakthrough", "clarity", "peace",
                "healing", "recovered", "overcame", "strength", "growth",
                "understand now", "make sense", "closure", "forgive",
                "learned", "wisdom", "acceptance", "moving forward"
            ]
            
            # Check for resolution keywords
            resolution_match = any(keyword in content for keyword in resolution_keywords)
            
            # Check emotional state transition (from negative to positive)
            current_mood = emotional_assessment.mood_assessment.category.value
            emotional_improvement = current_mood in ["happy", "peaceful", "grateful", "hopeful"]
            
            return resolution_match and emotional_improvement
            
        except (ValueError, AttributeError) as e:
            logger.warning("Error detecting emotional resolution: %s", e)
            return False

    async def _learn_emotional_memory_patterns(
        self,
        user_id: str,
        memory_data: dict[str, Any],
        emotional_assessment: Any,
        final_importance_score: float
    ):
        """Learn emotional-memory patterns from this interaction"""
        try:
            # Only learn from high-importance emotional memories
            if final_importance_score > 0.7:
                content = memory_data.get("content", "")
                emotion = emotional_assessment.emotional_prediction.predicted_emotion
                confidence = emotional_assessment.emotional_prediction.confidence
                
                # Extract emotional keywords for pattern learning
                emotional_keywords = await self._extract_emotional_context_keywords(
                    content, emotional_assessment
                )
                
                # Create emotional trigger pattern
                if emotional_keywords and confidence > 0.6:
                    pattern_data = {
                        "pattern_name": f"emotional_trigger_{emotion}_{user_id}",
                        "importance_multiplier": min(2.0, 1.0 + (final_importance_score - 0.5)),
                        "confidence_score": confidence,
                        "frequency_count": 1,
                        "pattern_keywords": emotional_keywords,
                        "emotional_associations": [emotion],
                        "context_requirements": {
                            "min_confidence": confidence * 0.8,
                            "mood_category": emotional_assessment.mood_assessment.category.value,
                            "stress_level": emotional_assessment.stress_assessment.level.value,
                        },
                    }
                    
                    await self.memory_importance_engine.save_importance_pattern(
                        user_id, "emotional_trigger", pattern_data
                    )
                    
                    logger.debug("Learned emotional trigger pattern for user %s: %s", user_id, emotion)
                    
        except (ValueError, KeyError) as e:
            logger.warning("Error learning emotional memory patterns: %s", e)

    async def _extract_emotional_context_keywords(
        self,
        content: str,
        emotional_assessment: Any
    ) -> list[str]:
        """Extract emotionally significant keywords from content"""
        try:
            content_lower = content.lower()
            
            # Emotional context keywords based on assessment
            emotion = emotional_assessment.emotional_prediction.predicted_emotion
            
            # Emotion-specific keyword sets
            emotion_keywords = {
                "happy": ["joy", "excited", "celebrate", "amazing", "wonderful", "great", "love"],
                "sad": ["upset", "down", "depressed", "hurt", "disappointed", "cry", "pain"],
                "angry": ["mad", "frustrated", "furious", "annoyed", "rage", "irritated"],
                "anxious": ["worried", "nervous", "scared", "afraid", "panic", "stress"],
                "grateful": ["thankful", "appreciate", "blessed", "grateful", "lucky"],
                "hopeful": ["optimistic", "looking forward", "excited about", "believe"],
            }
            
            # Extract relevant keywords
            relevant_keywords = []
            
            # Add emotion-specific keywords found in content
            if emotion in emotion_keywords:
                for keyword in emotion_keywords[emotion]:
                    if keyword in content_lower:
                        relevant_keywords.append(keyword)
            
            # Add general emotional words
            general_emotional_words = content_lower.split()
            emotional_word_list = [
                "feel", "feeling", "emotion", "heart", "soul", "mind",
                "hope", "dream", "fear", "worry", "love", "hate",
                "trust", "doubt", "confident", "insecure", "strong", "weak"
            ]
            
            for word in general_emotional_words:
                if word in emotional_word_list and word not in relevant_keywords:
                    relevant_keywords.append(word)
            
            return relevant_keywords[:5]  # Limit to top 5 most relevant
            
        except (ValueError, AttributeError) as e:
            logger.warning("Error extracting emotional keywords: %s", e)
            return []

    async def get_emotional_memory_insights(self, user_id: str) -> dict[str, Any]:
        """Get insights about user's emotional-memory patterns"""
        try:
            # Get user's emotional patterns
            patterns = await self.memory_importance_engine.load_user_importance_patterns(user_id)
            emotional_patterns = [p for p in patterns if p.get("pattern_type") == "emotional_trigger"]
            
            # Analyze patterns
            insights = {
                "total_emotional_patterns": len(emotional_patterns),
                "dominant_emotions": [],
                "emotional_triggers": [],
                "pattern_confidence_avg": 0.0,
                "emotional_memory_enhancement_active": len(emotional_patterns) > 0,
            }
            
            if emotional_patterns:
                # Find dominant emotions
                emotion_counts = {}
                confidence_sum = 0.0
                
                for pattern in emotional_patterns:
                    emotions = pattern.get("emotional_associations", [])
                    confidence = pattern.get("confidence_score", 0.0)
                    confidence_sum += confidence
                    
                    for emotion in emotions:
                        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                
                # Sort by frequency
                insights["dominant_emotions"] = sorted(
                    emotion_counts.items(), key=lambda x: x[1], reverse=True
                )[:3]
                
                insights["pattern_confidence_avg"] = confidence_sum / len(emotional_patterns)
                
                # Get top triggers
                insights["emotional_triggers"] = [
                    {
                        "pattern_name": p.get("pattern_name", ""),
                        "emotions": p.get("emotional_associations", []),
                        "confidence": p.get("confidence_score", 0.0),
                        "keywords": p.get("pattern_keywords", [])[:3],  # Top 3 keywords
                    }
                    for p in sorted(emotional_patterns, key=lambda x: x.get("confidence_score", 0), reverse=True)[:3]
                ]
            
            return insights
            
        except (ValueError, KeyError) as e:
            logger.warning("Error getting emotional memory insights: %s", e)
            return {
                "total_emotional_patterns": 0,
                "dominant_emotions": [],
                "emotional_triggers": [],
                "pattern_confidence_avg": 0.0,
                "emotional_memory_enhancement_active": False,
                "error": str(e),
            }