"""
Temporal Intelligence Protocol for WhisperEngine
Provides factory functions and integration points for temporal intelligence features
"""

import logging

from .temporal_intelligence_client import TemporalIntelligenceClient, create_temporal_intelligence_client
from .confidence_analyzer import ConfidenceAnalyzer, create_confidence_analyzer

logger = logging.getLogger(__name__)


def create_temporal_intelligence_system(knowledge_router=None) -> tuple[TemporalIntelligenceClient, ConfidenceAnalyzer]:
    """
    Create complete temporal intelligence system
    
    Args:
        knowledge_router: Optional PostgreSQL knowledge router for actual relationship scores
    
    Returns:
        tuple: (TemporalIntelligenceClient, ConfidenceAnalyzer)
    """
    temporal_client = create_temporal_intelligence_client()
    confidence_analyzer = create_confidence_analyzer(knowledge_router=knowledge_router)
    
    logger.info("Temporal intelligence system initialized (enabled: %s, postgres_integration: %s)", 
                temporal_client.enabled, knowledge_router is not None)
    return temporal_client, confidence_analyzer


def get_temporal_intelligence_status() -> dict:
    """
    Get status of temporal intelligence system
    
    Returns:
        dict: Status information
    """
    temporal_client = create_temporal_intelligence_client()
    
    return {
        'temporal_intelligence_enabled': temporal_client.enabled,
        'influxdb_available': temporal_client.enabled,
        'confidence_analysis_available': True,
        'features': {
            'confidence_evolution': temporal_client.enabled,
            'relationship_progression': temporal_client.enabled,
            'conversation_quality': temporal_client.enabled,
            'temporal_queries': temporal_client.enabled
        }
    }


# Module exports for easy importing
__all__ = [
    'TemporalIntelligenceClient',
    'ConfidenceAnalyzer', 
    'create_temporal_intelligence_client',
    'create_confidence_analyzer',
    'create_temporal_intelligence_system',
    'get_temporal_intelligence_status'
]