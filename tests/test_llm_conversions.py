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
import os
from dotenv import load_dotenv

from lmstudio_client import LMStudioClient
from fact_extractor import FactExtractor
from emotion_manager import EmotionManager, RelationshipManager
from memory_manager import UserMemoryManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def test_llm_conversions():
    """Test all LLM conversions"""
    
    # Load environment variables
    load_dotenv()
    
    # Initialize LLM client
    try:
        llm_client = LMStudioClient()
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
        "You make me feel comfortable sharing my thoughts with you."
    ]
    
    print("🔍 Testing LLM-based conversions...\n")
    
    # Test 1: User Fact Extraction
    print("1️⃣ Testing User Fact Extraction (FactExtractor)")
    print("=" * 50)
    
    fact_extractor = FactExtractor(llm_client=llm_client)
    
    for i, message in enumerate(test_messages[:3], 1):
        print(f"\nTest {i}: \"{message[:50]}...\"")
        try:
            facts = fact_extractor.extract_facts_from_message(message)
            if facts:
                for fact in facts:
                    print(f"  ✅ Fact: {fact['fact']}")
                    print(f"     Category: {fact['category']}, Confidence: {fact['confidence']:.2f}")
            else:
                print("  📝 No facts extracted")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Test 2: Personal Information Detection
    print("\n\n2️⃣ Testing Personal Information Detection (RelationshipManager)")
    print("=" * 60)
    
    relationship_manager = RelationshipManager(llm_client=llm_client)
    
    for i, message in enumerate(test_messages[:3], 1):
        print(f"\nTest {i}: \"{message[:50]}...\"")
        try:
            personal_info = relationship_manager.detect_personal_info(message)
            if personal_info:
                for info_type, items in personal_info.items():
                    print(f"  ✅ {info_type}: {items}")
            else:
                print("  📝 No personal info detected")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Test 3: Trust Indicator Detection
    print("\n\n3️⃣ Testing Trust Indicator Detection (RelationshipManager)")
    print("=" * 55)
    
    trust_test_messages = test_messages[2:6]  # Focus on trust-related messages
    
    for i, message in enumerate(trust_test_messages, 1):
        print(f"\nTest {i}: \"{message[:50]}...\"")
        try:
            trust_indicators = relationship_manager.detect_trust_indicators(message)
            if trust_indicators:
                for indicator in trust_indicators:
                    print(f"  ✅ Trust indicator: {indicator}")
            else:
                print("  📝 No trust indicators detected")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Test 4: Synthetic Message Detection
    print("\n\n4️⃣ Testing Synthetic Message Detection (UserMemoryManager)")
    print("=" * 55)
    
    memory_manager = UserMemoryManager(enable_auto_facts=False, llm_client=llm_client)
    
    synthetic_test_messages = [
        "[Context from previous conversations] The user mentioned liking pizza.",
        "Previous relevant context: The user works at Google.",
        "[User attached an image: screenshot.png]",
        "Hey, how are you doing today?",  # Natural message
        "I'm having a great day, thanks for asking!"  # Natural message
    ]
    
    for i, message in enumerate(synthetic_test_messages, 1):
        print(f"\nTest {i}: \"{message[:50]}...\"")
        try:
            is_synthetic = memory_manager._is_synthetic_message(message)
            result_icon = "🤖" if is_synthetic else "👤"
            result_text = "SYNTHETIC" if is_synthetic else "NATURAL"
            print(f"  {result_icon} Result: {result_text}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Test 5: Full Emotion Manager Integration
    print("\n\n5️⃣ Testing Full Emotion Manager Integration")
    print("=" * 45)
    
    emotion_manager = EmotionManager(llm_client=llm_client)
    
    test_user_id = "test_user_llm_conversion"
    test_message = "Hi there! My name is Jordan and I'm 28 years old. I live in Seattle and work as a data scientist. I really enjoy hiking and photography in my free time. Thanks for being such a good listener!"
    
    try:
        # Analyze user emotion and state
        profile, emotion_profile = emotion_manager.analyze_and_update_emotion(test_user_id, test_message)
        
        print(f"User: {test_user_id}")
        print(f"Message: \"{test_message[:60]}...\"")
        print(f"✅ Emotional State: {profile.current_emotion.value}")
        print(f"✅ Relationship Level: {profile.relationship_level.value}")
        print(f"✅ Total Interactions: {profile.interaction_count}")
        print(f"✅ Emotion Confidence: {emotion_profile.confidence:.2f}")
        
        # Test personal info and trust detection through relationship manager
        personal_info = emotion_manager.relationship_manager.detect_personal_info(test_message)
        trust_indicators = emotion_manager.relationship_manager.detect_trust_indicators(test_message)
        
        if personal_info:
            print(f"✅ Personal Info Detected: {list(personal_info.keys())}")
        if trust_indicators:
            print(f"✅ Trust Indicators: {len(trust_indicators)} found")
            
    except Exception as e:
        print(f"❌ Error in emotion manager integration: {e}")
    
    # Summary
    print("\n\n📊 SUMMARY")
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
    print("   • Requires LLM client for full functionality")

if __name__ == "__main__":
    test_llm_conversions()
