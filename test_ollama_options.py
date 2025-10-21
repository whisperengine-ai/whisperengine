#!/usr/bin/env python3
"""
Test script to verify Ollama options.num_predict is being sent correctly.
"""
import json
import os
import sys

# Set environment for Ollama
os.environ["LLM_CHAT_API_URL"] = "http://localhost:11434/v1"
os.environ["LLM_CHAT_MODEL"] = "dolphin-mistral:7b"

from src.llm.llm_client import LLMClient

# Create LLM client - it will use environment variables
client = LLMClient()

print("✅ LLM Client initialized")
print(f"   is_ollama: {client.is_ollama}")
print(f"   chat_endpoint: {client.chat_endpoint}")
print(f"   api_url: {client.api_url}")

# Test payload generation (we'll intercept before sending)
def mock_post(*args, **kwargs):
    """Mock POST to capture the payload"""
    payload = kwargs.get('json', {})
    print("\n📦 PAYLOAD BEING SENT:")
    print(json.dumps(payload, indent=2))
    
    # Check for options.num_predict
    if 'options' in payload:
        print("\n✅ SUCCESS: 'options' object found in payload")
        if 'num_predict' in payload['options']:
            print(f"✅ SUCCESS: 'num_predict' = {payload['options']['num_predict']}")
        else:
            print("❌ FAILURE: 'num_predict' NOT in options object")
    else:
        print("\n❌ FAILURE: 'options' object NOT in payload")
    
    # Don't actually send the request
    sys.exit(0)

# Mock the session.post method
client.session.post = mock_post

# Try to generate chat completion (will be intercepted)
try:
    client.generate_chat_completion(
        messages=[
            {"role": "user", "content": "Test message"}
        ],
        model="dolphin-mistral:7b",
        temperature=0.7,
        max_tokens=4096
    )
except SystemExit:
    pass  # Expected from our mock
