#!/usr/bin/env python3
"""
Demo script for CDL Self-Memory System Phase 1

Tests importing Elena's personal knowledge and querying for personal information.
This demonstrates the core functionality of the bot self-memory system.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.memory.bot_self_memory_system import BotSelfMemorySystem, create_bot_self_memory_system
from src.memory.memory_protocol import create_memory_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_cdl_self_memory():
    """Demonstrate CDL self-memory system functionality"""
    
    print("🧠 CDL Self-Memory System Demo")
    print("=" * 50)
    
    try:
        # Initialize memory manager
        print("1. Initializing vector memory system...")
        memory_manager = create_memory_manager(memory_type="vector")
        await memory_manager.health_check()
        print("✅ Memory system initialized")
        
        # Create bot self-memory system for Elena
        print("\n2. Creating Elena's self-memory system...")
        elena_memory = create_bot_self_memory_system("elena", memory_manager)
        print("✅ Elena's self-memory system created")
        
        # Import Elena's CDL knowledge
        print("\n3. Importing Elena's personal knowledge from CDL...")
        imported_count = await elena_memory.import_cdl_knowledge("elena-rodriguez.json")
        print(f"✅ Imported {imported_count} knowledge entries")
        
        # Get knowledge statistics
        print("\n4. Getting knowledge statistics...")
        stats = await elena_memory.get_knowledge_stats()
        print(f"📊 Knowledge Statistics:")
        print(f"   - Total entries: {stats.get('total_knowledge_entries', 0)}")
        print(f"   - Categories: {stats.get('knowledge_categories', {})}")
        print(f"   - Self-reflections: {stats.get('self_reflections', 0)}")
        
        # Test personal knowledge queries
        print("\n5. Testing personal knowledge queries...")
        
        test_queries = [
            ("Do you have a boyfriend?", ["boyfriend", "dating", "relationship"]),
            ("Tell me about your childhood", ["childhood", "growing up", "family"]),
            ("What are you working on?", ["projects", "research", "goals"]),
            ("What's your daily routine?", ["routine", "schedule", "habits"]),
            ("Tell me about your family", ["family", "background", "grandmother"])
        ]
        
        for question, search_terms in test_queries:
            print(f"\n❓ Query: '{question}'")
            
            # Try different search approaches
            for search_term in search_terms[:2]:  # Test first 2 search terms
                results = await elena_memory.query_self_knowledge(search_term, limit=2)
                
                if results:
                    print(f"   🔍 Search term '{search_term}' found {len(results)} results:")
                    for i, result in enumerate(results, 1):
                        content = result['content'][:120] + "..." if len(result['content']) > 120 else result['content']
                        print(f"      {i}. [{result['category']}] {content}")
                        print(f"         (confidence: {result['confidence_score']:.2f}, relevance: {result.get('relevance_score', 0.0):.2f})")
                    break
                else:
                    print(f"   ❌ No results for search term '{search_term}'")
        
        # Test self-reflection storage (mock data)
        print("\n6. Testing self-reflection storage...")
        from src.memory.bot_self_memory_system import SelfReflection
        
        mock_reflection = SelfReflection(
            interaction_context="User asked about marine biology research",
            bot_response_preview="I got really excited talking about coral restoration and mentioned my grandmother's fishing wisdom...",
            effectiveness_score=0.85,
            authenticity_score=0.95,
            emotional_resonance=0.90,
            learning_insight="I'm most authentic when I connect my research to family traditions and personal experiences",
            improvement_suggestion="I should reference specific research findings more often to build credibility"
        )
        
        await elena_memory.store_self_reflection(mock_reflection)
        print("✅ Self-reflection stored successfully")
        
        # Test recent insights retrieval
        print("\n7. Testing recent insights retrieval...")
        insights = await elena_memory.get_recent_insights(limit=2)
        if insights:
            print(f"📝 Found {len(insights)} recent insights:")
            for i, insight in enumerate(insights, 1):
                print(f"   {i}. {insight['learning_insight']}")
                print(f"      Improvement: {insight['improvement_suggestion']}")
                print(f"      Effectiveness: {insight['effectiveness_score']:.2f}")
        else:
            print("❌ No recent insights found")
        
        print("\n🎉 Demo completed successfully!")
        print("\nNext steps:")
        print("- Integrate with CDL prompt system")
        print("- Test with other characters (Marcus, Dream, etc.)")
        print("- Implement Phase 2: Self-reflection system")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run demo
    asyncio.run(demo_cdl_self_memory())