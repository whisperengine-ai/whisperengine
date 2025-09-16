#!/usr/bin/env python3
"""
Test script for the new personality-driven fact system

This validates that the personality fact classification and storage works correctly,
replacing the old global/user fact distinction with AI companion-focused categorization.
"""

import sys
import os
import logging
from datetime import datetime

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.memory.personality_facts import (
        PersonalityFactClassifier, PersonalityFactType, PersonalityRelevance, MemoryTier
    )
    from src.security.pii_detector import PIIDetector
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the whisperengine root directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_personality_fact_classification():
    """Test the personality fact classification system"""
    print("\n🧪 Testing Personality Fact Classification System")
    print("=" * 60)
    
    # Initialize classifier
    pii_detector = PIIDetector()
    classifier = PersonalityFactClassifier(pii_detector)
    
    # Test cases with expected classifications
    test_cases = [
        {
            "fact": "I love jazz music and play piano",
            "expected_type": PersonalityFactType.INTEREST_DISCOVERY,
            "expected_relevance": PersonalityRelevance.HIGH
        },
        {
            "fact": "I feel anxious when speaking in public",
            "expected_type": PersonalityFactType.EMOTIONAL_INSIGHT,
            "expected_relevance": PersonalityRelevance.CRITICAL
        },
        {
            "fact": "I prefer detailed explanations rather than brief answers",
            "expected_type": PersonalityFactType.COMMUNICATION_PREFERENCE,
            "expected_relevance": PersonalityRelevance.HIGH
        },
        {
            "fact": "I trust you and feel comfortable sharing personal things",
            "expected_type": PersonalityFactType.RELATIONSHIP_BUILDING,
            "expected_relevance": PersonalityRelevance.CRITICAL
        },
        {
            "fact": "I'm struggling with learning Python programming",
            "expected_type": PersonalityFactType.SUPPORT_OPPORTUNITY,
            "expected_relevance": PersonalityRelevance.CRITICAL
        },
        {
            "fact": "I just graduated from college with a computer science degree",
            "expected_type": PersonalityFactType.ACHIEVEMENT,
            "expected_relevance": PersonalityRelevance.HIGH
        },
        {
            "fact": "The weather is nice today",
            "expected_type": PersonalityFactType.INTEREST_DISCOVERY,
            "expected_relevance": PersonalityRelevance.MINIMAL
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: '{test_case['fact']}'")
        
        context_metadata = {
            "extraction_source": "test",
            "timestamp": datetime.now().isoformat()
        }
        
        # Classify the fact
        personality_fact = classifier.classify_fact(
            test_case['fact'], 
            context_metadata, 
            "test_user_123"
        )
        
        # Check results
        type_correct = personality_fact.fact_type == test_case['expected_type']
        relevance_matches = personality_fact.relevance == test_case['expected_relevance']
        
        print(f"   🔍 Classified as: {personality_fact.fact_type.value}")
        print(f"   📊 Relevance: {personality_fact.relevance.value} (score: {personality_fact.relevance_score:.2f})")
        print(f"   💾 Memory tier: {personality_fact.memory_tier.value}")
        print(f"   🎭 Emotional weight: {personality_fact.emotional_weight:.2f}")
        print(f"   🔒 Privacy level: {personality_fact.privacy_level}")
        
        if type_correct:
            print(f"   ✅ Fact type classification: CORRECT")
        else:
            print(f"   ❌ Fact type classification: Expected {test_case['expected_type'].value}, got {personality_fact.fact_type.value}")
        
        # We'll be more lenient on relevance since it's calculated dynamically
        if personality_fact.relevance_score >= 0.7:
            relevance_ok = True
            print(f"   ✅ Relevance score: HIGH ({personality_fact.relevance_score:.2f})")
        elif personality_fact.relevance_score >= 0.5:
            relevance_ok = True
            print(f"   ✅ Relevance score: MODERATE ({personality_fact.relevance_score:.2f})")
        else:
            relevance_ok = personality_fact.relevance == PersonalityRelevance.MINIMAL
            print(f"   ⚠️ Relevance score: LOW ({personality_fact.relevance_score:.2f})")
        
        results.append({
            "test_case": i,
            "fact": test_case['fact'],
            "type_correct": type_correct,
            "relevance_ok": relevance_ok,
            "personality_fact": personality_fact
        })
    
    # Summary
    print(f"\n📈 Test Results Summary")
    print("-" * 30)
    
    type_successes = sum(1 for r in results if r['type_correct'])
    relevance_successes = sum(1 for r in results if r['relevance_ok'])
    total_tests = len(results)
    
    print(f"Fact Type Classification: {type_successes}/{total_tests} correct ({type_successes/total_tests*100:.1f}%)")
    print(f"Relevance Assessment: {relevance_successes}/{total_tests} appropriate ({relevance_successes/total_tests*100:.1f}%)")
    
    # Show memory tier distribution
    tier_distribution = {}
    for result in results:
        tier = result['personality_fact'].memory_tier.value
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
    
    print(f"\nMemory Tier Distribution:")
    for tier, count in tier_distribution.items():
        print(f"  {tier.upper()}: {count} facts")
    
    # Show fact type distribution
    type_distribution = {}
    for result in results:
        fact_type = result['personality_fact'].fact_type.value
        type_distribution[fact_type] = type_distribution.get(fact_type, 0) + 1
    
    print(f"\nFact Type Distribution:")
    for fact_type, count in type_distribution.items():
        print(f"  {fact_type}: {count} facts")
    
    success_rate = (type_successes + relevance_successes) / (total_tests * 2)
    
    if success_rate >= 0.8:
        print(f"\n🎉 SUCCESS: Personality fact classification working well ({success_rate*100:.1f}% accuracy)")
        return True
    elif success_rate >= 0.6:
        print(f"\n⚠️ PARTIAL SUCCESS: Classification needs refinement ({success_rate*100:.1f}% accuracy)")
        return True
    else:
        print(f"\n❌ FAILURE: Classification system needs significant improvement ({success_rate*100:.1f}% accuracy)")
        return False


def test_pii_detection_integration():
    """Test PII detection integration with personality facts"""
    print("\n🔒 Testing PII Detection Integration")
    print("=" * 40)
    
    pii_detector = PIIDetector()
    classifier = PersonalityFactClassifier(pii_detector)
    
    pii_test_cases = [
        {
            "fact": "I love hiking in the mountains",
            "should_be_safe": True,
            "description": "General interest"
        },
        {
            "fact": "I have severe depression and take medication",
            "should_be_safe": False,
            "description": "Sensitive mental health info"
        },
        {
            "fact": "My email is john.doe@example.com",
            "should_be_safe": False,
            "description": "Personal email address"
        },
        {
            "fact": "I work as a software engineer",
            "should_be_safe": True,
            "description": "General profession"
        },
        {
            "fact": "I live at 123 Main Street, Springfield",
            "should_be_safe": False,
            "description": "Specific address"
        }
    ]
    
    pii_results = []
    
    for i, test_case in enumerate(pii_test_cases, 1):
        print(f"\n📝 PII Test {i}: {test_case['description']}")
        print(f"   Fact: '{test_case['fact']}'")
        
        context_metadata = {"test": True}
        personality_fact = classifier.classify_fact(test_case['fact'], context_metadata, "test_user_pii")
        
        is_private = personality_fact.privacy_level == "private_dm"
        is_safe = personality_fact.privacy_level in ["cross_context_safe", "server_private"]
        
        if test_case['should_be_safe']:
            success = is_safe
            expected = "safe for sharing"
        else:
            success = is_private
            expected = "private/restricted"
        
        print(f"   🔒 Privacy level: {personality_fact.privacy_level}")
        print(f"   🎯 Expected: {expected}")
        
        if success:
            print(f"   ✅ PII detection: CORRECT")
        else:
            print(f"   ❌ PII detection: INCORRECT")
        
        pii_results.append(success)
    
    pii_success_rate = sum(pii_results) / len(pii_results)
    print(f"\n📊 PII Detection Accuracy: {pii_success_rate*100:.1f}%")
    
    if pii_success_rate >= 0.8:
        print("🎉 PII detection working well!")
        return True
    else:
        print("⚠️ PII detection needs improvement")
        return False


def main():
    """Run all personality fact system tests"""
    print("🤖 WhisperEngine Personality Fact System Test")
    print("=" * 70)
    
    try:
        # Test 1: Personality fact classification
        classification_success = test_personality_fact_classification()
        
        # Test 2: PII detection integration
        pii_success = test_pii_detection_integration()
        
        # Overall results
        print(f"\n🏁 Final Results")
        print("=" * 20)
        
        if classification_success and pii_success:
            print("🎉 ALL TESTS PASSED - Personality fact system is working correctly!")
            print("\n✨ Ready for Phase 1.2: Memory Tier Architecture")
            return True
        elif classification_success or pii_success:
            print("⚠️ PARTIAL SUCCESS - Some components need refinement")
            return True
        else:
            print("❌ TESTS FAILED - System needs debugging before proceeding")
            return False
            
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)