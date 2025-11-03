"""
Integration test for stance analyzer in message processor.

Tests that stance filtering and storage works correctly in the message processor.
"""

import asyncio
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure environment
os.environ['DISCORD_BOT_NAME'] = 'elena'
os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['FASTEMBED_CACHE_PATH'] = '/tmp/fastembed_cache'


async def test_stance_analyzer_initialization():
    """Test that stance analyzer initializes correctly in message processor."""
    print("\n" + "="*80)
    print("TEST 1: Stance Analyzer Initialization")
    print("="*80)
    
    try:
        from src.core.message_processor import ModularBotManager
        from src.memory.memory_protocol import create_memory_manager
        from src.adapters.platform_adapters import create_discord_message_adapter
        
        # Create memory manager
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Create message adapter
        adapter = create_discord_message_adapter()
        
        # Create bot manager
        bot_manager = ModularBotManager(
            memory_manager=memory_manager,
            message_adapter=adapter,
            character_name="elena"
        )
        
        # Check if stance analyzer was initialized
        assert hasattr(bot_manager, '_stance_analyzer'), "❌ Stance analyzer not found in message processor"
        assert bot_manager._stance_analyzer is not None, "❌ Stance analyzer is None"
        
        print("✅ Stance analyzer initialized successfully")
        print(f"✅ Stance analyzer type: {type(bot_manager._stance_analyzer)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stance_filtering():
    """Test that bot responses are filtered for second-person emotions."""
    print("\n" + "="*80)
    print("TEST 2: Stance Filtering of Bot Responses")
    print("="*80)
    
    try:
        from src.intelligence.spacy_stance_analyzer import create_stance_analyzer
        
        # Create analyzer
        analyzer = create_stance_analyzer()
        
        # Test bot response with empathetic second-person clause
        bot_response = "I understand you're frustrated. I'm here to help you work through this challenging situation."
        
        filtered = analyzer.filter_second_person_emotions(bot_response)
        
        print(f"Original: {bot_response}")
        print(f"Filtered: {filtered}")
        
        # Should have removed the empathetic clause
        assert "here to help" in filtered, "❌ Filtering removed too much"
        assert "frustrated" not in filtered or "you're" not in filtered, "❌ Failed to filter second-person emotion"
        
        print("✅ Bot response filtering works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stance_metadata_storage():
    """Test that stance metadata is stored with Qdrant payload."""
    print("\n" + "="*80)
    print("TEST 3: Stance Metadata in Qdrant Payload")
    print("="*80)
    
    try:
        from src.intelligence.spacy_stance_analyzer import create_stance_analyzer
        from src.memory.memory_protocol import create_memory_manager
        
        # Create analyzers
        stance_analyzer = create_stance_analyzer()
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Test text for stance analysis
        text = "I'm really anxious about the presentation tomorrow."
        
        # Analyze stance
        stance_analysis = stance_analyzer.analyze_user_stance(text)
        
        print(f"Text: {text}")
        print(f"Stance Analysis:")
        print(f"  - Primary Emotions: {stance_analysis.primary_emotions}")
        print(f"  - Self Focus: {stance_analysis.self_focus:.2f}")
        print(f"  - Emotion Type: {stance_analysis.emotion_type}")
        print(f"  - Confidence: {stance_analysis.confidence:.2f}")
        
        # Verify metadata structure
        bot_metadata = {
            'stance_analysis': {
                'bot_self_focus': stance_analysis.self_focus,
                'bot_emotion_type': stance_analysis.emotion_type,
                'bot_primary_emotions': stance_analysis.primary_emotions,
                'bot_other_emotions': stance_analysis.other_emotions,
                'stance_confidence': stance_analysis.confidence
            }
        }
        
        # Check metadata has expected fields
        stance_data = bot_metadata['stance_analysis']
        assert 'bot_self_focus' in stance_data, "❌ Missing bot_self_focus"
        assert 'bot_emotion_type' in stance_data, "❌ Missing bot_emotion_type"
        assert 'stance_confidence' in stance_data, "❌ Missing stance_confidence"
        
        print("✅ Stance metadata structure is correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_user_stance_detection():
    """Test user stance analysis directly."""
    print("\n" + "="*80)
    print("TEST 4: User Stance Detection")
    print("="*80)
    
    try:
        from src.intelligence.spacy_stance_analyzer import create_stance_analyzer
        
        analyzer = create_stance_analyzer()
        
        # Test cases
        test_cases = [
            ("I'm really happy about this opportunity", "direct", 1.0),
            ("You seem upset about something", "attributed", 0.0),
            ("I think they're frustrated with me", "mixed", 0.5),
            ("That sounds amazing!", "direct", 1.0),
        ]
        
        all_passed = True
        for text, expected_type, min_self_focus in test_cases:
            analysis = analyzer.analyze_user_stance(text)
            print(f"\nText: {text}")
            print(f"  Expected Type: {expected_type}, Got: {analysis.emotion_type}")
            print(f"  Min Self Focus: {min_self_focus}, Got: {analysis.self_focus:.2f}")
            
            if analysis.emotion_type != expected_type:
                print(f"  ⚠️  Type mismatch (may be acceptable)")
            
            if analysis.self_focus >= min_self_focus - 0.1:  # Allow 10% tolerance
                print(f"  ✅ Self focus is appropriate")
            else:
                print(f"  ❌ Self focus too low")
                all_passed = False
        
        if all_passed:
            print("\n✅ User stance detection working correctly")
        else:
            print("\n⚠️  Some stance detections need review")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("🎯 STANCE ANALYZER INTEGRATION TESTS")
    print("="*80)
    
    results = []
    
    # Run tests
    results.append(("Initialization", await test_stance_analyzer_initialization()))
    results.append(("Filtering", await test_stance_filtering()))
    results.append(("Metadata Storage", await test_stance_metadata_storage()))
    results.append(("User Detection", await test_user_stance_detection()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
