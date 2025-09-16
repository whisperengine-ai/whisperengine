"""
Test script for automatic fact extraction feature
"""

import sys
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from fact_extractor import FactExtractor


def test_fact_extraction():
    """Test the fact extraction functionality"""

    extractor = FactExtractor()

    test_cases = [
        {
            "message": "I love pizza and have a cat named Whiskers",
            "expected_facts": ["likes pizza", "has a cat named Whiskers"],
        },
        {
            "message": "I work as a software engineer in San Francisco",
            "expected_facts": ["works as software engineer"],
        },
        {
            "message": "My favorite color is blue and I am 25 years old",
            "expected_facts": ["likes blue", "is 25 years old"],
        },
        {
            "message": "I recently went to Japan for vacation",
            "expected_facts": ["visited Japan", "recently went to Japan"],
        },
        {"message": "I am learning to play the guitar", "expected_facts": ["is learning guitar"]},
    ]

    total_tests = len(test_cases)
    passed_tests = 0

    for _i, test_case in enumerate(test_cases, 1):

        try:
            extracted_facts = extractor.extract_facts_from_message(test_case["message"])

            if extracted_facts:
                for fact in extracted_facts:
                    (
                        "🟢"
                        if fact["confidence"] >= 0.8
                        else "🟡" if fact["confidence"] >= 0.6 else "🔴"
                    )
                passed_tests += 1
            else:
                pass

        except Exception:
            pass

    if passed_tests == total_tests:
        pass
    elif passed_tests > 0:
        pass
    else:
        pass

    return passed_tests == total_tests


def main():
    """Main test function"""

    try:
        success = test_fact_extraction()

        if success:
            pass

    except Exception:
        return False

    return success


if __name__ == "__main__":
    main()
