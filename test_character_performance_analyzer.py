#!/usr/bin/env python3
"""
Quick Test: Character Performance Analyzer - Sprint 4

Tests the basic functionality of the Character Performance Analyzer
without requiring full system setup.
"""

import sys
import os
import asyncio
import logging

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.characters.performance_analyzer import (
    create_character_performance_analyzer,
    CharacterEffectivenessData,
    PerformanceMetric
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_character_performance_analyzer():
    """Test Character Performance Analyzer functionality"""
    
    logger.info("🧪 Testing Character Performance Analyzer - Sprint 4: CharacterEvolution")
    
    try:
        # Create analyzer without dependencies (will use mock data)
        analyzer = create_character_performance_analyzer()
        
        # Test 1: Basic character effectiveness analysis
        logger.info("\n📊 Test 1: Character Effectiveness Analysis")
        effectiveness_data = await analyzer.analyze_character_effectiveness("elena", days_back=14)
        
        assert isinstance(effectiveness_data, CharacterEffectivenessData)
        assert effectiveness_data.bot_name == "elena"
        assert 0.0 <= effectiveness_data.overall_effectiveness <= 1.0
        assert len(effectiveness_data.metric_scores) == 6  # 6 performance metrics
        
        logger.info("✅ Character effectiveness analysis: PASSED")
        logger.info(f"   - Overall effectiveness: {effectiveness_data.overall_effectiveness:.2f}")
        logger.info(f"   - Conversation quality: {effectiveness_data.conversation_quality_avg:.2f}")
        logger.info(f"   - Memory effectiveness: {effectiveness_data.memory_effectiveness_score:.2f}")
        logger.info(f"   - Relationship progression: {effectiveness_data.relationship_progression_rate:.2f}")
        
        # Test 2: Optimization opportunity identification
        logger.info("\n🎯 Test 2: Optimization Opportunity Identification")
        opportunities = await analyzer.identify_optimization_opportunities("elena")
        
        assert isinstance(opportunities, list)
        assert len(opportunities) > 0  # Should find some opportunities with mock data
        
        logger.info("✅ Optimization opportunity identification: PASSED")
        logger.info(f"   - Opportunities found: {len(opportunities)}")
        
        for i, opp in enumerate(opportunities[:3]):  # Show first 3
            logger.info(f"   - Opportunity {i+1}: {opp.category.value} (Impact: {opp.impact_potential:.2f})")
        
        # Test 3: CDL trait correlation analysis
        logger.info("\n🎭 Test 3: CDL Trait Correlation Analysis")
        trait_correlations = await analyzer.correlate_personality_traits_with_outcomes("elena")
        
        assert isinstance(trait_correlations, dict)
        # May be empty if CDL parser not available, but should not error
        
        logger.info("✅ CDL trait correlation analysis: PASSED")
        logger.info(f"   - Trait correlations analyzed: {len(trait_correlations)}")
        
        # Test 4: Multiple character analysis
        logger.info("\n👥 Test 4: Multiple Character Analysis")
        
        characters = ["elena", "marcus", "jake"]
        character_results = {}
        
        for character in characters:
            try:
                result = await analyzer.analyze_character_effectiveness(character, days_back=7)
                character_results[character] = result.overall_effectiveness
                logger.info(f"   - {character.capitalize()}: {result.overall_effectiveness:.2f}")
            except Exception as e:
                logger.warning(f"   - {character.capitalize()}: Error ({e})")
        
        assert len(character_results) > 0
        logger.info("✅ Multiple character analysis: PASSED")
        
        # Test 5: Performance metric validation
        logger.info("\n📈 Test 5: Performance Metric Validation")
        
        # Check all performance metrics are present
        expected_metrics = {
            PerformanceMetric.CONVERSATION_QUALITY,
            PerformanceMetric.CONFIDENCE_TRENDS,
            PerformanceMetric.MEMORY_EFFECTIVENESS,
            PerformanceMetric.RELATIONSHIP_PROGRESSION,
            PerformanceMetric.TRUST_BUILDING,
            PerformanceMetric.USER_ENGAGEMENT
        }
        
        actual_metrics = set(effectiveness_data.metric_scores.keys())
        assert expected_metrics == actual_metrics
        
        # Verify all scores are valid (0-1 range)
        for metric, score in effectiveness_data.metric_scores.items():
            assert 0.0 <= score <= 1.0, f"Invalid score for {metric}: {score}"
        
        logger.info("✅ Performance metric validation: PASSED")
        logger.info(f"   - All {len(expected_metrics)} metrics present and valid")
        
        # Summary
        logger.info("\n🎉 Character Performance Analyzer Test Summary:")
        logger.info("✅ Basic character effectiveness analysis: PASSED")
        logger.info("✅ Optimization opportunity identification: PASSED") 
        logger.info("✅ CDL trait correlation analysis: PASSED")
        logger.info("✅ Multiple character analysis: PASSED")
        logger.info("✅ Performance metric validation: PASSED")
        logger.info(f"\n📊 Sprint 4 Character Performance Analyzer: 5/5 tests PASSED")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Character Performance Analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test execution"""
    logger.info("🚀 Sprint 4: CharacterEvolution - Character Performance Analyzer Test")
    logger.info("="*70)
    
    success = await test_character_performance_analyzer()
    
    if success:
        logger.info("\n🎯 CHARACTER PERFORMANCE ANALYZER READY FOR SPRINT 4!")
        logger.info("Next: Implement CDL Parameter Optimizer")
    else:
        logger.error("\n❌ Character Performance Analyzer needs fixes before proceeding")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())