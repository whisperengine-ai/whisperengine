#!/usr/bin/env python3
"""
Demo: LLM-Powered CDL Self-Memory System

Demonstrates the new AI-powered bot self-memory system that uses LLM Tool Calling
to intelligently extract personal knowledge from CDL files, generate self-reflections,
and query bot knowledge contextually.

This is the enhanced version that leverages WhisperEngine's existing LLM infrastructure
instead of using hardcoded CDL parsing.
"""

import asyncio
import logging
import json
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
import sys
sys.path.append('.')

# Import required components
from src.llm.llm_protocol import create_llm_client
from src.memory.memory_protocol import create_memory_manager
from src.memory.llm_powered_bot_memory import create_llm_powered_bot_memory


async def demo_llm_knowledge_extraction():
    """Demo: LLM-powered knowledge extraction from Elena's CDL file"""
    logger.info("🧠 === LLM-Powered Knowledge Extraction Demo ===")
    
    try:
        # Initialize components
        llm_client = create_llm_client("openrouter")
        memory_manager = create_memory_manager("vector")
        
        # Create LLM-powered bot memory for Elena
        elena_memory = create_llm_powered_bot_memory("elena", llm_client, memory_manager)
        
        # Extract knowledge from Elena's CDL file using LLM
        logger.info("📖 Extracting knowledge from Elena's CDL file using LLM...")
        extraction_result = await elena_memory.extract_cdl_knowledge_with_llm("elena-rodriguez.json")
        
        # Display results
        logger.info(f"✅ LLM Knowledge Extraction Complete!")
        logger.info(f"   📊 Total items extracted: {extraction_result.total_items}")
        logger.info(f"   🎯 Confidence score: {extraction_result.confidence_score:.2f}")
        logger.info(f"   📂 Categories found: {list(extraction_result.categories.keys())}")
        
        # Show some examples
        for category, items in extraction_result.categories.items():
            if items:  # Only show categories with content
                logger.info(f"\n🔸 {category.upper()} ({len(items)} items):")
                for i, item in enumerate(items[:2], 1):  # Show first 2 items
                    content = item.get('content', '')[:100] + "..." if len(item.get('content', '')) > 100 else item.get('content', '')
                    queries = item.get('search_queries', [])[:3]  # Show first 3 queries
                    logger.info(f"   {i}. {content}")
                    logger.info(f"      🔍 Searchable: {', '.join(queries)}")
                    logger.info(f"      📈 Confidence: {item.get('confidence', 0.0):.2f}")
        
        return elena_memory, extraction_result
        
    except Exception as e:
        logger.error(f"❌ Knowledge extraction demo failed: {e}")
        return None, None


async def demo_llm_knowledge_queries(elena_memory):
    """Demo: LLM-powered personal knowledge queries"""
    logger.info("\n🔍 === LLM-Powered Knowledge Query Demo ===")
    
    # Test queries that Elena should be able to answer about herself
    test_queries = [
        "Do you have a boyfriend?",
        "Tell me about your research",
        "What's your daily routine like?",
        "What are you passionate about?",
        "Do you have any fears or concerns?"
    ]
    
    for query in test_queries:
        try:
            logger.info(f"\n❓ Query: '{query}'")
            
            # Use LLM to find and format relevant knowledge
            query_result = await elena_memory.query_personal_knowledge_with_llm(query, limit=3)
            
            if query_result.get("found_relevant_info"):
                logger.info("✅ Found relevant personal knowledge!")
                
                relevant_items = query_result.get("relevant_items", [])
                logger.info(f"   📝 Found {len(relevant_items)} relevant items")
                
                for i, item in enumerate(relevant_items, 1):
                    content = item.get('formatted_content', '')
                    category = item.get('category', 'unknown')
                    confidence = item.get('confidence', 0.0)
                    logger.info(f"   {i}. [{category.upper()}] {content[:120]}...")
                    logger.info(f"      🎯 Confidence: {confidence:.2f}")
                
                # Show response guidance
                guidance = query_result.get("response_guidance", "")
                if guidance:
                    logger.info(f"   💡 Response guidance: {guidance[:100]}...")
                
                authenticity_tips = query_result.get("authenticity_tips", "")
                if authenticity_tips:
                    logger.info(f"   🎭 Authenticity tips: {authenticity_tips[:100]}...")
            else:
                logger.info("❌ No relevant personal knowledge found")
                guidance = query_result.get("response_guidance", "No guidance available")
                logger.info(f"   💭 Guidance: {guidance}")
                
        except Exception as e:
            logger.error(f"❌ Query '{query}' failed: {e}")


async def demo_llm_self_reflection():
    """Demo: LLM-powered self-reflection on interactions"""
    logger.info("\n🤔 === LLM-Powered Self-Reflection Demo ===")
    
    try:
        # Initialize components
        llm_client = create_llm_client("openrouter")
        memory_manager = create_memory_manager("vector")
        elena_memory = create_llm_powered_bot_memory("elena", llm_client, memory_manager)
        
        # Simulate interaction data
        interaction_data = {
            "user_message": "Tell me about your research on coral reefs",
            "bot_response": "I'm passionate about coral reef conservation! My research focuses on how rising ocean temperatures affect coral health. I've been studying bleaching patterns in the Caribbean, and it's both heartbreaking and motivating. Every day I see the urgency of this work - these ecosystems support 25% of marine life but cover less than 1% of the ocean floor.",
            "character_context": "Elena Rodriguez - Marine Biologist, specializes in coral reef research",
            "interaction_outcome": "positive_engagement"
        }
        
        logger.info("🎭 Simulating interaction self-reflection...")
        logger.info(f"   👤 User: {interaction_data['user_message']}")
        logger.info(f"   🤖 Elena: {interaction_data['bot_response'][:80]}...")
        
        # Generate LLM-powered self-reflection
        reflection = await elena_memory.generate_self_reflection_with_llm(interaction_data)
        
        logger.info(f"\n✅ LLM Self-Reflection Generated!")
        logger.info(f"   🎯 Effectiveness Score: {reflection.effectiveness_score:.2f}")
        logger.info(f"   🎭 Authenticity Score: {reflection.authenticity_score:.2f}")
        logger.info(f"   💖 Emotional Resonance: {reflection.emotional_resonance:.2f}")
        logger.info(f"   🧠 Dominant Trait: {reflection.dominant_personality_trait}")
        
        logger.info(f"\n📝 Self-Evaluation:")
        logger.info(f"   {reflection.self_evaluation}")
        
        logger.info(f"\n💡 Learning Insight:")
        logger.info(f"   {reflection.learning_insight}")
        
        logger.info(f"\n🔄 Improvement Suggestion:")
        logger.info(f"   {reflection.improvement_suggestion}")
        
        return reflection
        
    except Exception as e:
        logger.error(f"❌ Self-reflection demo failed: {e}")
        return None


async def demo_llm_insight_tracking(elena_memory):
    """Demo: Tracking LLM-generated insights over time"""
    logger.info("\n📈 === LLM Insight Tracking Demo ===")
    
    try:
        # Get recent LLM-generated insights
        recent_insights = await elena_memory.get_recent_llm_insights(limit=3)
        
        if recent_insights:
            logger.info(f"✅ Found {len(recent_insights)} recent LLM insights:")
            
            for i, insight in enumerate(recent_insights, 1):
                logger.info(f"\n🔸 Insight #{i}:")
                logger.info(f"   💡 Learning: {insight.get('learning_insight', 'N/A')}")
                logger.info(f"   🔄 Improvement: {insight.get('improvement_suggestion', 'N/A')}")
                logger.info(f"   🎯 Effectiveness: {insight.get('effectiveness_score', 0.0):.2f}")
                logger.info(f"   🎭 Dominant Trait: {insight.get('dominant_personality_trait', 'N/A')}")
                logger.info(f"   📅 Created: {insight.get('created_at', 'N/A')}")
        else:
            logger.info("ℹ️ No recent insights found (this is normal for first run)")
            
    except Exception as e:
        logger.error(f"❌ Insight tracking demo failed: {e}")


async def demo_character_comparison():
    """Demo: Compare knowledge extraction between different characters"""
    logger.info("\n⚖️ === Character Knowledge Comparison Demo ===")
    
    try:
        # Initialize components
        llm_client = create_llm_client("openrouter")
        memory_manager = create_memory_manager("vector")
        
        # Test with different characters
        characters = [
            ("elena", "elena-rodriguez.json", "Marine Biologist"),
            ("marcus", "marcus-thompson.json", "AI Researcher")
        ]
        
        extraction_results = {}
        
        for bot_name, character_file, description in characters:
            logger.info(f"\n🔸 Extracting knowledge for {bot_name.title()} ({description})...")
            
            # Check if character file exists
            character_path = Path(f"characters/examples/{character_file}")
            if not character_path.exists():
                logger.warning(f"   ⚠️ Character file not found: {character_file}")
                continue
            
            # Create bot memory and extract knowledge
            bot_memory = create_llm_powered_bot_memory(bot_name, llm_client, memory_manager)
            result = await bot_memory.extract_cdl_knowledge_with_llm(character_file)
            
            extraction_results[bot_name] = result
            
            logger.info(f"   ✅ Extracted {result.total_items} items")
            logger.info(f"   📂 Categories: {list(result.categories.keys())}")
            logger.info(f"   🎯 Confidence: {result.confidence_score:.2f}")
        
        # Compare results
        if len(extraction_results) > 1:
            logger.info(f"\n📊 Comparison Results:")
            for bot_name, result in extraction_results.items():
                logger.info(f"   🤖 {bot_name.title()}: {result.total_items} items, {result.confidence_score:.2f} confidence")
        
        return extraction_results
        
    except Exception as e:
        logger.error(f"❌ Character comparison demo failed: {e}")
        return {}


async def main():
    """Run complete LLM-Powered CDL Self-Memory System demo"""
    logger.info("🚀 Starting LLM-Powered CDL Self-Memory System Demo")
    logger.info("=" * 60)
    
    try:
        # Phase 1: LLM Knowledge Extraction
        elena_memory, extraction_result = await demo_llm_knowledge_extraction()
        
        if elena_memory and extraction_result:
            # Phase 2: LLM Knowledge Queries
            await demo_llm_knowledge_queries(elena_memory)
            
            # Phase 3: LLM Self-Reflection
            reflection = await demo_llm_self_reflection()
            
            # Phase 4: LLM Insight Tracking
            await demo_llm_insight_tracking(elena_memory)
        
        # Phase 5: Character Comparison
        await demo_character_comparison()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 LLM-Powered CDL Self-Memory System Demo Complete!")
        logger.info("\nKey Features Demonstrated:")
        logger.info("✅ AI-powered knowledge extraction from CDL files")
        logger.info("✅ Intelligent contextual knowledge queries")
        logger.info("✅ LLM-generated self-reflection and analysis")
        logger.info("✅ Automated personality evolution tracking")
        logger.info("✅ Multi-character knowledge comparison")
        
        logger.info("\n💡 Next Steps:")
        logger.info("• Integrate with Discord bot message handlers")
        logger.info("• Add knowledge query to CDL prompt generation")
        logger.info("• Implement real-time self-reflection triggers")
        logger.info("• Create personality evolution dashboards")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())