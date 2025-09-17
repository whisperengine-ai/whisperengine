"""
Comprehensive Error Tracking System

Provides detailed error tracking, analysis, and reporting capabilities
for debugging and operational monitoring.
"""

import json
import logging
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import hashlib
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # System-breaking errors
    HIGH = "high"         # Major functionality impacted
    MEDIUM = "medium"     # Minor functionality impacted
    LOW = "low"          # Cosmetic or edge case issues
    INFO = "info"        # Informational, not actually errors


class ErrorCategory(Enum):
    """Categories of errors for classification."""
    LLM_SERVICE = "llm_service"
    DATABASE = "database"
    MEMORY_SYSTEM = "memory_system"
    DISCORD_API = "discord_api"
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    USER_INPUT = "user_input"
    SYSTEM_RESOURCE = "system_resource"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for an error."""
    user_id: Optional[str] = None
    channel_id: Optional[str] = None
    guild_id: Optional[str] = None
    command: Optional[str] = None
    platform: str = "unknown"
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    active_connections: Optional[int] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorEvent:
    """Individual error event record."""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    stack_trace: str
    context: ErrorContext
    resolved: bool = False
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    first_occurrence: Optional[datetime] = None
    occurrence_count: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'error_id': self.error_id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value,
            'category': self.category.value,
            'message': self.message,
            'exception_type': self.exception_type,
            'stack_trace': self.stack_trace,
            'resolved': self.resolved,
            'resolution_notes': self.resolution_notes,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'first_occurrence': self.first_occurrence.isoformat() if self.first_occurrence else None,
            'occurrence_count': self.occurrence_count,
            'context': {
                'user_id': self.context.user_id,
                'channel_id': self.context.channel_id,
                'guild_id': self.context.guild_id,
                'command': self.context.command,
                'platform': self.context.platform,
                'session_id': self.context.session_id,
                'request_id': self.context.request_id,
                'memory_usage': self.context.memory_usage,
                'cpu_usage': self.context.cpu_usage,
                'active_connections': self.context.active_connections,
                'additional_data': self.context.additional_data
            }
        }


@dataclass
class ErrorPattern:
    """Identified error pattern for analysis."""
    pattern_id: str
    error_signature: str
    category: ErrorCategory
    severity: ErrorSeverity
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    affected_users: List[str]
    error_rate: float  # errors per hour
    resolution_status: str  # 'open', 'investigating', 'resolved'
    common_contexts: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'pattern_id': self.pattern_id,
            'error_signature': self.error_signature,
            'category': self.category.value,
            'severity': self.severity.value,
            'occurrence_count': self.occurrence_count,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'affected_users': self.affected_users,
            'error_rate': self.error_rate,
            'resolution_status': self.resolution_status,
            'common_contexts': self.common_contexts
        }


class ErrorTracker:
    """Comprehensive error tracking and analysis system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.data_dir = Path(self.config.get('data_dir', 'data/errors'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Error storage
        self.error_events: Dict[str, ErrorEvent] = {}
        self.error_patterns: Dict[str, ErrorPattern] = {}
        
        # Error rate tracking
        self.error_counts_by_hour: Dict[str, int] = defaultdict(int)
        self.error_counts_by_category: Dict[ErrorCategory, int] = defaultdict(int)
        self.error_counts_by_severity: Dict[ErrorSeverity, int] = defaultdict(int)
        
        # Configuration
        self.max_stack_trace_length = self.config.get('max_stack_trace_length', 2000)
        self.pattern_detection_threshold = self.config.get('pattern_detection_threshold', 5)
        self.max_history_days = self.config.get('max_history_days', 30)
        
        # Auto-categorization rules
        self._categorization_rules = self._init_categorization_rules()
        
        # Load existing data
        self._load_persisted_data()
        
        logger.info("Error tracker initialized")
    
    def _init_categorization_rules(self) -> Dict[str, ErrorCategory]:
        """Initialize automatic error categorization rules."""
        return {
            # LLM Service errors
            'llm': ErrorCategory.LLM_SERVICE,
            'openai': ErrorCategory.LLM_SERVICE,
            'model': ErrorCategory.LLM_SERVICE,
            'api_key': ErrorCategory.LLM_SERVICE,
            'rate_limit': ErrorCategory.LLM_SERVICE,
            'timeout': ErrorCategory.LLM_SERVICE,
            
            # Database errors
            'database': ErrorCategory.DATABASE,
            'sqlite': ErrorCategory.DATABASE,
            'postgresql': ErrorCategory.DATABASE,
            'connection': ErrorCategory.DATABASE,
            'query': ErrorCategory.DATABASE,
            'transaction': ErrorCategory.DATABASE,
            
            # Memory system errors
            'memory_system': ErrorCategory.MEMORY_SYSTEM,
            'chroma': ErrorCategory.MEMORY_SYSTEM,
            'embedding': ErrorCategory.MEMORY_SYSTEM,
            'vector': ErrorCategory.MEMORY_SYSTEM,
            
            # Discord API errors
            'discord': ErrorCategory.DISCORD_API,
            'bot': ErrorCategory.DISCORD_API,
            'webhook': ErrorCategory.DISCORD_API,
            'discord_permission': ErrorCategory.DISCORD_API,
            
            # Network errors
            'network': ErrorCategory.NETWORK,
            'http': ErrorCategory.NETWORK,
            'ssl': ErrorCategory.NETWORK,
            'certificate': ErrorCategory.NETWORK,
            'dns': ErrorCategory.NETWORK,
            
            # File system errors
            'file': ErrorCategory.FILE_SYSTEM,
            'path': ErrorCategory.FILE_SYSTEM,
            'file_permission': ErrorCategory.FILE_SYSTEM,
            'disk': ErrorCategory.FILE_SYSTEM,
            
            # Configuration errors
            'config': ErrorCategory.CONFIGURATION,
            'environment': ErrorCategory.CONFIGURATION,
            'settings': ErrorCategory.CONFIGURATION,
            '.env': ErrorCategory.CONFIGURATION,
            
            # Authentication errors
            'auth': ErrorCategory.AUTHENTICATION,
            'token': ErrorCategory.AUTHENTICATION,
            'login': ErrorCategory.AUTHENTICATION,
            'credential': ErrorCategory.AUTHENTICATION,
            
            # User input errors
            'validation': ErrorCategory.USER_INPUT,
            'input': ErrorCategory.USER_INPUT,
            'parameter': ErrorCategory.USER_INPUT,
            
            # System resource errors
            'memory_usage': ErrorCategory.SYSTEM_RESOURCE,
            'cpu': ErrorCategory.SYSTEM_RESOURCE,
            'resource': ErrorCategory.SYSTEM_RESOURCE,
        }
    
    def _load_persisted_data(self):
        """Load persisted error data."""
        try:
            # Load error events
            events_file = self.data_dir / 'error_events.json'
            if events_file.exists():
                with open(events_file, 'r', encoding='utf-8') as f:
                    events_data = json.load(f)
                
                for event_data in events_data:
                    event = self._dict_to_error_event(event_data)
                    self.error_events[event.error_id] = event
            
            # Load error patterns
            patterns_file = self.data_dir / 'error_patterns.json'
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                
                for pattern_data in patterns_data:
                    pattern = self._dict_to_error_pattern(pattern_data)
                    self.error_patterns[pattern.pattern_id] = pattern
            
            logger.info("Loaded %d error events and %d patterns", len(self.error_events), len(self.error_patterns))
            
        except (IOError, json.JSONDecodeError, KeyError) as e:
            logger.error("Error loading persisted error data: %s", e)
    
    def _save_persisted_data(self):
        """Save error data to disk."""
        try:
            # Save error events (last 30 days only)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.max_history_days)
            recent_events = [
                event.to_dict() for event in self.error_events.values()
                if event.timestamp >= cutoff_date
            ]
            
            events_file = self.data_dir / 'error_events.json'
            with open(events_file, 'w', encoding='utf-8') as f:
                json.dump(recent_events, f, indent=2)
            
            # Save error patterns
            patterns_data = [pattern.to_dict() for pattern in self.error_patterns.values()]
            patterns_file = self.data_dir / 'error_patterns.json'
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2)
            
            logger.debug("Error data saved to disk")
            
        except (IOError, OSError) as e:
            logger.error("Error saving error data: %s", e)
    
    def _dict_to_error_event(self, data: Dict[str, Any]) -> ErrorEvent:
        """Convert dictionary to ErrorEvent object."""
        context = ErrorContext(
            user_id=data['context'].get('user_id'),
            channel_id=data['context'].get('channel_id'),
            guild_id=data['context'].get('guild_id'),
            command=data['context'].get('command'),
            platform=data['context'].get('platform', 'unknown'),
            session_id=data['context'].get('session_id'),
            request_id=data['context'].get('request_id'),
            memory_usage=data['context'].get('memory_usage'),
            cpu_usage=data['context'].get('cpu_usage'),
            active_connections=data['context'].get('active_connections'),
            additional_data=data['context'].get('additional_data', {})
        )
        
        return ErrorEvent(
            error_id=data['error_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            severity=ErrorSeverity(data['severity']),
            category=ErrorCategory(data['category']),
            message=data['message'],
            exception_type=data['exception_type'],
            stack_trace=data['stack_trace'],
            context=context,
            resolved=data.get('resolved', False),
            resolution_notes=data.get('resolution_notes'),
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None,
            first_occurrence=datetime.fromisoformat(data['first_occurrence']) if data.get('first_occurrence') else None,
            occurrence_count=data.get('occurrence_count', 1)
        )
    
    def _dict_to_error_pattern(self, data: Dict[str, Any]) -> ErrorPattern:
        """Convert dictionary to ErrorPattern object."""
        return ErrorPattern(
            pattern_id=data['pattern_id'],
            error_signature=data['error_signature'],
            category=ErrorCategory(data['category']),
            severity=ErrorSeverity(data['severity']),
            occurrence_count=data['occurrence_count'],
            first_seen=datetime.fromisoformat(data['first_seen']),
            last_seen=datetime.fromisoformat(data['last_seen']),
            affected_users=data['affected_users'],
            error_rate=data['error_rate'],
            resolution_status=data['resolution_status'],
            common_contexts=data['common_contexts']
        )
    
    def track_error(self, exception: Exception, context: Optional[ErrorContext] = None,
                   severity: Optional[ErrorSeverity] = None,
                   category: Optional[ErrorCategory] = None) -> str:
        """Track a new error event."""
        
        # Get exception details
        exc_type = type(exception).__name__
        exc_message = str(exception)
        stack_trace = traceback.format_exc()
        
        # Truncate stack trace if too long
        if len(stack_trace) > self.max_stack_trace_length:
            stack_trace = stack_trace[:self.max_stack_trace_length] + "\n... (truncated)"
        
        # Auto-categorize if not provided
        if category is None:
            category = self._auto_categorize_error(exc_message, stack_trace)
        
        # Auto-determine severity if not provided
        if severity is None:
            severity = self._auto_determine_severity(exc_type, exc_message, category)
        
        # Generate error signature for pattern detection
        error_signature = self._generate_error_signature(exc_type, exc_message, stack_trace)
        
        # Create error ID
        timestamp = datetime.now(timezone.utc)
        error_id = hashlib.md5(f"{error_signature}_{timestamp.isoformat()}".encode()).hexdigest()[:16]
        
        # Use default context if none provided
        if context is None:
            context = ErrorContext()
        
        # Check if this is a recurring error
        existing_pattern = self._find_matching_pattern(error_signature)
        if existing_pattern:
            existing_pattern.occurrence_count += 1
            existing_pattern.last_seen = timestamp
            if context.user_id and context.user_id not in existing_pattern.affected_users:
                existing_pattern.affected_users.append(context.user_id)
        
        # Create error event
        error_event = ErrorEvent(
            error_id=error_id,
            timestamp=timestamp,
            severity=severity,
            category=category,
            message=exc_message,
            exception_type=exc_type,
            stack_trace=stack_trace,
            context=context,
            first_occurrence=timestamp
        )
        
        # Store error event
        self.error_events[error_id] = error_event
        
        # Update tracking counters
        hour_key = timestamp.strftime('%Y-%m-%d_%H')
        self.error_counts_by_hour[hour_key] += 1
        self.error_counts_by_category[category] += 1
        self.error_counts_by_severity[severity] += 1
        
        # Check for new patterns
        if not existing_pattern:
            self._check_for_new_pattern(error_signature, error_event)
        
        # Save data
        self._save_persisted_data()
        
        logger.error("Tracked error %s: %s - %s", error_id, exc_type, exc_message)
        return error_id
    
    def _auto_categorize_error(self, message: str, stack_trace: str) -> ErrorCategory:
        """Automatically categorize an error based on message and stack trace."""
        text_to_check = (message + " " + stack_trace).lower()
        
        for keyword, category in self._categorization_rules.items():
            if keyword in text_to_check:
                return category
        
        return ErrorCategory.UNKNOWN
    
    def _auto_determine_severity(self, exc_type: str, message: str, 
                                category: ErrorCategory) -> ErrorSeverity:
        """Automatically determine error severity."""
        
        # Critical severity conditions
        critical_types = ['SystemExit', 'KeyboardInterrupt', 'MemoryError', 'SystemError']
        critical_keywords = ['connection lost', 'service unavailable', 'database error', 'authentication failed']
        
        if exc_type in critical_types:
            return ErrorSeverity.CRITICAL
        
        for keyword in critical_keywords:
            if keyword in message.lower():
                return ErrorSeverity.CRITICAL
        
        # High severity conditions
        high_keywords = ['timeout', 'rate limit', 'permission denied', 'invalid token']
        if exc_type in ['ConnectionError', 'TimeoutError'] or any(kw in message.lower() for kw in high_keywords):
            return ErrorSeverity.HIGH
        
        # Category-based severity
        if category in [ErrorCategory.LLM_SERVICE, ErrorCategory.DATABASE, ErrorCategory.DISCORD_API]:
            return ErrorSeverity.HIGH
        elif category in [ErrorCategory.MEMORY_SYSTEM, ErrorCategory.CONFIGURATION]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _generate_error_signature(self, exc_type: str, message: str, stack_trace: str) -> str:
        """Generate a signature for error pattern detection."""
        # Extract the most relevant line from stack trace
        stack_lines = stack_trace.split('\n')
        relevant_lines = [line for line in stack_lines if 'File "' in line and 'whisperengine' in line]
        
        if relevant_lines:
            # Use the last relevant line (closest to the error)
            signature_base = f"{exc_type}:{relevant_lines[-1]}"
        else:
            # Fallback to exception type and first few words of message
            message_words = message.split()[:5]
            signature_base = f"{exc_type}:{' '.join(message_words)}"
        
        return hashlib.md5(signature_base.encode()).hexdigest()[:12]
    
    def _find_matching_pattern(self, error_signature: str) -> Optional[ErrorPattern]:
        """Find an existing pattern matching the error signature."""
        for pattern in self.error_patterns.values():
            if pattern.error_signature == error_signature:
                return pattern
        return None
    
    def _check_for_new_pattern(self, error_signature: str, error_event: ErrorEvent):
        """Check if this error forms a new pattern."""
        # Count recent occurrences of this signature
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        matching_events = [
            event for event in self.error_events.values()
            if (self._generate_error_signature(event.exception_type, event.message, event.stack_trace) == error_signature
                and event.timestamp >= recent_cutoff)
        ]
        
        if len(matching_events) >= self.pattern_detection_threshold:
            # Create new pattern
            pattern_id = f"pattern_{error_signature}"
            affected_users = list(set([event.context.user_id for event in matching_events 
                                     if event.context.user_id]))
            
            pattern = ErrorPattern(
                pattern_id=pattern_id,
                error_signature=error_signature,
                category=error_event.category,
                severity=error_event.severity,
                occurrence_count=len(matching_events),
                first_seen=min(event.timestamp for event in matching_events),
                last_seen=max(event.timestamp for event in matching_events),
                affected_users=affected_users,
                error_rate=len(matching_events) / 24.0,  # per hour
                resolution_status='open',
                common_contexts=self._extract_common_contexts(matching_events)
            )
            
            self.error_patterns[pattern_id] = pattern
            logger.warning("New error pattern detected: %s - %d occurrences", pattern_id, len(matching_events))
    
    def _extract_common_contexts(self, events: List[ErrorEvent]) -> Dict[str, Any]:
        """Extract common context elements from similar errors."""
        platforms = Counter([event.context.platform for event in events])
        commands = Counter([event.context.command for event in events if event.context.command])
        
        return {
            'most_common_platform': platforms.most_common(1)[0] if platforms else None,
            'most_common_command': commands.most_common(1)[0] if commands else None,
            'unique_users_affected': len(set([event.context.user_id for event in events if event.context.user_id]))
        }
    
    def resolve_error_pattern(self, pattern_id: str, resolution_notes: str):
        """Mark an error pattern as resolved."""
        if pattern_id in self.error_patterns:
            pattern = self.error_patterns[pattern_id]
            pattern.resolution_status = 'resolved'
            pattern.common_contexts['resolution_notes'] = resolution_notes
            
            logger.info("Error pattern %s marked as resolved", pattern_id)
            self._save_persisted_data()
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_errors = [error for error in self.error_events.values() if error.timestamp >= cutoff_time]
        
        # Category breakdown
        category_counts = Counter([error.category for error in recent_errors])
        severity_counts = Counter([error.severity for error in recent_errors])
        
        # Error rate calculation
        total_errors = len(recent_errors)
        error_rate = total_errors / hours if hours > 0 else 0
        
        # Most common errors
        error_types = Counter([error.exception_type for error in recent_errors])
        
        # Active patterns
        active_patterns = [pattern for pattern in self.error_patterns.values() 
                          if pattern.resolution_status != 'resolved' and pattern.last_seen >= cutoff_time]
        
        return {
            'time_period_hours': hours,
            'total_errors': total_errors,
            'error_rate_per_hour': error_rate,
            'errors_by_category': {cat.value: count for cat, count in category_counts.items()},
            'errors_by_severity': {sev.value: count for sev, count in severity_counts.items()},
            'most_common_error_types': error_types.most_common(5),
            'active_patterns': len(active_patterns),
            'unresolved_critical_errors': len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL and not e.resolved])
        }
    
    def get_error_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get error trends over the specified number of days."""
        trends = {}
        now = datetime.now(timezone.utc)
        
        for day in range(days):
            day_start = now - timedelta(days=day+1)
            day_end = now - timedelta(days=day)
            
            day_errors = [error for error in self.error_events.values() 
                         if day_start <= error.timestamp < day_end]
            
            day_key = day_start.strftime('%Y-%m-%d')
            trends[day_key] = {
                'total_errors': len(day_errors),
                'critical_errors': len([e for e in day_errors if e.severity == ErrorSeverity.CRITICAL]),
                'high_severity_errors': len([e for e in day_errors if e.severity == ErrorSeverity.HIGH]),
                'unique_error_types': len(set([e.exception_type for e in day_errors]))
            }
        
        return trends
    
    def export_error_report(self, days: int = 7) -> Dict[str, Any]:
        """Export comprehensive error report."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'report_period_days': days,
            'summary': self.get_error_summary(hours=days*24),
            'trends': self.get_error_trends(days=days),
            'error_patterns': [pattern.to_dict() for pattern in self.error_patterns.values()],
            'recent_critical_errors': [
                error.to_dict() for error in self.error_events.values()
                if error.timestamp >= cutoff_date and error.severity == ErrorSeverity.CRITICAL
            ]
        }
        
        return report
    
    def cleanup_old_errors(self):
        """Remove old error data beyond retention period."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.max_history_days)
        
        # Remove old error events
        old_error_ids = [
            error_id for error_id, error in self.error_events.items()
            if error.timestamp < cutoff_date
        ]
        
        for error_id in old_error_ids:
            del self.error_events[error_id]
        
        # Clean up hour-based counters
        old_hour_keys = [
            hour_key for hour_key in self.error_counts_by_hour.keys()
            if datetime.strptime(hour_key, '%Y-%m-%d_%H') < cutoff_date.replace(tzinfo=None)
        ]
        
        for hour_key in old_hour_keys:
            del self.error_counts_by_hour[hour_key]
        
        if old_error_ids or old_hour_keys:
            logger.info("Cleaned up %d old errors and %d hour counters", len(old_error_ids), len(old_hour_keys))
            self._save_persisted_data()


# Global error tracker instance
_error_tracker: Optional[ErrorTracker] = None


def get_error_tracker(config: Optional[Dict[str, Any]] = None) -> ErrorTracker:
    """Get the global error tracker instance."""
    # Using global state for singleton pattern
    # pylint: disable=global-statement
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker(config)
    return _error_tracker


def track_error(exception: Exception, context: Optional[ErrorContext] = None,
               severity: Optional[ErrorSeverity] = None,
               category: Optional[ErrorCategory] = None) -> str:
    """Convenience function to track an error using the global tracker."""
    tracker = get_error_tracker()
    return tracker.track_error(exception, context, severity, category)