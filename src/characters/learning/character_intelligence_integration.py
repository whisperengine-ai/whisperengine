"""
Character Intelligence Integration Framework
WhisperEngine Memory Intelligence Convergence - PHASE 4A Integration
Version: 1.0 - October 2025

Integrates the Unified Character Intelligence Coordinator into WhisperEngine's
message processing pipeline, enabling seamless character intelligence coordination
without disrupting existing functionality.

Core Capabilities:
- Seamless integration with existing message processor
- Backward compatibility with existing systems
- Performance monitoring and optimization
- Fallback handling for system failures
- Progressive enhancement architecture
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
from dataclasses import dataclass

from .unified_character_intelligence_coordinator import (
    UnifiedCharacterIntelligenceCoordinator,
    IntelligenceRequest,
    IntelligenceResponse,
    CoordinationStrategy,
    IntelligenceSystemType,
    create_unified_character_intelligence_coordinator
)

logger = logging.getLogger(__name__)

@dataclass
class IntegrationConfig:
    """Configuration for intelligence integration."""
    enabled: bool = True
    coordination_strategy: CoordinationStrategy = CoordinationStrategy.ADAPTIVE
    fallback_on_error: bool = True
    performance_monitoring: bool = True
    max_processing_time_ms: float = 5000.0
    min_systems_required: int = 1

class CharacterIntelligenceIntegration:
    """
    Integration layer for character intelligence coordination.
    
    This class provides a clean integration point between the existing
    WhisperEngine message processing pipeline and the new unified
    character intelligence coordination system.
    
    Key features:
    - Progressive enhancement (works with or without intelligence systems)
    - Backward compatibility (existing functionality unchanged)
    - Performance optimization (intelligent resource management)
    - Error resilience (graceful fallbacks)
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialize intelligence integration."""
        self.config = config or IntegrationConfig()
        self.coordinator: Optional[UnifiedCharacterIntelligenceCoordinator] = None
        self.integration_metrics = {
            'requests_processed': 0,
            'successful_coordinations': 0,
            'fallback_count': 0,
            'average_processing_time': 0.0
        }
        
        logger.info("🔗 Character Intelligence Integration initialized")
    
    async def initialize_coordinator(self,
                                   memory_manager=None,
                                   character_self_knowledge_extractor=None,
                                   character_graph_knowledge_builder=None,
                                   dynamic_trait_discovery=None,
                                   cdl_ai_integration=None,
                                   emotion_analyzer=None):
        """Initialize the unified intelligence coordinator with available systems."""
        try:
            self.coordinator = create_unified_character_intelligence_coordinator(
                memory_manager=memory_manager,
                character_self_knowledge_extractor=character_self_knowledge_extractor,
                character_graph_knowledge_builder=character_graph_knowledge_builder,
                dynamic_trait_discovery=dynamic_trait_discovery,
                cdl_ai_integration=cdl_ai_integration,
                emotion_analyzer=emotion_analyzer
            )
            
            logger.info("✅ Unified Character Intelligence Coordinator initialized")
            return True
            
        except (ImportError, ValueError, TypeError) as e:
            logger.warning("Failed to initialize intelligence coordinator: %s", e)
            self.coordinator = None
            return False
    
    async def enhance_message_processing(self,
                                       user_id: str,
                                       character_name: str,
                                       message_content: str,
                                       conversation_context: Optional[List[Dict[str, Any]]] = None,
                                       processing_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enhance message processing with unified character intelligence.
        
        This method integrates with the existing message processing pipeline
        to add intelligence coordination without disrupting existing functionality.
        
        Args:
            user_id: User identifier
            character_name: Character name
            message_content: Message content to process
            conversation_context: Optional conversation context
            processing_metadata: Optional processing metadata
            
        Returns:
            Dictionary containing intelligence enhancements and metadata
        """
        self.integration_metrics['requests_processed'] += 1
        
        # Check if intelligence coordination is enabled and available
        if not self.config.enabled or not self.coordinator:
            return await self._create_passthrough_result(processing_metadata)
        
        try:
            # Create intelligence request
            intelligence_request = IntelligenceRequest(
                user_id=user_id,
                character_name=character_name,
                message_content=message_content,
                conversation_context=conversation_context or [],
                coordination_strategy=self.config.coordination_strategy,
                performance_constraints={
                    'max_processing_time_ms': self.config.max_processing_time_ms
                }
            )
            
            # Coordinate intelligence with timeout
            intelligence_response = await asyncio.wait_for(
                self.coordinator.coordinate_intelligence(intelligence_request),
                timeout=self.config.max_processing_time_ms / 1000.0
            )
            
            # Update metrics
            self.integration_metrics['successful_coordinations'] += 1
            self._update_processing_time_metric(intelligence_response.processing_time_ms)
            
            # Build integration result
            return await self._create_intelligence_result(intelligence_response, processing_metadata)
            
        except asyncio.TimeoutError:
            logger.warning("Intelligence coordination timeout for user %s", user_id)
            self.integration_metrics['fallback_count'] += 1
            return await self._create_timeout_fallback_result(processing_metadata)
            
        except (ValueError, TypeError, KeyError) as e:
            logger.warning("Intelligence coordination error for user %s: %s", user_id, e)
            self.integration_metrics['fallback_count'] += 1
            return await self._create_error_fallback_result(processing_metadata, str(e))
    
    async def _create_intelligence_result(self, 
                                        intelligence_response: IntelligenceResponse,
                                        processing_metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create result with intelligence coordination data."""
        result = {
            'intelligence_coordination': {
                'enabled': True,
                'successful': True,
                'system_contributions': intelligence_response.system_contributions,
                'coordination_metadata': intelligence_response.coordination_metadata,
                'performance_metrics': intelligence_response.performance_metrics,
                'character_authenticity_score': intelligence_response.character_authenticity_score,
                'confidence_score': intelligence_response.confidence_score,
                'processing_time_ms': intelligence_response.processing_time_ms
            },
            'enhanced_context': {
                'intelligence_enhanced': True,
                'enhancement_summary': intelligence_response.enhanced_response,
                'systems_utilized': len(intelligence_response.system_contributions)
            }
        }
        
        # Merge with existing processing metadata
        if processing_metadata:
            result.update(processing_metadata)
        
        return result
    
    async def _create_passthrough_result(self, processing_metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create passthrough result when intelligence coordination is disabled."""
        result = {
            'intelligence_coordination': {
                'enabled': False,
                'successful': False,
                'reason': 'Intelligence coordination disabled or unavailable'
            },
            'enhanced_context': {
                'intelligence_enhanced': False
            }
        }
        
        if processing_metadata:
            result.update(processing_metadata)
        
        return result
    
    async def _create_timeout_fallback_result(self, processing_metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create fallback result for timeout scenarios."""
        result = {
            'intelligence_coordination': {
                'enabled': True,
                'successful': False,
                'reason': 'Processing timeout',
                'fallback_used': True
            },
            'enhanced_context': {
                'intelligence_enhanced': False,
                'fallback_reason': 'timeout'
            }
        }
        
        if processing_metadata:
            result.update(processing_metadata)
        
        return result
    
    async def _create_error_fallback_result(self, 
                                          processing_metadata: Optional[Dict[str, Any]],
                                          error: str) -> Dict[str, Any]:
        """Create fallback result for error scenarios."""
        result = {
            'intelligence_coordination': {
                'enabled': True,
                'successful': False,
                'reason': f'Processing error: {error}',
                'fallback_used': True
            },
            'enhanced_context': {
                'intelligence_enhanced': False,
                'fallback_reason': 'error'
            }
        }
        
        if processing_metadata:
            result.update(processing_metadata)
        
        return result
    
    def _update_processing_time_metric(self, processing_time_ms: float):
        """Update average processing time metric."""
        current_avg = self.integration_metrics['average_processing_time']
        successful_count = self.integration_metrics['successful_coordinations']
        
        # Calculate new average
        new_avg = ((current_avg * (successful_count - 1)) + processing_time_ms) / successful_count
        self.integration_metrics['average_processing_time'] = new_avg
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get current integration metrics."""
        total_requests = self.integration_metrics['requests_processed']
        successful = self.integration_metrics['successful_coordinations']
        fallbacks = self.integration_metrics['fallback_count']
        
        return {
            'total_requests': total_requests,
            'successful_coordinations': successful,
            'fallback_count': fallbacks,
            'success_rate': (successful / total_requests * 100) if total_requests > 0 else 0,
            'fallback_rate': (fallbacks / total_requests * 100) if total_requests > 0 else 0,
            'average_processing_time_ms': self.integration_metrics['average_processing_time'],
            'coordinator_available': self.coordinator is not None,
            'integration_enabled': self.config.enabled
        }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        if not self.coordinator:
            return {
                'coordinator_status': 'unavailable',
                'available_systems': [],
                'system_health': 'degraded'
            }
        
        # Check system availability
        available_systems = []
        for system_type in IntelligenceSystemType:
            if await self.coordinator.is_system_available(system_type):
                available_systems.append(system_type.value)
        
        return {
            'coordinator_status': 'available',
            'available_systems': available_systems,
            'system_count': len(available_systems),
            'system_health': 'healthy' if len(available_systems) >= self.config.min_systems_required else 'degraded',
            'integration_metrics': self.get_integration_metrics()
        }

def create_character_intelligence_integration(config: Optional[IntegrationConfig] = None) -> CharacterIntelligenceIntegration:
    """Factory function to create character intelligence integration."""
    return CharacterIntelligenceIntegration(config=config)