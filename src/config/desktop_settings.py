#!/usr/bin/env python3
"""
Desktop App Settings Manager
Manages user settings for system prompt, LLM configuration, and Discord bot settings.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class DesktopSettingsManager:
    """Manages desktop app user settings with persistence"""

    def __init__(self):
        self.settings_dir = Path.home() / ".whisperengine"
        self.settings_file = self.settings_dir / "desktop_settings.json"
        self.system_prompts_dir = self.settings_dir / "system_prompts"

        # Ensure directories exist
        self.settings_dir.mkdir(exist_ok=True)
        self.system_prompts_dir.mkdir(exist_ok=True)

        # Default settings
        self.default_settings = {
            "system_prompt": {
                "active_prompt": "default",
                "custom_prompts": {},
                "prompt_source": "built-in",  # built-in, custom, uploaded
            },
            "llm_config": {
                "api_url": "",
                "api_key": "",
                "model_name": "",
                "available_models": [],
                "last_validated": None,
                "validation_status": "unchecked",
            },
            "discord_config": {
                "bot_token": "",
                "last_validated": None,
                "validation_status": "unchecked",
            },
            "ui_preferences": {"auto_save": True, "show_advanced": False, "theme": "auto"},
            "version": "1.0.0",
            "last_updated": None,
        }

        # Load existing settings
        self.settings = self.load_settings()

    def load_settings(self) -> dict[str, Any]:
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file) as f:
                    loaded_settings = json.load(f)

                # Merge with defaults to handle new settings
                settings = self.default_settings.copy()
                self._deep_update(settings, loaded_settings)

                logger.info("Settings loaded successfully")
                return settings
            else:
                logger.info("No existing settings found, using defaults")
                return self.default_settings.copy()

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return self.default_settings.copy()

    def save_settings(self) -> bool:
        """Save settings to file"""
        try:
            self.settings["last_updated"] = datetime.now().isoformat()

            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=2)

            logger.info("Settings saved successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def _deep_update(self, base_dict: dict, update_dict: dict):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    # System Prompt Management
    def get_system_prompt_config(self) -> dict[str, Any]:
        """Get system prompt configuration"""
        return self.settings["system_prompt"].copy()

    def get_active_system_prompt(self) -> str:
        """Get the currently active system prompt text"""
        config = self.settings["system_prompt"]
        source = config["prompt_source"]
        active_prompt = config["active_prompt"]

        if source == "built-in":
            return self._get_built_in_prompt()
        elif source == "custom" and active_prompt in config["custom_prompts"]:
            return config["custom_prompts"][active_prompt]
        elif source == "uploaded":
            return self._load_uploaded_prompt(active_prompt)
        else:
            # Fallback to built-in
            return self._get_built_in_prompt()

    def _get_built_in_prompt(self) -> str:
        """Get built-in system prompt"""
        try:
            prompt_file = Path(__file__).parent.parent.parent / "prompts" / "default.md"
            if prompt_file.exists():
                return prompt_file.read_text()
            else:
                return """You are WhisperEngine, an advanced AI conversation platform with emotional intelligence and memory capabilities.

You are running in desktop app mode, providing:
- 🔒 Local privacy with SQLite storage
- 🧠 Advanced memory networks
- 💭 Emotional intelligence
- 🖥️ Native desktop integration

Be helpful, engaging, and demonstrate your advanced capabilities. Keep responses conversational but informative."""
        except Exception as e:
            logger.error(f"Failed to load built-in prompt: {e}")
            return "You are WhisperEngine, a helpful AI assistant."

    def save_custom_prompt(self, name: str, content: str) -> bool:
        """Save a custom system prompt"""
        try:
            self.settings["system_prompt"]["custom_prompts"][name] = content
            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to save custom prompt: {e}")
            return False

    def upload_prompt_file(self, filename: str, content: str) -> bool:
        """Save uploaded prompt file"""
        try:
            prompt_file = self.system_prompts_dir / filename
            prompt_file.write_text(content)

            self.settings["system_prompt"]["active_prompt"] = filename
            self.settings["system_prompt"]["prompt_source"] = "uploaded"

            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to upload prompt file: {e}")
            return False

    def _load_uploaded_prompt(self, filename: str) -> str:
        """Load uploaded prompt file"""
        try:
            prompt_file = self.system_prompts_dir / filename
            if prompt_file.exists():
                return prompt_file.read_text()
            else:
                logger.warning(f"Uploaded prompt file not found: {filename}")
                return self._get_built_in_prompt()
        except Exception as e:
            logger.error(f"Failed to load uploaded prompt: {e}")
            return self._get_built_in_prompt()

    def set_active_prompt(self, source: str, prompt_name: str) -> bool:
        """Set the active system prompt"""
        try:
            self.settings["system_prompt"]["prompt_source"] = source
            self.settings["system_prompt"]["active_prompt"] = prompt_name
            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to set active prompt: {e}")
            return False

    def delete_custom_prompt(self, name: str) -> bool:
        """Delete a custom prompt"""
        try:
            if name in self.settings["system_prompt"]["custom_prompts"]:
                del self.settings["system_prompt"]["custom_prompts"][name]

                # If this was the active prompt, switch to built-in
                if (
                    self.settings["system_prompt"]["prompt_source"] == "custom"
                    and self.settings["system_prompt"]["active_prompt"] == name
                ):
                    self.settings["system_prompt"]["prompt_source"] = "built-in"
                    self.settings["system_prompt"]["active_prompt"] = "default"

                return self.save_settings()
            return False
        except Exception as e:
            logger.error(f"Failed to delete custom prompt: {e}")
            return False

    def get_uploaded_prompts(self) -> list[str]:
        """Get list of uploaded prompt files"""
        try:
            return [f.name for f in self.system_prompts_dir.glob("*.txt") if f.is_file()]
        except Exception as e:
            logger.error(f"Failed to get uploaded prompts: {e}")
            return []

    # LLM Configuration Management
    def get_llm_config(self) -> dict[str, Any]:
        """Get LLM configuration"""
        return self.settings["llm_config"].copy()

    def set_llm_config(self, api_url: str, api_key: str, model_name: str = "") -> bool:
        """Set LLM configuration"""
        try:
            self.settings["llm_config"]["api_url"] = api_url
            self.settings["llm_config"]["api_key"] = api_key
            self.settings["llm_config"]["model_name"] = model_name
            self.settings["llm_config"]["validation_status"] = "unchecked"

            # Apply to environment for immediate use
            if api_url:
                os.environ["LLM_CHAT_API_URL"] = api_url
            if api_key:
                os.environ["LLM_API_KEY"] = api_key
            if model_name:
                os.environ["LLM_MODEL_NAME"] = model_name

            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to set LLM config: {e}")
            return False

    async def validate_llm_config(self) -> dict[str, Any]:
        """Validate LLM configuration and fetch available models"""
        config = self.settings["llm_config"]
        api_url = config["api_url"]
        api_key = config["api_key"]

        result = {"valid": False, "models": [], "error": None, "endpoint_info": {}}

        if not api_url:
            result["error"] = "API URL is required"
            return result

        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            # Try to fetch models
            models_url = api_url.rstrip("/") + "/models"

            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(models_url, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Handle different API response formats
                        if "data" in data and isinstance(data["data"], list):
                            # OpenAI-style format
                            models = [model.get("id", "") for model in data["data"]]
                        elif "models" in data:
                            # Some APIs use "models" key
                            models = data["models"]
                        elif isinstance(data, list):
                            # Direct list of models
                            models = [str(model) for model in data]
                        else:
                            models = []

                        result["valid"] = True
                        result["models"] = models
                        result["endpoint_info"] = {
                            "status": response.status,
                            "headers": dict(response.headers),
                        }

                        # Update settings
                        self.settings["llm_config"]["available_models"] = models
                        self.settings["llm_config"]["validation_status"] = "valid"
                        self.settings["llm_config"]["last_validated"] = datetime.now().isoformat()

                    else:
                        result["error"] = f"HTTP {response.status}: {await response.text()}"

        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)}"
        except Exception as e:
            result["error"] = f"Validation error: {str(e)}"

        # Update validation status
        if result["error"]:
            self.settings["llm_config"]["validation_status"] = "invalid"

        self.save_settings()
        return result

    # Discord Configuration Management
    def get_discord_config(self) -> dict[str, Any]:
        """Get Discord configuration"""
        return self.settings["discord_config"].copy()

    def set_discord_token(self, token: str) -> bool:
        """Set Discord bot token"""
        try:
            self.settings["discord_config"]["bot_token"] = token
            self.settings["discord_config"]["validation_status"] = "unchecked"

            # Apply to environment
            if token:
                os.environ["DISCORD_BOT_TOKEN"] = token

            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to set Discord token: {e}")
            return False

    async def validate_discord_token(self) -> dict[str, Any]:
        """Validate Discord bot token"""
        token = self.settings["discord_config"]["bot_token"]

        result = {"valid": False, "bot_info": {}, "error": None}

        if not token:
            result["error"] = "Discord bot token is required"
            return result

        try:
            headers = {"Authorization": f"Bot {token}"}

            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(
                    "https://discord.com/api/v10/users/@me", headers=headers, timeout=timeout
                ) as response:
                    if response.status == 200:
                        bot_info = await response.json()
                        result["valid"] = True
                        result["bot_info"] = {
                            "username": bot_info.get("username"),
                            "id": bot_info.get("id"),
                            "verified": bot_info.get("verified", False),
                        }

                        self.settings["discord_config"]["validation_status"] = "valid"
                        self.settings["discord_config"][
                            "last_validated"
                        ] = datetime.now().isoformat()

                    else:
                        result["error"] = f"HTTP {response.status}: Invalid token"

        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)}"
        except Exception as e:
            result["error"] = f"Validation error: {str(e)}"

        # Update validation status
        if result["error"]:
            self.settings["discord_config"]["validation_status"] = "invalid"

        self.save_settings()
        return result

    # UI Preferences
    def get_ui_preferences(self) -> dict[str, Any]:
        """Get UI preferences"""
        return self.settings["ui_preferences"].copy()

    def set_ui_preference(self, key: str, value: Any) -> bool:
        """Set a UI preference"""
        try:
            self.settings["ui_preferences"][key] = value
            return self.save_settings()
        except Exception as e:
            logger.error(f"Failed to set UI preference: {e}")
            return False

    # Export/Import
    def export_settings(self) -> dict[str, Any]:
        """Export settings for backup"""
        export_data = self.settings.copy()

        # Include uploaded prompts
        uploaded_prompts = {}
        for prompt_file in self.get_uploaded_prompts():
            try:
                content = self._load_uploaded_prompt(prompt_file)
                uploaded_prompts[prompt_file] = content
            except Exception as e:
                logger.warning(f"Failed to export prompt {prompt_file}: {e}")

        export_data["uploaded_prompts"] = uploaded_prompts
        return export_data

    def import_settings(self, import_data: dict[str, Any]) -> bool:
        """Import settings from backup"""
        try:
            # Import uploaded prompts
            if "uploaded_prompts" in import_data:
                for filename, content in import_data["uploaded_prompts"].items():
                    self.upload_prompt_file(filename, content)
                del import_data["uploaded_prompts"]

            # Import settings
            self._deep_update(self.settings, import_data)
            return self.save_settings()

        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False
