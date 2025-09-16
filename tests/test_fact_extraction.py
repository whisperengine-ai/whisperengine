"""
Test script for automatic fact extraction feature
"""

import sys
import logging
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from fact_extractor import FactExtractor


def test_fact_extraction():
    """Test the fact extraction functionality"""
    print("🧪 Testing Automatic Fact Extraction Feature")
    print("=" * 50)

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

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}/{total_tests}: {test_case['message']}")

        try:
            extracted_facts = extractor.extract_facts_from_message(test_case["message"])

            if extracted_facts:
                print(f"   ✅ Extracted {len(extracted_facts)} facts:")
                for fact in extracted_facts:
                    confidence_emoji = (
                        "🟢"
                        if fact["confidence"] >= 0.8
                        else "🟡" if fact["confidence"] >= 0.6 else "🔴"
                    )
                    print(
                        f"      {confidence_emoji} {fact['fact']} (confidence: {fact['confidence']:.1%}, category: {fact['category']})"
                    )
                passed_tests += 1
            else:
                print("   ❌ No facts extracted")

        except Exception as e:
            print(f"   💥 Error during extraction: {e}")

    print(f"\n📊 Results: {passed_tests}/{total_tests} tests extracted facts successfully")

    if passed_tests == total_tests:
        print("🎉 All tests passed! Automatic fact extraction is working correctly.")
    elif passed_tests > 0:
        print("⚠️ Some tests passed. The feature is partially working.")
    else:
        print("❌ All tests failed. There may be an issue with the fact extraction.")

    return passed_tests == total_tests


def main():
    """Main test function"""
    print("Discord Bot - Automatic Fact Extraction Test")
    print("This tests the new automatic fact discovery feature")
    print()

    try:
        success = test_fact_extraction()

        if success:
            print(
                "\n🚀 Ready to use! The automatic fact extraction feature has been successfully added to your Discord bot."
            )
            print("\nTo enable it:")
            print("1. Start your bot: python basic_discord_bot.py")
            print("2. Use the command: !auto_facts on")
            print("3. Have conversations and watch facts get automatically extracted!")
            print("\nNew commands available:")
            print("- !auto_facts [on/off] - Toggle automatic fact extraction")
            print("- !auto_extracted_facts - View automatically discovered facts")
            print("- !extract_facts <message> - Test fact extraction on any message")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

    return success


if __name__ == "__main__":
    main()
