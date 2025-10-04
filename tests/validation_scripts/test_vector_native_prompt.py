#!/usr/bin/env python3
"""
Test script for VectorNativePromptManager integration
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_vector_native_prompt_manager():
    """Test the VectorNativePromptManager with Elena's memory"""
    try:
        # Import required modules
        from src.memory.memory_protocol import create_memory_manager
        from src.prompts.vector_native_prompt_manager import create_vector_native_prompt_manager
        
        logger.info("🚀 Testing VectorNativePromptManager integration")
        
        # Create memory manager (should use Elena's collection)
        memory_manager = create_memory_manager(memory_type="vector")
        
        # Create vector-native prompt manager
        vector_prompt_manager = create_vector_native_prompt_manager(
            vector_memory_system=memory_manager,
            personality_engine=None
        )
        
        # Test with a sample prompt and message
        base_prompt = "You are Elena Rodriguez, a marine biologist who loves the ocean."
        user_id = "test_user_123"
        current_message = "Tell me about your favorite sea creatures"
        emotional_context = "curiosity"
        
        logger.info(f"📝 Creating contextualized prompt for user {user_id}")
        logger.info(f"💬 Message: {current_message}")
        logger.info(f"😊 Emotional context: {emotional_context}")
        
        # Create contextualized prompt
        enhanced_prompt = await vector_prompt_manager.create_contextualized_prompt(
            base_prompt=base_prompt,
            user_id=user_id,
            current_message=current_message,
            emotional_context=emotional_context
        )
        
        logger.info("✅ VectorNativePromptManager test completed successfully!")
        logger.info(f"📊 Enhanced prompt length: {len(enhanced_prompt)} characters")
        logger.info("🎯 Enhanced prompt preview:")
        logger.info("-" * 50)
        logger.info(enhanced_prompt[:500] + "..." if len(enhanced_prompt) > 500 else enhanced_prompt)
        logger.info("-" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ VectorNativePromptManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    logger.info("🧪 Starting VectorNativePromptManager test")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    success = await test_vector_native_prompt_manager()
    
    if success:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("💥 Test failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)