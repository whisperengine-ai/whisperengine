#!/usr/bin/env python3
"""
Test llama-cpp-python integration with WhisperEngine
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from env_manager import load_environment

if not load_environment():
    sys.exit(1)


def test_llamacpp_detection():
    """Test that llamacpp:// URLs are properly detected"""

    # Set environment for llamacpp
    os.environ["LLM_CHAT_API_URL"] = "llamacpp://local"

    from src.llm.llm_client import LLMClient

    client = LLMClient()

    # Check detection
    assert client.is_llamacpp, "llamacpp detection failed"
    assert (
        client.service_name == "llama-cpp-python"
    ), f"Expected 'llama-cpp-python', got '{client.service_name}'"

    return client


def test_llamacpp_without_model():
    """Test llamacpp initialization without a model (should fail gracefully)"""

    # Temporarily hide any existing models
    import os
    import shutil
    import tempfile

    models_dir = Path("./models")
    temp_dir = None
    moved_models = []

    try:
        # Create temp directory and move GGUF models temporarily
        if models_dir.exists():
            gguf_files = list(models_dir.glob("*.gguf"))
            if gguf_files:
                temp_dir = Path(tempfile.mkdtemp())
                for gguf_file in gguf_files:
                    temp_path = temp_dir / gguf_file.name
                    shutil.move(str(gguf_file), str(temp_path))
                    moved_models.append((gguf_file, temp_path))

        # Clear environment variable
        original_model_path = os.environ.pop("LLAMACPP_MODEL_PATH", None)

        client = test_llamacpp_detection()

        # Should have failed to initialize (no model available)
        assert (
            client.llamacpp_model is None
        ), "llamacpp_model should be None when no model is available"

        # Should still be able to check connection (will return False)
        is_connected = client.check_connection()
        assert not is_connected, "Connection check should return False when no model is loaded"

    finally:
        # Restore moved models
        for original_path, temp_path in moved_models:
            if temp_path.exists():
                shutil.move(str(temp_path), str(original_path))

        if temp_dir and temp_dir.exists():
            shutil.rmtree(str(temp_dir))

        # Restore environment variable
        if original_model_path:
            os.environ["LLAMACPP_MODEL_PATH"] = original_model_path

        if moved_models:
            pass


def test_llamacpp_chat_completion_error():
    """Test chat completion when model is not loaded (should return error response)"""

    client = test_llamacpp_detection()

    # Try to generate chat completion
    messages = [{"role": "user", "content": "Hello, can you help me?"}]

    response = client.generate_chat_completion(messages)

    # Should get error response
    assert "choices" in response, "Response should have 'choices' field"
    assert len(response["choices"]) > 0, "Response should have at least one choice"
    assert "error" in response, "Response should indicate an error occurred"

    choice = response["choices"][0]
    assert "message" in choice, "Choice should have 'message' field"
    assert choice["message"]["role"] == "assistant", "Response should be from assistant"

    content = choice["message"]["content"].lower()
    assert (
        "model" in content and "not loaded" in content
    ), f"Error message should mention model not loaded, got: {choice['message']['content']}"


def show_environment_config():
    """Show the environment variables used for llamacpp configuration"""


def show_usage_instructions():
    """Show instructions for using llamacpp with a real model"""


if __name__ == "__main__":

    try:
        test_llamacpp_detection()
        test_llamacpp_without_model()
        test_llamacpp_chat_completion_error()

        show_environment_config()
        show_usage_instructions()

    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
