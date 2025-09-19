#!/usr/bin/env python3
"""
Test script to verify OpenRouter integration
Run this to test your OpenRouter configuration before starting the bot.
"""
import os
import sys

from lmstudio_client import LMStudioClient


def test_openrouter_config():
    """Test OpenRouter configuration"""

    # Check environment variables
    api_url = os.getenv("LLM_CHAT_API_URL")
    api_key = os.getenv("OPENROUTER_API_KEY")
    model_name = os.getenv("LLM_CHAT_MODEL", "local-llm")

    # Check sentiment endpoint configuration
    sentiment_api_url = os.getenv("LLM_SENTIMENT_API_URL", api_url)
    os.getenv("LLM_SENTIMENT_API_KEY", api_key)
    os.getenv("LLM_SENTIMENT_MODEL_NAME", model_name)

    same_endpoint = sentiment_api_url == api_url
    if same_endpoint:
        pass
    else:
        pass

    # Initialize client
    try:
        client = LMStudioClient()
    except Exception:
        return False

    # Test connection
    try:
        is_connected = client.check_connection()
        if is_connected:
            pass
        else:
            if client.is_openrouter:
                pass
            else:
                pass
    except Exception:
        return False

    # Test simple chat (only if connected)
    if is_connected:
        try:
            messages = [
                {"role": "user", "content": "Say 'Hello from OpenRouter!' if you can read this."}
            ]
            response = client.generate_chat_completion(messages, max_tokens=50)

            if response and "choices" in response and len(response["choices"]) > 0:
                response["choices"][0]["message"]["content"]
            else:
                pass
        except Exception:
            return False

    return is_connected


def main():
    """Main test function"""
    # Load environment from .env if available
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    except Exception:
        pass

    success = test_openrouter_config()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
