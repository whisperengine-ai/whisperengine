"""
Simplified Emotion Integration Manager
=====================================

Modern, simplified emotion integration that replaces the complex Phase2Integration class.
Focuses on core emotion analysis without complex intervention logic.
Uses Enhanced Vector Emotion Analyzer as the primary system.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from .unified_emotion_integration import create_unified_emotion_integration
    UNIFIED_EMOTION_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logger.error("Unified Emotion Integration not available: %s", e)
    UNIFIED_EMOTION_INTEGRATION_AVAILABLE = False
    create_unified_emotion_integration = None


class SimplifiedEmotionManager:
    """
    Simplified emotion integration manager.
    
    Replaces the complex Phase2Integration class with a cleaner, focused approach.
    Provides emotion analysis without complex intervention management.
    """

    def __init__(self, vector_memory_manager=None):
        """Initialize simplified emotion manager"""
        self.vector_memory_manager = vector_memory_manager
        self.emotion_integration = None
        
        if UNIFIED_EMOTION_INTEGRATION_AVAILABLE and create_unified_emotion_integration:
            self.emotion_integration = create_unified_emotion_integration(vector_memory_manager)
            logger.info("✅ Simplified Emotion Manager initialized with Enhanced Vector system")
        else:
            logger.error("❌ Emotion integration not available")

    async def analyze_message_emotion(
        self, 
        user_id: str, 
        message: str, 
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze emotion in user message.
        
        Args:
            user_id: User identifier
            message: User message content
            conversation_context: Optional conversation context
            
        Returns:
            Emotion analysis result with recommendations
        """
        if not self.emotion_integration:
            return self._create_fallback_emotion_data(user_id)

        try:
            # Use conversation_context or create minimal context
            context = conversation_context or {"messages": []}
            
            # Get comprehensive emotional assessment
            assessment = await self.emotion_integration.comprehensive_emotional_assessment(
                user_id=user_id,
                current_message=message,
                conversation_context=context
            )
            
            # Transform to simplified format for callers
            emotion_data = {
                "user_id": user_id,
                "primary_emotion": assessment.get("primary_emotion", "neutral"),
                "confidence": assessment.get("confidence", 0.5),
                "intensity": assessment.get("intensity", 0.5),
                "recommendations": assessment.get("recommendations", []),
                "support_needed": assessment.get("intervention_needed", False),
                "analysis_method": "enhanced_vector",
                "timestamp": assessment.get("timestamp"),
                
                # Simplified emotion intelligence data for compatibility
                "emotional_intelligence": {
                    "primary_emotion": assessment.get("primary_emotion", "neutral"),
                    "confidence_score": assessment.get("confidence", 0.5),
                    "stress_indicators": assessment.get("stress_indicators", []),
                    "mood_trend": assessment.get("historical_patterns", {}).get("mood_trend", "stable"),
                    "support_recommendations": assessment.get("recommendations", []),
                    "analysis_complete": True
                }
            }
            
            logger.debug("Emotion analysis completed for user %s: %s (%.2f confidence)", 
                        user_id, emotion_data["primary_emotion"], emotion_data["confidence"])
            
            return emotion_data
            
        except Exception as e:
            logger.error("Emotion analysis failed for user %s: %s", user_id, e)
            return self._create_fallback_emotion_data(user_id, error=str(e))

    async def get_user_emotional_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get user emotional dashboard"""
        if not self.emotion_integration:
            return {"user_id": user_id, "error": "Emotion integration not available"}

        try:
            return await self.emotion_integration.get_user_emotional_dashboard(user_id)
        except Exception as e:
            logger.error("Failed to get emotional dashboard for user %s: %s", user_id, e)
            return {"user_id": user_id, "error": str(e)}

    async def get_system_health(self) -> Dict[str, Any]:
        """Get emotion system health status"""
        if not self.emotion_integration:
            return {"status": "unavailable", "error": "Emotion integration not available"}

        try:
            return await self.emotion_integration.get_system_health_report()
        except Exception as e:
            logger.error("Failed to get emotion system health: %s", e)
            return {"status": "error", "error": str(e)}

    def is_available(self) -> bool:
        """Check if emotion analysis is available"""
        return self.emotion_integration is not None

    def _create_fallback_emotion_data(self, user_id: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Create fallback emotion data when analysis fails"""
        return {
            "user_id": user_id,
            "primary_emotion": "neutral",
            "confidence": 0.1,
            "intensity": 0.5,
            "recommendations": [],
            "support_needed": False,
            "analysis_method": "fallback",
            "error": error,
            "emotional_intelligence": {
                "primary_emotion": "neutral",
                "confidence_score": 0.1,
                "stress_indicators": [],
                "mood_trend": "unknown",
                "support_recommendations": [],
                "analysis_complete": False,
                "fallback_mode": True
            }
        }


# Factory function for easy integration
def create_simplified_emotion_manager(vector_memory_manager=None) -> SimplifiedEmotionManager:
    """Create simplified emotion manager instance"""
    return SimplifiedEmotionManager(vector_memory_manager)


# Compatibility function for existing callers
async def process_message_with_emotional_intelligence(
    user_id: str, 
    message: str, 
    conversation_context: Dict[str, Any],
    emotion_manager: SimplifiedEmotionManager
) -> Dict[str, Any]:
    """
    Compatibility function that mimics the old Phase2Integration interface.
    
    Args:
        user_id: User identifier
        message: User message
        conversation_context: Conversation context
        emotion_manager: SimplifiedEmotionManager instance
        
    Returns:
        Enhanced context with emotion data
    """
    # Get emotion analysis
    emotion_data = await emotion_manager.analyze_message_emotion(
        user_id=user_id,
        message=message,
        conversation_context=conversation_context
    )
    
    # Add emotion data to context (maintaining compatibility)
    enhanced_context = conversation_context.copy()
    enhanced_context["emotional_intelligence"] = emotion_data["emotional_intelligence"]
    enhanced_context["emotion_analysis"] = emotion_data
    
    return enhanced_context