#!/usr/bin/env python3
"""
Quick test script for WhisperEngine Desktop App
Tests the API endpoints to verify functionality.
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8080"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data.get('version', 'unknown')}")
            print(f"   Active connections: {data.get('active_connections', 0)}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_chat_api():
    """Test the chat API endpoint"""
    try:
        payload = {
            "message": "Hello WhisperEngine! This is a test from the desktop app.",
            "user_id": "test_user"
        }
        
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat API test passed")
            print(f"   Response: {data['response'][:100]}...")
            print(f"   Metadata: {data.get('metadata', {})}")
            return True
        else:
            print(f"❌ Chat API test failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat API test error: {e}")
        return False

def test_web_ui():
    """Test that the web UI loads"""
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            content = response.text
            if "WhisperEngine" in content and "chat" in content.lower():
                print("✅ Web UI loads successfully")
                print("   Contains expected elements (title, chat interface)")
                return True
            else:
                print("❌ Web UI missing expected content")
                return False
        else:
            print(f"❌ Web UI test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web UI test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 WhisperEngine Desktop App Test Suite")
    print("=" * 50)
    
    # Wait a moment for the app to fully start
    print("Waiting for app to initialize...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health_check),
        ("Web UI", test_web_ui),
        ("Chat API", test_chat_api),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        if test_func():
            passed += 1
        
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! WhisperEngine desktop app is working correctly.")
        print(f"💻 Open your browser to {BASE_URL} to try the chat interface.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()