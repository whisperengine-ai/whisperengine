#!/usr/bin/env python3
"""
Test Multi-Bot Memory Querying Features

This demonstrates the advanced multi-bot memory capabilities:
1. Query all bots for a topic  
2. Query specific bots selectively
3. Cross-bot analysis
4. Bot memory statistics
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, 'src')

async def test_multi_bot_capabilities():
    """Test the new multi-bot memory query features"""
    
    # Set up environment
    os.environ["VECTOR_QDRANT_HOST"] = "localhost"
    os.environ["VECTOR_QDRANT_PORT"] = "6333"
    os.environ["MEMORY_SYSTEM_TYPE"] = "vector"
    
    try:
        from memory.memory_protocol import create_multi_bot_querier
        
        print("🚀 Multi-Bot Memory Query Features Test")
        print("=" * 45)
        
        # Create multi-bot querier
        querier = create_multi_bot_querier()
        if not querier:
            print("❌ Multi-bot querier not available")
            return False
        
        test_user = "demo_user_multibot"
        
        print("\n🌍 Test 1: Query All Bots")
        print("-" * 25)
        all_bot_results = await querier.query_all_bots(
            query="user preferences",
            user_id=test_user,
            top_k=10
        )
        
        print(f"Found memories from {len(all_bot_results)} bots:")
        for bot_name, memories in all_bot_results.items():
            print(f"  🤖 {bot_name}: {len(memories)} memories")
        
        print("\n🎯 Test 2: Query Specific Bots")
        print("-" * 30)
        specific_results = await querier.query_specific_bots(
            query="emotional support",
            user_id=test_user,
            bot_names=["Elena", "Gabriel"],
            top_k=5
        )
        
        print(f"Found memories from {len(specific_results)} of 2 requested bots:")
        for bot_name, memories in specific_results.items():
            print(f"  🤖 {bot_name}: {len(memories)} memories")
            if memories:
                print(f"      Sample: {memories[0]['content'][:60]}...")
        
        print("\n🔍 Test 3: Cross-Bot Analysis")
        print("-" * 28)
        analysis = await querier.cross_bot_analysis(
            user_id=test_user,
            analysis_topic="conversations"
        )
        
        print(f"Analysis Results:")
        print(f"  🎯 Topic: {analysis['topic']}")
        print(f"  🤖 Bots analyzed: {len(analysis['bots_analyzed'])}")
        print(f"  💾 Total memories: {analysis['total_memories']}")
        
        if 'insights' in analysis:
            insights = analysis['insights']
            print(f"  🏆 Most relevant bot: {insights.get('most_relevant_bot', 'N/A')}")
            print(f"  💫 Highest confidence bot: {insights.get('highest_confidence_bot', 'N/A')}")
            print(f"  📊 Most memories bot: {insights.get('most_memories_bot', 'N/A')}")
        
        print("\n📊 Test 4: Bot Memory Statistics")
        print("-" * 32)
        stats = await querier.get_bot_memory_stats(user_id=test_user)
        
        print(f"Memory statistics for {len(stats)} bots:")
        for bot_name, bot_stats in stats.items():
            print(f"  🤖 {bot_name}:")
            print(f"      📝 Total memories: {bot_stats['total_memories']}")
            print(f"      👥 Unique users: {bot_stats['unique_users']}")
            print(f"      💫 Avg confidence: {bot_stats['average_confidence']:.3f}")
            print(f"      🎯 Avg significance: {bot_stats['average_significance']:.3f}")
        
        print("\n🎉 All Multi-Bot Features Working!")
        print("\n💡 Advanced Use Cases Now Available:")
        print("   🔍 Admin can debug across all bots")
        print("   📊 Compare bot performance and behavior")
        print("   🤝 Enable collaborative bot decision making")
        print("   🧠 Synthesize knowledge across bot personalities")
        print("   📈 Analyze user patterns across different bot interactions")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_multi_bot_capabilities())
    sys.exit(0 if success else 1)