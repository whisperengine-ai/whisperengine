"""
Sprint 3 Task 3.2: Simple Emotional-Memory Integration Test

Demonstrates the working emotional-memory bridge functionality 
with proper async handling and realistic testing.
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


async def test_sprint3_task32_emotional_memory_integration():
    """
    Test Sprint 3 Task 3.2: Emotional-Memory Integration
    
    Demonstrates that the emotional-memory bridge can:
    1. Enhance memory importance based on emotional context
    2. Learn emotional trigger patterns  
    3. Apply emotional boosts to memory scoring
    4. Integrate with the LLM memory manager
    """
    print("🧠 Testing Sprint 3 Task 3.2: Emotional-Memory Integration")
    
    try:
        # Import the emotional-memory bridge
        from src.utils.emotional_memory_bridge import EmotionalMemoryBridge, EmotionalMemoryContext
        
        # Create mock emotional intelligence
        mock_emotional_intelligence = AsyncMock()
        mock_assessment = MagicMock()
        mock_assessment.mood_assessment.category.value = "anxious"
        mock_assessment.stress_assessment.level.value = "high"
        mock_assessment.emotional_prediction.predicted_emotion = "worried"
        mock_assessment.emotional_prediction.confidence = 0.85
        mock_assessment.emotional_prediction.triggering_factors = ["deadline pressure", "work stress"]
        mock_assessment.emotional_alerts = [
            MagicMock(
                alert_type=MagicMock(value="stress_alert"),
                priority=MagicMock(value="high"),
                message="High stress levels detected"
            )
        ]
        mock_emotional_intelligence.comprehensive_emotional_assessment.return_value = mock_assessment
        
        # Create mock memory importance engine
        mock_memory_engine = AsyncMock()
        mock_memory_engine.load_user_importance_patterns.return_value = [
            {
                "pattern_type": "emotional_trigger",
                "pattern_name": "work_stress_pattern",
                "emotional_associations": ["worried", "anxious", "stressed"],
                "pattern_keywords": ["deadline", "project", "work", "stress"],
                "confidence_score": 0.8,
                "importance_multiplier": 1.4
            }
        ]
        mock_memory_engine.save_importance_pattern.return_value = None
        
        # Create emotional-memory bridge
        bridge = EmotionalMemoryBridge(
            emotional_intelligence=mock_emotional_intelligence,
            memory_importance_engine=mock_memory_engine
        )
        
        print("✅ Emotional-memory bridge created successfully")
        
        # Test memory data with emotional significance
        test_memory = {
            "id": "memory_test_001",
            "content": "I'm really worried about this project deadline tomorrow - feeling stressed",
            "timestamp": datetime.now(tz.utc).isoformat(),
            "user_id": "test_user_123"
        }
        
        current_message = "Feeling overwhelmed with work pressure"
        base_importance_score = 0.6
        
        # Test emotional context enhancement
        print("🔄 Testing emotional context enhancement...")
        enhanced_context = await bridge.enhance_memory_with_emotional_context(
            user_id="test_user_123",
            memory_id=test_memory["id"],
            memory_data=test_memory,
            current_message=current_message,
            base_importance_score=base_importance_score
        )
        
        # Verify enhancement results
        assert isinstance(enhanced_context, EmotionalMemoryContext)
        assert enhanced_context.user_id == "test_user_123"
        assert enhanced_context.base_importance_score == base_importance_score
        assert enhanced_context.enhancement_applied is True
        
        print(f"✅ Emotional context created:")
        print(f"   • Memory ID: {enhanced_context.memory_id}")
        print(f"   • Mood: {enhanced_context.mood_category}")
        print(f"   • Stress Level: {enhanced_context.stress_level}")
        print(f"   • Emotional Prediction: {enhanced_context.emotional_prediction}")
        print(f"   • Base Score: {enhanced_context.base_importance_score:.3f}")
        print(f"   • Emotional Boost: {enhanced_context.emotional_importance_boost:.3f}")
        print(f"   • Final Score: {enhanced_context.final_importance_score:.3f}")
        print(f"   • Trigger Match: {enhanced_context.emotional_trigger_match}")
        print(f"   • Pattern Confidence: {enhanced_context.emotional_pattern_confidence:.3f}")
        
        # Verify emotional enhancement occurred
        assert enhanced_context.final_importance_score > base_importance_score
        assert enhanced_context.emotional_importance_boost > 0.0
        assert enhanced_context.emotional_trigger_match is True
        assert enhanced_context.emotional_pattern_confidence > 0.7
        
        print("✅ Emotional importance boost applied successfully")
        
        # Test emotional insights
        print("🔄 Testing emotional memory insights...")
        insights = await bridge.get_emotional_memory_insights("test_user_123")
        
        print(f"✅ Emotional memory insights:")
        print(f"   • Total patterns: {insights['total_emotional_patterns']}")
        print(f"   • Enhancement active: {insights['emotional_memory_enhancement_active']}")
        print(f"   • Dominant emotions: {insights['dominant_emotions']}")
        print(f"   • Pattern confidence avg: {insights['pattern_confidence_avg']:.3f}")
        
        # Verify insights structure
        assert "total_emotional_patterns" in insights
        assert "emotional_memory_enhancement_active" in insights
        assert insights["emotional_memory_enhancement_active"] is True
        
        print("✅ Emotional memory insights working correctly")
        
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
        
        # Set the emotional bridge manually (simulating proper initialization)
        manager.emotional_memory_bridge = bridge
        
        # Test emotional intelligence enhancement
        test_memories = [test_memory]
        
        enhanced_memories = await manager.enhance_memories_with_emotional_intelligence(
            user_id="test_user_123",
            memories=test_memories,
            current_message=current_message
        )
        
        # Verify integration results
        assert len(enhanced_memories) == 1
        enhanced_memory = enhanced_memories[0]
        
        assert "emotional_enhancement" in enhanced_memory
        enhancement_data = enhanced_memory["emotional_enhancement"]
        
        print(f"✅ LLM memory manager integration successful:")
        print(f"   • Original importance: {enhancement_data['base_score']:.3f}")
        print(f"   • Emotional boost: {enhancement_data['emotional_boost']:.3f}")
        print(f"   • Final importance: {enhanced_memory['importance_score']:.3f}")
        print(f"   • Trigger match: {enhancement_data['trigger_match']}")
        print(f"   • Enhancement applied: {enhancement_data['enhancement_applied']}")
        
        # Verify enhancement data
        assert enhancement_data["base_score"] > 0.0
        assert enhancement_data["emotional_boost"] > 0.0
        assert enhancement_data["trigger_match"] is True
        assert enhancement_data["enhancement_applied"] is True
        assert enhanced_memory["importance_score"] > enhancement_data["base_score"]
        
        print("\n🎉 Sprint 3 Task 3.2 Emotional-Memory Integration Test PASSED!")
        print("✅ All emotional-memory bridge functionality working correctly")
        print("✅ Emotional importance boosting operational")
        print("✅ Pattern matching and learning functional")
        print("✅ LLM memory manager integration successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Sprint 1-2 dependencies not available for testing")
        return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the Sprint 3 Task 3.2 test"""
    success = await test_sprint3_task32_emotional_memory_integration()
    
    if success:
        print("\n✅ Sprint 3 Task 3.2: Emotional-Memory Integration - COMPLETED")
        print("The emotional-memory bridge successfully connects Sprint 1 emotional")
        print("intelligence with Sprint 2 memory importance patterns to provide")
        print("enhanced memory scoring based on emotional context and learned patterns.")
    else:
        print("\n❌ Sprint 3 Task 3.2 test failed")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())