#!/usr/bin/env python3
"""
Test AI Service Integration
Simple test to verify the AI service can process messages correctly
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

async def test_ai_service():
    """Test the AI service integration"""
    print("🤖 Testing AI Service Integration...")
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        from src.core.native_ai_service import NativeAIService
        
        # Create AI service with test user ID
        ai_service = NativeAIService(user_id="test-user-123")
        print("✅ AI Service created")
        
        # Start the event loop
        ai_service.start_event_loop()
        print("✅ Event loop started")
        
        # Initialize the service
        success = await ai_service.initialize()
        if success:
            print("✅ AI Service initialized successfully")
        else:
            print("⚠️ AI Service initialization failed")
            return False
        
        # Test message processing
        test_message = "Hello! Can you tell me about yourself?"
        print(f"📨 Sending test message: '{test_message}'")
        
        response = await ai_service.process_message_async(test_message)
        
        print(f"🤖 AI Response:")
        print(f"   Content: {response.content[:100]}...")
        print(f"   Type: {response.message_type}")
        print(f"   Timestamp: {response.timestamp}")
        
        if response.message_type == "error":
            print("❌ AI Service returned an error response")
            return False
        else:
            print("✅ AI Service processed message successfully")
            return True
            
    except ImportError as e:
        print(f"❌ Failed to import AI service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during AI service test: {e}")
        return False
    finally:
        # Clean up
        if 'ai_service' in locals():
            ai_service.stop_event_loop()
            print("🛑 Event loop stopped")

if __name__ == "__main__":
    success = asyncio.run(test_ai_service())
    if success:
        print("\n🎉 AI Service Integration Test PASSED")
    else:
        print("\n❌ AI Service Integration Test FAILED")
    sys.exit(0 if success else 1)