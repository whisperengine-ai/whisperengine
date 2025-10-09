#!/usr/bin/env python3
"""
LM Studio Integration Test Script

This script tests the direct integration with LM Studio using the /v1/chat/completions
endpoint to ensure proper functionality with synthetic conversation generation.
"""

import os
import json
import asyncio
import requests
from src.llm.llm_protocol import create_llm_client

async def test_lm_studio_chat_completion():
    """Test LM Studio chat completion endpoint directly"""
    
    print("\n🔍 Testing LM Studio Chat Completion Integration")
    print("================================================")
    
    # Set environment variables for the test
    os.environ["LLM_CHAT_API_URL"] = "http://127.0.0.1:1234"  # Base URL without /v1
    os.environ["LLM_CLIENT_TYPE"] = "lmstudio"
    os.environ["LLM_CHAT_MODEL"] = "mistralai/mistral-nemo-instruct-2407"
    os.environ["LLM_CHAT_API_KEY"] = ""  # Local LM Studio doesn't require API key
    
    # Create LLM client using factory
    llm_client = create_llm_client()
    
    # Test messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant who provides brief, concise responses."
        },
        {
            "role": "user",
            "content": "Hello, can you help me today?"
        }
    ]
    
    try:
        # Test the chat completion endpoint
        print("Sending chat completion request to LM Studio...")
        response = llm_client.generate_chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=50
        )
        
        # Handle async if needed
        if hasattr(response, '__await__'):
            response = await response
        
        # Display the response
        print("\n✅ LM Studio Response:")
        print("----------------------")
        print(json.dumps(response, indent=2))
        
        # Extract the message content
        if 'choices' in response and response['choices']:
            choice = response['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                message_content = choice['message']['content']
                print(f"\n📝 Content: {message_content}")
            else:
                print("\n⚠️ No message content found in response format")
        else:
            print("\n⚠️ No choices found in response")
        
        # Check for completion tokens
        if 'usage' in response and 'completion_tokens' in response['usage']:
            completion_tokens = response['usage']['completion_tokens']
            print(f"\n🔢 Completion Tokens: {completion_tokens}")
            if completion_tokens == 0:
                print("❌ ERROR: Completion tokens is zero - model likely failed to generate text")
            else:
                print("✅ Model successfully generated completion tokens")
        
        return response
    except Exception as e:
        print(f"\n❌ Error testing LM Studio integration: {e}")
        return None

# Function to check if LM Studio is running
def is_lm_studio_running():
    """Check if LM Studio is running by querying the models endpoint"""
    try:
        response = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
        return response.status_code == 200
    except:
        return False

# Main function
async def main():
    """Main function to run the test"""
    if not is_lm_studio_running():
        print("❌ LM Studio is not running or not accessible at http://127.0.0.1:1234")
        print("Please start LM Studio and try again.")
        return
    
    await test_lm_studio_chat_completion()

if __name__ == "__main__":
    asyncio.run(main())