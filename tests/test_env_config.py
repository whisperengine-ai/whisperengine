#!/usr/bin/env python3
"""Test script to verify environment configuration for local LLM bundling."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from env_manager import load_environment


def test_environment_config():
    """Test that environment configuration is loaded correctly."""
    print("🔧 Testing environment configuration...")

    # Load environment
    if not load_environment():
        print("❌ Failed to load environment")
        return False

    print(f"✅ Environment loaded. Mode: {os.getenv('ENV_MODE', 'unknown')}")

    # Check critical LLM settings
    api_url = os.getenv("LLM_CHAT_API_URL")
    use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    local_model = os.getenv("LOCAL_LLM_MODEL")
    models_dir = os.getenv("LOCAL_MODELS_DIR", "./models")

    print(f"🤖 LLM Configuration:")
    print(f"   API URL: {api_url}")
    print(f"   Use Local LLM: {use_local}")
    print(f"   Local Model: {local_model}")
    print(f"   Models Directory: {models_dir}")

    # Check if models directory exists
    if os.path.exists(models_dir):
        models = [d for d in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, d))]
        print(f"   Available models: {models}")

        # Check if the configured model exists
        if local_model and local_model in models:
            print(f"✅ Configured model '{local_model}' found in models directory")
        else:
            print(f"❌ Configured model '{local_model}' not found in models directory")
    else:
        print(f"❌ Models directory '{models_dir}' does not exist")

    # Check if local:// protocol is configured
    if api_url and api_url.startswith("local://"):
        print("✅ Local LLM protocol configured correctly")
        return True
    else:
        print("❌ Local LLM protocol not configured (should be 'local://models')")
        return False


if __name__ == "__main__":
    success = test_environment_config()
    sys.exit(0 if success else 1)
