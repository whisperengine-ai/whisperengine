#!/usr/bin/env python3
"""
Test Enhanced Summarization System
Verify that Tyler's art mentorship conversations get detailed summaries
while regular conversations get standard summaries.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from memory.core.storage_abstraction import HierarchicalMemoryManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedSummarizationTester:
    """Test the enhanced summarization system"""
    
    def __init__(self):
        # Create minimal config for testing
        self.config = {
            'redis_enabled': False,
            'postgresql_enabled': False, 
            'chromadb_enabled': False,
            'neo4j_enabled': False
        }
        self.memory_manager = HierarchicalMemoryManager(self.config)
    
    async def test_tyler_art_mentorship_summary(self):
        """Test that Tyler's art advice gets detailed summary"""
        user_message = "Tyler, can you help me improve my digital art composition?"
        
        bot_response = """Here's a comprehensive approach to improving your digital art composition:

1. Rule of Thirds: Position your focal points along the intersection lines of an imaginary 3x3 grid
2. Leading Lines: Use elements like roads, rivers, or architectural features to guide the viewer's eye
3. Contrast and Balance: Create visual weight through color, value, and texture contrasts
4. Depth and Layering: Use foreground, middle ground, and background elements

For your assignment this week:
- Create 3 thumbnail sketches exploring different compositions
- Focus on silhouette strength - your shapes should read clearly even in black
- Practice the "squint test" - step back and see if your composition holds together

Try these techniques:
- Color temperature shifts (warm foreground, cool background)
- Atmospheric perspective for depth
- Asymmetrical balance for dynamic compositions

Remember, good composition guides the viewer's eye through your artwork in a deliberate way."""

        # Test the enhanced summarization
        summary = await self.memory_manager._generate_conversation_summary(
            user_message, bot_response
        )
        
        logger.info("=== TYLER ART MENTORSHIP TEST ===")
        logger.info(f"User Message: {user_message[:100]}...")
        logger.info(f"Bot Response Length: {len(bot_response)} characters")
        logger.info(f"Generated Summary: {summary}")
        logger.info(f"Summary Length: {len(summary)} characters")
        
        # Verify it's a detailed summary (should be close to 300 chars)
        assert len(summary) > 200, f"Tyler summary too short: {len(summary)} chars"
        assert "tyler" in summary.lower() or "mentor" in summary.lower(), "Should detect Tyler context"
        assert "step" in summary.lower() or "technique" in summary.lower() or "assignment" in summary.lower(), "Should preserve instructional content"
        
        logger.info("✅ Tyler art mentorship summary test PASSED")
        return summary
    
    async def test_regular_conversation_summary(self):
        """Test that regular conversations get standard summary"""
        user_message = "What's the weather like today?"
        bot_response = "I don't have access to real-time weather data, but you can check your local weather by looking outside or using a weather app on your phone."
        
        # Test standard summarization
        summary = await self.memory_manager._generate_conversation_summary(
            user_message, bot_response
        )
        
        logger.info("=== REGULAR CONVERSATION TEST ===")
        logger.info(f"User Message: {user_message}")
        logger.info(f"Bot Response: {bot_response}")
        logger.info(f"Generated Summary: {summary}")
        logger.info(f"Summary Length: {len(summary)} characters")
        
        # Verify it's a standard summary (should be around 150 chars or less)
        assert len(summary) <= 150, f"Regular summary too long: {len(summary)} chars"
        assert "asked" in summary.lower() or "discussed" in summary.lower(), "Should have basic intent"
        
        logger.info("✅ Regular conversation summary test PASSED")
        return summary
    
    async def test_instructional_content_detection(self):
        """Test detection of instructional content without Tyler context"""
        user_message = "How do I create a game in Python?"
        bot_response = """Here's a step-by-step guide to creating your first Python game:

Step 1: Install pygame library using 'pip install pygame'
Step 2: Set up your game window and basic game loop
Step 3: Add player input handling for movement
Step 4: Implement collision detection
Step 5: Add game objects like enemies or collectibles

This tutorial will give you a solid foundation for game development. Practice these techniques and then try building a simple Pong or Snake game."""
        
        summary = await self.memory_manager._generate_conversation_summary(
            user_message, bot_response
        )
        
        logger.info("=== INSTRUCTIONAL CONTENT TEST ===")
        logger.info(f"Generated Summary: {summary}")
        logger.info(f"Summary Length: {len(summary)} characters")
        
        # Should be treated as instructional (longer summary)
        assert len(summary) > 200, f"Instructional summary too short: {len(summary)} chars"
        assert "step" in summary.lower() or "guide" in summary.lower(), "Should detect instructional content"
        
        logger.info("✅ Instructional content detection test PASSED")
        return summary
    
    async def test_summary_comparison(self):
        """Compare different summary types side by side"""
        logger.info("\n" + "="*60)
        logger.info("ENHANCED SUMMARIZATION COMPARISON TEST")
        logger.info("="*60)
        
        tyler_summary = await self.test_tyler_art_mentorship_summary()
        regular_summary = await self.test_regular_conversation_summary()
        instructional_summary = await self.test_instructional_content_detection()
        
        logger.info("\n" + "="*60)
        logger.info("SUMMARY COMPARISON RESULTS")
        logger.info("="*60)
        logger.info(f"Tyler/Mentor Summary ({len(tyler_summary)} chars):")
        logger.info(f"  {tyler_summary}")
        logger.info(f"\nRegular Summary ({len(regular_summary)} chars):")
        logger.info(f"  {regular_summary}")
        logger.info(f"\nInstructional Summary ({len(instructional_summary)} chars):")
        logger.info(f"  {instructional_summary}")
        
        # Verify the hierarchy: Tyler/Instructional > Regular
        assert len(tyler_summary) > len(regular_summary), "Tyler summary should be longer than regular"
        assert len(instructional_summary) > len(regular_summary), "Instructional summary should be longer than regular"
        
        logger.info("\n✅ ALL ENHANCED SUMMARIZATION TESTS PASSED!")
        logger.info("🎯 Tyler's art advice will now be preserved in detailed summaries")
        
    async def run_all_tests(self):
        """Run the complete test suite"""
        try:
            await self.test_summary_comparison()
            
            logger.info("\n" + "🎉" * 20)
            logger.info("ENHANCED SUMMARIZATION SYSTEM VERIFIED!")
            logger.info("Tyler's art mentorship advice is now preserved!")
            logger.info("🎉" * 20)
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise

async def main():
    """Main test runner"""
    tester = EnhancedSummarizationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())