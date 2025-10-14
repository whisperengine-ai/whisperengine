#!/usr/bin/env python3
"""
Direct Context Switch Detection Test
===================================

Tests context switch detection feature directly to validate functionality.
"""

import asyncio
import logging
import os
import sys
sys.path.append('/Users/markcastillo/git/whisperengine')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_context_switch_detection():
    """Test context switch detection with a complex message."""
    try:
        # Set up environment
        os.environ['DISCORD_BOT_NAME'] = 'elena'
        os.environ['FASTEMBED_CACHE_PATH'] = '/tmp/fastembed_cache'
        os.environ['QDRANT_HOST'] = 'localhost'
        os.environ['QDRANT_PORT'] = '6334'
        os.environ['POSTGRES_HOST'] = 'localhost'
        os.environ['POSTGRES_PORT'] = '5433'
        os.environ['QDRANT_COLLECTION_NAME'] = 'whisperengine_memory_elena_7d'  # Use Elena's actual collection
        
        # Import and create components
        from src.memory.memory_protocol import create_memory_manager
        from src.intelligence.context_switch_detector import ContextSwitchDetector
        
        logger.info("🔍 Creating memory manager...")
        memory_manager = create_memory_manager(memory_type="vector")
        
        logger.info("🔍 Creating context switch detector...")
        context_detector = ContextSwitchDetector(vector_memory_store=memory_manager)
        
        # Test message with obvious topic and mood shift
        test_user_id = "672814231002939413"
        test_message = "Hey Elena, I was really excited about coral reefs earlier, but now I am feeling worried about climate change and want to shift to discussing poetry instead. Can you write me a haiku about sadness?"
        
        logger.info("🔍 Testing context switch detection...")
        logger.info(f"🔍 User ID: {test_user_id}")
        logger.info(f"🔍 Message: {test_message}")
        
        # Detect context switches
        detected_switches = await context_detector.detect_context_switches(
            user_id=test_user_id,
            new_message=test_message
        )
        
        logger.info(f"🎯 RESULT: Detected {len(detected_switches)} context switches")
        
        for i, switch in enumerate(detected_switches):
            logger.info(f"🔍 Switch {i+1}:")
            logger.info(f"  Type: {switch.switch_type}")
            logger.info(f"  Strength: {switch.strength}")
            logger.info(f"  Confidence: {switch.confidence_score}")
            logger.info(f"  Description: {switch.description}")
            logger.info(f"  Evidence: {switch.evidence}")
            logger.info(f"  Previous Context: {switch.previous_context}")
            logger.info(f"  New Context: {switch.new_context}")
        
        if len(detected_switches) > 0:
            logger.info("✅ Context switch detection is WORKING!")
        else:
            logger.warning("⚠️ No context switches detected - may need debugging")
            
    except Exception as e:
        logger.error(f"❌ Error testing context switch detection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_context_switch_detection())