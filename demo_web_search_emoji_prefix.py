#!/usr/bin/env python3
"""
Demo: Web Search with Emoji Prefix Integration
Shows how users will see emoji prefixes when web searches are performed.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock
from src.web_search.web_search_tool_manager import WebSearchToolManager
from src.memory.llm_tool_integration_manager import LLMToolIntegrationManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """Mock LLM client for testing"""
    
    async def generate_with_tools(self, messages, tools, max_tool_iterations=5, user_id=None):
        """Mock LLM response with tool calls"""
        # Simulate LLM deciding to use web search tool
        return {
            "choices": [{
                "message": {
                    "content": "Based on recent developments, AI technology has made remarkable advances in 2025, particularly in multimodal capabilities and reasoning.",
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "search_current_events",
                                "arguments": '{"query": "AI developments 2025", "search_focus": "news"}'
                            }
                        }
                    ]
                }
            }]
        }


async def demo_emoji_prefix():
    """Demo the complete emoji prefix flow"""
    print("🌐 WhisperEngine Web Search Emoji Prefix Demo")
    print("=" * 55)
    
    # Initialize components
    web_search_manager = WebSearchToolManager()
    mock_llm_client = MockLLMClient()
    
    # Create tool integration manager
    tool_manager = LLMToolIntegrationManager(
        vector_memory_tool_manager=None,
        intelligent_memory_manager=None,
        character_evolution_tool_manager=None,
        emotional_intelligence_tool_manager=None,
        phase3_memory_tool_manager=None,
        phase4_orchestration_manager=None,
        llm_client=mock_llm_client,
        web_search_tool_manager=web_search_manager
    )
    
    # Test scenarios
    test_messages = [
        "What are the latest AI developments?",
        "Tell me about recent news in technology", 
        "What happened today in AI research?",
        "Hello, how are you doing?" # Non-web search message
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Test {i}: User asks: \"{message}\"")
        
        # Check if web search would be triggered
        web_search_needed = tool_manager._detect_web_search_request(message)
        
        if web_search_needed:
            print(f"🔍 Web search keywords detected - search will be performed")
            
            # Simulate the full flow
            try:
                result = await tool_manager.execute_llm_with_tools(
                    user_message=message,
                    user_id="test_user_123",
                    character_context="Elena Rodriguez - Marine Biologist",
                    emotional_context={"mood": "curious", "engagement": "high"}
                )
                
                if result.get("success"):
                    llm_response = result.get("llm_response", "")
                    web_search_used = result.get("web_search_used", False)
                    
                    print(f"🤖 Bot response: \"{llm_response[:100]}{'...' if len(llm_response) > 100 else ''}\"")
                    
                    if web_search_used:
                        print(f"✅ User sees 🌐 emoji indicating web search was used!")
                    else:
                        print(f"ℹ️ No web search indicator (search may have failed)")
                        
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Exception during execution: {e}")
                
        else:
            print(f"💬 Regular conversation - no web search needed")
            print(f"🤖 Bot response: \"I'm doing well! How can I help you today?\"")
            print(f"ℹ️ No emoji prefix - no network usage")
    
    print(f"\n🎯 Summary:")
    print(f"   🌐 = User knows web search was performed")
    print(f"   💬 = Regular response, no network usage") 
    print(f"\n✅ Users now have clear visibility into network usage!")


if __name__ == "__main__":
    asyncio.run(demo_emoji_prefix())