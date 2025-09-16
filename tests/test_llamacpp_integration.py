#!/usr/bin/env python3
"""
Test llama-cpp-python integration with WhisperEngine
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from env_manager import load_environment
if not load_environment():
    print("❌ Failed to load environment configuration")
    sys.exit(1)

def test_llamacpp_detection():
    """Test that llamacpp:// URLs are properly detected"""
    print("🔍 Testing llamacpp:// URL detection...")
    
    # Set environment for llamacpp
    os.environ["LLM_CHAT_API_URL"] = "llamacpp://local"
    
    from src.llm.llm_client import LLMClient
    
    client = LLMClient()
    
    # Check detection
    assert client.is_llamacpp == True, "llamacpp detection failed"
    assert client.service_name == "llama-cpp-python", f"Expected 'llama-cpp-python', got '{client.service_name}'"
    
    print("✅ llamacpp:// URL detection works correctly")
    return client

def test_llamacpp_without_model():
    """Test llamacpp initialization without a model (should fail gracefully)"""
    print("🔍 Testing llamacpp initialization without model...")
    
    # Temporarily hide any existing models
    import tempfile
    import shutil
    import os
    
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
                print(f"   Temporarily moved {len(moved_models)} GGUF models")
        
        # Clear environment variable
        original_model_path = os.environ.pop("LLAMACPP_MODEL_PATH", None)
        
        client = test_llamacpp_detection()
        
        # Should have failed to initialize (no model available)
        assert client.llamacpp_model is None, "llamacpp_model should be None when no model is available"
        
        # Should still be able to check connection (will return False)
        is_connected = client.check_connection()
        assert is_connected == False, "Connection check should return False when no model is loaded"
        
        print("✅ llamacpp gracefully handles missing model")
        
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
            print(f"   Restored {len(moved_models)} GGUF models")

def test_llamacpp_chat_completion_error():
    """Test chat completion when model is not loaded (should return error response)"""
    print("🔍 Testing chat completion without loaded model...")
    
    client = test_llamacpp_detection()
    
    # Try to generate chat completion
    messages = [
        {"role": "user", "content": "Hello, can you help me?"}
    ]
    
    response = client.generate_chat_completion(messages)
    
    # Should get error response
    assert "choices" in response, "Response should have 'choices' field"
    assert len(response["choices"]) > 0, "Response should have at least one choice"
    assert "error" in response, "Response should indicate an error occurred"
    
    choice = response["choices"][0]
    assert "message" in choice, "Choice should have 'message' field"
    assert choice["message"]["role"] == "assistant", "Response should be from assistant"
    
    content = choice["message"]["content"].lower()
    assert "model" in content and "not loaded" in content, f"Error message should mention model not loaded, got: {choice['message']['content']}"
    
    print("✅ llamacpp returns proper error response when model not loaded")

def show_environment_config():
    """Show the environment variables used for llamacpp configuration"""
    print("\n📋 Environment Configuration for llama-cpp-python:")
    print(f"  LLM_CHAT_API_URL: {os.getenv('LLM_CHAT_API_URL', 'not set')}")
    print(f"  LLAMACPP_MODEL_PATH: {os.getenv('LLAMACPP_MODEL_PATH', 'not set')}")
    print(f"  LOCAL_MODELS_DIR: {os.getenv('LOCAL_MODELS_DIR', './models')}")
    print(f"  LLAMACPP_CONTEXT_SIZE: {os.getenv('LLAMACPP_CONTEXT_SIZE', '4096')}")
    print(f"  LLAMACPP_THREADS: {os.getenv('LLAMACPP_THREADS', '4')}")
    print(f"  LLAMACPP_USE_GPU: {os.getenv('LLAMACPP_USE_GPU', 'auto')}")

def show_usage_instructions():
    """Show instructions for using llamacpp with a real model"""
    print("\n📖 How to use llama-cpp-python with a real model:")
    print("1. Download a GGUF model (e.g., from HuggingFace)")
    print("   Example: wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf")
    print("2. Create a models directory: mkdir -p ./models")
    print("3. Move the model: mv Phi-3-mini-4k-instruct-q4.gguf ./models/")
    print("4. Set environment variables:")
    print("   export LLM_CHAT_API_URL=llamacpp://local")
    print("   export LLAMACPP_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf")
    print("5. Run your WhisperEngine application")
    print("\nAlternatively, just put any .gguf file in ./models/ and it will be auto-detected!")

if __name__ == "__main__":
    print("🚀 Testing llama-cpp-python integration with WhisperEngine\n")
    
    try:
        test_llamacpp_detection()
        test_llamacpp_without_model()
        test_llamacpp_chat_completion_error()
        
        print("\n🎉 All tests passed! llama-cpp-python integration is working correctly.")
        
        show_environment_config()
        show_usage_instructions()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)