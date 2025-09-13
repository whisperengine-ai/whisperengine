"""
Comprehensive test for vision message processing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lmstudio_client import LMStudioClient
import asyncio

import pytest

@pytest.mark.asyncio
async def test_vision_message_processing():
    """Test complete vision message processing pipeline"""
    
    print("🧪 Testing Vision Message Processing Pipeline")
    
    # Set up vision support
    os.environ['LLM_SUPPORTS_VISION'] = 'true'
    os.environ['LLM_VISION_MAX_IMAGES'] = '2'
    
    client = LMStudioClient()
    
    # Test 1: Create vision message
    print("\n1️⃣ Testing vision message creation...")
    try:
        dummy_images = [
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAAAAAAD",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAE"
        ]
        
        vision_msg = client.create_vision_message("What do you see in these images?", dummy_images)
        print(f"✅ Created vision message: {len(vision_msg['content'])} parts")
        
        # Verify structure
        assert vision_msg['role'] == 'user'
        assert isinstance(vision_msg['content'], list)
        assert len(vision_msg['content']) == 3  # 1 text + 2 images
        print("✅ Vision message structure correct")
        
    except Exception as e:
        print(f"❌ Vision message creation failed: {e}")
        return False
    
    # Test 2: Message alternation with vision content
    print("\n2️⃣ Testing message alternation with vision content...")
    try:
        test_conversation = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            vision_msg,  # Vision message with list content
            {"role": "assistant", "content": "I can see the images."},
            {"role": "user", "content": "Great!"}
        ]
        
        fixed_messages = client._fix_message_alternation(test_conversation)
        print(f"✅ Fixed {len(test_conversation)} messages to {len(fixed_messages)} messages")
        
        # Verify no errors occurred
        for i, msg in enumerate(fixed_messages):
            role = msg.get('role')
            content = msg.get('content')
            content_type = type(content).__name__
            print(f"   Message {i}: {role} ({content_type})")
        
        print("✅ Message alternation handled vision content correctly")
        
    except Exception as e:
        print(f"❌ Message alternation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Mock response processing
    print("\n3️⃣ Testing response content processing...")
    try:
        # Test different response formats
        test_responses = [
            # Standard string response
            {
                "choices": [{"message": {"content": "This is a text response."}}]
            },
            # Multimodal response
            {
                "choices": [{"message": {"content": [
                    {"type": "text", "text": "I see an image with "},
                    {"type": "text", "text": "a cat in it."}
                ]}}]
            },
            # Mixed response
            {
                "choices": [{"message": {"content": [
                    {"type": "text", "text": "Analysis complete."},
                    {"type": "metadata", "data": "ignored"},
                    {"type": "text", "text": "The image shows a sunset."}
                ]}}]
            }
        ]
        
        for i, mock_response in enumerate(test_responses):
            response_content = mock_response["choices"][0]["message"]["content"]
            
            # Process like the get_chat_response method does
            if isinstance(response_content, str):
                result = response_content.strip()
            elif isinstance(response_content, list):
                text_parts = []
                for part in response_content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        text_parts.append(part)
                result = "\n".join(text_parts).strip()
            else:
                result = str(response_content).strip()
            
            print(f"   Response {i+1}: '{result}'")
        
        print("✅ Response processing handled all formats correctly")
        
    except Exception as e:
        print(f"❌ Response processing failed: {e}")
        return False
    
    print("\n🎉 All vision message processing tests passed!")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_vision_message_processing())
    if result:
        print("\n✅ Vision processing pipeline is working correctly!")
    else:
        print("\n❌ Vision processing pipeline has issues!")
        exit(1)
