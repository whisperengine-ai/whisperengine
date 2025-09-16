"""
Test script for the LM Studio client
"""

import sys

from lmstudio_client import LMStudioClient


def main():
    # Create a client
    client = LMStudioClient()

    # Check if the server is running
    if not client.check_connection():
        sys.exit(1)


    # Test a simple chat completion
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, tell me a short joke."},
    ]

    client.get_chat_response(messages)


if __name__ == "__main__":
    main()
