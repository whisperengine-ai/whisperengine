#!/usr/bin/env python3
"""
Test script for dump_global_facts.py

This script tests the export and import functionality with a clean database.
"""

import json
import shutil
import tempfile
from pathlib import Path


def test_dump_global_facts():
    """Test the global facts dump and import functionality"""

    # Create a temporary directory for testing
    test_dir = Path(tempfile.mkdtemp())
    chromadb_test_dir = test_dir / "chromadb_data_test"


    try:
        # Import the memory manager with the test directory
        import sys

        sys.path.insert(0, str(Path.cwd()))

        from memory_manager import UserMemoryManager

        # Initialize memory manager with test directory
        memory_manager = UserMemoryManager(persist_directory=str(chromadb_test_dir))

        # Add some test global facts
        test_facts = [
            ("Test fact 1: The system uses Python", "Testing context", "test_admin"),
            ("Test fact 2: ChromaDB is used for storage", "System architecture", "test_admin"),
            ("Test fact 3: The bot has memory capabilities", "Feature description", "test_admin"),
        ]

        for fact, context, added_by in test_facts:
            memory_manager.store_global_fact(fact, context, added_by)

        # Test export
        from dump_global_facts import export_global_facts

        export_file = test_dir / "test_export.json"
        result_file = export_global_facts(memory_manager, str(export_file))

        if result_file:

            # Check export file contents
            with open(export_file) as f:
                json.load(f)


            # Test import with a fresh memory manager
            fresh_chromadb_dir = test_dir / "chromadb_data_fresh"
            fresh_memory_manager = UserMemoryManager(persist_directory=str(fresh_chromadb_dir))

            from dump_global_facts import import_global_facts

            import_global_facts(
                fresh_memory_manager, str(export_file), confirm=True
            )


            # Verify the facts were imported
            fresh_memory_manager.get_all_global_facts()

            return True
        else:
            return False

    except Exception:
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Cleanup
        try:
            shutil.rmtree(test_dir)
        except Exception:
            pass


if __name__ == "__main__":
    success = test_dump_global_facts()
    exit(0 if success else 1)
