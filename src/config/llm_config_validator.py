#!/usr/bin/env python3
"""
LLM Configuration Validator
Validates and reports the effective LLM configuration for WhisperEngine
"""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMConfigStatus:
    """Status of LLM configuration"""

    is_valid: bool
    source: str  # 'user_override', 'auto_detected', 'invalid'
    api_url: str | None
    model: str | None
    has_api_key: bool
    backend_name: str
    issues: list[str]
    recommendations: list[str]


class LLMConfigValidator:
    """Validates LLM configuration and provides recommendations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_configuration(self) -> LLMConfigStatus:
        """Validate the current LLM configuration"""
        issues = []
        recommendations = []

        # Check for user overrides
        user_url = os.getenv("LLM_CHAT_API_URL")
        user_base_url = os.getenv("LLM_BASE_URL")
        user_key = os.getenv("LLM_CHAT_API_KEY")
        user_model = os.getenv("LLM_CHAT_MODEL")

        # Determine effective URL
        effective_url = user_url or user_base_url

        if effective_url:
            # User has configured URL
            source = "user_override"
            backend_name = self._detect_backend_from_url(effective_url)

            # Validate user configuration
            if not self._is_valid_url(effective_url):
                issues.append(f"Invalid API URL format: {effective_url}")

            if "openrouter" in effective_url.lower() and not user_key:
                issues.append("OpenRouter API requires an API key")
                recommendations.append("Set LLM_CHAT_API_KEY environment variable")

            if not user_model:
                issues.append("No model specified")
                recommendations.append("Set LLM_CHAT_MODEL environment variable")

        else:
            # Use simple direct configuration check (no backend selector needed)
            # WhisperEngine uses OpenRouter API directly
            source = "direct_config"
            backend_name = "OpenRouter/Direct API"
            effective_url = os.getenv("LLM_CHAT_API_URL", "https://openrouter.ai/api/v1")
            
            if not effective_url:
                issues.append("No LLM API URL configured")
                recommendations.append("Set LLM_CHAT_API_URL environment variable")
            
            api_key = os.getenv("LLM_CHAT_API_KEY")
            if not api_key:
                issues.append("No LLM API key configured")
                recommendations.append("Set LLM_CHAT_API_KEY environment variable")

        # Final validation
        is_valid = len(issues) == 0 and effective_url is not None

        return LLMConfigStatus(
            is_valid=is_valid,
            source=source,
            api_url=effective_url,
            model=user_model,
            has_api_key=bool(user_key),
            backend_name=backend_name,
            issues=issues,
            recommendations=recommendations,
        )

    def _detect_backend_from_url(self, url: str) -> str:
        """Detect backend type from URL"""
        url_lower = url.lower()

        if "openrouter" in url_lower:
            return "OpenRouter"
        elif "localhost:1234" in url_lower or "127.0.0.1:1234" in url_lower:
            return "LM Studio"
        elif "localhost:11434" in url_lower or "127.0.0.1:11434" in url_lower:
            return "Ollama"
        elif "openai.com" in url_lower:
            return "OpenAI"
        elif "anthropic.com" in url_lower:
            return "Anthropic"
        # MLX backend disabled until implementation is complete
        # elif "mlx://" in url_lower:
        #     return "MLX"
        elif "llamacpp://" in url_lower:
            return "llama-cpp-python"
        elif "local://" in url_lower:
            return "Transformers"
        else:
            return "Custom API"

    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        if not url:
            return False

        # Special schemes (MLX disabled until backend implementation)
        if url.startswith(("llamacpp://", "local://")):
            return True

        # HTTP/HTTPS URLs
        if url.startswith(("http://", "https://")):
            return True

        return False

    def print_configuration_report(self):
        """Print a detailed configuration report"""
        config = self.validate_configuration()

        # Status

        # Configuration details
        if config.api_url:
            pass
        else:
            pass

        if config.model:
            pass
        else:
            pass

        # Issues
        if config.issues:
            for _issue in config.issues:
                pass

        # Recommendations
        if config.recommendations:
            for _rec in config.recommendations:
                pass

        # Override instructions


def validate_llm_config() -> LLMConfigStatus:
    """Convenience function to validate LLM configuration"""
    validator = LLMConfigValidator()
    return validator.validate_configuration()


def print_llm_config_report():
    """Convenience function to print configuration report"""
    validator = LLMConfigValidator()
    validator.print_configuration_report()


if __name__ == "__main__":
    # Command-line usage
    print_llm_config_report()
