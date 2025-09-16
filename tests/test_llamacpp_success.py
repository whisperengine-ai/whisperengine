#!/usr/bin/env python3
"""
Test llama-cpp-python integration with WhisperEngine - Success Cases
Tests actual model loading and chat completion when a model is available
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


def test_model_loading():
    """Test that GGUF model loads successfully"""

    client = test_llamacpp_detection()

    # Check if model loaded successfully
    if client.llamacpp_model is not None:

        # Test connection
        is_connected = client.check_connection()
        assert is_connected, "Connection check should return True when model is loaded"

        return client, True
    else:
        return client, False


def test_chat_completion():
    """Test actual chat completion with loaded model"""

    client, model_loaded = test_model_loading()

    if not model_loaded:
        return

    # Try to generate chat completion
    messages = [
        {
            "role": "user",
            "content": "Hello! Please respond with just 'Hello there!' to test the system.",
        }
    ]

    response = client.generate_chat_completion(messages, temperature=0.1, max_tokens=50)

    # Check response structure
    assert "choices" in response, "Response should have 'choices' field"
    assert len(response["choices"]) > 0, "Response should have at least one choice"

    choice = response["choices"][0]
    assert "message" in choice, "Choice should have 'message' field"
    assert choice["message"]["role"] == "assistant", "Response should be from assistant"

    content = choice["message"]["content"]
    assert len(content.strip()) > 0, "Response content should not be empty"


def test_performance():
    """Test basic performance characteristics"""

    client, model_loaded = test_model_loading()

    if not model_loaded:
        return

    import time

    messages = [{"role": "user", "content": "Count from 1 to 5."}]

    start_time = time.time()
    response = client.generate_chat_completion(messages, temperature=0.1, max_tokens=30)
    end_time = time.time()

    response_time = end_time - start_time
    response["choices"][0]["message"]["content"]

    if response_time < 30:  # Reasonable threshold
        pass
    else:
        pass


def show_model_info():
    """Show information about the loaded model"""

    models_dir = Path("./models")
    if models_dir.exists():
        gguf_files = list(models_dir.glob("*.gguf"))
        if gguf_files:
            for gguf_file in gguf_files:
                gguf_file.stat().st_size / (1024 * 1024)
        else:
            pass
    else:
        pass


if __name__ == "__main__":

    try:
        show_model_info()

        test_llamacpp_detection()
        model_loaded = test_model_loading()[1]

        if model_loaded:
            test_chat_completion()
            test_performance()

        else:
            pass

    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
