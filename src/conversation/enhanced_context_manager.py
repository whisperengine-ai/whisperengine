"""
Enhanced Conversation Context Manager

This module integrates the new conversation boundary management with the existing
conversation cache system to provide enhanced context management capabilities.

Key features:
- Seamless integration with existing HybridConversationCache
- Enhanced context building with conversation boundaries
- Intelligent context pruning for long conversations
- Multi-user conversation threading support
- Conversation resumption detection and handling
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import discord

from src.conversation.boundary_manager import (
    ConversationBoundaryManager,
    ConversationSession,
    ConversationState,
    TopicTransitionType,
)

logger = logging.getLogger(__name__)


class EnhancedConversationContextManager:
    """
    Enhanced conversation context manager that integrates boundary management
    with existing conversation cache for improved context handling.
    """

    def __init__(
        self,
        conversation_cache,
        boundary_manager: Optional[ConversationBoundaryManager] = None,
        enable_boundary_management: bool = True,
    ):
        """
        Initialize enhanced conversation context manager

        Args:
            conversation_cache: Existing HybridConversationCache instance
            boundary_manager: ConversationBoundaryManager instance (creates if None)
            enable_boundary_management: Whether to enable advanced boundary features
        """
        self.conversation_cache = conversation_cache
        self.enable_boundary_management = enable_boundary_management

        if enable_boundary_management:
            self.boundary_manager = boundary_manager or ConversationBoundaryManager()
        else:
            self.boundary_manager = None

        logger.info(
            f"EnhancedConversationContextManager initialized with boundary management: {enable_boundary_management}"
        )

    async def get_enhanced_conversation_context(
        self,
        channel,
        user_id: int,
        message_content: str,
        message_id: Optional[str] = None,
        limit: int = 15,
    ) -> Dict[str, Any]:
        """
        Get enhanced conversation context with boundary awareness

        Args:
            channel: Discord channel object
            user_id: Discord user ID
            message_content: Current message content for boundary analysis
            message_id: Discord message ID
            limit: Maximum messages to retrieve

        Returns:
            Enhanced conversation context with boundary information
        """
        context = {
            "messages": [],
            "boundary_info": {},
            "context_metadata": {},
            "conversation_guidance": {},
        }

        # Get basic conversation context from existing cache
        recent_messages = await self.conversation_cache.get_user_conversation_context(
            channel, user_id, limit=limit, exclude_message_id=message_id
        )

        # Convert Discord messages to standardized format
        context["messages"] = await self._format_messages_for_context(recent_messages)

        # Add boundary management if enabled
        if self.enable_boundary_management and self.boundary_manager:
            # Process message for boundary detection
            session = await self.boundary_manager.process_message(
                user_id=str(user_id),
                channel_id=str(channel.id),
                message_id=message_id or f"temp_{datetime.now().timestamp()}",
                message_content=message_content,
                timestamp=datetime.now(),
            )

            # Get boundary-aware context
            boundary_context = await self.boundary_manager.get_conversation_context(
                user_id=str(user_id), channel_id=str(channel.id), limit=limit, include_summary=True
            )

            context["boundary_info"] = boundary_context

            # Add context metadata
            context["context_metadata"] = await self._build_context_metadata(
                session, boundary_context
            )

            # Add conversation guidance
            context["conversation_guidance"] = await self._generate_conversation_guidance(
                session, message_content
            )

        # Add message count and basic statistics
        context["statistics"] = {
            "message_count": len(context["messages"]),
            "boundary_management_enabled": self.enable_boundary_management,
            "cache_source": "hybrid_cache",
        }

        return context

    async def handle_multi_user_context(
        self,
        channel,
        all_recent_messages: List[discord.Message],
        target_user_id: int,
        limit_per_user: int = 10,
    ) -> Dict[str, Any]:
        """
        Handle conversation context in multi-user channels

        Args:
            channel: Discord channel object
            all_recent_messages: All recent messages in channel
            target_user_id: Primary user ID for context
            limit_per_user: Message limit per user

        Returns:
            Multi-user aware conversation context
        """
        context = {
            "target_user_messages": [],
            "other_user_activity": {},
            "conversation_threads": [],
            "channel_context": {},
        }

        # Separate messages by user
        user_messages = {}
        for msg in all_recent_messages:
            user_id = msg.author.id
            if user_id not in user_messages:
                user_messages[user_id] = []
            user_messages[user_id].append(msg)

        # Get target user's conversation context
        target_messages = user_messages.get(target_user_id, [])
        context["target_user_messages"] = await self._format_messages_for_context(
            target_messages[-limit_per_user:]
        )

        # Analyze other users' activity
        other_users = [
            uid
            for uid in user_messages.keys()
            if uid != target_user_id and not any(msg.author.bot for msg in user_messages[uid])
        ]

        for other_user_id in other_users[:5]:  # Limit to 5 other users
            other_messages = user_messages[other_user_id]
            context["other_user_activity"][str(other_user_id)] = {
                "message_count": len(other_messages),
                "last_activity": (
                    other_messages[-1].created_at.isoformat() if other_messages else None
                ),
                "recent_topics": await self._extract_user_topics(
                    other_messages[-3:]
                ),  # Last 3 messages
            }

        # Get multi-user conversation threads if boundary management enabled
        if self.enable_boundary_management and self.boundary_manager:
            active_user_ids = [
                str(uid)
                for uid in user_messages.keys()
                if not any(msg.author.bot for msg in user_messages[uid])
            ]
            multi_user_context = await self.boundary_manager.get_multi_user_context(
                str(channel.id), active_user_ids, limit_per_user
            )
            context["conversation_threads"] = multi_user_context.get("conversation_threads", [])

        # Add channel context metadata
        context["channel_context"] = {
            "channel_id": str(channel.id),
            "total_users_active": len(user_messages),
            "total_messages_analyzed": len(all_recent_messages),
            "multi_user_conversation": len(other_users) > 0,
        }

        return context

    async def detect_conversation_resumption(
        self, channel, user_id: int, message_content: str, time_gap_threshold_minutes: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if user is resuming a previous conversation

        Args:
            channel: Discord channel object
            user_id: Discord user ID
            message_content: Current message content
            time_gap_threshold_minutes: Minimum gap to consider resumption

        Returns:
            Resumption information if detected, None otherwise
        """
        if not self.enable_boundary_management or not self.boundary_manager:
            return None

        # Check for conversation resumption
        bridge_message = await self.boundary_manager.resume_conversation(
            str(user_id), str(channel.id), message_content
        )

        if bridge_message:
            # Get session information
            session_key = f"{user_id}:{channel.id}"
            session = self.boundary_manager.active_sessions.get(session_key)

            if session:
                time_gap = datetime.now() - session.last_activity
                gap_minutes = time_gap.total_seconds() / 60

                if gap_minutes >= time_gap_threshold_minutes:
                    return {
                        "resumption_detected": True,
                        "bridge_message": bridge_message,
                        "time_gap_minutes": gap_minutes,
                        "previous_topic": (
                            session.current_topic.keywords[:3] if session.current_topic else None
                        ),
                        "conversation_summary": session.context_summary,
                        "session_state": session.state.value,
                    }

        return None

    async def suggest_conversation_actions(
        self, channel, user_id: int, message_content: str
    ) -> List[Dict[str, Any]]:
        """
        Suggest conversation management actions based on context

        Args:
            channel: Discord channel object
            user_id: Discord user ID
            message_content: Current message content

        Returns:
            List of suggested conversation actions
        """
        suggestions = []

        if not self.enable_boundary_management or not self.boundary_manager:
            return suggestions

        session_key = f"{user_id}:{channel.id}"
        session = self.boundary_manager.active_sessions.get(session_key)

        if not session:
            return suggestions

        # Suggest summarization for long conversations
        if session.is_long_conversation(40):  # 40+ messages
            suggestions.append(
                {
                    "action": "summarize_conversation",
                    "reason": f"Long conversation with {session.message_count} messages",
                    "priority": "medium",
                    "description": "Offer to summarize the conversation so far",
                }
            )

        # Suggest topic organization for multiple topics
        if len(session.topic_history) >= 3:
            suggestions.append(
                {
                    "action": "organize_topics",
                    "reason": f"Multiple topics discussed: {len(session.topic_history)}",
                    "priority": "low",
                    "description": "Help organize the different topics discussed",
                }
            )

        # Suggest goal setting if none exists
        if not session.conversation_goal and session.message_count >= 5:
            suggestions.append(
                {
                    "action": "set_conversation_goal",
                    "reason": "Extended conversation without clear goal",
                    "priority": "low",
                    "description": "Help establish a clear conversation objective",
                }
            )

        # Suggest conclusion for conversations with completion indicators
        completion_indicators = ["thanks", "got it", "that helps", "perfect", "understood"]
        if any(indicator in message_content.lower() for indicator in completion_indicators):
            suggestions.append(
                {
                    "action": "offer_conclusion",
                    "reason": "User indicated satisfaction with help received",
                    "priority": "high",
                    "description": "Offer to conclude the conversation or ask if anything else is needed",
                }
            )

        return suggestions

    # Private helper methods

    async def _format_messages_for_context(
        self, messages: List[discord.Message]
    ) -> List[Dict[str, Any]]:
        """Format Discord messages for conversation context"""
        formatted_messages = []

        for msg in messages:
            formatted_msg = {
                "content": msg.content,
                "author_id": str(msg.author.id),
                "author_name": msg.author.display_name or msg.author.name,
                "timestamp": msg.created_at.isoformat(),
                "is_bot": msg.author.bot,
                "message_id": str(msg.id),
            }

            # Add any attachments info
            if msg.attachments:
                formatted_msg["attachments"] = [
                    {"filename": att.filename, "content_type": att.content_type}
                    for att in msg.attachments
                ]

            formatted_messages.append(formatted_msg)

        return formatted_messages

    async def _build_context_metadata(
        self, session: ConversationSession, boundary_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build context metadata from session and boundary information"""
        metadata = {
            "session_duration_minutes": session.get_duration_minutes(),
            "conversation_maturity": self._assess_conversation_maturity(session),
            "context_complexity": self._assess_context_complexity(session),
            "topic_coherence": self._assess_topic_coherence(session),
        }

        # Add boundary-specific metadata
        if boundary_context.get("is_long_conversation"):
            metadata["requires_special_handling"] = True
            metadata["recommended_summarization"] = True

        if len(boundary_context.get("topic_history", [])) > 2:
            metadata["multi_topic_conversation"] = True
            metadata["topic_tracking_important"] = True

        return metadata

    async def _generate_conversation_guidance(
        self, session: ConversationSession, message_content: str
    ) -> Dict[str, Any]:
        """Generate conversation management guidance"""
        guidance: Dict[str, Any] = {
            "context_awareness_level": "high" if session.is_long_conversation() else "normal",
            "response_strategy": "detailed" if session.message_count < 5 else "concise",
            "topic_management": "track_closely" if len(session.topic_history) > 1 else "normal",
        }

        # Add specific guidance based on conversation state
        if session.state == ConversationState.RESUMED:
            guidance["special_considerations"] = [
                "acknowledge_resumption",
                "provide_context_bridge",
            ]
        elif session.state == ConversationState.INTERRUPTED:
            guidance["special_considerations"] = ["handle_interruption_gracefully"]

        # Add guidance based on message content
        if any(word in message_content.lower() for word in ["confused", "lost", "unclear"]):
            guidance["clarification_needed"] = True
            guidance["response_strategy"] = "explanatory"

        return guidance

    async def _extract_user_topics(self, messages: List[discord.Message]) -> List[str]:
        """Extract topics from user messages for multi-user context"""
        if not messages:
            return []

        # Simple topic extraction from recent messages
        topics = []
        for msg in messages:
            if not msg.author.bot and len(msg.content) > 10:
                # Extract meaningful words (basic approach)
                words = msg.content.lower().split()
                meaningful_words = [word for word in words if len(word) > 4 and word.isalpha()]
                topics.extend(meaningful_words[:3])  # Top 3 words per message

        # Return unique topics, limited to 5
        return list(dict.fromkeys(topics))[:5]

    def _assess_conversation_maturity(self, session: ConversationSession) -> str:
        """Assess how mature/developed the conversation is"""
        if session.message_count < 3:
            return "early"
        elif session.message_count < 10:
            return "developing"
        elif session.message_count < 25:
            return "mature"
        else:
            return "extensive"

    def _assess_context_complexity(self, session: ConversationSession) -> str:
        """Assess the complexity of the conversation context"""
        complexity_score = 0

        # Factor in message count
        complexity_score += min(session.message_count / 20, 2)

        # Factor in topic diversity
        complexity_score += len(session.topic_history) * 0.5

        # Factor in duration
        complexity_score += min(session.get_duration_minutes() / 60, 1)

        if complexity_score < 1:
            return "simple"
        elif complexity_score < 2:
            return "moderate"
        elif complexity_score < 3:
            return "complex"
        else:
            return "very_complex"

    def _assess_topic_coherence(self, session: ConversationSession) -> str:
        """Assess how coherent the conversation topics are"""
        if not session.topic_history:
            return "unknown"

        if len(session.topic_history) == 1:
            return "highly_coherent"
        elif len(session.topic_history) <= 2:
            return "coherent"
        elif len(session.topic_history) <= 4:
            return "moderately_coherent"
        else:
            return "diverse_topics"

    def get_manager_statistics(self) -> Dict[str, Any]:
        """Get statistics about the enhanced conversation manager"""
        stats = {
            "boundary_management_enabled": self.enable_boundary_management,
            "cache_type": type(self.conversation_cache).__name__,
        }

        if self.boundary_manager:
            stats.update(self.boundary_manager.get_session_statistics())

        return stats
