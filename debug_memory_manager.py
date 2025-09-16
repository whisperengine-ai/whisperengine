#!/usr/bin/env python3
"""
Debug script to check memory manager initialization
"""
import os
from src.memory.memory_manager import UserMemoryManager


def debug_memory_manager():
    print("=== Memory Manager Debug ===")

    # Check environment variables
    print("Environment Variables:")
    print(f"  LLM_EMBEDDING_API_URL: {os.getenv('LLM_EMBEDDING_API_URL')}")
    print(f"  USE_EXTERNAL_EMBEDDINGS: {os.getenv('USE_EXTERNAL_EMBEDDINGS')}")

    # Initialize memory manager
    try:
        memory_manager = UserMemoryManager()
        print("\nMemory Manager Attributes:")
        print(
            f"  use_external_embeddings: {getattr(memory_manager, 'use_external_embeddings', 'NOT_SET')}"
        )
        print(
            f"  add_documents_with_embeddings: {getattr(memory_manager, 'add_documents_with_embeddings', 'NOT_SET')}"
        )
        print(
            f"  query_with_embeddings: {getattr(memory_manager, 'query_with_embeddings', 'NOT_SET')}"
        )

        # Check the condition
        condition_result = getattr(memory_manager, "use_external_embeddings", False) and getattr(
            memory_manager, "add_documents_with_embeddings", None
        )
        print(
            f"\nCondition (use_external_embeddings and add_documents_with_embeddings): {condition_result}"
        )

    except Exception as e:
        print(f"Error initializing memory manager: {e}")


if __name__ == "__main__":
    debug_memory_manager()
