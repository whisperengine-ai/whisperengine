"""
Holistic AI Metrics Collection System
=====================================

Comprehensive metrics framework for measuring human-like AI performance
across all integrated phases (memory, emotion, personality, conversation).
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics collected"""
    PERFORMANCE = "performance"
    QUALITY = "quality" 
    USER_EXPERIENCE = "user_experience"
    HUMAN_LIKENESS = "human_likeness"

@dataclass
class ConversationMetrics:
    """Metrics for a single conversation interaction"""
    user_id: str
    timestamp: datetime
    
    # Performance metrics
    total_response_time: float
    memory_retrieval_time: float
    emotion_analysis_time: float
    phase_integration_time: float
    
    # Quality metrics
    memory_hit_rate: float
    memory_relevance_score: float
    emotional_appropriateness: float
    personality_consistency: float
    
    # User experience
    conversation_length: int
    user_engagement_score: float
    
    # Human-likeness indicators
    response_naturalness: float
    contextual_awareness: float
    emotional_intelligence_display: float

@dataclass
class SystemMetrics:
    """Aggregated system-wide metrics"""
    timestamp: datetime
    time_period: str  # "hourly", "daily", "weekly"
    
    # Aggregate scores
    avg_conversation_naturalness: float
    avg_memory_effectiveness: float
    avg_emotional_intelligence: float
    
    # Performance aggregates
    avg_response_time: float
    p95_response_time: float
    system_uptime: float
    
    # User experience aggregates
    daily_active_users: int
    avg_conversation_length: float
    user_retention_rate: float
    
    # Quality trends
    consistency_trend: float
    improvement_rate: float

class HolisticAIMetrics:
    """
    Comprehensive metrics collection and analysis for the human-like AI system
    """
    
    def __init__(self, redis_client=None, database_manager=None):
        self.redis_client = redis_client
        self.database_manager = database_manager
        self.metrics_cache = {}
        self.conversation_metrics = []
        
        # Metric calculation weights
        self.weights = {
            'consistency': 0.25,
            'emotional_appropriateness': 0.25,
            'contextual_relevance': 0.25,
            'response_fluency': 0.25
        }
    
    async def start_conversation_timing(self, user_id: str, message: str) -> str:
        """Start timing a conversation interaction"""
        interaction_id = f"{user_id}_{int(time.time() * 1000)}"
        
        self.metrics_cache[interaction_id] = {
            'user_id': user_id,
            'message': message,
            'start_time': time.time(),
            'phase_times': {},
            'quality_scores': {}
        }
        
        return interaction_id
    
    async def record_phase_timing(self, interaction_id: str, phase: str, duration: float):
        """Record timing for a specific processing phase"""
        if interaction_id in self.metrics_cache:
            self.metrics_cache[interaction_id]['phase_times'][phase] = duration
    
    async def record_quality_score(self, interaction_id: str, metric: str, score: float):
        """Record a quality metric score"""
        if interaction_id in self.metrics_cache:
            self.metrics_cache[interaction_id]['quality_scores'][metric] = score
    
    async def finalize_conversation_metrics(self, interaction_id: str, 
                                          response: str, 
                                          memory_results: List[Dict],
                                          emotion_results: Dict) -> ConversationMetrics:
        """Complete metrics collection for a conversation"""
        if interaction_id not in self.metrics_cache:
            return None
        
        cache_data = self.metrics_cache[interaction_id]
        total_time = time.time() - cache_data['start_time']
        
        # Calculate derived metrics
        memory_hit_rate = await self._calculate_memory_hit_rate(memory_results)
        memory_relevance = await self._calculate_memory_relevance(memory_results, cache_data['message'])
        emotional_appropriateness = await self._calculate_emotional_appropriateness(
            emotion_results, response
        )
        personality_consistency = await self._calculate_personality_consistency(
            cache_data['user_id'], response
        )
        
        # Create conversation metrics
        metrics = ConversationMetrics(
            user_id=cache_data['user_id'],
            timestamp=datetime.now(timezone.utc),
            total_response_time=total_time,
            memory_retrieval_time=cache_data['phase_times'].get('memory', 0),
            emotion_analysis_time=cache_data['phase_times'].get('emotion', 0),
            phase_integration_time=cache_data['phase_times'].get('integration', 0),
            memory_hit_rate=memory_hit_rate,
            memory_relevance_score=memory_relevance,
            emotional_appropriateness=emotional_appropriateness,
            personality_consistency=personality_consistency,
            conversation_length=len(cache_data['message'].split()),
            user_engagement_score=cache_data['quality_scores'].get('engagement', 0.5),
            response_naturalness=await self._calculate_response_naturalness(response),
            contextual_awareness=memory_relevance * 0.7 + personality_consistency * 0.3,
            emotional_intelligence_display=emotional_appropriateness
        )
        
        # Store metrics
        await self._store_conversation_metrics(metrics)
        
        # Clean up cache
        del self.metrics_cache[interaction_id]
        
        return metrics
    
    async def calculate_conversation_naturalness_score(self, metrics: ConversationMetrics) -> float:
        """Calculate the overall Conversation Naturalness Score (CNS)"""
        return (
            self.weights['consistency'] * metrics.personality_consistency +
            self.weights['emotional_appropriateness'] * metrics.emotional_appropriateness +
            self.weights['contextual_relevance'] * metrics.memory_relevance_score +
            self.weights['response_fluency'] * metrics.response_naturalness
        )
    
    async def calculate_memory_effectiveness_index(self, metrics: ConversationMetrics) -> float:
        """Calculate the Memory Effectiveness Index (MEI)"""
        # Get additional context from database
        relationship_depth = await self._get_relationship_depth(metrics.user_id)
        context_continuity = await self._calculate_context_continuity(metrics.user_id)
        
        return (
            0.3 * metrics.memory_hit_rate +
            0.3 * metrics.memory_relevance_score +
            0.2 * relationship_depth +
            0.2 * context_continuity
        )
    
    async def calculate_emotional_intelligence_accuracy(self, metrics: ConversationMetrics) -> float:
        """Calculate the Emotional Intelligence Accuracy (EIA)"""
        # Get emotional detection accuracy from recent history
        emotion_accuracy = await self._get_emotion_detection_accuracy(metrics.user_id)
        proactive_success = await self._get_proactive_support_success(metrics.user_id)
        
        return (
            0.4 * emotion_accuracy +
            0.3 * metrics.emotional_appropriateness +
            0.3 * proactive_success
        )
    
    async def generate_system_metrics(self, time_period: str = "daily") -> SystemMetrics:
        """Generate aggregated system metrics"""
        end_time = datetime.now(timezone.utc)
        
        if time_period == "hourly":
            start_time = end_time - timedelta(hours=1)
        elif time_period == "daily":
            start_time = end_time - timedelta(days=1)
        elif time_period == "weekly":
            start_time = end_time - timedelta(weeks=1)
        else:
            start_time = end_time - timedelta(days=1)
        
        # Get conversation metrics for time period
        recent_metrics = await self._get_metrics_for_period(start_time, end_time)
        
        if not recent_metrics:
            return None
        
        # Calculate aggregated metrics
        avg_cns = statistics.mean([
            await self.calculate_conversation_naturalness_score(m) for m in recent_metrics
        ])
        avg_mei = statistics.mean([
            await self.calculate_memory_effectiveness_index(m) for m in recent_metrics
        ])
        avg_eia = statistics.mean([
            await self.calculate_emotional_intelligence_accuracy(m) for m in recent_metrics
        ])
        
        response_times = [m.total_response_time for m in recent_metrics]
        
        return SystemMetrics(
            timestamp=end_time,
            time_period=time_period,
            avg_conversation_naturalness=avg_cns,
            avg_memory_effectiveness=avg_mei,
            avg_emotional_intelligence=avg_eia,
            avg_response_time=statistics.mean(response_times),
            p95_response_time=self._percentile(response_times, 95),
            system_uptime=await self._get_system_uptime(),
            daily_active_users=await self._count_active_users(start_time, end_time),
            avg_conversation_length=statistics.mean([m.conversation_length for m in recent_metrics]),
            user_retention_rate=await self._calculate_retention_rate(start_time, end_time),
            consistency_trend=await self._calculate_consistency_trend(recent_metrics),
            improvement_rate=await self._calculate_improvement_rate(time_period)
        )
    
    # Helper methods for metric calculations
    async def _calculate_memory_hit_rate(self, memory_results: List[Dict]) -> float:
        """Calculate how often relevant memories are found"""
        if not memory_results:
            return 0.0
        
        # Assume memories with score > 0.5 are "hits"
        hits = sum(1 for m in memory_results if m.get('score', 0) > 0.5)
        return hits / len(memory_results)
    
    async def _calculate_memory_relevance(self, memory_results: List[Dict], query: str) -> float:
        """Calculate average relevance of retrieved memories"""
        if not memory_results:
            return 0.0
        
        return statistics.mean([m.get('score', 0) for m in memory_results])
    
    async def _calculate_emotional_appropriateness(self, emotion_results: Dict, response: str) -> float:
        """Calculate how emotionally appropriate the response is"""
        try:
            detected_emotion = emotion_results.get('detected_emotion', 'neutral')
            response_sentiment = emotion_results.get('response_sentiment', 'neutral')
            
            # Define emotion compatibility matrix
            emotion_compatibility = {
                'joy': {'positive': 1.0, 'neutral': 0.8, 'negative': 0.2},
                'sadness': {'negative': 0.9, 'neutral': 0.7, 'positive': 0.3},
                'anger': {'negative': 0.8, 'neutral': 0.6, 'positive': 0.1},
                'fear': {'negative': 0.8, 'neutral': 0.7, 'positive': 0.4},
                'surprise': {'positive': 0.8, 'neutral': 0.8, 'negative': 0.6},
                'disgust': {'negative': 0.9, 'neutral': 0.6, 'positive': 0.2},
                'neutral': {'neutral': 1.0, 'positive': 0.8, 'negative': 0.7}
            }
            
            # Get base compatibility score
            compatibility = emotion_compatibility.get(detected_emotion, {}).get(response_sentiment, 0.5)
            
            # Adjust based on response content analysis
            response_lower = response.lower()
            
            # Boost score for empathetic responses
            empathy_indicators = ['understand', 'sorry', 'hear', 'feel', 'support', 'help']
            if any(word in response_lower for word in empathy_indicators):
                compatibility = min(1.0, compatibility + 0.1)
            
            # Reduce score for inappropriate responses to negative emotions
            if detected_emotion in ['sadness', 'anger', 'fear']:
                dismissive_words = ['just', 'simply', 'calm down', 'get over', 'no big deal']
                if any(phrase in response_lower for phrase in dismissive_words):
                    compatibility = max(0.0, compatibility - 0.3)
            
            return compatibility
            
        except Exception as e:
            logger.warning(f"Emotional appropriateness calculation failed: {e}")
            return 0.5
    
    async def _calculate_personality_consistency(self, user_id: str, response: str) -> float:
        """Calculate personality consistency score"""
        try:
            # Analyze response against established personality patterns
            response_lower = response.lower()
            
            # Define personality indicators and scoring
            personality_traits = {
                'formal': ['please', 'thank you', 'sir', 'madam', 'kindly', 'appreciate'],
                'casual': ['hey', 'yeah', 'cool', 'awesome', 'no worries', 'sure thing'],
                'helpful': ['help', 'assist', 'support', 'guide', 'explain', 'show'],
                'empathetic': ['understand', 'feel', 'sorry', 'hear you', 'support', 'care'],
                'analytical': ['analyze', 'consider', 'examine', 'evaluate', 'data', 'evidence'],
                'creative': ['imagine', 'creative', 'idea', 'innovative', 'unique', 'artistic']
            }
            
            # Score each trait presence
            trait_scores = {}
            total_words = len(response.split())
            
            for trait, indicators in personality_traits.items():
                matches = sum(1 for indicator in indicators if indicator in response_lower)
                trait_scores[trait] = matches / max(total_words, 1)  # Normalize by response length
            
            # Calculate consistency based on trait dominance
            if not trait_scores:
                return 0.5
            
            max_trait_score = max(trait_scores.values())
            trait_variety = len([score for score in trait_scores.values() if score > 0])
            
            # Higher consistency if one or two traits dominate (clear personality)
            if max_trait_score > 0.1 and trait_variety <= 2:
                consistency = 0.9
            elif max_trait_score > 0.05:
                consistency = 0.7
            elif trait_variety > 0:
                consistency = 0.6
            else:
                consistency = 0.5
            
            # Bonus for helpful and empathetic traits (core AI personality)
            if trait_scores.get('helpful', 0) > 0.05 or trait_scores.get('empathetic', 0) > 0.05:
                consistency = min(1.0, consistency + 0.1)
            
            return consistency
            
        except Exception as e:
            logger.warning("Personality consistency calculation failed: %s", str(e))
            return 0.5
    
    async def _calculate_response_naturalness(self, response: str) -> float:
        """Calculate how natural/human-like the response sounds"""
        # Would implement sophisticated NLP analysis
        # Placeholder based on response characteristics
        naturalness_factors = [
            len(response.split()) > 5,  # Not too short
            '.' in response or '!' in response,  # Proper punctuation
            not response.isupper(),  # Not all caps
            len(response) < 500,  # Not too long
        ]
        return sum(naturalness_factors) / len(naturalness_factors)
    
    def _emotion_to_score(self, emotion: str) -> float:
        """Convert emotion to numerical score for comparison"""
        emotion_scores = {
            'very_positive': 1.0, 'positive': 0.75, 'neutral': 0.5,
            'negative': 0.25, 'very_negative': 0.0
        }
        return emotion_scores.get(emotion.lower(), 0.5)
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def _store_conversation_metrics(self, metrics: ConversationMetrics):
        """Store conversation metrics to database"""
        if self.database_manager:
            await self.database_manager.store_metrics(asdict(metrics))
    
    async def _get_metrics_for_period(self, start_time: datetime, end_time: datetime) -> List[ConversationMetrics]:
        """Retrieve metrics for a time period"""
        # Placeholder - would query database
        return []
    
    async def _get_relationship_depth(self, user_id: str) -> float:
        """Get relationship depth score for user"""
        # Would query relationship tracking system
        return 0.6  # Placeholder
    
    async def _calculate_context_continuity(self, user_id: str) -> float:
        """Calculate how well context is maintained across conversations"""
        # Would analyze conversation history
        return 0.7  # Placeholder
    
    async def _get_emotion_detection_accuracy(self, user_id: str) -> float:
        """Get emotion detection accuracy for user"""
        # Would analyze emotion detection performance
        return 0.8  # Placeholder
    
    async def _get_proactive_support_success(self, user_id: str) -> float:
        """Get success rate of proactive support interventions"""
        # Would analyze intervention outcomes
        return 0.75  # Placeholder
    
    async def _get_system_uptime(self) -> float:
        """Get system uptime percentage"""
        return 0.99  # Placeholder
    
    async def _count_active_users(self, start_time: datetime, end_time: datetime) -> int:
        """Count active users in time period"""
        return 42  # Placeholder
    
    async def _calculate_retention_rate(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate user retention rate"""
        return 0.85  # Placeholder
    
    async def _calculate_consistency_trend(self, metrics: List[ConversationMetrics]) -> float:
        """Calculate trend in consistency over time"""
        if len(metrics) < 2:
            return 0.0
        
        consistency_scores = [m.personality_consistency for m in metrics]
        # Simple linear trend calculation
        if len(consistency_scores) >= 2:
            return (consistency_scores[-1] - consistency_scores[0]) / len(consistency_scores)
        return 0.0
    
    async def _calculate_improvement_rate(self, time_period: str) -> float:
        """Calculate rate of improvement over time"""
        # Would compare current period to previous period
        return 0.05  # Placeholder - 5% improvement