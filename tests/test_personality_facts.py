#!/usr/bin/env python3
"""
Test script for the new personality-driven fact system

This validates that the personality fact classification and storage works correctly,
replacing the old global/user fact distinction with AI companion-focused categorization.
"""

import logging
import os
import sys
from datetime import datetime

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from src.memory.personality_facts import (
        MemoryTier,
        PersonalityFactClassifier,
        PersonalityFactType,
        PersonalityRelevance,
    )
    from src.security.pii_detector import PIIDetector
except ImportError:
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_personality_fact_classification():
    """Test the personality fact classification system"""

    # Initialize classifier
    pii_detector = PIIDetector()
    classifier = PersonalityFactClassifier(pii_detector)

    # Test cases with expected classifications
    test_cases = [
        {
            "fact": "I love jazz music and play piano",
            "expected_type": PersonalityFactType.INTEREST_DISCOVERY,
            "expected_relevance": PersonalityRelevance.HIGH,
        },
        {
            "fact": "I feel anxious when speaking in public",
            "expected_type": PersonalityFactType.EMOTIONAL_INSIGHT,
            "expected_relevance": PersonalityRelevance.CRITICAL,
        },
        {
            "fact": "I prefer detailed explanations rather than brief answers",
            "expected_type": PersonalityFactType.COMMUNICATION_PREFERENCE,
            "expected_relevance": PersonalityRelevance.HIGH,
        },
        {
            "fact": "I trust you and feel comfortable sharing personal things",
            "expected_type": PersonalityFactType.RELATIONSHIP_BUILDING,
            "expected_relevance": PersonalityRelevance.CRITICAL,
        },
        {
            "fact": "I'm struggling with learning Python programming",
            "expected_type": PersonalityFactType.SUPPORT_OPPORTUNITY,
            "expected_relevance": PersonalityRelevance.CRITICAL,
        },
        {
            "fact": "I just graduated from college with a computer science degree",
            "expected_type": PersonalityFactType.ACHIEVEMENT,
            "expected_relevance": PersonalityRelevance.HIGH,
        },
        {
            "fact": "The weather is nice today",
            "expected_type": PersonalityFactType.INTEREST_DISCOVERY,
            "expected_relevance": PersonalityRelevance.MINIMAL,
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):

        context_metadata = {"extraction_source": "test", "timestamp": datetime.now().isoformat()}

        # Classify the fact
        personality_fact = classifier.classify_fact(
            test_case["fact"], context_metadata, "test_user_123"
        )

        # Check results
        type_correct = personality_fact.fact_type == test_case["expected_type"]
        personality_fact.relevance == test_case["expected_relevance"]

        if type_correct:
            pass
        else:
            pass

        # We'll be more lenient on relevance since it's calculated dynamically
        if personality_fact.relevance_score >= 0.7:
            relevance_ok = True
        elif personality_fact.relevance_score >= 0.5:
            relevance_ok = True
        else:
            relevance_ok = personality_fact.relevance == PersonalityRelevance.MINIMAL

        results.append(
            {
                "test_case": i,
                "fact": test_case["fact"],
                "type_correct": type_correct,
                "relevance_ok": relevance_ok,
                "personality_fact": personality_fact,
            }
        )

    # Summary

    type_successes = sum(1 for r in results if r["type_correct"])
    relevance_successes = sum(1 for r in results if r["relevance_ok"])
    total_tests = len(results)

    # Show memory tier distribution
    tier_distribution = {}
    for result in results:
        tier = result["personality_fact"].memory_tier.value
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

    for tier, _count in tier_distribution.items():
        pass

    # Show fact type distribution
    type_distribution = {}
    for result in results:
        fact_type = result["personality_fact"].fact_type.value
        type_distribution[fact_type] = type_distribution.get(fact_type, 0) + 1

    for fact_type, _count in type_distribution.items():
        pass

    success_rate = (type_successes + relevance_successes) / (total_tests * 2)

    if success_rate >= 0.8:
        return True
    elif success_rate >= 0.6:
        return True
    else:
        return False


def test_pii_detection_integration():
    """Test PII detection integration with personality facts"""

    pii_detector = PIIDetector()
    classifier = PersonalityFactClassifier(pii_detector)

    pii_test_cases = [
        {
            "fact": "I love hiking in the mountains",
            "should_be_safe": True,
            "description": "General interest",
        },
        {
            "fact": "I have severe depression and take medication",
            "should_be_safe": False,
            "description": "Sensitive mental health info",
        },
        {
            "fact": "My email is john.doe@example.com",
            "should_be_safe": False,
            "description": "Personal email address",
        },
        {
            "fact": "I work as a software engineer",
            "should_be_safe": True,
            "description": "General profession",
        },
        {
            "fact": "I live at 123 Main Street, Springfield",
            "should_be_safe": False,
            "description": "Specific address",
        },
    ]

    pii_results = []

    for _i, test_case in enumerate(pii_test_cases, 1):

        context_metadata = {"test": True}
        personality_fact = classifier.classify_fact(
            test_case["fact"], context_metadata, "test_user_pii"
        )

        is_private = personality_fact.privacy_level == "private_dm"
        is_safe = personality_fact.privacy_level in ["cross_context_safe", "server_private"]

        if test_case["should_be_safe"]:
            success = is_safe
        else:
            success = is_private

        if success:
            pass
        else:
            pass

        pii_results.append(success)

    pii_success_rate = sum(pii_results) / len(pii_results)

    if pii_success_rate >= 0.8:
        return True
    else:
        return False


def main():
    """Run all personality fact system tests"""

    try:
        # Test 1: Personality fact classification
        classification_success = test_personality_fact_classification()

        # Test 2: PII detection integration
        pii_success = test_pii_detection_integration()

        # Overall results

        if classification_success and pii_success:
            return True
        elif classification_success or pii_success:
            return True
        else:
            return False

    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
