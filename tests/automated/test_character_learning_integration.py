"""
Character Learning Integration Test
Test the character learning system directly to validate it's working
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
    LearningMomentType,
    create_character_learning_moment_detector
)

class MockMemoryManager:
    """Mock memory manager for testing."""
    
    async def retrieve_relevant_memories(self, user_id: str, query: str, limit: int, memory_type: str = None):
        """Mock memory retrieval."""
        base_time = datetime.now() - timedelta(days=30)
        return [
            {
                'id': 'hiking_memory',
                'content': 'I love hiking in beautiful mountain trails during autumn',
                'timestamp': base_time,
                'score': 0.85
            },
            {
                'id': 'nature_memory', 
                'content': 'The forest wildlife is amazing to observe',
                'timestamp': base_time - timedelta(days=15),
                'score': 0.75
            }
        ]

class MockEmotionAnalyzer:
    """Mock emotion analyzer for testing."""
    
    async def analyze_emotion(self, content: str, user_id: str):
        """Mock emotion analysis."""
        return {
            'primary_emotion': 'joy',
            'confidence': 0.9,
            'intensity': 0.7
        }

async def test_character_learning_integration():
    """Test complete character learning integration."""
    print("🧪 Testing Character Learning Integration")
    print("=" * 60)
    
    # Create mock components
    memory_manager = MockMemoryManager()
    emotion_analyzer = MockEmotionAnalyzer()
    
    # Test factory creation
    try:
        detector = create_character_learning_moment_detector(
            character_intelligence_coordinator=None,
            emotion_analyzer=emotion_analyzer,
            memory_manager=memory_manager
        )
        print("✅ Character learning moment detector created successfully")
    except Exception as e:
        print(f"❌ Failed to create detector: {str(e)}")
        return False
    
    # Create test context
    context = LearningMomentContext(
        user_id="test_user",
        character_name="Elena",
        current_message="I went hiking last month and saw incredible wildlife",
        conversation_history=[],
        emotional_context={'primary_emotion': 'joy'},
        episodic_memories=[
            {
                'id': 'hiking_memory',
                'content': 'I love hiking in beautiful mountain trails during autumn',
                'content_preview': 'I love hiking in beautiful mountain trails'
            }
        ]
    )
    
    # Test learning moment detection
    try:
        learning_moments = await detector.detect_learning_moments(context)
        print(f"✅ Learning moment detection completed")
        print(f"   Detected {len(learning_moments)} learning moments")
        
        for i, moment in enumerate(learning_moments):
            print(f"   Moment {i+1}: {moment.moment_type}")
            print(f"     Confidence: {moment.confidence:.3f}")
            print(f"     Response: {moment.suggested_response[:80]}...")
            
        return len(learning_moments) > 0
        
    except Exception as e:
        print(f"❌ Learning moment detection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run integration test."""
    try:
        success = await test_character_learning_integration()
        
        if success:
            print("\n✅ Character Learning Integration: PASSED")
        else:
            print("\n❌ Character Learning Integration: FAILED")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())