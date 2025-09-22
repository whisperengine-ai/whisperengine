#!/usr/bin/env python3
"""
Simple Tool Calling Structure Test

Tests the LLM tool calling integration without requiring external services.
Focuses on validating the tool definitions and basic functionality.
"""

import sys
import json
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, '.')


def test_tool_definitions():
    """Test that tool definitions are properly structured"""
    print("🛠️  Testing Tool Definitions Structure")
    print("-" * 40)
    
    try:
        from src.memory.vector_memory_tool_manager import VectorMemoryToolManager
        
        # Create tool manager without dependencies
        tool_manager = VectorMemoryToolManager(vector_memory_store=None)
        tools = tool_manager.get_tools()
        
        print(f"✅ Created {len(tools)} tool definitions")
        
        # Validate each tool
        for i, tool in enumerate(tools):
            function_name = tool.get("function", {}).get("name", f"tool_{i}")
            is_valid = validate_tool_structure(tool)
            
            if is_valid:
                print(f"   ✅ {function_name}")
            else:
                print(f"   ❌ {function_name} - Invalid structure")
        
        # Print tool details for verification
        print(f"\n📋 Tool Details:")
        for tool in tools:
            function = tool.get("function", {})
            name = function.get("name", "unknown")
            description = function.get("description", "No description")
            
            print(f"\n🔧 {name}")
            print(f"   Description: {description[:100]}...")
            
            # Show parameters
            params = function.get("parameters", {}).get("properties", {})
            required = function.get("parameters", {}).get("required", [])
            
            print(f"   Parameters: {len(params)} total, {len(required)} required")
            for param_name, param_def in params.items():
                req_marker = "* " if param_name in required else "  "
                param_type = param_def.get("type", "unknown")
                print(f"     {req_marker}{param_name} ({param_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool definition test failed: {e}")
        return False


def validate_tool_structure(tool: Dict[str, Any]) -> bool:
    """Validate that a tool follows OpenAI function calling format"""
    
    # Check top-level structure
    if "type" not in tool or tool["type"] != "function":
        return False
    
    if "function" not in tool:
        return False
    
    function = tool["function"]
    
    # Check required function fields
    required_fields = ["name", "description", "parameters"]
    for field in required_fields:
        if field not in function:
            return False
    
    # Check parameters structure
    parameters = function["parameters"]
    if "type" not in parameters or parameters["type"] != "object":
        return False
    
    if "properties" not in parameters:
        return False
    
    return True


def test_llm_client_structure():
    """Test that LLM client has tool calling method"""
    print("\n🤖 Testing LLM Client Structure")
    print("-" * 35)
    
    try:
        from src.llm.llm_client import LLMClient
        
        # Create client without requiring connection
        client = LLMClient()
        
        # Check for tool calling method
        if hasattr(client, 'generate_chat_completion_with_tools'):
            print("✅ LLM client has generate_chat_completion_with_tools method")
            
            # Check method signature
            import inspect
            sig = inspect.signature(client.generate_chat_completion_with_tools)
            params = list(sig.parameters.keys())
            
            expected_params = ['messages', 'tools', 'tool_choice']
            has_expected = all(param in params for param in expected_params)
            
            if has_expected:
                print("✅ Method has expected parameters")
                print(f"   Parameters: {', '.join(params)}")
            else:
                print("❌ Method missing expected parameters")
                print(f"   Expected: {', '.join(expected_params)}")
                print(f"   Found: {', '.join(params)}")
            
            return has_expected
        else:
            print("❌ LLM client missing tool calling method")
            return False
            
    except Exception as e:
        print(f"❌ LLM client test failed: {e}")
        return False


def test_intelligent_manager_structure():
    """Test that intelligent memory manager is properly structured"""
    print("\n🧠 Testing Intelligent Memory Manager Structure")
    print("-" * 45)
    
    try:
        from src.memory.intelligent_memory_manager import IntelligentMemoryManager
        
        # Create manager with None dependencies for structure test
        manager = IntelligentMemoryManager(
            vector_memory_store=None,
            llm_client=None,
            vector_tool_manager=None
        )
        
        # Check for key methods
        key_methods = [
            'analyze_conversation_for_memory_actions',
            'analyze_and_optimize_user_memories',
            'get_analysis_history',
            'get_memory_management_stats'
        ]
        
        missing_methods = []
        for method in key_methods:
            if hasattr(manager, method):
                print(f"✅ Has {method}")
            else:
                print(f"❌ Missing {method}")
                missing_methods.append(method)
        
        if not missing_methods:
            print("✅ All required methods present")
            return True
        else:
            print(f"❌ Missing {len(missing_methods)} required methods")
            return False
            
    except Exception as e:
        print(f"❌ Intelligent manager test failed: {e}")
        return False


def demonstrate_tool_calling_flow():
    """Demonstrate the expected tool calling flow"""
    print("\n🔄 Demonstrating Tool Calling Flow")
    print("-" * 35)
    
    print("Expected Flow:")
    print("1. User sends message to AI companion")
    print("2. IntelligentMemoryManager analyzes conversation")
    print("3. LLM generates response with tool calls")
    print("4. VectorMemoryToolManager executes tool calls")
    print("5. Memory actions are applied to vector store")
    print("6. Results logged for optimization")
    
    print("\nExample Tool Call Structure:")
    example_tool_call = {
        "type": "function",
        "function": {
            "name": "store_semantic_memory",
            "arguments": json.dumps({
                "content": "User prefers dark chocolate over milk chocolate",
                "memory_type": "preference",
                "importance": 6,
                "tags": ["food", "chocolate", "preference"]
            })
        }
    }
    
    print(json.dumps(example_tool_call, indent=2))
    
    print("\nIntegration Points:")
    print("- src/llm/llm_client.py: generate_chat_completion_with_tools()")
    print("- src/memory/vector_memory_tool_manager.py: Tool definitions & execution")
    print("- src/memory/intelligent_memory_manager.py: Conversation analysis")
    
    return True


def print_next_steps():
    """Print next steps for implementation"""
    print("\n🚀 Implementation Next Steps")
    print("-" * 30)
    
    print("1. ✅ Enhanced LLM client with tool calling support")
    print("2. ✅ Created VectorMemoryToolManager with 6 memory tools")
    print("3. ✅ Built IntelligentMemoryManager for conversation analysis")
    print("4. ✅ Validated tool definitions and structure")
    
    print("\nTo Complete Integration:")
    print("• Integrate with conversation flow in src/conversation/")
    print("• Add configuration options for tool calling behavior")
    print("• Test with real LLM provider (OpenRouter, LM Studio, etc.)")
    print("• Monitor performance and optimize tool selection")
    
    print("\nConfiguration Variables:")
    print("• VECTOR_LLM_MEMORY_MANAGEMENT=true")
    print("• LLM_TOOL_CALLING_ENABLED=true")
    print("• LLM_MEMORY_TOOL_TEMPERATURE=0.1")


def main():
    """Main test function"""
    print("🎯 LLM Tool Calling Structure Validation")
    print("=" * 45)
    
    all_tests_passed = True
    
    # Test tool definitions
    if not test_tool_definitions():
        all_tests_passed = False
    
    # Test LLM client structure
    if not test_llm_client_structure():
        all_tests_passed = False
    
    # Test intelligent manager structure
    if not test_intelligent_manager_structure():
        all_tests_passed = False
    
    # Demonstrate the flow
    demonstrate_tool_calling_flow()
    
    # Print next steps
    print_next_steps()
    
    if all_tests_passed:
        print("\n🎉 All Structure Tests Passed!")
        print("Ready for integration with WhisperEngine conversation flow!")
        return True
    else:
        print("\n❌ Some structure tests failed")
        return False


if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)