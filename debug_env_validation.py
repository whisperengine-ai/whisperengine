#!/usr/bin/env python3
"""
Debug environment validation in container
"""
import os
import sys

def debug_env_validation():
    print("🔍 Environment Variable Debug")
    print("=" * 50)
    
    # Check the three key variables
    discord_token = os.getenv("DISCORD_BOT_TOKEN", "")
    llm_url = os.getenv("LLM_CHAT_API_URL", "")
    llm_api_key = os.getenv("LLM_CHAT_API_KEY", "")
    
    print(f"DISCORD_BOT_TOKEN: '{discord_token}' (length: {len(discord_token)})")
    print(f"LLM_CHAT_API_URL: '{llm_url}' (length: {len(llm_url)})")
    print(f"LLM_CHAT_API_KEY: '{llm_api_key}' (length: {len(llm_api_key)})")
    
    print("\n🔍 Validation Logic Debug")
    print("-" * 30)
    
    # Check Discord token validation
    has_discord_token = bool(discord_token and not discord_token.startswith("your_"))
    print(f"Discord token valid: {has_discord_token}")
    if not has_discord_token:
        print(f"  - Token exists: {bool(discord_token)}")
        print(f"  - Starts with 'your_': {discord_token.startswith('your_')}")
    
    # Check LLM URL validation
    has_llm_url = bool(llm_url)
    print(f"LLM URL valid: {has_llm_url}")
    
    # Check API key validation  
    has_valid_api_key = (
        llm_api_key == "not-needed" or  # Local LLM
        (llm_api_key and not llm_api_key.startswith("your_") and not llm_api_key == "sk-placeholder")  # Real API key
    )
    print(f"API key valid: {has_valid_api_key}")
    if not has_valid_api_key:
        print(f"  - Key exists: {bool(llm_api_key)}")
        print(f"  - Equals 'not-needed': {llm_api_key == 'not-needed'}")
        print(f"  - Starts with 'your_': {llm_api_key.startswith('your_')}")
        print(f"  - Equals 'sk-placeholder': {llm_api_key == 'sk-placeholder'}")
    
    # Overall validation
    overall_valid = has_llm_url and has_valid_api_key and has_discord_token
    print(f"\nOverall validation: {overall_valid}")
    
    # Check container mode detection
    is_container = (
        os.path.exists("/.dockerenv") or
        bool(os.getenv("CONTAINER_MODE")) or
        bool(os.getenv("DOCKER_ENV")) or
        os.getenv("ENV_MODE") == "production"
    )
    print(f"Container mode detected: {is_container}")
    
    print("\n🔍 Container Mode Debug")
    print("-" * 30)
    print(f"/.dockerenv exists: {os.path.exists('/.dockerenv')}")
    print(f"CONTAINER_MODE: '{os.getenv('CONTAINER_MODE', '')}'")
    print(f"DOCKER_ENV: '{os.getenv('DOCKER_ENV', '')}'")
    print(f"ENV_MODE: '{os.getenv('ENV_MODE', '')}'")

if __name__ == "__main__":
    debug_env_validation()