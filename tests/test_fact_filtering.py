#!/usr/bin/env python3
"""
Test improved fact filtering to ensure bad facts are not extracted
"""
import logging
from lmstudio_client import LMStudioClient
from fact_extractor import FactExtractor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_fact_filtering():
    """Test that the improved fact extraction rejects inappropriate facts"""

    # Test messages with various types of content
    test_messages = [
        # GOOD facts (should be extracted)
        ("My name is Mark", ["My name is Mark", "name is Mark"]),  # Identity
        ("I like pizza", ["likes pizza"]),  # Preference
        ("I work as a teacher", ["works as a teacher"]),  # Job
        ("I have a dog named Max", ["has a dog named Max"]),  # Pet/relationship
        ("I live in California", ["lives in California"]),  # Location
        ("I play guitar", ["plays guitar"]),  # Hobby
        # BAD facts (should be rejected)
        ("I am feeling happy", []),  # Temporary emotion
        ("I am calm", []),  # Temporary state
        ("The user is feeling calm and happy", []),  # Emotional state
        ("I am going to listen to happy songs", []),  # Immediate intention
        ("I am asking for my name", []),  # Conversational context
        ("I am currently tired", []),  # Temporary condition
        ("I am responding to your question", []),  # Conversational response
        ("I will go to the store later", []),  # Future plan
        ("Right now I am excited", []),  # Temporal emotion
        ("Today I am feeling good", []),  # Daily emotion
    ]

    try:
        # Initialize LLM client and fact extractor
        llm_client = LMStudioClient()

        if not llm_client.check_connection():
            print("❌ LLM server not available - skipping LLM tests")
            return False

        fact_extractor = FactExtractor(llm_client)

        print("🧪 Testing improved fact filtering...")
        print("=" * 60)

        all_passed = True

        for message, expected_keywords in test_messages:
            print(f"\n📝 Testing: '{message}'")

            try:
                # Extract facts using the improved system
                extracted_facts = fact_extractor.extract_facts_from_message(message)

                print(f"   Extracted {len(extracted_facts)} facts:")
                for fact in extracted_facts:
                    print(f"     - {fact['fact']} (confidence: {fact['confidence']:.2f})")

                # Check if extraction matches expectations
                if not expected_keywords:
                    # Should extract no facts
                    if extracted_facts:
                        print(f"   ❌ FAIL: Expected no facts, but got {len(extracted_facts)}")
                        all_passed = False
                    else:
                        print("   ✅ PASS: Correctly rejected inappropriate fact")
                else:
                    # Should extract facts containing the expected keywords
                    if not extracted_facts:
                        print(
                            f"   ❌ FAIL: Expected facts with keywords {expected_keywords}, but got none"
                        )
                        all_passed = False
                    else:
                        found_match = False
                        for fact in extracted_facts:
                            for keyword in expected_keywords:
                                if keyword.lower() in fact["fact"].lower():
                                    found_match = True
                                    break
                            if found_match:
                                break

                        if found_match:
                            print("   ✅ PASS: Extracted appropriate fact")
                        else:
                            print(
                                f"   ❌ FAIL: No fact contained expected keywords {expected_keywords}"
                            )
                            all_passed = False

            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                all_passed = False

        print("\n" + "=" * 60)
        if all_passed:
            print("✅ ALL TESTS PASSED: Fact filtering is working correctly!")
        else:
            print("❌ SOME TESTS FAILED: Fact filtering needs more work")

        return all_passed

    except Exception as e:
        print(f"❌ Test setup error: {e}")
        return False


def main():
    """Run the fact filtering tests"""
    success = test_fact_filtering()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
