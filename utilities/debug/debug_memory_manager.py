#!/usr/bin/env python3
"""
Debug script to check memory manager initialization
"""

from src.memory.core.memory_factory import create_memory_manager


def debug_memory_manager():

    # Check environment variables

    # Initialize memory manager
    try:
        memory_manager = create_memory_manager(mode="unified")

        # Check the condition
        getattr(memory_manager, "use_external_embeddings", False) and getattr(
            memory_manager, "add_documents_with_embeddings", None
        )

    except Exception:
        pass


if __name__ == "__main__":
    debug_memory_manager()
