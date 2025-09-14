#!/usr/bin/env python3
"""
Test what the web UI is doing exactly to reproduce the 404 error
"""
import os
import asyncio
import logging
from datetime import datetime
from env_manager import load_environment
from src.llm.llm_client import LLMClient

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

async def test_web_ui_simulation():
    """Simulate exactly what the web UI is doing"""
    load_environment()
    
    # Create LLM client same as web UI
    llm_client = LLMClient()
    print(f"Created LLM client: {llm_client.service_name}")
    
    # Create the exact same message format as web UI
    user_id = "test_user"
    message = "Hello from simulated web UI"
    
    conversation_context = [
        {
            "role": "system", 
            "content": """You are WhisperEngine, an AI assistant with advanced emotional intelligence and memory capabilities. 

You embody a caring, thoughtful personality with deep conversational understanding. You:
- Remember previous conversations and build relationships
- Show emotional intelligence and empathy
- Adapt your communication style to the user
- Provide helpful, personalized responses
- Maintain conversation continuity

You are running as a desktop application providing local, private AI conversations."""
        },
        {
            "role": "user", 
            "content": message
        }
    ]
    
    print(f"\nTesting with {len(conversation_context)} messages...")
    print(f"System message length: {len(conversation_context[0]['content'])}")
    print(f"User message: {conversation_context[1]['content']}")
    
    # Test the exact same call as web UI
    start_time = datetime.now()
    try:
        print("\nCalling generate_chat_completion...")
        completion_response = llm_client.generate_chat_completion(
            messages=conversation_context,
            temperature=0.7,
            max_tokens=2000
        )
        
        print(f"Response type: {type(completion_response)}")
        print(f"Response keys: {list(completion_response.keys()) if isinstance(completion_response, dict) else 'Not a dict'}")
        
        # Extract response same as web UI
        if completion_response and 'choices' in completion_response:
            choice = completion_response['choices'][0]
            response = choice['message']['content']
            print(f"SUCCESS: {response}")
        else:
            print(f"FAILED: Invalid response format: {completion_response}")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    generation_time = int((datetime.now() - start_time).total_seconds() * 1000)
    print(f"Generation time: {generation_time}ms")

if __name__ == "__main__":
    asyncio.run(test_web_ui_simulation())