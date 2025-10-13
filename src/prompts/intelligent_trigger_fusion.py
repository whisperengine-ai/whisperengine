"""
Intelligent Trigger Fusion System

Replaces 1980s keyword matching with multi-source intelligence fusion.
Uses data already available in ai_components and pipeline_result for 
performant decision making without additional queries.

Key Principles:
- Zero additional database queries - uses existing enriched data
- Multi-source signal fusion for intelligent decisions  
- Confidence scoring instead of binary on/off
- Context-aware trigger sensitivity
- Performance-first design
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TriggerSignalStrength(Enum):
    """Signal strength levels for trigger fusion"""
    NONE = 0.0
    WEAK = 0.3
    MODERATE = 0.6
    STRONG = 0.8
    VERY_STRONG = 1.0


@dataclass
class IntelligenceSignal:
    """Single intelligence signal with confidence and evidence"""
    signal_type: str
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    evidence: Dict[str, Any]
    source: str  # 'vector', 'graph', 'relationship', 'temporal'


@dataclass
class TriggerDecision:
    """Multi-source trigger decision result"""
    should_trigger: bool
    confidence: float  # Combined confidence from all sources
    primary_signals: List[IntelligenceSignal]
    trigger_reason: str
    context_factors: Dict[str, Any]


class IntelligentTriggerFusion:
    """
    🧠 Multi-Source Intelligence Trigger System
    
    Fuses signals from:
    - Vector emotional intelligence (RoBERTa data)
    - Knowledge graph relevance 
    - Relationship context
    - Conversation patterns
    
    All using data already available in ai_components - no new queries!
    """
    
    def __init__(self):
        # Confidence thresholds for different trigger types
        self.trigger_thresholds = {
            'emotional_guidance': 0.7,
            'expertise_activation': 0.6,
            'relationship_context': 0.5,
            'mode_switching': 0.8
        }
    
    async def analyze_emotional_trigger_signals(self, ai_components: Dict[str, Any], message_content: str) -> List[IntelligenceSignal]:
        """
        Analyze emotional trigger signals using existing RoBERTa data.
        Uses data already in ai_components - no new queries.
        """
        signals = []
        
        # Signal 1: RoBERTa Emotional Intelligence (already computed)
        emotion_data = ai_components.get('emotion_data', {})
        if emotion_data and isinstance(emotion_data, dict):
            roberta_confidence = emotion_data.get('roberta_confidence', 0.0)
            emotional_intensity = emotion_data.get('emotional_intensity', 0.0)
            emotion_variance = emotion_data.get('emotion_variance', 0.0)
            
            # Multi-emotion situations need guidance
            is_multi_emotion = emotion_data.get('is_multi_emotion', False)
            
            # Calculate emotional trigger strength
            if roberta_confidence > 0.8 and emotional_intensity > 0.7:
                strength = min(roberta_confidence * emotional_intensity, 1.0)
                
                signals.append(IntelligenceSignal(
                    signal_type='high_confidence_emotion',
                    strength=strength,
                    confidence=roberta_confidence,
                    evidence={
                        'emotional_intensity': emotional_intensity,
                        'emotion_variance': emotion_variance,
                        'is_multi_emotion': is_multi_emotion,
                        'primary_emotion': emotion_data.get('emotion', 'unknown')
                    },
                    source='vector'
                ))
        
        # Signal 2: Relationship Emotional Context (if available)
        relationship_data = ai_components.get('relationship_state', {})
        if relationship_data:
            emotional_connection = relationship_data.get('emotional_connection', 0.0)
            trust_level = relationship_data.get('trust_level', 0.0)
            
            # High emotional connection + trust = deeper emotional guidance appropriate
            if emotional_connection > 7.0 and trust_level > 6.0:
                strength = min((emotional_connection + trust_level) / 20.0, 1.0)
                
                signals.append(IntelligenceSignal(
                    signal_type='relationship_emotional_readiness',
                    strength=strength,
                    confidence=0.9,  # High confidence in relationship metrics
                    evidence={
                        'emotional_connection': emotional_connection,
                        'trust_level': trust_level,
                        'depth_score': relationship_data.get('depth_score', 0.0)
                    },
                    source='relationship'
                ))
        
        # Signal 3: Message Content Semantic Patterns (use existing analysis)
        conversation_intelligence = ai_components.get('conversation_intelligence', {})
        if conversation_intelligence:
            context_quality = conversation_intelligence.get('context_quality_score', 0.0)
            
            # High context quality suggests sophisticated conversation needing guidance
            if context_quality > 0.7:
                signals.append(IntelligenceSignal(
                    signal_type='sophisticated_context',
                    strength=context_quality,
                    confidence=0.8,
                    evidence={
                        'context_quality': context_quality,
                        'conversation_patterns': conversation_intelligence
                    },
                    source='conversation'
                ))
        
        return signals
    
    async def analyze_expertise_trigger_signals(self, ai_components: Dict[str, Any], message_content: str) -> List[IntelligenceSignal]:
        """
        Analyze expertise domain trigger signals using existing data.
        Smarter than keyword matching - uses semantic and contextual analysis.
        """
        signals = []
        
        # Signal 1: Use existing conversation intelligence for topic detection
        conversation_intelligence = ai_components.get('conversation_intelligence', {})
        if conversation_intelligence:
            # Look for topic evolution toward expertise areas
            topic_evolution = conversation_intelligence.get('topic_evolution')
            context_shift = conversation_intelligence.get('context_shift_detected', False)
            
            if topic_evolution and 'technical' in str(topic_evolution).lower():
                signals.append(IntelligenceSignal(
                    signal_type='technical_topic_evolution',
                    strength=0.8,
                    confidence=0.9,
                    evidence={
                        'topic_evolution': topic_evolution,
                        'context_shift': context_shift
                    },
                    source='conversation'
                ))
        
        # Signal 2: Emotional pattern suggesting learning/curiosity
        emotion_data = ai_components.get('emotion_data', {})
        if emotion_data:
            primary_emotion = emotion_data.get('emotion', '').lower()
            secondary_emotions = emotion_data.get('mixed_emotions', [])
            
            # Curiosity, interest, or analytical emotions suggest expertise need
            learning_emotions = ['curiosity', 'interest', 'surprise', 'analytical']
            if any(emotion in primary_emotion for emotion in learning_emotions):
                strength = emotion_data.get('roberta_confidence', 0.5)
                
                signals.append(IntelligenceSignal(
                    signal_type='learning_emotional_state',
                    strength=strength,
                    confidence=emotion_data.get('roberta_confidence', 0.5),
                    evidence={
                        'primary_emotion': primary_emotion,
                        'secondary_emotions': secondary_emotions,
                        'detected_learning_pattern': True
                    },
                    source='vector'
                ))
        
        # Signal 3: Use vector memory relevance (if available)
        if hasattr(ai_components, 'memory_context'):
            memory_context = ai_components.get('memory_context', {})
            # If previous conversations showed expertise interest, boost signal
            if memory_context.get('expertise_pattern_detected'):
                signals.append(IntelligenceSignal(
                    signal_type='historical_expertise_interest',
                    strength=0.7,
                    confidence=0.8,
                    evidence=memory_context,
                    source='memory'
                ))
        
        return signals
    
    async def fuse_trigger_signals(self, signals: List[IntelligenceSignal], trigger_type: str) -> TriggerDecision:
        """
        Fuse multiple intelligence signals into a single trigger decision.
        Uses weighted confidence scoring and evidence aggregation.
        """
        if not signals:
            return TriggerDecision(
                should_trigger=False,
                confidence=0.0,
                primary_signals=[],
                trigger_reason="No intelligence signals detected",
                context_factors={}
            )
        
        # Weight signals by source reliability and confidence
        source_weights = {
            'vector': 1.0,      # RoBERTa data is highly reliable
            'relationship': 0.9, # Relationship metrics are quite reliable  
            'conversation': 0.8, # Conversation analysis is good
            'memory': 0.7       # Memory patterns are helpful but less immediate
        }
        
        weighted_confidence = 0.0
        total_weight = 0.0
        primary_signals = []
        evidence_aggregate = {}
        
        for signal in signals:
            weight = source_weights.get(signal.source, 0.5)
            weighted_contribution = signal.strength * signal.confidence * weight
            
            weighted_confidence += weighted_contribution
            total_weight += weight
            
            # Collect strong signals as primary
            if signal.strength > 0.6 and signal.confidence > 0.7:
                primary_signals.append(signal)
            
            # Aggregate evidence
            evidence_aggregate[f"{signal.source}_{signal.signal_type}"] = signal.evidence
        
        # Normalize confidence
        final_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0
        
        # Decision threshold
        threshold = self.trigger_thresholds.get(trigger_type, 0.6)
        should_trigger = final_confidence >= threshold
        
        # Generate reason
        if should_trigger:
            strong_signals = [s.signal_type for s in primary_signals]
            trigger_reason = f"Multi-source confidence {final_confidence:.2f} from: {', '.join(strong_signals)}"
        else:
            trigger_reason = f"Insufficient confidence {final_confidence:.2f} (threshold: {threshold})"
        
        return TriggerDecision(
            should_trigger=should_trigger,
            confidence=final_confidence,
            primary_signals=primary_signals,
            trigger_reason=trigger_reason,
            context_factors=evidence_aggregate
        )
    
    async def should_trigger_emotional_guidance(self, ai_components: Dict[str, Any], message_content: str) -> TriggerDecision:
        """
        Intelligent decision for emotional trigger activation.
        Uses multi-source fusion instead of keyword matching.
        """
        signals = await self.analyze_emotional_trigger_signals(ai_components, message_content)
        return await self.fuse_trigger_signals(signals, 'emotional_guidance')
    
    async def should_trigger_expertise_domain(self, ai_components: Dict[str, Any], message_content: str) -> TriggerDecision:
        """
        Intelligent decision for expertise domain activation.
        Uses semantic analysis instead of simple keyword matching.
        """
        signals = await self.analyze_expertise_trigger_signals(ai_components, message_content)
        return await self.fuse_trigger_signals(signals, 'expertise_activation')
    
    async def should_prioritize_relationship_context(self, ai_components: Dict[str, Any], message_content: str, mentioned_entities: Optional[List[str]] = None) -> TriggerDecision:
        """
        Intelligent decision for relationship context prioritization.
        Uses entity analysis and relationship strength fusion.
        """
        signals = []
        
        # Use existing relationship data
        relationship_data = ai_components.get('relationship_state', {})
        if relationship_data:
            depth_score = relationship_data.get('depth_score', 0.0)
            trust_level = relationship_data.get('trust_level', 0.0)
            
            # High trust + entity mentions = strong relationship context signal
            if mentioned_entities and depth_score > 50.0:
                # Boost for entity mentions in context
                entity_boost = min(len(mentioned_entities) * 0.2, 0.6)
                strength = min((depth_score / 100.0) + entity_boost, 1.0)
                
                signals.append(IntelligenceSignal(
                    signal_type='contextual_relationship_relevance',
                    strength=strength,
                    confidence=0.9,
                    evidence={
                        'depth_score': depth_score,
                        'trust_level': trust_level,
                        'mentioned_entities': mentioned_entities,
                        'entity_boost': entity_boost
                    },
                    source='relationship'
                ))
        
        return await self.fuse_trigger_signals(signals, 'relationship_context')


# Global instance for efficient reuse
_intelligent_trigger_fusion = None

def get_intelligent_trigger_fusion() -> IntelligentTriggerFusion:
    """Get the global intelligent trigger fusion instance."""
    global _intelligent_trigger_fusion
    if _intelligent_trigger_fusion is None:
        _intelligent_trigger_fusion = IntelligentTriggerFusion()
    return _intelligent_trigger_fusion