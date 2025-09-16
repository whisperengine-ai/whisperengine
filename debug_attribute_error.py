#!/usr/bin/env python3
"""
Quick test to see exact error location
"""
import os
import sys
import traceback

# Add src to path
sys.path.insert(0, "src")

# Set environment
os.environ["ENV_MODE"] = "development"

from src.memory.memory_manager import UserMemoryManager

try:
    manager = UserMemoryManager("test_user_123")


    # This should fail
    manager.add_documents_with_embeddings()

except Exception:
    traceback.print_exc()
