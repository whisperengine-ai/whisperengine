"""
Enhanced Memory Surprise Integration Test
Test integration of enhanced memory surprise system with character learning detector
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.characters.learning.character_learning_moment_detector import (
    CharacterLearningMomentDetector,
    LearningMomentContext,
    LearningMomentType
)

class MockMemoryManager:
    """Mock memory manager for integration testing."""
    
    async def retrieve_relevant_memories(self, user_id: str, query: str, limit: int, memory_type: str = None):
        """Mock memory retrieval."""
        # Create datetime objects for realistic testing
        base_time = datetime.now() - timedelta(days=30)  # 30 days ago
        return [
            {
                'id': 'test_mem_1',
                'content': 'I love hiking in beautiful mountain trails during autumn',
                'timestamp': base_time,  # datetime object instead of string
                'score': 0.85
            }
        ]

async def test_enhanced_integration():
    """Test enhanced memory surprise integration with character learning detector."""
    print("🔗 Testing Enhanced Memory Surprise Integration")
    print("=" * 60)
    
    # Create detector with mock memory manager
    memory_manager = MockMemoryManager()
    detector = CharacterLearningMomentDetector(
        memory_manager=memory_manager
    )
    
    # Create learning context
    context = LearningMomentContext(
        user_id="test_user",
        character_name="Elena",
        current_message="I'm planning a nature walk in the mountains this weekend",
        conversation_history=[],
        emotional_context={},
        episodic_memories=[
            {
                'id': 'fallback_mem',
                'content': 'I enjoyed the mountain hike last month',
                'content_preview': 'I enjoyed the mountain hike'
            }
        ]
    )
    
    # Test learning moment detection
    learning_moments = await detector.detect_learning_moments(context)
    
    print(f"Detected {len(learning_moments)} learning moments")
    
    for moment in learning_moments:
        if moment.moment_type == LearningMomentType.MEMORY_SURPRISE:
            print(f"✅ Memory surprise detected:")
            print(f"  Confidence: {moment.confidence:.3f}")
            print(f"  Response: {moment.suggested_response}")
            print(f"  Supporting data: {moment.supporting_data}")
            
            # Check if it's enhanced or fallback
            if 'surprise_type' in moment.supporting_data:
                print(f"  🚀 Enhanced system used (type: {moment.supporting_data['surprise_type']})")
            else:
                print(f"  📦 Fallback system used")
            
            return True
    
    print("❌ No memory surprises detected")
    return False

async def main():
    """Run integration test."""
    try:
        success = await test_enhanced_integration()
        if success:
            print("\n✅ Enhanced memory surprise integration test PASSED")
        else:
            print("\n❌ Enhanced memory surprise integration test FAILED")
        return success
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())