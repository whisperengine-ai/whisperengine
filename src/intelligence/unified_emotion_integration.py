"""
Unified Emotion Integration
===========================

Provides a clean integration layer that uses Enhanced Vector Emotion Analyzer
while maintaining compatibility with existing caller interfaces.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    from .enhanced_vector_emotion_analyzer import create_enhanced_emotion_analyzer
    ENHANCED_EMOTION_ANALYZER_AVAILABLE = True
except ImportError as e:
    logger.error("Enhanced Vector Emotion Analyzer not available: %s", e)
    ENHANCED_EMOTION_ANALYZER_AVAILABLE = False
    create_enhanced_emotion_analyzer = None


class UnifiedEmotionIntegration:
    """
    Unified emotion integration that provides a simplified interface
    for enhanced vector-native emotion analysis.
    """

    def __init__(self, vector_memory_manager=None):
        """Initialize unified emotion integration"""
        self.vector_memory_manager = vector_memory_manager
        self.emotional_intelligence = None
        
        if ENHANCED_EMOTION_ANALYZER_AVAILABLE and create_enhanced_emotion_analyzer:
            self.emotional_intelligence = create_enhanced_emotion_analyzer(vector_memory_manager)
            logger.info("Enhanced Vector Emotion Analyzer initialized successfully")
        else:
            logger.error("Enhanced Vector Emotion Analyzer not available")

    async def comprehensive_emotional_assessment(
        self, 
        user_id: str, 
        current_message: str, 
        conversation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive emotional assessment.
        
        Args:
            user_id: User identifier
            current_message: Current user message
            conversation_context: Conversation context
            
        Returns:
            Comprehensive emotional assessment
        """
        if not self.emotional_intelligence:
            return self._create_fallback_assessment(user_id)

        try:
            return await self.emotional_intelligence.comprehensive_emotional_assessment(
                user_id, current_message, conversation_context
            )
        except (AttributeError, ValueError, TypeError, KeyError) as e:
            logger.error("Comprehensive emotional assessment failed: %s", e)
            return self._create_fallback_assessment(user_id)

    async def get_user_emotional_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get user emotional dashboard"""
        if not self.emotional_intelligence:
            return {"user_id": user_id, "error": "Emotional intelligence not available"}

        try:
            return await self.emotional_intelligence.get_user_emotional_dashboard(user_id)
        except (AttributeError, ValueError, TypeError, KeyError) as e:
            logger.error("Failed to get emotional dashboard: %s", e)
            return {"user_id": user_id, "error": str(e)}

    async def execute_intervention(self, user_id: str, intervention_type: str) -> Dict[str, Any]:
        """Execute emotional intervention"""
        if not self.emotional_intelligence:
            return {"error": "Emotional intelligence not available"}

        try:
            return await self.emotional_intelligence.execute_intervention(user_id, intervention_type)
        except (AttributeError, ValueError, TypeError, KeyError) as e:
            logger.error("Failed to execute intervention: %s", e)
            return {"error": str(e)}

    async def track_intervention_response(
        self, 
        user_id: str, 
        intervention_id: str, 
        response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track intervention response"""
        if not self.emotional_intelligence:
            return {"error": "Emotional intelligence not available"}

        try:
            return await self.emotional_intelligence.track_intervention_response(
                user_id, intervention_id, response_data
            )
        except (AttributeError, ValueError, TypeError, KeyError) as e:
            logger.error("Failed to track intervention response: %s", e)
            return {"error": str(e)}

    async def get_system_health_report(self) -> Dict[str, Any]:
        """Get system health report"""
        if not self.emotional_intelligence:
            return {"error": "Emotional intelligence not available", "system_status": "unavailable"}

        try:
            return await self.emotional_intelligence.get_system_health_report()
        except (AttributeError, ValueError, TypeError, KeyError) as e:
            logger.error("Failed to get system health report: %s", e)
            return {"error": str(e), "system_status": "error"}

    def _create_fallback_assessment(self, user_id: str) -> Dict[str, Any]:
        """Create fallback assessment when primary system unavailable"""
        return {
            "user_id": user_id,
            "primary_emotion": "neutral",
            "confidence": 0.1,
            "intensity": 0.5,
            "analysis_method": "fallback",
            "error": "Enhanced emotion analysis not available"
        }


# Factory function for easy integration
def create_unified_emotion_integration(vector_memory_manager=None) -> UnifiedEmotionIntegration:
    """Create unified emotion integration instance"""
    return UnifiedEmotionIntegration(vector_memory_manager)