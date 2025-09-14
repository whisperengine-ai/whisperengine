#!/usr/bin/env python3
"""
Test with exact same component initialization as desktop app
"""
import os
import asyncio
import logging
from datetime import datetime
from env_manager import load_environment
from src.llm.llm_client import LLMClient
from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import DatabaseIntegrationManager
from src.ui.web_ui import create_web_ui

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

async def test_full_component_initialization():
    """Test with full component initialization like desktop app"""
    print("Testing with full component initialization...")
    load_environment()
    
    # Initialize components in same order as desktop app
    print("1. Initializing configuration manager...")
    config_manager = AdaptiveConfigManager()
    
    print("2. Initializing database manager...")
    db_manager = None
    try:
        db_manager = DatabaseIntegrationManager()
        print("   Database integration initialized for full capabilities")
    except Exception as e:
        print(f"   Database initialization failed (running in basic mode): {e}")
    
    print("3. Initializing LLM client...")
    llm_client = None
    try:
        llm_client = LLMClient()
        print("   LLM client initialized for AI conversations")
    except Exception as e:
        print(f"   LLM client initialization failed (demo mode): {e}")
    
    print("4. Creating web UI with full components...")
    web_ui = create_web_ui(
        db_manager=db_manager, 
        config_manager=config_manager,
        llm_client=llm_client
    )
    
    if llm_client:
        print("   WhisperEngine components initialized with full AI capabilities")
    
    # Now test the LLM client after full initialization
    print("\n5. Testing LLM client after full component initialization...")
    
    if llm_client:
        conversation_context = [
            {
                "role": "system", 
                "content": "You are a test assistant."
            },
            {
                "role": "user", 
                "content": "Hello from component test"
            }
        ]
        
        try:
            print("   Calling generate_chat_completion...")
            completion_response = llm_client.generate_chat_completion(
                messages=conversation_context,
                temperature=0.7,
                max_tokens=100
            )
            
            if completion_response and 'choices' in completion_response:
                choice = completion_response['choices'][0]
                response = choice['message']['content']
                print(f"   SUCCESS: {response}")
            else:
                print(f"   FAILED: Invalid response format: {completion_response}")
                
        except Exception as e:
            print(f"   EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("   No LLM client available for testing")
    
    # Test web UI generate_ai_response method
    print("\n6. Testing web UI generate_ai_response method...")
    try:
        response = await web_ui.generate_ai_response("test_user", "Hello from web UI test")
        print(f"   Web UI SUCCESS: {response.get('content', 'No content')}")
    except Exception as e:
        print(f"   Web UI EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_component_initialization())