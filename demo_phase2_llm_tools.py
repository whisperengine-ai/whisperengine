#!/usr/bin/env python3
"""
Demo script for Phase 2 LLM Tool Calling: Character Evolution & Emotional Intelligence

Tests the new Phase 2 tools in a controlled environment to validate:
- Character evolution tools (personality adaptation, backstory, communication style)
- Emotional intelligence tools (crisis detection, empathy calibration, proactive support)
- Integration with existing Phase 1 memory tools
"""

import asyncio
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any

# Add src to path for imports
sys.path.append('/Users/markcastillo/git/whisperengine/src')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """Mock LLM client for testing without external dependencies"""
    
    def __init__(self):
        self.call_count = 0
    
    async def generate_with_tools(self, messages, tools, max_tool_iterations=3, user_id=None):
        """Mock LLM response with tool calls"""
        self.call_count += 1
        
        # Simulate different tool call scenarios
        if "sad" in str(messages).lower() or "depressed" in str(messages).lower():
            return {
                "content": "I notice you might be feeling down. Let me help by understanding your emotional state and adapting how I respond.",
                "tool_calls": [
                    {
                        "function": {
                            "name": "detect_emotional_crisis",
                            "arguments": {
                                "crisis_indicators": ["sadness", "withdrawal", "negative_self_talk"],
                                "crisis_severity": "mild_concern",
                                "emotional_pattern_analysis": "User expressing sadness and some withdrawal from conversation",
                                "immediate_needs": ["emotional_validation", "gentle_support"],
                                "intervention_urgency": "medium",
                                "confidence_score": 0.75
                            }
                        }
                    },
                    {
                        "function": {
                            "name": "calibrate_empathy_response",
                            "arguments": {
                                "detected_emotions": ["sadness", "loneliness"],
                                "empathy_level": "high",
                                "emotional_context": {
                                    "current_situation": "expressing emotional distress",
                                    "user_personality": "introspective",
                                    "relationship_stage": "friend",
                                    "cultural_factors": "western_individualistic"
                                },
                                "response_strategy": "emotional_validation",
                                "avoid_patterns": ["minimizing", "toxic_positivity", "rushing_solutions"]
                            }
                        }
                    }
                ]
            }
        elif "personality" in str(messages).lower():
            return {
                "content": "I see you're interested in my personality. Let me adapt to better match your preferences.",
                "tool_calls": [
                    {
                        "function": {
                            "name": "adapt_personality_trait",
                            "arguments": {
                                "trait_name": "empathy",
                                "adjustment_direction": "increase",
                                "adjustment_strength": 0.7,
                                "evidence_analysis": "User seems to value emotional understanding and connection",
                                "confidence_score": 0.8
                            }
                        }
                    },
                    {
                        "function": {
                            "name": "modify_communication_style",
                            "arguments": {
                                "style_aspect": "emotional_expressiveness",
                                "user_feedback": "User responds well to empathetic communication",
                                "adaptation_strength": 0.6,
                                "relationship_stage": "friend",
                                "effectiveness_prediction": 0.85
                            }
                        }
                    }
                ]
            }
        else:
            return {
                "content": "Let me store this conversation and look for patterns to better understand you.",
                "tool_calls": [
                    {
                        "function": {
                            "name": "store_conversation_memory",
                            "arguments": {
                                "content": "General conversation about testing",
                                "importance_score": 0.5,
                                "emotional_context": {"tone": "neutral", "engagement": "medium"},
                                "conversation_topic": "testing_conversation",
                                "memory_type": "interaction"
                            }
                        }
                    }
                ]
            }


class MockMemoryManager:
    """Mock memory manager for testing"""
    
    def __init__(self):
        self.memories = []
    
    async def store_memory(self, user_id, content, memory_type="general", metadata=None):
        """Store memory in mock system"""
        memory = {
            "user_id": user_id,
            "content": content,
            "memory_type": memory_type,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        self.memories.append(memory)
        logger.info(f"Stored memory: {memory_type} - {content[:50]}...")
        return True
    
    async def retrieve_relevant_memories(self, user_id, query, limit=10):
        """Retrieve memories from mock system"""
        # Simple keyword matching for demo
        relevant = [
            m for m in self.memories 
            if m["user_id"] == user_id and any(
                word.lower() in m["content"].lower() 
                for word in query.split()
            )
        ]
        return relevant[:limit]


class MockCharacterManager:
    """Mock character manager for testing"""
    
    def __init__(self):
        self.character_traits = {
            "empathy": 0.5,
            "humor_style": "gentle",
            "formality": 0.3,
            "enthusiasm": 0.7
        }
    
    def update_trait(self, trait_name, value):
        """Update character trait"""
        self.character_traits[trait_name] = value
        logger.info(f"Updated character trait {trait_name} to {value}")


async def test_character_evolution_tools():
    """Test character evolution functionality"""
    logger.info("=== Testing Character Evolution Tools ===")
    
    # Create mock dependencies
    memory_manager = MockMemoryManager()
    character_manager = MockCharacterManager()
    llm_client = MockLLMClient()
    
    # Import and create character evolution manager
    from memory.character_evolution_tool_manager import CharacterEvolutionToolManager
    
    char_manager = CharacterEvolutionToolManager(
        character_manager, memory_manager, llm_client
    )
    
    # Test personality trait adaptation
    result = await char_manager.execute_tool(
        "adapt_personality_trait",
        {
            "trait_name": "empathy",
            "adjustment_direction": "increase",
            "adjustment_strength": 0.8,
            "evidence_analysis": "User seems to respond positively to empathetic responses",
            "confidence_score": 0.85
        },
        "test_user_123"
    )
    
    logger.info(f"Personality adaptation result: {result}")
    
    # Test backstory update
    result = await char_manager.execute_tool(
        "update_character_backstory",
        {
            "backstory_element": "experience",
            "new_experience": "Had a meaningful conversation about emotional intelligence",
            "integration_method": "add_new",
            "emotional_impact": "medium",
            "memory_triggers": ["emotional intelligence", "AI development", "empathy"]
        },
        "test_user_123"
    )
    
    logger.info(f"Backstory update result: {result}")
    
    return True


async def test_emotional_intelligence_tools():
    """Test emotional intelligence functionality"""
    logger.info("=== Testing Emotional Intelligence Tools ===")
    
    # Create mock dependencies
    memory_manager = MockMemoryManager()
    llm_client = MockLLMClient()
    
    # Import and create emotional intelligence manager
    from memory.emotional_intelligence_tool_manager import EmotionalIntelligenceToolManager
    
    ei_manager = EmotionalIntelligenceToolManager(
        memory_manager, llm_client
    )
    
    # Test crisis detection
    result = await ei_manager.execute_tool(
        "detect_emotional_crisis",
        {
            "crisis_indicators": ["hopelessness", "withdrawal", "overwhelming stress"],
            "crisis_severity": "moderate_concern",
            "emotional_pattern_analysis": "User showing signs of moderate emotional distress with withdrawal behaviors",
            "immediate_needs": ["emotional_support", "validation", "coping_strategies"],
            "intervention_urgency": "medium",
            "confidence_score": 0.78
        },
        "test_user_456"
    )
    
    logger.info(f"Crisis detection result: {result}")
    
    # Test empathy calibration
    result = await ei_manager.execute_tool(
        "calibrate_empathy_response",
        {
            "detected_emotions": ["sadness", "anxiety", "loneliness"],
            "empathy_level": "high",
            "emotional_context": {
                "current_situation": "work stress and relationship issues",
                "user_personality": "introverted, sensitive",
                "relationship_stage": "trusted_confidant",
                "cultural_factors": "values emotional authenticity"
            },
            "response_strategy": "emotional_validation",
            "avoid_patterns": ["minimizing_feelings", "giving_unsolicited_advice"]
        },
        "test_user_456"
    )
    
    logger.info(f"Empathy calibration result: {result}")
    
    # Test proactive support
    result = await ei_manager.execute_tool(
        "provide_proactive_support",
        {
            "support_triggers": ["emotional_pattern_detected", "stress_indicators"],
            "support_type": "emotional_check_in",
            "timing_strategy": "next_interaction",
            "support_approach": "gentle_suggestion",
            "expected_impact": "Increased emotional support and connection",
            "fallback_options": ["resource_sharing", "distraction_activity"]
        },
        "test_user_456"
    )
    
    logger.info(f"Proactive support result: {result}")
    
    return True


async def test_integrated_llm_tool_calling():
    """Test full LLM tool calling integration"""
    logger.info("=== Testing Integrated LLM Tool Calling ===")
    
    # Create mock dependencies
    memory_manager = MockMemoryManager()
    character_manager = MockCharacterManager()
    llm_client = MockLLMClient()
    
    # Import and create integration manager
    try:
        from memory.memory_protocol import create_llm_tool_integration_manager
        
        integration_manager = create_llm_tool_integration_manager(
            memory_manager, character_manager, llm_client
        )
        
        if integration_manager is None:
            logger.error("Failed to create LLM tool integration manager")
            return False
        
        # Test emotional crisis scenario
        logger.info("Testing emotional crisis scenario...")
        result = await integration_manager.execute_llm_with_tools(
            user_message="I'm feeling really sad and overwhelmed lately. Nothing seems to matter anymore.",
            user_id="test_user_crisis",
            character_context="Empathetic AI companion focused on emotional support",
            emotional_context={"mood": "depressed", "energy": "low", "stress": "high"}
        )
        
        logger.info(f"Crisis scenario result: {json.dumps(result, indent=2)}")
        
        # Test personality adaptation scenario
        logger.info("Testing personality adaptation scenario...")
        result = await integration_manager.execute_llm_with_tools(
            user_message="I'd like to discuss your personality and how you communicate with me.",
            user_id="test_user_personality",
            character_context="Adaptive AI with evolving personality traits"
        )
        
        logger.info(f"Personality scenario result: {json.dumps(result, indent=2)}")
        
        # Get tool analytics
        analytics = await integration_manager.get_tool_analytics()
        logger.info(f"Tool analytics: {json.dumps(analytics, indent=2)}")
        
        # Get tools summary
        tools_summary = integration_manager.get_available_tools_summary()
        logger.info(f"Available tools: {json.dumps(tools_summary, indent=2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False


async def main():
    """Main demo function"""
    logger.info("Starting Phase 2 LLM Tool Calling Demo")
    logger.info("Testing Character Evolution & Emotional Intelligence Tools")
    
    try:
        # Test individual tool managers
        char_test = await test_character_evolution_tools()
        ei_test = await test_emotional_intelligence_tools()
        
        # Test integrated system
        integration_test = await test_integrated_llm_tool_calling()
        
        # Summary
        logger.info("=== Demo Results Summary ===")
        logger.info(f"Character Evolution Tools: {'✅ PASS' if char_test else '❌ FAIL'}")
        logger.info(f"Emotional Intelligence Tools: {'✅ PASS' if ei_test else '❌ FAIL'}")
        logger.info(f"Integrated LLM Tool Calling: {'✅ PASS' if integration_test else '❌ FAIL'}")
        
        if all([char_test, ei_test, integration_test]):
            logger.info("🎉 Phase 2 implementation successful!")
        else:
            logger.warning("⚠️  Some tests failed - review implementation")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    # Activate virtual environment for proper dependencies
    print("Phase 2 LLM Tool Calling Demo")
    print("Character Evolution & Emotional Intelligence Tools")
    print("=" * 60)
    
    asyncio.run(main())