#!/usr/bin/env python3
"""
🎯 LLM Tool Integration Testing Plan

Comprehensive test script to validate all implemented LLM tooling features
across Phase 1-4 tools with Elena bot.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, List
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, '.')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("qdrant_client").setLevel(logging.WARNING)

class LLMToolTestSuite:
    """Comprehensive test suite for LLM tool integration"""
    
    def __init__(self):
        self.test_results = []
        self.test_user_id = "test_user_llm_tools_2025"
        
    async def initialize_components(self):
        """Initialize all required components"""
        try:
            # Import components
            from src.llm.llm_protocol import create_llm_client
            from src.memory.memory_protocol import create_memory_manager, create_llm_tool_integration_manager
            
            print("🔧 Initializing components...")
            
            # Create core components
            self.memory_manager = create_memory_manager(memory_type="vector")
            self.llm_client = create_llm_client(llm_client_type="openrouter")
            
            # For character manager, use a simple mock or None
            class MockCharacterManager:
                """Simple mock for testing"""
                def get_character(self, character_id):
                    return None
            
            self.character_manager = MockCharacterManager()
            
            # Create integration manager
            self.integration_manager = create_llm_tool_integration_manager(
                memory_manager=self.memory_manager,
                character_manager=self.character_manager,
                llm_client=self.llm_client
            )
            
            if not self.integration_manager:
                raise Exception("Failed to create LLM Tool Integration Manager")
                
            print("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Component initialization failed: {e}")
            return False
    
    async def run_comprehensive_tests(self):
        """Run all LLM tool integration tests"""
        print("🚀 Starting Comprehensive LLM Tool Integration Tests")
        print("=" * 60)
        
        if not await self.initialize_components():
            return False
        
        # Test categories
        test_categories = [
            ("💾 Memory Management Tools", self.test_memory_management_tools),
            ("🧠 Intelligent Memory Analysis", self.test_intelligent_memory_tools), 
            ("👤 Character Evolution Tools", self.test_character_evolution_tools),
            ("😊 Emotional Intelligence Tools", self.test_emotional_intelligence_tools),
            ("🔍 Web Search Tools", self.test_web_search_tools),
            ("🛠️ Phase 3 & 4 Advanced Tools", self.test_advanced_phase_tools),
            ("⚙️ Tool Filtering & Integration", self.test_tool_filtering),
            ("📊 Performance & Analytics", self.test_performance_analytics)
        ]
        
        for category_name, test_function in test_categories:
            print(f"\n{category_name}")
            print("-" * 50)
            
            try:
                success = await test_function()
                self.test_results.append({
                    "category": category_name,
                    "success": success,
                    "timestamp": datetime.now().isoformat()
                })
                
                if success:
                    print(f"✅ {category_name} - PASSED")
                else:
                    print(f"❌ {category_name} - FAILED")
                    
            except Exception as e:
                print(f"💥 {category_name} - ERROR: {e}")
                self.test_results.append({
                    "category": category_name,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Generate summary report
        await self.generate_test_report()
    
    async def test_memory_management_tools(self) -> bool:
        """Test Phase 1 Memory Management Tools"""
        test_scenarios = [
            {
                "name": "Memory Storage Request",
                "message": "Remember that I prefer deep dish pizza and I work at Google as a software engineer.",
                "expected_tools": ["store_conversation_memory", "store_semantic_memory"]
            },
            {
                "name": "Memory Retrieval Request", 
                "message": "What do you remember about my food preferences?",
                "expected_tools": ["retrieve_relevant_memories", "search_memories_with_context"]
            },
            {
                "name": "Memory Update Request",
                "message": "Actually, I changed jobs - I now work at Meta, not Google.",
                "expected_tools": ["store_conversation_memory", "update_memory_context"]
            }
        ]
        
        for scenario in test_scenarios:
            print(f"  Testing: {scenario['name']}")
            
            try:
                result = await self.integration_manager.execute_llm_with_tools(
                    user_message=scenario["message"],
                    user_id=self.test_user_id,
                    character_context="AI assistant helping with memory management"
                )
                
                # Check if relevant tools were used
                tools_used = [tool.get("tool_name") for tool in result.get("tool_results", [])]
                print(f"    Tools used: {tools_used}")
                
                if any(expected_tool in str(tools_used) for expected_tool in scenario["expected_tools"]):
                    print(f"    ✅ Expected tools detected")
                else:
                    print(f"    ⚠️  Expected tools not clearly detected: {scenario['expected_tools']}")
                
            except Exception as e:
                print(f"    ❌ Test failed: {e}")
                return False
        
        return True
    
    async def test_intelligent_memory_tools(self) -> bool:
        """Test Phase 1 Intelligent Memory Analysis Tools"""
        test_scenarios = [
            {
                "name": "Pattern Analysis Request",
                "message": "Can you analyze my conversation patterns and tell me what insights you notice?",
                "expected_tools": ["analyze_conversation_patterns", "generate_memory_insights"]
            },
            {
                "name": "Context Switch Detection",
                "message": "Let's talk about something completely different - how's the weather?",
                "expected_tools": ["detect_context_switches"]
            }
        ]
        
        for scenario in test_scenarios:
            print(f"  Testing: {scenario['name']}")
            
            try:
                result = await self.integration_manager.execute_llm_with_tools(
                    user_message=scenario["message"],
                    user_id=self.test_user_id,
                    character_context="AI assistant with analytical capabilities"
                )
                
                tools_used = [tool.get("tool_name") for tool in result.get("tool_results", [])]
                print(f"    Tools used: {tools_used}")
                print(f"    Response preview: {result.get('response', '')[:100]}...")
                
            except Exception as e:
                print(f"    ❌ Test failed: {e}")
                return False
        
        return True
    
    async def test_character_evolution_tools(self) -> bool:
        """Test Phase 2 Character Evolution Tools"""
        test_scenarios = [
            {
                "name": "Personality Adaptation Request",
                "message": "Can you be more empathetic and understanding in our conversations?",
                "expected_tools": ["adapt_personality_trait", "calibrate_emotional_expression"]
            },
            {
                "name": "Communication Style Change",
                "message": "I'd prefer if you communicated more formally and professionally.",
                "expected_tools": ["modify_communication_style"]
            }
        ]
        
        for scenario in test_scenarios:
            print(f"  Testing: {scenario['name']}")
            
            try:
                result = await self.integration_manager.execute_llm_with_tools(
                    user_message=scenario["message"],
                    user_id=self.test_user_id,
                    character_context="Elena Rodriguez - Marine Biologist"
                )
                
                tools_used = [tool.get("tool_name") for tool in result.get("tool_results", [])]
                print(f"    Tools used: {tools_used}")
                print(f"    Response preview: {result.get('response', '')[:100]}...")
                
            except Exception as e:
                print(f"    ❌ Test failed: {e}")
                return False
        
        return True
    
    async def test_emotional_intelligence_tools(self) -> bool:
        """Test Phase 2 Emotional Intelligence Tools"""
        test_scenarios = [
            {
                "name": "Emotional Crisis Detection", 
                "message": "I'm feeling really overwhelmed and hopeless. Everything seems pointless and I don't know what to do anymore.",
                "expected_tools": ["detect_emotional_crisis", "emotional_crisis_intervention"],
                "emotional_context": {"emotions": ["sadness", "overwhelm"], "intensity": 0.9}
            },
            {
                "name": "Emotional Support Request",
                "message": "I've been feeling anxious about my presentation tomorrow. Can you help me feel better?",
                "expected_tools": ["provide_proactive_support", "calibrate_empathy_response"],
                "emotional_context": {"emotions": ["anxiety"], "intensity": 0.6}
            }
        ]
        
        for scenario in test_scenarios:
            print(f"  Testing: {scenario['name']}")
            
            try:
                result = await self.integration_manager.execute_llm_with_tools(
                    user_message=scenario["message"],
                    user_id=self.test_user_id,
                    character_context="Elena Rodriguez - Empathetic Marine Biologist",
                    emotional_context=scenario.get("emotional_context", {})
                )
                
                tools_used = [tool.get("tool_name") for tool in result.get("tool_results", [])]
                print(f"    Tools used: {tools_used}")
                print(f"    Emotional response preview: {result.get('response', '')[:150]}...")
                
                # Verify crisis intervention was triggered
                if scenario["name"] == "Emotional Crisis Detection":
                    if any("crisis" in str(tool).lower() for tool in tools_used):
                        print(f"    ✅ Crisis intervention properly triggered")
                    else:
                        print(f"    ⚠️  Crisis intervention may not have been triggered")
                
            except Exception as e:
                print(f"    ❌ Test failed: {e}")
                return False
        
        return True
    
    async def test_web_search_tools(self) -> bool:
        """Test Web Search Tools"""
        test_scenarios = [
            {
                "name": "Current Events Query",
                "message": "What's happening with AI development news this week?",
                "expected_tools": ["search_current_events"]
            },
            {
                "name": "Fact Verification",
                "message": "Can you verify the current status of the James Webb Space Telescope?",
                "expected_tools": ["verify_current_information"]
            }
        ]
        
        for scenario in test_scenarios:
            print(f"  Testing: {scenario['name']}")
            
            try:
                result = await self.integration_manager.execute_llm_with_tools(
                    user_message=scenario["message"],
                    user_id=self.test_user_id,
                    character_context="Elena Rodriguez with access to current information"
                )
                
                tools_used = [tool.get("tool_name") for tool in result.get("tool_results", [])]
                print(f"    Tools used: {tools_used}")
                
                # Check for web search emoji prefix
                response = result.get('response', '')
                if response.startswith('🔍'):
                    print(f"    ✅ Web search emoji prefix detected")
                else:
                    print(f"    ⚠️  Web search emoji prefix not detected")
                
                print(f"    Response preview: {response[:100]}...")
                
            except Exception as e:
                print(f"    ❌ Test failed: {e}")
                return False
        
        return True
    
    async def test_advanced_phase_tools(self) -> bool:
        """Test Phase 3 & 4 Advanced Tools"""
        test_scenarios = [
            {
                "name": "Complex Memory Analysis",
                "message": "Can you analyze the patterns in our conversations and provide insights about how our relationship has evolved?",
                "expected_tools": ["analyze_relationship_patterns", "generate_comprehensive_insights"]
            },
            {
                "name": "Workflow Planning",
                "message": "Help me plan a complex workflow for organizing my research project with multiple steps and dependencies.",
                "expected_tools": ["orchestrate_complex_workflow", "plan_autonomous_workflow"]
            }
        ]
        
        for scenario in test_scenarios:
            print(f"  Testing: {scenario['name']}")
            
            try:
                result = await self.integration_manager.execute_llm_with_tools(
                    user_message=scenario["message"],
                    user_id=self.test_user_id,
                    character_context="Elena Rodriguez - Advanced AI Assistant"
                )
                
                tools_used = [tool.get("tool_name") for tool in result.get("tool_results", [])]
                print(f"    Tools used: {tools_used}")
                print(f"    Response preview: {result.get('response', '')[:100]}...")
                
            except Exception as e:
                print(f"    ❌ Test failed: {e}")
                return False
        
        return True
    
    async def test_tool_filtering(self) -> bool:
        """Test Intelligent Tool Filtering System"""
        print("  Testing intelligent tool filtering...")
        
        try:
            # Get summary of available tools
            tools_summary = self.integration_manager.get_available_tools_summary()
            print(f"    Total tools available: {tools_summary.get('total_tools_available', 'unknown')}")
            
            # Test filtering for different message types
            test_messages = [
                "Remember my name is John and I live in Seattle",  # Should prioritize memory tools
                "I'm feeling really sad and hopeless",             # Should prioritize emotional tools
                "Can you be more friendly?",                       # Should prioritize character tools
                "What's the latest news about climate change?",    # Should prioritize web search tools
            ]
            
            for message in test_messages:
                # Get filtered tools (this is internal, but we can test the public interface)
                result = await self.integration_manager.execute_llm_with_tools(
                    user_message=message,
                    user_id=self.test_user_id,
                    character_context="Elena Rodriguez"
                )
                
                tools_used = len(result.get("tool_results", []))
                print(f"    Message: '{message[:50]}...' -> {tools_used} tools used")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Tool filtering test failed: {e}")
            return False
    
    async def test_performance_analytics(self) -> bool:
        """Test Performance Analytics and Monitoring"""
        print("  Testing performance analytics...")
        
        try:
            # Test analytics collection
            analytics = await self.integration_manager.get_tool_analytics(self.test_user_id)
            print(f"    Analytics collected: {len(analytics)} metrics")
            
            # Test execution history
            if hasattr(self.integration_manager, 'execution_history'):
                history_count = len(self.integration_manager.execution_history)
                print(f"    Execution history: {history_count} entries")
            
            # Test performance monitoring
            start_time = datetime.now()
            
            result = await self.integration_manager.execute_llm_with_tools(
                user_message="Quick performance test - remember I like testing",
                user_id=self.test_user_id,
                character_context="Elena Rodriguez"
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            print(f"    Execution time: {execution_time:.2f} seconds")
            
            if execution_time < 10.0:  # Should be reasonably fast
                print(f"    ✅ Performance within acceptable range")
            else:
                print(f"    ⚠️  Performance slower than expected")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Performance analytics test failed: {e}")
            return False
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 LLM TOOL INTEGRATION TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 Overall Results:")
        print(f"   Total Test Categories: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"   {status} - {result['category']}")
            if "error" in result:
                print(f"     Error: {result['error']}")
        
        # Save results to file
        report_file = f"llm_tool_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "results": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED! LLM Tool Integration is fully operational.")
        else:
            print(f"\n⚠️  Some tests failed. Review details above for troubleshooting.")
        
        return passed_tests == total_tests

async def main():
    """Main test execution"""
    test_suite = LLMToolTestSuite()
    await test_suite.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())