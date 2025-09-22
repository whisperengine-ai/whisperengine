#!/usr/bin/env python3
"""
Test Enhanced Vector Emotion Analyzer
=====================================

Test script to verify the enhanced vector emotion analyzer functionality.
"""

import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.intelligence.enhanced_vector_emotion_analyzer import create_enhanced_emotion_analyzer
from src.intelligence.unified_emotion_integration import create_unified_emotion_integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_enhanced_emotion_analyzer():
    """Test the enhanced vector emotion analyzer"""
    logger.info("Testing Enhanced Vector Emotion Analyzer...")
    
    # Create analyzer without vector memory for testing
    analyzer = create_enhanced_emotion_analyzer(vector_memory_manager=None)
    
    if not analyzer:
        logger.error("Failed to create Enhanced Vector Emotion Analyzer")
        return False
        
    logger.info("✅ Enhanced Vector Emotion Analyzer created successfully")
    
    # Test basic emotion analysis
    test_messages = [
        ("I'm feeling really happy today!", "test_user_1"),
        ("This is so frustrating, nothing is working!", "test_user_2"),
        ("I'm worried about the meeting tomorrow", "test_user_3"),
        ("Everything is just perfect right now", "test_user_4"),
        ("I don't know how I feel about this", "test_user_5")
    ]
    
    for message, user_id in test_messages:
        try:
            logger.info(f"Analyzing: '{message}' for user {user_id}")
            
            result = await analyzer.analyze_emotion(
                content=message,
                user_id=user_id,
                conversation_context=None,
                recent_emotions=None
            )
            
            logger.info(f"  ✅ Result: {result.primary_emotion} (confidence: {result.confidence:.2f}, intensity: {result.intensity:.2f})")
            
        except Exception as e:
            logger.error(f"  ❌ Error analyzing '{message}': {e}")
            return False
    
    # Test comprehensive emotional assessment
    try:
        logger.info("Testing comprehensive emotional assessment...")
        
        assessment = await analyzer.comprehensive_emotional_assessment(
            user_id="test_user_comprehensive",
            current_message="I've been feeling really down lately, everything seems overwhelming",
            conversation_context={"messages": []}
        )
        
        logger.info(f"  ✅ Assessment: {assessment['primary_emotion']} (confidence: {assessment['confidence']:.2f})")
        logger.info(f"  📊 Recommendations: {assessment.get('recommendations', [])}")
        
    except Exception as e:
        logger.error(f"  ❌ Error in comprehensive assessment: {e}")
        return False
    
    # Test dashboard functionality
    try:
        logger.info("Testing emotional dashboard...")
        
        dashboard = await analyzer.get_user_emotional_dashboard("test_user_dashboard")
        logger.info(f"  ✅ Dashboard: {dashboard.get('message', 'Generated successfully')}")
        
    except Exception as e:
        logger.error(f"  ❌ Error in dashboard: {e}")
        return False
    
    # Test intervention system
    try:
        logger.info("Testing intervention system...")
        
        intervention = await analyzer.execute_intervention("test_user_intervention", "supportive_check_in")
        logger.info(f"  ✅ Intervention: {intervention.get('strategy', 'Executed successfully')}")
        
    except Exception as e:
        logger.error(f"  ❌ Error in intervention: {e}")
        return False
    
    # Test system health
    try:
        logger.info("Testing system health report...")
        
        health = await analyzer.get_system_health_report()
        logger.info(f"  ✅ Health: {health.get('system_status', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"  ❌ Error in health report: {e}")
        return False
    
    logger.info("🎉 Enhanced Vector Emotion Analyzer tests completed successfully!")
    return True


async def test_unified_integration():
    """Test the unified emotion integration"""
    logger.info("Testing Unified Emotion Integration...")
    
    # Create integration without vector memory for testing
    integration = create_unified_emotion_integration(vector_memory_manager=None)
    
    if not integration:
        logger.error("Failed to create Unified Emotion Integration")
        return False
        
    logger.info("✅ Unified Emotion Integration created successfully")
    
    # Test comprehensive assessment through integration
    try:
        logger.info("Testing integration comprehensive assessment...")
        
        assessment = await integration.comprehensive_emotional_assessment(
            user_id="integration_test_user",
            current_message="I'm feeling anxious about this new project",
            conversation_context={"messages": []}
        )
        
        logger.info(f"  ✅ Assessment: {assessment['primary_emotion']} (confidence: {assessment['confidence']:.2f})")
        
    except Exception as e:
        logger.error(f"  ❌ Error in integration assessment: {e}")
        return False
    
    logger.info("🎉 Unified Emotion Integration tests completed successfully!")
    return True


async def main():
    """Main test function"""
    logger.info("🚀 Starting Enhanced Vector Emotion System Tests...")
    
    # Test enhanced analyzer
    analyzer_success = await test_enhanced_emotion_analyzer()
    
    # Test unified integration
    integration_success = await test_unified_integration()
    
    if analyzer_success and integration_success:
        logger.info("✅ All tests passed! Enhanced Vector Emotion System is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed! Check the logs above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)