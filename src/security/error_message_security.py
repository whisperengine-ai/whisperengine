"""
Error Message Security System
Addresses CVSS 5.3 Error Message Information Disclosure Vulnerability

This module provides secure error handling that prevents:
- Internal system architecture exposure
- Database schema and file path leakage
- API endpoint and service provider disclosure
- User ID and sensitive data exposure in error messages
- Stack trace information leakage to end users

SECURITY FEATURES:
- Sanitized error messages for public consumption
- Detailed logging for developers (secure channels only)
- Context-aware error filtering
- User-friendly generic error responses
- Security event logging for suspicious errors
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import discord

# Import secure logging for error audit trail
try:
    from secure_logging import DataSensitivity, LogLevel, get_secure_logger

    secure_logger = get_secure_logger("error_message_security")
    HAS_SECURE_LOGGING = True
except ImportError:
    # Fallback to standard logging if secure logging not available
    secure_logger = logging.getLogger("error_message_security")
    HAS_SECURE_LOGGING = False

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Classification of error severity for security filtering"""

    LOW = "low"  # Minor errors, safe to show more detail
    MEDIUM = "medium"  # Moderate errors, show generic message
    HIGH = "high"  # Serious errors, minimal information
    CRITICAL = "critical"  # Security-sensitive, no information


class ErrorContext(Enum):
    """Context where error occurred determines filtering level"""

    PUBLIC_CHANNEL = "public_channel"  # Strictest filtering
    PRIVATE_DM = "private_dm"  # Moderate filtering
    ADMIN_CHANNEL = "admin_channel"  # Minimal filtering
    SYSTEM_LOG = "system_log"  # Full detail allowed


@dataclass
class SecureErrorResponse:
    """Secure error response with sanitized user message and detailed logging"""

    user_message: str  # Safe message for end user
    log_message: str  # Detailed message for logs
    error_code: str  # Generic error identifier
    severity: ErrorSeverity
    context: ErrorContext
    sanitized_details: str | None = None
    requires_admin_notification: bool = False


class ErrorMessageSecurity:
    """
    Security system for error message handling and information disclosure prevention.

    This class sanitizes error messages to prevent:
    - File path disclosure
    - Database schema exposure
    - API endpoint leakage
    - Internal architecture revelation
    - User data exposure
    """

    def __init__(self):
        self.sensitive_patterns = self._load_sensitive_patterns()
        self.generic_messages = self._load_generic_messages()
        self.error_counts = {}  # Track error patterns for security monitoring

    def _load_sensitive_patterns(self) -> list[tuple[str, str]]:
        """Load patterns that should be filtered from error messages"""
        return [
            # File paths and directory structures
            (r"/Users/[^/\s]+/[^\s]*", "[PATH_REDACTED]"),
            (r"/home/[^/\s]+/[^\s]*", "[PATH_REDACTED]"),
            (r"C:\\[^\s]*", "[PATH_REDACTED]"),
            (r"/var/log/[^\s]*", "[LOG_PATH_REDACTED]"),
            (r"/tmp/[^\s]*", "[TEMP_PATH_REDACTED]"),
            # Database and storage details
            (r"chromadb_data[^\s]*", "[DB_PATH_REDACTED]"),
            (r'collection [\'"]([^\'"]+)[\'"]', "collection [COLLECTION_REDACTED]"),
            (r'database [\'"]([^\'"]+)[\'"]', "database [DB_REDACTED]"),
            (r'table [\'"]([^\'"]+)[\'"]', "table [TABLE_REDACTED]"),
            # API endpoints and services
            (r"https?://api\.[^\s]+", "[API_ENDPOINT_REDACTED]"),
            (r"https?://[^\s]+\.openai\.com[^\s]*", "[OPENAI_API_REDACTED]"),
            (r"https?://[^\s]+\.anthropic\.com[^\s]*", "[ANTHROPIC_API_REDACTED]"),
            (r"https?://[^\s]+", "[URL_REDACTED]"),
            # User IDs and sensitive identifiers
            (r"user_id[:\s]+(\d{15,})", "user_id: [USER_ID_REDACTED]"),
            (r"User (\d{15,})", "User [USER_ID_REDACTED]"),
            (r"channel_id[:\s]+(\d{15,})", "channel_id: [CHANNEL_ID_REDACTED]"),
            (r"guild_id[:\s]+(\d{15,})", "guild_id: [GUILD_ID_REDACTED]"),
            # API keys and tokens (partial matching)
            (r"sk-[A-Za-z0-9]{20,}", "[API_KEY_REDACTED]"),
            (r"Bearer [A-Za-z0-9]{20,}", "Bearer [TOKEN_REDACTED]"),
            (r"token[:\s]+[A-Za-z0-9]{20,}", "token: [TOKEN_REDACTED]"),
            # Memory and system details
            (r"memory address 0x[a-fA-F0-9]+", "memory address [ADDR_REDACTED]"),
            (r"PID \d+", "PID [PID_REDACTED]"),
            (r"port \d{4,5}", "port [PORT_REDACTED]"),
            # Stack trace file references
            (r'File "([^"]+\.py)"', 'File "[SCRIPT_REDACTED]"'),
            (r"line \d+", "line [LINE_REDACTED]"),
            # Environment variables
            (r'env\[[\'"]([^\'"]+)[\'"]\]', "env[[ENV_VAR_REDACTED]]"),
            (r'os\.environ\[[\'"]([^\'"]+)[\'"]\]', "os.environ[[ENV_VAR_REDACTED]]"),
        ]

    def _load_generic_messages(self) -> dict[str, str]:
        """Load generic error messages for different error types"""
        return {
            "connection_error": "I'm having trouble connecting to external services. Please try again later.",
            "timeout_error": "The request took too long to process. Please try again.",
            "rate_limit_error": "I'm being rate limited. Please wait a moment before trying again.",
            "memory_error": "I encountered an issue accessing my memory. Please try again.",
            "validation_error": "There was an issue with the input provided. Please check and try again.",
            "permission_error": "I don't have permission to perform this action.",
            "api_error": "There was an issue with an external service. Please try again later.",
            "database_error": "I encountered a storage issue. Please try again later.",
            "processing_error": "I encountered an issue processing your request. Please try again.",
            "unknown_error": "An unexpected error occurred. Please try again later.",
            "system_error": "A system error occurred. Please contact an administrator if this persists.",
        }

    def sanitize_error_message(
        self,
        error_message: str,
        context: ErrorContext = ErrorContext.PUBLIC_CHANNEL,
        error_type: str = "unknown_error",
    ) -> SecureErrorResponse:
        """
        Sanitize an error message for safe public consumption.

        Args:
            error_message: Original error message
            context: Context where error will be shown
            error_type: Type of error for appropriate generic message

        Returns:
            SecureErrorResponse with sanitized user message and detailed log message
        """

        # Track error patterns for security monitoring
        self._track_error_pattern(error_message, error_type)

        # Determine severity based on message content
        severity = self._classify_error_severity(error_message)

        # Create detailed log message (preserve original for debugging)
        log_message = f"[{error_type}] {error_message}"

        # Sanitize message based on context and severity
        user_message = self._apply_sanitization(error_message, context, severity)

        # For public channels, use generic messages for high/critical severity
        # For other contexts, allow sanitized messages to show through
        if context == ErrorContext.PUBLIC_CHANNEL and severity in [
            ErrorSeverity.HIGH,
            ErrorSeverity.CRITICAL,
        ]:
            user_message = self.generic_messages.get(
                error_type, self.generic_messages["unknown_error"]
            )
        elif context == ErrorContext.PRIVATE_DM and severity == ErrorSeverity.CRITICAL:
            # Even in DM, critical errors get generic messages
            user_message = self.generic_messages.get(
                error_type, self.generic_messages["unknown_error"]
            )

        # Generate error code for tracking
        error_code = self._generate_error_code(error_type, error_message)

        # Check if admin notification is needed
        requires_admin_notification = (
            severity == ErrorSeverity.CRITICAL or self._is_suspicious_error(error_message)
        )

        response = SecureErrorResponse(
            user_message=user_message,
            log_message=log_message,
            error_code=error_code,
            severity=severity,
            context=context,
            requires_admin_notification=requires_admin_notification,
        )

        # Log the error securely
        self._log_secure_error(response)

        return response

    def _apply_sanitization(
        self, message: str, context: ErrorContext, severity: ErrorSeverity
    ) -> str:
        """Apply sanitization patterns to remove sensitive information"""

        sanitized = message

        # Apply all sensitive pattern replacements
        for pattern, replacement in self.sensitive_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        # Additional context-specific sanitization
        if context == ErrorContext.PUBLIC_CHANNEL:
            # Most restrictive - remove almost all technical details
            sanitized = re.sub(r"\b\w+Error\b", "Error", sanitized)
            sanitized = re.sub(r"Exception.*", "Exception occurred", sanitized)
            sanitized = re.sub(r"Traceback.*", "Error details omitted", sanitized, flags=re.DOTALL)

        elif context == ErrorContext.PRIVATE_DM:
            # Moderate filtering - keep some technical context
            sanitized = re.sub(
                r"Traceback \(most recent call last\):.*",
                "[Stack trace omitted]",
                sanitized,
                flags=re.DOTALL,
            )

        # Admin channels get minimal filtering
        # System logs get no additional filtering beyond pattern replacement

        return sanitized

    def _classify_error_severity(self, error_message: str) -> ErrorSeverity:
        """Classify error severity based on message content"""

        message_lower = error_message.lower()

        # Critical errors - potential security issues
        critical_indicators = [
            "unauthorized",
            "forbidden",
            "access denied",
            "permission denied",
            "authentication failed",
            "invalid token",
            "api key",
            "secret",
            "sql injection",
            "xss",
            "csrf",
            "directory traversal",
        ]

        # High severity - system/service issues
        high_indicators = [
            "database",
            "connection refused",
            "timeout",
            "service unavailable",
            "internal server error",
            "chromadb",
            "memory error",
            "disk full",
        ]

        # Medium severity - processing issues
        medium_indicators = [
            "validation",
            "parsing",
            "format",
            "invalid input",
            "bad request",
            "not found",
            "missing",
            "empty response",
        ]

        for indicator in critical_indicators:
            if indicator in message_lower:
                return ErrorSeverity.CRITICAL

        for indicator in high_indicators:
            if indicator in message_lower:
                return ErrorSeverity.HIGH

        for indicator in medium_indicators:
            if indicator in message_lower:
                return ErrorSeverity.MEDIUM

        return ErrorSeverity.LOW

    def _is_suspicious_error(self, error_message: str) -> bool:
        """Detect potentially suspicious error patterns that may indicate attacks"""

        suspicious_patterns = [
            r"union.*select",  # SQL injection attempts
            r"<script.*>",  # XSS attempts
            r"\.\./",  # Directory traversal
            r"eval\s*\(",  # Code injection
            r"system\s*\(",  # System command injection
            r"import.*os",  # Python injection attempts
            r"__import__",  # Python injection attempts
            r"exec\s*\(",  # Code execution attempts
        ]

        message_lower = error_message.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True

        return False

    def _track_error_pattern(self, error_message: str, error_type: str):
        """Track error patterns for security monitoring"""

        # Create a hash of the error pattern for tracking
        pattern_hash = hashlib.sha256(f"{error_type}:{error_message[:100]}".encode()).hexdigest()[
            :16
        ]

        if pattern_hash not in self.error_counts:
            self.error_counts[pattern_hash] = {
                "count": 0,
                "first_seen": datetime.now(),
                "last_seen": datetime.now(),
                "error_type": error_type,
                "sample_message": error_message[:100],
            }

        self.error_counts[pattern_hash]["count"] += 1
        self.error_counts[pattern_hash]["last_seen"] = datetime.now()

        # Alert on suspicious frequency
        if self.error_counts[pattern_hash]["count"] > 10:
            self._alert_error_frequency(pattern_hash, self.error_counts[pattern_hash])

    def _generate_error_code(self, error_type: str, error_message: str) -> str:
        """Generate a unique but safe error code for tracking"""

        # Create hash from error details
        error_hash = hashlib.sha256(f"{error_type}:{error_message}".encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d")

        return f"ERR-{timestamp}-{error_hash.upper()}"

    def _log_secure_error(self, response: SecureErrorResponse):
        """Log error information securely"""

        if HAS_SECURE_LOGGING:
            # Use secure logging with appropriate sensitivity
            if response.severity == ErrorSeverity.CRITICAL:
                secure_logger.log_security_event(
                    message=f"[CRITICAL_ERROR] {response.log_message}",
                    threat_level="critical",
                    event_type="critical_error",
                    user_id=None,
                    additional_data={
                        "error_code": response.error_code,
                        "context": response.context.value,
                        "requires_admin_notification": response.requires_admin_notification,
                    },
                )
            else:
                # Map severity to threat level
                threat_levels = {
                    ErrorSeverity.HIGH: "high",
                    ErrorSeverity.MEDIUM: "medium",
                    ErrorSeverity.LOW: "low",
                }

                secure_logger.log_security_event(
                    message=response.log_message,
                    threat_level=threat_levels.get(response.severity, "low"),
                    event_type="error_occurred",
                    user_id=None,
                    additional_data={"error_code": response.error_code},
                )
        else:
            # Fallback logging
            log_level = {
                ErrorSeverity.CRITICAL: logger.critical,
                ErrorSeverity.HIGH: logger.error,
                ErrorSeverity.MEDIUM: logger.warning,
                ErrorSeverity.LOW: logger.info,
            }.get(response.severity, logger.info)

            log_level(f"[{response.error_code}] {response.log_message}")

    def _alert_error_frequency(self, pattern_hash: str, error_data: dict):
        """Alert on suspicious error frequency patterns"""

        if HAS_SECURE_LOGGING:
            secure_logger.log_security_event(
                message=f"High frequency error pattern detected: {error_data['error_type']}",
                threat_level="medium",
                event_type="high_error_frequency",
                user_id=None,
                additional_data={
                    "pattern_hash": pattern_hash,
                    "error_count": error_data["count"],
                    "sample_message": error_data["sample_message"],
                    "first_seen": error_data["first_seen"].isoformat(),
                    "last_seen": error_data["last_seen"].isoformat(),
                },
            )

    def handle_discord_error(self, error: Exception, context: discord.Message | None = None) -> str:
        """
        Handle Discord-specific errors with appropriate context awareness.

        Args:
            error: The exception that occurred
            context: Discord message context (if available)

        Returns:
            Safe error message for user
        """

        # Determine context from Discord message
        if context:
            if isinstance(context.channel, discord.DMChannel):
                error_context = ErrorContext.PRIVATE_DM
            elif hasattr(context.channel, "guild") and context.channel.guild:
                error_context = ErrorContext.PUBLIC_CHANNEL
            else:
                error_context = ErrorContext.PUBLIC_CHANNEL
        else:
            error_context = ErrorContext.SYSTEM_LOG

        # Classify error type
        error_type = self._classify_discord_error(error)

        # Get sanitized response
        response = self.sanitize_error_message(
            str(error), context=error_context, error_type=error_type
        )

        # Notify admin if needed
        if response.requires_admin_notification:
            self._notify_admin_async(response, context)

        return response.user_message

    def _classify_discord_error(self, error: Exception) -> str:
        """Classify Discord/bot-specific error types"""

        error_name = type(error).__name__
        error_message = str(error).lower()

        # Map exception types to error categories
        error_type_mapping = {
            "ConnectionError": "connection_error",
            "TimeoutError": "timeout_error",
            "HTTPException": "api_error",
            "Forbidden": "permission_error",
            "NotFound": "api_error",
            "RateLimitError": "rate_limit_error",
            "LLMError": "api_error",
            "MemoryError": "memory_error",
            "ValidationError": "validation_error",
        }

        # Check for specific error patterns
        if "rate limit" in error_message or "too many requests" in error_message:
            return "rate_limit_error"
        elif "timeout" in error_message:
            return "timeout_error"
        elif "connection" in error_message:
            return "connection_error"
        elif "permission" in error_message or "forbidden" in error_message:
            return "permission_error"
        elif "memory" in error_message or "chromadb" in error_message:
            return "memory_error"

        return error_type_mapping.get(error_name, "unknown_error")

    def _notify_admin_async(self, response: SecureErrorResponse, context: discord.Message | None):
        """Notify administrators of critical errors (async-safe)"""

        # This would integrate with admin notification system
        # For now, just log the critical error
        if HAS_SECURE_LOGGING:
            secure_logger.log_security_event(
                message=f"Critical error requires admin attention: {response.error_code}",
                threat_level="critical",
                event_type="admin_notification_required",
                user_id=None,
                additional_data={
                    "user_message": response.user_message,
                    "context_type": str(context.channel.type) if context else "unknown",
                    "guild_id": str(context.guild.id) if context and context.guild else None,
                    "channel_id": str(context.channel.id) if context else None,
                },
            )


# Global instance for easy importing
error_security = ErrorMessageSecurity()


def secure_error_handler(error: Exception, context: discord.Message | None = None) -> str:
    """
    Convenient function to handle errors securely.

    Usage:
        try:
            # risky operation
        except Exception as e:
            safe_message = secure_error_handler(e, message)
            await message.reply(safe_message)
    """
    return error_security.handle_discord_error(error, context)


def sanitize_error_for_logging(error_message: str) -> str:
    """
    Sanitize error message for secure logging.

    Usage:
        logger.error(sanitize_error_for_logging(f"Database error: {str(e)}"))
    """
    response = error_security.sanitize_error_message(error_message, context=ErrorContext.SYSTEM_LOG)
    return response.log_message
