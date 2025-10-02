#!/usr/bin/env python3
"""
Test script to verify the enhanced pipeline is working with latest features
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_features():
    """Test the enhanced pipeline features"""
    logger.info("🧪 Testing Enhanced WhisperEngine Pipeline Features")
    
    # Test 1: Fidelity-first memory retrieval
    logger.info("📝 Test 1: Fidelity-first memory retrieval")
    try:
        from src.memory.memory_protocol import create_memory_manager
        memory_manager = create_memory_manager(memory_type="vector")
        
        if hasattr(memory_manager, 'retrieve_relevant_memories_fidelity_first'):
            logger.info("✅ Fidelity-first memory method available")
        else:
            logger.warning("⚠️ Fidelity-first memory method not found")
    except Exception as e:
        logger.error(f"❌ Memory system test failed: {e}")
    
    # Test 2: OptimizedPromptBuilder
    logger.info("📝 Test 2: OptimizedPromptBuilder")
    try:
        from src.prompts.optimized_prompt_builder import create_optimized_prompt_builder
        prompt_builder = create_optimized_prompt_builder(max_words=1000)
        logger.info("✅ OptimizedPromptBuilder created successfully")
    except Exception as e:
        logger.error(f"❌ OptimizedPromptBuilder test failed: {e}")
    
    # Test 3: HybridContextDetector
    logger.info("📝 Test 3: HybridContextDetector")
    try:
        from src.prompts.hybrid_context_detector import create_hybrid_context_detector
        context_detector = create_hybrid_context_detector()
        
        # Test analysis
        test_message = "Are you an AI? I remember we talked about this before."
        analysis = context_detector.analyze_context(test_message)
        
        logger.info(f"✅ HybridContextDetector analysis complete:")
        logger.info(f"   - AI guidance needed: {analysis.needs_ai_guidance}")
        logger.info(f"   - Memory context needed: {analysis.needs_memory_context}")
        logger.info(f"   - Personality needed: {analysis.needs_personality}")
        
    except Exception as e:
        logger.error(f"❌ HybridContextDetector test failed: {e}")
    
    # Test 4: CDL Integration
    logger.info("📝 Test 4: CDL Integration")
    try:
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        cdl_integration = CDLAIPromptIntegration()
        logger.info("✅ CDL Integration initialized successfully")
    except Exception as e:
        logger.error(f"❌ CDL Integration test failed: {e}")
    
    logger.info("🎉 Enhanced pipeline feature testing complete!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_features())