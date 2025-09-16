"""
Comprehensive test for vision message processing
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio

import pytest
from lmstudio_client import LMStudioClient


@pytest.mark.asyncio
async def test_vision_message_processing():
    """Test complete vision message processing pipeline"""


    # Set up vision support
    os.environ["LLM_SUPPORTS_VISION"] = "true"
    os.environ["LLM_VISION_MAX_IMAGES"] = "2"

    client = LMStudioClient()

    # Test 1: Create vision message
    try:
        dummy_images = [
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAAAAAAD",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAE",
        ]

        vision_msg = client.create_vision_message("What do you see in these images?", dummy_images)

        # Verify structure
        assert vision_msg["role"] == "user"
        assert isinstance(vision_msg["content"], list)
        assert len(vision_msg["content"]) == 3  # 1 text + 2 images

    except Exception:
        return False

    # Test 2: Message alternation with vision content
    try:
        test_conversation = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            vision_msg,  # Vision message with list content
            {"role": "assistant", "content": "I can see the images."},
            {"role": "user", "content": "Great!"},
        ]

        fixed_messages = client._fix_message_alternation(test_conversation)

        # Verify no errors occurred
        for _i, msg in enumerate(fixed_messages):
            msg.get("role")
            content = msg.get("content")
            type(content).__name__


    except Exception:
        import traceback

        traceback.print_exc()
        return False

    # Test 3: Mock response processing
    try:
        # Test different response formats
        test_responses = [
            # Standard string response
            {"choices": [{"message": {"content": "This is a text response."}}]},
            # Multimodal response
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "I see an image with "},
                                {"type": "text", "text": "a cat in it."},
                            ]
                        }
                    }
                ]
            },
            # Mixed response
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "Analysis complete."},
                                {"type": "metadata", "data": "ignored"},
                                {"type": "text", "text": "The image shows a sunset."},
                            ]
                        }
                    }
                ]
            },
        ]

        for _i, mock_response in enumerate(test_responses):
            response_content = mock_response["choices"][0]["message"]["content"]

            # Process like the get_chat_response method does
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
                str(response_content).strip()



    except Exception:
        return False

    return True


if __name__ == "__main__":
    result = asyncio.run(test_vision_message_processing())
    if result:
        pass
    else:
        exit(1)
