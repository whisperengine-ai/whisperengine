#!/usr/bin/env python3
"""
LLM Configuration Checker
Shows exactly which endpoints and models are being used for each AI feature.
Run with: docker exec whisperengine-bot python3 check_llm_config.py
"""

import os


def check_llm_config():
    """Display current LLM configuration in a clear format."""

    # Main chat configuration
    main_url = os.getenv("LLM_CHAT_API_URL", "NOT SET")
    main_model = os.getenv("LLM_CHAT_MODEL", "NOT SET")
    main_key = os.getenv("LLM_CHAT_API_KEY")

    # Emotion analysis configuration
    emotion_url = os.getenv("LLM_EMOTION_API_URL", main_url)
    emotion_key = os.getenv("LLM_EMOTION_API_KEY", main_key)
    emotion_model = os.getenv("LLM_EMOTION_MODEL", main_model)

    if emotion_url == main_url:
        pass

    # Facts analysis configuration
    facts_url = os.getenv("LLM_FACTS_API_URL", emotion_url)
    facts_model = os.getenv("LLM_FACTS_MODEL", emotion_model)
    os.getenv("LLM_FACTS_API_KEY", emotion_key)

    if facts_url == main_url:
        pass

    # Service detection
    if "openrouter.ai" in main_url:
        pass
    elif "localhost:1234" in main_url or "127.0.0.1:1234" in main_url:
        pass
    elif "11434" in main_url or "ollama" in main_url.lower():
        pass
    else:
        pass

    # Configuration recommendations
    if emotion_url == main_url and facts_url == main_url:
        pass
    else:
        pass

    if emotion_model == main_model:
        pass

    if facts_model != main_model:
        pass


if __name__ == "__main__":
    check_llm_config()
