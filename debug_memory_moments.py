#!/usr/bin/env python3
"""
Test script to debug Memory Moments initialization issue
"""
import sys
sys.path.append('/app')

try:
    # Test if we can access the running bot instance somehow
    print("Testing Memory Moments initialization dependencies...")
    
    # Test imports
    from src.personality.memory_moments import MemoryTriggeredMoments
    print("✅ MemoryTriggeredMoments import successful")
    
    from src.intelligence import Phase2Integration
    print("✅ Phase2Integration import successful")
    
    from src.memory.core.memory_factory import create_memory_manager
    print("✅ create_memory_manager import successful")
    
    # Test basic initialization
    print("\nTesting basic initialization...")
    
    # This would normally require an LLM client, so we'll just check the class
    print(f"MemoryTriggeredMoments: {MemoryTriggeredMoments}")
    print(f"Phase2Integration: {Phase2Integration}")
    print(f"create_memory_manager: {create_memory_manager}")
    
    print("\n✅ All critical imports successful - Memory Moments should be working")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()