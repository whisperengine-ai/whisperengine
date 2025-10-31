"""
Proactive Engagement Engine Protocol and Factory for WhisperEngine

DEPRECATED: ProactiveConversationEngagementEngine was removed (orphaned code).
The active production system is in src/enrichment/proactive_engagement_engine.py
which runs in background workers and caches results in PostgreSQL.

This factory now only returns NoOpEngagementEngine for backward compatibility.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def create_engagement_engine(
    engagement_engine_type: Optional[str] = None,  # noqa: ARG001
    thread_manager: Optional[Any] = None,  # noqa: ARG001
    memory_moments: Optional[Any] = None,  # noqa: ARG001
    emotional_engine: Optional[Any] = None,  # noqa: ARG001
    personality_profiler: Optional[Any] = None,  # noqa: ARG001
    memory_manager: Optional[Any] = None  # noqa: ARG001
) -> Any:
    """
    Factory function for proactive engagement engine - DEPRECATED.
    
    The conversation-based ProactiveConversationEngagementEngine was removed after
    Phase 1-2 optimization (commit 9c17d66). The production system runs in the
    enrichment worker and caches results in PostgreSQL strategic_engagement_opportunities.
    
    This factory now always returns NoOpEngagementEngine for backward compatibility.
    All parameters are kept for API compatibility but ignored.
    
    Returns:
        NoOpEngagementEngine instance
    """
    logger.info("ProactiveConversationEngagementEngine removed - using NoOpEngagementEngine (enrichment worker provides real functionality)")
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