#!/usr/bin/env python3
"""
Test script to verify the improved JSON parsing error handling in user fact extraction
"""

import sys
import os
import json
import logging

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lmstudio_client import LMStudioClient
from exceptions import LLMError

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_malformed_json_handling():
    """Test handling of malformed JSON responses"""

    # Create a mock LLM client to test JSON parsing
    client = LMStudioClient()

    # Test cases of malformed JSON that we've seen
    test_cases = [
        # Case 1: Missing opening brace and fact field (the actual error we saw)
        """{
  "user_facts": [
    {
      "fact": "name is Cynthia",
      "category": "personal_info",
      "confidence": 1.0,
      "reasoning": "The message explicitly states 'My name is Cynthia by the way.'"
    },
    "category": "relationship",
    "confidence": 1.0,
      "reasoning": "The message indicates a 'officially' meeting, suggesting a relationship context."
    }
  ]
}""",
        # Case 2: Valid JSON for comparison
        """{
  "user_facts": [
    {
      "fact": "name is Cynthia",
      "category": "personal_info",
      "confidence": 1.0,
      "reasoning": "The message explicitly states 'My name is Cynthia by the way.'"
    }
  ]
}""",
        # Case 3: Empty facts
        '{"user_facts": []}',
        # Case 4: Completely malformed
        '{"user_facts": [{"fact": "incomplete',
    ]

    for i, test_json in enumerate(test_cases):
        print(f"\n--- Test Case {i+1} ---")
        print(f"Input JSON: {test_json[:100]}{'...' if len(test_json) > 100 else ''}")

        try:
            # Simulate the JSON parsing logic from extract_user_facts
            response_text = test_json.strip()

            # Apply the same cleaning logic
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

            # Try to parse
            try:
                fact_data = json.loads(response_text)
                print(f"✓ Successfully parsed JSON: {len(fact_data.get('user_facts', []))} facts")

            except json.JSONDecodeError as e:
                print(f"✗ JSON parsing failed: {e}")

                # Apply the same fix logic
                import re

                fixed_text = response_text

                # Look for malformed patterns
                malformed_pattern = r'}\s*,\s*"(category|confidence|reasoning)":'
                if re.search(malformed_pattern, fixed_text):
                    print("  → Detected malformed array element - returning empty facts")
                    result = {"user_facts": []}
                else:
                    # Look for missing fact field
                    pattern_no_fact = r'\{\s*"(?:category|confidence|reasoning)":'
                    if re.search(pattern_no_fact, fixed_text):
                        print("  → Detected object missing 'fact' field - extracting valid facts")

                        complete_facts = []
                        fact_pattern = r'\{\s*"fact"\s*:\s*"[^"]*"[^}]*\}'
                        fact_matches = re.finditer(fact_pattern, fixed_text, re.DOTALL)

                        for match in fact_matches:
                            try:
                                fact_json = match.group(0)
                                fact_obj = json.loads(fact_json)
                                if "fact" in fact_obj and "category" in fact_obj:
                                    complete_facts.append(fact_obj)
                                    print(f"    → Extracted valid fact: {fact_obj['fact']}")
                            except json.JSONDecodeError:
                                continue

                        result = {"user_facts": complete_facts}
                    else:
                        print("  → No specific fix pattern matched - returning empty facts")
                        result = {"user_facts": []}

                print(f"  → Final result: {len(result.get('user_facts', []))} facts")

        except Exception as e:
            print(f"✗ Unexpected error: {e}")


if __name__ == "__main__":
    print("Testing improved JSON parsing error handling for user fact extraction")
    test_malformed_json_handling()
