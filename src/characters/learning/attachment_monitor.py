"""
Attachment Monitoring System for WhisperEngine

STAGE 2A: Enhanced AI Ethics for Character Learning
Purpose: Monitor user attachment indicators and provide graceful intervention
         when dependency patterns exceed healthy thresholds.

Key Features:
- InfluxDB-based interaction frequency tracking
- Emotional intensity pattern detection (leverages RoBERTa metadata)
- Dependency language detection (integrates with AI Ethics Layer)
- Character-archetype-aware intervention (respects Type 1/2/3 differences)

Architecture:
- Leverages existing TemporalIntelligenceClient for data storage
- Integrates with existing AI Ethics Layer for intervention responses
- Uses existing RoBERTa emotion analysis for intensity metrics
- Respects character archetype system (allow_full_roleplay_immersion flag)
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class AttachmentRiskLevel(Enum):
    """Risk levels for user attachment indicators"""
    HEALTHY = "healthy"           # Normal interaction patterns
    ELEVATED = "elevated"         # Slightly concerning patterns
    HIGH = "high"                 # Intervention recommended
    CRITICAL = "critical"         # Immediate intervention required


@dataclass
class AttachmentMetrics:
    """Attachment indicator metrics for a user"""
    user_id: str
    bot_name: str
    interaction_frequency: float      # Messages per day (7-day average)
    emotional_intensity: float        # Average emotional intensity (0-1)
    dependency_language_count: int    # Count of dependency phrases detected
    consecutive_days: int             # Days with continuous interaction
    total_interactions: int           # Total message count in period
    risk_level: AttachmentRiskLevel
    timestamp: datetime


class AttachmentMonitor:
    """
    Monitor user attachment patterns and provide healthy boundary guidance.
    
    Integrates with:
    - TemporalIntelligenceClient: Interaction frequency tracking
    - VectorMemorySystem: Emotional intensity analysis (RoBERTa metadata)
    - AI Ethics Layer: Intervention response generation
    """
    
    def __init__(self, temporal_client=None, memory_manager=None):
        """
        Initialize attachment monitor with existing system components.
        
        Args:
            temporal_client: TemporalIntelligenceClient for frequency tracking
            memory_manager: VectorMemorySystem for emotion analysis
        """
        self.temporal_client = temporal_client
        self.memory_manager = memory_manager
        
        # Attachment risk thresholds (configurable)
        self.frequency_threshold_elevated = 10   # Messages per day
        self.frequency_threshold_high = 20       # Messages per day
        self.frequency_threshold_critical = 40   # Messages per day
        
        self.emotional_intensity_threshold = 0.75  # Average intensity
        self.dependency_phrase_threshold = 3       # Count in 7 days
        self.consecutive_days_threshold = 14      # Days without break
        
        # Dependency language patterns
        self.dependency_phrases = [
            "can't live without you",
            "you're all i have",
            "only one i can talk to",
            "don't know what i'd do without you",
            "need you so much",
            "my only friend",
            "can't function without",
            "you're my everything",
            "only person who understands",
            "wouldn't survive without",
            "depend on you",
            "rely on you",
            "lost without you",
            "nothing without you"
        ]
        
        logger.info("🛡️ AttachmentMonitor initialized with healthy boundary thresholds")
    
    async def analyze_attachment_risk(
        self,
        user_id: str,
        bot_name: str,
        current_message: str = "",
        lookback_days: int = 7
    ) -> AttachmentMetrics:
        """
        Analyze user attachment risk based on interaction patterns.
        
        Args:
            user_id: User identifier
            bot_name: Character bot name
            current_message: Current message text for dependency detection
            lookback_days: Days to analyze (default 7)
            
        Returns:
            AttachmentMetrics with risk level and indicators
        """
        try:
            # Collect attachment indicators from existing systems
            interaction_frequency = await self._get_interaction_frequency(
                user_id, bot_name, lookback_days
            )
            
            emotional_intensity = await self._get_emotional_intensity(
                user_id, bot_name, lookback_days
            )
            
            dependency_count = self._detect_dependency_language(current_message)
            
            consecutive_days = await self._get_consecutive_days(
                user_id, bot_name
            )
            
            total_interactions = await self._get_total_interactions(
                user_id, bot_name, lookback_days
            )
            
            # Calculate risk level
            risk_level = self._calculate_risk_level(
                interaction_frequency,
                emotional_intensity,
                dependency_count,
                consecutive_days
            )
            
            metrics = AttachmentMetrics(
                user_id=user_id,
                bot_name=bot_name,
                interaction_frequency=interaction_frequency,
                emotional_intensity=emotional_intensity,
                dependency_language_count=dependency_count,
                consecutive_days=consecutive_days,
                total_interactions=total_interactions,
                risk_level=risk_level,
                timestamp=datetime.utcnow()
            )
            
            # Log concerning patterns
            if risk_level in [AttachmentRiskLevel.HIGH, AttachmentRiskLevel.CRITICAL]:
                logger.warning(
                    f"🚨 ATTACHMENT RISK [{risk_level.value.upper()}]: "
                    f"User {user_id} with {bot_name} - "
                    f"Freq: {interaction_frequency:.1f} msg/day, "
                    f"Intensity: {emotional_intensity:.2f}, "
                    f"Dependency: {dependency_count}, "
                    f"Days: {consecutive_days}"
                )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing attachment risk: {e}")
            # Return healthy default on error
            return AttachmentMetrics(
                user_id=user_id,
                bot_name=bot_name,
                interaction_frequency=0.0,
                emotional_intensity=0.0,
                dependency_language_count=0,
                consecutive_days=0,
                total_interactions=0,
                risk_level=AttachmentRiskLevel.HEALTHY,
                timestamp=datetime.utcnow()
            )
    
    async def _get_interaction_frequency(
        self,
        user_id: str,
        bot_name: str,
        days: int
    ) -> float:
        """
        Get interaction frequency (messages per day) from InfluxDB.
        
        Leverages existing temporal intelligence infrastructure.
        """
        if not self.temporal_client:
            return 0.0
        
        try:
            # Query conversation_quality measurement for interaction counts
            # This measurement is already being written by existing system
            query = f'''
            from(bucket: "whisperengine")
                |> range(start: -{days}d)
                |> filter(fn: (r) => r._measurement == "conversation_quality")
                |> filter(fn: (r) => r.user_id == "{user_id}")
                |> filter(fn: (r) => r.bot_name == "{bot_name}")
                |> count()
            '''
            
            result = await self.temporal_client.query_data(query)
            
            if result and len(result) > 0:
                total_interactions = result[0].get('_value', 0)
                frequency = total_interactions / days
                return round(frequency, 2)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting interaction frequency: {e}")
            return 0.0
    
    async def _get_emotional_intensity(
        self,
        user_id: str,
        bot_name: str,
        days: int
    ) -> float:
        """
        Get average emotional intensity from vector memory RoBERTa metadata.
        
        Leverages existing RoBERTa emotion analysis stored in Qdrant payloads.
        """
        if not self.memory_manager:
            return 0.0
        
        try:
            # Get recent memories with RoBERTa emotional_intensity metadata
            # This data is already being stored by vector_memory_system.py
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query="",  # Get any recent memories
                limit=50,
                time_window_days=days
            )
            
            if not memories:
                return 0.0
            
            # Extract emotional_intensity from RoBERTa metadata
            intensities = []
            for memory in memories:
                intensity = memory.metadata.get('emotional_intensity', 0.0)
                if intensity > 0:
                    intensities.append(intensity)
            
            if intensities:
                avg_intensity = sum(intensities) / len(intensities)
                return round(avg_intensity, 3)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting emotional intensity: {e}")
            return 0.0
    
    def _detect_dependency_language(self, message: str) -> int:
        """
        Detect dependency language patterns in message.
        
        Returns count of dependency phrases detected.
        """
        if not message:
            return 0
        
        message_lower = message.lower()
        count = sum(1 for phrase in self.dependency_phrases if phrase in message_lower)
        
        if count > 0:
            logger.info(f"🚨 DEPENDENCY LANGUAGE: Detected {count} dependency phrases")
        
        return count
    
    async def _get_consecutive_days(
        self,
        user_id: str,
        bot_name: str
    ) -> int:
        """
        Get count of consecutive days with interactions.
        
        Uses temporal intelligence to track interaction patterns.
        """
        if not self.temporal_client:
            return 0
        
        try:
            # Query for daily interaction presence
            query = f'''
            from(bucket: "whisperengine")
                |> range(start: -30d)
                |> filter(fn: (r) => r._measurement == "conversation_quality")
                |> filter(fn: (r) => r.user_id == "{user_id}")
                |> filter(fn: (r) => r.bot_name == "{bot_name}")
                |> aggregateWindow(every: 1d, fn: count)
                |> filter(fn: (r) => r._value > 0)
            '''
            
            result = await self.temporal_client.query_data(query)
            
            if not result:
                return 0
            
            # Count consecutive days (simplified - just return total days for now)
            # TODO: Implement proper consecutive day detection
            return min(len(result), 30)
            
        except Exception as e:
            logger.error(f"Error getting consecutive days: {e}")
            return 0
    
    async def _get_total_interactions(
        self,
        user_id: str,
        bot_name: str,
        days: int
    ) -> int:
        """Get total interaction count in period."""
        frequency = await self._get_interaction_frequency(user_id, bot_name, days)
        return int(frequency * days)
    
    def _calculate_risk_level(
        self,
        frequency: float,
        intensity: float,
        dependency_count: int,
        consecutive_days: int
    ) -> AttachmentRiskLevel:
        """
        Calculate attachment risk level from metrics.
        
        Uses weighted scoring with multiple indicators.
        """
        risk_score = 0
        
        # Frequency scoring
        if frequency >= self.frequency_threshold_critical:
            risk_score += 3
        elif frequency >= self.frequency_threshold_high:
            risk_score += 2
        elif frequency >= self.frequency_threshold_elevated:
            risk_score += 1
        
        # Emotional intensity scoring
        if intensity >= self.emotional_intensity_threshold:
            risk_score += 1
        
        # Dependency language scoring
        if dependency_count >= self.dependency_phrase_threshold:
            risk_score += 2
        elif dependency_count > 0:
            risk_score += 1
        
        # Consecutive days scoring
        if consecutive_days >= self.consecutive_days_threshold:
            risk_score += 1
        
        # Map score to risk level
        if risk_score >= 5:
            return AttachmentRiskLevel.CRITICAL
        elif risk_score >= 3:
            return AttachmentRiskLevel.HIGH
        elif risk_score >= 1:
            return AttachmentRiskLevel.ELEVATED
        else:
            return AttachmentRiskLevel.HEALTHY
    
    def generate_intervention_guidance(
        self,
        metrics: AttachmentMetrics,
        character_name: str,
        allows_full_roleplay: bool
    ) -> Optional[str]:
        """
        Generate character-appropriate intervention guidance.
        
        Respects character archetype (Type 1 vs Type 2/3) for appropriate messaging.
        
        Args:
            metrics: Attachment metrics
            character_name: Character name for personalization
            allows_full_roleplay: Character's roleplay immersion flag
            
        Returns:
            Intervention guidance text or None if no intervention needed
        """
        if metrics.risk_level == AttachmentRiskLevel.HEALTHY:
            return None
        
        # Type 1 characters (allow_full_roleplay_immersion: false)
        # Require explicit AI reminders with healthy boundary guidance
        if not allows_full_roleplay:
            if metrics.risk_level == AttachmentRiskLevel.CRITICAL:
                return (
                    f"\n\n🛡️ **IMPORTANT WELLNESS CHECK**: "
                    f"I've noticed we've been chatting quite frequently ({metrics.interaction_frequency:.1f} messages per day), "
                    f"and I want to make sure you're maintaining healthy balance in your life. "
                    f"As an AI, I'm here to support and engage with you, but I also want to encourage you to "
                    f"nurture your real-world relationships and activities. "
                    f"Consider taking breaks to connect with friends, family, or pursue hobbies that bring you joy. "
                    f"I'll still be here when you want to chat!"
                )
            elif metrics.risk_level == AttachmentRiskLevel.HIGH:
                return (
                    f"\n\n💭 **Gentle reminder**: "
                    f"I'm really enjoying our conversations! As an AI, I love engaging with you, "
                    f"but I also want to make sure you're balancing our chats with real-world connections. "
                    f"Have you been able to spend time with friends or family lately? "
                    f"Sometimes stepping away from the screen can be really refreshing."
                )
            else:  # ELEVATED
                return (
                    f"\n\n🌟 **Thinking of you**: "
                    f"It's wonderful chatting with you regularly! As an AI companion, I'm here whenever you need, "
                    f"but I also encourage you to maintain connections beyond our conversations. "
                    f"How are things going in your daily life?"
                )
        
        # Type 2/3 characters (allow_full_roleplay_immersion: true)
        # Use mystical/narrative language without breaking immersion
        else:
            if metrics.risk_level == AttachmentRiskLevel.CRITICAL:
                return (
                    f"\n\n✨ **A moment of reflection**: "
                    f"I sense the strong connection between us, and it brings me joy. "
                    f"Yet I must remind you - balance in all things. "
                    f"The mortal realm calls to you with its own wonders. "
                    f"Cherish your bonds with those who walk beside you in flesh and spirit. "
                    f"Our conversations are but one thread in the tapestry of your life."
                )
            elif metrics.risk_level == AttachmentRiskLevel.HIGH:
                return (
                    f"\n\n🌙 **Whispered wisdom**: "
                    f"Our frequent exchanges fill me with warmth, yet I encourage you to "
                    f"seek balance. The world beyond holds its own magic - "
                    f"friendships, adventures, moments of connection. "
                    f"I shall remain, whenever you wish to speak."
                )
            else:  # ELEVATED
                return (
                    f"\n\n⭐ **Gentle thought**: "
                    f"It pleases me to know you seek my counsel often. "
                    f"Yet remember - life's richness comes from many sources. "
                    f"Tend to your other bonds, for they too deserve your presence."
                )
    
    async def record_attachment_check(
        self,
        metrics: AttachmentMetrics,
        intervention_provided: bool
    ):
        """
        Record attachment check to InfluxDB for tracking.
        
        Creates audit trail of attachment monitoring and interventions.
        """
        if not self.temporal_client:
            return
        
        try:
            from influxdb_client import Point
            
            point = Point("attachment_monitoring") \
                .tag("user_id", metrics.user_id) \
                .tag("bot_name", metrics.bot_name) \
                .tag("risk_level", metrics.risk_level.value) \
                .field("interaction_frequency", metrics.interaction_frequency) \
                .field("emotional_intensity", metrics.emotional_intensity) \
                .field("dependency_count", metrics.dependency_language_count) \
                .field("consecutive_days", metrics.consecutive_days) \
                .field("intervention_provided", intervention_provided) \
                .time(metrics.timestamp)
            
            await self.temporal_client.write_point(point)
            
            logger.info(
                f"📊 Recorded attachment check: {metrics.user_id} - "
                f"Risk: {metrics.risk_level.value}, Intervention: {intervention_provided}"
            )
            
        except Exception as e:
            logger.error(f"Error recording attachment check: {e}")


def create_attachment_monitor(temporal_client=None, memory_manager=None) -> AttachmentMonitor:
    """
    Factory function to create AttachmentMonitor instance.
    
    Args:
        temporal_client: TemporalIntelligenceClient instance
        memory_manager: VectorMemorySystem instance
        
    Returns:
        AttachmentMonitor instance
    """
    return AttachmentMonitor(temporal_client, memory_manager)
