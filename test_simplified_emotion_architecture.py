#!/usr/bin/env python3
"""
Test Simplified Emotion Architecture
===================================

Test the simplified emotion integration to ensure it works properly
and can replace the complex Phase2Integration system.
"""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_simplified_emotion_architecture():
    """Test the complete simplified emotion architecture"""
    logger.info("🧪 Testing Simplified Emotion Architecture...")
    
    try:
        # Test 1: Import simplified emotion manager
        from src.intelligence.simplified_emotion_manager import (
            create_simplified_emotion_manager,
            process_message_with_emotional_intelligence
        )
        logger.info("✅ Successfully imported SimplifiedEmotionManager")

        # Test 2: Create simplified emotion manager
        emotion_manager = create_simplified_emotion_manager(vector_memory_manager=None)
        logger.info("✅ SimplifiedEmotionManager created successfully")

        # Test 3: Check availability
        is_available = emotion_manager.is_available()
        logger.info("✅ Emotion manager availability: %s", is_available)

        if not is_available:
            logger.warning("⚠️ Emotion manager not available - may indicate missing dependencies")
            return False

        # Test 4: Analyze message emotion
        test_messages = [
            ("I'm feeling really excited about this project!", "test_user_1"),
            ("This is so frustrating, nothing seems to work", "test_user_2"),
            ("I'm worried about tomorrow's presentation", "test_user_3")
        ]

        for message, user_id in test_messages:
            logger.info("Analyzing: '%s' for user %s", message, user_id)
            
            emotion_data = await emotion_manager.analyze_message_emotion(
                user_id=user_id,
                message=message,
                conversation_context=None
            )
            
            logger.info("  ✅ Result: %s (confidence: %.2f, support needed: %s)", 
                       emotion_data["primary_emotion"], 
                       emotion_data["confidence"],
                       emotion_data["support_needed"])

        # Test 5: Test compatibility function
        logger.info("Testing compatibility function...")
        
        conversation_context = {"messages": [], "user_id": "test_compatibility"}
        enhanced_context = await process_message_with_emotional_intelligence(
            user_id="test_compatibility",
            message="I'm feeling really happy today!",
            conversation_context=conversation_context,
            emotion_manager=emotion_manager
        )
        
        # Check if emotion data was added to context
        if "emotional_intelligence" in enhanced_context:
            emotion_intel = enhanced_context["emotional_intelligence"]
            logger.info("  ✅ Compatibility function: %s (confidence: %.2f)", 
                       emotion_intel["primary_emotion"], 
                       emotion_intel["confidence_score"])
        else:
            logger.error("  ❌ Compatibility function failed - no emotion data in context")
            return False

        # Test 6: Get system health
        logger.info("Testing system health...")
        health = await emotion_manager.get_system_health()
        logger.info("  ✅ System health: %s", health.get("status", "unknown"))

        # Test 7: Get user dashboard
        logger.info("Testing user dashboard...")
        dashboard = await emotion_manager.get_user_emotional_dashboard("test_dashboard")
        logger.info("  ✅ Dashboard: %s", dashboard.get("message", "Generated"))

        logger.info("🎉 Simplified Emotion Architecture tests completed successfully!")
        return True

    except ImportError as e:
        logger.error("❌ Import error: %s", e)
        return False
    except Exception as e:
        logger.error("❌ Test error: %s", e)
        return False


async def test_metrics_integration_compatibility():
    """Test that metrics integration could work with simplified system"""
    logger.info("🔬 Testing Metrics Integration Compatibility...")
    
    try:
        # Import metrics integration to check compatibility
        from src.metrics.metrics_integration import MetricsIntegration
        logger.info("✅ MetricsIntegration imported successfully")
        
        # Check that the updated method signature exists
        import inspect
        
        # Get the process_message_with_metrics method
        method = getattr(MetricsIntegration, 'process_message_with_metrics')
        signature = inspect.signature(method)
        params = list(signature.parameters.keys())
        
        # Check for updated parameter name
        if 'simplified_emotion_manager' in params:
            logger.info("✅ MetricsIntegration updated to use simplified_emotion_manager")
        elif 'emotional_intelligence' in params:
            logger.warning("⚠️ MetricsIntegration still uses legacy emotional_intelligence parameter")
        else:
            logger.warning("⚠️ MetricsIntegration parameters: %s", params)
        
        logger.info("🎉 Metrics Integration compatibility check completed!")
        return True
        
    except Exception as e:
        logger.error("❌ Metrics integration test error: %s", e)
        return False


async def main():
    """Main test function"""
    logger.info("🚀 Starting Simplified Emotion Architecture Tests...")
    
    # Test simplified emotion architecture
    architecture_success = await test_simplified_emotion_architecture()
    
    # Test metrics compatibility
    metrics_success = await test_metrics_integration_compatibility()
    
    if architecture_success and metrics_success:
        logger.info("✅ All simplified architecture tests passed!")
        logger.info("🎯 Ready to migrate callers from Phase2Integration to SimplifiedEmotionManager")
        return True
    else:
        logger.error("❌ Some tests failed! Check the logs above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)