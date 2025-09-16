"""
Secure Logging System for Discord Bot
Addresses CVSS 5.8 Logging Security Vulnerabilities

This module provides secure logging with automatic PII sanitization,
data masking, and compliance with privacy standards.
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import discord


class LogLevel(Enum):
    """Security-aware log levels with data sensitivity classification"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SECURITY = "SECURITY"  # Special level for security events


class DataSensitivity(Enum):
    """Classification of data sensitivity for logging decisions"""

    PUBLIC = "public"  # Safe to log in full
    INTERNAL = "internal"  # Can log with basic sanitization
    SENSITIVE = "sensitive"  # Must be heavily masked/hashed
    CONFIDENTIAL = "confidential"  # Should not be logged at all


@dataclass
class LogEntry:
    """Structured log entry with security metadata"""

    timestamp: datetime
    level: LogLevel
    message: str
    context: str | None = None
    user_id_hash: str | None = None
    channel_type: str | None = None
    sensitive_data_removed: bool = False
    original_length: int | None = None


class SecureLogger:
    """
    Secure logging system with automatic PII sanitization and data masking.

    Features:
    - Automatic PII detection and sanitization
    - User ID hashing for privacy
    - Message content sanitization
    - Structured logging with security metadata
    - Configurable sensitivity levels
    - Audit trail for security events
    """

    def __init__(self, name: str, log_level: LogLevel = LogLevel.INFO):
        self.name = name
        self.log_level = log_level
        self.logger = logging.getLogger(name)
        self._setup_secure_formatting()

        # PII patterns for automatic detection
        self.pii_patterns = {
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
            "discord_token": re.compile(r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}"),
            "api_key": re.compile(
                r'(?i)(api[_-]?key|token|secret)["\s]*[:=\s]["\s]*[\w-]+|sk-[\w\d]+'
            ),
            "discord_id": re.compile(r"\b\d{17,19}\b"),  # Discord snowflake IDs
        }

        # Sensitive content indicators
        self.sensitive_indicators = [
            "password",
            "token",
            "secret",
            "key",
            "auth",
            "private",
            "confidential",
            "personal",
            "medical",
            "financial",
            "ssn",
            "social security",
        ]

    def _setup_secure_formatting(self):
        """Setup secure log formatting with structured output"""
        formatter = SecureLogFormatter()

        # Create secure handler (in production, this should go to secure log storage)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

        # Map our custom log levels to standard logging levels
        if self.log_level == LogLevel.SECURITY:
            self.logger.setLevel(logging.WARNING)  # Security events are important
        else:
            self.logger.setLevel(getattr(logging, self.log_level.value))

    def _hash_user_id(self, user_id: str | int) -> str:
        """Create privacy-safe hash of user ID for logging"""
        if user_id is None:
            return "anonymous"

        # Use first 8 characters of SHA-256 hash for space efficiency
        hash_obj = hashlib.sha256(str(user_id).encode())
        return f"user_{hash_obj.hexdigest()[:8]}"

    def _sanitize_message_content(
        self, content: str, sensitivity: DataSensitivity = DataSensitivity.SENSITIVE
    ) -> tuple[str, bool]:
        """
        Sanitize message content based on sensitivity level
        Returns (sanitized_content, was_modified)
        """
        if not content:
            return "", False

        modified = False

        # Remove PII patterns
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(content):
                if sensitivity == DataSensitivity.CONFIDENTIAL:
                    content = f"[CONTENT REMOVED - {pii_type.upper()} DETECTED]"
                else:
                    content = pattern.sub(f"[{pii_type.upper()}_REDACTED]", content)
                modified = True

        # Check for sensitive indicators
        content_lower = content.lower()
        for indicator in self.sensitive_indicators:
            if indicator in content_lower:
                if sensitivity in (DataSensitivity.SENSITIVE, DataSensitivity.CONFIDENTIAL):
                    # Replace sensitive parts with placeholder
                    content = re.sub(
                        f"(?i){re.escape(indicator)}[^\\s]*",
                        f"[{indicator.upper()}_REDACTED]",
                        content,
                    )
                    modified = True

        # Truncate very long messages
        if len(content) > 200:
            content = content[:200] + "... [TRUNCATED]"
            modified = True

        return content, modified

    def _classify_discord_context(self, message=None, channel=None) -> str:
        """Classify Discord context for appropriate logging sensitivity"""
        if message:
            if isinstance(message.channel, discord.DMChannel):
                return "dm"
            elif isinstance(message.channel, discord.GroupChannel):
                return "group_dm"
            elif isinstance(message.channel, discord.TextChannel):
                return "guild_text"
            elif isinstance(message.channel, discord.VoiceChannel):
                return "guild_voice"
        elif channel:
            return type(channel).__name__.lower()
        return "unknown"

    def log_user_action(
        self,
        level: LogLevel,
        message: str,
        user_id: str | int | None = None,
        discord_message=None,
        context: str | None = None,
        sensitivity: DataSensitivity = DataSensitivity.INTERNAL,
    ):
        """
        Log user action with appropriate security sanitization

        Args:
            level: Log level
            message: Log message template
            user_id: User ID (will be hashed)
            discord_message: Discord message object for context
            context: Additional context information
            sensitivity: Data sensitivity level for sanitization
        """

        # Hash user ID for privacy
        user_hash = self._hash_user_id(user_id) if user_id else None

        # Classify channel context if Discord message provided
        channel_type = None
        if discord_message:
            channel_type = self._classify_discord_context(discord_message)
            if not user_id and discord_message.author:
                user_hash = self._hash_user_id(discord_message.author.id)

        # Sanitize the message content
        sanitized_message, was_sanitized = self._sanitize_message_content(message, sensitivity)

        # Create structured log entry
        log_entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            message=sanitized_message,
            context=context,
            user_id_hash=user_hash,
            channel_type=channel_type,
            sensitive_data_removed=was_sanitized,
            original_length=len(message) if was_sanitized else None,
        )

        # Format final log message
        log_msg = self._format_log_entry(log_entry)

        # Log with appropriate level
        if level == LogLevel.SECURITY:
            python_level = logging.WARNING  # Security events are important
        else:
            python_level = getattr(logging, level.value)
        self.logger.log(python_level, log_msg)

    def _format_log_entry(self, entry: LogEntry) -> str:
        """Format log entry for secure output"""
        components = [f"[{entry.level.value}]", f"[{entry.timestamp.isoformat()}]"]

        if entry.user_id_hash:
            components.append(f"[{entry.user_id_hash}]")

        if entry.channel_type:
            components.append(f"[{entry.channel_type}]")

        if entry.context:
            components.append(f"[{entry.context}]")

        components.append(entry.message)

        if entry.sensitive_data_removed:
            components.append("[SANITIZED]")

        return " ".join(components)

    def log_security_event(
        self,
        message: str,
        user_id: str | int | None = None,
        threat_level: str = "medium",
        event_type: str = "security_violation",
        additional_data: dict | None = None,
    ):
        """
        Log security-related events with high priority

        Args:
            message: Security event description
            user_id: User involved (will be hashed)
            threat_level: low/medium/high/critical
            event_type: Type of security event
            additional_data: Additional structured data (will be sanitized)
        """

        security_msg = f"SECURITY_EVENT: {event_type.upper()} - {message}"

        if additional_data:
            # Sanitize additional data
            sanitized_data = {}
            for key, value in additional_data.items():
                if isinstance(value, str):
                    sanitized_value, _ = self._sanitize_message_content(
                        value, DataSensitivity.CONFIDENTIAL
                    )
                    sanitized_data[key] = sanitized_value
                else:
                    sanitized_data[key] = str(value)[:100]  # Truncate non-string values

            security_msg += f" | Data: {json.dumps(sanitized_data)}"

        self.log_user_action(
            level=LogLevel.SECURITY,
            message=security_msg,
            user_id=user_id,
            context=f"threat_level_{threat_level}",
            sensitivity=DataSensitivity.CONFIDENTIAL,
        )

    def log_message_processing(self, discord_message, action: str, result: str = "success"):
        """
        Log message processing events with appropriate sanitization

        Args:
            discord_message: Discord message object
            action: Action being performed (e.g., "fact_extraction", "emotion_analysis")
            result: Result of the action
        """

        # Get basic message info without logging content
        message_info = f"Action: {action} | Result: {result}"

        # Determine sensitivity based on channel type
        channel_type = self._classify_discord_context(discord_message)
        sensitivity = (
            DataSensitivity.SENSITIVE if channel_type == "dm" else DataSensitivity.INTERNAL
        )

        self.log_user_action(
            level=LogLevel.INFO,
            message=message_info,
            discord_message=discord_message,
            context=f"msg_processing_{action}",
            sensitivity=sensitivity,
        )

    def log_api_interaction(
        self,
        api_name: str,
        endpoint: str,
        status: str,
        user_id: str | int | None = None,
        response_size: int | None = None,
        error_details: str | None = None,
    ):
        """
        Log API interactions with security focus

        Args:
            api_name: Name of the API (e.g., "openai", "elevenlabs")
            endpoint: API endpoint called
            status: success/error/timeout
            user_id: User associated with request (will be hashed)
            response_size: Size of response in bytes
            error_details: Error details (will be sanitized)
        """

        api_msg = f"API: {api_name} | Endpoint: {endpoint} | Status: {status}"

        if response_size:
            api_msg += f" | Response: {response_size} bytes"

        if error_details:
            # Sanitize error details to remove potential API keys or sensitive info
            sanitized_error, _ = self._sanitize_message_content(
                error_details, DataSensitivity.SENSITIVE
            )
            api_msg += f" | Error: {sanitized_error}"

        level = LogLevel.ERROR if status == "error" else LogLevel.INFO

        self.log_user_action(
            level=level,
            message=api_msg,
            user_id=user_id,
            context=f"api_{api_name}",
            sensitivity=DataSensitivity.INTERNAL,
        )

    def log_database_operation(
        self,
        operation: str,
        table: str,
        user_id: str | int | None = None,
        record_count: int | None = None,
        operation_result: str = "success",
    ):
        """
        Log database operations with privacy protection

        Args:
            operation: Type of operation (select/insert/update/delete)
            table: Database table name
            user_id: User associated with operation (will be hashed)
            record_count: Number of records affected
            operation_result: Result of operation
        """

        db_msg = f"DB: {operation.upper()} on {table} | Result: {operation_result}"

        if record_count is not None:
            db_msg += f" | Records: {record_count}"

        level = LogLevel.ERROR if operation_result == "error" else LogLevel.DEBUG

        self.log_user_action(
            level=level,
            message=db_msg,
            user_id=user_id,
            context=f"db_{operation}",
            sensitivity=DataSensitivity.INTERNAL,
        )


class SecureLogFormatter(logging.Formatter):
    """Custom formatter for secure logging with structured output"""

    def format(self, record):
        # Use the message as-is since SecureLogger already handles formatting
        return record.getMessage()


# Global secure logger instances
secure_logger = SecureLogger("discord_bot_secure", LogLevel.INFO)
security_logger = SecureLogger("security_events", LogLevel.SECURITY)


def get_secure_logger(name: str) -> SecureLogger:
    """Get a secure logger instance for a specific component"""
    return SecureLogger(f"discord_bot.{name}", LogLevel.INFO)
