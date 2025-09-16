#!/usr/bin/env python3
"""
Test specifically for the trailing comma issue we encountered in the emotion analysis
"""
import re
import json

# The exact problematic JSON from the logs
problematic_json = """
{
  "primary_emotion": "frustrated",
  "confidence": 0.85,
  "intensity": 0.7,
  "secondary_emotions": [
    "disappointed",
    "angry"
  ],
  "reasoning": "The user sent a greeting message, which is typically used to initiate conversation or greet someone. The tone of the message seems polite but lacks enthusiasm.",
}
"""


def clean_json_for_parsing(response_text):
    """Apply the same cleaning logic as in lmstudio_client.py"""
    # Remove JSON comments (// style comments) that some LLMs add
    # Use negative lookbehind to avoid matching URLs (http:// or https://)
    response_text = re.sub(r"(?<!http:)(?<!https:)//.*?(?=[\r\n]|$)", "", response_text)
    response_text = re.sub(r"/\*.*?\*/", "", response_text, flags=re.DOTALL)

    # Remove trailing commas that make JSON invalid
    response_text = re.sub(r",(\s*[}\]])", r"\1", response_text)

    return response_text.strip()


def test_trailing_comma_fix():
    """Test that the specific trailing comma issue is fixed"""
    print("Testing the exact trailing comma issue from the logs...")
    print("=" * 60)

    print("Original problematic JSON:")
    print(problematic_json)
    print("\n" + "=" * 60)

    # Try to parse without fix (should fail)
    try:
        json.loads(problematic_json)
        print("❌ UNEXPECTED: Original JSON parsed without issues")
    except json.JSONDecodeError as e:
        print(f"✅ EXPECTED: Original JSON fails to parse: {e}")

    print("\n" + "=" * 60)

    # Apply the fix
    cleaned_json = clean_json_for_parsing(problematic_json)
    print("JSON after trailing comma removal:")
    print(cleaned_json)
    print("\n" + "=" * 60)

    # Try to parse with fix (should succeed)
    try:
        parsed_data = json.loads(cleaned_json)
        print("✅ SUCCESS: Cleaned JSON parsed successfully!")
        print(f"Primary emotion: {parsed_data['primary_emotion']}")
        print(f"Confidence: {parsed_data['confidence']}")
        print(f"Intensity: {parsed_data['intensity']}")
        print(f"Secondary emotions: {parsed_data['secondary_emotions']}")
        print(f"Reasoning: {parsed_data['reasoning'][:50]}...")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ FAILED: Cleaned JSON still fails to parse: {e}")
        return False


if __name__ == "__main__":
    success = test_trailing_comma_fix()

    print("\n" + "=" * 60)
    if success:
        print("🎉 TRAILING COMMA FIX VERIFIED! The emotion analysis error is resolved.")
    else:
        print("⚠️  Test failed. The fix needs more work.")
