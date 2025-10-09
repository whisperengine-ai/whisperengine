"""
Character Vector Episodic Intelligence System

Core system for extracting episodic memories from existing RoBERTa-scored vector conversations.
Enables characters to naturally reference memorable moments from their past interactions.

Based on analysis findings:
- Focus on roberta_confidence > 0.8 memories
- Use emotional_intensity > 0.7 for moment selection  
- Multi-emotion moments provide richer context
- High-potential characters: Sophia (74%), Jake (68%), Marcus (69%)
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

@dataclass
class EpisodicMemory:
    """Represents a memorable moment from past conversations"""
    id: str
    content: str
    user_id: str
    timestamp: datetime
    primary_emotion: str
    roberta_confidence: float
    emotional_intensity: float
    is_multi_emotion: bool
    mixed_emotions: List[Tuple[str, float]]
    memorable_score: float
    context_type: str  # 'personal_sharing', 'creative_moment', 'expertise', 'vulnerability'
    content_preview: str
    bot_response: Optional[str] = None

@dataclass
class CharacterInsight:
    """Character self-insights derived from conversation patterns"""
    insight_type: str  # 'emotional_pattern', 'topic_enthusiasm', 'personality_trait'
    description: str
    confidence: float
    supporting_memories: List[str]  # Memory IDs
    first_observed: datetime
    reinforcement_count: int

class CharacterVectorEpisodicIntelligence:
    """
    Extracts episodic memories and character insights from existing vector conversations
    
    Core functionality:
    - detect_memorable_moments_from_vector_patterns()
    - extract_character_insights_from_vector_patterns() 
    - get_episodic_memory_for_response_enhancement()
    """
    
    def __init__(self, qdrant_client: Optional[QdrantClient] = None):
        self.qdrant_client = qdrant_client or QdrantClient(
            host=os.getenv('QDRANT_HOST', 'localhost'),
            port=int(os.getenv('QDRANT_PORT', '6334')),
            timeout=30
        )
        self.memorable_threshold = 0.8  # RoBERTa confidence threshold
        self.emotion_intensity_threshold = 0.7
        self.multi_emotion_bonus = 0.2
        self.personal_keywords = [
            'feel', 'think', 'remember', 'love', 'hate', 'excited', 'worried', 
            'hope', 'dream', 'fear', 'grateful', 'proud', 'disappointed', 'amazed'
        ]
    
    async def detect_memorable_moments_from_vector_patterns(
        self, 
        collection_name: str, 
        user_id: Optional[str] = None,
        limit: int = 50,
        days_back: int = 90
    ) -> List[EpisodicMemory]:
        """
        Detect memorable moments using existing RoBERTa emotional intelligence data
        
        Args:
            collection_name: Bot-specific Qdrant collection
            user_id: Optional filter for specific user
            limit: Maximum memorable moments to return
            days_back: How far back to search for memories
            
        Returns:
            List of EpisodicMemory objects sorted by memorable score
        """
        try:
            # Build search filters
            must_conditions = []
            
            if user_id:
                must_conditions.append(
                    models.FieldCondition(
                        key="user_id", 
                        match=models.MatchValue(value=user_id)
                    )
                )
            
            # Time filter for recent memories
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Get recent memories with high RoBERTa confidence
            scroll_filter = models.Filter(
                must=must_conditions
            ) if must_conditions else None
            
            # Scroll through memories to find memorable candidates
            memorable_memories = []
            scroll_result = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=scroll_filter,
                limit=1000,  # Large batch to analyze
                with_payload=True,
                with_vectors=False
            )
            
            points = scroll_result[0]
            
            if not points:
                logger.info(f"No memories found in collection {collection_name}")
                return []
            
            # Analyze each memory for memorable potential
            for point in points:
                memory = await self._evaluate_memory_memorability(point)
                if memory and memory.memorable_score >= 3.0:  # Threshold from analysis
                    memorable_memories.append(memory)
            
            # Sort by memorable score and return top candidates
            memorable_memories.sort(key=lambda m: m.memorable_score, reverse=True)
            
            logger.info(f"Found {len(memorable_memories)} memorable moments from {len(points)} total memories")
            return memorable_memories[:limit]
            
        except Exception as e:
            logger.error(f"Error detecting memorable moments: {e}")
            return []
    
    async def _evaluate_memory_memorability(self, point) -> Optional[EpisodicMemory]:
        """Evaluate a single memory point for memorability using analysis criteria"""
        try:
            payload = point.payload
            if not payload:
                return None
            
            # Extract required fields
            content = payload.get('content', '')
            user_id = payload.get('user_id', '')
            roberta_confidence = payload.get('roberta_confidence', 0.0)
            emotional_intensity = payload.get('emotional_intensity', 0.0)
            primary_emotion = payload.get('primary_emotion', 'neutral')
            is_multi_emotion = payload.get('is_multi_emotion', False)
            mixed_emotions = payload.get('mixed_emotions', [])
            
            # Parse timestamp
            timestamp_str = payload.get('timestamp', '')
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
            
            # Calculate memorable score using analysis criteria
            score = 0.0
            context_type = 'general'
            
            # High RoBERTa confidence (>0.8) - Primary indicator
            if isinstance(roberta_confidence, (int, float)) and roberta_confidence > self.memorable_threshold:
                score += 2.0
            
            # High emotional intensity (>0.7) - Strong emotional moments
            if isinstance(emotional_intensity, (int, float)) and emotional_intensity > self.emotion_intensity_threshold:
                score += 2.0
            
            # Multi-emotion complexity - Richer emotional context
            if is_multi_emotion:
                score += 1.0
            
            # Rich content length - Substantial conversations
            if len(str(content)) > 200:
                score += 1.0
            
            # Personal information sharing - Vulnerable/meaningful moments
            content_lower = str(content).lower()
            if any(keyword in content_lower for keyword in self.personal_keywords):
                score += 1.0
                context_type = 'personal_sharing'
            
            # Creative/analytical content - Intellectual engagement
            creative_keywords = ['create', 'imagine', 'design', 'build', 'solve', 'analyze']
            if any(keyword in content_lower for keyword in creative_keywords):
                score += 0.5
                if context_type == 'general':
                    context_type = 'creative_moment'
            
            # Professional expertise sharing - Domain knowledge
            expertise_keywords = ['research', 'study', 'analysis', 'experience', 'professional']
            if any(keyword in content_lower for keyword in expertise_keywords):
                score += 0.5
                if context_type == 'general':
                    context_type = 'expertise'
            
            # Skip if score too low
            if score < 3.0:
                return None
            
            # Create EpisodicMemory object
            return EpisodicMemory(
                id=str(point.id),
                content=content,
                user_id=user_id,
                timestamp=timestamp,
                primary_emotion=primary_emotion,
                roberta_confidence=roberta_confidence,
                emotional_intensity=emotional_intensity,
                is_multi_emotion=is_multi_emotion,
                mixed_emotions=mixed_emotions,
                memorable_score=score,
                context_type=context_type,
                content_preview=content[:150] + '...' if len(content) > 150 else content,
                bot_response=payload.get('bot_response', '')
            )
            
        except Exception as e:
            logger.error(f"Error evaluating memory memorability: {e}")
            return None
    
    async def extract_character_insights_from_vector_patterns(
        self, 
        collection_name: str,
        memorable_memories: List[EpisodicMemory]
    ) -> List[CharacterInsight]:
        """
        Extract character self-insights from emotional patterns in memorable moments
        
        Args:
            collection_name: Bot-specific collection name
            memorable_memories: List of memorable moments to analyze
            
        Returns:
            List of CharacterInsight objects
        """
        try:
            insights = []
            
            if not memorable_memories:
                return insights
            
            # Analyze emotional patterns
            emotion_patterns = self._analyze_emotional_patterns(memorable_memories)
            insights.extend(emotion_patterns)
            
            # Analyze topic enthusiasm patterns
            topic_patterns = self._analyze_topic_enthusiasm(memorable_memories)
            insights.extend(topic_patterns)
            
            # Analyze personality trait patterns
            personality_patterns = self._analyze_personality_traits(memorable_memories)
            insights.extend(personality_patterns)
            
            # Sort by confidence
            insights.sort(key=lambda i: i.confidence, reverse=True)
            
            logger.info(f"Extracted {len(insights)} character insights from {len(memorable_memories)} memorable moments")
            return insights[:10]  # Top 10 insights
            
        except Exception as e:
            logger.error(f"Error extracting character insights: {e}")
            return []
    
    def _analyze_emotional_patterns(self, memories: List[EpisodicMemory]) -> List[CharacterInsight]:
        """Analyze dominant emotional patterns in character responses"""
        emotion_counts = defaultdict(int)
        emotion_intensities = defaultdict(list)
        
        for memory in memories:
            if memory.primary_emotion and memory.primary_emotion != 'neutral':
                emotion_counts[memory.primary_emotion] += 1
                emotion_intensities[memory.primary_emotion].append(memory.emotional_intensity)
        
        insights = []
        total_memories = len(memories)
        
        for emotion, count in emotion_counts.items():
            if count >= 3:  # Need multiple instances
                frequency = count / total_memories
                avg_intensity = sum(emotion_intensities[emotion]) / len(emotion_intensities[emotion])
                
                if frequency > 0.3:  # 30% or more of memorable moments
                    insight = CharacterInsight(
                        insight_type='emotional_pattern',
                        description=f"I often feel {emotion} during meaningful conversations",
                        confidence=frequency * avg_intensity,
                        supporting_memories=[m.id for m in memories if m.primary_emotion == emotion][:3],
                        first_observed=min(m.timestamp for m in memories if m.primary_emotion == emotion),
                        reinforcement_count=count
                    )
                    insights.append(insight)
        
        return insights
    
    def _analyze_topic_enthusiasm(self, memories: List[EpisodicMemory]) -> List[CharacterInsight]:
        """Analyze topics that generate high emotional engagement"""
        topic_keywords = {
            'nature': ['ocean', 'marine', 'environment', 'conservation', 'wildlife', 'ecosystem'],
            'creativity': ['create', 'design', 'art', 'imagine', 'build', 'craft'],
            'technology': ['code', 'programming', 'algorithm', 'AI', 'computer', 'software'],
            'relationships': ['friend', 'family', 'love', 'connection', 'bond', 'relationship'],
            'learning': ['learn', 'study', 'research', 'discover', 'understand', 'knowledge'],
            'adventure': ['travel', 'explore', 'adventure', 'journey', 'discover', 'experience']
        }
        
        topic_scores = defaultdict(list)
        
        for memory in memories:
            content_lower = memory.content.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    # Score based on emotional intensity and confidence
                    score = memory.emotional_intensity * memory.roberta_confidence
                    topic_scores[topic].append((score, memory))
        
        insights = []
        for topic, scores_memories in topic_scores.items():
            if len(scores_memories) >= 2:  # Need multiple instances
                avg_score = sum(score for score, _ in scores_memories) / len(scores_memories)
                if avg_score > 0.6:  # High engagement threshold
                    memories_for_topic = [memory for _, memory in scores_memories]
                    insight = CharacterInsight(
                        insight_type='topic_enthusiasm',
                        description=f"I get particularly engaged when discussing {topic}",
                        confidence=avg_score,
                        supporting_memories=[m.id for m in memories_for_topic][:3],
                        first_observed=min(m.timestamp for m in memories_for_topic),
                        reinforcement_count=len(scores_memories)
                    )
                    insights.append(insight)
        
        return insights
    
    def _analyze_personality_traits(self, memories: List[EpisodicMemory]) -> List[CharacterInsight]:
        """Analyze personality traits reflected in conversation patterns"""
        trait_indicators = {
            'supportive': ['help', 'support', 'encourage', 'understand', 'care'],
            'curious': ['why', 'how', 'what if', 'wonder', 'question', 'explore'],
            'empathetic': ['feel', 'understand', 'sorry', 'compassion', 'empathy'],
            'enthusiastic': ['excited', 'amazing', 'wonderful', 'love', 'fantastic'],
            'thoughtful': ['think', 'consider', 'reflect', 'ponder', 'analyze']
        }
        
        trait_scores = defaultdict(list)
        
        for memory in memories:
            # Analyze bot response if available
            text_to_analyze = memory.bot_response or memory.content
            text_lower = text_to_analyze.lower()
            
            for trait, indicators in trait_indicators.items():
                matches = sum(1 for indicator in indicators if indicator in text_lower)
                if matches > 0:
                    # Score based on match density and emotional intensity
                    score = (matches / len(indicators)) * memory.emotional_intensity
                    trait_scores[trait].append((score, memory))
        
        insights = []
        for trait, scores_memories in trait_scores.items():
            if len(scores_memories) >= 3:  # Need multiple instances
                avg_score = sum(score for score, _ in scores_memories) / len(scores_memories)
                if avg_score > 0.3:  # Trait expression threshold
                    memories_for_trait = [memory for _, memory in scores_memories]
                    insight = CharacterInsight(
                        insight_type='personality_trait',
                        description=f"I tend to be {trait} in my interactions",
                        confidence=avg_score,
                        supporting_memories=[m.id for m in memories_for_trait][:3],
                        first_observed=min(m.timestamp for m in memories_for_trait),
                        reinforcement_count=len(scores_memories)
                    )
                    insights.append(insight)
        
        return insights
    
    async def get_episodic_memory_for_response_enhancement(
        self, 
        collection_name: str,
        current_message: str,
        user_id: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get relevant episodic memories and character insights for response enhancement
        
        Args:
            collection_name: Bot-specific collection 
            current_message: Current user message for context matching
            user_id: User to get memories for
            limit: Maximum memories to return
            
        Returns:
            Dict with 'memories', 'insights', and 'context_suggestions'
        """
        try:
            # Get memorable moments for this user
            memorable_memories = await self.detect_memorable_moments_from_vector_patterns(
                collection_name=collection_name,
                user_id=user_id,
                limit=20  # Get more to filter
            )
            
            # Get character insights
            character_insights = await self.extract_character_insights_from_vector_patterns(
                collection_name=collection_name,
                memorable_memories=memorable_memories
            )
            
            # Filter memories relevant to current context
            relevant_memories = self._filter_relevant_memories(
                memorable_memories, 
                current_message, 
                limit
            )
            
            # Generate context suggestions
            context_suggestions = self._generate_context_suggestions(
                relevant_memories, 
                character_insights,
                current_message
            )
            
            return {
                'memories': [self._memory_to_dict(m) for m in relevant_memories],
                'insights': [self._insight_to_dict(i) for i in character_insights[:3]],
                'context_suggestions': context_suggestions,
                'total_memorable_moments': len(memorable_memories),
                'memory_confidence': sum(m.memorable_score for m in relevant_memories) / max(len(relevant_memories), 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting episodic memory for response enhancement: {e}")
            return {
                'memories': [],
                'insights': [],
                'context_suggestions': [],
                'total_memorable_moments': 0,
                'memory_confidence': 0.0
            }
    
    def _filter_relevant_memories(
        self, 
        memories: List[EpisodicMemory], 
        current_message: str, 
        limit: int
    ) -> List[EpisodicMemory]:
        """Filter memories relevant to current conversation context"""
        current_lower = current_message.lower()
        
        # Score memories by relevance
        scored_memories = []
        for memory in memories:
            relevance_score = 0.0
            
            # Content similarity (simple keyword matching)
            memory_words = memory.content.lower().split()
            current_words = current_lower.split()
            common_words = set(memory_words) & set(current_words)
            if common_words:
                relevance_score += len(common_words) / max(len(current_words), 1)
            
            # Context type relevance
            if memory.context_type == 'personal_sharing' and any(
                word in current_lower for word in self.personal_keywords
            ):
                relevance_score += 0.5
            
            # Emotional relevance - similar emotional context
            if memory.primary_emotion:
                emotion_keywords = {
                    'joy': ['happy', 'excited', 'great', 'wonderful', 'amazing'],
                    'sadness': ['sad', 'upset', 'disappointed', 'sorry'],
                    'fear': ['worried', 'scared', 'anxious', 'nervous'],
                    'anger': ['angry', 'frustrated', 'annoyed', 'mad']
                }
                
                emotion_words = emotion_keywords.get(memory.primary_emotion, [])
                if any(word in current_lower for word in emotion_words):
                    relevance_score += 0.3
            
            # Recent memories get slight boost
            days_ago = (datetime.now() - memory.timestamp).days
            if days_ago < 7:
                relevance_score += 0.2
            elif days_ago < 30:
                relevance_score += 0.1
            
            scored_memories.append((relevance_score, memory))
        
        # Sort by relevance and memorable score
        scored_memories.sort(key=lambda x: (x[0], x[1].memorable_score), reverse=True)
        
        return [memory for _, memory in scored_memories[:limit]]
    
    def _generate_context_suggestions(
        self, 
        memories: List[EpisodicMemory], 
        insights: List[CharacterInsight],
        current_message: str
    ) -> List[str]:
        """Generate natural context suggestions for episodic references"""
        suggestions = []
        
        # Memory-based suggestions
        for memory in memories[:2]:  # Top 2 relevant memories
            if memory.context_type == 'personal_sharing':
                suggestions.append(f"Remember when you shared about {memory.content_preview}")
            elif memory.context_type == 'creative_moment':
                suggestions.append(f"This reminds me of when we discussed {memory.content_preview}")
            elif memory.context_type == 'expertise':
                suggestions.append(f"Building on what we explored before: {memory.content_preview}")
        
        # Insight-based suggestions
        for insight in insights[:2]:  # Top 2 insights
            if insight.insight_type == 'emotional_pattern':
                suggestions.append(f"Character self-awareness: {insight.description}")
            elif insight.insight_type == 'topic_enthusiasm':
                suggestions.append(f"Character enthusiasm: {insight.description}")
        
        return suggestions[:3]  # Max 3 suggestions
    
    def _memory_to_dict(self, memory: EpisodicMemory) -> Dict[str, Any]:
        """Convert EpisodicMemory to dictionary for serialization"""
        return {
            'id': memory.id,
            'content_preview': memory.content_preview,
            'timestamp': memory.timestamp.isoformat(),
            'primary_emotion': memory.primary_emotion,
            'memorable_score': memory.memorable_score,
            'context_type': memory.context_type,
            'emotional_intensity': memory.emotional_intensity,
            'roberta_confidence': memory.roberta_confidence
        }
    
    def _insight_to_dict(self, insight: CharacterInsight) -> Dict[str, Any]:
        """Convert CharacterInsight to dictionary for serialization"""
        return {
            'type': insight.insight_type,
            'description': insight.description,
            'confidence': insight.confidence,
            'reinforcement_count': insight.reinforcement_count
        }

# Factory function for dependency injection
def create_character_vector_episodic_intelligence(
    qdrant_client: Optional[QdrantClient] = None
) -> CharacterVectorEpisodicIntelligence:
    """Factory function to create CharacterVectorEpisodicIntelligence instance"""
    return CharacterVectorEpisodicIntelligence(qdrant_client=qdrant_client)