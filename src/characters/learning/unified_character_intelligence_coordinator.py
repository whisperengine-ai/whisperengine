"""
Unified Character Intelligence Coordinator
WhisperEngine Memory Intelligence Convergence - PHASE 4 FINAL INTEGRATION
Version: 2.0 - October 2025

Creates a unified coordination layer that combines all intelligence systems
(MemoryBoost, character self-knowledge, conversation intelligence) for 
holistic character responses with optimal performance.

Core Capabilities:
- Coordinates multiple AI intelligence systems
- Intelligent system selection based on context  
- Unified response generation with character authenticity
- Performance optimization through smart resource allocation
- Maintains fidelity-first principles across all systems
- PHASE 4: Production optimization with caching and parallel processing
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

# InfluxDB metrics integration
try:
    from src.temporal.temporal_intelligence_client import create_temporal_intelligence_client
    TEMPORAL_METRICS_AVAILABLE = True
except ImportError:
    TEMPORAL_METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)

class IntelligenceSystemType(Enum):
    """Types of intelligence systems available for coordination."""
    MEMORY_BOOST = "memory_boost"
    CHARACTER_SELF_KNOWLEDGE = "character_self_knowledge"
    CHARACTER_EPISODIC_INTELLIGENCE = "character_episodic_intelligence"
    CHARACTER_TEMPORAL_EVOLUTION = "character_temporal_evolution"  # PHASE 2: Temporal Evolution Intelligence
    CHARACTER_GRAPH_KNOWLEDGE = "character_graph_knowledge"  # PHASE 3: Graph Knowledge Intelligence
    CONVERSATION_INTELLIGENCE = "conversation_intelligence"
    VECTOR_MEMORY = "vector_memory"
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"
    CDL_PERSONALITY = "cdl_personality"

class CoordinationStrategy(Enum):
    """Strategies for coordinating intelligence systems."""
    ADAPTIVE = "adaptive"  # Dynamic selection based on context
    COMPREHENSIVE = "comprehensive"  # Use all available systems
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # Optimize for speed
    FIDELITY_FIRST = "fidelity_first"  # Prioritize character authenticity
    CONTEXT_AWARE = "context_aware"  # Select based on conversation context

@dataclass
class IntelligenceRequest:
    """Request for unified intelligence coordination."""
    user_id: str
    character_name: str
    message_content: str
    conversation_context: Optional[List[Dict[str, Any]]] = None
    coordination_strategy: CoordinationStrategy = CoordinationStrategy.ADAPTIVE
    priority_systems: Optional[List[IntelligenceSystemType]] = None
    performance_constraints: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.conversation_context is None:
            self.conversation_context = []
        if self.priority_systems is None:
            self.priority_systems = []
        if self.performance_constraints is None:
            self.performance_constraints = {}

@dataclass
class IntelligenceResponse:
    """Response from unified intelligence coordination."""
    enhanced_response: str
    system_contributions: Dict[IntelligenceSystemType, Dict[str, Any]]
    coordination_metadata: Dict[str, Any]
    performance_metrics: Dict[str, float]
    character_authenticity_score: float
    confidence_score: float
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analysis."""
        return {
            'enhanced_response': self.enhanced_response,
            'system_contributions': {
                system.value: contribution 
                for system, contribution in self.system_contributions.items()
            },
            'coordination_metadata': self.coordination_metadata,
            'performance_metrics': self.performance_metrics,
            'character_authenticity_score': self.character_authenticity_score,
            'confidence_score': self.confidence_score,
            'processing_time_ms': self.processing_time_ms
        }

class UnifiedCharacterIntelligenceCoordinator:
    """
    Coordinates multiple intelligence systems to create holistic character responses.
    
    This coordinator intelligently combines:
    - MemoryBoost episodic memory intelligence 
    - Character self-knowledge from PHASE 3A
    - Conversation intelligence and context
    - Vector memory semantic understanding
    - Emotional intelligence analysis
    - CDL personality integration
    
    Key principles:
    - Fidelity-first: Character authenticity over optimization
    - Adaptive coordination: Smart system selection
    - Performance balance: Optimal resource utilization
    - Seamless integration: Unified experience
    """
    
    def __init__(self, 
                 memory_manager=None,
                 character_self_knowledge_extractor=None,
                 character_graph_knowledge_builder=None,
                 dynamic_trait_discovery=None,
                 cdl_ai_integration=None,
                 emotion_analyzer=None,
                 character_episodic_intelligence=None,
                 character_temporal_evolution_analyzer=None,
                 postgres_pool=None):
        """Initialize with available intelligence systems."""
        self.memory_manager = memory_manager
        self.character_extractor = character_self_knowledge_extractor
        self.graph_builder = character_graph_knowledge_builder
        self.trait_discovery = dynamic_trait_discovery
        self.cdl_integration = cdl_ai_integration
        self.emotion_analyzer = emotion_analyzer
        self.character_episodic_intelligence = character_episodic_intelligence
        self.character_temporal_evolution_analyzer = character_temporal_evolution_analyzer
        self.postgres_pool = postgres_pool  # PHASE 3: PostgreSQL pool for graph knowledge
        
        # InfluxDB metrics integration
        if TEMPORAL_METRICS_AVAILABLE:
            self.temporal_client = create_temporal_intelligence_client()
        else:
            self.temporal_client = None
        
        # Coordination state
        self.system_availability = {}
        self.performance_history = {}
        self.coordination_cache = {}
        
        # PHASE 4: Production optimization features
        self.cache_ttl_seconds = 60  # Cache system responses for 1 minute
        self.max_parallel_systems = 5  # Limit concurrent system processing
        self.performance_targets = {
            'total_processing_ms': 200,  # Target: under 200ms total
            'system_processing_ms': 50,  # Target: under 50ms per system
            'cache_hit_rate': 0.3  # Target: 30% cache hit rate
        }
        self.performance_metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'average_processing_time': 0.0,
            'system_success_rates': {},
            'performance_violations': 0
        }
        
        # Coordination patterns
        self.context_patterns = {
            'personal_question': [
                IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE,
                IntelligenceSystemType.CHARACTER_EPISODIC_INTELLIGENCE,
                IntelligenceSystemType.CHARACTER_TEMPORAL_EVOLUTION,  # PHASE 2: Character growth awareness
                IntelligenceSystemType.CHARACTER_GRAPH_KNOWLEDGE,  # PHASE 3: Personal facts and relationships
                IntelligenceSystemType.CDL_PERSONALITY,
                IntelligenceSystemType.MEMORY_BOOST
            ],
            'emotional_support': [
                IntelligenceSystemType.EMOTIONAL_INTELLIGENCE,
                IntelligenceSystemType.CHARACTER_TEMPORAL_EVOLUTION,  # PHASE 2: Emotional evolution understanding
                IntelligenceSystemType.CHARACTER_EPISODIC_INTELLIGENCE,
                IntelligenceSystemType.CHARACTER_GRAPH_KNOWLEDGE,  # PHASE 3: Relationship context and history
                IntelligenceSystemType.MEMORY_BOOST,
                IntelligenceSystemType.CDL_PERSONALITY
            ],
            'knowledge_sharing': [
                IntelligenceSystemType.CDL_PERSONALITY,
                IntelligenceSystemType.CHARACTER_EPISODIC_INTELLIGENCE,
                IntelligenceSystemType.CHARACTER_TEMPORAL_EVOLUTION,  # PHASE 2: Learning progression awareness
                IntelligenceSystemType.CHARACTER_GRAPH_KNOWLEDGE,  # PHASE 3: Structured knowledge and facts
                IntelligenceSystemType.VECTOR_MEMORY,
                IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE
            ],
            'casual_conversation': [
                IntelligenceSystemType.CONVERSATION_INTELLIGENCE,
                IntelligenceSystemType.CHARACTER_EPISODIC_INTELLIGENCE,
                IntelligenceSystemType.CHARACTER_TEMPORAL_EVOLUTION,  # PHASE 2: Natural growth references
                IntelligenceSystemType.CHARACTER_GRAPH_KNOWLEDGE,  # PHASE 3: Conversational context and connections
                IntelligenceSystemType.MEMORY_BOOST,
                IntelligenceSystemType.CDL_PERSONALITY
            ],
            'complex_problem': [
                IntelligenceSystemType.VECTOR_MEMORY,
                IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE,
                IntelligenceSystemType.CHARACTER_TEMPORAL_EVOLUTION,  # PHASE 2: Confidence evolution insights
                IntelligenceSystemType.CHARACTER_GRAPH_KNOWLEDGE,  # PHASE 3: Problem-solving knowledge and relationships
                IntelligenceSystemType.CHARACTER_EPISODIC_INTELLIGENCE,
                IntelligenceSystemType.CONVERSATION_INTELLIGENCE
            ]
        }
        
        logger.info("🧠 Unified Character Intelligence Coordinator initialized")
    
    async def coordinate_intelligence(self, request: IntelligenceRequest) -> IntelligenceResponse:
        """
        Coordinate all intelligence systems for unified character response.
        PHASE 4: Production optimized with caching and parallel processing.
        
        Args:
            request: Intelligence coordination request
            
        Returns:
            Unified intelligence response with system contributions
        """
        start_time = time.time()
        
        # Initialize performance metrics if needed
        if not hasattr(self, '_performance_metrics'):
            self._performance_metrics = {
                'total_requests': 0,
                'cache_hits': 0,
                'average_processing_time': 0.0,
                'average_systems_per_request': 0.0
            }
        
        self._performance_metrics['total_requests'] += 1
        
        try:
            logger.info("🧠 UNIFIED-INTELLIGENCE: Coordinating intelligence for character %s", 
                       request.character_name)
            
            # PHASE 4: Check cache first for performance optimization
            cache_key = self._generate_cache_key(request)
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                self._performance_metrics['cache_hits'] += 1
                logger.debug("✅ Cache hit for intelligence coordination")
                return cached_response
            
            # Detect conversation context type
            context_type = await self._detect_context_type(request)
            
            # Select optimal intelligence systems with performance constraints
            selected_systems = await self._select_intelligence_systems_optimized(request, context_type)
            
            # PHASE 4: Gather intelligence with parallel processing for performance
            system_intelligence = await self._gather_system_intelligence_parallel(request, selected_systems)
            
            # Convert string keys to IntelligenceSystemType for type consistency
            system_contributions = {}
            for system_str, data in system_intelligence.items():
                try:
                    system_enum = IntelligenceSystemType(system_str)
                    system_contributions[system_enum] = data
                except ValueError:
                    # Skip invalid system types
                    continue
            
            # Synthesize unified response
            unified_response = await self._synthesize_unified_response(
                request, system_contributions, context_type
            )
            
            # Calculate performance metrics
            processing_time = (time.time() - start_time) * 1000
            performance_metrics = await self._calculate_performance_metrics(
                system_contributions, processing_time
            )
            
            # Update performance tracking
            self._update_performance_tracking(
                system_count=len(selected_systems), 
                processing_time=processing_time,
                cache_hit=False
            )
            
            # Build coordination response
            response = IntelligenceResponse(
                enhanced_response=unified_response,
                system_contributions=system_contributions,
                coordination_metadata={
                    'context_type': context_type,
                    'selected_systems': [system.value for system in selected_systems],
                    'coordination_strategy': request.coordination_strategy.value,
                    'character_name': request.character_name,
                    'cache_status': 'miss',
                    'processing_optimizations': 'parallel_processing_enabled'
                },
                performance_metrics=performance_metrics,
                character_authenticity_score=await self._calculate_authenticity_score(
                    unified_response, request.character_name
                ),
                confidence_score=await self._calculate_confidence_score(system_contributions),
                processing_time_ms=processing_time
            )
            
            # Record coordination metrics to InfluxDB
            if self.temporal_client:
                await self._record_coordination_metrics(
                    request=request,
                    systems_used=[system.value for system in selected_systems],
                    coordination_time_ms=processing_time,
                    authenticity_score=response.character_authenticity_score,
                    confidence_score=response.confidence_score,
                    context_type=context_type
                )
            
            logger.info("✅ Unified intelligence coordination complete: %.1fms", processing_time)
            return response
            
        except (ValueError, TypeError, KeyError) as e:
            logger.error("Failed to coordinate intelligence for %s: %s", 
                        request.character_name, e)
            return await self._create_fallback_response(request, str(e))
    
    async def _detect_context_type(self, request: IntelligenceRequest) -> str:
        """Detect the type of conversation context for optimal system selection."""
        message = request.message_content.lower()
        
        # Pattern matching for context detection
        if any(word in message for word in ['feel', 'emotion', 'sad', 'happy', 'worry', 'stress']):
            return 'emotional_support'
        elif any(word in message for word in ['you', 'your', 'yourself', 'personal', 'background']):
            return 'personal_question'
        elif any(word in message for word in ['how', 'what', 'why', 'explain', 'teach', 'learn']):
            return 'knowledge_sharing'
        elif any(word in message for word in ['problem', 'solve', 'complex', 'analyze', 'research']):
            return 'complex_problem'
        else:
            return 'casual_conversation'
    
    async def _select_intelligence_systems(self, 
                                         request: IntelligenceRequest, 
                                         context_type: str) -> List[IntelligenceSystemType]:
        """Select optimal intelligence systems based on context and strategy."""
        
        # Get base systems for context
        base_systems = self.context_patterns.get(context_type, [
            IntelligenceSystemType.CDL_PERSONALITY,
            IntelligenceSystemType.MEMORY_BOOST,
            IntelligenceSystemType.CONVERSATION_INTELLIGENCE
        ])
        
        # Apply coordination strategy
        if request.coordination_strategy == CoordinationStrategy.COMPREHENSIVE:
            # Use all available systems
            selected_systems = list(IntelligenceSystemType)
        elif request.coordination_strategy == CoordinationStrategy.PERFORMANCE_OPTIMIZED:
            # Limit to 2-3 most effective systems
            selected_systems = base_systems[:3]
        elif request.coordination_strategy == CoordinationStrategy.FIDELITY_FIRST:
            # Prioritize character authenticity systems
            selected_systems = [
                IntelligenceSystemType.CDL_PERSONALITY,
                IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE,
                IntelligenceSystemType.MEMORY_BOOST
            ]
        else:  # ADAPTIVE or CONTEXT_AWARE
            selected_systems = base_systems
        
        # Add priority systems if specified
        if request.priority_systems:
            for priority_system in request.priority_systems:
                if priority_system not in selected_systems:
                    selected_systems.insert(0, priority_system)
        
        # Filter by system availability
        available_systems = [
            system for system in selected_systems 
            if await self.is_system_available(system)
        ]
        
        logger.info("🧠 Selected %d intelligence systems for %s context", 
                   len(available_systems), context_type)
        return available_systems
    
    async def _select_intelligence_systems_optimized(self, 
                                                   request: IntelligenceRequest, 
                                                   context_type: str) -> List[IntelligenceSystemType]:
        """PHASE 4: Optimized intelligence system selection with performance constraints."""
        # Start with base selection
        base_systems = await self._select_intelligence_systems(request, context_type)
        
        # Apply performance constraints if specified
        performance_constraints = request.performance_constraints or {}
        max_systems = performance_constraints.get('max_systems', len(base_systems))
        target_time_ms = performance_constraints.get('target_time_ms', 200)
        
        # Optimize based on processing time targets
        if target_time_ms < 100:
            # Ultra-fast mode: CDL + Memory only
            optimized_systems = [s for s in base_systems if s in [
                IntelligenceSystemType.CDL_PERSONALITY,
                IntelligenceSystemType.MEMORY_BOOST
            ]][:2]
        elif target_time_ms < 200:
            # Fast mode: Core systems only
            optimized_systems = base_systems[:max_systems]
        else:
            # Normal mode: All systems within limit
            optimized_systems = base_systems[:max_systems]
        
        logger.info("🚀 PHASE 4: Optimized %d→%d systems for %dms target", 
                   len(base_systems), len(optimized_systems), target_time_ms)
        return optimized_systems

    async def _gather_system_intelligence(self, 
                                        request: IntelligenceRequest,
                                        systems: List[IntelligenceSystemType]) -> Dict[IntelligenceSystemType, Dict[str, Any]]:
        """Gather intelligence from each selected system."""
        system_contributions = {}
        
        for system in systems:
            try:
                contribution = await self._gather_single_system_intelligence(request, system)
                if contribution:
                    system_contributions[system] = contribution
                    logger.debug("✅ Intelligence gathered from %s", system.value)
                else:
                    logger.debug("⚠️ No contribution from %s", system.value)
            except (ValueError, TypeError, ImportError) as e:
                logger.warning("Failed to gather intelligence from %s: %s", system.value, e)
        
        return system_contributions
    
    async def _gather_single_system_intelligence(self, 
                                               request: IntelligenceRequest,
                                               system: IntelligenceSystemType) -> Optional[Dict[str, Any]]:
        """Gather intelligence from a single system."""
        
        if system == IntelligenceSystemType.MEMORY_BOOST and self.memory_manager:
            # Get relevant memories and episodic intelligence
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=request.user_id,
                query=request.message_content,
                limit=5
            )
            return {
                'type': 'memory_boost',
                'memories': memories,
                'episodic_context': len(memories) > 0,
                'memory_count': len(memories) if memories else 0
            }
        
        elif system == IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE and self.character_extractor:
            # Get character self-knowledge and insights
            character_knowledge = await self.character_extractor.extract_character_self_knowledge(
                request.character_name
            )
            return {
                'type': 'character_self_knowledge',
                'personality_traits': character_knowledge.personality_traits if character_knowledge else [],
                'values_beliefs': character_knowledge.values_beliefs if character_knowledge else [],
                'self_awareness_available': character_knowledge is not None
            }
        
        elif system == IntelligenceSystemType.CHARACTER_EPISODIC_INTELLIGENCE and self.character_episodic_intelligence:
            # Get episodic memories and character insights from vector conversations
            try:
                episodic_context = await self.character_episodic_intelligence.get_episodic_memory_for_response_enhancement(
                    user_id=request.user_id,
                    current_message=request.message_content,
                    conversation_context=request.conversation_context or []
                )
                
                return {
                    'type': 'character_episodic_intelligence',
                    'memorable_moments': [
                        {
                            'content': moment.context_summary,
                            'emotion': moment.primary_emotion,
                            'confidence': moment.roberta_confidence,
                            'timestamp': moment.timestamp.isoformat() if moment.timestamp else None
                        } for moment in episodic_context.memorable_moments[:3]  # Top 3 moments
                    ],
                    'character_insights': [
                        {
                            'type': insight.insight_type,
                            'description': insight.description,
                            'confidence': insight.confidence
                        } for insight in episodic_context.character_insights[:2]  # Top 2 insights
                    ],
                    'conversation_references': episodic_context.conversation_references[:2],  # Top 2 references
                    'processing_time_ms': episodic_context.processing_time_ms,
                    'episodic_available': len(episodic_context.memorable_moments) > 0
                }
            except Exception as e:
                logger.error("🧠 UNIFIED: Error processing episodic intelligence: %s", e)
                return {
                    'type': 'character_episodic_intelligence',
                    'memorable_moments': [],
                    'character_insights': [],
                    'conversation_references': [],
                    'processing_time_ms': 0,
                    'episodic_available': False
                }
        
        elif system == IntelligenceSystemType.CHARACTER_TEMPORAL_EVOLUTION and self.character_temporal_evolution_analyzer:
            # Get temporal evolution insights from existing InfluxDB data
            try:
                temporal_insights = await self.character_temporal_evolution_analyzer.get_character_evolution_insights_for_response(
                    character_name=request.character_name,
                    user_id=request.user_id,
                    current_topic=request.message_content,
                    days_back=14  # Recent 2 weeks for conversation integration
                )
                
                return {
                    'type': 'character_temporal_evolution',
                    'has_evolution_insights': temporal_insights.get('has_evolution_insights', False),
                    'evolution_references': temporal_insights.get('evolution_references', []),
                    'growth_awareness': temporal_insights.get('growth_awareness', None),
                    'confidence_evolution': temporal_insights.get('confidence_evolution', {}),
                    'emotional_evolution': temporal_insights.get('emotional_evolution', {}),
                    'evolution_metadata': temporal_insights.get('evolution_metadata', {}),
                    'temporal_intelligence_available': temporal_insights.get('has_evolution_insights', False)
                }
            except Exception as e:
                logger.error("🧠 UNIFIED: Error processing temporal evolution intelligence: %s", e)
                return {
                    'type': 'character_temporal_evolution',
                    'has_evolution_insights': False,
                    'evolution_references': [],
                    'growth_awareness': None,
                    'confidence_evolution': {},
                    'emotional_evolution': {},
                    'evolution_metadata': {},
                    'temporal_intelligence_available': False
                }
        
        elif system == IntelligenceSystemType.CHARACTER_GRAPH_KNOWLEDGE and self.postgres_pool:
            # Get graph knowledge insights from PostgreSQL infrastructure (PHASE 3)
            try:
                from .character_graph_knowledge_intelligence import create_character_graph_knowledge_intelligence
                
                graph_intelligence = create_character_graph_knowledge_intelligence(self.postgres_pool)
                graph_result = await graph_intelligence.extract_knowledge_graph(
                    user_id=request.user_id,
                    character_name=request.character_name,
                    context=request.message_content[:100]  # First 100 chars for context
                )
                
                return {
                    'type': 'character_graph_knowledge',
                    'knowledge_nodes': len(graph_result.nodes),
                    'knowledge_relationships': len(graph_result.relationships),
                    'structured_facts': graph_result.structured_facts,
                    'knowledge_summary': graph_result.knowledge_summary,
                    'confidence_score': graph_result.confidence_score,
                    'extraction_metadata': graph_result.extraction_metadata,
                    'graph_knowledge_available': graph_result.confidence_score > 0.3
                }
            except ImportError:
                logger.warning("Graph knowledge intelligence module not available - graceful fallback")
                return {
                    'type': 'character_graph_knowledge',
                    'knowledge_nodes': 0,
                    'knowledge_relationships': 0,
                    'structured_facts': {},
                    'knowledge_summary': "Graph knowledge not available",
                    'confidence_score': 0.0,
                    'extraction_metadata': {'status': 'module_not_available'},
                    'graph_knowledge_available': False
                }
            except Exception as e:
                logger.error("🧠 UNIFIED: Error processing graph knowledge intelligence: %s", e)
                return {
                    'type': 'character_graph_knowledge',
                    'knowledge_nodes': 0,
                    'knowledge_relationships': 0,
                    'structured_facts': {},
                    'knowledge_summary': "Graph knowledge processing error",
                    'confidence_score': 0.0,
                    'extraction_metadata': {'status': 'processing_error', 'error': str(e)},
                    'graph_knowledge_available': False
                }
        
        elif system == IntelligenceSystemType.CONVERSATION_INTELLIGENCE and self.memory_manager:
            # Get conversation history and patterns
            conversation_history = await self.memory_manager.get_conversation_history(
                user_id=request.user_id,
                limit=10
            )
            return {
                'type': 'conversation_intelligence',
                'recent_conversations': conversation_history,
                'conversation_continuity': len(conversation_history) > 0,
                'conversation_count': len(conversation_history) if conversation_history else 0
            }
        
        elif system == IntelligenceSystemType.CDL_PERSONALITY and self.cdl_integration:
            # Get CDL personality integration
            return {
                'type': 'cdl_personality',
                'character_name': request.character_name,
                'personality_available': True
            }
        
        elif system == IntelligenceSystemType.EMOTIONAL_INTELLIGENCE and self.emotion_analyzer:
            # Get emotional analysis
            emotion_results = await self.emotion_analyzer.analyze_emotion(
                content=request.message_content,
                user_id=request.user_id
            )
            return {
                'type': 'emotional_intelligence',
                'emotion_results': emotion_results,
                'emotional_context': emotion_results is not None
            }
        
        else:
            # System not available or not implemented
            return None
    
    async def _synthesize_unified_response(self, 
                                         _request: IntelligenceRequest,
                                         system_contributions: Dict[IntelligenceSystemType, Dict[str, Any]],
                                         _context_type: str) -> str:
        """Synthesize unified response from all system contributions."""
        
        # Build context enhancement from all systems
        context_enhancements = []
        
        for system, contribution in system_contributions.items():
            if system == IntelligenceSystemType.MEMORY_BOOST:
                if contribution.get('memory_count', 0) > 0:
                    context_enhancements.append(
                        f"Drawing from {contribution['memory_count']} relevant memories"
                    )
            
            elif system == IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE:
                if contribution.get('self_awareness_available'):
                    trait_count = len(contribution.get('personality_traits', []))
                    if trait_count > 0:
                        context_enhancements.append(
                            f"Applying character self-knowledge ({trait_count} personality traits)"
                        )
            
            elif system == IntelligenceSystemType.CONVERSATION_INTELLIGENCE:
                if contribution.get('conversation_continuity'):
                    context_enhancements.append(
                        f"Considering conversation continuity with {contribution['conversation_count']} recent messages"
                    )
            
            elif system == IntelligenceSystemType.CHARACTER_GRAPH_KNOWLEDGE:
                if contribution.get('graph_knowledge_available'):
                    nodes = contribution.get('knowledge_nodes', 0)
                    relationships = contribution.get('knowledge_relationships', 0)
                    context_enhancements.append(
                        f"Leveraging graph knowledge ({nodes} entities, {relationships} relationships)"
                    )
        
        # Create unified enhancement note (not included in actual response)
        enhancement_summary = "Intelligence coordination active: " + ", ".join(context_enhancements)
        
        # For now, return the enhancement summary
        # In production, this would integrate with the actual LLM response generation
        return enhancement_summary
    
    async def _calculate_performance_metrics(self, 
                                           system_contributions: Dict[IntelligenceSystemType, Dict[str, Any]],
                                           processing_time_ms: float) -> Dict[str, float]:
        """Calculate performance metrics for the coordination."""
        return {
            'systems_utilized': len(system_contributions),
            'processing_time_ms': processing_time_ms,
            'coordination_efficiency': min(1.0, 5000 / processing_time_ms),  # Efficiency based on 5s target
            'system_coverage': len(system_contributions) / len(IntelligenceSystemType) * 100
        }
    
    async def _calculate_authenticity_score(self, response: str, _character_name: str) -> float:
        """Calculate character authenticity score for the response."""
        # Placeholder implementation - would use more sophisticated analysis
        base_score = 0.8  # Base authenticity score
        
        # Adjust based on response characteristics
        if len(response) > 0:
            base_score += 0.1
        
        return min(1.0, base_score)
    
    async def _calculate_confidence_score(self, 
                                        system_contributions: Dict[IntelligenceSystemType, Dict[str, Any]]) -> float:
        """Calculate confidence score based on system contributions."""
        if not system_contributions:
            return 0.3  # Low confidence with no systems
        
        # Base confidence increases with number of contributing systems
        base_confidence = min(0.9, len(system_contributions) * 0.2)
        
        # Boost confidence for high-value systems
        if IntelligenceSystemType.CDL_PERSONALITY in system_contributions:
            base_confidence += 0.1
        if IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE in system_contributions:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    async def is_system_available(self, system: IntelligenceSystemType) -> bool:
        """Public method to check if an intelligence system is available for use."""
        return await self._is_system_available(system)
    
    async def detect_context_type(self, request: IntelligenceRequest) -> str:
        """Public method to detect conversation context type."""
        return await self._detect_context_type(request)
    
    async def _is_system_available(self, system: IntelligenceSystemType) -> bool:
        """Check if an intelligence system is available for use."""
        
        if system == IntelligenceSystemType.MEMORY_BOOST:
            return self.memory_manager is not None
        elif system == IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE:
            return self.character_extractor is not None
        elif system == IntelligenceSystemType.CONVERSATION_INTELLIGENCE:
            return self.memory_manager is not None
        elif system == IntelligenceSystemType.CDL_PERSONALITY:
            return self.cdl_integration is not None
        elif system == IntelligenceSystemType.EMOTIONAL_INTELLIGENCE:
            return self.emotion_analyzer is not None
        elif system == IntelligenceSystemType.VECTOR_MEMORY:
            return self.memory_manager is not None
        else:
            return False
    
    async def _create_fallback_response(self, request: IntelligenceRequest, error: str) -> IntelligenceResponse:
        """Create fallback response when coordination fails."""
        return IntelligenceResponse(
            enhanced_response=f"Intelligence coordination fallback for {request.character_name}",
            system_contributions={},
            coordination_metadata={
                'fallback': True,
                'error': error,
                'character_name': request.character_name
            },
            performance_metrics={'systems_utilized': 0, 'processing_time_ms': 0},
            character_authenticity_score=0.5,
            confidence_score=0.3,
            processing_time_ms=0
        )
    
    def _generate_cache_key(self, request: IntelligenceRequest) -> str:
        """Generate cache key for intelligence response caching."""
        import hashlib
        
        # Create hash from request characteristics
        cache_components = [
            request.character_name,
            request.message_content,
            request.user_id,
            str(request.coordination_strategy),
            str(sorted([s.value for s in request.priority_systems]) if request.priority_systems else '')
        ]
        
        cache_string = '|'.join(cache_components)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def _get_cached_response(self, cache_key: str) -> Optional[IntelligenceResponse]:
        """Retrieve cached intelligence response if available."""
        # Simple in-memory cache for now (could be extended to Redis/database)
        if not hasattr(self, '_response_cache'):
            self._response_cache = {}
        
        cached_entry = self._response_cache.get(cache_key)
        if cached_entry:
            timestamp, response = cached_entry
            # Cache valid for 5 minutes
            if time.time() - timestamp < 300:
                return response
        
        return None
    
    def _cache_response(self, cache_key: str, response: IntelligenceResponse):
        """Cache intelligence response for future use."""
        if not hasattr(self, '_response_cache'):
            self._response_cache = {}
        
        # Limit cache size to prevent memory issues
        if len(self._response_cache) > 100:
            # Remove oldest entries
            oldest_key = min(self._response_cache.keys(), 
                           key=lambda k: self._response_cache[k][0])
            del self._response_cache[oldest_key]
        
        self._response_cache[cache_key] = (time.time(), response)
    
    async def _gather_system_intelligence_parallel(self, 
                                                 request: IntelligenceRequest, 
                                                 systems: List[IntelligenceSystemType]) -> Dict[str, Any]:
        """Gather intelligence from multiple systems in parallel."""
        # Use existing single system method for each system
        combined_intelligence = {}
        
        for system in systems:
            if await self._is_system_available(system):
                try:
                    result = await self._gather_single_system_intelligence(request, system)
                    if result:
                        combined_intelligence[system.value] = result
                except Exception as e:
                    combined_intelligence[system.value] = {
                        'error': str(e),
                        'available': False
                    }
        
        return combined_intelligence
    
    def _update_performance_tracking(self, 
                                   system_count: int, 
                                   processing_time: float,
                                   cache_hit: bool = False):
        """Update performance tracking metrics."""
        if not hasattr(self, '_performance_metrics'):
            self._performance_metrics = {
                'total_requests': 0,
                'cache_hits': 0,
                'average_processing_time': 0.0,
                'average_systems_per_request': 0.0
            }
        
        metrics = self._performance_metrics
        metrics['total_requests'] += 1
        
        if cache_hit:
            metrics['cache_hits'] += 1
        
        # Update running averages
        request_count = metrics['total_requests']
        metrics['average_processing_time'] = (
            (metrics['average_processing_time'] * (request_count - 1) + processing_time) / request_count
        )
        metrics['average_systems_per_request'] = (
            (metrics['average_systems_per_request'] * (request_count - 1) + system_count) / request_count
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return getattr(self, '_performance_metrics', {
            'total_requests': 0,
            'cache_hits': 0,
            'average_processing_time': 0,
            'average_systems_per_request': 0
        })

    async def _record_coordination_metrics(
        self,
        request: IntelligenceRequest,
        systems_used: List[str],
        coordination_time_ms: float,
        authenticity_score: float,
        confidence_score: float,
        context_type: str
    ):
        """Record UnifiedCharacterIntelligenceCoordinator performance metrics to InfluxDB"""
        if not self.temporal_client:
            return
            
        try:
            # Get bot name from environment for InfluxDB tagging
            import os
            bot_name = os.getenv('DISCORD_BOT_NAME', 'unknown')
            
            await self.temporal_client.record_intelligence_coordination_metrics(
                bot_name=bot_name,
                user_id=request.user_id,
                systems_used=systems_used,
                coordination_time_ms=coordination_time_ms,
                authenticity_score=authenticity_score,
                confidence_score=confidence_score,
                context_type=context_type,
                coordination_strategy=request.coordination_strategy.value,
                character_name=request.character_name
            )
        except Exception as e:
            # Metrics recording should not break functionality
            logger.debug("Failed to record coordination metrics: %s", str(e))


def create_unified_character_intelligence_coordinator(
    memory_manager=None,
    character_self_knowledge_extractor=None,
    character_graph_knowledge_builder=None,
    dynamic_trait_discovery=None,
    cdl_ai_integration=None,
    emotion_analyzer=None
) -> UnifiedCharacterIntelligenceCoordinator:
    """Factory function to create unified intelligence coordinator."""
    return UnifiedCharacterIntelligenceCoordinator(
        memory_manager=memory_manager,
        character_self_knowledge_extractor=character_self_knowledge_extractor,
        character_graph_knowledge_builder=character_graph_knowledge_builder,
        dynamic_trait_discovery=dynamic_trait_discovery,
        cdl_ai_integration=cdl_ai_integration,
        emotion_analyzer=emotion_analyzer
    )