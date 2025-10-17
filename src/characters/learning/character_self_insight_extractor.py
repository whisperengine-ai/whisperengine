"""
Character Self-Insight Extractor

Converts LearningMoment objects detected during conversations into CharacterInsight 
database records for long-term persistence. Part of the Character Learning Persistence
system (Phase 6 of Memory Intelligence Convergence Roadmap).

This extractor bridges the real-time learning moment detection system with the
PostgreSQL-based character learning storage layer, handling:
- Mapping learning moment types to insight types
- Extracting triggers from conversation context
- Determining importance levels and confidence scores
- Deduplication and validation
"""

import logging
import re
from typing import List, Optional
from datetime import datetime

from src.characters.learning.character_learning_moment_detector import (
    LearningMoment,
    LearningMomentType
)
from src.characters.learning.character_insight_storage import CharacterInsight

logger = logging.getLogger(__name__)


class CharacterSelfInsightExtractor:
    """
    Extracts persistent insights from detected learning moments.
    
    Converts ephemeral LearningMoment objects (detected during conversation)
    into CharacterInsight database records (persisted for long-term learning).
    """
    
    # Mapping from LearningMomentType to database insight_type
    MOMENT_TO_INSIGHT_TYPE = {
        LearningMomentType.GROWTH_INSIGHT: "emotional_growth",
        LearningMomentType.USER_OBSERVATION: "user_pattern_recognition",
        LearningMomentType.MEMORY_SURPRISE: "memory_connection",
        LearningMomentType.KNOWLEDGE_EVOLUTION: "knowledge_evolution",
        LearningMomentType.EMOTIONAL_GROWTH: "emotional_growth",
        LearningMomentType.RELATIONSHIP_AWARENESS: "relationship_evolution"
    }
    
    def __init__(self, min_confidence: float = 0.6, min_importance: int = 4):
        """
        Initialize the extractor with quality thresholds.
        
        Args:
            min_confidence: Minimum confidence score to persist (0.0-1.0)
            min_importance: Minimum importance level to persist (1-10 scale)
        """
        self.min_confidence = min_confidence
        self.min_importance = min_importance
        logger.info("📝 CharacterSelfInsightExtractor initialized (min_confidence=%.2f, min_importance=%d)",
                   min_confidence, min_importance)
    
    def extract_insights_from_learning_moments(
        self,
        learning_moments: List[LearningMoment],
        character_id: int,
        conversation_context: Optional[str] = None
    ) -> List[CharacterInsight]:
        """
        Extract CharacterInsight records from detected LearningMoments.
        
        Args:
            learning_moments: List of detected learning moments from conversation
            character_id: Database ID of the character (from characters table)
            conversation_context: Optional summary of conversation that triggered insights
            
        Returns:
            List of CharacterInsight objects ready for storage
        """
        if not learning_moments:
            logger.debug("📝 No learning moments to extract insights from")
            return []
        
        insights = []
        for moment in learning_moments:
            try:
                insight = self._convert_moment_to_insight(
                    moment=moment,
                    character_id=character_id,
                    conversation_context=conversation_context
                )
                
                # Quality filtering
                if insight.confidence_score < self.min_confidence:
                    logger.debug("📝 Filtered out low-confidence insight: %.2f < %.2f",
                               insight.confidence_score, self.min_confidence)
                    continue
                
                if insight.importance_level < self.min_importance:
                    logger.debug("📝 Filtered out low-importance insight: %d < %d",
                               insight.importance_level, self.min_importance)
                    continue
                
                insights.append(insight)
                logger.info("📝 Extracted insight: [%s] %s (confidence=%.2f, importance=%d)",
                          insight.insight_type, insight.insight_content[:50], 
                          insight.confidence_score, insight.importance_level)
                
            except (ValueError, KeyError, AttributeError) as e:
                logger.error("📝 Failed to convert learning moment to insight: %s", e, exc_info=True)
                continue
        
        logger.info("📝 Extracted %d insights from %d learning moments", len(insights), len(learning_moments))
        return insights
    
    def _convert_moment_to_insight(
        self,
        moment: LearningMoment,
        character_id: int,
        conversation_context: Optional[str]
    ) -> CharacterInsight:
        """
        Convert a single LearningMoment to a CharacterInsight.
        
        Args:
            moment: Detected learning moment
            character_id: Character database ID
            conversation_context: Conversation summary
            
        Returns:
            CharacterInsight ready for storage
        """
        # Map moment type to insight type
        insight_type = self.MOMENT_TO_INSIGHT_TYPE.get(
            moment.moment_type,
            "general_learning"
        )
        
        # Extract insight content from suggested_response
        # Remove character-voice formatting to get core insight
        insight_content = self._extract_core_insight(moment.suggested_response)
        
        # Calculate importance level (1-10 scale) from confidence (0.0-1.0)
        importance_level = self._calculate_importance_level(moment)
        
        # Extract emotional valence from supporting data
        emotional_valence = self._extract_emotional_valence(moment)
        
        # Extract trigger keywords
        triggers = self._extract_triggers(moment)
        
        # Extract supporting evidence
        supporting_evidence = self._extract_supporting_evidence(moment)
        
        # Create CharacterInsight
        insight = CharacterInsight(
            character_id=character_id,
            insight_type=insight_type,
            insight_content=insight_content,
            confidence_score=moment.confidence,
            importance_level=importance_level,
            discovery_date=datetime.utcnow(),
            conversation_context=conversation_context or moment.trigger_content[:500],
            emotional_valence=emotional_valence,
            triggers=triggers,
            supporting_evidence=supporting_evidence
        )
        
        return insight
    
    def _extract_core_insight(self, suggested_response: str) -> str:
        """
        Extract the core learning insight from a character-voiced response.
        
        Examples:
            "I've noticed you really light up when we talk about marine biology!"
            -> "Shows enthusiasm when discussing marine biology"
            
            "You know, I feel like I'm becoming more confident in my explanations"
            -> "Growing confidence in educational explanations"
        """
        # Remove common conversational filler
        insight = suggested_response
        
        # Remove character voice patterns
        patterns_to_remove = [
            r"^(You know,?\s*)",
            r"^(I've noticed that\s*)",
            r"^(I feel like\s*)",
            r"^(It seems like\s*)",
            r"^(I think\s*)",
            r"^(Looking back,?\s*)",
            r"(!+)$",  # Remove excitement punctuation at end
        ]
        
        for pattern in patterns_to_remove:
            insight = re.sub(pattern, "", insight, flags=re.IGNORECASE)
        
        # Truncate to reasonable length
        if len(insight) > 500:
            insight = insight[:497] + "..."
        
        return insight.strip()
    
    def _calculate_importance_level(self, moment: LearningMoment) -> int:
        """
        Calculate importance level (1-10) from learning moment metadata.
        
        Factors:
        - Base confidence score (0.0-1.0 -> 1-10)
        - Moment type weight (some types more significant)
        - Supporting data richness
        """
        # Base score from confidence (scale 0.0-1.0 to 1-10)
        base_score = moment.confidence * 10
        
        # Type-based importance modifiers
        type_weights = {
            LearningMomentType.EMOTIONAL_GROWTH: 1.2,
            LearningMomentType.RELATIONSHIP_AWARENESS: 1.2,
            LearningMomentType.KNOWLEDGE_EVOLUTION: 1.1,
            LearningMomentType.GROWTH_INSIGHT: 1.1,
            LearningMomentType.USER_OBSERVATION: 1.0,
            LearningMomentType.MEMORY_SURPRISE: 0.9
        }
        
        weight = type_weights.get(moment.moment_type, 1.0)
        adjusted_score = base_score * weight
        
        # Supporting data bonus (+1 if rich supporting data)
        if moment.supporting_data and len(moment.supporting_data) >= 3:
            adjusted_score += 1
        
        # Clamp to 1-10 range
        importance = max(1, min(10, round(adjusted_score)))
        
        return importance
    
    def _extract_emotional_valence(self, moment: LearningMoment) -> Optional[float]:
        """
        Extract emotional valence (-1.0 to 1.0) from learning moment.
        
        Returns:
            Float in range -1.0 (negative) to 1.0 (positive), or None if unknown
        """
        supporting_data = moment.supporting_data or {}
        
        # Check for explicit emotional_valence
        if 'emotional_valence' in supporting_data:
            return supporting_data['emotional_valence']
        
        # Check for dominant emotion
        if 'dominant_emotion' in supporting_data:
            emotion_valence_map = {
                'joy': 0.8, 'happiness': 0.8, 'excitement': 0.7, 'love': 0.9,
                'interest': 0.5, 'curiosity': 0.5, 'surprise': 0.3,
                'neutral': 0.0,
                'sadness': -0.6, 'fear': -0.7, 'anger': -0.8, 'disgust': -0.7
            }
            emotion = supporting_data['dominant_emotion'].lower()
            return emotion_valence_map.get(emotion, 0.0)
        
        # Default: slightly positive (learning is generally positive)
        return 0.3
    
    def _extract_triggers(self, moment: LearningMoment) -> List[str]:
        """
        Extract keyword triggers that should activate this insight in future conversations.
        
        Examples:
            "Shows enthusiasm about marine biology" -> ["marine", "biology", "ocean"]
        """
        triggers = []
        
        # Extract from trigger_content
        if moment.trigger_content:
            # Simple keyword extraction (lowercase, remove punctuation)
            words = re.findall(r'\b\w{4,}\b', moment.trigger_content.lower())
            triggers.extend(words[:5])  # Limit to 5 keywords
        
        # Extract from supporting_data
        supporting_data = moment.supporting_data or {}
        if 'key_topics' in supporting_data:
            key_topics = supporting_data['key_topics']
            if isinstance(key_topics, list):
                triggers.extend([t.lower() for t in key_topics[:3]])
        
        # Deduplicate and limit
        unique_triggers = list(dict.fromkeys(triggers))  # Preserve order
        return unique_triggers[:8]  # Max 8 triggers
    
    def _extract_supporting_evidence(self, moment: LearningMoment) -> List[str]:
        """
        Extract supporting evidence quotes/examples for this insight.
        
        Returns:
            List of evidence strings (max 5)
        """
        evidence = []
        
        # Use trigger_content as primary evidence
        if moment.trigger_content:
            evidence.append(f"Trigger: {moment.trigger_content[:200]}")
        
        # Extract from supporting_data
        supporting_data = moment.supporting_data or {}
        
        if 'user_quote' in supporting_data:
            evidence.append(f"User: {supporting_data['user_quote'][:200]}")
        
        if 'conversation_examples' in supporting_data:
            examples = supporting_data['conversation_examples']
            if isinstance(examples, list):
                for ex in examples[:2]:  # Max 2 examples
                    evidence.append(f"Example: {str(ex)[:200]}")
        
        return evidence[:5]  # Max 5 pieces of evidence


def create_character_self_insight_extractor(
    min_confidence: float = 0.6,
    min_importance: int = 4
) -> CharacterSelfInsightExtractor:
    """
    Factory function to create a CharacterSelfInsightExtractor.
    
    Args:
        min_confidence: Minimum confidence score to persist (0.0-1.0)
        min_importance: Minimum importance level to persist (1-10)
        
    Returns:
        Configured CharacterSelfInsightExtractor instance
    """
    return CharacterSelfInsightExtractor(
        min_confidence=min_confidence,
        min_importance=min_importance
    )
