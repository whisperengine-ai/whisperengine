#!/usr/bin/env python3
"""
LLM Configuration Checker
Shows exactly which endpoints and models are being used for each AI feature.
Run with: docker exec whisperengine-bot python3 check_llm_config.py
"""

import os

def check_llm_config():
    """Display current LLM configuration in a clear format."""
    
    print("🤖 WhisperEngine LLM Configuration Summary")
    print("=" * 50)
    
    # Main chat configuration
    main_url = os.getenv("LLM_CHAT_API_URL", "NOT SET")
    main_model = os.getenv("LLM_CHAT_MODEL", "NOT SET")
    main_key = os.getenv("LLM_CHAT_API_KEY")
    
    print(f"📝 MAIN CONVERSATION:")
    print(f"   Endpoint: {main_url}")
    print(f"   Model:    {main_model}")
    print(f"   API Key:  {'✅ SET' if main_key else '❌ NOT SET'}")
    print()
    
    # Emotion analysis configuration
    emotion_url = os.getenv("LLM_EMOTION_API_URL", main_url)
    emotion_key = os.getenv("LLM_EMOTION_API_KEY", main_key)
    emotion_model = os.getenv("LLM_EMOTION_MODEL", main_model)
    
    print(f"💝 EMOTION ANALYSIS:")
    print(f"   Endpoint: {emotion_url}")
    print(f"   Model:    {emotion_model} (uses main model)")
    print(f"   API Key:  {'✅ SET' if emotion_key else '❌ NOT SET'}")
    if emotion_url == main_url:
        print(f"   📌 Using same endpoint as main conversation")
    print()
    
    # Facts analysis configuration
    facts_url = os.getenv("LLM_FACTS_API_URL", emotion_url)
    facts_model = os.getenv("LLM_FACTS_MODEL", emotion_model)
    facts_key = os.getenv("LLM_FACTS_API_KEY", emotion_key)
    
    print(f"📊 FACT EXTRACTION:")
    print(f"   Endpoint: {facts_url}")
    print(f"   Model:    {facts_model}")
    print(f"   API Key:  {'✅ SET' if facts_key else '❌ NOT SET'}")
    if facts_url == main_url:
        print(f"   📌 Using same endpoint as main conversation")
    print()
    
    # Service detection
    if "openrouter.ai" in main_url:
        service = "OpenRouter"
    elif "localhost:1234" in main_url or "127.0.0.1:1234" in main_url:
        service = "LM Studio (Local)"
    elif "11434" in main_url or "ollama" in main_url.lower():
        service = "Ollama (Local)"
    else:
        service = "Custom/Unknown"
    
    print(f"🔗 DETECTED SERVICE: {service}")
    print()
    
    # Configuration recommendations
    print("💡 CONFIGURATION STATUS:")
    if emotion_url == main_url and facts_url == main_url:
        print("   ✅ Unified configuration - all features use the same endpoint")
    else:
        print("   ⚠️  Mixed configuration - different endpoints for different features")
    
    if emotion_model == main_model:
        print("   ✅ Emotion analysis uses main model (efficient)")
    
    if facts_model != main_model:
        print(f"   ✅ Fact extraction uses optimized model ({facts_model})")
    
    print()
    print("🔧 To run this check: docker exec whisperengine-bot python3 check_llm_config.py")

if __name__ == "__main__":
    check_llm_config()