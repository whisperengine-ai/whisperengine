#!/usr/bin/env python3
"""
Test script for Web Search integration in WhisperEngine

This script tests the new web search functionality without requiring
the full bot infrastructure.
"""

import asyncio
import logging
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.web_search.web_search_tool_manager import WebSearchToolManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_web_search():
    """Test web search functionality"""
    print("🔍 Testing WhisperEngine Web Search Integration")
    print("=" * 50)
    
    # Initialize web search tool manager
    search_manager = WebSearchToolManager()
    
    print(f"✅ Web Search Manager initialized with {len(search_manager.tools)} tools")
    
    # List available tools
    print("\n📋 Available Tools:")
    for i, tool in enumerate(search_manager.tools, 1):
        tool_name = tool['function']['name']
        tool_desc = tool['function']['description']
        print(f"{i}. {tool_name}: {tool_desc}")
    
    # Test current events search
    print("\n🔍 Testing Current Events Search:")
    print("Query: 'AI developments 2025'")
    
    result = await search_manager.execute_tool(
        "search_current_events",
        {
            "query": "AI developments 2025",
            "max_results": 3,
            "search_focus": "news"
        },
        "test_user_123"
    )
    
    if result.get("success"):
        print("✅ Search successful!")
        print(f"📊 Found {result.get('results_count', 0)} results")
        
        for i, search_result in enumerate(result.get("results", []), 1):
            print(f"\n{i}. {search_result.get('title', 'No title')}")
            print(f"   Source: {search_result.get('source', 'Unknown')}")
            print(f"   Snippet: {search_result.get('snippet', 'No snippet')[:100]}...")
    else:
        print("❌ Search failed:")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Test information verification
    print("\n🔍 Testing Information Verification:")
    print("Claim: 'Python is still the most popular programming language in 2025'")
    
    result = await search_manager.execute_tool(
        "verify_current_information",
        {
            "claim_to_verify": "Python is still the most popular programming language in 2025",
            "context": "programming language popularity rankings",
            "max_results": 2
        },
        "test_user_123"
    )
    
    if result.get("success"):
        print("✅ Verification search successful!")
        print(f"📊 Found {result.get('sources_found', 0)} verification sources")
        
        for i, source in enumerate(result.get("verification_sources", []), 1):
            print(f"\n{i}. {source.get('title', 'No title')}")
            print(f"   Source: {source.get('source', 'Unknown')}")
            print(f"   Snippet: {source.get('snippet', 'No snippet')[:100]}...")
    else:
        print("❌ Verification failed:")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Show usage statistics
    print("\n📈 Usage Statistics:")
    stats = search_manager.get_tool_usage_stats()
    print(f"   Total searches: {stats['total_searches']}")
    print(f"   Successful searches: {stats['successful_searches']}")
    print(f"   Success rate: {stats['success_rate']:.1%}")
    
    print("\n🎉 Web Search Integration test completed!")
    print("✅ Ready to integrate with WhisperEngine bot characters")


if __name__ == "__main__":
    try:
        asyncio.run(test_web_search())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()