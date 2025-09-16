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
    sys.exit(1)


def check_gpu_availability():
    """Check GPU availability and configuration"""

    try:
        import torch

        # Check CUDA availability
        cuda_available = torch.cuda.is_available()

        if cuda_available:
            for i in range(torch.cuda.device_count()):
                torch.cuda.get_device_name(i)
                torch.cuda.get_device_properties(i).total_memory / 1024**3

        # Check MPS (Apple Silicon) availability
        mps_available = torch.backends.mps.is_available()

        return cuda_available or mps_available

    except ImportError:
        return False
    except Exception:
        return False


def check_model_configuration():
    """Check current model configuration"""

    # Check environment variables
    llm_url = os.getenv("LLM_CHAT_API_URL", "not_set")
    model_name = os.getenv("LLM_MODEL_NAME", "not_set")
    local_model = os.getenv("LOCAL_LLM_MODEL", "not_set")
    os.getenv("USE_LOCAL_LLM", "false")

    # Determine the execution path
    is_local_llm = llm_url == "local://"

    return is_local_llm, model_name, local_model


def test_model_device_usage():
    """Test actual model device usage"""

    try:
        import torch

        from src.llm.llm_client import LLMClient

        # Initialize LLM client
        client = LLMClient()

        if hasattr(client, "local_model") and client.local_model is not None:

            # Check which device the model is on
            next(client.local_model.parameters()).device

            # Check model dtype
            next(client.local_model.parameters()).dtype

            # Test a small inference to see actual device usage
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                memory_before = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0

                # Try a small inference
                test_input = client.local_tokenizer("Hello", return_tensors="pt")
                with torch.no_grad():
                    _ = client.local_model(**test_input)

                memory_after = torch.cuda.memory_allocated() if torch.cuda.is_available() else 0
                (memory_after - memory_before) / 1024**2  # MB

            elif torch.backends.mps.is_available():
                pass

            return True

        else:
            return False

    except Exception:
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test function"""

    # Check GPU availability
    gpu_available = check_gpu_availability()

    # Check model configuration
    is_local, model_name, local_model = check_model_configuration()

    # Test actual model usage if local
    if is_local:
        model_on_gpu = test_model_device_usage()
    else:
        model_on_gpu = False

    # Summary

    if is_local and gpu_available and not model_on_gpu:
        pass
    elif is_local and not gpu_available:
        pass
    elif model_on_gpu:
        pass


if __name__ == "__main__":
    main()
