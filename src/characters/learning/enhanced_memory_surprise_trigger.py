"""
Enhanced Memory Surprise Triggers
WhisperEngine Character Learning Enhancement
Version: 1.0 - October 2025

Advanced vector-based memory surprise detection that leverages the existing
WhisperEngine Qdrant vector memory system for authentic conversation references
that genuinely surprise the character.

Features:
- Vector-based semantic similarity using existing Qdrant infrastructure
- Temporal memory pattern analysis
- Emotional context similarity detection
- Multi-dimensional memory surprise scoring
- Natural conversation flow integration
"""

import logging
import asyncio
import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class MemorySurpriseScore:
    """Detailed scoring for memory surprise opportunities."""
    overall_score: float
    semantic_similarity: float
    temporal_surprise: float
    emotional_resonance: float
    contextual_relevance: float
    supporting_evidence: Dict[str, Any]

@dataclass
class MemorySurprise:
    """Enhanced memory surprise with detailed context."""
    memory_id: str
    similarity_score: MemorySurpriseScore
    memory_content: str
    memory_timestamp: datetime
    trigger_phrase: str
    surprise_type: str  # "unexpected_connection", "distant_memory", "pattern_recognition", "emotional_echo"
    natural_integration: str
    character_response_template: str

class EnhancedMemorySurpriseTrigger:
    """
    Enhanced memory surprise detection using vector-based similarity and
    sophisticated pattern recognition for authentic character learning moments.
    """

    def __init__(self, memory_manager=None, character_intelligence_coordinator=None):
        """Initialize the enhanced memory surprise trigger system."""
        self.memory_manager = memory_manager
        self.character_intelligence_coordinator = character_intelligence_coordinator
        
        # Enhanced thresholds for different types of surprises - balanced approach
        self.semantic_similarity_threshold = 0.5   # Balanced threshold for semantic connections
        self.temporal_surprise_threshold = 0.4     # Balanced threshold for time-based surprises
        self.emotional_resonance_threshold = 0.5   # Balanced threshold for emotional connections
        self.overall_surprise_threshold = 0.4      # Balanced minimum for realistic detection
        
        # Temporal thresholds for surprise detection
        self.recent_memory_days = 3      # Memories within 3 days are "recent"
        self.distant_memory_days = 14    # Memories older than 14 days are "distant"
        self.pattern_memory_days = 7     # Look for patterns within 7 days

    async def detect_memory_surprises(self, 
                                    user_id: str,
                                    current_message: str,
                                    conversation_context: List[Dict[str, str]],
                                    character_name: str) -> List[MemorySurprise]:
        """
        Detect memory surprises using enhanced vector-based analysis.
        
        Returns a list of memory surprises ordered by surprise score.
        """
        surprises = []
        
        try:
            if not self.memory_manager:
                logger.debug("Memory manager not available for enhanced surprise detection")
                return surprises

            # Get relevant memories using vector similarity
            relevant_memories = await self._get_vector_similar_memories(
                user_id, current_message, character_name
            )
            
            if not relevant_memories:
                logger.debug("No relevant memories found for surprise detection")
                return surprises

            # Analyze each memory for surprise potential
            for memory in relevant_memories:
                surprise = await self._analyze_memory_surprise_potential(
                    memory, current_message, conversation_context, user_id
                )
                
                if surprise and surprise.similarity_score.overall_score >= self.overall_surprise_threshold:
                    surprises.append(surprise)

            # Sort by overall surprise score
            surprises.sort(key=lambda s: s.similarity_score.overall_score, reverse=True)
            
            # Limit to top 3 most surprising memories
            surprises = surprises[:3]
            
            logger.info("Enhanced memory surprise detection found %d surprises for user %s", 
                       len(surprises), user_id)
            
            return surprises
            
        except Exception as e:
            logger.error("Enhanced memory surprise detection failed: %s", str(e))
            return surprises

    async def _get_vector_similar_memories(self, 
                                         user_id: str, 
                                         current_message: str,
                                         character_name: str) -> List[Dict[str, Any]]:
        """Get memories using vector similarity search from existing Qdrant system."""
        try:
            if not self.memory_manager:
                logger.debug("Memory manager not available for vector similarity search")
                return []
                
            # Use existing memory manager vector search
            similar_memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=current_message,
                limit=15  # Get more candidates for analysis
            )
            
            # Filter to exclude very recent memories (avoid redundancy)
            filtered_memories = []
            cutoff_time = datetime.now()
            
            for memory in similar_memories:
                memory_time = memory.get('timestamp')
                if isinstance(memory_time, str):
                    try:
                        memory_time = datetime.fromisoformat(memory_time.replace('Z', '+00:00'))
                        # Convert to naive datetime for comparison
                        if memory_time.tzinfo is not None:
                            memory_time = memory_time.replace(tzinfo=None)
                    except:
                        continue
                elif not isinstance(memory_time, datetime):
                    continue
                    
                # Skip very recent memories to avoid immediate echoes (2 hours)
                time_diff = cutoff_time - memory_time
                if time_diff.total_seconds() > 2 * 3600:  # 2 hours in seconds
                    filtered_memories.append(memory)
            
            logger.debug("Found %d vector-similar memories for surprise analysis", len(filtered_memories))
            return filtered_memories
            
        except Exception as e:
            logger.error("Vector similarity memory retrieval failed: %s", str(e))
            return []

    async def _analyze_memory_surprise_potential(self, 
                                               memory: Dict[str, Any],
                                               current_message: str,
                                               conversation_context: List[Dict[str, str]],
                                               user_id: str) -> Optional[MemorySurprise]:
        """Analyze a specific memory for surprise potential."""
        try:
            memory_content = memory.get('content', '')
            memory_timestamp = memory.get('timestamp')
            
            if not memory_content:
                return None
                
            # Convert timestamp if needed
            if isinstance(memory_timestamp, str):
                try:
                    memory_timestamp = datetime.fromisoformat(memory_timestamp.replace('Z', '+00:00'))
                except:
                    memory_timestamp = datetime.now() - timedelta(days=1)
            elif not isinstance(memory_timestamp, datetime):
                memory_timestamp = datetime.now() - timedelta(days=1)

            # Calculate multi-dimensional surprise scores
            semantic_similarity = await self._calculate_vector_semantic_similarity(
                current_message, memory_content
            )
            
            temporal_surprise = self._calculate_temporal_surprise(memory_timestamp)
            
            emotional_resonance = await self._calculate_emotional_resonance(
                current_message, memory_content, memory
            )
            
            contextual_relevance = self._calculate_contextual_relevance(
                memory_content, conversation_context
            )
            
            # Calculate overall surprise score
            overall_score = (
                semantic_similarity * 0.35 +       # 35% weight on semantic similarity
                temporal_surprise * 0.25 +         # 25% weight on temporal surprise
                emotional_resonance * 0.25 +       # 25% weight on emotional resonance
                contextual_relevance * 0.15        # 15% weight on contextual relevance
            )
            
            # Create surprise score object
            surprise_score = MemorySurpriseScore(
                overall_score=overall_score,
                semantic_similarity=semantic_similarity,
                temporal_surprise=temporal_surprise,
                emotional_resonance=emotional_resonance,
                contextual_relevance=contextual_relevance,
                supporting_evidence={
                    'memory_age_days': (datetime.now() - memory_timestamp).days,
                    'memory_content_length': len(memory_content),
                    'similarity_confidence': memory.get('score', 0.0)
                }
            )
            
            # Determine surprise type
            surprise_type = self._determine_surprise_type(surprise_score, memory_timestamp)
            
            # Generate natural integration and response
            natural_integration, response_template = self._generate_surprise_response(
                memory_content, current_message, surprise_type, memory_timestamp
            )
            
            # Create memory surprise object
            memory_surprise = MemorySurprise(
                memory_id=memory.get('id', 'unknown'),
                similarity_score=surprise_score,
                memory_content=memory_content[:200],  # Truncate for display
                memory_timestamp=memory_timestamp,
                trigger_phrase=self._extract_trigger_phrase(current_message, memory_content),
                surprise_type=surprise_type,
                natural_integration=natural_integration,
                character_response_template=response_template
            )
            
            return memory_surprise
            
        except Exception as e:
            logger.error("Memory surprise analysis failed: %s", str(e))
            return None

    async def _calculate_vector_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using vector embeddings if available."""
        try:
            # Try to use existing fastembed system if available
            if self.memory_manager and hasattr(self.memory_manager, 'embedding_model'):
                embedding_model = self.memory_manager.embedding_model
                
                # Generate embeddings
                embedding1 = await embedding_model.embed([text1])
                embedding2 = await embedding_model.embed([text2])
                
                if embedding1 and embedding2:
                    # Calculate cosine similarity
                    import numpy as np
                    vec1 = np.array(embedding1[0])
                    vec2 = np.array(embedding2[0])
                    
                    # Cosine similarity
                    dot_product = np.dot(vec1, vec2)
                    norm1 = np.linalg.norm(vec1)
                    norm2 = np.linalg.norm(vec2)
                    
                    if norm1 > 0 and norm2 > 0:
                        similarity = dot_product / (norm1 * norm2)
                        return max(0.0, similarity)  # Ensure non-negative
            
            # Fallback to word overlap if vector embeddings not available
            return self._calculate_word_overlap_similarity(text1, text2)
            
        except Exception as e:
            logger.debug("Vector similarity calculation failed, using fallback: %s", str(e))
            return self._calculate_word_overlap_similarity(text1, text2)

    def _calculate_word_overlap_similarity(self, text1: str, text2: str) -> float:
        """Enhanced word overlap similarity calculation with semantic boosting."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Remove common stop words for better semantic matching
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'i', 'you', 'it', 'this', 'that', 'my', 'me'}
        words1_filtered = words1 - stop_words
        words2_filtered = words2 - stop_words
        
        # Calculate basic overlap
        intersection = words1_filtered.intersection(words2_filtered)
        union = words1_filtered.union(words2_filtered)
        basic_similarity = len(intersection) / len(union) if union else 0.0
        
        # Boost similarity for related concepts
        concept_pairs = [
            (['hiking', 'walk', 'nature', 'mountain', 'trail'], ['outdoor', 'exercise', 'adventure']),
            (['work', 'job', 'project', 'task'], ['stress', 'deadline', 'office', 'career']),
            (['travel', 'vacation', 'trip'], ['family', 'chat', 'conversation', 'planning']),
            (['food', 'restaurant', 'pasta'], ['dining', 'meal', 'eat'])
        ]
        
        concept_boost = 0.0
        for concept_group1, concept_group2 in concept_pairs:
            if any(word in words1_filtered for word in concept_group1) and any(word in words2_filtered for word in concept_group1):
                concept_boost += 0.3
            elif any(word in words1_filtered for word in concept_group1) and any(word in words2_filtered for word in concept_group2):
                concept_boost += 0.2
        
        # Combine basic similarity with concept boost
        enhanced_similarity = min(1.0, basic_similarity + concept_boost)
        
        return enhanced_similarity

    def _calculate_temporal_surprise(self, memory_timestamp: datetime) -> float:
        """Calculate surprise score based on temporal distance."""
        now = datetime.now()
        
        # Convert both to naive datetime for comparison
        if memory_timestamp.tzinfo is not None:
            memory_timestamp = memory_timestamp.replace(tzinfo=None)
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)
            
        time_diff = now - memory_timestamp
        days_ago = time_diff.days
        
        if days_ago < 1:
            # Very recent - low surprise
            return 0.2
        elif days_ago < self.recent_memory_days:
            # Recent - medium surprise
            return 0.5
        elif days_ago < self.distant_memory_days:
            # Medium distance - high surprise
            return 0.9
        else:
            # Very distant - maximum surprise
            return 1.0

    async def _calculate_emotional_resonance(self, 
                                           current_message: str, 
                                           memory_content: str,
                                           memory: Dict[str, Any]) -> float:
        """Calculate emotional resonance between current message and memory."""
        try:
            # Check if memory has emotional metadata
            memory_emotion = memory.get('emotion_data', {})
            current_emotion_strength = 0.5  # Default neutral
            memory_emotion_strength = 0.5   # Default neutral
            
            # Extract emotion strength if available
            if isinstance(memory_emotion, dict):
                memory_emotion_strength = memory_emotion.get('emotional_intensity', 0.5)
            
            # Simple emotional keyword matching (can be enhanced with RoBERTa)
            emotional_keywords = {
                'positive': ['happy', 'excited', 'joy', 'love', 'amazing', 'wonderful'],
                'negative': ['sad', 'angry', 'frustrated', 'disappointed', 'worried'],
                'neutral': ['interesting', 'think', 'consider', 'maybe', 'perhaps']
            }
            
            current_emotional_indicators = 0
            memory_emotional_indicators = 0
            
            current_lower = current_message.lower()
            memory_lower = memory_content.lower()
            
            for emotion_type, keywords in emotional_keywords.items():
                for keyword in keywords:
                    if keyword in current_lower:
                        current_emotional_indicators += 1
                    if keyword in memory_lower:
                        memory_emotional_indicators += 1
            
            # Calculate resonance based on emotional similarity
            if current_emotional_indicators > 0 and memory_emotional_indicators > 0:
                resonance = min(1.0, (current_emotional_indicators + memory_emotional_indicators) / 10)
            else:
                resonance = 0.3  # Low resonance for non-emotional content
            
            return resonance
            
        except Exception as e:
            logger.debug("Emotional resonance calculation failed: %s", str(e))
            return 0.4  # Default medium resonance

    def _calculate_contextual_relevance(self, 
                                      memory_content: str,
                                      conversation_context: List[Dict[str, str]]) -> float:
        """Calculate how relevant the memory is to the current conversation context."""
        try:
            if not conversation_context:
                return 0.5  # Medium relevance if no context
            
            # Get recent conversation topics
            recent_content = ' '.join([
                msg.get('content', '') for msg in conversation_context[-5:]
            ]).lower()
            
            memory_lower = memory_content.lower()
            
            # Extract key topics from both
            memory_words = set(memory_lower.split())
            context_words = set(recent_content.split())
            
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
            memory_words = memory_words - stop_words
            context_words = context_words - stop_words
            
            if not memory_words or not context_words:
                return 0.3
            
            # Calculate topic overlap
            overlap = memory_words.intersection(context_words)
            relevance = len(overlap) / len(memory_words.union(context_words))
            
            return min(1.0, relevance * 2)  # Boost relevance score
            
        except Exception as e:
            logger.debug("Contextual relevance calculation failed: %s", str(e))
            return 0.4

    def _determine_surprise_type(self, score: MemorySurpriseScore, memory_timestamp: datetime) -> str:
        """Determine the type of memory surprise based on scoring."""
        days_ago = (datetime.now() - memory_timestamp).days
        
        if score.semantic_similarity > 0.8 and days_ago < 7:
            return "unexpected_connection"
        elif days_ago > 14:
            return "distant_memory"
        elif score.emotional_resonance > 0.7:
            return "emotional_echo"
        else:
            return "pattern_recognition"

    def _generate_surprise_response(self, 
                                  memory_content: str,
                                  current_message: str,
                                  surprise_type: str,
                                  memory_timestamp: datetime) -> Tuple[str, str]:
        """Generate natural integration and response templates."""
        days_ago = (datetime.now() - memory_timestamp).days
        
        # Create preview of memory content
        memory_preview = memory_content[:80] + "..." if len(memory_content) > 80 else memory_content
        
        if surprise_type == "unexpected_connection":
            integration = "When the conversation naturally connects to the previous topic"
            response = f"Oh! This reminds me of something you mentioned recently about {memory_preview}"
            
        elif surprise_type == "distant_memory":
            integration = "When a distant memory becomes suddenly relevant"
            response = f"You know, this brings back something you told me {days_ago} days ago about {memory_preview}"
            
        elif surprise_type == "emotional_echo":
            integration = "When emotional resonance creates a memory connection"
            response = f"The way you're talking about this reminds me of when you shared {memory_preview}"
            
        else:  # pattern_recognition
            integration = "When recognizing a pattern in user behavior or interests"
            response = f"I'm noticing a pattern here - this connects to what you mentioned about {memory_preview}"
        
        return integration, response

    def _extract_trigger_phrase(self, current_message: str, memory_content: str) -> str:
        """Extract the specific phrase that triggered the memory connection."""
        current_words = current_message.lower().split()
        memory_words = memory_content.lower().split()
        
        # Find overlapping phrases
        for i in range(len(current_words) - 1):
            phrase = ' '.join(current_words[i:i+2])
            if phrase in memory_content.lower():
                return phrase
        
        # Fall back to single word matches
        overlap = set(current_words).intersection(set(memory_words))
        if overlap:
            return list(overlap)[0]
        
        return current_message[:30] + "..." if len(current_message) > 30 else current_message


def create_enhanced_memory_surprise_trigger(memory_manager=None, character_intelligence_coordinator=None):
    """Factory function to create enhanced memory surprise trigger."""
    return EnhancedMemorySurpriseTrigger(
        memory_manager=memory_manager,
        character_intelligence_coordinator=character_intelligence_coordinator
    )