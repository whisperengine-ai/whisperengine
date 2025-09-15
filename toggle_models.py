#!/usr/bin/env python3
"""
Simple Model Toggle for WhisperEngine
Switch between Remote (OpenRouter/OpenAI) and Local HTTP APIs (LM Studio/Ollama)
"""

import shutil
from pathlib import Path

def toggle_to_local():
    """Switch to local HTTP models (LM Studio or Ollama)"""
    env_file = Path(".env")
    backup_file = Path(".env.remote")
    
    # Backup current .env if it's not already backed up
    if not backup_file.exists():
        shutil.copy(env_file, backup_file)
        print("📁 Backed up current .env to .env.remote")
    
    # Read current .env
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace remote URLs with local LM Studio (default)
    content = content.replace(
        'LLM_CHAT_API_URL=https://openrouter.ai/api/v1',
        'LLM_CHAT_API_URL=http://localhost:1234/v1'
    )
    content = content.replace(
        'LLM_CHAT_API_URL=https://api.openai.com/v1',
        'LLM_CHAT_API_URL=http://localhost:1234/v1'
    )
    content = content.replace(
        'LLM_FACTS_API_URL=https://openrouter.ai/api/v1', 
        'LLM_FACTS_API_URL=http://localhost:1234/v1'
    )
    content = content.replace(
        'LLM_FACTS_API_URL=https://api.openai.com/v1', 
        'LLM_FACTS_API_URL=http://localhost:1234/v1'
    )
    content = content.replace(
        'LLM_EMOTION_API_URL=https://openrouter.ai/api/v1',
        'LLM_EMOTION_API_URL=http://localhost:1234/v1'
    )
    content = content.replace(
        'LLM_EMOTION_API_URL=https://api.openai.com/v1',
        'LLM_EMOTION_API_URL=http://localhost:1234/v1'
    )
    
    # Comment out API keys (not needed for local servers)
    content = content.replace(
        'LLM_CHAT_API_KEY=sk-or-v1-',
        '# LLM_CHAT_API_KEY=sk-or-v1-'
    )
    content = content.replace(
        'LLM_CHAT_API_KEY=sk-',
        '# LLM_CHAT_API_KEY=sk-'
    )
    content = content.replace(
        'LLM_FACTS_API_KEY=sk-or-v1-',
        '# LLM_FACTS_API_KEY=sk-or-v1-'
    )
    content = content.replace(
        'LLM_FACTS_API_KEY=sk-',
        '# LLM_FACTS_API_KEY=sk-'
    )
    content = content.replace(
        'LLM_EMOTION_API_KEY=sk-or-v1-',
        '# LLM_EMOTION_API_KEY=sk-or-v1-'
    )
    content = content.replace(
        'LLM_EMOTION_API_KEY=sk-',
        '# LLM_EMOTION_API_KEY=sk-'
    )
    
    # Set model to local-model (works with LM Studio)
    content = content.replace(
        'LLM_CHAT_MODEL_NAME=',
        'LLM_CHAT_MODEL_NAME=local-model'
    )
    
    # Write updated .env
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("🏠 Switched to LOCAL HTTP models (LM Studio on localhost:1234)")
    print("💡 For Ollama, change port to 11434 manually")
    print("🔧 Make sure your local model server is running!")

def toggle_to_ollama():
    """Switch to local Ollama HTTP API"""
    env_file = Path(".env")
    backup_file = Path(".env.remote")
    
    # Backup current .env if it's not already backed up
    if not backup_file.exists():
        shutil.copy(env_file, backup_file)
        print("📁 Backed up current .env to .env.remote")
    
    # Read current .env
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace any URLs with Ollama HTTP endpoint
    content = content.replace(
        'LLM_CHAT_API_URL=https://openrouter.ai/api/v1',
        'LLM_CHAT_API_URL=http://localhost:11434/v1'
    )
    content = content.replace(
        'LLM_CHAT_API_URL=https://api.openai.com/v1',
        'LLM_CHAT_API_URL=http://localhost:11434/v1'
    )
    content = content.replace(
        'LLM_CHAT_API_URL=http://localhost:1234/v1',
        'LLM_CHAT_API_URL=http://localhost:11434/v1'
    )
    content = content.replace(
        'LLM_FACTS_API_URL=https://openrouter.ai/api/v1', 
        'LLM_FACTS_API_URL=http://localhost:11434/v1'
    )
    content = content.replace(
        'LLM_FACTS_API_URL=https://api.openai.com/v1', 
        'LLM_FACTS_API_URL=http://localhost:11434/v1'
    )
    content = content.replace(
        'LLM_FACTS_API_URL=http://localhost:1234/v1', 
        'LLM_FACTS_API_URL=http://localhost:11434/v1'
    )
    content = content.replace(
        'LLM_EMOTION_API_URL=https://openrouter.ai/api/v1',
        'LLM_EMOTION_API_URL=http://localhost:11434/v1'
    )
    content = content.replace(
        'LLM_EMOTION_API_URL=https://api.openai.com/v1',
        'LLM_EMOTION_API_URL=http://localhost:11434/v1'
    )
    content = content.replace(
        'LLM_EMOTION_API_URL=http://localhost:1234/v1',
        'LLM_EMOTION_API_URL=http://localhost:11434/v1'
    )
    
    # Comment out API keys (not needed for Ollama)
    content = content.replace(
        'LLM_CHAT_API_KEY=sk-or-v1-',
        '# LLM_CHAT_API_KEY=sk-or-v1-'
    )
    content = content.replace(
        'LLM_CHAT_API_KEY=sk-',
        '# LLM_CHAT_API_KEY=sk-'
    )
    content = content.replace(
        'LLM_FACTS_API_KEY=sk-or-v1-',
        '# LLM_FACTS_API_KEY=sk-or-v1-'
    )
    content = content.replace(
        'LLM_FACTS_API_KEY=sk-',
        '# LLM_FACTS_API_KEY=sk-'
    )
    content = content.replace(
        'LLM_EMOTION_API_KEY=sk-or-v1-',
        '# LLM_EMOTION_API_KEY=sk-or-v1-'
    )
    content = content.replace(
        'LLM_EMOTION_API_KEY=sk-',
        '# LLM_EMOTION_API_KEY=sk-'
    )
    
    # Set model to work with Ollama
    content = content.replace(
        'LLM_CHAT_MODEL_NAME=local-model',
        'LLM_CHAT_MODEL_NAME=llama3.2:3b'
    )
    
    # Write updated .env
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("🦙 Switched to OLLAMA HTTP API (localhost:11434)")
    print("🔧 Make sure Ollama is running with: ollama serve")
    print("📦 Install model with: ollama pull llama3.2:3b")

def toggle_to_remote():
    """Switch back to remote OpenRouter/OpenAI"""
    env_file = Path(".env")
    backup_file = Path(".env.remote")
    
    if backup_file.exists():
        shutil.copy(backup_file, env_file)
        print("🌐 Restored remote configuration from backup")
    else:
        print("❌ No remote backup found (.env.remote)")
        print("💡 You'll need to manually configure remote APIs")

def main():
    """Main toggle interface"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python toggle_models.py [local|ollama|remote]")
        print("")
        print("Available options:")
        print("  local  - Switch to LM Studio (localhost:1234)")
        print("  ollama - Switch to Ollama HTTP (localhost:11434)")
        print("  remote - Switch back to OpenRouter/OpenAI")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == "local":
        toggle_to_local()
    elif mode == "ollama":
        toggle_to_ollama()
    elif mode == "remote":
        toggle_to_remote()
    else:
        print(f"❌ Unknown mode: {mode}")
        print("Valid modes: local, ollama, remote")

if __name__ == "__main__":
    main()