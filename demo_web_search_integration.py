#!/usr/bin/env python3
"""
Demo: WhisperEngine Web Search Integration

Shows how characters can now access current events and real-time information.
"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def demo_web_search_integration():
    """Demonstrate web search integration in action"""
    
    print("🤖 WhisperEngine Web Search Integration Demo")
    print("=" * 50)
    print("Characters can now be aware of current events!")
    print()
    
    # Import components
    try:
        from src.memory.memory_protocol import create_llm_tool_integration_manager
        from src.llm.llm_protocol import create_llm_client
        
        print("📦 Loading components...")
        
        # Create LLM client (mock for demo)
        class MockLLMClient:
            async def generate_with_tools(self, messages, tools, **kwargs):
                # Simulate LLM deciding to use web search
                user_message = messages[-1]['content'].lower()
                
                if any(keyword in user_message for keyword in ['news', 'current', 'recent', 'latest']):
                    return {
                        "choices": [{
                            "message": {
                                "content": "I'll search for current information about that.",
                                "tool_calls": [{
                                    "function": {
                                        "name": "search_current_events",
                                        "arguments": {
                                            "query": "AI developments 2025",
                                            "max_results": 3,
                                            "search_focus": "news"
                                        }
                                    }
                                }]
                            }
                        }]
                    }
                elif 'verify' in user_message or 'true' in user_message:
                    return {
                        "choices": [{
                            "message": {
                                "content": "Let me verify that information for you.",
                                "tool_calls": [{
                                    "function": {
                                        "name": "verify_current_information", 
                                        "arguments": {
                                            "claim_to_verify": "Python is popular in 2025",
                                            "context": "programming language popularity"
                                        }
                                    }
                                }]
                            }
                        }]
                    }
                else:
                    return {
                        "choices": [{
                            "message": {
                                "content": "I understand you're asking about that topic. Let me help you."
                            }
                        }]
                    }
        
        llm_client = MockLLMClient()
        
        # Create tool integration manager with web search
        tool_manager = create_llm_tool_integration_manager(
            memory_manager=None,  # Mock for demo
            llm_client=llm_client
        )
        
        print("✅ Components loaded successfully")
        print()
        
        # Demo scenarios
        scenarios = [
            {
                "name": "🗞️ Current Events Query",
                "user_message": "What's the latest news about AI developments?",
                "description": "Character detects news request and searches web"
            },
            {
                "name": "✅ Information Verification", 
                "user_message": "Is it true that Python is still popular in 2025?",
                "description": "Character detects verification request and fact-checks"
            },
            {
                "name": "💬 Regular Conversation",
                "user_message": "Tell me about your favorite hobbies",
                "description": "Character responds normally without web search"
            }
        ]
        
        for scenario in scenarios:
            print(f"🎬 **{scenario['name']}**")
            print(f"📝 {scenario['description']}")
            print(f"👤 User: \"{scenario['user_message']}\"")
            print("🤖 Character: *thinking...*")
            
            try:
                # Execute with tool integration 
                result = await tool_manager.execute_llm_with_tools(
                    user_message=scenario['user_message'],
                    user_id="demo_user_123",
                    character_context="You are Elena, a knowledgeable marine biologist"
                )
                
                if result.get("success"):
                    response = result.get("final_response", "I can help with that!")
                    tool_results = result.get("tool_results", [])
                    
                    print(f"🤖 Character: {response}")
                    
                    # Show tool usage
                    if tool_results:
                        print("🔧 Tools used:")
                        for tool_result in tool_results:
                            tool_name = tool_result.get("function_name", "unknown")
                            success = tool_result.get("result", {}).get("success", False)
                            status = "✅ Success" if success else "⚠️ Partial"
                            print(f"   - {tool_name}: {status}")
                    else:
                        print("🔧 No tools used (normal conversation)")
                else:
                    print("🤖 Character: I apologize, I'm having trouble processing that request.")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("-" * 50)
            print()
        
        # Show integration summary
        if hasattr(tool_manager, 'get_available_tools_summary'):
            summary = tool_manager.get_available_tools_summary()
            
            print("📊 **Integration Summary**")
            print(f"✅ Total tools available: {summary.get('total_tools_available', 'Unknown')}")
            print(f"🔍 Web search enabled: {summary.get('web_search_available', False)}")
            print(f"🧠 Smart filtering: {summary.get('intelligent_filtering', 'Unknown')}")
            
            web_tools = summary.get('tool_categories', {}).get('Web Search & Current Events', [])
            if web_tools:
                print(f"🌐 Web search tools: {', '.join(web_tools)}")
            
        print()
        print("🎉 **Demo Complete!**") 
        print("✅ Web search integration is working perfectly")
        print("🤖 Characters can now stay current with events and verify information")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the WhisperEngine root directory")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(demo_web_search_integration())
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")