#!/usr/bin/env python3
"""
Desktop App LLM Integration Manager
Seamlessly integrates local LLM detection and configuration into the desktop app startup process.
"""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DesktopLLMManager:
    """Manages LLM integration for desktop app mode"""

    def __init__(self):
        self.auto_detection_enabled = True
        self.fallback_to_cloud = True
        self.setup_guidance_enabled = True

    async def initialize_llm_for_desktop(self) -> dict[str, Any]:
        """Initialize and configure LLM for desktop app"""
        logger.info("🤖 Initializing LLM for desktop app...")

        result = {
            "status": "unknown",
            "configuration": {},
            "server_info": None,
            "setup_guidance": None,
            "next_steps": [],
        }

        try:
            # Check if user has manually configured LLM
            if self._has_manual_llm_config():
                logger.info("📝 Manual LLM configuration detected")
                result["status"] = "manual_config"
                result["configuration"] = self._get_current_config()
                result["next_steps"] = ["validate_manual_config"]
                return result

            # Auto-detect local LLM servers
            if self.auto_detection_enabled:
                from src.llm.local_server_detector import detect_and_configure_local_llm

                logger.info("🔍 Auto-detecting local LLM servers...")
                detection_result = await detect_and_configure_local_llm()

                if detection_result.get("configuration_applied"):
                    # Found and configured local server
                    server = detection_result["selected_server"]
                    logger.info(f"✅ Local LLM configured: {server.name}")

                    # Apply configuration to environment
                    await self._apply_server_configuration(server)

                    result["status"] = "local_configured"
                    result["server_info"] = server
                    result["configuration"] = {
                        "LLM_CHAT_API_URL": server.url,
                        "LLM_MODEL_NAME": server.models[0] if server.models else "local-llm",
                    }
                    result["next_steps"] = ["test_connection", "ready_for_use"]

                elif detection_result.get("setup_recommendation"):
                    # No local servers found, provide setup guidance
                    recommendation = detection_result["setup_recommendation"]
                    logger.info(f"💡 Setup guidance: {recommendation.preferred_server}")

                    result["status"] = "setup_required"
                    result["setup_guidance"] = recommendation
                    result["next_steps"] = ["show_setup_guidance", "fallback_to_cloud"]

                else:
                    # Detection failed
                    logger.warning("⚠️ LLM detection failed")
                    result["status"] = "detection_failed"
                    result["next_steps"] = ["fallback_to_cloud", "manual_config"]

            # Handle fallback options
            if (
                result["status"] in ["setup_required", "detection_failed"]
                and self.fallback_to_cloud
            ):
                fallback_result = await self._setup_cloud_fallback()
                if fallback_result:
                    result["status"] = "cloud_fallback"
                    result["configuration"].update(fallback_result)
                    result["next_steps"] = ["cloud_setup_guidance"]

            return result

        except Exception as e:
            logger.error(f"❌ LLM initialization failed: {e}")
            result["status"] = "initialization_failed"
            result["error"] = str(e)
            result["next_steps"] = ["manual_config", "contact_support"]
            return result

    def _has_manual_llm_config(self) -> bool:
        """Check if user has manually configured LLM settings"""
        # Check for explicit LLM configuration
        api_url = os.getenv("LLM_CHAT_API_URL")
        api_key = os.getenv("LLM_CHAT_API_KEY")

        # If user set non-default URL or has API key, consider it manual config
        if api_key:  # API key suggests cloud service
            return True
        if api_url and api_url != "http://localhost:1234/v1":  # Non-default URL
            return True

        return False

    def _get_current_config(self) -> dict[str, str]:
        """Get current LLM configuration from environment"""
        return {
            "LLM_CHAT_API_URL": os.getenv("LLM_CHAT_API_URL", ""),
            "LLM_CHAT_API_KEY": os.getenv("LLM_CHAT_API_KEY", ""),
            "LLM_MODEL_NAME": os.getenv("LLM_MODEL_NAME", "local-llm"),
        }

    async def _apply_server_configuration(self, server_info) -> bool:
        """Apply detected server configuration to environment"""
        try:
            # Set environment variables for the detected server
            os.environ["LLM_CHAT_API_URL"] = server_info.url

            # Use first available model or default
            if server_info.models:
                model_name = server_info.models[0]
                # Clean up model name (remove tags like :latest)
                if ":" in model_name:
                    model_name = model_name.split(":")[0]
                os.environ["LLM_MODEL_NAME"] = model_name

            # Clear any API key (local servers don't need them)
            if "LLM_CHAT_API_KEY" in os.environ:
                del os.environ["LLM_CHAT_API_KEY"]

            logger.info(
                f"🔧 Applied configuration: {server_info.url} with model {os.environ.get('LLM_MODEL_NAME')}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to apply server configuration: {e}")
            return False

    async def _setup_cloud_fallback(self) -> dict[str, str] | None:
        """Setup cloud API fallback configuration"""
        # For now, just provide guidance - don't auto-configure cloud APIs
        # as they require user API keys
        logger.info("🌐 Cloud fallback available - setup guidance provided")
        return None

    async def validate_current_configuration(self) -> dict[str, Any]:
        """Validate the current LLM configuration"""
        try:
            from src.llm.llm_client import LLMClient

            logger.info("🔍 Validating current LLM configuration...")

            # Test current configuration
            client = LLMClient()
            is_connected = client.check_connection()

            config_info = client.get_client_config()

            result = {
                "is_valid": is_connected,
                "service_name": config_info.get("service_name", "Unknown"),
                "api_url": config_info.get("api_url", ""),
                "model_name": config_info.get("chat_model", ""),
                "supports_vision": config_info.get("supports_vision", False),
            }

            if is_connected:
                logger.info(f"✅ LLM validation successful: {result['service_name']}")

                # Try a quick test response
                try:
                    test_response = client.get_chat_response(
                        [
                            {
                                "role": "user",
                                "content": "Respond with exactly: 'LLM connection test successful'",
                            }
                        ]
                    )
                    result["test_response"] = test_response
                    result["response_test_passed"] = "successful" in test_response.lower()
                except Exception as e:
                    result["response_test_passed"] = False
                    result["response_test_error"] = str(e)
            else:
                logger.warning(f"❌ LLM validation failed: {result['service_name']} not reachable")

            return result

        except Exception as e:
            logger.error(f"❌ Configuration validation error: {e}")
            return {"is_valid": False, "error": str(e), "service_name": "Validation Failed"}

    def get_setup_guidance_for_ui(self, setup_recommendation) -> dict[str, Any]:
        """Format setup guidance for display in desktop app UI"""
        if not setup_recommendation:
            return {}

        return {
            "title": f"Set up {setup_recommendation.preferred_server} for Local AI",
            "description": setup_recommendation.memory_note,
            "recommended_models": setup_recommendation.recommended_models,
            "setup_url": setup_recommendation.setup_url,
            "steps": setup_recommendation.installation_steps,
            "benefits": [
                "🔒 Complete privacy - no data sent to cloud",
                "⚡ Fast responses - no internet required",
                "💰 No API costs - run unlimited conversations",
                "🎛️ Full control - choose your preferred models",
            ],
        }

    async def auto_refresh_configuration(self) -> bool:
        """Periodically refresh LLM server detection"""
        try:
            # Re-run detection to catch newly started servers
            from src.llm.local_server_detector import detect_and_configure_local_llm

            current_url = os.getenv("LLM_CHAT_API_URL", "")
            detection_result = await detect_and_configure_local_llm()

            if detection_result.get("configuration_applied"):
                server = detection_result["selected_server"]
                new_url = server.url

                # Only update if we found a better/different server
                if new_url != current_url:
                    logger.info(f"🔄 Updated LLM configuration: {server.name}")
                    await self._apply_server_configuration(server)
                    return True

            return False

        except Exception as e:
            logger.debug(f"Auto-refresh failed: {e}")
            return False


# Factory function for easy integration
async def initialize_desktop_llm() -> dict[str, Any]:
    """Initialize LLM for desktop app - convenience function"""
    manager = DesktopLLMManager()
    return await manager.initialize_llm_for_desktop()


async def configure_llamacpp_for_desktop() -> dict[str, Any]:
    """Configure llama-cpp-python for desktop app"""
    logger.info("🔧 Configuring llama-cpp-python for desktop app...")

    result = {
        "status": "not_configured",
        "model_path": None,
        "auto_detected": False,
        "instructions": [],
    }

    try:
        # Check for GGUF models in models directory
        models_dir = Path("./models")
        if models_dir.exists():
            gguf_files = list(models_dir.glob("*.gguf"))
            if gguf_files:
                model_path = str(gguf_files[0])
                logger.info(f"🎯 Auto-detected GGUF model: {model_path}")

                # Configure environment
                os.environ["LLM_CHAT_API_URL"] = "llamacpp://local"
                os.environ["LLAMACPP_MODEL_PATH"] = model_path

                result["status"] = "configured"
                result["model_path"] = model_path
                result["auto_detected"] = True
                result["instructions"] = [
                    f"Configured llama-cpp-python with {model_path}",
                    "Ready to use for local AI inference",
                ]

                return result

        # No models found, provide setup instructions
        result["status"] = "setup_needed"
        result["instructions"] = [
            "No GGUF models found. To use llama-cpp-python:",
            "1. Create models directory: mkdir -p ./models",
            "2. Download a GGUF model (e.g., from HuggingFace)",
            "3. Place the .gguf file in ./models/",
            "4. Restart the application",
            "",
            "Example download commands:",
            "wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
            "mv Phi-3-mini-4k-instruct-q4.gguf ./models/",
            "",
            "Benefits of llama-cpp-python:",
            "- Faster inference than PyTorch",
            "- Lower memory usage",
            "- Better CPU performance",
            "- No internet required",
        ]

    except Exception as e:
        logger.error(f"❌ Failed to configure llama-cpp-python: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result


# Validation function for UI
async def validate_desktop_llm() -> dict[str, Any]:
    """Validate current LLM configuration - convenience function"""
    manager = DesktopLLMManager()
    return await manager.validate_current_configuration()
