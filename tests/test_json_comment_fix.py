#!/usr/bin/env python3
"""
Test script to verify the JSON comment removal fix is working correctly
"""
import re
import json

# Test JSON with comments that was causing the issue
test_json_with_comments = """
{
  "user_facts": [
    {
      "fact": "I'm a fan of pizza",
      "category": "preference", 
      "confidence": 0.95, // Assuming this is a clear and persistent fact
      "reasoning": "It's a common interest that many people share"
    },
    {
      "fact": "I'm a teacher by profession",
      "category": "personal_info", 
      "confidence": 0.95, // Assuming this is a clear and persistent fact
      "reasoning": "It's a profession that many people aspire to"
    },
    {
      "fact": "I enjoy playing guitar",
      "category": "hobby", 
      "confidence": 0.95, // Assuming this is a clear and persistent fact
      "reasoning": "It's a hobby that many people enjoy"
    }
  ]
}
"""


# Test the comment removal function used in the fix
def clean_json_comments(response_text):
    """Remove JSON comments like the fix does - improved version"""
    # Remove single-line comments but avoid URLs
    # Look for // that are not preceded by http: or https:
    response_text = re.sub(r"(?<!http:)(?<!https:)//.*?(?=[\r\n]|$)", "", response_text)
    # Remove multi-line comments
    response_text = re.sub(r"/\*.*?\*/", "", response_text, flags=re.DOTALL)
    # Remove trailing commas that make JSON invalid
    response_text = re.sub(r",(\s*[}\]])", r"\1", response_text)
    return response_text.strip()


def test_json_comment_removal():
    """Test that the comment removal fix works correctly"""
    print("Testing JSON comment removal fix...")
    print("=" * 50)

    # Test the original problematic JSON
    print("Original JSON with comments:")
    print(test_json_with_comments)
    print("\n" + "=" * 50)

    # Clean the JSON
    cleaned_json = clean_json_comments(test_json_with_comments)
    print("JSON after comment removal:")
    print(cleaned_json)
    print("\n" + "=" * 50)

    # Try to parse it
    try:
        parsed_data = json.loads(cleaned_json)
        print("✅ SUCCESS: JSON parsed successfully!")
        print(f"Found {len(parsed_data['user_facts'])} user facts:")
        for i, fact in enumerate(parsed_data["user_facts"], 1):
            print(
                f"  {i}. {fact['fact']} (category: {fact['category']}, confidence: {fact['confidence']})"
            )
        return True
    except json.JSONDecodeError as e:
        print(f"❌ FAILED: JSON parsing error: {e}")
        return False


def test_edge_cases():
    """Test various edge cases for comment removal"""
    print("\n" + "=" * 50)
    print("Testing edge cases...")

    test_cases = [
        # Single line comment at end
        '{"test": "value"} // comment',
        # Single line comment in middle
        '{\n  "test": "value", // comment\n  "other": "value2"\n}',
        # Multi-line comment
        '{\n  "test": "value",\n  /* multi\n     line\n     comment */\n  "other": "value2"\n}',
        # Mixed comments
        '{\n  "test": "value", // single comment\n  /* multi comment */\n  "other": "value2"\n}',
        # URL in string (should not be affected)
        '{"url": "http://example.com/path"}',
        # JSON without comments
        '{"clean": "json", "no": "comments"}',
        # Trailing comma (the new issue we're fixing)
        '{\n  "primary_emotion": "frustrated",\n  "confidence": 0.85,\n  "reasoning": "The user sent a greeting message",\n}',
        # Trailing comma in array
        '{\n  "emotions": ["happy", "excited",],\n  "confidence": 0.9\n}',
    ]

    all_passed = True
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Input:  {repr(test_case)}")
        cleaned = clean_json_comments(test_case)
        print(f"Output: {repr(cleaned)}")

        try:
            json.loads(cleaned)
            print("✅ Valid JSON after cleaning")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            all_passed = False

    return all_passed


if __name__ == "__main__":
    success1 = test_json_comment_removal()
    success2 = test_edge_cases()

    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED! The JSON comment removal fix is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
