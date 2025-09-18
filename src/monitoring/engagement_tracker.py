"""
User Engagement Metrics System

Tracks and analyzes user engagement patterns, conversation quality,
and platform usage for operational insights and optimization.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """Types of user interactions to track."""
    MESSAGE = "message"
    COMMAND = "command"
    REACTION = "reaction"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    ERROR_ENCOUNTERED = "error_encountered"
    FEATURE_USED = "feature_used"


class UserExperienceLevel(Enum):
    """User experience levels for segmentation."""
    NEW = "new"  # < 7 days
    REGULAR = "regular"  # 7-30 days
    EXPERIENCED = "experienced"  # > 30 days


@dataclass
class UserSession:
    """Individual user session data."""
    user_id: str
    platform: str  # 'discord' or 'desktop'
    start_time: datetime
    end_time: Optional[datetime] = None
    message_count: int = 0
    command_count: int = 0
    error_count: int = 0
    features_used: List[str] = field(default_factory=list)
    avg_response_time: Optional[float] = None
    satisfaction_score: Optional[float] = None  # 0-10 scale
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get session duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def interactions_per_minute(self) -> Optional[float]:
        """Calculate interactions per minute."""
        if self.duration:
            total_interactions = self.message_count + self.command_count
            minutes = self.duration.total_seconds() / 60
            return total_interactions / minutes if minutes > 0 else 0
        return None


@dataclass
class ConversationMetrics:
    """Metrics for conversation quality and engagement."""
    conversation_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    message_count: int = 0
    avg_message_length: float = 0.0
    response_times: List[float] = field(default_factory=list)
    topics_discussed: List[str] = field(default_factory=list)
    sentiment_scores: List[float] = field(default_factory=list)
    ai_accuracy_rating: Optional[float] = None  # User feedback
    memory_recalls: int = 0  # How many times memory was recalled
    personality_adaptations: int = 0  # How many times personality adapted
    
    @property
    def avg_response_time(self) -> Optional[float]:
        """Average response time in seconds."""
        return statistics.mean(self.response_times) if self.response_times else None
    
    @property
    def avg_sentiment(self) -> Optional[float]:
        """Average sentiment score."""
        return statistics.mean(self.sentiment_scores) if self.sentiment_scores else None


@dataclass
class PlatformMetrics:
    """Platform-specific usage metrics."""
    platform: str
    active_users_today: int = 0
    active_users_week: int = 0
    active_users_month: int = 0
    total_sessions: int = 0
    avg_session_duration: Optional[float] = None
    total_messages: int = 0
    total_commands: int = 0
    error_rate: float = 0.0
    most_used_features: List[Tuple[str, int]] = field(default_factory=list)
    peak_usage_hours: List[int] = field(default_factory=list)


@dataclass
class EngagementSummary:
    """Overall engagement summary."""
    timestamp: datetime
    total_active_users: int
    new_users: int
    returning_users: int
    avg_session_duration: float
    total_conversations: int
    avg_conversation_length: float
    overall_satisfaction: Optional[float] = None
    platform_breakdown: Dict[str, PlatformMetrics] = field(default_factory=dict)
    top_features: List[Tuple[str, int]] = field(default_factory=list)
    user_retention_rate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_active_users': self.total_active_users,
            'new_users': self.new_users,
            'returning_users': self.returning_users,
            'avg_session_duration': self.avg_session_duration,
            'total_conversations': self.total_conversations,
            'avg_conversation_length': self.avg_conversation_length,
            'overall_satisfaction': self.overall_satisfaction,
            'user_retention_rate': self.user_retention_rate,
            'top_features': self.top_features,
            'platform_breakdown': {
                platform: {
                    'active_users_today': metrics.active_users_today,
                    'active_users_week': metrics.active_users_week,
                    'active_users_month': metrics.active_users_month,
                    'total_sessions': metrics.total_sessions,
                    'avg_session_duration': metrics.avg_session_duration,
                    'total_messages': metrics.total_messages,
                    'total_commands': metrics.total_commands,
                    'error_rate': metrics.error_rate,
                    'most_used_features': metrics.most_used_features,
                    'peak_usage_hours': metrics.peak_usage_hours
                }
                for platform, metrics in self.platform_breakdown.items()
            }
        }


class EngagementTracker:
    """Comprehensive user engagement tracking system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.data_dir = Path(self.config.get('data_dir', 'data/engagement'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory tracking
        self.active_sessions: Dict[str, UserSession] = {}
        self.conversation_metrics: Dict[str, ConversationMetrics] = {}
        self.daily_metrics: List[EngagementSummary] = []
        
        # User data
        self.user_first_seen: Dict[str, datetime] = {}
        self.user_last_seen: Dict[str, datetime] = {}
        self.user_total_sessions: Dict[str, int] = {}
        
        # Configuration
        self.session_timeout = timedelta(minutes=self.config.get('session_timeout_minutes', 30))
        self.max_history_days = self.config.get('max_history_days', 90)
        
        # Load existing data
        self._load_persisted_data()
        
        logger.info("Engagement tracker initialized")
    
    def _load_persisted_data(self):
        """Load persisted engagement data."""
        try:
            # Load user data
            user_data_file = self.data_dir / 'user_data.json'
            if user_data_file.exists():
                with open(user_data_file, 'r') as f:
                    data = json.load(f)
                    
                self.user_first_seen = {
                    uid: datetime.fromisoformat(timestamp)
                    for uid, timestamp in data.get('first_seen', {}).items()
                }
                self.user_last_seen = {
                    uid: datetime.fromisoformat(timestamp)
                    for uid, timestamp in data.get('last_seen', {}).items()
                }
                self.user_total_sessions = data.get('total_sessions', {})
                
            logger.info(f"Loaded data for {len(self.user_first_seen)} users")
            
        except Exception as e:
            logger.error(f"Error loading persisted engagement data: {e}")
    
    def _save_persisted_data(self):
        """Save engagement data to disk."""
        try:
            user_data = {
                'first_seen': {
                    uid: timestamp.isoformat()
                    for uid, timestamp in self.user_first_seen.items()
                },
                'last_seen': {
                    uid: timestamp.isoformat()
                    for uid, timestamp in self.user_last_seen.items()
                },
                'total_sessions': self.user_total_sessions
            }
            
            user_data_file = self.data_dir / 'user_data.json'
            with open(user_data_file, 'w') as f:
                json.dump(user_data, f, indent=2)
                
            logger.debug("Engagement data saved to disk")
            
        except Exception as e:
            logger.error(f"Error saving engagement data: {e}")
    
    def start_session(self, user_id: str, platform: str = 'discord') -> str:
        """Start a new user session."""
        now = datetime.now(timezone.utc)
        
        # End any existing session for this user
        if user_id in self.active_sessions:
            self.end_session(user_id)
        
        # Create new session
        session = UserSession(
            user_id=user_id,
            platform=platform,
            start_time=now
        )
        
        self.active_sessions[user_id] = session
        
        # Update user tracking
        if user_id not in self.user_first_seen:
            self.user_first_seen[user_id] = now
        
        self.user_last_seen[user_id] = now
        self.user_total_sessions[user_id] = self.user_total_sessions.get(user_id, 0) + 1
        
        logger.debug(f"Started session for user {user_id} on {platform}")
        return f"{user_id}_{now.timestamp()}"
    
    def end_session(self, user_id: str):
        """End a user session."""
        if user_id not in self.active_sessions:
            return
        
        session = self.active_sessions[user_id]
        session.end_time = datetime.now(timezone.utc)
        
        # Archive session data
        self._archive_session(session)
        
        # Remove from active sessions
        del self.active_sessions[user_id]
        
        logger.debug(f"Ended session for user {user_id}")
    
    def track_interaction(self, user_id: str, interaction_type: InteractionType, 
                         metadata: Optional[Dict[str, Any]] = None):
        """Track a user interaction."""
        # Ensure user has active session
        if user_id not in self.active_sessions:
            self.start_session(user_id)
        
        session = self.active_sessions[user_id]
        metadata = metadata or {}
        
        # Update session based on interaction type
        if interaction_type == InteractionType.MESSAGE:
            session.message_count += 1
        elif interaction_type == InteractionType.COMMAND:
            session.command_count += 1
            command_name = metadata.get('command_name')
            if command_name and command_name not in session.features_used:
                session.features_used.append(command_name)
        elif interaction_type == InteractionType.ERROR_ENCOUNTERED:
            session.error_count += 1
        elif interaction_type == InteractionType.FEATURE_USED:
            feature_name = metadata.get('feature_name')
            if feature_name and feature_name not in session.features_used:
                session.features_used.append(feature_name)
        
        # Track response time if provided
        response_time = metadata.get('response_time')
        if response_time is not None:
            if session.avg_response_time is None:
                session.avg_response_time = response_time
            else:
                # Rolling average
                session.avg_response_time = (session.avg_response_time + response_time) / 2
        
        # Update last seen
        self.user_last_seen[user_id] = datetime.now(timezone.utc)
        
        logger.debug(f"Tracked {interaction_type.value} for user {user_id}")
    
    def start_conversation(self, conversation_id: str, user_id: str) -> ConversationMetrics:
        """Start tracking a conversation."""
        metrics = ConversationMetrics(
            conversation_id=conversation_id,
            user_id=user_id,
            start_time=datetime.now(timezone.utc)
        )
        
        self.conversation_metrics[conversation_id] = metrics
        return metrics
    
    def track_conversation_event(self, conversation_id: str, event_type: str, 
                               data: Optional[Dict[str, Any]] = None):
        """Track an event within a conversation."""
        if conversation_id not in self.conversation_metrics:
            return
        
        metrics = self.conversation_metrics[conversation_id]
        data = data or {}
        
        if event_type == 'message':
            metrics.message_count += 1
            message_length = data.get('message_length', 0)
            if message_length > 0:
                if metrics.avg_message_length == 0:
                    metrics.avg_message_length = message_length
                else:
                    # Rolling average
                    total_length = metrics.avg_message_length * (metrics.message_count - 1) + message_length
                    metrics.avg_message_length = total_length / metrics.message_count
        
        elif event_type == 'response_time':
            response_time = data.get('response_time')
            if response_time is not None:
                metrics.response_times.append(response_time)
        
        elif event_type == 'sentiment':
            sentiment = data.get('sentiment_score')
            if sentiment is not None:
                metrics.sentiment_scores.append(sentiment)
        
        elif event_type == 'topic':
            topic = data.get('topic')
            if topic and topic not in metrics.topics_discussed:
                metrics.topics_discussed.append(topic)
        
        elif event_type == 'memory_recall':
            metrics.memory_recalls += 1
        
        elif event_type == 'personality_adaptation':
            metrics.personality_adaptations += 1
        
        elif event_type == 'user_rating':
            metrics.ai_accuracy_rating = data.get('rating')
    
    def end_conversation(self, conversation_id: str):
        """End a conversation and finalize metrics."""
        if conversation_id not in self.conversation_metrics:
            return
        
        metrics = self.conversation_metrics[conversation_id]
        metrics.end_time = datetime.now(timezone.utc)
        
        # Archive conversation metrics
        self._archive_conversation(metrics)
        
        logger.debug(f"Ended conversation {conversation_id}")
    
    def _archive_session(self, session: UserSession):
        """Archive a completed session."""
        # For now, just log the session data
        # In a full implementation, this would save to database
        logger.info(f"Session archived: {session.user_id} - "
                   f"Duration: {session.duration}, "
                   f"Messages: {session.message_count}, "
                   f"Commands: {session.command_count}")
    
    def _archive_conversation(self, metrics: ConversationMetrics):
        """Archive conversation metrics."""
        # For now, just log the conversation data
        # In a full implementation, this would save to database
        logger.info(f"Conversation archived: {metrics.conversation_id} - "
                   f"Messages: {metrics.message_count}, "
                   f"Avg Response Time: {metrics.avg_response_time}")
    
    def get_user_experience_level(self, user_id: str) -> UserExperienceLevel:
        """Determine user experience level based on history."""
        if user_id not in self.user_first_seen:
            return UserExperienceLevel.NEW
        
        days_since_first = (datetime.now(timezone.utc) - self.user_first_seen[user_id]).days
        
        if days_since_first < 7:
            return UserExperienceLevel.NEW
        elif days_since_first < 30:
            return UserExperienceLevel.REGULAR
        else:
            return UserExperienceLevel.EXPERIENCED
    
    def get_active_users(self, hours: int = 24) -> List[str]:
        """Get list of users active in the last N hours."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        active_users = []
        for user_id, last_seen in self.user_last_seen.items():
            if last_seen >= cutoff_time:
                active_users.append(user_id)
        
        return active_users
    
    def generate_engagement_summary(self) -> EngagementSummary:
        """Generate comprehensive engagement summary."""
        now = datetime.now(timezone.utc)
        
        # Get active users for different time periods
        active_24h = self.get_active_users(24)
        active_7d = self.get_active_users(24 * 7)
        active_30d = self.get_active_users(24 * 30)
        
        # Calculate new vs returning users
        new_users = [uid for uid in active_24h 
                    if self.get_user_experience_level(uid) == UserExperienceLevel.NEW]
        returning_users = [uid for uid in active_24h 
                          if self.get_user_experience_level(uid) != UserExperienceLevel.NEW]
        
        # Calculate average session duration
        active_session_durations = []
        for session in self.active_sessions.values():
            if session.start_time >= now - timedelta(hours=24):
                duration = (now - session.start_time).total_seconds()
                active_session_durations.append(duration)
        
        avg_session_duration = (statistics.mean(active_session_durations) 
                               if active_session_durations else 0.0)
        
        # Calculate conversation metrics
        recent_conversations = [
            conv for conv in self.conversation_metrics.values()
            if conv.start_time >= now - timedelta(hours=24)
        ]
        
        avg_conversation_length = (
            statistics.mean([conv.message_count for conv in recent_conversations])
            if recent_conversations else 0.0
        )
        
        # Platform breakdown
        platform_breakdown = {}
        discord_users = [uid for uid in active_24h 
                        if self.active_sessions.get(uid, UserSession('', 'discord', now)).platform == 'discord']
        desktop_users = [uid for uid in active_24h 
                        if self.active_sessions.get(uid, UserSession('', 'desktop', now)).platform == 'desktop']
        
        if discord_users:
            platform_breakdown['discord'] = PlatformMetrics(
                platform='discord',
                active_users_today=len([uid for uid in discord_users if uid in active_24h]),
                active_users_week=len([uid for uid in discord_users if uid in active_7d]),
                active_users_month=len([uid for uid in discord_users if uid in active_30d])
            )
        
        if desktop_users:
            platform_breakdown['desktop'] = PlatformMetrics(
                platform='desktop',
                active_users_today=len([uid for uid in desktop_users if uid in active_24h]),
                active_users_week=len([uid for uid in desktop_users if uid in active_7d]),
                active_users_month=len([uid for uid in desktop_users if uid in active_30d])
            )
        
        # Create summary
        summary = EngagementSummary(
            timestamp=now,
            total_active_users=len(active_24h),
            new_users=len(new_users),
            returning_users=len(returning_users),
            avg_session_duration=avg_session_duration,
            total_conversations=len(recent_conversations),
            avg_conversation_length=avg_conversation_length,
            platform_breakdown=platform_breakdown
        )
        
        # Store in daily metrics
        self.daily_metrics.append(summary)
        
        # Clean old metrics
        cutoff_date = now - timedelta(days=self.max_history_days)
        self.daily_metrics = [m for m in self.daily_metrics if m.timestamp >= cutoff_date]
        
        # Save data
        self._save_persisted_data()
        
        # Only log when there are active users or when in debug mode
        if len(active_24h) > 0:
            logger.info(f"Generated engagement summary: {len(active_24h)} active users")
        else:
            # Downgrade to debug level for zero activity to reduce log noise
            logger.debug(f"Generated engagement summary: 0 active users")
            
        return summary
    
    def export_engagement_report(self, days: int = 7) -> Dict[str, Any]:
        """Export detailed engagement report."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        recent_summaries = [s for s in self.daily_metrics if s.timestamp >= cutoff_date]
        
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'report_period_days': days,
            'total_registered_users': len(self.user_first_seen),
            'active_sessions': len(self.active_sessions),
            'daily_summaries': [summary.to_dict() for summary in recent_summaries],
            'user_distribution': {
                'new': len([uid for uid in self.user_first_seen.keys() 
                           if self.get_user_experience_level(uid) == UserExperienceLevel.NEW]),
                'regular': len([uid for uid in self.user_first_seen.keys() 
                               if self.get_user_experience_level(uid) == UserExperienceLevel.REGULAR]),
                'experienced': len([uid for uid in self.user_first_seen.keys() 
                                   if self.get_user_experience_level(uid) == UserExperienceLevel.EXPERIENCED])
            }
        }
        
        return report
    
    def cleanup_old_sessions(self):
        """Clean up inactive sessions."""
        now = datetime.now(timezone.utc)
        inactive_users = []
        
        for user_id, session in self.active_sessions.items():
            if now - session.start_time > self.session_timeout:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            self.end_session(user_id)
        
        if inactive_users:
            logger.info(f"Cleaned up {len(inactive_users)} inactive sessions")


# Global engagement tracker instance
_engagement_tracker: Optional[EngagementTracker] = None


def get_engagement_tracker(config: Optional[Dict[str, Any]] = None) -> EngagementTracker:
    """Get the global engagement tracker instance."""
    global _engagement_tracker
    if _engagement_tracker is None:
        _engagement_tracker = EngagementTracker(config)
    return _engagement_tracker