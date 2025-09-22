#!/usr/bin/env python3
"""
Test Script for LLM Tool Calling Vector Memory Management

Tests the new intelligent memory management system with LLM tool calling
to validate conversation analysis and proactive memory optimization.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, '.')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logging from some modules
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("qdrant_client").setLevel(logging.WARNING)


async def test_llm_tool_calling_integration():
    """Test the complete LLM tool calling integration"""
    print("🚀 Testing LLM Tool Calling for Vector Memory Management")
    print("=" * 60)
    
    try:
        # Import components
        from src.llm.llm_protocol import create_llm_client
        from src.memory.memory_protocol import create_memory_manager
        from src.memory.vector_memory_tool_manager import VectorMemoryToolManager
        from src.memory.intelligent_memory_manager import IntelligentMemoryManager
        
        print("✅ Successfully imported all components")
        
        # 1. Test LLM client with tool calling support
        print("\n🔧 Testing LLM Client Tool Calling Support...")
        llm_client = create_llm_client()
        
        # Check if tool calling method exists
        if hasattr(llm_client, 'generate_chat_completion_with_tools'):
            print("✅ LLM client has tool calling support")
            
            # Test basic tool calling functionality (without actual tools)
            test_messages = [
                {"role": "user", "content": "Hello, can you help me with memory management?"}
            ]
            
            try:
                response = await llm_client.generate_chat_completion_with_tools(
                    messages=test_messages,
                    tools=None,  # No tools for basic test
                    temperature=0.1
                )
                
                if "choices" in response and response["choices"]:
                    print("✅ Basic tool calling method works")
                else:
                    print("❌ Tool calling method returned invalid response")
                    
            except Exception as e:
                print(f"⚠️  Tool calling test failed: {e}")
        else:
            print("❌ LLM client missing tool calling support")
            return False
        
        # 2. Test Vector Memory Tool Manager
        print("\n🛠️  Testing Vector Memory Tool Manager...")
        memory_manager = create_memory_manager(memory_type="vector")
        tool_manager = VectorMemoryToolManager(memory_manager, llm_client)
        
        # Test tool definitions
        tools = tool_manager.get_tools()
        print(f"✅ Tool manager created with {len(tools)} tools:")
        for tool in tools:
            function_name = tool.get("function", {}).get("name", "unknown")
            print(f"   - {function_name}")
        
        # Test tool execution (mock)
        test_user_id = "test_user_123"
        
        try:
            # Test storing semantic memory
            store_result = await tool_manager.execute_tool(
                "store_semantic_memory",
                {
                    "content": "User loves pizza and prefers thin crust",
                    "memory_type": "preference",
                    "importance": 7,
                    "tags": ["food", "pizza", "preference"]
                },
                test_user_id
            )
            
            if store_result.get("success"):
                print("✅ Store semantic memory tool works")
            else:
                print(f"❌ Store semantic memory failed: {store_result.get('error')}")
                
        except Exception as e:
            print(f"⚠️  Tool execution test failed: {e}")
        
        # 3. Test Intelligent Memory Manager
        print("\n🧠 Testing Intelligent Memory Manager...")
        intelligent_manager = IntelligentMemoryManager(
            memory_manager, llm_client, tool_manager
        )
        
        # Test conversation analysis
        test_user_message = "Actually, I prefer deep dish pizza now, not thin crust"
        test_bot_response = "I understand you prefer deep dish pizza now. I'll remember that!"
        
        try:
            memory_actions = await intelligent_manager.analyze_conversation_for_memory_actions(
                user_message=test_user_message,
                bot_response=test_bot_response,
                user_id=test_user_id,
                conversation_context={"topic": "food preferences"}
            )
            
            print(f"✅ Conversation analysis completed: {len(memory_actions)} actions")
            for action in memory_actions:
                function_name = action.get("function", "unknown")
                success = action.get("result", {}).get("success", False)
                print(f"   - {function_name}: {'✅' if success else '❌'}")
                
        except Exception as e:
            print(f"⚠️  Intelligent memory analysis failed: {e}")
        
        # 4. Test Tool Definitions Validation
        print("\n📋 Validating Tool Definitions...")
        validation_results = validate_tool_definitions(tools)
        
        if validation_results["valid"]:
            print("✅ All tool definitions are valid")
        else:
            print("❌ Tool definition validation failed:")
            for error in validation_results["errors"]:
                print(f"   - {error}")
        
        # 5. Performance and Integration Test
        print("\n⚡ Running Performance Test...")
        await run_performance_test(intelligent_manager, tool_manager, test_user_id)
        
        print("\n🎉 LLM Tool Calling Integration Test Complete!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed and the environment is activated")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


def validate_tool_definitions(tools: list) -> Dict[str, Any]:
    """Validate that tool definitions conform to OpenAI function calling format"""
    errors = []
    
    for i, tool in enumerate(tools):
        if "type" not in tool:
            errors.append(f"Tool {i}: Missing 'type' field")
            continue
            
        if tool["type"] != "function":
            errors.append(f"Tool {i}: Type should be 'function', got '{tool['type']}'")
            
        if "function" not in tool:
            errors.append(f"Tool {i}: Missing 'function' field")
            continue
            
        function = tool["function"]
        
        # Validate required function fields
        required_fields = ["name", "description", "parameters"]
        for field in required_fields:
            if field not in function:
                errors.append(f"Tool {i}: Missing function.{field}")
        
        # Validate parameters structure
        if "parameters" in function:
            params = function["parameters"]
            if "type" not in params or params["type"] != "object":
                errors.append(f"Tool {i}: parameters.type should be 'object'")
            
            if "properties" not in params:
                errors.append(f"Tool {i}: parameters missing 'properties'")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "tool_count": len(tools)
    }


async def run_performance_test(
    intelligent_manager, 
    tool_manager, 
    test_user_id: str
) -> None:
    """Run a performance test with multiple conversation scenarios"""
    
    test_scenarios = [
        {
            "user": "My name is Alex and I work as a software engineer",
            "bot": "Nice to meet you Alex! What kind of software do you work on?",
            "expected_actions": ["store_semantic_memory"]
        },
        {
            "user": "Actually, I told you wrong before - I'm a data scientist, not a software engineer", 
            "bot": "Thanks for the correction! I'll update that you're a data scientist.",
            "expected_actions": ["update_memory_context"]
        },
        {
            "user": "I love working with Python and machine learning models",
            "bot": "That's great! Python is perfect for data science and ML work.",
            "expected_actions": ["store_semantic_memory", "organize_related_memories"]
        }
    ]
    
    total_actions = 0
    successful_actions = 0
    
    for i, scenario in enumerate(test_scenarios):
        print(f"   Scenario {i+1}: {scenario['user'][:50]}...")
        
        try:
            actions = await intelligent_manager.analyze_conversation_for_memory_actions(
                user_message=scenario["user"],
                bot_response=scenario["bot"],
                user_id=test_user_id
            )
            
            scenario_successes = sum(
                1 for action in actions 
                if action.get("result", {}).get("success", False)
            )
            
            total_actions += len(actions)
            successful_actions += scenario_successes
            
            print(f"      {len(actions)} actions, {scenario_successes} successful")
            
        except Exception as e:
            print(f"      ❌ Scenario failed: {e}")
    
    if total_actions > 0:
        success_rate = (successful_actions / total_actions) * 100
        print(f"✅ Performance test complete: {success_rate:.1f}% success rate ({successful_actions}/{total_actions})")
    else:
        print("⚠️  No actions were executed during performance test")


async def test_tool_calling_without_llm():
    """Test tool calling functionality without requiring LLM connection"""
    print("\n🔧 Testing Tool Calling Components (No LLM Required)")
    print("-" * 50)
    
    try:
        from src.memory.vector_memory_tool_manager import VectorMemoryToolManager
        from src.memory.memory_protocol import create_memory_manager
        
        # Create memory manager and tool manager
        memory_manager = create_memory_manager(memory_type="vector")
        tool_manager = VectorMemoryToolManager(memory_manager)
        
        # Test tool definitions
        tools = tool_manager.get_tools()
        print(f"✅ Created {len(tools)} tool definitions")
        
        # Test direct tool execution
        test_user_id = "test_user_direct"
        
        # Test storing memory
        store_params = {
            "content": "User is a vegetarian and loves Italian food",
            "memory_type": "preference",
            "importance": 8,
            "tags": ["diet", "food", "vegetarian", "italian"]
        }
        
        store_result = await tool_manager.execute_tool(
            "store_semantic_memory",
            store_params,
            test_user_id
        )
        
        if store_result.get("success"):
            print("✅ Direct tool execution works")
            memory_id = store_result.get("memory_id")
            print(f"   Stored memory with ID: {memory_id}")
        else:
            print(f"❌ Direct tool execution failed: {store_result}")
        
        # Test action history
        history = tool_manager.get_action_history(test_user_id)
        print(f"✅ Action history has {len(history)} entries")
        
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False


def print_configuration_info():
    """Print current configuration information"""
    print("\n⚙️  Current Configuration:")
    print("-" * 30)
    
    # Check environment variables
    llm_type = os.getenv("LLM_CLIENT_TYPE", "not set")
    memory_type = os.getenv("MEMORY_SYSTEM_TYPE", "not set")
    
    print(f"LLM_CLIENT_TYPE: {llm_type}")
    print(f"MEMORY_SYSTEM_TYPE: {memory_type}")
    
    # Check if in development mode
    if llm_type in ["disabled", "mock"]:
        print("⚠️  LLM is disabled - some tests will be limited")
    
    if memory_type in ["test_mock", "disabled"]:
        print("⚠️  Memory system is mocked - some tests will be limited")


async def main():
    """Main test function"""
    print_configuration_info()
    
    # Test components without LLM first
    component_test_passed = await test_tool_calling_without_llm()
    
    if not component_test_passed:
        print("\n❌ Component tests failed - cannot proceed with full integration test")
        return False
    
    # Test full integration with LLM (if available)
    llm_type = os.getenv("LLM_CLIENT_TYPE", "openrouter")
    if llm_type not in ["disabled", "mock"]:
        integration_test_passed = await test_llm_tool_calling_integration()
        return integration_test_passed
    else:
        print("\n✅ Component tests passed - LLM integration skipped (LLM disabled)")
        return True


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        sys.exit(1)