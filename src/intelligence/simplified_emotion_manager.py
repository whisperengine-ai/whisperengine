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

    async def analyze_message_emotion_with_reactions(
        self, 
        user_id: str, 
        message: str, 
        conversation_context: Optional[Dict[str, Any]] = None,
        emoji_reaction_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze emotion in user message enhanced with emoji reaction feedback.
        
        Args:
            user_id: User identifier
            message: User message content
            conversation_context: Optional conversation context
            emoji_reaction_context: Recent emoji reaction patterns from user
            
        Returns:
            Enhanced emotion analysis with multimodal intelligence
        """
        logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Starting emotion analysis with reactions for user {user_id}")
        logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Message: '{message[:100]}{'...' if len(message) > 100 else ''}'")
        logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Has conversation context: {bool(conversation_context)}")
        logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Has emoji reaction context: {bool(emoji_reaction_context)}")
        
        # Get base emotion analysis
        logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Getting base emotion analysis")
        base_emotion = await self.analyze_message_emotion(user_id, message, conversation_context)
        logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Base emotion result: {base_emotion}")
        
        # Enhance with emoji reaction data if available
        if emoji_reaction_context and emoji_reaction_context.get("emotional_context") != "neutral":
            reaction_emotion = emoji_reaction_context.get("emotional_context", "neutral")
            reaction_confidence = emoji_reaction_context.get("confidence", 0.0)
            
            logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Enhancing with emoji reactions - emotion: {reaction_emotion}, confidence: {reaction_confidence:.3f}")
            
            # Blend text-based emotion with reaction-based emotion
            # Reactions are immediate feedback, so weight them highly for recent context
            if reaction_confidence > 0.5:
                logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Strong reaction confidence (>0.5), blending emotions")
                # Strong reaction confidence - blend emotions
                enhanced_emotion = self._blend_emotions(
                    text_emotion=base_emotion.get("primary_emotion", "neutral"),
                    text_confidence=base_emotion.get("confidence", 0.5),
                    reaction_emotion=reaction_emotion,
                    reaction_confidence=reaction_confidence
                )
                
                logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Blended emotion result: {enhanced_emotion}")
                
                base_emotion.update({
                    "primary_emotion": enhanced_emotion["emotion"],
                    "confidence": enhanced_emotion["confidence"],
                    "multimodal_source": "text_and_reactions",
                    "emoji_feedback": {
                        "recent_pattern": reaction_emotion,
                        "pattern_confidence": reaction_confidence,
                        "sample_size": emoji_reaction_context.get("sample_size", 0)
                    }
                })
                
                # Enhance emotional intelligence section
                if "emotional_intelligence" in base_emotion:
                    base_emotion["emotional_intelligence"].update({
                        "multimodal_analysis": True,
                        "emoji_feedback_integrated": True,
                        "reaction_pattern": reaction_emotion,
                        "confidence_boost": reaction_confidence
                    })
                
                logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Enhanced emotion with reactions: {base_emotion}")
            else:
                logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: Weak reaction confidence (<0.5), keeping base emotion")
        else:
            logger.info(f"🎭 SIMPLIFIED EMOTION MANAGER: No emoji reaction context or neutral reaction, using base emotion only")
        
        return base_emotion
    
    def _blend_emotions(self, text_emotion: str, text_confidence: float, 
                       reaction_emotion: str, reaction_confidence: float) -> Dict[str, Any]:
        """
        Blend text-based emotion analysis with emoji reaction patterns.
        
        Args:
            text_emotion: Emotion detected from text
            text_confidence: Confidence in text emotion
            reaction_emotion: Emotion pattern from reactions
            reaction_confidence: Confidence in reaction pattern
            
        Returns:
            Blended emotion result
        """
        # Map reaction types to standard emotions
        reaction_to_emotion_map = {
            "positive_strong": "joy",
            "positive_mild": "contentment", 
            "negative_strong": "frustration",
            "negative_mild": "concern",
            "mystical_wonder": "awe",
            "tech_appreciation": "engagement",
            "surprise": "surprise",
            "confusion": "confusion",
            "neutral_thoughtful": "contemplation"
        }
        
        mapped_reaction = reaction_to_emotion_map.get(reaction_emotion, reaction_emotion)
        
        # If emotions align, boost confidence
        if text_emotion == mapped_reaction or self._emotions_compatible(text_emotion, mapped_reaction):
            return {
                "emotion": text_emotion,
                "confidence": min(0.95, (text_confidence + reaction_confidence) / 2 + 0.1)
            }
        
        # If emotions conflict, use the one with higher confidence
        if reaction_confidence > text_confidence:
            return {
                "emotion": mapped_reaction,
                "confidence": reaction_confidence
            }
        else:
            return {
                "emotion": text_emotion,
                "confidence": text_confidence
            }
    
    def _emotions_compatible(self, emotion1: str, emotion2: str) -> bool:
        """Check if two emotions are compatible/related."""
        compatible_groups = [
            {"joy", "contentment", "engagement", "awe"},
            {"frustration", "concern", "confusion"},
            {"surprise", "awe", "contemplation"},
            {"neutral", "contemplation"}
        ]
        
        for group in compatible_groups:
            if emotion1 in group and emotion2 in group:
                return True
        return False

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
            
            # 🧠 DEBUG: Log conversation context for debugging
            logger.info(f"🧠 CONTEXT DEBUG: conversation_context type: {type(conversation_context)}")
            logger.info(f"🧠 CONTEXT DEBUG: conversation_context keys: {list(conversation_context.keys()) if isinstance(conversation_context, dict) else 'Not a dict'}")
            if isinstance(conversation_context, dict) and "messages" in conversation_context:
                logger.info(f"🧠 CONTEXT DEBUG: Found {len(conversation_context['messages'])} messages in conversation context")
            else:
                logger.info(f"🧠 CONTEXT DEBUG: No messages found in conversation context")
            
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
                
                # 🎭 MIXED EMOTION ENHANCEMENT: Add mixed emotion information
                "mixed_emotions": assessment.get("mixed_emotions", []),
                "emotion_description": assessment.get("emotion_description", assessment.get("primary_emotion", "neutral")),
                "all_emotions": assessment.get("all_emotions", {}),
                
                # 🎭 TRAJECTORY: Add emotional trajectory information
                "emotional_trajectory": assessment.get("emotional_trajectory", []),
                
                # Simplified emotion intelligence data for compatibility
                "emotional_intelligence": {
                    "primary_emotion": assessment.get("primary_emotion", "neutral"),
                    "confidence_score": assessment.get("confidence", 0.5),
                    "stress_indicators": assessment.get("stress_indicators", []),
                    "mood_trend": assessment.get("historical_patterns", {}).get("mood_trend", "stable"),
                    "support_recommendations": assessment.get("recommendations", []),
                    "analysis_complete": True,
                    # 🎭 MIXED EMOTION ENHANCEMENT: Include in emotional intelligence
                    "mixed_emotions": assessment.get("mixed_emotions", []),
                    "emotion_description": assessment.get("emotion_description", assessment.get("primary_emotion", "neutral")),
                    # 🎭 TRAJECTORY: Include emotional trajectory in EI data
                    "emotional_trajectory": assessment.get("emotional_trajectory", [])
                }
            }
            
            logger.info("🎭 SIMPLIFIED EMOTION MANAGER: Base emotion result: %s", emotion_data)
            
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

    async def process_message_with_emotional_intelligence(
        self, 
        user_id: str, 
        message: str, 
        conversation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compatibility method that mimics the old Phase2Integration interface.
        
        Args:
            user_id: User identifier
            message: User message
            conversation_context: Conversation context
            
        Returns:
            Enhanced context with emotion data
        """
        # Get emotion analysis using the new method
        emotion_data = await self.analyze_message_emotion(
            user_id=user_id,
            message=message,
            conversation_context=conversation_context
        )
        
        # Add emotion data to context (maintaining compatibility)
        enhanced_context = conversation_context.copy()
        enhanced_context["emotional_intelligence"] = emotion_data["emotional_intelligence"]
        enhanced_context["emotion_analysis"] = emotion_data
        
        return enhanced_context


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