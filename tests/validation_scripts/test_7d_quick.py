#!/usr/bin/env python3
"""
Quick Test: Enhanced 7D Vector System

Simple test to verify the 7D vector system is working correctly.
"""

import asyncio
import os
import sys

async def test_7d_system():
    """Test basic 7D vector functionality"""
    
    print("🎯 Testing Enhanced 7D Vector System")
    print("=" * 40)
    
    # Set environment
    os.environ['QDRANT_HOST'] = 'localhost'
    os.environ['QDRANT_PORT'] = '6334'
    os.environ['QDRANT_COLLECTION_NAME'] = 'test_7d_quick'
    os.environ['DISCORD_BOT_NAME'] = 'TestBot'
    
    # Set a writable cache directory
    import tempfile
    temp_dir = tempfile.gettempdir()
    os.environ['FASTEMBED_CACHE_PATH'] = temp_dir
    
    try:
        # Test 7D analyzer
        print("1. Testing 7D Analyzer...")
        from src.intelligence.enhanced_7d_vector_analyzer import Enhanced7DVectorAnalyzer
        
        analyzer = Enhanced7DVectorAnalyzer()
        
        # Test analysis
        result = await analyzer.analyze_all_dimensions(
            content="I'm excited about marine research!",
            user_id="test_user",
            character_name="elena"
        )
        
        print(f"✅ Relationship: {result['relationship_key']}")
        print(f"✅ Personality: {result['personality_key']}")
        print(f"✅ Interaction: {result['interaction_key']}")
        print(f"✅ Temporal: {result['temporal_key']}")
        
        # Test memory system
        print("\n2. Testing Vector Memory Store...")
        from src.memory.vector_memory_system import VectorMemoryStore, VectorMemory, MemoryType
        
        memory_store = VectorMemoryStore()
        print("✅ Memory store initialized")
        
        # Test storing a memory with 7D vectors
        print("\n3. Testing Memory Storage...")
        memory = VectorMemory(
            id="test_7d_001",
            user_id="test_user",
            memory_type=MemoryType.CONVERSATION,
            content="I'm excited about marine research and want to learn more!",
            source="test"
        )
        
        memory_id = await memory_store.store_memory(memory)
        print(f"✅ Memory stored with 7D vectors: {memory_id}")
        
        print("\n🎉 7D Vector System Test Complete!")
        print("✅ All components working correctly")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_7d_system())
    sys.exit(0 if success else 1)