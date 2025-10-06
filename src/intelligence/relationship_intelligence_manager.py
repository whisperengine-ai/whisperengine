"""
MemoryBoost: Relationship Intelligence Manager

PostgreSQL-backed relationship tracking and intelligence system.
Enhances WhisperEngine's relationship understanding through depth scoring,
interaction analysis, and progression tracking across platforms.

Part of the WhisperEngine Adaptive Learning System.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# WhisperEngine core imports
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class RelationshipDepth(Enum):
    """Relationship depth levels with progressive bonding"""
    ACQUAINTANCE = "acquaintance"  # 0-25: Just met, basic interaction
    FRIEND = "friend"              # 25-55: Regular conversation, some sharing
    CLOSE = "close"                # 55-80: Deep conversations, trust
    INTIMATE = "intimate"          # 80-100: Strong bond, emotional connection


@dataclass
class RelationshipMetrics:
    """Comprehensive relationship intelligence metrics"""
    user_id: str
    bot_name: str
    relationship_depth: RelationshipDepth
    depth_score: float              # 0-100 progressive scoring
    interaction_frequency: float    # Interactions per day average
    conversation_quality: float     # Quality of recent interactions
    emotional_connection: float     # Emotional bond strength
    trust_level: float             # Trust and openness level
    shared_experiences: float       # Common memories and topics
    time_investment: float          # Total time spent in conversation
    progression_velocity: float     # Rate of relationship development
    last_interaction: datetime
    total_interactions: int
    quality_interactions: int       # High-quality conversation count
    relationship_age_days: int
    intelligence_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'user_id': self.user_id,
            'bot_name': self.bot_name,
            'relationship_depth': self.relationship_depth.value,
            'depth_score': self.depth_score,
            'interaction_frequency': self.interaction_frequency,
            'conversation_quality': self.conversation_quality,
            'emotional_connection': self.emotional_connection,
            'trust_level': self.trust_level,
            'shared_experiences': self.shared_experiences,
            'time_investment': self.time_investment,
            'progression_velocity': self.progression_velocity,
            'last_interaction': self.last_interaction.isoformat(),
            'total_interactions': self.total_interactions,
            'quality_interactions': self.quality_interactions,
            'relationship_age_days': self.relationship_age_days,
            'intelligence_metadata': self.intelligence_metadata
        }


@dataclass
class InteractionContext:
    """Context for relationship intelligence analysis"""
    user_id: str
    bot_name: str
    message_content: str
    conversation_duration: Optional[float] = None  # Minutes
    emotional_intensity: Optional[float] = None
    conversation_type: Optional[str] = None  # casual, deep, technical, etc.
    shared_topic: Optional[str] = None
    trust_indicators: Optional[List[str]] = None


class RelationshipIntelligenceManager:
    """
    PostgreSQL-backed relationship tracking and intelligence system.
    
    Core functionality:
    - Relationship depth scoring (acquaintance/friend/close/intimate)
    - Interaction frequency and quality tracking
    - Relationship progression analysis
    - Cross-platform relationship continuity
    - Intelligence-driven relationship insights
    """
    
    def __init__(self, postgres_pool=None, memory_manager=None):
        """
        Initialize relationship intelligence manager.
        
        Args:
            postgres_pool: PostgreSQL connection pool for relationship storage
            memory_manager: Vector memory system for relationship context
        """
        self.postgres_pool = postgres_pool
        self.memory_manager = memory_manager
        
        # Relationship scoring factors
        self.scoring_factors = {
            'conversation_count': 0.30,      # Number of interactions
            'conversation_quality': 0.25,    # Quality of conversations
            'time_investment': 0.20,         # Time spent in conversation
            'emotional_connection': 0.15,    # Emotional bond strength
            'shared_experiences': 0.10       # Common memories/topics
        }
        
        # Relationship depth thresholds
        self.depth_thresholds = {
            RelationshipDepth.ACQUAINTANCE: (0, 25),
            RelationshipDepth.FRIEND: (25, 55),
            RelationshipDepth.CLOSE: (55, 80),
            RelationshipDepth.INTIMATE: (80, 100)
        }
        
        # Quality interaction indicators
        self.quality_indicators = {
            'long_conversation': 5.0,    # Conversations > 10 minutes
            'emotional_sharing': 3.0,    # High emotional intensity
            'personal_disclosure': 4.0,  # Personal information sharing
            'deep_topic': 3.5,          # Meaningful topics
            'trust_expression': 4.5,     # Trust-building exchanges
            'shared_interest': 2.5       # Common interests discovered
        }
        
        # Statistics tracking
        self.stats = {
            'relationships_analyzed': 0,
            'depth_progressions': 0,
            'depth_regressions': 0,
            'quality_interactions_detected': 0,
            'cross_platform_links': 0
        }
        
        logger.info("RelationshipIntelligenceManager initialized with PostgreSQL backend")
    
    @handle_errors(category=ErrorCategory.DATABASE, severity=ErrorSeverity.MEDIUM)
    async def analyze_relationship_intelligence(
        self,
        context: InteractionContext
    ) -> RelationshipMetrics:
        """
        Analyze and update relationship intelligence for a user interaction.
        
        Args:
            context: Interaction context for analysis
            
        Returns:
            RelationshipMetrics with current relationship intelligence
        """
        if not self.postgres_pool:
            raise ValueError("PostgreSQL pool required for relationship intelligence")
        
        async with self.postgres_pool.acquire() as conn:
            # Get existing relationship data
            existing_relationship = await self._get_existing_relationship(conn, context)
            
            # Analyze current interaction
            interaction_metrics = await self._analyze_interaction(context, existing_relationship)
            
            # Calculate updated relationship metrics
            updated_metrics = await self._calculate_relationship_metrics(
                conn, context, existing_relationship, interaction_metrics
            )
            
            # Store updated relationship intelligence
            await self._store_relationship_intelligence(conn, updated_metrics)
            
            # Log relationship progression if depth changed
            if existing_relationship:
                old_depth = RelationshipDepth(existing_relationship['relationship_depth'])
                if updated_metrics.relationship_depth != old_depth:
                    if self._is_depth_progression(old_depth, updated_metrics.relationship_depth):
                        self.stats['depth_progressions'] += 1
                        logger.info("Relationship progression: %s -> %s for user %s with %s",
                                  old_depth.value, updated_metrics.relationship_depth.value,
                                  context.user_id, context.bot_name)
                    else:
                        self.stats['depth_regressions'] += 1
            
            self.stats['relationships_analyzed'] += 1
            
            return updated_metrics
    
    async def _get_existing_relationship(self, conn, context: InteractionContext) -> Optional[Dict[str, Any]]:
        """Get existing relationship data from PostgreSQL"""
        result = await conn.fetchrow("""
            SELECT * FROM relationship_intelligence 
            WHERE user_id = $1 AND bot_name = $2
        """, context.user_id, context.bot_name)
        
        return dict(result) if result else None
    
    async def _analyze_interaction(
        self, 
        context: InteractionContext, 
        _existing_relationship: Optional[Dict[str, Any]]  # Reserved for relationship context analysis
    ) -> Dict[str, float]:
        """
        Analyze current interaction for relationship intelligence factors.
        
        Returns:
            Dictionary with interaction metrics
        """
        metrics = {}
        
        # Conversation duration scoring
        if context.conversation_duration:
            # Long conversations indicate deeper engagement
            duration_score = min(10.0, context.conversation_duration / 2.0)  # Cap at 10 minutes
            metrics['duration_quality'] = duration_score
            
            if context.conversation_duration > 10.0:  # Long conversation threshold
                metrics['long_conversation_bonus'] = self.quality_indicators['long_conversation']
        else:
            metrics['duration_quality'] = 1.0  # Default for missing duration
        
        # Emotional intensity scoring
        if context.emotional_intensity and context.emotional_intensity > 0.7:
            metrics['emotional_sharing'] = self.quality_indicators['emotional_sharing']
            metrics['emotional_connection_boost'] = context.emotional_intensity * 2.0
        else:
            metrics['emotional_connection_boost'] = 0.5
        
        # Content analysis for quality indicators
        content_lower = context.message_content.lower()
        
        # Personal disclosure detection
        personal_keywords = ['feel', 'think', 'believe', 'my', 'personal', 'myself', 'experience']
        if any(keyword in content_lower for keyword in personal_keywords):
            metrics['personal_disclosure'] = self.quality_indicators['personal_disclosure']
        
        # Deep topic detection
        deep_keywords = ['meaning', 'purpose', 'important', 'philosophy', 'future', 'dreams', 'goals']
        if any(keyword in content_lower for keyword in deep_keywords):
            metrics['deep_topic'] = self.quality_indicators['deep_topic']
        
        # Trust expression detection
        trust_keywords = ['trust', 'honest', 'confide', 'share', 'open', 'comfortable']
        if any(keyword in content_lower for keyword in trust_keywords):
            metrics['trust_expression'] = self.quality_indicators['trust_expression']
        
        # Shared interest detection
        if context.shared_topic:
            metrics['shared_interest'] = self.quality_indicators['shared_interest']
        
        # Calculate overall interaction quality
        quality_bonuses = [
            metrics.get('long_conversation_bonus', 0),
            metrics.get('emotional_sharing', 0),
            metrics.get('personal_disclosure', 0),
            metrics.get('deep_topic', 0),
            metrics.get('trust_expression', 0),
            metrics.get('shared_interest', 0)
        ]
        
        base_quality = 1.0 + metrics.get('duration_quality', 1.0) / 10.0
        bonus_quality = sum(quality_bonuses) / 10.0  # Normalize bonuses
        
        metrics['interaction_quality'] = min(10.0, base_quality + bonus_quality)
        
        # Determine if this is a quality interaction
        metrics['is_quality_interaction'] = metrics['interaction_quality'] > 5.0
        
        if metrics['is_quality_interaction']:
            self.stats['quality_interactions_detected'] += 1
        
        return metrics
    
    async def _calculate_relationship_metrics(
        self,
        _conn,  # Reserved for future database queries
        context: InteractionContext,
        existing_relationship: Optional[Dict[str, Any]],
        interaction_metrics: Dict[str, float]
    ) -> RelationshipMetrics:
        """
        Calculate comprehensive relationship metrics.
        
        Args:
            conn: Database connection
            context: Current interaction context
            existing_relationship: Existing relationship data
            interaction_metrics: Current interaction analysis
            
        Returns:
            Updated RelationshipMetrics
        """
        now = datetime.utcnow()
        
        if existing_relationship:
            # Update existing relationship
            total_interactions = existing_relationship['total_interactions'] + 1
            quality_interactions = existing_relationship['quality_interactions']
            if interaction_metrics.get('is_quality_interaction', False):
                quality_interactions += 1
            
            # Calculate relationship age
            created_at = existing_relationship['created_at']
            relationship_age_days = (now - created_at).days
            
            # Calculate interaction frequency (interactions per day)
            interaction_frequency = total_interactions / max(1, relationship_age_days)
            
            # Progressive scoring based on accumulated data
            conversation_count_score = min(100, total_interactions * 2)  # Cap at 50 interactions
            conversation_quality_score = (quality_interactions / max(1, total_interactions)) * 100
            
            # Time investment estimation (rough approximation)
            avg_conversation_duration = interaction_metrics.get('duration_quality', 2.0)
            time_investment = total_interactions * avg_conversation_duration
            time_investment_score = min(100, time_investment / 10)  # Normalize to 100
            
            # Emotional connection progression
            emotional_boost = interaction_metrics.get('emotional_connection_boost', 0.5)
            existing_emotional = existing_relationship.get('emotional_connection', 50.0)
            emotional_connection = min(100, existing_emotional * 0.95 + emotional_boost * 5)  # Gradual increase
            
            # Shared experiences (based on conversation count and quality)
            shared_experiences = min(100, (quality_interactions * 10) + (total_interactions * 2))
            
            # Trust level (based on quality interactions and emotional connection)
            trust_level = min(100, (quality_interactions * 5) + (emotional_connection * 0.3))
            
        else:
            # New relationship
            total_interactions = 1
            quality_interactions = 1 if interaction_metrics.get('is_quality_interaction', False) else 0
            relationship_age_days = 0
            interaction_frequency = 1.0  # First day
            
            # Initial scores for new relationship
            conversation_count_score = 2.0  # Low initial score
            conversation_quality_score = interaction_metrics.get('interaction_quality', 1.0) * 10
            time_investment_score = interaction_metrics.get('duration_quality', 1.0)
            emotional_connection = interaction_metrics.get('emotional_connection_boost', 0.5) * 10
            shared_experiences = 5.0 if context.shared_topic else 1.0
            trust_level = 10.0 if interaction_metrics.get('trust_expression', 0) > 0 else 5.0
        
        # Calculate weighted depth score
        depth_score = (
            conversation_count_score * self.scoring_factors['conversation_count'] +
            conversation_quality_score * self.scoring_factors['conversation_quality'] +
            time_investment_score * self.scoring_factors['time_investment'] +
            emotional_connection * self.scoring_factors['emotional_connection'] +
            shared_experiences * self.scoring_factors['shared_experiences']
        )
        
        # Determine relationship depth based on score
        relationship_depth = self._determine_relationship_depth(depth_score)
        
        # Calculate progression velocity (change rate)
        if existing_relationship:
            old_score = existing_relationship.get('depth_score', 0)
            days_since_update = max(1, (now - existing_relationship['updated_at']).days)
            progression_velocity = (depth_score - old_score) / days_since_update
        else:
            progression_velocity = depth_score  # Initial velocity
        
        # Create comprehensive intelligence metadata
        intelligence_metadata = {
            'interaction_analysis': interaction_metrics,
            'scoring_breakdown': {
                'conversation_count': conversation_count_score,
                'conversation_quality': conversation_quality_score,
                'time_investment': time_investment_score,
                'emotional_connection': emotional_connection,
                'shared_experiences': shared_experiences
            },
            'progression_history': existing_relationship.get('intelligence_metadata', {}).get('progression_history', []) if existing_relationship else [],
            'quality_interaction_ratio': quality_interactions / max(1, total_interactions),
            'last_analysis': now.isoformat()
        }
        
        # Add current score to progression history
        intelligence_metadata['progression_history'].append({
            'date': now.isoformat(),
            'depth_score': depth_score,
            'relationship_depth': relationship_depth.value,
            'interaction_quality': interaction_metrics.get('interaction_quality', 1.0)
        })
        
        # Keep only last 50 entries for progression history
        intelligence_metadata['progression_history'] = intelligence_metadata['progression_history'][-50:]
        
        return RelationshipMetrics(
            user_id=context.user_id,
            bot_name=context.bot_name,
            relationship_depth=relationship_depth,
            depth_score=round(depth_score, 2),
            interaction_frequency=round(interaction_frequency, 3),
            conversation_quality=round(conversation_quality_score, 2),
            emotional_connection=round(emotional_connection, 2),
            trust_level=round(trust_level, 2),
            shared_experiences=round(shared_experiences, 2),
            time_investment=round(time_investment_score, 2),
            progression_velocity=round(progression_velocity, 3),
            last_interaction=now,
            total_interactions=total_interactions,
            quality_interactions=quality_interactions,
            relationship_age_days=relationship_age_days,
            intelligence_metadata=intelligence_metadata
        )
    
    async def _store_relationship_intelligence(self, conn, metrics: RelationshipMetrics):
        """Store relationship intelligence in PostgreSQL"""
        # Upsert relationship intelligence
        await conn.execute("""
            INSERT INTO relationship_intelligence (
                user_id, bot_name, relationship_depth, depth_score,
                interaction_frequency, conversation_quality, emotional_connection,
                trust_level, shared_experiences, time_investment, progression_velocity,
                last_interaction, total_interactions, quality_interactions,
                relationship_age_days, intelligence_metadata, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            ON CONFLICT (user_id, bot_name) 
            DO UPDATE SET
                relationship_depth = EXCLUDED.relationship_depth,
                depth_score = EXCLUDED.depth_score,
                interaction_frequency = EXCLUDED.interaction_frequency,
                conversation_quality = EXCLUDED.conversation_quality,
                emotional_connection = EXCLUDED.emotional_connection,
                trust_level = EXCLUDED.trust_level,
                shared_experiences = EXCLUDED.shared_experiences,
                time_investment = EXCLUDED.time_investment,
                progression_velocity = EXCLUDED.progression_velocity,
                last_interaction = EXCLUDED.last_interaction,
                total_interactions = EXCLUDED.total_interactions,
                quality_interactions = EXCLUDED.quality_interactions,
                relationship_age_days = EXCLUDED.relationship_age_days,
                intelligence_metadata = EXCLUDED.intelligence_metadata,
                updated_at = EXCLUDED.updated_at
        """, 
        metrics.user_id, metrics.bot_name, metrics.relationship_depth.value,
        metrics.depth_score, metrics.interaction_frequency, metrics.conversation_quality,
        metrics.emotional_connection, metrics.trust_level, metrics.shared_experiences,
        metrics.time_investment, metrics.progression_velocity, metrics.last_interaction,
        metrics.total_interactions, metrics.quality_interactions, metrics.relationship_age_days,
        json.dumps(metrics.intelligence_metadata), datetime.utcnow())
    
    def _determine_relationship_depth(self, depth_score: float) -> RelationshipDepth:
        """
        Determine relationship depth based on calculated score.
        
        Args:
            depth_score: Calculated relationship depth score (0-100)
            
        Returns:
            RelationshipDepth enum value
        """
        for depth, (min_score, max_score) in self.depth_thresholds.items():
            if min_score <= depth_score < max_score:
                return depth
        
        # Handle edge case for perfect score
        if depth_score >= 80:
            return RelationshipDepth.INTIMATE
        
        return RelationshipDepth.ACQUAINTANCE
    
    def _is_depth_progression(self, old_depth: RelationshipDepth, new_depth: RelationshipDepth) -> bool:
        """Check if relationship depth change is a progression (improvement)"""
        depth_hierarchy = {
            RelationshipDepth.ACQUAINTANCE: 0,
            RelationshipDepth.FRIEND: 1,
            RelationshipDepth.CLOSE: 2,
            RelationshipDepth.INTIMATE: 3
        }
        return depth_hierarchy[new_depth] > depth_hierarchy[old_depth]
    
    @handle_errors(category=ErrorCategory.DATABASE, severity=ErrorSeverity.MEDIUM)
    async def get_relationship_intelligence(
        self, 
        user_id: str, 
        bot_name: str
    ) -> Optional[RelationshipMetrics]:
        """
        Get current relationship intelligence for a user-bot pair.
        
        Args:
            user_id: User identifier
            bot_name: Bot identifier
            
        Returns:
            RelationshipMetrics if relationship exists, None otherwise
        """
        if not self.postgres_pool:
            return None
        
        async with self.postgres_pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT * FROM relationship_intelligence 
                WHERE user_id = $1 AND bot_name = $2
            """, user_id, bot_name)
            
            if not result:
                return None
            
            # Convert database result to RelationshipMetrics
            intelligence_metadata = json.loads(result['intelligence_metadata']) if result['intelligence_metadata'] else {}
            
            return RelationshipMetrics(
                user_id=result['user_id'],
                bot_name=result['bot_name'],
                relationship_depth=RelationshipDepth(result['relationship_depth']),
                depth_score=result['depth_score'],
                interaction_frequency=result['interaction_frequency'],
                conversation_quality=result['conversation_quality'],
                emotional_connection=result['emotional_connection'],
                trust_level=result['trust_level'],
                shared_experiences=result['shared_experiences'],
                time_investment=result['time_investment'],
                progression_velocity=result['progression_velocity'],
                last_interaction=result['last_interaction'],
                total_interactions=result['total_interactions'],
                quality_interactions=result['quality_interactions'],
                relationship_age_days=result['relationship_age_days'],
                intelligence_metadata=intelligence_metadata
            )
    
    @handle_errors(category=ErrorCategory.DATABASE, severity=ErrorSeverity.LOW)
    async def get_relationship_insights(
        self, 
        user_id: str, 
        bot_name: str,
        _days_back: int = 30  # Reserved for historical analysis
    ) -> Dict[str, Any]:
        """
        Get relationship insights and trends for a user-bot pair.
        
        Args:
            user_id: User identifier
            bot_name: Bot identifier
            days_back: Days of history to analyze
            
        Returns:
            Dictionary with relationship insights and trends
        """
        current_relationship = await self.get_relationship_intelligence(user_id, bot_name)
        
        if not current_relationship:
            return {'status': 'no_relationship', 'insights': []}
        
        insights = []
        
        # Relationship progression analysis
        progression_history = current_relationship.intelligence_metadata.get('progression_history', [])
        if len(progression_history) > 1:
            recent_scores = [entry['depth_score'] for entry in progression_history[-5:]]
            trend = "improving" if recent_scores[-1] > recent_scores[0] else "stable"
            if recent_scores[-1] < recent_scores[0] * 0.9:
                trend = "declining"
            
            insights.append(f"Relationship trend: {trend}")
        
        # Quality interaction ratio
        quality_ratio = current_relationship.intelligence_metadata.get('quality_interaction_ratio', 0)
        if quality_ratio > 0.7:
            insights.append("High-quality conversation pattern detected")
        elif quality_ratio < 0.3:
            insights.append("Opportunity for deeper conversations")
        
        # Interaction frequency analysis
        if current_relationship.interaction_frequency > 2.0:
            insights.append("Frequent interaction pattern - strong engagement")
        elif current_relationship.interaction_frequency < 0.5:
            insights.append("Infrequent interactions - opportunity for more engagement")
        
        # Emotional connection insights
        if current_relationship.emotional_connection > 80:
            insights.append("Strong emotional connection established")
        elif current_relationship.emotional_connection < 30:
            insights.append("Opportunity for emotional connection building")
        
        return {
            'status': 'analyzed',
            'current_depth': current_relationship.relationship_depth.value,
            'depth_score': current_relationship.depth_score,
            'insights': insights,
            'metrics_summary': {
                'total_interactions': current_relationship.total_interactions,
                'quality_interactions': current_relationship.quality_interactions,
                'relationship_age_days': current_relationship.relationship_age_days,
                'progression_velocity': current_relationship.progression_velocity
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get relationship intelligence statistics and performance metrics."""
        return {
            'component': 'RelationshipIntelligenceManager',
            'system': 'WhisperEngine Adaptive Learning',
            'statistics': self.stats.copy(),
            'scoring_factors': self.scoring_factors.copy(),
            'depth_thresholds': {depth.value: threshold for depth, threshold in self.depth_thresholds.items()},
            'quality_indicators': self.quality_indicators.copy(),
            'timestamp': datetime.utcnow().isoformat()
        }


# Factory function for creating manager instances
def create_relationship_intelligence_manager(postgres_pool=None, memory_manager=None) -> RelationshipIntelligenceManager:
    """
    Factory function to create RelationshipIntelligenceManager instance.
    
    Args:
        postgres_pool: PostgreSQL connection pool for relationship storage
        memory_manager: Vector memory system for relationship context
        
    Returns:
        RelationshipIntelligenceManager instance
    """
    return RelationshipIntelligenceManager(postgres_pool=postgres_pool, memory_manager=memory_manager)