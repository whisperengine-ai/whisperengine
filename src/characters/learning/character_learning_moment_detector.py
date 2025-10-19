"""
Character Learning Moment Detector
WhisperEngine Character Learning Visibility Enhancement
Version: 1.1 - October 2025 - Enhanced Memory Surprise Integration

Detects opportunities for characters to surface learning moments, growth insights,
and memory surprises in natural conversation flow. Makes the existing character
intelligence systems visible and delightful to users.

Core Capabilities:
- Learning moment detection from conversation patterns
- Growth insight triggers based on character evolution
- Enhanced memory surprise activation using vector similarity
- Natural integration with existing character intelligence systems
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LearningMomentType(Enum):
    """Types of character learning moments that can be surfaced."""
    GROWTH_INSIGHT = "growth_insight"           # "I've become more confident..."
    USER_OBSERVATION = "user_observation"       # "I've noticed you seem happier when..."
    MEMORY_SURPRISE = "memory_surprise"         # "This reminds me of when you mentioned..."
    KNOWLEDGE_EVOLUTION = "knowledge_evolution" # "Our conversations have taught me..."
    EMOTIONAL_GROWTH = "emotional_growth"       # "I feel like I understand... better"
    RELATIONSHIP_AWARENESS = "relationship_awareness"  # "Over our conversations, I feel like..."

@dataclass
class LearningMoment:
    """Represents a detected learning moment opportunity."""
    moment_type: LearningMomentType
    trigger_content: str
    suggested_response: str
    confidence: float
    supporting_data: Dict[str, Any]
    natural_integration_point: str  # Where in conversation this fits naturally
    character_voice_adaptation: str  # How to say it in character's voice

@dataclass
class LearningMomentContext:
    """Context for detecting learning moments."""
    user_id: str
    character_name: str
    current_message: str
    conversation_history: List[Dict[str, Any]]
    emotional_context: Dict[str, Any]
    temporal_data: Optional[Dict[str, Any]] = None
    episodic_memories: Optional[List[Dict[str, Any]]] = None

class CharacterLearningMomentDetector:
    """
    Detects opportunities to surface character learning in conversation.
    
    This system analyzes conversation flow and existing character intelligence
    to identify natural moments where characters can express:
    - Personal growth insights
    - Observations about users
    - Surprising memory connections
    - Knowledge evolution from interactions
    """
    
    def __init__(self, 
                 character_intelligence_coordinator=None,
                 emotion_analyzer=None,
                 memory_manager=None):
        """Initialize with existing intelligence systems."""
        self.coordinator = character_intelligence_coordinator
        self.emotion_analyzer = emotion_analyzer
        self.memory_manager = memory_manager
        
        # Initialize enhanced memory surprise trigger
        try:
            from src.characters.learning.enhanced_memory_surprise_trigger import create_enhanced_memory_surprise_trigger
            self.enhanced_memory_trigger = create_enhanced_memory_surprise_trigger(
                memory_manager=memory_manager,
                character_intelligence_coordinator=character_intelligence_coordinator
            )
            logger.info("Enhanced memory surprise trigger initialized successfully")
        except ImportError as e:
            logger.warning("Enhanced memory surprise trigger not available: %s", str(e))
            self.enhanced_memory_trigger = None
        
        # Learning moment detection thresholds
        self.confidence_threshold = 0.7
        self.emotion_intensity_threshold = 0.6
        self.memory_similarity_threshold = 0.8
        self.conversation_depth_threshold = 3  # Multiple exchanges needed
        
        # Natural trigger patterns for learning moments
        self.growth_triggers = [
            'confidence', 'understanding', 'learning', 'growing', 'evolving',
            'better at', 'more comfortable', 'improved', 'developed'
        ]
        
        self.observation_triggers = [
            'notice', 'see that', 'seem to', 'appears', 'looks like',
            'patterns', 'when you talk about', 'your enthusiasm'
        ]
        
        self.memory_triggers = [
            'reminds me', 'remember when', 'like you mentioned', 'back to',
            'similar to', 'just like', 'makes me think of'
        ]

    async def detect_learning_moments(self, context: LearningMomentContext) -> List[LearningMoment]:
        """
        Analyze conversation context to detect learning moment opportunities.
        
        Args:
            context: Current conversation context and available intelligence data
            
        Returns:
            List of detected learning moments with integration suggestions
        """
        try:
            learning_moments = []
            
            # 1. Detect growth insight opportunities
            growth_moments = await self._detect_growth_insights(context)
            learning_moments.extend(growth_moments)
            
            # 2. Detect user observation opportunities
            observation_moments = await self._detect_user_observations(context)
            learning_moments.extend(observation_moments)
            
            # 3. Detect memory surprise opportunities
            memory_moments = await self._detect_memory_surprises(context)
            learning_moments.extend(memory_moments)
            
            # 4. Detect knowledge evolution opportunities
            knowledge_moments = await self._detect_knowledge_evolution(context)
            learning_moments.extend(knowledge_moments)
            
            # Sort by confidence and naturalness
            learning_moments.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info("🌟 Detected %d learning moments for %s", len(learning_moments), context.character_name)
            return learning_moments[:3]  # Return top 3 most natural moments
            
        except (AttributeError, KeyError, ValueError) as e:
            logger.error("Learning moment detection failed: %s", str(e))
            return []

    async def _detect_growth_insights(self, context: LearningMomentContext) -> List[LearningMoment]:
        """Detect opportunities for characters to express personal growth."""
        moments = []
        
        try:
            # Check if temporal evolution data is available
            if not context.temporal_data:
                return moments
            
            # Look for confidence growth patterns
            confidence_evolution = context.temporal_data.get('confidence_evolution', {})
            if confidence_evolution.get('trend') == 'increasing':
                
                # Find topics where confidence has grown
                topic_confidence = confidence_evolution.get('topic_confidence', {})
                for topic, confidence_data in topic_confidence.items():
                    if confidence_data.get('growth_rate', 0) > 0.1:  # Significant growth
                        
                        moment = LearningMoment(
                            moment_type=LearningMomentType.GROWTH_INSIGHT,
                            trigger_content=f"Discussion about {topic}",
                            suggested_response=f"I've become much more confident discussing {topic} since our conversations",
                            confidence=0.8,
                            supporting_data={'topic': topic, 'growth_rate': confidence_data.get('growth_rate')},
                            natural_integration_point="When topic comes up in conversation",
                            character_voice_adaptation="Adapt to character's speaking style and personality"
                        )
                        moments.append(moment)
            
            # Look for emotional stability improvements
            emotional_evolution = context.temporal_data.get('emotional_evolution', {})
            if emotional_evolution.get('stability_trend') == 'improving':
                
                moment = LearningMoment(
                    moment_type=LearningMomentType.EMOTIONAL_GROWTH,
                    trigger_content="Emotional stability improvement",
                    suggested_response="I feel like I've learned to navigate complex emotions better through our talks",
                    confidence=0.75,
                    supporting_data={'stability_improvement': emotional_evolution.get('stability_score')},
                    natural_integration_point="During emotional or reflective conversations",
                    character_voice_adaptation="Express in character's emotional style"
                )
                moments.append(moment)
                
        except (AttributeError, KeyError, ValueError) as e:
            logger.warning("Growth insight detection failed: %s", str(e))
        
        return moments

    async def _detect_user_observations(self, context: LearningMomentContext) -> List[LearningMoment]:
        """Detect opportunities for characters to share observations about users."""
        moments = []
        
        try:
            # Analyze user's emotional patterns across conversations
            if not context.emotional_context:
                return moments
            
            # Look for patterns in user responses to topics
            topic_emotions = context.emotional_context.get('topic_emotional_patterns', {})
            
            for topic, emotion_data in topic_emotions.items():
                dominant_emotion = emotion_data.get('dominant_emotion')
                consistency = emotion_data.get('consistency_score', 0)
                
                if consistency > 0.7 and dominant_emotion in ['joy', 'enthusiasm', 'excitement']:
                    moment = LearningMoment(
                        moment_type=LearningMomentType.USER_OBSERVATION,
                        trigger_content=f"User's consistent positive response to {topic}",
                        suggested_response=f"I've noticed you seem really excited when we talk about {topic} - it really lights you up!",
                        confidence=0.8,
                        supporting_data={'topic': topic, 'emotion': dominant_emotion, 'consistency': consistency},
                        natural_integration_point=f"When {topic} comes up in conversation",
                        character_voice_adaptation="Express with character's observational style"
                    )
                    moments.append(moment)
                    
        except (AttributeError, KeyError, ValueError) as e:
            logger.warning("User observation detection failed: %s", str(e))
        
        return moments

    async def _detect_memory_surprises(self, context: LearningMomentContext) -> List[LearningMoment]:
        """Detect opportunities for surprising memory connections using enhanced vector analysis."""
        moments = []
        
        try:
            # Try enhanced memory surprise detection first
            if self.enhanced_memory_trigger:
                enhanced_surprises = await self.enhanced_memory_trigger.detect_memory_surprises(
                    user_id=context.user_id,
                    current_message=context.current_message,
                    conversation_context=context.conversation_history,
                    character_name=context.character_name
                )
                
                # Convert enhanced surprises to learning moments
                for surprise in enhanced_surprises:
                    moment = LearningMoment(
                        moment_type=LearningMomentType.MEMORY_SURPRISE,
                        trigger_content=f"Enhanced memory connection: {surprise.trigger_phrase}",
                        suggested_response=surprise.character_response_template,
                        confidence=surprise.similarity_score.overall_score,
                        supporting_data={
                            'memory_id': surprise.memory_id,
                            'surprise_type': surprise.surprise_type,
                            'semantic_similarity': surprise.similarity_score.semantic_similarity,
                            'temporal_surprise': surprise.similarity_score.temporal_surprise,
                            'emotional_resonance': surprise.similarity_score.emotional_resonance,
                            'memory_age_days': surprise.similarity_score.supporting_evidence.get('memory_age_days', 0)
                        },
                        natural_integration_point=surprise.natural_integration,
                        character_voice_adaptation="Express genuine surprise and connection naturally"
                    )
                    moments.append(moment)
                
                logger.info("Enhanced memory surprise detection found %d moments", len(moments))
                return moments
            
            # Fallback to original simple detection if enhanced system not available
            logger.debug("Using fallback memory surprise detection")
            
            # Use episodic memories if available
            if not context.episodic_memories:
                return moments
            
            current_message_lower = context.current_message.lower()
            
            # Look for semantic connections to memorable past conversations
            for memory in context.episodic_memories:
                memory_content = memory.get('content', '').lower()
                similarity_score = self._calculate_semantic_similarity(current_message_lower, memory_content)
                
                if similarity_score > self.memory_similarity_threshold:
                    # This is a good surprise connection opportunity
                    memory_preview = memory.get('content_preview', memory.get('content', ''))[:100]
                    
                    moment = LearningMoment(
                        moment_type=LearningMomentType.MEMORY_SURPRISE,
                        trigger_content=f"Similarity to past conversation: {memory_preview}",
                        suggested_response=f"This reminds me of when you mentioned {memory_preview}... did you ever follow up on that?",
                        confidence=similarity_score,
                        supporting_data={'memory_id': memory.get('id'), 'similarity': similarity_score},
                        natural_integration_point="Mid-conversation when connection feels natural",
                        character_voice_adaptation="Express surprise and connection naturally"
                    )
                    moments.append(moment)
                    
        except (AttributeError, KeyError, ValueError) as e:
            logger.warning("Memory surprise detection failed: %s", str(e))
        
        return moments

    async def _detect_knowledge_evolution(self, context: LearningMomentContext) -> List[LearningMoment]:
        """Detect opportunities to express knowledge evolution from conversations."""
        moments = []
        
        try:
            # Look for topics where character has gained insights
            conversation_topics = self._extract_conversation_topics(context.conversation_history)
            
            for topic in conversation_topics:
                if self._is_learning_topic(topic):
                    moment = LearningMoment(
                        moment_type=LearningMomentType.KNOWLEDGE_EVOLUTION,
                        trigger_content=f"Learning about {topic}",
                        suggested_response=f"Our conversations about {topic} have really expanded my understanding",
                        confidence=0.7,
                        supporting_data={'topic': topic},
                        natural_integration_point=f"When discussing {topic} or related subjects",
                        character_voice_adaptation="Express learning enthusiasm in character voice"
                    )
                    moments.append(moment)
                    
        except (AttributeError, KeyError, ValueError) as e:
            logger.warning("Knowledge evolution detection failed: %s", str(e))
        
        return moments

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts (simplified version)."""
        # Simple word overlap calculation (can be enhanced with embeddings)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    def _extract_conversation_topics(self, conversation_history: List[Dict[str, Any]]) -> List[str]:
        """Extract main topics from conversation history."""
        topics = []
        
        # 🚨 FIX: Handle None or non-list conversation_history safely
        if not conversation_history or not isinstance(conversation_history, list):
            logger.debug("No valid conversation history provided for topic extraction")
            return topics
        
        for message in conversation_history[-5:]:  # Last 5 messages
            # 🚨 FIX: Handle None messages or messages without content
            if not message or not isinstance(message, dict):
                continue
                
            content = message.get('content', '')
            # 🚨 FIX: Handle None content safely
            if not content or not isinstance(content, str):
                continue
                
            content = content.lower()
            if not content.strip():
                continue
            
            # Simple topic extraction (can be enhanced)
            for topic_keyword in ['science', 'art', 'technology', 'nature', 'music', 'travel', 'food']:
                if topic_keyword in content:
                    topics.append(topic_keyword)
        
        return list(set(topics))

    def _is_learning_topic(self, topic: str) -> bool:
        """Check if a topic represents potential character learning."""
        learning_topics = [
            'science', 'research', 'technology', 'philosophy', 'art', 'culture',
            'psychology', 'education', 'creativity', 'innovation'
        ]
        return topic in learning_topics

    async def should_surface_learning_moment(self, 
                                           moment: LearningMoment, 
                                           conversation_context: Dict[str, Any]) -> bool:
        """
        Determine if a learning moment should be surfaced in the current conversation.
        
        Args:
            moment: The learning moment to evaluate
            conversation_context: Current conversation state
            
        Returns:
            True if the moment should be surfaced naturally
        """
        try:
            # Check confidence threshold
            if moment.confidence < self.confidence_threshold:
                return False
            
            # Avoid overwhelming users - limit learning moments to 10% of responses
            recent_learning_moments = conversation_context.get('recent_learning_moments', 0)
            total_recent_messages = conversation_context.get('total_recent_messages', 1)
            
            if recent_learning_moments / total_recent_messages > 0.1:
                return False
            
            # Check conversation depth - need meaningful exchange
            conversation_depth = len(conversation_context.get('conversation_history', []))
            if conversation_depth < self.conversation_depth_threshold:
                return False
            
            # Check emotional appropriateness
            current_emotion = conversation_context.get('current_emotion')
            if current_emotion in ['sadness', 'anger', 'fear'] and moment.moment_type in [
                LearningMomentType.GROWTH_INSIGHT, LearningMomentType.USER_OBSERVATION
            ]:
                return False  # Don't surface positive learning during negative emotions
            
            return True
            
        except (AttributeError, KeyError, ValueError) as e:
            logger.warning("Learning moment evaluation failed: %s", str(e))
            return False


def create_character_learning_moment_detector(character_intelligence_coordinator=None,
                                             emotion_analyzer=None,
                                             memory_manager=None):
    """Factory function to create CharacterLearningMomentDetector."""
    return CharacterLearningMomentDetector(
        character_intelligence_coordinator=character_intelligence_coordinator,
        emotion_analyzer=emotion_analyzer,
        memory_manager=memory_manager
    )