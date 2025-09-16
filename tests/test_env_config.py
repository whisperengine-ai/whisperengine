#!/usr/bin/env python3
"""Test script to verify environment configuration for local LLM bundling."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from env_manager import load_environment


def test_environment_config():
    """Test that environment configuration is loaded correctly."""

    # Load environment
    if not load_environment():
        return False

    # Check critical LLM settings
    api_url = os.getenv("LLM_CHAT_API_URL")
    os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    local_model = os.getenv("LOCAL_LLM_MODEL")
    models_dir = os.getenv("LOCAL_MODELS_DIR", "./models")

    # Check if models directory exists
    if os.path.exists(models_dir):
        models = [d for d in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, d))]

        # Check if the configured model exists
        if local_model and local_model in models:
            pass
        else:
            pass
    else:
        pass

    # Check if local:// protocol is configured
    if api_url and api_url.startswith("local://"):
        return True
    else:
        return False


if __name__ == "__main__":
    success = test_environment_config()
    sys.exit(0 if success else 1)
