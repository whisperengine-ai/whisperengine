#!/usr/bin/env python3
"""
LLM Configuration Validator
Validates and reports the effective LLM configuration for WhisperEngine
"""

import os
import logging
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMConfigStatus:
    """Status of LLM configuration"""

    is_valid: bool
    source: str  # 'user_override', 'auto_detected', 'invalid'
    api_url: Optional[str]
    model: Optional[str]
    has_api_key: bool
    backend_name: str
    issues: List[str]
    recommendations: List[str]


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
            # Try auto-detection
            try:
                from src.llm.smart_backend_selector import get_smart_backend_selector

                selector = get_smart_backend_selector()
                optimal_backend = selector.get_optimal_backend()

                if optimal_backend:
                    source = "auto_detected"
                    backend_name = optimal_backend.name
                    config = selector.get_backend_config(optimal_backend)
                    effective_url = config.get("LLM_CHAT_API_URL")

                    if not effective_url:
                        issues.append("Auto-detection failed to provide valid URL")

                else:
                    source = "invalid"
                    backend_name = "None Available"
                    effective_url = None
                    issues.append("No suitable LLM backend found")
                    recommendations.extend(selector.get_setup_recommendations())

            except ImportError as e:
                source = "invalid"
                backend_name = "Detection Failed"
                effective_url = None
                issues.append(f"Backend auto-detection not available: {str(e)}")
                recommendations.append("Install smart backend selector dependencies")
            except (AttributeError, RuntimeError, OSError) as e:
                source = "invalid"
                backend_name = "Detection Failed"
                effective_url = None
                issues.append(f"Backend auto-detection failed: {str(e)}")
                recommendations.append("Manual configuration required")

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
        elif "mlx://" in url_lower:
            return "MLX"
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

        # Special schemes
        if url.startswith(("mlx://", "llamacpp://", "local://")):
            return True

        # HTTP/HTTPS URLs
        if url.startswith(("http://", "https://")):
            return True

        return False

    def print_configuration_report(self):
        """Print a detailed configuration report"""
        config = self.validate_configuration()

        print("🔧 WhisperEngine LLM Configuration Report")
        print("=" * 50)

        # Status
        status_icon = "✅" if config.is_valid else "❌"
        print(f"{status_icon} Status: {'Valid' if config.is_valid else 'Invalid'}")
        print(f"📍 Source: {config.source}")
        print(f"🔗 Backend: {config.backend_name}")

        # Configuration details
        if config.api_url:
            print(f"🌐 API URL: {config.api_url}")
        else:
            print("🌐 API URL: Not configured")

        if config.model:
            print(f"🤖 Model: {config.model}")
        else:
            print("🤖 Model: Not specified")

        print(f"🔑 API Key: {'Configured' if config.has_api_key else 'Not set'}")

        # Issues
        if config.issues:
            print("\n⚠️ Issues:")
            for issue in config.issues:
                print(f"   - {issue}")

        # Recommendations
        if config.recommendations:
            print("\n💡 Recommendations:")
            for rec in config.recommendations:
                print(f"   - {rec}")

        # Override instructions
        print("\n🔧 User Override Variables:")
        print("   LLM_CHAT_API_URL - Primary API endpoint URL")
        print("   LLM_BASE_URL - Alternative base URL setting")
        print("   LLM_CHAT_API_KEY - API authentication key")
        print("   LLM_CHAT_MODEL - Specific model name")
        print("\nSet any of these environment variables to override auto-detection.")


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
