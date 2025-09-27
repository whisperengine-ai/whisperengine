"""
Enhanced Conversation Boundary Management System

This module provides advanced conversation management capabilities including:
- Conversation session tracking and boundary detection
- Topic transition analysis and conversation segmentation
- Enhanced context management for long conversations (50+ messages)
- Multi-user channel conversation threading
- Conversation resumption after interruptions
- Intelligent context pruning and summarization

Key improvements over the existing system:
- Explicit conversation session boundaries instead of continuous streams
- Topic coherence tracking and automatic segmentation
- Conversation state persistence across cache expiration
- Context preservation for conversation resumption
- Separate conversation threads in multi-user channels
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation states for session management"""

    ACTIVE = "active"  # Currently ongoing conversation
    PAUSED = "paused"  # Temporarily paused (user went idle)
    RESUMED = "resumed"  # Recently resumed after a pause
    COMPLETED = "completed"  # Conversation naturally ended
    INTERRUPTED = "interrupted"  # Interrupted by another user/topic
    ARCHIVED = "archived"  # Stored for historical reference


class TopicTransitionType(Enum):
    """Types of topic transitions in conversations"""

    NATURAL_FLOW = "natural_flow"  # Topic evolved naturally
    EXPLICIT_CHANGE = "explicit_change"  # User explicitly changed topic
    INTERRUPTION = "interruption"  # External interruption
    RESUMPTION = "resumption"  # Resuming previous topic
    NEW_SESSION = "new_session"  # Starting completely new conversation


@dataclass
class ConversationTopic:
    """Represents a conversation topic segment"""

    topic_id: str
    keywords: list[str]
    start_time: datetime
    end_time: datetime | None = None
    message_count: int = 0
    emotional_tone: str | None = None
    resolution_status: str | None = None  # resolved, pending, ongoing

    def is_active(self) -> bool:
        """Check if topic is currently active"""
        return self.end_time is None

    def get_duration_minutes(self) -> float:
        """Get topic duration in minutes"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds() / 60


@dataclass
class ConversationSession:
    """Represents a complete conversation session with boundaries"""

    session_id: str
    user_id: str
    channel_id: str
    start_time: datetime
    last_activity: datetime
    state: ConversationState = ConversationState.ACTIVE
    current_topic: ConversationTopic | None = None
    topic_history: list[ConversationTopic] = field(default_factory=list)
    message_count: int = 0
    context_summary: str = ""
    conversation_goal: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

    def get_duration_minutes(self) -> float:
        """Get total session duration in minutes"""
        return (self.last_activity - self.start_time).total_seconds() / 60

    def is_long_conversation(self, message_threshold: int = 50) -> bool:
        """Check if this is a long conversation requiring special handling"""
        return self.message_count >= message_threshold

    def get_active_topics(self) -> list[ConversationTopic]:
        """Get currently active topics"""
        return [topic for topic in self.topic_history if topic.is_active()]


@dataclass
class ConversationSegment:
    """A segment of conversation with coherent context"""

    segment_id: str
    session_id: str
    start_message_id: str | None
    end_message_id: str | None
    topic: ConversationTopic
    message_ids: list[str] = field(default_factory=list)
    context_summary: str = ""
    importance_score: float = 0.0

    def add_message(self, message_id: str):
        """Add message to this segment"""
        self.message_ids.append(message_id)
        if not self.start_message_id:
            self.start_message_id = message_id
        self.end_message_id = message_id


class ConversationBoundaryManager:
    """
    Advanced conversation boundary management system

    Handles conversation session tracking, topic transitions, and context management
    for both long conversations and multi-user scenarios.
    """

    def __init__(
        self,
        session_timeout_minutes: int = 30,
        topic_transition_threshold: float = 0.6,
        max_context_messages: int = 100,
        summarization_threshold: int = 50,
        llm_client=None,
        redis_client=None,
    ):
        """
        Initialize conversation boundary manager

        Args:
            session_timeout_minutes: Minutes before marking session as paused
            topic_transition_threshold: Threshold for detecting topic changes (0-1)
            max_context_messages: Maximum messages to keep in active context
            summarization_threshold: Message count before triggering summarization
            llm_client: LLM client for intelligent summarization (optional)
            redis_client: Redis client for session persistence (optional)
        """
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.topic_transition_threshold = topic_transition_threshold
        self.max_context_messages = max_context_messages
        self.summarization_threshold = summarization_threshold
        self.llm_client = llm_client
        self.redis_client = redis_client

        # Active session storage
        self.active_sessions: dict[str, ConversationSession] = {}
        self.session_segments: dict[str, list[ConversationSegment]] = {}

        # Topic transition keywords for detection
        self.transition_indicators = {
            "explicit_change": [
                "anyway",
                "by the way",
                "speaking of",
                "on another note",
                "let me ask about",
                "different question",
                "new topic",
                "change subject",
                "moving on",
                "forget that",
            ],
            "resumption": [
                "back to",
                "returning to",
                "as I was saying",
                "continuing",
                "earlier you mentioned",
                "going back to",
            ],
            "completion": [
                "thanks for helping",
                "that answers my question",
                "got it",
                "makes sense",
                "understood",
                "perfect",
                "that's all",
            ],
        }

        logger.info(
            f"ConversationBoundaryManager initialized with {session_timeout_minutes}min timeout"
        )

    def _get_session_redis_key(self, user_id: str, channel_id: str) -> str:
        """Get Redis key for storing conversation session"""
        return f"conversation_session:{user_id}:{channel_id}"

    async def _save_session_to_redis(self, session: ConversationSession) -> None:
        """Persist conversation session to Redis"""
        if not self.redis_client:
            return
        
        try:
            # Prepare session data for serialization
            session_data = {
                'session_id': session.session_id,
                'user_id': session.user_id,
                'channel_id': session.channel_id,
                'start_time': session.start_time.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'state': session.state.value,
                'message_count': session.message_count,
                'context_summary': session.context_summary,
                'conversation_goal': session.conversation_goal,
                'metadata': session.metadata,
                'topic_history': []
            }
            
            # Serialize topic history
            for topic in session.topic_history:
                topic_data = {
                    'topic_id': topic.topic_id,
                    'keywords': topic.keywords,
                    'start_time': topic.start_time.isoformat(),
                    'end_time': topic.end_time.isoformat() if topic.end_time else None,
                    'message_count': topic.message_count,
                    'emotional_tone': topic.emotional_tone,
                    'resolution_status': topic.resolution_status
                }
                session_data['topic_history'].append(topic_data)
            
            # Store in Redis with 2-hour TTL (longer than session timeout for recovery)
            redis_key = self._get_session_redis_key(session.user_id, session.channel_id)
            await self.redis_client.setex(redis_key, 7200, json.dumps(session_data))
            
            logger.debug("Saved session %s to Redis", session.session_id)
            
        except Exception as e:
            logger.warning("Failed to save session to Redis: %s", str(e))

    async def _load_session_from_redis(self, user_id: str, channel_id: str) -> ConversationSession | None:
        """Load conversation session from Redis"""
        if not self.redis_client:
            return None
            
        try:
            redis_key = self._get_session_redis_key(user_id, channel_id)
            session_data_str = await self.redis_client.get(redis_key)
            
            if not session_data_str:
                return None
                
            session_data = json.loads(session_data_str)
            
            # Reconstruct topic history
            topic_history = []
            for topic_data in session_data.get('topic_history', []):
                end_time = None
                if topic_data.get('end_time'):
                    end_time = datetime.fromisoformat(topic_data['end_time'])
                    
                topic = ConversationTopic(
                    topic_id=topic_data['topic_id'],
                    keywords=topic_data['keywords'],
                    start_time=datetime.fromisoformat(topic_data['start_time']),
                    end_time=end_time,
                    message_count=topic_data['message_count'],
                    emotional_tone=topic_data.get('emotional_tone'),
                    resolution_status=topic_data.get('resolution_status')
                )
                topic_history.append(topic)
            
            # Reconstruct session
            session = ConversationSession(
                session_id=session_data['session_id'],
                user_id=session_data['user_id'],
                channel_id=session_data['channel_id'],
                start_time=datetime.fromisoformat(session_data['start_time']),
                last_activity=datetime.fromisoformat(session_data['last_activity']),
                state=ConversationState(session_data['state']),
                message_count=session_data['message_count'],
                context_summary=session_data.get('context_summary', ''),
                conversation_goal=session_data.get('conversation_goal'),
                metadata=session_data.get('metadata', {}),
                topic_history=topic_history,
                current_topic=topic_history[-1] if topic_history else None
            )
            
            logger.debug("Loaded session %s from Redis", session.session_id)
            return session
            
        except Exception as e:
            logger.warning("Failed to load session from Redis: %s", str(e))
            return None

    async def _try_recover_session(self, user_id: str, channel_id: str) -> ConversationSession | None:
        """Try to recover session from Redis if not in memory"""
        session_key = f"{user_id}:{channel_id}"
        
        # Check if already in memory
        if session_key in self.active_sessions:
            return self.active_sessions[session_key]
        
        # Try to load from Redis
        session = await self._load_session_from_redis(user_id, channel_id)
        
        if session:
            # Check if session is still valid (not too old)
            time_since_activity = datetime.now() - session.last_activity
            if time_since_activity <= self.session_timeout * 2:  # Give some buffer
                # Restore to memory
                self.active_sessions[session_key] = session
                logger.info("Recovered conversation session for user %s from Redis", user_id)
                return session
            else:
                # Session too old, don't restore
                logger.debug("Found old session for user %s, not restoring", user_id)
                
        return None

    async def process_message(
        self,
        user_id: str,
        channel_id: str,
        message_id: str,
        message_content: str,
        timestamp: datetime | None = None,
    ) -> ConversationSession:
        """
        Process a new message and update conversation boundaries

        Args:
            user_id: Discord user ID
            channel_id: Discord channel ID
            message_id: Discord message ID
            message_content: Message content for analysis
            timestamp: Message timestamp (defaults to now)

        Returns:
            Updated conversation session
        """
        timestamp = timestamp or datetime.now()
        session_key = f"{user_id}:{channel_id}"

        # Get or create conversation session (try recovery first)
        session = await self._get_or_create_session(user_id, channel_id, timestamp)

        # Update session activity
        session.update_activity()
        session.message_count += 1

        # Detect topic transitions
        transition_type = await self._detect_topic_transition(session, message_content)

        # Handle topic transitions
        if transition_type != TopicTransitionType.NATURAL_FLOW:
            await self._handle_topic_transition(
                session, message_content, transition_type, timestamp
            )

        # Update current topic
        if session.current_topic:
            session.current_topic.message_count += 1
        else:
            # Start new topic if none exists
            await self._start_new_topic(session, message_content, timestamp)

        # Check if conversation needs summarization
        if session.is_long_conversation(self.summarization_threshold):
            await self._update_conversation_summary(session)

        # Store session updates in memory and Redis
        self.active_sessions[session_key] = session
        await self._save_session_to_redis(session)

        return session

    async def get_conversation_context(
        self, user_id: str, channel_id: str, limit: int = 15, include_summary: bool = True
    ) -> dict[str, Any]:
        """
        Get enhanced conversation context with boundary awareness

        Args:
            user_id: Discord user ID
            channel_id: Discord channel ID
            limit: Maximum recent messages to include
            include_summary: Whether to include conversation summary

        Returns:
            Enhanced conversation context with session boundaries
        """
        session_key = f"{user_id}:{channel_id}"
        session = self.active_sessions.get(session_key)

        context = {
            "session_exists": session is not None,
            "recent_messages_limit": limit,
            "conversation_boundaries": [],
        }

        if not session:
            context["status"] = "new_conversation"
            return context

        # Add session information
        context.update(
            {
                "session_id": session.session_id,
                "session_state": session.state.value,
                "duration_minutes": session.get_duration_minutes(),
                "message_count": session.message_count,
                "is_long_conversation": session.is_long_conversation(),
                "conversation_goal": session.conversation_goal,
            }
        )

        # Add current topic information
        if session.current_topic:
            context["current_topic"] = {
                "topic_id": session.current_topic.topic_id,
                "keywords": session.current_topic.keywords,
                "duration_minutes": session.current_topic.get_duration_minutes(),
                "message_count": session.current_topic.message_count,
                "emotional_tone": session.current_topic.emotional_tone,
            }

        # Add conversation summary for long conversations
        if include_summary and session.context_summary:
            context["conversation_summary"] = session.context_summary

        # Add topic history
        context["topic_history"] = [
            {
                "topic_id": topic.topic_id,
                "keywords": topic.keywords[:5],  # Limit keywords
                "message_count": topic.message_count,
                "duration_minutes": topic.get_duration_minutes(),
                "status": "active" if topic.is_active() else "completed",
            }
            for topic in session.topic_history[-5:]  # Last 5 topics
        ]

        # Add conversation boundaries for context pruning
        boundaries = await self._identify_conversation_boundaries(session, limit)
        context["conversation_boundaries"] = boundaries

        return context

    async def handle_conversation_interruption(
        self, user_id: str, channel_id: str, interrupting_user_id: str
    ) -> None:
        """
        Handle conversation interruption by another user

        Args:
            user_id: Original user ID
            channel_id: Discord channel ID
            interrupting_user_id: User who interrupted the conversation
        """
        session_key = f"{user_id}:{channel_id}"
        session = self.active_sessions.get(session_key)

        if session and session.state == ConversationState.ACTIVE:
            # Mark current topic as interrupted
            if session.current_topic:
                session.current_topic.end_time = datetime.now()
                session.current_topic.resolution_status = "interrupted"

            # Update session state
            session.state = ConversationState.INTERRUPTED
            session.metadata["interrupted_by"] = interrupting_user_id
            session.metadata["interruption_time"] = datetime.now().isoformat()

            logger.debug(
                f"Conversation interrupted for user {user_id} by user {interrupting_user_id}"
            )

    async def resume_conversation(
        self, user_id: str, channel_id: str, resume_message: str
    ) -> str | None:
        """
        Resume an interrupted or paused conversation

        Args:
            user_id: Discord user ID
            channel_id: Discord channel ID
            resume_message: Message indicating resumption

        Returns:
            Context bridge message for smooth resumption
        """
        session_key = f"{user_id}:{channel_id}"
        session = self.active_sessions.get(session_key)

        if not session:
            return None

        if session.state in [ConversationState.PAUSED, ConversationState.INTERRUPTED]:
            # Generate context bridge
            bridge_message = await self._generate_resumption_bridge(session, resume_message)

            # Update session state
            session.state = ConversationState.RESUMED
            session.update_activity()

            # Resume or create new topic
            await self._handle_conversation_resumption(session, resume_message)

            logger.debug(f"Conversation resumed for user {user_id} after {session.state.value}")
            return bridge_message

        return None

    async def end_conversation_session(
        self, user_id: str, channel_id: str, completion_reason: str = "natural_end"
    ) -> str | None:
        """
        End a conversation session gracefully

        Args:
            user_id: Discord user ID
            channel_id: Discord channel ID
            completion_reason: Reason for ending the conversation

        Returns:
            Conversation summary for archival
        """
        session_key = f"{user_id}:{channel_id}"
        session = self.active_sessions.get(session_key)

        if not session:
            return None

        # End current topic
        if session.current_topic:
            session.current_topic.end_time = datetime.now()
            session.current_topic.resolution_status = "completed"

        # Update session state
        session.state = ConversationState.COMPLETED
        session.metadata["completion_reason"] = completion_reason
        session.metadata["end_time"] = datetime.now().isoformat()

        # Generate final summary
        final_summary = await self._generate_conversation_summary(session)
        session.context_summary = final_summary

        # Archive session (remove from active sessions)
        self.active_sessions.pop(session_key, None)

        logger.info(f"Conversation session ended for user {user_id}: {completion_reason}")
        return final_summary

    async def get_multi_user_context(
        self, channel_id: str, active_user_ids: list[str], limit_per_user: int = 10
    ) -> dict[str, Any]:
        """
        Get conversation context for multi-user channels

        Args:
            channel_id: Discord channel ID
            active_user_ids: List of users currently active in channel
            limit_per_user: Message limit per user

        Returns:
            Multi-user conversation context
        """
        context = {
            "channel_id": channel_id,
            "active_users": len(active_user_ids),
            "user_sessions": {},
            "conversation_threads": [],
        }

        # Get session info for each active user
        for user_id in active_user_ids:
            session_key = f"{user_id}:{channel_id}"
            session = self.active_sessions.get(session_key)

            if session:
                context["user_sessions"][user_id] = {
                    "session_state": session.state.value,
                    "current_topic": (
                        session.current_topic.keywords[:3] if session.current_topic else None
                    ),
                    "message_count": session.message_count,
                    "duration_minutes": session.get_duration_minutes(),
                }

        # Identify conversation threads (topics being discussed simultaneously)
        threads = await self._identify_conversation_threads(channel_id, active_user_ids)
        context["conversation_threads"] = threads

        return context

    # Private helper methods

    async def _get_or_create_session(
        self, user_id: str, channel_id: str, timestamp: datetime
    ) -> ConversationSession:
        """Get existing session, try recovery from Redis, or create new one"""
        session_key = f"{user_id}:{channel_id}"

        # Check for existing active session in memory
        if session_key in self.active_sessions:
            session = self.active_sessions[session_key]

            # Check if session has timed out
            if timestamp - session.last_activity > self.session_timeout:
                session.state = ConversationState.PAUSED
                logger.debug(f"Session timed out for user {user_id}, marking as paused")

            return session

        # Try to recover session from Redis
        recovered_session = await self._try_recover_session(user_id, channel_id)
        if recovered_session:
            # Update activity and check for timeout
            if timestamp - recovered_session.last_activity > self.session_timeout:
                recovered_session.state = ConversationState.RESUMED
                logger.info("Recovered session for user %s, marked as RESUMED", user_id)
            else:
                logger.info("Recovered active session for user %s", user_id)
            
            recovered_session.update_activity()
            return recovered_session

        # Create new session
        session_id = hashlib.md5(
            f"{user_id}:{channel_id}:{timestamp.isoformat()}".encode()
        ).hexdigest()[:12]
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            channel_id=channel_id,
            start_time=timestamp,
            last_activity=timestamp,
        )

        # Add to active sessions and save to Redis
        self.active_sessions[session_key] = session
        await self._save_session_to_redis(session)

        logger.debug(f"Created new conversation session {session_id} for user {user_id}")
        return session

    async def _detect_topic_transition(
        self, session: ConversationSession, message_content: str
    ) -> TopicTransitionType:
        """Detect if message indicates a topic transition"""
        message_lower = message_content.lower()

        # Check for explicit transition indicators
        for transition_type, indicators in self.transition_indicators.items():
            for indicator in indicators:
                if indicator in message_lower:
                    # Map transition indicator keys to enum values
                    if transition_type == "explicit_change":
                        return TopicTransitionType.EXPLICIT_CHANGE
                    elif transition_type == "resumption":
                        return TopicTransitionType.RESUMPTION
                    elif transition_type == "completion":
                        return TopicTransitionType.NATURAL_FLOW  # Map completion to natural flow

        # Check for new session indicators (conversation starters)
        if session.message_count == 1:
            return TopicTransitionType.NEW_SESSION

        # TODO: Add semantic similarity analysis for natural topic transitions
        # This would compare current message content with recent topic keywords
        # and determine if the topic has shifted naturally

        return TopicTransitionType.NATURAL_FLOW

    async def _handle_topic_transition(
        self,
        session: ConversationSession,
        message_content: str,
        transition_type: TopicTransitionType,
        timestamp: datetime,
    ) -> None:
        """Handle detected topic transition"""

        # End current topic if exists
        if session.current_topic:
            session.current_topic.end_time = timestamp

            # Set resolution status based on transition type
            if "completion" in transition_type.value.lower():
                session.current_topic.resolution_status = "resolved"
            elif transition_type == TopicTransitionType.INTERRUPTION:
                session.current_topic.resolution_status = "interrupted"
            else:
                session.current_topic.resolution_status = "ended"

        # Start new topic
        await self._start_new_topic(session, message_content, timestamp)

        logger.debug(f"Topic transition handled: {transition_type.value}")

    async def _start_new_topic(
        self, session: ConversationSession, message_content: str, timestamp: datetime
    ) -> None:
        """Start a new conversation topic"""
        topic_id = hashlib.md5(
            f"{session.session_id}:{timestamp.isoformat()}".encode()
        ).hexdigest()[:8]

        # Extract keywords from message (simple word extraction for now)
        keywords = await self._extract_topic_keywords(message_content)

        new_topic = ConversationTopic(
            topic_id=topic_id, keywords=keywords, start_time=timestamp, message_count=1
        )

        session.current_topic = new_topic
        session.topic_history.append(new_topic)

        logger.debug(f"Started new topic {topic_id} with keywords: {keywords[:3]}")

    async def _extract_topic_keywords(self, message_content: str) -> list[str]:
        """Extract topic keywords from message content"""
        # Simple keyword extraction (can be enhanced with NLP)
        words = message_content.lower().split()

        # Filter out common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "its",
            "our",
            "their",
        }

        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return keywords[:10]  # Return top 10 keywords

    async def _update_conversation_summary(self, session: ConversationSession) -> None:
        """Update conversation summary using LLM-based intelligent summarization"""
        if not session.topic_history:
            return

        # Use LLM-based summarization if available, otherwise fall back to keyword-based
        if self.llm_client:
            session.context_summary = await self._generate_llm_conversation_summary(session)
        else:
            # Fallback to basic keyword summarization
            topics_summary = []
            for topic in session.topic_history:
                if topic.message_count >= 3:  # Only include substantial topics
                    topic_summary = (
                        f"Discussed {', '.join(topic.keywords[:3])} ({topic.message_count} messages)"
                    )
                    if topic.resolution_status:
                        topic_summary += f" - {topic.resolution_status}"
                    topics_summary.append(topic_summary)

            session.context_summary = (
                f"Conversation spanning {session.get_duration_minutes():.1f} minutes with {session.message_count} messages. Topics: "
                + "; ".join(topics_summary)
            )

        logger.debug("Updated conversation summary for session %s", session.session_id)

    async def _generate_llm_conversation_summary(self, session: ConversationSession) -> str:
        """Generate intelligent conversation summary using LLM"""
        try:
            # Extract conversation content from topic history
            conversation_content = []
            for topic in session.topic_history[-3:]:  # Last 3 topics
                topic_desc = f"Discussed: {', '.join(topic.keywords[:5])}"
                if topic.message_count > 1:
                    topic_desc += f" ({topic.message_count} messages)"
                if topic.resolution_status:
                    topic_desc += f" - {topic.resolution_status}"
                conversation_content.append(topic_desc)
            
            if not conversation_content:
                return f"Brief conversation with {session.message_count} messages over {session.get_duration_minutes():.1f} minutes"
            
            content_text = "; ".join(conversation_content)
            
            # Create summarization prompt
            duration = session.get_duration_minutes()
            summary_prompt = f"""Create a concise 2-3 sentence summary of this conversation focusing on the main topics and outcomes.

Duration: {duration:.1f} minutes
Messages: {session.message_count}
Topics discussed: {content_text}

Summary:"""

            # Generate summary using LLM (use async safe method)
            try:
                response = await self.llm_client.generate_chat_completion_safe([
                    {"role": "user", "content": summary_prompt}
                ], max_tokens=80, temperature=0.3)  # Low temperature for consistent summaries
            except Exception as llm_error:
                logger.warning("LLM client error: %s, falling back to basic summary", str(llm_error))
                return f"Conversation spanning {session.get_duration_minutes():.1f} minutes with {session.message_count} messages"
            
            # Extract content from response
            if isinstance(response, dict) and "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0].get("message", {}).get("content", "")
                summary = content.strip()
            else:
                # Fallback if response format is unexpected
                summary = str(response).strip()
            
            # Add basic stats prefix for context
            return f"[{duration:.1f}min, {session.message_count} msgs] {summary}"
            
        except Exception as e:
            logger.warning("LLM summarization failed: %s, falling back to basic summary", str(e))
            # Fallback to basic summary
            return f"Conversation spanning {session.get_duration_minutes():.1f} minutes with {session.message_count} messages"

    async def _identify_conversation_boundaries(
        self, session: ConversationSession, limit: int
    ) -> list[dict[str, Any]]:
        """Identify conversation boundaries for context pruning"""
        boundaries = []

        # Add topic boundaries
        for topic in session.topic_history[-3:]:  # Last 3 topics
            boundary = {
                "type": "topic_boundary",
                "topic_id": topic.topic_id,
                "keywords": topic.keywords[:3],
                "start_time": topic.start_time.isoformat(),
                "message_count": topic.message_count,
                "importance": min(topic.message_count / 10, 1.0),  # Normalize importance
            }
            boundaries.append(boundary)

        # Add session boundaries
        if session.is_long_conversation():
            boundaries.append(
                {
                    "type": "session_boundary",
                    "session_id": session.session_id,
                    "start_time": session.start_time.isoformat(),
                    "total_messages": session.message_count,
                    "importance": 1.0,  # Session boundaries are always important
                }
            )

        return boundaries

    async def _generate_resumption_bridge(
        self, session: ConversationSession, resume_message: str
    ) -> str:
        """Generate context bridge message for conversation resumption"""
        if not session.current_topic or not session.topic_history:
            return "Welcome back! How can I help you today?"

        last_topic = session.topic_history[-1] if session.topic_history else session.current_topic
        topic_keywords = ", ".join(last_topic.keywords[:3])

        # Calculate time gap
        time_gap = datetime.now() - session.last_activity
        gap_minutes = time_gap.total_seconds() / 60

        if gap_minutes < 60:
            time_phrase = f"{gap_minutes:.0f} minutes ago"
        elif gap_minutes < 1440:  # Less than 24 hours
            time_phrase = f"{gap_minutes/60:.1f} hours ago"
        else:
            time_phrase = f"{gap_minutes/1440:.1f} days ago"

        bridge = f"Welcome back! We were discussing {topic_keywords} about {time_phrase}."

        if session.conversation_goal:
            bridge += f" We were working on: {session.conversation_goal}."

        bridge += " Please continue with your question or let me know if you'd like to discuss something else."

        return bridge

    async def _handle_conversation_resumption(
        self, session: ConversationSession, resume_message: str
    ) -> None:
        """Handle conversation resumption logic"""
        # Check if resuming previous topic or starting new one
        if session.current_topic and any(
            keyword in resume_message.lower() for keyword in session.current_topic.keywords
        ):
            # Resuming previous topic
            session.current_topic.end_time = None  # Reactivate topic
            session.current_topic.resolution_status = "resumed"
        else:
            # Starting new topic after resumption
            await self._start_new_topic(session, resume_message, datetime.now())

    async def _generate_conversation_summary(self, session: ConversationSession) -> str:
        """Generate final conversation summary"""
        duration = session.get_duration_minutes()

        summary = f"Conversation completed after {duration:.1f} minutes with {session.message_count} messages. "

        if session.topic_history:
            completed_topics = [
                topic
                for topic in session.topic_history
                if topic.resolution_status in ["resolved", "completed"]
            ]

            if completed_topics:
                summary += f"Successfully resolved {len(completed_topics)} topic(s): "
                topic_summaries = [f"{', '.join(topic.keywords[:2])}" for topic in completed_topics]
                summary += "; ".join(topic_summaries) + ". "

        if session.conversation_goal:
            summary += f"Conversation goal: {session.conversation_goal}. "

        return summary

    async def _identify_conversation_threads(
        self, channel_id: str, user_ids: list[str]
    ) -> list[dict[str, Any]]:
        """Identify active conversation threads in multi-user channel"""
        threads = []

        for user_id in user_ids:
            session_key = f"{user_id}:{channel_id}"
            session = self.active_sessions.get(session_key)

            if session and session.current_topic:
                thread = {
                    "user_id": user_id,
                    "topic_keywords": session.current_topic.keywords[:3],
                    "message_count": session.current_topic.message_count,
                    "duration_minutes": session.current_topic.get_duration_minutes(),
                    "state": session.state.value,
                }
                threads.append(thread)

        return threads

    def get_active_session_count(self) -> int:
        """Get number of active conversation sessions"""
        return len(
            [s for s in self.active_sessions.values() if s.state == ConversationState.ACTIVE]
        )

    def get_session_statistics(self) -> dict[str, Any]:
        """Get conversation session statistics"""
        sessions = list(self.active_sessions.values())

        if not sessions:
            return {"total_sessions": 0}

        states = [s.state.value for s in sessions]
        durations = [s.get_duration_minutes() for s in sessions]
        message_counts = [s.message_count for s in sessions]

        return {
            "total_sessions": len(sessions),
            "active_sessions": len([s for s in sessions if s.state == ConversationState.ACTIVE]),
            "average_duration_minutes": sum(durations) / len(durations),
            "average_message_count": sum(message_counts) / len(message_counts),
            "session_states": {state: states.count(state) for state in set(states)},
            "long_conversations": len([s for s in sessions if s.is_long_conversation()]),
        }
