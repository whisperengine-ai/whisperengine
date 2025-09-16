#!/usr/bin/env python3
"""
Quick setup script for llama-cpp-python integration
Downloads a small test model and configures WhisperEngine to use it
"""

import logging
import os
import sys
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_test_model():
    """Download a small GGUF model for testing"""
    models_dir = Path("./models")
    models_dir.mkdir(exist_ok=True)

    # Small efficient model for testing (~650MB)
    model_url = "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
    model_filename = "Phi-3-mini-4k-instruct-q4.gguf"
    model_path = models_dir / model_filename

    if model_path.exists():
        logger.info(f"✅ Model already exists: {model_path}")
        return str(model_path)

    logger.info(f"📥 Downloading test model: {model_filename}")
    logger.info(f"   URL: {model_url}")
    logger.info("   Size: ~650MB (this may take a few minutes)")

    try:

        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                min(100, (downloaded * 100) // total_size)
                downloaded // (1024 * 1024)
                total_size // (1024 * 1024)

        urllib.request.urlretrieve(model_url, model_path, progress_hook)
        logger.info(f"✅ Download complete: {model_path}")
        return str(model_path)

    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        return None


def configure_environment(model_path):
    """Configure environment variables for llamacpp"""
    logger.info("🔧 Configuring environment for llama-cpp-python...")

    # Create or update .env file
    env_file = Path(".env")
    env_lines = []

    # Read existing .env if it exists
    if env_file.exists():
        with open(env_file) as f:
            env_lines = f.readlines()

    # Update or add llamacpp configuration
    new_lines = []
    updated_url = False
    updated_path = False

    for line in env_lines:
        if line.startswith("LLM_CHAT_API_URL="):
            new_lines.append("LLM_CHAT_API_URL=llamacpp://local\n")
            updated_url = True
        elif line.startswith("LLAMACPP_MODEL_PATH="):
            new_lines.append(f"LLAMACPP_MODEL_PATH={model_path}\n")
            updated_path = True
        else:
            new_lines.append(line)

    # Add new lines if not updated
    if not updated_url:
        new_lines.append("LLM_CHAT_API_URL=llamacpp://local\n")
    if not updated_path:
        new_lines.append(f"LLAMACPP_MODEL_PATH={model_path}\n")

    # Write back to .env
    with open(env_file, "w") as f:
        f.writelines(new_lines)

    logger.info(f"✅ Updated {env_file} with llamacpp configuration")


def verify_installation():
    """Verify that llama-cpp-python is installed"""
    logger.info("🔍 Checking llama-cpp-python installation...")

    try:
        import llama_cpp

        logger.info(f"✅ llama-cpp-python is installed (version: {llama_cpp.__version__})")
        return True
    except ImportError:
        logger.error("❌ llama-cpp-python is not installed")
        logger.info("   Install with: source .venv/bin/activate && pip install llama-cpp-python")
        return False


def test_integration():
    """Test the integration by running our test script"""
    logger.info("🧪 Testing llama-cpp-python integration...")

    try:
        # Run the comprehensive success test instead
        result = os.system("source .venv/bin/activate && python test_llamacpp_success.py")
        if result == 0:
            logger.info("✅ Integration test passed!")
            return True
        else:
            logger.error("❌ Integration test failed")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to run integration test: {e}")
        return False


def main():

    # Check installation
    if not verify_installation():
        return 1

    # Download model
    model_path = download_test_model()
    if not model_path:
        return 1

    # Configure environment
    configure_environment(model_path)

    # Test integration
    if not test_integration():
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
