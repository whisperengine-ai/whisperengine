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
        print("❌ Cannot connect to LM Studio server. Make sure it's running on http://localhost:1234")
        sys.exit(1)
    
    print("✅ Connected to LM Studio server")
    
    # Test a simple chat completion
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, tell me a short joke."}
    ]
    
    print("Sending request to LLM...")
    response = client.get_chat_response(messages)
    print("\nResponse from LLM:")
    print("-" * 40)
    print(response)
    print("-" * 40)
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()
