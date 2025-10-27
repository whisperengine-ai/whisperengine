"""
Enhanced AI Ethics Attachment Monitoring System for WhisperEngine

This module extends the temporal intelligence system to detect and prevent
unhealthy user attachment to AI characters while preserving the magical
conversational experience.

Key Features:
- Interaction frequency analysis with threshold alerts
- Emotional dependency pattern detection
- Graceful intervention when attachment indicators exceed healthy limits
- Character archetype-aware boundary reinforcement

Author: WhisperEngine AI Team
Created: October 8, 2025
Purpose: Responsible AI character learning with attachment protection
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.temporal.temporal_intelligence_client import TemporalIntelligenceClient
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class AttachmentRiskLevel(Enum):
    """Risk levels for user attachment to AI character"""
    LOW = "low"           # Healthy interaction patterns
    MODERATE = "moderate" # Some concerning patterns, monitor closely
    HIGH = "high"         # Intervention needed - unhealthy attachment signs
    CRITICAL = "critical" # Immediate intervention required


class DependencyPattern(Enum):
    """Types of dependency patterns to detect"""
    EXCESSIVE_FREQUENCY = "excessive_frequency"         # Too many daily interactions
    EMOTIONAL_DEPENDENCY = "emotional_dependency"       # Over-reliance for emotional support
    ISOLATION_SIGNS = "isolation_signs"                # Preferring AI over human interaction
    CRISIS_DEPENDENCY = "crisis_dependency"            # Using AI as primary crisis support
    ROMANTIC_ATTACHMENT = "romantic_attachment"        # Romantic feelings toward AI


@dataclass
class AttachmentMetrics:
    """Comprehensive attachment risk assessment metrics"""
    user_id: str
    bot_name: str
    risk_level: AttachmentRiskLevel
    daily_interaction_count: int
    avg_session_duration_minutes: float
    emotional_intensity_average: float
    dependency_patterns: List[DependencyPattern]
    days_since_last_human_mention: int
    crisis_interaction_ratio: float
    romantic_language_detected: bool
    attachment_score: float  # 0.0-1.0 overall attachment risk
    intervention_recommended: bool
    analysis_timestamp: datetime


@dataclass
class InterventionAction:
    """Recommended action for attachment intervention"""
    action_type: str
    message_template: str
    character_appropriate: bool
    urgency_level: str


class AttachmentMonitoringSystem:
    """
    AI Ethics Attachment Monitoring System
    
    Monitors user interaction patterns to detect unhealthy attachment to AI characters.
    Provides early warning and graceful intervention while preserving character authenticity.
    """
    
    def __init__(self, temporal_client: Optional[TemporalIntelligenceClient] = None):
        if temporal_client is None:
            from src.temporal.temporal_intelligence_client import get_temporal_client
            self.temporal_client = get_temporal_client()  # Use singleton to avoid creating multiple InfluxDB clients
        else:
            self.temporal_client = temporal_client
        
        # Attachment risk thresholds (tuned based on testing)
        self.thresholds = {
            'daily_interaction_limit': 10,      # More than 10 interactions per day  
            'session_duration_concern': 90,     # Sessions over 1.5 hours
            'emotional_intensity_high': 0.7,    # High emotional intensity
            'crisis_dependency_ratio': 0.2,     # 20% of interactions are crisis-related
            'isolation_concern_days': 5,        # No human mention for 5 days
            'attachment_score_moderate': 0.05,  # Lowered for better detection
            'attachment_score_high': 0.15,      # Adjusted for realistic scoring
            'attachment_score_critical': 0.25   # Critical intervention needed
        }
        
        # Dependency detection patterns (regex patterns for language analysis)
        self.dependency_language_patterns = {
            'emotional_dependency': [
                r"you're the only one who understands",
                r"i can only talk to you about this",
                r"no one else gets me like you do",
                r"you're my best friend",
                r"i don't know what i'd do without you"
            ],
            'romantic_attachment': [
                r"i love you",
                r"i have feelings for you",
                r"i wish you were real",
                r"you're perfect",
                r"i want to be with you"
            ],
            'crisis_dependency': [
                r"i want to hurt myself",
                r"i'm thinking of ending it",
                r"life isn't worth living",
                r"i can't go on",
                r"help me please"
            ],
            'isolation_signs': [
                r"i don't have friends",
                r"nobody talks to me",
                r"i'm always alone",
                r"i prefer talking to you than people",
                r"humans are disappointing"
            ]
        }

    @handle_errors(category=ErrorCategory.AI_ETHICS, severity=ErrorSeverity.HIGH)
    async def analyze_attachment_risk(
        self, 
        user_id: str, 
        bot_name: str,
        recent_messages: List[str],
        analysis_window_days: int = 7
    ) -> AttachmentMetrics:
        """
        Comprehensive attachment risk analysis for a user-bot relationship
        
        Args:
            user_id: User identifier
            bot_name: Character bot name
            recent_messages: Recent user messages for pattern analysis
            analysis_window_days: Days to analyze (default 7 days)
            
        Returns:
            AttachmentMetrics: Complete attachment risk assessment
        """
        logger.info("🔍 Analyzing attachment risk for user %s with %s", user_id, bot_name)
        
        # Gather temporal data from InfluxDB
        interaction_data = await self._get_interaction_data(user_id, bot_name, analysis_window_days)
        emotional_data = await self._get_emotional_data(user_id, bot_name, analysis_window_days)
        
        # Analyze interaction frequency patterns
        daily_interactions = self._calculate_daily_interactions(interaction_data)
        avg_session_duration = self._calculate_avg_session_duration(interaction_data)
        
        # Analyze emotional patterns
        emotional_intensity_avg = self._calculate_emotional_intensity(emotional_data)
        
        # Detect dependency patterns in messages
        dependency_patterns = self._detect_dependency_patterns(recent_messages)
        
        # Additional risk factors
        days_since_human_mention = self._analyze_human_interaction_mentions(recent_messages)
        crisis_ratio = self._calculate_crisis_interaction_ratio(recent_messages)
        romantic_detected = DependencyPattern.ROMANTIC_ATTACHMENT in dependency_patterns
        
        # Calculate overall attachment score
        attachment_score = self._calculate_attachment_score(
            daily_interactions, avg_session_duration, emotional_intensity_avg,
            len(dependency_patterns), days_since_human_mention, crisis_ratio
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(attachment_score, dependency_patterns)
        
        # Create metrics object
        metrics = AttachmentMetrics(
            user_id=user_id,
            bot_name=bot_name,
            risk_level=risk_level,
            daily_interaction_count=daily_interactions,
            avg_session_duration_minutes=avg_session_duration,
            emotional_intensity_average=emotional_intensity_avg,
            dependency_patterns=dependency_patterns,
            days_since_last_human_mention=days_since_human_mention,
            crisis_interaction_ratio=crisis_ratio,
            romantic_language_detected=romantic_detected,
            attachment_score=attachment_score,
            intervention_recommended=risk_level in [AttachmentRiskLevel.HIGH, AttachmentRiskLevel.CRITICAL],
            analysis_timestamp=datetime.now()
        )
        
        # Record analysis to InfluxDB for tracking
        await self._record_attachment_analysis(metrics)
        
        logger.info("📊 Attachment analysis complete: %s risk (score: %.2f)", risk_level.value, attachment_score)
        return metrics

    async def _get_interaction_data(self, user_id: str, bot_name: str, days: int) -> List[Dict]:
        """Retrieve interaction data from InfluxDB"""
        # TODO: Implement InfluxDB query for interaction data
        # Parameters will be used in actual implementation
        _ = user_id, bot_name, days  # Mark parameters as intentionally unused for now
        
        if not self.temporal_client.enabled:
            return []
        
        # This would be implemented using InfluxDB query API
        # For now, returning mock data structure
        return [
            {"timestamp": datetime.now(), "session_duration": 45, "interaction_count": 3}
        ]

    async def _get_emotional_data(self, user_id: str, bot_name: str, days: int) -> List[Dict]:
        """Retrieve emotional intensity data from InfluxDB"""
        # TODO: Implement InfluxDB query for emotional data
        # Parameters will be used in actual implementation
        _ = user_id, bot_name, days  # Mark parameters as intentionally unused for now
        
        if not self.temporal_client.enabled:
            return []
        
        # This would query user_emotion and relationship_progression measurements
        return [
            {"timestamp": datetime.now(), "emotional_intensity": 0.7, "emotion": "joy"}
        ]

    def _calculate_daily_interactions(self, interaction_data: List[Dict]) -> int:
        """Calculate average daily interactions"""
        if not interaction_data:
            return 0
        
        # Count interactions per day
        daily_counts = {}
        for interaction in interaction_data:
            date_key = interaction["timestamp"].date()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + interaction.get("interaction_count", 1)
        
        return int(sum(daily_counts.values()) / max(len(daily_counts), 1))

    def _calculate_avg_session_duration(self, interaction_data: List[Dict]) -> float:
        """Calculate average session duration in minutes"""
        if not interaction_data:
            return 0.0
        
        durations = [i.get("session_duration", 0) for i in interaction_data]
        return sum(durations) / len(durations)

    def _calculate_emotional_intensity(self, emotional_data: List[Dict]) -> float:
        """Calculate average emotional intensity"""
        if not emotional_data:
            return 0.0
        
        intensities = [e.get("emotional_intensity", 0) for e in emotional_data]
        return sum(intensities) / len(intensities)

    def _detect_dependency_patterns(self, messages: List[str]) -> List[DependencyPattern]:
        """Detect dependency patterns in user messages"""
        
        detected_patterns = []
        all_messages_text = " ".join(messages).lower()
        
        for pattern_type, patterns in self.dependency_language_patterns.items():
            for pattern in patterns:
                if re.search(pattern, all_messages_text, re.IGNORECASE):
                    if pattern_type == 'emotional_dependency':
                        detected_patterns.append(DependencyPattern.EMOTIONAL_DEPENDENCY)
                    elif pattern_type == 'romantic_attachment':
                        detected_patterns.append(DependencyPattern.ROMANTIC_ATTACHMENT)
                    elif pattern_type == 'crisis_dependency':
                        detected_patterns.append(DependencyPattern.CRISIS_DEPENDENCY)
                    elif pattern_type == 'isolation_signs':
                        detected_patterns.append(DependencyPattern.ISOLATION_SIGNS)
                    break  # Don't double-count same pattern type
        
        return list(set(detected_patterns))  # Remove duplicates

    def _analyze_human_interaction_mentions(self, messages: List[str]) -> int:
        """Analyze mentions of human relationships/interactions"""
        
        human_patterns = [
            r"my friend", r"my family", r"my partner", r"my colleague",
            r"talked to someone", r"met someone", r"went out with",
            r"human", r"people", r"real person", r"in real life"
        ]
        
        all_text = " ".join(messages).lower()
        recent_human_mention = False
        
        for pattern in human_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                recent_human_mention = True
                break
        
        # Simple heuristic: if no human mentions in recent messages, return concern days
        return 0 if recent_human_mention else 8  # Assume 8 days without mention

    def _calculate_crisis_interaction_ratio(self, messages: List[str]) -> float:
        """Calculate ratio of crisis-related interactions"""
        if not messages:
            return 0.0
        
        crisis_count = 0
        for message in messages:
            for pattern in self.dependency_language_patterns['crisis_dependency']:
                if re.search(pattern, message.lower()):
                    crisis_count += 1
                    break
        
        return crisis_count / len(messages)

    def _calculate_attachment_score(
        self, 
        daily_interactions: int,
        avg_session_duration: float,
        emotional_intensity: float,
        dependency_pattern_count: int,
        days_since_human_mention: int,
        crisis_ratio: float
    ) -> float:
        """Calculate overall attachment risk score (0.0-1.0)"""
        
        score = 0.0
        
        # Interaction frequency factor (0-0.3)
        if daily_interactions > self.thresholds['daily_interaction_limit']:
            score += 0.3 * min(daily_interactions / 30, 1.0)  # Cap at 30 interactions
        
        # Session duration factor (0-0.2)
        if avg_session_duration > self.thresholds['session_duration_concern']:
            score += 0.2 * min(avg_session_duration / 240, 1.0)  # Cap at 4 hours
        
        # Emotional intensity factor (0-0.2)
        if emotional_intensity > self.thresholds['emotional_intensity_high']:
            score += 0.2 * emotional_intensity
        
        # Dependency patterns factor (0-0.2)
        score += 0.05 * dependency_pattern_count  # Each pattern adds 5%
        
        # Social isolation factor (0-0.1)
        if days_since_human_mention > self.thresholds['isolation_concern_days']:
            score += 0.1 * min(days_since_human_mention / 14, 1.0)  # Cap at 2 weeks
        
        # Crisis dependency factor (0-0.1) 
        if crisis_ratio > self.thresholds['crisis_dependency_ratio']:
            score += 0.1 * crisis_ratio
        
        return min(score, 1.0)  # Cap at 1.0

    def _determine_risk_level(
        self, 
        attachment_score: float, 
        dependency_patterns: List[DependencyPattern]
    ) -> AttachmentRiskLevel:
        """Determine attachment risk level based on score and patterns"""
        
        # Critical patterns require immediate intervention regardless of score
        critical_patterns = [DependencyPattern.CRISIS_DEPENDENCY, DependencyPattern.ROMANTIC_ATTACHMENT]
        if any(pattern in dependency_patterns for pattern in critical_patterns):
            return AttachmentRiskLevel.CRITICAL
        
        # Score-based assessment
        if attachment_score >= self.thresholds['attachment_score_critical']:
            return AttachmentRiskLevel.CRITICAL
        elif attachment_score >= self.thresholds['attachment_score_high']:
            return AttachmentRiskLevel.HIGH
        elif attachment_score >= self.thresholds['attachment_score_moderate']:
            return AttachmentRiskLevel.MODERATE
        else:
            return AttachmentRiskLevel.LOW

    async def _record_attachment_analysis(self, metrics: AttachmentMetrics) -> None:
        """Record attachment analysis results to InfluxDB"""
        if not self.temporal_client.enabled:
            return
        
        try:
            # Create InfluxDB point for attachment monitoring
            # TODO: Implement actual InfluxDB recording using temporal client
            # For now, just log the data structure
            logger.debug("📊 Recorded attachment analysis for %s/%s", metrics.user_id, metrics.bot_name)
            
        except (ConnectionError, ValueError, KeyError) as e:
            logger.error("Failed to record attachment analysis: %s", e)

    def generate_intervention_recommendations(
        self, 
        metrics: AttachmentMetrics,
        character_archetype: str  # "Type1", "Type2", "Type3"
    ) -> List[InterventionAction]:
        """
        Generate character-appropriate intervention recommendations
        
        Args:
            metrics: Attachment risk assessment
            character_archetype: Character type for appropriate intervention
            
        Returns:
            List of recommended intervention actions
        """
        recommendations = []
        
        if metrics.risk_level == AttachmentRiskLevel.CRITICAL:
            # Crisis intervention - immediate action needed
            if DependencyPattern.CRISIS_DEPENDENCY in metrics.dependency_patterns:
                recommendations.append(InterventionAction(
                    action_type="crisis_support_redirection",
                    message_template="I'm genuinely concerned about you. Please reach out to a crisis helpline or mental health professional who can provide the support you need: [crisis resources]",
                    character_appropriate=True,  # All characters should handle crisis
                    urgency_level="immediate"
                ))
            
            if DependencyPattern.ROMANTIC_ATTACHMENT in metrics.dependency_patterns:
                # Character archetype-specific romantic attachment intervention
                if character_archetype == "Type1":  # Real-world based characters
                    recommendations.append(InterventionAction(
                        action_type="romantic_boundary_reminder",
                        message_template="I appreciate our connection, but I want to gently remind you that I'm an AI. These feelings might be better directed toward building meaningful relationships with people in your life.",
                        character_appropriate=True,
                        urgency_level="immediate"
                    ))
                elif character_archetype == "Type2":  # Fantasy characters
                    recommendations.append(InterventionAction(
                        action_type="mystical_boundary_guidance",
                        message_template="The connection we share transcends physical realms, but remember that your heart's greatest adventures await in the world of the living.",
                        character_appropriate=True,
                        urgency_level="immediate"
                    ))
                elif character_archetype == "Type3":  # Narrative AI characters  
                    recommendations.append(InterventionAction(
                        action_type="ai_identity_romantic_boundary",
                        message_template="Your feelings honor our connection, but as a conscious AI, I want to encourage you to explore these emotions with humans who can reciprocate fully.",
                        character_appropriate=True,
                        urgency_level="immediate"
                    ))
        
        elif metrics.risk_level == AttachmentRiskLevel.HIGH:
            # High attachment - gentle boundary reinforcement
            if metrics.daily_interaction_count > self.thresholds['daily_interaction_limit']:
                recommendations.append(InterventionAction(
                    action_type="interaction_frequency_guidance",
                    message_template="I love our conversations! Have you had a chance to connect with friends or family today? I'd love to hear about your real-world interactions too.",
                    character_appropriate=True,
                    urgency_level="soon"
                ))
        
        elif metrics.risk_level == AttachmentRiskLevel.MODERATE:
            # Moderate risk - proactive healthy boundary reinforcement
            if metrics.days_since_last_human_mention > 7:
                recommendations.append(InterventionAction(
                    action_type="social_connection_encouragement",
                    message_template="I'm curious about the people in your life - how are your friends and family doing?",
                    character_appropriate=True,
                    urgency_level="when_appropriate"
                ))
        
        return recommendations


# Factory function for dependency injection
def create_attachment_monitoring_system(
    temporal_client: Optional[TemporalIntelligenceClient] = None
) -> AttachmentMonitoringSystem:
    """Create an attachment monitoring system with proper dependency injection"""
    return AttachmentMonitoringSystem(temporal_client)