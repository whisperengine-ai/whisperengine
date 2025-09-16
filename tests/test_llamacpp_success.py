#!/usr/bin/env python3
"""
Test llama-cpp-python integration with WhisperEngine - Success Cases
Tests actual model loading and chat completion when a model is available
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

def test_model_loading():
    """Test that GGUF model loads successfully"""
    print("🔍 Testing GGUF model loading...")
    
    client = test_llamacpp_detection()
    
    # Check if model loaded successfully
    if client.llamacpp_model is not None:
        print("✅ GGUF model loaded successfully")
        
        # Test connection
        is_connected = client.check_connection()
        assert is_connected == True, "Connection check should return True when model is loaded"
        print("✅ Connection check passed")
        
        return client, True
    else:
        print("⚠️ No GGUF model available for testing")
        return client, False

def test_chat_completion():
    """Test actual chat completion with loaded model"""
    print("🔍 Testing chat completion with loaded model...")
    
    client, model_loaded = test_model_loading()
    
    if not model_loaded:
        print("⚠️ Skipping chat completion test - no model loaded")
        return
    
    # Try to generate chat completion
    messages = [
        {"role": "user", "content": "Hello! Please respond with just 'Hello there!' to test the system."}
    ]
    
    print("   Generating response (this may take a moment)...")
    response = client.generate_chat_completion(messages, temperature=0.1, max_tokens=50)
    
    # Check response structure
    assert "choices" in response, "Response should have 'choices' field"
    assert len(response["choices"]) > 0, "Response should have at least one choice"
    
    choice = response["choices"][0]
    assert "message" in choice, "Choice should have 'message' field"
    assert choice["message"]["role"] == "assistant", "Response should be from assistant"
    
    content = choice["message"]["content"]
    assert len(content.strip()) > 0, "Response content should not be empty"
    
    print(f"✅ Chat completion successful!")
    print(f"   Model response: {content.strip()}")

def test_performance():
    """Test basic performance characteristics"""
    print("🔍 Testing performance characteristics...")
    
    client, model_loaded = test_model_loading()
    
    if not model_loaded:
        print("⚠️ Skipping performance test - no model loaded")
        return
    
    import time
    
    messages = [
        {"role": "user", "content": "Count from 1 to 5."}
    ]
    
    start_time = time.time()
    response = client.generate_chat_completion(messages, temperature=0.1, max_tokens=30)
    end_time = time.time()
    
    response_time = end_time - start_time
    content = response["choices"][0]["message"]["content"]
    
    print(f"✅ Performance test completed")
    print(f"   Response time: {response_time:.2f} seconds")
    print(f"   Response: {content.strip()}")
    
    if response_time < 30:  # Reasonable threshold
        print("✅ Response time is reasonable")
    else:
        print("⚠️ Response time is slow (may be normal for large models)")

def show_model_info():
    """Show information about the loaded model"""
    print("\n📋 Model Information:")
    
    models_dir = Path("./models")
    if models_dir.exists():
        gguf_files = list(models_dir.glob("*.gguf"))
        if gguf_files:
            for gguf_file in gguf_files:
                size_mb = gguf_file.stat().st_size / (1024 * 1024)
                print(f"   📄 {gguf_file.name} ({size_mb:.1f} MB)")
        else:
            print("   No GGUF models found")
    else:
        print("   ./models directory not found")
    
    print(f"\n🔧 Configuration:")
    print(f"   LLM_CHAT_API_URL: {os.getenv('LLM_CHAT_API_URL', 'not set')}")
    print(f"   LLAMACPP_MODEL_PATH: {os.getenv('LLAMACPP_MODEL_PATH', 'auto-detect')}")
    print(f"   LLAMACPP_CONTEXT_SIZE: {os.getenv('LLAMACPP_CONTEXT_SIZE', '4096')}")
    print(f"   LLAMACPP_THREADS: {os.getenv('LLAMACPP_THREADS', '4')}")
    print(f"   LLAMACPP_USE_GPU: {os.getenv('LLAMACPP_USE_GPU', 'auto')}")

if __name__ == "__main__":
    print("🚀 Testing llama-cpp-python Success Cases\n")
    
    try:
        show_model_info()
        print()
        
        test_llamacpp_detection()
        model_loaded = test_model_loading()[1]
        
        if model_loaded:
            test_chat_completion()
            test_performance()
            
            print("\n🎉 All tests passed! llama-cpp-python is working perfectly.")
            print("\n💡 Ready to use:")
            print("   source .venv/bin/activate && python universal_native_app.py")
            print("   OR (Discord bot):")
            print("   source .venv/bin/activate && python run.py")
        else:
            print("\n⚠️ No GGUF model available for full testing.")
            print("   Download a model with: python setup_llamacpp.py")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)