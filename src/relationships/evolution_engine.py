"""
Relationship Evolution Engine - Dynamic Relationship Management

Implements dynamic relationship scoring that adapts based on interaction patterns
and conversation outcomes. Makes relationships ACTUALLY EVOLVE based on user
interactions rather than remaining static.

Core Features:
- Dynamic relationship score updates after each conversation
- Simple progression/regression based on conversation quality
- RoBERTa emotion variance integration for complexity detection
- Integration with conversation quality tracking for outcomes
- PostgreSQL storage for relationship history

MVP Approach:
- Focus on making relationships update based on conversations
- Use existing conversation outcome data for quality signals
- Leverage RoBERTa emotion_variance for nuanced scoring
- Simple increment/decrement logic (can enhance later)
- No complex multi-dimensional modeling yet
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class RelationshipMetric(Enum):
    """Relationship metrics we track"""
    TRUST = "trust"
    AFFECTION = "affection"
    ATTUNEMENT = "attunement"


class ConversationQuality(Enum):
    """Conversation quality levels (from Sprint 1 TrendWise)"""
    EXCELLENT = "excellent"  # High engagement, positive sentiment
    GOOD = "good"           # Satisfactory interaction
    AVERAGE = "average"     # Standard interaction
    POOR = "poor"           # Low engagement, issues
    FAILED = "failed"       # Conversation breakdown


@dataclass
class RelationshipScores:
    """Current relationship scores for a user-bot pair"""
    user_id: str
    bot_name: str
    trust: float           # 0-1 scale
    affection: float       # 0-1 scale
    attunement: float      # 0-1 scale
    interaction_count: int
    last_updated: datetime
    created_at: datetime
    

@dataclass
class RelationshipUpdate:
    """Result of a relationship score update"""
    user_id: str
    bot_name: str
    previous_scores: RelationshipScores
    new_scores: RelationshipScores
    changes: Dict[str, float]  # metric -> delta
    conversation_quality: ConversationQuality
    emotion_complexity: float  # From RoBERTa emotion_variance
    update_reason: str
    timestamp: datetime


@dataclass
class ProgressionRates:
    """Relationship progression/regression rates"""
    trust_rate: float       # How fast trust changes per conversation
    affection_rate: float   # How fast affection changes
    attunement_rate: float  # How fast attunement changes
    complexity_modifier: float  # Adjustment based on emotional complexity


class RelationshipEvolutionEngine:
    """
    Core engine for dynamic relationship scoring.
    
    Makes relationships evolve naturally based on conversation patterns:
    - Updates trust/affection/attunement after each conversation
    - Uses Sprint 1 ConversationOutcome for quality signals
    - Leverages Sprint 2 RoBERTa emotion_variance for complexity
    - Simple increment/decrement logic with emotional nuance
    """
    
    def __init__(
        self,
        postgres_pool=None,
        temporal_client=None,
        memory_manager=None
    ):
        """
        Initialize relationship evolution engine.
        
        Args:
            postgres_pool: PostgreSQL connection pool
            temporal_client: InfluxDB temporal client (for storing events)
            memory_manager: Memory manager (for RoBERTa emotion data)
        """
        self.postgres_pool = postgres_pool
        self.temporal_client = temporal_client
        self.memory_manager = memory_manager
        self.logger = logger
        
        # Default progression rates (can be tuned)
        self.default_rates = {
            'trust_positive': 0.03,      # +0.03 per EXCELLENT conversation
            'trust_negative': -0.02,     # -0.02 per POOR conversation
            'affection_positive': 0.04,  # Affection changes faster
            'affection_negative': -0.03,
            'attunement_positive': 0.02, # Attunement changes slowest (understanding takes time)
            'attunement_negative': -0.01
        }
        
        # Emotional complexity modifiers
        self.complexity_thresholds = {
            'high_complexity': 0.5,  # emotion_variance > 0.5 = complex emotional state
            'low_complexity': 0.2     # emotion_variance < 0.2 = simple emotional state
        }
    
    async def calculate_dynamic_relationship_score(
        self,
        user_id: str,
        bot_name: str,
        conversation_quality: ConversationQuality,
        emotion_data: Optional[Dict[str, Any]] = None
    ) -> RelationshipUpdate:
        """
        Calculate and update relationship scores based on conversation outcome.
        
        This is the CORE method that makes relationships actually evolve!
        
        Args:
            user_id: User identifier
            bot_name: Bot name
            conversation_quality: Quality of recent conversation (from Sprint 1)
            emotion_data: Optional emotion analysis data (from Sprint 2 RoBERTa)
            
        Returns:
            RelationshipUpdate with previous/new scores and changes
        """
        try:
            # Get current relationship scores
            current_scores = await self._get_current_scores(user_id, bot_name)
            
            # Get progression rates (can be user-specific in future)
            rates = await self._get_progression_rates(user_id, bot_name)
            
            # Extract emotion complexity from RoBERTa data
            emotion_variance = 0.0
            if emotion_data:
                emotion_variance = emotion_data.get('emotion_variance', 0.0)
            
            # Calculate score changes based on conversation quality
            trust_delta = self._calculate_trust_change(
                conversation_quality, 
                rates, 
                emotion_variance
            )
            affection_delta = self._calculate_affection_change(
                conversation_quality,
                rates,
                emotion_variance
            )
            attunement_delta = self._calculate_attunement_change(
                conversation_quality,
                rates,
                emotion_variance
            )
            
            # Apply changes (with bounds checking)
            new_trust = max(0.0, min(1.0, current_scores.trust + trust_delta))
            new_affection = max(0.0, min(1.0, current_scores.affection + affection_delta))
            new_attunement = max(0.0, min(1.0, current_scores.attunement + attunement_delta))
            
            # Create new scores
            new_scores = RelationshipScores(
                user_id=user_id,
                bot_name=bot_name,
                trust=new_trust,
                affection=new_affection,
                attunement=new_attunement,
                interaction_count=current_scores.interaction_count + 1,
                last_updated=datetime.now(),
                created_at=current_scores.created_at
            )
            
            # Store updated scores in PostgreSQL
            await self._store_relationship_scores(new_scores)
            
            # Record update event to InfluxDB for trend analysis
            await self._record_update_event(
                user_id, 
                bot_name, 
                trust_delta, 
                affection_delta, 
                attunement_delta,
                conversation_quality,
                emotion_variance
            )
            
            # Create update result
            update = RelationshipUpdate(
                user_id=user_id,
                bot_name=bot_name,
                previous_scores=current_scores,
                new_scores=new_scores,
                changes={
                    'trust': trust_delta,
                    'affection': affection_delta,
                    'attunement': attunement_delta
                },
                conversation_quality=conversation_quality,
                emotion_complexity=emotion_variance,
                update_reason=self._generate_update_reason(
                    conversation_quality, 
                    emotion_variance,
                    trust_delta,
                    affection_delta,
                    attunement_delta
                ),
                timestamp=datetime.now()
            )
            
            self.logger.info(
                f"🔄 Relationship updated for {bot_name}/{user_id}: "
                f"trust={trust_delta:+.3f}, affection={affection_delta:+.3f}, "
                f"attunement={attunement_delta:+.3f} (quality={conversation_quality.value})"
            )
            
            return update
            
        except Exception as e:
            self.logger.error(f"Error calculating relationship score: {e}")
            raise
    
    def _calculate_trust_change(
        self,
        quality: ConversationQuality,
        rates: ProgressionRates,
        emotion_variance: float
    ) -> float:
        """
        Calculate trust score change based on conversation quality.
        
        Trust increases with good conversations, decreases with poor ones.
        High emotional complexity (emotion_variance) slows trust changes.
        """
        base_change = 0.0
        
        if quality == ConversationQuality.EXCELLENT:
            base_change = rates.trust_rate * 1.5  # Extra boost for excellent
        elif quality == ConversationQuality.GOOD:
            base_change = rates.trust_rate
        elif quality == ConversationQuality.AVERAGE:
            base_change = rates.trust_rate * 0.3  # Slight increase
        elif quality == ConversationQuality.POOR:
            base_change = -abs(rates.trust_rate) * 0.7  # Trust damaged
        elif quality == ConversationQuality.FAILED:
            base_change = -abs(rates.trust_rate) * 1.5  # Significant damage
        
        # Apply emotional complexity modifier
        # High emotion_variance = complex emotional state = slower trust changes
        if emotion_variance > self.complexity_thresholds['high_complexity']:
            complexity_modifier = 0.7  # 30% slower when emotions are complex
        elif emotion_variance < self.complexity_thresholds['low_complexity']:
            complexity_modifier = 1.2  # 20% faster when emotions are clear
        else:
            complexity_modifier = 1.0
        
        return base_change * complexity_modifier
    
    def _calculate_affection_change(
        self,
        quality: ConversationQuality,
        rates: ProgressionRates,
        emotion_variance: float
    ) -> float:
        """
        Calculate affection score change.
        
        Affection responds to emotional connection and engagement.
        Changes faster than trust (easier to like/dislike than trust/distrust).
        """
        base_change = 0.0
        
        if quality == ConversationQuality.EXCELLENT:
            base_change = rates.affection_rate * 1.3
        elif quality == ConversationQuality.GOOD:
            base_change = rates.affection_rate
        elif quality == ConversationQuality.AVERAGE:
            base_change = rates.affection_rate * 0.2  # Slight increase
        elif quality == ConversationQuality.POOR:
            base_change = -abs(rates.affection_rate) * 0.8
        elif quality == ConversationQuality.FAILED:
            base_change = -abs(rates.affection_rate) * 1.3
        
        # Affection is less affected by emotional complexity
        # (you can like someone even when emotions are confusing)
        if emotion_variance > self.complexity_thresholds['high_complexity']:
            complexity_modifier = 0.9
        else:
            complexity_modifier = 1.0
        
        return base_change * complexity_modifier
    
    def _calculate_attunement_change(
        self,
        quality: ConversationQuality,
        rates: ProgressionRates,
        emotion_variance: float
    ) -> float:
        """
        Calculate attunement score change.
        
        Attunement = how well the bot understands the user.
        Changes slowest (understanding takes time and consistency).
        """
        base_change = 0.0
        
        if quality == ConversationQuality.EXCELLENT:
            base_change = rates.attunement_rate * 1.5  # Excellent conversations show understanding
        elif quality == ConversationQuality.GOOD:
            base_change = rates.attunement_rate
        elif quality == ConversationQuality.AVERAGE:
            base_change = rates.attunement_rate * 0.5  # Slow progress
        elif quality == ConversationQuality.POOR:
            base_change = -abs(rates.attunement_rate) * 0.5  # Misunderstanding
        elif quality == ConversationQuality.FAILED:
            base_change = -abs(rates.attunement_rate) * 1.0  # Clear misunderstanding
        
        # High emotional complexity can actually increase attunement 
        # (successfully navigating complex emotions shows deep understanding)
        if emotion_variance > self.complexity_thresholds['high_complexity']:
            if quality in [ConversationQuality.EXCELLENT, ConversationQuality.GOOD]:
                complexity_modifier = 1.2  # Bonus for handling complexity well
            else:
                complexity_modifier = 0.8  # Penalty for failing with complexity
        else:
            complexity_modifier = 1.0
        
        return base_change * complexity_modifier
    
    async def _get_current_scores(
        self,
        user_id: str,
        bot_name: str
    ) -> RelationshipScores:
        """Get current relationship scores from PostgreSQL."""
        if not self.postgres_pool:
            # Return default scores if no database
            return self._default_scores(user_id, bot_name)
        
        try:
            async with self.postgres_pool.acquire() as conn:
                # Query relationship_scores table
                row = await conn.fetchrow("""
                    SELECT trust, affection, attunement, interaction_count, 
                           last_updated, created_at
                    FROM relationship_scores
                    WHERE user_id = $1 AND bot_name = $2
                """, user_id, bot_name)
                
                if row:
                    return RelationshipScores(
                        user_id=user_id,
                        bot_name=bot_name,
                        trust=float(row['trust']),
                        affection=float(row['affection']),
                        attunement=float(row['attunement']),
                        interaction_count=row['interaction_count'],
                        last_updated=row['last_updated'],
                        created_at=row['created_at']
                    )
                else:
                    # First interaction - return defaults
                    return self._default_scores(user_id, bot_name)
                    
        except Exception as e:
            self.logger.error(f"Error fetching relationship scores: {e}")
            return self._default_scores(user_id, bot_name)
    
    def _default_scores(self, user_id: str, bot_name: str) -> RelationshipScores:
        """Return default relationship scores for new relationships."""
        return RelationshipScores(
            user_id=user_id,
            bot_name=bot_name,
            trust=0.5,        # Neutral starting trust
            affection=0.4,    # Slight positive initial impression
            attunement=0.3,   # Understanding starts low (needs time)
            interaction_count=0,
            last_updated=datetime.now(),
            created_at=datetime.now()
        )
    
    async def _get_progression_rates(
        self,
        user_id: str,
        bot_name: str
    ) -> ProgressionRates:
        """
        Get relationship progression rates.
        
        For MVP, returns default rates. Future enhancement:
        could be user-specific or learned from patterns.
        """
        return ProgressionRates(
            trust_rate=self.default_rates['trust_positive'],
            affection_rate=self.default_rates['affection_positive'],
            attunement_rate=self.default_rates['attunement_positive'],
            complexity_modifier=1.0
        )
    
    async def _store_relationship_scores(
        self,
        scores: RelationshipScores
    ) -> None:
        """Store updated relationship scores in PostgreSQL."""
        if not self.postgres_pool:
            self.logger.warning("No PostgreSQL pool - relationship scores not persisted")
            return
        
        try:
            async with self.postgres_pool.acquire() as conn:
                # Upsert relationship_scores
                await conn.execute("""
                    INSERT INTO relationship_scores 
                        (user_id, bot_name, trust, affection, attunement, 
                         interaction_count, last_updated, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (user_id, bot_name)
                    DO UPDATE SET
                        trust = EXCLUDED.trust,
                        affection = EXCLUDED.affection,
                        attunement = EXCLUDED.attunement,
                        interaction_count = EXCLUDED.interaction_count,
                        last_updated = EXCLUDED.last_updated
                """, 
                scores.user_id, scores.bot_name, scores.trust, scores.affection,
                scores.attunement, scores.interaction_count, scores.last_updated,
                scores.created_at
                )
                
        except Exception as e:
            self.logger.error(f"Error storing relationship scores: {e}")
            raise
    
    async def _record_update_event(
        self,
        user_id: str,
        bot_name: str,
        trust_delta: float,
        affection_delta: float,
        attunement_delta: float,
        quality: ConversationQuality,
        emotion_variance: float
    ) -> None:
        """Record relationship update event to InfluxDB for trend analysis."""
        if not self.temporal_client:
            return
        
        try:
            # Map conversation quality to interaction_quality score
            quality_mapping = {
                ConversationQuality.EXCELLENT: 0.9,
                ConversationQuality.GOOD: 0.75,
                ConversationQuality.AVERAGE: 0.5,
                ConversationQuality.POOR: 0.3,
                ConversationQuality.FAILED: 0.1
            }
            interaction_quality = quality_mapping.get(quality, 0.5)
            
            # Calculate communication_comfort from emotion variance
            # Low variance = comfortable (stable emotions)
            # High variance = uncomfortable (volatile emotions)
            communication_comfort = max(0.0, 1.0 - emotion_variance)
            
            # Get current scores for absolute values
            current_scores = await self._get_current_scores(user_id, bot_name)
            
            # Create RelationshipMetrics with calculated values
            from src.temporal.temporal_intelligence_client import RelationshipMetrics
            
            metrics = RelationshipMetrics(
                trust_level=float(current_scores.trust),
                affection_level=float(current_scores.affection),
                attunement_level=float(current_scores.attunement),
                interaction_quality=interaction_quality,
                communication_comfort=communication_comfort
            )
            
            # Record to InfluxDB
            await self.temporal_client.record_relationship_progression(
                bot_name=bot_name,
                user_id=user_id,
                relationship_metrics=metrics,
                session_id=None,
                timestamp=datetime.now()
            )
            
            self.logger.debug(
                f"📊 Recorded relationship progression to InfluxDB: "
                f"{bot_name}/{user_id} (trust={current_scores.trust:.2f})"
            )
            
        except Exception as e:
            self.logger.debug(f"Failed to record relationship update to InfluxDB: {e}")
            # Don't raise - InfluxDB recording is supplementary
    
    def _generate_update_reason(
        self,
        quality: ConversationQuality,
        emotion_variance: float,
        trust_delta: float,
        affection_delta: float,
        attunement_delta: float
    ) -> str:
        """Generate human-readable reason for relationship update."""
        reason_parts = []
        
        # Quality-based reason
        if quality == ConversationQuality.EXCELLENT:
            reason_parts.append("excellent conversation quality")
        elif quality == ConversationQuality.GOOD:
            reason_parts.append("good conversation quality")
        elif quality == ConversationQuality.AVERAGE:
            reason_parts.append("average conversation quality")
        elif quality == ConversationQuality.POOR:
            reason_parts.append("poor conversation quality")
        elif quality == ConversationQuality.FAILED:
            reason_parts.append("failed conversation")
        
        # Emotion complexity
        if emotion_variance > self.complexity_thresholds['high_complexity']:
            reason_parts.append("high emotional complexity")
        elif emotion_variance < self.complexity_thresholds['low_complexity']:
            reason_parts.append("clear emotional state")
        
        # Significant changes
        if abs(trust_delta) > 0.05:
            direction = "increased" if trust_delta > 0 else "decreased"
            reason_parts.append(f"trust {direction} significantly")
        
        return "; ".join(reason_parts) if reason_parts else "routine update"


# Factory function for dependency injection
def create_relationship_evolution_engine(
    postgres_pool=None,
    temporal_client=None,
    memory_manager=None
) -> RelationshipEvolutionEngine:
    """
    Factory function to create RelationshipEvolutionEngine instance.
    
    Args:
        postgres_pool: PostgreSQL connection pool
        temporal_client: InfluxDB temporal client
        memory_manager: Memory manager instance
        
    Returns:
        Configured RelationshipEvolutionEngine instance
    """
    return RelationshipEvolutionEngine(
        postgres_pool=postgres_pool,
        temporal_client=temporal_client,
        memory_manager=memory_manager
    )
