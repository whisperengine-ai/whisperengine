#!/usr/bin/env python3
"""
Simple Elena Localhost Test
Direct test without loading container environment
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

# FORCE localhost environment (don't load .env.elena!)
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['POSTGRES_DB'] = 'whisperengine'
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine123'

os.environ['REDIS_HOST'] = 'localhost'
os.environ['REDIS_PORT'] = '6380'
os.environ['REDIS_DB'] = '0'

os.environ['QDRANT_HOST'] = 'localhost'
os.environ['QDRANT_PORT'] = '6334'
os.environ['QDRANT_COLLECTION_NAME'] = 'whisperengine_memory'

# Use OpenRouter (from Elena's config)
os.environ['LLM_CLIENT_TYPE'] = 'openrouter'

async def test_simple_elena():
    """Simple test of Elena's CDL system locally"""
    print("🧪 Simple Elena Localhost Test")
    print("="*40)
    
    try:
        # Test 1: CDL Character loading
        print("🔍 Testing CDL Character System...")
        elena_file = Path("characters/examples/elena-rodriguez.json")
        if elena_file.exists():
            print("   ✅ Elena character file found")
            
            # Try to parse it
            try:
                import json
                with open(elena_file) as f:
                    character_data = json.load(f)
                print(f"   ✅ Character JSON loaded: {character_data.get('basic_info', {}).get('name', 'Unknown')}")
            except Exception as e:
                print(f"   ❌ JSON parsing failed: {e}")
                return False
        else:
            print("   ❌ Elena character file not found")
            return False
        
        # Test 2: CDL Integration
        print("🔍 Testing CDL AI Integration...")
        try:
            from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
            cdl = CDLAIPromptIntegration()
            
            # Try to create a prompt
            prompt = await cdl.create_character_aware_prompt(
                character_file="characters/examples/elena-rodriguez.json",
                user_id="test_user",
                message_content="Hola!"
            )
            
            if "Elena" in prompt and ("marine" in prompt.lower() or "océano" in prompt.lower()):
                print("   ✅ CDL prompt generated with Elena personality")
            else:
                print(f"   ❌ CDL prompt missing personality: {prompt[:200]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ CDL Integration failed: {e}")
            return False
        
        # Test 3: Simple LLM test (using environment config)
        print("🔍 Testing LLM Client...")
        try:
            # Load environment first
            from dotenv import load_dotenv
            load_dotenv()  # This loads our .env file with OpenRouter config
            
            from src.llm.llm_protocol import create_llm_client
            llm_client = create_llm_client()  # Uses environment config
            
            # Simple test with proper message format
            messages = [
                {"role": "system", "content": "You are Elena, a marine biologist. Respond in character."},
                {"role": "user", "content": "Say hello in Spanish"}
            ]
            
            response = await llm_client.generate_chat_completion_safe(messages)
            
            if response and len(response) > 10:
                print(f"   ✅ LLM response: {response[:100]}...")
            else:
                print(f"   ❌ LLM response too short: {response}")
                return False
                
        except Exception as e:
            print(f"   ❌ LLM test failed: {e}")
            return False
        
        print("🎉 All tests passed! Elena personality system works locally")
        return True
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_elena())
    exit(0 if success else 1)