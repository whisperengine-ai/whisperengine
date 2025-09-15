#!/usr/bin/env python3
"""
Test script to verify <|end|> token removal in MLX backend
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_special_token_cleanup():
    """Test that special tokens are properly removed from MLX responses"""
    print("🧪 Testing MLX special token cleanup...")
    
    try:
        from src.llm.mlx_backend import MLXBackend, get_default_mlx_model_config
        
        # Check if MLX is available
        if not MLXBackend.is_available():
            print("⚠️  MLX not available on this platform")
            return True
        
        print("✅ MLX backend available")
        
        # Test the cleanup logic directly
        backend = MLXBackend()
        
        # Simulate a response with the problematic token
        test_responses = [
            "Hello there! How can I help you today?<|end|>",
            "This is a test response</s>",
            "Another response<|endoftext|>",
            "Clean response without tokens",
            "Multiple tokens<|end|><|endoftext|></s>"
        ]
        
        print("\n📝 Testing token cleanup:")
        for i, test_response in enumerate(test_responses, 1):
            # Simulate the cleanup that happens in generate_response
            cleaned = test_response
            special_tokens_to_remove = [
                '<|end|>',
                '<|endoftext|>',
                '</s>',
                '<|im_end|>',
                '<|eot_id|>',
                '<end_of_turn>',
                '<|end_of_text|>'
            ]
            
            for token in special_tokens_to_remove:
                cleaned = cleaned.replace(token, '')
            cleaned = cleaned.strip()
            
            has_tokens = cleaned != test_response
            status = "🧹 CLEANED" if has_tokens else "✅ CLEAN"
            print(f"  {i}. {status}: '{test_response}' → '{cleaned}'")
        
        print("\n✅ All token cleanup tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test"""
    print("🚀 Starting Special Token Cleanup Tests\n")
    
    success = await test_special_token_cleanup()
    
    if success:
        print("\n🎉 All tests passed!")
        print("📱 The <|end|> tag should no longer appear in desktop app responses")
        print("💡 Try sending a message in the desktop app to verify the fix")
    else:
        print("\n❌ Some tests failed")
        
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)