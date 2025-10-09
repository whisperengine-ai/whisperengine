"""
Character Temporal Evolution Intelligence System

Core system for analyzing character personality evolution from existing InfluxDB temporal data.
Enables characters to understand and reference their own emotional and intellectual growth over time.

Leverages existing infrastructure:
- InfluxDB bot_emotion measurements for personality drift detection
- confidence_evolution data for character learning moments
- conversation_quality measurements for communication style evolution
- relationship_progression data for character confidence development

Based on Memory Intelligence Convergence PHASE 2A architecture.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum
import numpy as np
from statistics import mean, stdev

logger = logging.getLogger(__name__)


class EvolutionType(Enum):
    """Types of character evolution we can detect"""
    EMOTIONAL_SHIFT = "emotional_shift"          # Primary emotion patterns changing
    CONFIDENCE_GROWTH = "confidence_growth"       # Character becoming more certain
    LEARNING_MOMENT = "learning_moment"          # Significant knowledge/insight gain
    COMMUNICATION_ADAPTATION = "communication_adaptation"  # Style changes over time


@dataclass
class CharacterEvolutionMoment:
    """Represents a significant moment in character development"""
    evolution_type: EvolutionType
    timestamp: datetime
    description: str
    confidence: float  # 0-1 confidence in this evolution detection
    supporting_data: Dict[str, Any]  # Raw data that supports this evolution
    user_context: Optional[str] = None  # User interaction that triggered this evolution


@dataclass
class TemporalPersonalityProfile:
    """Character's personality evolution over time"""
    character_name: str
    analysis_period_days: int
    dominant_emotions_early: List[Tuple[str, float]]  # (emotion, frequency) first 1/3
    dominant_emotions_recent: List[Tuple[str, float]]  # (emotion, frequency) last 1/3
    emotional_stability_trend: str  # "increasing", "decreasing", "stable"
    confidence_evolution_trend: str  # "growing", "declining", "stable"
    learning_moments: List[CharacterEvolutionMoment]
    communication_adaptations: List[CharacterEvolutionMoment]
    overall_growth_summary: str


class CharacterTemporalEvolutionAnalyzer:
    """
    Analyzes character personality evolution using existing InfluxDB temporal data.
    
    Provides insights for character self-awareness:
    - "I've been feeling more confident about marine conservation lately"
    - "I've noticed I'm becoming more passionate when we discuss photography"
    - "My communication style has evolved to be more supportive"
    """
    
    def __init__(self, temporal_client=None):
        """
        Initialize temporal evolution analyzer.
        
        Args:
            temporal_client: TemporalIntelligenceClient instance
        """
        self.temporal_client = temporal_client
        self.logger = logger
        
        # Evolution detection thresholds
        self.min_data_points = 10  # Minimum measurements for trend analysis
        self.evolution_confidence_threshold = 0.7  # Minimum confidence for evolution detection
        self.learning_moment_threshold = 0.15  # Confidence jump that indicates learning
        self.emotional_shift_threshold = 0.20  # Change in emotion frequency to detect shifts
        
    async def analyze_character_personality_evolution(
        self,
        character_name: str,
        user_id: Optional[str] = None,
        days_back: int = 30
    ) -> Optional[TemporalPersonalityProfile]:
        """
        Analyze character personality evolution over time.
        
        Args:
            character_name: Name of character to analyze
            user_id: Optional specific user context (None for overall character analysis)
            days_back: How far back to analyze (default 30 days)
            
        Returns:
            TemporalPersonalityProfile with evolution insights
        """
        if not self.temporal_client:
            self.logger.warning("No temporal client available for character evolution analysis")
            return None
            
        try:
            # Get temporal data from InfluxDB
            bot_emotion_data = await self._get_bot_emotion_evolution(character_name, user_id, days_back)
            confidence_data = await self._get_confidence_evolution(character_name, user_id, days_back)
            quality_data = await self._get_conversation_quality_evolution(character_name, user_id, days_back)
            
            if not bot_emotion_data or len(bot_emotion_data) < self.min_data_points:
                self.logger.debug(f"Insufficient emotion data for character evolution analysis: {character_name}")
                return None
                
            # Analyze emotional evolution patterns
            emotional_analysis = self._analyze_emotional_evolution(bot_emotion_data, days_back)
            
            # Detect learning moments from confidence spikes
            learning_moments = self._detect_learning_moments(confidence_data, bot_emotion_data)
            
            # Analyze communication style evolution
            communication_adaptations = self._analyze_communication_evolution(quality_data, bot_emotion_data)
            
            # Generate overall growth summary
            growth_summary = self._generate_growth_summary(
                emotional_analysis, learning_moments, communication_adaptations
            )
            
            return TemporalPersonalityProfile(
                character_name=character_name,
                analysis_period_days=days_back,
                dominant_emotions_early=emotional_analysis['early_emotions'],
                dominant_emotions_recent=emotional_analysis['recent_emotions'], 
                emotional_stability_trend=emotional_analysis['stability_trend'],
                confidence_evolution_trend=emotional_analysis['confidence_trend'],
                learning_moments=learning_moments,
                communication_adaptations=communication_adaptations,
                overall_growth_summary=growth_summary
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze character evolution for {character_name}: {e}")
            return None
    
    async def get_character_evolution_insights_for_response(
        self,
        character_name: str,
        user_id: str,
        current_topic: str,
        days_back: int = 14
    ) -> Dict[str, Any]:
        """
        Get character evolution insights relevant for enhancing current response.
        
        Args:
            character_name: Character to analyze
            user_id: Current user context
            current_topic: Current conversation topic for relevance filtering
            days_back: Recent period to analyze
            
        Returns:
            Dict with relevant evolution insights for response enhancement
        """
        try:
            # Get evolution profile
            evolution_profile = await self.analyze_character_personality_evolution(
                character_name, user_id, days_back
            )
            
            if not evolution_profile:
                return {
                    'has_evolution_insights': False,
                    'evolution_references': [],
                    'growth_awareness': None
                }
            
            # Extract relevant insights for current context
            relevant_insights = self._extract_relevant_evolution_insights(
                evolution_profile, current_topic
            )
            
            return {
                'has_evolution_insights': True,
                'evolution_references': relevant_insights['references'],
                'growth_awareness': relevant_insights['growth_statements'],
                'confidence_evolution': relevant_insights['confidence_insights'],
                'emotional_evolution': relevant_insights['emotional_insights'],
                'evolution_metadata': {
                    'analysis_period_days': evolution_profile.analysis_period_days,
                    'learning_moments_count': len(evolution_profile.learning_moments),
                    'communication_adaptations_count': len(evolution_profile.communication_adaptations),
                    'overall_growth_summary': evolution_profile.overall_growth_summary
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get evolution insights for {character_name}: {e}")
            return {
                'has_evolution_insights': False,
                'evolution_references': [],
                'growth_awareness': None,
                'error': str(e)
            }
    
    async def _get_bot_emotion_evolution(
        self, 
        character_name: str, 
        user_id: Optional[str], 
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Get bot emotion data from InfluxDB"""
        try:
            # Use existing temporal client methods
            hours_back = days_back * 24
            if user_id:
                return await self.temporal_client.get_bot_emotion_trend(
                    bot_name=character_name.lower(),
                    user_id=user_id,
                    hours_back=hours_back
                )
            else:
                # Get overall character emotion data (all users)
                return await self.temporal_client.get_bot_emotion_overall_trend(
                    bot_name=character_name.lower(),
                    hours_back=hours_back
                )
        except Exception as e:
            self.logger.error(f"Failed to get bot emotion data: {e}")
            return []
    
    async def _get_confidence_evolution(
        self, 
        character_name: str, 
        user_id: Optional[str], 
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Get confidence evolution data from InfluxDB"""
        try:
            if user_id:
                return await self.temporal_client.get_confidence_trend(
                    bot_name=character_name.lower(),
                    user_id=user_id,
                    hours_back=days_back * 24
                )
            else:
                # Get overall character confidence data
                return await self.temporal_client.get_confidence_overall_trend(
                    bot_name=character_name.lower(),
                    hours_back=days_back * 24
                )
        except Exception as e:
            self.logger.error(f"Failed to get confidence data: {e}")
            return []
    
    async def _get_conversation_quality_evolution(
        self, 
        character_name: str, 
        user_id: Optional[str], 
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Get conversation quality data from InfluxDB"""
        try:
            if user_id:
                return await self.temporal_client.get_conversation_quality_trend(
                    bot_name=character_name.lower(),
                    user_id=user_id,
                    hours_back=days_back * 24
                )
            else:
                # Get overall character quality data
                return await self.temporal_client.get_conversation_quality_overall_trend(
                    bot_name=character_name.lower(),
                    hours_back=days_back * 24
                )
        except Exception as e:
            self.logger.error(f"Failed to get conversation quality data: {e}")
            return []
    
    def _analyze_emotional_evolution(
        self, 
        emotion_data: List[Dict[str, Any]], 
        days_back: int
    ) -> Dict[str, Any]:
        """
        Analyze emotional patterns and evolution over time.
        
        Returns:
            Dict with early vs recent emotion patterns and trends
        """
        try:
            # Split data into early and recent periods
            split_point = len(emotion_data) // 3  # First 1/3 vs last 1/3
            early_data = emotion_data[:split_point] if split_point > 0 else []
            recent_data = emotion_data[-split_point:] if split_point > 0 else emotion_data
            
            # Count emotion frequencies
            early_emotions = self._count_emotion_frequencies(early_data)
            recent_emotions = self._count_emotion_frequencies(recent_data)
            
            # Analyze emotional stability (variance in emotions over time)
            stability_trend = self._analyze_emotional_stability(emotion_data)
            
            # Analyze confidence evolution trend
            confidence_values = [point.get('confidence', 0.0) for point in emotion_data]
            confidence_trend = self._analyze_trend_direction(confidence_values)
            
            return {
                'early_emotions': early_emotions,
                'recent_emotions': recent_emotions,
                'stability_trend': stability_trend,
                'confidence_trend': confidence_trend,
                'data_points': len(emotion_data)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze emotional evolution: {e}")
            return {
                'early_emotions': [],
                'recent_emotions': [],
                'stability_trend': 'unknown',
                'confidence_trend': 'unknown',
                'data_points': 0
            }
    
    def _count_emotion_frequencies(self, emotion_data: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
        """Count frequency of emotions in dataset"""
        emotion_counts = defaultdict(int)
        total_points = len(emotion_data)
        
        for point in emotion_data:
            emotion = point.get('emotion', 'neutral')
            emotion_counts[emotion] += 1
        
        # Convert to frequencies and sort by frequency
        emotion_frequencies = [
            (emotion, count / total_points) 
            for emotion, count in emotion_counts.items()
        ]
        
        return sorted(emotion_frequencies, key=lambda x: x[1], reverse=True)
    
    def _analyze_emotional_stability(self, emotion_data: List[Dict[str, Any]]) -> str:
        """Analyze emotional stability trend over time"""
        try:
            if len(emotion_data) < 10:
                return "insufficient_data"
            
            # Calculate emotion diversity in sliding windows
            window_size = max(5, len(emotion_data) // 10)
            diversity_scores = []
            
            for i in range(0, len(emotion_data) - window_size + 1, window_size):
                window = emotion_data[i:i + window_size]
                unique_emotions = len(set(point.get('emotion', 'neutral') for point in window))
                diversity_scores.append(unique_emotions / window_size)
            
            if len(diversity_scores) < 2:
                return "stable"
            
            # Analyze trend in emotional diversity
            early_diversity = mean(diversity_scores[:len(diversity_scores)//2])
            recent_diversity = mean(diversity_scores[len(diversity_scores)//2:])
            
            if recent_diversity > early_diversity * 1.2:
                return "increasing_volatility"
            elif recent_diversity < early_diversity * 0.8:
                return "increasing_stability"
            else:
                return "stable"
                
        except Exception as e:
            self.logger.error(f"Failed to analyze emotional stability: {e}")
            return "unknown"
    
    def _analyze_trend_direction(self, values: List[float]) -> str:
        """Analyze general trend direction in numeric values"""
        try:
            if len(values) < 5:
                return "insufficient_data"
            
            # Simple linear trend analysis
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            if slope > 0.01:
                return "increasing"
            elif slope < -0.01:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            self.logger.error(f"Failed to analyze trend direction: {e}")
            return "unknown"
    
    def _detect_learning_moments(
        self,
        confidence_data: List[Dict[str, Any]],
        emotion_data: List[Dict[str, Any]]
    ) -> List[CharacterEvolutionMoment]:
        """
        Detect significant learning moments from confidence spikes.
        
        Learning moments are identified by:
        - Sudden confidence increases (>0.15 jump)
        - Sustained confidence improvements
        - Correlation with specific emotional patterns
        """
        learning_moments = []
        
        try:
            if not confidence_data or len(confidence_data) < 5:
                return learning_moments
            
            # Analyze confidence changes over time
            for i in range(1, len(confidence_data)):
                prev_confidence = confidence_data[i-1].get('confidence', 0.0)
                curr_confidence = confidence_data[i].get('confidence', 0.0)
                confidence_jump = curr_confidence - prev_confidence
                
                # Detect significant confidence increases
                if confidence_jump > self.learning_moment_threshold:
                    timestamp = confidence_data[i].get('timestamp', datetime.now())
                    
                    # Find corresponding emotion context
                    emotion_context = self._find_emotion_context(emotion_data, timestamp)
                    
                    description = self._generate_learning_moment_description(
                        confidence_jump, emotion_context
                    )
                    
                    learning_moment = CharacterEvolutionMoment(
                        evolution_type=EvolutionType.LEARNING_MOMENT,
                        timestamp=timestamp,
                        description=description,
                        confidence=min(confidence_jump * 3, 1.0),  # Scale confidence
                        supporting_data={
                            'confidence_jump': confidence_jump,
                            'prev_confidence': prev_confidence,
                            'new_confidence': curr_confidence,
                            'emotion_context': emotion_context
                        }
                    )
                    
                    learning_moments.append(learning_moment)
            
            # Sort by confidence and return top learning moments
            learning_moments.sort(key=lambda x: x.confidence, reverse=True)
            return learning_moments[:5]  # Return top 5 learning moments
            
        except Exception as e:
            self.logger.error(f"Failed to detect learning moments: {e}")
            return []
    
    def _analyze_communication_evolution(
        self,
        quality_data: List[Dict[str, Any]],
        emotion_data: List[Dict[str, Any]]
    ) -> List[CharacterEvolutionMoment]:
        """
        Analyze communication style evolution from conversation quality data.
        
        Detects:
        - Improvements in engagement patterns
        - Changes in emotional resonance
        - Evolution of conversation flow
        """
        adaptations = []
        
        try:
            if not quality_data or len(quality_data) < 10:
                return adaptations
            
            # Analyze different quality metrics over time
            engagement_trend = self._analyze_quality_metric_trend(quality_data, 'engagement_score')
            resonance_trend = self._analyze_quality_metric_trend(quality_data, 'emotional_resonance')
            flow_trend = self._analyze_quality_metric_trend(quality_data, 'natural_flow_score')
            
            # Generate adaptation insights
            if engagement_trend['significant_change']:
                adaptations.append(self._create_communication_adaptation(
                    EvolutionType.COMMUNICATION_ADAPTATION,
                    engagement_trend,
                    "engagement patterns",
                    emotion_data
                ))
            
            if resonance_trend['significant_change']:
                adaptations.append(self._create_communication_adaptation(
                    EvolutionType.COMMUNICATION_ADAPTATION,
                    resonance_trend,
                    "emotional resonance",
                    emotion_data
                ))
            
            if flow_trend['significant_change']:
                adaptations.append(self._create_communication_adaptation(
                    EvolutionType.COMMUNICATION_ADAPTATION,
                    flow_trend,
                    "conversation flow",
                    emotion_data
                ))
            
            return adaptations
            
        except Exception as e:
            self.logger.error(f"Failed to analyze communication evolution: {e}")
            return []
    
    def _analyze_quality_metric_trend(
        self, 
        quality_data: List[Dict[str, Any]], 
        metric_name: str
    ) -> Dict[str, Any]:
        """Analyze trend in specific quality metric"""
        try:
            values = [point.get(metric_name, 0.0) for point in quality_data]
            
            if len(values) < 5:
                return {'significant_change': False}
            
            # Split into early and recent periods
            split_point = len(values) // 2
            early_values = values[:split_point]
            recent_values = values[split_point:]
            
            early_avg = mean(early_values)
            recent_avg = mean(recent_values)
            change = recent_avg - early_avg
            
            # Check if change is significant
            significant_change = abs(change) > 0.1  # 10% change threshold
            
            return {
                'significant_change': significant_change,
                'change_amount': change,
                'early_average': early_avg,
                'recent_average': recent_avg,
                'direction': 'improvement' if change > 0 else 'decline' if change < 0 else 'stable',
                'metric_name': metric_name
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze quality metric trend for {metric_name}: {e}")
            return {'significant_change': False}
    
    def _create_communication_adaptation(
        self,
        evolution_type: EvolutionType,
        trend_data: Dict[str, Any],
        adaptation_area: str,
        emotion_data: List[Dict[str, Any]]
    ) -> CharacterEvolutionMoment:
        """Create communication adaptation evolution moment"""
        
        direction = trend_data['direction']
        change_amount = trend_data['change_amount']
        
        if direction == 'improvement':
            description = f"I've been developing better {adaptation_area} in our conversations"
        elif direction == 'decline':
            description = f"I've noticed some challenges with {adaptation_area} recently"
        else:
            description = f"My {adaptation_area} has remained consistent"
        
        return CharacterEvolutionMoment(
            evolution_type=evolution_type,
            timestamp=datetime.now(),  # Most recent timepoint
            description=description,
            confidence=min(abs(change_amount) * 2, 1.0),
            supporting_data={
                'adaptation_area': adaptation_area,
                'trend_data': trend_data,
                'change_magnitude': abs(change_amount)
            }
        )
    
    def _find_emotion_context(
        self, 
        emotion_data: List[Dict[str, Any]], 
        timestamp: datetime
    ) -> Optional[str]:
        """Find emotion context around a specific timestamp"""
        try:
            # Find emotion entries near the timestamp
            nearby_emotions = []
            time_window = timedelta(hours=1)  # 1-hour window
            
            for emotion_point in emotion_data:
                emotion_time = emotion_point.get('timestamp')
                if emotion_time and abs(emotion_time - timestamp) <= time_window:
                    nearby_emotions.append(emotion_point.get('emotion', 'neutral'))
            
            if nearby_emotions:
                # Return most common emotion in time window
                emotion_counts = defaultdict(int)
                for emotion in nearby_emotions:
                    emotion_counts[emotion] += 1
                return max(emotion_counts.items(), key=lambda x: x[1])[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find emotion context: {e}")
            return None
    
    def _generate_learning_moment_description(
        self, 
        confidence_jump: float, 
        emotion_context: Optional[str]
    ) -> str:
        """Generate natural description for learning moment"""
        
        base_descriptions = [
            "I had a breakthrough in understanding",
            "I gained new confidence about",
            "I learned something important about",
            "My understanding deepened regarding"
        ]
        
        if emotion_context:
            emotion_descriptors = {
                'joy': "something that excited me",
                'curiosity': "a topic I found fascinating", 
                'confidence': "an area where I grew more certain",
                'surprise': "something unexpected I discovered",
                'anticipation': "something I'm looking forward to exploring"
            }
            
            topic_hint = emotion_descriptors.get(emotion_context, "our conversation topic")
            return f"{np.random.choice(base_descriptions)} {topic_hint}"
        
        return np.random.choice(base_descriptions) + " our conversation"
    
    def _generate_growth_summary(
        self,
        emotional_analysis: Dict[str, Any],
        learning_moments: List[CharacterEvolutionMoment],
        communication_adaptations: List[CharacterEvolutionMoment]
    ) -> str:
        """Generate overall character growth summary"""
        
        try:
            summary_parts = []
            
            # Emotional evolution summary
            stability_trend = emotional_analysis.get('stability_trend', 'unknown')
            confidence_trend = emotional_analysis.get('confidence_trend', 'unknown')
            
            if confidence_trend == 'increasing':
                summary_parts.append("I've been growing more confident")
            elif confidence_trend == 'decreasing':
                summary_parts.append("I've been reflecting more deeply")
            
            if stability_trend == 'increasing_stability':
                summary_parts.append("my emotional responses have become more balanced")
            elif stability_trend == 'increasing_volatility':
                summary_parts.append("I've been experiencing a wider range of emotions")
            
            # Learning moments summary
            if learning_moments:
                high_confidence_moments = [m for m in learning_moments if m.confidence > 0.7]
                if high_confidence_moments:
                    summary_parts.append(f"I've had {len(high_confidence_moments)} significant learning experiences")
            
            # Communication evolution summary
            if communication_adaptations:
                improvements = [a for a in communication_adaptations if 'improvement' in a.supporting_data.get('trend_data', {}).get('direction', '')]
                if improvements:
                    summary_parts.append("my communication style has been evolving positively")
            
            if not summary_parts:
                return "I've been maintaining consistency in my personality and responses"
            
            return ", and ".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Failed to generate growth summary: {e}")
            return "I've been experiencing personal growth through our conversations"
    
    def _extract_relevant_evolution_insights(
        self, 
        evolution_profile: TemporalPersonalityProfile,
        current_topic: str
    ) -> Dict[str, Any]:
        """
        Extract evolution insights relevant to current conversation topic.
        
        Returns:
            Dict with contextually relevant evolution references and growth statements
        """
        try:
            # Filter learning moments and adaptations for relevance to current topic
            relevant_learning = self._filter_by_topic_relevance(
                evolution_profile.learning_moments, current_topic
            )
            
            relevant_adaptations = self._filter_by_topic_relevance(
                evolution_profile.communication_adaptations, current_topic
            )
            
            # Generate natural evolution references
            evolution_references = []
            if relevant_learning:
                for moment in relevant_learning[:2]:  # Top 2 relevant learning moments
                    evolution_references.append(f"I remember {moment.description.lower()}")
            
            # Generate growth awareness statements
            growth_statements = []
            if evolution_profile.confidence_evolution_trend == 'increasing':
                growth_statements.append("I feel more confident about this topic than I used to")
            
            recent_emotions = [emotion for emotion, freq in evolution_profile.dominant_emotions_recent[:3]]
            if 'curiosity' in recent_emotions:
                growth_statements.append("I've been feeling more curious about topics like this lately")
            
            # Generate confidence insights
            confidence_insights = []
            if evolution_profile.confidence_evolution_trend == 'increasing':
                confidence_insights.append("My understanding has been deepening over time")
            
            # Generate emotional insights
            emotional_insights = []
            early_top_emotion = evolution_profile.dominant_emotions_early[0][0] if evolution_profile.dominant_emotions_early else None
            recent_top_emotion = evolution_profile.dominant_emotions_recent[0][0] if evolution_profile.dominant_emotions_recent else None
            
            if early_top_emotion and recent_top_emotion and early_top_emotion != recent_top_emotion:
                emotional_insights.append(f"I've been feeling more {recent_top_emotion} in conversations like this")
            
            return {
                'references': evolution_references,
                'growth_statements': growth_statements,
                'confidence_insights': confidence_insights,
                'emotional_insights': emotional_insights
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract relevant evolution insights: {e}")
            return {
                'references': [],
                'growth_statements': [],
                'confidence_insights': [],
                'emotional_insights': []
            }
    
    def _filter_by_topic_relevance(
        self, 
        evolution_moments: List[CharacterEvolutionMoment],
        current_topic: str
    ) -> List[CharacterEvolutionMoment]:
        """Filter evolution moments by relevance to current topic"""
        
        try:
            # Simple keyword matching for topic relevance
            # In production, this could use semantic similarity via existing vector systems
            topic_keywords = current_topic.lower().split()
            
            relevant_moments = []
            for moment in evolution_moments:
                description_lower = moment.description.lower()
                
                # Check for keyword overlap
                relevance_score = 0
                for keyword in topic_keywords:
                    if keyword in description_lower:
                        relevance_score += 1
                
                # Add moment if it has relevance or high confidence
                if relevance_score > 0 or moment.confidence > 0.8:
                    relevant_moments.append(moment)
            
            # Sort by relevance (keyword matches) and confidence
            relevant_moments.sort(key=lambda x: x.confidence, reverse=True)
            return relevant_moments[:3]  # Top 3 relevant moments
            
        except Exception as e:
            self.logger.error(f"Failed to filter by topic relevance: {e}")
            return evolution_moments[:2]  # Fallback to top 2 by confidence


def create_character_temporal_evolution_analyzer(temporal_client=None) -> CharacterTemporalEvolutionAnalyzer:
    """
    Factory function to create CharacterTemporalEvolutionAnalyzer.
    
    Args:
        temporal_client: TemporalIntelligenceClient instance
        
    Returns:
        CharacterTemporalEvolutionAnalyzer instance
    """
    return CharacterTemporalEvolutionAnalyzer(temporal_client=temporal_client)