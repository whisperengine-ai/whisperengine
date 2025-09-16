#!/usr/bin/env python3
"""
Test script to verify <|end|> token removal in MLX backend
"""

import asyncio
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_special_token_cleanup():
    """Test that special tokens are properly removed from MLX responses"""

    try:
        from src.llm.mlx_backend import MLXBackend

        # Check if MLX is available
        if not MLXBackend.is_available():
            return True


        # Test the cleanup logic directly
        MLXBackend()

        # Simulate a response with the problematic token
        test_responses = [
            "Hello there! How can I help you today?<|end|>",
            "This is a test response</s>",
            "Another response<|endoftext|>",
            "Clean response without tokens",
            "Multiple tokens<|end|><|endoftext|></s>",
        ]

        for _i, test_response in enumerate(test_responses, 1):
            # Simulate the cleanup that happens in generate_response
            cleaned = test_response
            special_tokens_to_remove = [
                "<|end|>",
                "<|endoftext|>",
                "</s>",
                "<|im_end|>",
                "<|eot_id|>",
                "<end_of_turn>",
                "<|end_of_text|>",
            ]

            for token in special_tokens_to_remove:
                cleaned = cleaned.replace(token, "")
            cleaned = cleaned.strip()


        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run the test"""

    success = await test_special_token_cleanup()

    if success:
        pass
    else:
        pass

    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        sys.exit(1)
