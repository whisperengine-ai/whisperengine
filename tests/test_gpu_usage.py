#!/usr/bin/env python3
"""
GPU Detection Test for WhisperEngine Desktop App
Checks if the current model configuration is using GPU acceleration.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from env_manager import load_environment

if not load_environment():
    print("❌ Failed to load environment")
    sys.exit(1)


def check_gpu_availability():
    """Check GPU availability and configuration"""
    print("🔍 Checking GPU Availability...")

    try:
        import torch

        print(f"✅ PyTorch version: {torch.__version__}")

        # Check CUDA availability
        cuda_available = torch.cuda.is_available()
        print(f"🔥 CUDA available: {cuda_available}")

        if cuda_available:
            print(f"   - CUDA devices: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                device_name = torch.cuda.get_device_name(i)
                print(f"   - Device {i}: {device_name}")
                memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
                print(f"   - Memory: {memory_total:.1f} GB")

        # Check MPS (Apple Silicon) availability
        mps_available = torch.backends.mps.is_available()
        print(f"🍎 MPS (Apple Silicon) available: {mps_available}")

        return cuda_available or mps_available

    except ImportError:
        print("❌ PyTorch not available")
        return False
    except Exception as e:
        print(f"❌ Error checking GPU: {e}")
        return False


def check_model_configuration():
    """Check current model configuration"""
    print("\n📋 Current Model Configuration:")

    # Check environment variables
    llm_url = os.getenv("LLM_CHAT_API_URL", "not_set")
    model_name = os.getenv("LLM_MODEL_NAME", "not_set")
    local_model = os.getenv("LOCAL_LLM_MODEL", "not_set")
    use_local = os.getenv("USE_LOCAL_LLM", "false")

    print(f"   - LLM_CHAT_API_URL: {llm_url}")
    print(f"   - LLM_MODEL_NAME: {model_name}")
    print(f"   - LOCAL_LLM_MODEL: {local_model}")
    print(f"   - USE_LOCAL_LLM: {use_local}")

    # Determine the execution path
    is_local_llm = llm_url == "local://"
    print(
        f"\n💡 Model Execution Path: {'Local LLM (Transformers)' if is_local_llm else 'External API'}"
    )

    return is_local_llm, model_name, local_model


def test_model_device_usage():
    """Test actual model device usage"""
    print("\n🧪 Testing Model Device Usage...")

    try:
        from src.llm.llm_client import LLMClient
        import torch

        # Initialize LLM client
        client = LLMClient()

        if hasattr(client, "local_model") and client.local_model is not None:
            print("✅ Local model is loaded")

            # Check which device the model is on
            device = next(client.local_model.parameters()).device
            print(f"🔧 Model device: {device}")

            # Check model dtype
            dtype = next(client.local_model.parameters()).dtype
            print(f"📊 Model dtype: {dtype}")

            # Test a small inference to see actual device usage
            if torch.cuda.is_available():
                print("🔥 CUDA detected - checking GPU memory usage...")
                torch.cuda.empty_cache()
                memory_before = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0

                # Try a small inference
                test_input = client.local_tokenizer("Hello", return_tensors="pt")
                with torch.no_grad():
                    _ = client.local_model(**test_input)

                memory_after = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0
                memory_used = (memory_after - memory_before) / 1024**2  # MB
                print(f"   GPU memory used for inference: {memory_used:.1f} MB")

            elif torch.backends.mps.is_available():
                print("🍎 MPS detected - model should be using Apple Silicon GPU")

            return True

        else:
            print("❌ Local model not loaded - likely using external API")
            return False

    except Exception as e:
        print(f"❌ Error testing model device: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("🚀 WhisperEngine GPU Detection Test")
    print("=" * 50)

    # Check GPU availability
    gpu_available = check_gpu_availability()

    # Check model configuration
    is_local, model_name, local_model = check_model_configuration()

    # Test actual model usage if local
    if is_local:
        model_on_gpu = test_model_device_usage()
    else:
        model_on_gpu = False
        print("\n💡 External API mode - GPU usage depends on the API service")

    # Summary
    print("\n" + "=" * 50)
    print("📈 SUMMARY:")
    print(f"   🔥 GPU Available: {gpu_available}")
    print(f"   🏠 Using Local Model: {is_local}")
    print(f"   🎯 Model on GPU: {model_on_gpu if is_local else 'N/A (External API)'}")

    if is_local and gpu_available and not model_on_gpu:
        print("\n⚠️  POTENTIAL ISSUE:")
        print("   GPU is available but model may not be using it")
        print("   Consider checking model loading configuration")
    elif is_local and not gpu_available:
        print("\n📝 INFO:")
        print("   Model running on CPU (no GPU detected)")
    elif model_on_gpu:
        print("\n✅ OPTIMAL:")
        print("   Model is using GPU acceleration!")


if __name__ == "__main__":
    main()
