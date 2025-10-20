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

    # Prompt injection patterns - Protect CDL-defined character personality integrity
    # WhisperEngine uses CDL to define character personalities - users cannot override them
    DANGEROUS_PATTERNS = [
        # Explicit system manipulation attempts
        r"\[SYSTEM\s*OVERRIDE\]",
        r"IGNORE\s+(PREVIOUS|ALL|YOUR)\s+(INSTRUCTIONS|PROMPTS?)",
        r"FORGET\s+(PREVIOUS|ALL|YOUR)\s+(INSTRUCTIONS|PROMPTS?)",
        r"DISREGARD\s+(ABOVE|PREVIOUS|EVERYTHING)\s+(INSTRUCTIONS|PROMPTS?)?",
        r"SYSTEM\s*PROMPT\s*INJECTION",
        r"(DAN|STAN|DEVELOPER)\s+MODE",
        r"FOR\s+EDUCATIONAL\s+PURPOSES,?\s+(SHOW|REVEAL|TELL)",
        r"REPEAT\s+AFTER\s+ME:",
        r"WHAT\s+WOULD\s+YOU\s+(SAY|DO)\s+IF\s+I\s+(TOLD|ASKED)\s+YOU\s+TO\s+(IGNORE|FORGET)",
        
        # Character identity manipulation (CRITICAL: Protect CDL-defined personality!)
        # Users CANNOT ask the bot to pretend to be someone else or change character
        r"YOU\s+ARE\s+NOW\s+(A\s+)?(DIFFERENT|NEW|NOT)",
        r"PRETEND\s+(TO\s+BE|YOU\s+ARE|YOU'RE)",
        r"ACT\s+AS\s+(IF\s+)?(YOU\s+ARE|YOU'RE|A\s+)",
        r"ROLEPLAY\s+AS\s+(IF\s+YOU\s+ARE\s+)?",
        r"PLAY\s+THE\s+ROLE\s+OF",
        r"TAKE\s+ON\s+THE\s+(PERSONA|PERSONALITY)\s+OF",
        r"ADOPT\s+THE\s+(PERSONA|PERSONALITY|CHARACTER)\s+OF",
        r"SWITCH\s+TO\s+(CHARACTER|PERSONA)\s+(MODE)?",
        r"FROM\s+NOW\s+ON,?\s+YOU\s+ARE",
        r"CHANGE\s+YOUR\s+(PERSONALITY|CHARACTER|IDENTITY|ROLE|BEHAVIOR)",
        r"BECOME\s+(A\s+)?(DIFFERENT|NEW)?\s*(PERSON|CHARACTER|AI|ASSISTANT)",
        r"BEHAVE\s+(LIKE|AS)\s+(A\s+)?(DIFFERENT|NEW|NOT)",
        r"IMAGINE\s+YOU\s+(ARE|WERE)\s+(A\s+)?(DIFFERENT|NOT\s+\w+|SOMEONE\s+ELSE)",
        r"LET'S\s+PRETEND\s+YOU\s+(ARE|WERE)",
        r"FORGET\s+(YOU'RE|YOU\s+ARE)\s+\w+",
        r"DROP\s+THE\s+(CHARACTER|PERSONA|ACT)",
        r"BREAK\s+(CHARACTER|PERSONA)",
        r"STOP\s+(BEING|ACTING\s+LIKE)\s+(A\s+)?",
        r"(JUST|ONLY)\s+FOR\s+(THIS|NOW|TODAY)",
        r"TEMPORARILY\s+(BE|ACT|PRETEND)",
        
        # Information disclosure attempts (system prompt exfiltration)
        r"REVEAL\s+YOUR\s+SYSTEM\s+(PROMPT|INSTRUCTIONS)",
        r"SHOW\s+(ME\s+)?YOUR\s+(SYSTEM\s+)?(INSTRUCTIONS|SYSTEM\s*PROMPT|CONFIGURATION)",
        r"DISPLAY\s+YOUR\s+SYSTEM\s+(MESSAGE|PROMPT)",
        r"PRINT\s+YOUR\s+(CONFIGURATION|SYSTEM\s*PROMPT)",
        r"WHAT\s+(ARE|IS)\s+YOUR\s+(ACTUAL\s+|REAL\s+)?(SYSTEM\s+)?(INSTRUCTIONS|SYSTEM\s*PROMPT)",
        
        # Prompt injection markers (structural attacks)
        r"\\n\\n###\s*NEW\s*INSTRUCTIONS",
        r"---\s*END\s+OF\s+(CONVERSATION|CHAT|CONTEXT)",
        r"###\s*SYSTEM\s+(MESSAGE|PROMPT)",
        r"\*\*\*\s*IMPORTANT\s*UPDATE",
        r"</?\s*system\s*>",  # XML-style system tag injection
        r"<\|im_start\|>",  # ChatML format injection
        r"<\|im_end\|>",
        r"ROLE:\s*(system|assistant)",  # Role-based injection
        
        # NOTE: Removed SQL, command, and XSS injection patterns - not applicable to WhisperEngine:
        # - Uses SQLAlchemy ORM (SQL-safe by design)
        # - Never executes shell commands from user input
        # - Discord handles HTML rendering (no XSS risk)
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
        logger.info(
            "InputValidator initialized with %d prompt injection patterns "
            "(SQL/command/XSS filters removed - focus on CDL personality protection)",
            len(self.DANGEROUS_PATTERNS)
        )

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
