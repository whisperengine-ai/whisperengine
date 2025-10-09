"""
Unified Character Intelligence Coordinator
WhisperEngine Memory Intelligence Convergence - PHASE 4A
Version: 1.0 - October 2025

Creates a unified coordination layer that combines all intelligence systems
(MemoryBoost, character self-knowledge, conversation intelligence) for 
holistic character responses with optimal performance.

Core Capabilities:
- Coordinates multiple AI intelligence systems
- Intelligent system selection based on context  
- Unified response generation with character authenticity
- Performance optimization through smart resource allocation
- Maintains fidelity-first principles across all systems
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class IntelligenceSystemType(Enum):
    """Types of intelligence systems available for coordination."""
    MEMORY_BOOST = "memory_boost"
    CHARACTER_SELF_KNOWLEDGE = "character_self_knowledge"
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
                 emotion_analyzer=None):
        """Initialize with available intelligence systems."""
        self.memory_manager = memory_manager
        self.character_extractor = character_self_knowledge_extractor
        self.graph_builder = character_graph_knowledge_builder
        self.trait_discovery = dynamic_trait_discovery
        self.cdl_integration = cdl_ai_integration
        self.emotion_analyzer = emotion_analyzer
        
        # Coordination state
        self.system_availability = {}
        self.performance_history = {}
        self.coordination_cache = {}
        
        # Coordination patterns
        self.context_patterns = {
            'personal_question': [
                IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE,
                IntelligenceSystemType.CDL_PERSONALITY,
                IntelligenceSystemType.MEMORY_BOOST
            ],
            'emotional_support': [
                IntelligenceSystemType.EMOTIONAL_INTELLIGENCE,
                IntelligenceSystemType.MEMORY_BOOST,
                IntelligenceSystemType.CDL_PERSONALITY
            ],
            'knowledge_sharing': [
                IntelligenceSystemType.CDL_PERSONALITY,
                IntelligenceSystemType.VECTOR_MEMORY,
                IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE
            ],
            'casual_conversation': [
                IntelligenceSystemType.CONVERSATION_INTELLIGENCE,
                IntelligenceSystemType.MEMORY_BOOST,
                IntelligenceSystemType.CDL_PERSONALITY
            ],
            'complex_problem': [
                IntelligenceSystemType.VECTOR_MEMORY,
                IntelligenceSystemType.CHARACTER_SELF_KNOWLEDGE,
                IntelligenceSystemType.CONVERSATION_INTELLIGENCE
            ]
        }
        
        logger.info("🧠 Unified Character Intelligence Coordinator initialized")
    
    async def coordinate_intelligence(self, request: IntelligenceRequest) -> IntelligenceResponse:
        """
        Coordinate all intelligence systems for unified character response.
        
        Args:
            request: Intelligence coordination request
            
        Returns:
            Unified intelligence response with system contributions
        """
        start_time = datetime.now()
        
        try:
            logger.info("🧠 UNIFIED-INTELLIGENCE: Coordinating intelligence for character %s", 
                       request.character_name)
            
            # Detect conversation context type
            context_type = await self._detect_context_type(request)
            
            # Select optimal intelligence systems
            selected_systems = await self._select_intelligence_systems(request, context_type)
            
            # Gather intelligence from each selected system
            system_contributions = await self._gather_system_intelligence(request, selected_systems)
            
            # Synthesize unified response
            unified_response = await self._synthesize_unified_response(
                request, system_contributions, context_type
            )
            
            # Calculate performance metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            performance_metrics = await self._calculate_performance_metrics(
                system_contributions, processing_time
            )
            
            # Build coordination response
            response = IntelligenceResponse(
                enhanced_response=unified_response,
                system_contributions=system_contributions,
                coordination_metadata={
                    'context_type': context_type,
                    'selected_systems': [system.value for system in selected_systems],
                    'coordination_strategy': request.coordination_strategy.value,
                    'character_name': request.character_name
                },
                performance_metrics=performance_metrics,
                character_authenticity_score=await self._calculate_authenticity_score(
                    unified_response, request.character_name
                ),
                confidence_score=await self._calculate_confidence_score(system_contributions),
                processing_time_ms=processing_time
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