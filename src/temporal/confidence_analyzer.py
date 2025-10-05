"""
Confidence Analysis Module for WhisperEngine
Calculates confidence metrics from conversation data and AI components
"""

import logging
from typing import Dict, Any

from .temporal_intelligence_client import ConfidenceMetrics, RelationshipMetrics, ConversationQualityMetrics

logger = logging.getLogger(__name__)


class ConfidenceAnalyzer:
    """
    Analyzes conversation data to calculate confidence metrics for temporal tracking
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_confidence_metrics(
        self,
        ai_components: Dict[str, Any],
        memory_count: int = 0,
        processing_time_ms: float = 0.0  # Currently unused but reserved for future processing speed analysis
    ) -> ConfidenceMetrics:
        """
        Calculate confidence metrics from AI components and conversation data
        
        Args:
            ai_components: AI pipeline results (emotion, context, phase4, etc.)
            memory_count: Number of memories retrieved
            processing_time_ms: Processing time in milliseconds (reserved for future use)
            
        Returns:
            ConfidenceMetrics: Calculated confidence measurements
        """
        # Note: processing_time_ms reserved for future confidence calculations based on response speed
        _ = processing_time_ms  # Acknowledge parameter for future use
        
        # Extract emotion analysis confidence
        emotion_confidence = 0.5  # Default
        if 'emotion_analysis' in ai_components:
            emotion_data = ai_components['emotion_analysis']
            emotion_confidence = emotion_data.get('confidence', 0.5)
            
        # Extract context analysis confidence
        context_confidence = 0.5  # Default
        if 'context_analysis' in ai_components:
            context_data = ai_components['context_analysis']
            confidence_scores = context_data.get('confidence_scores', {})
            if confidence_scores:
                # Average of all context confidence scores
                context_confidence = sum(confidence_scores.values()) / len(confidence_scores)
                
        # Calculate user fact confidence based on memory availability
        user_fact_confidence = min(0.9, 0.3 + (memory_count * 0.1))  # More memories = higher confidence
        
        # Calculate relationship confidence from Phase 4 data
        relationship_confidence = 0.5  # Default
        if 'phase4_intelligence' in ai_components:
            phase4_data = ai_components['phase4_intelligence']
            # Use relationship level as confidence indicator
            relationship_level = phase4_data.get('relationship_level', 'acquaintance')
            relationship_mapping = {
                'stranger': 0.2,
                'acquaintance': 0.4,
                'friend': 0.7,
                'close_friend': 0.9
            }
            relationship_confidence = relationship_mapping.get(relationship_level, 0.5)
            
        # Calculate overall confidence as weighted average
        overall_confidence = (
            emotion_confidence * 0.25 +
            context_confidence * 0.25 +
            user_fact_confidence * 0.25 +
            relationship_confidence * 0.25
        )
        
        return ConfidenceMetrics(
            user_fact_confidence=user_fact_confidence,
            relationship_confidence=relationship_confidence,
            context_confidence=context_confidence,
            emotional_confidence=emotion_confidence,
            overall_confidence=overall_confidence
        )

    def calculate_relationship_metrics(
        self,
        ai_components: Dict[str, Any],
        conversation_history_length: int = 0
    ) -> RelationshipMetrics:
        """
        Calculate relationship progression metrics
        
        Args:
            ai_components: AI pipeline results
            conversation_history_length: Length of conversation history
            
        Returns:
            RelationshipMetrics: Calculated relationship measurements
        """
        
        # Base trust on emotion analysis and conversation length
        trust_level = 0.5  # Default baseline
        if 'emotion_analysis' in ai_components:
            emotion_data = ai_components['emotion_analysis']
            primary_emotion = emotion_data.get('primary_emotion', 'neutral')
            intensity = emotion_data.get('intensity', 0.5)
            
            # Positive emotions increase trust
            if primary_emotion in ['joy', 'surprise']:
                trust_level += intensity * 0.2
            elif primary_emotion in ['anger', 'fear', 'disgust']:
                trust_level -= intensity * 0.1
                
        # Longer conversations indicate higher trust
        trust_level += min(0.3, conversation_history_length * 0.02)
        trust_level = max(0.1, min(0.9, trust_level))  # Clamp to reasonable range
        
        # Affection based on emotional resonance and interaction quality
        affection_level = 0.4  # Default baseline
        if 'phase4_intelligence' in ai_components:
            phase4_data = ai_components['phase4_intelligence']
            interaction_type = phase4_data.get('interaction_type', 'general')
            
            # Personal interactions indicate higher affection
            if interaction_type in ['personal', 'emotional_support']:
                affection_level += 0.2
            elif interaction_type == 'general':
                affection_level += 0.1
                
        # Attunement based on context understanding and response appropriateness
        attunement_level = 0.5  # Default
        if 'context_analysis' in ai_components:
            context_data = ai_components['context_analysis']
            confidence_scores = context_data.get('confidence_scores', {})
            if confidence_scores:
                attunement_level = sum(confidence_scores.values()) / len(confidence_scores)
                
        # Interaction quality based on overall system performance
        interaction_quality = (trust_level + affection_level + attunement_level) / 3
        
        # Communication comfort based on conversation flow
        communication_comfort = 0.6  # Default baseline
        if conversation_history_length > 5:  # Established conversation
            communication_comfort = min(0.9, 0.5 + (conversation_history_length * 0.01))
            
        return RelationshipMetrics(
            trust_level=trust_level,
            affection_level=affection_level,
            attunement_level=attunement_level,
            interaction_quality=interaction_quality,
            communication_comfort=communication_comfort
        )

    def calculate_conversation_quality(
        self,
        ai_components: Dict[str, Any],
        response_length: int = 0,
        processing_time_ms: float = 0.0
    ) -> ConversationQualityMetrics:
        """
        Calculate conversation quality metrics
        
        Args:
            ai_components: AI pipeline results
            response_length: Length of bot response
            processing_time_ms: Time to process and respond
            
        Returns:
            ConversationQualityMetrics: Quality measurements
        """
        
        # Engagement score based on emotion and interaction type
        engagement_score = 0.5  # Default
        if 'emotion_analysis' in ai_components:
            emotion_data = ai_components['emotion_analysis']
            intensity = emotion_data.get('intensity', 0.5)
            engagement_score = max(0.3, min(0.9, intensity))
            
        # Satisfaction based on response appropriateness and length
        satisfaction_score = 0.6  # Default
        if 50 <= response_length <= 500:  # Optimal response length
            satisfaction_score = 0.8
        elif response_length > 500:
            satisfaction_score = 0.7  # Slightly verbose
        elif response_length < 50:
            satisfaction_score = 0.5  # Too brief
            
        # Natural flow based on processing time (faster = more natural)
        natural_flow_score = 0.7  # Default
        if processing_time_ms < 1000:  # Very fast
            natural_flow_score = 0.9
        elif processing_time_ms < 3000:  # Normal
            natural_flow_score = 0.8
        elif processing_time_ms > 5000:  # Slow
            natural_flow_score = 0.5
            
        # Emotional resonance from emotion analysis confidence
        emotional_resonance = 0.6  # Default
        if 'emotion_analysis' in ai_components:
            emotion_data = ai_components['emotion_analysis']
            emotional_resonance = emotion_data.get('confidence', 0.6)
            
        # Topic relevance based on context analysis
        topic_relevance = 0.7  # Default
        if 'context_analysis' in ai_components:
            context_data = ai_components['context_analysis']
            confidence_scores = context_data.get('confidence_scores', {})
            if confidence_scores:
                topic_relevance = sum(confidence_scores.values()) / len(confidence_scores)
                
        return ConversationQualityMetrics(
            engagement_score=engagement_score,
            satisfaction_score=satisfaction_score,
            natural_flow_score=natural_flow_score,
            emotional_resonance=emotional_resonance,
            topic_relevance=topic_relevance
        )


# Factory function
def create_confidence_analyzer() -> ConfidenceAnalyzer:
    """Create and return confidence analyzer instance"""
    return ConfidenceAnalyzer()