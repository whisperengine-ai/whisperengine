#!/usr/bin/env python3
"""
API Key Management Security Module
Addresses CVSS 6.7 - API Key and Credential Management Issues

This module provides secure API key handling, validation, and management
to prevent credential exposure and enhance security.
"""

import hashlib
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class APIKeyType(Enum):
    """Types of API keys supported"""

    DISCORD_BOT = "discord_bot"
    OPENROUTER = "openrouter"
    ELEVENLABS = "elevenlabs"
    LLM_SENTIMENT = "llm_sentiment"
    UNKNOWN = "unknown"


class SecurityThreat(Enum):
    """API key security threats"""

    INVALID_FORMAT = "invalid_format"
    WEAK_KEY = "weak_key"
    EXPIRED_KEY = "expired_key"
    LOGGED_KEY = "logged_key"
    EXPOSED_KEY = "exposed_key"


@dataclass
class APIKeyInfo:
    """Information about an API key"""

    key_type: APIKeyType
    masked_key: str
    is_valid: bool
    format_score: float
    security_threats: list[SecurityThreat]
    last_validated: datetime | None = None
    validation_attempts: int = 0


class APIKeySecurityManager:
    """
    Secure API key management with validation, masking, and threat detection
    """

    def __init__(self):
        """Initialize the API key security manager"""
        self.key_cache: dict[str, APIKeyInfo] = {}
        self.security_events: list[dict[str, Any]] = []

        # API key format patterns for validation
        self.key_patterns = {
            APIKeyType.DISCORD_BOT: [
                r"^[A-Za-z0-9_-]{59}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{38}$",  # Standard Discord bot token
                r"^[A-Za-z0-9_-]{24}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{39}$",  # Alternative format
            ],
            APIKeyType.OPENROUTER: [
                r"^sk-or-v1-[a-f0-9]{64}$",  # OpenRouter API key format
                r"^sk-[A-Za-z0-9]{48}$",  # Alternative OpenAI-like format
            ],
            APIKeyType.ELEVENLABS: [
                r"^[a-f0-9]{32}$",  # ElevenLabs API key format
                r"^[A-Za-z0-9]{32}$",  # Alternative alphanumeric format
            ],
            APIKeyType.LLM_SENTIMENT: [
                r"^sk-[A-Za-z0-9]{48}$",  # Generic LLM API key
                r"^[A-Za-z0-9_-]{32,}$",  # Generic format
            ],
        }

        # Dangerous patterns that might indicate placeholder/example keys
        self.placeholder_patterns = [
            r"^your_.*_key_here$",
            r"^your_.*_token_here$",
            r"^example_key$",
            r"^test_key$",
            r"^demo_key$",
            r"^placeholder$",
            r"^xxx+$",
            r"^abc123$",
            r"^123456$",
            r"^password$",
            r"^secret$",
        ]

        # Patterns that might appear in logs that should be masked
        self.sensitive_patterns = [
            r'(api.?key[:=]\s*["\']?)([A-Za-z0-9_.-]{8,})(["\']?)',
            r"(authorization[:=]\s*bearer\s+)([A-Za-z0-9_.-]{8,})",
            r'(token[:=]\s*["\']?)([A-Za-z0-9_.-]{8,})(["\']?)',
            r'(xi-api-key[:=]\s*["\']?)([A-Za-z0-9_.-]{8,})(["\']?)',
            r"(sk-[A-Za-z0-9_.-]{6,})",  # OpenAI/OpenRouter style keys (standalone)
            r'(OPENROUTER_API_KEY[:=]\s*["\']?)([A-Za-z0-9_.-]{8,})(["\']?)',
            r'(ELEVENLABS_API_KEY[:=]\s*["\']?)([A-Za-z0-9_.-]{8,})(["\']?)',
        ]

    def validate_api_key(self, key: str, key_type: APIKeyType = APIKeyType.UNKNOWN) -> APIKeyInfo:
        """
        Validate an API key for format, security, and authenticity

        Args:
            key: The API key to validate
            key_type: Type of API key (if known)

        Returns:
            APIKeyInfo with validation results
        """
        if not key or not isinstance(key, str):
            return APIKeyInfo(
                key_type=key_type,
                masked_key="[EMPTY_KEY]",
                is_valid=False,
                format_score=0.0,
                security_threats=[SecurityThreat.INVALID_FORMAT],
            )

        # Create masked version for safe logging
        masked_key = self.mask_api_key(key)

        # Detect key type if unknown
        if key_type == APIKeyType.UNKNOWN:
            key_type = self.detect_key_type(key)

        # Check for security threats
        threats = self.scan_key_threats(key)

        # Calculate format score
        format_score = self.calculate_format_score(key, key_type)

        # Determine if key is valid
        is_valid = (
            format_score >= 0.7
            and SecurityThreat.INVALID_FORMAT not in threats
            and SecurityThreat.WEAK_KEY not in threats
        )

        # Create key info
        key_info = APIKeyInfo(
            key_type=key_type,
            masked_key=masked_key,
            is_valid=is_valid,
            format_score=format_score,
            security_threats=threats,
            last_validated=datetime.now(),
            validation_attempts=1,
        )

        # Cache the result (using hash to avoid storing actual key)
        key_hash = self._hash_key(key)
        self.key_cache[key_hash] = key_info

        # Log security event
        self.security_events.append(
            {
                "type": "api_key_validation",
                "key_type": key_type.value,
                "masked_key": masked_key,
                "is_valid": is_valid,
                "format_score": format_score,
                "threats": [t.value for t in threats],
                "timestamp": datetime.now().isoformat(),
            }
        )

        if not is_valid:
            logger.warning(
                f"API key validation failed: {masked_key} - Threats: {[t.value for t in threats]}"
            )
        else:
            logger.debug(f"API key validated successfully: {masked_key}")

        return key_info

    def mask_api_key(self, key: str) -> str:
        """
        Create a masked version of API key for safe logging

        Args:
            key: The API key to mask

        Returns:
            Masked version of the key
        """
        if not key or len(key) < 8:
            return "[INVALID_KEY]"

        # Show first 4 and last 4 characters, mask the middle
        if len(key) <= 12:
            return f"{key[:2]}{'*' * (len(key) - 4)}{key[-2:]}"
        else:
            middle_length = len(key) - 8
            return f"{key[:4]}{'*' * min(middle_length, 20)}{key[-4:]}"

    def detect_key_type(self, key: str) -> APIKeyType:
        """
        Detect the type of API key based on format patterns

        Args:
            key: The API key to analyze

        Returns:
            Detected key type
        """
        for key_type, patterns in self.key_patterns.items():
            for pattern in patterns:
                if re.match(pattern, key, re.IGNORECASE):
                    return key_type

        return APIKeyType.UNKNOWN

    def scan_key_threats(self, key: str) -> list[SecurityThreat]:
        """
        Scan API key for security threats

        Args:
            key: The API key to scan

        Returns:
            List of detected security threats
        """
        threats = []

        # Check for placeholder patterns
        for pattern in self.placeholder_patterns:
            if re.search(pattern, key, re.IGNORECASE):
                threats.append(SecurityThreat.WEAK_KEY)
                break

        # Check minimum length and complexity
        if len(key) < 20:
            threats.append(SecurityThreat.WEAK_KEY)

        # Check for obvious weak patterns
        unique_chars = len(set(key.lower()))

        if (
            key.lower() in ["test", "demo", "example", "placeholder"]
            or re.match(r"^[0-9]+$", key)  # All numbers
            or re.match(r"^[a-z]+$", key)  # All lowercase letters only
            or re.match(r"^[A-Z]+$", key)  # All uppercase letters only
            or (len(key) > 32 and unique_chars < 8)  # Very few unique characters in long keys
            or (len(key) <= 32 and unique_chars < 5)
        ):  # Few unique characters in shorter keys
            threats.append(SecurityThreat.WEAK_KEY)

        # Check for invalid format (basic validation)
        if not re.match(r"^[A-Za-z0-9_.-]+$", key):
            threats.append(SecurityThreat.INVALID_FORMAT)

        return threats

    def calculate_format_score(self, key: str, key_type: APIKeyType) -> float:
        """
        Calculate a format score for the API key (0.0 to 1.0)

        Args:
            key: The API key to score
            key_type: Type of the key

        Returns:
            Format score (higher is better)
        """
        score = 0.0

        # Check length
        if len(key) >= 20:
            score += 0.3
        if len(key) >= 32:
            score += 0.2

        # Check character diversity
        char_types = 0
        if re.search(r"[a-z]", key):
            char_types += 1
        if re.search(r"[A-Z]", key):
            char_types += 1
        if re.search(r"[0-9]", key):
            char_types += 1
        if re.search(r"[_.-]", key):
            char_types += 1

        score += char_types * 0.1

        # Check format pattern match
        if key_type != APIKeyType.UNKNOWN:
            patterns = self.key_patterns.get(key_type, [])
            for pattern in patterns:
                if re.match(pattern, key):
                    score += 0.3
                    break

        return min(score, 1.0)

    def sanitize_for_logging(self, text: str) -> str:
        """
        Sanitize text to remove API keys before logging

        Args:
            text: Text that might contain API keys

        Returns:
            Sanitized text with API keys masked
        """
        sanitized = text

        for pattern in self.sensitive_patterns:

            def mask_match(match):
                # Handle different pattern structures
                if match.lastindex == 1:
                    # Pattern like (sk-[A-Za-z0-9_.-]{8,})
                    key = match.group(1)
                    return self.mask_api_key(key) if key else "[REDACTED]"
                elif match.lastindex >= 2:
                    # Pattern like (prefix)(key)(suffix)
                    prefix = match.group(1) if match.lastindex >= 1 else ""
                    key = match.group(2) if match.lastindex >= 2 else ""
                    suffix = match.group(3) if match.lastindex >= 3 else ""

                    # Mask the key part
                    masked_key = self.mask_api_key(key) if key else "[REDACTED]"
                    return f"{prefix}{masked_key}{suffix}"
                else:
                    return "[REDACTED]"

            sanitized = re.sub(pattern, mask_match, sanitized, flags=re.IGNORECASE)

        return sanitized

    def validate_environment_keys(self) -> dict[str, APIKeyInfo]:
        """
        Validate all API keys found in environment variables

        Returns:
            Dictionary mapping env var names to validation results
        """
        env_keys = {
            "DISCORD_BOT_TOKEN": APIKeyType.DISCORD_BOT,
            "OPENROUTER_API_KEY": APIKeyType.OPENROUTER,
            "ELEVENLABS_API_KEY": APIKeyType.ELEVENLABS,
            "LLM_SENTIMENT_API_KEY": APIKeyType.LLM_SENTIMENT,
        }

        results = {}

        for env_var, key_type in env_keys.items():
            key_value = os.getenv(env_var)
            if key_value:
                results[env_var] = self.validate_api_key(key_value, key_type)
            else:
                results[env_var] = APIKeyInfo(
                    key_type=key_type,
                    masked_key="[NOT_SET]",
                    is_valid=False,
                    format_score=0.0,
                    security_threats=[SecurityThreat.INVALID_FORMAT],
                )

        return results

    def secure_header_creation(self, api_key: str, header_type: str = "Bearer") -> dict[str, str]:
        """
        Securely create authorization headers with validation

        Args:
            api_key: The API key to use
            header_type: Type of authorization header ("Bearer", "xi-api-key", etc.)

        Returns:
            Dictionary with authorization headers
        """
        if not api_key:
            logger.error("Attempted to create auth header with empty API key")
            return {}

        # Validate the key first
        key_info = self.validate_api_key(api_key)

        if not key_info.is_valid:
            logger.error(f"Attempted to use invalid API key: {key_info.masked_key}")
            return {}

        # Create appropriate header based on type
        if header_type.lower() == "bearer":
            return {"Authorization": f"Bearer {api_key}"}
        elif header_type.lower() == "xi-api-key":
            return {"xi-api-key": api_key}
        else:
            logger.warning(f"Unknown header type: {header_type}")
            return {"Authorization": f"{header_type} {api_key}"}

    def get_security_report(self) -> dict[str, Any]:
        """
        Get a comprehensive security report for API key management

        Returns:
            Dictionary containing security report
        """
        env_validation = self.validate_environment_keys()

        total_keys = len(env_validation)
        valid_keys = sum(1 for info in env_validation.values() if info.is_valid)
        invalid_keys = total_keys - valid_keys

        # Count threat types
        threat_counts = {}
        for info in env_validation.values():
            for threat in info.security_threats:
                threat_counts[threat.value] = threat_counts.get(threat.value, 0) + 1

        return {
            "summary": {
                "total_keys_checked": total_keys,
                "valid_keys": valid_keys,
                "invalid_keys": invalid_keys,
                "security_score": (valid_keys / total_keys * 100) if total_keys > 0 else 0,
            },
            "key_status": {
                env_var: {
                    "type": info.key_type.value,
                    "masked_key": info.masked_key,
                    "is_valid": info.is_valid,
                    "format_score": info.format_score,
                    "threats": [t.value for t in info.security_threats],
                }
                for env_var, info in env_validation.items()
            },
            "threat_analysis": threat_counts,
            "recommendations": self._generate_security_recommendations(env_validation),
            "recent_events": self.security_events[-10:],  # Last 10 events
        }

    def _generate_security_recommendations(
        self, env_validation: dict[str, APIKeyInfo]
    ) -> list[str]:
        """Generate security recommendations based on validation results"""
        recommendations = []

        for env_var, info in env_validation.items():
            if not info.is_valid:
                if info.masked_key == "[NOT_SET]":
                    recommendations.append(
                        f"Set {env_var} environment variable with a valid API key"
                    )
                elif SecurityThreat.WEAK_KEY in info.security_threats:
                    recommendations.append(
                        f"Replace weak {env_var} with a proper API key (not placeholder)"
                    )
                elif SecurityThreat.INVALID_FORMAT in info.security_threats:
                    recommendations.append(f"Fix invalid format for {env_var}")
            elif info.format_score < 0.8:
                recommendations.append(f"Consider regenerating {env_var} for better security")

        if not recommendations:
            recommendations.append("All API keys appear to be properly configured")

        return recommendations

    def _hash_key(self, key: str) -> str:
        """Create a hash of the key for caching purposes"""
        return hashlib.sha256(key.encode()).hexdigest()


# Global instance for use throughout the application
_api_key_manager = None


def get_api_key_manager() -> APIKeySecurityManager:
    """Get or create the global API key manager instance"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeySecurityManager()
    return _api_key_manager


def validate_api_key(key: str, key_type: APIKeyType = APIKeyType.UNKNOWN) -> APIKeyInfo:
    """Convenience function to validate an API key"""
    manager = get_api_key_manager()
    return manager.validate_api_key(key, key_type)


def mask_api_key(key: str) -> str:
    """Convenience function to mask an API key"""
    manager = get_api_key_manager()
    return manager.mask_api_key(key)


def sanitize_for_logging(text: str) -> str:
    """Convenience function to sanitize text for logging"""
    manager = get_api_key_manager()
    return manager.sanitize_for_logging(text)


def secure_headers(api_key: str, header_type: str = "Bearer") -> dict[str, str]:
    """Convenience function to create secure headers"""
    manager = get_api_key_manager()
    return manager.secure_header_creation(api_key, header_type)


if __name__ == "__main__":
    # Test the API key security manager
    manager = APIKeySecurityManager()

    # Test various key validation scenarios
    test_keys = [
        (
            "sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            APIKeyType.OPENROUTER,
        ),
        ("your_openrouter_api_key_here", APIKeyType.OPENROUTER),
        ("abcdef1234567890abcdef1234567890ab", APIKeyType.ELEVENLABS),
        ("test_key", APIKeyType.UNKNOWN),
        ("", APIKeyType.UNKNOWN),
    ]


    for key, key_type in test_keys:
        result = manager.validate_api_key(key, key_type)

    # Test environment validation
    report = manager.get_security_report()

    for _env_var, _status in report["key_status"].items():
        pass

    for _rec in report["recommendations"]:
        pass
