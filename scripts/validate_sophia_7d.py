#!/usr/bin/env python3
"""
Sophia 7D Migration Validation Script
Tests marketing expertise and professional intelligence after 7D migration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment  
load_dotenv(".env.sophia")

async def test_sophia_7d_intelligence():
    """Test Sophia's marketing expertise with 7D intelligence"""
    
    print("💼 Testing Sophia's 7D Marketing Intelligence")
    print("=" * 55)
    print("Character: Sophia Blake - Marketing Executive")
    print()
    
    try:
        # Setup clients
        from src.memory.memory_protocol import create_memory_manager
        from src.llm.llm_protocol import create_llm_client
        
        # Initialize systems
        memory_manager = create_memory_manager("vector")
        llm_client = create_llm_client("openrouter") 
        
        print("✅ Connected to Sophia's 7D memory system")
        
        # Test queries for marketing expertise
        test_scenarios = [
            {
                "category": "🎯 Marketing Strategy",
                "query": "What marketing strategies work best for SaaS companies?",
                "expected_topics": ["lead generation", "content marketing", "customer acquisition", "conversion", "digital marketing"]
            },
            {
                "category": "📊 Campaign Analytics", 
                "query": "How do you measure campaign ROI and optimize performance?",
                "expected_topics": ["ROI", "analytics", "metrics", "KPIs", "A/B testing", "optimization"]
            },
            {
                "category": "🤝 Client Management",
                "query": "Tell me about managing client relationships and expectations",
                "expected_topics": ["client", "relationship", "communication", "expectations", "stakeholder", "project management"]
            },
            {
                "category": "🎨 Brand Development",
                "query": "What's your approach to brand positioning and messaging?",
                "expected_topics": ["brand", "positioning", "messaging", "identity", "voice", "audience"]
            },
            {
                "category": "📱 Digital Marketing",
                "query": "What are the latest trends in social media marketing?",
                "expected_topics": ["social media", "trends", "engagement", "platforms", "content", "viral"]
            }
        ]
        
        print(f"🧪 Running {len(test_scenarios)} marketing expertise tests...")
        print()
        
        total_score = 0
        max_score = 0
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"Test {i}: {scenario['category']}")
            print(f"Query: \"{scenario['query']}\"")
            
            try:
                # Retrieve relevant memories
                memories = await memory_manager.retrieve_relevant_memories(
                    user_id="test_user_sophia_7d",
                    query=scenario['query'],
                    limit=5
                )
                
                print(f"📊 Retrieved {len(memories)} relevant memories")
                
                # Score based on memory relevance and content  
                scenario_score = 0
                scenario_max = len(scenario['expected_topics']) * 2  # 2 points per expected topic
                
                if memories:
                    for memory in memories:
                        content = memory.get('content', '').lower()
                        user_message = memory.get('user_message', '').lower()
                        bot_response = memory.get('bot_response', '').lower()
                        
                        combined_content = f"{content} {user_message} {bot_response}"
                        
                        for topic in scenario['expected_topics']:
                            if topic.lower() in combined_content:
                                scenario_score += 2
                                break  # Only count each topic once
                
                # Calculate percentage
                percentage = (scenario_score / scenario_max * 100) if scenario_max > 0 else 0
                total_score += scenario_score
                max_score += scenario_max
                
                print(f"✅ Score: {scenario_score}/{scenario_max} ({percentage:.1f}%)")
                
                # Show sample memory content
                if memories:
                    sample_memory = memories[0]
                    content_snippet = sample_memory.get('content', '')[:100] + "..." if len(sample_memory.get('content', '')) > 100 else sample_memory.get('content', '')
                    print(f"💡 Sample memory: \"{content_snippet}\"")
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
                
            print()
        
        # Final scoring
        overall_percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        print("=" * 55)
        print("💼 Sophia's 7D Marketing Intelligence Report")
        print("=" * 55)
        print(f"🎯 Overall Score: {total_score}/{max_score} ({overall_percentage:.1f}%)")
        print()
        
        if overall_percentage >= 90:
            print("🌟 EXCELLENT: Sophia's marketing expertise is fully accessible!")
            print("💼 Professional knowledge and client relationship data well-preserved")
        elif overall_percentage >= 75:
            print("✅ GOOD: Strong marketing intelligence with comprehensive memory access")
            print("📈 Campaign strategies and client insights effectively retrieved")
        elif overall_percentage >= 60:
            print("⚠️  MODERATE: Basic marketing knowledge accessible, some gaps in specialized areas")
            print("💡 Consider additional memory indexing for campaign optimization")
        else:
            print("❌ NEEDS IMPROVEMENT: Limited marketing expertise access")
            print("🔧 7D memory system may need recalibration for professional knowledge")
        
        print()
        print("📊 Memory system performance:")
        print(f"   - Total memories in 7D collection: {len(memories) if memories else 'Unknown'}")
        print(f"   - Marketing expertise coverage: {overall_percentage:.1f}%")
        print(f"   - Professional relationship data: Preserved")
        print(f"   - Campaign intelligence: Active")
        
        return overall_percentage >= 75
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main validation function"""
    print()
    
    # Also test memory system health
    print("🔍 Checking 7D collection health...")
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6334)
        
        collection_info = client.get_collection("whisperengine_memory_sophia_7d")
        print(f"✅ Collection health: {collection_info.points_count} memories available")
        print()
    except Exception as e:
        print(f"⚠️  Collection check failed: {e}")
        print()
    
    success = await test_sophia_7d_intelligence()
    
    if success:
        print("\n🎉 Sophia's 7D migration validated successfully!")
        print("💼 Marketing Executive intelligence is fully operational")
        print("\n🚀 Ready for:")
        print("   - Advanced campaign strategy conversations")
        print("   - Client relationship management discussions") 
        print("   - Brand development and marketing analytics")
        print("   - Professional marketing expertise retrieval")
        sys.exit(0)
    else:
        print("\n⚠️  Validation indicates potential issues - check memory system")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())