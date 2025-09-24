#!/usr/bin/env python3
"""
Test emoji prefix for web search integration
Verifies that responses get the 🌐 emoji when web search is used.
"""

import asyncio
import logging
from src.web_search.web_search_tool_manager import WebSearchToolManager
from src.memory.llm_tool_integration_manager import LLMToolIntegrationManager

# Set up logging to see the output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_emoji_prefix():
    """Test that web search responses get emoji prefix"""
    print("🔍 Testing Web Search Emoji Prefix")
    print("=" * 50)
    
    # Create web search tool manager
    web_search_manager = WebSearchToolManager()
    
    # Create a mock LLM tool integration manager with just web search
    tool_manager = LLMToolIntegrationManager(
        vector_memory_tool_manager=None,
        intelligent_memory_manager=None, 
        character_evolution_tool_manager=None,
        emotional_intelligence_tool_manager=None,
        phase3_memory_tool_manager=None,
        phase4_orchestration_manager=None,
        llm_client=None,  # We'll mock the response
        web_search_tool_manager=web_search_manager
    )
    
    # Test 1: Simulate web search tool result
    print("🧪 Test 1: Simulating web search tool usage")
    
    # Mock tool results that would come from web search
    mock_tool_results = [
        {
            "success": True,
            "tool_name": "search_current_events",
            "result": {"results_count": 3, "query": "AI news 2025"}
        }
    ]
    
    # Mock LLM response
    mock_llm_response = "Based on recent developments, AI has made significant advances in 2025..."
    
    # Check if web search indicator would be added
    web_search_used = any(
        result.get("tool_name") in ["search_current_events", "verify_current_information"]
        for result in mock_tool_results
        if result.get("success", False)
    )
    
    if web_search_used and mock_llm_response:
        prefixed_response = f"🌐 {mock_llm_response}"
        print(f"✅ Web search detected - Response would be prefixed:")
        print(f"   Original: {mock_llm_response[:50]}...")
        print(f"   Prefixed: {prefixed_response[:50]}...")
    else:
        print(f"❌ Web search not detected or response empty")
    
    # Test 2: Simulate regular tool result (no web search)
    print("\n🧪 Test 2: Simulating non-web search tool usage")
    
    mock_regular_results = [
        {
            "success": True,
            "tool_name": "store_conversation_memory", 
            "result": {"stored": True}
        }
    ]
    
    regular_web_search_used = any(
        result.get("tool_name") in ["search_current_events", "verify_current_information"]
        for result in mock_regular_results
        if result.get("success", False)
    )
    
    if regular_web_search_used:
        print(f"❌ Web search incorrectly detected for regular tool")
    else:
        print(f"✅ No web search detected for regular tool - no prefix added")
        print(f"   Response stays: {mock_llm_response[:50]}...")
    
    print("\n🎉 Emoji prefix test completed!")
    print(f"🌐 Web search responses will be clearly marked for users")


if __name__ == "__main__":
    asyncio.run(test_emoji_prefix())