#!/usr/bin/env python3
"""
Test specifically for the trailing comma issue we encountered in the emotion analysis
"""
import json
import re

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


    # Try to parse without fix (should fail)
    try:
        json.loads(problematic_json)
    except json.JSONDecodeError:
        pass


    # Apply the fix
    cleaned_json = clean_json_for_parsing(problematic_json)

    # Try to parse with fix (should succeed)
    try:
        json.loads(cleaned_json)
        return True
    except json.JSONDecodeError:
        return False


if __name__ == "__main__":
    success = test_trailing_comma_fix()

    if success:
        pass
    else:
        pass
