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

from src.memory.core.memory_factory import create_memory_manager

try:
    manager = create_memory_manager(mode="unified")

    # This should fail
    manager.add_documents_with_embeddings()

except Exception:
    traceback.print_exc()
