#!/usr/bin/env python3
"""
Simple test to verify memory system fixes without UI interference.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from env_manager import load_environment

if not load_environment():
    sys.exit(1)



async def test_minimal_memory():
    """Minimal test of memory system components"""
    try:
        # Test Phase 3 import
        from src.memory.phase3_integration import Phase3MemoryNetworks


        # Test memory manager import


        # Create a test instance
        Phase3MemoryNetworks()



        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function"""

    success = await test_minimal_memory()

    if success:
        pass
    else:
        pass


if __name__ == "__main__":
    asyncio.run(main())
