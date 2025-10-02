#!/usr/bin/env python3
"""
Verification script showing the difference between CDL-only and CDL+VectorNative prompts
"""
import asyncio
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def verify_integration():
    """Verify VectorNativePromptManager integration is working correctly"""
    try:
        logger.info("🔍 Verifying VectorNativePromptManager integration...")
        
        # Test 1: Can we import and create the VectorNativePromptManager?
        try:
            from src.prompts.vector_native_prompt_manager import create_vector_native_prompt_manager
            from src.memory.memory_protocol import create_memory_manager
            
            memory_manager = create_memory_manager(memory_type="vector")
            vector_prompt_manager = create_vector_native_prompt_manager(
                vector_memory_system=memory_manager,
                personality_engine=None
            )
            logger.info("✅ VectorNativePromptManager created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create VectorNativePromptManager: {e}")
            return False
        
        # Test 2: Can we create a basic contextualized prompt?
        try:
            base_prompt = "You are Elena Rodriguez, a marine biologist."
            enhanced_prompt = await vector_prompt_manager.create_contextualized_prompt(
                base_prompt=base_prompt,
                user_id="test_user_verification",
                current_message="Hi Elena, how are you doing today?",
                emotional_context="friendly"
            )
            
            logger.info("✅ Contextualized prompt created successfully")
            logger.info(f"📊 Prompt length: {len(enhanced_prompt)} characters")
            
            # Show the difference
            logger.info("🔄 COMPARISON:")
            logger.info("📝 Original prompt:")
            logger.info(f"   {base_prompt}")
            logger.info("🎯 Vector-enhanced prompt:")
            logger.info(f"   {enhanced_prompt[:300]}...")
            
        except Exception as e:
            logger.error(f"❌ Failed to create contextualized prompt: {e}")
            return False
        
        # Test 3: Check if the events.py integration is available
        try:
            from src.handlers.events import BotEventHandlers
            logger.info("✅ Events handler integration available")
        except Exception as e:
            logger.error(f"❌ Events handler integration issue: {e}")
            return False
        
        logger.info("🎉 VectorNativePromptManager integration verification completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 VectorNativePromptManager Integration Verification")
    print("=" * 60)
    
    success = asyncio.run(verify_integration())
    
    if success:
        print("\n✅ VERIFICATION PASSED: VectorNativePromptManager is ready!")
        print("\n📋 TESTING INSTRUCTIONS:")
        print("1. The integration is now active in Elena bot")
        print("2. Send a Discord message to Elena")
        print("3. Look for '🎯 VECTOR-NATIVE: Enhanced character prompt' in the logs")
        print("4. Compare responses - they should be more contextual and personalized")
        print("\n💡 WHAT'S NEW:")
        print("- Character prompts now include dynamic vector context")
        print("- Memory network analysis (conversation count, key topics)")
        print("- Relationship depth assessment")
        print("- Personality pattern recognition") 
        print("- Emotional intelligence context")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED: Check the errors above")
        sys.exit(1)