"""
Proactive Engagement Engine Protocol and Factory for WhisperEngine

Provides a clean, extensible interface for proactive engagement functionality with factory pattern
for simplified dependency injection and configuration management.
"""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def create_engagement_engine(
    engagement_engine_type: Optional[str] = None,
    thread_manager: Optional[Any] = None,
    memory_moments: Optional[Any] = None,
    emotional_engine: Optional[Any] = None,
    personality_profiler: Optional[Any] = None,
    memory_manager: Optional[Any] = None
) -> Any:
    """
    Factory function to create proactive engagement engine instances.
    
    Args:
        engagement_engine_type: Type of engagement engine ('full', 'basic', 'disabled', 'mock')
        thread_manager: Conversation thread manager (optional)
        memory_moments: Memory moments system (optional)
        emotional_engine: Emotional context engine (optional)
        personality_profiler: Personality profiler (optional)
        memory_manager: Vector memory manager (optional)
        
    Returns:
        Engagement engine implementation
    """
    if engagement_engine_type is None:
        engagement_engine_type = os.getenv("ENGAGEMENT_ENGINE_TYPE", "full")
    
    engagement_engine_type = engagement_engine_type.lower()
    
    logger.info("Creating engagement engine: %s", engagement_engine_type)
    
    if engagement_engine_type == "disabled":
        return NoOpEngagementEngine()
    
    elif engagement_engine_type == "full":
        try:
            # Create the main engagement engine with simplified component handling
            from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine
            
            engine = ProactiveConversationEngagementEngine(
                thread_manager=thread_manager,  # Pass through - None is fine
                memory_moments=memory_moments,  # Pass through - None is fine  
                emotional_engine=emotional_engine,  # Pass through - None is fine
                personality_profiler=personality_profiler,  # Pass through - None is fine
                memory_manager=memory_manager
            )
            
            logger.info("Full engagement engine initialized")
            return engine
            
        except ImportError as e:
            logger.warning("Failed to import engagement engine dependencies: %s", e)
            logger.info("Falling back to disabled engagement engine")
            return NoOpEngagementEngine()
        except (OSError, RuntimeError, ValueError) as e:
            logger.error("Failed to initialize engagement engine: %s", e)
            logger.info("Falling back to disabled engagement engine")
            return NoOpEngagementEngine()
    
    elif engagement_engine_type == "basic":
        try:
            # Create basic engagement engine without optional components
            from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine
            
            engine = ProactiveConversationEngagementEngine(
                thread_manager=None,
                memory_moments=None,
                emotional_engine=None,
                personality_profiler=None,
                memory_manager=memory_manager
            )
            
            logger.info("Basic engagement engine initialized")
            return engine
            
        except ImportError as e:
            logger.warning("Failed to import basic engagement engine: %s", e)
            logger.info("Falling back to disabled engagement engine")
            return NoOpEngagementEngine()
    
    elif engagement_engine_type == "mock":
        # For testing - could implement a mock engagement engine
        logger.info("Mock engagement engine not implemented, using disabled")
        return NoOpEngagementEngine()
    
    else:
        logger.warning("Unknown engagement engine type: %s, using disabled", engagement_engine_type)
        return NoOpEngagementEngine()


class NoOpEngagementEngine:
    """No-operation engagement engine for when engagement functionality is disabled."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze_engagement_potential(self, user_id: str, message: Any, conversation_history: list):
        """No-op engagement potential analysis (MessageProcessor interface)."""
        _ = user_id, message, conversation_history  # Unused arguments
        self.logger.debug("Engagement engine disabled - analyze_engagement_potential no-op")
        return {
            "engagement_potential": 0.0,
            "analysis_status": "disabled",
            "recommendations": []
        }
    
    async def analyze_conversation_engagement(self, user_id: str, context_id: str, recent_messages: list, current_thread_info=None):
        """No-op conversation engagement analysis."""
        _ = user_id, context_id, recent_messages, current_thread_info  # Unused arguments
        self.logger.debug("Engagement engine disabled - analyze_conversation_engagement no-op")
        return {
            "engagement_analysis": "disabled",
            "recommendations": [],
            "intervention_needed": False
        }
    
    async def analyze_conversation_flow(self, conversation_data):
        """No-op conversation flow analysis."""
        _ = conversation_data  # Unused argument
        self.logger.debug("Engagement engine disabled - analyze_conversation_flow no-op")
        return None
    
    async def suggest_engagement_action(self, context):
        """No-op engagement action suggestion."""
        _ = context  # Unused argument
        self.logger.debug("Engagement engine disabled - suggest_engagement_action no-op")
        return None
    
    async def process_engagement_trigger(self, trigger_data):
        """No-op engagement trigger processing."""
        _ = trigger_data  # Unused argument
        self.logger.debug("Engagement engine disabled - process_engagement_trigger no-op")
        return None
    
    def get_engagement_status(self):
        """Get engagement status."""
        return {"status": "disabled", "active_triggers": 0, "suggestions_count": 0}