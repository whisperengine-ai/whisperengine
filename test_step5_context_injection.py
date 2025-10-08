#!/usr/bin/env python3
"""
STEP 5: Proactive Context Injection Test

Tests the CharacterContextEnhancer that automatically detects topics in user 
messages and injects relevant character knowledge into system prompts.
"""

import asyncio
import logging
import os
import sys
import asyncpg

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def setup_test_environment():
    """Set up test environment with database connection and components"""
    # PostgreSQL connection - use Docker container credentials
    postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port = int(os.getenv('POSTGRES_PORT', '5433'))
    postgres_user = os.getenv('POSTGRES_USER', 'whisperengine')
    postgres_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
    postgres_db = os.getenv('POSTGRES_DB', 'whisperengine')

    try:
        # Create connection pool
        postgres_pool = await asyncpg.create_pool(
            host=postgres_host,
            port=postgres_port,
            user=postgres_user,
            password=postgres_password,
            database=postgres_db,
            min_size=1,
            max_size=5
        )
        
        logger.info("✅ PostgreSQL connection established")
        
        # Import components
        from src.characters.cdl.character_graph_manager import create_character_graph_manager
        from src.characters.cdl.character_context_enhancer import create_character_context_enhancer
        
        # Create CharacterGraphManager
        character_graph_manager = create_character_graph_manager(postgres_pool)
        
        # Create CharacterContextEnhancer (STEP 5 component)
        context_enhancer = create_character_context_enhancer(
            character_graph_manager, postgres_pool
        )
        
        return postgres_pool, character_graph_manager, context_enhancer
        
    except (asyncpg.PostgresError, ConnectionError) as e:
        logger.error("❌ Test setup failed: %s", e)
        return None, None, None


async def test_topic_detection(context_enhancer):
    """Test topic detection functionality"""
    logger.info("🔍 Testing topic detection...")
    
    test_messages = [
        ("I've been thinking about getting into underwater photography", 
         ["marine_biology", "photography"]),
        ("My AI research is focusing on neural network safety", 
         ["ai_research"]),
        ("I love cooking Italian food and trying new recipes", 
         ["food"]),
        ("Just got back from an amazing trip to Japan", 
         ["travel"]),
        ("Working on my indie game using Unity", 
         ["game_development", "technology"]),
        ("Need help with my marketing campaign strategy", 
         ["marketing"]),
        ("Hello there! How are you today?", 
         [])  # Should detect no specific topics
    ]
    
    success_count = 0
    total_tests = len(test_messages)
    
    for message, expected_topics in test_messages:
        # Use public method for testing
        detected_topics = context_enhancer.detect_topics_public(message)
        
        # Check if all expected topics were detected
        topics_found = all(topic in detected_topics for topic in expected_topics)
        
        if topics_found:
            success_count += 1
            logger.info("✅ Message: '%s...' → Topics: %s", 
                       message[:50], detected_topics)
        else:
            logger.warning("❌ Message: '%s...' → Expected: %s, Got: %s", 
                          message[:50], expected_topics, detected_topics)
    
    logger.info("📊 Topic Detection: %d/%d tests passed (%.1f%%)", 
               success_count, total_tests, (success_count/total_tests)*100)
    
    return success_count == total_tests


async def test_context_injection_elena(context_enhancer):
    """Test context injection for Elena (marine biologist)"""
    logger.info("🎯 Testing context injection for Elena...")
    
    base_prompt = """You are Elena Rodriguez, a marine biologist passionate about ocean conservation.
Your personality: Warm, educational, scientifically rigorous, optimistic about conservation."""
    
    test_scenarios = [
        {
            "message": "I'm interested in learning about coral reef diving",
            "character": "elena",
            "expected_topics": ["marine_biology", "diving"],
            "should_enhance": True,
            "description": "Marine biology + diving topic should trigger Elena's expertise"
        },
        {
            "message": "What's your favorite type of photography equipment?", 
            "character": "elena",
            "expected_topics": ["photography"],
            "should_enhance": False,  # Elena is marine biologist, not photographer
            "description": "Photography topic should have low relevance for Elena"
        },
        {
            "message": "How's the weather today?",
            "character": "elena", 
            "expected_topics": [],
            "should_enhance": False,
            "description": "Generic message should not trigger context injection"
        }
    ]
    
    success_count = 0
    total_tests = len(test_scenarios)
    
    for scenario in test_scenarios:
        try:
            result = await context_enhancer.detect_and_inject_context(
                user_message=scenario["message"],
                character_name=scenario["character"],
                base_system_prompt=base_prompt,
                relevance_threshold=0.5
            )
            
            # Check topic detection
            topics_correct = set(result.detected_topics) >= set(scenario["expected_topics"])
            
            # Check injection behavior
            if scenario["should_enhance"]:
                # Should have enhanced the prompt
                prompt_enhanced = len(result.enhanced_prompt) > len(base_prompt)
                injection_score_good = result.injection_score >= 0.5
                success = topics_correct and prompt_enhanced and injection_score_good
                
                if success:
                    logger.info("✅ %s - Enhanced (score: %.2f)", 
                               scenario["description"], result.injection_score)
                    logger.info("   Topics: %s → Injected: %d background, %d abilities, %d memories", 
                               result.detected_topics,
                               len(result.relevant_background),
                               len(result.relevant_abilities), 
                               len(result.relevant_memories))
                else:
                    logger.warning("❌ %s - Enhancement failed", scenario["description"])
                    logger.warning("   Topics correct: %s, Prompt enhanced: %s, Score: %.2f",
                                  topics_correct, prompt_enhanced, result.injection_score)
            else:
                # Should NOT have significantly enhanced the prompt
                prompt_not_much_enhanced = result.injection_score < 0.5
                success = topics_correct and prompt_not_much_enhanced
                
                if success:
                    logger.info("✅ %s - No significant enhancement (score: %.2f)", 
                               scenario["description"], result.injection_score)
                else:
                    logger.warning("❌ %s - Unexpected enhancement (score: %.2f)",
                                  scenario["description"], result.injection_score)
            
            if success:
                success_count += 1
                
        except Exception as e:
            logger.error("❌ Error testing scenario '%s': %s", scenario["description"], e)
    
    logger.info("📊 Context Injection Elena: %d/%d tests passed (%.1f%%)", 
               success_count, total_tests, (success_count/total_tests)*100)
    
    return success_count == total_tests


async def test_multiple_characters(context_enhancer):
    """Test context injection across different characters"""
    logger.info("🎭 Testing context injection for multiple characters...")
    
    base_prompt = "You are {character_name} with your unique expertise and background."
    
    test_scenarios = [
        {
            "message": "I want to learn underwater photography for marine research",
            "character": "elena",
            "topics": ["marine_biology", "photography"],
            "expected_high_relevance": True,
            "description": "Elena + marine topics should be highly relevant"
        },
        {
            "message": "I'm building an AI ethics framework for my startup",
            "character": "marcus", 
            "topics": ["ai_research", "technology"],
            "expected_high_relevance": True,
            "description": "Marcus + AI topics should be highly relevant"
        },
        {
            "message": "Need advice on indie game marketing strategies",
            "character": "ryan",
            "topics": ["game_development", "marketing"],
            "expected_high_relevance": True,
            "description": "Ryan + game dev topics should be highly relevant"
        }
    ]
    
    success_count = 0
    total_tests = len(test_scenarios)
    
    for scenario in test_scenarios:
        try:
            result = await context_enhancer.detect_and_inject_context(
                user_message=scenario["message"],
                character_name=scenario["character"],
                base_system_prompt=base_prompt.format(character_name=scenario["character"]),
                relevance_threshold=0.3  # Lower threshold for testing
            )
            
            # Check if relevance expectation matches
            has_high_relevance = result.injection_score >= 0.5
            expectation_met = has_high_relevance == scenario["expected_high_relevance"]
            
            if expectation_met:
                success_count += 1
                logger.info("✅ %s - Score: %.2f, Topics: %s", 
                           scenario["description"], result.injection_score, result.detected_topics)
                
                if result.injection_score > 0.3:
                    logger.info("   Context injected: %d items total",
                               len(result.relevant_background) + 
                               len(result.relevant_abilities) + 
                               len(result.relevant_memories))
            else:
                logger.warning("❌ %s - Expected high relevance: %s, Got score: %.2f",
                              scenario["description"], scenario["expected_high_relevance"], 
                              result.injection_score)
                
        except Exception as e:
            logger.error("❌ Error testing character %s: %s", scenario["character"], e)
    
    logger.info("📊 Multiple Characters: %d/%d tests passed (%.1f%%)", 
               success_count, total_tests, (success_count/total_tests)*100)
    
    return success_count == total_tests


async def main():
    """Main test execution"""
    print("🚀 STEP 5: Proactive Context Injection Test Suite")
    logger.info("🚀 STEP 5: Proactive Context Injection Test Suite")
    logger.info("=" * 80)
    
    # Setup test environment
    postgres_pool, character_graph_manager, context_enhancer = await setup_test_environment()
    
    if not all([postgres_pool, character_graph_manager, context_enhancer]):
        logger.error("❌ Failed to set up test environment")
        return False
    
    try:
        # Run test suites
        test_results = []
        
        # Test 1: Topic Detection
        result1 = await test_topic_detection(context_enhancer)
        test_results.append(("Topic Detection", result1))
        
        # Test 2: Context Injection for Elena
        result2 = await test_context_injection_elena(context_enhancer)
        test_results.append(("Elena Context Injection", result2))
        
        # Test 3: Multiple Characters
        result3 = await test_multiple_characters(context_enhancer)
        test_results.append(("Multiple Characters", result3))
        
        # Summary
        logger.info("=" * 80)
        logger.info("📊 STEP 5 TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info("%s: %s", test_name, status)
        
        success_rate = (passed_tests / total_tests) * 100
        logger.info("-" * 40)
        logger.info("Overall Success Rate: %.1f%% (%d/%d)", success_rate, passed_tests, total_tests)
        
        if success_rate >= 80:
            logger.info("🎉 STEP 5 Proactive Context Injection: SUCCESSFUL")
            return True
        else:
            logger.warning("⚠️ STEP 5 Proactive Context Injection: NEEDS IMPROVEMENT")
            return False
            
    finally:
        # Cleanup
        if postgres_pool:
            await postgres_pool.close()
            logger.info("🔌 PostgreSQL connection closed")


if __name__ == "__main__":
    asyncio.run(main())