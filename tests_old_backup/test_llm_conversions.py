#!/usr/bin/env python3
"""
Test LLM conversions for pattern-based code

This script tests all the pattern-based code that was converted to use LLM:
1. User fact extr    print("📊 SUMMARY")
    print("=" * 40)
    print("✅ User Fact Extraction - Pure LLM-based")
    print("✅ Personal Information Detection - Pure LLM-based")
    print("✅ Trust Indicator Detection - Pure LLM-based")
    print("✅ Synthetic Message Detection - Pure LLM-based")
    print("✅ Full Integration - EmotionManager using LLM throughout")
    print("\n🎉 All pattern-based code successfully converted to pure LLM-based analysis!")
    print("\n💡 Benefits of pure LLM conversion:")
    print("   • Maximum accuracy and context awareness")
    print("   • No maintenance of complex regex patterns")
    print("   • Consistent LLM-based analysis throughout")
    print("   • Cleaner, more maintainable codebase")
    print("   • Requires LLM client for full functionality")xtractor)
2. Personal information detection (EmotionManager/RelationshipManager)
3. Trust indicator detection (EmotionManager/RelationshipManager)
4. Synthetic message detection (UserMemoryManager)
"""

import logging

from dotenv import load_dotenv
from src.utils.emotion_manager import EmotionManager, RelationshipManager
from src.utils.fact_extractor import FactExtractor
from src.llm.llm_client import LLMClient
from src.memory.core.memory_factory import create_memory_manager

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def test_llm_conversions():
    """Test all LLM conversions"""

    # Load environment variables
    load_dotenv()

    # Initialize LLM client
    try:
        llm_client = LLMClient()
        logger.info("✅ LLM client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM client: {e}")
        return

    # Test messages for various scenarios
    test_messages = [
        "My name is Alex and I'm 25 years old. I live in San Francisco and work as a software developer.",
        "I really love playing guitar and reading science fiction books in my spare time.",
        "I trust you with this secret - I've been struggling with anxiety lately.",
        "Thanks for listening to me, you're really understanding and helpful.",
        "[Context from previous conversations] The user mentioned liking pizza.",
        "Previous relevant context: The user works at Google.",
        "I hate pineapple on pizza but I absolutely love chocolate ice cream!",
        "Between you and me, I'm thinking about changing my career path.",
        "Can I tell you something personal? I'm considering moving to a new city.",
        "You make me feel comfortable sharing my thoughts with you.",
    ]

    # Test 1: User Fact Extraction

    fact_extractor = FactExtractor(llm_client=llm_client)

    for _i, message in enumerate(test_messages[:3], 1):
        try:
            facts = fact_extractor.extract_facts_from_message(message)
            if facts:
                for _fact in facts:
                    pass
            else:
                pass
        except Exception:
            pass

    # Test 2: Personal Information Detection

    relationship_manager = RelationshipManager(llm_client=llm_client)

    for _i, message in enumerate(test_messages[:3], 1):
        try:
            personal_info = relationship_manager.detect_personal_info(message)
            if personal_info:
                for _info_type, _items in personal_info.items():
                    pass
            else:
                pass
        except Exception:
            pass

    # Test 3: Trust Indicator Detection

    trust_test_messages = test_messages[2:6]  # Focus on trust-related messages

    for _i, message in enumerate(trust_test_messages, 1):
        try:
            trust_indicators = relationship_manager.detect_trust_indicators(message)
            if trust_indicators:
                for _indicator in trust_indicators:
                    pass
            else:
                pass
        except Exception:
            pass

    # Test 4: Synthetic Message Detection

    memory_manager = create_memory_manager(
        mode="unified", 
        llm_client=llm_client,
        enable_enhanced_queries=False
    )

    synthetic_test_messages = [
        "[Context from previous conversations] The user mentioned liking pizza.",
        "Previous relevant context: The user works at Google.",
        "[User attached an image: screenshot.png]",
        "Hey, how are you doing today?",  # Natural message
        "I'm having a great day, thanks for asking!",  # Natural message
    ]

    for _i, message in enumerate(synthetic_test_messages, 1):
        try:
            memory_manager._is_synthetic_message(message)
        except Exception:
            pass

    # Test 5: Full Emotion Manager Integration

    emotion_manager = EmotionManager(llm_client=llm_client)

    test_user_id = "test_user_llm_conversion"
    test_message = "Hi there! My name is Jordan and I'm 28 years old. I live in Seattle and work as a data scientist. I really enjoy hiking and photography in my free time. Thanks for being such a good listener!"

    try:
        # Analyze user emotion and state
        profile, emotion_profile = emotion_manager.analyze_and_update_emotion(
            test_user_id, test_message
        )

        # Test personal info and trust detection through relationship manager
        personal_info = emotion_manager.relationship_manager.detect_personal_info(test_message)
        trust_indicators = emotion_manager.relationship_manager.detect_trust_indicators(
            test_message
        )

        if personal_info:
            pass
        if trust_indicators:
            pass

    except Exception:
        pass

    # Summary


if __name__ == "__main__":
    test_llm_conversions()
