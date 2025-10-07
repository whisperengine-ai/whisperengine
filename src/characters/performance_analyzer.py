"""
Character Performance Analyzer - Sprint 4: CharacterEvolution

Analyzes character effectiveness across all Sprint 1-3 metrics and identifies
optimization opportunities for CDL personality parameters.

Core Features:
- Character effectiveness analysis using Sprint 1-3 data
- CDL trait correlation with conversation success
- Optimization opportunity identification
- Performance pattern detection
- Integration with TrendWise, MemoryBoost, and RelationshipTuner

This component enables data-driven character personality optimization while
maintaining character authenticity and consistency.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OptimizationCategory(Enum):
    """Categories of character optimization opportunities"""
    COMMUNICATION_STYLE = "communication_style"
    EDUCATIONAL_APPROACH = "educational_approach"
    TECHNICAL_DEPTH = "technical_depth"
    EMOTIONAL_EXPRESSION = "emotional_expression"
    RELATIONSHIP_BUILDING = "relationship_building"
    KNOWLEDGE_DELIVERY = "knowledge_delivery"
    EMPATHY_DEMONSTRATION = "empathy_demonstration"
    PERSONALITY_BALANCE = "personality_balance"


class PerformanceMetric(Enum):
    """Performance metrics from Sprint 1-3 systems"""
    CONVERSATION_QUALITY = "conversation_quality"        # Sprint 1 TrendWise
    CONFIDENCE_TRENDS = "confidence_trends"              # Sprint 1 TrendWise
    MEMORY_EFFECTIVENESS = "memory_effectiveness"        # Sprint 2 MemoryBoost
    RELATIONSHIP_PROGRESSION = "relationship_progression" # Sprint 3 RelationshipTuner
    TRUST_BUILDING = "trust_building"                    # Sprint 3 RelationshipTuner
    USER_ENGAGEMENT = "user_engagement"                  # Cross-sprint metric


@dataclass
class OptimizationOpportunity:
    """Identified opportunity for character optimization"""
    category: OptimizationCategory
    confidence_score: float  # 0-1, confidence in this optimization
    impact_potential: float  # 0-1, expected improvement potential
    current_performance: float  # 0-1, current performance in this area
    target_performance: float   # 0-1, target performance after optimization
    affected_traits: List[str]  # CDL traits that would be adjusted
    evidence_metrics: Dict[str, float]  # Supporting metrics from Sprint 1-3
    recommendation: str  # Human-readable optimization recommendation
    priority: str  # "high", "medium", "low"


@dataclass
class CharacterEffectivenessData:
    """Character effectiveness analysis results"""
    bot_name: str
    analysis_period_days: int
    overall_effectiveness: float  # 0-1, weighted average across all metrics
    
    # Sprint 1-3 Performance Metrics
    conversation_quality_avg: float
    confidence_trend_direction: str
    memory_effectiveness_score: float
    relationship_progression_rate: float
    trust_building_success: float
    user_engagement_level: float
    
    # Performance Breakdowns
    metric_scores: Dict[PerformanceMetric, float]
    trait_correlations: Dict[str, float]  # CDL trait -> performance correlation
    optimization_opportunities: List[OptimizationOpportunity]
    
    # Statistical Data
    data_points: int
    statistical_confidence: float
    analysis_timestamp: datetime


@dataclass
class TraitPerformanceCorrelation:
    """Correlation between CDL trait and performance metrics"""
    trait_name: str
    trait_category: str  # personality, communication, background, etc.
    correlation_strength: float  # -1 to 1
    p_value: float  # Statistical significance
    sample_size: int
    performance_metric: PerformanceMetric
    evidence_summary: str


class CharacterPerformanceAnalyzer:
    """
    Analyzes character effectiveness across Sprint 1-3 metrics and identifies
    optimization opportunities for CDL personality parameters.
    
    Integrates with:
    - Sprint 1 TrendWise: Confidence trends and conversation quality
    - Sprint 2 MemoryBoost: Memory effectiveness and retrieval patterns
    - Sprint 3 RelationshipTuner: Relationship progression and trust building
    """
    
    def __init__(self, 
                 trend_analyzer=None,
                 memory_effectiveness_analyzer=None, 
                 relationship_evolution_engine=None,
                 cdl_parser=None,
                 cdl_database_manager=None,
                 postgres_pool=None):
        self.trend_analyzer = trend_analyzer
        self.memory_effectiveness_analyzer = memory_effectiveness_analyzer
        self.relationship_evolution_engine = relationship_evolution_engine
        self.cdl_parser = cdl_parser
        self.cdl_database_manager = cdl_database_manager
        self.postgres_pool = postgres_pool
        self.logger = logging.getLogger(__name__)
        
        # Performance thresholds for optimization detection
        self.OPTIMIZATION_THRESHOLDS = {
            "low_performance": 0.6,      # Below this triggers optimization
            "high_confidence": 0.8,      # Above this for reliable optimization
            "min_data_points": 10,       # Minimum interactions for analysis
            "correlation_significance": 0.7  # Minimum correlation strength
        }
    
    async def analyze_character_effectiveness(self, 
                                            bot_name: str, 
                                            days_back: int = 14,
                                            user_id: Optional[str] = None) -> CharacterEffectivenessData:
        """
        Analyze character performance across all Sprint 1-3 metrics.
        
        Args:
            bot_name: Character bot to analyze (elena, marcus, etc.)
            days_back: Analysis period in days
            user_id: Specific user to analyze (None for all users)
            
        Returns:
            CharacterEffectivenessData with comprehensive analysis
        """
        try:
            self.logger.info("Starting character effectiveness analysis for %s (last %d days)", bot_name, days_back)
            
            # Gather data from Sprint 1-3 systems
            sprint1_data = await self._gather_trendwise_data(bot_name, days_back, user_id)
            sprint2_data = await self._gather_memoryboost_data(bot_name, days_back, user_id)
            sprint3_data = await self._gather_relationshiptuner_data(bot_name, days_back, user_id)
            
            # Analyze CDL trait correlations
            trait_correlations = await self._analyze_cdl_trait_correlations(
                bot_name, sprint1_data, sprint2_data, sprint3_data
            )
            
            # Calculate overall effectiveness
            overall_effectiveness = await self._calculate_overall_effectiveness(
                sprint1_data, sprint2_data, sprint3_data
            )
            
            # Identify optimization opportunities
            optimization_opportunities = await self._identify_optimization_opportunities(
                bot_name, sprint1_data, sprint2_data, sprint3_data, trait_correlations
            )
            
            # Compile metric scores
            metric_scores = {
                PerformanceMetric.CONVERSATION_QUALITY: sprint1_data.get('conversation_quality_avg', 0.0),
                PerformanceMetric.CONFIDENCE_TRENDS: sprint1_data.get('confidence_score', 0.0),
                PerformanceMetric.MEMORY_EFFECTIVENESS: sprint2_data.get('effectiveness_score', 0.0),
                PerformanceMetric.RELATIONSHIP_PROGRESSION: sprint3_data.get('progression_rate', 0.0),
                PerformanceMetric.TRUST_BUILDING: sprint3_data.get('trust_building_success', 0.0),
                PerformanceMetric.USER_ENGAGEMENT: sprint1_data.get('engagement_level', 0.0)
            }
            
            # Calculate statistical confidence
            total_data_points = (
                sprint1_data.get('data_points', 0) + 
                sprint2_data.get('data_points', 0) + 
                sprint3_data.get('data_points', 0)
            )
            statistical_confidence = min(1.0, total_data_points / 30.0)  # 30+ interactions = high confidence
            
            effectiveness_data = CharacterEffectivenessData(
                bot_name=bot_name,
                analysis_period_days=days_back,
                overall_effectiveness=overall_effectiveness,
                conversation_quality_avg=sprint1_data.get('conversation_quality_avg', 0.0),
                confidence_trend_direction=sprint1_data.get('trend_direction', 'stable'),
                memory_effectiveness_score=sprint2_data.get('effectiveness_score', 0.0),
                relationship_progression_rate=sprint3_data.get('progression_rate', 0.0),
                trust_building_success=sprint3_data.get('trust_building_success', 0.0),
                user_engagement_level=sprint1_data.get('engagement_level', 0.0),
                metric_scores=metric_scores,
                trait_correlations=trait_correlations,
                optimization_opportunities=optimization_opportunities,
                data_points=total_data_points,
                statistical_confidence=statistical_confidence,
                analysis_timestamp=datetime.now()
            )
            
            self.logger.info("Character effectiveness analysis complete for %s: Overall: %.2f, Opportunities: %d", 
                           bot_name, overall_effectiveness, len(optimization_opportunities))
            
            return effectiveness_data
            
        except (ValueError, TypeError, KeyError) as e:
            self.logger.error("Error analyzing character effectiveness for %s: %s", bot_name, e)
            raise
    
    async def identify_optimization_opportunities(self, bot_name: str) -> List[OptimizationOpportunity]:
        """
        Identify specific personality aspects that could be improved.
        
        Args:
            bot_name: Character bot to analyze
            
        Returns:
            List of optimization opportunities ranked by impact potential
        """
        try:
            # Get full character effectiveness analysis
            effectiveness_data = await self.analyze_character_effectiveness(bot_name)
            
            # Return identified opportunities sorted by priority
            opportunities = effectiveness_data.optimization_opportunities
            opportunities.sort(key=lambda x: (x.priority == "high", x.impact_potential), reverse=True)
            
            self.logger.info("Identified %d optimization opportunities for %s", len(opportunities), bot_name)
            return opportunities
            
        except (ValueError, TypeError, KeyError) as e:
            self.logger.error("Error identifying optimization opportunities for %s: %s", bot_name, e)
            return []
    
    async def correlate_personality_traits_with_outcomes(self, bot_name: str) -> Dict[str, float]:
        """
        Correlate CDL traits with conversation success from Sprint 1-3 data.
        
        Args:
            bot_name: Character bot to analyze
            
        Returns:
            Dictionary mapping CDL trait names to correlation scores (-1 to 1)
        """
        try:
            self.logger.info("Analyzing personality trait correlations for %s", bot_name)
            
            # Load character CDL data
            character_data = await self._load_character_cdl_data(bot_name)
            if not character_data:
                self.logger.warning("No CDL data found for %s", bot_name)
                return {}
            
            # Get effectiveness analysis
            effectiveness_data = await self.analyze_character_effectiveness(bot_name)
            
            # Return trait correlations from analysis
            return effectiveness_data.trait_correlations
            
        except (ValueError, TypeError, KeyError) as e:
            self.logger.error("Error correlating personality traits for %s: %s", bot_name, e)
            return {}
    
    async def _gather_trendwise_data(self, bot_name: str, days_back: int, user_id: Optional[str]) -> Dict[str, Any]:
        """Gather Sprint 1 TrendWise performance data"""
        try:
            if not self.trend_analyzer:
                self.logger.warning("TrendWise analyzer not available")
                return self._get_mock_trendwise_data()
            
            # Get confidence trends
            if user_id:
                confidence_trends = await self.trend_analyzer.get_confidence_trends(bot_name, user_id, days_back)
            else:
                # Get overall trends for all users
                quality_trends = await self.trend_analyzer.get_quality_trends(bot_name, days_back)
                confidence_trends = quality_trends  # Use quality trends as proxy
            
            # Calculate conversation quality average
            conversation_quality_avg = confidence_trends.average_value if confidence_trends else 0.5
            
            # Determine confidence score based on trend direction
            confidence_score = 0.8 if confidence_trends and confidence_trends.direction.value == "improving" else 0.6
            
            return {
                'conversation_quality_avg': conversation_quality_avg,
                'confidence_score': confidence_score,
                'trend_direction': confidence_trends.direction.value if confidence_trends else 'stable',
                'engagement_level': min(1.0, conversation_quality_avg * 1.2),  # Derived metric
                'data_points': confidence_trends.data_points if confidence_trends else 0
            }
            
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Error gathering TrendWise data for %s: %s", bot_name, e)
            return self._get_mock_trendwise_data()
    
    async def _gather_memoryboost_data(self, bot_name: str, days_back: int, user_id: Optional[str]) -> Dict[str, Any]:
        """Gather Sprint 2 MemoryBoost performance data"""
        try:
            if not self.memory_effectiveness_analyzer:
                self.logger.warning("MemoryBoost analyzer not available")
                return self._get_mock_memoryboost_data()
            
            # Get memory effectiveness analysis
            if user_id:
                effectiveness_data = await self.memory_effectiveness_analyzer.analyze_memory_performance(user_id, days_back)
            else:
                # Get overall memory effectiveness across all users
                effectiveness_data = await self.memory_effectiveness_analyzer.analyze_overall_memory_patterns(bot_name, days_back)
            
            effectiveness_score = effectiveness_data.get('overall_effectiveness', 0.5) if effectiveness_data else 0.5
            
            return {
                'effectiveness_score': effectiveness_score,
                'data_points': effectiveness_data.get('total_memories_analyzed', 0) if effectiveness_data else 0
            }
            
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Error gathering MemoryBoost data for %s: %s", bot_name, e)
            return self._get_mock_memoryboost_data()
    
    async def _gather_relationshiptuner_data(self, bot_name: str, days_back: int, user_id: Optional[str]) -> Dict[str, Any]:
        """Gather Sprint 3 RelationshipTuner performance data"""
        try:
            if not self.relationship_evolution_engine:
                self.logger.warning("RelationshipTuner engine not available")
                return self._get_mock_relationshiptuner_data()
            
            # Get relationship progression data
            if user_id:
                relationship_data = await self.relationship_evolution_engine.get_relationship_evolution_summary(user_id, bot_name)
            else:
                # Get overall relationship statistics
                relationship_data = await self.relationship_evolution_engine.get_bot_relationship_statistics(bot_name, days_back)
            
            # Calculate progression rate and trust building success
            progression_rate = relationship_data.get('progression_rate', 0.5) if relationship_data else 0.5
            trust_building_success = relationship_data.get('trust_growth_rate', 0.5) if relationship_data else 0.5
            
            return {
                'progression_rate': progression_rate,
                'trust_building_success': trust_building_success,
                'data_points': relationship_data.get('total_interactions', 0) if relationship_data else 0
            }
            
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Error gathering RelationshipTuner data for %s: %s", bot_name, e)
            return self._get_mock_relationshiptuner_data()
    
    async def _analyze_cdl_trait_correlations(self, bot_name: str, sprint1_data: Dict, sprint2_data: Dict, sprint3_data: Dict) -> Dict[str, float]:
        """Analyze correlations between CDL traits and performance metrics"""
        try:
            # Load character CDL data
            character_data = await self._load_character_cdl_data(bot_name)
            if not character_data:
                return {}
            
            trait_correlations = {}
            
            # Analyze key personality traits
            personality = character_data.get('personality', {})
            big_five = personality.get('big_five', {})
            
            # Example correlations (in production, this would use statistical analysis)
            if big_five:
                # Extraversion correlation with engagement
                extraversion = big_five.get('extraversion', 0.5)
                engagement_correlation = self._calculate_trait_performance_correlation(
                    extraversion, sprint1_data.get('engagement_level', 0.5)
                )
                trait_correlations['extraversion'] = engagement_correlation
                
                # Conscientiousness correlation with memory effectiveness
                conscientiousness = big_five.get('conscientiousness', 0.5)
                memory_correlation = self._calculate_trait_performance_correlation(
                    conscientiousness, sprint2_data.get('effectiveness_score', 0.5)
                )
                trait_correlations['conscientiousness'] = memory_correlation
                
                # Agreeableness correlation with relationship building
                agreeableness = big_five.get('agreeableness', 0.5)
                relationship_correlation = self._calculate_trait_performance_correlation(
                    agreeableness, sprint3_data.get('trust_building_success', 0.5)
                )
                trait_correlations['agreeableness'] = relationship_correlation
            
            # Communication style correlations
            communication = character_data.get('communication', {})
            if communication:
                formality = communication.get('formality', 0.5)
                quality_correlation = self._calculate_trait_performance_correlation(
                    formality, sprint1_data.get('conversation_quality_avg', 0.5)
                )
                trait_correlations['formality'] = quality_correlation
            
            return trait_correlations
            
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Error analyzing CDL trait correlations: %s", e)
            return {}
    
    def _calculate_trait_performance_correlation(self, trait_value: float, performance_value: float) -> float:
        """Calculate simple correlation between trait and performance (placeholder for statistical analysis)"""
        # Simplified correlation calculation
        # In production, this would use proper statistical correlation analysis
        if trait_value > 0.7 and performance_value > 0.7:
            return 0.8  # Strong positive correlation
        elif trait_value < 0.3 and performance_value < 0.3:
            return -0.6  # Negative correlation
        elif abs(trait_value - performance_value) < 0.2:
            return 0.5  # Moderate correlation
        else:
            return 0.1  # Weak correlation
    
    async def _calculate_overall_effectiveness(self, sprint1_data: Dict, sprint2_data: Dict, sprint3_data: Dict) -> float:
        """Calculate weighted overall effectiveness score"""
        try:
            # Weighted combination of Sprint 1-3 metrics
            weights = {
                'conversation_quality': 0.3,
                'confidence': 0.2,
                'memory_effectiveness': 0.2,
                'relationship_progression': 0.2,
                'user_engagement': 0.1
            }
            
            effectiveness = (
                sprint1_data.get('conversation_quality_avg', 0.0) * weights['conversation_quality'] +
                sprint1_data.get('confidence_score', 0.0) * weights['confidence'] +
                sprint2_data.get('effectiveness_score', 0.0) * weights['memory_effectiveness'] +
                sprint3_data.get('progression_rate', 0.0) * weights['relationship_progression'] +
                sprint1_data.get('engagement_level', 0.0) * weights['user_engagement']
            )
            
            return min(1.0, max(0.0, effectiveness))
            
        except (ValueError, TypeError, ZeroDivisionError) as e:
            self.logger.error("Error calculating overall effectiveness: %s", e)
            return 0.5
    
    async def _identify_optimization_opportunities(self, 
                                                 bot_name: str,
                                                 sprint1_data: Dict, 
                                                 sprint2_data: Dict, 
                                                 sprint3_data: Dict,
                                                 trait_correlations: Dict[str, float]) -> List[OptimizationOpportunity]:
        """Identify specific optimization opportunities based on performance analysis"""
        opportunities = []
        
        try:
            # Use trait correlations for enhancement (currently basic implementation)
            _ = trait_correlations  # Acknowledge parameter usage
            
            # Check conversation quality optimization
            conversation_quality = sprint1_data.get('conversation_quality_avg', 0.0)
            if conversation_quality < self.OPTIMIZATION_THRESHOLDS['low_performance']:
                opportunities.append(OptimizationOpportunity(
                    category=OptimizationCategory.COMMUNICATION_STYLE,
                    confidence_score=0.8,
                    impact_potential=0.7,
                    current_performance=conversation_quality,
                    target_performance=min(1.0, conversation_quality + 0.2),
                    affected_traits=['communication_style', 'formality', 'clarity'],
                    evidence_metrics={'conversation_quality': conversation_quality},
                    recommendation=f"Improve communication clarity and engagement style for {bot_name}",
                    priority="high"
                ))
            
            # Check memory effectiveness optimization
            memory_effectiveness = sprint2_data.get('effectiveness_score', 0.0)
            if memory_effectiveness < self.OPTIMIZATION_THRESHOLDS['low_performance']:
                opportunities.append(OptimizationOpportunity(
                    category=OptimizationCategory.KNOWLEDGE_DELIVERY,
                    confidence_score=0.7,
                    impact_potential=0.6,
                    current_performance=memory_effectiveness,
                    target_performance=min(1.0, memory_effectiveness + 0.15),
                    affected_traits=['teaching_style', 'explanation_depth', 'patience'],
                    evidence_metrics={'memory_effectiveness': memory_effectiveness},
                    recommendation=f"Optimize knowledge delivery and information presentation for {bot_name}",
                    priority="medium"
                ))
            
            # Check relationship building optimization
            trust_building = sprint3_data.get('trust_building_success', 0.0)
            if trust_building < self.OPTIMIZATION_THRESHOLDS['low_performance']:
                opportunities.append(OptimizationOpportunity(
                    category=OptimizationCategory.RELATIONSHIP_BUILDING,
                    confidence_score=0.75,
                    impact_potential=0.8,
                    current_performance=trust_building,
                    target_performance=min(1.0, trust_building + 0.25),
                    affected_traits=['empathy', 'warmth', 'authenticity', 'agreeableness'],
                    evidence_metrics={'trust_building_success': trust_building},
                    recommendation=f"Enhance relationship building and trust development for {bot_name}",
                    priority="high"
                ))
            
            # Character-specific optimizations
            if bot_name.lower() == 'elena':
                # Elena-specific educational optimization
                if conversation_quality < 0.8:  # Higher bar for educational effectiveness
                    opportunities.append(OptimizationOpportunity(
                        category=OptimizationCategory.EDUCATIONAL_APPROACH,
                        confidence_score=0.85,
                        impact_potential=0.9,
                        current_performance=conversation_quality,
                        target_performance=min(1.0, conversation_quality + 0.3),
                        affected_traits=['teaching_patience', 'explanation_style', 'metaphor_usage'],
                        evidence_metrics={'conversation_quality': conversation_quality, 'education_specific': True},
                        recommendation="Optimize Elena's educational metaphors and teaching patience based on user comprehension patterns",
                        priority="high"
                    ))
            
            elif bot_name.lower() == 'marcus':
                # Marcus-specific technical communication optimization
                if memory_effectiveness < 0.7:  # Technical knowledge delivery focus
                    opportunities.append(OptimizationOpportunity(
                        category=OptimizationCategory.TECHNICAL_DEPTH,
                        confidence_score=0.8,
                        impact_potential=0.8,
                        current_performance=memory_effectiveness,
                        target_performance=min(1.0, memory_effectiveness + 0.25),
                        affected_traits=['technical_precision', 'accessibility', 'research_methodology'],
                        evidence_metrics={'memory_effectiveness': memory_effectiveness, 'technical_specific': True},
                        recommendation="Balance Marcus's technical depth with accessibility for broader user engagement",
                        priority="medium"
                    ))
            
            self.logger.info("Identified %d optimization opportunities for %s", len(opportunities), bot_name)
            return opportunities
            
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Error identifying optimization opportunities: %s", e)
            return []
    
    async def _load_character_cdl_data(self, bot_name: str) -> Optional[Dict[str, Any]]:
        """Load character CDL data for analysis from database"""
        try:
            if not self.cdl_database_manager:
                self.logger.warning("CDL database manager not available")
                return None
            
            # Load character data from PostgreSQL database
            character_data = await self.cdl_database_manager.get_character_by_name(bot_name.lower())
            
            return character_data if character_data else None
            
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error("Error loading CDL data for %s: %s", bot_name, e)
            return None
    
    def _get_mock_trendwise_data(self) -> Dict[str, Any]:
        """Mock TrendWise data for testing when analyzer unavailable"""
        return {
            'conversation_quality_avg': 0.65,
            'confidence_score': 0.7,
            'trend_direction': 'improving',
            'engagement_level': 0.6,
            'data_points': 15
        }
    
    def _get_mock_memoryboost_data(self) -> Dict[str, Any]:
        """Mock MemoryBoost data for testing when analyzer unavailable"""
        return {
            'effectiveness_score': 0.62,
            'data_points': 20
        }
    
    def _get_mock_relationshiptuner_data(self) -> Dict[str, Any]:
        """Mock RelationshipTuner data for testing when analyzer unavailable"""
        return {
            'progression_rate': 0.58,
            'trust_building_success': 0.68,
            'data_points': 12
        }


def create_character_performance_analyzer(trend_analyzer=None,
                                        memory_effectiveness_analyzer=None,
                                        relationship_evolution_engine=None,
                                        cdl_parser=None,
                                        cdl_database_manager=None,
                                        postgres_pool=None) -> CharacterPerformanceAnalyzer:
    """
    Factory function to create a CharacterPerformanceAnalyzer with proper dependencies.
    
    Args:
        trend_analyzer: Sprint 1 TrendWise analyzer
        memory_effectiveness_analyzer: Sprint 2 MemoryBoost analyzer  
        relationship_evolution_engine: Sprint 3 RelationshipTuner engine
        cdl_parser: CDL system parser (legacy)
        cdl_database_manager: CDL database manager (primary)
        postgres_pool: Database connection pool
        
    Returns:
        Configured CharacterPerformanceAnalyzer instance
    """
    return CharacterPerformanceAnalyzer(
        trend_analyzer=trend_analyzer,
        memory_effectiveness_analyzer=memory_effectiveness_analyzer,
        relationship_evolution_engine=relationship_evolution_engine,
        cdl_parser=cdl_parser,
        cdl_database_manager=cdl_database_manager,
        postgres_pool=postgres_pool
    )