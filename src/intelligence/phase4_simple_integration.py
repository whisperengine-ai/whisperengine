"""
Phase 4: Human-Like Conversation Intelligence Integration - Simplified Version

This module provides the highest level of conversational AI by integrating:
- Phase 2: Predictive Emotional Intelligence 
- Phase 3: Multi-Dimensional Memory Networks
- Human-Like Conversation Optimization
- Enhanced Query Processing

The Phase 4 integration harmonizes all systems to create truly human-like interactions
while maintaining the sophisticated capabilities of existing phases.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConversationMode(Enum):
    """Different modes of conversation processing"""
    HUMAN_LIKE = "human_like"  # Prioritize emotional intelligence and natural flow
    ANALYTICAL = "analytical"  # Prioritize factual accuracy and detailed analysis
    BALANCED = "balanced"     # Balance between human-like and analytical
    ADAPTIVE = "adaptive"     # Automatically adapt based on context

class InteractionType(Enum):
    """Types of user interactions"""
    CASUAL_CHAT = "casual_chat"
    PROBLEM_SOLVING = "problem_solving" 
    EMOTIONAL_SUPPORT = "emotional_support"
    INFORMATION_SEEKING = "information_seeking"
    CREATIVE_COLLABORATION = "creative_collaboration"

@dataclass
class Phase4Context:
    """Unified context for Phase 4 processing"""
    user_id: str
    message: str
    conversation_mode: ConversationMode
    interaction_type: InteractionType
    phase2_results: Optional[Dict[str, Any]] = None
    phase3_results: Optional[Dict[str, Any]] = None
    human_like_results: Optional[Dict[str, Any]] = None
    memory_enhancement_results: Optional[Dict[str, Any]] = None
    processing_metadata: Optional[Dict[str, Any]] = None

class Phase4HumanLikeIntegration:
    """
    Phase 4: Ultimate Human-Like Conversation Intelligence
    
    Integrates all previous phases with human-like optimization to create
    the most natural and emotionally intelligent chatbot experience.
    """
    
    def __init__(self, 
                 phase2_integration=None,
                 phase3_memory_networks=None,
                 memory_manager=None,
                 llm_client=None,
                 enable_adaptive_mode: bool = True,
                 memory_optimization: bool = True,
                 emotional_resonance: bool = True,
                 max_memory_queries: int = 15,
                 max_conversation_history: int = 25,
                 relationship_tracking: str = "enhanced",
                 query_optimization: bool = True):
        """
        Initialize Phase 4 integration
        
        Args:
            phase2_integration: Phase 2 emotional intelligence system
            phase3_memory_networks: Phase 3 memory networks system  
            memory_manager: Base memory manager
            llm_client: LLM client for processing
            enable_adaptive_mode: Whether to use adaptive features
            memory_optimization: Enable memory optimization features
            emotional_resonance: Enable emotional resonance features
            max_memory_queries: Maximum number of memory queries per interaction
            max_conversation_history: Maximum conversation history to maintain
            relationship_tracking: Level of relationship tracking (basic/enhanced)
            query_optimization: Enable query optimization
        """
        self.phase2_integration = phase2_integration
        self.phase3_memory_networks = phase3_memory_networks
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.enable_adaptive_mode = enable_adaptive_mode
        
        # Store configuration parameters
        self.memory_optimization = memory_optimization
        self.emotional_resonance = emotional_resonance
        self.max_memory_queries = max_memory_queries
        self.max_conversation_history = max_conversation_history
        self.relationship_tracking = relationship_tracking
        self.query_optimization = query_optimization
        
        # Initialize enhanced query processor for memory optimization
        self.enhanced_query_processor = None
        try:
            from ..utils.enhanced_query_processor import EnhancedQueryProcessor
            self.enhanced_query_processor = EnhancedQueryProcessor()
            logger.info("✅ Enhanced query processor initialized")
        except Exception as e:
            logger.warning(f"Enhanced query processor not available: {e}")
        
        # Conversation state tracking
        self.interaction_history = {}  # user_id -> List[InteractionType]
        self.relationship_depth = {}  # user_id -> relationship level
        
        logger.info("🤖 Phase 4: Human-Like Integration initialized")
    
    async def process_comprehensive_message(self, 
                                          user_id: str, 
                                          message: str,
                                          conversation_context: Optional[List[Dict]] = None,
                                          discord_context: Optional[Dict] = None) -> Phase4Context:
        """
        Comprehensive message processing that integrates all phases
        
        Args:
            user_id: User identifier
            message: User message content
            conversation_context: Full conversation context
            discord_context: Discord-specific context (channel, guild, etc.)
            
        Returns:
            Phase4Context with all analysis results
        """
        # Check if Phase 4 is enabled - Always enabled for full AI experience
        enable_phase4 = True  # Always enabled in unified AI system
        # Note: Phase 4 is permanently enabled for full AI capabilities
        
        processing_start = datetime.now(timezone.utc)
        logger.debug(f"Starting Phase 4 comprehensive processing for user {user_id}")
        
        try:
            # Step 1: Classify interaction type
            interaction_type = await self._classify_interaction_type(message, conversation_context)
            
            # Initialize Phase 4 context
            processing_metadata = {
                'start_time': processing_start,
                'phases_executed': [],
                'performance_metrics': {}
            }
            
            phase4_context = Phase4Context(
                user_id=user_id,
                message=message,
                conversation_mode=ConversationMode.BALANCED,
                interaction_type=interaction_type,
                processing_metadata=processing_metadata
            )
            
            # Step 2: Execute Phase 2 (Emotional Intelligence) if available
            if self.phase2_integration:
                try:
                    logger.debug("Executing Phase 2: Emotional Intelligence Analysis")
                    phase2_start = datetime.now(timezone.utc)
                    
                    phase2_context = {
                        'topic': self._extract_topic_hint(message),
                        'communication_style': 'adaptive',
                        'user_id': user_id,
                        'message_length': len(message),
                        'timestamp': processing_start.isoformat(),
                        'interaction_type': interaction_type.value
                    }
                    
                    phase2_results = await self.phase2_integration.process_message_with_emotional_intelligence(
                        user_id=user_id,
                        message=message,
                        conversation_context=phase2_context
                    )
                    
                    phase4_context.phase2_results = phase2_results
                    processing_metadata['phases_executed'].append('phase2')
                    processing_metadata['performance_metrics']['phase2_duration'] = (
                        datetime.now(timezone.utc) - phase2_start
                    ).total_seconds()
                    
                    logger.debug("✅ Phase 2 analysis completed")
                    
                except Exception as e:
                    logger.error(f"Phase 2 processing failed: {e}")
                    phase4_context.phase2_results = None
            
            # Step 3: Execute Phase 3 (Memory Networks) if available and enabled
            enable_phase3 = True  # Always enabled in unified AI system
            enable_phase3_background = True  # Always enabled for better performance
            
            if self.phase3_memory_networks and self.memory_manager and enable_phase3:
                try:
                    logger.debug(f"Executing Phase 3: Memory Networks Analysis (background={enable_phase3_background})")
                    phase3_start = datetime.now(timezone.utc)
                    
                    if enable_phase3_background:
                        # Start Phase 3 analysis in background, don't wait for completion
                        asyncio.create_task(self._run_phase3_background(user_id, processing_metadata))
                        phase4_context.phase3_results = {"status": "running_in_background", "started_at": phase3_start.isoformat()}
                        processing_metadata['phases_executed'].append('phase3_background')
                        logger.debug("✅ Phase 3 analysis started in background")
                    else:
                        # Traditional synchronous execution
                        phase3_results = await self.phase3_memory_networks.analyze_complete_memory_network(
                            user_id=user_id,
                            memory_manager=self.memory_manager
                        )
                        
                        phase4_context.phase3_results = phase3_results
                        processing_metadata['phases_executed'].append('phase3')
                        processing_metadata['performance_metrics']['phase3_duration'] = (
                            datetime.now(timezone.utc) - phase3_start
                        ).total_seconds()
                        
                        logger.debug("✅ Phase 3 analysis completed synchronously")
                    
                except Exception as e:
                    logger.error(f"Phase 3 processing failed: {e}")
                    phase4_context.phase3_results = None
            
            # Step 4: Execute Enhanced Memory Query Processing
            if self.enhanced_query_processor:
                try:
                    logger.debug("Executing Enhanced Memory Query Processing")
                    memory_enhancement_start = datetime.now(timezone.utc)
                    
                    # Generate optimized memory queries based on all available context
                    enhanced_query_result = self.enhanced_query_processor.process_message(message)
                    
                    # Convert to our expected format
                    memory_enhancement_results = {
                        'enhanced_queries': [
                            {
                                'query': query.query,
                                'weight': query.weight,
                                'query_type': query.query_type,
                                'confidence': query.confidence
                            }
                            for query in enhanced_query_result.primary_queries
                        ],
                        'fallback_query': enhanced_query_result.fallback_query,
                        'extracted_entities': enhanced_query_result.extracted_entities,
                        'intent_classification': enhanced_query_result.intent_classification,
                        'emotional_context': enhanced_query_result.emotional_context
                    }
                    
                    phase4_context.memory_enhancement_results = memory_enhancement_results
                    processing_metadata['phases_executed'].append('memory_enhancement')
                    processing_metadata['performance_metrics']['memory_enhancement_duration'] = (
                        datetime.now(timezone.utc) - memory_enhancement_start
                    ).total_seconds()
                    
                    logger.debug("✅ Enhanced memory processing completed")
                    
                except Exception as e:
                    logger.error(f"Enhanced memory processing failed: {e}")
                    phase4_context.memory_enhancement_results = None
            
            # Step 5: Calculate total processing time and update conversation state
            total_duration = (datetime.now(timezone.utc) - processing_start).total_seconds()
            processing_metadata['total_duration'] = total_duration
            processing_metadata['phases_completed'] = len(processing_metadata['phases_executed'])
            
            # Update conversation state for future interactions
            self._update_conversation_state(user_id, phase4_context)
            
            logger.info(f"✅ Phase 4 comprehensive processing completed for user {user_id} "
                       f"in {total_duration:.2f}s (phases: {', '.join(processing_metadata['phases_executed'])})")
            
            return phase4_context
            
        except Exception as e:
            logger.error(f"Phase 4 comprehensive processing failed for user {user_id}: {e}")
            # Return minimal context with error information
            error_metadata = {
                'error': str(e),
                'phases_executed': [],
                'total_duration': (datetime.now(timezone.utc) - processing_start).total_seconds()
            }
            return Phase4Context(
                user_id=user_id,
                message=message,
                conversation_mode=ConversationMode.BALANCED,
                interaction_type=InteractionType.CASUAL_CHAT,
                processing_metadata=error_metadata
            )
    
    async def _classify_interaction_type(self, 
                                       message: str,
                                       conversation_context: Optional[List[Dict]] = None) -> InteractionType:
        """Classify the type of interaction based on message content and context"""
        
        message_lower = message.lower()
        
        # Problem solving indicators
        problem_keywords = ['help', 'problem', 'issue', 'stuck', 'error', 'fix', 'solve']
        if any(keyword in message_lower for keyword in problem_keywords):
            return InteractionType.PROBLEM_SOLVING
        
        # Emotional support indicators
        emotion_keywords = ['feel', 'feeling', 'worried', 'stressed', 'sad', 'anxious', 'upset']
        if any(keyword in message_lower for keyword in emotion_keywords):
            return InteractionType.EMOTIONAL_SUPPORT
        
        # Information seeking indicators
        info_keywords = ['what', 'how', 'when', 'where', 'why', 'tell me', 'explain']
        if any(keyword in message_lower for keyword in info_keywords):
            return InteractionType.INFORMATION_SEEKING
        
        # Creative collaboration indicators
        creative_keywords = ['create', 'design', 'build', 'make', 'idea', 'brainstorm']
        if any(keyword in message_lower for keyword in creative_keywords):
            return InteractionType.CREATIVE_COLLABORATION
        
        return InteractionType.CASUAL_CHAT
    
    def _extract_topic_hint(self, message: str) -> str:
        """Extract a topic hint from the message for Phase 2 context"""
        message_lower = message.lower()
        
        # Simple topic extraction based on keywords
        if any(word in message_lower for word in ['code', 'programming', 'software']):
            return 'technology'
        elif any(word in message_lower for word in ['feel', 'emotion', 'mood']):
            return 'emotional'
        elif any(word in message_lower for word in ['work', 'job', 'career']):
            return 'professional'
        elif any(word in message_lower for word in ['friend', 'relationship', 'family']):
            return 'social'
        else:
            return 'general'
    
    def _update_conversation_state(self, user_id: str, phase4_context: Phase4Context):
        """Update conversation state for future interactions"""
        
        # Update interaction history
        if user_id not in self.interaction_history:
            self.interaction_history[user_id] = []
        self.interaction_history[user_id].append(phase4_context.interaction_type)
        
        # Keep only last 20 interactions to prevent memory bloat
        if len(self.interaction_history[user_id]) > 20:
            self.interaction_history[user_id] = self.interaction_history[user_id][-20:]
        
        # Update relationship depth based on interaction patterns
        self._update_relationship_depth(user_id, phase4_context)
    
    def _update_relationship_depth(self, user_id: str, phase4_context: Phase4Context):
        """Update relationship depth based on interaction patterns"""
        
        current_level = self.relationship_depth.get(user_id, 'new')
        interaction_count = len(self.interaction_history.get(user_id, []))
        
        # Simple relationship progression based on interaction count and types
        if interaction_count < 5:
            new_level = 'new'
        elif interaction_count < 15:
            new_level = 'developing'
        elif interaction_count < 50:
            new_level = 'established'
        else:
            new_level = 'deep'
        
        # Consider emotional support interactions for deeper relationships
        if user_id in self.interaction_history:
            emotional_interactions = sum(1 for interaction in self.interaction_history[user_id] 
                                       if interaction == InteractionType.EMOTIONAL_SUPPORT)
            if emotional_interactions >= 3 and new_level in ['developing', 'established']:
                if new_level == 'developing':
                    new_level = 'established'
                elif new_level == 'established':
                    new_level = 'deep'
        
        self.relationship_depth[user_id] = new_level
        
        if new_level != current_level:
            logger.debug(f"Relationship depth updated for user {user_id}: {current_level} -> {new_level}")
    
    def get_comprehensive_context_for_response(self, phase4_context: Phase4Context) -> Dict[str, Any]:
        """
        Generate comprehensive context for LLM response generation
        
        This method combines all Phase results into a unified context that can be used
        to generate the most appropriate and human-like response.
        """
        
        response_context = {
            'user_id': phase4_context.user_id,
            'interaction_type': phase4_context.interaction_type.value,
            'relationship_level': self.relationship_depth.get(phase4_context.user_id, 'new'),
            'processing_summary': {
                'phases_executed': phase4_context.processing_metadata.get('phases_executed', []) if isinstance(phase4_context.processing_metadata, dict) else (phase4_context.processing_metadata if isinstance(phase4_context.processing_metadata, list) else []),
                'total_duration': phase4_context.processing_metadata.get('total_duration', 0) if isinstance(phase4_context.processing_metadata, dict) else 0,
                'phases_completed': phase4_context.processing_metadata.get('phases_completed', 0) if isinstance(phase4_context.processing_metadata, dict) else len(phase4_context.processing_metadata) if isinstance(phase4_context.processing_metadata, list) else 0
            }
        }
        
        # Add Phase 2 emotional intelligence guidance
        if phase4_context.phase2_results:
            emotional_guidance = {
                'tone_adjustments': [],
                'content_suggestions': [],
                'avoid_topics': [],
                'priority_focus': []
            }
            
            # Extract guidance from Phase 2 results
            if 'mood_assessment' in phase4_context.phase2_results:
                mood = phase4_context.phase2_results['mood_assessment']
                if isinstance(mood, dict):
                    emotional_guidance['current_mood'] = mood.get('current_mood', 'neutral')
                    
                    # Add mood-specific guidance
                    if mood.get('current_mood') in ['sad', 'anxious', 'stressed']:
                        emotional_guidance['tone_adjustments'].extend([
                            'empathetic', 'supportive', 'gentle'
                        ])
                        emotional_guidance['content_suggestions'].extend([
                            'offer_support', 'validate_feelings', 'provide_comfort'
                        ])
                    elif mood.get('current_mood') in ['happy', 'excited', 'positive']:
                        emotional_guidance['tone_adjustments'].extend([
                            'enthusiastic', 'celebratory', 'encouraging'
                        ])
            
            response_context['emotional_guidance'] = emotional_guidance
        
        # Add Phase 3 memory network insights for contextualized responses
        if phase4_context.phase3_results:
            memory_insights = {
                'important_topics': [],
                'relationship_patterns': [],
                'conversation_clusters': []
            }
            
            # Extract key insights from Phase 3 results
            if 'network_insights' in phase4_context.phase3_results:
                insights = phase4_context.phase3_results['network_insights']
                if isinstance(insights, dict):
                    memory_insights['network_strength'] = insights.get('network_strength', 0)
                    memory_insights['key_topics'] = insights.get('primary_topics', [])
            
            response_context['memory_insights'] = memory_insights
        
        # Add enhanced memory query results
        if phase4_context.memory_enhancement_results and isinstance(phase4_context.memory_enhancement_results, dict):
            enhanced_memory = {
                'enhanced_queries': phase4_context.memory_enhancement_results.get('enhanced_queries', []),
                'extracted_entities': phase4_context.memory_enhancement_results.get('extracted_entities', []),
                'intent_classification': phase4_context.memory_enhancement_results.get('intent_classification', 'unknown'),
                'emotional_context': phase4_context.memory_enhancement_results.get('emotional_context')
            }
            response_context['enhanced_memory'] = enhanced_memory
        
        return response_context
    
    async def cleanup(self):
        """Cleanup resources and connections"""
        try:
            # Clear conversation state (keep relationship depth for persistence)
            # No conversation modes to clear anymore
            
            logger.info("Phase 4 Human-Like Integration cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during Phase 4 cleanup: {e}")

    def get_integration_status(self) -> Dict[str, Any]:
        """Get the current status of all integrated systems"""
        return {
            'phase4_status': 'active',
            'phase2_available': self.phase2_integration is not None,
            'phase3_available': self.phase3_memory_networks is not None,
            'enhanced_query_processor_available': self.enhanced_query_processor is not None,
            'adaptive_mode_enabled': self.enable_adaptive_mode,
            'tracked_users': {
                'interaction_histories': len(self.interaction_history),
                'relationship_depths': len(self.relationship_depth)
            },
            'integration_health': self._check_integration_health()
        }
    
    async def _run_phase3_background(self, user_id: str, processing_metadata: Dict[str, Any]):
        """Run Phase 3 analysis in background without blocking the main response"""
        try:
            if not self.phase3_memory_networks or not self.memory_manager:
                logger.warning("Phase 3 components not available for background analysis")
                return
            
            logger.debug(f"Starting background Phase 3 analysis for user {user_id}")
            phase3_start = datetime.now(timezone.utc)
            
            # Run the memory network analysis
            phase3_results = await self.phase3_memory_networks.analyze_complete_memory_network(
                user_id=user_id,
                memory_manager=self.memory_manager
            )
            
            duration = (datetime.now(timezone.utc) - phase3_start).total_seconds()
            logger.info(f"✅ Background Phase 3 analysis completed for user {user_id} in {duration:.2f}s")
            
            # Store results in a background cache if needed
            # This could be enhanced to update a cache that future requests can use
            
        except Exception as e:
            logger.error(f"Background Phase 3 analysis failed for user {user_id}: {e}")
    
    def _check_integration_health(self) -> str:
        """Check the health of all integrated systems"""
        available_systems = 0
        total_systems = 3  # Phase2, Phase3, EnhancedQuery
        
        if self.phase2_integration:
            available_systems += 1
        if self.phase3_memory_networks:
            available_systems += 1
        if self.enhanced_query_processor:
            available_systems += 1
        
        health_percentage = (available_systems / total_systems) * 100
        
        if health_percentage >= 75:
            return 'excellent'
        elif health_percentage >= 50:
            return 'good'
        elif health_percentage >= 25:
            return 'fair'
        else:
            return 'poor'