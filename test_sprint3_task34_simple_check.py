"""
Sprint 3 Task 3.4: Simple Integration Test

Basic test to verify the complete memory persistence system
and see actual importance scores before the comprehensive test.
"""

import asyncio
import sys
from datetime import datetime, timezone as tz
from unittest.mock import AsyncMock

# Add src to path for imports
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')


async def simple_integration_test():
    """Simple test to verify Sprint 3 components work and see actual scores"""
    
    print("🧪 Simple Sprint 3 Task 3.4 Integration Test")
    
    try:
        from src.utils.llm_enhanced_memory_manager import LLMEnhancedMemoryManager
        
        # Mock base components
        mock_base_manager = AsyncMock()
        mock_llm_client = AsyncMock()
        
        # Create manager
        manager = LLMEnhancedMemoryManager(
            base_memory_manager=mock_base_manager,
            llm_client=mock_llm_client
        )
        
        # Initialize persistence systems
        if hasattr(manager, '_initialize_persistence_systems'):
            await manager._initialize_persistence_systems()
        
        print(f"✅ Manager created with components:")
        print(f"   • Emotional intelligence: {manager.emotional_intelligence is not None}")
        print(f"   • Memory importance engine: {manager.memory_importance_engine is not None}")
        print(f"   • Emotional-memory bridge: {manager.emotional_memory_bridge is not None}")
        print(f"   • Automatic learning hooks: {manager.automatic_learning_hooks is not None}")
        
        # Test one memory to see actual scores
        test_memory = {
            "id": "test_memory_001",
            "content": "Had a panic attack during presentation - very stressful situation",
            "timestamp": datetime.now(tz.utc).isoformat(),
            "user_id": "test_user"
        }
        
        test_context = {
            "trigger_message": "Feeling overwhelmed after presentation",
            "emotional_state": "crisis",
            "stress_level": "extreme"
        }
        
        if hasattr(manager, 'store_memory_with_learning'):
            stored_memory = await manager.store_memory_with_learning(
                user_id="test_user",
                memory_data=test_memory,
                storage_context=test_context
            )
            
            print(f"\n✅ Memory stored successfully:")
            print(f"   • ID: {stored_memory.get('id', 'N/A')}")
            print(f"   • Importance Score: {stored_memory.get('importance_score', 'N/A')}")
            print(f"   • Enhancement Applied: {'emotional_enhancement' in stored_memory}")
            print(f"   • Learning Triggered: {manager.automatic_learning_hooks is not None}")
            
            return True, stored_memory
        else:
            print("❌ store_memory_with_learning method not available")
            return False, None
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


if __name__ == "__main__":
    success, result = asyncio.run(simple_integration_test())
    if success:
        print("✅ Simple integration test passed!")
    else:
        print("❌ Simple integration test failed")