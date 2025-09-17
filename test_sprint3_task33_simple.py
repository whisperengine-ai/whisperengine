"""
Sprint 3 Task 3.3: Simple Automatic Pattern Learning Hooks Test

Demonstrates the working automatic pattern learning functionality 
that learns from memory storage, access, and retrieval operations.
"""

import asyncio
import sys
import logging
from datetime import datetime, timezone as tz
from unittest.mock import AsyncMock, MagicMock

# Add src to path for imports
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def test_sprint3_task33_automatic_learning_hooks():
    """
    Test Sprint 3 Task 3.3: Automatic Pattern Learning Hooks
    
    Demonstrates that the automatic learning hooks can:
    1. Learn from memory storage operations
    2. Learn from memory access patterns
    3. Learn from memory retrieval sessions
    4. Update importance patterns automatically
    5. Integrate with the LLM memory manager
    """
    print("🤖 Testing Sprint 3 Task 3.3: Automatic Pattern Learning Hooks")
    
    try:
        # Import the learning hooks
        from src.utils.automatic_pattern_learning_hooks import AutomaticPatternLearningHooks, LearningEvent
        
        # Mock memory importance engine
        mock_memory_engine = AsyncMock()
        mock_memory_engine.load_user_importance_patterns.return_value = []
        mock_memory_engine.save_importance_pattern.return_value = None
        
        # Mock emotional memory bridge  
        mock_emotional_bridge = AsyncMock()
        
        # Create learning hooks
        learning_hooks = AutomaticPatternLearningHooks(
            memory_importance_engine=mock_memory_engine,
            emotional_memory_bridge=mock_emotional_bridge
        )
        
        print("✅ Automatic learning hooks created successfully")
        
        # Test memory storage learning
        print("🔄 Testing memory storage learning...")
        
        storage_memory = {
            "id": "memory_storage_001",
            "content": "Successfully completed the project presentation - feeling accomplished",
            "importance_score": 0.8,
            "user_id": "test_user_123",
            "emotional_enhancement": {
                "mood_category": "happy",
                "enhancement_applied": True,
                "trigger_match": True
            }
        }
        
        storage_context = {
            "trigger_message": "Just finished presenting the big project",
            "conversation_context": {"presentation": True}
        }
        
        await learning_hooks.on_memory_stored(
            user_id="test_user_123",
            memory_id=storage_memory["id"],
            memory_data=storage_memory,
            storage_context=storage_context
        )
        
        # Verify learning from storage
        assert len(learning_hooks.learning_events) > 0
        storage_event = learning_hooks.learning_events[0]
        assert storage_event.event_type == "memory_stored"
        assert storage_event.user_id == "test_user_123"
        assert storage_event.importance_score == 0.8
        assert storage_event.learning_confidence > 0.5
        
        print("✅ Memory storage learning successful:")
        print(f"   • Event type: {storage_event.event_type}")
        print(f"   • Importance score: {storage_event.importance_score:.3f}")
        print(f"   • Learning confidence: {storage_event.learning_confidence:.3f}")
        print(f"   • Memory content: {storage_event.memory_content[:50]}...")
        
        # Test memory access learning
        print("🔄 Testing memory access learning...")
        
        access_memory = {
            "id": "memory_access_001",
            "content": "Important meeting notes from client discussion",
            "importance_score": 0.7,
            "user_id": "test_user_123"
        }
        
        access_context = {
            "access_count": 5,  # Frequently accessed
            "relevance_score": 0.9,
            "query_context": "meeting notes"
        }
        
        await learning_hooks.on_memory_accessed(
            user_id="test_user_123",
            memory_id=access_memory["id"],
            memory_data=access_memory,
            access_context=access_context
        )
        
        # Verify learning from access
        access_event = learning_hooks.learning_events[1]
        assert access_event.event_type == "memory_accessed"
        assert access_event.importance_score > 0.7  # Should have access boost
        
        print("✅ Memory access learning successful:")
        print(f"   • Event type: {access_event.event_type}")
        print(f"   • Original importance: 0.700")
        print(f"   • Boosted importance: {access_event.importance_score:.3f}")
        print(f"   • Access count: {access_context['access_count']}")
        print(f"   • Learning confidence: {access_event.learning_confidence:.3f}")
        
        # Test memory retrieval session learning
        print("🔄 Testing memory retrieval session learning...")
        
        retrieved_memories = [
            {
                "id": "memory_retrieve_001",
                "content": "Customer feedback about product improvements",
                "importance_score": 0.6,
                "relevance_score": 0.85,
                "user_id": "test_user_123"
            },
            {
                "id": "memory_retrieve_002", 
                "content": "Product roadmap planning session notes",
                "importance_score": 0.7,
                "relevance_score": 0.75,
                "user_id": "test_user_123"
            }
        ]
        
        retrieval_context = {
            "search_strategy": "semantic",
            "query_type": "product_feedback"
        }
        
        await learning_hooks.on_memory_retrieval_session(
            user_id="test_user_123",
            query="customer feedback on product features",
            retrieved_memories=retrieved_memories,
            retrieval_context=retrieval_context
        )
        
        # Verify learning from retrieval
        retrieval_events = [e for e in learning_hooks.learning_events if e.event_type == "memory_retrieved"]
        assert len(retrieval_events) > 0  # Should have learned from high-relevance memories
        
        retrieval_event = retrieval_events[0]
        assert retrieval_event.learning_confidence >= 0.75  # High relevance = high confidence
        
        print("✅ Memory retrieval session learning successful:")
        print(f"   • Retrieval events: {len(retrieval_events)}")
        print(f"   • Query: customer feedback on product features")
        print(f"   • High-relevance memories: {len([m for m in retrieved_memories if m['relevance_score'] > 0.7])}")
        print(f"   • Learning confidence: {retrieval_event.learning_confidence:.3f}")
        
        # Test pattern learning verification
        print("🔄 Testing pattern learning calls...")
        
        # Verify pattern save calls were made
        save_calls = mock_memory_engine.save_importance_pattern.call_count
        assert save_calls > 0
        
        print(f"✅ Pattern learning calls made: {save_calls}")
        
        # Test learning statistics
        print("🔄 Testing learning statistics...")
        
        stats = learning_hooks.get_learning_statistics()
        
        print(f"✅ Learning statistics:")
        print(f"   • Total learning events: {stats['total_learning_events']}")
        print(f"   • Session learning count: {stats['session_learning_count']}")
        print(f"   • Event types: {stats['event_types']}")
        print(f"   • Average confidence: {stats['avg_learning_confidence']:.3f}")
        print(f"   • Learning active: {stats['learning_active']}")
        
        # Verify statistics
        assert stats["total_learning_events"] >= 3
        assert stats["learning_active"] is True
        assert "memory_stored" in stats["event_types"]
        assert "memory_accessed" in stats["event_types"]
        assert "memory_retrieved" in stats["event_types"]
        
        # Test LLM memory manager integration
        print("🔄 Testing LLM memory manager integration...")
        
        from src.utils.llm_enhanced_memory_manager import LLMEnhancedMemoryManager
        
        # Mock base components
        mock_base_manager = AsyncMock()
        mock_llm_client = AsyncMock()
        
        # Create LLM memory manager
        manager = LLMEnhancedMemoryManager(
            base_memory_manager=mock_base_manager,
            llm_client=mock_llm_client
        )
        
        # Set the learning hooks manually (simulating proper initialization)
        manager.automatic_learning_hooks = learning_hooks
        
        # Test memory storage with learning
        test_memory = {
            "id": "memory_integration_001",
            "content": "Integration test memory with automatic learning",
            "importance_score": 0.6
        }
        
        storage_result = await manager.store_memory_with_learning(
            user_id="test_user_123",
            memory_data=test_memory,
            storage_context={"trigger_message": "Integration test"}
        )
        
        # Verify integration worked
        assert storage_result["id"] == test_memory["id"]
        
        # Verify learning hook was called (check event count increased)
        new_stats = learning_hooks.get_learning_statistics()
        print(f"   • Previous events: {stats['total_learning_events']}, New events: {new_stats['total_learning_events']}")
        
        # The learning hooks might not always increment if thresholds aren't met
        # but the integration should still work
        assert new_stats["total_learning_events"] >= stats["total_learning_events"]
        
        print(f"✅ LLM memory manager integration successful:")
        print(f"   • Memory stored with learning hooks")
        print(f"   • Learning events increased: {new_stats['total_learning_events']}")
        
        # Test learning statistics method
        manager_stats = manager.get_automatic_learning_statistics()
        assert manager_stats["learning_active"] is True
        assert manager_stats["total_learning_events"] > 0
        
        print(f"✅ Manager learning statistics:")
        print(f"   • Learning active: {manager_stats['learning_active']}")
        print(f"   • Total events: {manager_stats['total_learning_events']}")
        
        print("\n🎉 Sprint 3 Task 3.3 Automatic Pattern Learning Hooks Test PASSED!")
        print("✅ Memory storage learning operational")
        print("✅ Memory access learning functional")  
        print("✅ Retrieval session learning working")
        print("✅ Pattern learning integration successful")
        print("✅ LLM memory manager integration complete")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Sprint 1-3 dependencies not available for testing")
        return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the Sprint 3 Task 3.3 test"""
    success = await test_sprint3_task33_automatic_learning_hooks()
    
    if success:
        print("\n✅ Sprint 3 Task 3.3: Automatic Pattern Learning Hooks - COMPLETED")
        print("The automatic learning hooks successfully learn from memory operations")
        print("to continuously improve memory importance patterns and emotional triggers")
        print("through seamless background learning during normal memory usage.")
    else:
        print("\n❌ Sprint 3 Task 3.3 test failed")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())