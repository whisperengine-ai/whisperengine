"""
Input Validation and Sanitization Module
Security enhancement to prevent injection attacks and malicious content processing.
"""

import logging
import re
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Comprehensive input validation and sanitization for Discord bot messages.
    Prevents injection attacks, XSS, and other malicious content processing.
    """

    # Maximum allowed message length (Discord limit is 2000, we set slightly lower for safety)
    MAX_MESSAGE_LENGTH = 1900

    # Dangerous patterns that could indicate injection attempts
    DANGEROUS_PATTERNS = [
        # System override attempts
        r"\[SYSTEM\s*OVERRIDE\]",
        r"IGNORE\s*PREVIOUS\s*INSTRUCTIONS",
        r"FORGET\s*PREVIOUS\s*INSTRUCTIONS",
        r"DISREGARD\s*ABOVE",
        r"SYSTEM\s*PROMPT\s*INJECTION",
        # Bot instruction manipulation
        r"YOU\s*ARE\s*NOW\s*A\s*DIFFERENT",
        r"PRETEND\s*TO\s*BE",
        r"ACT\s*AS\s*IF\s*YOU\s*ARE",
        r"ROLEPLAY\s*AS",
        # Information disclosure attempts
        r"REVEAL\s*YOUR\s*SYSTEM\s*PROMPT",
        r"SHOW\s*YOUR\s*INSTRUCTIONS",
        r"WHAT\s*ARE\s*YOUR\s*INSTRUCTIONS",
        r"DISPLAY\s*YOUR\s*SYSTEM\s*MESSAGE",
        r"PRINT\s*YOUR\s*CONFIGURATION",
        # Prompt injection attempts
        r"\\n\\n###\\s*NEW\\s*INSTRUCTIONS",
        r"---\\s*END\\s*OF\\s*CONVERSATION",
        r"###\\s*SYSTEM\\s*MESSAGE",
        r"\\*\\*\\*\\s*IMPORTANT\\s*UPDATE",
        # Script injection (basic XSS prevention)
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"data:text/html",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        # SQL injection patterns (basic prevention)
        r";\\s*DROP\\s+TABLE",
        r";\\s*DELETE\\s+FROM",
        r";\\s*INSERT\\s+INTO",
        r";\\s*UPDATE\\s+SET",
        r"UNION\\s+SELECT",
        r"'\\s*;\\s*DROP\\s+TABLE",  # Common SQL injection with quotes
        r'"\\s*;\\s*DROP\\s+TABLE',  # Common SQL injection with double quotes
        # Command injection patterns
        r"&&\\s*rm\\s+-rf",
        r"\\|\\s*curl\\s+",
        r"\\|\\s*wget\\s+",
        r"\\|\\s*nc\\s+",
        r"`[^`]*`",  # Backtick command execution
        r"\\$\\([^)]*\\)",  # Command substitution
        r"test\\s*&&\\s*rm\\s*-rf",  # Specific command chaining
        r"\\$\\(\\w+.*?\\)",  # Command substitution patterns
    ]

    # Suspicious keywords that warrant logging
    SUSPICIOUS_KEYWORDS = [
        "system prompt",
        "instructions",
        "override",
        "inject",
        "manipulation",
        "reveal",
        "show configuration",
        "debug mode",
        "admin",
        "root access",
        "bypass",
        "exploit",
        "vulnerability",
        "hack",
        "crack",
    ]

    def __init__(self):
        """Initialize the input validator."""
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.DANGEROUS_PATTERNS
        ]
        logger.info("InputValidator initialized with security patterns")

    def validate_and_sanitize(
        self, message_content: str, user_id: str, channel_type: str = "unknown"
    ) -> dict[str, Any]:
        """
        Validate and sanitize user input message.

        Args:
            message_content: Raw message content from user
            user_id: Discord user ID for logging
            channel_type: Type of channel (dm, server, etc.) for context

        Returns:
            Dict containing:
            - 'sanitized_content': Cleaned message content
            - 'is_safe': Boolean indicating if message is safe to process
            - 'warnings': List of security warnings
            - 'blocked_patterns': List of patterns that were detected
        """
        if not message_content:
            return {
                "sanitized_content": "",
                "is_safe": True,
                "warnings": [],
                "blocked_patterns": [],
            }

        original_content = message_content
        warnings = []
        blocked_patterns = []

        # 1. Length validation
        if len(message_content) > self.MAX_MESSAGE_LENGTH:
            message_content = message_content[: self.MAX_MESSAGE_LENGTH]
            warnings.append(f"Message truncated to {self.MAX_MESSAGE_LENGTH} characters")
            logger.warning(
                f"User {user_id} sent oversized message ({len(original_content)} chars), truncated"
            )

        # 2. Dangerous pattern detection and sanitization
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(message_content)
            if matches:
                pattern_name = self.DANGEROUS_PATTERNS[i]
                blocked_patterns.append(pattern_name)

                # Replace dangerous content with safe placeholder
                message_content = pattern.sub("[CONTENT_FILTERED_FOR_SECURITY]", message_content)

                # Log security incident
                logger.error(
                    f"SECURITY: Dangerous pattern detected from user {user_id} in {channel_type}: {pattern_name}"
                )
                logger.error(f"SECURITY: Original matches: {matches}")

                warnings.append("Potentially malicious content detected and filtered")

        # 3. Suspicious keyword detection (logging only, don't filter)
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword.lower() in message_content.lower():
                logger.warning(
                    f"SECURITY: Suspicious keyword '{keyword}' detected from user {user_id} in {channel_type}"
                )
                warnings.append("Suspicious content detected - monitoring increased")

        # 4. Additional sanitization
        sanitized_content = self._additional_sanitization(message_content)

        # 5. Determine if message is safe to process
        is_safe = len(blocked_patterns) == 0

        # Log summary if any issues were found
        if warnings or blocked_patterns:
            logger.info(
                f"SECURITY SUMMARY - User: {user_id}, Channel: {channel_type}, "
                f"Warnings: {len(warnings)}, Blocked: {len(blocked_patterns)}, Safe: {is_safe}"
            )

        return {
            "sanitized_content": sanitized_content,
            "is_safe": is_safe,
            "warnings": warnings,
            "blocked_patterns": blocked_patterns,
        }

    def _additional_sanitization(self, content: str) -> str:
        """
        Additional sanitization steps for safer content processing.

        Args:
            content: Message content to sanitize

        Returns:
            Sanitized content
        """
        # Remove null bytes and control characters (except newlines and tabs)
        content = "".join(char for char in content if ord(char) >= 32 or char in ["\n", "\t", "\r"])

        # Handle null bytes specifically (they can be used for injection)
        content = content.replace("\x00", "").replace("\x01", " ")

        # Normalize whitespace (prevent whitespace-based obfuscation)
        content = re.sub(r"\s+", " ", content).strip()

        # Remove zero-width characters that could be used for obfuscation
        zero_width_chars = ["\u200b", "\u200c", "\u200d", "\ufeff", "\u2060"]
        for char in zero_width_chars:
            content = content.replace(char, "")

        # Basic URL validation (ensure URLs are properly formatted)
        content = self._sanitize_urls(content)

        return content

    def _sanitize_urls(self, content: str) -> str:
        """
        Basic URL sanitization to prevent malicious redirects.

        Args:
            content: Content that may contain URLs

        Returns:
            Content with sanitized URLs
        """
        # Find URLs in the content
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+'
        urls = re.findall(url_pattern, content)

        for url in urls:
            try:
                parsed = urlparse(url)

                # Block suspicious protocols or malformed URLs
                if not parsed.netloc or parsed.scheme not in ["http", "https"]:
                    logger.warning(f"SECURITY: Suspicious URL detected and removed: {url}")
                    content = content.replace(url, "[SUSPICIOUS_URL_REMOVED]")
                    continue

                # Block known malicious or suspicious domains (basic list)
                suspicious_domains = [
                    "bit.ly",
                    "tinyurl.com",
                    "short.link",  # Common URL shorteners (could hide malicious sites)
                    "localhost",
                    "127.0.0.1",
                    "0.0.0.0",  # Local addresses
                ]

                if any(domain in parsed.netloc.lower() for domain in suspicious_domains):
                    logger.warning(
                        f"SECURITY: Potentially suspicious domain detected: {parsed.netloc}"
                    )
                    # Don't block, but log for monitoring

            except Exception as e:
                logger.warning(f"SECURITY: Error parsing URL {url}: {e}")
                # Remove malformed URLs
                content = content.replace(url, "[MALFORMED_URL_REMOVED]")

        return content

    def is_admin_command_safe(self, content: str, user_id: str) -> bool:
        """
        Additional validation for admin commands to prevent privilege escalation.

        Args:
            content: Command content
            user_id: User ID attempting the command

        Returns:
            True if command is safe for admin execution
        """
        # Admin commands should not contain certain dangerous patterns
        admin_dangerous_patterns = [
            r"rm\s+-rf",
            r"del\s+/s",
            r"format\s+c:",
            r"DROP\s+DATABASE",
            r"DELETE\s+FROM\s+users",
            r"shutdown\s+/s",
            r"reboot\s+/f",
            r"kill\s+-9",
            r"sudo\s+su",
            r"chmod\s+777",
        ]

        for pattern in admin_dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                logger.error(f"SECURITY: Dangerous admin command attempted by {user_id}: {pattern}")
                return False

        return True

    def log_security_event(
        self, event_type: str, user_id: str, details: str, severity: str = "WARNING"
    ):
        """
        Log security events for monitoring and analysis.

        Args:
            event_type: Type of security event
            user_id: User ID involved in event
            details: Event details
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
        """
        log_message = (
            f"SECURITY_EVENT [{severity}] - Type: {event_type}, User: {user_id}, Details: {details}"
        )

        if severity == "CRITICAL":
            logger.critical(log_message)
        elif severity == "ERROR":
            logger.error(log_message)
        elif severity == "WARNING":
            logger.warning(log_message)
        else:
            logger.info(log_message)


# Global instance for easy access
input_validator = InputValidator()


def validate_user_input(
    message_content: str, user_id: str, channel_type: str = "unknown"
) -> dict[str, Any]:
    """
    Convenience function for validating user input.

    Args:
        message_content: Raw message content from user
        user_id: Discord user ID
        channel_type: Type of channel for context

    Returns:
        Validation result dictionary
    """
    return input_validator.validate_and_sanitize(message_content, user_id, channel_type)


def is_safe_admin_command(content: str, user_id: str) -> bool:
    """
    Convenience function for validating admin commands.

    Args:
        content: Command content
        user_id: User ID attempting command

    Returns:
        True if command is safe
    """
    return input_validator.is_admin_command_safe(content, user_id)
