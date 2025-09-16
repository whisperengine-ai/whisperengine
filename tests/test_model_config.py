#!/usr/bin/env python3
"""
Test script to verify model name configuration
"""

import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lmstudio_client import LMStudioClient


def test_model_configuration():
    """Test that model name is configured correctly"""

    # Test default environment

    LMStudioClient()

    # Test with environment variables
    os.environ["LLM_MODEL_NAME"] = "llama-2-13b-chat"
    os.environ["LLM_SENTIMENT_MODEL_NAME"] = "llama-2-7b-instruct"

    LMStudioClient()

    # Test method calls use the correct models

    try:
        pass
    except Exception:
        pass




if __name__ == "__main__":
    test_model_configuration()
