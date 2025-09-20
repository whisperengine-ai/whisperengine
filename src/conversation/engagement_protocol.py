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
    personality_profiler: Optional[Any] = None
) -> Any:
    """
    Factory function to create proactive engagement engine instances.
    
    Args:
        engagement_engine_type: Type of engagement engine ('full', 'basic', 'disabled', 'mock')
        thread_manager: Conversation thread manager (optional)
        memory_moments: Memory moments system (optional)
        emotional_engine: Emotional context engine (optional)
        personality_profiler: Personality profiler (optional)
        
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
            # Import all optional components for full functionality
            components = {}
            
            # Thread Manager
            try:
                from src.conversation.advanced_thread_manager import AdvancedConversationThreadManager
                components['thread_manager'] = thread_manager or AdvancedConversationThreadManager
                logger.debug("Thread manager available for engagement engine")
            except ImportError:
                logger.warning("Thread manager not available - limited thread integration")
                components['thread_manager'] = None
            
            # Memory Moments
            try:
                import src.personality.memory_moments  # Just check availability
                _ = src.personality.memory_moments  # Mark as used
                components['memory_moments'] = memory_moments
                logger.debug("Memory moments available for engagement engine")
            except ImportError:
                logger.warning("Memory moments not available - limited memory integration")
                components['memory_moments'] = None
            
            # Emotional Context
            try:
                import src.intelligence.emotional_context_engine  # Just check availability
                _ = src.intelligence.emotional_context_engine  # Mark as used
                components['emotional_engine'] = emotional_engine
                logger.debug("Emotional context available for engagement engine")
            except ImportError:
                logger.warning("Emotional context not available - limited emotional integration")
                components['emotional_engine'] = None
            
            # Personality Profiler
            try:
                import src.intelligence.dynamic_personality_profiler  # Just check availability
                _ = src.intelligence.dynamic_personality_profiler  # Mark as used
                components['personality_profiler'] = personality_profiler
                logger.debug("Personality profiler available for engagement engine")
            except ImportError:
                logger.warning("Personality profiler not available - limited personality integration")
                components['personality_profiler'] = None
            
            # Create the main engagement engine
            from src.conversation.proactive_engagement_engine import ProactiveConversationEngagementEngine
            
            engine = ProactiveConversationEngagementEngine(
                thread_manager=components['thread_manager'],
                memory_moments=components['memory_moments'],
                emotional_engine=components['emotional_engine'],
                personality_profiler=components['personality_profiler']
            )
            
            logger.info("Full engagement engine initialized with available components")
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
                personality_profiler=None
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