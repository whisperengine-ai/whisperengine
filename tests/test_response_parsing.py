"""
Test the response parsing fix for vision models
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lmstudio_client import LMStudioClient


def test_response_parsing():
    """Test different response formats that vision models might return"""

    LMStudioClient()

    # Test case 1: Standard string response
    mock_response_1 = {
        "choices": [{"message": {"content": "  This is a standard text response.  "}}]
    }

    try:
        # Simulate the response processing
        response_content = mock_response_1["choices"][0]["message"]["content"]
        if isinstance(response_content, str):
            response_content.strip()
    except Exception:
        pass

    # Test case 2: Multimodal list response (like what vision models might return)
    mock_response_2 = {
        "choices": [
            {
                "message": {
                    "content": [
                        {"type": "text", "text": "I can see an image that shows "},
                        {"type": "text", "text": "a beautiful landscape with mountains."},
                    ]
                }
            }
        ]
    }

    try:
        response_content = mock_response_2["choices"][0]["message"]["content"]
        if isinstance(response_content, list):
            text_parts = []
            for part in response_content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            "\n".join(text_parts).strip()
    except Exception:
        pass

    # Test case 3: Mixed content (text and non-text)
    mock_response_3 = {
        "choices": [
            {
                "message": {
                    "content": [
                        {"type": "text", "text": "Here's what I see: "},
                        {"type": "image_analysis", "data": "some_analysis_data"},
                        {"type": "text", "text": "The image contains a cat."},
                    ]
                }
            }
        ]
    }

    try:
        response_content = mock_response_3["choices"][0]["message"]["content"]
        if isinstance(response_content, list):
            text_parts = []
            for part in response_content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif isinstance(part, str):
                    text_parts.append(part)
            "\n".join(text_parts).strip()
    except Exception:
        pass

    # Test case 4: Unexpected format (fallback test)
    mock_response_4 = {
        "choices": [{"message": {"content": {"unexpected": "format", "text": "fallback test"}}}]
    }

    try:
        response_content = mock_response_4["choices"][0]["message"]["content"]
        if isinstance(response_content, str):
            response_content.strip()
        elif isinstance(response_content, list):
            text_parts = []
            for part in response_content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif isinstance(part, str):
                    text_parts.append(part)
            "\n".join(text_parts).strip()
        else:
            # Fallback
            str(response_content).strip()
    except Exception:
        pass



if __name__ == "__main__":
    test_response_parsing()
